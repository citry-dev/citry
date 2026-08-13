"""
The Citry settings schema.

``CitrySettings`` is the typed, immutable configuration for a ``Citry`` instance.
It starts small and grows field-by-field as the engine does. Unknown settings
are rejected: ``Citry`` accepts only the fields defined here.

See ``docs/design/extensions.md`` section 5.2 for the rationale (a real schema
object, not a loose dict).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast, get_args

from citry_core.template_parser import analyze_browser_source

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from citry.cache import CitryCache
    from citry.extension import Extension

# The build environment (dev_prod_mode.md). Defined as a real value, not only a
# type annotation, so the allowed set can be derived from it for validation.
Mode = Literal["production", "development"]
_ALLOWED_MODES: tuple[str, ...] = get_args(Mode)
LintSeverity = Literal["ignore", "warning", "error"]
_ALLOWED_LINT_SEVERITIES: tuple[str, ...] = get_args(LintSeverity)
SecurityCspMode = Literal["off", "warn", "strict"]
_ALLOWED_SECURITY_CSP_MODES: tuple[str, ...] = get_args(SecurityCspMode)
SecurityJavascriptMode = Literal["allow", "warn", "omit", "forbid"]
_ALLOWED_SECURITY_JAVASCRIPT_MODES: tuple[str, ...] = get_args(SecurityJavascriptMode)
SecurityScriptIntegrityMode = Literal["off", "citry"]
_ALLOWED_SECURITY_SCRIPT_INTEGRITY_MODES: tuple[str, ...] = get_args(SecurityScriptIntegrityMode)


def _validate_security_mode(name: str, value: object, allowed: tuple[str, ...]) -> str:
    """Validate one engine or per-serialization security mode."""
    if type(value) is not str or value not in allowed:
        msg = f"Citry {name} must be one of {allowed}, got {value!r}"
        raise ValueError(msg)
    return value


def _validate_security_csp(value: object) -> SecurityCspMode:
    return cast("SecurityCspMode", _validate_security_mode("security_csp", value, _ALLOWED_SECURITY_CSP_MODES))


def _validate_security_javascript(value: object) -> SecurityJavascriptMode:
    return cast(
        "SecurityJavascriptMode",
        _validate_security_mode("security_javascript", value, _ALLOWED_SECURITY_JAVASCRIPT_MODES),
    )


def _validate_security_script_integrity(value: object) -> SecurityScriptIntegrityMode:
    return cast(
        "SecurityScriptIntegrityMode",
        _validate_security_mode(
            "security_script_integrity",
            value,
            _ALLOWED_SECURITY_SCRIPT_INTEGRITY_MODES,
        ),
    )


def _is_template_variable_name(name: object) -> bool:
    """Return whether a string has one exact Python identifier identity."""
    if type(name) is not str or not name:
        return False
    try:
        parsed = ast.parse(name, mode="eval").body
    except (SyntaxError, UnicodeEncodeError, ValueError):
        return False
    # Python normalizes some Unicode spellings while parsing. Runtime mapping
    # keys do not, so accept only a name whose parsed identity is unchanged.
    return isinstance(parsed, ast.Name) and parsed.id == name


def _is_alpine_variable_name(name: object) -> bool:
    """Return whether OXC parses a string as one exact free JS identifier."""
    if type(name) is not str or not name:
        return False
    try:
        valid, references = analyze_browser_source(name, "expression")
    except (TypeError, ValueError, UnicodeError):
        return False
    encoded_length = len(name.encode("utf-8"))
    return valid and references == [(name, 0, encoded_length)]


@dataclass(frozen=True, slots=True)
class LintSettings:
    """
    Configure Citry's template and browser lint rules and analysis-only variables.

    Attributes:
        rule_unknown_template_variable: Severity for a free template root that
            is absent from the proven component namespace. The default is
            ``"error"``. A schema that explicitly allows extra fields caps
            this rule at ``"warning"``.
        template_variables: Extra variables known to template analysis but not
            injected at runtime. Values are annotations. Use
            ``Annotated[T, "description"]`` to attach concise documentation.
        rule_unknown_alpine_variable: Severity for a free Alpine-expression
            root absent from the component's proven browser scope. The default
            is ``"error"``.
        alpine_variables: Extra variables or custom Alpine magics known only to
            browser analysis. Values use the same annotation convention as
            ``template_variables``.
        rule_unknown_component_js_variable: Severity for a free variable used
            inside a ``$component`` initializer. The default is ``"error"``.
        component_js_globals: Extra globals available to component JavaScript
            analysis. Values use the same annotation convention as
            ``template_variables``.

    Raises:
        TypeError: If a variable or global collection is not a mapping.
        ValueError: If a severity or variable name is invalid.

    """

    rule_unknown_template_variable: LintSeverity = "error"
    rule_i18n_missing_param_type: LintSeverity = "warning"
    template_variables: Mapping[str, object] = field(default_factory=dict)
    rule_unknown_alpine_variable: LintSeverity = "error"
    alpine_variables: Mapping[str, object] = field(default_factory=dict)
    rule_unknown_component_js_variable: LintSeverity = "error"
    component_js_globals: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if (
            type(self.rule_unknown_template_variable) is not str
            or self.rule_unknown_template_variable not in _ALLOWED_LINT_SEVERITIES
        ):
            msg = (
                "rule_unknown_template_variable must be one of "
                f"{_ALLOWED_LINT_SEVERITIES}, got {self.rule_unknown_template_variable!r}"
            )
            raise ValueError(msg)
        if (
            type(self.rule_i18n_missing_param_type) is not str
            or self.rule_i18n_missing_param_type not in _ALLOWED_LINT_SEVERITIES
        ):
            msg = (
                "rule_i18n_missing_param_type must be one of "
                f"{_ALLOWED_LINT_SEVERITIES}, got {self.rule_i18n_missing_param_type!r}"
            )
            raise ValueError(msg)
        try:
            variables = dict(self.template_variables)
        except (TypeError, ValueError) as err:
            msg = "LintSettings.template_variables must be a mapping"
            raise TypeError(msg) from err
        invalid_name = next((name for name in variables if not _is_template_variable_name(name)), None)
        if invalid_name is not None:
            msg = f"LintSettings.template_variables contains invalid template variable name {invalid_name!r}"
            raise ValueError(msg)
        object.__setattr__(self, "template_variables", variables)
        if (
            type(self.rule_unknown_alpine_variable) is not str
            or self.rule_unknown_alpine_variable not in _ALLOWED_LINT_SEVERITIES
        ):
            msg = (
                "rule_unknown_alpine_variable must be one of "
                f"{_ALLOWED_LINT_SEVERITIES}, got {self.rule_unknown_alpine_variable!r}"
            )
            raise ValueError(msg)
        try:
            alpine_variables = dict(self.alpine_variables)
        except (TypeError, ValueError) as err:
            msg = "LintSettings.alpine_variables must be a mapping"
            raise TypeError(msg) from err
        invalid_alpine_name = next(
            (name for name in alpine_variables if not _is_alpine_variable_name(name)),
            None,
        )
        if invalid_alpine_name is not None:
            msg = f"LintSettings.alpine_variables contains invalid Alpine variable name {invalid_alpine_name!r}"
            raise ValueError(msg)
        object.__setattr__(self, "alpine_variables", alpine_variables)
        if (
            type(self.rule_unknown_component_js_variable) is not str
            or self.rule_unknown_component_js_variable not in _ALLOWED_LINT_SEVERITIES
        ):
            msg = (
                "rule_unknown_component_js_variable must be one of "
                f"{_ALLOWED_LINT_SEVERITIES}, got {self.rule_unknown_component_js_variable!r}"
            )
            raise ValueError(msg)
        try:
            component_js_globals = dict(self.component_js_globals)
        except (TypeError, ValueError) as err:
            msg = "LintSettings.component_js_globals must be a mapping"
            raise TypeError(msg) from err
        invalid_component_js_name = next(
            (name for name in component_js_globals if not _is_alpine_variable_name(name)),
            None,
        )
        if invalid_component_js_name is not None:
            msg = (
                "LintSettings.component_js_globals contains invalid JavaScript identifier "
                f"{invalid_component_js_name!r}"
            )
            raise ValueError(msg)
        object.__setattr__(self, "component_js_globals", component_js_globals)


@dataclass(frozen=True, slots=True)
class CitrySettings:
    """
    Immutable settings for a ``Citry`` instance.

    Attributes:
        extensions: The extensions to install on the instance. Each entry is
            an ``Extension`` subclass, a ready-made instance, or an import
            string like ``"myapp.extensions.MyExtension"``. The set is fixed
            once the instance is constructed.
        extensions_defaults: Default config values for extensions, keyed by
            extension name, e.g. ``{"events": {"_csrf": True}}``. When an
            extension reads a config field for a component, the component's
            own nested config class wins, a value given here fills in next,
            and the extension's built-in default comes last.
        dirs: Directories searched when resolving a component's asset files
            (``template_file``, ``js_file``, ``css_file``, and ``Dependencies``
            entries), after the directory of the component's own ``.py`` file.
            Entries are converted to ``Path`` and must be absolute; this is
            validated at construction (a relative entry raises ``ValueError``).
        cache: Where citry stores what it caches: a
            [`CitryCache`][citry.CitryCache] object or an import string
            like ``"myapp.caching.MyCache"``. ``None`` gives the instance its
            own in-memory cache. The live backend built from this setting is
            ``Citry.cache``.
        sandbox_expressions: Whether template expressions (``{{ ... }}`` and
            dynamic ``c-*`` attributes) are evaluated in the security sandbox.
            On by default. Turning it off evaluates expressions as plain Python,
            which is faster but removes security guardrails.
            Only do so when every template comes from a trusted source.
        autodiscover: Whether to import the component modules under ``dirs`` the
            first time a component is looked up, so their classes register
            themselves without being imported by hand. On by default; when no
            ``dirs`` are set there is nothing to scan, so the default instance
            does nothing. The directories must be importable (on
            ``sys.path``/``PYTHONPATH``). See ``Citry.autodiscover`` and
            ``citry.autodiscovery``.
        mode: The build environment, ``"production"`` (the default) or
            ``"development"``. It is the single source of truth for whether the
            engine includes developer-only output: in ``"development"`` the
            built-in ``debug`` extension is auto-registered (visual component
            boundaries) and the client ownership graph carries source
            provenance. An unrecognized value raises ``ValueError`` at
            construction. See ``docs/design/dev_prod_mode.md``.
        template_globals: Variables exposed to every component's template
            without being returned from each ``template_data()``. They are
            merged into every component's template variables on render, so a
            template can reference one directly (``{{ site_name }}``). A
            component's own ``template_data`` wins when it returns a key of the
            same name, so globals act as defaults. The value given here is the
            starting set; the live, editable copy is ``Citry.template_globals``,
            which is how you add or change a global after the instance exists
            (including the default instance, created at import before your code
            runs).
        lint: Template lint severities and analysis-only variables. Runtime
            globals are discovered from ``Citry.template_globals`` and do not
            need to be repeated here.
        security_csp: CSP compatibility policy for Citry-managed output.
            ``"off"`` preserves current behavior, ``"warn"`` reports
            incompatibilities without changing output, and ``"strict"``
            enforces Citry's strict-CSP contract.
        security_javascript: JavaScript delivery policy. ``"allow"`` keeps
            current behavior, ``"warn"`` inventories client requirements,
            ``"omit"`` leaves Citry-managed JavaScript out, and ``"forbid"``
            rejects rendered subtrees that require executable client behavior.
        security_script_integrity: Script integrity policy. ``"off"`` does
            not compute security digests; ``"citry"`` collects SHA-384
            metadata for structured scripts whose bytes Citry can prove.
        id_generator: A function returning the per-render id stamped on each
            component instance (``component.id``, which drives the
            ``data-cid-<id>`` markers that scope a component's CSS and JS on the
            page). Given as a callable or a ``"path.to.func"`` import string;
            passing a class also works: it is called once, and the resulting
            object is used as the generator (handy when the generator keeps
            state, like a counter). ``None`` uses the built-in generator. Override
            it for stable ids in snapshot tests. The generator must return ids
            that are unique among the components on one page and contain only
            lowercase ASCII letters, digits, hyphens, and underscores. The
            lowercase rule is required because the id is embedded in an HTML
            attribute name. This does not touch ``class_id``, which stays a
            stable hash of the component's import path.
        secret: The signing secret for values citry hands to the browser and
            must recognize when they come back, such as the state the Events
            extension round-trips on each event call. A single string is the
            common form. A list means key rotation: the first entry signs new
            values, and a value signed by any entry still verifies, so
            already-issued values stay valid while a new key rolls out. A bare
            string is stored as a one-element list. ``None`` (the default)
            means no secret is set. Django projects can reuse their existing
            key by passing ``citry.contrib.django.secret()``.
        event_result_resolvers: Result resolvers for the Events extension.
            When an event handler returns a value, citry converts it into the
            actions sent back to the browser (the instructions the client
            runtime applies: re-render this component, redirect, and so on).
            A resolver adds support for your own return types: it is given the
            handler's return value and either converts it into those actions
            or declines, letting the next resolver try. Resolvers run in
            order, after the built-in conversions; the first one to convert
            the value wins.
        event_payload_codecs: Payload codecs for the Events extension's HTTP
            endpoints. A codec reads one request format (identified by its
            content type) into the event call the extension expects, so
            clients are not limited to the built-in JSON, form, and query
            formats. Codecs given here are tried before the built-in ones, in
            order.

        Every security mode is enforced during serialization. The defaults
        preserve established output; restrictive JavaScript modes inventory,
        omit, or reject client behavior without changing render-cache data.

    """

    extensions: Sequence[type[Extension] | Extension | str] = ()
    extensions_defaults: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    dirs: tuple[Path, ...] = ()
    cache: CitryCache | str | None = None
    sandbox_expressions: bool = True
    autodiscover: bool = True
    mode: Mode = "production"
    template_globals: Mapping[str, Any] = field(default_factory=dict)
    lint: LintSettings = field(default_factory=LintSettings)
    # Advanced/niche settings
    id_generator: Callable[[], str] | str | None = None
    secret: str | list[str] | None = None
    event_result_resolvers: Sequence[Any] = ()
    event_payload_codecs: Sequence[Any] = ()
    security_csp: SecurityCspMode = "off"
    security_javascript: SecurityJavascriptMode = "allow"
    security_script_integrity: SecurityScriptIntegrityMode = "off"

    def __post_init__(self) -> None:
        # Copy every input into its immutable stored shape, so a direct
        # CitrySettings(...) is as safe as one built through Citry(...):
        # changing a caller's list or dict after construction cannot reach
        # into these frozen settings, and both construction paths store the
        # same shape.

        # The build environment is a fixed set of strings. Reject an unknown
        # value here so a typo cannot silently ship or omit developer output;
        # every later read of the mode can then trust it (dev_prod_mode.md).
        if self.mode not in _ALLOWED_MODES:
            msg = f"Citry mode must be one of {_ALLOWED_MODES}, got {self.mode!r}"
            raise ValueError(msg)

        _validate_security_csp(self.security_csp)
        _validate_security_javascript(self.security_javascript)
        _validate_security_script_integrity(self.security_script_integrity)

        # Extensions are copied into a tuple of their own.
        object.__setattr__(self, "extensions", tuple(self.extensions))

        # Asset search dirs must be absolute, the same rule django-components
        # has for COMPONENTS.dirs. Relative lookups need no entry here: a
        # component's files already resolve against its own .py file. Each
        # entry is converted to Path and the whole is stored as a tuple.
        dir_paths = tuple(Path(d) for d in self.dirs)
        for dir_path in dir_paths:
            if not dir_path.is_absolute():
                msg = f"Citry dirs must be absolute paths, got {str(dir_path)!r}"
                raise ValueError(msg)
        object.__setattr__(self, "dirs", dir_paths)

        # The two config mappings are stored as fresh dicts, so changing the
        # caller's mapping cannot change these frozen settings.
        object.__setattr__(self, "extensions_defaults", dict(self.extensions_defaults))
        object.__setattr__(self, "template_globals", dict(self.template_globals))
        if type(self.lint) is not LintSettings:
            msg = "CitrySettings.lint must be a LintSettings value"
            raise TypeError(msg)

        # A bare-string secret is stored as a one-element list, so readers
        # always see the rotation form: first entry signs, every entry verifies.
        if isinstance(self.secret, str):
            object.__setattr__(self, "secret", [self.secret])
        elif self.secret is not None:
            # A copy, so changing the caller's list cannot change these settings.
            object.__setattr__(self, "secret", list(self.secret))

        # The resolver and codec sequences are copied into tuples of their own.
        object.__setattr__(self, "event_result_resolvers", tuple(self.event_result_resolvers))
        object.__setattr__(self, "event_payload_codecs", tuple(self.event_payload_codecs))
