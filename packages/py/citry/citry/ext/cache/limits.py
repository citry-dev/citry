"""Non-configurable safety limits for render-cache keys and artifacts."""

from __future__ import annotations

_MAX_KEY_DEPTH = 32
_MAX_KEY_NODES = 10_000
_MAX_KEY_BYTES = 64 * 1024

_MAX_ARTIFACT_BYTES = 16 * 1024 * 1024
_MAX_ARTIFACT_DEPTH = 128
_MAX_ARTIFACT_RECORDS = 100_000


class _InvalidArtifactTextError(ValueError):
    """An artifact string cannot be represented by the UTF-8 wire format."""


def _validate_artifact_text_size(value: str) -> int:
    """Return the UTF-8 size of an artifact after enforcing its read cap."""
    if type(value) is not str:
        msg = f"Cached render artifacts must be exact strings; got {type(value).__name__}."
        raise ValueError(msg)
    # Every Unicode code point occupies at least one UTF-8 byte, so this check
    # rejects obviously oversized inputs before allocating an encoded copy.
    if len(value) > _MAX_ARTIFACT_BYTES:
        msg = "Cached render artifact exceeds the absolute 16 MiB format limit."
        raise ValueError(msg)
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        msg = "Cached render artifact must be valid UTF-8 text; Unicode surrogates are unsupported."
        raise _InvalidArtifactTextError(msg) from error
    size = len(encoded)
    if size > _MAX_ARTIFACT_BYTES:
        msg = "Cached render artifact exceeds the absolute 16 MiB format limit."
        raise ValueError(msg)
    return size
