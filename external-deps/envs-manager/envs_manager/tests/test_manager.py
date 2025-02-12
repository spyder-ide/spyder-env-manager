# SPDX-FileCopyrightText: 2022-present Spyder Development Team and envs-manager contributors
#
# SPDX-License-Identifier: MIT

import os
from pathlib import Path
import time
import subprocess
import sys

import pytest

from envs_manager.manager import Manager


TESTS_DIR = Path(__file__).parent.absolute()
ENV_FILES = TESTS_DIR / "env_files"
ENV_FILES_CONDA_LIKE = ENV_FILES / "conda-like-files"
ENV_FILES_VENV = ENV_FILES / "venv-files"
MANAGER_BACKENDS_SETUP = [
    ("venv", None, None),
    ("conda-like", os.environ.get("ENV_BACKEND_EXECUTABLE"), None),
]
BACKENDS = [
    (
        ("venv", None, None),
        "pip",
        ["packaging==21.0"],
        ["packaging"],
        ["foo"],
        (
            ["Could not find a version that satisfies the requirement foo"],
            ["Could not find a version that satisfies the requirement foo"],
            ["WARNING: Skipping foo as it is not installed"],
        ),
        # Key returned by list call, Number of packages returned, Number of properties returned per package, Package description
        [2, 1, 6, "The PyPA recommended tool for installing Python packages."],
    ),
    (
        ("venv", None, "test_env"),
        "pip",
        ["packaging==21.0"],
        ["packaging"],
        ["foo"],
        (
            ["Could not find a version that satisfies the requirement foo"],
            ["Could not find a version that satisfies the requirement foo"],
            ["WARNING: Skipping foo as it is not installed"],
        ),
        # Key returned by list call, Number of packages returned, Number of properties returned per package, Package description
        [2, 1, 6, "The PyPA recommended tool for installing Python packages."],
    ),
    (
        ("conda-like", os.environ.get("ENV_BACKEND_EXECUTABLE"), None),
        "python",
        ["packaging=21.0"],
        ["packaging"],
        ["foo"],
        (
            ["libmamba Could not solve for environment specs", "PackagesNotFoundError"],
            ["All requested packages already installed", "PackageNotInstalledError"],
            [
                "Nothing to do",
                "Failure: packages to remove not found in the environment",
                "PackagesNotFoundError",
            ],
        ),
        # Key returned by list call, Number of packages returned, Number of properties returned per package, Package description
        [2, 1, 6, "General purpose programming language"],
    ),
    (
        ("conda-like", os.environ.get("ENV_BACKEND_EXECUTABLE"), "test_env"),
        "python",
        ["packaging=21.0"],
        ["packaging"],
        ["foo"],
        (
            ["libmamba Could not solve for environment specs", "PackagesNotFoundError"],
            ["All requested packages already installed", "PackageNotInstalledError"],
            [
                "Nothing to do",
                "Failure: packages to remove not found in the environment",
                "PackagesNotFoundError",
            ],
        ),
        # Number of keys returned by list call, Number of packages returned, Number of properties returned per package, Package description
        [2, 1, 6, "General purpose programming language"],
    ),
]


if os.name == "nt":
    BASE_IMPORT_EXPORT_FILENAME = "win"
elif sys.platform.startswith("linux"):
    BASE_IMPORT_EXPORT_FILENAME = "linux"
else:
    BASE_IMPORT_EXPORT_FILENAME = "macos"

IMPORT_EXPORT_BACKENDS = [
    (
        ("venv", None, None),
        str(ENV_FILES_VENV / "venv_import_env.txt"),
        str(ENV_FILES_VENV / "venv_export_env.txt"),
    ),
    (
        ("venv", None, "test_env"),
        str(ENV_FILES_VENV / "venv_import_env.txt"),
        str(ENV_FILES_VENV / "venv_export_env.txt"),
    ),
    (
        ("conda-like", os.environ.get("ENV_BACKEND_EXECUTABLE"), None),
        str(
            ENV_FILES_CONDA_LIKE / f"{BASE_IMPORT_EXPORT_FILENAME}_conda_import_env.yml"
        ),
        str(
            ENV_FILES_CONDA_LIKE / f"{BASE_IMPORT_EXPORT_FILENAME}_conda_export_env.yml"
        ),
    ),
    (
        ("conda-like", os.environ.get("ENV_BACKEND_EXECUTABLE"), "test_env"),
        str(
            ENV_FILES_CONDA_LIKE / f"{BASE_IMPORT_EXPORT_FILENAME}_conda_import_env.yml"
        ),
        str(
            ENV_FILES_CONDA_LIKE / f"{BASE_IMPORT_EXPORT_FILENAME}_conda_export_env.yml"
        ),
    ),
]


def wait_until(condition, interval=0.1, timeout=1, **kwargs):
    start = time.time()
    while not condition(**kwargs) and time.time() - start < timeout:
        time.sleep(interval)
    assert condition(**kwargs)


def package_installed(manager_instance, installed_packages):
    list_result, package_list = manager_instance.list()
    assert list_result
    for package in installed_packages:
        packages_names = [package["name"] for package in package_list["packages"]]
        return package.split("=")[0] in packages_names


def packages_uninstalled(manager_instance, installed_packages):
    list_result, package_list = manager_instance.list()
    assert list_result
    for package in installed_packages:
        packages_names = [package["name"] for package in package_list["packages"]]
        return package not in packages_names


def check_packages(manager_instance, package, version):
    list_result, packages_list = manager_instance.list()
    assert list_result
    packages_info = [
        (package["name"], package["version"]) for package in packages_list["packages"]
    ]
    return (package, version) in packages_info


@pytest.fixture
def manager_instance(request, tmp_path):
    backend, executable, env_name = request.param
    if not env_name:
        # Passing full env directory
        root_path = None
        envs_directory = tmp_path / "envs"
        env_directory = envs_directory / f"test_{backend}"
        if backend == "conda-like":
            envs_directory.mkdir(parents=True)
        else:
            env_directory.mkdir(parents=True)
    else:
        # Pass root_path and env_name letting manager create env directory path
        root_path = tmp_path
        env_directory = None

    manager_instance = Manager(
        backend,
        root_path=root_path,
        env_name=env_name,
        env_directory=env_directory,
        external_executable=executable,
    )
    yield manager_instance
    manager_instance.delete_environment()


@pytest.mark.parametrize(
    "manager_instance",
    MANAGER_BACKENDS_SETUP,
    indirect=["manager_instance"],
)
def test_manager_backends_python_executable(manager_instance, capsys):
    # Create an environment with Python in it
    with capsys.disabled():
        create_result, _ = manager_instance.create_environment(
            packages=["python==3.10"], force=True
        )
    assert create_result

    # Get Python Zen with the Python executable from the environment
    python_executable = manager_instance.backend_instance.python_executable_path
    python_output = subprocess.check_output(
        " ".join([python_executable, "-c", '"import this"']), shell=True, text=True
    )
    assert "Now is better than never." in python_output


@pytest.mark.parametrize(
    "manager_instance,initial_package,installed_packages,updated_packages,errored_packages,messages,list_info",
    BACKENDS,
    indirect=["manager_instance"],
)
def test_manager_backends(
    manager_instance,
    initial_package,
    installed_packages,
    updated_packages,
    errored_packages,
    messages,
    list_info,
    capsys,
):
    # Create an environment with Python in it
    with capsys.disabled():
        create_result, _ = manager_instance.create_environment(
            packages=["python==3.10"], force=True
        )
    assert create_result

    # List packages and check correct list result dimensions
    list_result, initial_list = manager_instance.list()
    assert list_result
    package_info = None
    for package in initial_list["packages"]:
        if package["name"] == initial_package:
            package_info = package
    assert package_info
    (
        list_info_number,
        package_number,
        package_info_number,
        package_description,
    ) = list_info
    assert len(initial_list) == list_info_number
    assert len(initial_list["packages"]) > package_number
    assert len(package_info) == package_info_number
    assert package_info["description"] == package_description

    # Install a new package in the created environment
    with capsys.disabled():
        install_result, _ = manager_instance.install(
            packages=installed_packages, force=True
        )
    assert install_result

    # Check package was installed
    wait_until(
        package_installed,
        manager_instance=manager_instance,
        installed_packages=installed_packages,
    )

    # Update installed package
    with capsys.disabled():
        update_result, _ = manager_instance.update(
            packages=updated_packages, force=True
        )
    assert update_result

    # Uninstall the new package
    with capsys.disabled():
        uninstall_result, _ = manager_instance.uninstall(
            packages=installed_packages, force=True
        )
    assert uninstall_result

    # Check package was uninstalled
    wait_until(
        packages_uninstalled,
        manager_instance=manager_instance,
        installed_packages=installed_packages,
    )

    (
        install_error_messages,
        update_warning_messages,
        uninstall_warning_messages,
    ) = messages
    # Try to install unexisting package
    with capsys.disabled():
        install_error_result, install_error_message = manager_instance.install(
            packages=errored_packages, force=True
        )
    assert not install_error_result
    assert any(
        [
            install_expected_error in install_error_message
            for install_expected_error in install_error_messages
        ]
    )

    # Try to update unexisting package
    with capsys.disabled():
        update_error_result, update_error_message = manager_instance.update(
            packages=errored_packages, force=True, capture_output=True
        )
    print(update_error_message)
    assert not update_error_result
    assert any(
        [
            update_expected_error in update_error_message
            for update_expected_error in update_warning_messages
        ]
    )

    # Try to uninstall unexisting package
    with capsys.disabled():
        (
            uninstall_warning_result,
            uninstall_warning_message,
        ) = manager_instance.uninstall(
            packages=errored_packages, force=True, capture_output=True
        )
    print(uninstall_warning_message)
    assert uninstall_warning_result
    assert any(
        [
            uninstall_expected_error in uninstall_warning_message.stdout
            or uninstall_expected_error in uninstall_warning_message.stderr
            for uninstall_expected_error in uninstall_warning_messages
        ]
    )


@pytest.mark.parametrize(
    "manager_instance,initial_import_path,expected_export_path",
    IMPORT_EXPORT_BACKENDS,
    indirect=["manager_instance"],
)
def test_manager_backends_import_export(
    manager_instance, initial_import_path, expected_export_path, tmp_path, capsys
):
    # Import environment definition
    with capsys.disabled():
        import_result, import_menssage = manager_instance.import_environment(
            initial_import_path, force=True
        )
    print(import_menssage)
    assert import_result
    wait_until(
        check_packages,
        manager_instance=manager_instance,
        package="packaging",
        version="21.3",
    )

    # Install packaging 21.0
    channels = None
    if manager_instance.backend_instance.ID == "conda-like":
        channels = ["conda-forge"]
    with capsys.disabled():
        install_result, install_message = manager_instance.install(
            ["packaging==21.0"], channels=channels, force=True, capture_output=True
        )
    print(install_message)
    assert install_result

    # Wait until package is installed
    wait_until(
        check_packages,
        manager_instance=manager_instance,
        package="packaging",
        version="21.0",
    )

    # Export environment and check if is the expected one
    export_path_dir = tmp_path / "exported"
    export_path_dir.mkdir()
    if manager_instance.backend_instance.ID == "venv":
        export_path_file = export_path_dir / "exported_file.txt"
    else:
        export_path_file = export_path_dir / "exported_file.yml"

    with capsys.disabled():
        export_result, export_message = manager_instance.export_environment(
            str(export_path_file)
        )
    print(export_message)
    assert export_result
    assert export_path_file.exists()

    with open(expected_export_path) as expected_export_path_file:
        expected_export = set()
        for expected_line in expected_export_path_file.readlines():
            if (
                "=" in expected_line
                and "ca-certificates" not in expected_line
                and "openssl" not in expected_line
            ):
                expected_export.add(expected_line.strip())

    with open(export_path_file) as generated_export_path_file:
        generated_export = set()
        for generated_line in generated_export_path_file.readlines():
            if (
                "=" in generated_line
                and "ca-certificates" not in generated_line
                and "openssl" not in generated_line
            ):
                generated_export.add(generated_line.strip())

    assert generated_export == expected_export
