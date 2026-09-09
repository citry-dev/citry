"""Differential retirement checks, including sparse IDs and retained snapshots."""

from __future__ import annotations

import argparse
import random
from dataclasses import fields
from typing import Any

from probe import install, load_native, own
from storage_probe import install_storage


def make_graph(seed: int) -> Any:
    """Build relationship-consistent graphs with historical and later records."""
    rng = random.Random(seed)  # noqa: S311 - Reproducible graph fixtures.
    graph = own.OwnershipGraph()
    count = rng.randrange(2, 35)
    names = [f"component-{i}" for i in range(count)]
    # Collisions exercise set table layouts, including resize boundaries.
    invocation_ids = [i * rng.choice((32, 256, 4096)) + seed * 65536 for i in range(1, count)]
    invocation_ids = list(dict.fromkeys(invocation_ids))
    region_ids = [17 + i * 32 for i in range(rng.randrange(1, 25))]
    fill_ids = list(range(1, rng.randrange(2, 15)))
    graph._logical_instances = [own.LogicalInstanceRecord(1, names[0], "Root", "Root", None, None, transparent=False)]
    for i, invocation_id in enumerate(invocation_ids, 1):
        parent = rng.choice(names[:i])
        target = names[i] if rng.random() < 0.9 else None
        selectors = tuple(rng.sample(names[:i], k=rng.randrange(min(i, 3))))
        invocation = own.ComponentInvocationRecord(
            invocation_id,
            10 + i * 4,
            parent,
            "Source",
            1,
            "child",
            "Target",
            None,
            None,
            target,
            rng.choice([None, *region_ids]),
            (),
            selectors,
            rng.choice(list(own.OwnershipState)),
        )
        graph._component_invocations.append(invocation)
        graph._invocation_index[invocation_id] = i - 1
        graph._queue_index[invocation_id] = i - 1
        graph._render_queue.append(
            own.RenderQueueRecord(
                invocation_id,
                invocation.order + 1,
                target,
                invocation.order + 2,
                None,
                rng.choice(list(own.QueueState)),
            )
        )
        graph._logical_instances.append(
            own.LogicalInstanceRecord(
                invocation.order + 2,
                names[i],
                f"Class{i}",
                "Component",
                invocation_id,
                parent,
                transparent=False,
                state=rng.choice(list(own.OwnershipState)),
            )
        )
        graph._init_ancestry.append(
            own.InitAncestryRecord(
                invocation.order + 3,
                invocation_id,
                parent,
                names[i],
                rng.choice(list(own.OwnershipState)),
            )
        )
    for fill_id in fill_ids:
        owner = rng.choice([None, *names])
        receiver = rng.choice([None, *names])
        graph._logical_fills.append(
            own.LogicalFillRecord(
                fill_id,
                2 + fill_id,
                rng.choice(list(own.LogicalFillKind)),
                f"slot-{fill_id % 3}",
                rng.choice(list(own.SourcePolicy)),
                owner,
                "Owner",
                None,
                None,
                receiver,
                "Receiver",
                None,
                rng.choice(list(own.OwnershipState)),
            )
        )
        graph._fill_index[fill_id] = len(graph._logical_fills) - 1
    for i, region_id in enumerate(region_ids):
        receiver = rng.choice([None, *names])
        graph._physical_regions.append(
            own.PhysicalRegionRequestRecord(
                region_id,
                5 + i * 9,
                rng.choice(fill_ids),
                receiver,
                None,
                rng.choice([None, *names]),
                None,
                rng.choice([None, *region_ids[:i]]),
                receiver,
                rng.choice([None, *names]),
                rng.choice(list(own.RegionState)),
            )
        )
        graph._region_index[region_id] = i
    graph._order = 300
    graph._relation_indexes_current = False
    return graph


def clone_native(reference: Any, enable: Any, *, stored: bool = False) -> Any:
    """Copy reference rows through the same native journal boundary as capture."""
    enable()
    graph = own.OwnershipGraph()
    if isinstance(graph._component_invocations, list):
        # The shipping runtime delays native storage until its first nested call.
        graph._initialize_native_storage()
    for name in ("_logical_instances", "_init_ancestry", "_logical_fills", "_physical_regions"):
        if stored:
            table = getattr(graph, name)
            for row in getattr(reference, name):
                table.append(row)
        else:
            setattr(graph, name, list(getattr(reference, name)))
    for name in ("_invocation_index", "_queue_index", "_fill_index", "_region_index", "_receiver_fill"):
        setattr(graph, name, dict(getattr(reference, name)))
    graph._order = reference._order
    journal = graph._component_invocations.journal
    for invocation, queue in zip(reference._component_invocations, reference._render_queue, strict=True):
        index = journal.capture(tuple(invocation[:12]), queue.enqueued_order)
        journal.set_invocation(index, invocation)
        journal.set_queue(index, queue)
    return graph


def check(seed_count: int = 1000, *, stored: bool = False, native_ancestors: bool = False) -> None:
    """Compare all rows, settlement order and indexes after sequential retirements."""
    native = load_native()
    enable, disable = (
        install_storage(native, {"native_calls": 0, "fallback_calls": 0}, native_ancestors=native_ancestors)
        if stored
        else install(native, native_retirement=True)
    )
    for seed in range(seed_count):
        disable()
        reference = make_graph(seed)
        candidate = clone_native(reference, enable, stored=stored)
        saved_reference = reference.snapshot()
        saved_candidate = candidate.snapshot()
        rng = random.Random(seed + 1_000_000)  # noqa: S311 - Reproducible retirement inputs.
        names = [row.render_id for row in reference._logical_instances]
        regions = [row.id for row in reference._physical_regions]
        for step in range(3):
            inputs = {
                "through_order": rng.randrange(0, 210),
                "descendant_render_ids": set(rng.sample(names, rng.randrange(len(names) + 1))),
                "preserved_render_ids": set(rng.sample(names, rng.randrange(min(4, len(names))))),
                "preserved_region_ids": set(rng.sample([999999, *regions], rng.randrange(min(4, len(regions))))),
            }
            owner = rng.choice(names)
            disable()
            reference.retire_component_output(owner, **inputs)
            enable()
            candidate.retire_component_output(owner, **inputs)
            if reference.snapshot() != candidate.snapshot():
                for descriptor in fields(reference.snapshot()):
                    field = descriptor.name
                    left = getattr(reference.snapshot(), field)
                    right = getattr(candidate.snapshot(), field)
                    if left != right:
                        raise AssertionError(
                            f"seed={seed} step={step} field={field}: {left!r} != {right!r}; {inputs!r}"
                        )
            if reference._order != candidate._order or reference._receiver_fill != candidate._receiver_fill:
                raise AssertionError(f"seed={seed} step={step}: order or receiver lookup differs")
            if saved_reference != saved_candidate:
                raise AssertionError(f"seed={seed} step={step}: retained snapshots changed")
            # A subsequent Python reader must observe the same rebuilt relations.
            reference._ensure_relation_indexes()
            candidate._ensure_relation_indexes()
            if reference._region_ids_by_receiver != candidate._region_ids_by_receiver:
                raise AssertionError(f"seed={seed} step={step}: receiver index differs")
    disable()
    print(f"{seed_count} graphs, {seed_count * 3} sequential retirement comparisons passed")


def check_fallback(*, stored: bool = False, native_ancestors: bool = False) -> None:
    """Require unsupported IDs to fail before mutation and use the reference."""

    class CustomId(str):
        __slots__ = ()

    class CustomNumber(int):
        __slots__ = ()

    class RehashedRegion(int):
        __slots__ = ()

        def __hash__(self) -> int:
            return -12345

    cases = [
        ("string", None, None),
        ("slot_name", None, None),
        ("preserved_region", None, None),
        ("through_order", None, None),
        ("current_order", None, None),
        *[
            ("row", table, field)
            for table, fields_to_check in (
                ("_component_invocations", ("id", "order", "physical_parent_region_id")),
                ("_logical_instances", ("order",)),
                ("_init_ancestry", ("order", "invocation_id")),
                ("_logical_fills", ("id", "order")),
                ("_physical_regions", ("id", "order", "logical_fill_id", "containing_region_id")),
            )
            for field in fields_to_check
        ],
    ]
    native = load_native()
    enable, disable = (
        install_storage(native, {"native_calls": 0, "fallback_calls": 0}, native_ancestors=native_ancestors)
        if stored
        else install(native, native_retirement=True)
    )
    for kind, table_name, field in cases:
        disable()
        reference = make_graph(0 if kind == "preserved_region" else 123)
        through = 300
        preserved_regions = set()
        if kind == "string":
            reference._logical_instances[0] = reference._logical_instances[0]._replace(
                render_id=CustomId("component-0")
            )
        elif kind == "slot_name":
            reference._logical_fills[0] = reference._logical_fills[0]._replace(slot_name=CustomId("slot-0"))
        elif kind == "preserved_region":
            preserved_regions = {RehashedRegion(17)}
        elif kind == "through_order":
            through = CustomNumber(300)
        elif kind == "current_order":
            reference._order = CustomNumber(300)
        else:
            rows = getattr(reference, table_name)
            index = next(i for i, row in enumerate(rows) if getattr(row, field) is not None)
            rows[index] = rows[index]._replace(**{field: CustomNumber(getattr(rows[index], field))})
        candidate = clone_native(reference, enable, stored=stored)
        before = candidate.snapshot()
        before_order = candidate._order
        try:
            candidate._component_invocations.journal.retire_output(
                (
                    candidate._logical_instances,
                    candidate._init_ancestry,
                    candidate._logical_fills,
                    candidate._physical_regions,
                ),
                ("component-0", through, set(), set(), preserved_regions),
                candidate._order,
                (own.RegionState.CAPTURED, own.OwnershipState.RETIRED, own.QueueState.RETIRED, own.QueueState.FAILED)
                + ((own.RegionState.RETIRED,) if stored else ()),
            )
        except native.UnsupportedRetirement:
            pass
        else:
            raise AssertionError(f"Custom values must reject native calculation: {kind} {table_name} {field}")
        if candidate.snapshot() != before or candidate._order != before_order:
            raise AssertionError("Unsupported input mutated the journal before fallback")
        disable()
        reference.retire_component_output("component-0", through_order=through, preserved_region_ids=preserved_regions)
        enable()
        candidate.retire_component_output("component-0", through_order=through, preserved_region_ids=preserved_regions)
        if candidate.snapshot() != reference.snapshot() or candidate._order != reference._order:
            raise AssertionError(f"Custom-value fallback differs from Python: {kind} {table_name} {field}")
    disable()
    print(f"{len(cases)} custom-value rejection and Python fallback cases passed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=1000)
    parser.add_argument("--storage", action="store_true")
    parser.add_argument("--native-ancestors", action="store_true")
    args = parser.parse_args()
    if args.native_ancestors and not args.storage:
        parser.error("--native-ancestors requires --storage")
    check(args.seeds, stored=args.storage, native_ancestors=args.native_ancestors)
    check_fallback(stored=args.storage, native_ancestors=args.native_ancestors)


if __name__ == "__main__":
    main()
