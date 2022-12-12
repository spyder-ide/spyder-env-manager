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


def test_env_manager(qtbot):
    """Create plugin widget and show it."""
    SpyderEnvManagerWidget.CONF_SECTION = "spyder_env_manager"
    widget = SpyderEnvManagerWidget(None)
    widget.setup()
    widget.show()
