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

import os.path
import functools
import signal
import subprocess

from ducktools.pythonfinder import list_python_installs, PythonInstall


def list_installs_deduped() -> list[PythonInstall]:
    """
    Get a list of Python executables, but try to avoid multiple aliases to the same Python runtime.

    :return: List of PythonInstall instances
    """
    installs = list_python_installs()

    # First sort so the executables are in priority order
    deduped_installs = []
    used_stdlib_folders = set()
    for inst in installs:
        fld = inst.paths.get("stdlib")
        if fld:
            if fld in used_stdlib_folders:
                continue
            used_stdlib_folders.add(fld)
    
        deduped_installs.append(inst)

    return deduped_installs


class IgnoreSignals:
    @staticmethod
    def null_handler(signum, frame):
        # This just ignores signals, used to ignore in the parent process temporarily
        # The child process will still receive the signals.
        pass

    def __init__(self, signums: list[int]):
        self.old_signals: dict[int, signal._HANDLER] = {}
        self.signums = signums

    def __enter__(self):
        if self.old_signals:
            raise RuntimeError("ignore_signals is not reentrant")

        for signum in self.signums:
            self.old_signals[signum] = signal.signal(signum, self.null_handler)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for signum, handler in self.old_signals.items():
            signal.signal(signum, handler)


def ignore_keyboardinterrupt():
    return IgnoreSignals([signal.SIGINT])


@functools.wraps(subprocess.run, assigned=("__doc__", "__type_params__", "__annotations__"))
def run(*args, **kwargs):
    with ignore_keyboardinterrupt():
        subprocess.run(*args, **kwargs)
