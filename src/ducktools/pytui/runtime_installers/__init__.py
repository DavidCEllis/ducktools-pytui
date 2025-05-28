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
from functools import lru_cache

from ducktools.pythonfinder import PythonInstall

from .base import PythonListing, RuntimeManager

# Windows python installer should come before UV if available
if sys.platform == "win32":
    from . import pythoncore as pythoncore
    from . import uv as uv
else:
    from . import uv as uv


@lru_cache(maxsize=None)
def get_managers() -> list[RuntimeManager]:
    managers = []
    for m in RuntimeManager.available_managers:
        inst = m()
        if inst.executable:
            managers.append(inst)
    return managers


def fetch_downloads() -> list[PythonListing]:
    downloads = []
    for m in get_managers():
        downloads.extend(m.fetch_downloads())

    return downloads


def find_matching_listing(install: PythonInstall) -> PythonListing | None:
    for manager in get_managers():
        listing = manager.find_matching_listing(install)
        if listing:
            break
    else:
        listing = None

    return listing
