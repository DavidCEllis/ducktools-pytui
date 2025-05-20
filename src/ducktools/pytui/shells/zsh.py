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

import sys

from ._core import Shell


class ZShell(Shell):
    name = "Z shell"
    bin_name = "zsh"
    exclude = (sys.platform == "win32")

    def get_venv_shell_command(self, env):
        base_prompt = "%n@%m:%~/ >"  # The SUSE prompt theme
        venv_prompt = env["PYTUI_VIRTUAL_ENV_PROMPT"]
        prompt = f"({venv_prompt}) {base_prompt} "

        cmd = [self.path, "--no-rcs"]

        # Set all environment variables here
        env_updates = {
            "PATH": env["PYTUI_PATH"],
            "VIRTUAL_ENV": env["PYTUI_VIRTUAL_ENV"],
            "VIRTUAL_ENV_PROMPT": env["PYTUI_VIRTUAL_ENV_PROMPT"],
            "PS1": prompt,
        }

        return cmd, env_updates
