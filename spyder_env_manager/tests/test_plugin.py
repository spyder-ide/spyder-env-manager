# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------
"""
Spyder Env Manager plugin tests.
"""
# Standard library imports
import logging
from unittest.mock import Mock

# Third-party imports
import pytest
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QMainWindow

# Spyder imports
from spyder.config.manager import CONF

# Local imports
from spyder_env_manager.spyder.plugin import SpyderEnvManager
from spyder_env_manager.spyder.widgets.main_widget import (
    SpyderEnvManagerWidget,
    SpyderEnvManagerWidgetActions,
)
from spyder_env_manager.spyder.widgets.helper_widgets import (
    CustomParametersDialog,
)

# Constants
LONG_OPERATION_TIMEOUT = 100000
OPERATION_TIMEOUT = 50000


# ---- Fixtures
# ------------------------------------------------------------------------
class MainMock(QMainWindow):
    def __init__(self):
        super().__init__()
        self.switcher = Mock()
        self.main = self
        self.resize(640, 480)

    def get_plugin(self, plugin_name, error=True):
        return Mock()


@pytest.fixture
def spyder_env_manager(tmp_path, qtbot, monkeypatch):
    # Mocking mainwindow and config
    window = MainMock()
    backends_root_path = tmp_path / "backends"
    backends_root_path.mkdir(parents=True)

    def get_conf(self, option, default=None, section=None):
        if option == "environments_path":
            return str(backends_root_path)
        else:
            return default

    monkeypatch.setattr(SpyderEnvManagerWidget, "get_conf", get_conf)

    # Setup plugin
    plugin = SpyderEnvManager(parent=window, configuration=CONF)
    widget = plugin.get_widget()
    window.setCentralWidget(widget)
    qtbot.addWidget(window)
    window.show()

    yield plugin

    # Wait for pending operations and close
    qtbot.waitUntil(lambda: widget.actions_enabled, timeout=LONG_OPERATION_TIMEOUT)
    widget.close()
    del plugin
    del window


# ---- Tests
# ------------------------------------------------------------------------
def test_plugin_initial_state(spyder_env_manager, qtbot):
    """Check plugin initialization and that actions and widgets have the correct state when initializing."""
    widget = spyder_env_manager.get_widget()

    # Check for widgets initialization
    assert widget.select_environment.currentData() is None
    assert widget.select_environment.isEnabled()
    assert widget.stack_layout.currentWidget() == widget.infowidget

    # Check widget actions
    disabled_actions_ids = [
        SpyderEnvManagerWidgetActions.InstallPackage,
        SpyderEnvManagerWidgetActions.DeleteEnvironment,
        SpyderEnvManagerWidgetActions.ExportEnvironment,
    ]
    for action_id, action in widget.get_actions().items():
        if action_id in disabled_actions_ids:
            assert not action.isEnabled()
        else:
            assert action.isEnabled()


def test_environment_creation(spyder_env_manager, qtbot, caplog):
    """Test creating an environment."""
    caplog.set_level(logging.DEBUG)
    widget = spyder_env_manager.get_widget()

    def handle_env_creation_dialog():
        dialog = widget.findChild(CustomParametersDialog)
        dialog.lineedit_string.setText("test_env")
        dialog.combobox_edit.setCurrentText("3.8")
        dialog.accept()

    QTimer.singleShot(100, handle_env_creation_dialog)
    widget._message_new_environment()

    qtbot.waitUntil(
        lambda: widget.stack_layout.currentWidget() == widget.packages_table,
        timeout=LONG_OPERATION_TIMEOUT,
    )
    assert widget.select_environment.currentText() == "test_env"
    qtbot.waitUntil(
        lambda: widget.packages_table.source_model.rowCount() == 2,
        timeout=OPERATION_TIMEOUT,
    )
