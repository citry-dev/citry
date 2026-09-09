"""Check Python reference lifetimes and conversion in the packaged ownership binding."""

import bisect
import gc
import weakref
from typing import Any, NamedTuple

import pytest

from citry_core import _rust
from citry_core._ownership import Journal, RecordTable, UnsupportedRetirement


class Invocation(NamedTuple):
    id: Any
    order: Any
    source: Any
    source_class: Any
    site: Any
    tag: Any
    target_class: Any
    key: Any
    mode: Any
    target: Any
    region: Any
    bindings: Any
    selectors: Any
    state: Any


class Queue(NamedTuple):
    id: Any
    enqueued: Any
    target: Any
    rendered: Any
    settled: Any
    state: Any


class Instance(NamedTuple):
    order: Any
    id: Any
    class_id: Any
    name: Any
    invocation: Any
    parent: Any
    transparent: Any
    state: Any


class Edge(NamedTuple):
    order: Any
    invocation: Any
    parent: Any
    child: Any
    state: Any


class Fill(NamedTuple):
    id: Any
    order: Any
    kind: Any
    name: Any
    policy: Any
    owner: Any
    owner_class: Any
    site: Any
    invocation: Any
    receiver: Any
    receiver_class: Any
    fallback: Any
    state: Any


class Region(NamedTuple):
    id: Any
    order: Any
    fill: Any
    receiver: Any
    site: Any
    owner: Any
    source: Any
    containing: Any
    transition: Any
    result: Any
    state: Any


class Row(NamedTuple):
    order: Any
    payload: Any
    state: Any


def journal():
    return Journal(Invocation, Queue, "active", "enqueued", "rendered")


def capture(value, *, identifier=1, order=2):
    return value.capture((identifier, 1, "owner", "Owner", 1, "child", "Child", None, None, None, None, ()), order)


def tables():
    instances, edges, fills, regions = (
        RecordTable(factory, len(factory._fields)) for factory in (Instance, Edge, Fill, Region)
    )
    instances.append_values((1, "owner", "Owner", "Owner", None, None, False, "active"))
    instances.append_values((4, "child", "Child", "Child", 1, "owner", False, "active"))
    edges.append_values((5, 1, "owner", "child", "active"))
    return instances, edges, fills, regions


def retire(value, records, *, through=10):
    return value.retire_output(
        records,
        ("owner", through, {"child"}, set(), set()),
        10,
        ("captured", "retired", "retired", "failed", "retired"),
    )


def test_packaged_types_and_exception_identity():
    assert Journal is _rust.ownership.Journal
    assert RecordTable is _rust.ownership.RecordTable
    assert UnsupportedRetirement is _rust.ownership.UnsupportedRetirement
    value = journal()
    capture(value, identifier=2**64)
    saved = value.invocation(0)
    with pytest.raises(UnsupportedRetirement, match="fit u64"):
        retire(value, tables())
    assert value.invocation(0) is saved
    assert saved.state == "active"


def test_sequence_reads_keep_field_identity_and_retained_views():
    payload = object()
    value = RecordTable(Row, 3)
    value.set_tuple_constructor(tuple.__new__)
    value.append_values((1, payload, "active"))
    before = value[0]
    assert type(before) is Row
    assert value[-1] is before
    assert before.payload is payload
    assert bisect.bisect_right(value, 1, key=lambda row: row.order) == 1
    value.patch(0, ((2, "retired"),))
    assert before.state == "active"
    assert value[0].state == "retired"
    assert list(value) == [value[0]]
    assigned = Row(2, payload, "assigned")
    value[0] = assigned
    assert value[0] is assigned
    value.append(assigned)
    assert value[1] is assigned
    with pytest.raises(IndexError):
        value[2]
    with pytest.raises(IndexError):
        value.patch(0, ((2, "wrong"), (3, None)))
    assert value[0] is assigned
    with pytest.raises(ValueError, match="width"):
        value.append_values((1,))
    assert len(value) == 2


def test_failed_export_can_be_retried():
    value = RecordTable(Row, 3)
    value.append_values((1, "payload", "active"))
    value.set_tuple_constructor(42)
    with pytest.raises(TypeError):
        value[0]
    value.set_tuple_constructor(tuple.__new__)
    assert value[0] == Row(1, "payload", "active")


def test_journal_retains_arbitrary_precision_orders_and_previous_views():
    enqueued, rendered, settled = (int(str(2**64 + offset)) for offset in range(1, 4))
    value = journal()
    value.set_tuple_constructor(tuple.__new__)
    capture(value, order=enqueued)
    initial = value.queue(0)
    assert initial.enqueued is enqueued
    assert value.bind(0, "Child", "child", rendered, selector=False) == "owner"
    bound = value.invocation(0)
    value.settle(0, settled, "settled")
    assert value.queue(0).rendered is rendered
    assert value.queue(0).settled is settled
    assert initial.target is None
    value.bind(0, "Selector", "selector", 0, selector=True)
    assert bound.selectors == ()
    assert value.invocation(0).selectors == ("selector",)
    order = value.retire_many([0], settled, "retired", "retired", "failed")
    assert value.queue(0).settled is order
    assert order == settled + 1
    assert bound.state == "active"


def test_failed_queue_and_assigned_orders_survive_retirement():
    value = journal()
    capture(value)
    enqueued, rendered = (int(str(2**64 + offset)) for offset in (1, 2))
    value.set_queue(0, Queue(1, enqueued, None, rendered, None, "failed"))
    before = value.queue(0)
    order = 2**64 + 3
    assert value.retire_many([0], order, "retired", "retired", "failed") is order
    assert value.queue(0) is before
    # A later setter invalidates the queue cache and forces a fresh export.
    value.set_invocation(0, value.invocation(0))
    assert value.queue(0).enqueued is enqueued
    assert value.queue(0).rendered is rendered


def test_native_retirement_updates_rows_and_keeps_earlier_exports():
    value = journal()
    capture(value)
    value.bind(0, "Child", "child", 3, selector=False)
    records = tables()
    before = tuple(tuple(table) for table in records)
    order, receivers, promoted = retire(value, records)
    assert order == 11
    assert receivers == []
    assert promoted is False
    assert value.invocation(0).state == "retired"
    assert value.queue(0).settled == 11
    assert records[0][0].state == "active"
    assert records[0][1].state == "retired"
    assert records[1][0].state == "retired"
    assert before[0][1].state == "active"
    assert before[1][0].state == "active"


@pytest.mark.parametrize("kind", ["table-type", "table-width", "cutoff", "states"])
def test_retirement_rejects_unsupported_inputs_before_mutation(kind):
    value = journal()
    capture(value)
    records = tables()
    before = value.invocation(0)
    if kind == "table-type":
        records = ([], *records[1:])
        error = TypeError
    elif kind == "table-width":
        records = (RecordTable(Row, 3), *records[1:])
        error = ValueError
    else:
        error = UnsupportedRetirement if kind == "cutoff" else ValueError
    inputs = ("owner", -1 if kind == "cutoff" else 10, {"child"}, set(), set())
    states = () if kind == "states" else ("captured", "retired", "retired", "failed", "retired")
    with pytest.raises(error):
        value.retire_output(records, inputs, 10, states)
    assert value.invocation(0) is before


@pytest.mark.parametrize("exported", [False, True])
@pytest.mark.parametrize("kind", ["table", "journal"])
def test_native_fields_and_export_caches_release_cycles(kind, exported):
    class Payload:
        pass

    payload = Payload()
    if kind == "table":
        value = RecordTable(Row, 3)
        value.append_values((1, payload, "active"))
        if exported:
            value[0]
    else:
        value = journal()
        capture(value, order=payload)
        if exported:
            value.queue(0)
    payload.owner = value
    reference = weakref.ref(payload)
    del payload, value
    gc.collect()
    assert reference() is None
