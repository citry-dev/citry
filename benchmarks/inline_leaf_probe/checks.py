"""Observe selected callbacks and compare the declared remaining output and ownership."""

from __future__ import annotations

import itertools
import json
import re
from collections import Counter
from contextlib import contextmanager
from typing import Any

from benchmarks.inline_leaf_probe import adapter, compare
from benchmarks.leaf_contract_probe import adapter as identity_adapter
from benchmarks.render_structure_probe.census import digest

import citry.util.id as ids
from citry import component_render as runtime
from citry.nodes import ComponentNode
from citry.ownership import OwnershipGraph


@contextmanager
def installed(module: Any, variant: str) -> Any:
    """Restore every patched entry point after each bounded fixture comparison."""
    original = runtime._render_one, runtime._finalize, ComponentNode.render
    try:
        if variant == "identity":
            identity_adapter.install(module, enabled=True)
        elif variant == "inline":
            adapter.install(module, enabled=True)
        elif variant != "reference":
            raise ValueError("Unknown inline experiment variant")
        yield
    finally:
        runtime._render_one, runtime._finalize, ComponentNode.render = original


def observe(module: Any, call: Any) -> dict[str, Any]:
    """Keep full snapshot values for comparison and report activation independently."""
    snapshots = []
    counts: Counter[str] = Counter()
    original_snapshot = OwnershipGraph.snapshot
    original_render = runtime._render_one
    original_initializer = module.HeroIcon.__init__

    def snapshot(graph: Any) -> Any:
        result = original_snapshot(graph)
        snapshots.append(result)
        return result

    def render(element: Any, parent: Any = None, provides: Any = None) -> Any:
        result = original_render(element, parent, provides)
        if element.comp_cls is module.HeroIcon:
            counts["selected_calls"] += 1
            if result.render.frame.render_id is not None:
                counts["selected_frames_with_id"] += 1
        return result

    def initialize(self: Any, *args: Any, **kwargs: Any) -> Any:
        counts["selected_initializations"] += 1
        return original_initializer(self, *args, **kwargs)

    OwnershipGraph.snapshot = snapshot
    runtime._render_one = render
    module.HeroIcon.__init__ = initialize
    ids._id_counter = itertools.count()
    try:
        output = call()
        generated = next(ids._id_counter)
    finally:
        OwnershipGraph.snapshot = original_snapshot
        runtime._render_one = original_render
        module.HeroIcon.__init__ = original_initializer
    names, selected = compare.render_names(snapshots, module.HeroIcon.class_id)
    client_ids = {value for match in re.finditer(r'\bdata-cid="([^"]*)"', output) for value in match[1].split()}
    counts["selected_client_markers"] = len(client_ids & selected)
    wire_ids = {
        row["renderId"]
        for match in re.finditer(r'<script type="application/json" data-citry-graph>(.*?)</script>', output, re.DOTALL)
        for graph in json.loads(match[1])["graphs"]
        for row in graph["componentInstances"]
    }
    counts["selected_wire_instances"] = len(wire_ids & selected)
    counts["selected_identities"] = len(selected)
    counts["generated_ids"] = generated
    counts["selected_invocations"] = len(
        {
            row.id
            for s in snapshots
            for row in s.component_invocations
            if row.target_class_id == module.HeroIcon.class_id
        }
    )
    return {
        "raw_html": output,
        "names": names,
        "selected": selected,
        "html": compare.html(output, names, selected),
        "graphs": [compare.graph(s, names, module.HeroIcon.class_id) for s in snapshots],
        "raw_counts": [{name: len(getattr(s, name)) for name in s.__dataclass_fields__} for s in snapshots],
        "counts": dict(counts),
    }


def shifted_names(names: dict[str, str], selected: set[str], offset: int) -> tuple[dict[str, str], set[str]]:
    """Follow the ordinary fixed-width generator without changing global generator state."""
    changed = {}
    for key in names:
        value = (int(key[1:], 36) + offset) % (36**8)
        chars = []
        for _ in range(8):
            value, digit = divmod(value, 36)
            chars.append("0123456789abcdefghijklmnopqrstuvwxyz"[digit])
        changed[key] = "c" + "".join(reversed(chars))
    return {changed[key]: name for key, name in names.items()}, {changed[key] for key in selected}


def summary(observation: dict[str, Any]) -> dict[str, Any]:
    """Keep compact evidence after full in-memory comparisons finish."""
    return {
        "html_digest": digest(observation["html"]),
        "graph_digests": [digest(graph) for graph in observation["graphs"]],
        "counts": observation["counts"],
        "raw_counts": observation["raw_counts"],
        "raw_bytes": len(observation["raw_html"].encode()),
    }
