# History of changes

## Version 0.1.3 (2023-02-16)

### Issues Closed

* [Issue 27](https://github.com/spyder-ide/envs-manager/issues/27) - Prevent showing `print` statements when running programmatically ([PR 28](https://github.com/spyder-ide/envs-manager/pull/28) by [@dalthviz](https://github.com/dalthviz))

In this release 1 issue was closed.

### Pull Requests Merged

* [PR 29](https://github.com/spyder-ide/envs-manager/pull/29) - PR: Expose env Python executable path for all the backends, by [@dalthviz](https://github.com/dalthviz)
* [PR 28](https://github.com/spyder-ide/envs-manager/pull/28) - PR: Use `logging` module instead of `print`, by [@dalthviz](https://github.com/dalthviz) ([27](https://github.com/spyder-ide/envs-manager/issues/27))

In this release 2 pull requests were closed.


----


## Version 0.1.2 (2023-01-31)

### Pull Requests Merged

* [PR 26](https://github.com/spyder-ide/envs-manager/pull/26) - PR: Changes to environment packages listing and fix testing with micromamba 1.x, by [@dalthviz](https://github.com/dalthviz)
* [PR 25](https://github.com/spyder-ide/envs-manager/pull/25) - PR: Add list environments functionality per backend and don't remove env folder when deleting for conda-like backend, by [@dalthviz](https://github.com/dalthviz)
* [PR 24](https://github.com/spyder-ide/envs-manager/pull/24) - PR: Update README, by [@dalthviz](https://github.com/dalthviz)

In this release 3 pull requests were closed.


----


## Version 0.1.1 (2022-12-08)

### Issues Closed

* [Issue 13](https://github.com/spyder-ide/envs-manager/issues/13) - Add util function to manage `subprocess.run` calls between backends ([PR 23](https://github.com/spyder-ide/envs-manager/pull/23) by [@dalthviz](https://github.com/dalthviz))

In this release 1 issue was closed.

### Pull Requests Merged

* [PR 23](https://github.com/spyder-ide/envs-manager/pull/23) - PR: Refactor use of `subprocess.run`, by [@dalthviz](https://github.com/dalthviz) ([13](https://github.com/spyder-ide/envs-manager/issues/13))
* [PR 22](https://github.com/spyder-ide/envs-manager/pull/22) - PR: Add missing return and force kwarg to methods, by [@dalthviz](https://github.com/dalthviz)

In this release 2 pull requests were closed.


----


## Version 0.1.0 (2022-11-22)

### Issues Closed

* [Issue 17](https://github.com/spyder-ide/envs-manager/issues/17) - Add package dependency attribute ([PR 19](https://github.com/spyder-ide/envs-manager/pull/19) by [@dalthviz](https://github.com/dalthviz))
* [Issue 12](https://github.com/spyder-ide/envs-manager/issues/12) - Add more info when listing packages ([PR 18](https://github.com/spyder-ide/envs-manager/pull/18) by [@dalthviz](https://github.com/dalthviz))
* [Issue 10](https://github.com/spyder-ide/envs-manager/issues/10) - Add `list_environments` command ([PR 16](https://github.com/spyder-ide/envs-manager/pull/16) by [@dalthviz](https://github.com/dalthviz))
* [Issue 9](https://github.com/spyder-ide/envs-manager/issues/9) - Add `update` command for packages ([PR 15](https://github.com/spyder-ide/envs-manager/pull/15) by [@dalthviz](https://github.com/dalthviz))
* [Issue 8](https://github.com/spyder-ide/envs-manager/issues/8) - Import - Export behavior Conda vs Micromamba and tests with conda executable ([PR 14](https://github.com/spyder-ide/envs-manager/pull/14) by [@dalthviz](https://github.com/dalthviz))

In this release 5 issues were closed.

### Pull Requests Merged

* [PR 21](https://github.com/spyder-ide/envs-manager/pull/21) - PR: Add initial release instructions, by [@dalthviz](https://github.com/dalthviz)
* [PR 20](https://github.com/spyder-ide/envs-manager/pull/20) - PR: Update package name due to name collision with `envmanager` package, by [@dalthviz](https://github.com/dalthviz)
* [PR 19](https://github.com/spyder-ide/envs-manager/pull/19) - PR: Add attribute to keep track of packages whose installation was actually requested when listing them, by [@dalthviz](https://github.com/dalthviz) ([17](https://github.com/spyder-ide/envs-manager/issues/17))
* [PR 18](https://github.com/spyder-ide/envs-manager/pull/18) - PR: Add description info for listed packages and increase CI timeout to 20 min, by [@dalthviz](https://github.com/dalthviz) ([12](https://github.com/spyder-ide/envs-manager/issues/12))
* [PR 16](https://github.com/spyder-ide/envs-manager/pull/16) - PR: Initial implementation to pass name instead of full directory for environments and list environments command, by [@dalthviz](https://github.com/dalthviz) ([10](https://github.com/spyder-ide/envs-manager/issues/10))
* [PR 15](https://github.com/spyder-ide/envs-manager/pull/15) - PR: Add update packages command and refactor `executable`/`executable_path` attributtes, by [@dalthviz](https://github.com/dalthviz) ([9](https://github.com/spyder-ide/envs-manager/issues/9))
* [PR 14](https://github.com/spyder-ide/envs-manager/pull/14) - PR: Handle conda vs micromamba case to export envs and add testing jobs with conda executable, by [@dalthviz](https://github.com/dalthviz) ([8](https://github.com/spyder-ide/envs-manager/issues/8))
* [PR 11](https://github.com/spyder-ide/envs-manager/pull/11) - PR: Update create, delete, list commands and fix output management for uninstall, by [@dalthviz](https://github.com/dalthviz)
* [PR 5](https://github.com/spyder-ide/envs-manager/pull/5) - PR: Add initial import/export functionality and tests, by [@dalthviz](https://github.com/dalthviz)
* [PR 4](https://github.com/spyder-ide/envs-manager/pull/4) - PR: Install/uninstall logic improvements, mamba backend removal and workflows for Windows and MacOS, by [@dalthviz](https://github.com/dalthviz)
* [PR 3](https://github.com/spyder-ide/envs-manager/pull/3) - PR: Fix test workflow syntax and update README (CI, docs), by [@dalthviz](https://github.com/dalthviz)
* [PR 2](https://github.com/spyder-ide/envs-manager/pull/2) - PR: Initial package structure, CLI and interface ideas, by [@dalthviz](https://github.com/dalthviz)

In this release 12 pull requests were closed.
