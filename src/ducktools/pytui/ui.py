# This file is a part of ducktools.pytui
# A TUI for managing Python installs and virtual environments
#
# Copyright (C) 2025  David C Ellis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os.path
from pathlib import Path
import typing

from ducktools.pythonfinder import PythonInstall
from ducktools.pythonfinder.venv import get_python_venvs, PythonVEnv

from textual.app import App
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, Label

from .commands import launch_repl, launch_shell, create_venv
from .util import list_installs_deduped


DATATABLE_BINDINGS_NO_ENTER = [b for b in DataTable.BINDINGS if b.key != "enter"]
CWD = Path.cwd()


class VEnvTable(DataTable):
    BINDINGS = [
        Binding(key="enter", action="app.activated_shell", description="Activate VEnv and Launch Shell", show=True),
        Binding(key="r", action="app.launch_venv_repl", description="Launch VEnv Python REPL", show=True),
        # Binding(key="p", action="show_packages", description="List Installed Packages", show=True),
        *DATATABLE_BINDINGS_NO_ENTER,
    ]

    def on_mount(self):
        self.load_venvs()

    def load_venvs(self):
        self.loading = True
        try:
            self.cursor_type = "row"
            self.add_columns("Version", "Environment Path", "Runtime Path")
            for venv in get_python_venvs(base_dir=CWD, recursive=False, search_parent_folders=True):
                folder = str(Path(venv.folder).relative_to(CWD))
                self.add_row(venv.version_str, folder, venv.parent_executable, key=venv)
        finally:
            self.loading = False


class RuntimeTable(DataTable):
    BINDINGS = [
        # Binding(key="v", action="app.create_venv", description="Create Virtual Environment", show=True),
        Binding(key="r", action="app.launch_runtime", description="Launch Runtime Python REPL", show=True),
        *DATATABLE_BINDINGS_NO_ENTER
    ]

    def on_mount(self):
        self.load_runtimes()

    def load_runtimes(self):
        self.loading = True
        try:
            self.cursor_type = "row"
            self.add_columns("Version", "Managed By", "Implementation", "Path")
            for install in list_installs_deduped():
                self.add_row(
                    install.version_str,
                    install.managed_by,
                    install.implementation,
                    install.executable,
                    key=install
                )
        finally:
            self.loading = False


class ManagerApp(App):
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
    ]

    CSS = """
    .boxed {
        height: auto;
        border: solid green;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._venv_table = VEnvTable()
        self._runtime_table = RuntimeTable()

    def compose(self):
        yield Header()
        with Vertical(classes="boxed"):
            yield Label("Virtual Environments")
            yield self._venv_table
        with Vertical(classes="boxed"):
            yield Label("Python Runtimes")
            yield self._runtime_table
        yield Footer()

    def action_launch_runtime(self):
        table = self._runtime_table

        row = table.coordinate_to_cell_key(table.cursor_coordinate)

        install = typing.cast(PythonInstall, row.row_key.value)
        python_exe = install.executable

        # Suspend the app and launch python
        # Ignore keyboard interrupts otherwise the program will exit when this exits.
        with self.suspend():
            launch_repl(python_exe)

        # Redraw
        self.refresh()

    def action_launch_venv_repl(self):
        table = self._venv_table
        row = table.coordinate_to_cell_key(table.cursor_coordinate)

        install = typing.cast(PythonVEnv, row.row_key.value)
        python_exe = install.executable

        # Suspend the app and launch python
        # Ignore keyboard interrupts otherwise the program will exit when this exits.
        with self.suspend():
            launch_repl(python_exe)

        # Redraw
        self.refresh()

    def action_activated_shell(self):
        table = self._venv_table
        row = table.coordinate_to_cell_key(table.cursor_coordinate)
        venv = typing.cast(PythonVEnv, row.row_key.value)
        with self.suspend():
            launch_shell(venv)

        # Redraw
        self.refresh()

    def on_mount(self):
        self.title = "Ducktools.PyTui: Python Environment and Runtime Manager"
