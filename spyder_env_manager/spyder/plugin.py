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
from functools import cached_property
import qtawesome as qta
from qtpy.QtCore import Signal

# Spyder imports
from spyder.api.fonts import SpyderFontType
from spyder.api.plugin_registration.decorators import (
    on_plugin_available,
    on_plugin_teardown,
)
from spyder.api.plugins import Plugins, SpyderDockablePlugin
from spyder.api.translations import get_translation
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

    # --- Constants
    NAME = CONF_SECTION
    REQUIRES = [Plugins.MainInterpreter, Plugins.Preferences]
    OPTIONAL = [Plugins.RemoteClient]
    WIDGET_CLASS = SpyderEnvManagerWidget
    CONF_SECTION = CONF_SECTION
    CONF_DEFAULTS = CONF_DEFAULTS
    CONF_VERSION = CONF_VERSION
    CONF_WIDGET_CLASS = SpyderEnvManagerConfigPage
    TABIFY = [Plugins.Help]
    CONF_FILE = True

    # --- Signals
    sig_set_spyder_custom_interpreter = Signal(str)
    """
    Signal to inform that the user wants to set the Python interpreter of an
    environment as the Spyder custom interpreter.

    Parameters
    ----------
    environment_python_path: str
        Path to the environment Python interpreter.
    """

    # --- SpyderDockablePlugin API
    # ------------------------------------------------------------------------
    @staticmethod
    def get_name():
        return _("Environments Manager")

    @staticmethod
    def get_description():
        return _("Spyder 6+ plugin to manage Python virtual environments and packages")

    @staticmethod
    def get_icon():
        return qta.icon("mdi.archive", color=ima.MAIN_FG_COLOR)

    def on_initialize(self):
        main_widget = self.get_widget()
        main_widget.sig_set_spyder_custom_interpreter.connect(
            self.sig_set_spyder_custom_interpreter
        )

    @on_plugin_available(plugin=Plugins.Preferences)
    def on_preferences_available(self):
        preferences = self.get_plugin(Plugins.Preferences)
        preferences.register_plugin_preferences(self)

    @on_plugin_available(plugin=Plugins.MainInterpreter)
    def on_maininterpreter_available(self):
        main_interpreter = self.get_plugin(Plugins.MainInterpreter)
        self.sig_set_spyder_custom_interpreter.connect(
            main_interpreter.set_custom_interpreter
        )

    @on_plugin_teardown(plugin=Plugins.Preferences)
    def on_preferences_teardown(self):
        # Deregister conf page
        preferences = self.get_plugin(Plugins.Preferences)
        preferences.deregister_plugin_preferences(self)

    @on_plugin_teardown(plugin=Plugins.MainInterpreter)
    def on_maininterpreter_teardown(self):
        self.sig_set_spyder_custom_interpreter.disconnect()

    # @on_plugin_available(plugin=Plugins.RemoteClient)
    # def on_remoteclient_available(self):
    #     """
    #     Connect to the Remote Client plugin to update the main widget when
    #     the remote client is connected or disconnected.
    #     """

    @cached_property
    def _remote_client(self):
        return self.get_plugin(Plugins.RemoteClient)

    def on_close(self, cancellable=True):
        return True

    def update_font(self):
        """Update font from Preferences"""
        rich_font = self.get_font(font_type=SpyderFontType.Interface)
        self.get_widget().update_font(rich_font)

    # --- Public API
    # ------------------------------------------------------------------------
