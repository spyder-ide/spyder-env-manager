# SPDX-FileCopyrightText: 2022-present Spyder Development Team and envs-manager contributors
#
# SPDX-License-Identifier: MIT

import subprocess

import requests

PYPI_API_PACKAGE_INFO_URL = "https://pypi.org/pypi/{package_name}/json"
ANACONDA_API_PACKAGE_INFO = "https://api.anaconda.org/package/{channel}/{package_name}"


def run_command(command, capture_output=True, run_env=None):
    """
    Run commands using `subprocess.run`

    Parameters
    ----------
    command : list[str]
        List of string arguments that conform the command to be executed.
    capture_output : bool, optional
        If the output (stdout and stderr) of the command should be stored. The default is True.
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
        )
    else:
        result = subprocess.run(
            command, stderr=subprocess.PIPE, check=True, text=True, env=run_env
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


class EnvManagerInstance:
    ID = ""

    def __init__(self, environment_path, external_executable=None):
        self.environment_path = environment_path
        self.external_executable = external_executable
        self.executable_variant = None
        assert self.validate(), f"{self.ID} backend unavailable!"

    @property
    def python_executable_path(self):
        raise NotImplementedError()

    def validate(self):
        pass

    def create_environment(self, packages=None, channels=None, force=False):
        raise NotImplementedError()

    def delete_environment(self, force=False):
        raise NotImplementedError()

    def activate_environment(self):
        raise NotImplementedError()

    def deactivate_environment(self):
        raise NotImplementedError()

    def export_environment(self, export_file_path=None):
        raise NotImplementedError()

    def import_environment(self, import_file_path, force=False):
        raise NotImplementedError()

    def install_packages(
        self,
        packages,
        channels=None,
        force=False,
        capture_output=False,
    ):
        raise NotImplementedError()

    def uninstall_packages(self, packages, force=False, capture_output=False):
        raise NotImplementedError()

    def update_packages(self, packages, force=False, capture_output=False):
        raise NotImplementedError()

    def list_packages(self):
        raise NotImplementedError()

    @classmethod
    def list_environments(cls, root_path, external_executable=None):
        raise NotImplementedError()
