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
import sys

import shellingham
from ducktools.pythonfinder import PythonInstall
from ducktools.pythonfinder.venv import PythonVEnv
from ducktools.lazyimporter import LazyImporter, ModuleImport

from ._version import __version__
from .platform_paths import SHELL_SCRIPT_FOLDER
from .util import run

_laz = LazyImporter([ModuleImport("zipfile")])

_shell_scriptfiles = [
    "activate_pytui.ps1",
    "activate_pytui.sh",
]

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


def get_shell_script(filename: str):
    if os.path.exists(__file__):
        # Use them from the source folder if available
        shell_script_folder = os.path.join(os.path.dirname(__file__), "shell_scripts")
    elif os.path.isfile(sys.argv[0]):  # zipapp potentially
        # In a zipapp they may not be, so extract them
        shell_script_folder = SHELL_SCRIPT_FOLDER

        shell_script_verfile = os.path.join(SHELL_SCRIPT_FOLDER, ".version")
        valid_verfile = False
        try:
            with open(shell_script_verfile) as f:
                script_ver = f.read()
            if script_ver == __version__:
                valid_verfile = True
        except FileNotFoundError:
            pass

        if not valid_verfile:
            # Clear out anything that might be there and remake the folder
            shutil.rmtree(SHELL_SCRIPT_FOLDER, ignore_errors=True)
            os.makedirs(SHELL_SCRIPT_FOLDER, exist_ok=True)

            # Get the zipfile path to open and the internal shell script folder
            zipfile_path = os.path.abspath(sys.argv[0])
            scripts_path = os.path.join(
                os.path.dirname(__file__), "shell_scripts"
            ).removeprefix(zipfile_path + os.sep)

            if sys.platform == "win32":
                # Zipfile needs '/' for internal paths
                scripts_path = scripts_path.replace("\\", "/")

            zipapp_contents = _laz.zipfile.ZipFile(zipfile_path)
            for name in _shell_scriptfiles:
                script_path = f"{scripts_path}/{name}"
                output_path = os.path.join(shell_script_folder, name)
                with zipapp_contents.open(script_path) as read_f, \
                        open(output_path, 'wb') as write_f:
                    write_f.write(read_f.read())

            with open(shell_script_verfile, 'w') as f:
                f.write(__version__)
    else:
        raise FileNotFoundError("Could not find shell script folder.")

    return os.path.join(shell_script_folder, filename)


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


def delete_venv(venv_path: str):
    shutil.rmtree(venv_path, ignore_errors=True)


def install_requirements(
    *,
    venv: PythonVEnv,
    requirements_path: str,
    no_deps: bool = False,
):
    command = [
        venv.executable,
        "-m", "pip",
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

    venv_prompt = f"pytui: {os.path.basename(venv.folder)}"
    venv_bindir = os.path.dirname(venv.executable)
    try:
        shell_name, shell = shellingham.detect_shell()
    except shellingham.ShellDetectionFailure:
        if os.name == "posix":
            shell = os.environ["SHELL"]
            shell_name = os.path.basename(shell)
        elif os.name == "nt":
            # Almost certainly "cmd.exe"
            shell = os.environ["COMSPEC"]
            shell_name = os.path.splitext(os.path.basename(shell))[0]
        else:
            raise RuntimeError(f"Shell detection failed")

    # dedupe and construct the PATH for the shell here
    if sys.platform == "win32" and shell_name == "bash":
        # Git bash needs special env handling as it follows linux conventions
        # And does not provide the PATH variable to child processes
        drive, venv_dir = os.path.splitdrive(venv_bindir)
        if ":" in drive:
            drive = drive.replace(":", "").lower()
            drive = f"/{drive}"
        venv_dir = venv_dir.replace("\\", "/")
        new_venv_bindir = "".join([drive, venv_dir])

        # Get the current git bash PATH
        prompt_getter = subprocess.run(
            [shell, "-ic", "echo $PATH"],
            text=True,
            capture_output=True
        )
        git_bash_path = prompt_getter.stdout.strip()
        deduped_path = []
        for p in git_bash_path.split(":"):
            if p in deduped_path:
                continue
            deduped_path.append(p)
        venv_env_path = ":".join([new_venv_bindir, *deduped_path])

    else:
        # In other cases follow the OS conventions
        deduped_path = []
        for p in old_path.split(os.pathsep):
            if p in deduped_path:
                continue
            deduped_path.append(p)

        venv_env_path = os.pathsep.join([venv_bindir, *deduped_path])

    # Environment variables may get overwritten so also create PYTUI versions
    env["PATH"] = env["PYTUI_PATH"] = venv_env_path
    env["VIRTUAL_ENV"] = env["PYTUI_VIRTUAL_ENV"] = venv.folder
    env["VIRTUAL_ENV_PROMPT"] = env["PYTUI_VIRTUAL_ENV_PROMPT"] = venv_prompt

    if os.name == "nt" and not WIN_HISTORY_FIXED:
        fix_win_history()

    if shell_name == "cmd":
        # Windows cmd prompt - history doesn't work for some reason
        shell_prompt = env.get("PROMPT", "$P$G")
        if old_venv_prompt and old_venv_prompt in shell_prompt:
            # Some prompts have colours etc
            new_prompt = shell_prompt.replace(old_venv_prompt, f"pytui: {venv_prompt}")
        else:
            new_prompt = f"({venv_prompt}) {shell_prompt}"
        env["PROMPT"] = new_prompt
        cmd = [shell, "/k"]  # This effectively hides the copyright message

    elif shell_name == "powershell":
        rcfile = get_shell_script("activate_pytui.ps1")
        with open(rcfile, encoding="utf8") as f:
            prompt_command = f.read()
        cmd = [shell, "-NoExit", prompt_command]

    elif shell_name == "bash":
        # Invoke our custom activation script as the rcfile
        # This includes ~/.bashrc but handles activation from Python
        rcfile = get_shell_script("activate_pytui.sh")
        cmd = [shell, "--rcfile", rcfile]

    elif shell_name == "zsh":
        # Try to get the shell PS1 from subprocess
        prompt_getter = subprocess.run(
            [shell, "-ic", "echo $PS1"],
            text=True, 
            capture_output=True
        )
        shell_prompt = prompt_getter.stdout.strip()
        
        if old_venv_prompt:
            shell_prompt = shell_prompt.removeprefix(old_venv_prompt)
        
        if not shell_prompt:
            shell_prompt = "%n@%m %1~ %#"
        
        shell_prompt = f"({venv_prompt}) {shell_prompt} "
        env["PS1"] = shell_prompt
        cmd = [shell, "--no-rcs"]

    else:
        # We'll probably need some extra config here
        print(f"UNSUPPORTED SHELL: {shell_name!r}.")
        print(
            "PATH may not have been correctly modified. "
            "Check if $PATH matches $PYTUI_PATH"
        )
        cmd = [shell]

    print("\nVEnv shell from ducktools.pytui: type 'exit' to close")
    run(cmd, env=env)  # type: ignore
