# This file is a part of ducktools.pytui
# A TUI for managing Python installs and virtual environments
#
# Copyright (C) 2025  David C Ellis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os
import os.path
import json
import sys
from typing import ClassVar

from ducktools.classbuilder.prefab import Prefab, as_dict, attribute


# Code to work out where to store data
# Store in LOCALAPPDATA for windows, User folder for other operating systems
if sys.platform == "win32":
    # os.path.expandvars will actually import a whole bunch of other modules
    # Try just using the environment.
    if _local_app_folder := os.environ.get("LOCALAPPDATA"):
        if not os.path.isdir(_local_app_folder):
            raise FileNotFoundError(
                f"Could not find local app data folder {_local_app_folder}"
            )
    else:
        raise EnvironmentError(
            "Environment variable %LOCALAPPDATA% "
            "for local application data folder location "
            "not found"
        )
    USER_FOLDER = _local_app_folder
    PYTUI_FOLDER = os.path.join(USER_FOLDER, "ducktools", "pytui")
else:
    USER_FOLDER = os.path.expanduser("~")

    # Versions prior to 0.1.3 used this old folder
    OLD_FOLDER = os.path.join(USER_FOLDER, ".ducktools", "pytui")
    PYTUI_FOLDER = os.path.join(USER_FOLDER, ".config", "ducktools", "pytui")

    # If you used a version prior to v0.1.3
    if os.path.exists(OLD_FOLDER):
        import shutil

        # Delete the old folder if the new one already exists, move otherwise
        if os.path.exists(PYTUI_FOLDER):
            shutil.rmtree(OLD_FOLDER)
        else:
            os.makedirs(os.path.dirname(PYTUI_FOLDER), exist_ok=True)
            shutil.move(OLD_FOLDER, PYTUI_FOLDER)


CONFIG_FILE = os.path.join(PYTUI_FOLDER, "config.json")


class Config(Prefab):
    VENV_SEARCH_MODES: ClassVar[set[str]] = {
        "cwd", "parents", "recursive", "recursive_parents"
    }
    config_file: str = attribute(default=CONFIG_FILE, serialize=False)
    venv_search_mode: str = "parents"
    fast_runtime_search: bool = False
    include_pip: bool = True
    latest_pip: bool = True

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
            fast_runtime_search = raw_input.get("fast_runtime_search", False)
            include_pip = raw_input.get("include_pip", True)
            latest_pip = raw_input.get("latest_pip", True)

            if venv_search_mode not in cls.VENV_SEARCH_MODES:
                venv_search_mode = "parents"
            if not isinstance(fast_runtime_search, bool):
                fast_runtime_search = False
            if not isinstance(include_pip, bool):
                include_pip = True
            if not isinstance(latest_pip, bool):
                latest_pip = True

            config = cls(
                config_file=config_file,
                venv_search_mode=venv_search_mode,
                fast_runtime_search=fast_runtime_search,
                include_pip=include_pip,
                latest_pip=latest_pip,
            )

            if raw_input != as_dict(config):
                config.write_config()

        else:
            config = cls(config_file=config_file)
            config.write_config()
        return config
