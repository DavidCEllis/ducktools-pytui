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


from ducktools.pytui.shells import _core as core, cmd


CMD_PATH = R"C:\Windows\System32\cmd.exe"


def test_registered():
    assert cmd.CMDShell.bin_name in core.Shell.registry
    assert cmd.CMDShell is core.Shell.registry[cmd.CMDShell.bin_name]


def test_frompath():
    assert core.Shell.from_path(CMD_PATH) == cmd.CMDShell(CMD_PATH)


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
        "PROMPT": "$P$G",
        "PYTUI_PATH": path,
        "PYTUI_VIRTUAL_ENV": venv,
        "PYTUI_VIRTUAL_ENV_PROMPT": prompt,
    }

    cmdshell = cmd.CMDShell(CMD_PATH)

    shell_cmd, env_updates = cmdshell.get_venv_shell_command(env)

    assert shell_cmd == [CMD_PATH, "/k"]
    assert env_updates == {
        "PATH": path,
        "VIRTUAL_ENV": venv,
        "VIRTUAL_ENV_PROMPT": prompt,
        "PROMPT": "(pytui: .venv) $P$G",
    }

    # Test with an old venv already in prompt
    env = {
        "PROMPT": "(pytui: .oldvenv) $P$G",
        "VIRTUAL_ENV_PROMPT": "pytui: .oldvenv",
        "PYTUI_PATH": path,
        "PYTUI_VIRTUAL_ENV": venv,
        "PYTUI_VIRTUAL_ENV_PROMPT": prompt,
    }

    shell_cmd, env_updates = cmdshell.get_venv_shell_command(env)

    assert env_updates == {
        "PATH": path,
        "VIRTUAL_ENV": venv,
        "VIRTUAL_ENV_PROMPT": prompt,
        "PROMPT": "(pytui: .venv) $P$G",
    }