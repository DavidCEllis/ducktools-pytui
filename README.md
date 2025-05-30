# Ducktools: PyTUI #

A terminal based user interface for managing Python installs and virtual environments.

## Usage ##

The easiest way to install ducktools.pytui is as a tool from PyPI using `uv` or `pipx`.

`uv tool install ducktools-pytui` or `pipx install ducktools-pytui`

Run with `pytui` or `ducktools-pytui`.

There is also now a zipapp available on
[the releases page](https://github.com/DavidCEllis/ducktools-pytui/releases/latest)
and should be usable as long as you have Python 3.8 or newer.

## Screenshots ##

### Managing virtual environments ###

![screenshot showing ducktools-pytui displaying a list of venvs and runtimes](images/pytui_menu.png)

### Installing new runtimes ###

![screenshot showing ducktools-pytui displaying a list of available runtimes to install](images/pytui_runtimes.png)

### Listing packages installed in a virtual environment (3.9+ only) ###

![screenshot showing ducktools-pytui listing packages installed in a virtual environment](images/pytui_package_list.png)

## Features ##

* List Python Virtual Environments relative to the current folder alongside those installed in a
  configurable global folder
* List Python Runtimes discovered by [ducktools-pythonfinder](https://github.com/DavidCEllis/ducktools-pythonfinder)
* Launch a Terminal with a selected venv activated
  * Currently only fish, bash (and git bash on Windows), zsh, powershell and cmd are supported
    * zsh and cmd only have basic support
  * Use `exit` to close the shell and return to PyTUI
* Launch a REPL with the selected venv
* Launch a REPL with the selected runtime
* List installed packages in a venv (Python 3.9 or later)
* Create a venv from a specific runtime in the working directory or a global folder (Python 3.4 or later)
* Delete a selected venv
* Install a runtime (Requires either the Windows Python Manager or UV to be available)
* Uninstall a runtime (Only those managed by the Windows Python Manager or UV)

## Basic Configuration ##

Some configuration is available by editing the config.json file located here:

* Windows: `%LOCALAPPDATA%\ducktools\pytui\config.json`
* Non-Windows: `~/.config/ducktools/pytui/config.json`

Config can be seen and edited from the commandline with the `config` subcommand.

Some example commands:

* `pytui config` - Shows the location of the config file and its current state
* `pytui config -h` - Shows the options for modifying the config file
* `pytui config --exclude-pip` - Prevent `pip` from being included

### Config Values ###

* `venv_search_mode` - Where to search for VEnv folders
  * `"cwd"` - Search in the working directory only
  * `"parents"` - Search in the working directory and each parent folder (default)
  * `"recursive"` - Search in the working directory and subfolders recursively
  * `"recursive_parents"` - Combine the "recursive" and "parents" options (only the CWD is recursively searched)
* `include_pip` - Whether to include `pip` (and `setuptools` where appropriate) in created VEnvs (default: `True`)
* `latest_pip` - Download the latest `pip` for Python versions where it is available (default: `True`)
* `global_venv_folder` - The folder to use for global pytui venvs, `~/.local/share/ducktools/pytui/venvs` by default
* `shell_path` - Path to the shell used to launch activated venvs

### Clearing the discovered Python install cache ###

The Python install discovery cache is handled by the 
[ducktools-pythonfinder](https://github.com/DavidCEllis/ducktools-pythonfinder)
 package.

The easiest way to clear the cache is to use the `ducktools-pythonfinder` commandline.

* With uv: `uvx ducktools-pythonfinder clear-cache`
* With pipx: `pipx run ducktools-pythonfinder clear-cache`
* With the [pythonfinder zipapp](https://github.com/DavidCEllis/ducktools-pythonfinder/releases/latest): `python pythonfinder.pyz clear-cache`

### Shell Discovery ###

By default PyTUI will check your `$SHELL` variable if it is set for the path to your default shell.
If this exists and is a supported shell it will be used. Otherwise it will search `PATH` for shells
in this order:

* Windows: `pwsh.exe`, `powershell.exe`, `cmd.exe`, `bash.exe`
* Non-Windows: `fish`, `bash`, `zsh`

On Windows as a last resort if none of these are found it will search for the `COMSPEC` environment
variable to find a path to `cmd.exe`.

A data folder of shell scripts is kept in this location:

* Windows: `%LOCALAPPDATA%\ducktools\pytui\shell_scripts
* Non-Windows: `~/.local/share/ducktools/pytui/shell_scripts`

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
    not add a new dimension to it
