"""Compare compact keys and run the output-cache contracts under the adapter."""

# ruff: noqa: S101 - executable experiment assertions

from __future__ import annotations

import hashlib
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.native_attrs_output_probe.adapter import NATIVE  # noqa: E402

from citry import Const, Markup  # noqa: E402


def model(values: Any) -> tuple[Any, ...] | None:
    """Express the existing admission rules with a flat result for comparison."""
    if type(values) is not dict or len(values) > 16:
        return None
    fields, chars = [], 0
    for key, value in values.items():
        if type(key) is not str:
            return None
        chars += len(key)
        kind = type(value)
        if kind is str:
            chars += len(value)
        elif kind is int:
            if value.bit_length() > 256:
                return None
        elif value is not None and kind is not bool:
            return None
        if chars > 2048:
            return None
        fields.extend((key, kind, value))
    return tuple(fields)


def main() -> None:
    """Verify value/type identity, exact bounds and adapted existing cache tests."""
    rng = random.Random(20261004)  # noqa: S311 - repeatable cases
    keys = ["title", "ID", "class", "style", "DÄTA", "", "\ud800", "🦊"]
    values = [None, False, True, 0, 1, -1, 1 << 255, -(1 << 255), 1 << 256, "", "\udfff", "🦊", "a" * 2048]
    admitted = 0
    for _ in range(2000):
        items = {rng.choice(keys): rng.choice(values) for _ in range(rng.randrange(19))}
        expected = model(items)
        actual = NATIVE.cache_key(items)
        assert actual == expected
        if actual is not None:
            admitted += 1
            assert all(first is second for first, second in zip(actual, expected, strict=True))

    class CustomString(str):
        __slots__ = ()

    class CustomInt(int):
        pass

    class CustomDict(dict):
        pass

    bounds = [
        {"k": "x" * 2047},
        {"k": "x" * 2048},
        {str(i): i for i in range(16)},
        {str(i): i for i in range(17)},
        {"n": (1 << 256) - 1},
        {"n": 1 << 256},
        {"n": -((1 << 256) - 1)},
        {"n": -(1 << 256)},
        {CustomString("key"): "value"},
        {"key": CustomString("value")},
        {"key": CustomInt(1)},
        {"key": Markup("value")},
        {"key": Const("value")},
        {"key": ["value"]},
        {"key": 1.0},
        CustomDict(key="value"),
        [("key", "value")],
    ]
    for items in bounds:
        assert NATIVE.cache_key(items) == model(items)
    assert NATIVE.cache_key({"key": True}) != NATIVE.cache_key({"key": 1})
    assert NATIVE.cache_key({"a": 1, "b": 2}) != NATIVE.cache_key({"b": 2, "a": 1})

    test_path = ROOT / "packages/py/citry/tests/test_attrs_output_cache.py"
    source = test_path.read_text()
    # One test inspects the private key; retain its same barrier trigger at the new offset.
    assert source.count("key[0][2].startswith") == 1
    source = source.replace("key[0][2].startswith", "key[2].startswith")
    # The fresh-interpreter backend test must install this adapter after patching the backend.
    assert source.count("from citry import nodes\n") == 1
    source = source.replace(
        "from citry import nodes\n",
        "from citry import nodes\nfrom benchmarks.native_attrs_output_probe.adapter import install\ninstall(True)\n",
    )
    source = "from benchmarks.native_attrs_output_probe.adapter import install\ninstall(True)\n" + source
    with tempfile.TemporaryDirectory(prefix="citry-native-output-tests-") as directory:
        test_copy = Path(directory) / "test_output_cache.py"
        test_copy.write_text(source)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_copy), "-q", "--override-ini", "addopts="],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
    report = {
        "seeded_keys_compared": 2000,
        "seeded_admitted_keys_with_reference_identity": admitted,
        "bounds_and_unsupported_cases": len(bounds),
        "type_and_order_distinct": True,
        "original_cache_test_source_sha256": hashlib.sha256(test_path.read_bytes()).hexdigest(),
        "adapted_cache_test_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "cache_test_scope": "Original cache tests with flat-key offset and adapter installed in parent/child.",
        "pytest_output": result.stdout + result.stderr,
    }
    (ROOT / "benchmarks/results/repeat-render/native-attrs-output-contracts.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
