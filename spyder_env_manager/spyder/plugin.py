# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------
"""
Spyder Env Manager Plugin.
"""

# Third-party imports
from qtpy.QtGui import QIcon

# Spyder imports
from spyder.api.plugins import Plugins, SpyderDockablePlugin
from spyder.api.translations import get_translation

# Local imports
from spyder_env_manager.spyder.confpage import SpyderEnvManagerConfigPage
from spyder_env_manager.spyder.widgets.main_widget import SpyderEnvManagerWidget

_ = get_translation("spyder_env_manager.spyder")


class SpyderEnvManager(SpyderDockablePlugin):
    """
    Spyder Env Manager plugin.
    """

    NAME = "spyder_env_manager"
    REQUIRES = []
    OPTIONAL = []
    WIDGET_CLASS = SpyderEnvManagerWidget
    CONF_SECTION = NAME
    CONF_WIDGET_CLASS = SpyderEnvManagerConfigPage
    TABIFY = [Plugins.Help]

    # --- Signals

    # --- SpyderDockablePlugin API
    # ------------------------------------------------------------------------
    def get_name(self):
        return _("Spyder Env Manager")

    def get_description(self):
        return _("Spyder 5+ plugin to manage Python virtual environments and packages")

    def get_icon(self):
        return QIcon()

    def on_initialize(self):
        widget = self.get_widget()

    def check_compatibility(self):
        valid = True
        message = ""  # Note: Remember to use _("") to localize the string
        return valid, message

    def on_close(self, cancellable=True):
        return True

    # --- Public API
    # ------------------------------------------------------------------------
