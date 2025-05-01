from pathlib import Path
import subprocess

base_dir = Path(__file__).parents[1]
pyproject_file = str(base_dir  / "pyproject.toml")
requirements_file = str(base_dir / "requirements.txt")
constraints_file = str(base_dir / "constraints.txt")

def upgrade_requirements():
    subprocess.run(
        [
            "uv", "pip", "compile",
            pyproject_file,
            "--universal",
            "--generate-hashes",
            "-o", requirements_file,
            "--constraint", constraints_file,
            "--upgrade",
        ]
    )

if __name__ == "__main__":
    upgrade_requirements()
