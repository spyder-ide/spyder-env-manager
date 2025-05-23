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
from spyder_env_manager.spyder.api import ManagerRequest
from spyder.api.translations import get_translation

# Localization
_ = get_translation("spyder")

# Setup logger
logger = logging.getLogger(__name__)


class EnvironmentManagerWorker(QObject):
    """
    Worker to run environment manager actions over environments
    without blocking the Spyder user interface.
    """

    sig_ready = Signal(object, bool, object)
    """
    Signal to inform that the worker has finished successfully.

    Parameters
    ----------
    manager: object
        Manager object instance handling the environment
    result: bool
        True if the action was successful. False otherwise.
    message: object
        Subprocess result or string message containing handled errors to be shown.
    """

    def __init__(self, parent, request: ManagerRequest):
        QObject.__init__(self)
        self._parent = parent
        self.manager = Manager(**request["manager_options"])
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
        try:
            result = self.run_manager_action()
            print(result)
            #foo
            status = result["status"]
            output = result["output"]
        except Exception as e:
            error_msg = _(
                "Unable to run action over environment: "
                "<br><br> <tt>{exception_string}</tt>"
            ).format(exception_string=str(e))
            logger.exception(error_msg)

        self.error = error_msg
        print(error_msg)
        try:
            self.sig_ready.emit(self.manager, status, output or error_msg)
        except RuntimeError:
            pass
