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

        buttons_box, buttons_layout = self._create_buttons()
        buttons_box.rejected.connect(self.reject)

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
                self._set_buttons_state(
                    visible_widget=AvailableManagerWidgets.ListEnvsWidget
                )
            else:
                self._set_buttons_state(
                    visible_widget=AvailableManagerWidgets.NewEnvWidget
                )

            self._is_shown = True

        super().showEvent(event)

    @property
    def _env_name(self):
        return self._envs_manager.new_env_widget.get_env_name().strip()

    @property
    def _python_version(self):
        return self._envs_manager.new_env_widget.get_python_version()

    @property
    def _changed_packages(self):
        return self._envs_manager.edit_env_widget.get_changed_packages()

    @property
    def _environments(self):
        return self._envs_manager.list_envs_widget.get_environments()

    def _on_widget_shown(self, widget: AvailableManagerWidgets, action: EditEnvActions):
        self._set_buttons_state(visible_widget=widget, edit_action=action)
        if widget in [
            AvailableManagerWidgets.NewEnvWidget,
            AvailableManagerWidgets.ListEnvsWidget,
        ]:
            self._envs_manager.edit_env_widget.clear_content()
        elif (
            widget == AvailableManagerWidgets.EditEnvWidget
            and action == EditEnvActions.EditEnv
        ):
            self._envs_manager.edit_env_widget.set_enabled(False)

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
        if visible_widget == AvailableManagerWidgets.NewEnvWidget:
            self._button_next.setVisible(True)
            self._button_create.setVisible(False)
            if self._environments:
                self._button_back.setVisible(True)
            else:
                self._button_back.setVisible(False)
        elif visible_widget == AvailableManagerWidgets.ListEnvsWidget:
            self._button_next.setVisible(False)
            self._button_create.setVisible(False)
            self._button_back.setVisible(False)
        elif visible_widget == AvailableManagerWidgets.EditEnvWidget:
            if edit_action == EditEnvActions.CreateEnv:
                self._button_next.setVisible(False)
                self._button_create.setVisible(True)
                self._button_back.setVisible(True)
            else:
                self._button_next.setVisible(False)
                self._button_create.setVisible(False)
                self._button_back.setVisible(True)

    def _on_next_button_clicked(self):
        if not self._envs_manager.new_env_widget.validate_page():
            return

        self._envs_manager.edit_env_widget.setup(self._env_name, self._python_version)
        self._envs_manager.show_edit_env_widget(action=EditEnvActions.CreateEnv)

    def _on_create_button_clicked(self):
        self._envs_manager._run_action_for_env(
            SpyderEnvManagerWidgetActions.NewEnvironment,
            env_name=self._env_name,
            python_version=self._python_version,
            packages=self._changed_packages,
        )

        self._button_back.setVisible(False)
        self._button_create.setEnabled(False)
        self._button_cancel.setEnabled(False)
        self._envs_manager.edit_env_widget.set_enabled(False)

    def _on_back_button_clicked(self):
        if self._environments:
            self._envs_manager.show_list_envs_widget()
        else:
            self._envs_manager.show_new_env_widget()

    def _on_packages_loaded(self):
        self._button_create.setVisible(False)
        self._button_cancel.setEnabled(True)
        self._envs_manager.edit_env_widget.set_enabled(True)
