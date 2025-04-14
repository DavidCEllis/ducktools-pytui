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

# Here we can use pathlib as it's a build script
import sys

import shutil
import subprocess
import zipapp

from pathlib import Path


project_path = Path(__file__).parents[1]
project_build_path = project_path / "build" / "project_build"
build_path = project_path / "build" / "application"
build_bin = build_path / "bin"
dist_path = project_path / "dist" / "pytui.pyz"
main_func = "ducktools.pytui.__main__:main"


def main():
    # Prepare install and build paths
    shutil.rmtree(build_path, ignore_errors=True)
    shutil.rmtree(project_build_path, ignore_errors=True)
    dist_path.unlink(missing_ok=True)

    build_path.mkdir(parents=True)
    dist_path.parent.mkdir(parents=True, exist_ok=True)

    # Download locked dependencies
    subprocess.run(
        [
            sys.executable, "-m",
            "pip", "install",
            "--no-compile",
            "-r", str(project_path / "requirements.txt"),
            "--target", str(build_path),
        ]
    )

    # Install just the current package in another folder
    subprocess.run(
        [
            sys.executable, "-m",
            "pip", "install",
            "--no-compile", str(project_path),
            "--no-deps",
            "--target", str(project_build_path)
        ]
    )

    shutil.move(
        project_build_path / "ducktools" / "pytui",
        build_path / "ducktools" / "pytui",
    )

    for fld in project_build_path.glob("ducktools_pytui*/"):
        shutil.move(str(fld), str(build_path))  # convert to str for 3.8

    # Remove script files
    shutil.rmtree(build_bin)
    shutil.rmtree(project_build_path)

    zipapp.create_archive(
        build_path,
        dist_path,
        interpreter="/usr/bin/env python3",
        main=main_func,
    )


if __name__ == "__main__":
    main()
