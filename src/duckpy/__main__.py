import argparse

from . import __version__
from .commands import py_list

def get_parser():

    parser = argparse.ArgumentParser(
        prog="duckpy",
        description=f"Alternate Python Launcher for Windows Version {__version__[1:]}",
        allow_abbrev=False,
    )
    parser.add_argument(
        "-0", "--list",
        dest="list_opt",
        action="store_true",
        help="List the available pythons"
    )
    parser.add_argument(
        "-0p", "--list-paths",
        dest="list_paths",
        action="store_true",
        help="List with paths"
    )

    return parser


def main():
    parser = get_parser()
    args, extras = parser.parse_known_args()

    print(args)


if __name__ == "__main__":
    main()
