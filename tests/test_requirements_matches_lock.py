import subprocess

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


from ducktools.pytui.runtime_installers.uv import UVManager


BASE_DIR = Path(__file__).parents[1]
REQUIREMENTS = BASE_DIR / "requirements.txt"


def test_requirements_updated():
    # Check that if the lockfile has been updated
    # the requirements file matches the lockfile
    # Skip if UV unavailable
    uv_path = UVManager().executable
    if uv_path is None:
        pytest.skip(reason="UV is not available on Path")

    current_requirements = REQUIREMENTS.read_text()

    with TemporaryDirectory() as tmpdir:
        requirements_file = Path(tmpdir) / "requirements.txt"
        subprocess.run(
            [
                uv_path, "export",
                "--locked",
                "--no-dev",
                "--no-header",
                "--no-emit-project",
                "-o", requirements_file,
            ],
            check=True,
            capture_output=True,
        )
        test_requirements = requirements_file.read_text()

    assert current_requirements == test_requirements
