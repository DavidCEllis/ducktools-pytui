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
from unittest.mock import patch, PropertyMock

import pytest

from ducktools.pytui.runtime_installers import uv

collect_ignore_glob = []

if sys.platform != "win32":
    collect_ignore_glob.append("**/win32/*")
else:
    collect_ignore_glob.append("**/posix/*")


@pytest.fixture(scope="function")
def uv_executable():
    with patch.object(uv.UVManager, "executable", new_callable=PropertyMock) as fake_uv:
        fake_uv.return_value = "uv"
        yield


@pytest.fixture(scope="function")
def uv_python_dir():
    with patch.object(uv.UVManager, "runtime_folder", new_callable=PropertyMock) as fake_py_dir:
        if sys.platform == "win32":
            fake_py_dir.return_value = "C:\\Users\\ducks\\AppData\\Roaming\\uv\\python"
        else:
            fake_py_dir.return_value = "/home/david/.local/share/uv/python"
        yield
