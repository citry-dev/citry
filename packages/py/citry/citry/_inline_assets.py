"""Shared normalization for inline component asset declarations."""

from __future__ import annotations

from textwrap import dedent


def normalize_inline_asset(source: str) -> str:
    """Remove indentation shared by the non-blank lines of an inline asset."""
    if type(source) is not str:
        msg = f"inline component assets must be strings, got {type(source).__name__}"
        raise TypeError(msg)
    return dedent(source)


__all__ = ["normalize_inline_asset"]
