# Ducktools: PyTUI #

A terminal based user interface for managing Python installs and virtual environments.

## Usage ##

The easiest way to install ducktools.pytui is as a tool from PyPI using `uv` or `pipx`.

`uv tool install ducktools-pytui` or `pipx install ducktools-pytui`

Run with `pytui` or `ducktools-pytui`.

There is also now a zipapp available on 
[the releases page](https://github.com/DavidCEllis/ducktools-pytui/releases/latest)
and should be usable as long as you have Python 3.10 or newer.

## Example ##

![screenshot showing ducktools-pytui displaying a list of venvs and runtimes](images/pytui_menu.png)

## Features ##

* List Python Virtual Environments relative to the current folder
* List Python Runtimes discovered by [ducktools-pythonfinder](https://github.com/DavidCEllis/ducktools-pythonfinder)
* Launch a Terminal with a selected venv activated
  * Currently only 'tested' with bash (and limited git bash on Windows), zsh (on macos), powershell and cmd
  * Other shells will almost certainly break the environment variable changes
  * This isn't the standard `activate` script, as it puts PyTUI in the background and launches a new shell
  * Use `exit` to close the shell and return to PyTUI
* Launch a REPL with the selected venv
* Launch a REPL with the selected runtime
* List installed packages in a venv (Python 3.9 or later)
* Create a venv from a specific runtime in the working directory or a global folder (Python 3.4 or later)
* Delete a selected venv
* Install a runtime (Requires UV installed and on PATH)
* Uninstall a runtime (UV runtimes only)

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
* `include_pip` - Whether to include `pip` (and `setuptools` where appropriate) in created VEnvs (default: `True`)
* `latest_pip` - Download the latest `pip` for Python versions where it is available (default: `True`)
* `global_venv_folder` - The folder to use for global pytui venvs, `~/.local/share/ducktools/pytui/venvs` by default

### Possible Extras ###

* Support other common shells
* Highlight broken venvs where the base install no longer exists

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
