# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------
"""
Spyder Env Manager plugin tests.
"""

# Local imports
from spyder_env_manager.spyder.widgets.main_widget import SpyderEnvManagerWidget


def test_env_manager(qtbot):
    """Create plugin widget and show it."""
    widget = SpyderEnvManagerWidget(None)
    widget.setup()
    qtbot.addWidget(widget)
    widget.show()
