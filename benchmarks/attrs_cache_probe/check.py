"""Check the attribute cache's admitted values, fallbacks and retention bounds."""

from __future__ import annotations

import json
import random
from typing import Any

from probe import attrs, candidate_node_formatter, nodes


def outcome(function: Any, node: Any, values: Any, *, validate: bool) -> Any:
    """Compare output type/text or the original diagnostic type/text."""
    try:
        result = function(node, values, None, validate_keys=validate)
    except Exception as error:  # noqa: BLE001 - exception parity is the subject
        return "error", type(error), str(error)
    return "result", type(result), result


def main() -> None:
    """Exercise both warm hits and repeated unsupported inputs outside timing."""
    original = nodes.ElementAttrsNode._format
    changed, cache = candidate_node_formatter(original)
    node = nodes.ElementAttrsNode("<div>", (0, 5), (), ())
    node._tag_name = "div"
    randomizer = random.Random(20260908)  # noqa: S311 - reproducible differential inputs
    names = ("title", "TITLE", "class", "CLASS", "style", "disabled", "aria-label", "data-value", "bad name")
    values = (None, False, True, 0, 1, -1, "", " <>&\"' ", "café", "same", "width: 10px", 1 << 255, 1 << 256)
    for _ in range(3000):
        mapping = {name: randomizer.choice(values) for name in randomizer.sample(names, randomizer.randrange(6))}
        validate = bool(randomizer.getrandbits(1))
        expected = outcome(original, node, mapping, validate=validate)
        if outcome(changed, node, mapping, validate=validate) != expected:
            raise AssertionError("Changed a randomized formatting outcome")
        if outcome(changed, node, mapping, validate=validate) != expected:
            raise AssertionError("Changed a retained formatting outcome")

    class DynamicHtml:
        def __init__(self) -> None:
            self.calls = 0

        def __html__(self) -> str:
            self.calls += 1
            return str(self.calls)

    custom = DynamicHtml()
    if changed(node, {"title": custom}, None) != ' title="1"':
        raise AssertionError("Changed first protocol invocation")
    if changed(node, {"title": custom}, None) != ' title="2"' or custom.calls != 2:
        raise AssertionError("Suppressed a repeated protocol invocation")

    class CustomNode(nodes.ElementAttrsNode):
        @property
        def tag_name(self) -> str:
            self.tag_reads += 1
            return "custom"

    custom_node = CustomNode("<custom>", (0, 8), (), ())
    custom_node.tag_reads = 0
    for _ in range(2):
        changed(custom_node, {"title": "same"}, None)
    if custom_node.tag_reads != 2:
        raise AssertionError("Suppressed a custom tag getter")

    changed(node, {"title": "warm"}, None)
    formatter = attrs._format_resolved_attrs_to_str
    calls = 0

    def replacement(_mapping: Any) -> str:
        nonlocal calls
        calls += 1
        return f"changed-{calls}"

    attrs._format_resolved_attrs_to_str = replacement
    try:
        first = changed(node, {"title": "warm"}, None)
        second = changed(node, {"title": "warm"}, None)
    finally:
        attrs._format_resolved_attrs_to_str = formatter
    if first != " changed-1" or second != " changed-2" or calls != 2:
        raise AssertionError("Suppressed a rebound formatter alias")

    guarded, bounds = candidate_node_formatter(original)
    for mapping in ({"title": "x" * 2049}, {f"k{i}": i for i in range(17)}, {"title": 1 << 256}):
        for _ in range(2):
            if outcome(guarded, node, mapping, validate=True) != outcome(original, node, mapping, validate=True):
                raise AssertionError("Changed an oversized fallback")
    if bounds.cache_info().currsize:
        raise AssertionError("Retained an oversized input")
    for i in range(1000):
        guarded(node, {"title": str(i)}, None)
    if bounds.cache_info().currsize != 256:
        raise AssertionError("FIFO entry bound changed")
    if cache.cache_info().hits == 0:
        raise AssertionError("Differential checks never reached a warm cache hit")
    print(
        json.dumps(
            {
                "randomized_cases_twice": 3000,
                "protocol_calls_preserved": custom.calls,
                "custom_tag_reads_preserved": custom_node.tag_reads,
                "rebound_alias_calls_preserved": calls,
                "oversized_fallbacks": 3,
                "churned_entries": 1000,
                "retained_entries": bounds.cache_info().currsize,
                "preinstalled_helpers_qualified": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
