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
from __future__ import annotations

import functools
from abc import ABC, abstractmethod
from typing import ClassVar

from ducktools.pythonfinder.shared import PythonInstall, version_str_to_tuple
from ducktools.classbuilder.prefab import Prefab, attribute, get_attributes


class RuntimeManager(ABC):
    available_managers: ClassVar[list[type[RuntimeManager]]] = []
    organisation: ClassVar[str | None] = None

    def __init_subclass__(cls):
        RuntimeManager.available_managers.append(cls)

    @functools.cached_property
    @abstractmethod
    def executable(self) -> str | None:
        """
        Get the path to the manager executable or None if it is not installed
        """
        ...

    @functools.cached_property
    @abstractmethod
    def runtime_folder(self) -> str | None:
        """
        Get the folder containing all python runtimes managed by this tool
        None if not installed
        """
        ...

    @abstractmethod
    def fetch_installed(self) -> list[PythonListing]:
        """
        Get a list of installed runtimes managed by the manager
        """
        ...

    @abstractmethod
    def fetch_downloads(self) -> list[PythonListing]:
        """
        List available downloads, exclude already downloaded
        """

    @abstractmethod
    def find_matching_listing(self, install: PythonInstall) -> PythonListing | None:
        """
        Find the listing matching a python install

        :param install:
        :return:
        """
        ...


class PythonListing(Prefab, kw_only=True):
    manager: RuntimeManager

    key: str
    version: str
    implementation: str
    variant: str
    arch: str

    _version_tuple: tuple[int, int, int, str, int] | None = attribute(default=None, private=True)

    @property
    def version_tuple(self) -> tuple[int, int, int, str, int]:
        if not self._version_tuple:
            self._version_tuple = version_str_to_tuple(self.version)
        return self._version_tuple


    @classmethod
    def from_dict(cls, manager: RuntimeManager, entry: dict):
        # designed to not fail if extra keys are added
        attrib_names = set(get_attributes(cls))

        kwargs = entry.copy()
        for key in entry.keys():
            if key not in attrib_names:
                del kwargs[key]

        return cls(manager=manager, **kwargs)

    @property
    def full_key(self):
        return f"{type(self).__name__} / {self.key}"

    def install(self):
        raise NotImplementedError("Base Listing Class does not implement install/uninstall")

    def uninstall(self):
        raise NotImplementedError("Base Listing Class does not implement install/uninstall")
