"""Experimental scope classes executed with the ownership module's live globals."""

from __future__ import annotations

# ruff: noqa: TC004 - runtime names come from the live ownership exec globals
from functools import wraps
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from citry.ownership import (
        _ACTIVE_REGION,
        _SELECTED_SUPPLY,
        _SLOT_SITE,
        SourceLocationKind,
        _SelectedSupply,
        _SlotSite,
    )


class _ProbeScope:
    __slots__ = ()

    def __call__(self, function: Any) -> Any:
        """Decorators get a fresh scope for each call, as contextlib provides."""

        @wraps(function)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            with self._recreate_cm():
                return function(*args, **kwargs)

        return decorated


class _ProbeRegionScope(_ProbeScope):
    __slots__ = ("graph", "region_id", "token")

    def __init__(self, graph: Any, region_id: Any) -> None:
        self.graph = graph
        self.region_id = region_id

    def _recreate_cm(self) -> Any:
        return type(self)(self.graph, self.region_id)

    def __enter__(self) -> None:
        graph, region_id = self.graph, self.region_id
        del self.graph, self.region_id
        self.token = _ACTIVE_REGION.set((graph, region_id))

    def __exit__(self, _typ: object, _value: object, _traceback: object) -> bool:
        token = self.token
        del self.token
        _ACTIVE_REGION.reset(token)
        return False


class _ProbeSupplyScope(_ProbeScope):
    __slots__ = ("fill_id", "graph", "slot", "token")

    def __init__(self, graph: Any, slot: Any, fill_id: Any) -> None:
        self.graph, self.slot, self.fill_id = graph, slot, fill_id

    def _recreate_cm(self) -> Any:
        return type(self)(self.graph, self.slot, self.fill_id)

    def __enter__(self) -> None:
        graph, slot, fill_id = self.graph, self.slot, self.fill_id
        del self.graph, self.slot, self.fill_id
        self.token = _SELECTED_SUPPLY.set(_SelectedSupply(graph=graph, slot=slot, logical_fill_id=fill_id))

    def __exit__(self, _typ: object, _value: object, _traceback: object) -> bool:
        token = self.token
        del self.token
        _SELECTED_SUPPLY.reset(token)
        return False


class _ProbeSiteScope(_ProbeScope):
    __slots__ = ("context", "graph", "position", "source", "token")

    def __init__(self, graph: Any, context: Any, source: Any, position: Any) -> None:
        self.graph, self.context, self.source, self.position = graph, context, source, position

    def _recreate_cm(self) -> Any:
        return type(self)(self.graph, self.context, self.source, self.position)

    def __enter__(self) -> Any:
        graph, context, source, position = self.graph, self.context, self.source, self.position
        del self.graph, self.context, self.source, self.position
        component = context.component
        if component is None:
            raise RuntimeError("A slot outlet requires a component-owned render context.")
        location_id = graph.record_source_location(
            context,
            kind=SourceLocationKind.SLOT_OUTLET,
            source=source,
            position=position,
        )
        self.token = _SLOT_SITE.set(
            _SlotSite(graph=graph, receiver_render_id=component.id, source_location_id=location_id)
        )
        return location_id

    def __exit__(self, _typ: object, _value: object, _traceback: object) -> bool:
        token = self.token
        del self.token
        _SLOT_SITE.reset(token)
        return False


class _ProbeInvocationScope(_ProbeScope):
    __slots__ = ("delegate", "exit_method", "graph", "invocation_id")

    def __init__(self, graph: Any, invocation_id: Any) -> None:
        self.graph, self.invocation_id = graph, invocation_id

    def _recreate_cm(self) -> Any:
        return type(self)(self.graph, self.invocation_id)

    def __enter__(self) -> None:
        graph, invocation_id = self.graph, self.invocation_id
        del self.graph, self.invocation_id
        parent_region_id = (
            None
            if invocation_id is None
            else graph._component_invocations[graph._invocation_index[invocation_id]].physical_parent_region_id
        )
        self.delegate = None
        if parent_region_id is not None:
            delegate = graph.active_region(parent_region_id)
            # Match with-block lookup order and ignore the inner entry value.
            enter = type(delegate).__enter__
            self.exit_method = type(delegate).__exit__
            self.delegate = delegate
            try:
                enter(delegate)
            except BaseException:
                del self.delegate, self.exit_method
                raise

    def __exit__(self, typ: object, value: object, traceback: object) -> bool:
        delegate = self.delegate
        del self.delegate
        if delegate is None:
            return False
        exit_method = self.exit_method
        del self.exit_method
        result = exit_method(delegate, typ, value, traceback)
        return bool(result) if typ is not None else False


def _probe_active_region(self: Any, region_id: Any) -> Any:
    return _ProbeRegionScope(self, region_id)


def _probe_select_supply(self: Any, slot: Any, fill_id: Any) -> Any:
    return _ProbeSupplyScope(self, slot, fill_id)


def _probe_slot_site(self: Any, context: Any, *, source: Any, position: Any) -> Any:
    return _ProbeSiteScope(self, context, source, position)


def _probe_active_invocation_region(self: Any, invocation_id: Any) -> Any:
    return _ProbeInvocationScope(self, invocation_id)
