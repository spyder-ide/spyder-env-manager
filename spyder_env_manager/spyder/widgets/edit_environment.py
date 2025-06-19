# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# -----------------------------------------------------------------------------

import qstylizer.style
from qtpy.QtCore import QSize
from qtpy.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout

from spyder.api.fonts import SpyderFontType, SpyderFontsMixin
from spyder.api.translations import _
from spyder.utils.icon_manager import ima
from spyder.utils.qthelpers import create_toolbutton
from spyder.utils.stylesheet import AppStyle
from spyder.widgets.config import SpyderConfigPage


class EditEnvironment(SpyderConfigPage, SpyderFontsMixin):

    # SpyderConfigPage API
    MIN_HEIGHT = 100
    LOAD_FROM_CONFIG = False

    def __init__(self, parent):
        super().__init__(parent)

        big_font = self.get_font(SpyderFontType.Interface)
        big_font.setPointSize(big_font.pointSize() + 1)

        self.env_action = QLabel("")
        self.env_action.setFont(big_font)

        python_version_label = QLabel(_("Python version"))
        self.python_version = QLabel("")
        self.python_version.setFont(big_font)

        first_line_layout = QHBoxLayout()
        first_line_layout.addWidget(self.env_action)
        first_line_layout.addStretch()
        first_line_layout.addWidget(python_version_label)

        second_line_layout = QHBoxLayout()
        second_line_layout.addStretch()
        second_line_layout.addWidget(self.python_version)

        package_name = self.create_lineedit(
            text=_("Install package"),
            option=None,
            tip=_(
                "Write here the package name as you will pass it to Conda, e.g pandas "
                "or matplotlib"
            ),
        )
        package_name.textbox.setMinimumWidth(400)

        package_version = self.create_lineedit(
            text=_("Version"),
            option=None,
            tip=_("If no version is provided, the latest one will be installed"),
            placeholder=_("Latest"),
        )

        add_package_button = create_toolbutton(self, icon=ima.icon("edit_add"))
        add_package_button.setIconSize(
            QSize(AppStyle.ConfigPageIconSize, AppStyle.ConfigPageIconSize)
        )

        add_package_layout = QVBoxLayout()
        # Empty label to show the button aligned with the lineedits in the second row
        add_package_layout.addWidget(QLabel(" "))
        add_package_layout.addWidget(add_package_button)

        fields_layout = QHBoxLayout()
        fields_layout.addWidget(package_name)
        fields_layout.addWidget(package_version)
        fields_layout.addSpacing(2 * AppStyle.MarginSize)
        fields_layout.addLayout(add_package_layout)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(  # FIXME!
            5 * AppStyle.MarginSize,
            6 * AppStyle.MarginSize,
            2 * AppStyle.MarginSize,
            2 * AppStyle.MarginSize,
        )

        layout.addLayout(first_line_layout)
        layout.addSpacing(-AppStyle.MarginSize)
        layout.addLayout(second_line_layout)
        layout.addSpacing(3 * AppStyle.MarginSize)
        layout.addLayout(fields_layout)
        layout.addStretch()

        self.setLayout(layout)

        self.setStyleSheet(self._stylesheet)

    def setup(self, env_name: str, python_version: str):
        self.env_action.setText(_("Creating environment: ") + f"<b>{env_name}</b>")
        self.python_version.setText(f"<b>{python_version}</b>")

    @property
    def _stylesheet(self):
        css = qstylizer.style.StyleSheet()

        css.QToolButton.setValues(
            height="22px",
            width="22px",
        )

        return css.toString()
