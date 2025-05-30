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

# Handle the Windows python PyManager
from __future__ import annotations

import functools
import json
import os.path
import platform
import re
import shutil
import subprocess

from typing import ClassVar

from ducktools.classbuilder.prefab import prefab

from .base import RuntimeManager, PythonListing


freethreaded_re = re.compile(r"^\d+.\d+t.*$")


class PythonCoreManager(RuntimeManager):
    organisation: ClassVar[str] = "PythonCore"

    @functools.cached_property
    def executable(self):
        return shutil.which("pymanager")

    def fetch_installed(self):
        cmd = [
            self.executable, "list", "--only-managed", "--format=json",
        ]
        installed_list_cmd = subprocess.run(
            cmd, capture_output=True, text=True, check=True,
        )
        json_data = json.loads(installed_list_cmd.stdout)
        installed_pys = [
            PythonCoreListing.from_dict(manager=self, entry=v)
            for v in json_data.get("versions", [])
        ]
        return installed_pys

    @functools.lru_cache(maxsize=None)
    def _get_download_cache(self):
        """
        Get the raw unfiltered download list.
        This is cached to avoid repeated calls to PyManager for downloads.
        This data should only change on new Python releases.

        :return: List of PythonCoreListings for all downloads
        """
        cmd = [
            self.executable, "list", "--online", "--format=json",
        ]
        download_list_cmd = subprocess.run(
            cmd, capture_output=True, text=True, check=True,
        )
        json_data = json.loads(download_list_cmd.stdout)

        downloads = [
            PythonCoreListing.from_dict(manager=self, entry=v)
            for v in json_data.get("versions", [])
        ]

        return downloads

    def fetch_downloads(self):
        """
        Get the filtered list of downloads, with installed versions removed.

        :return: filtered download list
        """
        downloads = self._get_download_cache()

        installed_versions = {(v.key, v.version) for v in self.fetch_installed()}

        # PythonEmbed used for embedded distributions
        # PythonTest used for distributions with tests
        # PythonCore are the ones we want
        arch = platform.machine()
        if arch == "AMD64":
            arch = "x86_64"

        download_listings = [
            v
            for v in downloads
            if (v.key, v.version) not in installed_versions
            and v.company == "PythonCore"
            and v.arch == arch
        ]

        return self.sort_listings(download_listings)


@prefab(kw_only=True)
class PythonCoreListing(PythonListing):
    manager: PythonCoreManager

    name: str
    tag: str
    company: str
    install_for: list[str]

    @classmethod
    def from_dict(cls, manager: PythonCoreManager, entry: dict):
        key = entry["id"]
        version = entry["sort-version"]
        name = entry["display-name"]
        company = entry["company"]

        implementation = "cpython"
        tag = entry["tag"]
        install_for = entry["install-for"]
        variant = "freethreaded" if freethreaded_re.match(tag) else "default"
        path = entry.get("executable")
        url = entry.get("url")

        # Fix up non-existent paths
        if not (path and os.path.exists(path)):
            path = None

        if "-32" in key:
            arch = "x86"
        elif "-arm64" in key:
            arch = "ARM64"
        else:
            arch = "x86_64"

        return cls(
            manager=manager,
            key=key,
            version=version,
            name=name,
            company=company,
            implementation=implementation,
            variant=variant,
            tag=tag,
            install_for=install_for,
            path=path,
            url=url,
            arch=arch,
        )

    @property
    def will_overwrite(self):
        for v in self.manager.fetch_installed():
            if self.tag == v.tag:
                return True
        return False

    def install(self):
        if self.path:
            return None

        # Guard against empty list
        if self.install_for:
            tag = self.install_for[0]
        else:
            tag = self.tag

        cmd = [
            self.manager.executable, "install", tag, "-y",
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True
        )
        return result


    def uninstall(self):
        if not (self.path and os.path.exists(self.path)):
            return None

        # Guard against empty list
        if self.install_for:
            tag = self.install_for[0]
        else:
            tag = self.tag

        cmd = [
            self.manager.executable, "uninstall", tag, "-y",
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True
        )
        return result
