"""Reuse ownership contract probes with the binding from the normal package build."""

from __future__ import annotations

import argparse
import hashlib
import json
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "benchmarks/ownership_journal_probe"))

import check_retirement  # noqa: E402
import check_storage  # noqa: E402
import pytest  # noqa: E402
from benchmarks.ownership_journal_probe.probe import check_journal_contracts  # noqa: E402
from benchmarks.packaged_ownership_probe import probe as packaged  # noqa: E402


def main() -> None:
    """Check raw contracts, callback/replay state and optional broad pytest activation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", action="store_true")
    args = parser.parse_args()
    result_dir = ROOT / "benchmarks/results/repeat-render"
    paths = (
        Path(__file__).resolve(),
        Path(packaged.__file__),
        Path(check_retirement.__file__),
        Path(check_storage.__file__),
        ROOT / "benchmarks/ownership_journal_probe/probe.py",
        ROOT / "benchmarks/ownership_journal_probe/storage_probe.py",
        ROOT / "benchmarks/native_combined_capture_probe/contracts.py",
        ROOT / "benchmarks/native_ownership_qualification/queue_order_checks.py",
        packaged.PROBE_ARTIFACT,
    )
    print(
        json.dumps({"hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}),
        flush=True,
    )
    check_journal_contracts(packaged.NATIVE)
    check_storage.check_tables(packaged.NATIVE)
    # Only the native loader changes; the reference still runs Python retirement.
    check_retirement.load_native = lambda: packaged.NATIVE
    check_retirement.check(1000, stored=True)
    check_retirement.check_fallback(stored=True)
    saved_probe, saved_argv = sys.modules.get("probe"), sys.argv
    sys.modules["probe"] = packaged
    try:
        sys.argv = [
            "contracts.py",
            "--output",
            str(result_dir / "packaged-ownership-contracts.json"),
        ]
        runpy.run_path(str(ROOT / "benchmarks/native_combined_capture_probe/contracts.py"), run_name="__main__")
        sys.argv = ["queue_order_checks.py"]
        runpy.run_path(
            str(ROOT / "benchmarks/native_ownership_qualification/queue_order_checks.py"), run_name="__main__"
        )
        if args.suite:
            packaged.ENABLE()
            raise SystemExit(pytest.main(["packages/py/citry/tests", "-m", "not e2e", "--no-cov", "-q"]))
    finally:
        packaged.RESTORE()
        sys.argv = saved_argv
        if saved_probe is None:
            sys.modules.pop("probe", None)
        else:
            sys.modules["probe"] = saved_probe


if __name__ == "__main__":
    main()
