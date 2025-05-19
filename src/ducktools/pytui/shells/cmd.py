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

from ._core import Shell


class CMDShell(Shell):
    name = "Command Prompt"
    bin_name = "cmd.exe"

    def get_venv_shell_command(self, env):
        shell_prompt = env.get("PROMPT", "$P$G")
        old_venv_prompt = env.get("VIRTUAL_ENV_PROMPT")
        new_venv_prompt = env["PYTUI_VIRTUAL_ENV_PROMPT"]


        if old_venv_prompt and old_venv_prompt in shell_prompt:
            new_prompt = shell_prompt.replace(old_venv_prompt, new_venv_prompt)
        else:
            new_prompt = f"({new_venv_prompt}) {shell_prompt}"

        cmd = [self.path, "/k"]
        env_updates = {
            "PATH": env["PYTUI_PATH"],
            "VIRTUAL_ENV": env["PYTUI_VIRTUAL_ENV"],
            "VIRTUAL_ENV_PROMPT": env["PYTUI_VIRTUAL_ENV_PROMPT"],
            "PROMPT": new_prompt,
        }

        return cmd, env_updates
