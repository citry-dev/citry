"""Run all non-browser Citry tests with the combined native ownership candidate."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmarks/native_combined_capture_probe"))

import pytest  # noqa: E402
from probe import ENABLE, PROBE_ARTIFACT, RESTORE  # noqa: E402

if __name__ == "__main__":
    paths = (
        Path(__file__).resolve(),
        ROOT / "benchmarks/native_combined_capture_probe/adapter.py",
        ROOT / "benchmarks/native_record_export_probe/adapter.py",
        ROOT / "benchmarks/native_slot_region_probe/adapter.py",
        PROBE_ARTIFACT,
    )
    print(
        json.dumps({"hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}),
        flush=True,
    )
    ENABLE()
    try:
        result = pytest.main(["packages/py/citry/tests", "-m", "not e2e", "--no-cov", "-q"])
    finally:
        RESTORE()
    raise SystemExit(result)
