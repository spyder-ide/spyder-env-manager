## Instructions to release a new Spyder-env-manager version

To release a new version of spyder-env-manager (on PyPI and Conda-forge) follow these steps

### Prerequisites

In order to do a release, you need to have:

* An environment with the packages required to do the release (`loghub`, `pip`, `setuptools`, `twine`, `wheel`). If using `conda`, you can create a `release` environment with

      conda create -n release python=3.9
      conda activate release
      pip install -U pip setuptools twine wheel loghub

* A clone of this repository (usually your fork with an `upstream` remote pointing to the project original repo)

* The corresponding credentials (PyPI, GitHub, etc).

### PyPI

* Update local repo with

      git fetch upstream && git checkout main && git merge upstream/main

* Close the current [milestone on GitHub](https://github.com/spyder-ide/spyder-env-manager/milestones)

* Clean your local repo with (selecting option 1)

      git clean -xfdi

* Update `CHANGELOG.md` with

      loghub spyder-ide/spyder-env-manager -m vX.Y.Z

* Update `__version__` in `spyder/__init__.py` (set release version, remove `dev0`):

      git add . && git commit -m "Release X.Y.Z"

* Update the most important release packages with

      pip install -U pip setuptools twine wheel loghub

* Create source distribution and wheel with

      python -bb -X dev -W error -m build

* Check generated files with

      twine check --strict dist/*

* Upload generated files with

      twine upload dist/*

* Create release tag with

      git tag -a vX.Y.Z -m "Release X.Y.Z"

* Update `__version__` in `spyder/__init__.py` (add `dev0` and increment minor)

* Create `Back to work` commit with

      git add . && git commit -m "Back to work"

* Push changes and tag with

      git push upstream main && git push upstream --tags

* Create a [GitHub Release](https://github.com/spyder-ide/spyder-env-manager/releases) (`Draft a new release` and `Publish release`). You can use the `Auto generate release notes` as a base template for the release description and to that add a link to the Changelog (the new release related info).

### Conda-forge

* After doing the release on PyPI check for the `regro-cf-autotick-bot` automatic PR on the [Spyder-env-manager feedstock repo](https://github.com/conda-forge/spyder-env-manager-feedstock/pulls). Review it, check if any dependency or changes are needed and merge it.
