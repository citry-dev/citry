"""Observe which Python readers force exports from current native ownership tables."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from probe import ENABLE, NATIVE, PROBE_ARTIFACT, PROBE_ROOT, RESTORE, ROOT, TABLES, OwnershipGraph, ids, scenario


def main() -> None:
    """Count exports outside timing and compare the instrumented HTML."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    counts = Counter()
    graphs = []
    ENABLE()
    original_initialize = OwnershipGraph.__init__

    def counted_factory(factory: Any) -> Any:
        def build(*fields: Any) -> Any:
            # Keep only the caller name; retaining frames would alter object lifetimes.
            caller = sys._getframe(1).f_code.co_name
            counts[(factory.__name__, caller)] += 1
            return factory(*fields)

        return build

    def initialize(graph: Any) -> None:
        original_initialize(graph)
        graphs.append(graph)
        for name, factory in TABLES.items():
            setattr(graph, name, NATIVE.RecordTable(counted_factory(factory), len(factory._fields)))

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
        if ordinary != instrumented or not graphs or not counts:
            raise RuntimeError("Native export instrumentation changed HTML or did not activate")
        rows = {name: sum(len(getattr(graph, name)) for graph in graphs) for name in TABLES}
    finally:
        RESTORE()
    report = {
        "instrumentation": "Untimed factory wrappers; nearest Python caller only; four RecordTable families.",
        "html_equal": True,
        "native_ancestors": False,
        "rows_captured": rows,
        "exports": [
            {"record": record, "caller": caller, "count": count} for (record, caller), count in counts.most_common()
        ],
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__).resolve(),
                Path(__file__).with_name("probe.py"),
                PROBE_ROOT / "probe.py",
                PROBE_ROOT / "storage_probe.py",
                PROBE_ARTIFACT,
            )
        },
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
