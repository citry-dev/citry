"""
Templates at the logic nesting limit fit the frame budget on the Python render path.

The fixtures, the budget and what is checked are described in
``_frame_budget.py``.
"""

from __future__ import annotations

import pytest

from ._frame_budget import check_render_path, only_in_linux_jobs


@pytest.mark.qualification
@only_in_linux_jobs
def test_the_logic_limit_fits_the_frame_budget_on_the_python_path() -> None:
    check_render_path("python")
