# envs-manager

## Project information
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/envs-manager.svg)](https://pypi.org/project/envs-manager)

[![PyPI - Version](https://img.shields.io/pypi/v/envs-manager.svg)](https://pypi.org/project/envs-manager)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/envs-manager)](https://pypi.org/project/envs-manager)

[![conda - version](https://img.shields.io/conda/vn/conda-forge/envs-manager.svg)](https://www.anaconda.org/conda-forge/envs-manager)
[![conda - Downloads](https://img.shields.io/conda/dn/conda-forge/envs-manager.svg)](https://www.anaconda.org/conda-forge/envs-manager)

## Build status
[![Windows status](https://github.com/spyder-ide/envs-manager/workflows/Windows%20tests/badge.svg)](https://github.com/spyder-ide/envs-manager/actions?query=workflow%3A%22Windows+tests%22)
[![Linux status](https://github.com/spyder-ide/envs-manager/workflows/Linux%20tests/badge.svg)](https://github.com/spyder-ide/envs-manager/actions?query=workflow%3A%22Linux+tests%22)
[![MacOS status](https://github.com/spyder-ide/envs-manager/workflows/Macos%20tests/badge.svg)](https://github.com/spyder-ide/envs-manager/actions?query=workflow%3A%22Macos+tests%22)
[![codecov](https://codecov.io/gh/spyder-ide/envs-manager/branch/main/graph/badge.svg?token=H2GZWHIL43)](https://codecov.io/gh/spyder-ide/envs-manager)

-----

**Table of Contents**

- [Installation](#installation)
    - [PyPI](#pypi)
    - [Conda](#conda)
- [Development](#development)
- [License](#license)

## Installation

### PyPI

```console
pip install envs-manager
```

### Conda

```console
conda install -c conda-forge envs-manager
```

## Development

* Fork and clone the repo. To clone:

```console
git clone <link to your fork.git>
cd envs-manager
```

* Create a Python environment and activate it. For example with conda:

```console
conda env create -n envs-manager --file requirements/environment.yml
conda activate envs-manager
```

* Install development version:

```console
pip install -e .
```

* Setup pre-commit:

```console
pre-commit install
```

* To run the test suite:

You will need to setup the `ENV_BACKEND_EXECUTABLE` environmental variable in order to use a `conda-like` manager. This environment variable should point to a conda or mamba executable. For example, if you have micromamba downloaded on Windows you should set `ENV_BACKEND_EXECUTABLE=<path to micromamba executable>/micromamba.exe`. After that you should be able to run our tests with:

```console
pytest -vv
```

* To check the command line options you need to run:

```console
envs-manager --help
```

## License

`envs-manager` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
