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

# mypy: disable-error-code="attr-defined"
# attributes don't exist on non-windows platform
# but this entire file is only imported on windows.
"""
Helper code to 'fix' the windows terminal history in order to get command history
in Python that doesn't use PyREPL.

Copied from:
https://discuss.python.org/t/interactive-command-history-in-session-started-with-subprocess-on-windows/3701/5
"""
from __future__ import annotations

import ctypes
import collections
from ctypes import wintypes

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

HISTORY_NO_DUP_FLAG = 1


class ConsoleHistoryInfoStruct(ctypes.Structure):
    _fields_ = (
        ('cbSize', wintypes.UINT),
        ('HistoryBufferSize', wintypes.UINT),
        ('NumberOfHistoryBuffers', wintypes.UINT),
        ('dwFlags', wintypes.DWORD)
    )

    def __init__(self, *args, **kwds):
        super().__init__(ctypes.sizeof(self), *args, **kwds)


ConsoleHistoryInfo = collections.namedtuple(
    'ConsoleHistoryInfo',
    'bufsize nbuf flags'
)


def get_console_history_info():
    info = ConsoleHistoryInfoStruct()
    if not kernel32.GetConsoleHistoryInfo(ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())

    return ConsoleHistoryInfo(
        info.HistoryBufferSize,
        info.NumberOfHistoryBuffers,
        info.dwFlags
    )


def set_console_history_info(
    bufsize=512,
    nbuf=32,
    flags=HISTORY_NO_DUP_FLAG
):
    info = ConsoleHistoryInfoStruct(bufsize, nbuf, flags)
    if not kernel32.SetConsoleHistoryInfo(ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
