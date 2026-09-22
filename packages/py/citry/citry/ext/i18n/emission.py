"""Serialize client-enabled i18n providers and their exact message roots."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from citry._owned_resource import _OwnedResource
from citry.citry_render import selected_render_ids
from citry.ext.dependencies.types import Script

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
    from collections.abc import Mapping

    from citry.citry import Citry
    from citry.ext.dependencies.emission import OnDependenciesContext

    from .extension import I18nExtension

RUNTIME_PATH = "ext/i18n/runtime.js"
MESSAGES_PATH = "ext/i18n/messages"
_RUNTIME_SOURCE = Path(__file__).parent / "client" / "vue-plugin.source.js"


@cache
def client_runtime_js() -> str:
    """Read the committed browser bundle once per process."""
    return _RUNTIME_SOURCE.read_text(encoding="utf-8")


@cache
def vue_plugin_js() -> str:
    """Read the native Vue plugin source once per process."""
    return client_runtime_js()


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
    selected_ids = selected_render_ids(ctx.selected_render)
    records = {
        render_id: record
        for render_id, record in cast("dict[str, I18nRenderRecord]", ctx.context.extra.get(EXTRA_KEY, {})).items()
        if render_id in selected_ids
    }
    providers, requirements = _provider_manifest_entries(extension, ctx.context, records)
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
    # Load the i18n runtime before component scripts that use its Vue APIs.
    ctx.scripts.insert(0, runtime)


def prepared_i18n_payload(
    extension: I18nExtension,
    *,
    context: Any,
    records: dict[str, I18nRenderRecord],
    render_to_occurrence: Mapping[str, str],
    occurrence_parents: Mapping[str, str | None],
) -> dict[str, object]:
    """Build checked i18n data keyed by stable Vue occurrence IDs."""
    providers, requirements = _provider_manifest_entries(
        extension,
        context,
        records,
        render_to_occurrence=render_to_occurrence,
        occurrence_parents=occurrence_parents,
    )
    mapped_providers: dict[str, dict[str, object]] = {}
    for provider in providers:
        render_id = cast("str", provider["id"])
        host_occurrence_id = render_to_occurrence.get(render_id)
        occurrence_id = None if host_occurrence_id is None else occurrence_parents.get(host_occurrence_id)
        if occurrence_id is None:
            raise ValueError(f"i18n provider {render_id!r} has no owning Vue occurrence.")
        parent = provider["parent"]
        if isinstance(parent, str):
            parent = (
                occurrence_parents.get(render_to_occurrence[parent])
                if parent in render_to_occurrence
                else {"serverProviderId": parent}
            )
        mapped = provider | {"id": occurrence_id, "parent": parent, "serverProviderId": render_id}
        prior = mapped_providers.get(occurrence_id)
        if prior is not None and prior != mapped:
            raise ValueError(f"i18n provider roles conflict on Vue occurrence {occurrence_id!r}.")
        mapped_providers[occurrence_id] = mapped
    mapped_requirements: list[dict[str, object]] = []
    for requirement in requirements:
        owner = cast("str", requirement["owner"])
        # Named apart from the `provider` entries mapped above: this one is the
        # render id a requirement points at, not a provider record.
        provider_render_id = cast("str", requirement["provider"])
        owner_id = render_to_occurrence.get(owner)
        if owner_id is None:
            raise ValueError(f"i18n requirement owner {owner!r} has no selected Vue occurrence.")
        mapped_requirements.append(
            requirement
            | {
                "owner": owner_id,
                "provider": (
                    occurrence_parents.get(render_to_occurrence[provider_render_id])
                    if provider_render_id in render_to_occurrence
                    else {"serverProviderId": provider_render_id}
                ),
            }
        )
    barrier_parents: set[str] = set()
    for render_id, record in records.items():
        if not record.client_barrier or render_id not in render_to_occurrence:
            continue
        # A barrier is recorded against the occurrence that contains it, so a root
        # occurrence has no parent to record and contributes no barrier.
        barrier_parent = occurrence_parents.get(render_to_occurrence[render_id])
        if barrier_parent is not None:
            barrier_parents.add(barrier_parent)
    barriers = sorted(barrier_parents)
    if set(barriers) & set(mapped_providers):
        raise ValueError("One Vue occurrence cannot be both an i18n provider and barrier.")
    if not mapped_providers and not mapped_requirements and not barriers:
        return {"barriers": [], "providers": [], "requirements": []}
    return {
        "barriers": barriers,
        "catalog_revision": extension.catalog_revision,
        "contexts": {
            locale: _context_to_wire(extension.make_context(locale=locale)) for locale in extension.config.locales
        },
        "formats": extension.config.formats.to_wire(),
        "formats_revision": extension.config.formats_revision,
        "locales": list(extension.config.locales),
        "messages_url": (
            extension.citry.build_url(MESSAGES_PATH) if extension.citry.mounted_prefix is not None else None
        ),
        "parsers": {locale: extension.browser_parser_artifact(locale=locale) for locale in extension.config.locales},
        "providers": list(mapped_providers.values()),
        "requirements": mapped_requirements,
        "runtime": "@fluent/bundle@0.19.1",
    }


def _provider_manifest_entries(
    extension: I18nExtension,
    context: Any,
    records: dict[str, I18nRenderRecord],
    *,
    render_to_occurrence: Mapping[str, str] | None = None,
    occurrence_parents: Mapping[str, str | None] | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if (render_to_occurrence is None) != (occurrence_parents is None):
        raise ValueError("Prepared i18n ancestry requires both render and occurrence parent mappings.")
    prepared_render_map = cast("Mapping[str, str]", render_to_occurrence)
    prepared_parent_map = cast("Mapping[str, str | None]", occurrence_parents)
    parent_by_id = {
        render_id: (record.provider.parent if record.provider is not None else record.client_owner)
        for render_id, record in records.items()
    }
    provider_records = {render_id: record for render_id, record in records.items() if record.provider is not None}
    barriers = {render_id for render_id, record in records.items() if record.client_barrier}

    def physical_ancestors(render_id: str) -> tuple[str, ...]:
        ancestors: list[str] = []
        visited = {render_id}
        current = parent_by_id.get(render_id)
        # Walking stops at the tree root (no parent) and at the ambient owner,
        # which stands for "outside any component" rather than a real ancestor.
        while current is not None and current != AMBIENT_CLIENT_OWNER:
            if current in visited:
                raise RuntimeError("The i18n provider tree contains a component-parent cycle.")
            ancestors.append(current)
            visited.add(current)
            current = parent_by_id.get(current)
        return tuple(ancestors)

    def prepared_occurrence(render_id: str) -> str:
        occurrence_id = prepared_render_map.get(render_id)
        if occurrence_id is None:
            raise ValueError(f"i18n render {render_id!r} has no selected Vue occurrence.")
        return occurrence_id

    def occurrence_ancestors(occurrence_id: str) -> tuple[str, ...]:
        ancestors: list[str] = []
        visited: set[str] = set()
        current: str | None = occurrence_id
        while current is not None:
            if current in visited:
                raise RuntimeError("The prepared Vue occurrence tree contains a parent cycle.")
            if current not in prepared_parent_map:
                raise ValueError(f"Prepared Vue occurrence {current!r} has no parent record.")
            ancestors.append(current)
            visited.add(current)
            current = prepared_parent_map[current]
        return tuple(ancestors)

    def role_occurrence(render_id: str) -> str:
        host_occurrence = prepared_occurrence(render_id)
        owner_occurrence = prepared_parent_map.get(host_occurrence)
        if owner_occurrence is None:
            raise ValueError(f"i18n provider or barrier {render_id!r} has no owning Vue occurrence.")
        return owner_occurrence

    provider_by_occurrence: dict[str, str] = {}
    barrier_occurrences: set[str] = set()
    if render_to_occurrence is not None:
        for provider_id in provider_records:
            provider_occurrence = role_occurrence(provider_id)
            prior = provider_by_occurrence.setdefault(provider_occurrence, provider_id)
            if prior != provider_id:
                raise ValueError(f"i18n provider roles conflict on Vue occurrence {provider_occurrence!r}.")
        barrier_occurrences = {role_occurrence(render_id) for render_id in barriers}

    def nearest_provider(render_id: str) -> tuple[str | None, bool]:
        if render_to_occurrence is None:
            candidates: tuple[str, ...] = physical_ancestors(render_id)
        else:
            candidates = occurrence_ancestors(prepared_occurrence(render_id))
        for current in candidates:
            if render_to_occurrence is not None:
                if current in barrier_occurrences:
                    return None, True
                provider_id = provider_by_occurrence.get(current)
                if provider_id is not None:
                    return provider_id, False
                continue
            if current in barriers:
                return None, True
            if current in provider_records:
                return current, False
        return None, False

    def descendant_providers(render_id: str) -> tuple[str, ...]:
        if render_to_occurrence is not None:
            owner_occurrence = prepared_occurrence(render_id)
            return tuple(
                provider_id
                for provider_id in provider_records
                if owner_occurrence in occurrence_ancestors(role_occurrence(provider_id))
            )
        descendants: list[str] = []
        for provider_id in provider_records:
            if provider_id == render_id or render_id in physical_ancestors(provider_id):
                descendants.append(provider_id)
        return tuple(descendants)

    external_owner = context.provides.get(CLIENT_CONTEXT_KEY)
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

    external_context = context.provides.get("citry_i18n")
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
