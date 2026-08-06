"""Check client-graph revision vectors with only the Python standard library."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

MAX_SAFE_INTEGER = 9_007_199_254_740_991
VECTORS_PATH = Path(__file__).with_name("canonicalization.json")


def _quote(value: str) -> str:
    escapes = {
        '"': '\\"',
        "\\": "\\\\",
        "\b": "\\b",
        "\t": "\\t",
        "\n": "\\n",
        "\f": "\\f",
        "\r": "\\r",
    }
    parts = ['"']
    index = 0
    while index < len(value):
        char = value[index]
        codepoint = ord(char)
        if char in escapes:
            parts.append(escapes[char])
        elif 0xD800 <= codepoint <= 0xDBFF and index + 1 < len(value):
            low = ord(value[index + 1])
            if 0xDC00 <= low <= 0xDFFF:
                parts.append(chr(0x10000 + ((codepoint - 0xD800) << 10) + low - 0xDC00))
                index += 1
            else:
                parts.append(f"\\u{codepoint:04x}")
        elif codepoint <= 0x1F or 0xD800 <= codepoint <= 0xDFFF:
            parts.append(f"\\u{codepoint:04x}")
        else:
            parts.append(char)
        index += 1
    parts.append('"')
    return "".join(parts)


def canonical_json(value: Any) -> str:
    """Return the exact client-graph canonical JSON for one decoded value."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int | float):
        if isinstance(value, float) and (not math.isfinite(value) or not value.is_integer()):
            raise ValueError("number is not a decoded integer")
        if not 0 <= value <= MAX_SAFE_INTEGER:
            raise ValueError("integer is outside the client-graph range")
        return str(int(value))
    if isinstance(value, str):
        return _quote(value)
    if isinstance(value, list):
        return "[" + ",".join(canonical_json(item) for item in value) + "]"
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise ValueError("object keys must be strings")
        keys = sorted(value, key=lambda key: key.encode("utf-16-be", "surrogatepass"))
        return "{" + ",".join(f"{_quote(key)}:{canonical_json(value[key])}" for key in keys) + "}"
    raise ValueError("value is not JSON")


def _values(vector: dict[str, Any]) -> list[Any]:
    if "manifest" in vector:
        return [{key: value for key, value in vector["manifest"].items() if key != "revision"}]
    if "input" in vector:
        return [vector["input"]]
    if "equivalentInputJson" in vector:
        return [json.loads(text) for text in vector["equivalentInputJson"]]
    return [json.loads(vector["inputJson"])]


def main() -> int:
    document = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
    if document.get("format") != "citry-client-graph-canonicalization/1":
        raise AssertionError("unknown canonicalization vector format")
    vectors = document.get("vectors")
    if not isinstance(vectors, list):
        raise TypeError("canonicalization vectors must be an array")

    for vector in vectors:
        try:
            encoded = [canonical_json(value).encode() for value in _values(vector)]
        except ValueError:
            if vector.get("expect") != "reject":
                raise
            continue
        if vector.get("expect") == "reject":
            msg = f"{vector['name']} unexpectedly passed"
            raise AssertionError(msg)
        if any(value != encoded[0] for value in encoded[1:]):
            msg = f"{vector['name']} equivalent inputs differ"
            raise AssertionError(msg)
        canonical = encoded[0]
        if "canonicalJson" in vector and canonical.decode() != vector["canonicalJson"]:
            msg = f"{vector['name']} canonical JSON differs"
            raise AssertionError(msg)
        if "canonicalUtf8Hex" in vector and canonical.hex() != vector["canonicalUtf8Hex"]:
            msg = f"{vector['name']} canonical bytes differ"
            raise AssertionError(msg)
        if "sha256" in vector and hashlib.sha256(canonical).hexdigest() != vector["sha256"]:
            msg = f"{vector['name']} hash differs"
            raise AssertionError(msg)

    sys.stdout.write(f"client-graph canonicalization: ok ({len(vectors)} vectors)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
