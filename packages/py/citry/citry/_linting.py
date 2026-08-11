"""Build portable template-lint settings without retaining runtime values."""

from __future__ import annotations

import ast
import types
import typing
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast, get_args, get_origin

from citry._class_introspection import _safe_class_import_path, _static_class_dict, _static_class_mro
from citry._nested_declarations import _active_nested_class_declarations
from citry._schema_introspection import _format_annotation
from citry.introspection import _is_utf8_string
from citry.settings import LintSettings, LintSeverity, _is_alpine_variable_name

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry import Citry

VariableSource = Literal["runtime-global", "application", "component", "extension"]
NamespacePolicy = Literal["closed", "allow-extra", "unknown"]
_VARIABLE_SOURCES = {"runtime-global", "application", "component", "extension"}
_NAMESPACE_POLICIES = {"closed", "allow-extra", "unknown"}
_RULE_SEVERITIES = {"ignore", "warning", "error"}


@dataclass(frozen=True, slots=True)
class TemplateVariableInfo:
    """Describe one known template variable using detached portable text."""

    name: str
    type_display: str | None
    type_fidelity: Literal["normalized", "unavailable"]
    description: str | None
    source: VariableSource

    def __post_init__(self) -> None:
        if not _is_exact_template_name(self.name):
            msg = f"Invalid portable template variable name: {self.name!r}"
            raise ValueError(msg)
        normalized = type(self.type_display) is str and bool(self.type_display)
        unavailable = self.type_display is None
        if (self.type_fidelity == "normalized" and not normalized) or (
            self.type_fidelity == "unavailable" and not unavailable
        ):
            msg = "Template variable type fidelity must match its display value"
            raise ValueError(msg)
        if self.type_display is not None and not _is_utf8_string(self.type_display):
            msg = "Template variable type displays must be valid UTF-8 strings"
            raise ValueError(msg)
        if self.type_display is not None and _normalize_type_display(self.type_display) != self.type_display:
            msg = "Template variable type displays must be canonical passive annotation expressions"
            raise ValueError(msg)
        if self.description is not None and (type(self.description) is not str or not self.description):
            msg = "Template variable descriptions must be non-empty strings or None"
            raise ValueError(msg)
        if self.description is not None and not _is_utf8_string(self.description):
            msg = "Template variable descriptions must be valid UTF-8 strings"
            raise ValueError(msg)
        if type(self.source) is not str or self.source not in _VARIABLE_SOURCES:
            msg = f"Unknown template variable source: {self.source!r}"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready detached copy."""
        return {
            "name": self.name,
            "type_display": self.type_display,
            "type_fidelity": self.type_fidelity,
            "description": self.description,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, value: object) -> TemplateVariableInfo:
        """Validate and restore one detached variable record."""
        if type(value) is not dict or set(value) != {
            "name",
            "type_display",
            "type_fidelity",
            "description",
            "source",
        }:
            msg = "template variable data must contain the exact supported fields"
            raise ValueError(msg)
        return cls(
            name=value["name"],  # type: ignore[arg-type]
            type_display=value["type_display"],  # type: ignore[arg-type]
            type_fidelity=value["type_fidelity"],  # type: ignore[arg-type]
            description=value["description"],  # type: ignore[arg-type]
            source=value["source"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class AlpineVariableInfo:
    """Describe one known Alpine variable using detached portable text."""

    name: str
    type_display: str | None
    type_fidelity: Literal["normalized", "unavailable"]
    description: str | None
    source: VariableSource

    def __post_init__(self) -> None:
        if not _is_alpine_variable_name(self.name):
            msg = f"Invalid portable Alpine variable name: {self.name!r}"
            raise ValueError(msg)
        normalized = type(self.type_display) is str and bool(self.type_display)
        unavailable = self.type_display is None
        if (self.type_fidelity == "normalized" and not normalized) or (
            self.type_fidelity == "unavailable" and not unavailable
        ):
            msg = "Alpine variable type fidelity must match its display value"
            raise ValueError(msg)
        if self.type_display is not None and not _is_utf8_string(self.type_display):
            msg = "Alpine variable type displays must be valid UTF-8 strings"
            raise ValueError(msg)
        if self.type_display is not None and _normalize_type_display(self.type_display) != self.type_display:
            msg = "Alpine variable type displays must be canonical passive annotation expressions"
            raise ValueError(msg)
        if self.description is not None and (type(self.description) is not str or not self.description):
            msg = "Alpine variable descriptions must be non-empty strings or None"
            raise ValueError(msg)
        if self.description is not None and not _is_utf8_string(self.description):
            msg = "Alpine variable descriptions must be valid UTF-8 strings"
            raise ValueError(msg)
        if type(self.source) is not str or self.source not in _VARIABLE_SOURCES:
            msg = f"Unknown Alpine variable source: {self.source!r}"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready detached copy."""
        return {
            "name": self.name,
            "type_display": self.type_display,
            "type_fidelity": self.type_fidelity,
            "description": self.description,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, value: object) -> AlpineVariableInfo:
        """Validate and restore one detached variable record."""
        if type(value) is not dict or set(value) != {
            "name",
            "type_display",
            "type_fidelity",
            "description",
            "source",
        }:
            msg = "Alpine variable data must contain the exact supported fields"
            raise ValueError(msg)
        return cls(
            name=value["name"],  # type: ignore[arg-type]
            type_display=value["type_display"],  # type: ignore[arg-type]
            type_fidelity=value["type_fidelity"],  # type: ignore[arg-type]
            description=value["description"],  # type: ignore[arg-type]
            source=value["source"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class TemplateLintInfo:
    """Carry one component's effective lint rule and known global variables."""

    rule_unknown_template_variable: LintSeverity
    template_variables: tuple[TemplateVariableInfo, ...]
    rule_i18n_missing_param_type: LintSeverity = "warning"
    rule_unknown_alpine_variable: LintSeverity = "error"
    alpine_variables: tuple[AlpineVariableInfo, ...] = ()
    rule_unknown_component_js_variable: LintSeverity = "error"
    component_js_globals: tuple[AlpineVariableInfo, ...] = ()
    allows_extra_variables: bool = False

    def __post_init__(self) -> None:
        if (
            type(self.rule_unknown_template_variable) is not str
            or self.rule_unknown_template_variable not in _RULE_SEVERITIES
        ):
            msg = f"Unknown template lint severity: {self.rule_unknown_template_variable!r}"
            raise ValueError(msg)
        if type(self.template_variables) is not tuple or any(
            type(item) is not TemplateVariableInfo for item in self.template_variables
        ):
            msg = "TemplateLintInfo.template_variables must be a tuple of TemplateVariableInfo values"
            raise TypeError(msg)
        if (
            type(self.rule_i18n_missing_param_type) is not str
            or self.rule_i18n_missing_param_type not in _RULE_SEVERITIES
        ):
            msg = f"Unknown i18n missing-param lint severity: {self.rule_i18n_missing_param_type!r}"
            raise ValueError(msg)
        if (
            type(self.rule_unknown_alpine_variable) is not str
            or self.rule_unknown_alpine_variable not in _RULE_SEVERITIES
        ):
            msg = f"Unknown Alpine lint severity: {self.rule_unknown_alpine_variable!r}"
            raise ValueError(msg)
        if type(self.alpine_variables) is not tuple or any(
            type(item) is not AlpineVariableInfo for item in self.alpine_variables
        ):
            msg = "TemplateLintInfo.alpine_variables must be a tuple of AlpineVariableInfo values"
            raise TypeError(msg)
        if (
            type(self.rule_unknown_component_js_variable) is not str
            or self.rule_unknown_component_js_variable not in _RULE_SEVERITIES
        ):
            msg = f"Unknown component-JavaScript lint severity: {self.rule_unknown_component_js_variable!r}"
            raise ValueError(msg)
        if type(self.component_js_globals) is not tuple or any(
            type(item) is not AlpineVariableInfo for item in self.component_js_globals
        ):
            msg = "TemplateLintInfo.component_js_globals must be a tuple of AlpineVariableInfo values"
            raise TypeError(msg)
        if type(self.allows_extra_variables) is not bool:
            msg = "TemplateLintInfo.allows_extra_variables must be a bool"
            raise TypeError(msg)
        names = tuple(item.name for item in self.template_variables)
        if names != tuple(sorted(set(names))):
            msg = "Template lint variables must be unique and sorted by name"
            raise ValueError(msg)
        alpine_names = tuple(item.name for item in self.alpine_variables)
        if alpine_names != tuple(sorted(set(alpine_names))):
            msg = "Alpine lint variables must be unique and sorted by name"
            raise ValueError(msg)
        component_js_names = tuple(item.name for item in self.component_js_globals)
        if component_js_names != tuple(sorted(set(component_js_names))):
            msg = "Component JavaScript globals must be unique and sorted by name"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready detached copy."""
        return {
            "rule_unknown_template_variable": self.rule_unknown_template_variable,
            "template_variables": [item.to_dict() for item in self.template_variables],
            "rule_i18n_missing_param_type": self.rule_i18n_missing_param_type,
            "rule_unknown_alpine_variable": self.rule_unknown_alpine_variable,
            "alpine_variables": [item.to_dict() for item in self.alpine_variables],
            "rule_unknown_component_js_variable": self.rule_unknown_component_js_variable,
            "component_js_globals": [item.to_dict() for item in self.component_js_globals],
            "allows_extra_variables": self.allows_extra_variables,
        }

    @classmethod
    def from_dict(cls, value: object) -> TemplateLintInfo:
        """Validate and restore one detached lint record."""
        if type(value) is not dict or set(value) != {
            "rule_unknown_template_variable",
            "template_variables",
            "rule_i18n_missing_param_type",
            "rule_unknown_alpine_variable",
            "alpine_variables",
            "rule_unknown_component_js_variable",
            "component_js_globals",
            "allows_extra_variables",
        }:
            msg = "template lint data must contain the exact supported fields"
            raise ValueError(msg)
        variables = value["template_variables"]
        if type(variables) is not list:
            msg = "template_variables must be a list"
            raise ValueError(msg)
        alpine_variables = value["alpine_variables"]
        if type(alpine_variables) is not list:
            msg = "alpine_variables must be a list"
            raise ValueError(msg)
        component_js_globals = value["component_js_globals"]
        if type(component_js_globals) is not list:
            msg = "component_js_globals must be a list"
            raise ValueError(msg)
        return cls(
            rule_unknown_template_variable=value["rule_unknown_template_variable"],  # type: ignore[arg-type]
            template_variables=tuple(TemplateVariableInfo.from_dict(item) for item in variables),
            rule_i18n_missing_param_type=value["rule_i18n_missing_param_type"],  # type: ignore[arg-type]
            rule_unknown_alpine_variable=value["rule_unknown_alpine_variable"],  # type: ignore[arg-type]
            alpine_variables=tuple(AlpineVariableInfo.from_dict(item) for item in alpine_variables),
            rule_unknown_component_js_variable=value["rule_unknown_component_js_variable"],  # type: ignore[arg-type]
            component_js_globals=tuple(AlpineVariableInfo.from_dict(item) for item in component_js_globals),
            allows_extra_variables=value["allows_extra_variables"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class _ComponentLintOverrides:
    """Hold only the component-authored values layered over application policy."""

    rule_unknown_template_variable: LintSeverity | None
    rule_i18n_missing_param_type: LintSeverity | None
    template_variables: Mapping[str, object]
    variable_owners: Mapping[str, type]
    rule_unknown_alpine_variable: LintSeverity | None
    alpine_variables: Mapping[str, object]
    alpine_variable_owners: Mapping[str, type]
    rule_unknown_component_js_variable: LintSeverity | None
    component_js_globals: Mapping[str, object]
    component_js_global_owners: Mapping[str, type]


def _application_lint_info(citry: Citry) -> TemplateLintInfo:
    """Detach live runtime globals and application lint metadata for tooling."""
    variables = {
        name: _runtime_variable_info(name, value)
        for name, value in citry.template_globals.items()
        if _is_exact_template_name(name)
    }
    for name, annotation in citry.settings.lint.template_variables.items():
        variables[name] = _annotation_variable_info(name, annotation, source="application")
    alpine_variables = {
        name: _annotation_alpine_variable_info(name, annotation, source="application")
        for name, annotation in citry.settings.lint.alpine_variables.items()
    }
    component_js_globals = {
        name: _annotation_alpine_variable_info(name, annotation, source="application")
        for name, annotation in citry.settings.lint.component_js_globals.items()
    }
    return TemplateLintInfo(
        rule_unknown_template_variable=citry.settings.lint.rule_unknown_template_variable,
        template_variables=tuple(variables[name] for name in sorted(variables)),
        rule_i18n_missing_param_type=citry.settings.lint.rule_i18n_missing_param_type,
        rule_unknown_alpine_variable=citry.settings.lint.rule_unknown_alpine_variable,
        alpine_variables=tuple(alpine_variables[name] for name in sorted(alpine_variables)),
        rule_unknown_component_js_variable=citry.settings.lint.rule_unknown_component_js_variable,
        component_js_globals=tuple(component_js_globals[name] for name in sorted(component_js_globals)),
    )


def _component_lint_info(citry: Citry, component_class: type) -> TemplateLintInfo:
    """Apply one component's C3-composed overrides to application metadata."""
    application = _application_lint_info(citry)
    overrides = _component_lint_overrides(component_class)
    variables: dict[str, TemplateVariableInfo] = {}
    allows_extra_variables = False
    for _extension_name, contribution in citry.extensions._template_namespace_contributions(component_class):
        allows_extra_variables = allows_extra_variables or contribution.allows_extra_variables
        for name, annotation in contribution.template_variables.items():
            candidate = _annotation_variable_info(name, annotation, source="extension")
            previous = variables.get(name)
            if previous is None or previous == candidate:
                variables[name] = candidate
            else:
                # Conflicting extension claims keep the name known without
                # guessing which detached type or description is authoritative.
                variables[name] = TemplateVariableInfo(name, None, "unavailable", None, "extension")
    variables.update((item.name, item) for item in application.template_variables)
    for name, annotation in overrides.template_variables.items():
        variables[name] = _annotation_variable_info(name, annotation, source="component")
    alpine_variables = {item.name: item for item in application.alpine_variables}
    for name, annotation in overrides.alpine_variables.items():
        alpine_variables[name] = _annotation_alpine_variable_info(name, annotation, source="component")
    component_js_globals = {item.name: item for item in application.component_js_globals}
    for name, annotation in overrides.component_js_globals.items():
        component_js_globals[name] = _annotation_alpine_variable_info(name, annotation, source="component")
    return TemplateLintInfo(
        rule_unknown_template_variable=(
            overrides.rule_unknown_template_variable
            if overrides.rule_unknown_template_variable is not None
            else application.rule_unknown_template_variable
        ),
        template_variables=tuple(variables[name] for name in sorted(variables)),
        rule_i18n_missing_param_type=(
            overrides.rule_i18n_missing_param_type
            if overrides.rule_i18n_missing_param_type is not None
            else application.rule_i18n_missing_param_type
        ),
        rule_unknown_alpine_variable=(
            overrides.rule_unknown_alpine_variable
            if overrides.rule_unknown_alpine_variable is not None
            else application.rule_unknown_alpine_variable
        ),
        alpine_variables=tuple(alpine_variables[name] for name in sorted(alpine_variables)),
        rule_unknown_component_js_variable=(
            overrides.rule_unknown_component_js_variable
            if overrides.rule_unknown_component_js_variable is not None
            else application.rule_unknown_component_js_variable
        ),
        component_js_globals=tuple(component_js_globals[name] for name in sorted(component_js_globals)),
        allows_extra_variables=allows_extra_variables,
    )


def _validate_component_lint(component_class: type) -> None:
    """Reject malformed nested Lint declarations while defining a component."""
    _component_lint_overrides(component_class)


def _component_lint_overrides(component_class: type) -> _ComponentLintOverrides:
    """Compose active nested Lint declarations from base to nearest class."""
    rule: LintSeverity | None = None
    i18n_missing_param_rule: LintSeverity | None = None
    variables: dict[str, object] = {}
    variable_owners: dict[str, type] = {}
    alpine_rule: LintSeverity | None = None
    alpine_variables: dict[str, object] = {}
    alpine_variable_owners: dict[str, type] = {}
    component_js_rule: LintSeverity | None = None
    component_js_globals: dict[str, object] = {}
    component_js_global_owners: dict[str, type] = {}
    declarations = _active_nested_class_declarations(component_class, "Lint")
    for declaration in reversed(declarations):
        lint_class = cast("type", declaration.value)
        public_values: dict[str, object] = {}
        public_owners: dict[str, type] = {}
        for candidate in reversed(_static_class_mro(lint_class)):
            for name, value in _static_class_dict(candidate).items():
                if name.startswith("_"):
                    continue
                public_values[name] = value
                public_owners[name] = candidate
        unknown = set(public_values) - {
            "rule_unknown_template_variable",
            "rule_i18n_missing_param_type",
            "template_variables",
            "rule_unknown_alpine_variable",
            "alpine_variables",
            "rule_unknown_component_js_variable",
            "component_js_globals",
        }
        if unknown:
            rendered = ", ".join(sorted(unknown))
            msg = f"Component {component_class.__name__}.Lint has unknown setting(s): {rendered}"
            raise ValueError(msg)
        if "rule_unknown_template_variable" in public_values:
            candidate_rule = public_values["rule_unknown_template_variable"]
            if type(candidate_rule) is not str or candidate_rule not in _RULE_SEVERITIES:
                msg = (
                    f"Component {component_class.__name__}.Lint.rule_unknown_template_variable "
                    "must be 'ignore', 'warning', or 'error'"
                )
                raise ValueError(msg)
            rule = cast("LintSeverity", candidate_rule)
        if "rule_i18n_missing_param_type" in public_values:
            candidate_rule = public_values["rule_i18n_missing_param_type"]
            if type(candidate_rule) is not str or candidate_rule not in _RULE_SEVERITIES:
                msg = (
                    f"Component {component_class.__name__}.Lint.rule_i18n_missing_param_type "
                    "must be 'ignore', 'warning', or 'error'"
                )
                raise ValueError(msg)
            i18n_missing_param_rule = cast("LintSeverity", candidate_rule)
        if "rule_unknown_alpine_variable" in public_values:
            candidate_rule = public_values["rule_unknown_alpine_variable"]
            if type(candidate_rule) is not str or candidate_rule not in _RULE_SEVERITIES:
                msg = (
                    f"Component {component_class.__name__}.Lint.rule_unknown_alpine_variable "
                    "must be 'ignore', 'warning', or 'error'"
                )
                raise ValueError(msg)
            alpine_rule = cast("LintSeverity", candidate_rule)
        if "rule_unknown_component_js_variable" in public_values:
            candidate_rule = public_values["rule_unknown_component_js_variable"]
            if type(candidate_rule) is not str or candidate_rule not in _RULE_SEVERITIES:
                msg = (
                    f"Component {component_class.__name__}.Lint.rule_unknown_component_js_variable "
                    "must be 'ignore', 'warning', or 'error'"
                )
                raise ValueError(msg)
            component_js_rule = cast("LintSeverity", candidate_rule)
        if "template_variables" in public_values:
            candidate_variables = public_values["template_variables"]
            try:
                # Reuse the public settings validator so component and app
                # names follow exactly the same Python identity contract.
                validated = LintSettings(template_variables=cast("Mapping[str, object]", candidate_variables))
            except TypeError as err:
                msg = f"Component {component_class.__name__}.Lint.template_variables must be a mapping"
                raise TypeError(msg) from err
            variables.update(validated.template_variables)
            owner = public_owners["template_variables"]
            variable_owners.update(dict.fromkeys(validated.template_variables, owner))
        if "alpine_variables" in public_values:
            candidate_variables = public_values["alpine_variables"]
            try:
                validated = LintSettings(alpine_variables=cast("Mapping[str, object]", candidate_variables))
            except TypeError as err:
                msg = f"Component {component_class.__name__}.Lint.alpine_variables must be a mapping"
                raise TypeError(msg) from err
            alpine_variables.update(validated.alpine_variables)
            owner = public_owners["alpine_variables"]
            alpine_variable_owners.update(dict.fromkeys(validated.alpine_variables, owner))
        if "component_js_globals" in public_values:
            candidate_variables = public_values["component_js_globals"]
            try:
                validated = LintSettings(component_js_globals=cast("Mapping[str, object]", candidate_variables))
            except TypeError as err:
                msg = f"Component {component_class.__name__}.Lint.component_js_globals must be a mapping"
                raise TypeError(msg) from err
            component_js_globals.update(validated.component_js_globals)
            owner = public_owners["component_js_globals"]
            component_js_global_owners.update(dict.fromkeys(validated.component_js_globals, owner))
    return _ComponentLintOverrides(
        rule,
        i18n_missing_param_rule,
        variables,
        variable_owners,
        alpine_rule,
        alpine_variables,
        alpine_variable_owners,
        component_js_rule,
        component_js_globals,
        component_js_global_owners,
    )


def _component_lint_variable_owners(component_class: type) -> Mapping[str, type]:
    """Return the exact nested class that supplied each effective variable."""
    return _component_lint_overrides(component_class).variable_owners


def _component_alpine_variable_owners(component_class: type) -> Mapping[str, type]:
    """Return the nested class that supplied each effective Alpine variable."""
    return _component_lint_overrides(component_class).alpine_variable_owners


def _component_js_global_owners(component_class: type) -> Mapping[str, type]:
    """Return the nested class that supplied each component-JavaScript global."""
    return _component_lint_overrides(component_class).component_js_global_owners


def _annotation_variable_info(
    name: str,
    annotation: object,
    *,
    source: VariableSource,
) -> TemplateVariableInfo:
    """Detach a supported annotation and optional Annotated description."""
    value = annotation
    description: str | None = None
    try:
        origin = get_origin(annotation)
        arguments = get_args(annotation)
    except Exception:  # noqa: BLE001 - user typing objects may define unsafe protocols
        origin = None
        arguments = ()
    if origin is typing.Annotated and arguments:
        value = arguments[0]
        metadata = arguments[1:]
        if len(metadata) == 1 and type(metadata[0]) is str and metadata[0]:
            description = metadata[0]
    type_display = _normalize_type_display(_format_annotation(value))
    return TemplateVariableInfo(
        name=name,
        type_display=type_display,
        type_fidelity="normalized" if type_display is not None else "unavailable",
        description=description,
        source=source,
    )


def _annotation_alpine_variable_info(
    name: str,
    annotation: object,
    *,
    source: VariableSource,
) -> AlpineVariableInfo:
    """Detach an Alpine analysis-only annotation and optional description."""
    value = annotation
    description: str | None = None
    try:
        origin = get_origin(annotation)
        arguments = get_args(annotation)
    except Exception:  # noqa: BLE001 - user typing objects may define unsafe protocols
        origin = None
        arguments = ()
    if origin is typing.Annotated and arguments:
        value = arguments[0]
        metadata = arguments[1:]
        if len(metadata) == 1 and type(metadata[0]) is str and metadata[0]:
            description = metadata[0]
    type_display = _normalize_type_display(_format_annotation(value))
    return AlpineVariableInfo(
        name=name,
        type_display=type_display,
        type_fidelity="normalized" if type_display is not None else "unavailable",
        description=description,
        source=source,
    )


def _runtime_variable_info(name: str, value: object) -> TemplateVariableInfo:
    """Infer only stable runtime value shapes that can cross the worker boundary."""
    type_display = _normalize_type_display(_runtime_type_display(value))
    return TemplateVariableInfo(
        name=name,
        type_display=type_display,
        type_fidelity="normalized" if type_display is not None else "unavailable",
        description=None,
        source="runtime-global",
    )


def _runtime_type_display(value: object, active: set[int] | None = None) -> str | None:
    """Return a conservative type display without retaining or serializing the value."""
    if value is None:
        return None
    value_type = type(value)
    if value_type in {bool, bytes, float, int, str}:
        return _format_annotation(value_type)
    if value_type is type:
        class_path = _safe_class_import_path(cast("type", value))
        return f"type[{class_path}]" if class_path is not None else None
    if value_type in {list, tuple, set, frozenset}:
        if active is None:
            active = set()
        identity = id(value)
        if identity in active:
            return None
        active.add(identity)
        items = cast("list[object] | tuple[object, ...] | set[object] | frozenset[object]", value)
        try:
            item_types = {_runtime_type_display(item, active) for item in items}
            if not items or None in item_types or len(item_types) != 1:
                return None
            label = value_type.__name__
            return f"{label}[{next(iter(item_types))}]"
        finally:
            active.remove(identity)
    if value_type is dict:
        if active is None:
            active = set()
        identity = id(value)
        if identity in active:
            return None
        active.add(identity)
        mapping = cast("dict[object, object]", value)
        try:
            key_types = {_runtime_type_display(item, active) for item in mapping}
            value_types = {_runtime_type_display(item, active) for item in mapping.values()}
            if not mapping or None in key_types or None in value_types or len(key_types) != 1 or len(value_types) != 1:
                return None
            return f"dict[{next(iter(key_types))}, {next(iter(value_types))}]"
        finally:
            active.remove(identity)
    if value_type is types.MappingProxyType:
        return None
    return _safe_class_import_path(value_type)


def _is_exact_template_name(name: object) -> bool:
    """Match runtime mapping keys to the parser's exact Python name identity."""
    if type(name) is not str or not name:
        return False
    try:
        node = ast.parse(name, mode="eval").body
    except (SyntaxError, UnicodeEncodeError, ValueError):
        return False
    return isinstance(node, ast.Name) and node.id == name


def _normalize_type_display(value: str | None) -> str | None:
    """Keep one passive annotation expression and canonicalize its spelling."""
    if value is None:
        return None
    try:
        expression = ast.parse(value, mode="eval")
    except (SyntaxError, UnicodeEncodeError, ValueError, MemoryError, RecursionError):
        return None
    forbidden = (
        ast.Await,
        ast.Call,
        ast.DictComp,
        ast.GeneratorExp,
        ast.IfExp,
        ast.Lambda,
        ast.ListComp,
        ast.NamedExpr,
        ast.SetComp,
        ast.Yield,
        ast.YieldFrom,
    )
    if any(isinstance(node, forbidden) for node in ast.walk(expression)):
        return None
    normalized = ast.unparse(expression.body)
    return normalized if _is_utf8_string(normalized) else None


__all__: list[str] = []
