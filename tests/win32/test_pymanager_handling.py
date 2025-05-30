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
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ducktools.pytui.runtime_installers.pythoncore import PythonCoreManager, PythonCoreListing

example_folder = Path(__file__).parents[1] / "example_data" / "win32"

@functools.lru_cache(maxsize=None)
def pymanager_download_json() -> str:
    return (example_folder / "pymanager_download_list.json").read_text()

@functools.lru_cache(maxsize=None)
def pymanager_install_json() -> str:
    return (example_folder / "pymanager_install_list.json").read_text()

@pytest.fixture()
def pymanager_installed_pythons():
    manager = PythonCoreManager()
    pys = [
        PythonCoreListing.from_dict(manager=manager, entry=v)
        for v in json.loads(pymanager_install_json()).get("versions", [])
    ]
    return pys


# noinspection PyPropertyAccess
def test_check_pymanager():
    manager = PythonCoreManager()
    with patch("shutil.which") as fake_which:
        fake_which.return_value = r"C:\Users\david\AppData\Local\Microsoft\WindowsApps\pymanager.exe"

        out = manager.executable

        fake_which.assert_called()
        assert out == r"C:\Users\david\AppData\Local\Microsoft\WindowsApps\pymanager.exe"

    del manager.executable

    with patch("shutil.which") as fake_which:
        fake_which.return_value = None

        out = manager.executable
        fake_which.assert_called()
        assert out is None

def test_fake_pymanager(pymanager_executable):
    manager = PythonCoreManager()
    assert manager.executable == "pymanager.exe"


def test_fetch_installed(pymanager_executable):
    with patch("subprocess.run") as fake_process:
        cmd_output = MagicMock()
        cmd_output.stdout = pymanager_install_json()
        fake_process.return_value = cmd_output

        manager = PythonCoreManager()

        installed_pys = manager.fetch_installed()

        fake_process.assert_called_once_with(
            [
                "pymanager.exe", "list", "--only-managed", "--format=json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        expected = [
            'pythoncore-3.13t-64',
            'pythoncore-3.12-64',
            'pythoncore-3.12-32',
            'pythoncore-3.12-arm64',
            'pythoncore-3.14-64',
        ]

        assert [p.key for p in installed_pys] == expected


def test_fetch_downloads(pymanager_executable, pymanager_installed_pythons):
    # Fake as AMD64 for filtering
    with patch("platform.machine") as machine_mock, \
        patch("subprocess.run") as fake_process, \
        patch.object(PythonCoreManager, "fetch_installed") as fake_installed:

        machine_mock.return_value = "AMD64"

        fake_installed.return_value = pymanager_installed_pythons

        cmd_output = MagicMock()
        cmd_output.stdout = pymanager_download_json()
        fake_process.return_value = cmd_output

        manager = PythonCoreManager()
        download_pys = manager.fetch_downloads()

        fake_installed.assert_called()
        fake_process.assert_called_once_with(
            ["pymanager.exe", "list", "--online", "--format=json"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Check values have been filtered
        for p in pymanager_installed_pythons:
            assert p.key not in download_pys

        expected = [
            "pythoncore-3.14t-64",
            "pythoncore-3.13-64",
            "pythoncore-3.11-64",
            "pythoncore-3.10-64",
            "pythoncore-3.9-64",
            "pythoncore-3.8-64",
            "pythoncore-3.7-64",
            "pythoncore-3.6-64",
            "pythoncore-3.5-64",
        ]

        assert [p.key for p in download_pys] == expected


def test_install(pymanager_executable):
    manager = PythonCoreManager()
    listing = PythonCoreListing(
        manager=manager,
        key='pythoncore-3.14-64',
        version='3.14.0b1',
        implementation='cpython',
        variant='default',
        arch='x86_64',
        path=None,
        url='https://www.python.org/ftp/python/3.14.0/python-3.14.0b1t-amd64.zip',
        name='Python 3.14.0b1',
        company="PythonCore",
        tag='3.14-dev-64',
        install_for=[
            "3.14.0b1-64",
            "3.14-64",
            "3-64",
            "3.14-dev-64",
            "3-dev-64",
        ]
    )

    with patch("subprocess.run") as fake_process, \
        patch.object(PythonCoreManager, "fetch_installed") as fake_installed:
        fake_installed.return_value = []
        listing.install()
        fake_process.assert_called_once_with(
            [
                "pymanager.exe", "install", "3.14.0b1-64", "-y"
            ],
            capture_output=True,
            text=True,
        )
