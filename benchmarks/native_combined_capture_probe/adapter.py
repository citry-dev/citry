"""Combine existing native slot preparation with direct immutable-record export."""

from __future__ import annotations

from typing import Any

from benchmarks.native_record_export_probe.adapter import configure, install_export
from benchmarks.native_slot_region_probe.adapter import install_region

import citry.ownership as own

__all__ = ["configure", "install_combined"]


def install_combined(native: Any, stats: dict[str, int]) -> tuple[Any, Any, Any]:
    """Compose the two opt-in methods and retain existing-native/production modes."""
    slot_enable, base_enable, restore = install_region(native, stats)
    export_enable, _, _ = install_export(native, stats)
    slot_enable()
    capture = own.OwnershipGraph.capture_slot_call
    restore()
    export_enable()
    initialize = own.OwnershipGraph.__init__
    restore()

    def candidate() -> None:
        base_enable()
        own.OwnershipGraph.__init__ = initialize
        own.OwnershipGraph.capture_slot_call = capture

    return candidate, base_enable, restore
