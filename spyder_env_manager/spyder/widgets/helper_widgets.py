# Standard imports
import re
import os
import os.path as osp

# Third party imports
from qtpy import PYQT5
from qtpy.compat import (getexistingdirectory, getopenfilename, from_qvariant,
                         to_qvariant)
from qtpy.QtCore import QPoint, QRegExp, QSize, Qt, QRegularExpression
from qtpy.QtGui import (QAbstractTextDocumentLayout, QPainter,
                        QRegExpValidator, QTextDocument, QRegularExpressionValidator)
from qtpy.QtWidgets import ( QComboBox, QDialog, QDialogButtonBox,
                             QGridLayout, QLineEdit, QLabel, QHBoxLayout,
                             QFileDialog, QVBoxLayout, QPushButton, QWidget)

# Local imports
from spyder.config.base import _
from spyder.utils.icon_manager import ima
from spyder.utils.stringmatching import get_search_regex
from spyder.widgets.comboboxes import FileComboBox
from spyder.config.user import NoDefault
from spyder.py3compat import to_text_string
from spyder.utils.misc import getcwd_or_home


class MessageComboBox(QDialog):
    def __init__(self, editor, title, messages, types, contents):
        QDialog.__init__(self, editor, Qt.WindowTitleHint
                         | Qt.WindowCloseButtonHint)

        # Destroying the C++ object right after closing the dialog box,
        # otherwise it may be garbage-collected in another QThread
        # (e.g. the editor's analysis thread in Spyder), thus leading to
        # a segmentation fault on UNIX or an application crash on Windows
        self.resize(450, 180)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.lineedits = {}

        self.setWindowTitle(_(title))
        self.setModal(True)


        glayout = QGridLayout()
        glayout.setContentsMargins(0, 0, 0, 0)
        for i, message in enumerate(messages):
            label = QLabel(_((message + ": ")))
            #label.setStyleSheet("border: 1px solid white;")
            glayout.addWidget(label, i, 0, alignment=Qt.AlignVCenter)
            if types[i] == 'ComboBox':
                self.comboBox = QComboBox()
                self.comboBox.addItems(contents[i])
                #self.comboBox.setStyleSheet("border: 1px solid white;")
                glayout.addWidget(self.comboBox, i, 1, 1, 2,Qt.AlignVCenter)
            elif types[i] == 'ComboBoxEdit':
                re = QRegularExpression("[0-9]+([.][0-9]+)*?")
                validator = QRegularExpressionValidator(re, self)
                self.comboBox = QComboBox()
                self.comboBox.addItems(contents[i])
                #self.comboBox.setStyleSheet("border: 1px solid white;")
                self.comboBox.setValidator(validator)
                self.comboBox.setEditable(True)
                #self.comboBox.textChanged.connect(self.text_has_changed)
                glayout.addWidget(self.comboBox, i, 1, 1, 2,Qt.AlignVCenter)
                
            elif types[i] == 'LineEditVersion':
                self.lineedit = QLineEdit()
                re = QRegularExpression("[0-9]+([.][0-9]+)*?")
                validator = QRegularExpressionValidator(re, self)
                self.lineedit.setValidator(validator)
                #self.lineedit.textChanged.connect(self.text_has_changed)
                #self.lineedit.setStyleSheet("border: 1px solid white;")
                glayout.addWidget(self.lineedit, i, 1, 1, 2,Qt.AlignVCenter)
            elif types[i] == 'LineEditString':
                self.lineedit = QLineEdit()
                re = QRegularExpression("[a-zA-Z]+")
                validator = QRegularExpressionValidator(re, self)
                self.lineedit.setValidator(validator)
                #self.lineedit.setStyleSheet("border: 1px solid white;")
                glayout.addWidget(self.lineedit, i, 1, 1, 2,Qt.AlignVCenter)
            else:
                if os.name == 'nt':
                    filters = _("Files")+" (*.yml, *.json)"
                else:
                    filters = None
                self.cus_exec_combo = self.create_file_combobox(
                    _('No file choosen'),
                    contents[i],
                    'No file choosen',
                    filters=filters,
                    #validate_callback=self._is_spyder_environment,
                )
                #self.cus_exec_combo.setStyleSheet("border: 1px solid white;")
                glayout.addWidget(self.cus_exec_combo, i, 1, i, 2,Qt.AlignVCenter)
            glayout.setVerticalSpacing(0)

        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
                                Qt.Horizontal, self)
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        btnlayout = QHBoxLayout()
        btnlayout.addWidget(bbox)
        #btnlayout.addStretch(1)

        ok_button = bbox.button(QDialogButtonBox.Ok)
        #ok_button.setEnabled(False)

        layout = QVBoxLayout()
        #glayout.setStyleSheet("border: 1px solid black;")
        layout.addLayout(glayout, Qt.AlignTop)
        layout.addLayout(btnlayout)
        self.setLayout(layout)

        #self.lineedit.setFocus()
    
    
    def text_has_changed(self):
        """Line edit's text has changed."""
        
        if self.lineedit.hasAcceptableInput():
            self.lineedit.setStyleSheet("border-color: blue")
        else:
            self.lineedit.setStyleSheet("border-color: red")
    

    def create_file_combobox(self, text, choices, option, default=NoDefault,
                             tip=None, restart=False, filters=None,
                             adjust_to_contents=True,
                             default_line_edit=False, section=None,
                             validate_callback=None):
        """choices: couples (name, key)"""
        if section is not None and section != self.CONF_SECTION:
            self.cross_section_options[option] = section
        combobox = FileComboBox(self, adjust_to_contents=adjust_to_contents,
                                default_line_edit=default_line_edit)
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

        msg = _('Invalid file path')
        #self.validate_data[edit] = (
        #    validate_callback if validate_callback else osp.isfile,
        #    msg)
        browse_btn = QPushButton(ima.icon('FileIcon'), '', self)
        browse_btn.setToolTip(_("Select file"))
        options = QFileDialog.DontResolveSymlinks
        browse_btn.clicked.connect(
            lambda: self.select_file(edit, filters, options=options))

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
        filename, _selfilter = getopenfilename(self, title, basedir, filters,
                                               **kwargs)
        if filename:
            edit.setText(filename)