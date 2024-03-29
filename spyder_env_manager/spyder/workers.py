# -*- coding: utf-8 -*-
#
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------

# Standard library imports
import logging
import subprocess

# Third-party imports
from qtpy.QtCore import QObject, Signal

# Spyder and local imports
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

    def __init__(
        self, parent, manager, manager_action, *manager_args, **manager_kwargs
    ):
        QObject.__init__(self)
        self._parent = parent
        self.manager = manager
        self.manager_action = manager_action
        self.manager_args = manager_args
        self.manager_kwargs = manager_kwargs
        self.error = None

    def run_manager_action(self):
        """Execute environment manager action and return."""
        logger.info(f"Running manager action: {self.manager_action}")

        manager_action_result = self.manager_action(
            *self.manager_args, **self.manager_kwargs
        )

        logger.debug(f"Manager action result: {manager_action_result}")

        return manager_action_result

    def start(self):
        """Main method of the worker."""
        result = False
        message = error_msg = None
        try:
            result, message = self.run_manager_action()
            if isinstance(message, subprocess.CompletedProcess):
                message = message.stdout
        except Exception as e:
            error_msg = _(
                "Unable to run action over environment: "
                "<br><br> <tt>{exception_string}</tt>"
            ).format(exception_string=str(e))
            logger.exception(error_msg)

        self.error = error_msg
        try:
            self.sig_ready.emit(self.manager, result, message or error_msg)
        except RuntimeError:
            pass
