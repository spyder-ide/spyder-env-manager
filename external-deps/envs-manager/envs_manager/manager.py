# SPDX-FileCopyrightText: 2022-present Spyder Development Team and envs-manager contributors
#
# SPDX-License-Identifier: MIT

import os
from pathlib import Path

from envs_manager.backends.venv_interface import VEnvInterface
from envs_manager.backends.conda_like_interface import CondaLikeInterface


DEFAULT_BACKENDS_ROOT_PATH = Path(
    os.environ.get(
        "BACKENDS_ROOT_PATH", str(Path.home() / ".envs-manager" / "backends")
    )
)
DEFAULT_BACKEND = os.environ.get("ENV_BACKEND", "venv")
DEFAULT_ENVS_ROOT_PATH = DEFAULT_BACKENDS_ROOT_PATH / DEFAULT_BACKEND / "envs"
EXTERNAL_EXECUTABLE = os.environ.get("ENV_BACKEND_EXECUTABLE", None)


class Manager:
    """
    Class to handle different Python environment and packages managers implementations.
    """

    BACKENDS = {
        VEnvInterface.ID: VEnvInterface,
        CondaLikeInterface.ID: CondaLikeInterface,
    }

    def __init__(
        self,
        backend,
        root_path=None,
        env_name=None,
        env_directory=None,
        external_executable=None,
    ):
        self.backend_class = self.BACKENDS[backend]
        self.env_name = env_name
        self.root_path = root_path

        if env_directory:
            self.env_directory = str(env_directory)
        elif root_path and env_name:
            self.env_directory = root_path / backend / "envs" / env_name
        else:
            raise Exception(
                "'env_directory' or 'root_path' and 'env_name' should be provided"
            )

        self.backend_instance = self.backend_class(
            str(self.env_directory), external_executable=str(external_executable)
        )

    def create_environment(self, packages=None, channels=None, force=False):
        if channels:
            return self.backend_instance.create_environment(
                packages, channels=channels, force=force
            )
        else:
            return self.backend_instance.create_environment(packages, force=force)

    def delete_environment(self, force=False):
        return self.backend_instance.delete_environment(force=force)

    def activate(self):
        self.backend_instance.activate_environment()

    def deactivate(self):
        self.backend_instance.deactivate_environment()

    def export_environment(self, export_file_path=None):
        return self.backend_instance.export_environment(
            export_file_path=export_file_path
        )

    def import_environment(self, import_file_path, force=False):
        return self.backend_instance.import_environment(import_file_path, force=force)

    def install(self, packages=None, channels=None, force=False, capture_output=False):
        if channels:
            return self.backend_instance.install_packages(
                packages=packages,
                channels=channels,
                force=force,
                capture_output=capture_output,
            )
        else:
            return self.backend_instance.install_packages(
                packages, force=force, capture_output=capture_output
            )

    def uninstall(self, packages, force=False, capture_output=False):
        return self.backend_instance.uninstall_packages(
            packages, force=force, capture_output=capture_output
        )

    def update(self, packages, force=False, capture_output=False):
        return self.backend_instance.update_packages(
            packages, force=force, capture_output=capture_output
        )

    def list(self):
        return self.backend_instance.list_packages()

    @classmethod
    def list_environments(
        cls,
        backend=DEFAULT_BACKEND,
        root_path=DEFAULT_BACKENDS_ROOT_PATH,
        external_executable=None,
    ):
        return cls.BACKENDS[backend].list_environments(
            root_path, external_executable=external_executable
        )
