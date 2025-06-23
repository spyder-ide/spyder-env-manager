# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# -----------------------------------------------------------------------------

import functools

import qstylizer.style
from qtpy.QtCore import QSize, Signal
from qtpy.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout

from spyder.api.fonts import SpyderFontType, SpyderFontsMixin
from spyder.api.translations import _
from spyder.utils.icon_manager import ima
from spyder.utils.palette import SpyderPalette
from spyder.utils.qthelpers import create_toolbutton
from spyder.utils.stylesheet import AppStyle
from spyder.widgets.config import SpyderConfigPage

from spyder_env_manager.spyder.widgets.packages_table import (
    EnvironmentPackagesTable,
    PackageInfo,
)


class EditEnvironment(SpyderConfigPage, SpyderFontsMixin):

    # SpyderConfigPage API
    MIN_HEIGHT = 100
    LOAD_FROM_CONFIG = False

    sig_packages_changed = Signal(bool)
    sig_packages_loaded = Signal()

    def __init__(self, parent):
        super().__init__(parent)

        self._packages_to_change: list[PackageInfo] = []

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

        self._package_name = self.create_lineedit(
            text=_("Install package"),
            option=None,
            tip=_(
                "Write the package name as you'd pass it to Conda, e.g pandas "
                "or matplotlib"
            ),
        )
        self._package_name.textbox.setMinimumWidth(400)

        self._package_version = self.create_lineedit(
            text=_("Version"),
            option=None,
            tip=_("If no version is provided, the latest one will be installed"),
            placeholder=_("Latest"),
        )

        self._add_package_button = create_toolbutton(
            self,
            icon=ima.icon("edit_add"),
            triggered=self._on_add_package_button_clicked,
        )
        self._add_package_button.setIconSize(
            QSize(AppStyle.ConfigPageIconSize, AppStyle.ConfigPageIconSize)
        )

        add_package_layout = QVBoxLayout()
        # Empty label to show the button aligned with the lineedits in the second row
        add_package_layout.addWidget(QLabel(" "))
        add_package_layout.addWidget(self._add_package_button)

        fields_layout = QHBoxLayout()
        fields_layout.addWidget(self._package_name)
        fields_layout.addSpacing(2 * AppStyle.MarginSize)
        fields_layout.addWidget(self._package_version)
        fields_layout.addSpacing(2 * AppStyle.MarginSize)
        fields_layout.addLayout(add_package_layout)

        packages_table_header = QLabel(_("Packages to install"))
        packages_table_header.setObjectName("packages-table-header")

        self._packages_table = EnvironmentPackagesTable(self, name_column_width=400)
        self._packages_table.setObjectName("packages-table")

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(  # FIXME!
            6 * AppStyle.MarginSize + 1,
            6 * AppStyle.MarginSize,
            # There are some pixels by default on the right side. Don't know where they
            # come from and can't get rid of them. But with the ones added below we
            # have almost the same as in the left side.
            2 * AppStyle.MarginSize + 1,
            2 * AppStyle.MarginSize,
        )

        layout.addLayout(first_line_layout)
        layout.addSpacing(-AppStyle.MarginSize)
        layout.addLayout(second_line_layout)
        layout.addSpacing(3 * AppStyle.MarginSize)
        layout.addLayout(fields_layout)
        layout.addSpacing(8 * AppStyle.MarginSize)
        layout.addWidget(packages_table_header)
        layout.addWidget(self._packages_table)
        layout.addStretch()

        self.setLayout(layout)

        self.setStyleSheet(self._stylesheet)

    def setup(self, env_name: str, python_version: str):
        self.env_action.setText(_("Creating environment: ") + f"<b>{env_name}</b>")
        self.python_version.setText(f"<b>{python_version}</b>")

    def get_changed_packages(self):
        packages_to_change = []
        for package in self._packages_to_change:
            if package["requested"]:
                name = package["title"]
                version = package["additional_info"]
                package_to_install = (
                    f"{name}={version}" if version != _("Latest") else name
                )
                packages_to_change.append(package_to_install)

        return packages_to_change

    def load_env_packages(self, packages, only_requested):
        """Load the environment packages."""
        if packages is not None:
            if not packages[0].get("title"):
                packages = self._transform_packages_list_to_info(packages)

            # Reset this list to avoid a Qt error.
            self._packages_to_change = []

            # Load packages into the table
            self._packages_table.load_packages(packages, only_requested)

            self.sig_packages_loaded.emit()

    def set_enabled(self, state: bool):
        self._package_name.textbox.setEnabled(state)
        self._package_version.textbox.setEnabled(state)
        self._add_package_button.setEnabled(state)
        self._packages_table.set_enabled(state, change_text_color=not state)

    def _transform_packages_list_to_info(self, packages_list):
        """
        Transform packages list in the envs-manager format to the one used to display
        them in packages_table.
        """
        packages_info = []
        for package in packages_list:
            info = PackageInfo(
                title=package["name"],
                additional_info=package["version"],
                requested=package["requested"],
                # description=package["description"],
            )

            if package["requested"]:
                info["widget"] = self._create_remove_package_button(package["name"])

            packages_info.append(info)

        return packages_info

    def _on_add_package_button_clicked(self):
        name = self._package_name.textbox.text().strip()
        version = self._package_version.textbox.text().strip()

        remove_package_button = self._create_remove_package_button(name)
        package_info = PackageInfo(
            title=name,
            additional_info=version if version else _("Latest"),
            widget=remove_package_button,
            requested=True,
        )
        self._packages_to_change.append(package_info)

        self._packages_table.load_packages(
            self._packages_to_change, only_requested=True
        )

        self.sig_packages_changed.emit(True)

    def _on_remove_package_button_clicked(self, package_name):
        for package in self._packages_to_change:
            if package["title"] == package_name:
                package["requested"] = False

        self._packages_table.load_packages(
            self._packages_to_change, only_requested=True
        )

        if self._packages_table.model.rowCount() == 0:
            self.sig_packages_changed.emit(False)

    def _create_remove_package_button(self, package_name):
        button = create_toolbutton(
            self,
            icon=ima.icon("edit_remove"),
            triggered=functools.partial(
                self._on_remove_package_button_clicked, package_name
            ),
        )
        button.setIconSize(
            QSize(AppStyle.ConfigPageIconSize - 2, AppStyle.ConfigPageIconSize - 2)
        )

        return button

    @property
    def _stylesheet(self):
        css = qstylizer.style.StyleSheet()

        css.QToolButton.setValues(
            height="20px",
            width="20px",
        )

        # Remove indent automatically added by Qt because it breaks layout alignment
        css.QLabel.setValues(**{"qproperty-indent": "0"})

        # These margins were added to deal with the indent added by Qt above
        self._package_name.textbox.setStyleSheet("margin-left: 0px")
        self._package_version.textbox.setStyleSheet("margin-left: 0px")

        css["QLabel#packages-table-header"].setValues(
            # Increase padding (the default one is too small).
            padding=f"{2 * AppStyle.MarginSize}px",
            # Make it a bit different from a default QPushButton to not drag
            # the same amount of attention to it.
            backgroundColor=SpyderPalette.COLOR_BACKGROUND_3,
            # Add top rounded borders
            borderTopLeftRadius=SpyderPalette.SIZE_BORDER_RADIUS,
            borderTopRightRadius=SpyderPalette.SIZE_BORDER_RADIUS,
            # Remove bottom rounded borders
            borderBottomLeftRadius="0px",
            borderBottomRightRadius="0px",
        )

        css["QTableView#packages-table"].setValues(
            # Remove these borders to make it appear attached to the top label
            borderTop="0px",
            borderTopLeftRadius="0px",
            borderTopRightRadius="0px",
            # Match border color with the top label one and avoid to change
            # that color when the widget is given focus
            borderLeft=f"1px solid {SpyderPalette.COLOR_BACKGROUND_3}",
            borderRight=f"1px solid {SpyderPalette.COLOR_BACKGROUND_3}",
            borderBottom=f"1px solid {SpyderPalette.COLOR_BACKGROUND_3}",
            # Make row borders go from the left to the right edge of the table
            paddingLeft="0px",
            paddingRight="0px",
        )

        return css.toString()
