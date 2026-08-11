"""Shared conversion of editor file URIs into local filesystem paths."""

from __future__ import annotations

import sys
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
from urllib.parse import unquote, urlsplit


def file_uri_path(uri: str) -> Path | None:
    """Convert one local or UNC file URI using the host path flavor."""
    pure = _file_uri_pure_path(uri, windows=sys.platform == "win32")
    return Path(str(pure)) if pure is not None else None


def canonical_document_uri(uri: str) -> str:
    """Canonicalize a local editor URI while preserving non-file identities."""
    path = file_uri_path(uri)
    if path is None:
        return uri
    try:
        return path.resolve().as_uri()
    except (OSError, ValueError):
        return uri


def _file_uri_pure_path(uri: str, *, windows: bool) -> PurePath | None:
    """Parse a file URI independently of the host running the test."""
    parsed = urlsplit(uri)
    if parsed.scheme != "file":
        return None
    path = unquote(parsed.path)
    authority = unquote(parsed.netloc)
    if authority.lower() == "localhost":
        authority = ""
    if windows:
        if authority:
            if len(authority) == 2 and authority[1] == ":":
                path = f"{authority}{path}"
            else:
                path = f"//{authority}{path}"
        elif len(path) >= 3 and path[0] == "/" and path[1].isalpha() and path[2] == ":":
            # RFC file URIs spell a Windows drive as /C:/..., while pathlib
            # interprets that leading slash as a root-relative path.
            path = path[1:]
        return PureWindowsPath(path)
    if authority:
        path = f"//{authority}{path}"
    return PurePosixPath(path)


__all__ = ["canonical_document_uri", "file_uri_path"]
