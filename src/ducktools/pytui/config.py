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
import json
from typing import ClassVar

from ducktools.classbuilder.prefab import Prefab, as_dict, attribute


from .platform_paths import (
    CONFIG_FILE, GLOBAL_VENV_FOLDER,
)


class Config(Prefab):
    VENV_SEARCH_MODES: ClassVar[set[str]] = {
        "cwd", "parents", "recursive", "recursive_parents"
    }
    config_file: str = attribute(default=CONFIG_FILE, serialize=False)
    venv_search_mode: str = "parents"
    include_pip: bool = True
    latest_pip: bool = True
    global_venv_folder: str = GLOBAL_VENV_FOLDER

    def write_config(self):
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(as_dict(self), f, indent=4)

    @classmethod
    def from_file(cls, config_file=CONFIG_FILE):
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                try:
                    raw_input = json.load(f)
                except json.JSONDecodeError:
                    raw_input = {}

            venv_search_mode = raw_input.get("venv_search_mode", "parents")
            include_pip = raw_input.get("include_pip", True)
            latest_pip = raw_input.get("latest_pip", True)
            global_venv_folder = raw_input.get("global_venv_folder", GLOBAL_VENV_FOLDER)

            if venv_search_mode not in cls.VENV_SEARCH_MODES:
                venv_search_mode = "parents"
            if not isinstance(include_pip, bool):
                include_pip = True
            if not isinstance(latest_pip, bool):
                latest_pip = True

            config = cls(
                config_file=config_file,
                venv_search_mode=venv_search_mode,
                include_pip=include_pip,
                latest_pip=latest_pip,
                global_venv_folder=global_venv_folder,
            )

            if raw_input != as_dict(config):
                config.write_config()

        else:
            config = cls(config_file=config_file)
            config.write_config()
        return config
