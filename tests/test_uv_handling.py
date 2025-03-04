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
import sys
import subprocess

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ducktools.pythonfinder import PythonInstall
from ducktools.pytui.runtime_installers import uv
from ducktools.pytui.runtime_installers.uv import UVPythonListing

if sys.platform == "win32":
    example_folder = Path(__file__).parent / "example_data" / "win32"
else:
    example_folder = Path(__file__).parent / "example_data"


@functools.cache
def uv_download_json() -> str:
    return (example_folder / "uv_download_list.json").read_text()


@functools.cache
def uv_install_json() -> str:
    return (example_folder / "uv_install_list.json").read_text()


@pytest.fixture()
def uv_installed_pythons(uv_python_dir) -> list[uv.UVPythonListing]:
    pys = [uv.UVPythonListing.from_dict(v) for v in json.loads(uv_install_json())]
    return pys


def test_check_uv():
    with patch("subprocess.run") as fake_process:
        cmd_output = MagicMock()
        cmd_output.stdout = "uv 0.6.4 (04db70662 2025-03-03)\n"
        fake_process.return_value = cmd_output

        out = uv.check_uv()
        fake_process.assert_called()
        assert out is True

    uv.check_uv.cache_clear()

    with patch("subprocess.run", side_effect=FileNotFoundError) as fake_process:
        out = uv.check_uv()
        fake_process.assert_called()
        assert out is False

    uv.check_uv.cache_clear()

    with patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(1, ""),
    ) as fake_process:
        out = uv.check_uv()
        fake_process.assert_called()
        assert out is False

    uv.check_uv.cache_clear()


def test_uv_python_dir():
    if sys.platform == "win32":
        base = "C:\\Users\\ducks\\AppData\\Roaming\\uv\\python"
    else:
        base = "/home/david/.local/share/uv/python"

    with patch("subprocess.run") as fake_process:
        cmd_output = MagicMock()
        cmd_output.stdout = f"{base}\n"
        fake_process.return_value = cmd_output

        out = uv.uv_python_dir()
        fake_process.assert_called()
        assert out == base

    uv.uv_python_dir.cache_clear()

    with patch("subprocess.run", side_effect=FileNotFoundError) as fake_process:
        out = uv.uv_python_dir()
        fake_process.assert_called()
        assert out is None

    uv.uv_python_dir.cache_clear()

    with patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(1, ""),
    ) as fake_process:
        out = uv.uv_python_dir()
        fake_process.assert_called()
        assert out is None

    uv.uv_python_dir.cache_clear()


def test_fetch_installed(uv_python_dir):
    with patch("subprocess.run") as fake_process:
        cmd_output = MagicMock()
        cmd_output.stdout = uv_install_json()
        fake_process.return_value = cmd_output

        installed_pys = uv.fetch_installed()

        fake_process.assert_called_once_with(
            [
                "uv",
                "python",
                "list",
                "--output-format",
                "json",
                "--only-installed",
                "--python-preference",
                "only-managed",
                "--all-versions",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

    if sys.platform == "win32":
        expected = [
            "cpython-3.14.0a5-windows-x86_64-none",
            "cpython-3.14.0a4-windows-x86_64-none",
            "cpython-3.13.2-windows-x86_64-none",
            "cpython-3.12.9-windows-x86_64-none",
            "cpython-3.11.11-windows-x86_64-none",
            "cpython-3.10.16-windows-x86_64-none",
            "cpython-3.9.21-windows-x86_64-none",
            "cpython-3.8.20-windows-x86_64-none",
            "pypy-3.11.11-windows-x86_64-none",
            # Note this final entry is *not* the key the list command reports
            # But is actually the key needed to uninstall correctly
            "pypy-3.10.19-windows-x86_64-none",
        ]
    else:
        expected = [
            "cpython-3.14.0a5-linux-x86_64-gnu",
            "cpython-3.14.0a4-linux-x86_64-gnu",
            "cpython-3.13.2-linux-x86_64-gnu",
            "cpython-3.12.9-linux-x86_64-gnu",
            "cpython-3.11.11-linux-x86_64-gnu",
            "cpython-3.10.16-linux-x86_64-gnu",
            "cpython-3.9.21-linux-x86_64-gnu",
            "cpython-3.8.20-linux-x86_64-gnu",
            "pypy-3.11.11-linux-x86_64-gnu",
            "pypy-3.10.19-linux-x86_64-gnu",
        ]

    assert [p.key for p in installed_pys] == expected


def test_fetch_downloads(uv_python_dir, uv_installed_pythons):
    with (
        patch("subprocess.run") as fake_process,
        patch.object(uv, "fetch_installed") as fake_installed,
    ):
        fake_installed.return_value = uv_installed_pythons

        cmd_output = MagicMock()
        cmd_output.stdout = uv_download_json()
        fake_process.return_value = cmd_output

        download_pys = uv.fetch_downloads()

        fake_installed.assert_called()
        fake_process.assert_called_once_with(
            [
                "uv",
                "python",
                "list",
                "--output-format",
                "json",
                "--only-downloads",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

    if sys.platform == "win32":
        expected = [
            "cpython-3.14.0a5+freethreaded-windows-x86_64-none",
            "cpython-3.13.2+freethreaded-windows-x86_64-none",
            "cpython-3.7.9-windows-x86_64-none",
            "pypy-3.9.19-windows-x86_64-none",
            "pypy-3.8.16-windows-x86_64-none",
            "pypy-3.7.13-windows-x86_64-none",
        ]

    else:
        expected = [
            "cpython-3.14.0a5+freethreaded-linux-x86_64-gnu",
            "cpython-3.13.2+freethreaded-linux-x86_64-gnu",
            "cpython-3.7.9-linux-x86_64-gnu",
            "pypy-3.9.19-linux-x86_64-gnu",
            "pypy-3.8.16-linux-x86_64-gnu",
            "pypy-3.7.13-linux-x86_64-gnu",
        ]

    assert [p.key for p in download_pys] == expected


@pytest.mark.skipif(sys.platform != "win32", reason="Windows version of test")
def test_find_matching_listing_win(uv_installed_pythons):
    inst_313 = PythonInstall(
        version=(3, 13, 2, "final", 0),
        executable="C:\\Users\\ducks\\AppData\\Roaming\\uv\\python\\cpython-3.13.2-windows-x86_64-none\\python.exe",
        architecture="64bit",
        implementation="cpython",
        managed_by="Astral UV",
        metadata={"freethreaded": False},
        shadowed=False,
    )

    # Due to a metadata error, UV installs/uninstalls this as 3.10.19, but lists it as 3.10.16
    # 3.10.19 is the key we need, so make sure we still get the useful key even if it isn't the right version.
    pypy_310 = PythonInstall(
        version=(3, 10, 16, "final", 0),
        executable="C:\\Users\\ducks\\AppData\\Roaming\\uv\\python\\pypy-3.10.19-windows-x86_64-none\\python.exe",
        architecture="64bit",
        implementation="pypy",
        managed_by="Astral UV",
        metadata={"pypy_version": (7, 3, 19, "final", 0)},
        shadowed=False,
    )

    windows_install = PythonInstall(
        version=(3, 13, 1, "final", 0),
        executable="C:\\Users\\ducks\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
        architecture="64bit",
        implementation="cpython",
        managed_by="PythonCore",
        metadata={
            "Company": "PythonCore",
            "CompanyDisplayName": "Python Software Foundation",
            "CompanySupportUrl": "https://www.python.org/",
            "Tag": "3.13",
            "DisplayName": "Python 3.13 (64-bit)",
            "SupportUrl": "https://www.python.org/",
            "Version": "3.13.1",
            "SysVersion": "3.13",
            "SysArchitecture": "64bit",
            "InWindowsRegistry": True,
        },
        shadowed=False,
    )

    with patch.object(uv, "fetch_installed") as fake_installed:
        fake_installed.return_value = uv_installed_pythons

        uv_313 = uv.find_matching_listing(inst_313)

        assert uv_313.key == "cpython-3.13.2-windows-x86_64-none"

        uv_pypy_310 = uv.find_matching_listing(pypy_310)

        assert uv_pypy_310.key == "pypy-3.10.19-windows-x86_64-none"

        non_uv = uv.find_matching_listing(windows_install)

        assert non_uv is None


@pytest.mark.skipif(sys.platform == "win32", reason="Non-windows version of test")
def test_find_matching_listing_nonwin(uv_installed_pythons):
    inst_313 = PythonInstall(
        version=(3, 13, 2, "final", 0),
        executable="/home/david/.local/share/uv/python/cpython-3.13.2-linux-x86_64-gnu/bin/python",
        architecture="64bit",
        implementation="cpython",
        managed_by="Astral UV",
        metadata={"freethreaded": False},
        shadowed=False,
    )

    # Due to a metadata error, UV installs/uninstalls this as 3.10.19, but lists it as 3.10.16
    # 3.10.19 is the key we need, so make sure we still get the useful key even if it isn't the right version.
    pypy_310 = PythonInstall(
        version=(3, 10, 16, "final", 0),
        executable="/home/david/.local/share/uv/python/pypy-3.10.19-linux-x86_64-gnu/bin/python",
        architecture="64bit",
        implementation="pypy",
        managed_by="Astral UV",
        metadata={"pypy_version": (7, 3, 18, "final", 0)},
        shadowed=False,
    )

    pyenv_install = PythonInstall(
        version=(3, 13, 2, "final", 0),
        executable="/home/david/.pyenv/versions/3.13.2/bin/python",
        architecture="64bit",
        implementation="cpython",
        managed_by="pyenv",
        metadata={"freethreaded": False},
        shadowed=False,
    )

    with patch.object(uv, "fetch_installed") as fake_installed:
        fake_installed.return_value = uv_installed_pythons

        uv_313 = uv.find_matching_listing(inst_313)

        assert uv_313.key == "cpython-3.13.2-linux-x86_64-gnu"

        uv_pypy_310 = uv.find_matching_listing(pypy_310)

        assert uv_pypy_310.key == "pypy-3.10.19-linux-x86_64-gnu"

        non_uv = uv.find_matching_listing(pyenv_install)

        assert non_uv is None


def test_install(uv_python_dir):
    listing = UVPythonListing(
        key="cpython-3.14.0a5+freethreaded-windows-x86_64-none",
        version="3.14.0a5",
        version_parts={"major": 3, "minor": 14, "patch": 0},
        path=None,
        symlink=None,
        url="https://github.com/astral-sh/python-build-standalone/releases/download/20250212/cpython-3.14.0a5%2B20250212-x86_64-pc-windows-msvc-freethreaded%2Bpgo-full.tar.zst",
        os="windows",
        variant="freethreaded",
        implementation="cpython",
        arch="x86_64",
        libc="none",
    )
    with patch("subprocess.run") as fake_process:
        output = uv.install_python(listing)

        fake_process.assert_called_once_with(
            [
                "uv",
                "python",
                "install",
                listing.key,
                "--color",
                "never",
                "--no-progress",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        assert output == (
            "uv python install cpython-3.14.0a5+freethreaded-windows-x86_64-none --color never --no-progress"
        )


def test_uninstall(uv_python_dir):
    if sys.platform == "win32":
        py_path = "C:\\Users\\ducks\\AppData\\Roaming\\uv\\python\\cpython-3.13.2-windows-x86_64-none\\python.exe"
    else:
        # Yes this install path makes no sense
        # But it simplifies the amount of platform specific work needed
        py_path = "/home/david/.local/share/uv/python/cpython-3.13.2-windows-x86_64-none/bin/python3.13"

    listing = UVPythonListing(
        key="cpython-3.13.2-windows-x86_64-none",
        version="3.13.2",
        version_parts={"major": 3, "minor": 13, "patch": 2},
        path=py_path,
        symlink=None,
        url=None,
        os="windows",
        variant="default",
        implementation="cpython",
        arch="x86_64",
        libc="none",
    )

    with patch("subprocess.run") as fake_process:
        output = uv.uninstall_python(listing)

        fake_process.assert_called_once_with(
            [
                "uv",
                "python",
                "uninstall",
                listing.key,
                "--color",
                "never",
                "--no-progress",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        assert output == (
            "uv python uninstall cpython-3.13.2-windows-x86_64-none --color never --no-progress"
        )
