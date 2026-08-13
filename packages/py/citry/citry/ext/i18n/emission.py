"""Serialize client-enabled i18n providers and their exact message roots."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from citry._owned_resource import _OwnedResource
from citry.ext.dependencies.types import Script
from citry.ownership import OwnershipState, RegionState

from .context import LocaleContext
from .usage import (
    AMBIENT_CLIENT_OWNER,
    CLIENT_CONTEXT_KEY,
    EXTRA_KEY,
    ClientProviderUse,
    I18nRenderRecord,
    MessageOutputUse,
    ProviderFieldPolicy,
)

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.ext.dependencies.emission import OnDependenciesContext

    from .extension import I18nExtension

RUNTIME_PATH = "ext/i18n/runtime.js"
MESSAGES_PATH = "ext/i18n/messages"
_RUNTIME_SOURCE = Path(__file__).parent / "client" / "citry-i18n.js"


@cache
def client_runtime_js() -> str:
    """Read the committed browser bundle once per process."""
    return _RUNTIME_SOURCE.read_text(encoding="utf-8")


def client_runtime_resource(citry: Citry) -> _OwnedResource:
    """Return the shared source used by mounted emission and route serving."""
    url = citry.build_url(RUNTIME_PATH) if citry.mounted_prefix is not None else RUNTIME_PATH
    return _OwnedResource(
        url=url,
        content=client_runtime_js(),
        content_type="text/javascript",
        headers=(("Cache-Control", "no-store"),),
    )


def emit_i18n_dependencies(extension: I18nExtension, ctx: OnDependenciesContext) -> None:
    """Add the i18n runtime and provider manifest when the render needs them."""
    if (
        not extension.configured
        or ctx.strategy not in {"document", "fragment"}
        or ctx._security_javascript in {"omit", "forbid"}
    ):
        return
    records = cast("dict[str, I18nRenderRecord]", ctx.context.extra.get(EXTRA_KEY, {}))
    providers, requirements = _provider_manifest_entries(extension, ctx, records)
    if not providers and not requirements:
        return

    manifest = {
        "schema_version": 1,
        "runtime": "@fluent/bundle@0.19.1",
        "catalog_revision": extension.catalog_revision,
        "formats_revision": extension.config.formats_revision,
        "formats": extension.config.formats.to_wire(),
        "locales": list(extension.config.locales),
        "contexts": {
            locale: _context_to_wire(extension.make_context(locale=locale)) for locale in extension.config.locales
        },
        "messages_url": (
            extension.citry.build_url(MESSAGES_PATH) if extension.citry.mounted_prefix is not None else None
        ),
        "parsers": {locale: extension.browser_parser_artifact(locale=locale) for locale in extension.config.locales},
        "providers": providers,
        "requirements": requirements,
    }
    manifest_json = json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True).replace(
        "<", "\\u003c"
    )
    ctx.before_manifest.append(
        Script(
            kind="core",
            content=manifest_json,
            attrs={"type": "application/json", "data-citry-i18n": True},
        )
    )

    if extension.citry.mounted_prefix is not None:
        resource = client_runtime_resource(extension.citry)
        runtime = Script(kind="core", url=resource.url)
        runtime._owned_resource = resource
    else:
        runtime = Script(kind="core", content=client_runtime_js(), wrap=False)
    # The bootstrap must run before the Events bundle starts Alpine, but after
    # the dependency manager has created Citry.alpine and Citry.manager.
    ctx.scripts.insert(0, runtime)


def _provider_manifest_entries(
    extension: I18nExtension,
    ctx: OnDependenciesContext,
    records: dict[str, I18nRenderRecord],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    parent_by_id: dict[str, str | None] = {}
    instance_by_id: dict[str, Any] = {}
    invocation_by_id: dict[object, Any] = {}
    region_by_id: dict[object, Any] = {}
    active_ids: set[str] = set()
    ownership = ctx.context.ownership
    if ownership is not None:
        snapshot = ownership.snapshot()
        for logical in snapshot.logical_instances:
            if logical.state is OwnershipState.ACTIVE:
                active_ids.add(logical.render_id)
                parent_by_id[logical.render_id] = logical.logical_parent_render_id
                instance_by_id[logical.render_id] = logical
        invocation_by_id = {
            invocation.id: invocation
            for invocation in snapshot.component_invocations
            if invocation.state is OwnershipState.ACTIVE
        }
        region_by_id = {
            region.id: region for region in snapshot.physical_regions if region.state is RegionState.CAPTURED
        }
    if active_ids:
        records = {render_id: record for render_id, record in records.items() if render_id in active_ids}

    provider_records = {render_id: record for render_id, record in records.items() if record.provider is not None}
    barriers = {render_id for render_id, record in records.items() if record.client_barrier}

    def physical_ancestors(render_id: str) -> tuple[str, ...]:
        ancestors: list[str] = []
        visited: set[str] = {render_id}
        instance = instance_by_id.get(render_id)
        invocation_id = instance.invocation_id if instance is not None else None
        invocation = invocation_by_id.get(invocation_id)
        region_id = invocation.physical_parent_region_id if invocation is not None else None
        while region_id is not None:
            region = region_by_id.get(region_id)
            if region is None:
                break
            receiver = cast("str", region.receiver_render_id)
            if receiver in visited:
                raise RuntimeError("The i18n provider tree contains a physical-region cycle.")
            ancestors.append(receiver)
            visited.add(receiver)
            region_id = region.containing_region_id

        current = parent_by_id.get(ancestors[-1]) if ancestors else parent_by_id.get(render_id)
        logical_seen: set[str] = set()
        while current is not None:
            if current in logical_seen:
                raise RuntimeError("The i18n provider tree contains a component-parent cycle.")
            logical_seen.add(current)
            if current not in visited:
                ancestors.append(current)
                visited.add(current)
            current = parent_by_id.get(current)
        return tuple(ancestors)

    def nearest_provider(render_id: str) -> tuple[str | None, bool]:
        for current in physical_ancestors(render_id):
            if current in barriers:
                return None, True
            if current in provider_records:
                return current, False
        return None, False

    def descendant_providers(render_id: str) -> tuple[str, ...]:
        descendants: list[str] = []
        for provider_id in provider_records:
            if provider_id == render_id or render_id in physical_ancestors(provider_id):
                descendants.append(provider_id)
        return tuple(descendants)

    external_owner = ctx.context.provides.get(CLIENT_CONTEXT_KEY)
    if external_owner is not None and (type(external_owner) is not str or not external_owner):
        raise TypeError(f"The internal {CLIENT_CONTEXT_KEY!r} render provide must be a render ID.")

    outputs_by_requirement: dict[tuple[str, str], dict[MessageOutputUse, None]] = {}
    groups_by_requirement: dict[tuple[str, str], dict[str, None]] = {}
    bindings_by_requirement: dict[tuple[str, str], list[Any]] = {}
    for render_id, record in records.items():
        record.bindings.assert_ready()
        targets = dict.fromkeys(descendant_providers(render_id))
        blocked = False
        owner = record.client_owner
        if owner is None:
            owner, blocked = nearest_provider(render_id)
        if owner == AMBIENT_CLIENT_OWNER:
            owner = cast("str | None", external_owner)
        if owner is not None:
            targets[owner] = None
        elif external_owner is not None and not blocked:
            targets[cast("str", external_owner)] = None
            owner = cast("str", external_owner)
        if record.bindings.records:
            for binding in record.bindings.records:
                binding_owner = external_owner if binding.owner == AMBIENT_CLIENT_OWNER else binding.owner
                if binding_owner is None:
                    raise RuntimeError(f"Rendered $c-tr binding {binding.id!r} has no logical client i18n provider.")
                requirement_key = (render_id, binding_owner)
                binding_target = bindings_by_requirement.setdefault(requirement_key, [])
                binding_outputs = outputs_by_requirement.setdefault(requirement_key, {})
                binding_target.append(binding)
                binding_outputs[MessageOutputUse(binding.message, binding.output)] = None
        for target in targets:
            groups = groups_by_requirement.setdefault((render_id, target), {})
            groups.update(dict.fromkeys(record.client_messages))
            groups.update(dict.fromkeys(output.message for output in record.client_outputs))

    provider_entries: list[dict[str, object]] = []
    for render_id, record in provider_records.items():
        provider = cast("ClientProviderUse", record.provider)
        provider_entries.append(
            {
                "context": _context_to_wire(provider.context),
                "id": render_id,
                "parent": (external_owner if provider.parent == AMBIENT_CLIENT_OWNER else provider.parent),
                "policy": {
                    "direction": _policy_to_wire(provider.direction),
                    "locale": _policy_to_wire(provider.locale),
                    "time_zone": _policy_to_wire(provider.time_zone),
                },
            }
        )

    external_context = ctx.context.provides.get("citry_i18n")
    if external_owner is not None and type(external_context) is not LocaleContext:
        raise TypeError(
            f"A render provided {CLIENT_CONTEXT_KEY!r} without the matching exact LocaleContext under 'citry_i18n'."
        )
    contexts_by_provider = {
        render_id: cast("ClientProviderUse", record.provider).context for render_id, record in provider_records.items()
    }
    if external_owner is not None:
        contexts_by_provider[external_owner] = cast("LocaleContext", external_context)

    requirement_entries: list[dict[str, object]] = []
    requirement_keys = dict.fromkeys((*outputs_by_requirement, *groups_by_requirement))
    for owner, provider_id in requirement_keys:
        requirement_key = (owner, provider_id)
        output_set = outputs_by_requirement.get(requirement_key, {})
        outputs = tuple(output_set)
        messages = tuple(groups_by_requirement.get(requirement_key, {}))
        bindings = tuple(bindings_by_requirement.get(requirement_key, ()))
        if not outputs and not messages and not bindings:
            continue
        provider_context = contexts_by_provider[provider_id]
        artifact_locales = (
            extension.config.locales if extension.citry.mounted_prefix is None else (provider_context.locale,)
        )
        artifacts = {
            locale: extension.browser_artifact(locale=locale, outputs=outputs, messages=messages)
            for locale in artifact_locales
        }
        requirement_entries.append(
            {
                "artifacts": artifacts,
                "bindings": [_binding_to_wire(binding) for binding in bindings],
                "messages": list(messages),
                "owner": owner,
                "outputs": [_output_token(output) for output in outputs],
                "provider": provider_id,
                "rendered_locale": provider_context.locale,
            }
        )
    return provider_entries, requirement_entries


def _output_token(output: MessageOutputUse) -> str:
    return output.message if output.attr is None else f"{output.message}.{output.attr}"


def _binding_to_wire(binding: Any) -> dict[str, object]:
    target: dict[str, object] = {"kind": binding.target.kind}
    if binding.target.kind == "attribute":
        target["name"] = binding.target.name
    item: dict[str, object] = {
        "id": binding.id,
        "message": binding.message,
        "target": target,
        "values": {name: {"type": tagged[0], "value": tagged[1]} for name, tagged in binding.values},
    }
    if binding.output is not None:
        item["output"] = binding.output
    if binding.values_expression is not None:
        item["values_expression"] = binding.values_expression
    return item


def _context_to_wire(context: Any) -> dict[str, object]:
    return {
        "catalog_revision": context.catalog_revision,
        "direction": context.direction,
        "fallback_locales": list(context.fallback_locales),
        "formats_revision": context.formats_revision,
        "locale": context.locale,
        "time_zone": context.time_zone,
        "tzdb_revision": context.tzdb_revision,
    }


def _policy_to_wire(policy: ProviderFieldPolicy) -> dict[str, object]:
    result: dict[str, object] = {"mode": policy.mode}
    if policy.mode == "explicit":
        result["value"] = policy.value
    return result


__all__ = ["MESSAGES_PATH", "RUNTIME_PATH", "client_runtime_js", "emit_i18n_dependencies"]
