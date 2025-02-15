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
* List Python Runtimes
* Launch a Terminal with a selected venv activated
  * Currently only 'tested' with bash, zsh (on macos), powershell and cmd.
  * It's possible shell config files may break the environment variable changes. 
* Launch a REPL with the selected venv
* Launch a REPL with the selected runtime
* List installed packages in a venv
* Create a venv from a specific runtime
* Delete a selected venv

### Planned ###

* Config file with some saved settings
  * Option: Create venv without pip or without the latest pip
  * Keep the theme the user selected
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
