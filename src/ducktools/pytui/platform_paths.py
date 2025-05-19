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

import shutil
import sys
import os, os.path


__all__ = [
    "USER_FOLDER",
    "SHELL_SCRIPT_FOLDER",
    "PYTUI_FOLDER",
    "GLOBAL_VENV_FOLDER",
    "CONFIG_FILE",
]


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
    # On windows PYTUI and Config folders are the same
    PYTUI_FOLDER = os.path.join(USER_FOLDER, "ducktools", "pytui")
    CONFIG_FOLDER = PYTUI_FOLDER
    GLOBAL_VENV_FOLDER = os.path.join(PYTUI_FOLDER, "venvs")
else:
    USER_FOLDER = os.path.expanduser("~")

    # Versions prior to 0.1.3 used this old folder
    OLD_FOLDER = os.path.join(USER_FOLDER, ".ducktools", "pytui")

    CONFIG_FOLDER = os.path.join(USER_FOLDER, ".config", "ducktools", "pytui")
    PYTUI_FOLDER = os.path.join(USER_FOLDER, ".local", "share", "ducktools", "pytui")
    GLOBAL_VENV_FOLDER = os.path.join(PYTUI_FOLDER, "venvs")

    # If you used a version prior to v0.1.3
    if os.path.exists(OLD_FOLDER):

        # Move the folder if the new one doesn't already exist, otherwise leave it
        if not os.path.exists(CONFIG_FOLDER):
            os.makedirs(os.path.dirname(CONFIG_FOLDER), exist_ok=True)
            shutil.move(OLD_FOLDER, CONFIG_FOLDER)

CONFIG_FILE = os.path.join(CONFIG_FOLDER, "config.json")
SHELL_SCRIPT_FOLDER = os.path.join(PYTUI_FOLDER, "shell_scripts")
