"""Strict client-graph canonicalization at the Rust/Python boundary."""

from __future__ import annotations

import hashlib

import pytest

from citry_core import _rust


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ({"z": None, "a": [True, 1.0, "x\n"]}, '{"a":[true,1,"x\\n"],"z":null}'),
        ({"\ue000": 1, "\U00010000": 2}, '{"𐀀":2,"":1}'),
        ({"value": "\ud83d\ude00"}, '{"value":"😀"}'),
        ({"value": "\ud800"}, '{"value":"\\ud800"}'),
    ],
)
def test_canonical_json_and_revision(value: object, expected: str) -> None:
    canonical, revision = _rust.client_graph.canonical_json_and_revision(value)
    assert canonical == expected
    assert revision == hashlib.sha256(expected.encode()).hexdigest()


@pytest.mark.parametrize(
    "value",
    [
        {"value": 1.5},
        {"value": -1},
        {"value": 9_007_199_254_740_992},
        {1: "non-string key"},
        {"value": (1, 2)},
    ],
)
def test_canonical_json_rejects_values_outside_the_wire_contract(value: object) -> None:
    with pytest.raises(ValueError, match=r"integer|number|keys|unsupported"):
        _rust.client_graph.canonical_json_and_revision(value)
