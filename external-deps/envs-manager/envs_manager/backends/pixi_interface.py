# SPDX-FileCopyrightText: 2022-present Spyder Development Team and envs-manager contributors
#
# SPDX-License-Identifier: MIT

import base64
import json
import logging
import os
from pathlib import Path
import subprocess
import zipfile

from packaging.version import parse
from rattler import AboutJson
import requests

from envs_manager.backends.api import BackendInstance, BackendActionResult, run_command


logger = logging.getLogger("envs-manager")


class PixiInterface(BackendInstance):
    ID = "pixi"

    def __init__(self, environment_path, envs_directory, bin_directory):
        super().__init__(environment_path, envs_directory, bin_directory)

        # We use this to save the Pixi packages cache directory
        self._cache_dir = None

    @property
    def python_executable_path(self):
        pixi_env_dir = Path() / ".pixi" / "envs" / "default"

        if os.name == "nt":
            python_executable_path = (
                Path(self.environment_path) / pixi_env_dir / "python.exe"
            )
        else:
            python_executable_path = (
                Path(self.environment_path) / pixi_env_dir / "bin" / "python"
            )

        return str(python_executable_path)

    def validate(self):
        self.external_executable = self.find_backend_executable(exec_name="pixi")

        if self.external_executable is None:
            self.install_backend_executable()
            self.external_executable = self.find_backend_executable(exec_name="pixi")

        if self.external_executable:
            command = [self.external_executable, "--version"]
            try:
                result = run_command(command, capture_output=True)
                version = result.stdout.split()[1]
                if parse(version) >= parse("0.47.0"):
                    return True
            except subprocess.CalledProcessError as error:
                logger.error(error.stderr.strip())
            except Exception as error:
                logger.error(error, exc_info=True)

        return False

    def install_backend_executable(self):
        install_script = f"install{'.ps1' if os.name == 'nt' else '.sh'}"
        path_to_install_script = Path(self.bin_directory) / install_script

        # Download script to install Pixi
        req = requests.get(f"https://pixi.sh/{install_script}")
        with open(str(path_to_install_script), "w") as f:
            f.write(req.text)

        # Env vars to control how Pixi is installed
        env = os.environ.copy()
        env["PIXI_HOME"] = str(Path(self.bin_directory).parent)
        env["PIXI_NO_PATH_UPDATE"] = "true"

        # Install Pixi
        if os.name == "nt":
            install_command = [
                "powershell.exe",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(path_to_install_script),
            ]
        else:
            install_command = ["sh", install_script]

        try:
            run_command(
                install_command,
                run_env=env,
                cwd=self.bin_directory,
            )
        except subprocess.CalledProcessError as error:
            logger.error(error.stderr.strip())
            return
        except Exception as error:
            logger.error(error, exc_info=True)
            return

        # Cleanup
        try:
            os.remove(path_to_install_script)
        except Exception:
            pass

    def create_environment(self, packages=None, channels=None, force=False):
        # We need to run `pixi init` first
        init_command = [
            self.external_executable,
            "init",
            # Set all these platforms for the project so that its lock file works in
            # any OS supported by Spyder.
            "--platform",
            "linux-64",
            "--platform",
            "win-64",
            "--platform",
            "osx-64",
            "--platform",
            "osx-arm64",
            self.environment_path,
        ]

        if channels:
            for channel in channels:
                init_command += ["-c"] + [channel]

        try:
            result = run_command(init_command, capture_output=True)
            output = result.stdout or result.stderr
            logger.info(output.strip())
        except subprocess.CalledProcessError as error:
            error_text = error.stderr.strip()
            logger.error(error_text)
            return BackendActionResult(status=False, output=error_text)
        except Exception as error:
            logger.error(error, exc_info=True)
            return BackendActionResult(status=False, output=str(error))

        if packages:
            if not isinstance(packages, list):
                packages = [packages]

            command = [self.external_executable, "add"] + packages
            try:
                result = run_command(
                    command, capture_output=True, cwd=self.environment_path
                )
                output = (result.stdout or result.stderr).strip()
                logger.info(output)
                return BackendActionResult(status=True, output=output)
            except subprocess.CalledProcessError as error:
                error_text = error.stderr.strip()
                logger.error(error_text)
                return BackendActionResult(status=False, output=error_text)
            except Exception as error:
                logger.error(error, exc_info=True)
                return BackendActionResult(status=False, output=str(error))

    def delete_environment(self, force=False):
        # There is no command in Pixi to remove an env, so we rely on the OS
        # for that.
        # TODO: Add validation on Windows when the env is in use
        command = [
            "rmdir" if os.name == "nt" else "rm",
            "/S" if os.name == "nt" else "-r",  # Remove all files and subdirs
            "/Q" if os.name == "nt" else "-f",  # Don't ask
            self.environment_path,
        ]

        try:
            result = run_command(command, capture_output=True)
            logger.info(f"Deleting environment located at {self.environment_path}")
            return BackendActionResult(status=True, output=result.stdout)
        except subprocess.CalledProcessError as error:
            error_text = error.stderr.strip()
            logger.error(error_text)
            return BackendActionResult(status=False, output=error_text)
        except Exception as error:
            logger.error(error, exc_info=True)
            return BackendActionResult(status=False, output=str(error))

    def export_environment(self, export_file_path=None):
        env_path = Path(self.environment_path)

        try:
            # Use a temp zip file if necessary
            remove_zip_file = False
            if export_file_path is None:
                export_file_path = str(env_path / f"export_{env_path.name}.zip")
                remove_zip_file = True

            # Group pixi files into a single zip one
            with zipfile.ZipFile(export_file_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(str(env_path / "pixi.toml"), arcname="pixi.toml")
                zf.write(str(env_path / "pixi.lock"), arcname="pixi.lock")

            # Read zip file contents to send them to the frontend
            with open(export_file_path, "rb") as file:
                zip_content = file.read()

            # Remove temp zip file
            if remove_zip_file:
                try:
                    Path(export_file_path).unlink()
                except Exception:
                    pass
            else:
                logger.info(f"Environment exported to {export_file_path}")

            return BackendActionResult(status=True, output=zip_content)
        except Exception as error:
            logger.error(error, exc_info=True)
            return BackendActionResult(status=False, output=str(error))

    def import_environment(self, import_file_path, force=False):
        # Create directory where the environment will be installed
        env_path = Path(self.environment_path)
        if env_path.is_dir():
            msg = "An environment with the selected name already exists"
            logger.info(msg)
            return BackendActionResult(status=False, output=msg)
        else:
            env_path.mkdir(parents=True)

        # Validations for the zip file
        remove_import_file = False
        if import_file_path.endswith(".zip"):
            # Check if the import file exists
            if not Path(import_file_path).is_file():
                msg = "The import file you passed doesn't exist"
                logger.info(msg)
                return BackendActionResult(status=False, output=msg)
        else:
            try:
                # Check if we received base64 enconded bytes, which can be sent from
                # the frontend as the contents of the file itself. If that's the case,
                # create a temp zip file from them.
                decoded_bytes = base64.b64decode(import_file_path.encode("utf-8"))
                import_file_path = str(
                    Path(self.envs_directory) / (env_path.name + ".zip")
                )
                with open(import_file_path, "wb") as file:
                    file.write(decoded_bytes)

                remove_import_file = True
            except Exception:
                msg = (
                    "It was not possible to use the bytes you passed to create the "
                    "import file"
                )
                logger.info(msg)
                return BackendActionResult(status=False, output=msg)

        # Uncompress zip file
        try:
            with zipfile.ZipFile(import_file_path, "r") as zf:
                zf.extractall(path=str(env_path))
        except Exception as error:
            logger.error(error, exc_info=True)

            if remove_import_file:
                try:
                    os.remove(str(import_file_path))
                except Exception:
                    pass

            msg = (
                f"There was an error uncompressing the import file. The error is: "
                f"{error}"
            )
            return BackendActionResult(status=False, output=msg)

        # Remove temp file if necessary
        if remove_import_file:
            try:
                Path(import_file_path).unlink()
            except Exception:
                pass

        # Create the environment
        command = [self.external_executable, "install"]
        try:
            result = run_command(
                command, capture_output=True, cwd=self.environment_path
            )
            output = (result.stdout or result.stderr).strip()
            logger.info(output)
            return BackendActionResult(status=True, output=output)
        except subprocess.CalledProcessError as error:
            error_text = error.stderr.strip()
            logger.error(error_text)
            return BackendActionResult(status=False, output=error_text)
        except Exception as error:
            logger.error(error, exc_info=True)
            return BackendActionResult(status=False, output=str(error))

    def install_packages(
        self,
        packages,
        channels=None,
        force=False,
        capture_output=False,
    ):
        # Add channels to pixi.toml
        if channels is not None:
            channels_command = [
                self.external_executable,
                "workspace",
                "channel",
                "add",
            ] + channels

            try:
                result = run_command(
                    channels_command,
                    capture_output=capture_output,
                    cwd=self.environment_path,
                )
                logger.info((result.stdout or result.stderr).strip())
            except subprocess.CalledProcessError as error:
                error_text = error.stderr.strip()
                logger.error(error_text)
                return BackendActionResult(status=False, output=error_text)
            except Exception as error:
                logger.error(error, exc_info=True)
                return BackendActionResult(status=False, output=str(error))

        # Add packages
        command = [self.external_executable, "add"] + packages

        try:
            result = run_command(
                command, capture_output=capture_output, cwd=self.environment_path
            )

            output = None
            if capture_output:
                output = (result.stdout or result.stderr).strip()
                logger.info(output)

            return BackendActionResult(status=True, output=output if output else "")
        except subprocess.CalledProcessError as error:
            error_text = error.stderr.strip()
            logger.error(error_text)
            return BackendActionResult(status=False, output=error_text)
        except Exception as error:
            logger.error(error, exc_info=True)
            return BackendActionResult(status=False, output=str(error))

    def uninstall_packages(self, packages, force=False, capture_output=False):
        command = [self.external_executable, "remove"] + packages

        try:
            result = run_command(
                command, capture_output=capture_output, cwd=self.environment_path
            )

            output = None
            if capture_output:
                output = (result.stdout or result.stderr).strip()
                logger.info(output)

            return BackendActionResult(status=True, output=output if output else "")
        except subprocess.CalledProcessError as error:
            error_text = error.stderr.strip()
            logger.error(error_text)
            return BackendActionResult(status=False, output=error_text)
        except Exception as error:
            logger.error(error, exc_info=True)
            return BackendActionResult(status=False, output=str(error))

    def update_packages(self, packages, force=False, capture_output=False):
        command = [self.external_executable, "upgrade"] + packages

        try:
            result = run_command(
                command, capture_output=capture_output, cwd=self.environment_path
            )

            output = None
            if capture_output:
                output = (result.stdout or result.stderr).strip()
                logger.info(output)
                return BackendActionResult(status=True, output=output)
            else:
                return BackendActionResult(status=True, output="")
        except subprocess.CalledProcessError as error:
            error_text = error.stderr.strip()
            logger.error(error_text)
            return BackendActionResult(status=False, output=error_text)
        except Exception as error:
            logger.error(error, exc_info=True)
            return BackendActionResult(status=False, output=str(error))

    def list_packages(self):
        # All packages
        command = [self.external_executable, "list"]
        result = run_command(command, capture_output=True, cwd=self.environment_path)
        result_lines = result.stdout.split("\n")

        # Requsted packages
        requested_command = [self.external_executable, "list", "--explicit"]
        result_requested = run_command(
            requested_command, capture_output=True, cwd=self.environment_path
        )
        packages_requested = result_requested.stdout.split("\n")[1:-1]
        packages_requested = [package.split()[0] for package in packages_requested]

        formatted_packages = []
        formatted_list = dict(
            environment=self.environment_path, packages=formatted_packages
        )

        for package in result_lines[1:-1]:
            package_info = package.split()
            package_name = package_info[0]
            package_version = package_info[1]
            package_build = package_info[2]
            package_channel = package_info[5]
            package_requested = package_name in packages_requested

            package_dir = package_name + "-" + package_version + "-" + package_build
            package_full_info = self._get_package_info(package_dir)
            package_description = (
                package_full_info.description or package_full_info.summary
            )

            # Only take the first sentence of the description and replace eols by
            # spaces
            if package_description:
                package_description = package_description.split(".")[0].replace(
                    "\n", " "
                )

            formatted_package = dict(
                name=package_name,
                version=package_version,
                build=package_build,
                channel=package_channel,
                description=package_description,
                requested=package_requested,
            )
            formatted_packages.append(formatted_package)

        logger.info(result.stdout.strip())
        return BackendActionResult(status=True, output=formatted_list)

    def list_environments(self):
        environments = {}

        logger.info(f"# {self.ID} environments")
        for env_dir_path in Path(self.envs_directory).iterdir():
            environments[env_dir_path.name] = str(env_dir_path)
            logger.info(f"{env_dir_path.name} - {str(env_dir_path)}")

        return BackendActionResult(status=True, output=environments)

    def _get_package_info(self, package_dir):
        """
        Get package information from the Pixi packages cache.

        Parameters
        ----------
        package_dir : str
            Package directory name in the Pixi packages cache.

        Returns
        -------
        package_info : AboutJson
            Py-rattler object with metadata about the package.
        """
        info = None

        if self._cache_dir is None:
            try:
                command = [self.external_executable, "info", "--json"]
                result = run_command(command, capture_output=True)
                self._cache_dir = json.loads(result.stdout).get("cache_dir")
            except subprocess.CalledProcessError as error:
                logger.error(error, exc_info=True)
                return

        if self._cache_dir is not None:
            absolute_package_dir = Path(self._cache_dir) / "pkgs" / package_dir
            info = AboutJson.from_package_directory(str(absolute_package_dir))

        return info
