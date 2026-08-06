"""Detached Events payload export and mutation-free replay staging."""

from __future__ import annotations

import json
from dataclasses import fields
from typing import TYPE_CHECKING, Any, cast

from citry.ext.cache.errors import CacheArtifactError
from citry.extension import RenderCacheWrite, StagedRenderCacheContribution

from .emission import EXTRA_KEY, EventInstanceEntry
from .tokens import (
    StateTokenError,
    _prepare_state_token_values,
    _resolve_hints,
    _value_matches,
    verify_state_token,
)

if TYPE_CHECKING:
    from citry.ext.events.extension import EventsExtension
    from citry.extension import OnRenderCacheExportContext, OnRenderCacheStageContext


def export_events_cache(
    extension: EventsExtension,  # noqa: ARG001 - kept symmetric with staging
    ctx: OnRenderCacheExportContext,
) -> dict[str, object]:
    """Export only selected active Events instances using local references."""
    local_by_id = {instance.render_id: instance.index for instance in ctx.instances}
    entries: dict[EventInstanceEntry, None] = ctx.root_context.extra.get(EXTRA_KEY, {})
    exported: list[dict[str, object]] = []
    for entry in entries:
        if entry.render_id not in ctx.selected_render_ids:
            continue
        try:
            values = json.loads(entry.public_state_json)
        except (json.JSONDecodeError, RecursionError) as err:  # pragma: no cover - produced internally
            raise CacheArtifactError("A live Events entry contains invalid public-value JSON.") from err
        state: dict[str, object] | None
        if entry.state_token:
            state = {
                "storage": "server" if entry.state_token.startswith("ces1.") else "signed",
                "token": entry.state_token,
                "values": values,
            }
        else:
            state = None
        exported.append(
            {
                "class_id": entry.component_class_id,
                "instance": local_by_id[entry.render_id],
                "state": state,
            }
        )
    return {"instances": exported}


def stage_events_cache(
    extension: EventsExtension,
    ctx: OnRenderCacheStageContext,
) -> StagedRenderCacheContribution:
    """Verify archived tokens and prepare fresh-ID Events entries."""
    if set(ctx.payload) != {"instances"} or type(ctx.payload["instances"]) is not list:
        raise CacheArtifactError("Events render-cache payload has an invalid field set.")

    expected: dict[int, tuple[type, Any]] = {}
    for index, class_id in enumerate(ctx.instance_class_ids):
        try:
            component_class = ctx.citry.get_component_by_class_id(class_id)
        except KeyError as err:
            raise CacheArtifactError(f"Events artifact instance {index} has no current component class.") from err
        info = extension.resolve(component_class)
        if info.events_cls is not None:
            expected[index] = (component_class, info)

    entries: dict[EventInstanceEntry, None] = {}
    writes: list[RenderCacheWrite] = []
    markers: list[tuple[int, tuple[str, ...]]] = []
    seen: set[int] = set()
    for record_index, raw in enumerate(ctx.payload["instances"]):
        path = f"events.instances[{record_index}]"
        if type(raw) is not dict or set(raw) != {"class_id", "instance", "state"}:
            raise CacheArtifactError(f"{path} has an invalid field set.")
        record = cast("dict[str, object]", raw)
        instance = record["instance"]
        if type(instance) is not int or instance not in expected:
            raise CacheArtifactError(f"{path}.instance does not refer to an Events component.")
        if instance in seen:
            raise CacheArtifactError(f"{path}.instance is duplicated.")
        seen.add(instance)
        component_class, info = expected[instance]
        class_id_value = record["class_id"]
        if type(class_id_value) is not str or class_id_value != ctx.instance_class_ids[instance]:
            raise CacheArtifactError(f"{path}.class_id does not match its artifact instance.")
        class_id = class_id_value

        state = record["state"]
        if info.state_cls is None or info.state_meta is None:
            if state is not None:
                raise CacheArtifactError(f"{path}.state must be null for a stateless Events component.")
            token = ""
            public_values: dict[str, object] = {}
        else:
            if type(state) is not dict or set(state) != {"storage", "token", "values"}:
                raise CacheArtifactError(f"{path}.state has an invalid field set.")
            state_record = cast("dict[str, object]", state)
            storage = state_record["storage"]
            token_value = state_record["token"]
            public_value = state_record["values"]
            if type(storage) is not str or storage != info.state_meta.storage:
                raise CacheArtifactError(f"{path}.state.storage is incompatible with current State metadata.")
            if type(token_value) is not str or not token_value:
                raise CacheArtifactError(f"{path}.state.token must be a non-empty string.")
            if (storage == "server") != token_value.startswith("ces1."):
                raise CacheArtifactError(f"{path}.state.token does not match its storage mode.")
            if type(public_value) is not dict:
                raise CacheArtifactError(f"{path}.state.values must be a JSON object.")
            public_values = cast("dict[str, object]", public_value)
            try:
                verified = verify_state_token(
                    token_value,
                    cls=component_class,
                    secrets=list(ctx.citry.settings.secret or []),
                    cache=ctx.citry.cache,
                )
            except StateTokenError as err:
                raise CacheArtifactError(f"{path}.state.token is no longer replayable: {err}") from err
            state_fields = tuple(field.name for field in fields(info.state_cls))
            if set(verified.state_kwargs) != set(state_fields):
                raise CacheArtifactError(f"{path}.state.token fields do not match the current State class.")
            hints = _resolve_hints(info.state_cls)
            for field_name in state_fields:
                if not _value_matches(verified.state_kwargs[field_name], hints.get(field_name)):
                    raise CacheArtifactError(
                        f"{path}.state.token field {field_name!r} does not match its current type."
                    )
            expected_public = {name: verified.state_kwargs[name] for name in info.state_meta.public}
            if not _exact_json_equal(public_values, expected_public):
                raise CacheArtifactError(f"{path}.state.values do not match the protected token.")
            prepared = _prepare_state_token_values(
                dict(verified.state_kwargs),
                class_id=class_id,
                secret=ctx.citry.settings.secret,
                max_age=info.state_meta.max_age,
                max_bytes=info.state_meta.max_bytes,
                storage=info.state_meta.storage,
            )
            token = prepared.token
            if prepared.cache_key is not None:
                writes.append(
                    RenderCacheWrite(
                        key=prepared.cache_key,
                        value=cast("str", prepared.cache_value),
                        ttl=prepared.ttl,
                        rollback_delete=True,
                    )
                )

        entry = EventInstanceEntry(
            render_id=ctx.instance_ids[instance],
            component_class_id=class_id,
            state_token=token or None,
            public_state_json=json.dumps(public_values, sort_keys=True),
        )
        entries[entry] = None
        markers.append((instance, (f'data-cid="{ctx.instance_ids[instance]}"',)))

    if seen != set(expected):
        raise CacheArtifactError("Events render-cache payload has incomplete instance coverage.")
    return StagedRenderCacheContribution(
        extra_items=((EXTRA_KEY, entries),) if entries else (),
        cache_writes=tuple(writes),
        frame_markers=tuple(markers),
    )


def _exact_json_equal(left: object, right: object) -> bool:
    """Compare JSON values without Python's bool/int or int/float equality collapse."""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        left_dict = cast("dict[str, object]", left)
        right_dict = cast("dict[str, object]", right)
        return set(left_dict) == set(right_dict) and all(
            _exact_json_equal(left_dict[key], right_dict[key]) for key in left_dict
        )
    if type(left) is list:
        left_list = cast("list[object]", left)
        right_list = cast("list[object]", right)
        return len(left_list) == len(right_list) and all(
            _exact_json_equal(left_item, right_item)
            for left_item, right_item in zip(left_list, right_list, strict=True)
        )
    return bool(left == right)


__all__: list[str] = []
