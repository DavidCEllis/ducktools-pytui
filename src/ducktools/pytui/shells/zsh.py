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

from ._shell_core import Shell, get_shell_script


class ZshShell(Shell):
    name = "Z shell"
    bin_name = "zsh"
    exclude = (sys.platform == "win32")

    def get_venv_shell_command(self, env):
        zshrc_script = get_shell_script("zsh/.zshrc")

        cmd = [self.path]
        # for zsh, make the folder to check for .zshrc our script
        # That sets the extra environment variables
        env_updates = {
            "ZDOTDIR": os.path.dirname(zshrc_script),
        }

        if old_zdotdir := env.get("ZDOTDIR"):
            env["OLD_ZDOTDIR"] = old_zdotdir

        return cmd, env_updates
