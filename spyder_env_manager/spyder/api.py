# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------
"""
Spyder Env Manager API.
"""

from __future__ import annotations
from typing import TypedDict

from envs_manager.api import ManagerActions, ManagerOptions


class SpyderEnvManagerActions:

    ToolsMenuAction = "tools_menu_action"


class SpyderEnvManagerWidgetActions:
    # Triggers
    SelectEnvironment = "select_environment"
    NewEnvironment = "new_environment"
    DeleteEnvironment = "delete_environment"
    InstallPackage = "install_package"
    ListPackages = "list_packages"

    # Options menu actions
    ImportEnvironment = "import_environment_action"
    ExportEnvironment = "export_environment_action"
    ToggleExcludeDependency = "exclude_dependency_action"
    ToggleEnvironmentAsCustomInterpreter = "environment_as_custom_interpreter"


class ManagerRequest(TypedDict):
    """
    Dictionary with the necessary parameters to request an action to the manager
    backend.
    """

    manager_options: ManagerOptions
    """Options for envs_manager.Manager"""

    action: ManagerActions
    """Action that the manager will perform."""

    action_options: dict | None
    """Options for the action that will be performed."""
