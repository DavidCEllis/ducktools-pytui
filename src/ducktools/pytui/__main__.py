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

import os, os.path
import sys

from ._version import __version__


class UnsupportedPythonError(Exception):
    pass


def _check_windows_dir():
    # Double-clicking to launch the zipapp may put the user in the system32
    # folder on Windows.
    # Inside a zipapp, __file__ won't exist on the file system as it is inside the archive.
    if not os.path.exists(__file__) and (win_path := os.environ.get("WINDIR")):
        sys32 = os.path.join(win_path, "System32")
        if os.path.samefile(os.getcwd(), sys32) and (user_path := os.environ.get("USERPROFILE")):
            os.chdir(user_path)


def get_parser():
    import argparse

    from .config import Config

    parser = argparse.ArgumentParser(
        prog="ducktools-pytui",
        description="Prototype Python venv and runtime manager",
    )
    parser.add_argument("-V", "--version", action="version", version=__version__)

    # Config parser arguments
    subparsers = parser.add_subparsers(title="Subcommands", dest="subcommand")
    config_parser = subparsers.add_parser("config", help="Subcommand for setting config options")

    config_parser.add_argument(
        "--set-shell",
        action="store",
        metavar="SHELL_NAME or SHELL_PATH",
        help="Set the shell to be used for launching activated environments"
    )

    config_parser.add_argument(
        "--set-search-mode",
        action="store",
        choices=Config.VENV_SEARCH_MODES,
        help="Set the search mode to be used",
    )

    config_parser.add_argument(
        "--set-global-venv-dir",
        action="store",
        help="Set the global venv folder",
    )

    include_pip_group = config_parser.add_mutually_exclusive_group()
    include_pip_group.add_argument(
        "--include-pip",
        dest="include_pip",
        action="store_true",
        default=None,
        help="Include pip when creating venv"
    )
    include_pip_group.add_argument(
        "--exclude-pip",
        dest="include_pip",
        action="store_false",
        default=None,
        help="Exclude pip when creating a venv"
    )

    update_pip_group = config_parser.add_mutually_exclusive_group()
    update_pip_group.add_argument(
        "--update-pip",
        dest="update_pip",
        action="store_true",
        default=None,
        help="Update pip to the latest version when creating a venv"
    )
    update_pip_group.add_argument(
        "--bundled-pip",
        dest="update_pip",
        action="store_false",
        default=None,
        help="Use the version of pip bundled with the runtime when creating a venv"
    )

    return parser


def main():
    if sys.version_info < (3, 8):
        v = sys.version_info
        print(
            f"Unsupported Python: {v.major}.{v.minor}.{v.micro} is not supported. "
            f"PyTUI requires Python 3.8 or later."
        )
        input("Press ENTER to close")
        sys.exit()

    if sys.argv[1:]:
        parser = get_parser()
        args = parser.parse_args()

        if args.subcommand == "config":
            from .config import Config
            config = Config.from_file()

            update_config = False
            if (shell := args.set_shell) is not None:
                new_shell = config.set_shell(shell)
                if new_shell:
                    print(f"Default shell set to '{new_shell}'")
                    update_config = True
                else:
                    print(f"Shell '{shell}' could not be found.")

            if (search_mode := args.set_search_mode) is not None:
                update_config = True
                config.venv_search_mode = search_mode
                print(f"venv search mode set to '{search_mode}'")

            if (venv_path := args.set_global_venv_dir) is not None:
                update_config = True
                venv_path = os.path.expanduser(venv_path)
                config.global_venv_folder = venv_path
                print(f"Global venv folder set to \"{venv_path}\"")

            if (include_pip := args.include_pip) is not None:
                update_config = True
                config.include_pip = args.include_pip
                if include_pip:
                    print("New venvs will be created WITH pip")
                else:
                    print("New venvs will be created WITHOUT pip")

            if (update_pip := args.update_pip) is not None:
                update_config = True
                config.latest_pip = update_pip
                if update_pip:
                    print("New venvs with pip will update to the latest pip")
                else:
                    print("New venvs with pip will use the bundled pip")

            if update_config:
                config.write_config()
            else:
                import json
                from ducktools.classbuilder.prefab import as_dict

                print(f"Config file: \"{config.config_file}\"")
                print("Current Settings:")

                data = json.dumps(as_dict(config), indent=2)
                print(data)
                print("\nFor editing options, check '--help'")

    else:
        if sys.platform == "win32":
            _check_windows_dir()

        # No arguments, launch pytui
        from .ui import ManagerApp
        import asyncio

        app = ManagerApp()
        if sys.version_info >= (3, 10):
            asyncio.run(app.run_async())
        else:
            app.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
