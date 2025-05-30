# ducktools-pytui
# MIT License
#
# Copyright (c) 2025 David C Ellis
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from __future__ import annotations

import os
import os.path
import sys

import asyncio
import functools
import subprocess
import sysconfig

from ducktools.pythonfinder import PythonInstall
from ducktools.pythonfinder.venv import list_python_venvs, PythonVEnv, PythonPackage

from textual import work, markup
from textual.app import App
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import Button, DataTable, Footer, Header, Input, Label
from textual.widgets.data_table import CellDoesNotExist


from ._version import __version__ as app_version
from .commands import launch_repl, launch_shell, create_venv, delete_venv
from .config import Config
from .util import list_installs_deduped
from .runtime_installers import (
    PythonListing,
    fetch_downloads,
    find_matching_listing,
    get_managers,
)


CWD = os.getcwd()


class InstallableRuntimeTable(DataTable):
    def __init__(self, runtimes: list[PythonListing], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.runtimes = runtimes

    def on_mount(self):
        self.setup_columns()
        self.list_downloads()

    def setup_columns(self):
        self.cursor_type = "row"
        self.add_columns("Version", "Manager", "Implementation", "Variant", "Architecture")

    def list_downloads(self):
        for dl in self.runtimes:
            self.add_row(
                dl.version,
                dl.manager.organisation,
                dl.implementation,
                dl.variant,
                dl.arch,
                key=dl.full_key,
            )


class RuntimeInstallScreen(ModalScreen["PythonListing | None"]):
    BINDINGS = [
        Binding(key="enter", action="install", description="Install Runtime", priority=True, show=True),
        Binding(key="escape", action="cancel", description="Cancel", show=True),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.runtimes = fetch_downloads()
        self.install_table = InstallableRuntimeTable(self.runtimes)

        self.install_button = Button("Install", variant="success", id="install")
        self.cancel_button = Button("Cancel", id="cancel")

    @property
    def runtimes_by_key(self):
        return {
            v.full_key: v for v in self.runtimes
        }

    @property
    def selected_runtime(self) -> PythonListing | None:
        table = self.install_table

        try:
            row = table.coordinate_to_cell_key(table.cursor_coordinate)
        except CellDoesNotExist:
            return None

        return self.runtimes_by_key.get(row.row_key.value)

    def compose(self):
        with Vertical(classes="boxed"):
            yield Label("Available Python Runtimes")
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


class DependencyScreen(ModalScreen["list[PythonPackage]"]):
    BINDINGS = [
        Binding(key="r", action="reload_dependencies", description="Reload Dependencies", show=True),
        Binding(key="escape", action="close", description="Close", show=True),
    ]

    venv: PythonVEnv
    dependency_cache: list[PythonPackage] | None
    venv_table: DataTable

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


class VEnvCreateScreen(ModalScreen["str | None"]):
    BINDINGS = [
        Binding(key="enter", action="create", description="Create VEnv", show=True, priority=True),
        Binding(key="escape", action="cancel", description="Cancel", show=True),
    ]

    def __init__(self, runtime: PythonInstall, global_venv=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.runtime = runtime
        self.global_venv = global_venv

        if global_venv:
            self.venv_input = Input(
                placeholder="VEnv Path",
                validators=[Length(minimum=1)],
                validate_on=["submitted"],
            )
        else:
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
        if self.global_venv and len(self.venv_input.value) == 0:
            self.notify("Must provide a name in order to create a global venv", severity="warning")
        else:
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

    def on_mount(self):
        self.setup_columns()
        self.call_after_refresh(self.load_venvs, clear_first=False)

    def setup_columns(self):
        self.cursor_type = "row"
        self.add_columns("Version", "Global", "Environment Path", "Runtime Path")

    @staticmethod
    def _keysort(rowtuple):
        return rowtuple[1], rowtuple[2]

    def sort_by_path(self):
        self.sort(key=self._keysort)

    def venv_from_key(self, key) -> PythonVEnv:
        return self._venv_catalogue[key]

    def add_venv(self, venv: PythonVEnv, sort=False, global_venv=False):
        self._venv_catalogue[venv.folder] = venv

        if global_venv:
            self.add_row(
                venv.version_str,
                True,
                venv.folder,
                venv.parent_executable,
                key=venv.folder
            )
        else:
            folder = os.path.relpath(venv.folder, start=CWD)
            self.add_row(venv.version_str, False, folder, venv.parent_executable, key=venv.folder)
        if sort:
            self.sort_by_path()

    def remove_venv(self, venv: PythonVEnv):
        self.remove_row(row_key=venv.folder)
        self._venv_catalogue.pop(venv.folder)

    @work
    async def load_venvs(self, clear_first=True):
        self.loading = True
        try:
            if clear_first:
                self.clear(columns=False)
                self._venv_catalogue = {}

            recursive = "recursive" in self.config.venv_search_mode
            search_parent_folders = "parents" in self.config.venv_search_mode

            global_venv_folder = self.config.global_venv_folder

            loop = asyncio.get_running_loop()
            get_venvs = functools.partial(
                list_python_venvs,
                base_dir=CWD,
                recursive=recursive,
                search_parent_folders=search_parent_folders
            )

            venvs = await loop.run_in_executor(
                None,
                get_venvs,
            )

            for venv in venvs:
                if not os.path.commonpath([venv.folder, global_venv_folder]) == global_venv_folder:
                    self.add_venv(venv, sort=False)

            if os.path.exists(self.config.global_venv_folder):
                get_global_venvs = functools.partial(
                    list_python_venvs,
                    base_dir=self.config.global_venv_folder,
                    recursive=True,
                    search_parent_folders=False,
                )

                global_venvs = await loop.run_in_executor(
                    None,
                    get_global_venvs
                )

                for venv in global_venvs:
                    self.add_venv(venv, global_venv=True, sort=False)

        finally:
            self.sort_by_path()
            self.refresh_bindings()
            self.loading = False


class RuntimeTable(DataTable):
    BINDINGS = [
        Binding(key="r", action="app.launch_runtime", description="Launch Runtime REPL", show=True),
        Binding(key="v", action="app.create_venv", description="Create VEnv", show=True),
        Binding(key="g", action="app.create_global_venv", description="Create Global VEnv", show=True),
    ]

    if get_managers():
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
        self.call_after_refresh(self.load_runtimes, clear_first=False)

    def setup_columns(self):
        self.cursor_type = "row"
        self.add_columns("Version", "Managed By", "Implementation", "Path")

    def runtime_from_key(self, key) -> PythonInstall:
        return self._runtime_catalogue[key]

    @work
    async def load_runtimes(self, clear_first=True):
        self.loading = True
        try:
            if clear_first:
                self.clear()
                self._runtime_catalogue = {}

            loop = asyncio.get_running_loop()
            deduped_installs = await loop.run_in_executor(None, list_installs_deduped)

            for install in deduped_installs:
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
            self.refresh_bindings()
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

    config: Config
    _venv_table: VEnvTable
    _runtime_table: RuntimeTable
    _venv_dependency_cache: dict[str, list[PythonPackage]]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = Config.from_file()

        self._venv_table = VEnvTable(config=self.config)
        self._runtime_table = RuntimeTable(config=self.config)
        self._runtime_table.styles.height = "1fr"

        self._venv_dependency_cache = {}

    def on_mount(self):
        self.title = f"Ducktools.PyTUI v{app_version}: Python Environment and Runtime Manager"

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
            self.notify("No VEnv selected")
            return

        if self.config.shell is None:
            self.notify("Failed to find known shell on PATH")
            return

        with self.suspend():
            launch_shell(venv, self.config.shell)

        # Redraw
        self.refresh()

    def _check_runtime_for_venv(self, runtime: PythonInstall | None) -> bool:
        """
        Check if a runtime is selected and if it can be used to create a venv

        :param runtime: PythonInstall object
        :return:
        """
        if runtime is None:
            self.notify("No runtime selected.", severity="warning")
            return False

        if runtime.implementation.lower() == "micropython":
            self.notify(
                "MicroPython does not support VEnv creation.",
                title="Error",
                severity="error",
            )
            return False
        elif runtime.version < (3, 4):
            self.notify(
                f"ducktools-pytui does not support VEnv creation for Python {runtime.version_str}",
                title="Error",
                severity="error",
            )
            return False

        return True

    async def _build_venv(
        self,
        runtime: PythonInstall,
        venv_path: str,
        global_venv: bool
    ) -> None:
        """
        Call python and create the actual venv

        :param runtime:
        :param venv_path:
        :return:
        """
        self._venv_table.loading = True
        loop = asyncio.get_running_loop()
        try:
            new_venv = await loop.run_in_executor(
                None,
                create_venv,
                runtime, venv_path, self.config.include_pip, self.config.latest_pip,
            )
        except FileExistsError:
            self.notify(
                f"Failed to create venv {venv_path!r}, folder already exists",
                title="Error",
                severity="error",
            )
        except subprocess.CalledProcessError as e:
            self.notify(f"Failed to create venv {venv_path!r}. Process Error: {e}")
        else:
            self.notify(f"VEnv {venv_path!r} created", title="Success")
            self._venv_table.add_venv(new_venv, sort=True, global_venv=global_venv)
        finally:
            self._venv_table.loading = False

    @work
    async def action_create_venv(self):
        runtime = self.selected_runtime
        if self._check_runtime_for_venv(runtime) is False:
            return

        venv_screen = VEnvCreateScreen(runtime=runtime)
        venv_name = await self.push_screen_wait(venv_screen)

        if venv_name is None:
            return
        elif venv_name == "":
            venv_name = ".venv"

        await self._build_venv(runtime, venv_name, global_venv=False)

    @work
    async def action_create_global_venv(self):
        runtime = self.selected_runtime
        if self._check_runtime_for_venv(runtime) is False:
            return

        venv_screen = VEnvCreateScreen(runtime=runtime, global_venv=True)
        venv_name = await self.push_screen_wait(venv_screen)

        venv_path = os.path.join(self.config.global_venv_folder, venv_name)

        self._venv_table.loading = True

        await self._build_venv(runtime, venv_path, global_venv=True)

    def action_delete_venv(self):
        venv = self.selected_venv
        if venv is None:
            return

        if venv.folder == sys.prefix:
            self.notify(
                "Can not delete the VEnv being used to run ducktools-pytui",
                severity="warning",
            )
            return

        delete_venv(venv)
        self._venv_table.remove_venv(venv)
        self._venv_dependency_cache.pop(venv.folder, None)

    @work
    async def action_install_runtime(self):
        if not get_managers():
            return

        runtime_screen = RuntimeInstallScreen()
        runtime = await self.push_screen_wait(runtime_screen)

        if runtime is not None:
            if runtime.will_overwrite:
                # Add a confirmation prompt here
                pass

            self._runtime_table.loading = True
            loop = asyncio.get_running_loop()

            try:
                result = await loop.run_in_executor(None, runtime.install)  # noqa
                # self.notify(result.stderr)
            except FileNotFoundError as e:
                self.notify(
                    f"Install Failed: {markup.escape(str(e))}",
                    title="Manager Not Found",
                    severity="error",
                )
            else:
                if result.returncode == 0:
                    self.notify(
                        f"{runtime.key} installed successfully",
                        title="New Install"
                    )
                    self._runtime_table.load_runtimes(clear_first=True)
                else:
                    for line in result.stderr.split("\n"):
                        if line:   
                            self.notify(
                                markup.escape(line.strip()),
                                title="Failed Install",
                                severity="error"
                            )
            finally:
                self._runtime_table.loading = False
                self.set_focus(self._runtime_table)
                self.refresh_bindings()

    @work
    async def action_uninstall_runtime(self):
        if not get_managers():
            return

        runtime = self.selected_runtime
        if runtime is None:
            return

        # Check if the executable is within the base prefix folder
        if runtime.paths.get("stdlib") == sysconfig.get_path("stdlib"):
            self.notify(
                "Can not uninstall the runtime being used to run ducktools-pytui",
                severity="warning",
            )
            return

        listing = find_matching_listing(runtime)
        if listing is None:
            self.notify(
                f"{runtime.executable} is not a managed runtime",
                severity="warning"
            )
            return

        loop = asyncio.get_running_loop()
        self._runtime_table.loading = True
        try:
            result = await loop.run_in_executor(None, listing.uninstall)  # noqa
            # self.notify(result.stderr)
        except FileNotFoundError as e:
            self.notify(
                f"Uninstall Failed: {markup.escape(str(e))}",
                title="Manager Not Found",
                severity="error",
            )
        else:
            if result.returncode == 0:
                self.notify(
                    f"Runtime {listing.key!r} uninstalled."
                )
                self._runtime_table.load_runtimes(clear_first=True)
            else:
                for line in result.stderr.split("\n"):
                    if line:   
                        self.notify(
                            markup.escape(line.strip()),
                            title="Failed Uninstall",
                            severity="error"
                        )
        finally:
            self._runtime_table.loading = False
            self.set_focus(self._runtime_table)
            self.refresh_bindings()
