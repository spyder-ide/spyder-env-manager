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
import base64
from functools import cached_property
import qtawesome as qta
from qtpy.QtCore import Signal

# Spyder imports
from spyder.api.plugin_registration.decorators import (
    on_plugin_available,
    on_plugin_teardown,
)
from spyder.api.plugins import Plugins, SpyderPluginV2
from spyder.api.translations import get_translation
from spyder.plugins.mainmenu.api import ApplicationMenus, ToolsMenuSections
from spyder.utils.icon_manager import ima

# Local imports
from spyder_env_manager.spyder.api import (
    SpyderEnvManagerActions,
    SpyderEnvManagerWidgetActions,
)
from spyder_env_manager.spyder.config import CONF_DEFAULTS, CONF_SECTION, CONF_VERSION
from spyder_env_manager.spyder.confpage import SpyderEnvManagerConfigPage
from spyder_env_manager.spyder.widgets.container import SpyderEnvManagerContainer

_ = get_translation("spyder_env_manager.spyder")


class SpyderEnvManager(SpyderPluginV2):
    """
    Spyder Env Manager plugin.
    """

    # --- Constants
    NAME = CONF_SECTION
    REQUIRES = [Plugins.MainInterpreter, Plugins.Preferences, Plugins.MainMenu]
    OPTIONAL = [Plugins.RemoteClient]
    CONTAINER_CLASS = SpyderEnvManagerContainer
    CONF_SECTION = CONF_SECTION
    CONF_DEFAULTS = CONF_DEFAULTS
    CONF_VERSION = CONF_VERSION
    CONF_WIDGET_CLASS = SpyderEnvManagerConfigPage
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

    sig_set_default_kernel_spec_requested = Signal(str, str)
    """
    Signal to request updating the default kernel spec in a remote machine.

    Parameters
    ----------
    name: str
        Kernelspec name.
    server_id:
        Server identifier.
    """

    # --- SpyderDockablePlugin API
    # ------------------------------------------------------------------------
    @staticmethod
    def get_name():
        return _("Environment manager")

    @staticmethod
    def get_description():
        return _("Spyder 6+ plugin to manage Python virtual environments and packages")

    @staticmethod
    def get_icon():
        return qta.icon("mdi.archive", color=ima.MAIN_FG_COLOR)

    def on_initialize(self):
        container = self.get_container()
        container.envs_manager.sig_set_spyder_custom_interpreter.connect(
            self.sig_set_spyder_custom_interpreter
        )
        container.envs_manager.sig_set_default_kernel_spec_requested.connect(
            self.sig_set_default_kernel_spec_requested
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

    @on_plugin_available(plugin=Plugins.RemoteClient)
    def on_remoteclient_available(self):
        self._remote_client.sig_import_env_requested.connect(self.import_remote_env)

    @cached_property
    def _remote_client(self):
        return self.get_plugin(Plugins.RemoteClient)

    @on_plugin_available(plugin=Plugins.MainMenu)
    def on_mainmenu_available(self):
        mainmenu = self.get_plugin(Plugins.MainMenu)

        action = self.get_action(SpyderEnvManagerActions.ToolsMenuAction)
        mainmenu.add_item_to_application_menu(
            action,
            menu_id=ApplicationMenus.Tools,
            section=ToolsMenuSections.Managers,
        )

    @on_plugin_teardown(plugin=Plugins.MainMenu)
    def on_mainmenu_teardown(self):
        mainmenu = self.get_plugin(Plugins.MainMenu)

        mainmenu.remove_item_from_application_menu(
            SpyderEnvManagerActions.ToolsMenuAction,
            menu_id=ApplicationMenus.Tools,
        )

    @on_plugin_teardown(plugin=Plugins.RemoteClient)
    def on_remoteclient_teardown(self):
        self._remote_client.sig_import_env_requested.disconnect(self.import_remote_env)

    def on_close(self, cancellable=True):
        return True

    # --- Public API
    # ------------------------------------------------------------------------
    def import_remote_env(self, server_id: str, import_file_path: str, env_name: str):
        # Get binary file contents
        with open(import_file_path, "rb") as file:
            import_file_contents = file.read()

        # Json can't serialize bytes, so we need to send a base64 encoded string
        encoded_string = base64.b64encode(import_file_contents).decode("utf-8")

        # Send request
        container = self.get_container()
        container.envs_manager._run_action_for_env(
            action=SpyderEnvManagerWidgetActions.ImportEnvironment,
            import_file_path=encoded_string,
            env_name=env_name,
            server_id=server_id,
        )
