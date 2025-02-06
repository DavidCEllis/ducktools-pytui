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
import subprocess

import shellingham
from ducktools.pythonfinder.venv import PythonVEnv

from .util import run


def launch_repl(python_exe: str) -> None:
    run([python_exe])


def create_venv(python_exe: str, venv_path: str = ".venv", include_pip: bool = True) -> PythonVEnv:
    # Unlike the regular venv command defaults this will create an environment
    # and download the *newest* pip (assuming the parent venv includes pip)

    if os.path.exists(venv_path):
        raise FileExistsError(f"VEnv '{venv_path}' already exists.")

    # These tasks run in the background so don't need to block ctrl+c
    if include_pip:
        subprocess.run([python_exe, "-m", "venv", "--upgrade-deps", venv_path])
    else:
        subprocess.run([python_exe, "-m", "venv", "--without-pip", venv_path])

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
    venv_dir = os.path.dirname(venv.executable)

    try:
        shell_name, shell = shellingham.detect_shell()
    except shellingham.ShellDetectionFailure:
        if os.name == "posix":
            shell_name, shell = "UNKNOWN", os.environ["SHELL"]
        elif os.name == "nt":
            shell_name, shell = "UNKNOWN", os.environ["COMSPEC"]
        else:
            raise RuntimeError(f"Shell detection failed")

    env["PATH"] = os.pathsep.join([venv_dir, old_path])
    env["VIRTUAL_ENV"] = venv.folder
    env["VIRTUAL_ENV_PROMPT"] = venv_prompt

    if shell_name == "cmd":
        # Windows cmd prompt - history doesn't work for some reason
        old_prompt = env.get("PROMPT", "$P$G")
        if old_venv_prompt and old_venv_prompt in old_prompt:
            # Some prompts have colours etc
            new_prompt = old_prompt.replace(old_venv_prompt, f"pytui: {venv_prompt}")
        else:
            new_prompt = f"(pytui: {venv_prompt}) {old_prompt}"
        env["PROMPT"] = new_prompt
        cmd = [shell, "/k"]  # This effectively hides the copyright message
    elif shell_name == "powershell":
        # Copied from activate.ps1
        prompt_command = """
        function global:_old_virtual_prompt {
        ""
        }
        $function:_old_virtual_prompt = $function:prompt
        function global:prompt {
            $previous_prompt_value = & $function:_old_virtual_prompt
            ("(pytui: " + $env:VIRTUAL_ENV_PROMPT + ") " + $previous_prompt_value)
        }
        """
        cmd = [shell, "-NoExit", prompt_command]
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
