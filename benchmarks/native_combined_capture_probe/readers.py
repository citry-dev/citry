"""Count direct construction of each ownership record family outside timing."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any

from probe import ENABLE, PROBE_ARTIFACT, RESTORE, ROOT, TABLES, OwnershipGraph, ids, scenario
from probe import ownership as own

# isort: split
from adapter import configure


def main() -> None:
    """Compare ordinary/direct-counted output and retain constructor activation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    counts = Counter()
    ENABLE()
    original_initialize = OwnershipGraph.__init__

    def constructor(factory: Any, fields: tuple[Any, ...]) -> Any:
        counts[factory.__name__] += 1
        return tuple.__new__(factory, fields)

    def initialize(graph: Any) -> None:
        original_initialize(graph)
        configure(graph, constructor)

    try:
        module = scenario()
        data = module.gen_render_data()
        for _ in range(6):
            module.render(data)
        ids._id_counter = itertools.count()
        ordinary = module.render(data)
        OwnershipGraph.__init__ = initialize
        ids._id_counter = itertools.count()
        instrumented = module.render(data)
        expected = {factory.__name__ for factory in TABLES.values()} | {
            own.ComponentInvocationRecord.__name__,
            own.RenderQueueRecord.__name__,
        }
        if (
            ordinary != instrumented
            or set(counts) != expected
            or not all(counts.values())
            or sum(counts.values()) != 2828
        ):
            raise RuntimeError("Direct constructor instrumentation changed output or missed a record family")
    finally:
        RESTORE()
    report = {
        "instrumentation": "Untimed direct-constructor wrapper for four record tables and invocation/queue journal.",
        "html_equal": True,
        "direct_constructions": dict(counts),
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__).resolve(),
                Path(__file__).with_name("adapter.py"),
                ROOT / "benchmarks/native_record_export_probe/adapter.py",
                ROOT / "benchmarks/native_slot_region_probe/adapter.py",
                Path(__file__).with_name("probe.py"),
                PROBE_ARTIFACT,
            )
        },
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
