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
import shutil
import subprocess

from ducktools.pythonfinder import PythonInstall
from ducktools.pythonfinder.venv import PythonVEnv

from ._version import __version__
from .shells import Shell
from .util import run


WIN_HISTORY_FIXED = False


def fix_win_history():
    """
    Fix the windows history and set a global flag that it has been set
    :return:
    """
    global WIN_HISTORY_FIXED
    from .util.win32_terminal_hist import set_console_history_info
    set_console_history_info()
    WIN_HISTORY_FIXED = True


def launch_repl(python_exe: str) -> None:
    if os.name == "nt" and not WIN_HISTORY_FIXED:
        fix_win_history()
    run([python_exe])  # type: ignore


def create_venv(
    python_runtime: PythonInstall,
    venv_path: str = ".venv",
    include_pip: bool = True,
    latest_pip: bool = True
) -> PythonVEnv:
    # Unlike the regular venv command defaults this will create an environment
    # and download the *newest* pip (assuming the parent venv includes pip)

    if os.path.exists(venv_path):
        raise FileExistsError(f"VEnv '{venv_path}' already exists.")

    python_exe = python_runtime.executable

    # Also always include the pip bundled with graalpy and don't update
    is_graalpy = python_runtime.implementation == "graalpy"

    venv_cmd = [python_exe, "-m", "venv", venv_path]
    if not is_graalpy:
        if not include_pip:
            venv_cmd.append("--without-pip")
        elif latest_pip and python_runtime.version >= (3, 9):
            venv_cmd.append("--upgrade-deps")

    # These tasks run in the background so don't need to block ctrl+c
    # Capture output to not mess with the textual display
    subprocess.run(venv_cmd, capture_output=True, check=True)

    config_path = os.path.join(os.path.realpath(venv_path), "pyvenv.cfg")

    return PythonVEnv.from_cfg(config_path)


def delete_venv(venv: PythonVEnv) -> None:
    shutil.rmtree(venv.folder, ignore_errors=True)


def install_requirements(
    *,
    venv: PythonVEnv,
    requirements_path: str,
    no_deps: bool = False,
) -> None:
    command = [
        venv.executable,
        "-m", "pip",
        "install",
        "-r", requirements_path,
    ]
    if no_deps:
        command.append("--no-deps")

    run(command)  # type: ignore


def launch_shell(venv: PythonVEnv, shell: Shell) -> None:
    # Launch a shell with a virtual environment activated.
    env = os.environ.copy()

    if "dev" in __version__:
        venv_prompt = f"pytui dev: {os.path.basename(venv.folder)}"
    else:
        venv_prompt = f"pytui: {os.path.basename(venv.folder)}"

    venv_bindir = os.path.dirname(venv.executable)

    base_path = shell.get_env_path()
    venv_env_path = shell.get_deduped_path(base_path, venv_bindir)

    # Set the PYTUI versions of PATH/VIRTUAL_ENV/VIRTUAL_ENV_PROMPT
    # These are copied over in the activation script
    # Or included in the env updates
    env["PYTUI_PATH"] = venv_env_path
    env["PYTUI_VIRTUAL_ENV"] = venv.folder
    env["PYTUI_VIRTUAL_ENV_PROMPT"] = venv_prompt

    env.pop("PYTHONHOME", None)

    if os.name == "nt" and not WIN_HISTORY_FIXED:
        fix_win_history()

    cmd, env_updates = shell.get_venv_shell_command(env)

    # Update env with any required environment variables
    env.update(env_updates)

    print("\nVEnv shell from ducktools.pytui: type 'exit' to close")
    run(cmd, env=env)  # type: ignore
