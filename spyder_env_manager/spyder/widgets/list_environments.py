# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# -----------------------------------------------------------------------------

"""
Widgets for users to select or add Python interpreters.
"""

from __future__ import annotations
import functools

import qstylizer.style
from qtpy.QtCore import Qt, QSize, Signal
from qtpy.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from spyder.api.fonts import SpyderFontType, SpyderFontsMixin
from spyder.api.widgets.mixins import SpyderWidgetMixin
from spyder.api.translations import _
from spyder.utils.icon_manager import ima
from spyder.utils.palette import SpyderPalette
from spyder.utils.stylesheet import AppStyle
from spyder.widgets.elementstable import Element, ElementsTable
from spyder.widgets.helperwidgets import FinderWidget


class EnvironmentsTableButtons:

    DeleteButton = "delete_button"
    ExportButton = "export_button"
    EditButton = "edit_button"


class EnvironmentsTable(ElementsTable, SpyderWidgetMixin):

    CONF_SECTION = ""

    def __init__(self, parent):
        super().__init__(parent, highlight_hovered_row=False)

    # ---- Public API
    # -------------------------------------------------------------------------
    def setup_envs(self, envs: dict[str, str], enabled: bool = True):
        elements = []
        for env_name, env_directory in envs.items():

            # Buttons associated to the element
            button_delete = self.create_toolbutton(
                EnvironmentsTableButtons.DeleteButton,
                icon=ima.icon("editclear"),
                tip=_("Delete environment"),
                triggered=functools.partial(
                    self.parent().sig_delete_env_requested.emit, env_name
                ),
                register=False,
            )

            button_export = self.create_toolbutton(
                EnvironmentsTableButtons.ExportButton,
                icon=ima.icon("fileexport"),
                tip=_("Export environment"),
                triggered=functools.partial(
                    self.parent().sig_export_env_requested.emit, env_name
                ),
                register=False,
            )

            button_edit = self.create_toolbutton(
                EnvironmentsTableButtons.EditButton,
                icon=ima.icon("edit"),
                tip=_("Edit environment"),
                triggered=functools.partial(
                    self.parent().sig_edit_env_requested.emit, env_name, env_directory
                ),
                register=False,
            )

            # Increase icon size for buttons
            for button in [button_delete, button_export, button_edit]:
                button.setIconSize(
                    QSize(AppStyle.ConfigPageIconSize, AppStyle.ConfigPageIconSize)
                )

            # Container widget for the buttons
            widget = QWidget(self)

            layout = QHBoxLayout()
            layout.addWidget(button_delete)
            layout.addWidget(button_export)
            layout.addWidget(button_edit)
            widget.setLayout(layout)

            # Create element
            element = Element(
                title=env_name,
                description=f"{env_directory}",
                icon=ima.icon("python"),
                widget=widget,
            )

            if not enabled:
                element["title_color"] = SpyderPalette.COLOR_DISABLED
                element["description_color"] = SpyderPalette.COLOR_DISABLED

            elements.append(element)

        if self.elements is None:
            self.setup_elements(elements)
        else:
            self.replace_elements(elements)

        self.setEnabled(enabled)


class ListEnvironments(QWidget, SpyderFontsMixin):

    sig_edit_env_requested = Signal(str, str)
    sig_delete_env_requested = Signal(str)
    sig_export_env_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # To hold a reference to the available envs. The mapping is
        # env_name -> env_directory
        self._envs: dict[str, str] = {}

        title_font = self.get_font(SpyderFontType.Interface)
        title_font.setPointSize(title_font.pointSize() + 2)

        title = QLabel(_("Available environments"))
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)

        self._table = EnvironmentsTable(self)
        self._table.setObjectName("envs-table")

        self._finder = FinderWidget(
            self, find_on_change=True, show_close_button=False, set_min_width=False
        )
        self._finder.sig_find_text.connect(self._do_find)

        layout = QVBoxLayout()
        layout.setContentsMargins(
            7 * AppStyle.MarginSize,
            5 * AppStyle.MarginSize,
            7 * AppStyle.MarginSize,
            # The bottom margin is set by the dialog
            0,
        )
        layout.addWidget(title)
        layout.addSpacing(AppStyle.MarginSize)
        layout.addWidget(self._table)
        layout.addWidget(self._finder)
        self.setLayout(layout)

        self.setStyleSheet(self._stylesheet)

    # ---- Public API
    # -------------------------------------------------------------------------
    def setup_environments(self, envs: dict[str, str]):
        self._envs = envs
        self._table.setup_envs(envs)

    def get_environments(self):
        return self._envs

    def add_environment(self, env_name: str, env_directory: str):
        self._envs[env_name] = env_directory
        self._table.setup_envs(self._envs)

    def delete_environment(self, env_name: str):
        self._envs.pop(env_name)
        self._table.setup_envs(self._envs)

    def set_enabled(self, state: bool):
        self._finder.setEnabled(state)
        self._table.setup_envs(self._envs, enabled=state)

    # ---- Private API
    # -------------------------------------------------------------------------
    def _do_find(self, text):
        self._table.do_find(text)

    @property
    def _stylesheet(self):
        css = qstylizer.style.StyleSheet()

        css.QToolButton.setValues(
            height="20px",
            width="20px",
        )

        # Remove indent automatically added by Qt because it breaks layout alignment
        css.QLabel.setValues(**{"qproperty-indent": "0"})

        css["QTableView#envs-table"].setValues(
            # This avoids setting a border color for the selected state
            border=f"1px solid {SpyderPalette.COLOR_BACKGROUND_3}",
            # Make row borders go from the left to the right edge of the table
            paddingLeft="0px",
            paddingRight="0px",
        )

        return css.toString()
