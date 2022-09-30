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
from qtpy.QtWidgets import QAction, QHBoxLayout, QWidget, QComboBox, QLabel, QVBoxLayout, QStackedLayout
from qtpy.QtGui import QColor
from qtpy.QtWebEngineWidgets import WEBENGINE, QWebEnginePage

# Local imports
from spyder.api.widgets.mixins import SpyderWidgetMixin
from spyder.api.config.decorators import on_conf_change
from spyder.api.translations import get_translation
from spyder.plugins.help.utils.sphinxify import (CSS_PATH, generate_context, usage, warning)
from spyder.api.shellconnect.main_widget import ShellConnectMainWidget
from spyder.plugins.variableexplorer.widgets.namespacebrowser import (
    NamespaceBrowser, NamespacesBrowserFinder, VALID_VARIABLE_CHARS)
from spyder.utils.programs import is_module_installed
from spyder.widgets.browser import FrameWebView
from spyder.utils.palette import QStylePalette
from spyder.widgets.findreplace import FindReplace
from spyder.widgets.simplecodeeditor import SimpleCodeEditor

# Localization
_ = get_translation('spyder')


# =============================================================================
# ---- Constants
# =============================================================================
MAIN_BG_COLOR = QStylePalette.COLOR_BACKGROUND_1

class SpyderEnvManagerWidgetActions:
    # Triggers
    SelectEnvironment = 'select_environment'
    NewEnvironment = 'new_environment'
    DeleteEnvironmentToolbar = 'delete_environment'

    # Options menu actions
    CreateEnvironment = 'create_environment_action'
    DeleteEnvironment = 'delete_environment_action'
    ImportEnvironment = 'import_environment_action'
    ExportEnvironment = 'export_environment_action'
    CloseEnvironment = 'close_environment_action'


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



class SpyderEnvManagerWidget(ShellConnectMainWidget):

    # PluginMainWidget class constants
    ENABLE_SPINNER = True


    def __init__(self, name=None, plugin=None, parent=None):
        super().__init__(name, plugin, parent)


        self.select_environment = QComboBox(self)
        self.select_environment.ID = SpyderEnvManagerWidgetActions.SelectEnvironment
        self.select_environment.addItems([_("No environments Available")])
        self.css_path = self.get_conf('css_path', CSS_PATH, 'appearance')

        # Create an example label
        self.plain_text = PlainText(self)

        # Add example label to layout
        self.stack_layout = layout = QStackedLayout()
        layout.addWidget(self.plain_text)
        self.setLayout(layout)

    # ---- PluginMainWidget API
    # ------------------------------------------------------------------------
    def get_title(self):
        return _('Spyder Env Manager')

    def setup(self):
        # ---- Options menu actions
        create_environment_action = self.create_action(
            SpyderEnvManagerWidgetActions.CreateEnvironment,
            text=_("Create new environment"),
            tip=_("Create new environment"),
            triggered=lambda x: self.import_data(),
        )

        delete_environment_action = self.create_action(
            SpyderEnvManagerWidgetActions.DeleteEnvironment,
            text=_("Delete environment"),
            tip=_("Delete environment"),
            triggered=lambda x: self.import_data(),
        )

        import_environment_action = self.create_action(
            SpyderEnvManagerWidgetActions.ImportEnvironment,
            text=_("Import environment from file (.yml, .txt)"),
            tip=_("Import environment from file (.yml, .txt)"),
            triggered=lambda x: self.import_data(),
        )

        export_environment_action = self.create_action(
            SpyderEnvManagerWidgetActions.ExportEnvironment,
            text=_("Export environment to file (.yml, .txt)"),
            tip=_("Export environment to file (.yml, .txt)"),
            triggered=lambda x: self.import_data(),
        )

        close_environment_action = self.create_action(
            SpyderEnvManagerWidgetActions.CloseEnvironment,
            text=_("Undock/Close environment"),
            tip=_("Undock/Close environment"),
            triggered=lambda x: self.import_data(),
        )

        
        # ---- Toolbar actions
        

        DeleteEnvironmentToolbar = self.create_action(
            SpyderEnvManagerWidgetActions.DeleteEnvironmentToolbar,
            text=_("Delete environment"),
            icon=self.create_icon('editdelete'),
            triggered=lambda x: self.reset_namespace(),
        )


        # Options menu
        options_menu = self.get_options_menu()
        for item in [create_environment_action, delete_environment_action,
                     import_environment_action, export_environment_action,
                     close_environment_action]:
            self.add_item_to_menu(
                item,
                menu=options_menu,
                section=SpyderEnvManagerWidgetOptionsMenuSections.Display,
            )

        # Main toolbar
        main_toolbar = self.get_main_toolbar()
        for item in [self.select_environment, DeleteEnvironmentToolbar]:
            self.add_item_to_toolbar(
                item,
                toolbar=main_toolbar,
                section=SpyderEnvManagerWidgetMainToolBarSections.Main,
            )
        #DeleteEnvironmentToolbar.setEnabled(False)

        text_full = _(
            "Click here to create a NEW ENVIRONMENT")
        self.plain_text.set_text(text_full)
        self.stack_layout.setCurrentWidget(self.plain_text)

    '''    
    def update_actions(self):
        action = self.get_action(SpyderEnvManagerWidgetActions.ToggleMinMax)
        action.setEnabled(is_module_installed('numpy'))
        nsb = self.current_widget()

        for __, action in self.get_actions().items():
            if action:
                # IMPORTANT: Since we are defining the main actions in here
                # and the context is WidgetWithChildrenShortcut we need to
                # assign the same actions to the children widgets in order
                # for shortcuts to work
                if nsb:
                    save_data_action = self.get_action(
                        VariableExplorerWidgetActions.SaveData)
                    save_data_action.setEnabled(nsb.filename is not None)

                    nsb_actions = nsb.actions()
                    if action not in nsb_actions:
                        nsb.addAction(action)
    '''
    @on_conf_change
    def on_section_conf_change(self, section):
        for index in range(self.count()):
            widget = self._stack.widget(index)
            if widget:
                widget.setup()


    # ---- Stack accesors
    # ------------------------------------------------------------------------
    def update_finder(self, nsb, old_nsb):
        """Initialize or update finder widget."""
        if self.finder is None:
            # Initialize finder/search related widgets
            self.finder = QWidget(self)
            self.text_finder = NamespacesBrowserFinder(
                nsb.editor,
                callback=nsb.editor.set_regex,
                main=nsb,
                regex_base=VALID_VARIABLE_CHARS)
            self.finder.text_finder = self.text_finder
            self.finder_close_button = self.create_toolbutton(
                'close_finder',
                triggered=self.hide_finder,
                icon=self.create_icon('DialogCloseButton'),
            )

            finder_layout = QHBoxLayout()
            finder_layout.addWidget(self.finder_close_button)
            finder_layout.addWidget(self.text_finder)
            finder_layout.setContentsMargins(0, 0, 0, 0)
            self.finder.setLayout(finder_layout)

            layout = self.layout()
            layout.addSpacing(1)
            layout.addWidget(self.finder)
        else:
            # Just update references to the same text_finder (Custom QLineEdit)
            # widget to the new current NamespaceBrowser and save current
            # finder state in the previous NamespaceBrowser
            if old_nsb is not None:
                self.save_finder_state(old_nsb)
            self.text_finder.update_parent(
                nsb.editor,
                callback=nsb.editor.set_regex,
                main=nsb,
            )

    def switch_widget(self, nsb, old_nsb):
        """
        Set the current NamespaceBrowser.

        This also setup the finder widget to work with the current
        NamespaceBrowser.
        """
        self.update_finder(nsb, old_nsb)
        finder_visible = nsb.set_text_finder(self.text_finder)
        self.finder.setVisible(finder_visible)
        search_action = self.get_action(SpyderEnvManagerWidgetActions.Search)
        search_action.setChecked(finder_visible)

    # ---- Public API
    # ------------------------------------------------------------------------

    def create_new_widget(self, shellwidget):
        nsb = NamespaceBrowser(self)
        nsb.set_shellwidget(shellwidget)
        nsb.setup()
        nsb.sig_free_memory_requested.connect(
            self.free_memory)
        nsb.sig_start_spinner_requested.connect(
            self.start_spinner)
        nsb.sig_stop_spinner_requested.connect(
            self.stop_spinner)
        nsb.sig_hide_finder_requested.connect(
            self.hide_finder)
        self._set_actions_and_menus(nsb)
        return nsb

    def close_widget(self, nsb):
        nsb.close()
        nsb.setParent(None)

    def import_data(self, filenames=None):
        """
        Import data in current namespace.
        """
        if self.count():
            nsb = self.current_widget()
            nsb.refresh_table()
            nsb.import_data(filenames=filenames)

    def save_data(self):
        if self.count():
            nsb = self.current_widget()
            nsb.save_data()
            self.update_actions()

    def reset_namespace(self):
        if self.count():
            nsb = self.current_widget()
            nsb.reset_namespace()

    @Slot(bool)
    def show_finder(self, checked):
        if self.count():
            nsb = self.current_widget()
            if checked:
                self.finder.text_finder.setText(nsb.last_find)
            else:
                self.save_finder_state(nsb)
                self.finder.text_finder.setText('')
            self.finder.setVisible(checked)
            if self.finder.isVisible():
                self.finder.text_finder.setFocus()
            else:
                nsb.editor.setFocus()

    @Slot()
    def hide_finder(self):
        action = self.get_action(SpyderEnvManagerWidgetActions.Search)
        action.setChecked(False)
        nsb = self.current_widget()
        self.save_finder_state(nsb)
        self.finder.text_finder.setText('')

    def save_finder_state(self, nsb):
        """
        Save finder state (last input text and visibility).

        The values are saved in the given NamespaceBrowser.
        """
        last_find = self.text_finder.text()
        finder_visibility = self.finder.isVisible()
        nsb.save_finder_state(last_find, finder_visibility)

    def refresh_table(self):
        if self.count():
            nsb = self.current_widget()
            nsb.refresh_table()

    @Slot()
    def free_memory(self):
        """
        Free memory signal.
        """
        self.sig_free_memory_requested.emit()
        QTimer.singleShot(self.INITIAL_FREE_MEMORY_TIME_TRIGGER,
                          self.sig_free_memory_requested)
        QTimer.singleShot(self.SECONDARY_FREE_MEMORY_TIME_TRIGGER,
                          self.sig_free_memory_requested)

    def resize_rows(self):
        self._current_editor.resizeRowsToContents()

    def resize_columns(self):
        self._current_editor.resize_column_contents()

    def paste(self):
        self._current_editor.paste()

    def copy(self):
        self._current_editor.copy()

    def edit_item(self):
        self._current_editor.edit_item()

    def plot_item(self):
        self._current_editor.plot_item('plot')

    def histogram_item(self):
        self._current_editor.plot_item('hist')

    def imshow_item(self):
        self._current_editor.imshow_item()

    def save_array(self):
        self._current_editor.save_array()

    def insert_item(self):
        self._current_editor.insert_item(below=False)

    def remove_item(self):
        self._current_editor.remove_item()

    def rename_item(self):
        self._current_editor.rename_item()

    def duplicate_item(self):
        self._current_editor.duplicate_item()

    def view_item(self):
        self._current_editor.view_item()

    # ---- Private API
    # ------------------------------------------------------------------------
    @property
    def _current_editor(self):
        editor = None
        if self.count():
            nsb = self.current_widget()
            editor = nsb.editor
        return editor

    def _set_actions_and_menus(self, nsb):
        """
        Set actions and menus created here and used by the namespace
        browser editor.

        Although this is not ideal, it's necessary to be able to use
        the CollectionsEditor widget separately from this plugin.
        """
        editor = nsb.editor

        # Actions
        editor.paste_action = self.paste_action
        editor.copy_action = self.copy_action
        editor.edit_action = self.edit_action
        editor.plot_action = self.plot_action
        editor.hist_action = self.hist_action
        editor.imshow_action = self.imshow_action
        editor.save_array_action = self.save_array_action
        editor.insert_action = self.insert_action
        editor.remove_action = self.remove_action
        editor.minmax_action = self.show_minmax_action
        editor.rename_action = self.rename_action
        editor.duplicate_action = self.duplicate_action
        editor.view_action = self.view_action


        # These actions are not used for dictionaries (so we don't need them
        # for namespaces) but we have to create them so they can be used in
        # several places in CollectionsEditor.
        editor.insert_action_above = QAction()
        editor.insert_action_below = QAction()



class RichText(QWidget, SpyderWidgetMixin):
    """
    WebView widget with find dialog
    """

    def __init__(self, parent):
        if PYQT5:
            super().__init__(parent, class_parent=parent)
        else:
            QWidget.__init__(self, parent)
            SpyderWidgetMixin.__init__(self, class_parent=parent)

        self.webview = FrameWebView(self)
        self.webview.setup()

        if WEBENGINE:
            self.webview.web_widget.page().setBackgroundColor(
                QColor(MAIN_BG_COLOR))
        else:
            self.webview.web_widget.setStyleSheet(
                "background:{}".format(MAIN_BG_COLOR))
            self.webview.page().setLinkDelegationPolicy(
                QWebEnginePage.DelegateAllLinks)

        self.find_widget = FindReplace(self)
        self.find_widget.set_editor(self.webview.web_widget)
        self.find_widget.hide()

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.webview)
        layout.addWidget(self.find_widget)
        self.setLayout(layout)

        # Signals

    def set_font(self, font, fixed_font=None):
        """Set font"""
        self.webview.set_font(font, fixed_font=fixed_font)

    def set_html(self, html_text, base_url):
        """Set html text"""
        self.webview.setHtml(html_text, base_url)

    def load_url(self, url):
        if isinstance(url, QUrl):
            qurl = url
        else:
            qurl = QUrl(url)
        self.webview.load(qurl)

    def clear(self):
        self.set_html('', self.webview.url())
