# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------
"""
Spyder Env Manager ConfigPage tests.
"""

# Third-party library imports
import pytest

# Spyder imports
from spyder.plugins.preferences.widgets.configdialog import ConfigDialog

# Local imports
from spyder_env_manager.spyder.confpage import SpyderEnvManagerConfigPage
from spyder_env_manager.tests.test_plugin import spyder_env_manager


def test_config(spyder_env_manager, qtbot):
    """Test that config page can be created and shown."""
    dlg = ConfigDialog()
    page = SpyderEnvManagerConfigPage(
        spyder_env_manager, parent=spyder_env_manager.main
    )
    page.initialize()
    dlg.add_page(page)
    qtbot.addWidget(dlg)
    dlg.show()
    # no assert, just check that the config page can be created


if __name__ == "__main__":
    pytest.main()
