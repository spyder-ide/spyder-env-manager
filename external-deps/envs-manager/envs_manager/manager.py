# SPDX-FileCopyrightText: 2022-present Spyder Development Team and envs-manager contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations
import os
from pathlib import Path
from typing import TypedDict, Literal

from envs_manager.backends.api import BackendActionResult, BackendInstance
from envs_manager.backends.venv_interface import VEnvInterface
from envs_manager.backends.conda_like_interface import CondaLikeInterface
from envs_manager.backends.pixi_interface import PixiInterface


DEFAULT_BACKENDS_ROOT_PATH = Path(
    os.environ.get(
        "BACKENDS_ROOT_PATH", str(Path.home() / ".envs-manager" / "backends")
    )
)
DEFAULT_BACKEND = os.environ.get("ENV_BACKEND", "venv")
DEFAULT_ENVS_ROOT_PATH = DEFAULT_BACKENDS_ROOT_PATH / DEFAULT_BACKEND / "envs"


ManagerActions = Literal[
    "create_environment",
    "delete_environment",
    "activate",
    "deactivate",
    "export_environment",
    "import_environment",
    "install",
    "uninstall",
    "update",
    "list",
    "list_environments",
]
"""Enum with the possible actions that can be performed by the manager."""


class ManagerOptions(TypedDict):
    """Options to create an instance of the manager class."""

    backend: str
    """Backend the manager will use."""

    root_path: str | None
    """
    Root path where the manager actions will be performed (e.g. where environments
    will be created).
    """

    env_name: str | None
    """Name of the environment to which the action will be performed."""

    env_directory: str | None
    """Path to the environment's directory."""


class ManagerActionResult(BackendActionResult):
    """Dictionary to report the result of a manager's action."""

    manager_options: ManagerOptions
    """Options that were used to create the manager."""


class Manager:
    """
    Class to handle different Python environment and package manager implementations.
    """

    BACKENDS = {
        VEnvInterface.ID: VEnvInterface,
        CondaLikeInterface.ID: CondaLikeInterface,
        PixiInterface.ID: PixiInterface,
    }

    def __init__(
        self,
        backend: str,
        root_path: str | Path | None = None,
        env_name: str | None = None,
        env_directory: str | Path | None = None,
    ):
        self.backend_class = self.BACKENDS[backend]
        self.env_name = env_name
        self.root_path = DEFAULT_BACKENDS_ROOT_PATH if root_path is None else root_path

        # This where the backend executable will be saved
        bin_directory = Path(self.root_path) / backend / "bin"
        if not bin_directory.exists():
            bin_directory.mkdir(parents=True)

        # This is where the environments for the given backend will be saved
        backend_envs_directory = Path(self.root_path) / backend / "envs"
        if not backend_envs_directory.exists():
            backend_envs_directory.mkdir()

        if env_directory:
            self.env_directory = Path(env_directory)
        elif root_path and env_name:
            self.env_directory = backend_envs_directory / env_name
        else:
            # This can happen when we want to get the list of environments
            self.env_directory = ""

        self.backend_instance: BackendInstance = self.backend_class(
            str(self.env_directory),
            str(backend_envs_directory),
            str(bin_directory),
        )

        self._manager_options = ManagerOptions(
            backend=backend,
            root_path=str(root_path),
            env_name=env_name,
            env_directory=str(self.env_directory),
        )

    def run_action(self, action: ManagerActions, action_options: dict | None = None):
        method = getattr(self, action)
        if action_options is not None:
            return method(**action_options)
        else:
            return method()

    def create_environment(
        self,
        packages: list[str] | None = None,
        channels: list[str] | None = None,
        force: bool = False,
    ) -> ManagerActionResult:
        if channels:
            backend_result = self.backend_instance.create_environment(
                packages, channels=channels, force=force
            )
        else:
            backend_result = self.backend_instance.create_environment(
                packages, force=force
            )

        return self._backend_to_manager_result(backend_result)

    def delete_environment(self, force: bool = False) -> ManagerActionResult:
        backend_result = self.backend_instance.delete_environment(force=force)
        return self._backend_to_manager_result(backend_result)

    def activate(self):
        self.backend_instance.activate_environment()

    def deactivate(self):
        self.backend_instance.deactivate_environment()

    def export_environment(
        self, export_file_path: str | None = None
    ) -> ManagerActionResult:
        backend_result = self.backend_instance.export_environment(
            export_file_path=export_file_path
        )
        return self._backend_to_manager_result(backend_result)

    def import_environment(
        self, import_file_path: str, force: bool = False
    ) -> ManagerActionResult:
        backend_result = self.backend_instance.import_environment(
            import_file_path, force=force
        )
        return self._backend_to_manager_result(backend_result)

    def install(
        self,
        packages: list[str] | None = None,
        channels: list[str] | None = None,
        force: bool = False,
        capture_output: bool = False,
    ) -> ManagerActionResult:
        if channels:
            backend_result = self.backend_instance.install_packages(
                packages=packages,
                channels=channels,
                force=force,
                capture_output=capture_output,
            )
        else:
            backend_result = self.backend_instance.install_packages(
                packages, force=force, capture_output=capture_output
            )

        return self._backend_to_manager_result(backend_result)

    def uninstall(
        self, packages: list[str], force: bool = False, capture_output: bool = False
    ) -> ManagerActionResult:
        backend_result = self.backend_instance.uninstall_packages(
            packages, force=force, capture_output=capture_output
        )
        return self._backend_to_manager_result(backend_result)

    def update(
        self, packages: list[str], force: bool = False, capture_output: bool = False
    ) -> ManagerActionResult:
        backend_result = self.backend_instance.update_packages(
            packages, force=force, capture_output=capture_output
        )
        return self._backend_to_manager_result(backend_result)

    def list(self) -> ManagerActionResult:
        backend_result = self.backend_instance.list_packages()
        return self._backend_to_manager_result(backend_result)

    def list_environments(self) -> ManagerActionResult:
        backend_result = self.backend_instance.list_environments()
        return self._backend_to_manager_result(backend_result)

    def _backend_to_manager_result(
        self,
        backend_result: BackendActionResult,
    ) -> ManagerActionResult:
        return ManagerActionResult(
            status=backend_result["status"],
            output=backend_result["output"],
            manager_options=self._manager_options,
        )
