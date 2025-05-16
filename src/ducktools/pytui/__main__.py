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

import os
import sys

from ._version import __version__

class UnsupportedPythonError(Exception):
    pass


def get_parser():
    import argparse
    parser = argparse.ArgumentParser(
        prog="ducktools-pytui",
        description="Prototype Python venv and runtime manager",
    )
    parser.add_argument("-V", "--version", action="version", version=__version__)
    parser.add_argument(
        "--configpath", action="store_true", help="print the path to the config file"
    )
    parser.add_argument(
        "--setshell",
        action="store",
        metavar="SHELL_NAME",
        help="Set the shell to be used for launching activated environments"
    )
    return parser


def main():
    if sys.version_info < (3, 8):
        v = sys.version_info
        raise UnsupportedPythonError(
            f"Python {v.major}.{v.minor}.{v.micro} is not supported. "
            f"ducktools.pytui requires Python 3.8 or later."
        )

    if sys.argv[1:]:
        parser = get_parser()
        args = parser.parse_args()

        if args.configpath:
            from .platform_paths import CONFIG_FILE
            sys.stdout.write(CONFIG_FILE)
            sys.stdout.write("\n")
            return 0
        elif shell_path := args.setshell:
            from .config import Config
            config = Config.from_file()
            out_shell = config.set_shell(shell_path)
            if out_shell:
                print(f"'{out_shell}' will now be used to launch activated shells")
                return
            else:
                print(f"'{shell_path}' could not be found or is an unsupported shell type")
                return

    from .ui import ManagerApp
    import asyncio

    app = ManagerApp()
    asyncio.run(app.run_async())
    return 0


if __name__ == "__main__":
    sys.exit(main())
