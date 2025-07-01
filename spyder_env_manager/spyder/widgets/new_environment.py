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

    def __init__(self, parent, max_width_for_content=510, import_env=False):
        super().__init__(parent)
        self._import_env = import_env

        title_font = self.get_font(SpyderFontType.Interface)
        title_font.setPointSize(title_font.pointSize() + 2)

        title = QLabel(
            _("Import environment") if self._import_env else _("Create new environment")
        )
        title.setWordWrap(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)

        if self._import_env:
            description_text = _(
                "Enter a zip file with the environment specification below to import "
                "it. After doing it, you'll be able to access it in the menu "
                "<i>Consoles > New console in environment</i>."
            )
        else:
            description_text = _(
                "We use Pixi to manage environments and packages. You can access "
                "them in the menu <i>Consoles > New console in environment</i>."
            )
        description = QLabel(description_text)
        description.setWordWrap(True)
        description.setFixedWidth(max_width_for_content)

        description_layout = QHBoxLayout()
        description_layout.addWidget(description)
        description_layout.setAlignment(Qt.AlignHCenter)

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

        if self._import_env:
            self.env_name.textbox.setFixedWidth(max_width_for_content - 260)
        else:
            self.env_name.textbox.setFixedWidth(max_width_for_content - 200)

        if self._import_env:
            self.zip_file = self.create_browsefile(
                text=_("File"),
                option=None,
                tip=_("Zip file that contains pixi.toml and pixi.lock"),
                filters=_("Zip files") + " (*.zip)",
                alignment=Qt.Vertical,
            )
            self.zip_file.textbox.setFixedWidth(200)
        else:
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
        fields_layout.addWidget(
            self.zip_file if self._import_env else self.python_version
        )
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
            5 * AppStyle.MarginSize,
            0,
            # The bottom margin is set by the dialog
            0,
        )
        layout.addWidget(title)
        layout.addSpacing(12 * AppStyle.MarginSize)
        layout.addLayout(description_layout)
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

    def get_zip_file(self):
        return self.zip_file.textbox.text()

    def clear_contents(self):
        self.env_name.textbox.clear()
        if self._import_env:
            self.zip_file.textbox.clear()
        else:
            self.python_version.combobox.setCurrentIndex(0)

    def set_enabled(self, state: bool):
        self.env_name.textbox.setEnabled(state)
        if self._import_env:
            self.zip_file.textbox.setEnabled(state)
        else:
            self.python_version.combobox.setEnabled(state)

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

    def _validate_name(self, name: str):
        return "" or (name.isalnum() and " " not in name)

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
