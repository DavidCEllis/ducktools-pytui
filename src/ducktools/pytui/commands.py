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
import sys
from pathlib import Path

import shellingham
from ducktools.pythonfinder.venv import PythonVEnv

from .util import run


def launch_repl(python_exe: str) -> None:
    run([python_exe])


def create_venv(python_exe: str, venv_path: str = ".venv", include_pip: bool = True) -> Path:
    # Unlike the regular venv command defaults this will create an environment
    # and download the *newest* pip (assuming the parent venv includes pip)

    if include_pip:
        run([python_exe, "-m", "venv", "--upgrade-deps", venv_path])
    else:
        run([python_exe, "-m", "venv", "--without-pip", venv_path])

    if sys.platform == "win32":
        python_path = Path(venv_path).resolve() / "Scripts" / "python.exe"
    else:
        python_path = Path(venv_path).resolve() / "bin" / "python"

    return python_path


def launch_shell(venv: PythonVEnv) -> None:
    # Launch a shell with a virtual environment activated.
    env = os.environ.copy()
    old_path = env.get("PATH", "")
    env["PATH"] = os.pathsep.join([str(Path(venv.executable).parent), old_path])
    env["VIRTUAL_ENV"] = venv.folder
    env["VIRTUAL_ENV_PROMPT"] = Path(venv.folder).name

    for t, v in env.items():
        if type(v) is not str:
            assert False, t

    try:
        shell_name, shell = shellingham.detect_shell()
    except shellingham.ShellDetectionFailure:
        if os.name == "posix":
            shell_name, shell = "UNKNOWN", os.environ["SHELL"]
        elif os.name == "nt":
            shell_name, shell = "UNKNOWN", os.environ["COMSPEC"]
        else:
            raise RuntimeError(f"Shell detection failed")

    if shell_name == "cmd":
        old_prompt = env.get("PROMPT", "$P$G")
        env["PROMPT"] = f"({Path(venv.folder).name}) {old_prompt}"
    elif shell_name == "bash":
        old_prompt = env.get("PS1", "")
        env["PS1"] = f"({Path(venv.folder).name}) {old_prompt}"

    print(f"Launching Shell with active VENV: {venv.folder}")
    print("Type 'exit' to close")
    run([shell], env=env)
