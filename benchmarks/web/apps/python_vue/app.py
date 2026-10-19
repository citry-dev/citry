"""Launch the shared JSON API with this adapter's compiled browser assets."""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCENARIO = HERE / "scenario"
if not SCENARIO.is_dir():
    SCENARIO = HERE.parents[1] / "scenarios/project_board"
sys.path.insert(0, str(SCENARIO))
from json_api import create_application  # noqa: E402

application = create_application(HERE)
