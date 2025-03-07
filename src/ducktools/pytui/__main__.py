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

import argparse
import sys

from ._version import __version__

class UnsupportedPythonError(Exception):
    pass


def get_parser():
    parser = argparse.ArgumentParser(
        prog="ducktools-pytui",
        description="Prototype Python venv and runtime manager",
    )
    parser.add_argument("-V", "--version", action="version", version=__version__)
    return parser


def main():
    if sys.version_info < (3, 10):
        v = sys.version_info
        raise UnsupportedPythonError(
            f"Python {v.major}.{v.minor}.{v.micro} is not supported. "
            f"ducktools.pytui requires Python 3.10 or later."
        )

    if sys.argv[1:]:
        parser = get_parser()
        parser.parse_args()

    from .ui import ManagerApp
    app = ManagerApp()
    app.run()


if __name__ == "__main__":
    main()
