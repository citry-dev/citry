"""Compare native ancestry membership, iteration and retained string identities."""

from __future__ import annotations

import argparse
import random

from check_retirement import clone_native, make_graph
from storage_probe import install_storage, load_native


def fresh(value: str | None) -> str | None:
    """Create equal strings independently so identity mistakes remain visible."""
    return value.encode().decode() if value is not None else None


def check(seeds: int) -> None:
    """Cover historical rows, cyclic ancestry, duplicate parents and selectors."""
    native = load_native()
    stats = {"native_calls": 0, "fallback_calls": 0}
    enable, disable = install_storage(native, stats, native_ancestors=True)
    try:
        for seed in range(seeds):
            disable()
            reference = make_graph(seed)
            rng = random.Random(seed + 999)  # noqa: S311 - Reproducible graph fixtures.
            names = [row.render_id for row in reference._logical_instances]
            # Later duplicate logical rows override only non-None parents.
            first = reference._logical_instances[0]
            reference._logical_instances.extend(
                [
                    first._replace(logical_parent_render_id=fresh(rng.choice(names))),
                    first._replace(logical_parent_render_id=None),
                ]
            )
            for index, row in enumerate(reference._logical_instances):
                reference._logical_instances[index] = row._replace(
                    render_id=fresh(row.render_id), logical_parent_render_id=fresh(row.logical_parent_render_id)
                )
            for index, row in enumerate(reference._component_invocations):
                reference._component_invocations[index] = row._replace(
                    source_render_id=fresh(row.source_render_id),
                    target_render_id=fresh(row.target_render_id),
                    selector_render_ids=tuple(fresh(value) for value in row.selector_render_ids),
                )
            for index, row in enumerate(reference._init_ancestry):
                reference._init_ancestry[index] = row._replace(
                    parent_render_id=fresh(row.parent_render_id), child_render_id=fresh(row.child_render_id)
                )
            candidate = clone_native(reference, enable, stored=True)
            for chosen in (
                set(),
                {fresh(names[0])},
                {fresh(value) for value in rng.sample(names, rng.randrange(len(names) + 1))},
            ):
                disable()
                expected = reference._with_ownership_ancestors(chosen)
                enable()
                actual = candidate._with_ownership_ancestors(chosen)
                if list(actual) != list(expected) or [id(value) for value in actual] != [
                    id(value) for value in expected
                ]:
                    raise AssertionError(f"Ancestry membership, iteration or identity differs at seed {seed}")
            if candidate._relation_indexes_current:
                raise AssertionError("Native ancestry marked unbuilt Python indexes current")
        if stats.get("ancestry_native_calls") != seeds * 3 or stats.get("ancestry_fallback_calls", 0):
            raise AssertionError(f"Unexpected ancestry activation counters: {stats}")
    finally:
        disable()
    print(f"{seeds} graphs, {seeds * 3} ancestry membership/iteration/identity comparisons passed")


def check_fallback() -> None:
    """Reject custom index keys before bypassing the original Python index builder."""

    class CustomString(str):
        __slots__ = ()

    class CustomInt(int):
        __slots__ = ()

    class CustomSet(set):
        pass

    class CustomTuple(tuple):
        __slots__ = ()

    cases = [
        ("_logical_instances", "render_id", CustomString),
        ("_logical_instances", "logical_parent_render_id", CustomString),
        ("_component_invocations", "source_render_id", CustomString),
        ("_component_invocations", "target_render_id", CustomString),
        ("_component_invocations", "physical_parent_region_id", CustomInt),
        ("_component_invocations", "id", CustomInt),
        ("_init_ancestry", "parent_render_id", CustomString),
        ("_init_ancestry", "child_render_id", CustomString),
        ("_physical_regions", "receiver_render_id", CustomString),
        ("_physical_regions", "logical_fill_id", CustomInt),
        ("_physical_regions", "containing_region_id", CustomInt),
        (None, "seed_subclass", CustomString),
        (None, "seed_surrogate", str),
        (None, "seed_set", CustomSet),
        (None, "seed_frozen", frozenset),
        (None, "selector_tuple", CustomTuple),
        (None, "selector_list", list),
    ]
    native = load_native()
    stats = {"native_calls": 0, "fallback_calls": 0}
    enable, disable = install_storage(native, stats, native_ancestors=True)
    try:
        for table, field, factory in cases:
            disable()
            reference = make_graph(123)
            chosen = {"component-0"}
            if table is not None:
                rows = getattr(reference, table)
                index = next(index for index, row in enumerate(rows) if getattr(row, field) is not None)
                rows[index] = rows[index]._replace(**{field: factory(getattr(rows[index], field))})
            elif field == "seed_subclass":
                chosen = {CustomString("component-0")}
            elif field == "seed_surrogate":
                chosen = {"\ud800"}
            elif field == "seed_set":
                chosen = CustomSet(chosen)
            elif field == "seed_frozen":
                chosen = frozenset(chosen)
            else:
                index = next(
                    i for i, row in enumerate(reference._component_invocations) if row.target_render_id is not None
                )
                row = reference._component_invocations[index]
                reference._component_invocations[index] = row._replace(
                    selector_render_ids=factory(row.selector_render_ids)
                )
                chosen = {row.target_render_id}
            candidate = clone_native(reference, enable, stored=True)
            before = candidate.snapshot()
            try:
                candidate._component_invocations.journal.ancestors(
                    candidate._logical_instances, candidate._init_ancestry, candidate._physical_regions, chosen
                )
            except native.UnsupportedRetirement:
                pass
            else:
                raise AssertionError(f"Native ancestry accepted unqualified {table}/{field}")
            disable()
            expected = reference._with_ownership_ancestors(chosen)
            enable()
            actual = candidate._with_ownership_ancestors(chosen)
            if list(actual) != list(expected) or candidate.snapshot() != before:
                raise AssertionError(f"Ancestry fallback differs for {table}/{field}")
        if stats.get("ancestry_fallback_calls") != len(cases):
            raise AssertionError(f"Missing ancestry fallbacks: {stats}")
    finally:
        disable()
    print(f"{len(cases)} unsupported-key/seed fallback cases passed")


def main() -> None:
    """Run opt-in ancestry checks without adding a repository-wide gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=1000)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    check(args.seeds)
    check_fallback()


if __name__ == "__main__":
    main()
