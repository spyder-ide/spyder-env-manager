# SPDX-FileCopyrightText: 2022-present Spyder Development Team and envs-manager contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations
import json
import typing as t

from traitlets import Unicode
from tornado import web
from jupyter_server.auth.decorator import authorized
from jupyter_server.extension.application import ExtensionApp
from jupyter_server.base.handlers import JupyterHandler

from envs_manager.manager import (
    DEFAULT_BACKENDS_ROOT_PATH,
    DEFAULT_BACKEND,
    Manager,
    ManagerActions,
)


class EnvManagerHandler(JupyterHandler):
    """Handler to list available environments."""

    _handler_action_regex = (
        rf"(?P<action>{'|'.join(action.value for action in ManagerActions)})"
    )

    auth_resource = "envs_manager"

    def get_manager(self) -> Manager:
        """Get the environment manager instance."""
        return Manager(
            backend=self.get_argument("backend", None)
            or self.settings["envs_manager_config"]["default_backend"],
            root_path=self.settings["envs_manager_config"]["root_path"],
            env_name=self.get_argument("env_name", None),
            env_directory=self.get_argument("env_directory", None),
        )

    def get_options(self) -> dict[str, t.Any]:
        return self.get_json_body() or {}

    def write_json(self, data, status=200):
        self.set_status(status)
        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps(data))

    @authorized
    @web.authenticated
    def post(self, action: str):
        try:
            manager = self.get_manager()
            action_options = self.get_options()
            self.write_json(
                manager.run_action(ManagerActions(action), action_options),
                status=200,
            )
        except Exception as e:
            self.set_status(501)
            self.finish(str(e))
            self.log_exception(type(e), e, e.__traceback__)


class EnvManagerApp(ExtensionApp):
    """Jupyter extension for managing environments."""

    name = "envs_manager"
    extension_url = "/envs_manager"
    open_browser = False

    root_path = Unicode(
        str(DEFAULT_BACKENDS_ROOT_PATH),
        config=True,
        help="Root path for the extension. Defaults to the Jupyter server root path.",
    )

    default_backend = Unicode(
        DEFAULT_BACKEND,
        config=True,
        help="Default backend to use for managing environments.",
    )

    handlers = [
        (
            rf"{extension_url}/{EnvManagerHandler._handler_action_regex}",
            EnvManagerHandler,
        ),
    ]  # type: ignore[list-item]
