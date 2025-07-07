# SPDX-FileCopyrightText: 2022-present Spyder Development Team and envs-manager contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import logging
from pathlib import Path
import subprocess
from typing import TypedDict

import requests


logger = logging.getLogger("envs-manager")


PYPI_API_PACKAGE_INFO_URL = "https://pypi.org/pypi/{package_name}/json"
ANACONDA_API_PACKAGE_INFO = "https://api.anaconda.org/package/{channel}/{package_name}"


def run_command(command, capture_output=True, run_env=None, cwd=None):
    """
    Run commands using `subprocess.run`

    Parameters
    ----------
    command : list[str]
        List of string arguments that conform the command to be executed.
    capture_output : bool, optional
        If the output (stdout and stderr) of the command should be stored. The default
        is True.
    run_env : dict, optional
        Process environment to use when running the command. The default is None.

    Returns
    -------
    result : subprocess.CompletedProcess
        The completed process result object.

    """
    if capture_output:
        result = subprocess.run(
            command,
            capture_output=capture_output,
            check=True,
            text=True,
            env=run_env,
            cwd=cwd,
        )
    else:
        result = subprocess.run(
            command, stderr=subprocess.PIPE, check=True, text=True, env=run_env, cwd=cwd
        )
    return result


def get_package_info(package_name, channel=None):
    """
    Get package information from the PyPI JSON API and fallback to the
    Anaconda package info API endpoint if needed and a channel is provided.

    Parameters
    ----------
    package_name : str
        Package name to query.
    channel : str, optional
        In case of fallback to the Anaconda endpoint check package info for
        the given package channel. The default is None.

    Returns
    -------
    package_info : dict
        Information about the package (e.g. metadata like its summary).
    """
    package_info_url = PYPI_API_PACKAGE_INFO_URL.format(package_name=package_name)
    package_info = requests.get(package_info_url).json()

    # Here the `message` key is checked since the PyPI JSON API endpoint returns
    # `{"message": "Not Found"}` in case a package was not found.
    # The fallback to the Ananconda API package info endpoint is only done if a `channel` is provided
    # Without a channel the Anaconda endpoint can't be used.
    if "message" in package_info and channel:
        package_info_url = ANACONDA_API_PACKAGE_INFO.format(
            channel=channel, package_name=package_name
        )
        package_info = {"info": requests.get(package_info_url).json()}
    elif "message" in package_info:
        package_info = None
    return package_info


class BackendActionResult(TypedDict):
    """Dictionary to report the result of a backend's action."""

    status: bool
    """True if the action was successful, False otherwise."""

    output: str
    """Action's output."""


class BackendInstance:
    ID = ""

    def __init__(
        self,
        environment_path: str,
        envs_directory: str,
        bin_directory: str,
    ):
        self.environment_path = environment_path
        self.envs_directory = envs_directory
        self.bin_directory = bin_directory
        self.external_executable = None
        self.executable_variant = None
        assert self.validate(), f"{self.ID} backend unavailable!"

    @property
    def python_executable_path(self) -> str:
        raise NotImplementedError

    def validate(self) -> bool:
        pass

    def find_backend_executable(self, exec_name: str):
        """Return the backend executable in bin_directory, if available."""
        cmd_list = [exec_name, f"{exec_name}.exe"]
        for cmd in cmd_list:
            path = Path(self.bin_directory) / cmd
            if path.exists():
                return str(path)

        return

    def install_backend_executable(self):
        """Install the backend executable in bin_directory."""
        raise NotImplementedError

    def create_environment(
        self,
        packages: list[str] | None = None,
        channels: list[str] | None = None,
        force: bool = False,
    ) -> BackendActionResult:
        raise NotImplementedError

    def delete_environment(self, force: bool = False) -> BackendActionResult:
        raise NotImplementedError

    def activate_environment(self):
        raise NotImplementedError

    def deactivate_environment(self):
        raise NotImplementedError

    def export_environment(
        self, export_file_path: str | None = None
    ) -> BackendActionResult:
        raise NotImplementedError

    def import_environment(
        self, import_file_path: str, force: bool = False
    ) -> BackendActionResult:
        raise NotImplementedError

    def install_packages(
        self,
        packages: list[str],
        channels: list[str] | None = None,
        force: bool = False,
        capture_output: bool = False,
    ) -> BackendActionResult:
        raise NotImplementedError

    def uninstall_packages(
        self, packages: list[str], force: bool = False, capture_output: bool = False
    ) -> BackendActionResult:
        raise NotImplementedError

    def update_packages(
        self, packages: list[str], force: bool = False, capture_output: bool = False
    ) -> BackendActionResult:
        raise NotImplementedError

    def list_packages(self) -> BackendActionResult:
        raise NotImplementedError

    def list_environments(self) -> BackendActionResult:
        raise NotImplementedError

    def create_kernelspec(
        self,
        name: str,
        display_name: str | None = None,
        profile: str | None = None,
        prefix: str | None = None,
        user: bool = True,
        env: dict[str, str] | None = None,
        frozen_modules: bool = False,
    ) -> BackendActionResult:
        """
        Create a Jupyter kernelspec for the environment.

        Parameters
        ----------
        name : str
            Name of the kernelspec.
        display_name : str, optional
            Display name of the kernelspec. If None, defaults to the environment name.
        profile : str, optional
            IPython profile to load. If None, defaults to the default profile.
        prefix : str, optional
            Install prefix for the kernelspec. If None, defaults to sys.prefix.
        user : bool, optional
            Install for the current user instead of system-wide. The default is True.
        env : dict[str, str], optional
            Environment variables to set for the kernel. The default is None.
        frozen_modules : bool, optional
            Enable frozen modules for potentially faster startup. The default is False.

        Returns
        -------
        BackendActionResult
            Result of the action.
        """
        command = [self.python_executable_path, "-m", "ipykernel", "install"]
        if user:
            command.append("--user")
        if name:
            command.extend(["--name", name])
        if display_name:
            command.extend(["--display-name", display_name])
        if profile:
            command.extend(["--profile", profile])
        if prefix:
            command.extend(["--prefix", prefix])
        if env:
            for key, value in env.items():
                command.extend(["--env", f"{key}={value}"])
        if frozen_modules:
            command.append("--frozen_modules")

        try:
            result = run_command(command, capture_output=True)
            output = result.stdout or result.stderr
            logger.info(output.strip())
        except subprocess.CalledProcessError as error:
            error_text = error.stderr.strip()
            logger.error(error_text)
            return BackendActionResult(status=False, output=error_text)
        except Exception as error:
            logger.error(error, exc_info=True)
            return BackendActionResult(status=False, output=str(error))

        return BackendActionResult(status=True, output=output.strip())


# parser.add_argument(
#             "--user",
#             action="store_true",
#             help="Install for the current user instead of system-wide",
#         )
#         parser.add_argument(
#             "--name",
#             type=str,
#             default=KERNEL_NAME,
#             help="Specify a name for the kernelspec."
#             " This is needed to have multiple IPython kernels at the same time.",
#         )
#         parser.add_argument(
#             "--display-name",
#             type=str,
#             help="Specify the display name for the kernelspec."
#             " This is helpful when you have multiple IPython kernels.",
#         )
#         parser.add_argument(
#             "--profile",
#             type=str,
#             help="Specify an IPython profile to load. "
#             "This can be used to create custom versions of the kernel.",
#         )
#         parser.add_argument(
#             "--prefix",
#             type=str,
#             help="Specify an install prefix for the kernelspec."
#             " This is needed to install into a non-default location, such as a conda/virtual-env.",
#         )
#         parser.add_argument(
#             "--sys-prefix",
#             action="store_const",
#             const=sys.prefix,
#             dest="prefix",
#             help="Install to Python's sys.prefix."
#             " Shorthand for --prefix='%s'. For use in conda/virtual-envs." % sys.prefix,
#         )
#         parser.add_argument(
#             "--env",
#             action="append",
#             nargs=2,
#             metavar=("ENV", "VALUE"),
#             help="Set environment variables for the kernel.",
#         )
#         parser.add_argument(
#             "--frozen_modules",
#             action="store_true",
#             help="Enable frozen modules for potentially faster startup."
#             " This has a downside of preventing the debugger from navigating to certain built-in modules.",
#         )
