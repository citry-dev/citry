"""Check ownership scope entry, restoration and explicit lifecycle limitations."""

# ruff: noqa: S101, PT017, PT018, BLE001 - executable protocol and exception-identity assertions

from __future__ import annotations

import gc
import json
import sys
from contextlib import contextmanager
from contextvars import copy_context
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from weakref import ref

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.ownership_scope_probe.adapter import install  # noqa: E402

from citry import ownership as o  # noqa: E402


def exercise(changed: bool) -> None:
    """Run the same observable scope operations for each implementation."""
    install(changed)
    graph, other = o.OwnershipGraph(), o.OwnershipGraph()
    cm = graph.active_region(1)
    assert o._ACTIVE_REGION.get() is None
    with cm as entered:
        assert entered is None
        assert graph.current_region_id() == 1
        with other.active_region(2):
            assert other.current_region_id() == 2
            assert graph.current_region_id() is None
        assert graph.current_region_id() == 1
    assert o._ACTIVE_REGION.get() is None

    for error in (ValueError("body"), StopIteration("body"), BaseException("body")):
        try:
            with graph.active_region(3):
                raise error
        except BaseException as caught:
            assert caught is error
        else:
            raise AssertionError("The scope suppressed an unhandled exception")
        assert o._ACTIVE_REGION.get() is None

    @graph.active_region(4)
    def decorated() -> int:
        return graph.current_region_id()

    assert decorated() == decorated() == 4
    assert o._ACTIVE_REGION.get() is None

    slot = object()
    with graph.select_supply(slot, 5) as entered:
        assert entered is None
        supply = o._SELECTED_SUPPLY.get()
        assert supply.graph is graph and supply.slot is slot and supply.logical_fill_id == 5
        captured = copy_context()
        with other.select_supply(object(), 6):
            assert o._SELECTED_SUPPLY.get().graph is other
        assert o._SELECTED_SUPPLY.get() is supply
    assert o._SELECTED_SUPPLY.get() is None
    assert captured.run(o._SELECTED_SUPPLY.get) is supply

    invocation = SimpleNamespace(physical_parent_region_id=7)
    graph._component_invocations = [invocation]
    graph._invocation_index = {1: 0}
    cm = graph.active_invocation_region(1)
    invocation.physical_parent_region_id = 8
    with cm:
        assert graph.current_region_id() == 8
    with graph.active_region(9), graph.active_invocation_region(None):
        assert graph.current_region_id() == 9

    events = []

    @contextmanager
    def active(region: Any) -> Any:
        events.append(("enter", region))
        try:
            yield "ignored"
        except ValueError as error:
            events.append(("suppressed", str(error)))
        finally:
            events.append(("exit", region))

    graph.active_region = active
    with graph.active_invocation_region(1) as entered:
        assert entered is None
        raise ValueError("handled")
    assert events == [("enter", 8), ("suppressed", "handled"), ("exit", 8)]
    del graph.active_region

    context = SimpleNamespace(component=None)
    cm = graph.slot_site(context, source="source", position=(0, 1))
    context.component = SimpleNamespace(id="entry")
    calls = []

    def record(ctx: Any, **kwargs: Any) -> int:
        calls.append((ctx, kwargs))
        ctx.component.id = "after-record"
        return 10

    graph.record_source_location = record
    with cm as entered:
        site = o._SLOT_SITE.get()
        assert entered == 10
        assert site.graph is graph and site.receiver_render_id == "after-record" and site.source_location_id == 10
    assert len(calls) == 1 and calls[0][0] is context
    assert calls[0][1] == {"kind": o.SourceLocationKind.SLOT_OUTLET, "source": "source", "position": (0, 1)}
    assert o._SLOT_SITE.get() is None
    try:
        with graph.slot_site(SimpleNamespace(component=None), source="source", position=(0, 1)):
            raise AssertionError("A component-free slot site was accepted")
    except RuntimeError as error:
        assert str(error) == "A slot outlet requires a component-owned render context."
    assert o._SLOT_SITE.get() is None

    temporary = o.OwnershipGraph()
    weak = ref(temporary)
    cm = temporary.active_region(11)
    with cm:
        pass
    del temporary
    gc.collect()
    assert weak() is None


def main() -> None:
    """Retain supported checks and the difference when an entered scope is abandoned."""
    outer = o._ACTIVE_REGION.set(None)
    try:
        for changed in (False, True):
            exercise(changed)
        abandoned = []
        for changed in (False, True):
            install(changed)
            token = o._ACTIVE_REGION.set(None)
            try:
                graph = o.OwnershipGraph()
                cm = graph.active_region(12)
                cm.__enter__()
                del cm
                gc.collect()
                abandoned.append(o._ACTIVE_REGION.get() is None)
            finally:
                o._ACTIVE_REGION.reset(token)
        assert abandoned == [True, False]
        entry_errors = []
        source_alive = []

        class Source:
            pass

        for changed in (False, True):
            install(changed)
            graph = o.OwnershipGraph()
            context = SimpleNamespace(component=SimpleNamespace(id="owner"))

            def fail(*_args: Any, **_kwargs: Any) -> Any:
                raise StopIteration("entry")

            graph.record_source_location = fail
            try:
                with graph.slot_site(context, source="source", position=(0, 1)):
                    raise AssertionError("The entry callback did not fail")
            except (RuntimeError, StopIteration) as error:
                entry_errors.append(type(error).__name__)
            graph.record_source_location = lambda *_args, **_kwargs: 1
            source = Source()
            weak_source = ref(source)
            cm = graph.slot_site(context, source=source, position=(0, 1))
            del source
            with cm:
                source_alive.append(weak_source() is not None)
        assert entry_errors == ["RuntimeError", "StopIteration"]
        assert source_alive == [True, False]
        report = {
            "nested_graph_restoration_and_exception_identity": True,
            "decorator_recreation": True,
            "copied_context_retains_original_supply_payload": True,
            "invocation_parent_is_looked_up_on_entry": True,
            "live_active_region_override_can_suppress": True,
            "slot_site_uses_entry_component_and_post_record_id": True,
            "entry_failure_leaves_slot_site_unchanged": True,
            "completed_manager_releases_graph": True,
            "abandoned_entered_scope_restores": {"reference": abandoned[0], "candidate": abandoned[1]},
            "entry_callback_stop_iteration": {"reference": entry_errors[0], "candidate": entry_errors[1]},
            "site_source_alive_during_body": {"reference": source_alive[0], "candidate": source_alive[1]},
            "production_compatible": False,
        }
        (ROOT / "benchmarks/results/performance-render/ownership-scope-contracts.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
        print(json.dumps(report, indent=2))
    finally:
        o._ACTIVE_REGION.reset(outer)
        install(changed=False)


if __name__ == "__main__":
    main()
