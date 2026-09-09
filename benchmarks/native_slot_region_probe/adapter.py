"""Prepare an active slot region in one native operation before its callback."""

from __future__ import annotations

from typing import Any

from benchmarks.ownership_journal_probe.storage_probe import install_storage

import citry.ownership as own


def install_region(native: Any, stats: dict[str, int]) -> tuple[Any, Any, Any]:
    """Return candidate, existing-native and production installation functions."""
    graph = own.OwnershipGraph
    base_enable, base_disable = install_storage(native, stats)
    base_enable()
    base_capture = graph.capture_slot_call
    base_disable()

    def capture(self: Any, slot: Any, callback: Any) -> Any:
        selected = own._SELECTED_SUPPLY.get()
        fill_id = (
            selected.logical_fill_id
            if selected is not None and selected.graph is self and selected.slot is slot
            else self._template_fill_by_slot_object.get(slot)
        )
        if fill_id is None:
            return callback()
        if not isinstance(self._logical_fills, native.RecordTable) or not isinstance(
            self._physical_regions, native.RecordTable
        ):
            return base_capture(self, slot, callback)
        site = own._SLOT_SITE.get()
        active = own._ACTIVE_REGION.get()
        containing_region_id = active[1] if active is not None and active[0] is self else None
        region_id = self._region_id + 1
        order = self._order + 1
        region_index = self._physical_regions.begin_slot_region(
            self._logical_fills,
            self._fill_index[fill_id],
            self._region_index[containing_region_id] if containing_region_id is not None else None,
            (region_id, order, fill_id, containing_region_id),
            (site.receiver_render_id, site.source_location_id) if site is not None and site.graph is self else None,
            own.OwnershipState.ACTIVE,
            own.RegionState.CAPTURED,
        )
        if region_index is None:
            return base_capture(self, slot, callback)
        self._region_id = region_id
        self._order = order
        self._region_index[region_id] = region_index
        self._relation_indexes_current = False
        token = own._ACTIVE_REGION.set((self, region_id))
        try:
            result = callback()
        except Exception:
            if isinstance(self._physical_regions, native.RecordTable):
                self._physical_regions.patch(region_index, ((10, own.RegionState.FAILED),))
            else:
                self._physical_regions[region_index] = self._physical_regions[region_index]._with_state(
                    own.RegionState.FAILED
                )
            raise
        finally:
            own._ACTIVE_REGION.reset(token)
        result_context = getattr(result, "context", None)
        result_frame = getattr(result, "frame", None)
        result_render_id = getattr(result_frame, "render_id", None)
        result_owner = (
            result_render_id
            if result_render_id is not None and getattr(result_context, "ownership", None) is self
            else None
        )
        if isinstance(self._physical_regions, native.RecordTable):
            self._physical_regions.patch(region_index, ((9, result_owner),))
        else:
            self._physical_regions[region_index] = self._physical_regions[region_index]._with_result_owner(
                result_owner
            )
        from citry.citry_render import CitryRender, PhysicalRegionPart, PhysicalRegionRender  # noqa: PLC0415

        wrapped = (
            PhysicalRegionRender(self, region_id, result)
            if isinstance(result, CitryRender)
            else PhysicalRegionPart(self, region_id, result)
        )
        self._region_results[region_id] = wrapped
        return wrapped

    def candidate() -> None:
        base_enable()
        graph.capture_slot_call = capture

    return candidate, base_enable, base_disable
