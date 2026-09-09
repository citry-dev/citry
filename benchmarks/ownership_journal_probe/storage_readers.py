"""Count immutable records exported by the native storage experiment, outside timing."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from collections import Counter
from pathlib import Path
from typing import Any

from storage_probe import TABLES, install_storage, load_native, own, scenario


def main() -> None:
    """Record the first Python caller visible when Rust requests a public row."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--native-ancestors", action="store_true")
    args = parser.parse_args()
    native = load_native()
    enable, disable = install_storage(
        native, {"native_calls": 0, "fallback_calls": 0}, native_ancestors=args.native_ancestors
    )
    module = scenario()
    data = module.gen_render_data()
    counts: Counter[Any] = Counter()
    graphs: list[Any] = []
    enable()
    initialize = own.OwnershipGraph.__init__

    def counted_factory(factory: Any) -> Any:
        def build(*fields: Any) -> Any:
            caller = inspect.currentframe().f_back
            counts[(factory.__name__, caller.f_code.co_name)] += 1
            return factory(*fields)

        return build

    def initialize_counted(graph: Any) -> None:
        initialize(graph)
        graphs.append(graph)
        for name, factory in TABLES.items():
            setattr(graph, name, native.RecordTable(counted_factory(factory), len(factory._fields)))

    try:
        for _ in range(6):
            module.render(data)
        own.OwnershipGraph.__init__ = initialize_counted
        module.render(data)
        report = {
            "native_ancestors": args.native_ancestors,
            "instrumentation": "Untimed factory wrappers; nearest Python caller only.",
            "storage_adapter_sha256": hashlib.sha256(
                (Path(__file__).parent / "storage_probe.py").read_bytes()
            ).hexdigest(),
            "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "rows_captured": {name: sum(len(getattr(graph, name)) for graph in graphs) for name in TABLES},
            "exports": [
                {"record": record, "caller": caller, "count": count}
                for (record, caller), count in counts.most_common()
            ],
        }
    finally:
        disable()
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
