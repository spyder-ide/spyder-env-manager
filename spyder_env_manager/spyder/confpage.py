# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------
"""
Spyder Env Manager Preferences Page.
"""

# Third-party imports
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QGroupBox, QLabel, QVBoxLayout

# Spyder and local imports
from spyder.api.preferences import PluginConfigPage
from spyder.api.translations import get_translation

_ = get_translation("spyder_env_manager.spyder")


class SpyderEnvManagerConfigPage(PluginConfigPage):

    # --- PluginConfigPage API
    # ------------------------------------------------------------------------
    def setup_page(self):
        paths_group = QGroupBox(_("Paths"))
        conda_like_path_label = QLabel(_("Conda-like executable:"))
        conda_like_path_label.setToolTip(_("Path to the conda/micromamba executable"))
        conda_like_path_label.setWordWrap(True)

        conda_like_path = QLabel(self.get_option("conda_file_executable_path"))
        conda_like_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        conda_like_path.setWordWrap(True)

        environments_path_label = QLabel(_("Root directory for environments location:"))
        environments_path_label.setToolTip(
            _(
                "Path to the root directory where created and managed environments"
                " are located"
            )
        )
        environments_path_label.setWordWrap(True)

        environments_path = QLabel(self.get_option("environments_path"))
        environments_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        environments_path.setWordWrap(True)

        paths_layout = QVBoxLayout()
        paths_layout.addWidget(conda_like_path_label)
        paths_layout.addWidget(conda_like_path)
        paths_layout.addWidget(environments_path_label)
        paths_layout.addWidget(environments_path)
        paths_group.setLayout(paths_layout)

        layout = QVBoxLayout()
        layout.addWidget(paths_group)
        layout.addStretch(1)
        self.setLayout(layout)
