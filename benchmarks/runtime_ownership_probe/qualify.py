"""Run recorded retirement and callback cases through the ordinary runtime."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "benchmarks/ownership_journal_probe")]

import check_retirement  # noqa: E402
import check_storage  # noqa: E402
from benchmarks.runtime_ownership_probe.reference import SOURCE, install  # noqa: E402

from citry import ownership  # noqa: E402
from citry_core import _ownership, _rust  # noqa: E402


def enable() -> None:
    """Restore ordinary runtime methods."""
    install(changed=True)


def disable() -> None:
    """Use the archived Python collector with current record classes."""
    install(changed=False)


def main() -> None:
    """Reuse seeded graph generation while switching actual runtime methods."""
    check_retirement.load_native = lambda: _ownership
    check_retirement.install_storage = lambda *_args, **_kwargs: (enable, disable)
    check_storage.install_storage = lambda *_args, **_kwargs: (enable, disable)
    try:
        check_retirement.check(1000, stored=True)
        check_retirement.check_fallback(stored=True)
        check_storage.check_mid_callback_replay(_ownership)
    finally:
        enable()
    paths = (
        Path(__file__).resolve(),
        Path(__file__).with_name("reference.py"),
        SOURCE,
        Path(ownership.__file__),
        Path(_rust.__file__),
        Path(check_retirement.__file__),
        Path(check_storage.__file__),
    )
    print(
        json.dumps({"hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}})
    )


if __name__ == "__main__":
    main()
