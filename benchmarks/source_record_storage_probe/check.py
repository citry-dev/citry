"""Check source-record identity, errors, replay rollback and native GC."""

# ruff: noqa: S101 - executable contract assertions

from __future__ import annotations

import gc
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from weakref import ref

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.source_record_storage_probe.adapter import install  # noqa: E402

from citry import ownership  # noqa: E402
from citry.citry_context import CitryContext  # noqa: E402


def run(changed: bool) -> dict[str, object]:
    """Exercise reads and writes before and after the source table changes."""
    install(changed)
    graph = ownership.OwnershipGraph()
    context = CitryContext(component=SimpleNamespace(id="owner", _citry_class_id="class"))

    def record(**extra: Any) -> Any:
        arguments = {"kind": ownership.SourceLocationKind.COMPONENT_CALL, "source": "éx", "position": (0, 2)}
        arguments.update(extra)
        return graph.record_source_location(context, **arguments)

    first = record()
    prefix = graph.source_location(first)
    graph._initialize_native_storage()
    assert graph.source_location(first) is prefix
    second = record(mapping_key="key", mapping_index=3)
    exported = graph.source_location(second)
    assert graph.source_location(second) is exported
    assert graph.snapshot().source_locations[1] is exported
    assert exported.snippet == "é"
    assert exported.mapping_key == "key"
    assert exported.mapping_index == 3
    assert exported.site is prefix.site
    errors = []
    for position in ((0, 1), (0, 9), (-1, 2)):
        before = (graph._source_id, graph._order, len(graph._source_locations))
        try:
            record(position=position)
        except RuntimeError as error:
            errors.append(str(error))
        else:
            raise AssertionError("Invalid UTF-8 byte span was accepted")
        assert before == (graph._source_id, graph._order, len(graph._source_locations))

    original_new = ownership.SourceLocationRecord.__new__
    constructor_calls = []

    def custom_new(cls: Any, *args: Any, **kwargs: Any) -> Any:
        constructor_calls.append(True)
        return original_new(cls, *args, **kwargs)

    ownership.SourceLocationRecord.__new__ = staticmethod(custom_new)
    try:
        record()
        assert constructor_calls == [True]
    finally:
        ownership.SourceLocationRecord.__new__ = staticmethod(original_new)

    before = graph.snapshot()
    failure = ValueError("rollback")
    try:
        with graph.replay_transaction():
            record()
            raise failure
    except ValueError as caught:
        assert caught is failure  # noqa: PT017 - standalone checker, no pytest dependency
    assert graph.snapshot() == before
    assert type(graph._source_locations) is list
    assert graph.source_location(second) is exported
    record()
    assert len(graph._source_locations) == len(before.source_locations) + 1

    # An override can change the record constructor while arguments are evaluated.
    # The eager path calls the changed constructor; deferred export can miss it.
    graph2 = ownership.OwnershipGraph()
    graph2._initialize_native_storage()
    callback_calls = []
    next_order = graph2._next_order

    def observed_new(cls: Any, *args: Any, **kwargs: Any) -> Any:
        callback_calls.append(True)
        return original_new(cls, *args, **kwargs)

    def change_constructor() -> int:
        ownership.SourceLocationRecord.__new__ = staticmethod(observed_new)
        return next_order()

    graph2._next_order = change_constructor
    try:
        graph2.record_source_location(
            context, kind=ownership.SourceLocationKind.COMPONENT_CALL, source="x", position=(0, 1)
        )
    finally:
        ownership.SourceLocationRecord.__new__ = staticmethod(original_new)

    cycle = ownership.OwnershipGraph()
    cycle._initialize_native_storage()
    holder = SimpleNamespace(graph=cycle)
    cycle.record_source_location(
        context, kind=ownership.SourceLocationKind.COMPONENT_CALL, source="x", position=(0, 1), mapping_key=holder
    )
    weak_graph = ref(cycle)
    del holder, cycle
    gc.collect()
    assert weak_graph() is None
    return {
        "prefix_identity": True,
        "export_identity": True,
        "site_identity": True,
        "invalid_span_errors": errors,
        "changed_constructor_called": True,
        "rollback_identity": True,
        "append_after_rollback": True,
        "field_cycle_collected": True,
        "constructor_changed_during_arguments_called": bool(callback_calls),
    }


if __name__ == "__main__":
    try:
        reference = run(changed=False)
        candidate = run(changed=True)
        assert reference["constructor_changed_during_arguments_called"] is True
        assert candidate["constructor_changed_during_arguments_called"] is False
        print(json.dumps({"reference": reference, "candidate": candidate, "production_compatible": False}, indent=2))
    finally:
        install(changed=False)
