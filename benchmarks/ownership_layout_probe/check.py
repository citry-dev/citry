"""Record collector-layout behavior in separate interpreted and compiled processes."""

# ruff: noqa: S101 - executable experiment assertions

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from weakref import ref

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.ownership_layout_probe.adapter import install  # noqa: E402


def worker(changed: bool) -> dict[str, Any]:
    """Observe explicit compatibility boundaries without declaring equivalence."""
    install(changed)
    from citry import ownership  # noqa: PLC0415
    from citry.citry_context import CitryContext  # noqa: PLC0415

    graph_type = ownership.OwnershipGraph
    graph = graph_type()
    ordinary_fields = sorted(vars(graph))
    graph._order = 2**100
    assert graph._next_order() == 2**100 + 1
    graph._next_order = lambda: 123
    assert graph._next_order() == 123
    del graph._next_order
    context = CitryContext(component=SimpleNamespace(id="owner", _citry_class_id="class"))
    source_id = graph.record_source_location(
        context, kind=ownership.SourceLocationKind.COMPONENT_CALL, source="éx", position=(0, 2)
    )
    row = graph.source_location(source_id)
    assert row.snippet == "é"
    assert graph.snapshot().source_locations[0] is row
    before = graph.snapshot()
    failure = ValueError("rollback")
    try:
        with graph.replay_transaction():
            graph.record_source_location(
                context, kind=ownership.SourceLocationKind.COMPONENT_CALL, source="z", position=(0, 1)
            )
            raise failure
    except ValueError as caught:
        assert caught is failure  # noqa: PT017 - standalone checker
    assert graph.snapshot() == before
    assert graph.source_location(source_id) is row
    retained = ref(graph)
    graph._source_site_cache["cycle"] = graph
    del graph
    gc.collect()
    assert retained() is None

    try:
        graph_type.snapshot = graph_type.snapshot
        class_assignment = "accepted"
    except TypeError as error:
        class_assignment = str(error)
    graph = graph_type()
    graph.__dict__["_order"] = 100
    dict_write_order = graph._next_order()
    descriptor_calls = []

    class Derived(graph_type):
        @property
        def _order(self) -> int:
            descriptor_calls.append("get")
            return 100

        @_order.setter
        def _order(self, value: object) -> None:
            descriptor_calls.append("set")

    derived = Derived()
    descriptor_calls.clear()
    subclass_order = derived._next_order()
    original_type = ownership.OwnershipGraph

    class Replacement(graph_type):
        pass

    try:
        ownership.OwnershipGraph = Replacement
        with ownership.ownership_render_scope() as current:
            honors_class_rebinding = type(current) is Replacement
    finally:
        ownership.OwnershipGraph = original_type
    return {
        "candidate": changed,
        "retained_field_identity": True,
        "arbitrary_precision_order": True,
        "instance_method_override": True,
        "replay_rollback": True,
        "field_cycle_collected": True,
        "instance_dictionary_fields": ordinary_fields,
        "class_method_assignment": class_assignment,
        "dict_write_next_order": dict_write_order,
        "subclass_property_next_order": subclass_order,
        "subclass_property_calls": descriptor_calls,
        "scope_honors_graph_class_rebinding": honors_class_rebinding,
    }


def main() -> None:
    """Retain both outcomes and source provenance for the known differences."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("reference", "candidate"))
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker == "candidate")))
        return
    report = {"production_compatible": False}
    for variant in ("reference", "candidate"):
        result = subprocess.run(
            [sys.executable, __file__, "--worker", variant], cwd=ROOT, capture_output=True, text=True, check=True
        )
        report[variant] = json.loads(result.stdout)
    report["hashes"] = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (
            Path(__file__),
            Path(__file__).with_name("adapter.py"),
            ROOT / "packages/py/citry/citry/ownership.py",
        )
    }
    report["build"] = json.loads((ROOT / "benchmarks/results/repeat-render/ownership-layout-build.json").read_text())
    (ROOT / "benchmarks/results/repeat-render/ownership-layout-contracts.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
