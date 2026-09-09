"""Run the retained browser cases with direct emission as the immediate candidate."""

from __future__ import annotations

import hashlib
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.composed_function_probe import browser  # noqa: E402
from benchmarks.composed_function_probe.adapter import installed as composed_installed  # noqa: E402
from benchmarks.function_text_probe.adapter import installed  # noqa: E402


def main() -> None:
    def mode(module: Any, variant: str, counts: dict[str, int] | None = None) -> Any:
        if variant == "immediate":
            return installed(module, enabled=True, counts=counts)
        return composed_installed(module, variant, counts)

    captured = io.StringIO()
    failed = False
    with patch.object(browser, "installed", mode), redirect_stdout(captured):
        try:
            browser.main()
        except SystemExit:
            failed = True
    report = json.loads(captured.getvalue())
    report["mode_note"] = "immediate uses direct emission; reference and deferred retain iteration 66 implementations"
    paths = [Path(__file__), Path(__file__).with_name("adapter.py"), Path(browser.__file__)]
    report["hashes"].update({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    print(json.dumps(report, indent=2))
    if failed or not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
