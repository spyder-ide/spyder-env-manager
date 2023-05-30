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
from pathlib import Path
from unittest.mock import Mock

# Third-party imports
import pytest
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QMainWindow

# Spyder imports
from spyder.config.manager import CONF

# Local imports
from spyder_env_manager.spyder.config import CONF_DEFAULTS
from spyder_env_manager.spyder.plugin import SpyderEnvManager
from spyder_env_manager.spyder.widgets.main_widget import (
    SpyderEnvManagerWidget,
    SpyderEnvManagerWidgetActions,
)
from spyder_env_manager.spyder.widgets.helper_widgets import (
    CustomParametersDialog,
)

# Constants
OPERATION_TIMEOUT = 120000
IMPORT_FILE_PATH = str(Path(__file__).parent / "data" / "import_env.yml")


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
def spyder_env_manager_conf(tmp_path, qtbot, monkeypatch):
    # Mocking mainwindow and get_config
    window = MainMock()
    backends_root_path = tmp_path / "backends"
    backends_root_path.mkdir(parents=True)

    def get_conf(self, option, default=None, section=None):
        if option == "environments_path":
            return str(backends_root_path)
        else:
            try:
                _, config_default_values = CONF_DEFAULTS[0]
                return config_default_values[option]
            except KeyError:
                return None

    monkeypatch.setattr(SpyderEnvManagerWidget, "get_conf", get_conf)

    # Setup plugin
    plugin = SpyderEnvManager(parent=window, configuration=CONF)
    window.setCentralWidget(plugin.get_widget())
    window.show()

    yield plugin

    # Wait for pending operations and close
    qtbot.waitUntil(
        lambda: plugin.get_widget().actions_enabled,
        timeout=OPERATION_TIMEOUT,
    )
    plugin.get_widget().close()
    window.close()


@pytest.fixture
def spyder_env_manager(tmp_path, qtbot, monkeypatch):
    # Mocking mainwindow, get_config and CONF
    window = MainMock()
    backends_root_path = tmp_path / "backends"
    backends_root_path.mkdir(parents=True)

    def get_conf(self, option, default=None, section=None):
        if option == "environments_path":
            return str(backends_root_path)
        else:
            try:
                _, config_default_values = CONF_DEFAULTS[0]
                return config_default_values[option]
            except KeyError:
                return None

    monkeypatch.setattr(SpyderEnvManagerWidget, "get_conf", get_conf)

    # Setup plugin
    plugin = SpyderEnvManager(parent=window, configuration=Mock())
    window.setCentralWidget(plugin.get_widget())
    window.show()

    yield plugin

    # Wait for pending operations and close
    qtbot.waitUntil(
        lambda: plugin.get_widget().actions_enabled,
        timeout=OPERATION_TIMEOUT,
    )
    plugin.get_widget().close()
    window.close()


# ---- Tests
# ------------------------------------------------------------------------
def test_plugin_initial_state(spyder_env_manager):
    """
    Check plugin initialization and that actions and widgets have the
    correct state when initialized.
    """
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
        SpyderEnvManagerWidgetActions.ToggleExcludeDependency,
        SpyderEnvManagerWidgetActions.ToggleEnvironmentAsCustomInterpreter,
    ]
    for action_id, action in widget.get_actions().items():
        if action_id in disabled_actions_ids:
            assert not action.isEnabled()
        else:
            assert action.isEnabled()


def test_environment_creation_and_deletion(spyder_env_manager, qtbot, caplog):
    """Test creating and deleting an environment."""
    caplog.set_level(logging.DEBUG)
    widget = spyder_env_manager.get_widget()

    # Create environment
    def handle_environment_creation_dialog():
        dialog = widget.findChild(CustomParametersDialog)
        dialog.lineedit_string.setText("test_env")
        dialog.combobox_edit.setCurrentText("3.8.16")
        dialog.accept()

    QTimer.singleShot(2000, handle_environment_creation_dialog)
    widget._message_new_environment()

    qtbot.waitUntil(
        lambda: widget.stack_layout.currentWidget() == widget.packages_table,
        timeout=OPERATION_TIMEOUT,
    )
    assert widget.select_environment.currentText() == "test_env"
    qtbot.waitUntil(
        lambda: widget.packages_table.source_model.rowCount() == 2,
        timeout=OPERATION_TIMEOUT,
    )

    # Delete environment
    widget._run_action_for_env(
        dialog=None, action=SpyderEnvManagerWidgetActions.DeleteEnvironment
    )

    qtbot.waitUntil(
        lambda: widget.stack_layout.currentWidget() == widget.infowidget,
        timeout=OPERATION_TIMEOUT,
    )
    assert widget.select_environment.currentData() is None


def test_environment_import(spyder_env_manager, qtbot, caplog):
    """Test importing an environment from a file."""
    caplog.set_level(logging.DEBUG)
    widget = spyder_env_manager.get_widget()

    def handle_environment_import_dialog():
        dialog = widget.findChild(CustomParametersDialog)
        dialog.lineedit_string.setText("test_env_import")
        dialog.file_combobox.combobox.lineEdit().setText(IMPORT_FILE_PATH)
        dialog.accept()

    QTimer.singleShot(2000, handle_environment_import_dialog)
    widget._message_import_environment()

    qtbot.waitUntil(
        lambda: widget.stack_layout.currentWidget() == widget.packages_table,
        timeout=OPERATION_TIMEOUT,
    )
    assert widget.select_environment.currentText() == "test_env_import"
    qtbot.waitUntil(
        lambda: widget.packages_table.source_model.rowCount() == 3,
        timeout=OPERATION_TIMEOUT,
    )


def test_environment_package_installation(spyder_env_manager, qtbot, caplog):
    """Test creating an environment and installing a package on it."""
    caplog.set_level(logging.DEBUG)
    widget = spyder_env_manager.get_widget()

    # Create environment
    create_dialog = Mock()
    create_dialog.combobox = combobox_mock = Mock()
    combobox_mock.currentText = Mock(return_value="conda-like")
    create_dialog.lineedit_string = lineedit_string_mock = Mock()
    lineedit_string_mock.text = Mock(return_value="test_env")
    create_dialog.combobox_edit = combobox_edit_mock = Mock()
    combobox_edit_mock.currentText = Mock(return_value="3.9.16")

    assert create_dialog.combobox.currentText() == "conda-like"
    assert create_dialog.lineedit_string.text() == "test_env"
    assert create_dialog.combobox_edit.currentText() == "3.9.16"

    widget._run_action_for_env(
        dialog=create_dialog, action=SpyderEnvManagerWidgetActions.NewEnvironment
    )

    qtbot.waitUntil(
        lambda: widget.stack_layout.currentWidget() == widget.packages_table,
        timeout=OPERATION_TIMEOUT,
    )
    assert widget.select_environment.currentText() == "test_env"
    qtbot.waitUntil(
        lambda: widget.packages_table.source_model.rowCount() == 2,
        timeout=OPERATION_TIMEOUT,
    )

    # Install package in environment
    install_dialog = Mock()
    install_dialog.lineedit_string = lineedit_string_mock = Mock()
    lineedit_string_mock.text = Mock(return_value="packaging")
    install_dialog.combobox = combobox_mock = Mock()
    combobox_mock.currentText = Mock(return_value="==")
    install_dialog.lineedit_version = lineedit_version_mock = Mock()
    lineedit_version_mock.text = Mock(return_value="22.0")

    assert install_dialog.lineedit_string.text() == "packaging"
    assert install_dialog.combobox.currentText() == "=="
    assert install_dialog.lineedit_version.text() == "22.0"

    widget._run_action_for_env(
        dialog=install_dialog, action=SpyderEnvManagerWidgetActions.InstallPackage
    )

    qtbot.waitUntil(
        lambda: widget.packages_table.source_model.rowCount() == 3,
        timeout=OPERATION_TIMEOUT,
    )
    assert widget.packages_table.get_package_info(0)["name"] == "packaging"
    assert widget.packages_table.get_package_info(0)["version"] == "22.0"
