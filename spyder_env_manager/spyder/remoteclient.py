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
import aiohttp

# Spyder and local imports
from spyder.api.translations import get_translation
from spyder.plugins.remoteclient.api.modules.base import (
    SpyderBaseJupyterAPI,
    SpyderRemoteAPIError,
)
from spyder.plugins.remoteclient.api.manager.base import SpyderRemoteAPIManagerBase

if t.TYPE_CHECKING:
    from aiohttp import ClientResponse

    from envs_manager.api import ManagerActionResult

    from spyder_env_manager.spyder.api import ManagerRequest


# Localization
_ = get_translation("spyder")

# Setup logger
logger = logging.getLogger(__name__)


class RemoteEnvManagerApiError(SpyderRemoteAPIError):
    """
    Exception raised when an error occurs in the remote environment manager API.
    """

    def __init__(self, config_id: str, url: str, error_str: str):
        """
        Initialize the RemoteEnvManagerApiError.

        Parameters
        ----------
        config_id: str
            Identifier of the remote server that caused the error.

        error_str: str
            Exception raised by the remote environment manager API.
        """
        self.error_str = error_str
        self.config_id = config_id
        self.url = url

    def __str__(self):
        """
        Return a string representation of the error.

        Returns
        -------
        str
            String representation of the error.
        """
        return _(
            "Unable to run action over environment: "
            "<br><br> <tt>{exception_string}</tt>"
        ).format(exception_string=self.error_str)


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
        if response.status == 501:
            self.error = await response.text()
            raise RemoteEnvManagerApiError(
                self.manager.config_id, str(response.url), self.error
            )

        response.raise_for_status()

    async def run_action(self, request: ManagerRequest) -> t.Tuple[bool, str, dict]:
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
        except RemoteEnvManagerApiError as e:
            logger.exception(
                f"Error on remote server {e.config_id} on {e.url}", exc_info=True
            )
            output = str(e)

        return status, output, manager_options

    async def run_manager_action(
        self, request: ManagerRequest, timout: int = 5 * 60
    ) -> ManagerActionResult:
        """
        Run an environment manager action on the remote server.

        Parameters
        ----------
        request: ManagerRequest
            Request containing the action and options.
        timout: int, optional
            Timeout for the request in seconds. Default is 5 minutes.

        Returns
        -------
        dict
            Result of the action.
        """
        async with self.session.post(
            self.api_url / request["action"].value,
            json=request.get("action_options"),
            params=request.get("manager_options"),
            timeout=aiohttp.ClientTimeout(total=timout),
        ) as response:
            return await response.json()
