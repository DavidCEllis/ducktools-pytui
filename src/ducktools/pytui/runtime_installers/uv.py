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
import json
import os.path
import subprocess

from ducktools.classbuilder.prefab import Prefab, attribute
from ducktools.pythonfinder.shared import version_str_to_tuple, PythonInstall


def check_uv() -> bool:
    """
    Checks if UV is available on Path.
    Just runs the '-v' version command.
    """
    try:
        subprocess.run(["uv", "-V"], check=True, capture_output=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    return True


class UVPythonListing(Prefab):
    # This is just a conversion of the json outputs frorm uv python list
    key: str
    version: str
    version_parts: dict
    path: str | None
    symlink: str | None
    url: str | None
    os: str
    variant: str
    implementation: str
    arch: str
    libc: str | None  # Apparently this is the string "none" instead of an actual None?
    _version_tuple: tuple[int, int, int, str, int] | None = attribute(default=None, private=True)

    def __prefab_post_init__(self, libc):
        # UV bug? gives this as a str instead of an actual None value
        self.libc = None if libc == "none" else libc

    @property
    def version_tuple(self):
        if not self._version_tuple:
            self._version_tuple = version_str_to_tuple(self.version)
        return self._version_tuple


def fetch_downloads(all_versions=False) -> list[UVPythonListing]:
    # Get the download and install lists to filter out already installed versions
    cmd = [
        "uv", "python", "list",
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
    installed_list_cmd = subprocess.run(
        [
            "uv", "python", "list",
            "--output-format", "json",
            "--only-installed",
            "--python-preference", "only-managed",
            "--all-versions",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    installed_keys = {
        v["key"] for v in json.loads(installed_list_cmd.stdout)
    }

    full_download_list = json.loads(download_list_cmd.stdout)

    download_listings = [
        UVPythonListing(**v) for v in full_download_list
        if v["key"] not in installed_keys
    ]

    return download_listings

def find_matching_listing(install: PythonInstall) -> UVPythonListing | None:
    if not install.managed_by.startswith("Astral"):
        return None

    # Get astral listings based on search
    installed_list_cmd = subprocess.run(
        [
            "uv", "python", "list",
            "--output-format", "json",
            "--only-installed",
            "--python-preference", "only-managed",
            "--all-versions",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    installed_dict = {
        os.path.dirname(os.path.realpath(v["path"])): UVPythonListing(**v)
        for v in json.loads(installed_list_cmd.stdout)
    }
    return installed_dict.get(os.path.dirname(install.executable), None)


def install_python(listing: UVPythonListing):
    cmd = [
        "uv", "python", "install",
        listing.key,
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

def uninstall_python(listing: UVPythonListing):
    cmd = [
        "uv", "python", "uninstall",
        listing.key,
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
