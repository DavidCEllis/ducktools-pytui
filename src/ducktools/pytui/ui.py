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
import os
import os.path

from asyncio import get_running_loop

from ducktools.pythonfinder import PythonInstall
from ducktools.pythonfinder.venv import get_python_venvs, PythonVEnv, PythonPackage

from textual import work
from textual.app import App
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Label
from textual.widgets.data_table import CellDoesNotExist

from .commands import launch_repl, launch_shell, create_venv
from .util import list_installs_deduped


DATATABLE_BINDINGS_NO_ENTER = [b for b in DataTable.BINDINGS if b.key != "enter"]
CWD = os.getcwd()


class DependencyScreen(ModalScreen[list[PythonPackage]]):
    BINDINGS = [
        Binding(key="c", action="close", description="Close", show=True),
        Binding(key="r", action="reload_dependencies", description="Reload Dependencies", show=True),
    ]

    def __init__(
        self,
        venv: PythonVEnv,
        dependency_cache: list[PythonPackage] | None
    ):
        super().__init__()
        self.venv = venv
        self.dependency_cache = dependency_cache

        self.venv_table = DataTable()

    def compose(self):
        with Vertical(classes="boxed"):
            yield Label(f"Packages installed in {self.venv.folder}")
            yield self.venv_table
            yield Footer()

    def on_mount(self):
        self.venv_table.cursor_type = "row"
        self.venv_table.add_columns("Dependency", "Version")
        self.load_dependencies()

    def action_close(self):
        self.dismiss(self.dependency_cache)

    async def action_reload_dependencies(self):
        self.load_dependencies(clear=True)

    @work
    async def load_dependencies(self, clear=False):
        self.venv_table.loading = True
        try:
            if clear:
                self.venv_table.clear()
                self.dependency_cache = None

            dependencies = self.dependency_cache
            if dependencies is None:
                loop = get_running_loop()
                dependencies = await loop.run_in_executor(None, self.venv.list_packages)

            for dep in dependencies:
                self.venv_table.add_row(dep.name, dep.version, key=dep.name)
        finally:
            self.venv_table.loading = False

        self.dependency_cache = dependencies


class VEnvTable(DataTable):
    BINDINGS = [
        Binding(key="enter", action="app.activated_shell", description="Activate VEnv and Launch Shell", show=True),
        Binding(key="r", action="app.launch_venv_repl", description="Launch VEnv Python REPL", show=True),
        Binding(key="p", action="app.list_venv_packages", description="List Installed Packages", show=True),
        *DATATABLE_BINDINGS_NO_ENTER,
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._venv_catalogue = {}

    def on_mount(self):
        self.setup_columns()
        self.load_venvs(clear_first=False)

    def setup_columns(self):
        self.cursor_type = "row"
        self.add_columns("Version", "Environment Path", "Runtime Path")

    def venv_from_key(self, key) -> PythonVEnv:
        return self._venv_catalogue[key]

    def load_venvs(self, clear_first=True):
        self.loading = True
        try:
            if clear_first:
                self.clear(columns=False)
                self._venv_catalogue = {}
            for venv in get_python_venvs(base_dir=CWD, recursive=False, search_parent_folders=True):
                self._venv_catalogue[venv.folder] = venv

                folder = os.path.relpath(venv.folder, start=CWD)
                self.add_row(venv.version_str, folder, venv.parent_executable, key=venv.folder)
        finally:
            self.loading = False


class RuntimeTable(DataTable):
    BINDINGS = [
        # Binding(key="v", action="app.create_venv", description="Create Virtual Environment", show=True),
        Binding(key="r", action="app.launch_runtime", description="Launch Runtime Python REPL", show=True),
        *DATATABLE_BINDINGS_NO_ENTER
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._runtime_catalogue = {}

    def on_mount(self):
        self.setup_columns()
        self.load_runtimes(clear_first=False)

    def setup_columns(self):
        self.cursor_type = "row"
        self.add_columns("Version", "Managed By", "Implementation", "Path")

    def runtime_from_key(self, key) -> PythonInstall:
        return self._runtime_catalogue[key]

    def load_runtimes(self, clear_first=True):
        self.loading = True
        try:
            if clear_first:
                self.clear()
                self._runtime_catalogue = {}

            for install in list_installs_deduped():
                self._runtime_catalogue[install.executable] = install

                self.add_row(
                    install.version_str,
                    install.managed_by,
                    install.implementation,
                    install.executable,
                    key=install.executable
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

        self._venv_dependency_cache: dict[str, list[PythonPackage]] = {}

    def on_mount(self):
        self.title = "Ducktools.PyTui: Python Environment and Runtime Manager"

    def compose(self):
        yield Header()
        with Vertical(classes="boxed"):
            yield Label("Virtual Environments")
            yield self._venv_table
        with Vertical(classes="boxed"):
            yield Label("Python Runtimes")
            yield self._runtime_table
        yield Footer()

    @property
    def selected_venv(self) -> PythonVEnv | None:
        table = self._venv_table

        try:
            row = table.coordinate_to_cell_key(table.cursor_coordinate)
        except CellDoesNotExist:
            return None

        return table.venv_from_key(row.row_key.value)

    @property
    def selected_runtime(self) -> PythonInstall | None:
        table = self._runtime_table

        try:
            row = table.coordinate_to_cell_key(table.cursor_coordinate)
        except CellDoesNotExist:
            return None

        return table.runtime_from_key(row.row_key.value)

    def action_launch_runtime(self):
        runtime = self.selected_runtime
        if runtime is None:
            return

        # Suspend the app and launch python
        # Ignore keyboard interrupts otherwise the program will exit when this exits.
        with self.suspend():
            launch_repl(runtime.executable)

        # Redraw
        self.refresh()

    def action_launch_venv_repl(self):
        venv = self.selected_venv
        if venv is None:
            return

        # Suspend the app and launch python
        # Ignore keyboard interrupts otherwise the program will exit when this exits.
        with self.suspend():
            launch_repl(venv.executable)

        # Redraw
        self.refresh()

    @work
    async def action_list_venv_packages(self):
        venv = self.selected_venv
        if venv is None:
            return

        dependency_cache = self._venv_dependency_cache.get(venv.folder)
        dependency_screen = DependencyScreen(venv=venv, dependency_cache=dependency_cache)

        dependencies = await self.push_screen_wait(dependency_screen)
        self._venv_dependency_cache[venv.folder] = dependencies

    def action_activated_shell(self):
        venv = self.selected_venv
        if venv is None:
            return

        with self.suspend():
            launch_shell(venv)

        # Redraw
        self.refresh()
