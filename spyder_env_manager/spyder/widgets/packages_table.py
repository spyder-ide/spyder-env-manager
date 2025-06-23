# -*- coding: utf-8 -*-
#
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------

"""
Package table widget.

This is the main widget used in the Spyder env Manager plugin
"""

# Standard library imports
from __future__ import annotations

# Third library imports
from qtpy.compat import to_qvariant
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from qtpy.QtGui import QColor

# Spyder and local imports
from spyder.api.fonts import SpyderFontType, SpyderFontsMixin
from spyder.api.translations import get_translation
from spyder.utils.palette import SpyderPalette
from spyder.widgets.elementstable import Element, ElementsTable


# Localization
_ = get_translation("spyder")


# Column constants
NAME, VERSION, DESCRIPTION = [0, 1, 2]


class PackageInfo(Element):

    requested: bool
    """Whether the package was requested by the user or not."""


class EnvironmentPackagesActions:
    """
    Actions available for a package from the `EnvironmentPackagesTable`
    context menu.
    """

    UpdatePackage = "update_package"
    UninstallPackage = "unistall_package"
    InstallPackageVersion = "install_package_version"


class EnvironmentPackagesMenu:
    PackageContextMenu = "package_context_menu"


class EnvironmentPackagesModel(QAbstractTableModel, SpyderFontsMixin):
    def __init__(self, parent):
        super().__init__(parent)
        self.all_packages = []
        self.packages = []
        self.packages_map = {}

    def flags(self, index):
        """Qt Override."""
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index))

    def data(self, index, role=Qt.DisplayRole):
        """Qt Override."""
        row = index.row()
        if not index.isValid() or not (0 <= row < len(self.packages)):
            return to_qvariant()

        package = self.packages[row]
        column = index.column()

        if role == Qt.DisplayRole:
            if column == NAME:
                text = package["name"]
                return to_qvariant(text)
            elif column == DESCRIPTION:
                text = package["description"]
                return to_qvariant(text)
            elif column == VERSION:
                text = package["version"]
                return to_qvariant(text)
        elif role == Qt.TextAlignmentRole:
            return to_qvariant(int(Qt.AlignCenter))
        elif role == Qt.FontRole:
            return self.get_font(font_type=SpyderFontType.Interface)
        elif role == Qt.BackgroundColorRole:
            if package["requested"]:
                return to_qvariant(QColor(SpyderPalette.COLOR_OCCURRENCE_4))
        return to_qvariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Qt Override."""
        if role == Qt.TextAlignmentRole:
            if orientation == Qt.Horizontal:
                return to_qvariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
            return to_qvariant(int(Qt.AlignRight | Qt.AlignVCenter))
        if role != Qt.DisplayRole:
            return to_qvariant()
        if orientation == Qt.Horizontal:
            if section == NAME:
                return to_qvariant(_("Name"))
            elif section == DESCRIPTION:
                return to_qvariant(_("Description"))
            elif section == VERSION:
                return to_qvariant(_("Version"))
        return to_qvariant()

    def rowCount(self, index=QModelIndex()):
        """Qt Override."""
        return len(self.packages)

    def columnCount(self, index=QModelIndex()):
        """Qt Override."""
        return 3


class EnvironmentPackagesTable(ElementsTable):
    """Table widget to show the installed packages in an environment."""

    sig_action_context_menu = Signal(str, dict)
    """
    This signal is emitted when an action in the widget context menu is triggered.

    Parameters
    ----------
    action : str
        The action being processed.
    package_info : dict
        Available information for the package on top of which the user requested to
        show the context menu of this widget.
    """

    def __init__(self, parent, name_column_width=None):
        super().__init__(parent, highlight_hovered_row=False)
        self._name_column_width = name_column_width
        self._packages: list[PackageInfo] | None = None

        # Setup context menu
        # self.context_menu = self.create_menu(EnvironmentPackagesMenu.PackageContextMenu)

    def get_package_info(self, index):
        """
        Get package information by index (i.e. row).

        Parameters
        ----------
        index : int
            Index of the request package.

        Returns
        -------
        dict
            Package information available.

        """
        return self.source_model.packages[index]

    def load_packages(
        self,
        packages: list[PackageInfo] | None = None,
        only_requested: bool = False,
    ):
        """
        Load given packages and filter them if needed.

        Parameters
        ----------
        only_requested : bool, optional
            True if the packages should be filtered and only requested packages
            be kept. The default is False.
        packages : list[PackageInfo], optional
            List of packages to be displayed on the widget. The default is None.
        """
        if packages:
            if only_requested:
                packages = list(filter(lambda package: package["requested"], packages))

            # Save list of packages to use them later
            self._packages = packages

            if self.elements is None:
                self.setup_elements(packages, set_layout=True)
            else:
                self.replace_elements(packages)

            if self._name_column_width is not None:
                self.horizontalHeader().resizeSection(0, self._name_column_width + 9)

    def set_enabled(self, state, change_text_color=False):
        self.setEnabled(state)
        if change_text_color:
            for package in self._packages:
                package["title_color"] = SpyderPalette.COLOR_DISABLED
                package["additional_info_color"] = SpyderPalette.COLOR_DISABLED

            self.load_packages(self._packages)

    def next_row(self):
        """Move to next row from currently selected row."""
        row = self.currentIndex().row()
        rows = self.source_model.rowCount()
        if row + 1 == rows:
            row = -1
        self.selectRow(row + 1)

    def previous_row(self):
        """Move to previous row from currently selected row."""
        row = self.currentIndex().row()
        rows = self.source_model.rowCount()
        if row == 0:
            row = rows
        self.selectRow(row - 1)

    def contextMenuEvent(self, event):
        """Qt Override."""
        self.context_menu.clear_actions()
        row = self.rowAt(event.pos().y())
        packages = self.source_model.packages
        if packages and packages[row]["requested"]:
            update_action = self.create_action(
                self,
                _("Update package"),
                triggered=lambda triggered: self.sig_action_context_menu.emit(
                    EnvironmentPackagesActions.UpdatePackage, packages[row]
                ),
                overwrite=True,
            )
            uninstall_action = self.create_action(
                self,
                _("Uninstall package"),
                triggered=lambda triggered: self.sig_action_context_menu.emit(
                    EnvironmentPackagesActions.UninstallPackage, packages[row]
                ),
                overwrite=True,
            )
            change_action = self.create_action(
                self,
                _("Change package version with a constraint"),
                triggered=lambda triggered: self.sig_action_context_menu.emit(
                    EnvironmentPackagesActions.InstallPackageVersion, packages[row]
                ),
                overwrite=True,
            )
            menu_actions = [
                update_action,
                uninstall_action,
                change_action,
            ]
            for menu_action in menu_actions:
                self.add_item_to_menu(menu_action, self.context_menu)
            self.context_menu.setMinimumWidth(100)
            self.context_menu.popup(event.globalPos())
            event.accept()

    def focusInEvent(self, e):
        """Qt Override."""
        super(EnvironmentPackagesTable, self).focusInEvent(e)
        self.selectRow(self.currentIndex().row())

    def keyPressEvent(self, event):
        """Qt Override."""
        key = event.key()
        if key in [Qt.Key_Enter, Qt.Key_Return]:
            self.show_editor()
        elif key in [Qt.Key_Backtab]:
            self.parent().reset_btn.setFocus()
        elif key in [Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right]:
            super(EnvironmentPackagesTable, self).keyPressEvent(event)
        else:
            super(EnvironmentPackagesTable, self).keyPressEvent(event)
