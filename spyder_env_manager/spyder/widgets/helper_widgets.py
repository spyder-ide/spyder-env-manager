# -*- coding: utf-8 -*-
#
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------

# Standard imports
import os
import os.path as osp

# Third party imports
import requests
from qtpy.compat import getopenfilename, getsavefilename
from qtpy.QtCore import QRegularExpression, Qt, Signal
from qtpy.QtGui import QRegularExpressionValidator
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Spyder and local imports
from spyder.config.base import _
from spyder.utils.icon_manager import ima
from spyder.utils.misc import getcwd_or_home
from spyder.widgets.comboboxes import FileComboBox
from spyder.widgets.helperwidgets import IconLineEdit


class CustomParametersDialogWidgets:
    ComboBox = "combobox"
    ComboBoxEdit = "combobox_edit"
    ComboBoxFile = "combobox_file"
    Label = "label"
    LineEditVersion = "lineedit_version"
    LineEditString = "lineedit_string"
    LineEditFile = "lineedit_file"


class WidgetTypeNotFound(Exception):
    pass


class CustomParametersDialog(QDialog):
    valid = Signal(bool, bool)

    def __init__(self, parent, title, messages, types, contents):
        super().__init__(parent, Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        self.resize(450, 130)
        self.setWindowTitle(title)
        self.setModal(True)
        self.lineedits = {}

        glayout = QGridLayout()
        glayout.setContentsMargins(0, 0, 0, 0)
        for idx, message in enumerate(messages):
            label = QLabel(_((message + ": ")))
            glayout.addWidget(label, idx, 0, alignment=Qt.AlignVCenter)
            if types[idx] == CustomParametersDialogWidgets.ComboBox:
                self.combobox = QComboBox()
                self.combobox.addItems(contents[idx])
                glayout.addWidget(self.combobox, idx, 1, 1, 2, Qt.AlignVCenter)
            elif types[idx] == CustomParametersDialogWidgets.ComboBoxEdit:
                re = QRegularExpression("[0-9]+([.][0-9]+)*?")
                validator = QRegularExpressionValidator(re, self)
                self.combobox_edit = QComboBox()
                self.combobox_edit.addItems(contents[idx])
                line_edit = IconLineEdit(self)
                self.combobox_edit.setLineEdit(line_edit)
                self.combobox_edit.setEditable(True)
                self.combobox_edit.lineEdit().setValidator(validator)
                self.combobox_edit.editTextChanged.connect(self.validate)
                self.valid.connect(line_edit.update_status)
                show_status = getattr(
                    self.combobox_edit.lineEdit(), "show_status_icon", None
                )
                if show_status:
                    show_status()
                glayout.addWidget(self.combobox_edit, idx, 1, 1, 2, Qt.AlignVCenter)
            elif types[idx] == CustomParametersDialogWidgets.LineEditVersion:
                self.lineedit_version = QLineEdit()
                re = QRegularExpression("[0-9]+([.][0-9]+)*?")
                validator = QRegularExpressionValidator(re, self)
                self.lineedit_version.setValidator(validator)
                glayout.addWidget(self.lineedit_version, idx, 1, 1, 2, Qt.AlignVCenter)
            elif types[idx] == CustomParametersDialogWidgets.Label:
                self.line_string = QLineEdit()
                self.line_string.setReadOnly(True)
                self.line_string.setText(list(contents[idx])[0])
                glayout.addWidget(self.line_string, idx, 1, 1, 2, Qt.AlignVCenter)
            elif types[idx] == CustomParametersDialogWidgets.LineEditString:
                self.lineedit_string = QLineEdit()
                re = QRegularExpression("[a-zA-Z_-]+")
                validator = QRegularExpressionValidator(re, self)
                self.lineedit_string.setValidator(validator)
                glayout.addWidget(self.lineedit_string, idx, 1, 1, 2, Qt.AlignVCenter)
            elif types[idx] == CustomParametersDialogWidgets.ComboBoxFile:
                if os.name == "nt":
                    filters = _("Files") + " (*.yml)"
                else:
                    filters = None
                self.file_combobox = self.create_file_combobox(
                    _("No file choosen"),
                    contents[idx],
                    tip=_("No file choosen"),
                    filters=filters,
                )
                glayout.addWidget(self.file_combobox, idx, 1, idx, 2, Qt.AlignVCenter)
            elif types[idx] == CustomParametersDialogWidgets.LineEditFile:
                if os.name == "nt":
                    filters = _("Files") + " (*.yml)"
                else:
                    filters = None
                self.file_lineedit = self.create_file_lineedit(
                    _("No file choosen"),
                    tip=_("No file choosen"),
                    filters=filters,
                )
                glayout.addWidget(self.file_lineedit, idx, 1, idx, 2, Qt.AlignVCenter)
            else:
                raise WidgetTypeNotFound(
                    "Widget type should be a valid value."
                    "For valid types check the 'CustomParametersDialogWidgets' class"
                )
            glayout.setVerticalSpacing(0)

        # Dialog buttons layout
        bbox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        btnlayout = QHBoxLayout()
        btnlayout.addWidget(bbox)

        # Dialog layout
        layout = QVBoxLayout()
        layout.addLayout(glayout, Qt.AlignTop)
        layout.addLayout(btnlayout)
        self.setLayout(layout)

    def validate(self, qstr, editing=True):
        """Validate entered path
        if self.comboBox.selected_text == qstr and qstr != '':
            self.valid.emit(True, True)
            return
        """
        valid = self.is_valid(qstr)
        if editing:
            if valid:
                self.valid.emit(True, False)
            else:
                self.valid.emit(False, False)

    def is_valid(self, qstr):
        url = ("https://www.python.org/downloads/release/python-{0}/").format(
            qstr.replace(".", "")
        )
        x = requests.head(url)
        return x.status_code == 200

    def text_has_changed(self):
        """Line edit's text has changed."""

        if self.lineedit.hasAcceptableInput():
            self.lineedit.setStyleSheet("border-color: blue")
        else:
            self.lineedit.setStyleSheet("border-color: red")

    def create_file_combobox(
        self,
        text,
        choices,
        tip=None,
        filters=None,
        adjust_to_contents=True,
        default_line_edit=False,
    ):
        """choices: couples (name, key)"""
        combobox = FileComboBox(
            self,
            adjust_to_contents=adjust_to_contents,
            default_line_edit=default_line_edit,
        )
        combobox.label_text = text
        edit = combobox.lineEdit()
        edit.label_text = text

        if tip is not None:
            combobox.setToolTip(tip)
        combobox.addItems(choices)
        combobox.choices = choices

        browse_btn = QPushButton(ima.icon("FileIcon"), "", self)
        browse_btn.setToolTip(_("Select file"))
        browse_btn.clicked.connect(
            lambda: self._select_file(
                edit,
                filters=filters,
                function=getopenfilename,
                options=QFileDialog.DontResolveSymlinks,
            )
        )

        layout = QGridLayout()
        layout.addWidget(combobox, 0, 0, 0, 9)
        layout.addWidget(browse_btn, 0, 10)
        layout.setContentsMargins(0, 0, 0, 0)
        widget = QWidget(self)
        widget.combobox = combobox
        widget.browse_btn = browse_btn
        widget.setLayout(layout)

        return widget

    def _select_file(self, edit, filters=None, function=getopenfilename, **kwargs):
        """Select File."""
        basedir = osp.dirname(str(edit.text()))
        if not osp.isdir(basedir):
            basedir = getcwd_or_home()
        if filters is None:
            filters = _("All files (*)")
        title = _("Select file")
        filename, _selfilter = function(self, title, basedir, filters, **kwargs)
        if filename:
            edit.setText(filename)

    def create_file_lineedit(self, text, tip=None, filters=None, **kwargs):
        """Select File to use for saving."""
        lineedit = QLineEdit()

        browse_btn = QPushButton(ima.icon("FileIcon"), "", self)
        browse_btn.setToolTip(_("Select file"))
        browse_btn.clicked.connect(
            lambda: self._select_file(
                lineedit,
                filters=filters,
                function=getsavefilename,
                options=QFileDialog.DontResolveSymlinks,
            )
        )

        layout = QGridLayout()
        layout.addWidget(lineedit, 0, 0, 0, 9)
        layout.addWidget(browse_btn, 0, 10)
        layout.setContentsMargins(0, 0, 0, 0)
        widget = QWidget(self)
        widget.lineedit = lineedit
        widget.browse_btn = browse_btn
        widget.setLayout(layout)

        return widget
