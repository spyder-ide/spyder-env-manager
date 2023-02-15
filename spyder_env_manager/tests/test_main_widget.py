# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------
"""
Spyder Env Manager main widget tests.
"""

# Local imports
from spyder_env_manager.spyder.widgets.main_widget import SpyderEnvManagerWidget


def test_env_manager(qtbot, tmp_path, monkeypatch):
    """Create plugin widget and show it."""
    backends_root_path = tmp_path / "backends"
    backends_root_path.mkdir(parents=True)

    def get_conf(self, option, default=None, section=None):
        if option == "environments_path":
            return str(backends_root_path)
        else:
            return default

    monkeypatch.setattr(SpyderEnvManagerWidget, "get_conf", get_conf)
    SpyderEnvManagerWidget.CONF_SECTION = "spyder_env_manager"

    widget = SpyderEnvManagerWidget("spyder_env_manager", None)
    qtbot.addWidget(widget)
    widget.setup()
    widget.show()
