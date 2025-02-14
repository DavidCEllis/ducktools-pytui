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
import shutil
import subprocess
import sys

import shellingham
from ducktools.pythonfinder import PythonInstall
from ducktools.pythonfinder.venv import PythonVEnv

from .util import run


USE_COLOR = True


def launch_repl(python_exe: str) -> None:
    run([python_exe])  # type: ignore


def create_venv(python_runtime: PythonInstall, venv_path: str = ".venv", include_pip: bool = True) -> PythonVEnv:
    # Unlike the regular venv command defaults this will create an environment
    # and download the *newest* pip (assuming the parent venv includes pip)

    if os.path.exists(venv_path):
        raise FileExistsError(f"VEnv '{venv_path}' already exists.")

    python_exe = python_runtime.executable
    # These tasks run in the background so don't need to block ctrl+c
    # Capture output to not mess with the textual display
    subprocess.run([python_exe, "-m", "venv", "--without-pip", venv_path], capture_output=True)

    if include_pip:
        # This actually seems to be faster than `--upgrade-deps`
        extras = ["pip"]
        if python_runtime.version < (3, 12):
            extras.append("setuptools")

        # Run the subprocess using *this* install to guarantee the presence of pip
        subprocess.run(
            [
                sys.executable, "-m", "pip",
                "--python", venv_path,
                "install", *extras
            ],
            capture_output=True,
        )

    config_path = os.path.join(os.path.realpath(venv_path), "pyvenv.cfg")

    return PythonVEnv.from_cfg(config_path)


def delete_venv(venv_path: str):
    shutil.rmtree(venv_path, ignore_errors=True)


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

    run(command)  # type: ignore


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
        shell_prompt = env.get("PROMPT", "$P$G")
        if old_venv_prompt and old_venv_prompt in shell_prompt:
            # Some prompts have colours etc
            new_prompt = shell_prompt.replace(old_venv_prompt, f"pytui: {venv_prompt}")
        else:
            new_prompt = f"(pytui: {venv_prompt}) {shell_prompt}"
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
        # If this is run in a venv, the prompt may exist in environ
        shell_prompt = os.environ.get("PS1", None)
        if shell_prompt is None:
            shell_echo = subprocess.run(
                "echo $PS1",
                shell=True,
                capture_output=True,
                text=True,
            )
            shell_prompt = shell_echo.stdout.rstrip()

        if not shell_prompt or shell_prompt.strip() == "$":
            # Get a reasonable default if this is empty or useless
            if USE_COLOR:
                shell_prompt = r"\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ "
            else:
                shell_prompt = r"\u@\h:\w\$ "

        if old_venv_prompt and old_venv_prompt in shell_prompt:
            shell_prompt = shell_prompt.replace(old_venv_prompt, "(pytui: $VIRTUAL_ENV_PROMPT) ")
        else:
            shell_prompt = f"(pytui: $VIRTUAL_ENV_PROMPT) {shell_prompt}"
        env["PS1"] = shell_prompt
        cmd = [shell, "--noprofile", "--norc"]
    elif shell_name == "zsh":
        shell_prompt = os.environ.get("PS1", None)
        if shell_prompt is None:
            shell_echo = subprocess.run(
                "echo $PS1",
                shell=True,
                capture_output=True,
                text=True,
            )
            shell_prompt = shell_echo.stdout.rstrip()

        if not shell_prompt:
            shell_prompt = "%n@%m %1~ %#"

        if old_venv_prompt and old_venv_prompt in shell_prompt:
            shell_prompt = shell_prompt.replace(old_venv_prompt, f"(pytui: {venv_prompt})")
        else:
            shell_prompt = f"(pytui: {venv_prompt}) {shell_prompt} "

        env["PS1"] = shell_prompt
        cmd = [shell, "--no-rcs"]
    else:
        # We'll probably need some extra config here
        cmd = [shell]

    print("\nVEnv shell from ducktools.pytui: type 'exit' to close")
    run(cmd, env=env)  # type: ignore
