# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# -----------------------------------------------------------------------------

from __future__ import annotations

import qstylizer.style
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout

from spyder.api.fonts import SpyderFontType, SpyderFontsMixin
from spyder.api.translations import _
from spyder.utils.stylesheet import AppStyle
from spyder.widgets.helperwidgets import MessageLabel
from spyder.widgets.config import SpyderConfigPage


class NewEnvironment(SpyderConfigPage, SpyderFontsMixin):

    # SpyderConfigPage API
    MIN_HEIGHT = 100
    LOAD_FROM_CONFIG = False

    def __init__(self, parent, max_width_for_content=510):
        super().__init__(parent)

        title_font = self.get_font(SpyderFontType.Interface)
        title_font.setPointSize(title_font.pointSize() + 2)

        title = QLabel(_("Create new environment"))
        title.setWordWrap(True)
        title.setFont(title_font)

        description = QLabel(
            _(
                "We use Pixi to manage environments and packages. You can access "
                "them in the menu <i>Consoles > New console in environment</i>."
            )
        )
        description.setWordWrap(True)
        description.setFixedWidth(max_width_for_content)

        header_v_layout = QVBoxLayout()
        header_v_layout.addWidget(title)
        header_v_layout.addWidget(description)

        header_layout = QHBoxLayout()
        header_layout.addLayout(header_v_layout)
        header_layout.setAlignment(Qt.AlignHCenter)

        self.env_name = self.create_lineedit(
            text=_("Name"),
            option=None,
            tip=_(
                "This must be alphanumeric and can't include spaces. If no name is "
                "set, then an environment called 'default' will be created"
            ),
            placeholder="default",
            validate_callback=self._validate_name,
            validate_reason=_("The name you selected is not valid"),
        )
        self.env_name.textbox.setFixedWidth(max_width_for_content - 200)

        python_versions = ["3.12", "3.11", "3.10", "3.9", "3.13"]
        python_choices = tuple([2 * (v,) for v in python_versions])
        self.python_version = self.create_combobox(
            text=_("Python version"),
            choices=python_choices,
            option=None,
            tip=_("This can't be modified after creation"),
            alignment=Qt.Vertical,
        )
        self.python_version.combobox.setFixedWidth(200)

        fields_layout = QHBoxLayout()
        fields_layout.addStretch()
        fields_layout.addWidget(self.env_name)
        fields_layout.addWidget(self.python_version)
        fields_layout.addStretch()

        self.validation_label = MessageLabel(self)
        self.validation_label.setFixedWidth(max_width_for_content - 20)
        self.validation_label.setAlignment(Qt.AlignHCenter)

        validation_layout = QHBoxLayout()
        validation_layout.addWidget(self.validation_label)
        validation_layout.setAlignment(Qt.AlignHCenter)

        layout = QVBoxLayout()
        layout.setContentsMargins(
            # There are some pixels by default on the right side. Don't know where they
            # come from and can't get rid of them. But with the ones added below we
            # have almost the same as in the left side.
            6 * AppStyle.MarginSize,
            15 * AppStyle.MarginSize,
            0,
            # The bottom margin is set by the dialog
            0,
        )
        layout.addLayout(header_layout)
        layout.addSpacing(5 * AppStyle.MarginSize)
        layout.addLayout(fields_layout)
        layout.addSpacing(9 * AppStyle.MarginSize)
        layout.addLayout(validation_layout)
        layout.addStretch()
        self.setLayout(layout)

        self.setStyleSheet(self._stylesheet)

    def get_env_name(self):
        env_name = self.env_name.textbox.text()
        if not env_name:
            env_name = "default"
        return env_name

    def get_python_version(self):
        return self.python_version.combobox.currentText()

    def _validate_name(self, name: str):
        return "" or (name.isalnum() and " " not in name)

    def validate_page(self):
        """Validate if the env name introduced by users is valid."""
        self._reset_validaton_state()
        name = self.get_env_name()

        # If the name is empty, we'll use 'default' for it.
        validation = self._validate_name(name)

        if not validation:
            self.validation_label.set_text(
                _("The environment name must be alphanumeric with no spaces")
            )
            self.env_name.status_action.setVisible(True)
            self.validation_label.setVisible(True)

        return validation

    def _reset_validaton_state(self):
        self.env_name.status_action.setVisible(False)
        self.validation_label.setVisible(False)

    @property
    def _stylesheet(self):
        css = qstylizer.style.StyleSheet()

        # Remove indent automatically added by Qt because it breaks layout alignment
        css.QLabel.setValues(**{"qproperty-indent": "0"})

        # This margin was added to deal with the indent added by Qt above
        self.env_name.textbox.setStyleSheet("margin-left: 0px")

        return css.toString()
