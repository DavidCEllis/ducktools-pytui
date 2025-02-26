"""
Helper code to 'fix' the windows terminal history in order to get command history
in Python that doesn't use PyREPL.

Copied from:
https://discuss.python.org/t/interactive-command-history-in-session-started-with-subprocess-on-windows/3701/5
"""

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
