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
import sys

from ducktools.pytui import config

def test_folder():
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        assert config.CONFIG_FILE == os.path.join(base, "ducktools", "pytui", "config.json")
    else:
        assert config.CONFIG_FILE == os.path.expanduser("~/.config/ducktools/pytui/config.json")
