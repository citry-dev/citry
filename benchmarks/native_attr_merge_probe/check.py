"""Compare merge values, current object identity, fallback and callback order."""

# ruff: noqa: S101 - executable experiment assertions

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.native_attr_merge_probe.adapter import NATIVE, ORIGINAL, merge  # noqa: E402

from citry import attrs  # noqa: E402


def outcome(function: Any, items: Any) -> Any:
    """Retain exception type and message as well as ordered successful values."""
    try:
        return list(function(items).items())
    except Exception as error:  # noqa: BLE001 - compare intentional unsupported values
        return type(error).__name__, str(error)


def main() -> None:
    """Exercise seeded values and callback behavior without timing instrumentation."""
    rng = random.Random(20261003)  # noqa: S311 - deterministic comparison
    keys = ["ID", "id", "CLASS", "class", "style", "STYLE", "@c-Thing", "@c-thing", "DÄTA", "däta"]
    values = [None, False, True, 0, 7, "", "a b a", "color: red; width: 0", ["a", {"a": False, "b": True}]]
    for _ in range(2000):
        items = [(rng.choice(keys), rng.choice(values)) for _ in range(rng.randrange(17))]
        assert outcome(ORIGINAL, items) == outcome(merge, items), items

    # Equal strings allocated in this call must keep the first key and last value.
    first = bytearray(b"data-current-key").decode()
    second = bytearray(b"data-current-key").decode()
    old, new = object(), object()
    items = [(first, old), (second, new)]
    actual = merge(items)
    assert next(iter(actual)) is first
    assert actual[first] is new

    class CustomKey(str):
        __slots__ = ()

    unsupported = [[(CustomKey("id"), 1)], [["id", 1]], [("id",)], [("id", 1, 2)], [("\ud800", 1)]]
    for items in unsupported:
        assert NATIVE.merge(items, attrs) is None
        assert outcome(ORIGINAL, items) == outcome(merge, items)
    for items in ((("id", 1),), iter([("id", 1)])):
        assert NATIVE.merge(items, attrs) is None
        assert merge(items) == {"id": 1}

    original_class, original_style = attrs._normalize_class_contributions, attrs.normalize_style
    callbacks = []
    try:
        for function in (ORIGINAL, merge):
            calls = []

            def style(values: Any, _calls: list[Any] = calls) -> str:
                _calls.append(("style", values))
                return "live style"

            def classes(values: Any, _calls: list[Any] = calls) -> str:
                _calls.append(("class", values))
                attrs.normalize_style = style
                return "live class"

            attrs._normalize_class_contributions = classes
            attrs.normalize_style = original_style
            result = function([("style", "old"), ("class", "a")])
            callbacks.append((calls, list(result.items())))
        assert callbacks[0] == callbacks[1]
    finally:
        attrs._normalize_class_contributions = original_class
        attrs.normalize_style = original_style

    original_identity = attrs._html_attr_identity
    try:

        class EqualHelper:  # noqa: PLW1641 - deliberately unhashable replacement callable
            def __eq__(self, other: object) -> bool:
                return True

            def __call__(self, name: str) -> str:
                return name

        attrs._html_attr_identity = EqualHelper()
        items = [("ID", 1), ("id", 2)]
        assert list(merge(items).items()) == items
    finally:
        attrs._html_attr_identity = original_identity

    report = {
        "seeded_ordered_outcome_comparisons": 2000,
        "current_key_and_value_identity": True,
        "unsupported_shapes_and_surrogates": len(unsupported) + 2,
        "class_callback_replaces_style_helper": True,
        "changed_identity_helper_uses_python": True,
        "callable_equality_cannot_bypass_guard": True,
        "note": "Experimental scope only; plan.md lists unqualified runtime mutation and lifetime cases.",
    }
    (ROOT / "benchmarks/results/performance-render/native-attr-merge-contracts.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report))


if __name__ == "__main__":
    main()
