# SPDX-FileCopyrightText: 2022-present Spyder Development Team and envs-manager contributors
#
# SPDX-License-Identifier: MIT

import json
import logging
import os
from pathlib import Path
import shutil
import subprocess

from packaging.version import parse
import yaml

from envs_manager.backends.api import (
    BackendActionResult,
    BackendInstance,
    get_package_info,
    run_command,
)

MICROMAMBA_VARIANT = "micromamba"
CONDA_VARIANT = "conda"


logger = logging.getLogger("envs-manager")


class CondaLikeInterface(BackendInstance):
    ID = "conda-like"

    @property
    def python_executable_path(self):
        if os.name == "nt":
            python_executable_path = Path(self.environment_path) / "python.exe"
        else:
            python_executable_path = Path(self.environment_path) / "bin" / "python"

        return str(python_executable_path)

    def validate(self):
        if self.external_executable is None:
            if os.name == "nt":
                cmd_list = ["conda.exe", "conda.bat", "mamba.exe", "micromamba.exe"]
            else:
                cmd_list = ["conda", "mamba", "micromamba"]

            for cmd in cmd_list:
                if shutil.which(cmd):
                    self.external_executable = shutil.which(cmd)

        if self.external_executable:
            command = [self.external_executable, "--version"]
            try:
                result = run_command(command, capture_output=True)
                version = result.stdout.split()
                if len(version) <= 1:
                    # We don't support Micromamba 2.0+ because it's not very reliable
                    if parse(version[0]) < parse("2.0.0"):
                        self.executable_variant = MICROMAMBA_VARIANT
                    else:
                        return False
                else:
                    # This is the minimal conda version we support
                    if parse(version[1]) > parse("24.1.0"):
                        self.executable_variant = version[0]
                    else:
                        return False
                return True
            except Exception as error:
                logger.error(error.stderr)
        return False

    def create_environment(self, packages=None, channels=None, force=False):
        command = [self.external_executable, "create", "-p", self.environment_path]

        packages = [] if packages is None else packages
        if packages:
            command += packages

        channels = ["conda-forge"] if channels is None else channels
        if channels:
            for channel in channels:
                command += ["-c"] + [channel]
        if force:
            command += ["-y"]

        try:
            result = run_command(command, capture_output=True)
            logger.info(result.stdout)
            return BackendActionResult(status=True, output=result.stdout)
        except subprocess.CalledProcessError as error:
            return BackendActionResult(status=False, output=error.stderr)
        except Exception as error:
            return BackendActionResult(status=False, output=str(error))

    def delete_environment(self, force=False):
        command = [
            self.external_executable,
            "remove",
            "-p",
            self.environment_path,
            "--all",
        ]
        if force:
            command += ["-y"]

        try:
            result = run_command(command, capture_output=True)
            logger.info(result.stdout)
            return BackendActionResult(status=True, output=result.stdout)
        except subprocess.CalledProcessError as error:
            return BackendActionResult(status=False, output=error.stderr)
        except Exception as error:
            return BackendActionResult(status=False, output=str(error))

    def activate_environment(self):
        raise NotImplementedError()

    def deactivate_environment(self):
        raise NotImplementedError()

    def export_environment(self, export_file_path=None):
        command = [
            self.external_executable,
            "env",
            "export",
            "-p",
            self.environment_path,
            "--from-history",
        ]
        try:
            result = run_command(command, capture_output=True)
            if export_file_path:
                with open(export_file_path, "w") as exported_file:
                    exported_file.write(result.stdout)
            logger.info(result.stdout)
            return BackendActionResult(status=True, output=result.stdout)
        except subprocess.CalledProcessError as error:
            logger.error(error.stderr)
            return BackendActionResult(status=False, output=error.stderr)
        except Exception as error:
            return BackendActionResult(status=False, output=str(error))

    def import_environment(self, import_file_path, force=False):
        if self.executable_variant == MICROMAMBA_VARIANT:
            command = [
                self.external_executable,
                "create",
                "-p",
                self.environment_path,
                f"--file={import_file_path}",
            ]
        else:
            command = [
                self.external_executable,
                "env",
                "create",
                "-p",
                self.environment_path,
                f"--file={import_file_path}",
            ]

        if force:
            command += ["-y"]

        try:
            result = run_command(command, capture_output=True)
            logger.info(result.stdout)
            return BackendActionResult(status=True, output=result.stdout)
        except subprocess.CalledProcessError as error:
            logger.error(error.stderr)
            return BackendActionResult(
                status=False,
                output=(
                    f"{error.stderr}\nNote: Importing environments only works for "
                    f"environment files created with the same operating system."
                ),
            )
        except Exception as error:
            return BackendActionResult(status=False, output=str(error))

    def install_packages(
        self,
        packages,
        channels=None,
        force=False,
        capture_output=False,
    ):
        command = [
            self.external_executable,
            "install",
            "-p",
            self.environment_path,
        ] + packages

        if force:
            command += ["-y"]

        channels = ["conda-forge"] if channels is None else channels
        if channels:
            for channel in channels:
                command += ["-c"] + [channel]

        try:
            result = run_command(command, capture_output=capture_output)
            if capture_output:
                logger.info(result.stdout or result.stderr)
            return BackendActionResult(
                status=True, output=result.stdout or result.stderr
            )
        except subprocess.CalledProcessError as error:
            logger.error(error.stderr)
            return BackendActionResult(status=False, output=error.stderr)
        except Exception as error:
            return BackendActionResult(status=False, output=str(error))

    def uninstall_packages(self, packages, force=False, capture_output=False):
        command = [
            self.external_executable,
            "remove",
            "-p",
            self.environment_path,
        ] + packages
        if force:
            command += ["-y"]
        try:
            result = run_command(command, capture_output=capture_output)
            if capture_output:
                logger.info(result.stdout or result.stderr)
            return BackendActionResult(
                status=True, output=result.stdout or result.stderr
            )
        except subprocess.CalledProcessError as error:
            if "PackagesNotFoundError" in error.stderr:
                return BackendActionResult(status=True, output=error.stderr)
            logger.error(error.stderr)
            return BackendActionResult(status=False, output=error.stderr)
        except Exception as error:
            return BackendActionResult(status=False, output=str(error))

    def update_packages(self, packages, force=False, capture_output=False):
        command = [
            self.external_executable,
            "update",
            "-p",
            self.environment_path,
        ] + packages
        if force:
            command += ["-y"]
        try:
            result = run_command(command, capture_output=capture_output)
            if capture_output:
                logger.info(result.stdout)
                if "All requested packages already installed" in result.stdout:
                    return BackendActionResult(status=False, output=result.stdout)
                else:
                    return BackendActionResult(status=True, output=result.stdout)
            else:
                return BackendActionResult(status=True, output=result.stdout)
        except subprocess.CalledProcessError as error:
            logger.error(error.stderr)
            return BackendActionResult(status=False, output=error.stderr)
        except Exception as error:
            return BackendActionResult(status=False, output=str(error))

    def list_packages(self):
        command = [self.external_executable, "list", "-p", self.environment_path]
        result = run_command(command, capture_output=True)
        result_lines = result.stdout.split("\n")

        export_env_result = self.export_environment()
        if export_env_result["status"]:
            packages_requested = yaml.load(
                export_env_result["output"], Loader=yaml.FullLoader
            )["dependencies"]
            packages_requested = [
                package.split("[")[0].split("=")[0] for package in packages_requested
            ]
        else:
            packages_requested = []

        if self.executable_variant == MICROMAMBA_VARIANT:
            skip_lines = 4
        else:
            skip_lines = 3

        formatted_packages = []
        formatted_list = dict(
            environment=self.environment_path, packages=formatted_packages
        )
        for package in result_lines[skip_lines:-1]:
            package_info = package.split()
            package_name = package_info[0]
            package_build = None if len(package_info) <= 2 else package_info[2]
            package_channel = None if len(package_info) <= 3 else package_info[3]
            package_full_info = get_package_info(package_name, channel=package_channel)
            package_description = (
                package_full_info["info"]["summary"] if package_full_info else None
            )
            package_requested = package_name in packages_requested
            formatted_package = dict(
                name=package_name,
                version=package_info[1],
                build=package_build,
                channel=package_channel,
                description=package_description,
                requested=package_requested,
            )
            formatted_packages.append(formatted_package)

        logger.info(result.stdout)
        return BackendActionResult(status=True, output=formatted_list)

    def list_environments(self):
        environments = {}
        first_environment = False
        command = [self.external_executable, "env", "list", "--json"]

        envs_directory = Path(self.envs_directory)
        envs_directory.mkdir(parents=True, exist_ok=True)

        try:
            result = run_command(command, capture_output=True)
            logger.debug(result.stdout)

            result_json = json.loads(result.stdout)
            logger.debug(result_json)

            logger.info(f"# {self.ID} environments")
            for env_dir in result_json["envs"]:
                env_dir_path = Path(env_dir)
                if envs_directory in env_dir_path.parents:
                    if not first_environment:
                        first_environment = True
                    environments[env_dir_path.name] = str(env_dir_path)
                    logger.info(f"{env_dir_path.name} - {str(env_dir_path)}")

            if not first_environment:
                logger.info(
                    f"No environments found for {self.ID} in {self.envs_directory}"
                )

            return BackendActionResult(status=True, output=environments)
        except subprocess.CalledProcessError as error:
            logger.error(error.stderr)
            return BackendActionResult(status=False, output=error.stderr)
        except Exception as error:
            return BackendActionResult(status=False, output=str(error))
