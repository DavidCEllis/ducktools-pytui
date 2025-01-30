# duckpy #

A terminal based user interface for managing Python installs and virtual environments.

## Usage ##

The easiest way to install DuckPy is as a tool from PyPI using `uv` or `pipx`.

`uv tool install duckpy` or `pipx install duckpy`

Run with `duckpy`.

## Features ##

### Done ###

* List Python Virtual Environments relative to the current folder
* List Python installs
* Launch a Terminal with a selected venv activated
* Launch a REPL with the selected venv
* Launch a REPL with the selected runtime

### Planned ###

* Create a venv from a specific runtime
* Delete a selected venv
* List installed packages in a venv
* Add commands to install/uninstall runtimes with specific tools if available (pyenv/uv/pymanage(r)(?))
* Highlight invalid venvs

### Not Planned ###

* Handle PEP-723 inline scripts
  * `ducktools-env` is my project for managing these
  * Potentially that could gain a TUI, but I'm not sure I'd want to merge the two things
* Handle Conda environments
  * Conda environments are a completely separate ecosystem, 
    while everything this supports uses the standard PyPI ecosystem
  * Supporting Conda would basically require a whole separate parallel set of commands
* Manage `duckpy` specific runtimes
  * I don't want to add *yet another* place Python can be installed
  * `duckpy` is intended to help manage tools and installs that already exist
