# -*- coding: utf-8 -*-
#
# -----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# -----------------------------------------------------------------------------

# Standard library imports
from typing import TYPE_CHECKING

# Third-party imports
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


if TYPE_CHECKING:
    from spyder_env_manager.spyder.widgets.manager import SpyderEnvManagerWidget


class EnvManagerDialog(QDialog):

    def __init__(self, parent, envs_manager):
        super().__init__(parent)

        self._is_shown = False
        self._envs_manager: SpyderEnvManagerWidget = envs_manager
        self._envs_manager.show_new_env_widget()
        self._envs_manager.sig_new_env_widget_is_shown.connect(
            self._on_new_env_widget_shown
        )

        buttons_box, buttons_layout = self._create_buttons()
        buttons_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.setContentsMargins(
            AppStyle.MarginSize,
            0,
            AppStyle.MarginSize,
            0,
        )
        layout.addWidget(self._envs_manager)
        layout.addSpacing(-(1 * AppStyle.MarginSize) if MAC else 0)
        layout.addLayout(buttons_layout)
        layout.addSpacing(3 * AppStyle.MarginSize)
        self.setLayout(layout)

    def showEvent(self, event):
        if not self._is_shown:
            self._set_buttons_state(is_new_env_widget_visible=True)
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

    def _on_new_env_widget_shown(self):
        self._set_buttons_state(is_new_env_widget_visible=True)

    def _create_buttons(self):
        bbox = SpyderDialogButtonBox(QDialogButtonBox.Cancel)

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
        layout.setContentsMargins(AppStyle.MarginSize, 0, AppStyle.MarginSize, 0)
        layout.addWidget(bbox)
        return bbox, layout

    def _set_buttons_state(self, is_new_env_widget_visible: bool):
        self._button_next.setVisible(is_new_env_widget_visible)
        self._button_create.setVisible(not is_new_env_widget_visible)
        self._button_back.setVisible(not is_new_env_widget_visible)

    def _on_next_button_clicked(self):
        if not self._envs_manager.new_env_widget.validate_page():
            return

        self._envs_manager.set_env_metadata(self._env_name, self._python_version)

        self._envs_manager.show_edit_env_widget()
        self._set_buttons_state(is_new_env_widget_visible=False)

    def _on_create_button_clicked(self):
        self._envs_manager._run_action_for_env(
            SpyderEnvManagerWidgetActions.NewEnvironment,
            self._env_name,
            self._python_version,
            self._changed_packages,
        )

    def _on_back_button_clicked(self):
        self._envs_manager.show_new_env_widget()
        self._set_buttons_state(is_new_env_widget_visible=True)
