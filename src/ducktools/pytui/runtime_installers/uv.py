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

import functools
import json
import os.path
import shutil
import subprocess
from pathlib import Path
from typing import ClassVar


from ducktools.pythonfinder.shared import PythonInstall

from .base import RuntimeManager, PythonListing


class UVManager(RuntimeManager):
    organisation: ClassVar[str] = "Astral UV"

    @functools.cached_property
    def executable(self) -> str | None:
        return shutil.which("uv")

    @functools.cached_property
    def runtime_folder(self) -> str | None:
        try:
            cmd = subprocess.run(
                ["uv", "python", "dir"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            py_dir = None
        else:
            py_dir = cmd.stdout.strip()
        return py_dir

    def fetch_installed(self) -> list[UVPythonListing]:
        """
        Fetch Python installs managed by UV
        """
        installed_list_cmd = subprocess.run(
            [
                self.executable, "python", "list",
                "--output-format", "json",
                "--only-installed",
                "--python-preference", "only-managed",
                "--all-versions",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        json_data = json.loads(installed_list_cmd.stdout)
        installed_pys = [
            UVPythonListing.from_dict(manager=self, entry=v) for v in json_data
        ]

        return installed_pys

    def fetch_downloads(self, all_versions=False) -> list[UVPythonListing]:
        """
        Get available UV downloads and filter out any installs that are already present.

        :param all_versions: Include *ALL* possible installs
        :return: list of possible python installs
        """
        cmd = [
            self.executable, "python", "list",
            "--output-format", "json",
            "--only-downloads",
        ]
        if all_versions:
            cmd.append("--all-versions")

        download_list_cmd = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        full_download_list = json.loads(download_list_cmd.stdout)

        installed_keys = {v.key for v in self.fetch_installed()}

        download_listings = [
            UVPythonListing.from_dict(manager=self, entry=v) for v in full_download_list
            if v["key"] not in installed_keys
        ]

        return download_listings

    def find_matching_listing(self, install: PythonInstall) -> UVPythonListing | None:
        if install.managed_by is None or not install.managed_by.startswith("Astral"):
            return None

        # Executable names may not match, one may find python.exe, the other pypy.exe
        # Use the parent folder.
        installed_dict = {
            os.path.dirname(os.path.abspath(py.path)): py
            for py in self.fetch_installed()
        }

        install_path = os.path.dirname(install.executable)

        return installed_dict.get(install_path, None)


class UVPythonListing(PythonListing, kw_only=True):
    manager: UVManager

    # These extra parts are UV Specific
    version_parts: dict
    path: str | None
    symlink: str | None
    url: str | None
    os: str
    libc: str | None  # Apparently this is the string "none" instead of an actual None.

    def __prefab_post_init__(self, key: str, path: str | None) -> None:
        if path is None:
            self.key = key
            self.path = path
        else:
            # Resolve path always, sometimes UV gives a relative path to cwd.
            self.path = os.path.abspath(path)

            # UV bug - key and path can mismatch if someone typoed the metadata
            base_path = self.manager.runtime_folder
            key_path = str(Path(self.path).relative_to(base_path).parts[0])
            self.key = key if key == key_path else key_path

    def install(self):
        if self.path:
            # Can't install already installed Python
            return None

        cmd = [
            self.manager.executable, "python", "install",
            self.key,
            "--color", "never",
            "--no-progress",
        ]
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return " ".join(cmd)


    def uninstall(self):
        if not self.path:
            # Can't uninstall non-installed Python
            return None

        cmd = [
            self.manager.executable, "python", "uninstall",
            self.key,
            "--color", "never",
            "--no-progress",
        ]
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return " ".join(cmd)