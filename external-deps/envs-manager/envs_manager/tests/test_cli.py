# SPDX-FileCopyrightText: 2022-present Spyder Development Team and envs-manager contributors
#
# SPDX-License-Identifier: MIT

import os
import subprocess

import pytest


SUBCOMMANDS = [
    "",
    "create",
    "delete",
    "activate",
    "deactivate",
    "export",
    "import",
    "install",
    "uninstall",
    "update",
    "list",
    "list-environments",
]

BACKENDS = [
    ("venv", [""], "test_env", "pip"),
    (
        "conda-like",
        ["Transaction finished", "Executing transaction: ...working... done"],
        "test_env",
        "python",
    ),
]


@pytest.mark.parametrize("subcommand", SUBCOMMANDS)
def test_cli_help(subcommand):
    if subcommand:
        subprocess.run(
            ["envs-manager", subcommand, "--help"],
            check=True,
        )
    else:
        subprocess.run(
            ["envs-manager", "--help"],
            check=True,
        )


@pytest.mark.parametrize("backend", BACKENDS)
def test_cli(tmp_path, backend):
    backend_value, create_result, list_env_result, package_list_env_result = backend
    backends_root_path = tmp_path / "backends"
    backends_root_path.mkdir(parents=True)
    os.environ["BACKENDS_ROOT_PATH"] = str(backends_root_path)

    # Check environment creation
    create_output = subprocess.check_output(
        " ".join(
            ["envs-manager", f"-b={backend_value}", f"-en={list_env_result}", "create"]
        ),
        shell=True,
    )
    assert any(
        [
            expected_create_result in str(create_output)
            for expected_create_result in create_result
        ]
    )
    assert f"Using ENV_BACKEND: {backend_value}" not in str(create_output)

    # Check environment listing
    list_env_output = subprocess.check_output(
        " ".join(
            [
                "envs-manager",
                f"-b={backend_value}",
                "list-environments",
            ]
        ),
        shell=True,
    )
    assert f"Using ENV_BACKEND: {backend_value}" not in str(list_env_output)
    assert list_env_result in str(list_env_output)

    # Check environment packages listing with debug logging level
    list_env_packages = subprocess.check_output(
        " ".join(
            [
                "envs-manager",
                f"-b={backend_value}",
                f"-en={list_env_result}",
                "-ll=10",
                "list",
            ]
        ),
        shell=True,
    )
    assert f"Using ENV_BACKEND: {backend_value}" in str(list_env_packages)
    assert package_list_env_result in str(list_env_packages)
