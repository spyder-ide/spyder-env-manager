# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Spyder env manager Main Plugin Widget.
"""

# Third party imports
from qtpy import PYQT5
from qtpy.QtCore import QTimer, Slot, QUrl, Qt
from qtpy.QtWidgets import QInputDialog, QMessageBox, QHBoxLayout, QWidget, QComboBox, QLabel, QVBoxLayout, QStackedLayout
from qtpy.QtGui import QColor
from qtpy.QtWebEngineWidgets import WEBENGINE, QWebEnginePage
import os.path as osp
from string import Template
import pathlib
import os
from qtpy.compat import getopenfilenames
from spyder_kernels.utils.iofuncs import iofunctions

# Local imports
from spyder.utils.misc import getcwd_or_home, remove_backslashes
from spyder.api.widgets.mixins import SpyderWidgetMixin
from spyder.api.config.decorators import on_conf_change
from spyder.api.translations import get_translation
from spyder.plugins.help.utils.sphinxify import ( generate_context, usage, warning)
from spyder.api.widgets.main_widget import PluginMainWidget
from spyder.plugins.variableexplorer.widgets.namespacebrowser import (
    NamespaceBrowser, NamespacesBrowserFinder, VALID_VARIABLE_CHARS)
from spyder.utils.programs import is_module_installed
from spyder.widgets.browser import FrameWebView
from spyder.utils.palette import QStylePalette
from spyder.widgets.findreplace import FindReplace
from spyder.widgets.simplecodeeditor import SimpleCodeEditor
from spyder.config.base import (
    get_home_dir, get_module_source_path, running_under_pytest)
import qtawesome as qta
from spyder.utils.icon_manager import ima
from spyder.config.manager import CONF
from spyder.utils.conda import get_list_conda_envs_cache
from spyder.utils.pyenv import get_list_pyenv_envs_cache
from spyder_env_manager.spyder.widgets.helper_widgets import MessageComboBox
from spyder_env_manager.spyder.widgets.packages_table import EnvironmentPackagesTable

# Localization
_ = get_translation('spyder')


# =============================================================================
# ---- Constants
# =============================================================================
PLUGINS_PATH = get_module_source_path('spyder', 'plugins')
TEMPLATES_PATH = osp.join(
    pathlib.Path(__file__), 'spyder', 'assets', 'templates')
MAIN_BG_COLOR = QStylePalette.COLOR_BACKGROUND_1
separador = osp.sep
ENVIRONMENT_MESSAGE = open(osp.join( separador.join(osp.dirname(os.path.abspath(__file__)).split(separador)[:-2]),'spyder','assets','templates' ,'environment_info.html')).read()
CSS_PATH = osp.join(PLUGINS_PATH, 'help', 'utils', 'static', 'css')
class SpyderEnvManagerWidgetActions:
    # Triggers
    SelectEnvironment = 'select_environment'
    NewEnvironment = 'new_environment'
    DeleteEnvironmentToolbar = 'delete_environment'
    InstallPackageToolbar = 'install_package'

    # Options menu actions
    ImportEnvironment = 'import_environment_action'
    ExportEnvironment = 'export_environment_action'
    ToggleExcludeDependency = 'exclude_dependency_action'



class SpyderEnvManagerWidgetOptionsMenuSections:
    Display = 'excludes_section'
    Highlight = 'highlight_section'


class SpyderEnvManagerWidgetMainToolBarSections:
    Main = 'main_section'








# =============================================================================
# ---- Widgets
# =============================================================================

class PlainText(QWidget):
    """
    Read-only editor widget with find dialog
    """



    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.editor = None

        # Read-only simple code editor
        self.editor = SimpleCodeEditor(self)
        self.editor.setup_editor(
            language='py',
            highlight_current_line=False,
            linenumbers=False,
        )
        self.editor.setReadOnly(True)
        self.editor.setContextMenuPolicy(Qt.CustomContextMenu)

        # Find/replace widget
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)
        self.setLayout(layout)


    def set_font(self, font, color_scheme=None):
        """Set font"""
        self.editor.set_color_scheme(color_scheme)
        self.editor.set_font(font)

    def set_color_scheme(self, color_scheme):
        """Set color scheme"""
        self.editor.set_color_scheme(color_scheme)

    def set_text(self, text):
        self.editor.set_language(None)

        self.editor.set_text(text)
        self.editor.set_cursor_position('sof')



class SpyderEnvManagerWidget(PluginMainWidget):

    # PluginMainWidget class constants
    ENABLE_SPINNER = True


    def __init__(self, name=None, plugin=None, parent=None):
        super().__init__(name, plugin, parent)

        conda_env = get_list_conda_envs_cache()
        pyenv_env = get_list_pyenv_envs_cache()
        envs = {**conda_env, **pyenv_env,'No environments available':''}
        #envs={}
        
        
        self.select_environment =  QComboBox(self)
        #self.create_combobox(
        #    _('Recent custom interpreters'),
        #    self.get_option('custom_interpreters_list'),
        #    'custom_interpreter',
        #)
        self.select_environment.ID = SpyderEnvManagerWidgetActions.SelectEnvironment
        #if not envs:
        #    envs={'No environments available'}
            
        self.select_environment.addItems(envs)
        

        self.select_environment.setToolTip('Select an environment')
        self.select_environment.setMinimumWidth(680)
        self.css_path = self.get_conf('css_path',CSS_PATH, 'appearance')

        self.infowidget = FrameWebView(self)
        self.table_layout = EnvironmentPackagesTable(self, text_color=ima.MAIN_FG_COLOR)
        self.stack_layout = layout = QStackedLayout()
        layout.addWidget(self.infowidget)
        layout.addWidget(self.table_layout)
        self.setLayout(self.stack_layout)
        #Signals
        self.select_environment.currentIndexChanged.connect(
            lambda x: self.source_changed())

    # ---- PluginMainWidget API
    # ------------------------------------------------------------------------
    def get_title(self):
        return _('Spyder Env Manager')

    def setup(self):
        # ---- Options menu actions

        exclude_dependency_action = self.create_action(
            SpyderEnvManagerWidgetActions.ToggleExcludeDependency,
            text=_("Exclude dependency packages"),
            tip=_("Exclude dependency packages"),
            toggled=lambda checked: self.packages_dependences(checked),
        )

        import_environment_action = self.create_action(
            SpyderEnvManagerWidgetActions.ImportEnvironment,
            text=_("Import environment from file (.yml, .txt)"),
            tip=_("Import environment from file (.yml, .txt)"),
            triggered=lambda x: self._message_import_environment(),
        )

        export_environment_action = self.create_action(
            SpyderEnvManagerWidgetActions.ExportEnvironment,
            text=_("Export environment to file (.yml, .txt)"),
            tip=_("Export environment to file (.yml, .txt)"),
            triggered=lambda x: self._message_save_environment(),
        )
        
        # ---- Toolbar actions
        NewEnvironmentToolbar = self.create_action(
            SpyderEnvManagerWidgetActions.NewEnvironment,
            text=_("New environment"),
            icon=qta.icon('mdi.plus',color=ima.MAIN_FG_COLOR, rotated=270),
            triggered=lambda x: self._message_new_environment(),
        )

        DeleteEnvironmentToolbar = self.create_action(
            SpyderEnvManagerWidgetActions.DeleteEnvironmentToolbar,
            text=_("Delete environment"),
            icon=self.create_icon('editclear'),
            triggered=lambda x: self._message_delete_environment(),
        )

        InstallPackageToolbar = self.create_action(
            SpyderEnvManagerWidgetActions.InstallPackageToolbar,
            text=_("Install package"),
            icon=qta.icon('mdi.view-grid-plus-outline',color=ima.MAIN_FG_COLOR),
            #mdi.toy-brick-plus-outline
            triggered=lambda x: self._message_install_package(),
        )
        

        # Options menu
        options_menu = self.get_options_menu()
        for item in [exclude_dependency_action]:
            self.add_item_to_menu(
                item,
                menu=options_menu,
                section=SpyderEnvManagerWidgetOptionsMenuSections.Highlight)
        for item in [import_environment_action, export_environment_action]:
            self.add_item_to_menu(
                item,
                menu=options_menu,
                section=SpyderEnvManagerWidgetOptionsMenuSections.Display,
            )

        # Main toolbar
        main_toolbar = self.get_main_toolbar()        

        for item in [self.select_environment,NewEnvironmentToolbar,                     
                     InstallPackageToolbar, DeleteEnvironmentToolbar]:
            self.add_item_to_toolbar(
                item,
                toolbar=main_toolbar,
                section=SpyderEnvManagerWidgetMainToolBarSections.Main,
            )

        #self.table_layout.sig_update_package.connect(self.update_package)
        self.show_intro_message()
        self.source_changed()
        
        #DeleteEnvironmentToolbar.setEnabled(False)

        #text_full = _(
        #    "Click here to create a NEW ENVIRONMENT")
        #self.rich_text.set_text(text_full)
        #self.stack_layout.setCurrentWidget(self.rich_text)

    def show_intro_message(self):
        """Show message on Help with the right shortcuts."""
        intro_message_eq = _(
            "Click <span title='New environment' style='border : 0.5px solid #c0c0c0;'>&#xFF0B;</span> to create a new environment or to import an environment definition from a file , click the <span title='Options' style='border : 1px solid #c0c0c0;'>&#9776;</span> button on the top right too.")
        self.mainMessage = self._create_info_environment_page(title='Usage',message=intro_message_eq)
        self.infowidget.setHtml(
                self.mainMessage,
                QUrl.fromLocalFile(self.css_path)
            )

    def update_font(self, rich_font):
        self._rich_font = rich_font
        self.infowidget.set_font(rich_font)

    def source_changed(self):
        currentEnvironment = self.select_environment.currentText()
        if currentEnvironment == 'No environments available':
            self.stack_layout.setCurrentWidget(self.infowidget)
            self.get_action(SpyderEnvManagerWidgetActions.InstallPackageToolbar).setEnabled(False)
            self.get_action(SpyderEnvManagerWidgetActions.DeleteEnvironmentToolbar).setEnabled(False)
            self.get_action(SpyderEnvManagerWidgetActions.ExportEnvironment).setEnabled(False)
            self.get_action(SpyderEnvManagerWidgetActions.InstallPackageToolbar).setEnabled(False)
            
        else:
            # Editor
            self.stack_layout.setCurrentWidget(self.table_layout)
            self.get_action(SpyderEnvManagerWidgetActions.InstallPackageToolbar).setEnabled(True)
            self.get_action(SpyderEnvManagerWidgetActions.DeleteEnvironmentToolbar).setEnabled(True)
            self.get_action(SpyderEnvManagerWidgetActions.ExportEnvironment).setEnabled(True)
            self.get_action(SpyderEnvManagerWidgetActions.InstallPackageToolbar).setEnabled(True)
        
    def _create_info_environment_page(self,title,message):
        """Create html page to show while the kernel is starting"""
        environment_message_template = Template(ENVIRONMENT_MESSAGE)
        page = environment_message_template.substitute(
            css_path=self.css_path,
            title=title,
            message=message)
        return page

    def update_actions(self):
        pass

    def _message_save_environment(self):
        title = _('File save dialog')
        messages = _('Select where to save the exported environment file')
        self._message_box(title, messages)

    def _message_delete_environment(self):
        title = _('Delete environment')
        messages = _('Are you sure you want to delete the current environment?')
        self._message_box(title, messages)

    def _message_update_packages(self):
        title = _('Update packages')
        messages = _('Are you sure you want to update the selected packages?')
        self._message_box(title, messages)
        

    def _message_import_environment(self):
        title = _('Import Python environment')
        messages = [_('Manager to use'),_('Packages file')]
        types = ['ComboBox','Other']
        contents=[{'Conda-like','Pyenv'},{}]
        self._message_box_editable(title, messages, contents, types)

    def _message_new_environment(self):
        title = _('New Python environment')
        messages = ['Manager to use','Python version']
        types = ['ComboBox','ComboBoxEdit']
        contents=[{'Conda-like','Pyenv'},{'3.7','3.8','3.9','3.10'}]
        self._message_box_editable(title, messages, contents, types)

    def _message_install_package(self):
        title = _('Install package')
        messages = ['Package','Constraint','Version']
        types = ['LineEditString','ComboBox','LineEditVersion']
        contents=[{},{'==', '<=', '>=', '<', '>','latest'},{}]
        self._message_box_editable(title, messages, contents, types)

    def _message_box_editable(self, title, messages, contents, types):
        box = MessageComboBox(self, title=title, messages=messages, types=types, contents=contents)    
        #box.setMaximumWidth(box.width())
        #box.setMaximumHeight(box.height())
        #box.setMinimumWidth(box.width())
        #box.setMinimumHeight(box.height())    
        box.show()

    def _message_box(self, title, message):        
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setIcon(QMessageBox.Question)
        box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        box.setDefaultButton(QMessageBox.Ok)
        box.setText(message)
        box.show()

    
   
    def import_data(self, filenames=None):
        """Import data from text file."""

        
        title = _("Import data")
        if filenames is None:
            basedir = getcwd_or_home()
            filenames, _selfilter = getopenfilenames(self, title, basedir,
                                                     iofunctions.load_filters)
            if not filenames:
                return
        elif isinstance(filenames, str):
            filenames = [filenames]

        for filename in filenames:
            self.filename = str(filename)
            if os.name == "nt":
                self.filename = remove_backslashes(self.filename)
            extension = osp.splitext(self.filename)[1].lower()

            if extension not in iofunctions.load_funcs:
                buttons = QMessageBox.Yes | QMessageBox.Cancel
                answer = QMessageBox.question(self, title,
                            _("<b>Unsupported file extension '%s'</b><br><br>"
                              "Would you like to import it anyway "
                              "(by selecting a known file format)?"
                              ) % extension, buttons)
                if answer == QMessageBox.Cancel:
                    return
                formats = list(iofunctions.load_extensions.keys())
                item, ok = QInputDialog.getItem(self, title,
                                                _('Open file as:'),
                                                formats, 0, False)
                if ok:
                    extension = iofunctions.load_extensions[str(item)]
                else:
                    return

            load_func = iofunctions.load_funcs[extension]
                
            # 'import_wizard' (self.setup_io)
            if isinstance(load_func, str):
                # Import data with import wizard
                pass

    def save_data(self):
        if self.count():
            nsb = self.current_widget()
            nsb.save_data()
            #self.update_actions()

    def reset_namespace(self):
        if self.count():
            nsb = self.current_widget()
            nsb.reset_namespace()


    def refresh_table(self):
        if self.count():
            nsb = self.current_widget()
            nsb.refresh_table()

    def packages_dependences(self, value):
        self.table_layout.load_packages(value)

    # ---- Private API
    # ------------------------------------------------------------------------



