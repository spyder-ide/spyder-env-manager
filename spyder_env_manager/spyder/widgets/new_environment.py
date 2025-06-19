# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# -----------------------------------------------------------------------------

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout

from spyder.api.fonts import SpyderFontType, SpyderFontsMixin
from spyder.api.translations import _
from spyder.utils.stylesheet import AppStyle
from spyder.widgets.config import SpyderConfigPage


class NewEnvironment(SpyderConfigPage, SpyderFontsMixin):

    # SpyderConfigPage API
    MIN_HEIGHT = 100
    LOAD_FROM_CONFIG = False

    def __init__(self, parent):
        super().__init__(parent)

        title_font = self.get_font(SpyderFontType.Interface)
        title_font.setPointSize(title_font.pointSize() + 2)

        title = QLabel(_("Create a new environment"))
        title.setWordWrap(True)
        title.setFont(title_font)

        description = QLabel(
            _(
                "We use Pixi to manage environments and packages. You can access "
                "them in the menu <i>Consoles > New console in environment </i>."
            )
        )
        description.setWordWrap(True)
        description.setFixedWidth(510)

        header_v_layout = QVBoxLayout()
        header_v_layout.addWidget(title)
        header_v_layout.addWidget(description)

        header_layout = QHBoxLayout()
        header_layout.addStretch()
        header_layout.addLayout(header_v_layout)
        header_layout.addStretch()

        self.env_name = self.create_lineedit(
            text=_("Name"),
            option=None,
            tip=_("This must be alphanumeric and can't include spaces"),
        )
        self.env_name.textbox.setFixedWidth(300)

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

        layout = QVBoxLayout()
        layout.addSpacing(12 * AppStyle.MarginSize)
        layout.addLayout(header_layout)
        layout.addSpacing(5 * AppStyle.MarginSize)
        layout.addLayout(fields_layout)
        layout.addStretch()
        self.setLayout(layout)

    def get_env_name(self):
        return self.env_name.textbox.text()

    def get_python_version(self):
        return self.python_version.combobox.currentText()
