# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------
"""
Spyder Env Manager Main Widget.
"""


# Third party imports
from qtpy.QtWidgets import QHBoxLayout, QLabel


# Spyder imports
from spyder.api.config.decorators import on_conf_change
from spyder.api.translations import get_translation

from spyder.api.widgets.main_widget import PluginMainWidget


# Localization
_ = get_translation("spyder_env_manager.spyder")


class SpyderEnvManagerActions:
    ExampleAction = "example_action"


class SpyderEnvManagerToolBarSections:
    ExampleSection = "example_section"


class SpyderEnvManagerOptionsMenuSections:
    ExampleSection = "example_section"


class SpyderEnvManagerWidget(PluginMainWidget):

    # PluginMainWidget class constants

    # Signals

    def __init__(self, name=None, plugin=None, parent=None):
        super().__init__(name, plugin, parent)

        # Create an example label
        self._example_label = QLabel("Example Label 3")

        # Add example label to layout
        layout = QHBoxLayout()
        layout.addWidget(self._example_label)
        self.setLayout(layout)

    # --- PluginMainWidget API
    # ------------------------------------------------------------------------
    def get_title(self):
        return _("Spyder Env Manager")

    def get_focus_widget(self):
        pass

    def setup(self):
        # Create an example action
        example_action = self.create_action(
            name=SpyderEnvManagerActions.ExampleAction,
            text="Example action",
            tip="Example hover hint",
            icon=self.create_icon("spyder"),
            triggered=lambda: print("Example action triggered!"),
        )

        # Add an example action to the plugin options menu
        menu = self.get_options_menu()
        self.add_item_to_menu(
            example_action,
            menu,
            SpyderEnvManagerOptionsMenuSections.ExampleSection,
        )

        # Add an example action to the plugin toolbar
        toolbar = self.get_main_toolbar()
        self.add_item_to_toolbar(
            example_action,
            toolbar,
            SpyderEnvManagerOptionsMenuSections.ExampleSection,
        )

    def update_actions(self):
        pass

    @on_conf_change
    def on_section_conf_change(self, section):
        pass

    # --- Public API
    # ------------------------------------------------------------------------


class RichText(QWidget, SpyderWidgetMixin):
    """
    WebView widget with find dialog
    """

    sig_link_clicked = Signal(QUrl)

    def __init__(self, parent):
        if PYQT5:
            super().__init__(parent, class_parent=parent)
        else:
            QWidget.__init__(self, parent)
            SpyderWidgetMixin.__init__(self, class_parent=parent)

        self.webview = FrameWebView(self)
        self.webview.setup()

        if WEBENGINE:
            self.webview.web_widget.page().setBackgroundColor(QColor(MAIN_BG_COLOR))
        else:
            self.webview.web_widget.setStyleSheet("background:{}".format(MAIN_BG_COLOR))
            self.webview.page().setLinkDelegationPolicy(QWebEnginePage.DelegateAllLinks)

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
        self.webview.linkClicked.connect(self.sig_link_clicked)

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
        self.set_html("", self.webview.url())
