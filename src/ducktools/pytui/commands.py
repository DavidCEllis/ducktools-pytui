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

import shellingham
from ducktools.pythonfinder.venv import PythonVEnv

from .util import run


def launch_repl(python_exe: str) -> None:
    run([python_exe])


def create_venv(python_exe: str, venv_path: str = ".venv", include_pip: bool = True) -> PythonVEnv:
    # Unlike the regular venv command defaults this will create an environment
    # and download the *newest* pip (assuming the parent venv includes pip)

    if include_pip:
        run([python_exe, "-m", "venv", "--upgrade-deps", venv_path])
    else:
        run([python_exe, "-m", "venv", "--without-pip", venv_path])

    config_path = os.path.join(os.path.realpath(venv_path), "pyvenv.cfg")

    return PythonVEnv.from_cfg(config_path)


def install_requirements(
    *,
    venv: PythonVEnv,
    requirements_path: str,
    no_deps: bool = False,
):
    base_python = venv.parent_executable
    venv_path = venv.folder

    command = [
        base_python,
        "-m", "pip",
        "--python", venv_path,
        "install",
        "-r", requirements_path,
    ]
    if no_deps:
        command.append("--no-deps")

    run(command)


def launch_shell(venv: PythonVEnv) -> None:
    # Launch a shell with a virtual environment activated.
    env = os.environ.copy()
    old_path = env.get("PATH", "")
    old_venv_prompt = os.environ.get("VIRTUAL_ENV_PROMPT", "")

    venv_prompt = os.path.basename(venv.folder)

    env["PATH"] = os.pathsep.join([os.path.dirname(venv.executable), old_path])
    env["VIRTUAL_ENV"] = venv.folder
    env["VIRTUAL_ENV_PROMPT"] = venv_prompt

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
        # Windows cmd prompt keep it simple
        old_prompt = env.get("PROMPT", "$P$G")
        old_prompt = old_prompt.removeprefix(f"({old_venv_prompt}) ")
        env["PROMPT"] = f"(pytui: {venv_prompt}) {old_prompt}"
        cmd = [shell, "/k"]  # This effectively hides the copyright message
    elif shell_name == "bash":
        # Dynamic prompt appears to work in BASH at least on Ubuntu
        old_prompt = env.get("PS1", r"\u@\h \w\$")
        old_prompt = old_prompt.removeprefix(old_venv_prompt)
        env["PS1"] = f"(pytui: $VIRTUAL_ENV_PROMPT) {old_prompt}"
        cmd = [shell, "--noprofile", "--norc"]
    elif shell_name == "zsh":
        # Didn't have so much luck on MacOS
        old_prompt = env.get("PS1", "%n@%m %1~:")
        old_prompt = old_prompt.removeprefix(old_venv_prompt)
        env["PS1"] = f"(pytui: {venv_prompt}) {old_prompt}"
        cmd = [shell, "--no-rcs"]
    else:
        # We'll probably need some extra config here
        cmd = [shell]

    print("\nVEnv shell from ducktools.pytui: type 'exit' to close")
    run(cmd, env=env)
