# -*- coding: utf-8 -*-
#
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------

# Standard library imports
import logging

# Third-party imports
from envs_manager.api import Manager, ManagerActionResult
from qtpy.QtCore import QObject, Signal

# Spyder and local imports
from spyder.api.config.mixins import SpyderConfigurationObserver
from spyder.api.translations import get_translation
from spyder_env_manager.spyder.api import ManagerRequest
from spyder_env_manager.spyder.config import CONF_SECTION

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

    def __init__(self, parent, request: ManagerRequest):
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
