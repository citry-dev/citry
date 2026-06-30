#!/usr/bin/env python
"""
Run every validator in scripts/validators/ and report which invariants hold.

Each validator module exports `check() -> list[str]`: a list of problem
descriptions, empty when the invariant holds. Validators are discovered
automatically, so adding one is just dropping a new `<name>.py` file in that
directory (files whose name starts with `_` are skipped).

Run directly, or as the `validators` phase of scripts/check.py.
"""

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path

_VALIDATORS_DIR = Path(__file__).resolve().parent / "validators"


def _load_check(path: Path) -> Callable[[], list[str]]:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        msg = f"could not load {path}"
        raise ImportError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.check


def run_validators() -> bool:
    """Run all validators; return True when every invariant holds."""
    paths = sorted(p for p in _VALIDATORS_DIR.glob("*.py") if not p.name.startswith("_"))
    ok = True
    for path in paths:
        name = path.stem
        try:
            problems = _load_check(path)()
        except Exception as exc:  # noqa: BLE001 - a broken validator should fail loudly, not abort the run
            print(f"FAIL {name}: {exc}", file=sys.stderr)
            ok = False
            continue
        if problems:
            ok = False
            print(f"FAIL {name}", file=sys.stderr)
            for problem in problems:
                print(f"  - {problem}", file=sys.stderr)
        else:
            print(f"PASS {name}")
    return ok


def main() -> int:
    if run_validators():
        print("\nAll validators passed.")
        return 0
    print("\nSome validators failed.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
