"""Check live inputs, helper replacements and explicit prototype limitations."""

# ruff: noqa: S101 - executable experimental assertions

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.attrs_pipeline_probe import adapter  # noqa: E402

from citry import Component, attrs, nodes  # noqa: E402
from citry.citry_context import CitryContext  # noqa: E402


class Inputs:
    key = "c-bind"

    def __init__(self, values: dict[str, Any]) -> None:
        self.values = values
        self.calls = 0

    def resolve(self, context: Any) -> Any:
        self.calls += 1
        return self.values


def make(values: dict[str, Any], component: Any = None) -> tuple[Any, Any, Any]:
    """Use a live spread so the same node sees changing application inputs."""
    source = Inputs(values)
    node = nodes.ElementAttrsNode("<div>", (0, 5), (source,), ())
    context = CitryContext(component=component)
    return node, context, source


def main() -> None:
    """Exercise supported prototype cases and retain an observable read-order gap."""
    try:
        outputs = []
        for changed in (False, True):
            adapter.install(changed)
            node, context, source = make({"class": "a a b", "style": "color:red;color:blue", "title": "<&"})
            results = [node.render(context), node.render(context)]
            source.values = {"title": "changed", "class": "a", "disabled": True, "hidden": False}
            results.append(node.render(context))
            assert source.calls == 3
            outputs.append(results)
        assert outputs[0] == outputs[1]

        adapter.install(changed=True)
        node, context, source = make({"style": "color:red"})
        assert node.render(context) == ' style="color: red;"'
        original = attrs.parse_string_style
        try:
            attrs.parse_string_style = lambda _value: {"color": "blue"}
            assert node.render(context) == ' style="color: blue;"'
        finally:
            attrs.parse_string_style = original

        original = attrs._collect_class
        node, context, source = make({"class": "a" * 257})
        node.render(context)
        try:
            attrs._collect_class = lambda _value, result: result.update({"changed": True})
            assert node.render(context) == ' class="changed"'
        finally:
            attrs._collect_class = original

        class Content:
            def __init__(self) -> None:
                self.calls = 0

            def __html__(self) -> str:
                self.calls += 1
                return str(self.calls)

        value = Content()
        node, context, source = make({"title": value})
        assert node.render(context) == ' title="1"'
        assert node.render(context) == ' title="2"'
        node, context, source = make({"class": False})
        for _ in range(2):
            try:
                node.render(context)
            except TypeError:
                pass
            else:
                raise AssertionError("An invalid class value was accepted")
        assert source.calls == 2

        node, context, source = make({"title": "before"})
        node.render(context)
        node._resolve = lambda _context: {"title": "override"}
        assert node.render(context) == ' title="override"'

        component = Component._create_instance()
        node, context, source = make({"title": "plain"}, component)
        node.render(context)
        manager = component.citry.extensions
        try:
            manager.has_attrs_resolved_hook = lambda **_kwargs: True
            manager.on_attrs_resolved = lambda **_kwargs: {"title": "hooked"}
            assert node.render(context) == ' title="hooked"'
        finally:
            del manager.has_attrs_resolved_hook
            del manager.on_attrs_resolved

        adapter.install(changed=True)
        node, context, source = make({"title": "start"})
        for index in range(300):
            source.values = {"title": str(index)}
            node.render(context)
        assert len(adapter.CACHE) == 256

        class Observed(Component):
            def __getattribute__(self, name: str) -> Any:
                if name == "citry":
                    self.reads += 1
                return super().__getattribute__(name)

        reads = []
        for changed in (False, True):
            adapter.install(changed)
            component = Observed._create_instance()
            component.reads = 0
            node, context, source = make({"title": "fresh"}, component)
            node.render(context)
            reads.append(component.reads)
        assert reads[0] != reads[1]
        report = {
            "changed_values_order_normalization_and_escaping": True,
            "input_callbacks_once_per_render": True,
            "post_warm_style_parser_and_class_collector_changes": True,
            "custom_html_values_remain_live": True,
            "invalid_class_repeats_error": True,
            "node_override_and_added_hook_remain_live": True,
            "cache_bound_after_300_keys": 256,
            "unqualified_component_citry_reads_on_miss": {"reference": reads[0], "candidate": reads[1]},
            "production_compatible": False,
        }
        (ROOT / "benchmarks/results/repeat-render/attrs-pipeline-contracts.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
        print(json.dumps(report, indent=2))
    finally:
        adapter.install(changed=False)


if __name__ == "__main__":
    main()
