# -*- coding: utf-8 -*-
#
# -----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# -----------------------------------------------------------------------------


# Third-party imports
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)

# Spyder imports
from spyder.api.translations import _
from spyder.api.widgets.dialogs import SpyderDialogButtonBox
from spyder.utils.stylesheet import AppStyle, MAC

# Local imports
from spyder_env_manager.spyder.api import SpyderEnvManagerWidgetActions
from spyder_env_manager.spyder.widgets.manager import (
    AvailableManagerWidgets,
    EditEnvActions,
    SpyderEnvManagerWidget,
)


class EnvManagerDialog(QDialog):

    def __init__(
        self, parent, envs_manager: SpyderEnvManagerWidget, title: str, icon: QIcon
    ):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setWindowIcon(icon)

        self._is_shown = False
        self._envs_manager = envs_manager
        self._envs_manager.sig_widget_is_shown.connect(self._on_widget_shown)
        self._envs_manager.edit_env_widget.sig_packages_loaded.connect(
            self._on_packages_loaded
        )

        self._buttons_box, buttons_layout = self._create_buttons()
        self._buttons_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._envs_manager)
        layout.addSpacing(
            -(1 * AppStyle.MarginSize) if MAC else 2 * AppStyle.MarginSize
        )
        layout.addLayout(buttons_layout)
        layout.addSpacing(4 * AppStyle.MarginSize)
        self.setLayout(layout)

    def showEvent(self, event):
        if not self._is_shown:
            if self._environments:
                self._envs_manager.show_list_envs_widget()
            else:
                self._envs_manager.show_new_env_widget()

            self._is_shown = True

        super().showEvent(event)

    @property
    def _env_name(self):
        if self._envs_manager.new_env_widget.isVisible():
            return self._envs_manager.new_env_widget.get_env_name().strip()
        elif self._envs_manager.import_env_widget.isVisible():
            return self._envs_manager.import_env_widget.get_env_name().strip()
        else:
            return self._envs_manager.edit_env_widget.get_env_name()

    @property
    def _python_version(self):
        return self._envs_manager.new_env_widget.get_python_version()

    @property
    def _changed_packages(self):
        return self._envs_manager.edit_env_widget.get_changed_packages()

    @property
    def _environments(self):
        return self._envs_manager.list_envs_widget.get_environments()

    @property
    def _import_file(self):
        return self._envs_manager.import_env_widget.get_zip_file()

    def _on_widget_shown(self, widget: AvailableManagerWidgets, action: EditEnvActions):
        self._set_buttons_state(visible_widget=widget, edit_action=action)
        if widget in [
            AvailableManagerWidgets.NewEnvWidget,
            AvailableManagerWidgets.ListEnvsWidget,
            AvailableManagerWidgets.ImportEnvWidget,
        ]:
            self._envs_manager.edit_env_widget.clear_content()
            self._envs_manager.new_env_widget.clear_contents()
            self._envs_manager.import_env_widget.clear_contents()
        elif widget == AvailableManagerWidgets.EditEnvWidget:
            if action == EditEnvActions.EditEnv:
                self._envs_manager.edit_env_widget.set_enabled(False)
                self._envs_manager.edit_env_widget.set_empty_message_visible(False)
            else:
                self._envs_manager.edit_env_widget.set_empty_message_visible(True)

    def _create_buttons(self):
        bbox = SpyderDialogButtonBox(QDialogButtonBox.Cancel)

        self._button_cancel = bbox.button(QDialogButtonBox.Cancel)

        self._button_next = QPushButton(_("Next"))
        self._button_next.clicked.connect(self._on_next_button_clicked)
        bbox.addButton(self._button_next, QDialogButtonBox.ActionRole)

        self._button_back = QPushButton(_("Back"))
        self._button_back.clicked.connect(self._on_back_button_clicked)
        bbox.addButton(self._button_back, QDialogButtonBox.ResetRole)

        self._button_create = QPushButton(_("Create"))
        self._button_create.clicked.connect(self._on_create_button_clicked)
        self._button_create.setEnabled(False)
        self._envs_manager.edit_env_widget.sig_packages_changed.connect(
            self._button_create.setEnabled
        )
        bbox.addButton(self._button_create, QDialogButtonBox.ActionRole)

        self._button_import = QPushButton(_("Import"))
        self._button_import.clicked.connect(self._on_import_button_clicked)
        bbox.addButton(self._button_import, QDialogButtonBox.ActionRole)

        layout = QHBoxLayout()
        layout.setContentsMargins(
            3 * AppStyle.MarginSize, 0, 3 * AppStyle.MarginSize, 0
        )
        layout.addWidget(bbox)
        return bbox, layout

    def _set_buttons_state(
        self,
        visible_widget: AvailableManagerWidgets,
        edit_action: EditEnvActions | None = None,
    ):
        self._buttons_box.setEnabled(True)

        if visible_widget == AvailableManagerWidgets.NewEnvWidget:
            self._button_next.setVisible(True)
            self._button_create.setVisible(False)
            self._button_import.setVisible(False)
            self._button_cancel.setText("Cancel")
            if self._environments:
                self._button_back.setVisible(True)
            else:
                self._button_back.setVisible(False)
        elif visible_widget == AvailableManagerWidgets.ListEnvsWidget:
            self._button_cancel.setText("Close")
            for button in [
                self._button_next,
                self._button_create,
                self._button_back,
                self._button_import,
            ]:
                button.setVisible(False)
        elif visible_widget == AvailableManagerWidgets.ImportEnvWidget:
            self._envs_manager.import_env_widget.set_enabled(True)
            self._button_next.setVisible(False)
            self._button_create.setVisible(False)
            self._button_import.setVisible(True)
            self._button_cancel.setText("Cancel")
            if self._environments:
                self._button_back.setVisible(True)
            else:
                self._button_back.setVisible(False)
        elif visible_widget == AvailableManagerWidgets.EditEnvWidget:
            self._button_next.setVisible(False)
            self._button_import.setVisible(False)
            self._button_back.setVisible(True)
            if edit_action == EditEnvActions.CreateEnv:
                self._button_create.setVisible(True)
                self._button_create.setEnabled(False)
                self._button_cancel.setText("Cancel")
            else:
                self._button_create.setVisible(False)
                self._button_cancel.setText("Close")

    def _on_next_button_clicked(self):
        env_names = list(self._environments.keys())
        if not self._envs_manager.new_env_widget.validate_contents(env_names):
            return

        self._envs_manager.edit_env_widget.setup(self._env_name, self._python_version)
        self._envs_manager.show_edit_env_widget(action=EditEnvActions.CreateEnv)

    def _on_create_button_clicked(self):
        self._envs_manager._run_action_for_env(
            action=SpyderEnvManagerWidgetActions.NewEnvironment,
            env_name=self._env_name,
            python_version=self._python_version,
            packages=self._changed_packages,
        )

        self._buttons_box.setEnabled(False)
        self._envs_manager.edit_env_widget.set_enabled(False)

    def _on_back_button_clicked(self):
        if self._environments:
            self._envs_manager.show_list_envs_widget()
        else:
            self._envs_manager.show_new_env_widget()

    def _on_import_button_clicked(self):
        env_names = list(self._environments.keys())
        if not self._envs_manager.import_env_widget.validate_contents(env_names):
            return

        self._envs_manager.import_env_widget.set_message(
            _("The environment is being imported. Please wait...")
        )
        self._envs_manager._run_action_for_env(
            action=SpyderEnvManagerWidgetActions.ImportEnvironment,
            env_name=self._env_name,
            import_file_path=self._import_file,
        )

        self._buttons_box.setEnabled(False)
        self._envs_manager.import_env_widget.set_enabled(False)

    def _on_packages_loaded(self):
        self._button_create.setVisible(False)
        self._envs_manager.edit_env_widget.set_enabled(True)
        self._button_cancel.setText("Close")
