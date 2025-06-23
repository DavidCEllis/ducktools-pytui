import sys

import pytest

from ducktools.pytui.ui import substitute_home


@pytest.mark.parametrize(
        "path, expected", 
        [
            ("/usr/bin/python", None),  # None is used for unchanged
            ("/home/david/.local/share/ducktools", "~/.local/share/ducktools"),
            ("/home/other/.local/share/ducktools", None),
        ],
    )
def test_substitute_home(path, expected):
    homedir = "/home/david"

    if expected is None or sys.platform == "win32":
        expected = path

    assert substitute_home(path, homedir=homedir) == expected
