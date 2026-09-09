"""Compare production attribute output and diagnostics with the pinned old method."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

from check import outcome
from probe import ROOT, nodes, reference_node_formatter


def main() -> None:
    """Exercise randomized misses and immediate reuse in both validation modes."""
    original = reference_node_formatter()
    changed = nodes.ElementAttrsNode._format
    node = nodes.ElementAttrsNode("<div>", (0, 5), (), ())
    randomizer = random.Random(20260908)  # noqa: S311 - reproducible differential inputs
    names = ("title", "TITLE", "class", "CLASS", "style", "disabled", "aria-label", "data-value", "bad name")
    values = (None, False, True, 0, 1, -1, "", " <>&\"' ", "café", "same", "width: 10px", 1 << 255, 1 << 256)
    for _ in range(3000):
        mapping = {name: randomizer.choice(values) for name in randomizer.sample(names, randomizer.randrange(6))}
        validate = bool(randomizer.getrandbits(1))
        expected = outcome(original, node, mapping, validate=validate)
        for _ in range(2):
            if outcome(changed, node, mapping, validate=validate) != expected:
                raise AssertionError("Production changed a randomized formatting outcome")
    print(
        json.dumps(
            {
                "reference": "5bad7af8 ElementAttrsNode._format",
                "randomized_cases_twice": 3000,
                "hashes": {
                    str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (
                        Path(__file__).resolve(),
                        ROOT / "packages/py/citry/citry/nodes/__init__.py",
                        ROOT / "packages/py/citry/citry/attrs.py",
                        ROOT / "packages/py/citry/citry/util/html.py",
                    )
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
