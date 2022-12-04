# -*- coding: utf-8 -*-
#
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------

"""
Spyder env manager Main Plugin Widget.
"""

# Standard library imports
import os
import os.path as osp
from pathlib import Path
from string import Template

# Third party imports
from envs_manager.backends.conda_like_interface import CondaLikeInterface
from envs_manager.manager import Manager
import qtawesome as qta
from qtpy.QtCore import QThread, QUrl
from qtpy.QtGui import QColor
from qtpy.QtWebEngineWidgets import WEBENGINE, QWebEnginePage
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QMessageBox,
    QSizePolicy,
    QStackedLayout,
)

# Spyder and local imports
from spyder.api.translations import get_translation
from spyder.api.widgets.main_widget import PluginMainWidget
from spyder.config.base import get_module_source_path
from spyder.dependencies import SPYDER_KERNELS_REQVER
from spyder.utils.icon_manager import ima
from spyder.utils.palette import QStylePalette
from spyder.widgets.browser import FrameWebView

from spyder_env_manager.spyder.workers import EnvironmentManagerWorker
from spyder_env_manager.spyder.widgets.helper_widgets import MessageComboBox
from spyder_env_manager.spyder.widgets.packages_table import (
    EnvironmentPackagesTable,
)

# Localization
_ = get_translation("spyder")


# =============================================================================
# ---- Constants
# =============================================================================
PLUGINS_PATH = get_module_source_path("spyder", "plugins")
TEMPLATES_PATH = Path(__file__) / "spyder" / "assets" / "templates"
MAIN_BG_COLOR = QStylePalette.COLOR_BACKGROUND_1
separador = osp.sep
ENVIRONMENT_MESSAGE = Path(
    separador.join(osp.dirname(os.path.abspath(__file__)).split(separador)[:-2]),
    "spyder",
    "assets",
    "templates",
    "environment_info.html",
)
CSS_PATH = Path(PLUGINS_PATH) / "help" / "utils" / "static" / "css"
SPYDER_KERNELS_VERSION = SPYDER_KERNELS_REQVER.split(";")[0]


class SpyderEnvManagerWidgetActions:
    # Triggers
    SelectEnvironment = "select_environment"
    NewEnvironment = "new_environment"
    DeleteEnvironment = "delete_environment"
    InstallPackage = "install_package"

    # Options menu actions
    ImportEnvironment = "import_environment_action"
    ExportEnvironment = "export_environment_action"
    ToggleExcludeDependency = "exclude_dependency_action"


class SpyderEnvManagerWidgetOptionsMenuSections:
    Display = "excludes_section"
    Highlight = "highlight_section"


class SpyderEnvManagerWidgetMainToolBarSections:
    Main = "main_section"


# =============================================================================
# ---- Widgets
# =============================================================================


class SpyderEnvManagerWidget(PluginMainWidget):

    # PluginMainWidget class constants
    ENABLE_SPINNER = True

    def __init__(self, name=None, plugin=None, parent=None):
        super().__init__(name, plugin, parent)

        self.envs = Manager.list_environments(backend=CondaLikeInterface.ID)
        self.env_manager_action_thread = None
        self.manager_worker = None
        self.select_environment = QComboBox(self)
        self.select_environment.ID = SpyderEnvManagerWidgetActions.SelectEnvironment

        for env_name, env_directory in self.envs.items():
            self.select_environment.addItem(env_name, env_directory)

        if not self.envs:
            self.envs = {"No environments available"}
            self.select_environment.addItems(self.envs)

        self.select_environment.setToolTip("Select an environment")
        self.select_environment.setSizeAdjustPolicy(
            QComboBox.AdjustToMinimumContentsLength
        )
        self.select_environment.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        selected_environment = self.get_conf("selected_environment")
        if selected_environment:
            self.select_environment.setCurrentText(selected_environment)
        self.css_path = self.get_conf("css_path", CSS_PATH, "appearance")

        self.infowidget = FrameWebView(self)
        if WEBENGINE:
            self.infowidget.web_widget.page().setBackgroundColor(QColor(MAIN_BG_COLOR))
        else:
            self.infowidget.web_widget.setStyleSheet(
                "background:{}".format(MAIN_BG_COLOR)
            )
            self.infowidget.page().setLinkDelegationPolicy(
                QWebEnginePage.DelegateAllLinks
            )
        self.table_layout = EnvironmentPackagesTable(self, text_color=ima.MAIN_FG_COLOR)
        self.stack_layout = layout = QStackedLayout()
        layout.addWidget(self.infowidget)
        layout.addWidget(self.table_layout)
        self.setLayout(self.stack_layout)

        # Signals
        self.select_environment.currentIndexChanged.connect(self.source_changed)

    # ---- PluginMainWidget API
    # ------------------------------------------------------------------------
    def get_title(self):
        return _("Spyder Env Manager")

    def setup(self):
        # ---- Options menu actions

        exclude_dependency_action = self.create_action(
            SpyderEnvManagerWidgetActions.ToggleExcludeDependency,
            text=_("Exclude dependency packages"),
            tip=_("Exclude dependency packages"),
            toggled=self.packages_dependences,
        )

        import_environment_action = self.create_action(
            SpyderEnvManagerWidgetActions.ImportEnvironment,
            text=_("Import environment from file (.yml, .txt)"),
            tip=_("Import environment from file (.yml, .txt)"),
            triggered=self._message_import_environment,
        )

        export_environment_action = self.create_action(
            SpyderEnvManagerWidgetActions.ExportEnvironment,
            text=_("Export environment to file (.yml, .txt)"),
            tip=_("Export environment to file (.yml, .txt)"),
            triggered=self._message_save_environment,
        )

        # ---- Toolbar actions
        new_environment_action = self.create_action(
            SpyderEnvManagerWidgetActions.NewEnvironment,
            text=_("New environment"),
            icon=qta.icon("mdi.plus", color=ima.MAIN_FG_COLOR, rotated=270),
            triggered=self._message_new_environment,
        )

        delete_environment_action = self.create_action(
            SpyderEnvManagerWidgetActions.DeleteEnvironment,
            text=_("Delete environment"),
            icon=self.create_icon("editclear"),
            triggered=self._message_delete_environment,
        )

        install_package_action = self.create_action(
            SpyderEnvManagerWidgetActions.InstallPackage,
            text=_("Install package"),
            icon=qta.icon("mdi.view-grid-plus-outline", color=ima.MAIN_FG_COLOR),
            # mdi.toy-brick-plus-outline
            triggered=self._message_install_package,
        )

        # Options menu
        options_menu = self.get_options_menu()
        for item in [exclude_dependency_action]:
            self.add_item_to_menu(
                item,
                menu=options_menu,
                section=SpyderEnvManagerWidgetOptionsMenuSections.Highlight,
            )
        for item in [import_environment_action, export_environment_action]:
            self.add_item_to_menu(
                item,
                menu=options_menu,
                section=SpyderEnvManagerWidgetOptionsMenuSections.Display,
            )

        # Main toolbar
        main_toolbar = self.get_main_toolbar()

        for item in [
            self.select_environment,
            new_environment_action,
            install_package_action,
            delete_environment_action,
        ]:
            self.add_item_to_toolbar(
                item,
                toolbar=main_toolbar,
                section=SpyderEnvManagerWidgetMainToolBarSections.Main,
            )

        self.show_intro_message()
        self.source_changed()

    def show_intro_message(self):
        """Show introduction message to use the plugin."""
        intro_message_eq = _(
            "Click <span title='New environment' style='border : 0.5px solid #c0c0c0;'>&#xFF0B;</span> to create a new environment or to import an environment definition from a file , click the <span title='Options' style='border : 1px solid #c0c0c0;'>&#9776;</span> button on the top right too."
        )
        self.mainMessage = self._create_info_environment_page(
            title="Usage", message=intro_message_eq
        )
        self.infowidget.setHtml(self.mainMessage, QUrl.fromLocalFile(self.css_path))

    def update_font(self, rich_font):
        self._rich_font = rich_font
        self.infowidget.set_font(rich_font)

    def source_changed(self):
        current_environment = self.select_environment.currentText()
        actions = [
            SpyderEnvManagerWidgetActions.InstallPackage,
            SpyderEnvManagerWidgetActions.DeleteEnvironment,
            SpyderEnvManagerWidgetActions.ExportEnvironment,
        ]
        environments_available = current_environment != "No environments available"
        for action in actions:
            self.get_action(action).setEnabled(environments_available)
        if environments_available:
            self.stack_layout.setCurrentWidget(self.table_layout)
            # TODO: Set selected env interpreter as Spyder main interpreter
        else:
            self.stack_layout.setCurrentWidget(self.infowidget)

    def update_actions(self):
        pass

    def packages_dependences(self, value):
        self.table_layout.load_packages(value)

    def start_spinner(self):
        for action in self.get_actions().values():
            action.setEnabled(False)
        super().start_spinner()

    def stop_spinner(self):
        for action in self.get_actions().values():
            action.setEnabled(True)
        self.source_changed()
        super().stop_spinner()

    def on_close(self):
        env_name = self.select_environment.currentText()
        self.set_conf("selected_environment", env_name)

    # ---- Private API
    # ------------------------------------------------------------------------

    def _create_info_environment_page(self, title, message):
        """Create html page to show while the kernel is starting"""
        with open(ENVIRONMENT_MESSAGE) as templete_message:
            environment_message_template = Template(templete_message.read())
            page = environment_message_template.substitute(
                css_path=self.css_path, title=title, message=message
            )
        return page

    def _add_new_environment_entry(self, manager, action_result, result_message):
        if action_result:
            if self.envs == {"No environments available"}:
                self.select_environment.clear()
            self.select_environment.addItem(manager.env_name, manager.env_directory)
            self.select_environment.setCurrentText(manager.env_name)
            self.set_conf("selected_environment", manager.env_name)
            self.set_conf(
                "environments_list", Manager.list_environments(CondaLikeInterface.ID)
            )
        else:
            # TODO: Show error message
            # result_message -> str
            print(self.manager_worker.error)
            print(result_message)
        self.stop_spinner()

    def _env_action(self, dialog, action=None):
        if action == SpyderEnvManagerWidgetActions.NewEnvironment:
            root_path = Path(self.get_conf("environments_path"))
            external_executable = self.get_conf("conda_file_executable_path")
            packages = [
                f"python={dialog.combobox_edit.currentText()}",
                f"spyder-kernels{SPYDER_KERNELS_VERSION}",
            ]
            env_name = dialog.lineedit_string.text()
            manager = Manager(
                "conda-like",
                root_path=root_path,
                env_name=env_name,
                external_executable=external_executable,
            )
            if (
                self.env_manager_action_thread
                and self.env_manager_action_thread.isRunning()
            ):
                self.env_manager_action_thread.quit()
                self.env_manager_action_thread.wait()

            self.env_manager_action_thread = QThread(None)
            self.manager_worker = EnvironmentManagerWorker(
                self, manager, manager.create_environment, packages=packages, force=True
            )
            self.manager_worker.sig_ready.connect(self._add_new_environment_entry)
            self.manager_worker.sig_ready.connect(self.env_manager_action_thread.quit)
            self.manager_worker.moveToThread(self.env_manager_action_thread)
            self.env_manager_action_thread.started.connect(self.manager_worker.start)
            self.start_spinner()
            self.env_manager_action_thread.start()
        elif action == SpyderEnvManagerWidgetActions.ImportEnvironment:
            pass
        elif action == SpyderEnvManagerWidgetActions.InstallPackage:
            pass

    def _message_save_environment(self):
        title = _("File save dialog")
        messages = _("Select where to save the exported environment file")
        self._message_box(title, messages)

    def _message_delete_environment(self):
        title = _("Delete environment")
        messages = _("Are you sure you want to delete the current environment?")
        self._message_box(title, messages)

    def _message_update_packages(self):
        title = _("Update packages")
        messages = _("Are you sure you want to update the selected packages?")
        self._message_box(title, messages)

    def _message_import_environment(self):
        title = _("Import Python environment")
        messages = [_("Manager to use"), _("Packages file")]
        types = ["ComboBox", "Other"]
        contents = [{"conda-like"}, {}]
        self._message_box_editable(
            title,
            messages,
            contents,
            types,
            action=SpyderEnvManagerWidgetActions.ImportEnvironment,
        )

    def _message_new_environment(self):
        title = _("New Python environment")
        messages = ["Manager to use", "Environment Name", "Python version"]
        types = ["ComboBox", "LineEditString", "ComboBoxEdit"]
        contents = [
            {"conda-like"},
            {},
            ["3.7.15", "3.8.15", "3.9.15", "3.10.8"],
        ]
        self._message_box_editable(
            title,
            messages,
            contents,
            types,
            action=SpyderEnvManagerWidgetActions.NewEnvironment,
        )

    def _message_install_package(self):
        title = _("Install package")
        messages = ["Package", "Constraint", "Version"]
        types = ["LineEditString", "ComboBox", "LineEditVersion"]
        contents = [{}, {"==", "<=", ">=", "<", ">", "latest"}, {}]
        self._message_box_editable(
            title,
            messages,
            contents,
            types,
            action=SpyderEnvManagerWidgetActions.InstallPackage,
        )

    def _message_box_editable(self, title, messages, contents, types, action=None):
        box = MessageComboBox(
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
            self._env_action(box, action=action)

    def _message_box(self, title, message):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setIcon(QMessageBox.Question)
        box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        box.setDefaultButton(QMessageBox.Ok)
        box.setText(message)
        box.show()
