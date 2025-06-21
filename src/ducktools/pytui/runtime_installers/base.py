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
import operator
import os.path
import subprocess
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, ClassVar, Final, Generic, TypeAlias, TypeVar

from ducktools.pythonfinder.shared import PythonInstall, version_str_to_tuple
from ducktools.classbuilder.prefab import prefab, attribute


_version_tuple_type: TypeAlias = tuple[int, int, int, str, int]  # type statement needs 3.12+


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
    def full_key(self) -> str:
        return f"{type(self).__name__} / {self.key}"

    @property
    def will_overwrite(self) -> bool:
        return False

    @classmethod
    @abstractmethod
    def from_dict(cls, manager, entry) -> PythonListing:
        ...

    @abstractmethod
    def install(self) -> subprocess.CompletedProcess | None:
        ...

    @abstractmethod
    def uninstall(self) -> subprocess.CompletedProcess | None:
        ...


Listing = TypeVar("Listing", bound=PythonListing)


class RuntimeManager(Generic[Listing], ABC):
    available_managers: Final[list[type[RuntimeManager]]] = []
    
    organisation: ClassVar[str]

    def __init_subclass__(cls) -> None:
        RuntimeManager.available_managers.append(cls)

    @staticmethod
    def sort_listings(listings: Iterable[Listing]) -> list[Listing]:
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
    def fetch_installed(self) -> list[Listing]:
        """
        Get a list of installed runtimes managed by the manager
        """
        ...

    @abstractmethod
    def _get_download_cache(self) -> list[Listing]:
        """
        List all available downloads (cached method)
        """

    @abstractmethod
    def fetch_downloads(self) -> list[Listing]:
        """
        List available downloads, exclude already downloaded (not cached)
        """

    def find_matching_listing(self, install: PythonInstall) -> Listing | None:
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
