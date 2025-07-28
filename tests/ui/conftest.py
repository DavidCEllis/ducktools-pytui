import json
from pathlib import Path
from unittest.mock import patch

from pytest import fixture

from ducktools.pythonfinder import PythonInstall
from ducktools.pythonfinder.venv import PythonVEnv

from ducktools.pytui.config import Config


DATA_FOLDER = Path(__file__).parents[1] / "example_data" / "pythonfinder"


@fixture
async def patched_config():
    with (
        patch.object(Config, "from_file") as patched_config,
        patch.object(Config, "write_config"),  # prevent accidental writes
    ):
        # This file shouldn't actually be created as the write is patched
        config = Config(config_file="/tmp/pytui_test_config.json")
        patched_config.return_value = config
        yield config


@fixture(scope="session")
async def runtimes() -> list[PythonInstall]:
    raw_installs = json.loads((DATA_FOLDER / "runtimes_data.json").read_text())
    pys = [PythonInstall.from_json(**inst) for inst in raw_installs]
    assert len(pys) > 0
    return pys


@fixture(scope="session")
async def local_venvs() -> list[PythonVEnv]:
    raw_venvs = json.loads((DATA_FOLDER / "local_venvs.json").read_text())
    venvs = []
    for v in raw_venvs:
        venv = PythonVEnv(
            folder=v["folder"],
            executable=v["executable"],
            version=tuple(v["version"]),
            parent_path=v["parent_path"],
            _parent_executable=v["_parent_executable"],
        )
        venvs.append(venv)
    return venvs


@fixture(scope="session")
async def global_venvs() -> list[PythonVEnv]:
    raw_venvs = json.loads((DATA_FOLDER / "global_venvs.json").read_text())
    venvs = []
    for v in raw_venvs:
        venv = PythonVEnv(
            folder=v["folder"],
            executable=v["executable"],
            version=tuple(v["version"]),
            parent_path=v["parent_path"],
            _parent_executable=v["_parent_executable"],
        )
        venvs.append(venv)
    return venvs


@fixture(autouse=True)
async def patch_list_installs(runtimes):
    with patch("ducktools.pytui.ui.list_installs_deduped") as mock_deduped:
        mock_deduped.return_value = runtimes
        yield mock_deduped


@fixture(autouse=True)
async def patch_list_venvs(local_venvs, global_venvs, patched_config):
    def get_venv(base_dir=None, recursive=False, search_parent_folders=False):
        if base_dir == patched_config.global_venv_folder:
            return global_venvs
        else:
            return local_venvs


    with patch("ducktools.pytui.ui.list_python_venvs") as venv_mock:
        venv_mock.side_effect = get_venv
        yield venv_mock
