import sys
from operator import itemgetter
from unittest.mock import patch

import pytest

import ducktools.pytui.ui as ui
from ducktools.pytui.ui import ManagerApp, MANAGED_BY_MAPPING, substitute_home

from textual.worker import WorkerFailed


@patch("ducktools.pytui.ui.HOME", "/home/ducksual")
@pytest.mark.flaky(reruns=5)
async def test_runtime_table(runtimes, patch_list_installs):
    app = ManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()  # Wait for processing

        patch_list_installs.assert_called()

        assert app._runtime_table.row_count > 0
        row_data = [app._runtime_table.get_row_at(i) for i in range(0, app._runtime_table.row_count)]
        row_data.sort(key=itemgetter(3))  # Sort by Path

        expected = [
            [
                py.version_str if py.implementation_version_str == py.version_str else f"{py.version_str} / {py.implementation_version_str}",
                MANAGED_BY_MAPPING.get(py.managed_by, py.managed_by),
                py.implementation,
                substitute_home(py.executable)
            ]
            for py in runtimes
        ]
        expected.sort(key=itemgetter(3))
        assert row_data == expected
