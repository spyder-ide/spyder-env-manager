# -*- coding: utf-8 -*-
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
from qtpy.compat import getopenfilename
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
from spyder.config.user import NoDefault
from spyder.py3compat import to_text_string
from spyder.utils.icon_manager import ima
from spyder.utils.misc import getcwd_or_home
from spyder.widgets.comboboxes import FileComboBox
from spyder.widgets.helperwidgets import IconLineEdit


class MessageComboBox(QDialog):
    valid = Signal(bool, bool)

    def __init__(self, editor, title, messages, types, contents):
        QDialog.__init__(self, editor, Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        # Destroying the C++ object right after closing the dialog box,
        # otherwise it may be garbage-collected in another QThread
        # (e.g. the editor's analysis thread in Spyder), thus leading to
        # a segmentation fault on UNIX or an application crash on Windows
        self.resize(450, 130)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.lineedits = {}

        self.setWindowTitle(_(title))
        self.setModal(True)

        glayout = QGridLayout()
        glayout.setContentsMargins(0, 0, 0, 0)
        for i, message in enumerate(messages):
            label = QLabel(_((message + ": ")))
            glayout.addWidget(label, i, 0, alignment=Qt.AlignVCenter)
            if types[i] == "ComboBox":
                self.comboBox = QComboBox()
                self.comboBox.addItems(contents[i])
                glayout.addWidget(self.comboBox, i, 1, 1, 2, Qt.AlignVCenter)
            elif types[i] == "ComboBoxEdit":
                re = QRegularExpression("[0-9]+([.][0-9]+)*?")
                validator = QRegularExpressionValidator(re, self)
                self.comboBox = QComboBox()
                self.comboBox.addItems(contents[i])
                line_edit = IconLineEdit(self)
                self.comboBox.setLineEdit(line_edit)
                self.comboBox.setEditable(True)
                self.comboBox.lineEdit().setValidator(validator)
                self.comboBox.editTextChanged.connect(self.validate)
                self.valid.connect(line_edit.update_status)
                show_status = getattr(
                    self.comboBox.lineEdit(), "show_status_icon", None
                )
                if show_status:
                    show_status()
                glayout.addWidget(self.comboBox, i, 1, 1, 2, Qt.AlignVCenter)

            elif types[i] == "LineEditVersion":
                self.lineedit = QLineEdit()
                re = QRegularExpression("[0-9]+([.][0-9]+)*?")
                validator = QRegularExpressionValidator(re, self)
                self.lineedit.setValidator(validator)
                glayout.addWidget(self.lineedit, i, 1, 1, 2, Qt.AlignVCenter)
            elif types[i] == "LineEditString":
                self.lineedit = QLineEdit()
                re = QRegularExpression("[a-zA-Z]+")
                validator = QRegularExpressionValidator(re, self)
                self.lineedit.setValidator(validator)
                glayout.addWidget(self.lineedit, i, 1, 1, 2, Qt.AlignVCenter)
            else:
                if os.name == "nt":
                    filters = _("Files") + " (*.yml, *.json)"
                else:
                    filters = None
                self.cus_exec_combo = self.create_file_combobox(
                    _("No file choosen"),
                    contents[i],
                    "No file choosen",
                    filters=filters,
                )
                glayout.addWidget(self.cus_exec_combo, i, 1, i, 2, Qt.AlignVCenter)
            glayout.setVerticalSpacing(0)

        bbox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        btnlayout = QHBoxLayout()
        btnlayout.addWidget(bbox)

        ok_button = bbox.button(QDialogButtonBox.Ok)

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
        option,
        default=NoDefault,
        tip=None,
        restart=False,
        filters=None,
        adjust_to_contents=True,
        default_line_edit=False,
        section=None,
    ):
        """choices: couples (name, key)"""
        if section is not None and section != self.CONF_SECTION:
            self.cross_section_options[option] = section
        combobox = FileComboBox(
            self,
            adjust_to_contents=adjust_to_contents,
            default_line_edit=default_line_edit,
        )
        combobox.restart_required = restart
        combobox.label_text = text
        edit = combobox.lineEdit()
        edit.label_text = text
        edit.restart_required = restart
        self.lineedits[edit] = (section, option, default)

        if tip is not None:
            combobox.setToolTip(tip)
        combobox.addItems(choices)
        combobox.choices = choices

        msg = _("Invalid file path")
        browse_btn = QPushButton(ima.icon("FileIcon"), "", self)
        browse_btn.setToolTip(_("Select file"))
        options = QFileDialog.DontResolveSymlinks
        browse_btn.clicked.connect(
            lambda: self.select_file(edit, filters, options=options)
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

    def select_file(self, edit, filters=None, **kwargs):
        """Select File"""
        basedir = osp.dirname(to_text_string(edit.text()))
        if not osp.isdir(basedir):
            basedir = getcwd_or_home()
        if filters is None:
            filters = _("All files (*)")
        title = _("Select file")
        filename, _selfilter = getopenfilename(self, title, basedir, filters, **kwargs)
        if filename:
            edit.setText(filename)
