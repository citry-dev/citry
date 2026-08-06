"""Conservative authored-template analysis for ``citry check``."""

from __future__ import annotations

import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from citry._app_selection import CheckAppSelection, app_failure_message
from citry._class_introspection import _safe_class_import_path, _static_class_dict, _static_class_mro
from citry._inline_assets import normalize_inline_asset
from citry.analysis import discover_python_templates
from citry.assets import _find_pair_declaration, _inspect_asset_path, module_dir
from citry.autodiscovery import _iter_py_files
from citry.tag_rules import build_tag_rules
from citry_core.template_parser import RESERVED_TAG_NAMES, TemplateElement, parse_diagnostic, parse_template

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry import Citry
    from citry.component import Component
    from citry_core.template_parser import TagRules, Template


TRANSFORM_NOTE = "extension-transformed template validation is unavailable; checking authored Citry source"


@dataclass(frozen=True, slots=True)
class CheckFinding:
    """One source or template finding."""

    origin: str
    message: str
    code: str = "citry.check.finding"
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
        if self.findings:
            return 1
        return 0


@dataclass(frozen=True, slots=True)
class _TemplateSource:
    origin: str
    content: str


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
    unique_classes = {id(comp_cls): comp_cls for comp_cls in registrations.values()}
    components = sorted(unique_classes.values(), key=_class_label)
    findings: list[CheckFinding] = []
    sources: list[_TemplateSource] = []
    seen_sources: set[tuple[object, ...]] = set()
    seen_file_paths: set[Path] = set()

    for comp_cls in components:
        if engine._is_builtin_component(comp_cls):
            continue
        class_label = _class_label(comp_cls)
        try:
            owner, inline, filepath = _find_pair_declaration(comp_cls, "template", "template_file")
        except (Exception, SystemExit) as exc:  # noqa: BLE001 - one bad component must not stop the batch
            findings.append(CheckFinding(class_label, _error_message("cannot inspect template declaration", exc)))
            continue

        if inline is None and filepath is None:
            continue
        language = _effective_class_value(comp_cls, "template_lang")
        if language is not None:
            findings.append(
                CheckFinding(
                    class_label,
                    f"unsupported non-None template_lang ({type(language).__name__}); template skipped",
                ),
            )
            continue

        source_key = (id(owner), "template")
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        if inline is not None:
            if type(inline) is not str:
                findings.append(CheckFinding(class_label, "inline template is not a str; template skipped"))
                continue
            sources.append(
                _TemplateSource(
                    origin=f"{_class_label(owner)}.template",
                    content=normalize_inline_asset(inline),
                ),
            )
            continue
        if not isinstance(filepath, (str, Path)):
            findings.append(CheckFinding(class_label, "template_file is not a str or Path; template skipped"))
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
                    CheckFinding(class_label, f"cannot resolve template_file {str(filepath)!r}; searched {locations}"),
                )
                continue
            resolved_identity = resolved.resolve()
            if resolved_identity in seen_file_paths:
                continue
            seen_file_paths.add(resolved_identity)
            content = resolved.read_text(encoding="utf-8")
        except (Exception, SystemExit) as exc:  # noqa: BLE001 - one bad asset must not stop the batch
            findings.append(CheckFinding(class_label, _error_message("cannot read template_file", exc)))
            continue
        sources.append(_TemplateSource(origin=str(resolved), content=content))

    for source in sources:
        findings.extend(_check_template(source, rules=rules, known_names=known_names))
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
            findings.append(CheckFinding(str(path), _error_message("cannot analyze Python source", exc)))
            continue
        findings.extend(
            CheckFinding(
                f"{path} ({notice.component_name}.template)",
                notice.message,
            )
            for notice in discovery.notices
        )
        for region in discovery.regions:
            findings.extend(
                _check_template(
                    _TemplateSource(
                        origin=f"{path} ({region.component_name}.template)",
                        content=region.source_map.template_source,
                    ),
                ),
            )
    return findings


def _check_template(
    source: _TemplateSource,
    *,
    rules: Mapping[str, TagRules] | None = None,
    known_names: set[str] | None = None,
) -> list[CheckFinding]:
    """Parse one source and, in registry mode, inspect component tag names."""
    try:
        template = parse_template(source.content, user_rules=dict(rules) if rules is not None else None)
    except (SyntaxError, ValueError) as exc:
        diagnostic = parse_diagnostic(exc)
        if diagnostic is None:
            return [CheckFinding(source.origin, str(exc), code="citry.parse.configuration")]
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
    if known_names is None:
        return []
    return _unknown_component_findings(source.origin, template, known_names)


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
                        f"{line}:{column}: unknown registered component <{tag_name}>",
                        code="citry.component.unknown",
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


def _error_message(prefix: str, exc: BaseException) -> str:
    detail = str(exc)
    error_type = type(exc).__name__
    return f"{prefix}: {error_type}: {detail}" if detail else f"{prefix}: {error_type}"


__all__: list[str] = []
