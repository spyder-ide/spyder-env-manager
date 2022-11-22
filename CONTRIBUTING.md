# Contributing

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs on the [issue tracker](https://github.com/spyder-ide/spyder-env-manager/issues).

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

### Write Documentation

Spyder Env Manager could always use more documentation, whether as part of the
official Spyder Env Manager docs, in docstrings, or even on the web in blog posts,
articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue on the [issue tracker](https://github.com/spyder-ide/spyder-env-manager/issues).

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

## Get Started

Ready to contribute? Here's how to set up `Spyder Env Manager` for local development.

1. Fork the `spyder-env-manager` repo on GitHub.
2. Clone your fork locally:

```bash
git clone git@github.com:your_name_here/spyder-env-manager.git
cd spyder-env-manager/
```

3. Install your local copy into a conda environment:

```bash
conda create -n spyder-env-manager -c conda-forge python=3.9
conda activate spyder-env-manager
pip install -e .
```

4. Install testing dependencies:

```bash
pip install -r requirements/tests.txt
```

4. Setup pre-commit:

```bash
pip install pre-commit
pre-commit install
```

5. Create a branch for local development:

```bash
git checkout -b name-of-your-bugfix-or-feature
```

Now you can make your changes locally.

6. When you're done making changes, check that your changes pass the tests, including testing other Python versions:

```bash
pytest -vv -x spyder_env_manager
```

7. Commit your changes and push your branch to GitHub:

```bash
git add .
git commit -m "Your detailed description of your changes."
git push origin name-of-your-bugfix-or-feature
```

8. Submit a pull request through the GitHub website.

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 3.7+. Check
   https://github.com/spyder-ide/spyder-env-manager/pulls
   and make sure that the tests pass for all supported Python versions.

## Tips

To run a subset of tests:

```bash
pytest spyder_env_manager/tests/test_plugin.py
```

## Deploying

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in HISTORY.rst).
Then edit `spyder_env_manager/__init__.py` and update the plugin version and run:

```bash
git push
git push --tags
```

Github will then deploy to PyPI if tests pass.
