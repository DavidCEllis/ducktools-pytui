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

from unittest.mock import patch

from ducktools.pytui.shells import _core as core, bash

BASH_PATH = R"C:\Program Files\Git\usr\bin\bash.exe"


def test_registered():
    assert bash.GitBashShell.bin_name in core.Shell.registry
    assert bash.GitBashShell is core.Shell.registry[bash.GitBashShell.bin_name]


def test_frompath():
    assert core.Shell.from_path(BASH_PATH) == bash.GitBashShell(BASH_PATH)


def test_dedupe_path():
    venv_path = R"C:\Users\David\Source\ducktools-pytui\.venv\Scripts"
    bash_path = (
        "/c/Users/David/Source/ducktools-pytui/.venv/Scripts:"
        "/mingw64/bin:"
        "/usr/bin:"
        "/c/Users/David/.local/bin:"
        "/usr/bin:"
    )

    shell = bash.GitBashShell(BASH_PATH)

    expected = (
        "/c/Users/David/Source/ducktools-pytui/.venv/Scripts:"
        "/mingw64/bin:"
        "/usr/bin:"
        "/c/Users/David/.local/bin"
    )

    assert shell.get_deduped_path(bash_path, venv_path) == expected


def test_get_env_path():
    bash_env_path = (
        "/c/Users/David/Source/ducktools-pytui/.venv/Scripts:"
        "/mingw64/bin:"
        "/usr/bin:"
        "/c/Users/David/.local/bin:"
        "/usr/bin:"
    )

    with patch("subprocess.run") as run_mock:
        run_mock.return_value.stdout = bash_env_path
        env_path = bash.GitBashShell(BASH_PATH).get_env_path()

        assert env_path == bash_env_path
        run_mock.assert_called_once_with(
            [BASH_PATH, "-ic", "echo $PATH"],
            text=True,
            capture_output=True,
        )


def test_get_venv_shell_command():
    venv = "/c/Users/David/Source/ducktools-pytui/.venv"
    bash_path = (
        "/c/Users/David/Source/ducktools-pytui/.venv/Scripts:"
        "/mingw64/bin:"
        "/usr/bin:"
        "/c/Users/David/.local/bin"
    )
    prompt = "pytui: .venv"

    env = {
        "PYTUI_PATH": bash_path,
        "PYTUI_VIRTUAL_ENV": venv,
        "PYTUI_VIRTUAL_ENV_PROMPT": prompt,
    }

    with patch("ducktools.pytui.shells.bash.get_shell_script") as script_mock:
        def identity(x): return x

        script_mock.side_effect = identity

        shell = bash.GitBashShell(BASH_PATH)

        cmd, env_updates = shell.get_venv_shell_command(env)

        assert cmd == [BASH_PATH, "--rcfile", "activate_pytui.sh"]
        assert env_updates == {}  # environment variables are set in the script
