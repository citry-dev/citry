"""Canonical JSON, revisions, and ownership comments for the client graph."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any

from .issues import ProtocolValueError, ValidationIssue, pointer, utf16_key

PROTOCOL = "citry-client-graph/1"
COMMENT_PREFIX = "citry:g1"
REVISION_ALIAS_LENGTH = 8
MAX_SAFE_INTEGER = 9_007_199_254_740_991

_REVISION_RE = re.compile(r"^[0-9a-f]{64}$")
_REVISION_ALIAS_RE = re.compile(rf"^[0-9a-f]{{{REVISION_ALIAS_LENGTH}}}$")
_COMMENT_RE = re.compile(rf"^citry:g1:([0-9a-f]{{{REVISION_ALIAS_LENGTH}}}):([0-9]+):([ir]):([0-9]+):([se])$")


def _quote(value: str) -> str:
    """Quote a Python string exactly like JavaScript ``JSON.stringify``."""
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
        character = value[index]
        codepoint = ord(character)
        if character in escapes:
            parts.append(escapes[character])
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
            parts.append(character)
        index += 1
    parts.append('"')
    return "".join(parts)


def canonical_json(value: Any) -> str:
    """Return the exact browser-compatible canonical JSON for one graph value."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        if isinstance(value, float) and (not math.isfinite(value) or not value.is_integer()):
            msg = "number is not a decoded integer"
            raise ValueError(msg)
        if not 0 <= value <= MAX_SAFE_INTEGER:
            msg = "integer is outside the client-graph range"
            raise ValueError(msg)
        return str(int(value))
    if isinstance(value, str):
        return _quote(value)
    if isinstance(value, list):
        return "[" + ",".join(canonical_json(item) for item in value) + "]"
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            msg = "client-graph object keys must be strings"
            raise ValueError(msg)
        keys = sorted(value, key=utf16_key)
        return "{" + ",".join(f"{_quote(key)}:{canonical_json(value[key])}" for key in keys) + "}"
    msg = f"unsupported client-graph JSON value {type(value).__name__}"
    raise ValueError(msg)


def revision_for(unsigned_manifest: dict[str, Any]) -> str:
    """Return the lowercase SHA-256 revision for an unsigned manifest."""
    return hashlib.sha256(canonical_json(unsigned_manifest).encode("utf8")).hexdigest()


def inert_script_json(value: Any) -> str:
    """Serialize canonical graph JSON without permitting script-tag breakout."""
    return canonical_json(value).replace("<", "\\u003c")


def revision_alias(revision: str) -> str:
    """Return the short comment alias for one complete graph revision."""
    if not isinstance(revision, str) or _REVISION_RE.fullmatch(revision) is None:
        issue = ValidationIssue("/revision", "pattern", "The client-graph revision is invalid.")
        raise ProtocolValueError(issue)
    return revision[:REVISION_ALIAS_LENGTH]


def format_ownership_comment(
    revision: str,
    graph_id: int,
    kind: str,
    record_id: int,
    side: str,
) -> str:
    """Build one complete HTML comment that brackets a physical graph range."""
    alias = revision_alias(revision)
    values = (
        (graph_id, "graphId", type(graph_id) is int and 0 <= graph_id <= MAX_SAFE_INTEGER),
        (kind, "kind", isinstance(kind, str) and kind in {"i", "r"}),
        (record_id, "recordId", type(record_id) is int and 1 <= record_id <= MAX_SAFE_INTEGER),
        (side, "side", isinstance(side, str) and side in {"s", "e"}),
    )
    for _value, name, valid in values:
        if not valid:
            issue = ValidationIssue(pointer("", name), "pattern", f"The ownership-comment {name} is invalid.")
            raise ProtocolValueError(issue)
    return f"<!--{COMMENT_PREFIX}:{alias}:{graph_id}:{kind}:{record_id}:{side}-->"


def parse_ownership_comment(value: str) -> dict[str, str] | None:
    """Parse one ownership comment body without changing decimal identifiers."""
    match = _COMMENT_RE.fullmatch(value.strip())
    if match is None:
        return None
    revision_alias_value, graph_id, kind, record_id, side = match.groups()
    if _REVISION_ALIAS_RE.fullmatch(revision_alias_value) is None:
        return None
    return {
        "revisionAlias": revision_alias_value,
        "graphId": graph_id,
        "kind": kind,
        "recordId": record_id,
        "side": side,
        "key": f"{COMMENT_PREFIX}:{revision_alias_value}:{graph_id}:{kind}:{record_id}",
    }


__all__ = [
    "COMMENT_PREFIX",
    "MAX_SAFE_INTEGER",
    "PROTOCOL",
    "REVISION_ALIAS_LENGTH",
    "canonical_json",
    "format_ownership_comment",
    "inert_script_json",
    "parse_ownership_comment",
    "revision_alias",
    "revision_for",
]
