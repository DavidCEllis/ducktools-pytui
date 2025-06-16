import sys
from operator import itemgetter

import pytest

from ducktools.pytui.ui import ManagerApp, MANAGED_BY_MAPPING

from textual.worker import WorkerFailed

flaky_test = pytest.mark.xfail(
    reason="Test sometimes fails with no screen", 
    strict=False,
    raises=WorkerFailed,
)


@flaky_test
async def test_runtime_table(runtimes):
    app = ManagerApp()
    async with app.run_test() as pilot:
        row_data = [app._runtime_table.get_row_at(i) for i in range(0, app._runtime_table.row_count)]
        row_data.sort(key=itemgetter(3))  # Sort by Path
      
        expected = [
            [
                py.version_str if py.implementation_version_str == py.version_str else f"{py.version_str} / {py.implementation_version_str}",
                MANAGED_BY_MAPPING.get(py.managed_by, py.managed_by),
                py.implementation,
                py.executable
            ]
            for py in runtimes
        ]
        expected.sort(key=itemgetter(3))
        assert row_data == expected
        
