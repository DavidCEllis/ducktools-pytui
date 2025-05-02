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

from ducktools.classbuilder.prefab import prefab

from .base import RuntimeManager, PythonListing


freethreaded_re = re.compile(r"^\d+.\d+t.*$")


class PythonCoreManager(RuntimeManager):
    organisation = "PythonCore"

    @functools.cached_property
    def executable(self):
        return shutil.which("pymanager")

    def fetch_installed(self) -> list[PythonCoreListing]:
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

    def fetch_downloads(self) -> list[PythonCoreListing]:
        cmd = [
            self.executable, "list", "--online", "--format=json",
        ]
        download_list_cmd = subprocess.run(
            cmd, capture_output=True, text=True, check=True,
        )
        json_data = json.loads(download_list_cmd.stdout)

        installed_keys = {v.key for v in self.fetch_installed()}

        # PythonEmbed used for embedded distributions
        # PythonTest used for distributions with tests
        # PythonCore are the ones we want
        arch = platform.machine()
        if arch == "AMD64":
            arch = "x86_64"

        download_listings = []
        for v in json_data.get("versions", []):
            # Already installed or test/docs releases - skip
            if v["id"] in installed_keys or v["company"] != "PythonCore":
                continue
            listing = PythonCoreListing.from_dict(manager=self, entry=v)

            # Don't list alternate architecture installs
            if listing.arch == arch:
                download_listings.append(listing)

        return download_listings


@prefab(kw_only=True)
class PythonCoreListing(PythonListing):
    name: str
    tag: str

    @classmethod
    def from_dict(cls, manager: PythonCoreManager, entry: dict):
        key = entry["id"]
        version = entry["sort-version"]
        name = entry["display-name"]

        implementation = "cpython"
        tag = entry["tag"]  # Used to install version
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
            implementation=implementation,
            variant=variant,
            tag=tag,
            path=path,
            url=url,
            arch=arch,
        )

    def install(self):
        if self.path:
            return None
        cmd = [
            self.manager.executable, "install", self.tag, "-y",
        ]
        subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )
        return " ".join(cmd)


    def uninstall(self):
        if not (self.path and os.path.exists(self.path)):
            return None
        cmd = [
            self.manager.executable, "uninstall", self.tag, "-y",
        ]
        subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )
        return " ".join(cmd)