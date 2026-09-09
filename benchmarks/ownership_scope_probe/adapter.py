"""Install small ownership scope objects while retaining live ownership globals."""

from __future__ import annotations

from pathlib import Path

from citry import ownership

SOURCE = Path(__file__).with_name("scopes.py")
NAMES = ("active_region", "active_invocation_region", "select_supply", "slot_site")
ORIGINALS = {name: getattr(ownership.OwnershipGraph, name) for name in NAMES}
exec(compile(SOURCE.read_text(), str(SOURCE), "exec"), ownership.__dict__)  # noqa: S102 - experiment classes
CANDIDATES = {name: getattr(ownership, f"_probe_{name}") for name in NAMES}


def install(changed: bool) -> None:
    """Switch all four scope factories while leaving graph capture methods intact."""
    for name, method in (CANDIDATES if changed else ORIGINALS).items():
        setattr(ownership.OwnershipGraph, name, method)
