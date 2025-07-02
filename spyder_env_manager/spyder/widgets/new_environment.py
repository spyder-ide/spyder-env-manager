# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# -----------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
import re
import zipfile

import qstylizer.style
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout

from spyder.api.fonts import SpyderFontType, SpyderFontsMixin
from spyder.api.translations import _
from spyder.utils.icon_manager import ima
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

        self._default_as_env_name = True
        self._name_regexp = re.compile(r"^[a-zA-Z0-9_-]+$")

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
                status_icon=ima.icon("error"),
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

        self.message_label = MessageLabel(self)
        self.message_label.setFixedWidth(max_width_for_content - 20)
        self.message_label.setAlignment(Qt.AlignHCenter)

        message_layout = QHBoxLayout()
        message_layout.addWidget(self.message_label)
        message_layout.setAlignment(Qt.AlignHCenter)

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
        layout.addLayout(message_layout)
        layout.addStretch()
        self.setLayout(layout)

        self.setStyleSheet(self._stylesheet)

    def get_env_name(self):
        env_name = self.env_name.textbox.text()
        if not env_name and self._default_as_env_name:
            env_name = "default"
        return env_name

    def get_python_version(self):
        return self.python_version.combobox.currentText()

    def get_zip_file(self):
        return self.zip_file.textbox.text()

    def clear_contents(self):
        self.env_name.textbox.clear()
        self._reset_validaton_state()
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

    def set_message(self, text: str):
        self.message_label.set_text(text)
        self.message_label.setVisible(True)

    def allow_default_as_env_name(self, allow: bool):
        self._default_as_env_name = allow
        self.env_name.textbox.setPlaceholderText("default" if allow else "")

    def validate_page(self, env_names: list[str]):
        """Validate if the env name introduced by users is valid."""
        self._reset_validaton_state()
        name = self.get_env_name()

        validate_name = validate_zip = True
        reasons = ""
        if name == "":
            validate_name = False
            reasons = _("There are missing fields on this page")
        elif name in env_names:
            validate_name = False
            reasons = _("There is another environment with the same name")
        elif not self._validate_name(name):
            validate_name = False
            reasons = _(
                "The environment name must be alphanumeric with no spaces. It can "
                "also include dashes and underscores"
            )

        if self._import_env:
            validate_zip, zip_reason = self._validate_zip_file()
            if not validate_zip:
                if reasons and reasons != zip_reason:
                    reasons = "- " + reasons + ".<br>" + "- " + zip_reason + "."
                else:
                    reasons = zip_reason

        if not (validate_name and validate_zip):
            if not validate_name:
                self.env_name.status_action.setVisible(True)
            if not validate_zip:
                self.zip_file.status_action.setVisible(True)

            self.message_label.set_text(reasons)
            self.message_label.setVisible(True)

        return validate_name and validate_zip

    def _validate_name(self, name: str):
        return True if re.match(self._name_regexp, name) else False

    def _validate_zip_file(self):
        zip_file = Path(self.get_zip_file())
        validation, reason = (True, "")

        if self.get_zip_file() == "":
            validation, reason = (False, _("There are missing fields on this page"))
        elif not zip_file.is_file():
            validation, reason = (False, _("The file you selected doesn't exist"))
        elif zip_file.suffix != ".zip":
            validation, reason = (False, _("The file you selected is not a zip file"))
        else:
            try:
                with zipfile.ZipFile(zip_file, "r") as zf:
                    name_list = zf.namelist()

                if name_list != ["pixi.toml", "pixi.lock"]:
                    validation, reason = (
                        False,
                        _(
                            "The import file must contain pixi.toml and pixi.lock, "
                            "and no other files"
                        ),
                    )
            except Exception:
                validation, reason = (
                    False,
                    _("Unable to read the zip file you selected"),
                )

        return validation, reason

    def _reset_validaton_state(self):
        self.env_name.status_action.setVisible(False)
        if self._import_env:
            self.zip_file.status_action.setVisible(False)
        self.message_label.set_text("")
        self.message_label.setVisible(False)

    @property
    def _stylesheet(self):
        css = qstylizer.style.StyleSheet()

        # Remove indent automatically added by Qt because it breaks layout alignment
        css.QLabel.setValues(**{"qproperty-indent": "0"})

        # This margin was added to deal with the indent added by Qt above
        self.env_name.textbox.setStyleSheet("margin-left: 0px")

        return css.toString()
