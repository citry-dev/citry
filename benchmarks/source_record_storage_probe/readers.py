"""Count deferred source-record exports and identify their Python readers."""

from __future__ import annotations

import hashlib
import inspect
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.source_record_storage_probe.adapter import CANDIDATES, install  # noqa: E402
from benchmarks.source_record_storage_probe.probe import scenario  # noqa: E402

from citry import ownership  # noqa: E402


def main() -> None:
    """Observe one warm render; no reported duration comes from this diagnostic."""
    install(changed=True)
    module = scenario()
    data = module.gen_render_data()
    for _ in range(6):
        module.render(data)
    factories = Counter()
    capture_calls = 0
    prefixes = []
    original_initialize = ownership.OwnershipGraph._initialize_native_storage
    original_record = ownership.OwnershipGraph.record_source_location

    def export(cls: Any, fields: Any) -> Any:
        frame = inspect.currentframe()
        caller = frame.f_back
        factories[(caller.f_code.co_filename, caller.f_code.co_name)] += 1
        del caller, frame
        return tuple.__new__(cls, fields)

    def initialize(graph: Any) -> None:
        original_initialize(graph)
        if isinstance(graph._source_locations, ownership._RecordTable):
            prefixes.append(len(graph._source_locations))
            graph._source_locations.set_tuple_constructor(export)

    def record(graph: Any, *args: Any, **kwargs: Any) -> Any:
        nonlocal capture_calls
        capture_calls += 1
        return original_record(graph, *args, **kwargs)

    ownership.OwnershipGraph._initialize_native_storage = initialize
    ownership.OwnershipGraph.record_source_location = record
    try:
        output = module.render(data)
    finally:
        for name, method in CANDIDATES.items():
            setattr(ownership.OwnershipGraph, name, method)
        install(changed=False)
    report = {
        "diagnostic_only": True,
        "timing_measured": False,
        "capture_calls": capture_calls,
        "prefix_rows_at_conversion": prefixes,
        "native_export_count": sum(factories.values()),
        "exports_by_python_reader": [
            {"file": filename, "function": name, "count": count}
            for (filename, name), count in sorted(factories.items())
        ],
        "html_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__), Path(__file__).with_name("adapter.py"), Path(ownership.__file__))
        },
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
