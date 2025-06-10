# SPDX-FileCopyrightText: 2022-present Spyder Development Team and envs-manager contributors
#
# SPDX-License-Identifier: MIT

import os
from pathlib import Path
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
    (
        "pixi",
        [
            "pixi.toml",
            "Added python",
        ],
        "test_env",
        "python",
    ),
    (
        "conda-like",
        [
            "Transaction finished",
            "Executing transaction:",
            "Downloading and Extracting Packages:",
        ],
        "test_env",
        "python",
    ),
    ("venv", [""], "test_env", "pip"),
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

    env = os.environ.copy()
    if backend_value == "pixi":
        env["ENV_BACKEND_EXECUTABLE"] = str(
            Path(env.get("HOME")) / ".pixi" / "bin" / "pixi"
        )

    # Check environment creation
    create_output = subprocess.check_output(
        " ".join(
            ["envs-manager", f"-b={backend_value}", f"-e={list_env_result}", "create"]
        ),
        shell=True,
        env=env,
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
        env=env,
    )
    assert f"Using ENV_BACKEND: {backend_value}" not in str(list_env_output)
    assert list_env_result in str(list_env_output)

    # Check environment packages listing with debug logging level
    list_env_packages = subprocess.check_output(
        " ".join(
            [
                "envs-manager",
                f"-b={backend_value}",
                f"-e={list_env_result}",
                "-ll=10",
                "list",
            ]
        ),
        shell=True,
        env=env,
    )
    assert f"Using ENV_BACKEND: {backend_value}" in str(list_env_packages)
    assert package_list_env_result in str(list_env_packages)
