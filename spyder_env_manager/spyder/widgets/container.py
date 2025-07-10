# -*- coding: utf-8 -*-
#
# -----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# -----------------------------------------------------------------------------

"""Spyder env manager container."""

# Spyder imports
from spyder.api.widgets.main_container import PluginMainContainer

# Local imports
from spyder_env_manager.spyder.api import SpyderEnvManagerActions
from spyder_env_manager.spyder.widgets.dialog import EnvManagerDialog
from spyder_env_manager.spyder.widgets.manager import SpyderEnvManagerWidget


class SpyderEnvManagerContainer(PluginMainContainer):

    # ---- PluginMainContainer API
    # -------------------------------------------------------------------------
    def setup(self):
        self.envs_manager = SpyderEnvManagerWidget(
            self._plugin.get_name(), self._plugin, parent=self
        )

        # Widgets
        self.create_action(
            SpyderEnvManagerActions.ToolsMenuAction,
            self._plugin.get_name(),
            icon=self._plugin.get_icon(),
            triggered=self._show_envs_dialog,
        )

    def update_actions(self):
        pass

    # ---- Private API
    # -------------------------------------------------------------------------
    def _show_envs_dialog(self):
        dialog = EnvManagerDialog(
            self,
            self.envs_manager,
            title=self._plugin.get_name(),
            icon=self._plugin.get_icon(),
        )
        dialog.show()
