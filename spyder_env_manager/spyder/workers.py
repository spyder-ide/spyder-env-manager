# -*- coding: utf-8 -*-
#
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------

# Standard library imports
from __future__ import annotations
import typing as t
import logging

# Third-party imports
from envs_manager.api import Manager
from qtpy.QtCore import QObject, Signal

# Spyder and local imports
from spyder.api.config.mixins import SpyderConfigurationObserver
from spyder.api.translations import get_translation
from spyder.api.asyncdispatcher import AsyncDispatcher
from spyder_env_manager.spyder.config import CONF_SECTION
from spyder.plugins.remoteclient.api.modules.base import SpyderBaseJupyterAPI
from spyder.plugins.remoteclient.api.manager.base import SpyderRemoteAPIManagerBase

if t.TYPE_CHECKING:
    from aiohttp import ClientResponse

    from envs_manager.api import ManagerActionResult

    from spyder_env_manager.spyder.api import ManagerRequest
    from spyder_env_manager.spyder.widgets.main_widget import SpyderEnvManagerWidget


# Localization
_ = get_translation("spyder")

# Setup logger
logger = logging.getLogger(__name__)


class EnvironmentManagerWorker(QObject, SpyderConfigurationObserver):
    """
    Worker to run environment manager actions without blocking the Spyder user
    interface.
    """

    CONF_SECTION = CONF_SECTION

    sig_ready = Signal(bool, object, dict)
    """
    Signal to inform that the worker has finished successfully.

    Parameters
    ----------
    result: bool
        True if the action was successful. False otherwise.
    message: object
        Output or message containing handled errors to be shown.
    manager_options: ManagerOptions
        Options of the manager object that is handling the environment.
    """

    def __init__(self, parent: SpyderEnvManagerWidget, request: ManagerRequest):
        QObject.__init__(self)
        self._parent = parent

        manager_options = request["manager_options"]
        manager_options["root_path"] = self.get_conf("environments_path")
        self.manager = Manager(**manager_options)

        self.manager_action = request["action"]
        self.manager_action_options = request.get("action_options")
        self.error = None

    def run_manager_action(self) -> ManagerActionResult:
        """Execute environment manager action and return."""
        logger.info(f"Running manager action: {self.manager_action}")

        manager_action_result = self.manager.run_action(
            self.manager_action, self.manager_action_options
        )

        logger.debug(f"Manager action result: {manager_action_result}")

        return manager_action_result

    def start(self):
        """Main method of the worker."""
        status = False
        output = error_msg = None
        manager_options = {}

        try:
            result = self.run_manager_action()
            status = result["status"]
            output = result["output"]
            manager_options = result["manager_options"]

            # It's simpler to handle strings than bytes
            if isinstance(output, bytes):
                output = output.decode("utf-8")

            # This is necessary because we can't emit a TypedDict in a Qt signal
            manager_options = dict(manager_options)
        except Exception as e:
            error_msg = _(
                "Unable to run action over environment: "
                "<br><br> <tt>{exception_string}</tt>"
            ).format(exception_string=str(e))
            logger.exception(error_msg)

        self.error = error_msg
        try:
            self.sig_ready.emit(status, error_msg or output, manager_options)
        except RuntimeError:
            pass


@SpyderRemoteAPIManagerBase.register_api
class RemoteEnvironmentManagerAPI(SpyderBaseJupyterAPI):
    """
    Remote worker to run environment manager actions without blocking the Spyder
    user interface on a remote server.
    """

    base_url = "envs_manager"

    def __init__(self, *args, **kwargs):
        """
        Initialize the remote environment manager API.

        Parameters
        ----------
        args: tuple
            Positional arguments.
        kwargs: dict
            Keyword arguments.
        """
        super().__init__(*args, **kwargs)
        
        self.error = None

    async def _raise_for_status(self, response: ClientResponse):
        response.raise_for_status()

    async def run_action(
        self, request: ManagerRequest
    ) -> t.Tuple[bool, str, dict]:
        """
        Run an environment manager action on the remote server.

        Parameters
        ----------
        action: str
            The action to run.
        action_options: dict, optional
            Options for the action.

        Returns
        -------
        ManagerActionResult
            Result of the action.
        """

        status = False
        manager_options = {}

        try:
            result = await self.run_manager_action(request)
            status = result["status"]
            output = result["output"]
            manager_options = result["manager_options"]

            # It's simpler to handle strings than bytes
            if isinstance(output, bytes):
                output = output.decode("utf-8")

            # This is necessary because we can't emit a TypedDict in a Qt signal
            manager_options = dict(manager_options)
        except Exception as e:
            error_msg = _(
                "Unable to run action over environment: "
                "<br><br> <tt>{exception_string}</tt>"
            ).format(exception_string=str(e))
            logger.exception(error_msg)
            output = error_msg
            self.error = error_msg

        return status, output, manager_options

    async def run_manager_action(
        self, request: ManagerRequest
    ) -> ManagerActionResult:
        """
        Run an environment manager action on the remote server.

        Parameters
        ----------
        request: ManagerRequest
            Request containing the action and options.

        Returns
        -------
        dict
            Result of the action.
        """
        async with self.session.post(
            self.api_url / request["action"],
            json=request["action_options"],
            params=request["manager_options"]
            ) as response:
            return await response.json()
