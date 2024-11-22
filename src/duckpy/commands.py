import os
import sys

from ducktools.lazyimporter import LazyImporter
from ducktools.lazyimporter.capture import capture_imports


laz = LazyImporter()

with capture_imports(laz, auto_export=False):
    from ducktools.pythonfinder.win32 import get_registered_pythons


def _get_active_python():
    split_char = ";" if sys.platform == "win32" else ":"
    env_paths = os.environ.get("PATH", "").split(split_char)
    python = None

    for p in env_paths:
        try:
            for pth in os.scandir(p):
                if pth.name in {"python", "python.exe"}:
                    python = pth.path
                    break
        except FileNotFoundError:
            pass

        if python:
            break

    return python


def py_list(*, paths: bool = False):
    """
    Emulate `py --list` and `py --list-paths`

    This differs in that it will *not* highlight the 'latest' python install if it is
    not the version of Python that would be run by running `python` in the commandline.

    :param paths: List registered python installs
    :return: a list of windows registered python installs
    """
    # Get the details on active python
    in_venv = "VIRTUAL_ENV_PROMPT" in os.environ
    active_path = _get_active_python()
    if in_venv:
        if paths:
            print(f"  *               {active_path}")
        else:
            print(u"  *               Active venv")

    pythoncore_installs = []
    other_installs = []

    for py in laz.get_registered_pythons():
        company = py.metadata.get("Company", "PythonCore")
        version = py.metadata.get("SysVersion")
        tag = py.metadata.get("Tag")

        is_pythoncore = (company == "PythonCore")

        if is_pythoncore:
            ver = f"-V:{tag}"
        else:
            ver = f"-V:{company}/{tag}"

        if active_path == py.executable:
            ver += " *"

        if paths:
            line = f" {ver:<16} {py.executable}"
        else:
            line = f" {ver:<16} {py.metadata.get("DisplayName")}"

        if is_pythoncore:
            pythoncore_installs.append(line)
        else:
            other_installs.append(line)

    print("\n".join(pythoncore_installs))
    print("\n".join(other_installs))


if __name__ == "__main__":
    py_list()
