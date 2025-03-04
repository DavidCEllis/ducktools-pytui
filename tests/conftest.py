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
import sys
from unittest.mock import patch

import pytest

from ducktools.pytui.runtime_installers import uv

@pytest.fixture(scope="function")
def uv_python_dir():
    with patch.object(uv, "uv_python_dir") as fake_py_dir:
        if sys.platform == "win32":
            fake_py_dir.return_value = "C:\\Users\\ducks\\AppData\\Roaming\\uv\\python"
        else:
            fake_py_dir.return_value = "/home/david/.local/share/uv/python"
        yield
