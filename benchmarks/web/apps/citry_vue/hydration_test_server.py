"""
Test-only entry point: the board app with hydration switched on or off per process.

``test_hydration_e2e.py`` starts this module under uvicorn in a subprocess, so
the Django settings that importing ``app`` installs stay out of the pytest
process. The benchmark itself never imports this module.

Environment:
    BOARD_HYDRATION_TEST_SSR: ``"1"`` (default) serves pages the server wrote
        for Vue to hydrate; ``"0"`` serves the same pages with an empty Vue
        host so the browser mounts them, the reference for comparison.
"""

import os

import app

_ssr = os.environ.get("BOARD_HYDRATION_TEST_SSR", "1")
if _ssr not in {"0", "1"}:
    raise ValueError("BOARD_HYDRATION_TEST_SSR must be '0' or '1'.")

# Every serialization reads this setting, so changing it here changes every
# page this server writes. The settings object is frozen after construction;
# this server is test-only.
object.__setattr__(app.engine.settings, "ssr", _ssr == "1")

application = app.application
