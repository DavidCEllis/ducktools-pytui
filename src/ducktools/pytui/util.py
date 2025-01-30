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

# This is a generic utility wrapper to launch a subprocess
# while ignoring specific signals in the parent process
import functools
import signal
import subprocess


class IgnoreSignals:
    @staticmethod
    def null_handler(signum, frame):
        # This just ignores signals, used to ignore in the parent process temporarily
        # The child process will still receive the signals.
        pass

    def __init__(self, signums: list[int]):
        self.old_signals = {}
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
