"""Complete manifest construction and validation for the client graph."""

from __future__ import annotations

import hashlib
import json
import re
from typing import TYPE_CHECKING, Any

from .canonical import COMMENT_PREFIX, PROTOCOL, canonical_json, revision_for
from .issues import ProtocolValueError, ValidationIssue, copy_json, first_unknown, pointer, validate_strict_json
from .records import assemble_graph, build_graph, validate_graph
from .relationships import validate_relationships

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

_REVISION = re.compile(r"^[0-9a-f]{64}$")
_MANIFEST_FIELDS = ("protocol", "revision", "mode", "graphs", "delimiters")
_DELIMITER_FIELDS = ("format",)


class _AssembledManifest(dict[str, Any]):
    """Signed manifest carrying its already-produced canonical wire bytes."""

    serialized_json: str
    mutation_guard: str


def validate_revision(value: Any, path: str = "") -> ValidationIssue | None:
    """Return a correlation issue when a shaped revision does not match its manifest."""
    if not isinstance(value, dict):
        return None
    revision = value.get("revision")
    if not isinstance(revision, str) or _REVISION.fullmatch(revision) is None:
        return None
    unsigned = {key: item for key, item in value.items() if key != "revision"}
    try:
        expected = revision_for(unsigned)
    except (UnicodeEncodeError, ValueError):
        return None
    if revision == expected:
        return None
    return ValidationIssue(
        pointer(path, "revision"),
        "correlation",
        "The revision does not match the canonical unsigned manifest.",
    )


def _validate_manifest_shape(value: Any, path: str, *, strict: bool = True) -> ValidationIssue | None:
    """Return the first fixed-field issue without recalculating the revision."""
    if strict:
        issue = validate_strict_json(value, path)
        if issue is not None:
            return issue
    if not isinstance(value, dict):
        return ValidationIssue(path, "type", "The client-graph manifest must be an object.")
    for required in _MANIFEST_FIELDS:
        if required not in value:
            return ValidationIssue(pointer(path, required), "required", f"The manifest requires {required!r}.")
    found, unknown = first_unknown(value, set(_MANIFEST_FIELDS))
    if found:
        return ValidationIssue(pointer(path, unknown), "unknown_field", "The manifest has an unknown field.")
    if value["protocol"] != PROTOCOL:
        category = "enum" if isinstance(value["protocol"], str) else "type"
        return ValidationIssue(pointer(path, "protocol"), category, f"The manifest protocol must be {PROTOCOL}.")
    revision = value["revision"]
    if not isinstance(revision, str):
        return ValidationIssue(pointer(path, "revision"), "type", "The manifest revision must be a string.")
    if _REVISION.fullmatch(revision) is None:
        return ValidationIssue(
            pointer(path, "revision"), "pattern", "The manifest revision must be lowercase SHA-256."
        )
    mode = value["mode"]
    if not isinstance(mode, str):
        return ValidationIssue(pointer(path, "mode"), "type", "The manifest mode must be a string.")
    if mode not in {"production", "development"}:
        return ValidationIssue(pointer(path, "mode"), "enum", "The manifest mode must be production or development.")
    graphs = value["graphs"]
    if not isinstance(graphs, list):
        return ValidationIssue(pointer(path, "graphs"), "type", "The manifest graphs must be an array.")
    for index, graph in enumerate(graphs):
        issue = validate_graph(graph, pointer(pointer(path, "graphs"), index), strict=False)
        if issue is not None:
            return issue
    delimiters = value["delimiters"]
    delimiter_path = pointer(path, "delimiters")
    if not isinstance(delimiters, dict):
        return ValidationIssue(delimiter_path, "type", "The manifest delimiters must be an object.")
    if "format" not in delimiters:
        return ValidationIssue(
            pointer(delimiter_path, "format"), "required", "The manifest delimiters require 'format'."
        )
    found, unknown = first_unknown(delimiters, set(_DELIMITER_FIELDS))
    if found:
        return ValidationIssue(
            pointer(delimiter_path, unknown), "unknown_field", "The manifest delimiters have an unknown field."
        )
    if delimiters["format"] != COMMENT_PREFIX:
        category = "enum" if isinstance(delimiters["format"], str) else "type"
        return ValidationIssue(
            pointer(delimiter_path, "format"),
            category,
            f"The ownership-comment prefix must be {COMMENT_PREFIX}.",
        )
    return None


def validate_manifest(value: Any, path: str = "") -> ValidationIssue | None:
    """Return the first structural or relationship issue in a graph manifest."""
    issue = _validate_manifest_shape(value, path)
    if issue is not None:
        return issue
    issue = validate_revision(value, path)
    if issue is not None:
        return issue
    return validate_relationships(value, path)


def build_manifest(mode: str, graphs: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Build, sign, and completely validate one client-graph manifest."""
    return copy_json(assemble_manifest(mode, list(graphs), audit=True))


def assemble_manifest(
    mode: str,
    graphs: Sequence[dict[str, Any]],
    *,
    audit: bool,
    _canonicalize: Callable[[dict[str, Any]], tuple[str, str]] | None = None,
) -> dict[str, Any]:
    """Sign package-built graphs and optionally run their complete self-audit."""
    unsigned: dict[str, Any] = {
        "protocol": PROTOCOL,
        "mode": mode,
        "graphs": list(graphs),
        "delimiters": {"format": COMMENT_PREFIX},
    }
    manifest = _AssembledManifest({**unsigned, "revision": "0" * 64})
    if audit:
        issue = _validate_manifest_shape(manifest, "")
        if issue is None:
            issue = validate_relationships(manifest)
        if issue is not None:
            raise ProtocolValueError(issue)
    if _canonicalize is None:
        unsigned_json = canonical_json(unsigned)
        revision = hashlib.sha256(unsigned_json.encode("utf8")).hexdigest()
    else:
        unsigned_json, revision = _canonicalize(unsigned)
        if (
            not isinstance(unsigned_json, str)
            or not isinstance(revision, str)
            or _REVISION.fullmatch(revision) is None
        ):
            msg = "The client-graph canonicalizer returned an invalid result."
            raise TypeError(msg)
    manifest["revision"] = revision
    manifest.serialized_json = f'{unsigned_json[:-1]},"revision":{canonical_json(revision)}}}'.replace("<", "\\u003c")
    # The product artifact exposes ``manifest`` for protocol tooling, so it
    # remains mutable. A C-backed JSON guard lets the normal unchanged path
    # reuse the canonical bytes above; changed/invalid data falls back to the
    # full validator in ``serialize_manifest`` for its precise diagnostic.
    manifest.mutation_guard = json.dumps(
        manifest,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return manifest


def serialize_manifest(value: Any, *, audit: bool) -> str:
    """Validate a final manifest and serialize its canonical bytes."""
    issue = _validate_manifest_shape(value, "", strict=False)
    if issue is not None:
        strict_issue = validate_strict_json(value)
        if strict_issue is not None:
            raise ProtocolValueError(strict_issue)
        raise ProtocolValueError(issue)
    revision = value["revision"]
    unsigned = {key: item for key, item in value.items() if key != "revision"}
    try:
        unsigned_json = canonical_json(unsigned)
    except (UnicodeEncodeError, ValueError) as error:
        raise ProtocolValueError(ValidationIssue("", "strict_json", str(error))) from error
    expected = hashlib.sha256(unsigned_json.encode("utf8")).hexdigest()
    if revision != expected:
        raise ProtocolValueError(
            ValidationIssue(
                "/revision",
                "correlation",
                "The revision does not match the canonical unsigned manifest.",
            )
        )
    if audit:
        issue = validate_relationships(value)
        if issue is not None:
            raise ProtocolValueError(issue)
    # The closed top-level record sorts revision after protocol, so insert the
    # checked value before the final brace without walking every graph again.
    encoded = f'{unsigned_json[:-1]},"revision":{canonical_json(revision)}}}'
    return encoded.replace("<", "\\u003c")


def assert_valid_manifest(value: Any) -> dict[str, Any]:
    """Return a valid manifest or raise its first protocol issue."""
    issue = validate_manifest(value)
    if issue is not None:
        raise ProtocolValueError(issue)
    return value


__all__ = [
    "assemble_graph",
    "assemble_manifest",
    "assert_valid_manifest",
    "build_graph",
    "build_manifest",
    "serialize_manifest",
    "validate_graph",
    "validate_manifest",
    "validate_revision",
]
