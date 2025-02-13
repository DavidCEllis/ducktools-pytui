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

import asyncio

from ducktools.pythonfinder import PythonInstall
from ducktools.pythonfinder.venv import get_python_venvs, PythonVEnv, PythonPackage

from textual import work
from textual.app import App
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label
from textual.widgets.data_table import CellDoesNotExist

from .commands import launch_repl, launch_shell, create_venv, delete_venv
from .util import list_installs_deduped


# DATATABLE_BINDINGS_NO_ENTER = [b for b in DataTable.BINDINGS if b.key != "enter"]
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
                loop = asyncio.get_running_loop()
                dependencies = await loop.run_in_executor(None, self.venv.list_packages)

            for dep in sorted(dependencies, key=lambda x: x.name.lower()):
                self.venv_table.add_row(dep.name, dep.version, key=dep.name)
        finally:
            self.venv_table.loading = False

        self.dependency_cache = dependencies


class VEnvCreateScreen(ModalScreen[str | None]):
    BINDINGS = [
        Binding(key="escape", action="cancel", description="Cancel VEnv Creation")
    ]

    def __init__(self, runtime: PythonInstall, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.runtime = runtime
        self.venv_input = Input(placeholder="VEnv Path (default='.venv')")

    def compose(self):
        with Vertical(classes="boxed"):
            yield Label(f"Create VENV from {self.runtime.implementation} {self.runtime.version_str}")
            yield self.venv_input
            with Horizontal(classes="boxed_noborder"):
                yield Button("Create", variant="success", id="create")
                yield Button("Cancel", id="cancel")

    def action_cancel(self):
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted):
        self.dismiss(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            self.dismiss(self.venv_input.value)
        else:
            self.dismiss(None)


class VEnvTable(DataTable):
    BINDINGS = [
        Binding(key="enter", action="app.activated_shell", description="Launch VEnv Shell", show=True),
        Binding(key="r", action="app.launch_venv_repl", description="Launch VEnv REPL", show=True),
        Binding(key="p", action="app.list_venv_packages", description="List Packages", show=True),
        Binding(key="delete", action="app.delete_venv", description="Delete VEnv", show=True),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._venv_catalogue = {}
        self._sort_key = None

    def on_mount(self):
        self.setup_columns()
        self.load_venvs(clear_first=False)

    def setup_columns(self):
        self.cursor_type = "row"
        keys = self.add_columns("Version", "Environment Path", "Runtime Path")
        self._sort_key = keys[1]

    def sort_by_path(self):
        self.sort(self._sort_key)

    def venv_from_key(self, key) -> PythonVEnv:
        return self._venv_catalogue[key]

    def add_venv(self, venv: PythonVEnv, sort=False):
        self._venv_catalogue[venv.folder] = venv
        folder = os.path.relpath(venv.folder, start=CWD)
        self.add_row(venv.version_str, folder, venv.parent_executable, key=venv.folder)
        if sort:
            self.sort_by_path()

    def remove_venv(self, venv: PythonVEnv):
        self.remove_row(row_key=venv.folder)
        self._venv_catalogue.pop(venv.folder)

    def load_venvs(self, clear_first=True):
        self.loading = True
        try:
            if clear_first:
                self.clear(columns=False)
                self._venv_catalogue = {}
            for venv in get_python_venvs(base_dir=CWD, recursive=False, search_parent_folders=True):
                self.add_venv(venv, sort=False)
        finally:
            self.sort_by_path()
            self.loading = False


class RuntimeTable(DataTable):
    BINDINGS = [
        Binding(key="r", action="app.launch_runtime", description="Launch Runtime REPL", show=True),
        Binding(key="v", action="app.create_venv", description="Create VEnv", show=True),
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
        border: $primary-darken-2;
    }
    .boxed_fillheight {
        height: 1fr;
        border: $primary-darken-2;
    }
    .boxed_noborder {
        height: auto;
        border: hidden;
        margin: 1;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._venv_table = VEnvTable()
        self._runtime_table = RuntimeTable()
        self._runtime_table.styles.height = "1fr"

        self._venv_dependency_cache: dict[str, list[PythonPackage]] = {}

    def on_mount(self):
        self.title = "Ducktools.PyTui: Python Environment and Runtime Manager"

    def compose(self):
        yield Header()
        with Vertical(classes="boxed"):
            yield Label("Virtual Environments")
            yield self._venv_table
        with Vertical(classes="boxed_fillheight"):
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

    @work
    async def action_create_venv(self):
        runtime = self.selected_runtime
        if runtime is None:
            return

        venv_screen = VEnvCreateScreen(runtime=runtime)
        venv_name = await self.push_screen_wait(venv_screen)

        if venv_name is None:
            return
        elif venv_name == "":
            venv_name = ".venv"

        self._venv_table.loading = True
        loop = asyncio.get_event_loop()
        try:
            new_venv = await loop.run_in_executor(
                None,
                create_venv,
                runtime, venv_name
            )
        except FileExistsError:
            pass
        else:
            self._venv_table.add_venv(new_venv, sort=True)
        finally:
            self._venv_table.loading = False

    def action_delete_venv(self):
        venv = self.selected_venv
        if venv is None:
            return

        delete_venv(venv.folder)
        self._venv_table.remove_venv(venv)
        self._venv_dependency_cache.pop(venv.folder, None)
