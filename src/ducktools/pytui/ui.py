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
import sys

import asyncio
import subprocess

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
from .config import Config
from .runtime_installers import uv
from .util import list_installs_deduped


CWD = os.getcwd()


# I wrote this error screen modal and then discovered notify.
# It might still be useful in some cases so I'll leave it commented out
# class ErrorScreen(ModalScreen):
#     def __init__(self, message):
#         super().__init__()
#         self.message = message
#
#     def compose(self):
#         with Vertical(classes="boxed"):
#             yield Label(f"Error: {self.message}")
#             with Horizontal(classes="boxed_noborder"):
#                 yield Button("Dismiss", variant="error")
#
#     def on_button_pressed(self, event: Button.Pressed) -> None:
#         self.dismiss(None)


class UVPythonTable(DataTable):
    def __init__(self, runtimes: list[uv.UVPythonListing], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.runtimes = runtimes

    def on_mount(self):
        self.setup_columns()
        self.list_downloads()

    def setup_columns(self):
        self.cursor_type = "row"
        self.add_columns("Version", "Implementation", "Variant", "Architecture")

    def list_downloads(self):
        for dl in self.runtimes:
            self.add_row(dl.version, dl.implementation, dl.variant, dl.arch, key=dl.key)


class UVPythonScreen(ModalScreen[uv.UVPythonListing | None]):
    BINDINGS = [
        Binding(key="enter", action="install", description="Install Runtime", priority=True, show=True),
        Binding(key="escape", action="cancel", description="Cancel", show=True),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.runtimes = uv.fetch_downloads()
        self.install_table = UVPythonTable(self.runtimes)
        self.install_button = Button("Install", variant="success", id="install")
        self.cancel_button = Button("Cancel", id="cancel")

    @property
    def runtimes_by_key(self):
        return {
            v.key: v for v in self.runtimes
        }

    @property
    def selected_runtime(self) -> uv.UVPythonListing | None:
        table = self.install_table

        try:
            row = table.coordinate_to_cell_key(table.cursor_coordinate)
        except CellDoesNotExist:
            return None

        return self.runtimes_by_key.get(row.row_key.value)

    def compose(self):
        with Vertical(classes="boxed"):
            yield Label("Available UV Python Runtimes")
            yield self.install_table
            yield Footer()

    def action_install(self):
        if self.focused == self.install_table or self.focused == self.install_button:
            self.dismiss(self.selected_runtime)
        else:
            self.dismiss(None)

    def action_cancel(self):
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "install":
            self.dismiss(self.selected_runtime)
        else:
            self.dismiss(None)


class DependencyScreen(ModalScreen[list[PythonPackage]]):
    BINDINGS = [
        Binding(key="r", action="reload_dependencies", description="Reload Dependencies", show=True),
        Binding(key="escape", action="close", description="Close", show=True),
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
        Binding(key="enter", action="create", description="Create VEnv", show=True, priority=True),
        Binding(key="escape", action="cancel", description="Cancel", show=True),
    ]

    def __init__(self, runtime: PythonInstall, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.runtime = runtime
        self.venv_input = Input(placeholder="VEnv Path (default='.venv')")

    def compose(self):
        with Vertical(classes="boxed"):
            yield Label(f"Create VENV from {self.runtime.implementation} {self.runtime.version_str}")
            with Vertical(classes="boxed_noborder"):
                yield self.venv_input
            yield Footer()

    def action_cancel(self):
        self.dismiss(None)

    def action_create(self):
        self.dismiss(self.venv_input.value)

    def on_input_submitted(self, event: Input.Submitted):
        self.dismiss(event.value)


class VEnvTable(DataTable):
    BINDINGS = [
        Binding(key="enter", action="app.activated_shell", description="Launch VEnv Shell", show=True),
        Binding(key="r", action="app.launch_venv_repl", description="Launch VEnv REPL", show=True),
        Binding(key="p", action="app.list_venv_packages", description="List Packages", show=True),
        Binding(key="delete", action="app.delete_venv", description="Delete VEnv", show=True),
    ]

    def __init__(self, *args, config, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = config

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

            recursive = "recursive" in self.config.venv_search_mode
            search_parent_folders = "parents" in self.config.venv_search_mode
            for venv in get_python_venvs(
                base_dir=CWD,
                recursive=recursive,
                search_parent_folders=search_parent_folders,
            ):
                self.add_venv(venv, sort=False)

        finally:
            self.sort_by_path()
            self.loading = False


class RuntimeTable(DataTable):
    BINDINGS = [
        Binding(key="r", action="app.launch_runtime", description="Launch Runtime REPL", show=True),
        Binding(key="v", action="app.create_venv", description="Create VEnv", show=True),
    ]
    if uv.check_uv():
        BINDINGS.extend(
            [
                Binding(key="i", action="app.install_runtime", description="Install New Runtime", show=True),
                Binding(key="delete", action="app.uninstall_runtime", description="Uninstall Runtime", show=True),
            ]
        )

    def __init__(self, *args, config, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = config
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

            query_executables = not self.config.fast_runtime_search
            for install in list_installs_deduped(query_executables=query_executables):
                self._runtime_catalogue[install.executable] = install

                if install.version_str == install.implementation_version_str:
                    version_str = install.version_str
                else:
                    version_str = f"{install.version_str} / {install.implementation_version_str}"

                self.add_row(
                    version_str,
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
    .boxed_limitheight {
        height: auto;
        max-height: 90%;
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

        self.config: Config = Config.from_file()

        self._venv_table = VEnvTable(config=self.config)
        self._runtime_table = RuntimeTable(config=self.config)
        self._runtime_table.styles.height = "1fr"

        self._venv_dependency_cache: dict[str, list[PythonPackage]] = {}

    def on_mount(self):
        self.title = "Ducktools.PyTUI: Python Environment and Runtime Manager"

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
            self.notify("No VEnv Selected", severity="warning")
            return
        elif venv.version < (3, 9):
            self.notify(
                f"Package listing not supported for Python {venv.version_str}",
                severity="warning",
            )
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
            self.notify("No runtime selected.", severity="warning")

        if runtime.implementation.lower() == "micropython":
            self.notify(
                "MicroPython does not support VEnv creation.",
                title="Error",
                severity="error",
            )
            return
        elif runtime.version < (3, 4):
            self.notify(
                f"ducktools-pytui does not support VEnv creation for Python {runtime.version_str}",
                title="Error",
                severity="error",
            )
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
                runtime, venv_name, self.config.include_pip, self.config.latest_pip
            )
        except FileExistsError:
            self.notify(
                f"Failed to create venv {venv_name}, folder already exists",
                title="Error",
                severity="error",
            )
        except subprocess.CalledProcessError as e:
            self.notify(f"Failed to create venv {venv_name}. Process Error: {e}")
        else:
            self.notify(f"VEnv {venv_name!r} created", title="Success")
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

    @work
    async def action_install_runtime(self):
        if not uv.check_uv():
            return
        runtime_screen = UVPythonScreen()
        runtime = await self.push_screen_wait(runtime_screen)

        if runtime is not None:
            self._runtime_table.loading = True
            loop = asyncio.get_event_loop()
            try:
                log = await loop.run_in_executor(None, uv.install_python, runtime)
                # self.notify(log)
            except (FileNotFoundError, subprocess.CalledProcessError) as e:
                self.notify(
                    f"Install Failed: {e}",
                    title="Error",
                    severity="error",
                )
            else:
                self.notify(
                    f"{runtime.key} installed successfully",
                    title="New Install"
                )
                self._runtime_table.load_runtimes(clear_first=True)
            finally:
                self._runtime_table.loading = False
                self.set_focus(self._runtime_table)
                self.refresh_bindings()

    @work
    async def action_uninstall_runtime(self):
        if not uv.check_uv():
            return

        runtime = self.selected_runtime
        if runtime is None:
            return

        if runtime.executable.startswith(sys.base_prefix):
            self.notify(
                "Can not uninstall the runtime being used to run ducktools-pytui",
                severity="warning",
            )
            return

        uv_listing = uv.find_matching_listing(runtime)
        if uv_listing is None:
            self.notify(
                f"{runtime.executable} is not a UV managed runtime",
                severity="warning"
            )
            return

        loop = asyncio.get_event_loop()
        self._runtime_table.loading = True
        try:
            log = await loop.run_in_executor(None, uv.uninstall_python, uv_listing)
            # self.notify(log)
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            self.notify(
                f"Uninstall Failed: {e}",
                severity="error",
            )
        else:
            self.notify(
                f"Runtime {uv_listing.key!r} uninstalled."
            )
            self._runtime_table.load_runtimes(clear_first=True)
        finally:
            self._runtime_table.loading = False
            self.set_focus(self._runtime_table)
            self.refresh_bindings()
