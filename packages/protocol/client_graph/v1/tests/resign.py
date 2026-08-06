"""
Recompute the canonical revision of client-graph fixtures after editing them.

A fixture's `revision` is the SHA-256 of the canonical JSON with the revision
member omitted, so any hand edit invalidates it. Run this after changing
fixture content:

    python packages/protocol/client_graph/v1/tests/resign.py            # every listed fixture
    python packages/protocol/client_graph/v1/tests/resign.py NAME.json  # specific files

Fixtures whose index entry sets `"preserveRevision": true` are skipped when
re-signing everything: their defect is the signature itself. Naming one
explicitly re-signs it anyway. Standard library only; no install needed.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from check_canonicalization import canonical_json

FIXTURES = Path(__file__).resolve().parent


def resign(path: Path) -> bool:
    """Rewrite the file's revision; True when the file changed."""
    manifest = json.loads(path.read_text(encoding="utf8"))
    unsigned = {key: value for key, value in manifest.items() if key != "revision"}
    canonical = canonical_json(unsigned).encode("utf8")
    revision = hashlib.sha256(canonical).hexdigest()
    if manifest.get("revision") == revision:
        return False
    manifest["revision"] = revision
    path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf8")
    return True


def main() -> int:
    names = sys.argv[1:]
    if names:
        targets = [FIXTURES / name for name in names]
    else:
        index = json.loads((FIXTURES / "index.json").read_text(encoding="utf8"))
        targets = [FIXTURES / entry["manifest"] for entry in index if not entry.get("preserveRevision", False)]
    missing = [path.name for path in targets if not path.is_file()]
    if missing:
        print(f"not found: {', '.join(missing)}", file=sys.stderr)  # noqa: T201 - standalone CLI
        return 1
    changed = [path.name for path in targets if resign(path)]
    for name in changed:
        print(f"re-signed {name}")  # noqa: T201 - standalone CLI
    print(f"{len(changed)} of {len(targets)} fixtures needed re-signing")  # noqa: T201 - standalone CLI
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
