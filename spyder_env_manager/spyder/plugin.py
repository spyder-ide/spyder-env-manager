# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------
"""
Spyder Env Manager Plugin.
"""

# Standard library imports
from pathlib import Path

# Third-party imports
import qtawesome as qta

# Spyder imports
from spyder.api.plugins import Plugins, SpyderDockablePlugin
from spyder.api.translations import get_translation
from spyder.api.plugin_registration.decorators import on_plugin_available
from spyder.utils.icon_manager import ima

# Local imports
from spyder_env_manager.spyder.config import CONF_DEFAULTS, CONF_SECTION, CONF_VERSION
from spyder_env_manager.spyder.confpage import SpyderEnvManagerConfigPage
from spyder_env_manager.spyder.widgets.main_widget import SpyderEnvManagerWidget

_ = get_translation("spyder_env_manager.spyder")


class SpyderEnvManager(SpyderDockablePlugin):
    """
    Spyder Env Manager plugin.
    """

    NAME = CONF_SECTION
    REQUIRES = [Plugins.Preferences]
    OPTIONAL = []
    WIDGET_CLASS = SpyderEnvManagerWidget
    CONF_SECTION = CONF_SECTION
    CONF_DEFAULTS = CONF_DEFAULTS
    CONF_VERSION = CONF_VERSION
    CONF_WIDGET_CLASS = SpyderEnvManagerConfigPage
    TABIFY = [Plugins.Help]
    CONF_FILE = True

    # --- Signals

    # --- SpyderDockablePlugin API
    # ------------------------------------------------------------------------
    @staticmethod
    def get_name():
        return _("Environments Manager")

    def get_description(self):
        return _("Spyder 5+ plugin to manage Python virtual environments and packages")

    def get_icon(self):
        return qta.icon("mdi.archive", color=ima.MAIN_FG_COLOR)

    def on_initialize(self):
        widget = self.get_widget()

    @on_plugin_available(plugin=Plugins.Preferences)
    def on_preferences_available(self):
        preferences = self.get_plugin(Plugins.Preferences)
        preferences.register_plugin_preferences(self)

    def check_compatibility(self):
        message = _("")
        conda_like_executable_path = self.get_conf("conda_file_executable_path")
        valid = conda_like_executable_path and Path(conda_like_executable_path).exists()
        if not valid:
            message = _("Unable to find conda-like executable!")
        return valid, message

    def on_close(self, cancellable=True):
        return True

    def update_font(self):
        """Update font from Preferences"""
        rich_font = self.get_font(rich_text=True)
        self.get_widget().update_font(rich_font)

    # --- Public API
    # ------------------------------------------------------------------------
