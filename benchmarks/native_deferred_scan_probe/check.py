"""Compare native discovery with current Python task ordering and identities."""

# ruff: noqa: S101 - executable experimental assertions

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.native_deferred_scan_probe import adapter  # noqa: E402
from markupsafe import Markup  # noqa: E402

from citry import citry_render as renders  # noqa: E402
from citry import component_render as components  # noqa: E402
from citry.citry_context import CitryContext  # noqa: E402


def wrap(part: Any, *, render: bool = False) -> Any:
    """Build only the slots read by discovery, with deliberately different mirrored slots."""
    cls = renders.PhysicalRegionRender if render else renders.PhysicalRegionPart
    wrapper = object.__new__(cls)
    wrapper.part = part
    if render:
        wrapper.parts = [object.__new__(renders.DeferredComponent)]
        wrapper.context = CitryContext()
    return wrapper


def compare(root: Any) -> int:
    """Task constructors must retain the current list, node and context objects."""
    expected = adapter.ORIGINAL(root)
    actual = adapter.scan(root)
    assert len(expected) == len(actual)
    for before, after in zip(expected, actual, strict=True):
        assert type(before) is type(after)
        if isinstance(before, components._RenderTask):
            assert before.deferred is after.deferred
            assert before.position.parts is after.position.parts
            assert before.position.idx == after.position.idx
            assert before.position.parent_context is after.position.parent_context
        else:
            assert before.parent_context is after.parent_context
            assert before.child_context is after.child_context
    return len(actual)


def main() -> None:
    """Exercise current-tree edits, repeated occurrences, wrappers and fallbacks."""
    rng = random.Random(20261009)  # noqa: S311 - reproducible generated trees
    contexts = [CitryContext() for _ in range(4)]
    tasks = 0
    for _ in range(1000):
        pool = []
        for _depth in range(4):
            parts = []
            for _item in range(rng.randrange(8)):
                choice = rng.randrange(6)
                if choice == 0:
                    parts.append(object.__new__(renders.DeferredComponent))
                elif choice == 1 and pool:
                    parts.append(rng.choice(pool))
                elif choice in (2, 3) and pool:
                    parts.append(wrap(rng.choice(pool), render=choice == 3))
                elif choice == 4:
                    parts.append(renders.Placeholder("deps:js"))
                else:
                    parts.append(Markup("text") if rng.randrange(2) else "text")
            root = renders.CitryRender(parts, rng.choice(contexts))
            pool.append(root)
        assert adapter.NATIVE.scan(root, adapter.TYPES) is not None
        tasks += compare(root)
        root.parts.reverse()
        tasks += compare(root)

    deferred = object.__new__(renders.DeferredComponent)
    root = renders.CitryRender([wrap(deferred)], contexts[0])
    assert compare(root) == 0
    root.parts[:] = [wrap(wrap(renders.CitryRender([deferred], contexts[1])), render=True)]
    assert compare(root) == 2

    class CustomRender(renders.CitryRender):
        pass

    unsupported = [object(), CustomRender([deferred], contexts[1])]
    for part in unsupported:
        root = renders.CitryRender([part], contexts[0])
        assert adapter.NATIVE.scan(root, adapter.TYPES) is None
        compare(root)
    root = renders.CitryRender((deferred,), contexts[0])
    assert adapter.NATIVE.scan(root, adapter.TYPES) is None
    compare(root)

    original_getter = renders.CitryRender.__getattribute__
    reads = []

    def getter(self: Any, name: str) -> Any:
        reads.append(name)
        return original_getter(self, name)

    root = renders.CitryRender([deferred], contexts[0])
    try:
        renders.CitryRender.__getattribute__ = getter
        adapter.ORIGINAL(root)
        expected = reads[:]
        reads.clear()
        adapter.scan(root)
        assert reads == expected
    finally:
        renders.CitryRender.__getattribute__ = original_getter

    inner = renders.CitryRender([deferred], contexts[1])
    root = renders.CitryRender([inner], contexts[0])
    try:
        renders.CitryRender.__getattribute__ = lambda self, name: (
            renders.DeferredComponent if name == "__class__" else original_getter(self, name)
        )
        assert compare(root) == 1
        assert adapter.scan(root)[0].deferred is inner
    finally:
        renders.CitryRender.__getattribute__ = original_getter

    original_base = renders._PhysicalRegion
    root = renders.CitryRender([wrap(inner, render=True)], contexts[0])
    try:
        renders._PhysicalRegion = type("OtherRegion", (), {})
        compare(root)
    finally:
        renders._PhysicalRegion = original_base

    original_new = components._RenderTask.__new__
    calls = []

    def task_new(cls: Any, *args: Any, **kwargs: Any) -> Any:
        calls.append(1)
        return original_new(cls, *args, **kwargs)

    root = renders.CitryRender([deferred, object()], contexts[0])
    try:
        components._RenderTask.__new__ = staticmethod(task_new)
        adapter.scan(root)
        assert len(calls) == 1
    finally:
        components._RenderTask.__new__ = staticmethod(original_new)

    deep = renders.CitryRender([deferred], contexts[0])
    for _ in range(270):
        deep = renders.CitryRender([deep], contexts[0])
    assert adapter.NATIVE.scan(deep, adapter.TYPES) is None
    compare(deep)
    report = {
        "seeded_trees": 1000,
        "comparisons_before_and_after_reverse": 2000,
        "tasks_compared": tasks,
        "wrapped_deferred_preserves_original_ignore": True,
        "wrapped_render_uses_inner_context_and_parts": True,
        "unknown_subclass_nonlist_and_depth_fallback": True,
        "changed_getattribute_preserves_original_reads": True,
        "changed_class_dispatch_and_wrapper_base_use_original_scan": True,
        "changed_task_constructor_runs_once_on_unsupported_tree": True,
        "production_qualified": False,
    }
    (ROOT / "benchmarks/results/performance-render/native-deferred-scan-contracts.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
