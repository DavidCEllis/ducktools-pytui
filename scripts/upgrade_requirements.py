import re
import subprocess

from typing import NamedTuple
from pathlib import Path

base_dir = Path(__file__).parents[1]
pyproject_file = str(base_dir  / "pyproject.toml")
requirements_file = str(base_dir / "requirements.txt")
constraints_file = str(base_dir / "constraints.txt")
override_file = str(base_dir / "overrides.txt")


constraint_pattern = re.compile(
    R"(?P<package>.*?==\d+\.\d+\.?\d*)\s*;\s*(?P<constraints>.*?)\s*\\"
)


class ConstraintIssue(NamedTuple):
    package: str
    constraints: str


def check_version_constraints() -> None:
    # Check the requirements file for python version constraints
    discovered_constraints = []
        
    with open(requirements_file, 'r') as f:
        for line in f:
            if match := constraint_pattern.match(line):
                discovered_constraints.append(
                    ConstraintIssue(match["package"], match["constraints"])
                )                  
    if discovered_constraints:
        constraint_msg = "\n".join(
            f"\t{c.package!r}: {c.constraints!r}" for c in discovered_constraints
        )
        
        raise ValueError(f"Packages discovered with banned constraints:\n{constraint_msg}")


def upgrade_requirements():
    subprocess.run(
        [
            "uv", "pip", "compile",
            pyproject_file,
            "--universal",
            "--generate-hashes",
            "-o", requirements_file,
            # "--constraint", constraints_file,
            # "--override", override_file,
            "--upgrade",
        ],
    )


if __name__ == "__main__":
    upgrade_requirements()
    check_version_constraints()
