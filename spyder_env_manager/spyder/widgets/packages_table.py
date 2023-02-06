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

# Third library imports
from qtpy.compat import to_qvariant
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QAbstractItemView, QMenu, QTableView

# Spyder and local imports
from spyder.api.translations import get_translation
from spyder.api.widgets.mixins import SpyderWidgetMixin
from spyder.config.fonts import DEFAULT_SMALL_DELTA
from spyder.config.gui import get_font
from spyder.utils.palette import SpyderPalette
from spyder.utils.qthelpers import add_actions, create_action


# Localization
_ = get_translation("spyder")


# Column constants
NAME, VERSION, DESCRIPTION = [0, 1, 2]


class EnvironmentPackagesActions:
    # Actions available for a package (from the context menu)
    UpdatePackage = "update_package"
    UninstallPackage = "unistall_package"
    InstallPackageVersion = "install_package_version"


class EnvironmentPackagesMenu:
    PackageContextMenu = "package_context_menu"


class EnvironmentPackagesModel(QAbstractTableModel):
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
            return to_qvariant(get_font(font_size_delta=DEFAULT_SMALL_DELTA))
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


class EnvironmentPackagesTable(QTableView, SpyderWidgetMixin):
    """Table widget to show the packages inside an enviroment."""

    sig_action_context_menu = Signal(str, dict)
    """
    This signal is emitted when an action in the widget context menu is triggered.

    Parameters
    ----------
    action : str
        The action being processed.
    package_info : dict
        The information available for the package from where the context menu was raised.
    """

    def __init__(self, parent):
        super().__init__(parent, class_parent=parent)
        # Setup context menu
        self.context_menu = self.create_menu(EnvironmentPackagesMenu.PackageContextMenu)

        # Setup table model
        self.source_model = EnvironmentPackagesModel(self)
        self.setModel(self.source_model)

        # Setup table
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.load_packages(False)

    def get_package_info(self, index):
        """
        Get package information by index/row

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

    def load_packages(self, only_requested=False, packages=None):
        """
        Load given packages and filter them if needed.

        Parameters
        ----------
        only_requested : bool, optional
            True if the packages should be filtered and only requested packages be kept. The default is False.
        packages : list[dict], optional
            List of packages to be set on the widget. The default is None.
            The expected package structure is as follows:
            ```
            packages = [
                {
                    "name": "package name",
                    "description": "package description",
                    "version": "0.0.1",
                    "requested": False,
                },
            ]
            ```

        Returns
        -------
        None.

        """

        if packages:
            self.source_model.all_packages = packages
        if not packages and self.source_model.all_packages:
            packages = self.source_model.all_packages
        if packages:
            if only_requested:
                packages = list(filter(lambda package: package["requested"], packages))
            for idx, package in enumerate(packages):
                package["index"] = idx
            packages_map = {package["name"]: package for package in packages}
            self.source_model.beginResetModel()
            self.source_model.packages = packages
            self.source_model.packages_map = packages_map
            self.source_model.endResetModel()

            self.resizeColumnToContents(NAME)

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
            )
            uninstall_action = self.create_action(
                self,
                _("Uninstall package"),
                triggered=lambda triggered: self.sig_action_context_menu.emit(
                    EnvironmentPackagesActions.UninstallPackage, packages[row]
                ),
            )
            change_action = self.create_action(
                self,
                _("Change package version with a constraint"),
                triggered=lambda triggered: self.sig_action_context_menu.emit(
                    EnvironmentPackagesActions.InstallPackageVersion, packages[row]
                ),
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
