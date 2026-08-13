"""Conservative authored-template analysis for ``citry check``."""

from __future__ import annotations

import ast
import json
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

from citry._app_selection import CheckAppSelection, app_failure_message
from citry._class_introspection import (
    _safe_class_import_path,
    _safe_class_text,
    _static_class_dict,
    _static_class_mro,
)
from citry._component_introspection import _loaded_python_file
from citry._diagnostic_catalog import (
    BROWSER_INCOMPATIBLE_COMPONENT_PROP,
    BROWSER_MISSING_COMPONENT_PROP,
    BROWSER_UNKNOWN_COMPONENT_PROP,
    BROWSER_UNKNOWN_SERVER_EVENT,
    CHECK_PYTHON_SOURCE_UNREADABLE,
    CHECK_TEMPLATE_DECLARATION,
    CHECK_TEMPLATE_FILE_NOT_FOUND,
    CHECK_TEMPLATE_FILE_UNREADABLE,
    CHECK_TEMPLATE_LANGUAGE_UNSUPPORTED,
    CHECK_TEMPLATE_NAMESPACE_UNAVAILABLE,
    CHECK_TEMPLATE_VALUE_INVALID,
    I18N_ARGUMENT_INVALID,
    I18N_CATALOG_INVALID,
    I18N_CLIENT_MESSAGE_INVALID,
    I18N_CROSS_LANGUAGE_FALLBACK,
    I18N_UNKNOWN_MESSAGE,
    JS_DATA_UNSUPPORTED_TYPE,
    PARSE_CONFIGURATION,
    TEMPLATE_UNKNOWN_COMPONENT,
)
from citry._diagnostics import render_diagnostic
from citry._inline_assets import normalize_inline_asset
from citry._linting import _component_lint_info
from citry._template_data_source import TemplateDataSourceShape, analyze_template_data_source
from citry.analysis import (
    SERVER_EVENT_CALL_NAMES,
    AlpineLintConsumer,
    BrowserExpression,
    BrowserProp,
    ComponentJsLintConsumer,
    JsonWireType,
    TemplateLintConsumer,
    analyze_js_data_source,
    browser_client_prop_accepts,
    browser_component_prop_uses,
    browser_component_props,
    browser_component_scope_writes,
    browser_declarative_events,
    browser_expressions,
    browser_i18n_binding_directives,
    browser_i18n_profile_calls,
    browser_literal_calls,
    browser_literal_wire_type,
    discover_python_templates,
    json_wire_type_from_annotation,
    json_wire_type_from_expression,
    lint_csp_compatibility,
    lint_unknown_alpine_variables,
    lint_unknown_component_js_variables,
    lint_unknown_template_variables,
)
from citry.assets import _find_pair_declaration, _inspect_asset_path, module_dir
from citry.autodiscovery import _iter_py_files
from citry.ext.events.extension import _component_events_info
from citry.tag_rules import build_tag_rules
from citry_core.template_parser import RESERVED_TAG_NAMES, TemplateElement, parse_diagnostic, parse_template

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry import Citry
    from citry.component import Component
    from citry.ext.i18n.extension import I18nExtension
    from citry_core.template_parser import TagRules, Template


TRANSFORM_NOTE = "extension-transformed template validation is unavailable; checking authored Citry source"

_I18N_FORMAT_KINDS = (
    "number",
    "percent",
    "currency",
    "date",
    "time",
    "datetime",
    "relative_time",
    "list",
    "unit",
)


@dataclass(frozen=True, slots=True)
class CheckFinding:
    """One source or template finding."""

    origin: str
    message: str
    code: str
    severity: Literal["warning", "error"] = "error"
    start_index: int | None = None
    end_index: int | None = None
    line: int | None = None
    column: int | None = None
    end_line: int | None = None
    end_column: int | None = None


@dataclass(frozen=True, slots=True)
class CheckReport:
    """Complete output and exit status for one check run."""

    findings: tuple[CheckFinding, ...] = ()
    app_failure: str | None = None
    notes: tuple[str, ...] = ()

    @property
    def exit_code(self) -> int:
        """Use 2 for app/discovery degradation and 1 for ordinary findings."""
        if self.app_failure is not None:
            return 2
        if any(finding.severity == "error" for finding in self.findings):
            return 1
        return 0


@dataclass(slots=True)
class _TemplateSource:
    origin: str
    content: str
    consumers: list[type[Component]]


@dataclass(slots=True)
class _BrowserSource:
    """One authored component-JavaScript source and all registry consumers."""

    origin: str
    content: str
    consumers: list[type[Component]]


def check_project(selection: CheckAppSelection, cwd: Path) -> CheckReport:
    """Check a registry when one is available, otherwise scan definite literals."""
    if selection.failure is not None:
        return CheckReport(
            findings=tuple(_check_static(cwd)),
            app_failure=selection.failure,
        )
    if selection.engine is None:
        return CheckReport(findings=tuple(_check_static(cwd)))

    engine = selection.engine
    try:
        engine.initialize()
        registrations = engine.components
        rules = build_tag_rules(engine)
    except (Exception, SystemExit) as exc:  # noqa: BLE001 - tooling degrades on project-code failures
        return CheckReport(
            findings=tuple(_check_static(cwd)),
            app_failure=app_failure_message(exc),
        )

    return CheckReport(
        findings=tuple(_check_registry(engine, registrations, rules)),
        notes=(TRANSFORM_NOTE,),
    )


def _check_registry(
    engine: Citry,
    registrations: Mapping[str, type[Component]],
    rules: Mapping[str, TagRules],
) -> list[CheckFinding]:
    """Read each authored registry template directly and continue after failures."""
    known_names = {name.lower() for name in registrations}
    registered_components = {name.lower(): component for name, component in registrations.items()}
    unique_classes = {id(comp_cls): comp_cls for comp_cls in registrations.values()}
    components = sorted(unique_classes.values(), key=_class_label)
    findings: list[CheckFinding] = []
    sources: dict[tuple[object, ...], _TemplateSource] = {}
    browser_sources: dict[tuple[object, ...], _BrowserSource] = {}
    i18n_manifest: dict[str, dict[str, dict[str, Any]]] | None = None
    i18n_profiles: dict[str, dict[str, frozenset[str]]] | None = None

    i18n = engine.extensions._extensions_by_name.get("i18n")
    if i18n is not None and getattr(i18n, "available", False):
        try:
            i18n_extension = cast("I18nExtension", i18n)
            i18n_profiles = _i18n_profile_inventory(i18n_extension)
            i18n_extension._load_project_sources()
            compiled_catalog = i18n_extension._compiled_catalog
            if compiled_catalog is None:
                raise ValueError("The i18n compiler did not produce a project artifact.")
            artifact = json.loads(compiled_catalog.artifact_json())
            findings.extend(
                CheckFinding(
                    origin=diagnostic["path"],
                    message=diagnostic["message"],
                    code=diagnostic["code"],
                    severity=diagnostic["severity"],
                    start_index=diagnostic["start"],
                    end_index=diagnostic["end"],
                    line=diagnostic["line"],
                    column=diagnostic["column"],
                    end_line=diagnostic["line"],
                    end_column=diagnostic["column"] + diagnostic["end"] - diagnostic["start"],
                )
                for diagnostic in artifact["diagnostics"]
            )
            i18n_manifest = artifact["manifest"]
        except (Exception, SystemExit) as exc:  # noqa: BLE001 - one catalog error becomes one finding
            findings.append(
                CheckFinding(
                    "i18n catalog",
                    f"The project i18n catalog is invalid: {_error_detail(exc)}",
                    I18N_CATALOG_INVALID,
                )
            )

    for comp_cls in components:
        if engine._is_builtin_component(comp_cls):
            continue
        if i18n_manifest is not None:
            findings.extend(_client_message_findings(comp_cls, i18n_manifest))
            findings.extend(_i18n_python_findings(comp_cls, i18n_manifest, i18n_profiles or {}))
        findings.extend(_check_js_data_types(engine, comp_cls))
        _collect_browser_source(engine, comp_cls, browser_sources)
        class_label = _class_label(comp_cls)
        try:
            owner, inline, filepath = _find_pair_declaration(comp_cls, "template", "template_file")
        except (Exception, SystemExit) as exc:  # noqa: BLE001 - one bad component must not stop the batch
            findings.append(
                CheckFinding(
                    class_label,
                    render_diagnostic(CHECK_TEMPLATE_DECLARATION, detail=_error_detail(exc)),
                    CHECK_TEMPLATE_DECLARATION,
                )
            )
            continue

        if inline is None and filepath is None:
            continue
        language = _effective_class_value(comp_cls, "template_lang")
        if language is not None:
            findings.append(
                CheckFinding(
                    class_label,
                    render_diagnostic(CHECK_TEMPLATE_LANGUAGE_UNSUPPORTED, type=type(language).__name__),
                    CHECK_TEMPLATE_LANGUAGE_UNSUPPORTED,
                ),
            )
            continue

        source_key = (id(owner), "template")
        if inline is not None:
            if type(inline) is not str:
                findings.append(
                    CheckFinding(
                        class_label,
                        render_diagnostic(CHECK_TEMPLATE_VALUE_INVALID, variant="inline"),
                        CHECK_TEMPLATE_VALUE_INVALID,
                    )
                )
                continue
            existing = sources.get(source_key)
            if existing is None:
                sources[source_key] = _TemplateSource(
                    origin=f"{_class_label(owner)}.template",
                    content=normalize_inline_asset(inline),
                    consumers=[comp_cls],
                )
            else:
                existing.consumers.append(comp_cls)
            continue
        if not isinstance(filepath, (str, Path)):
            findings.append(
                CheckFinding(
                    class_label,
                    render_diagnostic(CHECK_TEMPLATE_VALUE_INVALID, variant="file"),
                    CHECK_TEMPLATE_VALUE_INVALID,
                )
            )
            continue

        try:
            inspection = _inspect_asset_path(
                filepath,
                owner_dir=module_dir(owner),
                search_dirs=engine.settings.dirs,
            )
            resolved = inspection.resolved_path
            if resolved is None:
                searched = ", ".join(str(path) for path in inspection.searched_paths)
                locations = searched or "no searchable locations"
                findings.append(
                    CheckFinding(
                        class_label,
                        render_diagnostic(
                            CHECK_TEMPLATE_FILE_NOT_FOUND,
                            path=str(filepath),
                            locations=locations,
                        ),
                        CHECK_TEMPLATE_FILE_NOT_FOUND,
                    ),
                )
                continue
            resolved_identity = resolved.resolve()
            content = resolved.read_text(encoding="utf-8")
        except (Exception, SystemExit) as exc:  # noqa: BLE001 - one bad asset must not stop the batch
            findings.append(
                CheckFinding(
                    class_label,
                    render_diagnostic(CHECK_TEMPLATE_FILE_UNREADABLE, detail=_error_detail(exc)),
                    CHECK_TEMPLATE_FILE_UNREADABLE,
                )
            )
            continue
        file_key = ("file", resolved_identity)
        existing = sources.get(file_key)
        if existing is None:
            sources[file_key] = _TemplateSource(origin=str(resolved), content=content, consumers=[comp_cls])
        else:
            existing.consumers.append(comp_cls)

    scope_names: dict[int, set[str]] = {}
    for browser_source in browser_sources.values():
        names = {write.name for write in browser_component_scope_writes(browser_source.content)}
        for component in browser_source.consumers:
            scope_names.setdefault(id(component), set()).update(names)

    for source in sources.values():
        try:
            lint_consumers = tuple(_checker_lint_consumer(engine, component) for component in source.consumers)
            alpine_lint_consumers = tuple(
                _checker_alpine_lint_consumer(
                    engine,
                    component,
                    scope_names.get(id(component), set()),
                )
                for component in source.consumers
            )
        except (Exception, SystemExit) as exc:  # noqa: BLE001 - one namespace must not stop the batch
            findings.append(
                CheckFinding(
                    source.origin,
                    render_diagnostic(CHECK_TEMPLATE_NAMESPACE_UNAVAILABLE, detail=_error_detail(exc)),
                    CHECK_TEMPLATE_NAMESPACE_UNAVAILABLE,
                )
            )
            lint_consumers = ()
            alpine_lint_consumers = ()
        findings.extend(
            _check_template(
                source,
                rules=rules,
                known_names=known_names,
                registered_components=registered_components,
                engine=engine,
                lint_consumers=lint_consumers,
                alpine_lint_consumers=alpine_lint_consumers,
                i18n_manifest=i18n_manifest,
                i18n_profiles=i18n_profiles,
            )
        )
    for browser_source in browser_sources.values():
        findings.extend(_check_browser_source(engine, browser_source, i18n_profiles or {}))
    return findings


def _check_static(cwd: Path) -> list[CheckFinding]:
    """Parse literals conservatively matched to local component subclasses."""
    findings: list[CheckFinding] = []
    for path in _iter_py_files(cwd):
        try:
            with tokenize.open(path) as source_file:
                source = source_file.read()
            discovery = discover_python_templates(source)
        except (OSError, SyntaxError, UnicodeError) as exc:
            findings.append(
                CheckFinding(
                    str(path),
                    render_diagnostic(CHECK_PYTHON_SOURCE_UNREADABLE, detail=_error_detail(exc)),
                    CHECK_PYTHON_SOURCE_UNREADABLE,
                )
            )
            continue
        findings.extend(
            _static_notice_finding(path, notice.component_name, notice.message) for notice in discovery.notices
        )
        for region in discovery.regions:
            findings.extend(
                _check_template(
                    _TemplateSource(
                        origin=f"{path} ({region.component_name}.template)",
                        content=region.source_map.template_source,
                        consumers=[],
                    ),
                ),
            )
    return findings


def _check_template(
    source: _TemplateSource,
    *,
    rules: Mapping[str, TagRules] | None = None,
    known_names: set[str] | None = None,
    registered_components: Mapping[str, type[Component]] | None = None,
    engine: Citry | None = None,
    lint_consumers: tuple[TemplateLintConsumer, ...] = (),
    alpine_lint_consumers: tuple[AlpineLintConsumer, ...] = (),
    i18n_manifest: dict[str, dict[str, dict[str, Any]]] | None = None,
    i18n_profiles: dict[str, dict[str, frozenset[str]]] | None = None,
) -> list[CheckFinding]:
    """Parse one source and, in registry mode, inspect component tag names."""
    try:
        template = parse_template(source.content, user_rules=dict(rules) if rules is not None else None)
    except (SyntaxError, ValueError) as exc:
        diagnostic = parse_diagnostic(exc)
        if diagnostic is None:
            return [CheckFinding(source.origin, str(exc), code=PARSE_CONFIGURATION)]
        return [
            CheckFinding(
                source.origin,
                str(exc),
                code=diagnostic.code,
                start_index=diagnostic.start_index,
                end_index=diagnostic.end_index,
                line=diagnostic.start_line,
                column=diagnostic.start_column,
                end_line=diagnostic.end_line,
                end_column=diagnostic.end_column,
            )
        ]
    findings = _unknown_component_findings(source.origin, template, known_names) if known_names is not None else []
    nested_parser = lambda value: parse_template(  # noqa: E731 - parser hook is passed as a value
        value,
        user_rules=dict(rules) if rules is not None else None,
    )
    findings.extend(
        _i18n_binding_findings(
            source.origin,
            source.content,
            template,
            i18n_manifest,
            parse_nested=nested_parser,
        )
    )
    if i18n_manifest is not None:
        findings.extend(
            _i18n_template_findings(
                source.origin,
                source.content,
                template,
                i18n_manifest,
                known_types=_known_template_types(engine, source.consumers),
                profiles=i18n_profiles or {},
            )
        )
    findings.extend(
        CheckFinding(
            origin=source.origin,
            message=finding.message,
            code=finding.code,
            severity=finding.severity,
            start_index=finding.start_index,
            end_index=finding.end_index,
            line=finding.line,
            column=finding.column,
            end_line=finding.line,
            end_column=finding.column + len(finding.name),
        )
        for finding in lint_unknown_template_variables(template, lint_consumers)
    )
    browser_hosts = browser_expressions(template, parse_nested=nested_parser)
    for expression in browser_hosts:
        findings.extend(_browser_i18n_profile_findings(source.origin, source.content, expression, i18n_profiles or {}))
    for finding in lint_unknown_alpine_variables(browser_hosts, alpine_lint_consumers):
        line, column = _byte_offset_coordinates(source.content, finding.start_index)
        end_line, end_column = _byte_offset_coordinates(source.content, finding.end_index)
        findings.append(
            CheckFinding(
                origin=source.origin,
                message=finding.message,
                code=finding.code,
                severity=finding.severity,
                start_index=finding.start_index,
                end_index=finding.end_index,
                line=line,
                column=column,
                end_line=end_line,
                end_column=end_column,
            )
        )
    csp_mode = engine.settings.security_csp if engine is not None else None
    for csp_finding in lint_csp_compatibility(browser_hosts, alpine_lint_consumers, csp_mode):
        line, column = _byte_offset_coordinates(source.content, csp_finding.start_index)
        end_line, end_column = _byte_offset_coordinates(source.content, csp_finding.end_index)
        findings.append(
            CheckFinding(
                origin=source.origin,
                message=csp_finding.message,
                code=csp_finding.code,
                severity=csp_finding.severity,
                start_index=csp_finding.start_index,
                end_index=csp_finding.end_index,
                line=line,
                column=column,
                end_line=end_line,
                end_column=end_column,
            )
        )
    event_names = _shared_event_names(source.consumers)
    if event_names is not None:
        for expression in browser_hosts:
            findings.extend(_unknown_event_findings(source.origin, source.content, expression, event_names))
        for event in browser_declarative_events(template, event_names, parse_nested=nested_parser):
            if event.name not in event_names:
                findings.append(
                    _unknown_event_finding(
                        source.origin,
                        source.content,
                        event.name,
                        event.start_index,
                        event.end_index,
                    )
                )
    if registered_components is not None:
        for props_use in browser_component_prop_uses(template, parse_nested=nested_parser):
            target = registered_components.get(props_use.tag_name.removeprefix("c-").lower())
            if target is None:
                continue
            if engine is None:
                continue
            contract = _checker_component_props(engine, target)
            if contract is None:
                continue
            by_name = {prop.name: prop for prop in contract}
            explicit = {property_.name for property_ in props_use.properties}
            for property_ in props_use.properties:
                expected = by_name.get(property_.name)
                if expected is not None:
                    actual = browser_literal_wire_type(property_.value_source)
                    if actual.kind != "unknown" and not browser_client_prop_accepts(expected.javascript, actual):
                        findings.append(
                            _browser_template_finding(
                                source.origin,
                                source.content,
                                property_.value_start_index,
                                property_.value_end_index,
                                BROWSER_INCOMPATIBLE_COMPONENT_PROP,
                                name=property_.name,
                                expected=expected.javascript,
                                actual=actual.javascript,
                            )
                        )
                    continue
                findings.append(
                    _browser_template_finding(
                        source.origin,
                        source.content,
                        property_.start_index,
                        property_.end_index,
                        BROWSER_UNKNOWN_COMPONENT_PROP,
                        name=property_.name,
                        tag=props_use.tag_name,
                    )
                )
            if props_use.has_dynamic_keys:
                continue
            for prop in contract:
                if not prop.required or prop.name in explicit:
                    continue
                findings.append(
                    _browser_template_finding(
                        source.origin,
                        source.content,
                        props_use.start_index,
                        props_use.end_index,
                        BROWSER_MISSING_COMPONENT_PROP,
                        name=prop.name,
                        tag=props_use.tag_name,
                    )
                )
    return findings


def _known_template_types(engine: Citry | None, consumers: list[type[Component]]) -> dict[str, str]:
    if engine is None:
        return {}
    candidates: dict[str, set[str]] = {}
    for component in consumers:
        component_info = engine.inspect_component(component)
        for schema in (component_info.schemas.kwargs, component_info.schemas.template_data):
            if schema.kind != "fields":
                continue
            for field in schema.fields:
                if field.type_display is not None:
                    candidates.setdefault(field.name, set()).add(field.type_display)
    return {name: next(iter(types)) for name, types in candidates.items() if len(types) == 1}


def _i18n_profile_inventory(extension: I18nExtension) -> dict[str, dict[str, frozenset[str]]]:
    """Return the literal profile names valid for direct format and parse calls."""
    formats = extension.config.formats
    format_profiles = {kind: frozenset(getattr(formats, kind)) for kind in _I18N_FORMAT_KINDS}
    parse_profiles = {
        "number": format_profiles["number"],
        "percent": format_profiles["percent"],
        "date": frozenset(name for name, profile in formats.date.items() if profile.input is not None),
        "time": frozenset(name for name, profile in formats.time.items() if profile.input is not None),
        "datetime": frozenset(name for name, profile in formats.datetime.items() if profile.input is not None),
    }
    return {"format": format_profiles, "parse": parse_profiles}


def _i18n_profile_target(function: ast.expr) -> tuple[str, str] | None:
    """Recognize the direct formatter/parser spellings owned by the public API."""
    if not isinstance(function, ast.Attribute):
        return None
    operation = function.attr
    owner = function.value
    if isinstance(owner, ast.Name) and owner.id == "fmt":
        return "format", operation
    if not isinstance(owner, ast.Attribute) or owner.attr not in {"format", "parse"}:
        return None
    i18n = owner.value
    if (
        not isinstance(i18n, ast.Attribute)
        or i18n.attr != "i18n"
        or not isinstance(i18n.value, ast.Name)
        or i18n.value.id != "self"
    ):
        return None
    return owner.attr, operation


def _literal_i18n_profile_finding(
    origin: str,
    source: str,
    expression: ast.Call,
    profiles: dict[str, dict[str, frozenset[str]]],
    start: int,
    end: int,
) -> CheckFinding | None:
    target = _i18n_profile_target(expression.func)
    if target is None:
        return None
    namespace, operation = target
    known = profiles.get(namespace, {}).get(operation)
    if known is None:
        return None
    keyword = next((item for item in expression.keywords if item.arg == "format"), None)
    if keyword is None or not isinstance(keyword.value, ast.Constant) or type(keyword.value.value) is not str:
        return None
    profile = cast("str", keyword.value.value)
    if profile in known:
        return None
    available = ", ".join(repr(item) for item in sorted(known)) or "none"
    return _i18n_use_finding(
        origin,
        source,
        f"Unknown i18n {namespace} profile {profile!r} for {operation}; configured profiles: {available}.",
        I18N_ARGUMENT_INVALID,
        start,
        end,
    )


def _browser_i18n_profile_findings(
    origin: str,
    source: str,
    expression: BrowserExpression,
    profiles: dict[str, dict[str, frozenset[str]]],
    *,
    owners: frozenset[str] = frozenset({"$i18n"}),
) -> list[CheckFinding]:
    findings: list[CheckFinding] = []
    operation_names = {"relativeTime": "relative_time"}
    for call in browser_i18n_profile_calls(expression, owners):
        operation = operation_names.get(call.operation, call.operation)
        known = profiles.get(call.namespace, {}).get(operation)
        if known is None or call.profile in known:
            continue
        available = ", ".join(repr(item) for item in sorted(known)) or "none"
        findings.append(
            _i18n_use_finding(
                origin,
                source,
                f"Unknown i18n {call.namespace} profile {call.profile!r} for {operation}; "
                f"configured profiles: {available}.",
                I18N_ARGUMENT_INVALID,
                call.start_index,
                call.end_index,
            )
        )
    return findings


def _literal_tr_target(expression: ast.Call) -> tuple[str, str | None] | None:
    if not expression.args or not isinstance(expression.args[0], ast.Constant):
        return None
    message_id = expression.args[0].value
    if type(message_id) is not str:
        return None
    attr_keyword = next((keyword for keyword in expression.keywords if keyword.arg == "attr"), None)
    if attr_keyword is None:
        return message_id, message_id
    attr_expression = attr_keyword.value
    if isinstance(attr_expression, ast.Constant):
        if attr_expression.value is None:
            return message_id, message_id
        if type(attr_expression.value) is str:
            return message_id, f"{message_id}.{attr_expression.value}"
    return message_id, None


def _literal_tr_call_findings(
    origin: str,
    source: str,
    expression: ast.Call,
    manifest: dict[str, dict[str, dict[str, Any]]],
    start: int,
    end: int,
    *,
    known_types: dict[str, str],
) -> list[CheckFinding]:
    target = _literal_tr_target(expression)
    if target is None:
        return []
    message_id, token = target
    if token is None:
        known = any(
            output == message_id or output.startswith(f"{message_id}.")
            for outputs in manifest.values()
            for output in outputs
        )
        return [] if known else [_i18n_message_finding(origin, source, message_id, start, end)]
    entries = _i18n_entries(manifest, token)
    if not entries:
        return [_i18n_message_finding(origin, source, token, start, end)]
    findings: list[CheckFinding] = []
    expected = cast("dict[str, dict[str, Any]]", entries[0][1]["interface"])
    explicit = {
        keyword.arg: keyword.value
        for keyword in expression.keywords
        if keyword.arg is not None and keyword.arg != "attr"
    }
    has_spread = any(keyword.arg is None for keyword in expression.keywords)
    if len(expression.args) != 1:
        findings.append(
            _i18n_use_finding(
                origin,
                source,
                "tr() accepts only the message ID as a positional argument.",
                I18N_ARGUMENT_INVALID,
                start,
                end,
            )
        )
    unknown = sorted(set(explicit) - set(expected))
    missing = sorted(set(expected) - set(explicit)) if not has_spread else []
    if unknown or missing:
        details = []
        if unknown:
            details.append(f"unknown argument(s): {', '.join(unknown)}")
        if missing:
            details.append(f"missing argument(s): {', '.join(missing)}")
        findings.append(
            _i18n_use_finding(
                origin,
                source,
                f"i18n output {token!r} has {', '.join(details)}.",
                I18N_ARGUMENT_INVALID,
                start,
                end,
            )
        )
    for name in sorted(set(explicit) & set(expected)):
        mismatch = _literal_i18n_type_mismatch(
            expected[name]["type_name"],
            explicit[name],
            known_types=known_types,
        )
        if mismatch is not None:
            findings.append(
                _i18n_use_finding(
                    origin,
                    source,
                    f"i18n argument {name!r} for {token!r} {mismatch}.",
                    I18N_ARGUMENT_INVALID,
                    start,
                    end,
                )
            )
    findings.extend(_cross_language_findings(origin, source, token, entries, start, end))
    return findings


def _i18n_python_findings(
    component: type[Component],
    manifest: dict[str, dict[str, dict[str, Any]]],
    profiles: dict[str, dict[str, frozenset[str]]],
) -> list[CheckFinding]:
    source_file = _loaded_python_file(component)
    qualname = _safe_class_text(component, "__qualname__")
    if source_file is None or qualname is None:
        return []
    try:
        with tokenize.open(source_file) as source_stream:
            source = source_stream.read()
        tree = ast.parse(source)
    except (OSError, SyntaxError, UnicodeError):
        return []
    scope = _python_qualified_scope(tree, qualname)
    if not isinstance(scope, ast.ClassDef):
        return []
    origin = f"{source_file} ({_class_label(component)})"
    findings: list[CheckFinding] = []
    for node in _component_i18n_calls(scope):
        start, end = _python_ast_byte_range(source, node)
        if _is_self_i18n_tr(node.func):
            findings.extend(
                _literal_tr_call_findings(
                    origin,
                    source,
                    node,
                    manifest,
                    start,
                    end,
                    known_types={},
                )
            )
            continue
        profile_finding = _literal_i18n_profile_finding(origin, source, node, profiles, start, end)
        if profile_finding is not None:
            findings.append(profile_finding)
    return findings


class _ComponentI18nCallVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: list[ast.Call] = []

    def visit_Call(self, node: ast.Call) -> None:
        self.calls.append(node)
        self.generic_visit(node)

    def visit_ClassDef(self, _node: ast.ClassDef) -> None:
        return

    def visit_FunctionDef(self, _node: ast.FunctionDef) -> None:
        return

    def visit_AsyncFunctionDef(self, _node: ast.AsyncFunctionDef) -> None:
        return


def _component_i18n_calls(scope: ast.ClassDef) -> list[ast.Call]:
    visitor = _ComponentI18nCallVisitor()
    for statement in scope.body:
        if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for method_statement in statement.body:
            visitor.visit(method_statement)
    return visitor.calls


def _python_qualified_scope(tree: ast.Module, qualname: str) -> ast.AST | None:
    body: list[ast.stmt] = tree.body
    current: ast.AST | None = None
    for part in (item for item in qualname.split(".") if item != "<locals>"):
        matches = [
            statement
            for statement in body
            if isinstance(statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and statement.name == part
        ]
        if len(matches) != 1:
            return None
        current = matches[0]
        body = current.body
    return current


def _is_self_i18n_tr(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "tr"
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "i18n"
        and isinstance(node.value.value, ast.Name)
        and node.value.value.id == "self"
    )


def _python_ast_byte_range(source: str, node: ast.expr) -> tuple[int, int]:
    lines = source.splitlines(keepends=True)
    end_lineno = node.end_lineno if node.end_lineno is not None else node.lineno
    end_col_offset = node.end_col_offset if node.end_col_offset is not None else node.col_offset
    start = sum(len(line.encode("utf-8")) for line in lines[: node.lineno - 1]) + node.col_offset
    end = sum(len(line.encode("utf-8")) for line in lines[: end_lineno - 1]) + end_col_offset
    return start, end


def _i18n_template_findings(
    origin: str,
    source: str,
    template: Template,
    manifest: dict[str, dict[str, dict[str, Any]]],
    *,
    known_types: dict[str, str],
    profiles: dict[str, dict[str, frozenset[str]]],
) -> list[CheckFinding]:
    """Check literal i18n calls against compiled outputs and typed source interfaces."""
    findings: list[CheckFinding] = []
    seen: set[tuple[int, str]] = set()
    for use in template.used_variables:
        if use.content not in {"tr", "fmt"}:
            continue
        call_source = _balanced_call_at(source, use.start_index)
        if call_source is None:
            continue
        try:
            expression = ast.parse(call_source, mode="eval").body
        except SyntaxError:
            continue
        if not isinstance(expression, ast.Call):
            continue
        end = use.start_index + len(call_source.encode())
        if not isinstance(expression.func, ast.Name) or expression.func.id != "tr":
            profile_finding = _literal_i18n_profile_finding(
                origin,
                source,
                expression,
                profiles,
                use.start_index,
                end,
            )
            if profile_finding is not None:
                findings.append(profile_finding)
            continue
        target = _literal_tr_target(expression)
        if target is None:
            continue
        message_id, token = target
        key = (use.start_index, token if token is not None else f"{message_id}.*")
        if key in seen:
            continue
        seen.add(key)
        findings.extend(
            _literal_tr_call_findings(
                origin,
                source,
                expression,
                manifest,
                use.start_index,
                end,
                known_types=known_types,
            )
        )
    for node in _trans_nodes(template):
        attrs = {attr.key.content: attr for attr in node.start_tag.attrs}
        message_attr = attrs.get("message")
        if message_attr is None or message_attr.inner_value is None:
            continue
        message_id = message_attr.inner_value.content
        start = message_attr.inner_value.start_index
        end = message_attr.inner_value.end_index
        attr_attr = attrs.get("attr")
        attribute = (
            attr_attr.inner_value.content if attr_attr is not None and attr_attr.inner_value is not None else None
        )
        token = message_id if attribute is None else f"{message_id}.{attribute}"
        entries = _i18n_entries(manifest, token)
        if not entries:
            findings.append(_i18n_message_finding(origin, source, token, start, end))
        else:
            findings.extend(_trans_contract_findings(origin, source, node, attrs, token, entries[0][1], start, end))
            findings.extend(_cross_language_findings(origin, source, token, entries, start, end))
    return findings


def _i18n_binding_findings(
    origin: str,
    source: str,
    template: Template,
    manifest: dict[str, dict[str, dict[str, Any]]] | None,
    *,
    parse_nested: Any,
) -> list[CheckFinding]:
    """Validate declarative binding syntax and statically known contracts."""
    findings: list[CheckFinding] = []
    for directive in browser_i18n_binding_directives(template, parse_nested=parse_nested):
        if directive.error is not None:
            start = (
                directive.error_start_index if directive.error_start_index is not None else directive.name_start_index
            )
            end = directive.error_end_index if directive.error_end_index is not None else directive.name_end_index
            findings.append(
                _i18n_use_finding(origin, source, directive.error, I18N_ARGUMENT_INVALID, start, max(start, end))
            )
            continue
        if manifest is None or directive.message is None:
            continue
        token = directive.message if directive.output is None else f"{directive.message}.{directive.output}"
        entries = _i18n_entries(manifest, token)
        start = directive.message_start_index or directive.name_start_index
        end = directive.message_end_index or directive.name_end_index
        if not entries:
            findings.append(_i18n_message_finding(origin, source, token, start, end))
            continue
        if directive.server_dynamic:
            continue
        interface = cast("dict[str, dict[str, Any]]", entries[0][1]["interface"])
        expected = {name for name, metadata in interface.items() if metadata["type_name"] != "Slot"}
        supplied = {argument.name for argument in directive.arguments}
        issues: list[str] = []
        unknown = sorted(supplied - expected)
        missing = (
            sorted(expected - supplied)
            if directive.has_values_expression and not directive.has_dynamic_arguments
            else []
        )
        if unknown:
            issues.append(f"unknown argument(s): {', '.join(unknown)}")
        if missing:
            issues.append(f"missing argument(s): {', '.join(missing)}")
        for argument in directive.arguments:
            metadata = interface.get(argument.name)
            if metadata is None:
                continue
            actual = browser_literal_wire_type(argument.value_source)
            if actual.kind != "unknown" and not _browser_i18n_type_accepts(metadata["type_name"], actual):
                issues.append(f"argument {argument.name!r} must be {metadata['type_name']}, not {actual.javascript}")
        if issues:
            findings.append(
                _i18n_use_finding(
                    origin,
                    source,
                    f"$c-tr output {token!r} has {'; '.join(issues)}.",
                    I18N_ARGUMENT_INVALID,
                    start,
                    end,
                )
            )
    return findings


def _browser_i18n_type_accepts(expected: str, actual: JsonWireType) -> bool:
    """Match proven JavaScript value kinds to the browser formatter contract."""
    if actual.kind == "union":
        return all(_browser_i18n_type_accepts(expected, item) for item in actual.items)
    allowed = {
        "str": {"string"},
        "int": {"number", "string"},
        "Decimal": {"number", "string"},
        "scalar": {"number", "string"},
        "datetime": set(),
    }.get(expected)
    return True if allowed is None or actual.kind == "unknown" else actual.kind in allowed


def _trans_nodes(template: Template) -> list[Any]:
    result: list[Any] = []
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        if node.start_tag.name.content.lower() == "c-trans":
            result.append(node)
        body = getattr(node, "body", None)
        if body is not None:
            result.extend(_trans_nodes(body))
    return result


def _trans_contract_findings(
    origin: str,
    source: str,
    node: Any,
    attrs: dict[str, Any],
    token: str,
    entry: dict[str, Any],
    start: int,
    end: int,
) -> list[CheckFinding]:
    interface = cast("dict[str, dict[str, Any]]", entry["interface"])
    scalar_names = {name for name, metadata in interface.items() if metadata["type_name"] != "Slot"}
    slot_names = {name for name, metadata in interface.items() if metadata["type_name"] == "Slot"}
    values: dict[str, ast.expr] | None = {}
    values_attr = attrs.get("c-values")
    if values_attr is not None and values_attr.inner_value is not None:
        values = None
        try:
            expression = ast.parse(values_attr.inner_value.content, mode="eval").body
        except SyntaxError:
            expression = None
        if isinstance(expression, ast.Dict) and all(
            key is not None and isinstance(key, ast.Constant) and type(key.value) is str for key in expression.keys
        ):
            values = {}
            for key, value in zip(expression.keys, expression.values, strict=True):
                if isinstance(key, ast.Constant) and type(key.value) is str:
                    values[cast("str", key.value)] = value
    fills: set[str] = set()
    body = getattr(node, "body", None)
    if body is not None:
        for element in body.elements:
            if not isinstance(element, TemplateElement.Node):
                continue
            fill = element._0
            if fill.start_tag.name.content.lower() != "c-fill":
                continue
            name_attr = next((attr for attr in fill.start_tag.attrs if attr.key.content == "name"), None)
            if name_attr is not None and name_attr.inner_value is not None:
                fills.add(name_attr.inner_value.content)
    issues: list[str] = []
    if values is not None:
        unknown_values = sorted(set(values) - scalar_names)
        missing_values = sorted(scalar_names - set(values))
        if unknown_values:
            issues.append(f"unknown values: {', '.join(unknown_values)}")
        if missing_values:
            issues.append(f"missing values: {', '.join(missing_values)}")
        for name in sorted(set(values) & scalar_names):
            mismatch = _literal_i18n_type_mismatch(interface[name]["type_name"], values[name])
            if mismatch is not None:
                issues.append(f"value {name!r} {mismatch}")
    unknown_fills = sorted(fills - slot_names)
    missing_fills = sorted(slot_names - fills)
    if unknown_fills:
        issues.append(f"unknown fills: {', '.join(unknown_fills)}")
    if missing_fills:
        issues.append(f"missing fills: {', '.join(missing_fills)}")
    collisions = sorted(fills & (set(values) if values is not None else set()))
    if collisions:
        issues.append(f"names used by both values and fills: {', '.join(collisions)}")
    if not issues:
        return []
    return [
        _i18n_use_finding(
            origin,
            source,
            f"<c-trans> output {token!r} has {'; '.join(issues)}.",
            I18N_ARGUMENT_INVALID,
            start,
            end,
        )
    ]


def _i18n_entries(manifest: dict[str, dict[str, dict[str, Any]]], token: str) -> list[tuple[str, dict[str, Any]]]:
    return [(locale, outputs[token]) for locale, outputs in sorted(manifest.items()) if token in outputs]


def _literal_i18n_type_mismatch(
    expected: str,
    expression: ast.expr,
    *,
    known_types: dict[str, str] | None = None,
) -> str | None:
    if expected == "Slot":
        return "is structural and must be supplied through <c-trans>, not tr()"
    if isinstance(expression, ast.Name) and known_types is not None:
        actual = known_types.get(expression.id)
        if actual is not None and not _i18n_type_accepts(expected, actual):
            return f"must be {expected}, not {actual}"
        return None
    if not isinstance(expression, ast.Constant):
        return None
    value = expression.value
    if expected == "str" and type(value) is not str:
        return f"must be str, not {type(value).__name__}"
    if expected == "scalar" and type(value) not in {str, int}:
        return f"must be str, int, or Decimal, not {type(value).__name__}"
    if expected == "int" and type(value) is not int:
        return f"must be int, not {type(value).__name__}"
    if expected in {"Decimal", "datetime"}:
        return f"must be an explicit {expected} value, not a literal {type(value).__name__}"
    return None


def _i18n_type_accepts(expected: str, actual: str) -> bool:
    short = actual.rsplit(".", maxsplit=1)[-1]
    if expected == "scalar":
        return short in {"str", "int", "Decimal"}
    return short == expected


def _cross_language_findings(
    origin: str,
    source: str,
    token: str,
    entries: list[tuple[str, dict[str, Any]]],
    start: int,
    end: int,
) -> list[CheckFinding]:
    fallbacks = [locale for locale, entry in entries if entry["bundle_locale"] != locale]
    if not fallbacks:
        return []
    return [
        _i18n_use_finding(
            origin,
            source,
            f"i18n output {token!r} falls back to another language for: {', '.join(fallbacks)}. "
            "Plain translated text cannot carry the selected language, so add translations for those locales.",
            I18N_CROSS_LANGUAGE_FALLBACK,
            start,
            end,
        )
    ]


def _client_message_findings(
    component: type[Component], manifest: dict[str, dict[str, dict[str, Any]]]
) -> list[CheckFinding]:
    result: list[CheckFinding] = []
    i18n_config = cast("Any", component).I18n
    for message_id in i18n_config.client_messages:
        tokens = sorted(
            {
                token
                for outputs in manifest.values()
                for token in outputs
                if token == message_id or token.startswith(f"{message_id}.")
            }
        )
        if not tokens:
            result.append(
                CheckFinding(
                    _class_label(component),
                    f"Component.I18n.client_messages names unknown message ID {message_id!r}.",
                    I18N_CLIENT_MESSAGE_INVALID,
                )
            )
            continue
        for token in tokens:
            fallback_locales = [
                locale for locale, entry in _i18n_entries(manifest, token) if entry["bundle_locale"] != locale
            ]
            if fallback_locales:
                result.append(
                    CheckFinding(
                        _class_label(component),
                        f"Client output {token!r} has no exact-locale output for: {', '.join(fallback_locales)}.",
                        I18N_CLIENT_MESSAGE_INVALID,
                    )
                )
    return result


def _balanced_call_at(source: str, byte_start: int) -> str | None:
    """Return one Python call beginning at a parser byte offset."""
    encoded = source.encode()
    tail = encoded[byte_start:].decode()
    open_index = tail.find("(")
    call_name = tail[:open_index].strip() if open_index >= 0 else ""
    if open_index < 0 or (call_name != "tr" and not call_name.startswith("fmt.")):
        return None
    depth = 0
    quote: str | None = None
    escaped = False
    for index, character in enumerate(tail[open_index:], start=open_index):
        if quote is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if character in {"'", '"'}:
            quote = character
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return tail[: index + 1]
    return None


def _i18n_message_finding(
    origin: str,
    source: str,
    message_id: str,
    start: int,
    end: int,
) -> CheckFinding:
    line, column = _byte_offset_coordinates(source, start)
    end_line, end_column = _byte_offset_coordinates(source, end)
    return CheckFinding(
        origin=origin,
        message=f"Unknown i18n message ID {message_id!r}; no component or configured catalog package defines it.",
        code=I18N_UNKNOWN_MESSAGE,
        start_index=start,
        end_index=end,
        line=line,
        column=column,
        end_line=end_line,
        end_column=end_column,
    )


def _i18n_use_finding(
    origin: str,
    source: str,
    message: str,
    code: str,
    start: int,
    end: int,
) -> CheckFinding:
    line, column = _byte_offset_coordinates(source, start)
    end_line, end_column = _byte_offset_coordinates(source, end)
    return CheckFinding(
        origin=origin,
        message=message,
        code=code,
        start_index=start,
        end_index=end,
        line=line,
        column=column,
        end_line=end_line,
        end_column=end_column,
    )


def _checker_lint_consumer(engine: Citry, component: type[Component]) -> TemplateLintConsumer:
    """Build the same detached root policy used by editor analysis from disk source."""
    component_info = engine.inspect_component(component)
    lint = _component_lint_info(engine, component)
    known_names = {variable.name for variable in lint.template_variables}
    schema = component_info.schemas.template_data
    if schema.kind == "fields":
        known_names.update(field.name for field in schema.fields)
        namespace_policy = schema.namespace_policy
    elif schema.kind == "opaque":
        namespace_policy = "unknown"
    else:
        kwargs_schema = component_info.schemas.kwargs
        kwargs_fields = tuple(field.name for field in kwargs_schema.fields) if kwargs_schema.kind == "fields" else None
        shape = _disk_template_data_shape(component, kwargs_fields)
        if shape is None:
            namespace_policy = "unknown"
        else:
            known_names.update(root.name for root in shape.roots)
            if shape.completeness == "open":
                namespace_policy = "unknown"
            elif shape.preserves_kwargs_extras:
                namespace_policy = kwargs_schema.namespace_policy
            else:
                namespace_policy = "closed"
    if lint.allows_extra_variables:
        namespace_policy = "allow-extra"
    return TemplateLintConsumer(
        known_names=frozenset(known_names),
        namespace_policy=namespace_policy,
        rule_unknown_template_variable=lint.rule_unknown_template_variable,
    )


def _checker_alpine_lint_consumer(
    engine: Citry,
    component: type[Component],
    scope_names: set[str],
) -> AlpineLintConsumer:
    """Build the strict browser namespace shared with editor analysis."""
    component_info = engine.inspect_component(component)
    lint = _component_lint_info(engine, component)
    known_names = {variable.name for variable in lint.alpine_variables}
    known_names.update(scope_names)
    schema = component_info.schemas.js_data
    if schema.kind == "fields":
        known_names.update(field.name for field in schema.fields)
    elif schema.kind == "absent":
        analyzed = _disk_js_data_shape(component)
        if analyzed is not None:
            known_names.update(root.name for root in analyzed[2].roots)
    return AlpineLintConsumer(
        known_names=frozenset(known_names),
        rule_unknown_alpine_variable=lint.rule_unknown_alpine_variable,
    )


def _disk_template_data_shape(
    component: type[Component],
    kwargs_fields: tuple[str, ...] | None,
) -> TemplateDataSourceShape | None:
    """Analyze the effective authored method from its already-loaded module file."""
    for candidate in _static_class_mro(component):
        namespace = _static_class_dict(candidate)
        if "template_data" not in namespace:
            continue
        source_file = _loaded_python_file(candidate)
        qualname = _safe_class_text(candidate, "__qualname__")
        if source_file is None or qualname is None:
            return None
        try:
            with tokenize.open(source_file) as source_stream:
                source = source_stream.read()
        except (OSError, SyntaxError, UnicodeError):
            return None
        return analyze_template_data_source(source, qualname, kwargs_fields=kwargs_fields)
    return None


def _check_js_data_types(engine: Citry, component: type[Component]) -> list[CheckFinding]:
    """Warn for source-proven JsData values outside Citry's strict JSON wire."""
    component_info = engine.inspect_component(component)
    schema = component_info.schemas.js_data
    findings: list[CheckFinding] = []
    if schema.kind == "fields":
        for field in schema.fields:
            wire_type = json_wire_type_from_annotation(field.type_display) if field.type_display is not None else None
            if wire_type is None or not wire_type.unsupported:
                continue
            coordinates = _field_coordinates(field.source_file, field.source_qualname, field.name)
            findings.append(
                _source_finding(
                    origin=f"{_class_label(component)}.JsData.{field.name}",
                    message=render_diagnostic(
                        JS_DATA_UNSUPPORTED_TYPE,
                        name=field.name,
                        detail="; ".join(wire_type.unsupported),
                    ),
                    code=JS_DATA_UNSUPPORTED_TYPE,
                    severity="warning",
                    coordinates=coordinates,
                )
            )
        return findings
    if schema.kind != "absent":
        return findings
    analyzed = _disk_js_data_shape(component)
    if analyzed is None:
        return findings
    source_file, source, shape = analyzed
    member_types: dict[str, dict[str, JsonWireType]] = {}
    kwargs_schema = component_info.schemas.kwargs
    if len(shape.parameters) >= 2 and kwargs_schema.kind == "fields":
        member_types[shape.parameters[1]] = {
            field.name: (
                json_wire_type_from_annotation(field.type_display)
                if field.type_display is not None
                else JsonWireType("unknown")
            )
            for field in kwargs_schema.fields
        }
    for root in shape.roots:
        wire_types = [
            json_wire_type_from_expression(value, member_types=member_types)
            for definition in root.definitions
            if (value := _range_source(source, definition.value_range)) is not None
        ]
        issues = tuple(dict.fromkeys(issue for item in wire_types for issue in item.unsupported))
        if not issues:
            continue
        definition = root.definitions[-1]
        findings.append(
            _source_finding(
                origin=f"{source_file} ({_class_label(component)}.js_data)",
                message=render_diagnostic(
                    JS_DATA_UNSUPPORTED_TYPE,
                    name=root.name,
                    detail="; ".join(issues),
                ),
                code=JS_DATA_UNSUPPORTED_TYPE,
                severity="warning",
                coordinates=_lsp_range_coordinates(source, definition.key_range),
            )
        )
    return findings


def _disk_js_data_shape(
    component: type[Component],
) -> tuple[Path, str, TemplateDataSourceShape] | None:
    """Analyze the effective authored js_data method from its loaded file."""
    for candidate in _static_class_mro(component):
        namespace = _static_class_dict(candidate)
        if "js_data" not in namespace:
            continue
        source_file = _loaded_python_file(candidate)
        qualname = _safe_class_text(candidate, "__qualname__")
        if source_file is None or qualname is None:
            return None
        try:
            with tokenize.open(source_file) as source_stream:
                source = source_stream.read()
        except (OSError, SyntaxError, UnicodeError):
            return None
        shape = analyze_js_data_source(source, qualname)
        return (source_file, source, shape) if shape is not None else None
    return None


def _collect_browser_source(
    engine: Citry,
    component: type[Component],
    sources: dict[tuple[object, ...], _BrowserSource],
) -> None:
    """Collect supported inline/file component JavaScript without executing loaders."""
    try:
        owner, inline, filepath = _find_pair_declaration(component, "js", "js_file")
    except (Exception, SystemExit):  # noqa: BLE001 - one invalid component must not stop the batch
        return
    if inline is None and filepath is None:
        return
    if _effective_class_value(component, "js_lang") is not None:
        return
    if type(inline) is str:
        inline_key: tuple[object, ...] = (id(owner), "js")
        existing = sources.get(inline_key)
        if existing is None:
            sources[inline_key] = _BrowserSource(
                f"{_class_label(owner)}.js",
                normalize_inline_asset(inline),
                [component],
            )
        else:
            existing.consumers.append(component)
        return
    if not isinstance(filepath, (str, Path)):
        return
    try:
        inspection = _inspect_asset_path(filepath, owner_dir=module_dir(owner), search_dirs=engine.settings.dirs)
        resolved = inspection.resolved_path
        if resolved is None:
            return
        content = resolved.read_text(encoding="utf-8")
        file_key: tuple[object, ...] = ("file", resolved.resolve())
    except (OSError, UnicodeError):
        return
    existing = sources.get(file_key)
    if existing is None:
        sources[file_key] = _BrowserSource(str(resolved), content, [component])
    else:
        existing.consumers.append(component)


def _checker_component_props(
    engine: Citry,
    component: type[Component],
) -> tuple[BrowserProp, ...] | None:
    """Read one current static `$component({props})` contract from disk."""
    try:
        owner, inline, filepath = _find_pair_declaration(component, "js", "js_file")
    except (Exception, SystemExit):  # noqa: BLE001 - project code failures degrade this check
        return None
    if _effective_class_value(component, "js_lang") is not None:
        return None
    if type(inline) is str:
        return browser_component_props(normalize_inline_asset(inline))
    if not isinstance(filepath, (str, Path)):
        return None
    try:
        inspection = _inspect_asset_path(
            filepath,
            owner_dir=module_dir(owner),
            search_dirs=engine.settings.dirs,
        )
        if inspection.resolved_path is None:
            return None
        source = inspection.resolved_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    return browser_component_props(source)


def _check_browser_source(
    engine: Citry,
    source: _BrowserSource,
    profiles: dict[str, dict[str, frozenset[str]]],
) -> list[CheckFinding]:
    """Check component initializer variables and literal server calls."""
    consumers: list[ComponentJsLintConsumer] = []
    i18n = engine.extensions.get_extension("i18n")
    i18n_configured = getattr(i18n, "configured", False) is True
    for component in source.consumers:
        lint = _component_lint_info(engine, component)
        known_names = {variable.name for variable in lint.component_js_globals}
        if i18n_configured:
            known_names.add("i18n")
        consumers.append(
            ComponentJsLintConsumer(
                known_names=frozenset(known_names),
                rule_unknown_component_js_variable=lint.rule_unknown_component_js_variable,
            )
        )
    findings = [
        _browser_source_finding(
            source.origin,
            source.content,
            finding.start_index,
            finding.end_index,
            finding.code,
            finding.message,
            finding.severity,
        )
        for finding in lint_unknown_component_js_variables(source.content, consumers)
    ]
    expression = BrowserExpression(
        source.content,
        0,
        len(source.content.encode("utf-8")),
        "statement",
        "component-js",
    )
    findings.extend(
        _browser_i18n_profile_findings(
            source.origin,
            source.content,
            expression,
            profiles,
            owners=frozenset({"i18n"}),
        )
    )
    event_names = _shared_event_names(source.consumers)
    if event_names is None:
        return findings
    findings.extend(_unknown_event_findings(source.origin, source.content, expression, event_names))
    return findings


def _browser_source_finding(
    origin: str,
    source: str,
    start_index: int,
    end_index: int,
    code: str,
    message: str,
    severity: Literal["warning", "error"],
) -> CheckFinding:
    """Map one portable browser-source finding to authored coordinates."""
    start = _byte_offset_coordinates(source, start_index)
    end = _byte_offset_coordinates(source, end_index)
    return CheckFinding(
        origin,
        message,
        code,
        severity=severity,
        start_index=start_index,
        end_index=end_index,
        line=start[0],
        column=start[1],
        end_line=end[0],
        end_column=end[1],
    )


def _shared_event_names(consumers: list[type[Component]]) -> frozenset[str] | None:
    if not consumers:
        return None
    names: list[set[str]] = []
    for component in consumers:
        info = _component_events_info(component)
        names.append(set(info.handlers) if info is not None else set())
    common = names[0]
    for candidate in names[1:]:
        common.intersection_update(candidate)
    return frozenset(common)


def _unknown_event_findings(
    origin: str,
    authored_source: str,
    expression: BrowserExpression,
    known_names: frozenset[str],
) -> list[CheckFinding]:
    findings: list[CheckFinding] = []
    for call in browser_literal_calls(expression, SERVER_EVENT_CALL_NAMES):
        if call.value in known_names:
            continue
        findings.append(
            _unknown_event_finding(
                origin,
                authored_source,
                call.value,
                call.start_index,
                call.end_index,
            )
        )
    return findings


def _unknown_event_finding(
    origin: str,
    authored_source: str,
    name: str,
    start_index: int,
    end_index: int,
) -> CheckFinding:
    start = _byte_offset_coordinates(authored_source, start_index)
    end = _byte_offset_coordinates(authored_source, end_index)
    return CheckFinding(
        origin,
        render_diagnostic(BROWSER_UNKNOWN_SERVER_EVENT, name=name),
        BROWSER_UNKNOWN_SERVER_EVENT,
        start_index=start_index,
        end_index=end_index,
        line=start[0],
        column=start[1],
        end_line=end[0],
        end_column=end[1],
    )


def _browser_template_finding(
    origin: str,
    source: str,
    start_index: int,
    end_index: int,
    code: str,
    **parameters: str,
) -> CheckFinding:
    """Map one catalog-backed browser check to authored template coordinates."""
    start = _byte_offset_coordinates(source, start_index)
    end = _byte_offset_coordinates(source, end_index)
    return CheckFinding(
        origin,
        render_diagnostic(code, **parameters),
        code,
        start_index=start_index,
        end_index=end_index,
        line=start[0],
        column=start[1],
        end_line=end[0],
        end_column=end[1],
    )


def _unknown_component_findings(
    origin: str,
    template: Template,
    known_names: set[str],
) -> list[CheckFinding]:
    findings: list[CheckFinding] = []
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node: Any = element._0
        tag_token = node.start_tag.name
        tag_name = tag_token.content
        normalized_tag = f"c-{tag_name[2:].lower()}" if tag_name.startswith("c-") else None
        if normalized_tag is not None and normalized_tag not in RESERVED_TAG_NAMES:
            component_name = normalized_tag.removeprefix("c-")
            if component_name not in known_names:
                line, column = tag_token.line_col
                findings.append(
                    CheckFinding(
                        origin,
                        render_diagnostic(TEMPLATE_UNKNOWN_COMPONENT, tag=tag_name),
                        code=TEMPLATE_UNKNOWN_COMPONENT,
                        start_index=tag_token.start_index,
                        end_index=tag_token.end_index,
                        line=line,
                        column=column,
                    )
                )
        body = getattr(node, "body", None)
        if body is not None:
            findings.extend(_unknown_component_findings(origin, body, known_names))
    return findings


def _effective_class_value(comp_cls: type[Component], name: str) -> object:
    for candidate in _static_class_mro(comp_cls):
        attrs = _static_class_dict(candidate)
        if name in attrs:
            return attrs[name]
    return None


def _class_label(comp_cls: type[Component]) -> str:
    return _safe_class_import_path(comp_cls) or "Component"


def _field_coordinates(
    source_file: Path | None,
    qualname: str | None,
    name: str,
) -> tuple[int, int, int, int, int, int] | None:
    if source_file is None or qualname is None or "<locals>" in qualname:
        return None
    try:
        with tokenize.open(source_file) as source_stream:
            source = source_stream.read()
        tree = ast.parse(source)
    except (OSError, SyntaxError, UnicodeError):
        return None
    body: list[ast.stmt] = tree.body
    class_node: ast.ClassDef | None = None
    for part in qualname.split("."):
        matches = [statement for statement in body if isinstance(statement, ast.ClassDef) and statement.name == part]
        if len(matches) != 1:
            return None
        class_node = matches[0]
        body = class_node.body
    if class_node is None:
        return None
    targets = [
        statement.target
        for statement in class_node.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
        and statement.target.id == name
    ]
    if len(targets) != 1:
        return None
    target = targets[0]
    lines = source.splitlines(keepends=True)
    start_index = sum(len(line.encode("utf-8")) for line in lines[: target.lineno - 1]) + target.col_offset
    end_index = start_index + len(name.encode("utf-8"))
    return (
        start_index,
        end_index,
        target.lineno - 1,
        target.col_offset,
        target.lineno - 1,
        target.col_offset + len(name),
    )


def _range_source(source: str, value_range: Any) -> str | None:
    if value_range is None:
        return None
    start = _lsp_position_char_offset(source, value_range.start.line, value_range.start.character)
    end = _lsp_position_char_offset(source, value_range.end.line, value_range.end.character)
    return source[start:end] if start is not None and end is not None and start <= end else None


def _lsp_range_coordinates(source: str, value_range: Any) -> tuple[int, int, int, int, int, int] | None:
    start_char = _lsp_position_char_offset(source, value_range.start.line, value_range.start.character)
    end_char = _lsp_position_char_offset(source, value_range.end.line, value_range.end.character)
    if start_char is None or end_char is None:
        return None
    return (
        len(source[:start_char].encode("utf-8")),
        len(source[:end_char].encode("utf-8")),
        value_range.start.line,
        value_range.start.character,
        value_range.end.line,
        value_range.end.character,
    )


def _lsp_position_char_offset(source: str, line: int, character: int) -> int | None:
    lines = source.splitlines(keepends=True)
    if line < 0 or line >= len(lines):
        return None
    content = lines[line].removesuffix("\n").removesuffix("\r")
    units = 0
    for index, char in enumerate(content):
        if units == character:
            return sum(len(item) for item in lines[:line]) + index
        units += len(char.encode("utf-16-le")) // 2
        if units > character:
            return None
    return sum(len(item) for item in lines[:line]) + len(content) if units == character else None


def _source_finding(
    *,
    origin: str,
    message: str,
    code: str,
    severity: Literal["warning", "error"],
    coordinates: tuple[int, int, int, int, int, int] | None,
) -> CheckFinding:
    if coordinates is None:
        return CheckFinding(origin, message, code, severity)
    start_index, end_index, line, column, end_line, end_column = coordinates
    return CheckFinding(
        origin,
        message,
        code,
        severity,
        start_index,
        end_index,
        line,
        column,
        end_line,
        end_column,
    )


def _byte_offset_coordinates(source: str, offset: int) -> tuple[int, int]:
    prefix = source.encode("utf-8")[:offset].decode("utf-8")
    line = prefix.count("\n")
    current = prefix.rsplit("\n", 1)[-1]
    return line, len(current.encode("utf-16-le")) // 2


def _error_detail(exc: BaseException) -> str:
    detail = str(exc)
    error_type = type(exc).__name__
    return f"{error_type}: {detail}" if detail else error_type


def _static_notice_finding(path: Path, component_name: str, message: str) -> CheckFinding:
    """Give conservative discovery notices a stable condition-specific code."""
    prefix = "unsupported non-None template_lang ("
    if message.startswith(prefix) and "); template skipped" in message:
        value_type = message[len(prefix) : message.index("); template skipped")]
        code = CHECK_TEMPLATE_LANGUAGE_UNSUPPORTED
        rendered = render_diagnostic(code, type=value_type)
    else:
        code = CHECK_TEMPLATE_DECLARATION
        rendered = render_diagnostic(code, detail=message)
    return CheckFinding(f"{path} ({component_name}.template)", rendered, code)


__all__: list[str] = []
