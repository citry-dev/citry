"""Capture and encode Events records for Vue prepared occurrences."""

from __future__ import annotations

import json
from dataclasses import fields
from typing import TYPE_CHECKING, NamedTuple

from citry._protocol.events import (
    build_component_instance,
    build_descriptor,
    build_handler_descriptor,
    build_manifest,
)
from citry.constness import const_value
from citry.ext.events.handlers import event_options
from citry.ext.events.tokens import mint_state_token

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.citry_context import CitryContext
    from citry.ext.events.extension import EventsExtension
    from citry.extension import OnComponentDataContext

EXTRA_KEY = "events"


class EventInstanceEntry(NamedTuple):
    """Signed browser credentials captured for one rendered Events occurrence."""

    render_id: str
    component_class_id: str
    state_token: str | None
    public_state_json: str


def capture_instance(extension: EventsExtension, ctx: OnComponentDataContext) -> None:
    """Record one Events occurrence after component data hooks have completed."""
    comp_cls = type(ctx.component)
    info = extension.resolve(comp_cls)
    if info.events_cls is None:
        return
    if info.state_cls is not None and info.state_meta is not None:
        state = extension.build_state(ctx.component)
        for state_field in fields(state):
            setattr(state, state_field.name, const_value(getattr(state, state_field.name)))
        meta = info.state_meta
        token = mint_state_token(
            state,
            class_id=comp_cls.class_id,
            secret=ctx.citry.settings.secret,
            max_age=meta.max_age,
            max_bytes=meta.max_bytes,
            storage=meta.storage,
            cache=ctx.citry.cache,
        )
        values = {name: getattr(state, name) for name in meta.public}
    else:
        token = None
        values = {}
    entry = EventInstanceEntry(
        render_id=ctx.component.id,
        component_class_id=comp_cls.class_id,
        state_token=token,
        public_state_json=json.dumps(values, sort_keys=True, allow_nan=False),
    )
    entries: dict[EventInstanceEntry, None] = ctx.context.extra.setdefault(EXTRA_KEY, {})
    entries[entry] = None
    from citry._vue.capture import direct_prepared_render_active  # noqa: PLC0415

    if not direct_prepared_render_active():
        ctx.context._add_root_markers([f'data-cid="{ctx.component.id}"'])


def merge_instance_entries(parent_context: CitryContext, child_context: CitryContext) -> None:
    """Bubble selected child credentials to the enclosing render context."""
    child_entries = child_context.extra.get(EXTRA_KEY)
    if child_entries:
        parent_entries: dict[EventInstanceEntry, None] = parent_context.extra.setdefault(EXTRA_KEY, {})
        parent_entries.update(child_entries)


def build_events_manifest(
    extension: EventsExtension,
    citry: Citry,
    entries: list[EventInstanceEntry],
) -> dict[str, object]:
    """Build validated Events descriptors and signed occurrence records."""
    descriptors: dict[str, dict[str, object]] = {}
    for entry in entries:
        if entry.component_class_id in descriptors:
            continue
        info = extension.resolve(citry.get_component_by_class_id(entry.component_class_id))
        event_handlers: dict[str, dict[str, object]] = {}
        for handler in info.handlers.values():
            options = event_options(handler.func)
            event_handlers[handler.name] = build_handler_descriptor(
                handler.methods[0],
                uses_state="state" in handler.params,
                debounce_milliseconds=handler.debounce,
                throttle_milliseconds=handler.throttle,
                latest_call_wins=options is not None and options.latest_wins,
                allow_batching=options is None or options.bundle,
            )
        writable = (
            info.state_meta.model
            if info.state_meta is not None and info.state_meta.model != info.state_meta.public
            else None
        )
        descriptors[entry.component_class_id] = build_descriptor(
            entry.component_class_id, event_handlers, writable_state_fields=writable
        )
    return build_manifest(
        list(descriptors.values()),
        [
            build_component_instance(
                entry.render_id,
                entry.component_class_id,
                entry.state_token,
                json.loads(entry.public_state_json),
            )
            for entry in entries
        ],
    )
