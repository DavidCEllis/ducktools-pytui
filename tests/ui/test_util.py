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

    expected = expected if expected is not None else path

    assert substitute_home(path, homedir=homedir) == expected
