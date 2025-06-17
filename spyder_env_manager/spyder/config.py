# -*- coding: utf-8 -*-
#
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------

"""Spyder Env Manager default configuration."""

# Third-party imports
from envs_manager.manager import DEFAULT_BACKENDS_ROOT_PATH


CONF_SECTION = "spyder_env_manager"
CONF_DEFAULTS = [
    (
        CONF_SECTION,
        {
            "environments_path": str(DEFAULT_BACKENDS_ROOT_PATH),
            "selected_environment": "",
            "exclude_dependency_action": True,
            "environment_as_custom_interpreter": False,
        },
    ),
]

# IMPORTANT NOTES:
# 1. If you want to *change* the default value of a current option, you need to
#    do a MINOR update in config version, e.g. from 1.0.0 to 1.1.0
# 2. If you want to *remove* options that are no longer needed in our codebase,
#    or if you want to *rename* options, then you need to do a MAJOR update in
#    version, e.g. from 1.0.0 to 2.0.0
# 3. You don't need to touch this value if you're just adding a new option
CONF_VERSION = "1.0.0"
