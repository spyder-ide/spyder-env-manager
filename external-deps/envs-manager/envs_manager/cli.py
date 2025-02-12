# SPDX-FileCopyrightText: 2022-present Spyder Development Team and envs-manager contributors
#
# SPDX-License-Identifier: MIT

import argparse
import logging
import sys

from envs_manager.manager import (
    DEFAULT_BACKENDS_ROOT_PATH,
    DEFAULT_BACKEND,
    EXTERNAL_EXECUTABLE,
    Manager,
)


def main(args=None):
    for backend in Manager.BACKENDS.keys():
        (DEFAULT_BACKENDS_ROOT_PATH / backend / "envs").mkdir(
            parents=True, exist_ok=True
        )

    parser = argparse.ArgumentParser(
        prog=__name__,
        description="Manage a virtual Python " "environment in a target " "directory.",
    )
    parser.add_argument(
        "-b",
        "--backend",
        default=DEFAULT_BACKEND,
        choices=list(Manager.BACKENDS.keys()),
        help="The implementation to "
        "create/manage a virtual "
        "Python environment in the given "
        "directory.",
    )
    parser.add_argument(
        "-en",
        "--env-name",
        help="The name of a directory where the virtual environment is or will be locate."
        "The environment is/will be located at <BACKENDS_ROOT_PATH>/<ENV_BACKEND>/envs/<env name>.",
    )

    parser.add_argument(
        "-ll",
        "--logging-level",
        type=int,
        default=logging.INFO,
        help="The logging level to use.",
    )

    main_subparser = parser.add_subparsers(title="commands", dest="command")

    # Create env
    parser_create = main_subparser.add_parser(
        "create",
        help="Create a virtual Python environment in the target directory.",
    )
    parser_create.add_argument(
        "--packages", nargs="+", help="List of packages to install."
    )
    parser_create.add_argument(
        "--channels", nargs="+", help="List of channels from where to install."
    )

    # Delete env
    parser_delete = main_subparser.add_parser(
        "delete",
        help="Delete a virtual Python environment in the target directory.",
    )

    # Activate env
    parser_activate = main_subparser.add_parser(
        "activate",
        help="Activate the virtual Python environment in the target directory.",
    )

    # Deactivate env
    parser_deactivate = main_subparser.add_parser(
        "deactivate",
        help="Deactivate the virtual Python environment in the target directory.",
    )

    # Export env
    parser_export = main_subparser.add_parser(
        "export",
        help="Export a virtual Python environment in the target directory to a file.",
    )
    parser_export.add_argument(
        "export_file_path", help="File path to export the environment."
    )

    # Import env
    parser_import = main_subparser.add_parser(
        "import",
        help="Import a virtual Python environment in the target directory from a file.",
    )
    parser_import.add_argument(
        "import_file_path",
        help="File path from where to import the environment.",
    )

    # Install packages
    parser_install = main_subparser.add_parser(
        "install",
        help="Install packages in the "
        "virtual Python "
        "environment placed in the "
        "target directory.",
    )
    parser_install.add_argument(
        "packages", nargs="+", help="List of packages to install."
    )
    parser_install.add_argument(
        "--channels", nargs="+", help="List of channels from where to install."
    )

    # Uninstall packages
    parser_uninstall = main_subparser.add_parser(
        "uninstall",
        help="Uninstall packages in the "
        "virtual Python "
        "environment placed in the "
        "target directory.",
    )
    parser_uninstall.add_argument(
        "packages", nargs="+", help="List of packages to uninstall."
    )

    # Update packages
    parser_update = main_subparser.add_parser(
        "update",
        help="Update packages in the "
        "virtual Python "
        "environment placed in the "
        "target directory.",
    )
    parser_update.add_argument(
        "packages", nargs="+", help="List of packages to update."
    )

    # List packages
    parser_list = main_subparser.add_parser(
        "list",
        help="List packages available in the "
        "virtual Python "
        "environment placed in the "
        "target directory.",
    )

    # List environments
    parser_list_environments = main_subparser.add_parser(
        "list-environments",
        help="List discoverable environments available with the current configuration.",
    )

    options = parser.parse_args(args)

    # Setup logging
    logging.basicConfig(
        level=options.logging_level,
        format="%(message)s",
        handlers=[logging.StreamHandler(stream=sys.stdout)],
    )
    logger = logging.getLogger("envs-manager")

    logger.debug(options)
    logger.debug(f"Using BACKENDS_ROOT_PATH: {DEFAULT_BACKENDS_ROOT_PATH}")
    logger.debug(f"Using ENV_BACKEND: {options.backend}")
    logger.debug(f"Using ENV_BACKEND_EXECUTABLE: {EXTERNAL_EXECUTABLE}")
    if options.env_name:
        manager = Manager(
            backend=options.backend,
            env_name=options.env_name,
            root_path=DEFAULT_BACKENDS_ROOT_PATH,
            external_executable=EXTERNAL_EXECUTABLE,
        )
        if options.command == "create":
            manager.create_environment(
                packages=options.packages or ["python"], channels=options.channels
            )
        elif options.command == "delete":
            manager.delete_environment()
        elif options.command == "activate":
            manager.activate()
        elif options.command == "deactivate":
            manager.deactivate()
        elif options.command == "export":
            manager.export_environment(options.export_file_path)
        elif options.command == "import":
            manager.import_environment(options.import_file_path)
        elif options.command == "install":
            manager.install(packages=options.packages)
        elif options.command == "uninstall":
            manager.uninstall(packages=options.packages)
        elif options.command == "update":
            manager.update(packages=options.packages)
        elif options.command == "list":
            manager.list()
    if options.command == "list-environments":
        if options.backend:
            Manager.list_environments(
                backend=options.backend, external_executable=EXTERNAL_EXECUTABLE
            )
        else:
            Manager.list_environments(external_executable=EXTERNAL_EXECUTABLE)
