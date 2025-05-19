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

from ducktools.pytui.shells import _core as core, powershell


POWERSHELL_PATH = R"C:\Program Files\PowerShell\7\pwsh.exe"
WINDOWS_POWERSHELL_PATH = R"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"


def test_registered():
    assert powershell.PowerShell.bin_name in core.Shell.registry
    assert powershell.WindowsPowerShell.bin_name in core.Shell.registry

    assert (powershell.PowerShell
            is core.Shell.registry[powershell.PowerShell.bin_name])
    assert (powershell.WindowsPowerShell
            is core.Shell.registry[powershell.WindowsPowerShell.bin_name])


def test_frompath():
    assert (core.Shell.from_path(POWERSHELL_PATH)
            == powershell.PowerShell(POWERSHELL_PATH))
    assert (core.Shell.from_path(WINDOWS_POWERSHELL_PATH)
            == powershell.WindowsPowerShell(WINDOWS_POWERSHELL_PATH))


def test_get_venv_shell_command():
    venv = R"C:\Users\David\Source\result\.venv"
    path = (
        R"C:\Users\David\Source\result\.venv\Scripts;"
        R"C:\Windows\system32;"
        R"C:\Users\David\.local\bin;"
        R"C:\Program Files\Github CLI"
    )
    prompt = "pytui: .venv"

    env = {
        "PYTUI_PATH": path,
        "PYTUI_VIRTUAL_ENV": venv,
        "PYTUI_VIRTUAL_ENV_PROMPT": prompt,
    }

    with patch("ducktools.pytui.shells.powershell.get_shell_script") as script_mock:
        def identity(x): return x

        script_mock.side_effect = identity

        shell = powershell.PowerShell(POWERSHELL_PATH)

        cmd, env_updates = shell.get_venv_shell_command(env)

        assert cmd == [POWERSHELL_PATH, "-NoExit", "activate_pytui.ps1"]
        assert env_updates == {}
