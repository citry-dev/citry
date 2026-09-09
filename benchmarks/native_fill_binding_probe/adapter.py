"""Group native fill checks and updates while retaining Python fallback paths."""

from __future__ import annotations

import inspect
from typing import Any

from benchmarks.ownership_journal_probe.storage_probe import install_storage

import citry.ownership as own


def install_binding(native: Any, stats: dict[str, int]) -> tuple[Any, Any, Any]:
    """Return candidate, existing-native and production installation functions."""
    graph = own.OwnershipGraph
    base_enable, base_disable = install_storage(native, stats)
    original_source = graph.bind_template_fill_sources
    original_supplied = graph.bind_supplied_slots

    def source(self: Any, slots: Any, invocation_id: Any) -> None:
        if not isinstance(self._logical_fills, native.RecordTable):
            return original_source(self, slots, invocation_id)
        invocation = self._component_invocations[self._invocation_index[invocation_id]]
        for slot in slots.values():
            fill_id = self._template_fill_by_slot_object.get(slot)
            if fill_id is None:
                continue
            fill_index = self._fill_index[fill_id]
            if isinstance(self._logical_fills, native.RecordTable):
                self._logical_fills.bind_fill_source(
                    fill_index,
                    invocation.source_render_id,
                    invocation_id,
                    own.SourcePolicy.TEMPLATE,
                    own.LogicalFillKind.FALLBACK,
                )
            else:
                # Iterating slots can replay and materialize the graph tables.
                fill = self._logical_fills[fill_index]
                if fill.source_policy != own.SourcePolicy.TEMPLATE or fill.kind == own.LogicalFillKind.FALLBACK:
                    continue
                if fill.lexical_owner_render_id != invocation.source_render_id:
                    msg = "A template fill source invocation must belong to the fill's lexical owner."
                    raise RuntimeError(msg)
                if fill.source_invocation_id is not None and fill.source_invocation_id != invocation_id:
                    msg = "A template fill cannot be rebound to a second source invocation."
                    raise RuntimeError(msg)
                self._logical_fills[fill_index] = fill._with_source_invocation(invocation_id)
        return None

    # Insert the active-attachment branch before the existing revival/forwarding
    # code. Keep the remainder from the current runtime, including error order.
    source_text = inspect.getsource(original_supplied)
    marker = "            if fill_id is not None:\n"
    if source_text.count(marker) != 1:
        raise RuntimeError("Supplied-fill control flow changed")
    branch = """            if (
                fill_id is not None
                and isinstance(self._logical_fills, _BindingTable)
                and self._logical_fills.attach_active_fill(
                    self._fill_index[fill_id], component.id,
                    component_class_id, OwnershipState.ACTIVE,
                )
            ):
                self._receiver_fill[key] = fill_id
                continue
"""
    import textwrap  # noqa: PLC0415

    namespace = {**own.__dict__, "_BindingTable": native.RecordTable}
    exec(  # noqa: S102
        "from __future__ import annotations\n" + textwrap.dedent(source_text.replace(marker, branch + marker)),
        namespace,
    )
    supplied = namespace[original_supplied.__name__]

    def candidate() -> None:
        base_enable()
        graph.bind_template_fill_sources = source
        graph.bind_supplied_slots = supplied

    return candidate, base_enable, base_disable
