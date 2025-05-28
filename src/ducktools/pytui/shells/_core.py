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

import os
import shutil
import sys
from typing import ClassVar

from ducktools.classbuilder.prefab import Prefab


from .. import _lazy_imports as _laz
from .._version import __version__
from ..platform_paths import SHELL_SCRIPT_FOLDER


class Shell(Prefab):
    registry: ClassVar[dict[str, type[Shell]]] = {}

    name: ClassVar[str] = ""  # Pretty Name
    bin_name: ClassVar[str] = ""  # Name of the binary
    exclude: ClassVar[bool] = False

    path: str

    def __init_subclass__(cls):
        if not cls.exclude:
            Shell.registry[cls.bin_name] = cls

    def get_venv_shell_command(
        self,
        env: dict[str, str]
    ) -> tuple[list[str], dict[str, str]]:  # pragma: no cover
        raise NotImplementedError("get_venv_shell_command must be implemented in subclasses")

    def get_env_path(self) -> str:
        """
        Get the PATH environment variable

        This exists as a method because some shells will have specific modified PATH
        variables.

        :return: PATH variable string
        """
        return os.environ.get("PATH", "")

    @staticmethod
    def get_deduped_path(path: str, venv_path: str) -> str:
        """
        Get the deduplicated PATH for an activated VENV

        This needs to be a shell dependent method as some shells such as git bash
        will need to have their own management

        :param path: The value of the PATH environment variable
        :param venv_path: The path to the venv's bin or Scripts folder
        :return: A new value for PATH
        """
        deduped_path = []

        # Add venv_path first, so it doesn't end up duplicated
        components = [venv_path, *path.split(os.pathsep)]
        for p in components:
            # Remove a trailing \ or / if it exists
            p = p.rstrip(os.path.sep)
            if p and p not in deduped_path:
                deduped_path.append(p)

        return os.pathsep.join(deduped_path)

    @classmethod
    def which(cls) -> Shell | None:
        """
        Get an instance of this shell type if it is on PATH

        :return: instance of shell type or None if the type is not on PATH
        """
        pth = shutil.which(cls.bin_name)
        if pth:
            return cls(pth)
        return None

    @classmethod
    def from_path(cls, path: str) -> Shell | None:
        name = os.path.basename(path)
        if sys.platform == "win32":
            name = name.lower()  # .EXE can come from which

        shell_type = Shell.registry.get(name)
        if shell_type:
            return shell_type(path)
        return None

    @classmethod
    def get_default(cls) -> Shell | None:
        shell = None
        # Check for SHELL environment variable
        if (shell_env := os.environ.get("SHELL")):
            shell = Shell.from_path(shell_env)

        # Attempt to find shells on PATH
        if shell is None:
            for shell_type in Shell.registry.values():
                shell = shell_type.which()
                if shell:
                    break
            else:
                if sys.platform == "win32":
                    shell_path = os.environ.get("COMSPEC")
                    if shell_path:
                        shell = Shell.from_path(shell_path)

        return shell


def get_shell_script(filename: str) -> str:
    """
    Get the path to the shell script in the SHELL_SCRIPT_FOLDER
    Extract it from the archive or venv folder if needed.

    ALWAYS overwrites the folder if the version does not match even if it is older.

    :param filename: Filename of the script in scripts/
    :return: Path to the file on the system
    """

    shell_script_verfile = os.path.join(SHELL_SCRIPT_FOLDER, ".version")
    valid_verfile = False
    try:
        with open(shell_script_verfile) as f:
            script_ver = f.read()
        if script_ver == __version__:
            valid_verfile = True
    except FileNotFoundError:
        pass

    if not valid_verfile:
        # Delete the old folder
        shutil.rmtree(SHELL_SCRIPT_FOLDER, ignore_errors=True)
        os.makedirs(SHELL_SCRIPT_FOLDER)

        # Get the 'folder' for the scripts directory
        script_folder = _laz.resources.files("ducktools.pytui.shells").joinpath("scripts")
        for script in script_folder.iterdir():
            dest = os.path.join(SHELL_SCRIPT_FOLDER, script.name)
            with _laz.resources.as_file(script) as source:
                shutil.copy(source, dest)

        # Write the version file script
        with open(shell_script_verfile, 'w') as f:
            f.write(__version__)

    script_file = os.path.join(SHELL_SCRIPT_FOLDER, filename)

    if not os.path.exists(script_file):
        raise FileNotFoundError(f"'{filename}' not found in '{SHELL_SCRIPT_FOLDER}'")

    return script_file
