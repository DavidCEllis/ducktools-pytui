# Ducktools: PyTUI #

A terminal based user interface for managing Python installs and virtual environments.

## Usage ##

The easiest way to install ducktools.pytui is as a tool from PyPI using `uv` or `pipx`.

`uv tool install ducktools-pytui` or `pipx install ducktools-pytui`

Run with `pytui` or `ducktools-pytui`.

## Example ##

![screenshot showing ducktools-pytui displaying a list of venvs and runtimes](images/pytui_menu.png)

## Features ##

* List Python Virtual Environments relative to the current folder
* List Python Runtimes discovered by [ducktools-pythonfinder](https://github.com/DavidCEllis/ducktools-pythonfinder)
* Launch a Terminal with a selected venv activated
  * Currently only 'tested' with bash, zsh (on macos), powershell and cmd.
  * It's possible shell config files may break the environment variable changes.
* Launch a REPL with the selected venv
* Launch a REPL with the selected runtime
* List installed packages in a venv (Python 3.9 or later)
* Create a venv from a specific runtime (Python 3.4 or later)
* Delete a selected venv

### Basic Configuration ###

Some configuration is available by editing the config.json file located here:

* Windows: `%LOCALAPPDATA%\ducktools\pytui\config.json`
* Linux/Mac/Other: `~/.config/ducktools/pytui/config.json`

### Config Values ###
* `venv_search_mode` - Where to search for VEnv folders
  * `"cwd"` - Search in the working directory only
  * `"parents"` - Search in the working directory and each parent folder (default)
  * `"recursive"` - Search in the working directory and subfolders recursively
  * `"recursive_parents"` - Combine the "recursive" and "parents" options (only the CWD is recursively searched)
* `fast_runtime_search` - Skip any potential Python runtimes that will require querying the interpreter (default: `False`)
  * This may make the start time faster in some cases, but will miss runtimes on PATH or alternate interpreters
* `include_pip` - Whether to include `pip` (and `setuptools` where appropriate) in created VEnvs (default: `True`)
* `latest_pip` - Download the latest `pip` for Python versions where it is available (default: `True`)

### Planned ###

* Allow selecting 'default' packages to install, auto-editable install option with extras
* Add commands to install/uninstall runtimes of tools with runtime managers (eg: UV, pyenv)
* Highlight invalid venvs

### Not Planned ###

* Handle PEP-723 inline scripts
  * `ducktools-env` is my project for managing these
  * Potentially that could gain a TUI, but I'm not sure I'd want to merge the two things
* Handle Conda environments
  * Conda environments are a completely separate ecosystem, 
    while everything this supports uses the standard PyPI ecosystem
  * Supporting Conda would basically require a whole separate parallel set of commands
* Manage `ducktools-pytui` specific runtimes
  * I don't want to add *yet another* place Python can be installed
  * `ducktools-pytui` is intended to help manage the chaos of Python runtime installs and environments, 
    not add a new dimension to it.
