# SPDX-FileCopyrightText: 2022-present Spyder Development Team and envs-manager contributors
#
# SPDX-License-Identifier: MIT


def _jupyter_server_extension_points():
    """
    Returns a list of dictionaries with metadata describing
    where to find the `_load_jupyter_server_extension` function.
    """
    from envs_manager.jupyter import EnvManagerApp

    return [{"module": "envs_manager.jupyter", "app": EnvManagerApp}]
