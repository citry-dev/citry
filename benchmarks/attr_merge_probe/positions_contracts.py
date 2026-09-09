"""Check prepared attribute-name positions with live values and helpers."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

from positions_probe import ORIGINAL, ROOT, attrs_module, merge_attrs, merge_items


def different_text(text: str) -> str:
    """Build a separate equal string object for the identity observation."""
    return bytearray(text.encode()).decode()


def main() -> None:
    """Retain focused checks without claiming production compatibility."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rng = random.Random(20260918)  # noqa: S311 - reproducible synthetic input
    keys = ("class", "CLASS", "style", "STYLE", "id", "ID", "title", "disabled", "data-value")
    for _ in range(300):
        items = []
        for _ in range(rng.randrange(10)):
            key = rng.choice(keys)
            if key.lower() == "class":
                value = rng.choice((None, "a b", " b c ", ""))
            elif key.lower() == "style":
                value = rng.choice((None, "color: red;", "color: blue; width: 1px;", ""))
            else:
                value = rng.choice((True, False, None, "text", '"><'))
            items.append((key, value))
        expected = list(ORIGINAL(items).items())
        first = merge_attrs(items)
        if list(first.items()) != expected:
            raise RuntimeError("A primitive merged result changed")
        first["caller_edit"] = "private"
        second = merge_attrs(items)
        if list(second.items()) != expected or first is second:
            raise RuntimeError("A cached merge failed to isolate its output dictionary")

    # Mutable structured values must be read again, including after mutation.
    structured = {"active": True}
    fallback = [("class", structured), ("data-number", 3)]
    for enabled in (True, False):
        structured["active"] = enabled
        if list(merge_attrs(fallback).items()) != list(ORIGINAL(fallback).items()):
            raise RuntimeError("Structured fallback changed")

    merge_items.cache_clear()
    for index in range(400):
        merge_attrs([("data-value-" + str(index), "item")])
    if merge_items.cache_info().currsize != 256:
        raise RuntimeError("The merged-attribute cache exceeded its entry bound")
    before = merge_items.cache_info()
    oversized = [("x" * 2049, "value")]
    if merge_attrs(oversized) != ORIGINAL(oversized) or merge_items.cache_info() != before:
        raise RuntimeError("An oversized input entered the cache or changed its result")

    merge_items.cache_clear()
    old_key, old_value = different_text("data-long-key"), different_text("long-value")
    new_key, new_value = different_text(old_key), different_text(old_value)
    if old_key is new_key or old_value is new_value:
        raise RuntimeError("The identity observation requires distinct equal strings")
    merge_attrs([(old_key, old_value)])
    current = [(new_key, new_value)]
    reference, candidate = ORIGINAL(current), merge_attrs(current)
    identity = {
        "reference_current_key": next(iter(reference)) is new_key,
        "reference_current_value": reference[new_key] is new_value,
        "candidate_current_key": next(iter(candidate)) is new_key,
        "candidate_current_value": candidate[new_key] is new_value,
    }
    if identity != {
        "reference_current_key": True,
        "reference_current_value": True,
        "candidate_current_key": True,
        "candidate_current_value": True,
    }:
        raise RuntimeError("Prepared merge positions failed to preserve current string identity")

    merge_items.cache_clear()
    sample = [("class", "a b")]
    merge_attrs(sample)
    normalizer = attrs_module._normalize_class_contributions
    attrs_module._normalize_class_contributions = lambda _values: "changed"
    try:
        helper = {"reference": ORIGINAL(sample), "candidate": merge_attrs(sample)}
    finally:
        attrs_module._normalize_class_contributions = normalizer
        merge_items.cache_clear()
    if helper["reference"] != helper["candidate"]:
        raise RuntimeError("Prepared merge positions ignored a current normalizer")
    original_identity = attrs_module._html_attr_identity
    attrs_module._html_attr_identity = lambda _key: "same"
    try:
        input_items = [("data-first", "one"), ("data-second", "two")]
        identity_helper = {"reference": ORIGINAL(input_items), "candidate": merge_attrs(input_items)}
    finally:
        attrs_module._html_attr_identity = original_identity
    if identity_helper["reference"] != identity_helper["candidate"]:
        raise RuntimeError("Prepared merge positions ignored an identity-helper replacement")
    report = {
        "production_qualified": False,
        "randomized_order_and_output_isolation_cases": 300,
        "structured_mutation_cases": 2,
        "cache_bound": 256,
        "oversized_fallback": True,
        "current_string_identity": identity,
        "changed_normalizer": helper,
        "changed_identity_helper": identity_helper,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__).resolve(), Path(__file__).with_name("positions_probe.py"))
        },
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
