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

if TYPE_CHECKING:
    from spyder_env_manager.spyder.widgets.manager import SpyderEnvManagerWidget


class EnvManagerDialog(QDialog):

    def __init__(self, parent, envs_manager):
        super().__init__(parent)

        self._is_shown = False
        self._envs_manager: SpyderEnvManagerWidget = envs_manager
        self._envs_manager.show_new_env_widget()

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

    def _create_buttons(self):
        bbox = SpyderDialogButtonBox(QDialogButtonBox.Cancel)

        self._button_next = QPushButton(_("Next"))
        self._button_next.clicked.connect(self._on_next_button_clicked)
        bbox.addButton(self._button_next, QDialogButtonBox.ActionRole)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, AppStyle.MarginSize, 0)
        layout.addWidget(bbox)
        return bbox, layout

    def _on_next_button_clicked(self):
        pass
