"""Conservative authored-template analysis for ``citry check``."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
import textwrap
import tokenize
import weakref
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass, replace
from dataclasses import field as dataclass_field
from pathlib import Path
from types import (
    GetSetDescriptorType,
    MappingProxyType,
    MemberDescriptorType,
    ModuleType,
    SimpleNamespace,
    WrapperDescriptorType,
)
from typing import TYPE_CHECKING, Any, Literal, cast

from citry._app_selection import CheckAppSelection, app_failure_message
from citry._authored_expression import parse_authored_expression
from citry._class_introspection import (
    _safe_class_import_path,
    _safe_class_text,
    _static_class_dict,
    _static_class_mro,
)
from citry._component_introspection import _loaded_python_file
from citry._css_lint import (
    CssLintFinding,
    TemplateCss,
    code_custom_properties,
    lint_misspelled_css_classes,
    lint_undeclared_css_classes,
    lint_undeclared_css_variables,
    style_type_is_css,
    template_css,
)
from citry._css_scan import ClassPattern, CssDeclarations, scan_css
from citry._diagnostic_catalog import (
    BROWSER_INCOMPATIBLE_COMPONENT_PROP,
    BROWSER_INCOMPATIBLE_SERVER_EVENT_FIELD,
    BROWSER_INVALID_STATE_BINDING_TARGET,
    BROWSER_MISSING_COMPONENT_KEY,
    BROWSER_MISSING_COMPONENT_PROP,
    BROWSER_MISSING_FORM_FIELD,
    BROWSER_MISSING_SERVER_EVENT_FIELD,
    BROWSER_UNKNOWN_FORM_FIELD,
    BROWSER_UNKNOWN_SERVER_EVENT,
    BROWSER_UNKNOWN_SERVER_EVENT_FIELD,
    BROWSER_UNKNOWN_STATE_FIELD,
    CHECK_PYTHON_SOURCE_UNREADABLE,
    CHECK_TEMPLATE_DECLARATION,
    CHECK_TEMPLATE_FILE_NOT_FOUND,
    CHECK_TEMPLATE_FILE_UNREADABLE,
    CHECK_TEMPLATE_LANGUAGE_UNSUPPORTED,
    CHECK_TEMPLATE_NAMESPACE_UNAVAILABLE,
    CHECK_TEMPLATE_NOT_CHECKED,
    CHECK_TEMPLATE_VALUE_INVALID,
    CHECK_URL_CHECKER_FAILED,
    CHECK_URL_CHECKER_MISSING,
    I18N_ARGUMENT_INVALID,
    I18N_CATALOG_INVALID,
    I18N_CLIENT_MESSAGE_INVALID,
    I18N_CROSS_LANGUAGE_FALLBACK,
    I18N_RICH_MESSAGE_FALLBACK,
    I18N_UNKNOWN_MESSAGE,
    JS_DATA_UNSUPPORTED_TYPE,
    PARSE_CONFIGURATION,
    TEMPLATE_MARKER_NAME_INVALID,
    TEMPLATE_UNDECLARED_TEMPLATE_DATA_KEY,
    TEMPLATE_UNKNOWN_COMPONENT,
)
from citry._diagnostics import render_diagnostic
from citry._i18n_guards import i18n_configured_guarded_calls
from citry._inline_assets import normalize_inline_asset
from citry._json_wire import SECRET_UNSUPPORTED_REASON
from citry._linting import _component_lint_info
from citry._markup_lint import MARKUP_LINT_RULES
from citry._path_checks import PathVerdict, check_paths, has_path_checkers, is_citry_path
from citry._provide_keys import inject_key_scopes
from citry._registry_lint import (
    ServerEventPayload,
    ServerEventPayloadFinding,
    server_event_calls,
    server_event_form_findings,
    server_event_forms,
    server_event_payload,
    server_event_payload_findings,
    template_has_vue_attributes,
    template_urls,
    unkeyed_repeated_component_calls,
    unknown_inject_key_findings,
    unknown_url_findings,
)
from citry._source_lines import line_break_count, source_lines
from citry._symbol_table import symtable
from citry._template_data_source import (
    TemplateDataSourceShape,
    analyze_css_data_source,
    analyze_template_data_source,
)
from citry._vue.json_data import _json_plain, _secret_key_path, _SecretInBrowserDataError
from citry._vue_compile_lint import lint_vue_compile
from citry._walk import Call, run
from citry._wire_classes import KwargsWireClasses, kwargs_wire_classes
from citry.analysis import (
    SERVER_EVENT_CALL_NAMES,
    AlpineAttributeFinding,
    AlpineAttributeLintConsumer,
    AttributeValueFinding,
    AttributeValueLintConsumer,
    BrowserComponentPropContribution,
    BrowserComponentPropSite,
    BrowserComponentSourceAnalysis,
    BrowserExpression,
    BrowserProp,
    ComponentJsLintConsumer,
    ComponentJsLintFinding,
    CssVariableFinding,
    JsonWireType,
    MarkupLintConsumer,
    MarkupLintFinding,
    MisspelledDirectiveFinding,
    MisspelledDirectiveLintConsumer,
    TemplateLintConsumer,
    UntracedComponentTemplate,
    VueLintConsumer,
    VueLintFinding,
    analyze_browser_component_source,
    analyze_js_data_source,
    browser_component_prop_findings,
    browser_component_prop_sites,
    browser_component_props,
    browser_declarative_events,
    browser_expressions,
    browser_i18n_binding_directives,
    browser_i18n_calls_checkable,
    browser_i18n_profile_calls,
    browser_literal_calls,
    browser_literal_wire_type,
    browser_state_binding_target_errors,
    browser_state_bindings,
    component_js_i18n_owners,
    discover_python_templates,
    discover_untraced_component_templates,
    json_wire_type_from_annotation,
    json_wire_type_from_expression,
    lint_alpine_attributes,
    lint_attribute_values,
    lint_component_js_prop_assignments,
    lint_invalid_vue_expressions,
    lint_markup,
    lint_misspelled_css_variables,
    lint_misspelled_directives,
    lint_prop_assignments,
    lint_undeclared_component_js_emits,
    lint_undeclared_component_listeners,
    lint_undeclared_template_emits,
    lint_unknown_component_js_members,
    lint_unknown_component_js_variables,
    lint_unknown_template_variables,
    lint_unknown_vue_variables,
    lint_vue_python_variables,
    mark_literal_findings,
    project_module_exists,
)
from citry.assets import (
    _find_pair_declaration,
    _inline_origin,
    _inspect_asset_path,
    loaded_messages_source,
    module_dir,
)
from citry.autodiscovery import _iter_py_files
from citry.component import Component
from citry.component_registry import NotRegistered
from citry.constness import Const, _unwrap_const_markers
from citry.ext.dependencies.types import Style
from citry.ext.events.csrf import csrf_field_names
from citry.ext.events.extension import _component_events_info
from citry.secret import Secret
from citry.settings import LintSettings
from citry.tag_rules import build_tag_rules
from citry.util.html import decode_attribute_entities
from citry_core.i18n import I18nCompileError
from citry_core.template_parser import (
    RESERVED_TAG_NAMES,
    ParseOptions,
    TemplateElement,
    parse_diagnostic,
    parse_template,
)
from citry_core.template_parser import (
    ForeignSpan as CoreForeignSpan,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable

    from citry.citry import Citry
    from citry.ext.i18n.extension import I18nExtension
    from citry.settings import LintSeverity
    from citry_core.template_parser import TagRules, Template


TRANSFORM_NOTE = "extension-transformed template validation is unavailable; checking authored Citry source"
# Which text a finding's range counts in: the whole file its origin names, or
# the inline class attribute (`template`, `js`, `css`, `messages`) it names.
# `citry.component_graph.ComponentGraphLocation.source_kind` uses the same values.
SourceKind = Literal["file", "inline"]
# A line break other than "\n": CR LF or a lone CR, which Python reads as "\n".
_CR_LINE_BREAK = re.compile(r"\r\n|\r")

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
    """
    One source or template finding.

    A finding with a position carries it twice: ``start_index`` and
    ``end_index`` are UTF-8 byte offsets, and the line and column fields count
    from 0, with columns in UTF-16 code units, as the Language Server Protocol
    does. ``source_kind`` says which text both count in: ``"file"`` for the
    file that ``origin`` names, ``"inline"`` for the inline string (such as a
    class's ``template``) that ``origin`` names, after its shared indentation
    is removed.
    """

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
    source_kind: SourceKind | None = None


@dataclass(frozen=True, slots=True)
class CheckReport:
    """
    Complete output and exit status for one check run.

    ``skipped_library_findings`` counts, per library name, the findings
    left out because they are in components a registered library provides.
    ``library_owners`` tells which findings those are, so
    ``citry check --types`` can leave out its own findings in the same
    components; it is ``None`` when the run reports library findings or
    checked no registry.
    """

    findings: tuple[CheckFinding, ...] = ()
    app_failure: str | None = None
    notes: tuple[str, ...] = ()
    skipped_library_findings: tuple[tuple[str, int], ...] = ()
    library_owners: _LibraryOwners | None = dataclass_field(default=None, compare=False, repr=False)

    @property
    def all_notes(self) -> tuple[str, ...]:
        """The notes to print, ending with the count of left-out library findings when there are any."""
        return (*self.notes, *library_findings_note(dict(self.skipped_library_findings)))

    def __post_init__(self) -> None:
        # A position without its base cannot be placed by a tool reading the
        # report, so a producer that forgets to say which text it counts in
        # fails here rather than shipping an ambiguous range.
        for finding in self.findings:
            if finding.start_index is not None and finding.source_kind is None:
                msg = f"check finding {finding.code} at {finding.origin} has a range but no source_kind"
                raise ValueError(msg)

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
    # Whether `content` is a whole file or an inline class attribute, which
    # tells a reader of the report where line 0 of a finding's range is.
    source_kind: SourceKind


@dataclass(slots=True)
class _BrowserSource:
    """One authored component-JavaScript source and all registry consumers."""

    origin: str
    content: str
    consumers: list[type[Component]]
    # As for `_TemplateSource`: a whole file, or an inline `js` or `css` string.
    source_kind: SourceKind


def check_project(selection: CheckAppSelection, cwd: Path, *, include_libraries: bool = False) -> CheckReport:
    """
    Check a registry when one is available, otherwise scan definite literals.

    Findings in components that a registered library provides are left out
    and counted in a note, unless ``include_libraries`` or
    ``LintSettings.include_libraries`` asks for them: the app's author
    cannot change that code, so they would only hide the app's own findings.
    """
    if selection.failure is not None:
        findings, notes = _check_static(cwd)
        return CheckReport(findings=tuple(findings), app_failure=selection.failure, notes=tuple(notes))
    if selection.engine is None:
        findings, notes = _check_static(cwd)
        return CheckReport(findings=tuple(findings), notes=tuple(notes))

    engine = selection.engine
    try:
        engine.initialize()
        registrations = engine.components
        rules = build_tag_rules(engine)
    except (Exception, SystemExit) as exc:  # noqa: BLE001 - tooling degrades on project-code failures
        findings, notes = _check_static(cwd)
        return CheckReport(findings=tuple(findings), app_failure=app_failure_message(exc), notes=tuple(notes))

    findings, notes, origin_consumers = _check_registry(engine, registrations, rules)
    # An inject key finding points into the component's Python file.
    findings.extend(_counted_in(_unknown_inject_key_findings(engine, registrations, cwd), "file"))
    if include_libraries or engine.settings.lint.include_libraries:
        return CheckReport(findings=tuple(findings), notes=(TRANSFORM_NOTE, *notes))
    owners = _LibraryOwners(engine, origin_consumers)
    kept, skipped = owners.split(findings)
    return CheckReport(
        findings=tuple(kept),
        notes=(TRANSFORM_NOTE, *notes),
        skipped_library_findings=tuple(sorted(skipped.items())),
        library_owners=owners,
    )


def library_findings_note(skipped: Mapping[str, int]) -> tuple[str, ...]:
    """The one note that says how many findings were left out and which libraries they came from, or none."""
    total = sum(skipped.values())
    if total == 0:
        return ()
    names = ", ".join(repr(name) for name in sorted(skipped))
    noun = "library" if len(skipped) == 1 else "libraries"
    findings = "finding" if total == 1 else "findings"
    return (
        f"left out {total} {findings} in components from the registered {noun} {names}; "
        "pass --include-libraries to report them",
    )


class _LibraryOwners:
    """
    Which registered components each finding belongs to, and which of them a library provides.

    A finding names its place as text: a component's import path with the
    attribute it is about (``pkg.mod.Card.template``), a file path with a
    component in brackets (``/src/card.py (pkg.mod.Card.js_data)``), or a
    file path with a line and column (``/src/card.py:3:5``). A finding
    belongs to a library only when every component it can be traced to
    comes from a library; a finding that names no known component is kept.
    """

    def __init__(self, engine: Citry, origin_consumers: Mapping[str, set[type[Component]]]) -> None:
        # A library's own classes are the concrete components it installed.
        self._library_of = engine._library_names_by_component()
        self._by_origin: dict[str, set[type[Component]]] = {}
        for origin, consumers in origin_consumers.items():
            self._by_origin.setdefault(_origin_path_key(origin), set()).update(consumers)
        self._by_label: dict[str, set[type[Component]]] = {}
        unique = {id(comp_cls): comp_cls for comp_cls in engine.components.values()}
        for comp_cls in unique.values():
            self._by_label.setdefault(_class_label(comp_cls), set()).add(comp_cls)
            module_file = _loaded_python_file(comp_cls)
            if module_file is not None:
                self._by_origin.setdefault(_origin_path_key(str(module_file)), set()).add(comp_cls)
            messages_file = _resolved_messages_file(engine, comp_cls)
            if messages_file is not None:
                self._by_origin.setdefault(_origin_path_key(str(messages_file)), set()).add(comp_cls)

    def library(self, origin: str) -> str | None:
        """The library a finding at ``origin`` is counted under, or ``None`` when an app component may own it."""
        owners = self._owners(origin)
        if not owners:
            return None
        libraries = {self._library_of.get(owner) for owner in owners}
        if None in libraries:
            return None
        # Code shared by two libraries, such as a theme library built on
        # another one, is still no app's code; it counts under one name.
        return min(cast("set[str]", libraries))

    def split(self, findings: Iterable[CheckFinding]) -> tuple[list[CheckFinding], dict[str, int]]:
        """Keep the findings an app component may own, and count the others per library."""
        kept: list[CheckFinding] = []
        skipped: dict[str, int] = {}
        for finding in findings:
            library = self.library(finding.origin)
            if library is None:
                kept.append(finding)
            else:
                skipped[library] = skipped.get(library, 0) + 1
        return kept, skipped

    def _owners(self, origin: str) -> set[type[Component]]:
        match = _ORIGIN_SHAPE.fullmatch(origin)
        place = origin if match is None else match["place"]
        label = None if match is None else match["label"]
        # A component in brackets is the one the finding is about, even when
        # the file holds code it inherits from another component.
        if label is not None:
            labelled = self._label_owners(label)
            if labelled:
                return labelled
        # A template, script, or stylesheet names exactly the components that use it.
        owners = self._by_origin.get(_origin_path_key(place))
        if owners:
            return owners
        # An inline `messages` string is named `<file>::<Class>.messages`.
        file_part, separator, _ = place.partition("::")
        if separator:
            owners = self._by_origin.get(_origin_path_key(file_part))
            if owners:
                return owners
        return self._label_owners(place)

    def _label_owners(self, text: str) -> set[type[Component]]:
        # The longest import path that the text starts with names the
        # component, so `pkg.mod.Card.JsData.field` finds `pkg.mod.Card`.
        candidate = text
        while candidate:
            owners = self._by_label.get(candidate)
            if owners:
                return owners
            candidate, _, _ = candidate.rpartition(".")
        return set()


def _resolved_messages_file(engine: Citry, comp_cls: type[Component]) -> Path | None:
    """The messages file a component reads, resolved as for its template file, or ``None``."""
    with suppress(Exception):
        owner, _inline, filepath = _find_pair_declaration(comp_cls, "messages", "messages_file")
        if isinstance(filepath, (str, Path)):
            inspection = _inspect_asset_path(filepath, owner_dir=module_dir(owner), search_dirs=engine.settings.dirs)
            if inspection.resolved_path is not None:
                return inspection.resolved_path.resolve()
    return None


# A place with an optional `:line:column` and an optional `(component label)`.
_ORIGIN_SHAPE = re.compile(r"(?P<place>.+?)(?::\d+:\d+)?(?: \((?P<label>[^()]*)\))?")


def _origin_path_key(place: str) -> str:
    """The text two origins share when they name the same file, however each spelled the path."""
    if not (place.startswith(("/", "\\")) or re.match(r"[A-Za-z]:[\\/]", place)):
        return place
    with suppress(OSError, ValueError):
        return str(Path(place).resolve())
    return place


def _check_registry(
    engine: Citry,
    registrations: Mapping[str, type[Component]],
    rules: Mapping[str, TagRules],
) -> tuple[list[CheckFinding], list[str], dict[str, set[type[Component]]]]:
    """
    Read each authored registry template directly and continue after failures.

    Returns the findings, the notes about checks that could not run, such
    as link paths no web framework integration could answer for, and the
    components that use each template, script, and stylesheet, keyed by
    the origin its findings name.
    """
    known_names = {name.lower() for name in registrations}
    unique_classes = {id(comp_cls): comp_cls for comp_cls in registrations.values()}
    components = sorted(unique_classes.values(), key=_class_label)
    findings: list[CheckFinding] = []
    sources: dict[tuple[object, ...], _TemplateSource] = {}
    browser_sources: dict[tuple[object, ...], _BrowserSource] = {}
    css_sources: dict[tuple[object, ...], _BrowserSource] = {}
    i18n_manifest: dict[str, dict[str, dict[str, Any]]] | None = None
    i18n_profiles: dict[str, dict[str, frozenset[str]]] | None = None
    links = _LinkCheck(verdicts={}, failures={})
    # The CSS rules compare each template with every component's CSS, so the
    # template facts they need are kept until every template has been read.
    css_templates: list[tuple[_TemplateSource, TemplateCss]] = []

    i18n = engine.extensions._extensions_by_name.get("i18n")
    # Component messages make i18n available without configuring it; only a
    # configured app has format profiles and gives the browser `$i18n`.
    i18n_configured = i18n is not None and getattr(i18n, "configured", False) is True
    if i18n is not None:
        try:
            # Reading `available` compiles every component's messages, so an
            # invalid catalog raises here and must become a finding, not a crash.
            i18n_available = bool(getattr(i18n, "available", False))
            if i18n_available:
                i18n_extension = cast("I18nExtension", i18n)
                i18n_profiles = _i18n_profile_inventory(i18n_extension)
                i18n_extension._load_project_sources()
                compiled_catalog = i18n_extension._compiled_catalog
                if compiled_catalog is None:
                    raise ValueError("The i18n compiler did not produce a project artifact.")
                artifact = json.loads(compiled_catalog.artifact_json())
                catalog_texts = _i18n_catalog_texts(engine, i18n_extension, components)
                findings.extend(
                    _i18n_diagnostic_finding(
                        diagnostic,
                        catalog_texts,
                        message=diagnostic["message"],
                        code=diagnostic["code"],
                        severity=diagnostic["severity"],
                    )
                    for diagnostic in artifact["diagnostics"]
                )
                i18n_manifest = artifact["manifest"]
        except (Exception, SystemExit) as exc:  # noqa: BLE001 - one catalog error becomes one finding
            message = f"The project i18n catalog is invalid: {_error_detail(exc)}"
            # A compile error carries the source position of the bad message,
            # so point the finding there when the compiler supplied one.
            diagnostic = _i18n_compile_diagnostic(exc)
            if diagnostic is None:
                findings.append(CheckFinding("i18n catalog", message, I18N_CATALOG_INVALID))
            else:
                findings.append(
                    _i18n_diagnostic_finding(
                        diagnostic,
                        _i18n_catalog_texts(engine, cast("I18nExtension", i18n), components),
                        message=message,
                        code=I18N_CATALOG_INVALID,
                    )
                )

    for comp_cls in components:
        if engine._is_builtin_component(comp_cls):
            continue
        if i18n_manifest is not None:
            # Text that falls back to another language still renders, so the
            # component's own Lint class or the app setting decides how loudly
            # check reports it.
            fallback_severity = _component_lint_info(engine, comp_cls).rule_i18n_cross_language_fallback
            findings.extend(_client_message_findings(comp_cls, i18n_manifest, fallback_severity=fallback_severity))
            # These read the component's Python file, so ranges count in it.
            findings.extend(
                _counted_in(
                    _i18n_python_findings(
                        comp_cls,
                        i18n_manifest,
                        i18n_profiles or {},
                        i18n_configured=i18n_configured,
                        fallback_severity=fallback_severity,
                    ),
                    "file",
                )
            )
        findings.extend(_counted_in(_check_js_data_types(engine, comp_cls), "file"))
        findings.extend(_undeclared_template_data_key_findings(engine, comp_cls))
        _collect_browser_source(engine, comp_cls, browser_sources)
        _collect_browser_source(engine, comp_cls, css_sources, kind="css")
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
                    source_kind="inline",
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
            sources[file_key] = _TemplateSource(
                origin=str(resolved), content=content, consumers=[comp_cls], source_kind="file"
            )
        else:
            existing.consumers.append(comp_cls)

    component_props: dict[type[Component], tuple[BrowserProp, ...] | None] = {}
    for browser_source in browser_sources.values():
        declared = browser_component_props(browser_source.content)
        for consumer in browser_source.consumers:
            if consumer not in component_props:
                component_props[consumer] = declared
            elif component_props[consumer] != declared:
                component_props[consumer] = None

    # The repeated-component rule reads a child's template to see whether it
    # makes the page use Vue.
    component_templates = {consumer: source.content for source in sources.values() for consumer in source.consumers}
    for source in sources.values():
        try:
            lint_consumers = tuple(_checker_lint_consumer(engine, component) for component in source.consumers)
            vue_lint_consumers = tuple(_checker_vue_lint_consumer(engine, component) for component in source.consumers)
            alpine_lint_consumers = tuple(
                _checker_alpine_lint_consumer(engine, component) for component in source.consumers
            )
            attribute_value_lint_consumers = tuple(
                AttributeValueLintConsumer(_component_lint_info(engine, component).rule_invalid_attribute_value)
                for component in source.consumers
            )
            # Each consumer's JavaScript is read once here, for the directives
            # it registers and for whether Vue passes a parent's attributes on.
            js_analyses = {component: _disk_component_js_analysis(engine, component) for component in source.consumers}
            directive_lint_consumers = tuple(
                MisspelledDirectiveLintConsumer(
                    _component_lint_info(engine, component).rule_misspelled_directive,
                    declared_directives=_declared_directives(js_analyses[component]),
                )
                for component in source.consumers
            )
            markup_lint_consumers = tuple(
                _checker_markup_lint_consumer(engine, component, js_analyses[component])
                for component in source.consumers
            )
            foreign_options = _checker_foreign_options(
                engine,
                source,
                content=source.content,
                template_kind="primary",
            )
        except (Exception, SystemExit) as exc:  # noqa: BLE001 - one namespace must not stop the batch
            findings.append(
                CheckFinding(
                    source.origin,
                    render_diagnostic(CHECK_TEMPLATE_NAMESPACE_UNAVAILABLE, detail=_error_detail(exc)),
                    CHECK_TEMPLATE_NAMESPACE_UNAVAILABLE,
                )
            )
            continue

        def nested_foreign_options(
            value: str,
            checked_source: _TemplateSource = source,
        ) -> ParseOptions | None:
            return _checker_foreign_options(
                engine,
                checked_source,
                content=value,
                template_kind="nested",
            )

        findings.extend(
            _check_template(
                source,
                rules=rules,
                known_names=known_names,
                engine=engine,
                lint_consumers=lint_consumers,
                vue_lint_consumers=vue_lint_consumers,
                alpine_lint_consumers=alpine_lint_consumers,
                attribute_value_lint_consumers=attribute_value_lint_consumers,
                directive_lint_consumers=directive_lint_consumers,
                markup_lint_consumers=markup_lint_consumers,
                i18n_manifest=i18n_manifest,
                i18n_profiles=i18n_profiles,
                i18n_configured=i18n_configured,
                foreign_options=foreign_options,
                nested_foreign_options=nested_foreign_options,
                component_props=component_props,
                component_templates=component_templates,
                links=links,
                css_templates=css_templates,
            )
        )
    for browser_source in browser_sources.values():
        findings.extend(
            _counted_in(
                _check_browser_source(engine, browser_source, i18n_profiles or {}, i18n_configured=i18n_configured),
                browser_source.source_kind,
            )
        )
    known_css = _KnownCss(engine, components, css_sources, browser_sources, css_templates)
    findings.extend(_css_class_findings(engine, css_templates, known_css))
    for css_source in css_sources.values():
        findings.extend(_counted_in(_check_css_source(engine, css_source, known_css), css_source.source_kind))
    origin_consumers: dict[str, set[type[Component]]] = {}
    for template_source in sources.values():
        origin_consumers.setdefault(template_source.origin, set()).update(template_source.consumers)
    for browser_source in (*browser_sources.values(), *css_sources.values()):
        origin_consumers.setdefault(browser_source.origin, set()).update(browser_source.consumers)
    return findings, links.notes(), origin_consumers


def _checker_foreign_options(
    engine: Citry,
    source: _TemplateSource,
    *,
    content: str,
    template_kind: Literal["primary", "nested"],
) -> ParseOptions | None:
    """Collect one consumer-independent foreign-span view for checking."""
    if not source.consumers:
        return None
    digest = hashlib.sha256()
    digest.update(source.origin.encode())
    digest.update(b"\0")
    digest.update(template_kind.encode())
    digest.update(b"\0")
    digest.update(content.encode())
    template_id = f"check:{digest.hexdigest()}"

    agreed_spans: tuple[CoreForeignSpan, ...] | None = None
    agreed_descriptor: tuple[tuple[object, ...], ...] | None = None
    for component in source.consumers:
        spans, _metadata = engine.extensions.on_template_foreign_spans(
            component,
            content,
            template_id=template_id,
            origin=source.origin,
            template_kind=template_kind,
        )
        typed_spans = cast("tuple[CoreForeignSpan, ...]", spans)
        descriptor = tuple(
            (
                span.start_byte,
                span.end_byte,
                span.provider,
                span.ordinal,
                span.may_control_body,
            )
            for span in typed_spans
        )
        if agreed_descriptor is None:
            agreed_spans = typed_spans
            agreed_descriptor = descriptor
        elif descriptor != agreed_descriptor:
            msg = (
                "components sharing this template disagree about its foreign source spans; "
                "Citry cannot check it as one source"
            )
            raise RuntimeError(msg)

    if not agreed_spans:
        return None
    return ParseOptions(list(agreed_spans))


def _check_static(cwd: Path) -> tuple[list[CheckFinding], list[str]]:
    """
    Parse literals conservatively matched to local component subclasses.

    Returns the findings, and a note for each class whose template this
    mode cannot check because its base class comes from another module.
    """
    findings: list[CheckFinding] = []
    notes: list[str] = []
    root = cwd.resolve()
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
        resolved = path.resolve()
        # A note, not a finding: nothing is wrong, but this mode skips the
        # template, and the developer should know which ones it skipped.
        notes.extend(
            _untraced_template_note(path, untraced)
            for untraced in discover_untraced_component_templates(
                source,
                is_project_module=_project_module_check(resolved, root),
            )
        )
        for region in discovery.regions:
            # Without the application only the owners' own Lint classes are
            # known; each unset rule keeps its no-application severity.
            findings.extend(
                _check_template(
                    _TemplateSource(
                        origin=f"{path} ({region.component_name}.template)",
                        content=region.source_map.template_source,
                        consumers=[],
                        source_kind="inline",
                    ),
                    alpine_lint_consumers=tuple(lint.alpine_consumer() for lint in region.owner_lint),
                    attribute_value_lint_consumers=tuple(
                        lint.attribute_value_consumer() for lint in region.owner_lint
                    ),
                    directive_lint_consumers=tuple(lint.directive_consumer() for lint in region.owner_lint),
                    markup_lint_consumers=tuple(lint.markup_consumer() for lint in region.owner_lint),
                ),
            )
    return findings, notes


def _check_template(
    source: _TemplateSource,
    *,
    rules: Mapping[str, TagRules] | None = None,
    known_names: set[str] | None = None,
    engine: Citry | None = None,
    lint_consumers: tuple[TemplateLintConsumer, ...] = (),
    vue_lint_consumers: tuple[VueLintConsumer, ...] = (),
    alpine_lint_consumers: tuple[AlpineAttributeLintConsumer, ...] = (),
    attribute_value_lint_consumers: tuple[AttributeValueLintConsumer, ...] = (),
    directive_lint_consumers: tuple[MisspelledDirectiveLintConsumer, ...] = (),
    markup_lint_consumers: tuple[MarkupLintConsumer, ...] = (),
    i18n_manifest: dict[str, dict[str, dict[str, Any]]] | None = None,
    i18n_profiles: dict[str, dict[str, frozenset[str]]] | None = None,
    i18n_configured: bool = False,
    foreign_options: ParseOptions | None = None,
    nested_foreign_options: Callable[[str], ParseOptions | None] | None = None,
    component_props: Mapping[type[Component], tuple[BrowserProp, ...] | None] | None = None,
    component_templates: Mapping[type[Component], str] | None = None,
    links: _LinkCheck | None = None,
    css_templates: list[tuple[_TemplateSource, TemplateCss]] | None = None,
) -> list[CheckFinding]:
    """
    Parse one source and, in registry mode, inspect component tag names.

    With ``css_templates``, the template's classes and CSS are appended to
    it, because the CSS rules can run only once every template has been read.
    """
    try:
        template = parse_template(
            source.content,
            user_rules=dict(rules) if rules is not None else None,
            options=foreign_options,
        )
    except (SyntaxError, ValueError) as exc:
        diagnostic = parse_diagnostic(exc)
        if diagnostic is None:
            return [CheckFinding(source.origin, str(exc), code=PARSE_CONFIGURATION)]
        if diagnostic.start_index is None or diagnostic.end_index is None:
            return [CheckFinding(source.origin, str(exc), code=diagnostic.code)]
        # The parser's own line and column count from 1, so the range is
        # rebuilt from its byte offsets to count like every other finding.
        return [
            _ranged_finding(
                source,
                str(exc),
                diagnostic.code,
                start_index=diagnostic.start_index,
                end_index=diagnostic.end_index,
            )
        ]
    findings = run(_unknown_component_findings(source, template, known_names)) if known_names is not None else []
    nested_parser = lambda value: parse_template(  # noqa: E731 - parser hook is passed as a value
        value,
        user_rules=dict(rules) if rules is not None else None,
        options=nested_foreign_options(value) if nested_foreign_options is not None else None,
    )
    for marker_finding in mark_literal_findings(template, parse_nested=nested_parser):
        line, column = _byte_offset_coordinates(source.content, marker_finding.start_index)
        end_line, end_column = _byte_offset_coordinates(source.content, marker_finding.end_index)
        findings.append(
            CheckFinding(
                source.origin,
                render_diagnostic(TEMPLATE_MARKER_NAME_INVALID, variant=marker_finding.reason),
                TEMPLATE_MARKER_NAME_INVALID,
                start_index=marker_finding.start_index,
                end_index=marker_finding.end_index,
                line=line,
                column=column,
                end_line=end_line,
                end_column=end_column,
            )
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
                fallback_severity=_shared_fallback_severity(engine, source.consumers),
            )
        )
    if not (foreign_options is not None and any(span.may_control_body for span in foreign_options.foreign_spans)):
        # The lint finding's own line and column count from 1, so the range
        # is rebuilt from its byte offsets to count like every other finding.
        findings.extend(
            _ranged_finding(
                source,
                finding.message,
                finding.code,
                start_index=finding.start_index,
                end_index=finding.end_index,
                severity=finding.severity,
            )
            for finding in lint_unknown_template_variables(template, lint_consumers)
        )
    # The Alpine, attribute-value, misspelled-directive, and HTML rules
    # need no component namespace, so static mode runs them too, with the
    # severities each owner's Lint class sets in its source. A rule no owner
    # sets uses its default, except that an invalid attribute value is then
    # a warning (see lint_attribute_values).
    browser_hosts = browser_expressions(template, parse_nested=nested_parser)
    attribute_findings: list[
        AlpineAttributeFinding | AttributeValueFinding | MisspelledDirectiveFinding | MarkupLintFinding
    ] = [
        *lint_alpine_attributes(template, alpine_lint_consumers, parse_nested=nested_parser),
        *lint_attribute_values(template, attribute_value_lint_consumers, parse_nested=nested_parser),
        *lint_misspelled_directives(template, directive_lint_consumers, parse_nested=nested_parser),
        *lint_markup(template, markup_lint_consumers, parse_nested=nested_parser),
        *lint_invalid_vue_expressions(template, browser_hosts, markup_lint_consumers, parse_nested=nested_parser),
        *lint_vue_compile(
            source.content,
            template,
            markup_lint_consumers,
            renders_in_place=_component_renders_in_place(engine) if engine is not None else None,
        ),
    ]
    for attribute_finding in attribute_findings:
        line, column = _byte_offset_coordinates(source.content, attribute_finding.start_index)
        end_line, end_column = _byte_offset_coordinates(source.content, attribute_finding.end_index)
        findings.append(
            CheckFinding(
                origin=source.origin,
                message=attribute_finding.message,
                code=attribute_finding.code,
                severity=attribute_finding.severity,
                start_index=attribute_finding.start_index,
                end_index=attribute_finding.end_index,
                line=line,
                column=column,
                end_line=end_line,
                end_column=end_column,
            )
        )
    if engine is not None and component_props is not None:
        sites = browser_component_prop_sites(template, parse_nested=nested_parser)

        def declared_props(site: BrowserComponentPropSite) -> tuple[BrowserProp, ...] | None:
            try:
                component = engine.get(site.tag.lower().removeprefix("c-"))
            except NotRegistered:
                return None
            return component_props.get(component)

        def literal_value_type(contribution: BrowserComponentPropContribution) -> JsonWireType:
            return browser_literal_wire_type(contribution.source)

        for prop_finding in browser_component_prop_findings(
            sites,
            declared_props=declared_props,
            value_type=literal_value_type,
        ):
            code = (
                BROWSER_MISSING_COMPONENT_PROP
                if prop_finding.kind == "missing"
                else BROWSER_INCOMPATIBLE_COMPONENT_PROP
            )
            parameters = (
                {"name": prop_finding.name, "tag": prop_finding.tag}
                if prop_finding.kind == "missing"
                else {
                    "name": prop_finding.name,
                    "expected": prop_finding.expected,
                    "actual": prop_finding.actual,
                }
            )
            line, column = _byte_offset_coordinates(source.content, prop_finding.start_index)
            end_line, end_column = _byte_offset_coordinates(source.content, prop_finding.end_index)
            findings.append(
                CheckFinding(
                    source.origin,
                    render_diagnostic(code, **parameters),
                    code,
                    start_index=prop_finding.start_index,
                    end_index=prop_finding.end_index,
                    line=line,
                    column=column,
                    end_line=end_line,
                    end_column=end_column,
                )
            )
    for expression in browser_hosts:
        findings.extend(
            _browser_i18n_profile_findings(
                source.origin,
                source.content,
                expression,
                i18n_profiles or {},
                i18n_configured=i18n_configured,
            )
        )
    for finding in (
        *lint_unknown_vue_variables(browser_hosts, vue_lint_consumers),
        *lint_vue_python_variables(browser_hosts, vue_lint_consumers),
    ):
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
    if engine is not None and source.consumers:
        findings.extend(_emit_findings(engine, source, browser_hosts))
        findings.extend(
            _missing_component_key_findings(
                engine,
                source,
                template,
                component_templates or {},
                parse_nested=nested_parser,
                rules=rules,
            )
        )
        findings.extend(_server_event_payload_findings(engine, source, template, parse_nested=nested_parser))
        if links is not None:
            findings.extend(_unknown_url_findings(engine, source, template, links, parse_nested=nested_parser))
        if css_templates is not None:
            css_templates.append((source, template_css(template, parse_nested=nested_parser)))
    for target_error in browser_state_binding_target_errors(template, parse_nested=nested_parser):
        findings.append(
            _browser_template_finding(
                source.origin,
                source.content,
                target_error.start_index,
                target_error.end_index,
                BROWSER_INVALID_STATE_BINDING_TARGET,
                detail=target_error.message,
            )
        )
    state_names = _shared_state_names(source.consumers)
    if state_names is not None:
        for binding in browser_state_bindings(template, parse_nested=nested_parser):
            if binding.name not in state_names:
                findings.append(
                    _browser_template_finding(
                        source.origin,
                        source.content,
                        binding.start_index,
                        binding.end_index,
                        BROWSER_UNKNOWN_STATE_FIELD,
                        name=binding.name,
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
    return _counted_in(findings, source.source_kind)


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
    i18n_configured: bool,
    owners: frozenset[str] = frozenset({"$i18n"}),
    proven_owner_spans: frozenset[tuple[int, int]] | None = None,
) -> list[CheckFinding]:
    # The editor applies the same rule, so both report the same browser calls.
    if not browser_i18n_calls_checkable(
        expression,
        owners,
        i18n_configured=i18n_configured,
        proven_owner_spans=proven_owner_spans,
    ):
        return []
    findings: list[CheckFinding] = []
    operation_names = {"relativeTime": "relative_time"}
    for call in browser_i18n_profile_calls(expression, owners, proven_owner_spans=proven_owner_spans):
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
    fallback_severity: LintSeverity,
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
    findings.extend(_cross_language_findings(origin, source, token, entries, start, end, severity=fallback_severity))
    return findings


def _i18n_python_findings(
    component: type[Component],
    manifest: dict[str, dict[str, dict[str, Any]]],
    profiles: dict[str, dict[str, frozenset[str]]],
    *,
    i18n_configured: bool,
    fallback_severity: LintSeverity,
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
    # Without i18n settings no profile exists, so a formatter call fails when
    # it runs, unless the component only calls it when i18n is configured.
    # The language server skips the same guarded calls.
    guarded = frozenset() if i18n_configured else i18n_configured_guarded_calls(scope)
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
                    fallback_severity=fallback_severity,
                )
            )
            continue
        if id(node) in guarded:
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
    # Python's line numbers end lines only at CR LF, CR, and LF.
    lines = source_lines(source)
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
    fallback_severity: LintSeverity,
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
                fallback_severity=fallback_severity,
            )
        )
    for node in run(_trans_nodes(template)):
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
            findings.extend(_rich_fallback_findings(origin, source, token, entries, start, end))
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


def _trans_nodes(template: Template) -> Generator[Call, Any, list[Any]]:
    result: list[Any] = []
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        if node.start_tag.name.content.lower() == "c-trans":
            result.append(node)
        body = getattr(node, "body", None)
        if body is not None:
            result.extend((yield Call(_trans_nodes, body)))
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
            # The value may start on an indented line of a multi-line
            # attribute, which only the wrapped parse accepts.
            expression = parse_authored_expression(values_attr.inner_value.content).body
        except (SyntaxError, ValueError):
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


def _shared_fallback_severity(engine: Citry | None, consumers: list[type[Component]]) -> LintSeverity:
    """Return the strictest fallback severity among the components that share one template."""
    # Without an app there are no settings to read, so the documented
    # default applies.
    if engine is None:
        return LintSettings().rule_i18n_cross_language_fallback
    # A template with no known owner follows the application setting.
    if not consumers:
        return engine.settings.lint.rule_i18n_cross_language_fallback
    # One template can serve several components; report at the strictest of
    # their settings, as the other shared-source rules do, so a component
    # that requires complete translations is not silenced by a lenient one.
    severities = {_component_lint_info(engine, component).rule_i18n_cross_language_fallback for component in consumers}
    return "error" if "error" in severities else "warning" if "warning" in severities else "ignore"


def _fallback_locales(entries: list[tuple[str, dict[str, Any]]]) -> list[str]:
    """Return the requested locales whose text comes from another locale's catalog."""
    return [locale for locale, entry in entries if entry["bundle_locale"] != locale]


def _cross_language_findings(
    origin: str,
    source: str,
    token: str,
    entries: list[tuple[str, dict[str, Any]]],
    start: int,
    end: int,
    *,
    severity: LintSeverity,
) -> list[CheckFinding]:
    # Plain text falls back at render time without failing, so a missing
    # translation is a coverage note whose severity the application chooses.
    if severity == "ignore":
        return []
    fallbacks = _fallback_locales(entries)
    if not fallbacks:
        return []
    return [
        _i18n_use_finding(
            origin,
            source,
            f"i18n output {token!r} has no translation for: {', '.join(fallbacks)}. "
            "Those locales show text from a fallback locale, and plain text cannot mark its own language.",
            I18N_CROSS_LANGUAGE_FALLBACK,
            start,
            end,
            severity=severity,
        )
    ]


def _rich_fallback_findings(
    origin: str,
    source: str,
    token: str,
    entries: list[tuple[str, dict[str, Any]]],
    start: int,
    end: int,
) -> list[CheckFinding]:
    # <c-trans> adds no element that could carry the fallback language, so
    # rendering it in a locale without a translation raises; this stays an
    # error whatever the fallback setting says.
    fallbacks = _fallback_locales(entries)
    if not fallbacks:
        return []
    return [
        _i18n_use_finding(
            origin,
            source,
            f"<c-trans> output {token!r} has no translation for: {', '.join(fallbacks)}. "
            "Rendering it in those locales fails, so add their translations.",
            I18N_RICH_MESSAGE_FALLBACK,
            start,
            end,
        )
    ]


def _client_message_findings(
    component: type[Component],
    manifest: dict[str, dict[str, dict[str, Any]]],
    *,
    fallback_severity: LintSeverity,
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
        # The browser formats a fallback with that locale's own catalog, so a
        # missing translation renders; it follows the same setting as tr().
        if fallback_severity == "ignore":
            continue
        for token in tokens:
            fallback_locales = _fallback_locales(_i18n_entries(manifest, token))
            if fallback_locales:
                result.append(
                    CheckFinding(
                        _class_label(component),
                        f"Client output {token!r} has no translation for: {', '.join(fallback_locales)}, "
                        "so the browser shows text from a fallback locale in those locales.",
                        I18N_CROSS_LANGUAGE_FALLBACK,
                        severity=fallback_severity,
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
    *,
    severity: Literal["warning", "error"] = "error",
) -> CheckFinding:
    line, column = _byte_offset_coordinates(source, start)
    end_line, end_column = _byte_offset_coordinates(source, end)
    return CheckFinding(
        origin=origin,
        message=message,
        code=code,
        severity=severity,
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
    if lint.template_data_keys is not None:
        # The component lists every key its template_data() returns, so the
        # template may use only the listed keys, the keys Citry can read from
        # the method, and the declared variables.
        known_names.update(lint.template_data_keys)
        namespace_policy = "closed"
    if lint.allows_extra_variables:
        namespace_policy = "allow-extra"
    return TemplateLintConsumer(
        known_names=frozenset(known_names),
        namespace_policy=namespace_policy,
        rule_unknown_template_variable=lint.rule_unknown_template_variable,
    )


def _undeclared_template_data_key_findings(engine: Citry, component: type[Component]) -> list[CheckFinding]:
    """
    Report a key that template_data() provably returns but ``Lint.template_data_keys`` leaves out.

    The list should name every key the method returns. A literal key it
    leaves out still works in the template, because Citry adds the keys it
    can read, but the list no longer says what the method returns. Only
    keys written as literals count: the keys a helper adds are the reason
    the list exists, and Citry cannot see them.
    """
    declared = _component_lint_info(engine, component).template_data_keys
    if declared is None:
        return []
    component_info = engine.inspect_component(component)
    kwargs_schema = component_info.schemas.kwargs
    kwargs_fields = tuple(field.name for field in kwargs_schema.fields) if kwargs_schema.kind == "fields" else None
    shape = _disk_template_data_shape(component, kwargs_fields)
    # Key ranges are offsets in the file of the class that defines
    # template_data(), which may be a base class.
    owner = next(
        (candidate for candidate in _static_class_mro(component) if "template_data" in _static_class_dict(candidate)),
        None,
    )
    source_file = None if owner is None else _loaded_python_file(owner)
    if shape is None or source_file is None:
        return []
    try:
        with tokenize.open(source_file) as source_stream:
            source = source_stream.read()
    except (OSError, SyntaxError, UnicodeError):
        return []
    findings: list[CheckFinding] = []
    known = set(declared)
    for root in shape.roots:
        if root.name in known or "literal" not in root.origins or not root.definitions:
            continue
        key_range = root.definitions[0].key_range
        findings.append(
            _source_finding(
                origin=f"{source_file} ({_class_label(component)}.template_data)",
                message=render_diagnostic(TEMPLATE_UNDECLARED_TEMPLATE_DATA_KEY, name=root.name),
                code=TEMPLATE_UNDECLARED_TEMPLATE_DATA_KEY,
                severity="warning",
                coordinates=_lsp_range_coordinates(source, key_range),
                source_kind="file",
            )
        )
    return findings


def _checker_alpine_lint_consumer(engine: Citry, component: type[Component]) -> AlpineAttributeLintConsumer:
    """Read one component's effective Alpine-attribute severities."""
    lint = _component_lint_info(engine, component)
    return AlpineAttributeLintConsumer(
        rule_alpine_attribute=lint.rule_alpine_attribute,
        rule_alpine_cloak=lint.rule_alpine_cloak,
    )


def _checker_vue_lint_consumer(
    engine: Citry,
    component: type[Component],
) -> VueLintConsumer:
    """Build the strict browser namespace shared with editor analysis."""
    component_info = engine.inspect_component(component)
    lint = _component_lint_info(engine, component)
    known_names = {variable.name for variable in lint.vue_variables}
    schema = component_info.schemas.js_data
    if schema.kind == "fields":
        known_names.update(field.name for field in schema.fields)
    elif schema.kind == "absent":
        analyzed = _disk_js_data_shape(component)
        if analyzed is not None:
            known_names.update(root.name for root in analyzed[2].roots)
    native_names, namespace_policy = _disk_vue_options_namespace(engine, component)
    known_names.update(native_names)
    return VueLintConsumer(
        known_names=frozenset(known_names),
        rule_unknown_vue_variable=lint.rule_unknown_vue_variable,
        namespace_policy=namespace_policy,
        rule_vue_python_variable=lint.rule_vue_python_variable,
    )


def _emit_findings(
    engine: Citry,
    source: _TemplateSource,
    browser_hosts: tuple[BrowserExpression, ...],
) -> list[CheckFinding]:
    """Check `$emit` names against the owners' `emits`, and child listeners against the child's."""
    owner_sources = [_disk_component_js_source(engine, component) for component in source.consumers]

    def child_source(tag: str) -> str | None:
        try:
            child = engine.get(tag.lower().removeprefix("c-"))
        except NotRegistered:
            return None
        return _disk_component_js_source(engine, child)

    return [
        _browser_source_finding(
            source.origin,
            source.content,
            finding.start_index,
            finding.end_index,
            finding.code,
            finding.message,
            finding.severity,
        )
        for finding in (
            # An owner without readable JavaScript declares no `emits`, so it
            # accepts every name and nothing can be reported for the template.
            *lint_undeclared_template_emits(
                browser_hosts,
                () if None in owner_sources else [text for text in owner_sources if text is not None],
            ),
            *lint_undeclared_component_listeners(
                browser_hosts,
                child_source,
                severities=[
                    _component_lint_info(engine, component).rule_undeclared_component_event
                    for component in source.consumers
                ],
            ),
            # Every owner must declare the name as a prop, so an owner
            # without readable JavaScript leaves nothing to report.
            *lint_prop_assignments(
                browser_hosts,
                () if None in owner_sources else [text for text in owner_sources if text is not None],
                severities=[
                    _component_lint_info(engine, component).rule_prop_assignment for component in source.consumers
                ],
            ),
        )
    ]


def _missing_component_key_findings(
    engine: Citry,
    source: _TemplateSource,
    template: Template,
    component_templates: Mapping[type[Component], str],
    *,
    parse_nested: Callable[[str], Template],
    rules: Mapping[str, TagRules] | None,
) -> list[CheckFinding]:
    """
    Report components that `<c-for>` repeats without `#c-key` on a page that uses Vue.

    On such a page Vue matches each repeated component by its key, and the
    render fails at the loop's second item when there is none. Whether the
    page uses Vue is decided for the whole page, which the check cannot
    see, so it reports a call only when the template's own component or the
    repeated component is known to make the page use Vue.
    """
    calls = unkeyed_repeated_component_calls(template, parse_nested=parse_nested)
    if not calls:
        return []
    active = [
        rule_severity
        for component in source.consumers
        if (rule_severity := _component_lint_info(engine, component).rule_missing_component_key) != "ignore"
    ]
    if not active:
        return []
    severity: Literal["warning", "error"] = "error" if "error" in active else "warning"
    vue_cache: dict[type[Component], bool] = {}

    def uses_vue(component: type[Component]) -> bool:
        if component not in vue_cache:
            vue_cache[component] = _makes_page_use_vue(component, component_templates.get(component), rules)
        return vue_cache[component]

    owner_uses_vue = any(uses_vue(component) for component in source.consumers)
    findings: list[CheckFinding] = []
    for call in calls:
        try:
            child = engine.get(call.tag.lower().removeprefix("c-"))
        except NotRegistered:
            continue
        # These render into their caller's HTML instead of as a component of
        # their own, so the loop never needs to tell them apart.
        if child.transparent or child.simple is True or child._citry_dynamic_selector:
            continue
        if not owner_uses_vue and not uses_vue(child):
            continue
        finding = _browser_template_finding(
            source.origin,
            source.content,
            call.start_index,
            call.end_index,
            BROWSER_MISSING_COMPONENT_KEY,
            tag=call.tag,
        )
        findings.append(replace(finding, severity=severity))
    return findings


def _makes_page_use_vue(
    component: type[Component],
    template_source: str | None,
    rules: Mapping[str, TagRules] | None,
) -> bool:
    """
    Return whether rendering a component makes its page use Vue, as far as its class and template show.

    The page uses Vue when any component on it has component JavaScript,
    browser data, an `Events` class, or a Vue attribute in its template. A
    `State` class alone does not count.
    """
    events = _component_events_info(component)
    if (events is not None and events.events_cls is not None) or _sends_browser_data(component):
        return True
    try:
        _owner, inline, filepath = _find_pair_declaration(component, "js", "js_file")
    except (Exception, SystemExit):  # noqa: BLE001 - an unreadable declaration proves nothing
        return False
    if inline is not None or filepath is not None:
        return True
    if template_source is None:
        return False
    try:
        template = parse_template(template_source, user_rules=dict(rules) if rules is not None else None)
    except (SyntaxError, ValueError):
        return False
    return template_has_vue_attributes(
        template,
        parse_nested=lambda value: parse_template(value, user_rules=dict(rules) if rules is not None else None),
    )


def _sends_browser_data(component: type[Component]) -> bool:
    """
    Return whether a component is known to send at least one value to the browser.

    The page uses Vue only when the data `js_data()` returns is not empty, so
    a `JsData` class with no fields, or a `js_data()` the source shows
    always returns `{}`, does not count. A `js_data()` whose source cannot be
    read may return data, so it counts.
    """
    schema = component.citry.inspect_component(component).schemas.js_data
    if schema.kind == "fields":
        return bool(schema.fields)
    if component.js_data is Component.js_data:
        return False
    analyzed = _disk_js_data_shape(component)
    return analyzed is None or bool(analyzed[2].roots) or analyzed[2].completeness != "closed"


def _server_event_payload_findings(
    engine: Citry,
    source: _TemplateSource,
    template: Template,
    *,
    parse_nested: Callable[[str], Template],
) -> list[CheckFinding]:
    """Check the literal arguments of `@c-*` bindings, and the fields of forms they submit, against each data class."""
    handlers = _shared_event_handlers(source.consumers)
    if not handlers:
        return []
    payloads: dict[str, ServerEventPayload] = {}
    for name, (data_class, query_string) in handlers.items():
        payload = server_event_payload(data_class, query_string=query_string)
        # A Pydantic model, or a class whose annotations do not resolve, is
        # checked by rules the template cannot see.
        if payload is not None:
            payloads[name] = payload
    found: list[ServerEventPayloadFinding] = []
    for call in server_event_calls(template, frozenset(payloads), parse_nested=parse_nested):
        found.extend(server_event_payload_findings(call, payloads[call.handler]))
    # The server removes the host's CSRF fields before it checks a form's
    # fields, so a form may hold that hidden input.
    dropped = csrf_field_names(engine)
    for form in server_event_forms(template, frozenset(payloads), parse_nested=parse_nested):
        found.extend(server_event_form_findings(form, payloads[form.call.handler], dropped_names=dropped))
    findings: list[CheckFinding] = []
    for finding in found:
        setting = _PAYLOAD_RULES[finding.code]
        active = [
            rule_severity
            for component in source.consumers
            if (rule_severity := getattr(_component_lint_info(engine, component), setting)) != "ignore"
        ]
        if not active:
            continue
        start = _byte_offset_coordinates(source.content, finding.start_index)
        end = _byte_offset_coordinates(source.content, finding.end_index)
        findings.append(
            CheckFinding(
                source.origin,
                finding.message,
                finding.code,
                severity="error" if "error" in active else "warning",
                start_index=finding.start_index,
                end_index=finding.end_index,
                line=start[0],
                column=start[1],
                end_line=end[0],
                end_column=end[1],
            )
        )
    return findings


@dataclass(slots=True)
class _LinkCheck:
    """
    What one `citry check` run learned about link paths, shared by every template.

    Each path is asked about once, however many templates link to it, and
    the notes about paths that could not be checked are written once per run.
    """

    verdicts: dict[str, PathVerdict]
    # Paths whose path checker raised, with the error.
    failures: dict[str, str]
    # The first path seen when no integration registered a path checker.
    unchecked: str | None = None

    def notes(self) -> list[str]:
        """Write one note for unchecked links and one for links a checker failed on."""
        notes: list[str] = []
        if self.unchecked is not None:
            message = render_diagnostic(CHECK_URL_CHECKER_MISSING, path=self.unchecked)
            notes.append(f"{message} [{CHECK_URL_CHECKER_MISSING}]")
        if self.failures:
            path = min(self.failures)
            detail = self.failures[path]
            message = (
                render_diagnostic(CHECK_URL_CHECKER_FAILED, path=path, detail=detail)
                if len(self.failures) == 1
                else render_diagnostic(
                    CHECK_URL_CHECKER_FAILED, variant="several", path=path, count=len(self.failures), detail=detail
                )
            )
            notes.append(f"{message} [{CHECK_URL_CHECKER_FAILED}]")
        return notes


def _unknown_url_findings(
    engine: Citry,
    source: _TemplateSource,
    template: Template,
    links: _LinkCheck,
    *,
    parse_nested: Callable[[str], Template],
) -> list[CheckFinding]:
    """Report literal link paths the host app does not serve, as its framework integration answers."""
    active = [
        rule_severity
        for component in source.consumers
        if (rule_severity := _component_lint_info(engine, component).rule_unknown_url) != "ignore"
    ]
    if not active:
        return []
    urls = template_urls(template, parse_nested=parse_nested)
    if not urls:
        return []
    if not has_path_checkers(engine):
        # Nothing can answer, so the run notes it once instead of guessing.
        if links.unchecked is None:
            # Citry's own routes are always served, so the note names a link
            # to the app's pages instead.
            links.unchecked = next((url.path for url in urls if not is_citry_path(engine, url.path)), None)
        return []
    asked = {url.path for url in urls} - links.verdicts.keys() - links.failures.keys()
    results = check_paths(engine, asked)
    links.verdicts.update(results.verdicts)
    links.failures.update(results.failures)
    verdicts = {path: (verdict.found, verdict.suggestion) for path, verdict in links.verdicts.items()}
    findings: list[CheckFinding] = []
    for finding in unknown_url_findings(urls, verdicts):
        start = _byte_offset_coordinates(source.content, finding.start_index)
        end = _byte_offset_coordinates(source.content, finding.end_index)
        findings.append(
            CheckFinding(
                source.origin,
                finding.message,
                finding.code,
                severity="error" if "error" in active else "warning",
                start_index=finding.start_index,
                end_index=finding.end_index,
                line=start[0],
                column=start[1],
                end_line=end[0],
                end_column=end[1],
            )
        )
    return findings


# The setting that controls each server-event payload finding.
_PAYLOAD_RULES = {
    BROWSER_UNKNOWN_SERVER_EVENT_FIELD: "rule_unknown_server_event_field",
    BROWSER_MISSING_SERVER_EVENT_FIELD: "rule_missing_server_event_field",
    BROWSER_INCOMPATIBLE_SERVER_EVENT_FIELD: "rule_incompatible_server_event_field",
    BROWSER_UNKNOWN_FORM_FIELD: "rule_unknown_form_field",
    BROWSER_MISSING_FORM_FIELD: "rule_missing_form_field",
}


def _unknown_inject_key_findings(
    engine: Citry,
    registrations: Mapping[str, type[Component]],
    cwd: Path,
) -> list[CheckFinding]:
    """
    Report each ``self.inject("key")`` whose key no provider above the component gives.

    The keys come from the templates that render each component, walked up
    to the page, with every key the app provides as the answer for a
    component no template renders. ``cwd`` is the project folder searched for
    ``render(provides={...})`` keys.
    """
    try:
        scopes = inject_key_scopes(engine, registrations, cwd)
    except (Exception, SystemExit):  # noqa: BLE001 - project code that breaks the walk must not stop the check
        return []
    if scopes is None:
        return []
    findings: list[CheckFinding] = []
    trees: dict[Path, tuple[str, ast.Module] | None] = {}
    for scope in scopes:
        if scope.provided is None:
            continue
        # A class shared by several components is reported unless all of them turn the rule off.
        active = [
            severity
            for component in scope.components
            if (severity := _component_lint_info(engine, component).rule_unknown_inject_key) != "ignore"
        ]
        if not active:
            continue
        if scope.file not in trees:
            try:
                with tokenize.open(scope.file) as stream:
                    text = stream.read()
                trees[scope.file] = (text, ast.parse(text))
            except (OSError, SyntaxError, UnicodeError, ValueError, RecursionError):
                trees[scope.file] = None
        parsed = trees[scope.file]
        if parsed is None:
            continue
        source, tree = parsed
        findings.extend(
            _i18n_use_finding(
                f"{scope.file} ({scope.label})",
                source,
                finding.message,
                finding.code,
                finding.start_index,
                finding.end_index,
                severity="error" if "error" in active else "warning",
            )
            for finding in unknown_inject_key_findings(
                source,
                tree,
                scope.qualname,
                component=scope.name,
                provided=scope.provided,
                everywhere=scope.everywhere,
            )
        )
    return findings


def _shared_event_handlers(consumers: list[type[Component]]) -> dict[str, tuple[type | None, bool]]:
    """
    Return each handler name every owner declares, with the data class they all use and whether GET may send it.

    A template shared by several components runs each binding against the
    component that renders it, so a handler is checked only when every owner
    has it with the same data class. Any other handler is left out. A
    handler that accepts GET may receive its arguments as a query string.
    """
    shared: dict[str, tuple[type | None, bool]] | None = None
    for component in consumers:
        info = _component_events_info(component)
        current = (
            {}
            if info is None
            else {name: (handler.data_schema, "GET" in handler.methods) for name, handler in info.handlers.items()}
        )
        if shared is None:
            shared = current
            continue
        shared = {
            name: (schema, query_string or current[name][1])
            for name, (schema, query_string) in shared.items()
            if name in current and current[name][0] is schema
        }
    return shared or {}


def _check_css_source(engine: Citry, source: _BrowserSource, known_css: _KnownCss) -> list[CheckFinding]:
    """Report `var(--name)` in one component CSS source that misspells a `css_data()` key, or that nothing sets."""
    lints = [_component_lint_info(engine, component) for component in source.consumers]
    misspelled_active = [lint.rule_misspelled_css_variable for lint in lints]
    undeclared_active = [lint.rule_undeclared_css_variable for lint in lints]
    misspelled_active = [severity for severity in misspelled_active if severity != "ignore"]
    undeclared_active = [severity for severity in undeclared_active if severity != "ignore"]
    if not misspelled_active and not undeclared_active:
        return []
    keys: set[str] = set()
    for component in source.consumers:
        component_keys = known_css.css_data_keys(component)
        # One owner whose keys are not all known may set any property.
        if component_keys is None:
            return []
        keys.update(component_keys)
    findings: list[CssVariableFinding | CssLintFinding] = list(
        lint_misspelled_css_variables(
            source.content,
            keys,
            severity="error" if "error" in misspelled_active else "warning",
        )
        if misspelled_active
        else ()
    )
    if undeclared_active:
        findings.extend(
            lint_undeclared_css_variables(
                source.content,
                keys | known_css.custom_properties(),
                severity="error" if "error" in undeclared_active else "warning",
                # A misspelled key already has a finding with a suggestion.
                reported={(finding.start_index, finding.end_index) for finding in findings},
            )
        )
    return [
        _browser_source_finding(
            source.origin,
            source.content,
            finding.start_index,
            finding.end_index,
            finding.code,
            finding.message,
            finding.severity,
        )
        for finding in findings
    ]


@dataclass(slots=True)
class _KnownCss:
    """
    The CSS that Citry reads for one `citry check` run, shared by the CSS rules.

    It covers every registered component: its `css` or `css_file`, the
    inline and local-file stylesheets in its `Dependencies`, and its
    template's `<style>` elements and `style` attributes; for custom
    properties also the `--name` strings in its JavaScript and Python module,
    and the keys its `css_data()` returns. Each part is read the first time
    a rule needs it, so a run with every CSS rule off reads nothing more.
    """

    engine: Citry
    components: list[type[Component]]
    css_sources: Mapping[tuple[object, ...], _BrowserSource]
    browser_sources: Mapping[tuple[object, ...], _BrowserSource]
    css_templates: list[tuple[_TemplateSource, TemplateCss]]
    # What each component's own `css` or `css_file` declares.
    own_declarations: dict[type[Component], CssDeclarations] | None = None
    declarations: CssDeclarations | None = None
    # Each component's `css_data()` keys, or None for a component whose keys
    # Citry cannot list; filled in as the rules ask.
    keys: dict[type[Component], frozenset[str] | None] | None = None
    known_properties: frozenset[str] | None = None

    def own(self, component: type[Component]) -> CssDeclarations:
        """Return what the component's own `css` or `css_file` declares."""
        if self.own_declarations is None:
            self.own_declarations = {}
            for css_source in self.css_sources.values():
                scanned = scan_css(css_source.content)
                for consumer in css_source.consumers:
                    self.own_declarations[consumer] = scanned
        return self.own_declarations.get(component, CssDeclarations())

    def declared(self) -> CssDeclarations:
        """Return what every stylesheet Citry reads declares."""
        if self.declarations is None:
            # One set per kind, built once: merging declarations one sheet at
            # a time would copy the growing sets for every component.
            classes: set[str] = set()
            patterns: dict[ClassPattern, None] = {}
            properties: set[str] = set()
            parts = [
                *(self.own(component) for component in self.components),
                *(scan_css(text) for text in _dependency_stylesheets(self.components)),
                *(used.declarations for _source, used in self.css_templates),
            ]
            for part in parts:
                classes.update(part.classes)
                patterns.update(dict.fromkeys(part.class_patterns))
                properties.update(part.custom_properties)
            self.declarations = CssDeclarations(
                classes=frozenset(classes),
                class_patterns=tuple(patterns),
                custom_properties=frozenset(properties),
            )
        return self.declarations

    def css_data_keys(self, component: type[Component]) -> frozenset[str] | None:
        """Return the component's `css_data()` keys, reading its source at most once per run."""
        if self.keys is None:
            self.keys = {}
        if component not in self.keys:
            self.keys[component] = _css_data_keys(self.engine, component)
        return self.keys[component]

    def custom_properties(self) -> frozenset[str]:
        """Return every custom property that something Citry reads sets, without the leading `--`."""
        if self.known_properties is None:
            # Citry sets each `css_data()` key on its component's root
            # element, and every element inside it, other components'
            # included, inherits the value.
            properties = {key for component in self.components for key in self.css_data_keys(component) or ()}
            properties.update(self.declared().custom_properties)
            # A script or Python code may set a property by name, as in
            # `style.setProperty("--gap", ...)` or `f"--accent: {color};"`.
            for browser_source in self.browser_sources.values():
                properties.update(code_custom_properties(browser_source.content))
            for source in _python_module_sources(self.components):
                properties.update(code_custom_properties(source))
            self.known_properties = frozenset(properties)
        return self.known_properties


# A `<style>` element in a pre-rendered `Dependencies` tag, such as
# `Markup("<style>.card { ... }</style>")`.
_STYLE_ELEMENT = re.compile(r"<style\b([^>]*)>(.*?)</style\s*>", re.IGNORECASE | re.DOTALL)
# A `type` or `lang` attribute in such a tag's attribute text.
_STYLE_TYPE_ATTRIBUTE = re.compile(r"""\b(?:type|lang)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""", re.IGNORECASE)


def _dependency_stylesheets(components: list[type[Component]]) -> list[str]:
    """
    Return the text of every `Dependencies` stylesheet Citry can read.

    That is an inline `Style(content=...)`, a pre-rendered `<style>` tag, and
    a local file that reads as UTF-8. A stylesheet linked by URL is not
    read. Resolving `Dependencies` calls any callable entry the component
    declares, as a render does; a declaration that raises is skipped.
    """
    texts: dict[object, str] = {}
    for component in components:
        try:
            dependencies = component.get_dependencies()
        except (Exception, SystemExit):  # noqa: BLE001, S112 - one bad declaration must not stop the batch
            continue
        for entries in dependencies.css.values():
            for entry in entries:
                if isinstance(entry, Style):
                    if entry.content:
                        texts.setdefault(("inline", entry.content), entry.content)
                elif isinstance(entry, Path):
                    if ("file", entry) not in texts:
                        try:
                            texts[("file", entry)] = entry.read_text(encoding="utf-8")
                        except (OSError, UnicodeError):
                            continue
                elif callable(getattr(entry, "__html__", None)):
                    try:
                        html = str(entry.__html__())
                    except (Exception, SystemExit):  # noqa: BLE001, S112 - one bad entry must not stop the batch
                        continue
                    for match in _STYLE_ELEMENT.finditer(html):
                        # A tag such as `<style type="text/x-scss">` holds a
                        # language Citry cannot read.
                        types = [
                            next(value for value in found.groups() if value is not None)
                            for found in _STYLE_TYPE_ATTRIBUTE.finditer(match.group(1))
                        ]
                        if all(style_type_is_css(decode_attribute_entities(value)) for value in types):
                            texts.setdefault(("inline", match.group(2)), match.group(2))
    return list(texts.values())


def _python_module_sources(components: list[type[Component]]) -> list[str]:
    """Return the source of each module that defines a registered component, read once per file."""
    sources: dict[Path, str] = {}
    for component in components:
        path = _loaded_python_file(component)
        if path is None or path in sources:
            continue
        try:
            with tokenize.open(path) as stream:
                sources[path] = stream.read()
        except (OSError, SyntaxError, UnicodeError):
            continue
    return list(sources.values())


def _css_class_findings(
    engine: Citry,
    css_templates: list[tuple[_TemplateSource, TemplateCss]],
    known_css: _KnownCss,
) -> list[CheckFinding]:
    """Report template classes that misspell a class the component's CSS styles, or that no CSS declares."""
    findings: list[CheckFinding] = []
    for source, used in css_templates:
        if not used.classes:
            continue
        lints = {component: _component_lint_info(engine, component) for component in source.consumers}
        misspelled_owners = [
            component for component, lint in lints.items() if lint.rule_misspelled_css_class != "ignore"
        ]
        undeclared_active = [
            lint.rule_undeclared_css_class for lint in lints.values() if lint.rule_undeclared_css_class != "ignore"
        ]
        # A template shared by several components is compared with the CSS of
        # each one that checks it.
        own = CssDeclarations()
        for component in misspelled_owners:
            own = own.merged(known_css.own(component))
        misspelled_severities = {lints[component].rule_misspelled_css_class for component in misspelled_owners}
        # Gathering every stylesheet Citry reads calls each component's
        # get_dependencies() and reads its files. The rule is on by default
        # and most templates have no near miss, so it is gathered only once
        # a class is one slip from the component's own CSS.
        class_findings: list[CssLintFinding] = list(
            lint_misspelled_css_classes(
                used.classes,
                own,
                known_css.declared,
                severity="error" if "error" in misspelled_severities else "warning",
            )
            if own.classes
            else ()
        )
        if undeclared_active:
            class_findings.extend(
                lint_undeclared_css_classes(
                    used.classes,
                    known_css.declared(),
                    severity="error" if "error" in undeclared_active else "warning",
                    # A misspelled class already has a finding with a suggestion.
                    reported={(finding.start_index, finding.end_index) for finding in class_findings},
                )
            )
        # The class positions count in the template, so each range does too.
        findings.extend(
            _ranged_finding(
                source,
                finding.message,
                finding.code,
                start_index=finding.start_index,
                end_index=finding.end_index,
                severity=finding.severity,
            )
            for finding in sorted(class_findings, key=lambda item: (item.start_index, item.end_index))
        )
    return findings


def _css_data_keys(engine: Citry, component: type[Component]) -> frozenset[str] | None:
    """Return every key a component's `css_data()` or `CssData` returns, or None when the set is not known."""
    schema = engine.inspect_component(component).schemas.css_data
    if schema.kind == "fields" and schema.namespace_policy == "closed":
        return frozenset(field.name for field in schema.fields)
    if schema.kind != "absent":
        return None
    for candidate in _static_class_mro(component):
        if "css_data" not in _static_class_dict(candidate):
            continue
        if candidate is Component:
            # Component's own `css_data()` returns no keys.
            return frozenset()
        source_file = _loaded_python_file(candidate)
        qualname = _safe_class_text(candidate, "__qualname__")
        if source_file is None or qualname is None:
            return None
        try:
            with tokenize.open(source_file) as source_stream:
                text = source_stream.read()
        except (OSError, SyntaxError, UnicodeError):
            return None
        shape = analyze_css_data_source(text, qualname)
        if shape is None or shape.completeness != "closed":
            return None
        return frozenset(root.name for root in shape.roots)
    return None


def _checker_markup_lint_consumer(
    engine: Citry,
    component: type[Component],
    js_analysis: BrowserComponentSourceAnalysis | None,
) -> MarkupLintConsumer:
    """
    Build one component's severities for the HTML rules, and whether a parent's attributes reach its root.

    Vue passes them on for a component with browser code unless its
    JavaScript proves ``inheritAttrs: false``; an unreadable value counts as
    passing them on, so the image rule stays quiet when unsure.
    """
    lint = _component_lint_info(engine, component)
    inherits_attributes = js_analysis is None or js_analysis.declared_inherit_attrs is not False
    return MarkupLintConsumer(
        **{rule_name: getattr(lint, rule_name) for rule_name in MARKUP_LINT_RULES},
        root_may_receive_attributes=_may_have_browser_code(component) and inherits_attributes,
        # The engine's CSP policy decides whether its templates are checked
        # for what a strict policy blocks.
        csp=lint.security_csp,
    )


def _component_renders_in_place(engine: Citry) -> Callable[[str], bool | None]:
    """
    Say whether a component tag renders in place in its caller's Vue template.

    A `transparent` or `simple` component is copied into the caller's template
    rather than called, so it may sit inside a Vue `v-for`. A tag the
    application does not register returns `None`.
    """

    def renders_in_place(name: str) -> bool | None:
        try:
            component = engine.get(name.lower())
        except NotRegistered:
            return None
        return bool(component.transparent or component.simple)

    return renders_in_place


def _may_have_browser_code(component: type[Component]) -> bool:
    """
    Return whether a component may run Vue code, so Vue passes a parent's attributes to its single root element.

    A component without browser code renders on the server only, where a
    parent's attributes are inputs and never reach the root element.
    """
    # Browser data, State, or event handlers may make Vue render the
    # component even without JavaScript of its own, so any of them counts.
    # Every component class gets an `Events` class, so its handlers decide.
    events = _component_events_info(component)
    if (
        component.JsData is not None
        or component.js_data is not Component.js_data
        or (events is not None and (events.handlers or events.state_cls is not None))
    ):
        return True
    # A declared `js` or `js_file` is browser code; reading the source is
    # not needed to know that.
    try:
        _owner, inline, filepath = _find_pair_declaration(component, "js", "js_file")
    except (Exception, SystemExit):  # noqa: BLE001 - an unreadable declaration may still be browser code
        return True
    return inline is not None or filepath is not None


def _declared_directives(js_analysis: BrowserComponentSourceAnalysis | None) -> frozenset[str] | None:
    """Return the directive names a component's JavaScript registers, or None when they are unknown."""
    return None if js_analysis is None else js_analysis.declared_directives


def _disk_component_js_analysis(engine: Citry, component: type[Component]) -> BrowserComponentSourceAnalysis | None:
    """Analyze the one JavaScript source a component runs, or return None when there is not exactly one."""
    source = _disk_component_js_source(engine, component)
    return None if source is None else analyze_browser_component_source(source)


def _disk_component_js_source(engine: Citry, component: type[Component]) -> str | None:
    """Return the one JavaScript source a component runs, without executing an asset loader."""
    sources: dict[tuple[object, ...], _BrowserSource] = {}
    _collect_browser_source(engine, component, sources)
    matching = [source for source in sources.values() if component in source.consumers]
    return matching[0].content if len(matching) == 1 else None


def _disk_vue_options_namespace(
    engine: Citry,
    component: type[Component],
) -> tuple[frozenset[str], Literal["closed", "unknown"]]:
    """Resolve public native Options names without executing an asset loader."""
    sources: dict[tuple[object, ...], _BrowserSource] = {}
    _collect_browser_source(engine, component, sources)
    matching = [source for source in sources.values() if component in source.consumers]
    if not matching:
        try:
            _owner, inline, filepath = _find_pair_declaration(component, "js", "js_file")
        except (Exception, SystemExit):  # noqa: BLE001 - conservative unknown namespace
            return frozenset(), "unknown"
        return (frozenset(), "closed") if inline is None and filepath is None else (frozenset(), "unknown")
    if len(matching) != 1:
        return frozenset(), "unknown"
    analysis = analyze_browser_component_source(matching[0].content)
    names = frozenset(item.exposed_name for item in analysis.public_names)
    unknown = not analysis.valid or any(section.state == "unknown" for section in analysis.sections)
    return names, "unknown" if unknown else "closed"


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
            label = f"{_class_label(component)}.JsData.{field.name}"
            findings.append(
                _source_finding(
                    # The range counts in the Python file, so the origin names
                    # that file, as the other findings about Python code do.
                    origin=f"{field.source_file} ({label})" if field.source_file is not None else label,
                    message=render_diagnostic(
                        JS_DATA_UNSUPPORTED_TYPE,
                        variant="secret" if SECRET_UNSUPPORTED_REASON in wire_type.unsupported else "default",
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
    # parameters[0] is the kwargs parameter for instance, class, and static methods alike.
    if shape.parameters and kwargs_schema.kind == "fields":
        member_types[shape.parameters[0]] = {
            field.name: (
                json_wire_type_from_annotation(field.type_display)
                if field.type_display is not None
                else JsonWireType("unknown")
            )
            for field in kwargs_schema.fields
        }
    # The language server's app worker copies the same class facts, so both
    # type a value such as `kwargs.task.lane` from `Task.lane`.
    wire_classes = kwargs_wire_classes(component) if member_types else KwargsWireClasses()
    member_annotations = {name: wire_classes.members for name in member_types}
    module_values = _js_data_module_values(component, source)
    for root in shape.roots:
        values = [
            value
            for definition in root.definitions
            if (value := _range_source(source, definition.value_range)) is not None
        ]
        wire_types = [
            json_wire_type_from_expression(
                value,
                member_types=member_types,
                member_annotations=member_annotations,
                classes=wire_classes.classes,
            )
            for value in values
        ]
        issues = tuple(dict.fromkeys(issue for item in wire_types for issue in item.unsupported))
        holds_secret = SECRET_UNSUPPORTED_REASON in issues
        if not issues:
            # A bare module-level name, such as `API_BASE`, has no type in
            # the source, but the loaded module holds the value js_data()
            # sends, so the browser's own JSON check can run on it. The same
            # holds for a name written inside a dict or list literal, such as
            # `{"config": {"token": SECRET_TOKEN}}`.
            module_issues = [
                issue
                for value in values
                for sent in _names_sent_as_written(value)
                if (issue := module_values(sent)) is not None
            ]
            issues = tuple(dict.fromkeys(issue.detail for issue in module_issues))
            holds_secret = any(issue.secret for issue in module_issues)
        if not issues:
            continue
        definition = root.definitions[-1]
        findings.append(
            _source_finding(
                origin=f"{source_file} ({_class_label(component)}.js_data)",
                message=render_diagnostic(
                    JS_DATA_UNSUPPORTED_TYPE,
                    # Rendering raises for a Secret, so the message says that
                    # rather than that only editor typing degrades.
                    variant="secret" if holds_secret else "default",
                    name=root.name,
                    detail="; ".join(issues),
                ),
                code=JS_DATA_UNSUPPORTED_TYPE,
                severity="warning",
                coordinates=_lsp_range_coordinates(source, definition.key_range),
            )
        )
    return findings


@dataclass(frozen=True, slots=True)
class _SentName:
    """
    A module-level name whose value `js_data()` sends unchanged.

    Attributes:
        path: The name and the attributes read from it, such as
            `("config", "API_TOKEN")` for `config.API_TOKEN`.
        starred: Whether the value is unpacked into a list, as in
            `[*TOKENS]`, so its items are sent rather than the value itself.
        wrappers: The callee of each `Const(...)` call around the value,
            written the same way as `path`. The value counts only when each
            one is Citry's `Const`, which sends what it wraps unchanged.

    """

    path: tuple[str, ...]
    starred: bool = False
    wrappers: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True, slots=True)
class _ModuleValueIssue:
    """Why a module-level value that `js_data()` sends cannot reach the browser."""

    detail: str
    # Rendering raises TypeError for a Secret, which the message then says.
    secret: bool


def _names_sent_as_written(value_source: str) -> list[_SentName]:
    """
    Return the module-level names whose values a `js_data()` value sends unchanged.

    That is the value itself when it is a name or an attribute of one, such
    as `config.API_TOKEN`, and each such name that is a whole item of a
    dict, list, or tuple literal inside it, unpacked with `*` into one,
    either branch of a conditional expression, or the first argument of a
    `Const(...)` call. A name used any other way, such as
    `len(TOKEN.get_secret_value())` or `get_token()`, is left out, because
    the browser receives what the expression computes, not the name's
    value.
    """
    try:
        # The value may come from inside a dict literal, where it can span
        # lines without parentheses of its own.
        node = parse_authored_expression(value_source.strip()).body
    except (SyntaxError, ValueError):
        return []
    names: list[_SentName] = []
    pending: list[tuple[ast.expr, bool, tuple[tuple[str, ...], ...]]] = [(node, False, ())]
    while pending:
        current, starred, wrappers = pending.pop(0)
        path = _attribute_path(current)
        if path is not None:
            names.append(_SentName(path, starred=starred, wrappers=wrappers))
        elif isinstance(current, ast.Dict) and starred:
            # `[*{"a": TOKEN}]` sends the dict's keys, not its values.
            pending.extend((key, False, wrappers) for key in current.keys if key is not None)
        elif isinstance(current, ast.Dict):
            # `{**CONFIG}` has no key, and sends CONFIG's items, which the
            # JSON check reads the same way as CONFIG itself.
            pending.extend((value, False, wrappers) for value in current.values)
        elif isinstance(current, (ast.List, ast.Tuple)):
            pending.extend(
                (item.value, True, wrappers) if isinstance(item, ast.Starred) else (item, False, wrappers)
                for item in current.elts
            )
        elif isinstance(current, ast.IfExp):
            # Either branch may be the one sent, so both are read.
            pending.extend([(current.body, starred, wrappers), (current.orelse, starred, wrappers)])
        elif isinstance(current, ast.Call) and current.args and not isinstance(current.args[0], ast.Starred):
            # Only a call that may be `Const` is followed; the issue check
            # confirms the callee on the loaded module before it counts.
            callee = _attribute_path(current.func)
            if callee is not None and callee[-1] == "Const":
                pending.append((current.args[0], starred, (*wrappers, callee)))
    return names


def _attribute_path(node: ast.expr) -> tuple[str, ...] | None:
    """Return `("a", "b", "c")` for a name or attribute chain `a.b.c`, or None for any other expression."""
    attributes: list[str] = []
    while isinstance(node, ast.Attribute):
        attributes.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    return (node.id, *reversed(attributes))


# The getters behind `cls.__dict__` and `cls.__mro__`, taken from `type`
# itself, so a metaclass that defines either name cannot run code when the
# check reads a class.
_CLASS_NAMESPACE = type.__dict__["__dict__"]
_CLASS_MRO = type.__dict__["__mro__"]
# The names whose definition on a class makes reading an attribute run code.
_ATTRIBUTE_HOOKS = ("__getattr__", "__getattribute__")
# Every ordinary class also holds a `__dict__` entry: the getter Python
# builds for it, which runs no user code. Any other kind, such as a
# property, could.
_BUILT_IN_GETTERS = (GetSetDescriptorType, MemberDescriptorType)
# Classes whose attribute reading Citry knows runs no user code. On Python
# 3.10, SimpleNamespace lists its own C `__getattribute__` in its class
# namespace, which would otherwise read as a hook that might run code.
_PLAIN_ATTRIBUTE_CLASSES = (object, type, ModuleType, SimpleNamespace)
# The exact types of a value the JSON check can read without running any
# code the value's own class defines. A Secret is a leaf the check reports.
_PLAIN_JSON_LEAVES = (type(None), bool, int, float, str, Secret)
_PLAIN_JSON_KEYS = (type(None), bool, int, float, str)


def _is_one_of(cls: type, classes: tuple[type, ...]) -> bool:
    """Return whether ``cls`` is one of ``classes``, comparing identity so no metaclass ``__eq__`` runs."""
    return any(cls is candidate for candidate in classes)


def _stored_entry(namespace: object, name: str) -> tuple[bool, object]:
    """
    Return the entry ``name`` of a plain dict or a class namespace.

    Looking the name up with ``in`` or ``[]`` would compare it with a key of
    the same hash, which runs that key's ``__eq__`` when the key is not a
    plain ``str``. So only exact ``str`` keys are compared.
    """
    if not _is_one_of(type(namespace), (dict, MappingProxyType)):
        return False, None
    # Loop over a copy: another thread may store on the class or module
    # meanwhile, and a dict that changes size during the loop raises.
    entries = cast("dict[object, object] | MappingProxyType[object, object]", namespace).copy()
    for key, value in entries.items():
        if type(key) is str and key == name:
            return True, value
    return False, None


def _class_attribute(cls: type, name: str) -> tuple[bool, object]:
    """Return the first value named ``name`` in the namespaces of ``cls`` and its bases, in MRO order."""
    for base in _CLASS_MRO.__get__(cls):
        found, value = _stored_entry(_CLASS_NAMESPACE.__get__(base), name)
        if found:
            return True, value
    return False, None


def _is_descriptor(value: object) -> bool:
    """Return whether reading ``value`` as a class attribute calls its ``__get__``."""
    return _class_attribute(type(value), "__get__")[0]


def _is_data_descriptor(value: object) -> bool:
    """Return whether ``value``, as a class attribute, wins over an instance's own ``__dict__`` entry."""
    value_type = type(value)
    return _class_attribute(value_type, "__set__")[0] or _class_attribute(value_type, "__delete__")[0]


def _read_stored_attribute(owner: object, name: str) -> tuple[bool, object]:
    """
    Read an attribute that is stored on a module, a class, or an instance, without calling any code.

    A property, a `__getattr__` hook, or a lazy settings object, such as
    Django's `settings`, would run code to produce the value, which a static
    check must not do. So the owner's class and its bases must leave
    attribute reading alone, and only a value stored in the owner's own
    `__dict__` counts. A class attribute that is itself a descriptor, such
    as a property or a method, does not count either, because reading it
    through the class calls it. Every class and namespace is read through
    `type`'s own getters, and names are compared only with exact `str`
    keys, so no `__eq__`, `__hash__`, or metaclass hook runs.

    Returns:
        Whether the value was found, and the value.

    """
    try:
        owner_mro = _CLASS_MRO.__get__(type(owner))
        for base in owner_mro:
            if _is_one_of(base, _PLAIN_ATTRIBUTE_CLASSES):
                continue
            namespace = _CLASS_NAMESPACE.__get__(base)
            if any(_stored_entry(namespace, hook)[0] for hook in _ATTRIBUTE_HOOKS):
                return False, None
            found, getter = _stored_entry(namespace, "__dict__")
            if found and not _is_one_of(type(getter), _BUILT_IN_GETTERS):
                return False, None
        # A data descriptor of the same name on the owner's class, such as a
        # property, is what Python returns, not the `__dict__` entry.
        found, class_value = _class_attribute(type(owner), name)
        if found and _is_data_descriptor(class_value):
            return False, None
        stored = object.__getattribute__(owner, "__dict__")
        # A dict subclass could run code when it is read.
        found, value = _stored_entry(stored, name)
        if not found:
            return False, None
        # Python calls a descriptor stored on a class when the class is read.
        if any(base is type for base in owner_mro) and _is_descriptor(value):
            return False, None
    except Exception:  # noqa: BLE001 - an exotic object must not stop the check
        return False, None
    return True, value


@dataclass(frozen=True, slots=True)
class _OpaquePart:
    """A part of a module value that the JSON check cannot read without running the part's own code."""

    value: object
    # Where the part sits, written the way Python reads it back, such as
    # `["config"]["path"]`; empty for the value itself.
    path: str
    # Whether the part is a dict key rather than a value.
    is_key: bool


def _key_text(key: object) -> str:
    """Write an exact built-in dict key the way Python reads it back, such as ``["name"]`` or ``[1]``."""
    if type(key) is str:
        return f"[{json.dumps(key, ensure_ascii=False)}]"
    return f"[{key!r}]"


def _first_opaque_part(value: object) -> _OpaquePart | None:
    """
    Return the first part of ``value`` that is not an exact built-in JSON type or a Secret, or None.

    The JSON check reads a value with ``isinstance`` and ``.items()``, which
    run code that a dict subclass or an object posing as another class, such
    as Django's ``SimpleLazyObject``, defines. This walk compares exact types
    only, so it runs none of it, and it does not recurse, so a deeply nested
    value cannot stop the check.
    """
    pending: list[tuple[object, str]] = [(value, "")]
    seen: set[int] = set()
    while pending:
        current, path = pending.pop()
        # Citry's own Const proxy sends what it wraps unchanged.
        unwrapped, current = _unwrap_const_markers(current)
        if not unwrapped:
            return _OpaquePart(current, path, is_key=False)
        current_type = type(current)
        if _is_one_of(current_type, _PLAIN_JSON_LEAVES):
            continue
        # A container that holds itself is the JSON check's to report, so
        # the walk only stops at the second visit.
        if id(current) in seen:
            continue
        if current_type is dict:
            seen.add(id(current))
            items = list(cast("dict[object, object]", current).items())
            for key, _item in items:
                if not _is_one_of(type(key), _PLAIN_JSON_KEYS):
                    return _OpaquePart(key, path, is_key=True)
            # Reversed so the stack pops them in the order the JSON check reads them.
            pending.extend((item, f"{path}{_key_text(key)}") for key, item in reversed(items))
        elif current_type is list or current_type is tuple:
            seen.add(id(current))
            items = list(enumerate(cast("list[object]", current)))
            pending.extend((item, f"{path}[{index}]") for index, item in reversed(items))
        else:
            return _OpaquePart(current, path, is_key=False)
    return None


def _runs_only_builtin_code(base: type, entry: object) -> bool:
    """
    Return whether an attribute hook on ``base`` is Python's own C code from the standard library.

    Many standard library types, such as ``Decimal`` or a bound method, list
    a ``__getattribute__`` that is only the built-in lookup, which never
    makes the value pass for another class. A weak reference proxy forwards
    the lookup to the object it points at, and so may a C type from another
    package, so those still count as hooks.
    """
    if type(entry) is not WrapperDescriptorType:
        return False
    # A weak reference proxy passes every lookup, `__class__` included, on
    # to the object it points at.
    if any(base is proxy for proxy in weakref.ProxyTypes):
        return False
    module = _safe_class_text(base, "__module__")
    return module is not None and (module == "builtins" or module.split(".")[0] in sys.stdlib_module_names)


def _never_json(value: object, *, is_key: bool = False) -> bool:
    """
    Return whether the JSON check refuses ``value`` whatever its class's own code would answer.

    As a value, the check accepts a dict, list, or tuple subclass and any
    registered ``Mapping``; as a dict key, it accepts a ``str`` subclass. An
    object that redefines ``__class__`` or attribute lookup, as a lazy
    object does, can pass for one of those. Only an object of any other
    class is certain to be refused.
    """
    try:
        value_type = type(value)
        mro = _CLASS_MRO.__get__(value_type)
        accepted: tuple[type, ...] = (str,) if is_key else (dict, list, tuple)
        if any(_is_one_of(base, accepted) for base in mro):
            return False
        for base in mro:
            if base is object:
                continue
            namespace = _CLASS_NAMESPACE.__get__(base)
            for hook in ("__class__", *_ATTRIBUTE_HOOKS):
                found, entry = _stored_entry(namespace, hook)
                if found and not (hook != "__class__" and _runs_only_builtin_code(base, entry)):
                    return False
        # The key check is `isinstance(key, str)`, which no registry changes.
        # The ABC check asks the class registry, not the value.
        return is_key or not issubclass(value_type, Mapping)
    except Exception:  # noqa: BLE001 - an exotic class must not stop the check
        return False


def _js_data_module_values(component: type[Component], source: str) -> Callable[[_SentName], _ModuleValueIssue | None]:
    """
    Return a check that says why a module-level value in a component's `js_data()` cannot be sent as JSON.

    The check answers None for a name that `js_data()` binds itself, for a
    name its module does not define, for an attribute it cannot read
    without running code, and for a value the browser can receive.
    """
    owner = next(
        (candidate for candidate in _static_class_mro(component) if "js_data" in _static_class_dict(candidate)), None
    )
    module = sys.modules.get(getattr(owner, "__module__", "")) if owner is not None else None
    qualname = _safe_class_text(owner, "__qualname__") if owner is not None else None
    if module is None or qualname is None:
        return lambda _sent: None
    try:
        scope = _python_qualified_scope(ast.parse(source), qualname)
    except (SyntaxError, ValueError):
        return lambda _sent: None
    method = next(
        (
            statement
            for statement in getattr(scope, "body", ())
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)) and statement.name == "js_data"
        ),
        None,
    )
    if method is None:
        return lambda _sent: None
    local_names = _function_local_names(source, method)
    if local_names is None:
        return lambda _sent: None

    def resolve(path: tuple[str, ...]) -> tuple[bool, object]:
        root = path[0]
        # A name js_data() binds itself hides the module name of the same
        # spelling, so the module's value is not what it sends.
        if not root.isidentifier() or root in local_names:
            return False, None
        # The module itself is read the same careful way as its attributes,
        # because `sys.modules` may hold any object.
        found, value = _read_stored_attribute(module, root)
        if not found:
            return False, None
        for name in path[1:]:
            found, value = _read_stored_attribute(value, name)
            if not found:
                return False, None
        return True, value

    def issue(sent: _SentName) -> _ModuleValueIssue | None:
        # A call that only looks like `Const(...)` may compute anything.
        for wrapper in sent.wrappers:
            found, callee = resolve(wrapper)
            if not found or callee is not Const:
                return None
        found, value = resolve(sent.path)
        if not found:
            return None
        label = ".".join(sent.path)
        if sent.starred:
            # `[*TOKENS]` sends TOKENS' items as a list; anything other than
            # a plain collection would run code to produce them.
            if not _is_one_of(type(value), (list, tuple, set, frozenset, dict)):
                return None
            value = list(cast("Iterable[object]", value))
        opaque = _first_opaque_part(value)
        if opaque is not None:
            # A value reached through attributes is judged only when it is
            # plain data. A module constant that holds something else is
            # reported only when no code of its own could make it pass.
            # Rendering checks data at any depth and raises for such a part,
            # so the part is reported however deeply it sits.
            name = _safe_class_text(type(opaque.value), "__name__")
            if len(sent.path) > 1 or name is None or not _never_json(opaque.value, is_key=opaque.is_key):
                return None
            what = "a dict key" if opaque.is_key else "a value"
            return _ModuleValueIssue(
                f"{label}{opaque.path} holds {what} of type {name}, which cannot be sent to the browser as JSON",
                secret=False,
            )
        try:
            _json_plain(value)
        except _SecretInBrowserDataError:
            # Rendering would raise for this value, so name the key that
            # holds the Secret, the way the runtime error does.
            path = _secret_key_path(value) or ""
            return _ModuleValueIssue(
                f"{label}{path} is a Secret; read the value on the server instead",
                secret=True,
            )
        except TypeError as exc:
            return _ModuleValueIssue(f"{label}: {exc}", secret=False)
        except ValueError as exc:
            return _ModuleValueIssue(f"{label}: {exc}", secret=False)
        return None

    return issue


def _function_local_names(source: str, function: ast.FunctionDef | ast.AsyncFunctionDef) -> frozenset[str] | None:
    """
    Return every name a function binds for itself, which hides a module name of the same spelling.

    Python's own symbol table decides, so a parameter, an assignment, an
    import, an `except ... as` name, a `match` capture, and a nested `def`
    all count, while a `global` name does not. None means the source could
    not be read, or that this interpreter has no symbol table (PyPy).
    """
    text = ast.get_source_segment(source, function)
    if text is None:
        return None
    # No symbol table means no answer, so the caller reads no module values.
    if symtable is None:
        return None
    try:
        table = symtable.symtable(textwrap.dedent(text), "<js_data>", "exec")
    except (SyntaxError, ValueError):
        return None
    scope = next((child for child in table.get_children() if child.get_name() == function.name), None)
    if scope is None:
        return None
    return frozenset(symbol.get_name() for symbol in scope.get_symbols() if symbol.is_local() or symbol.is_parameter())


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
    *,
    kind: Literal["js", "css"] = "js",
) -> None:
    """Collect supported inline/file component JavaScript, or CSS with ``kind="css"``, without executing loaders."""
    try:
        owner, inline, filepath = _find_pair_declaration(component, kind, f"{kind}_file")
    except (Exception, SystemExit):  # noqa: BLE001 - one invalid component must not stop the batch
        return
    if inline is None and filepath is None:
        return
    # A `js_lang` or `css_lang` value names a source language Citry does not read.
    if _effective_class_value(component, f"{kind}_lang") is not None:
        return
    if type(inline) is str:
        inline_key: tuple[object, ...] = (id(owner), kind)
        existing = sources.get(inline_key)
        if existing is None:
            sources[inline_key] = _BrowserSource(
                f"{_class_label(owner)}.{kind}",
                normalize_inline_asset(inline),
                [component],
                "inline",
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
        sources[file_key] = _BrowserSource(str(resolved), content, [component], "file")
    else:
        existing.consumers.append(component)


def _check_browser_source(
    engine: Citry,
    source: _BrowserSource,
    profiles: dict[str, dict[str, frozenset[str]]],
    *,
    i18n_configured: bool = False,
) -> list[CheckFinding]:
    """Check component initializer variables and literal server calls."""
    consumers: list[ComponentJsLintConsumer] = []
    member_rules: set[str] = set()
    for component in source.consumers:
        lint = _component_lint_info(engine, component)
        member_rules.add(lint.rule_unknown_component_js_member)
        known_names = {variable.name for variable in lint.component_js_globals}
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
    # A missing instance member is reported only when every consumer's
    # js_data() keys are known ahead of time; a component whose keys are only
    # set at run time is not checked. One source can serve several components,
    # so the strictest of their member severities applies, as for the variable
    # rule above, and the language server resolves it the same way.
    member_severity: Literal["ignore", "warning", "error"] = (
        "error"
        if "error" in member_rules or not member_rules
        else "warning"
        if "warning" in member_rules
        else "ignore"
    )
    findings.extend(
        _browser_source_finding(
            source.origin,
            source.content,
            finding.start_index,
            finding.end_index,
            finding.code,
            finding.message,
            finding.severity,
        )
        for finding in lint_unknown_component_js_members(
            source.content,
            _shared_js_data_names(engine, source.consumers),
            severity=member_severity,
        )
    )
    expression = BrowserExpression(
        source.content,
        0,
        len(source.content.encode("utf-8")),
        "statement",
        "component-js",
    )
    # Only reads the analyzer proves hold `component.$i18n` or `this.$i18n`
    # are i18n calls; another object that happens to be named `i18n` is not.
    i18n_owners, i18n_owner_spans = component_js_i18n_owners(source.content)
    findings.extend(
        _browser_i18n_profile_findings(
            source.origin,
            source.content,
            expression,
            profiles,
            i18n_configured=i18n_configured,
            owners=i18n_owners,
            proven_owner_spans=i18n_owner_spans,
        )
    )
    js_findings: tuple[ComponentJsLintFinding | VueLintFinding, ...] = (
        *lint_undeclared_component_js_emits(source.content),
        *lint_component_js_prop_assignments(
            source.content,
            severities=[
                _component_lint_info(engine, component).rule_prop_assignment for component in source.consumers
            ],
        ),
    )
    findings.extend(
        _browser_source_finding(
            source.origin,
            source.content,
            finding.start_index,
            finding.end_index,
            finding.code,
            finding.message,
            finding.severity,
        )
        for finding in js_findings
    )
    event_names = _shared_event_names(source.consumers)
    if event_names is None:
        return findings
    findings.extend(_unknown_event_findings(source.origin, source.content, expression, event_names))
    return findings


def _shared_js_data_names(engine: Citry, consumers: list[type[Component]]) -> frozenset[str] | None:
    """Return fields available to every owner, declining open or unknown data."""
    if not consumers:
        return None
    names: list[frozenset[str]] = []
    for component in consumers:
        schema = engine.inspect_component(component).schemas.js_data
        if schema.kind == "fields" and schema.namespace_policy == "closed":
            names.append(frozenset(field.name for field in schema.fields))
        elif schema.kind == "absent":
            analyzed = _disk_js_data_shape(component)
            if analyzed is None or analyzed[2].completeness != "closed":
                return None
            names.append(frozenset(root.name for root in analyzed[2].roots))
        else:
            return None
    return frozenset.intersection(*names)


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


def _shared_state_names(consumers: list[type[Component]]) -> frozenset[str] | None:
    """Keep only public State fields accepted by every known template owner."""
    if not consumers:
        return None
    names: list[set[str]] = []
    for component in consumers:
        info = _component_events_info(component)
        names.append(set(info.state_meta.public) if info is not None and info.state_meta is not None else set())
    common = names[0]
    for candidate in names[1:]:
        common.intersection_update(candidate)
    return frozenset(common)


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
    source: _TemplateSource,
    template: Template,
    known_names: set[str],
) -> Generator[Call, Any, list[CheckFinding]]:
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
                findings.append(
                    _ranged_finding(
                        source,
                        render_diagnostic(TEMPLATE_UNKNOWN_COMPONENT, tag=tag_name),
                        TEMPLATE_UNKNOWN_COMPONENT,
                        start_index=tag_token.start_index,
                        end_index=tag_token.end_index,
                    )
                )
        body = getattr(node, "body", None)
        if body is not None:
            findings.extend((yield Call(_unknown_component_findings, source, body, known_names)))
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
    # `col_offset` counts UTF-8 bytes on Python's own line, so the line is
    # split the way Python splits it before the offset is added.
    lines = source_lines(source)
    start_index = sum(len(line.encode("utf-8")) for line in lines[: target.lineno - 1]) + target.col_offset
    end_index = start_index + len(name.encode("utf-8"))
    return _byte_range_coordinates(source, start_index, end_index)


def _range_source(source: str, value_range: Any) -> str | None:
    if value_range is None:
        return None
    start = _lsp_position_char_offset(source, value_range.start.line, value_range.start.character)
    end = _lsp_position_char_offset(source, value_range.end.line, value_range.end.character)
    return source[start:end] if start is not None and end is not None and start <= end else None


def _lsp_range_coordinates(source: str, value_range: Any) -> tuple[int, int, int, int, int, int] | None:
    # The checker reads every other file the way Python reads text, with
    # each line break as one "\n", so byte offsets here count the same way.
    # Lines and columns do not depend on how a line ends.
    text = _CR_LINE_BREAK.sub("\n", source)
    start_char = _lsp_position_char_offset(text, value_range.start.line, value_range.start.character)
    end_char = _lsp_position_char_offset(text, value_range.end.line, value_range.end.character)
    if start_char is None or end_char is None:
        return None
    return _byte_range_coordinates(
        text,
        len(text[:start_char].encode("utf-8")),
        len(text[:end_char].encode("utf-8")),
    )


def _lsp_position_char_offset(source: str, line: int, character: int) -> int | None:
    # LSP clients end lines only at CR LF, CR, and LF.
    lines = source_lines(source)
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
    source_kind: SourceKind | None = None,
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
        source_kind,
    )


def _byte_offset_coordinates(source: str, offset: int) -> tuple[int, int]:
    """
    Return the line and column of a UTF-8 byte offset in ``source``.

    Both count from 0 and the column is in UTF-16 code units, as the Language
    Server Protocol counts them, so an editor can use them unchanged. Every
    finding range whose text the checker holds goes through here, which keeps
    all rules on one numbering.
    """
    prefix = source.encode("utf-8")[:offset].decode("utf-8")
    # Lines end where Python and editors end them (CR LF, CR, or LF), so a
    # Python file and the template inside it count lines the same way.
    current = source_lines(prefix)[-1] if prefix else ""
    if current.endswith(("\n", "\r")):
        current = ""
    return line_break_count(prefix), len(current.encode("utf-16-le")) // 2


def _byte_range_coordinates(source: str, start_index: int, end_index: int) -> tuple[int, int, int, int, int, int]:
    """Return a byte range in ``source`` with the line and column of each end, as ``_source_finding`` takes it."""
    line, column = _byte_offset_coordinates(source, start_index)
    end_line, end_column = _byte_offset_coordinates(source, end_index)
    return start_index, end_index, line, column, end_line, end_column


def _ranged_finding(
    source: _TemplateSource | _BrowserSource,
    message: str,
    code: str,
    *,
    start_index: int,
    end_index: int,
    severity: Literal["warning", "error"] = "error",
) -> CheckFinding:
    """Place a finding at byte offsets in one checked source, counting its range from that source's start."""
    line, column = _byte_offset_coordinates(source.content, start_index)
    end_line, end_column = _byte_offset_coordinates(source.content, end_index)
    return CheckFinding(
        source.origin,
        message,
        code,
        severity,
        start_index,
        end_index,
        line,
        column,
        end_line,
        end_column,
        source.source_kind,
    )


def _counted_in(findings: Iterable[CheckFinding], source_kind: SourceKind) -> list[CheckFinding]:
    """Record which text each positioned finding counts its range in."""
    # The rules for one source compute ranges in that source's text; only the
    # caller knows whether that text is a whole file or an inline attribute.
    return [
        replace(finding, source_kind=source_kind)
        if finding.start_index is not None and finding.source_kind is None
        else finding
        for finding in findings
    ]


def _i18n_compile_diagnostic(exc: BaseException) -> dict[str, Any] | None:
    """Return the located compiler diagnostic behind a catalog failure, if any."""
    # The i18n extension re-raises compile errors as ValueError, so the
    # compiler's own error is usually the cause rather than the exception itself.
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, I18nCompileError):
            try:
                diagnostic = json.loads(current.diagnostic_json)
            except (TypeError, ValueError):
                return None
            # Only a diagnostic with a complete position can place the finding.
            required = ("path", "start", "end", "line", "column")
            if isinstance(diagnostic, dict) and all(diagnostic.get(key) is not None for key in required):
                return diagnostic
            return None
        # Follow only an explicit `raise ... from`, so an unrelated error raised
        # while handling another one cannot lend its position.
        current = current.__cause__
    return None


def _i18n_catalog_texts(
    engine: Citry,
    extension: I18nExtension,
    components: Iterable[type[Component]],
) -> dict[str, tuple[str, SourceKind]]:
    """
    Return the text of each message source the i18n compiler reads, keyed by the path its diagnostics name.

    Each text comes with whether it is a file or a component's inline
    ``messages`` string, which is what a finding's ``source_kind`` reports.
    A component source is the text the messages loader produced, after
    extension hooks; one that failed to load, such as one the compiler
    rejected, is read again from its declaration.
    """
    texts: dict[str, tuple[str, SourceKind]] = {}
    # This only improves how a catalog error is placed, so a source the
    # checker cannot read back is skipped rather than turned into a crash.
    with suppress(Exception):
        for package in extension._packages:
            for package_source in package.sources:
                texts[package_source.path] = (package_source.content, "file")
    for component in components:
        with suppress(Exception):
            owner, inline, filepath = _find_pair_declaration(component, "messages", "messages_file")
            loaded = loaded_messages_source(component)
            if loaded is not None:
                _loaded_owner, content, origin = loaded
                texts[origin] = (content, "inline" if type(inline) is str else "file")
                continue
            # The keys repeat how the messages loader names each source.
            if type(inline) is str:
                texts[f"{_inline_origin(owner)}.messages"] = (normalize_inline_asset(inline), "inline")
            elif isinstance(filepath, (str, Path)):
                resolved = _inspect_asset_path(
                    filepath,
                    owner_dir=module_dir(owner),
                    search_dirs=engine.settings.dirs,
                ).resolved_path
                if resolved is not None:
                    texts[str(resolved)] = (resolved.read_text(encoding="utf-8"), "file")
    return texts


def _i18n_diagnostic_finding(
    diagnostic: Mapping[str, Any],
    catalog_texts: Mapping[str, tuple[str, SourceKind]],
    *,
    message: str,
    code: str,
    severity: Literal["warning", "error"] = "error",
) -> CheckFinding:
    """Place one i18n compiler diagnostic at the message source it names."""
    start, end = diagnostic["start"], diagnostic["end"]
    found = catalog_texts.get(diagnostic["path"])
    if found is not None and 0 <= start <= end <= len(found[0].encode("utf-8")):
        # The compiler counts lines and characters from 1, so the range is
        # rebuilt from its byte offsets to count like every other finding.
        text, source_kind = found
        coordinates = _byte_range_coordinates(text, start, end)
    else:
        # Without the text, shift the compiler's own numbers to count from 0;
        # its columns count characters, which matches UTF-16 units except
        # after an emoji. Its diagnostics cover one line, so the end column
        # follows from the span length. The messages loader names an inline
        # source `<module file>::<Class>.messages`, and anything else is a file.
        line, column = diagnostic["line"] - 1, diagnostic["column"] - 1
        coordinates = (start, end, line, column, line, column + end - start)
        path = diagnostic["path"]
        source_kind = "inline" if "::" in path and path.endswith(".messages") else "file"
    return _source_finding(
        origin=diagnostic["path"],
        message=message,
        code=code,
        severity=severity,
        coordinates=coordinates,
        source_kind=source_kind,
    )


def _error_detail(exc: BaseException) -> str:
    detail = str(exc)
    error_type = type(exc).__name__
    return f"{error_type}: {detail}" if detail else error_type


def _project_module_check(file: Path, root: Path) -> Callable[[str, int], bool]:
    """Return whether an import in ``file`` names a module of the project under ``root``."""

    def check(module: str, level: int) -> bool:
        return project_module_exists(module, level, file=file, root=root)

    return check


def _untraced_template_note(path: Path, untraced: UntracedComponentTemplate) -> str:
    """Write the note for a template `--static` skips, with its file, line, and code."""
    message = render_diagnostic(CHECK_TEMPLATE_NOT_CHECKED, component=untraced.component_name, base=untraced.base)
    return f"{path}:{untraced.line}: {message} [{CHECK_TEMPLATE_NOT_CHECKED}]"


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
