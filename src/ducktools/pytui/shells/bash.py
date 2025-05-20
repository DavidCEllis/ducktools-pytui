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
import subprocess
import sys

from ._core import Shell, get_shell_script



class BashShell(Shell):
    """
    Shell code for the Linux bash shell
    """
    name = "Bash"
    bin_name = "bash"
    exclude = (sys.platform == "win32")

    def get_venv_shell_command(self, env):
        rcfile = get_shell_script("activate_pytui.sh")
        cmd = [self.path, "--rcfile", rcfile]
        env_updates = {}
        return cmd, env_updates


class GitBashShell(BashShell):
    """
    Shell code for a Git Bash shell on Windows
    """
    name = "Git Bash"
    bin_name = "bash.exe"
    exclude = (sys.platform != "win32")

    def get_env_path(self) -> str:
        """
        Get the git bash environment Path

        This requires launching the shell and echoing
        the default $PATH variable

        :return: Git bash formatted PATH variable
        """
        prompt_getter = subprocess.run(
            [self.path, "-ic", "echo $PATH"],
            text=True,
            capture_output=True
        )
        return prompt_getter.stdout.strip()

    @staticmethod
    def get_deduped_path(path, venv_dir):
        """
        Special dedupe handling for git bash PATH details

        :param path: git bash $PATH output
        :param venv_dir: regular windows style path to VENV
        :return: new git bash style path without duplicates
        """
        # The PATH environment variable on git bash needs to look more like a linux path
        drive, venv_dir = os.path.splitdrive(venv_dir)
        if ":" in drive:
            drive = drive.replace(":", "").lower()
            drive = f"/{drive}"
        venv_dir = venv_dir.replace("\\", "/")
        new_venv_bindir = "".join([drive, venv_dir])

        deduped_path = []

        components = [new_venv_bindir, *path.split(":")]
        for p in components:
            p = p.rstrip("/")  # Remove trailing slash
            if p and p not in deduped_path:
                deduped_path.append(p)

        return ":".join(deduped_path)
