"""Bounded project discovery and server-side registry state."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from citry import TemplateAnalysis
from citry_lsp.catalog import CatalogIndex
from citry_lsp.environment import EnvironmentFileError, worker_environment
from citry_lsp.protocol import (
    CATALOG_SCHEMA_VERSION,
    SUPPORTED_CITRY_SERIES,
    ProjectStatus,
)

if TYPE_CHECKING:
    from citry_lsp.catalog import ComponentRecord

WORKER_TIMEOUT_SECONDS = 5.0
_SOURCE_ANALYSIS_VERSION = 1
_I18N_ANALYSIS_VERSION = 2


@dataclass(frozen=True, slots=True)
class I18nDefinitionRecord:
    """One compiler-proven source definition in UTF-8 catalog coordinates."""

    path: str
    start: int
    end: int
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class I18nParameterDeclarationRecord:
    """One exact source comment that declares a message parameter."""

    path: str
    start: int
    end: int
    line: int
    column: int
    description: str | None
    annotated: bool


@dataclass(frozen=True, slots=True)
class I18nParameterRecord:
    """One effective typed input and its source declarations."""

    name: str
    type_name: str
    direct: bool
    declarations: tuple[I18nParameterDeclarationRecord, ...]

    @property
    def descriptions(self) -> tuple[str, ...]:
        """Return distinct translator-facing descriptions in source order."""
        return tuple(
            dict.fromkeys(declaration.description for declaration in self.declarations if declaration.description)
        )


@dataclass(frozen=True, slots=True)
class I18nOutputRecord:
    """One public message value or attribute from the checked catalog graph."""

    token: str
    message: str
    attribute: str | None
    owner: str
    definition: I18nDefinitionRecord
    parameters: tuple[I18nParameterRecord, ...]


@dataclass(frozen=True, slots=True)
class I18nReferenceRecord:
    """One compiler-proven public Fluent message reference."""

    path: str
    start: int
    end: int
    token: str


class I18nProjectIndex:
    """Validated i18n facts copied out of the disposable app worker."""

    __slots__ = ("available", "configured", "locales", "outputs", "profiles", "references", "revision")
    available: bool
    configured: bool
    locales: tuple[str, ...]
    outputs: dict[str, I18nOutputRecord]
    profiles: dict[str, dict[str, tuple[str, ...]]]
    references: tuple[I18nReferenceRecord, ...]
    revision: str | None

    def __init__(self, payload: object) -> None:
        if type(payload) is not dict:
            raise ValueError("i18n analysis envelope is invalid")
        if payload.get("version") != _I18N_ANALYSIS_VERSION:
            raise ValueError(f"i18n analysis version {payload.get('version')!r} is unsupported")
        configured = payload.get("configured")
        if type(configured) is not bool:
            raise ValueError("i18n analysis configured flag is invalid")
        available = payload.get("available")
        if type(available) is not bool:
            raise ValueError("i18n analysis available flag is invalid")
        self.configured = configured
        self.available = available
        if not available:
            if configured:
                raise ValueError("configured i18n analysis cannot be unavailable")
            if set(payload) != {"version", "available", "configured"}:
                raise ValueError("unavailable i18n analysis has unexpected fields")
            self.revision = None
            self.locales = ()
            self.outputs = {}
            self.references = ()
            self.profiles = {"format": {}, "parse": {}}
            return
        if set(payload) != {
            "version",
            "available",
            "configured",
            "revision",
            "locales",
            "outputs",
            "references",
            "profiles",
        }:
            raise ValueError("available i18n analysis has unexpected fields")
        revision = payload.get("revision")
        locales = payload.get("locales")
        raw_outputs = payload.get("outputs")
        raw_references = payload.get("references")
        raw_profiles = payload.get("profiles")
        if type(revision) is not str or not revision:
            raise ValueError("i18n analysis revision is invalid")
        if type(locales) is not list or not locales or any(type(item) is not str or not item for item in locales):
            raise ValueError("i18n analysis locales are invalid")
        if type(raw_outputs) is not list:
            raise ValueError("i18n analysis outputs must be a list")
        if type(raw_references) is not list:
            raise ValueError("i18n analysis references must be a list")
        self.revision = revision
        self.locales = tuple(cast("list[str]", locales))
        outputs: dict[str, I18nOutputRecord] = {}
        for raw_output in raw_outputs:
            output = _i18n_output(raw_output)
            if output.token in outputs:
                raise ValueError(f"duplicate i18n output {output.token!r}")
            outputs[output.token] = output
        self.outputs = outputs
        self.references = tuple(_i18n_reference(item) for item in raw_references)
        self.profiles = _i18n_profiles(raw_profiles)

    def message_ids(self) -> tuple[str, ...]:
        """Return every public message ID in deterministic order."""
        return tuple(sorted({output.message for output in self.outputs.values()}))

    def output(self, message: str, attribute: str | None = None) -> I18nOutputRecord | None:
        """Return one checked main value or attribute."""
        token = message if attribute is None else f"{message}.{attribute}"
        return self.outputs.get(token)

    def profile_names(self, namespace: str, operation: str) -> tuple[str, ...]:
        """Return checked profile names for one formatter or parser operation."""
        return self.profiles.get(namespace, {}).get(operation, ())


def _i18n_output(payload: object) -> I18nOutputRecord:
    if type(payload) is not dict or set(payload) != {
        "token",
        "message",
        "attribute",
        "owner",
        "definition",
        "interface",
    }:
        raise ValueError("i18n output metadata is invalid")
    token = payload.get("token")
    message = payload.get("message")
    attribute = payload.get("attribute")
    owner = payload.get("owner")
    if type(token) is not str or not token or type(message) is not str or not message:
        raise ValueError("i18n output name is invalid")
    if attribute is not None and (type(attribute) is not str or not attribute):
        raise ValueError("i18n output attribute is invalid")
    expected_token = message if attribute is None else f"{message}.{attribute}"
    if token != expected_token or type(owner) is not str or not owner:
        raise ValueError("i18n output identity is invalid")
    definition = _i18n_definition(payload.get("definition"))
    raw_interface = payload.get("interface")
    if type(raw_interface) is not dict:
        raise ValueError("i18n output interface is invalid")
    parameters = tuple(
        _i18n_parameter(name, metadata) for name, metadata in sorted(raw_interface.items()) if type(name) is str
    )
    if len(parameters) != len(raw_interface):
        raise ValueError("i18n output parameter name is invalid")
    return I18nOutputRecord(token, message, cast("str | None", attribute), owner, definition, parameters)


def _i18n_definition(payload: object) -> I18nDefinitionRecord:
    if type(payload) is not dict or set(payload) != {"path", "start", "end", "line", "column"}:
        raise ValueError("i18n definition metadata is invalid")
    path = payload.get("path")
    start = payload.get("start")
    end = payload.get("end")
    line = payload.get("line")
    column = payload.get("column")
    if type(path) is not str or not path:
        raise ValueError("i18n definition path is invalid")
    if not all(type(item) is int for item in (start, end, line, column)):
        raise ValueError("i18n definition range is invalid")
    start = cast("int", start)
    end = cast("int", end)
    line = cast("int", line)
    column = cast("int", column)
    if min(start, end, line, column) < 0 or end <= start:
        raise ValueError("i18n definition range is invalid")
    return I18nDefinitionRecord(path, start, end, line, column)


def _i18n_reference(payload: object) -> I18nReferenceRecord:
    if type(payload) is not dict or set(payload) != {"path", "start", "end", "token"}:
        raise ValueError("i18n reference metadata is invalid")
    path = payload.get("path")
    start = payload.get("start")
    end = payload.get("end")
    token = payload.get("token")
    if type(path) is not str or not path or type(token) is not str or not token:
        raise ValueError("i18n reference identity is invalid")
    if type(start) is not int or type(end) is not int or start < 0 or end <= start:
        raise ValueError("i18n reference range is invalid")
    return I18nReferenceRecord(path, start, end, token)


def _i18n_parameter(name: object, payload: object) -> I18nParameterRecord:
    if type(name) is not str or not name or type(payload) is not dict:
        raise ValueError("i18n parameter metadata is invalid")
    if set(payload) != {"type_name", "direct", "declarations"}:
        raise ValueError("i18n parameter metadata has unexpected fields")
    type_name = payload.get("type_name")
    direct = payload.get("direct")
    declarations = payload.get("declarations")
    if type(type_name) is not str or not type_name or type(direct) is not bool or type(declarations) is not list:
        raise ValueError("i18n parameter metadata is invalid")
    validated_declarations: list[I18nParameterDeclarationRecord] = []
    for declaration in declarations:
        if type(declaration) is not dict or set(declaration) != {
            "path",
            "start",
            "end",
            "line",
            "column",
            "description",
            "annotated",
        }:
            raise ValueError("i18n parameter declaration is invalid")
        path = declaration.get("path")
        start = declaration.get("start")
        end = declaration.get("end")
        line = declaration.get("line")
        column = declaration.get("column")
        description = declaration.get("description")
        annotated = declaration.get("annotated")
        if (
            type(path) is not str
            or not path
            or type(start) is not int
            or type(end) is not int
            or type(line) is not int
            or type(column) is not int
            or min(start, end, line, column) < 0
            or end <= start
            or type(annotated) is not bool
        ):
            raise ValueError("i18n parameter declaration is invalid")
        if description is not None and type(description) is not str:
            raise ValueError("i18n parameter description is invalid")
        validated_declarations.append(
            I18nParameterDeclarationRecord(
                path,
                start,
                end,
                line,
                column,
                cast("str | None", description),
                annotated,
            )
        )
    return I18nParameterRecord(name, type_name, direct, tuple(validated_declarations))


def _i18n_profiles(payload: object) -> dict[str, dict[str, tuple[str, ...]]]:
    if type(payload) is not dict or set(payload) != {"format", "parse"}:
        raise ValueError("i18n profile metadata is invalid")
    result: dict[str, dict[str, tuple[str, ...]]] = {}
    for namespace in ("format", "parse"):
        raw_namespace = payload.get(namespace)
        if type(raw_namespace) is not dict:
            raise ValueError(f"i18n {namespace} profile metadata is invalid")
        operations: dict[str, tuple[str, ...]] = {}
        for operation, names in raw_namespace.items():
            if type(operation) is not str or not operation or type(names) is not list:
                raise ValueError(f"i18n {namespace} profile metadata is invalid")
            if any(type(name) is not str or not name for name in names) or len(names) != len(set(names)):
                raise ValueError(f"i18n {namespace} profile names are invalid")
            operations[operation] = tuple(cast("list[str]", names))
        result[namespace] = operations
    return result


@dataclass(frozen=True, slots=True)
class SourceClassRecord:
    """One class in a statically copied Python method-resolution chain."""

    module: str
    qualname: str
    source_file: Path
    resolution: str


@dataclass(frozen=True, slots=True)
class SourceLintRecord:
    """One direct authored lint-variable mapping copied by the app worker."""

    name: str
    kind: Literal["application", "component"]
    owner: str
    source_file: Path


@dataclass(frozen=True, slots=True)
class SourceEventRecord:
    """One effective server-event handler copied from the worker."""

    name: str
    method_name: str
    module: str
    qualname: str
    source_file: Path


@dataclass(frozen=True, slots=True)
class SourceStateFieldRecord:
    """One public Events State field copied from the worker."""

    name: str
    type_display: str | None
    description: str | None
    module: str
    qualname: str
    source_file: Path


class SourceAnalysisIndex:
    """Validated private worker provenance keyed by component generation."""

    __slots__ = (
        "_css_asset",
        "_css_data",
        "_events",
        "_js_asset",
        "_js_data",
        "_state",
        "_template_asset",
        "_template_data",
        "_template_lint",
    )

    def __init__(self, payload: object, catalog: CatalogIndex) -> None:
        if type(payload) is not dict or set(payload) != {"version", "components"}:
            raise ValueError("source analysis envelope is invalid")
        if payload.get("version") != _SOURCE_ANALYSIS_VERSION:
            raise ValueError(f"source analysis version {payload.get('version')!r} is unsupported")
        raw_components = payload.get("components")
        if type(raw_components) is not list:
            raise ValueError("source analysis components must be a list")
        template_data: dict[str, tuple[SourceClassRecord, ...] | None] = {}
        css_data: dict[str, tuple[SourceClassRecord, ...] | None] = {}
        js_data: dict[str, tuple[SourceClassRecord, ...] | None] = {}
        template_asset: dict[str, tuple[SourceClassRecord, ...] | None] = {}
        css_asset: dict[str, tuple[SourceClassRecord, ...] | None] = {}
        js_asset: dict[str, tuple[SourceClassRecord, ...] | None] = {}
        events: dict[str, tuple[SourceEventRecord, ...] | None] = {}
        state: dict[str, tuple[SourceStateFieldRecord, ...] | None] = {}
        template_lint: dict[str, dict[str, SourceLintRecord]] = {}
        for raw_component in raw_components:
            (
                definition_id,
                data_chain,
                css_data_chain,
                js_data_chain,
                asset_chain,
                css_asset_chain,
                js_asset_chain,
                event_handlers,
                state_fields,
                lint_variables,
            ) = _source_component(raw_component)
            if definition_id in template_data:
                raise ValueError(f"duplicate source analysis definition id {definition_id!r}")
            template_data[definition_id] = data_chain
            css_data[definition_id] = css_data_chain
            js_data[definition_id] = js_data_chain
            template_asset[definition_id] = asset_chain
            css_asset[definition_id] = css_asset_chain
            js_asset[definition_id] = js_asset_chain
            events[definition_id] = event_handlers
            state[definition_id] = state_fields
            template_lint[definition_id] = lint_variables
        expected = {component.definition_id for component in catalog.components}
        if set(template_data) != expected:
            raise ValueError("source analysis definition ids do not match the component catalog")
        self._template_data = template_data
        self._css_data = css_data
        self._js_data = js_data
        self._template_asset = template_asset
        self._css_asset = css_asset
        self._js_asset = js_asset
        self._events = events
        self._state = state
        self._template_lint = template_lint

    def template_data_chain(self, component: ComponentRecord) -> tuple[SourceClassRecord, ...] | None:
        """Return copied provenance for one exact catalog component."""
        return self._template_data.get(component.definition_id)

    def template_asset_chain(self, component: ComponentRecord) -> tuple[SourceClassRecord, ...] | None:
        """Return concrete-to-owner provenance for the effective template asset."""
        return self._template_asset.get(component.definition_id)

    def css_data_chain(self, component: ComponentRecord) -> tuple[SourceClassRecord, ...] | None:
        """Return copied provenance for the effective ``css_data`` method."""
        return self._css_data.get(component.definition_id)

    def css_asset_chain(self, component: ComponentRecord) -> tuple[SourceClassRecord, ...] | None:
        """Return concrete-to-owner provenance for the effective CSS asset."""
        return self._css_asset.get(component.definition_id)

    def js_data_chain(self, component: ComponentRecord) -> tuple[SourceClassRecord, ...] | None:
        """Return copied provenance for the effective ``js_data`` method."""
        return self._js_data.get(component.definition_id)

    def js_asset_chain(self, component: ComponentRecord) -> tuple[SourceClassRecord, ...] | None:
        """Return concrete-to-owner provenance for the effective JS asset."""
        return self._js_asset.get(component.definition_id)

    def event_handlers(self, component: ComponentRecord) -> tuple[SourceEventRecord, ...] | None:
        """Return exact effective server-event handler origins."""
        return self._events.get(component.definition_id)

    def state_fields(self, component: ComponentRecord) -> tuple[SourceStateFieldRecord, ...] | None:
        """Return public browser-visible State fields with authored origins."""
        return self._state.get(component.definition_id)

    def template_lint_definition(self, component: ComponentRecord, name: str) -> SourceLintRecord | None:
        """Return a direct lint-variable mapping for one exact component."""
        return self._template_lint.get(component.definition_id, {}).get(name)


def _source_component(
    value: object,
) -> tuple[
    str,
    tuple[SourceClassRecord, ...] | None,
    tuple[SourceClassRecord, ...] | None,
    tuple[SourceClassRecord, ...] | None,
    tuple[SourceClassRecord, ...] | None,
    tuple[SourceClassRecord, ...] | None,
    tuple[SourceClassRecord, ...] | None,
    tuple[SourceEventRecord, ...] | None,
    tuple[SourceStateFieldRecord, ...] | None,
    dict[str, SourceLintRecord],
]:
    if type(value) is not dict or set(value) != {
        "definition_id",
        "css_data",
        "css_asset",
        "js_data",
        "js_asset",
        "events",
        "template_data",
        "template_asset",
        "template_lint",
    }:
        raise ValueError("source analysis component entry is invalid")
    definition_id = value.get("definition_id")
    if type(definition_id) is not str or not definition_id:
        raise ValueError("source analysis definition id must be a non-empty string")
    return (
        definition_id,
        _source_resolution_chain(value.get("template_data"), definition_id, "template_data"),
        _source_resolution_chain(value.get("css_data"), definition_id, "css_data"),
        _source_resolution_chain(value.get("js_data"), definition_id, "js_data"),
        _source_resolution_chain(value.get("template_asset"), definition_id, "template_asset"),
        _source_resolution_chain(value.get("css_asset"), definition_id, "css_asset"),
        _source_resolution_chain(value.get("js_asset"), definition_id, "js_asset"),
        *_source_event_info(value.get("events"), definition_id),
        _source_lint_variables(value.get("template_lint"), definition_id),
    )


def _source_event_info(
    value: object,
    definition_id: str,
) -> tuple[tuple[SourceEventRecord, ...] | None, tuple[SourceStateFieldRecord, ...] | None]:
    if type(value) is not dict or set(value) != {"handlers", "state"}:
        raise ValueError(f"source analysis for {definition_id!r} has invalid events metadata")
    raw_handlers = value.get("handlers")
    raw_state = value.get("state")
    if raw_handlers is not None and type(raw_handlers) is not list:
        raise ValueError(f"source analysis for {definition_id!r} has invalid event handlers")
    handlers: list[SourceEventRecord] = []
    names: set[str] = set()
    for raw_handler in raw_handlers or []:
        if type(raw_handler) is not dict or set(raw_handler) != {
            "name",
            "method_name",
            "module",
            "qualname",
            "file",
        }:
            raise ValueError(f"source analysis for {definition_id!r} has an invalid event handler")
        name = raw_handler.get("name")
        method_name = raw_handler.get("method_name")
        module = raw_handler.get("module")
        qualname = raw_handler.get("qualname")
        source_file = raw_handler.get("file")
        if any(type(item) is not str or not item for item in (name, method_name, module, qualname, source_file)):
            raise ValueError(f"source analysis for {definition_id!r} has empty event provenance")
        name = cast("str", name)
        method_name = cast("str", method_name)
        module = cast("str", module)
        qualname = cast("str", qualname)
        source_file = cast("str", source_file)
        if name in names:
            raise ValueError(f"source analysis for {definition_id!r} has duplicate event names")
        path = Path(source_file)
        if not path.is_absolute():
            raise ValueError(f"source analysis for {definition_id!r} has a relative event source")
        names.add(name)
        handlers.append(SourceEventRecord(name, method_name, module, qualname, path.resolve()))
    if raw_state is not None and type(raw_state) is not list:
        raise ValueError(f"source analysis for {definition_id!r} has invalid State fields")
    state_fields: list[SourceStateFieldRecord] = []
    state_names: set[str] = set()
    for raw_field in raw_state or []:
        if type(raw_field) is not dict or set(raw_field) != {
            "name",
            "type_display",
            "description",
            "module",
            "qualname",
            "file",
        }:
            raise ValueError(f"source analysis for {definition_id!r} has an invalid State field")
        field_name = raw_field.get("name")
        type_display = raw_field.get("type_display")
        description = raw_field.get("description")
        field_module = raw_field.get("module")
        field_qualname = raw_field.get("qualname")
        field_file = raw_field.get("file")
        if (
            type(field_name) is not str
            or not field_name
            or (type_display is not None and type(type_display) is not str)
            or (description is not None and type(description) is not str)
            or type(field_module) is not str
            or not field_module
            or type(field_qualname) is not str
            or not field_qualname
            or type(field_file) is not str
            or not field_file
        ):
            raise ValueError(f"source analysis for {definition_id!r} has invalid State provenance")
        if field_name in state_names:
            raise ValueError(f"source analysis for {definition_id!r} has duplicate State fields")
        path = Path(field_file)
        if not path.is_absolute():
            raise ValueError(f"source analysis for {definition_id!r} has a relative State source")
        state_names.add(field_name)
        state_fields.append(
            SourceStateFieldRecord(
                field_name,
                type_display,
                description,
                field_module,
                field_qualname,
                path.resolve(),
            )
        )
    return (
        tuple(handlers) if raw_handlers is not None else None,
        tuple(state_fields) if raw_state is not None else None,
    )


def _source_lint_variables(value: object, definition_id: str) -> dict[str, SourceLintRecord]:
    """Validate direct source locators without trusting worker paths implicitly."""
    if type(value) is not dict or set(value) != {"variables"}:
        raise ValueError(f"source analysis for {definition_id!r} has invalid template_lint metadata")
    raw_variables = value.get("variables")
    if type(raw_variables) is not list:
        raise ValueError(f"source analysis for {definition_id!r} has invalid template_lint variables")
    variables: dict[str, SourceLintRecord] = {}
    for raw_variable in raw_variables:
        if type(raw_variable) is not dict or set(raw_variable) != {"name", "kind", "owner", "file"}:
            raise ValueError(f"source analysis for {definition_id!r} has an invalid lint variable")
        name = raw_variable.get("name")
        kind = raw_variable.get("kind")
        owner = raw_variable.get("owner")
        source_file = raw_variable.get("file")
        if type(name) is not str or not name or type(owner) is not str or not owner:
            raise ValueError(f"source analysis for {definition_id!r} has empty lint provenance")
        if kind not in {"application", "component"}:
            raise ValueError(f"source analysis for {definition_id!r} has an unknown lint origin")
        if type(source_file) is not str:
            raise ValueError(f"source analysis for {definition_id!r} has an invalid lint source file")
        path = Path(source_file)
        if not path.is_absolute():
            raise ValueError(f"source analysis for {definition_id!r} has a relative lint source path")
        if name in variables:
            raise ValueError(f"source analysis for {definition_id!r} has a duplicate lint variable")
        variables[name] = SourceLintRecord(name, cast("Literal['application', 'component']", kind), owner, path)
    return variables


def _source_resolution_chain(
    metadata: object,
    definition_id: str,
    kind: str,
) -> tuple[SourceClassRecord, ...] | None:
    """Validate one private concrete-to-owner class chain."""
    if type(metadata) is not dict or set(metadata) != {"resolution_chain"}:
        raise ValueError(f"source analysis for {definition_id!r} has invalid {kind} metadata")
    raw_chain = metadata.get("resolution_chain")
    if raw_chain is None:
        return None
    if type(raw_chain) is not list or not raw_chain:
        raise ValueError(f"source analysis for {definition_id!r} has an invalid {kind} resolution chain")
    chain: list[SourceClassRecord] = []
    for raw_class in raw_chain:
        if type(raw_class) is not dict or set(raw_class) != {"module", "qualname", "file", "resolution"}:
            raise ValueError(f"source analysis for {definition_id!r} has an invalid class record")
        module = raw_class.get("module")
        qualname = raw_class.get("qualname")
        source_file = raw_class.get("file")
        resolution = raw_class.get("resolution")
        if any(type(item) is not str or not item for item in (module, qualname, source_file, resolution)):
            raise ValueError(f"source analysis for {definition_id!r} has empty class provenance")
        module = cast("str", module)
        qualname = cast("str", qualname)
        path = Path(cast("str", source_file))
        if not path.is_absolute():
            raise ValueError(f"source analysis for {definition_id!r} has a relative source path")
        chain.append(SourceClassRecord(module, qualname, path, cast("str", resolution)))
    return tuple(chain)


@dataclass(frozen=True, slots=True)
class ProjectState:
    """One immutable project-analysis generation."""

    status: ProjectStatus
    analysis: TemplateAnalysis | None = None
    catalog: CatalogIndex | None = None
    source_analysis: SourceAnalysisIndex | None = None
    i18n: I18nProjectIndex | None = None
    security_csp: Literal["off", "warn", "strict"] | None = None
    _slot_data_fields: dict[str, dict[str, tuple[str, ...]]] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Index portable slot-data rules once for completion and hover."""
        indexed: dict[str, dict[str, tuple[str, ...]]] = {}
        if self.analysis is not None:
            raw_rules = self.analysis.to_dict().get("tag_rules")
            if type(raw_rules) is dict:
                for tag_name, raw_rule in raw_rules.items():
                    if type(tag_name) is not str or type(raw_rule) is not dict:
                        continue
                    raw_slots = raw_rule.get("slot_data_fields")
                    if type(raw_slots) is not dict:
                        continue
                    slots: dict[str, tuple[str, ...]] = {}
                    for slot_name, raw_fields in raw_slots.items():
                        if (
                            type(slot_name) is str
                            and type(raw_fields) is list
                            and all(type(item) is str for item in raw_fields)
                        ):
                            slots[slot_name] = tuple(raw_fields)
                    indexed[tag_name.lower()] = slots
        object.__setattr__(self, "_slot_data_fields", indexed)

    def component_slot_data_fields(
        self,
        component: ComponentRecord,
        slot_name: str,
    ) -> tuple[str, ...] | None:
        """Return a known slot-data field set, preserving known empty shapes."""
        for registered_name in component.registered_names:
            slots = self._slot_data_fields.get(f"c-{registered_name}".lower())
            if slots is not None and slot_name in slots:
                return slots[slot_name]
        return None


def load_project(
    workspace: Path,
    app: str | None,
    *,
    environment_file: Path | None = None,
    timeout: float = WORKER_TIMEOUT_SECONDS,
) -> ProjectState:
    """Load registry facts through a bounded worker or select syntax-only mode."""
    workspace = workspace.resolve()
    if app is None:
        return _syntax_only_project(workspace, environment_file)
    try:
        environment = worker_environment(environment_file)
    except EnvironmentFileError as exc:
        return _failure(
            workspace, app, _environment_file_failure(environment_file, exc), environment_file=environment_file
        )
    command = [
        sys.executable,
        "-m",
        "citry_lsp.app_worker",
        "--app",
        app,
        "--workspace",
        str(workspace),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=workspace,
            capture_output=True,
            check=False,
            env=environment,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return _failure(
            workspace,
            app,
            f"App discovery exceeded the {timeout:g}s startup limit.",
            environment_file=environment_file,
        )
    return _project_from_worker_output(
        workspace,
        app,
        completed.returncode,
        completed.stdout,
        completed.stderr,
        environment_file=environment_file,
    )


async def load_project_async(
    workspace: Path,
    app: str | None,
    *,
    environment_file: Path | None = None,
    timeout: float = WORKER_TIMEOUT_SECONDS,
) -> ProjectState:
    """
    Load a project without blocking the language-server event loop.

    The one-shot worker remains the only process that imports project code.
    Cancellation kills and reaps that worker before it reaches the caller, so
    an editor shutdown or superseded reload cannot leave discovery children
    behind.
    """
    workspace = workspace.resolve()
    if app is None:
        return _syntax_only_project(workspace, environment_file)
    try:
        environment = await asyncio.to_thread(worker_environment, environment_file)
    except EnvironmentFileError as exc:
        return _failure(
            workspace, app, _environment_file_failure(environment_file, exc), environment_file=environment_file
        )
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "citry_lsp.app_worker",
        "--app",
        app,
        "--workspace",
        str(workspace),
        cwd=workspace,
        env=environment,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
    except asyncio.TimeoutError:
        await _reap_project_worker(process)
        return _failure(
            workspace,
            app,
            f"App discovery exceeded the {timeout:g}s startup limit.",
            environment_file=environment_file,
        )
    except asyncio.CancelledError:
        await _reap_project_worker_cancellation_safe(process)
        raise
    return _project_from_worker_output(
        workspace,
        app,
        process.returncode,
        stdout.decode(errors="replace"),
        stderr.decode(errors="replace"),
        environment_file=environment_file,
    )


def _syntax_only_project(workspace: Path, environment_file: Path | None = None) -> ProjectState:
    return ProjectState(
        ProjectStatus(
            interpreter=sys.executable,
            workspace=str(workspace),
            environment_file=_environment_file_status(environment_file),
            mode="syntax-only",
            message="No Citry app configured; registry-derived checks and editor features are disabled.",
        )
    )


def _project_from_worker_output(
    workspace: Path,
    app: str,
    returncode: int | None,
    stdout: str,
    stderr: str,
    *,
    environment_file: Path | None = None,
) -> ProjectState:
    """Validate one completed worker response for sync and async callers."""
    if not stdout.strip():
        detail = stderr.strip()
        message = f"App worker exited with status {returncode} without a response."
        if detail:
            message = f"{message} {detail[:1000]}"
        return _failure(workspace, app, message, environment_file=environment_file)
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return _failure(
            workspace,
            app,
            f"App worker returned invalid JSON: {exc}",
            environment_file=environment_file,
        )
    if type(payload) is not dict or payload.get("ok") is not True:
        worker_detail: object = payload.get("error") if type(payload) is dict else None
        message = str(worker_detail or f"App worker exited with status {returncode}.")
        return _failure(workspace, app, message, environment_file=environment_file)
    # The target kind changes what the copied registry can claim, so status
    # must carry that boundary even though both paths provide registry facts.
    try:
        target_message = _target_status_message(payload.get("target"))
    except (TypeError, ValueError) as exc:
        return _failure(workspace, app, f"App worker protocol mismatch: {exc}", environment_file=environment_file)
    raw_catalog = payload.get("catalog")
    if type(raw_catalog) is dict:
        raw_schema_version = raw_catalog.get("schema_version")
        if type(raw_schema_version) is int and raw_schema_version != CATALOG_SCHEMA_VERSION:
            raw_citry_version = raw_catalog.get("citry_version")
            return _failure(
                workspace,
                app,
                f"Component catalog schema {raw_schema_version} is unsupported.",
                environment_file=environment_file,
                citry_version=raw_citry_version if type(raw_citry_version) is str else None,
                catalog_schema_version=raw_schema_version,
            )
    try:
        analysis = TemplateAnalysis.from_dict(payload.get("analysis"))
        catalog = CatalogIndex(raw_catalog)
        lint_ids = set(analysis.component_lint)
        catalog_ids = {component.definition_id for component in catalog.components}
        if lint_ids != catalog_ids:
            msg = "template lint component ids do not match the component catalog"
            raise ValueError(msg)
    except (TypeError, ValueError) as exc:
        return _failure(workspace, app, f"App worker protocol mismatch: {exc}", environment_file=environment_file)
    series = _version_series(catalog.citry_version)
    if series != SUPPORTED_CITRY_SERIES:
        expected = ".".join(str(part) for part in SUPPORTED_CITRY_SERIES)
        return _failure(
            workspace,
            app,
            f"Citry {catalog.citry_version} is outside this server's supported {expected}.x series.",
            environment_file=environment_file,
            citry_version=catalog.citry_version,
            catalog_schema_version=catalog.schema_version,
        )
    if catalog.schema_version != CATALOG_SCHEMA_VERSION:
        return _failure(
            workspace,
            app,
            f"Component catalog schema {catalog.schema_version} is unsupported.",
            environment_file=environment_file,
            citry_version=catalog.citry_version,
            catalog_schema_version=catalog.schema_version,
        )
    try:
        source_analysis = SourceAnalysisIndex(payload.get("source_analysis"), catalog)
        raw_extensions = payload.get("extensions")
        if type(raw_extensions) is not dict or set(raw_extensions) != {"i18n"}:
            raise ValueError("extension analysis envelope is invalid")
        i18n = I18nProjectIndex(raw_extensions.get("i18n"))
        raw_settings = payload.get("engine_settings")
        if type(raw_settings) is not dict or set(raw_settings) != {"version", "security_csp"}:
            raise ValueError("engine settings envelope is invalid")
        if raw_settings.get("version") != 1:
            raise ValueError("engine settings version is unsupported")
        security_csp = raw_settings.get("security_csp")
        if type(security_csp) is not str or security_csp not in {"off", "warn", "strict"}:
            raise ValueError("engine security_csp setting is invalid")
    except (TypeError, ValueError) as exc:
        return _failure(workspace, app, f"App worker protocol mismatch: {exc}", environment_file=environment_file)
    project_output = payload.get("project_output")
    # Preserve both the registry boundary and captured import output instead
    # of letting one useful status message hide the other.
    status_messages = [target_message] if target_message is not None else []
    if project_output:
        status_messages.append(f"Project output was captured during discovery: {project_output}")
    status_message = " ".join(status_messages) or None
    return ProjectState(
        ProjectStatus(
            interpreter=sys.executable,
            workspace=str(workspace),
            app=app,
            environment_file=_environment_file_status(environment_file),
            mode="registry",
            registry_ready=True,
            citry_version=catalog.citry_version,
            catalog_schema_version=catalog.schema_version,
            message=status_message,
        ),
        analysis=analysis,
        catalog=catalog,
        source_analysis=source_analysis,
        i18n=i18n,
        security_csp=cast("Literal['off', 'warn', 'strict']", security_csp),
    )


async def _reap_project_worker(process: asyncio.subprocess.Process) -> None:
    """Terminate and reap a disposable app-discovery worker."""
    if process.returncode is None:
        with suppress(ProcessLookupError, PermissionError):
            process.kill()
    try:
        await process.communicate()
    except (BrokenPipeError, ConnectionResetError, ProcessLookupError):
        await process.wait()


async def _reap_project_worker_cancellation_safe(process: asyncio.subprocess.Process) -> None:
    """Finish worker ownership cleanup even under repeated cancellation."""
    reaping = asyncio.create_task(_reap_project_worker(process))
    cancellation: asyncio.CancelledError | None = None
    while not reaping.done():
        try:
            await asyncio.shield(reaping)
        except asyncio.CancelledError as exc:
            cancellation = exc
    await reaping
    if cancellation is not None:
        raise cancellation


def _failure(
    workspace: Path,
    app: str,
    message: str,
    *,
    environment_file: Path | None = None,
    citry_version: str | None = None,
    catalog_schema_version: int | None = None,
) -> ProjectState:
    return ProjectState(
        ProjectStatus(
            interpreter=sys.executable,
            workspace=str(workspace),
            app=app,
            environment_file=_environment_file_status(environment_file),
            mode="syntax-only",
            registry_ready=False,
            citry_version=citry_version,
            catalog_schema_version=catalog_schema_version,
            message=f"App unavailable; using syntax-only analysis. {message}",
        )
    )


def _environment_file_status(environment_file: Path | None) -> str | None:
    return str(environment_file) if environment_file is not None else None


def _environment_file_failure(environment_file: Path | None, error: EnvironmentFileError) -> str:
    path = _environment_file_status(environment_file) or "the configured path"
    return f"Environment file {path!r} is unavailable: {error}."


def _target_status_message(value: object) -> str | None:
    """Describe when the worker copied a library rather than a host app."""
    if type(value) is not dict:
        raise TypeError("target metadata must be an object")
    kind = value.get("kind")
    if kind == "citry":
        if set(value) != {"kind"}:
            raise ValueError("Citry target metadata contains unsupported fields")
        return None
    if kind != "component-library":
        raise ValueError(f"target kind {kind!r} is unsupported")
    name = value.get("name")
    if type(name) is not str or not name:
        raise TypeError("component-library target name must be a non-empty string")
    if set(value) != {"kind", "name"}:
        raise ValueError("component-library target metadata contains unsupported fields")
    return (
        f"Component library {name!r} loaded with Citry's built-ins in library-only registry mode; "
        "host-app components, configuration, and host-provided extensions are not included."
    )


def _version_series(version: str) -> tuple[int, int] | None:
    try:
        major, minor, *_ = version.split(".")
        return int(major), int(minor)
    except (TypeError, ValueError):
        return None


__all__ = [
    "WORKER_TIMEOUT_SECONDS",
    "ProjectState",
    "SourceAnalysisIndex",
    "SourceClassRecord",
    "load_project",
    "load_project_async",
]
