"""JSON protocol records for experimental prepared-view revisions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from .prepared import PreparedViewMetadata


@dataclass(frozen=True, slots=True)
class DefinitionAsset:
    id: str
    url: str
    sha256: str
    target: str
    helper_contract: str
    directive_signature: tuple[dict[str, object], ...]
    replacement_sites: tuple[dict[str, object], ...]
    dynamic_elements: tuple[dict[str, object], ...] = ()
    local_call_runs: tuple[dict[str, object], ...] = ()
    local_calls: tuple[dict[str, object], ...] = ()
    opaque_html_sites: tuple[dict[str, object], ...] = ()
    runtime_event_sites: tuple[dict[str, object], ...] = ()


def revision_envelope(
    *,
    app_id: str,
    base_revision: int,
    view: PreparedViewMetadata,
    assets: tuple[DefinitionAsset, ...],
    updated_ids: tuple[str, ...],
    replacements: tuple[dict[str, object], ...] = (),
    definition_ids: dict[str, str] | None = None,
) -> dict[str, object]:
    if view.revision != base_revision + 1:
        raise ValueError("prepared revision must immediately follow base revision")
    if len(set(updated_ids)) != len(updated_ids):
        raise ValueError("updated occurrence ids must be unique")
    known = {item.id for item in view.occurrences}
    if not set(updated_ids) <= known:
        raise ValueError("updated occurrence id is unknown")
    prior_key: tuple[str, str] | None = None
    seen_remounts: set[str] = set()
    for replacement in replacements:
        if set(replacement) != {"ownerId", "siteId", "expectedRemountIds"}:
            raise ValueError("invalid replacement metadata shape")
        owner, site, ids = replacement["ownerId"], replacement["siteId"], replacement["expectedRemountIds"]
        if (
            not isinstance(owner, str)
            or not isinstance(site, str)
            or not isinstance(ids, list)
            or any(not isinstance(item, str) for item in ids)
        ):
            raise ValueError("invalid replacement metadata values")
        if owner not in known or owner not in updated_ids or any(item not in known or item == owner for item in ids):
            raise ValueError("replacement metadata references unknown or unupdated occurrences")
        parents = {item.id: item.parent_id for item in view.occurrences}
        for item in ids:
            cursor = parents[item]
            while cursor is not None and cursor != owner:
                cursor = parents[cursor]
            if cursor != owner:
                raise ValueError("expected remount is not below its replacement owner")
        key = (owner, site)
        if (prior_key is not None and key <= prior_key) or ids != sorted(set(ids)) or seen_remounts.intersection(ids):
            raise ValueError("replacement metadata must be sorted and unique")
        prior_key = key
        seen_remounts.update(ids)
    return prepared_manifest(app_id=app_id, view=view, assets=assets, definition_ids=definition_ids) | {
        "baseRevision": base_revision,
        "updatedIds": list(updated_ids),
        "replacements": list(replacements),
    }


def prepared_manifest(
    *,
    app_id: str,
    view: PreparedViewMetadata,
    assets: tuple[DefinitionAsset, ...],
    definition_ids: dict[str, str] | None = None,
) -> dict[str, object]:
    logical_ids = {item.id for item in view.definitions}
    compiled_ids = {item: item for item in logical_ids} if definition_ids is None else definition_ids
    if set(compiled_ids) != logical_ids or any(type(value) is not str or not value for value in compiled_ids.values()):
        raise ValueError("compiled definition ids must exactly cover logical definitions")
    asset_ids = [item.id for item in assets]
    if len(set(asset_ids)) != len(asset_ids) or set(asset_ids) != set(compiled_ids.values()):
        raise ValueError("definition assets must uniquely and exactly cover the prepared definitions")
    for asset in assets:
        if re.fullmatch(r"[0-9a-f]{64}", asset.sha256) is None:
            raise ValueError("definition asset digest must be lowercase SHA-256")
        if not asset.url.startswith("/") or not asset.url.endswith(f"/{asset.sha256}.js") or "//" in asset.url:
            raise ValueError("definition asset URL must be same-origin and content-addressed")
        if asset.target != "ordinary-vnodes/1":
            raise ValueError("definition asset target is unsupported")
        if re.fullmatch(r"[0-9a-f]{64}", asset.helper_contract) is None:
            raise ValueError("definition helper contract must be a lowercase SHA-256")
        _validate_directive_signature(asset.directive_signature)
        _validate_runtime_event_sites(asset.runtime_event_sites, asset.directive_signature)
        _validate_dynamic_elements(asset.dynamic_elements)
        _validate_opaque_html_sites(asset.opaque_html_sites)
        _validate_local_call_runs(asset.local_call_runs)
        _validate_local_calls(asset.local_calls)
    assets_by_id = {asset.id: asset for asset in assets}
    from .prepared import PreparedMarker  # noqa: PLC0415

    markers: list[dict[str, str]] = []
    prior_marker: tuple[str, str, str] | None = None
    marker_keys: set[tuple[str, str]] = set()
    marker_occurrences: set[str] = set()
    known_occurrences = {item.id for item in view.occurrences} if view.markers else set()
    for marker in view.markers:
        if type(marker) is not PreparedMarker:
            raise TypeError("prepared markers must be exact PreparedMarker values")
        owner_id = marker.owner_id
        name = marker.name
        occurrence_id = marker.occurrence_id
        order = (owner_id, name, occurrence_id)
        if (
            type(owner_id) is not str
            or owner_id not in known_occurrences
            or type(occurrence_id) is not str
            or occurrence_id not in known_occurrences
            or type(name) is not str
            or re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", name) is None
        ):
            raise ValueError("prepared marker metadata is invalid")
        if (owner_id, name) in marker_keys or occurrence_id in marker_occurrences:
            raise ValueError("prepared marker aliases must be unique")
        if prior_marker is not None and order <= prior_marker:
            raise ValueError("prepared marker metadata must be strictly sorted")
        marker_keys.add((owner_id, name))
        marker_occurrences.add(occurrence_id)
        prior_marker = order
        markers.append({"ownerId": owner_id, "name": name, "occurrenceId": occurrence_id})
    for occurrence in view.occurrences:
        asset = assets_by_id[compiled_ids[occurrence.definition_id]]
        opaque = occurrence.prepared_data.get("opaqueHtml", {})
        if type(opaque) is not dict:
            raise ValueError("prepared opaque HTML values must be an exact object")
        declared = {item["key"] for item in asset.opaque_html_sites}
        if set(opaque) != declared:
            raise ValueError("prepared opaque HTML values do not match definition declarations")
        for key, record in opaque.items():
            if type(record) is not dict or set(record) != {"html"} or type(record["html"]) is not str:
                raise ValueError(f"prepared opaque HTML record {key!r} is invalid")
    return {
        "protocol": "citry-vue-prepared/1",
        "appId": app_id,
        "revision": view.revision,
        "rootId": view.root_id,
        "markers": markers,
        "definitions": [
            {
                "id": item.id,
                "url": item.url,
                "sha256": item.sha256,
                "target": item.target,
                "helperContract": item.helper_contract,
                "directiveSignature": list(item.directive_signature),
                "replacementSites": list(item.replacement_sites),
                "dynamicElements": list(item.dynamic_elements),
                "localCallRuns": list(item.local_call_runs),
                "localCalls": list(item.local_calls),
                "opaqueHtmlSites": list(item.opaque_html_sites),
                "runtimeEventSites": list(item.runtime_event_sites),
            }
            for item in assets
        ],
        "occurrences": [
            {
                "id": item.id,
                "typeKey": item.type_key,
                "definitionId": compiled_ids[item.definition_id],
                "serverData": item.server_data,
                "preparedData": item.prepared_data,
                "parentId": item.parent_id,
                "placementKey": item.placement_key,
            }
            for item in view.occurrences
        ],
        "replacements": [],
    }


def _validate_opaque_html_sites(values: tuple[dict[str, object], ...]) -> None:
    seen: set[str] = set()
    for item in values:
        if type(item) is not dict or set(item) != {"key", "sourceStart", "sourceEnd", "origin"}:
            raise ValueError("opaque HTML site has an invalid shape")
        key, start, end, origin = (item[name] for name in ("key", "sourceStart", "sourceEnd", "origin"))
        if (
            type(key) is not str
            or re.fullmatch(r"citryOpaque[0-9A-Za-z]+", key) is None
            or key in seen
            or type(start) is not int
            or type(end) is not int
            or not 0 <= start < end
            or origin not in {"raw", "markup"}
        ):
            raise ValueError("opaque HTML site is invalid")
        seen.add(key)


def _validate_directive_signature(signature: tuple[dict[str, object], ...]) -> None:
    sites: set[str] = set()
    for item in signature:
        if type(item) is not dict or set(item) != {"siteId", "name", "arg", "modifiers"}:
            raise ValueError("runtime directive signature record has an invalid shape")
        site = item["siteId"]
        name = item["name"]
        arg = item["arg"]
        modifiers = item["modifiers"]
        if type(site) is not str or re.fullmatch(r"citryDirective[0-9A-Za-z]+", site) is None:
            raise ValueError("runtime directive signature site is invalid")
        if site in sites:
            raise ValueError("runtime directive signature site is duplicated")
        sites.add(site)
        if type(name) is not str or not name:
            raise ValueError("runtime directive signature name is invalid")
        if arg is not None and type(arg) is not str:
            raise ValueError("runtime directive signature argument is invalid")
        if type(modifiers) is not list or any(type(value) is not str or not value for value in modifiers):
            raise ValueError("runtime directive signature modifiers are invalid")
        if modifiers != sorted(set(modifiers)):
            raise ValueError("runtime directive signature modifiers must be sorted and unique")


def _validate_runtime_event_sites(
    values: tuple[dict[str, object], ...],
    directive_signature: tuple[dict[str, object], ...],
) -> None:
    named_runtime_directives = [item for item in directive_signature if item["name"] == "v-citry-runtime-events"]
    if any(item["arg"] is not None or item["modifiers"] != [] for item in named_runtime_directives):
        raise ValueError("runtime event directive declaration has arguments or modifiers")
    runtime_directives = {item["siteId"] for item in named_runtime_directives}
    declared_sites: set[str] = set()
    seen: set[str] = set()
    seen_routes: set[tuple[str, tuple[tuple[str, str, int | None], ...]]] = set()
    for site in values:
        if type(site) is not dict or set(site) != {"siteId", "bindingKey", "steps"}:
            raise ValueError("runtime event site has an invalid shape")
        site_id, binding_key, steps = (site[name] for name in ("siteId", "bindingKey", "steps"))
        if (
            type(site_id) is not str
            or re.fullmatch(r"citryDirective[0-9a-f]+D[0-9]+", site_id) is None
            or site_id in seen
            or site_id not in runtime_directives
            or type(binding_key) is not str
            or re.fullmatch(r"citryRuntimeEvents[0-9A-Za-z]+", binding_key) is None
            or type(steps) is not list
        ):
            raise ValueError("runtime event site is invalid or duplicated")
        binding_key = cast("str", binding_key)
        seen.add(site_id)
        declared_sites.add(site_id)
        for step in steps:
            if type(step) is not dict:
                raise ValueError("runtime event site step has an invalid shape")
            kind = step.get("kind")
            key = step.get("key")
            if kind == "branch":
                if (
                    set(step) != {"kind", "key", "index"}
                    or type(key) is not str
                    or re.fullmatch(r"citryIf[0-9]+", key) is None
                    or type(step["index"]) is not int
                    or not 0 <= step["index"] <= 2**53 - 1
                ):
                    raise ValueError("runtime event branch step is invalid")
            elif kind in {"each", "empty"}:
                if (
                    set(step) != {"kind", "key"}
                    or type(key) is not str
                    or re.fullmatch(r"citryLoop[0-9]+", key) is None
                ):
                    raise ValueError("runtime event loop step is invalid")
            else:
                raise ValueError("runtime event site step kind is invalid")
        route = (
            binding_key,
            tuple(
                (
                    step["kind"],
                    step["key"],
                    step["index"] if step["kind"] == "branch" else None,
                )
                for step in steps
            ),
        )
        if route in seen_routes:
            raise ValueError("runtime event site route and binding key are duplicated")
        seen_routes.add(route)
    if declared_sites != runtime_directives:
        raise ValueError("runtime event sites do not exactly match runtime directive declarations")


def _validate_dynamic_elements(values: tuple[dict[str, object], ...]) -> None:
    aliases: set[str] = set()
    for item in values:
        if type(item) is not dict or set(item) != {"alias", "tag", "sourceStart", "sourceEnd"}:
            raise ValueError("dynamic element metadata has an invalid shape")
        alias, tag = item["alias"], item["tag"]
        start, end = item["sourceStart"], item["sourceEnd"]
        if type(alias) is not str or re.fullmatch(r"citry-dynamic-[0-9a-f]{16}", alias) is None or alias in aliases:
            raise ValueError("dynamic element alias is invalid or duplicated")
        if type(tag) is not str or re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", tag) is None:
            raise ValueError("dynamic element tag is invalid")
        if tag.lower() in {"script", "style", "template"}:
            raise ValueError("dynamic script, style, and template elements are unsupported")
        if type(start) is not int or type(end) is not int or start < 0 or end <= start:
            raise ValueError("dynamic element source span is invalid")
        aliases.add(alias)


def _validate_local_call_runs(runs: tuple[dict[str, object], ...]) -> None:
    expected = {
        "runId",
        "typeKey",
        "componentTag",
        "sourceStart",
        "sourceEnd",
        "loopSourceStart",
        "loopSourceEnd",
        "collectionExpression",
        "idExpression",
        "keyExpression",
    }
    seen: set[str] = set()
    for run in runs:
        if type(run) is not dict or set(run) != expected:
            raise ValueError("local call-run metadata has an invalid shape")
        run_id = run["runId"]
        if type(run_id) is not str or re.fullmatch(r"citryRun[0-9]+", run_id) is None or run_id in seen:
            raise ValueError("local call-run id is invalid or duplicated")
        seen.add(run_id)
        if any(type(run[key]) is not str or not run[key] for key in ("typeKey", "componentTag")):
            raise ValueError("local call-run component identity is invalid")
        spans: list[int] = []
        for key in ("sourceStart", "sourceEnd", "loopSourceStart", "loopSourceEnd"):
            span_value = run[key]
            # Collected as exact integers so the ordering checks below compare
            # offsets rather than whatever the record happened to carry.
            if type(span_value) is not int or span_value < 0:
                raise ValueError("local call-run source spans are invalid")
            spans.append(span_value)
        source_start, source_end, loop_start, loop_end = spans
        if not (loop_start == source_start and loop_end == source_end and source_start < source_end):
            raise ValueError("local call-run source spans are not ordered")
        if run["collectionExpression"] != f"preparedData.callRuns.{run_id}":
            raise ValueError("local call-run collection expression is invalid")
        if run["idExpression"] != "citryOccurrenceId":
            raise ValueError("local call-run id expression is invalid")
        if run["keyExpression"] != "citryOccurrenceId":
            raise ValueError("local call-run key expression is invalid")


def _validate_local_calls(calls: tuple[dict[str, object], ...]) -> None:
    seen: set[str] = set()
    for call in calls:
        if type(call) is not dict or set(call) != {"localId", "typeKey", "componentTag", "bindings"}:
            raise ValueError("local call metadata has an invalid shape")
        local_id = call["localId"]
        if type(local_id) is not str or re.fullmatch(r"citryCall[0-9A-Za-z]+", local_id) is None:
            raise ValueError("local call id is invalid")
        if local_id in seen:
            raise ValueError("local call id is duplicated")
        seen.add(local_id)
        if any(type(call[key]) is not str or not call[key] for key in ("typeKey", "componentTag")):
            raise ValueError("local call component identity is invalid")
        bindings = call["bindings"]
        if type(bindings) is not list:
            raise ValueError("local call bindings are invalid")
        for binding in bindings:
            if type(binding) is not dict or set(binding) != {"kind", "name", "value", "sourceStart", "sourceEnd"}:
                raise ValueError("local call binding has an invalid shape")
            if binding["kind"] not in {
                "prop",
                "props-object",
                "events-object",
                "event",
                "ref-static",
                "ref-expression",
            }:
                raise ValueError("local call binding kind is invalid")
            if any(type(binding[key]) is not str for key in ("name", "value")):
                raise ValueError("local call binding text is invalid")
            if any(type(binding[key]) is not int or binding[key] < 0 for key in ("sourceStart", "sourceEnd")):
                raise ValueError("local call binding span is invalid")
            if binding["sourceEnd"] <= binding["sourceStart"]:
                raise ValueError("local call binding span is not ordered")
