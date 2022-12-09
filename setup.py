# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2022, Spyder Development Team and spyder-env-manager contributors
#
# Licensed under the terms of the MIT license
# ----------------------------------------------------------------------------
"""
Spyder Env Manager setup.
"""
from setuptools import find_packages, setup

from spyder_env_manager import __version__

setup(
    # See: https://setuptools.readthedocs.io/en/latest/setuptools.html
    name="spyder-env-manager",
    version=__version__,
    author="Spyder Development Team and spyder-env-manager contributors",
    author_email="spyder.python@gmail.com",
    description="Spyder 5+ plugin to manage Python virtual environments and packages",
    license="MIT license",
    url="https://github.com/spyder-ide/spyder-env-manager",
    python_requires=">= 3.7",
    install_requires=[
        "envs-manager>=0.1.1",
        "qtpy",
        "qtawesome",
        "spyder>=5.4.0",
    ],
    packages=find_packages(),
    entry_points={
        "spyder.plugins": [
            "spyder_env_manager = spyder_env_manager.spyder.plugin:SpyderEnvManager"
        ],
    },
    classifiers=[
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering",
    ],
)
