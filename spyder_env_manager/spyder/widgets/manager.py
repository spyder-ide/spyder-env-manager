# -*- coding: utf-8 -*-
#
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------

"""
Environment manager widget.
"""

# Standard library imports
from __future__ import annotations
from collections.abc import Callable
import os

# Third party imports
from envs_manager.api import ManagerActions, ManagerOptions
from envs_manager.backends.pixi_interface import PixiInterface
from envs_manager.manager import Manager
from packaging.version import parse
import qstylizer.style
from qtpy.compat import getsavefilename
from qtpy.QtCore import QThread, Signal
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QMessageBox,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
)

# Spyder imports
from spyder import __version__ as spyder_version
from spyder.api.translations import get_translation
from spyder.api.widgets.main_widget import (
    PluginMainWidget,
    PluginMainWidgetActions,
)
from spyder.dependencies import SPYDER_KERNELS_REQVER
from spyder.utils.icon_manager import ima
from spyder.utils.misc import getcwd_or_home
from spyder.utils.palette import SpyderPalette

# Local imports
from spyder_env_manager.spyder.api import ManagerRequest, SpyderEnvManagerWidgetActions
from spyder_env_manager.spyder.workers import EnvironmentManagerWorker
from spyder_env_manager.spyder.widgets.helper_widgets import (
    CustomParametersDialog,
    CustomParametersDialogWidgets,
)
from spyder_env_manager.spyder.widgets.edit_environment import EditEnvironment
from spyder_env_manager.spyder.widgets.list_environments import ListEnvironments
from spyder_env_manager.spyder.widgets.new_environment import NewEnvironment
from spyder_env_manager.spyder.widgets.packages_table import (
    EnvironmentPackagesActions,
)

# Localization
_ = get_translation("spyder")


# =============================================================================
# ---- Constants
# =============================================================================
SPYDER_KERNELS_VERSION = SPYDER_KERNELS_REQVER.split(";")[0]


class SpyderEnvManagerWidgetOptionsMenuSections:
    ImportExport = "import_export_section"
    AdvancedOptions = "advanced_options"


class SpyderEnvManagerWidgetMainToolBarSections:
    Main = "main_section"


class AvailableManagerWidgets:
    NewEnvWidget = "new_env"
    ListEnvsWidget = "list_envs"
    EditEnvWidget = "edit_env"
    ImportEnvWidget = "import_env"


class EditEnvActions:
    CreateEnv = "create_env"
    EditEnv = "edit_env"
    NoAction = "no_action"


# =============================================================================
# ---- Widgets
# =============================================================================
class SpyderEnvManagerWidget(PluginMainWidget):

    CONF_SECTION = "spyder_env_manager"  # FIXME

    # --- PluginMainWidget class constants
    ENABLE_SPINNER = True
    NO_ENVIRONMENTS_AVAILABLE = _("No environments available")

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

    sig_widget_is_shown = Signal(str, str)
    """
    Signal used to inform that one of the available stacked widgets is shown.

    Parameters
    ----------
    widget: AvailableManagerWidgets
        Widget that's shown at the moment.
    edit_action: EditEnvActions
        Action that edit_env_widget will perform.
    """

    def __init__(self, name, plugin, parent=None):
        super().__init__(name, plugin, parent=parent)

        # Since this is not part of dockable plugin, we don't need these margins
        self._margin_left = self._margin_right = self._margin_bottom = 0

        # Set min size
        self.setMinimumWidth(640)
        self.setMinimumHeight(480)

        # General attributes
        self.actions_enabled = True
        self.exclude_non_requested_packages = True
        self.env_manager_action_thread = QThread(None)
        self.manager_worker = None

        # Select environment widget
        self.select_environment = QComboBox(self)
        self.select_environment.ID = SpyderEnvManagerWidgetActions.SelectEnvironment

        self.select_environment.setToolTip("Select an environment")
        self.select_environment.setSizeAdjustPolicy(
            QComboBox.AdjustToMinimumContentsLength
        )
        self.select_environment.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        selected_environment = self.get_conf("selected_environment")
        if selected_environment:
            self.select_environment.setCurrentText(selected_environment)

        # Env widgets
        self.new_env_widget = NewEnvironment(self)
        self.edit_env_widget = EditEnvironment(self)
        self.list_envs_widget = ListEnvironments(self)
        self.import_env_widget = NewEnvironment(self, import_env=True)

        # Signals
        self.list_envs_widget.sig_edit_env_requested.connect(
            self.current_environment_changed
        )
        self.list_envs_widget.sig_delete_env_requested.connect(
            self._message_delete_environment
        )
        self.list_envs_widget.sig_export_env_requested.connect(self._export_environment)

        # Stackedwidget and layout
        self.stack_widget = QStackedWidget(self)
        self.stack_widget.addWidget(self.new_env_widget)
        self.stack_widget.addWidget(self.edit_env_widget)
        self.stack_widget.addWidget(self.list_envs_widget)
        self.stack_widget.addWidget(self.import_env_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack_widget)
        self.setLayout(layout)

        # Request the list of environments to populate the widget
        self._envs_listed = False
        self._list_environments()

        # We need to make these calls manually because the widget is not associated to
        # a plugin
        self._setup()
        self.setup()
        self.render_toolbars()

        self.setStyleSheet(self._stylesheet)

    # ---- PluginMainWidget API
    # ------------------------------------------------------------------------
    def get_title(self):
        return _("Spyder Env Manager")

    def setup(self):
        # ---- Options menu actions
        import_environment_action = self.create_action(
            SpyderEnvManagerWidgetActions.ImportEnvironment,
            text=_("Import environment from file (.zip)"),
            icon=self.create_icon("fileimport"),
            triggered=self.show_import_env_widget,
        )

        exclude_dependency_action = self.create_action(
            SpyderEnvManagerWidgetActions.ToggleExcludeDependency,
            text=_("Exclude dependency packages"),
            tip=_("Exclude dependency packages"),
            toggled=True,
            triggered=self.update_packages,
            option=SpyderEnvManagerWidgetActions.ToggleExcludeDependency,
            initial=self.get_conf(
                SpyderEnvManagerWidgetActions.ToggleExcludeDependency,
            ),
        )

        environment_as_custom_interpreter_action = self.create_action(
            SpyderEnvManagerWidgetActions.ToggleEnvironmentAsCustomInterpreter,
            text=_("Set current environment as Spyder's Python interpreter"),
            tip=_(
                "Set the current environment Python interpreter as "
                "the interpreter used by Spyder"
            ),
            toggled=True,
            triggered=lambda: self._environment_as_custom_interpreter(),
            option=SpyderEnvManagerWidgetActions.ToggleEnvironmentAsCustomInterpreter,
            initial=self.get_conf(
                SpyderEnvManagerWidgetActions.ToggleEnvironmentAsCustomInterpreter,
            ),
        )

        # ---- Toolbar actions
        new_environment_action = self.create_action(
            SpyderEnvManagerWidgetActions.NewEnvironment,
            text=_("New environment"),
            icon=ima.icon("edit_add"),
            triggered=self.show_new_env_widget,
        )

        # Options menu
        options_menu = self.get_options_menu()
        for item in [
            exclude_dependency_action,
            environment_as_custom_interpreter_action,
        ]:
            self.add_item_to_menu(
                item,
                menu=options_menu,
                section=SpyderEnvManagerWidgetOptionsMenuSections.AdvancedOptions,
            )

        # Main toolbar
        main_toolbar = self.get_main_toolbar()

        for item in [
            self.select_environment,
            new_environment_action,
            import_environment_action,
        ]:
            self.add_item_to_toolbar(
                item,
                toolbar=main_toolbar,
                section=SpyderEnvManagerWidgetMainToolBarSections.Main,
            )

        self.current_environment_changed()

    def current_environment_changed(
        self, environment_name: str | None = None, environment_path: str | None = None
    ):
        """
        Handle changing environment or changes inside the current environment.

        Either the current environment being displayed is different or
        the packages inside the current environment have changed.

        Parameters
        ----------
        index : int, optional
            Index of the current environment selected. The default is None.
        """
        environments_available = environment_path is not None
        if environments_available:
            self.start_spinner()
            self._run_action_for_env(
                action=SpyderEnvManagerWidgetActions.ListPackages,
                env_name=environment_name,
                env_directory=environment_path,
            )
            self.show_edit_env_widget(action=EditEnvActions.EditEnv)
            if self.get_conf(
                SpyderEnvManagerWidgetActions.ToggleEnvironmentAsCustomInterpreter,
            ):
                self._environment_as_custom_interpreter(
                    environment_path=environment_path
                )
        else:
            self.show_new_env_widget()
            self.stop_spinner()

    def update_actions(self):
        if self.actions_enabled:
            current_environment_path = self.select_environment.currentData()
            environments_available = current_environment_path is not None
            actions_ids = [
                SpyderEnvManagerWidgetActions.InstallPackage,
                SpyderEnvManagerWidgetActions.DeleteEnvironment,
                SpyderEnvManagerWidgetActions.ToggleExcludeDependency,
                SpyderEnvManagerWidgetActions.ToggleEnvironmentAsCustomInterpreter,
            ]
            for action_id, action in self.get_actions().items():
                if action_id in actions_ids:
                    action.setEnabled(environments_available)
                else:
                    action.setEnabled(True)

    def update_packages(
        self, only_requested, packages=None, env_name=None, env_directory=None
    ):
        self.exclude_non_requested_packages = only_requested
        self.edit_env_widget.load_env_packages(
            packages, env_name, env_directory, only_requested
        )
        self.stop_spinner()

    def start_spinner(self):
        self.actions_enabled = False
        for action_id, action in self.get_actions().items():
            if action_id not in PluginMainWidgetActions.__dict__.values():
                action.setEnabled(False)
        self.select_environment.setDisabled(True)
        super().start_spinner()

    def stop_spinner(self):
        self.actions_enabled = True
        self.update_actions()
        self.select_environment.setDisabled(False)
        super().stop_spinner()

    def on_close(self):
        env_name = self.select_environment.currentText()
        self.set_conf("selected_environment", env_name)
        if (
            self.env_manager_action_thread
            and self.env_manager_action_thread.isRunning()
        ):
            self.env_manager_action_thread.terminate()
            self.env_manager_action_thread.wait()

    # ---- Public API
    # ------------------------------------------------------------------------
    def show_new_env_widget(self):
        self.stack_widget.setCurrentWidget(self.new_env_widget)
        self.sig_widget_is_shown.emit(
            AvailableManagerWidgets.NewEnvWidget, EditEnvActions.NoAction
        )

    def show_edit_env_widget(self, action: EditEnvActions):
        self.stack_widget.setCurrentWidget(self.edit_env_widget)
        self.sig_widget_is_shown.emit(AvailableManagerWidgets.EditEnvWidget, action)

    def show_list_envs_widget(self):
        self.stack_widget.setCurrentWidget(self.list_envs_widget)
        self.sig_widget_is_shown.emit(
            AvailableManagerWidgets.ListEnvsWidget, EditEnvActions.NoAction
        )

    def show_import_env_widget(self):
        self.stack_widget.setCurrentWidget(self.import_env_widget)
        self.sig_widget_is_shown.emit(
            AvailableManagerWidgets.ImportEnvWidget, EditEnvActions.NoAction
        )

    # ---- Private API
    # ------------------------------------------------------------------------
    def _list_environments(self):
        request = ManagerRequest(
            manager_options=ManagerOptions(
                backend=PixiInterface.ID,
            ),
            action=ManagerActions.ListEnvironments,
        )

        self._run_env_manager_action(request, self._after_list_environments)

    def _handle_package_table_context_menu_actions(self, action, package_info):
        """
        Handle context menu actions defined in the packages table widget.

        The possible actions to choose affect a specific package.

        Parameters
        ----------
        action : str
            The Python environment action to be done.
            The action should defined on the `EnvironmentPackagesActions` enum class.
        package_info : dict
            Dictionary with the information of the package that will be modified
            by the action.

        Returns
        -------
        None.

        """
        package_name = package_info["name"]
        if action == EnvironmentPackagesActions.UpdatePackage:
            title = _("Update package")
            messages = _(
                "Are you sure you want to update <tt>{package_name}</tt>?"
            ).format(package_name=package_name)
            self._message_box(
                title,
                messages,
                action=EnvironmentPackagesActions.UpdatePackage,
                package_info=package_info,
            )
        elif action == EnvironmentPackagesActions.UninstallPackage:
            title = _("Uninstall package")
            messages = _(
                "Are you sure you want to uninstall <tt>{package_name}</tt>?"
            ).format(package_name=package_name)
            self._message_box(
                title,
                messages,
                action=EnvironmentPackagesActions.UninstallPackage,
                package_info=package_info,
            )
        elif action == EnvironmentPackagesActions.InstallPackageVersion:
            title = _("Change package version constraint")
            messages = ["Package", "Constraint", "Version"]
            types = [
                CustomParametersDialogWidgets.Label,
                CustomParametersDialogWidgets.ComboBox,
                CustomParametersDialogWidgets.LineEditVersion,
            ]
            contents = [
                [package_info["name"]],
                ["==", "<=", ">=", "<", ">", "latest"],
                {},
            ]
            self._message_box_editable(
                title,
                messages,
                contents,
                types,
                action=EnvironmentPackagesActions.InstallPackageVersion,
                package_info=package_info,
            )

    def _environment_as_custom_interpreter(self, environment_path: str | None = None):
        """
        Request a given environment or the Python interpreter of the current one to be
        set as Spyder's Python interpreter.

        Parameters
        ----------
        environment_path : str
            Path to the environment directory.

        Notes
        -----
        * This can be done only for local environments.
        """
        if not self.get_conf(
            SpyderEnvManagerWidgetActions.ToggleEnvironmentAsCustomInterpreter
        ):
            return
        if not environment_path:
            environment_path = self.select_environment.currentData()
        if not environment_path:
            return

        backend = PixiInterface.ID
        manager = Manager(
            backend,
            env_directory=environment_path,
        )

        self.sig_set_spyder_custom_interpreter.emit(
            manager.backend_instance.python_executable_path
        )

    def _add_new_environment_entry(
        self, action_result: bool, result_message: str, manager_options: ManagerOptions
    ):
        """
        Handle the addition of a new Python environment to the GUI.

        Add an entry into the `selected_environment` combobox and update the
        the `selected_environment` config option.

        Parameters
        ----------
        action_result : bool
            True if the environment creation was successful. False otherwise.
        result_message : str
            Resulting error or failure message in case `action_result` is False.
        manager_options : ManagerOptions
            Options used to create the manager.
        """
        if action_result:
            env_name = manager_options["env_name"]
            env_directory = manager_options["env_directory"]

            self.current_environment_changed(env_name, env_directory)
            self.list_envs_widget.add_environment(env_name, env_directory)
            self.set_conf("selected_environment", env_name)
            self.envs_available = True
        else:
            self._message_error_box(result_message)
        self.stop_spinner()

    def _after_list_environments(
        self, action_result: bool, result_message: str, manager_options: ManagerOptions
    ):
        # This function must be called only once, at startup. So, we use this variable
        # to prevent running it more times, which happens in our tests for some reason.
        if self._envs_listed:
            return

        if action_result:
            envs = result_message
        else:
            envs = {}

        if not envs:
            self.envs_available = False
            self.show_new_env_widget()
        else:
            self.list_envs_widget.setup_environments(envs)
            self.show_list_envs_widget()
            self.envs_available = True

        self._envs_listed = True

    def _after_import_environment(
        self, action_result: bool, result_message: str, manager_options: ManagerOptions
    ):
        """
        Handle the result of trying to create a new Python environment via the import
        functionality.

        Parameters
        ----------
        action_result : bool
            True if the environment creation was successful. False otherwise.
        result_message : str
            Resulting error or failure message in case `action_result` is False.
        manager : ManagerOptions
            Options used to create the manager.
        """
        if action_result:
            # Add new imported environment entry
            self._add_new_environment_entry(
                action_result, result_message, manager_options
            )
            self.show_list_envs_widget()

            # Install needed spyder-kernels version
            packages = [f"spyder-kernels{SPYDER_KERNELS_VERSION}"]

            request = ManagerRequest(
                manager_options=ManagerOptions(
                    backend=manager_options["backend"],
                    root_path=manager_options["root_path"],
                    env_name=manager_options["env_name"],
                ),
                action=ManagerActions.InstallPackages,
                action_options=dict(
                    packages=packages,
                    channels=(
                        self._prerelease_channels()
                        if parse(spyder_version).is_prerelease
                        else None
                    ),
                    force=True,
                    capture_output=True,
                ),
            )

            self._run_env_manager_action(request, self._after_package_changed)
        else:
            self._message_error_box(result_message)

        self.stop_spinner()

    def _after_export_environment(
        self, action_result: bool, result_message: str, manager_options: ManagerOptions
    ):
        """
        Handle the result of trying to export a Python environment.

        This shows a message box mentioning that the operation was successful or
        failed.

        Parameters
        ----------
        action_result : bool
            True if the environment exportation was successful. False otherwise.
        result_message : str
            Resulting error or failure message in case `action_result` is False.
        manager_options : ManagerOptions
            Options used to create the manager.
        """
        if action_result:
            self.list_envs_widget.set_enabled(True)

            QMessageBox.information(
                self,
                _("Environment exported"),
                _("Python Environment <tt>{env_name}</tt> was exported.").format(
                    env_name=manager_options["env_name"]
                ),
            )
        else:
            self._message_error_box(result_message)
        self.stop_spinner()

    def _after_package_changed(
        self, action_result: bool, result_message: str, manager_options: ManagerOptions
    ):
        """
        Handle the result of trying to install, uninstall or update a package.

        This updates the list of packages in the current environment if the operation
        was successful.

        Parameters
        ----------
        action_result : bool
            True if the package installation was successful. False otherwise.
        result_message : str
            Resulting error or failure message in case `action_result` is False.
        manager_options: ManagerOptions
            Options used to create the manager.
        """
        if action_result:
            self.current_environment_changed()
        else:
            self._message_error_box(result_message)
            self.stop_spinner()

    def _after_delete_environment(
        self, action_result: bool, result_message: str, manager_options: ManagerOptions
    ):
        """
        Handle the result of deleting a Python environment.

        This removes the environment item from the `selected_environment` combobox.

        Parameters
        ----------
        action_result : bool
            True if the environment deletion was successful. False otherwise.
        result_message : str
            Resulting error or failure message in case `action_result` is False.
        manager_options: ManagerOptions
            Options used to create the manager.
        """
        if action_result:
            self.list_envs_widget.delete_environment(manager_options["env_name"])
            self.list_envs_widget.set_enabled(True)
            if not self.list_envs_widget.get_environments():
                self.envs_available = False
                self.show_new_env_widget()
        else:
            self._message_error_box(result_message)
        self.stop_spinner()

    def _after_list_environment_packages(
        self, action_result: bool, result_message: str, manager_options: ManagerOptions
    ):
        """
        Handle the result of computing the current selected environment packages list.

        This updates the packages table widget with the new information.

        Parameters
        ----------
        action_result : bool
            True if the package listing was successful. False otherwise.
        result_message : str
            Resulting error or failure message in case `action_result` is False.
        manager : ManagerOptions
            Options used to create the manager.
        """
        if action_result:
            self.update_packages(
                self.exclude_non_requested_packages,
                result_message["packages"],
                manager_options["env_name"],
                manager_options["env_directory"],
            )
        else:
            self._message_error_box(result_message)
        self.stop_spinner()

    def _run_env_manager_action(self, request: ManagerRequest, on_ready: Callable):
        """
        Run Python environment manager in a worker and connect the result to a given
        callback.

        Parameters
        ----------
        request: ManagerRequest
            Dictionary with the necessary parameters to request an action to the
            manager backend.
        on_ready : SpyderEnvManagerWidget callable
            Method to run when the action finishes.
        """
        if (
            self.env_manager_action_thread
            and self.env_manager_action_thread.isRunning()
        ):
            self.env_manager_action_thread.quit()
            self.env_manager_action_thread.wait()

        self.manager_worker = EnvironmentManagerWorker(self, request)
        self.manager_worker.moveToThread(self.env_manager_action_thread)
        self.manager_worker.sig_ready.connect(on_ready)
        self.manager_worker.sig_ready.connect(self.env_manager_action_thread.quit)
        self.env_manager_action_thread.started.connect(self.manager_worker.start)
        self.start_spinner()
        self.env_manager_action_thread.start()

    def _run_action_for_package(self, package_info, dialog=None, action=None):
        """
        Setup an environment manager instance and run a package related action through
        it in the current environment.

        In case an invalid action was given an error dialog is shown.

        Parameters
        ----------
        package_info : dict
            Dictionary containing the info of the package to modify.
        dialog : CustomParametersDialog, optional
            Dialog instance that can have information about the package action
            that needs to be performed. The default is None.
        action : str, optional
            The package action to be performed. It should defined on the
            `EnvironmentPackagesActions` enum class. The default is None.

        Returns
        -------
        None.

        """
        backend = PixiInterface.ID
        package_name = package_info["name"]
        if action == EnvironmentPackagesActions.UpdatePackage:
            env_name = self.select_environment.currentText()
            request = ManagerRequest(
                manager_options=ManagerOptions(
                    backend=backend,
                    env_name=env_name,
                ),
                action=ManagerActions.UpdatePackages,
                action_options=dict(
                    packages=[package_name],
                    force=True,
                    capture_output=True,
                ),
            )
            self._run_env_manager_action(request, self._after_package_changed)
        elif action == EnvironmentPackagesActions.UninstallPackage:
            env_name = self.select_environment.currentText()
            request = ManagerRequest(
                manager_options=ManagerOptions(
                    backend=backend,
                    env_name=env_name,
                ),
                action=ManagerActions.UninstallPackages,
                action_options=dict(
                    packages=[package_name],
                    force=True,
                    capture_output=True,
                ),
            )
            self._run_env_manager_action(request, self._after_package_changed)
        elif dialog and action == EnvironmentPackagesActions.InstallPackageVersion:
            package_constraint = dialog.combobox.currentText()
            package_version = dialog.lineedit_version.text()
            packages = [f"{package_name}"]
            if package_constraint != "latest" and package_version:
                packages = [f"{package_name}{package_constraint}{package_version}"]
            env_name = self.select_environment.currentText()

            request = ManagerRequest(
                manager_options=ManagerOptions(
                    backend=backend,
                    env_name=env_name,
                ),
                action=ManagerActions.InstallPackages,
                action_options=dict(
                    packages=packages,
                    force=True,
                    capture_output=True,
                ),
            )

            self._run_env_manager_action(request, self._after_package_changed)
        else:
            self._message_error_box("Action unavailable at this moment.")

    def _run_action_for_env(
        self,
        action,
        env_name: str | None = None,
        env_directory: str | None = None,
        python_version: str | None = None,
        packages: list[str] | None = None,
        export_file_path: str | None = None,
        import_file_path: str | None = None,
        dialog=None,
    ):
        """
        Setup an environment manager instance and run an environment related
        action through it.

        In case an invalid action was given an error dialog is shown.

        Parameters
        ----------
        action : str, optional
            Environment action to be performed. The action should defined on the
            `SpyderEnvManagerWidgetActions` enum class. The default is None.
        env_name: str, optional
            Environment name.
        env_directory: str, optional
            Environment directory
        python_version: str, optional
            Environment Python version
        packages: list[str], optional
            List of packages for the environment.
        export_file_path: str, optional
            File to export the environment to.
        import_file_path: str, optional
            File to import the environment from.
        """
        backend = PixiInterface.ID
        if action == SpyderEnvManagerWidgetActions.NewEnvironment:
            packages = [
                f"python={python_version}",
                f"spyder-kernels{SPYDER_KERNELS_VERSION}",
            ] + ([] if packages is None else packages)

            request = ManagerRequest(
                manager_options=ManagerOptions(
                    backend=backend,
                    env_name=env_name,
                ),
                action=ManagerActions.CreateEnvironment,
                action_options=dict(
                    packages=packages,
                    channels=(
                        self._prerelease_channels()
                        if parse(spyder_version).is_prerelease
                        else None
                    ),
                    force=True,
                ),
            )

            self._run_env_manager_action(request, self._add_new_environment_entry)
        elif action == SpyderEnvManagerWidgetActions.ImportEnvironment:
            request = ManagerRequest(
                manager_options=ManagerOptions(
                    backend=backend,
                    env_name=env_name,
                ),
                action=ManagerActions.ImportEnvironment,
                action_options=dict(
                    import_file_path=import_file_path,
                    force=True,
                ),
            )

            self._run_env_manager_action(request, self._after_import_environment)
        elif dialog and action == SpyderEnvManagerWidgetActions.InstallPackage:
            package_name = dialog.lineedit_string.text()
            package_constraint = dialog.combobox.currentText()
            package_version = dialog.lineedit_version.text()
            packages = [f"{package_name}"]
            if package_constraint != "latest" and package_version:
                packages = [f"{package_name}{package_constraint}{package_version}"]
            env_name = self.select_environment.currentText()

            request = ManagerRequest(
                manager_options=ManagerOptions(
                    backend=backend,
                    env_name=env_name,
                ),
                action=ManagerActions.InstallPackages,
                action_options=dict(
                    packages=packages,
                    force=True,
                    capture_output=True,
                ),
            )

            self._run_env_manager_action(request, self._after_package_changed)
        elif action == SpyderEnvManagerWidgetActions.DeleteEnvironment:
            self.list_envs_widget.set_enabled(False)

            request = ManagerRequest(
                manager_options=ManagerOptions(
                    backend=backend,
                    env_name=env_name,
                ),
                action=ManagerActions.DeleteEnvironment,
                action_options=dict(
                    force=True,
                ),
            )

            self._run_env_manager_action(request, self._after_delete_environment)
        elif action == SpyderEnvManagerWidgetActions.ListPackages:
            if env_directory:
                request = ManagerRequest(
                    manager_options=ManagerOptions(
                        backend=backend,
                        env_name=env_name,
                        env_directory=env_directory,
                    ),
                    action=ManagerActions.ListPackages,
                )

                self._run_env_manager_action(
                    request, self._after_list_environment_packages
                )
        elif action == SpyderEnvManagerWidgetActions.ExportEnvironment:
            request = ManagerRequest(
                manager_options=ManagerOptions(
                    backend=backend,
                    env_name=env_name,
                ),
                action=ManagerActions.ExportEnvironment,
                action_options=dict(
                    export_file_path=export_file_path,
                ),
            )

            self._run_env_manager_action(request, self._after_export_environment)
        else:
            self._message_error_box("Action unavailable at this moment.")

    def _export_environment(self, env_name: str):
        self.sig_redirect_stdio_requested.emit(False)
        filename, _selfilter = getsavefilename(
            self,
            _("Export environment"),
            getcwd_or_home() + os.path.sep + f"{env_name}.zip",
            _("Zip files") + " (*.zip)",
        )
        self.sig_redirect_stdio_requested.emit(True)

        if filename:
            self.list_envs_widget.set_enabled(False)

            filename = os.path.normpath(filename)
            self._run_action_for_env(
                action=SpyderEnvManagerWidgetActions.ExportEnvironment,
                env_name=env_name,
                export_file_path=filename,
            )

    def _message_delete_environment(self, env_name: str):
        title = _("Delete environment")
        messages = _("Are you sure you want to delete the current environment?")
        self._message_box(
            title,
            messages,
            action=SpyderEnvManagerWidgetActions.DeleteEnvironment,
            env_name=env_name,
        )

    def _message_box_editable(
        self, title, messages, contents, types, action=None, package_info=None
    ):
        """
        Launch a `CustomParametersDialog` instance to get the needed information
        from the user to perform a given action over an environment.

        The action can modify an environment or a specific package on it.

        Parameters
        ----------
        title : str
            Dialog title.
        messages : list[str]
            Dialog message or labels to show. Each index is a field.
        contents : list[iterable]
            Initial values to set to the custom widget to add.
        types : list[str]
            Widget types that should be constructed in the dialog. Each index is a
            field that correspond to the `messages` list.
        action : str, optional
            Action to be performed with the collected information. It needs to be
            available in the `SpyderEnvManagerWidgetActions` or
            `EnvironmentPackagesActions` enum classes. The default is None.
        package_info : dict, optional
            Package information in case the action affects a specific package inside
            the environment. The default is None.

        Returns
        -------
        None.

        """
        box = CustomParametersDialog(
            self,
            title=title,
            messages=messages,
            types=types,
            contents=contents,
        )
        box.setMaximumWidth(box.width())
        box.setMaximumHeight(box.height())
        box.setMinimumWidth(box.width())
        box.setMinimumHeight(box.height())
        result = box.exec_()
        if result == QDialog.Accepted:
            if package_info:
                self._run_action_for_package(package_info, dialog=box, action=action)
            else:
                self._run_action_for_env(dialog=box, action=action)

    def _message_box(
        self, title, message, action=None, env_name=None, package_info=None
    ):
        """
        Launch a `QMessageBox` instance to get user approval before running the given
        action over an environment.

        The action can modify an environment or a specific package on it.

        Parameters
        ----------
        title : str
            Dialog title.
        message : str
            Dialog message to show.
        action : str, optional
            Action to be performed with the user's approval. It needs to be available
            in the `SpyderEnvManagerWidgetActions` or `EnvironmentPackagesActions`
            enum classes. The default is None.
        package_info : dict, optional
            Package information in case the action affects a specific package inside
            the environment. The default is None.
        """
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setIcon(QMessageBox.Question)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.Yes)
        box.setText(message)
        result = box.exec_()
        if result == QMessageBox.Yes:
            if package_info:
                self._run_action_for_package(package_info, action=action)
            else:
                self._run_action_for_env(action=action, env_name=env_name)

    def _message_error_box(self, message):
        """
        Launch a `QMessageBox` instance to show an error message.

        Parameters
        ----------
        message : str
            Error message to be shown.

        Returns
        -------
        None.

        """
        box = QMessageBox(self)
        box.setWindowTitle("Error message")
        box.setIcon(QMessageBox.Critical)
        box.setStandardButtons(QMessageBox.Ok)
        box.setDefaultButton(QMessageBox.Ok)
        box.setText(message)
        box.exec_()

    def _prerelease_channels(self):
        """Extra channels to make this plugin work with Spyder prereleases."""
        return [
            "conda-forge",
            "conda-forge/label/spyder_kernels_dev",
            "conda-forge/label/spyder_kernels_rc",
        ]

    @property
    def _stylesheet(self):
        css = qstylizer.style.StyleSheet()

        css["QStackedWidget"].setValues(
            borderTop=f"1px solid {SpyderPalette.COLOR_BACKGROUND_4}",
            borderRadius="0px",
        )

        return css.toString()
