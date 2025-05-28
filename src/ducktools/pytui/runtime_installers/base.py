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
import operator
import os.path
import subprocess
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import ClassVar

from ducktools.pythonfinder.shared import PythonInstall, version_str_to_tuple
from ducktools.classbuilder.prefab import prefab, attribute

# typing hack - avoid deprecated alias on newer python
if sys.version_info >= (3, 9):
    _version_tuple_type = tuple[int, int, int, str, int]
else:
    from typing import Tuple
    _version_tuple_type = Tuple[int, int, int, str, int]


class RuntimeManager(ABC):
    available_managers: ClassVar[list[type[RuntimeManager]]] = []
    organisation: ClassVar[str | None] = None

    def __init_subclass__(cls):
        RuntimeManager.available_managers.append(cls)

    @staticmethod
    def sort_listings(listings: Iterable[PythonListing]):
        new_listings = sorted(listings, key=operator.attrgetter("variant", "arch", "key"))
        new_listings.sort(key=operator.attrgetter("version_tuple"), reverse=True)
        new_listings.sort(key=operator.attrgetter("implementation"))
        return new_listings

    @functools.cached_property
    @abstractmethod
    def executable(self) -> str | None:
        """
        Get the path to the manager executable or None if it is not installed
        """
        ...

    @abstractmethod
    def fetch_installed(self) -> list[PythonListing]:
        """
        Get a list of installed runtimes managed by the manager
        """
        ...

    @abstractmethod
    def _get_download_cache(self):
        """
        List all available downloads (cached method)
        """

    @abstractmethod
    def fetch_downloads(self) -> list[PythonListing]:
        """
        List available downloads, exclude already downloaded (not cached)
        """

    def find_matching_listing(self, install: PythonInstall) -> PythonListing | None:
        if install.managed_by is None or not install.managed_by.startswith(self.organisation):
            return None

        # Executable names may not match, one may find python.exe, the other pypy.exe
        # Use the parent folder.
        installed_dict = {
            os.path.dirname(os.path.abspath(py.path)): py
            for py in self.fetch_installed()
            if py.path is not None
        }

        install_path = os.path.dirname(install.executable)

        return installed_dict.get(install_path, None)


@prefab(kw_only=True)
class PythonListing(ABC):
    manager: RuntimeManager

    key: str
    version: str
    implementation: str
    variant: str
    arch: str
    path: str | None
    url: str | None

    # `attribute` is a field specifier as defined in dataclass_transform
    # Not sure why it's not being picked up
    _version_tuple: _version_tuple_type | None = attribute(default=None, private=True)

    @property
    def version_tuple(self) -> _version_tuple_type:
        if not self._version_tuple:
            self._version_tuple = version_str_to_tuple(self.version)
        return self._version_tuple

    @property
    def full_key(self):
        return f"{type(self).__name__} / {self.key}"

    @property
    def will_overwrite(self):
        return False

    @classmethod
    @abstractmethod
    def from_dict(cls, manager, entry):
        ...

    @abstractmethod
    def install(self) -> subprocess.CompletedProcess | None:
        ...

    @abstractmethod
    def uninstall(self) -> subprocess.CompletedProcess | None:
        ...