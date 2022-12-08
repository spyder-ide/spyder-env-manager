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
from envs_manager.manager import Manager
import qtawesome as qta
from qtpy.QtCore import QUrl
from qtpy.QtWidgets import QComboBox, QDialog, QMessageBox, QSizePolicy, QStackedLayout

# Spyder and local imports
from spyder.api.translations import get_translation
from spyder.api.widgets.main_widget import PluginMainWidget
from spyder.config.base import get_module_source_path
from spyder.dependencies import SPYDER_KERNELS_REQVER
from spyder.utils.icon_manager import ima
from spyder.utils.palette import QStylePalette
from spyder.widgets.browser import FrameWebView

from spyder_env_manager.spyder.widgets.helper_widgets import MessageComboBox
from spyder_env_manager.spyder.widgets.packages_table import EnvironmentPackagesTable

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

        self.envs = self.get_conf("environments_list", {})

        self.select_environment = QComboBox(self)
        self.select_environment.ID = SpyderEnvManagerWidgetActions.SelectEnvironment
        if not self.envs:
            self.envs = {"No environments available"}

        self.select_environment.addItems(self.envs)

        self.select_environment.setToolTip("Select an environment")
        self.select_environment.setSizeAdjustPolicy(
            QComboBox.AdjustToMinimumContentsLength
        )
        self.select_environment.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.css_path = self.get_conf("css_path", CSS_PATH, "appearance")

        self.infowidget = FrameWebView(self)
        self.table_layout = EnvironmentPackagesTable(self, text_color=ima.MAIN_FG_COLOR)
        self.table_layout.sig_action_context_menu.connect(self.table_context_menu)
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
        """Show message on Help with the right shortcuts."""
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

    def table_context_menu(self, action, row):
        if action == "Update":
            title = _("Update packages")
            messages = _("Are you sure you want to update the selected packages?")
            self._message_box(title, messages, "Update")
        elif action == "Uninstall":
            title = _("Uninstall packages")
            messages = _("Are you sure you want to uninstall the selected packages?")
            self._message_box(title, messages, "Uninstall")
        elif action == "Change":
            title = _("Change package version constraint")
            messages = ["Package", "Constraint", "Version"]
            types = ["Label", "ComboBox", "LineEditVersion"]
            contents = [
                {self.table_layout.getPackageByRow(row)["package"]},
                {"==", "<=", ">=", "<", ">", "latest"},
                {},
            ]
            self._message_box_editable(
                title,
                messages,
                contents,
                types,
                action="Change",
            )

    def source_changed(self):
        currentEnvironment = self.select_environment.currentText()
        if currentEnvironment == "No environments available":
            self.stack_layout.setCurrentWidget(self.infowidget)
            self.get_action(SpyderEnvManagerWidgetActions.InstallPackage).setEnabled(
                False
            )
            self.get_action(SpyderEnvManagerWidgetActions.DeleteEnvironment).setEnabled(
                False
            )
            self.get_action(SpyderEnvManagerWidgetActions.ExportEnvironment).setEnabled(
                False
            )
            self.get_action(SpyderEnvManagerWidgetActions.InstallPackage).setEnabled(
                False
            )

        else:
            # Editor
            self.stack_layout.setCurrentWidget(self.table_layout)
            self.get_action(SpyderEnvManagerWidgetActions.InstallPackage).setEnabled(
                True
            )
            self.get_action(SpyderEnvManagerWidgetActions.DeleteEnvironment).setEnabled(
                True
            )
            self.get_action(SpyderEnvManagerWidgetActions.ExportEnvironment).setEnabled(
                True
            )
            self.get_action(SpyderEnvManagerWidgetActions.InstallPackage).setEnabled(
                True
            )

    def update_actions(self):
        pass

    def packages_dependences(self, value):
        self.table_layout.load_packages(value)

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

    def _env_action(self, dialog, action=None):
        if action == SpyderEnvManagerWidgetActions.NewEnvironment:
            root_path = Path(self.get_conf("environments_path"))
            external_executable = self.get_conf("conda_file_executable_path")
            packages = [
                f"python={dialog.combobox_edit.currentText()}",
                f"spyder-kernels{SPYDER_KERNELS_REQVER}",
            ]
            env_name = dialog.lineedit_string.text()
            manager = Manager(
                "conda-like",
                root_path=root_path,
                env_name=env_name,
                external_executable=external_executable,
            )
            manager.create_environment(packages=packages)
            if self.envs == {"No environments available"}:
                self.select_environment.clear()
            self.select_environment.addItem(env_name, manager.env_directory)

        elif action == SpyderEnvManagerWidgetActions.ImportEnvironment:
            pass
        elif action == SpyderEnvManagerWidgetActions.InstallPackage:
            pass
        elif action == SpyderEnvManagerWidgetActions.DeleteEnvironment:
            root_path = Path(self.get_conf("environments_path"))
            external_executable = self.get_conf("conda_file_executable_path")
            packages = [
                f"python={dialog.combobox_edit.currentText()}",
                f"spyder-kernels{SPYDER_KERNELS_REQVER}",
            ]
            env_name = dialog.lineedit_string.text()
            manager = Manager(
                "conda-like",
                root_path=root_path,
                env_name=env_name,
                external_executable=external_executable,
            )
            manager.delete_environment()
            self.select_environment.removeItem(self.select_environment.currentIndex())
        else:
            self._message_error_box("Action no available at this moment.")

    def _message_save_environment(self):
        title = _("File save dialog")
        messages = _("Select where to save the exported environment file")
        self._message_box(
            title, messages, SpyderEnvManagerWidgetActions.ExportEnvironment
        )

    def _message_delete_environment(self):
        title = _("Delete environment")
        messages = _("Are you sure you want to delete the current environment?")
        self._message_box(
            title, messages, SpyderEnvManagerWidgetActions.DeleteEnvironment
        )

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
        contents = [{"conda-like"}, {}, {"3.7.15", "3.8.15", "3.9.15", "3.10.8"}]
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
            self, title=title, messages=messages, types=types, contents=contents
        )
        box.setMaximumWidth(box.width())
        box.setMaximumHeight(box.height())
        box.setMinimumWidth(box.width())
        box.setMinimumHeight(box.height())
        result = box.exec_()
        if result == QDialog.Accepted:
            self._env_action(box, action=action)

    def _message_box(self, title, message, action=None):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setIcon(QMessageBox.Question)
        box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        box.setDefaultButton(QMessageBox.Ok)
        box.setText(message)
        result = box.exec_()
        if result == QDialog.Accepted:
            self._env_action(box, action=action)

    def _message_error_box(self, message):
        box = QMessageBox(self.parent)
        box.setWindowTitle("Error message")
        box.setIcon(QMessageBox.ERROR)
        box.setStandardButtons(QMessageBox.Ok)
        box.setDefaultButton(QMessageBox.Ok)
        box.setText(message)
        box.exec_()
