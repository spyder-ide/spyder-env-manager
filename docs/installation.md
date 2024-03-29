# Installation

## Stable release

To install Spyder Env Manager, run this command in your terminal:

```bash
conda install -c conda-forge spyder-env-manager
```

This is the preferred method to install Spyder Env Manager, as it will always install the most recent stable release.

Or with `pip`

```bash
pip install spyder-env-manager
```

Note that for the moment you need to have `conda` installed for the plugin to work, so even when installing with `pip`, `conda`also needs to be available

## From sources

The sources for Spyder Env Manager can be downloaded from the [Github repo](https://github.com/spyder-ide/spyder-env-manager).

You can either clone the public repository:

```bash
git clone git://github.com/spyder-ide/spyder-env-manager
```

Or download the [tarball](https://github.com/spyder-ide/spyder-env-manager/tarball/main):

```bash
curl -OJL https://github.com/spyder-ide/spyder-env-manager/tarball/main
```

Once you have a copy of the source, you can install it with:

```bash
pip install -e .
```
