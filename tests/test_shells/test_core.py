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
import sys
from unittest.mock import patch, mock_open

import pytest

from ducktools.pytui import __version__
from ducktools.pytui.shells import _core as core, get_shell_script
from ducktools.pytui.shells.bash import BashShell, GitBashShell
from ducktools.pytui.platform_paths import SHELL_SCRIPT_FOLDER


windows_only = pytest.mark.skipif(sys.platform != "win32", reason="Windows Only")
non_windows = pytest.mark.skipif(sys.platform == "win32", reason="Non-Windows Only")


def test_get_shell_script_output():
    # Test the output value at least is as expected
    bash_script = "activate_pytui.sh"

    # Mock that the version *IS* the latest one
    open_mock = mock_open(read_data=__version__)

    with patch("builtins.open", open_mock) as m, \
            patch("os.path.exists") as exists_mock, \
            patch("shutil.rmtree") as rmtree_mock:

        exists_mock.return_value = True
        expected = os.path.join(SHELL_SCRIPT_FOLDER, bash_script)

        result = get_shell_script(bash_script)

    assert result == expected

    exists_mock.assert_called_once_with(expected)
    m.assert_called_once_with(os.path.join(SHELL_SCRIPT_FOLDER, ".version"))
    rmtree_mock.assert_not_called()


class TestDedupePath:
    @non_windows
    def test_linux_path(self):
        venv_path = "/home/david/src/project/.venv"
        demo_path = (
            "/home/david/src/project/.venv:"
            "/home/david/.local/bin:"
            "/home/david/.local/bin:" # Pretty sure this is UV putting this in twice
            "/usr/local/sbin:"
            "/usr/local/bin:"
            "/usr/sbin:"
            "/usr/bin:"
            "/sbin:"
            "/bin:"
            "/usr/local/bin:"  # Duplicate that should be removed
        )

        shell = core.Shell("/bin/bash")

        deduped_expected = (
            "/home/david/src/project/.venv:"
            "/home/david/.local/bin:"
            "/usr/local/sbin:"
            "/usr/local/bin:"
            "/usr/sbin:"
            "/usr/bin:"
            "/sbin:"
            "/bin" # Trailing colon is gone in deduped
        )

        deduped = shell.get_deduped_path(demo_path, venv_path)

        assert deduped == deduped_expected

    @windows_only
    def test_windows_path(self):
        # I will change these back from R to r if I switch from VSCode
        venv_path = R"C:\Users\David\Source\result\.venv"
        demo_path = (
            R"C:\Windows\system32;"
            R"C:\Users\David\Source\result\.venv;"  # Should be removed
            R"C:\Users\David\.local\bin;"
            R"C:\Users\David\.local\bin\;"  # Duplicate should be removed
            R"C:\Program Files\Github CLI\;"
        )

        shell = core.Shell(R"C:\Program Files\PowerShell\7\pwsh.exe")
        deduped = shell.get_deduped_path(demo_path, venv_path)

        assert deduped == (
            R"C:\Users\David\Source\result\.venv;"
            R"C:\Windows\system32;"
            R"C:\Users\David\.local\bin;"
            R"C:\Program Files\Github CLI"
        )


def test_from_path_missing():
    assert core.Shell.from_path("unknown/path") is None


class TestGetDefault:
    @windows_only
    def test_get_default_win_envvar(self):
        # Test with an environment variable
        bash_path = R"C:\Program Files\Git\usr\bin\bash.exe"
        fake_env = {"SHELL": bash_path}
        with patch.dict("os.environ", fake_env, clear=True):
            shell = core.Shell.get_default()
            assert shell == GitBashShell(bash_path)

    @pytest.mark.parametrize("shell", core.Shell.registry.values())
    def test_get_default_which(self, shell):
        # Test with no environment variable
        def fake_which(path):
            if path == shell.bin_name:
                return path
            return None

        with patch.dict("os.environ", {}, clear=True), \
                patch("shutil.which") as mock_which:
            mock_which.side_effect = fake_which

            detected_shell = core.Shell.get_default()
            assert detected_shell == shell(shell.bin_name)

    @windows_only
    def test_backup_comspec(self):
        from ducktools.pytui.shells.cmd import CMDShell
        # Windows will use os.environ["COMSPEC"] if no shell is found on PATH
        cmd_path = R"C:\Windows\system32\cmd.exe"
        fake_env = {"COMSPEC": cmd_path}
        with patch.dict("os.environ", fake_env, clear=True), \
                patch("shutil.which") as mock_which:
            mock_which.return_value = None

            detected_shell = core.Shell.get_default()
            assert detected_shell == CMDShell(cmd_path)

    @non_windows
    def test_get_default_linux_envvar(self):
        bash_path = "/bin/bash"
        fake_env = {"SHELL": bash_path}
        with patch.dict("os.environ", fake_env, clear=True):
            shell = core.Shell.get_default()
            assert shell == BashShell(bash_path)
