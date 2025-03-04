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
import functools
import json
import os.path
import subprocess
from pathlib import Path


from ducktools.classbuilder.prefab import Prefab, attribute, get_attributes
from ducktools.pythonfinder.shared import version_str_to_tuple, PythonInstall


@functools.cache
def uv_python_dir() -> str | None:
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


@functools.cache
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
    libc: str | None  # Apparently this is the string "none" instead of an actual None.
    _version_tuple: tuple[int, int, int, str, int] | None = attribute(default=None, private=True)

    def __prefab_post_init__(self, key: str) -> None:
        # UV bug - key and path can mismatch if someone typoed the metadata
        if self.path is None:
            self.key = key
        else:
            base_path = uv_python_dir()
            key_path = str(Path(self.path).relative_to(base_path).parts[0])
            self.key = key if key == key_path else key_path

    @property
    def version_tuple(self) -> tuple[int, int, int, str, int]:
        if not self._version_tuple:
            self._version_tuple = version_str_to_tuple(self.version)
        return self._version_tuple

    @classmethod
    def from_dict(cls, entry: dict):
        # designed to not fail if extra keys are added
        attrib_names = set(get_attributes(cls))

        kwargs = entry.copy()
        for key in entry.keys():
            if key not in attrib_names:
                del kwargs[key]

        return cls(**kwargs)


def fetch_installed() -> list[UVPythonListing]:
    """
    Fetch Python installs managed by UV
    :return:
    """
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
    json_data = json.loads(installed_list_cmd.stdout)
    installed_pys = [
        UVPythonListing.from_dict(v) for v in json_data
    ]

    return installed_pys


def fetch_downloads(all_versions=False) -> list[UVPythonListing]:
    """
    Get available UV downloads and filter out any installs that are already present.

    :param all_versions: Include *ALL* possible installs
    :return: list of possible python installs
    """
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
    full_download_list = json.loads(download_list_cmd.stdout)

    installed_keys = {v.key for v in fetch_installed()}

    download_listings = [
        UVPythonListing.from_dict(v) for v in full_download_list
        if v["key"] not in installed_keys
    ]

    return download_listings


def find_matching_listing(install: PythonInstall) -> UVPythonListing | None:
    if install.managed_by is None or not install.managed_by.startswith("Astral"):
        return None

    # Executable names may not match, one may find python.exe, the other pypy.exe
    # Use the parent folder.
    installed_dict = {
        os.path.dirname(os.path.abspath(py.path)): py
        for py in fetch_installed()
    }

    install_path = os.path.dirname(install.executable)

    return installed_dict.get(install_path, None)


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
