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

from ducktools.pytui.shells import _core as core, fish

FISH_PATH = "usr/bin/fish"

def test_registered():
    assert fish.FishShell.bin_name in core.Shell.registry
    assert fish.FishShell is core.Shell.registry[fish.FishShell.bin_name]


def test_frompath():
    assert core.Shell.from_path(FISH_PATH) == fish.FishShell(FISH_PATH)


def test_get_venv_shell_command():
    venv = "/home/david/src/ducktools-pytui/.venv"
    env_path = (
        "/home/david/src/ducktools-pytui/.venv"
        "/home/david/.pyenv/shims:"
        "/home/david/.cargo/bin:"
        "/home/david/.pyenv/bin:"
        "/home/david/.local/bin:"
        "/home/david/bin:"
        "/usr/local/sbin:"
        "/usr/local/bin:"
        "/usr/sbin:"
        "/usr/bin:"
        "/sbin:"
        "/bin:"
        "/usr/games:"
        "/usr/local/games:"
        "/snap/bin"
    )
    prompt = "pytui: .venv"

    env = {
        "PYTUI_PATH": env_path,
        "PYTUI_VIRTUAL_ENV": venv,
        "PYTUI_VIRTUAL_ENV_PROMPT": prompt,
    }

    with patch("ducktools.pytui.shells.fish.get_shell_script") as script_mock:
        def identity(x): return x
        script_mock.side_effect = identity

        shell = fish.FishShell(FISH_PATH)

        cmd, env_updates = shell.get_venv_shell_command(env)

        assert cmd == [FISH_PATH, "-C", "source \"activate_pytui.fish\"", "-i"]
        assert env_updates == {}  # environment variables are set in the script
