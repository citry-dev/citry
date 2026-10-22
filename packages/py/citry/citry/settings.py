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
    from collections.abc import Callable, Iterable, Mapping, Sequence

    from typing_extensions import Self

    from citry.cache import CitryCache
    from citry.extension import Extension

# The build environment (dev_prod_mode.md). Defined as a real value, not only a
# type annotation, so the allowed set can be derived from it for validation.
Mode = Literal["production", "development"]
_ALLOWED_MODES: tuple[str, ...] = get_args(Mode)
# 64 MiB: generous, so an app with many components and stylesheets rarely
# drops one an open page still needs.
DEFAULT_VUE_ASSET_MAX_BYTES = 64 * 1024 * 1024
# Deep enough for any real page, low enough that data which contains itself
# fails within a fraction of a second instead of exhausting memory.
DEFAULT_MAX_COMPONENT_DEPTH = 2000
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


# Lint setting names from citry 0.5.1 mapped to the setting that took over
# their job. They are not accepted as aliases (Alpine's `$` helpers have no
# meaning in a Vue scope); the map only lets the error name the replacement.
_REPLACED_LINT_SETTINGS: dict[str, str] = {
    "rule_unknown_alpine_variable": "rule_unknown_vue_variable",
    "alpine_variables": "vue_variables",
}


def _replaced_lint_settings_hint(names: Iterable[str]) -> str | None:
    """Return a sentence naming the replacement for each 0.5.1 lint setting in ``names``, or None."""
    replaced = sorted(name for name in names if name in _REPLACED_LINT_SETTINGS)
    if not replaced:
        return None
    renames = ", ".join(f"{name!r} to {_REPLACED_LINT_SETTINGS[name]!r}" for name in replaced)
    return f"Vue lint settings replace the Alpine ones; rename {renames}."


def _is_vue_variable_name(name: object) -> bool:
    """Return whether OXC parses a string as one exact free JS identifier."""
    if type(name) is not str or not name:
        return False
    try:
        valid, references = analyze_browser_source(name, "expression")
    except (TypeError, ValueError, UnicodeError):
        return False
    encoded_length = len(name.encode("utf-8"))
    return valid and references == [(name, 0, encoded_length)]


# Rule severities that LintSettings, a component's Lint class, and the
# editor's lint record each store as a plain string, so every place that
# copies, checks, or combines them reads this one list.
_TEMPLATE_RULE_FIELDS = (
    "rule_misspelled_attribute",
    "rule_misspelled_element",
    "rule_unknown_aria_attribute",
    "rule_invalid_nesting",
    "rule_duplicate_id",
    "rule_missing_image_alt",
    "rule_invalid_model_target",
    "rule_misspelled_event",
    "rule_invalid_vue_expression",
    "rule_vue_compile_error",
    "rule_undeclared_component_event",
    "rule_missing_component_key",
    "rule_prop_assignment",
    "rule_unknown_server_event_field",
    "rule_missing_server_event_field",
    "rule_incompatible_server_event_field",
    "rule_unknown_form_field",
    "rule_missing_form_field",
    "rule_misspelled_css_variable",
    "rule_misspelled_css_class",
    "rule_undeclared_css_class",
    "rule_undeclared_css_variable",
    "rule_unknown_url",
    "rule_unknown_inject_key",
)


@dataclass(frozen=True, slots=True)
class LintSettings:
    """
    Configure Citry's template and browser lint rules, analysis-only variables, and the render-time input type check.

    Attributes:
        rule_unknown_template_variable: Severity for a free template root that
            is absent from the proven component namespace. The default is
            ``"error"``. A schema that explicitly allows extra fields caps
            this rule at ``"warning"``.
        rule_i18n_missing_param_type: Severity for a translation message
            variable that has no ``@param`` comment giving its type, when
            the variable is used only as plain text on the server. Variables
            used in a selector, a formatting function, a browser call, or as a
            ``Slot`` always need a type, whatever this setting says. The
            default is ``"warning"``.
        template_variables: Extra variables known to template analysis but not
            injected at runtime. Values are annotations. Use
            ``Annotated[T, "description"]`` to attach concise documentation.
        rule_unknown_vue_variable: Severity for a free Vue-expression
            root absent from the component's proven browser scope. The default
            is ``"error"``.
        vue_variables: Extra variables or custom Vue magics known only to
            browser analysis. Values use the same annotation convention as
            ``template_variables``.
        rule_unknown_component_js_variable: Severity for a free variable used
            inside a ``$component`` initializer. The default is ``"error"``.
        component_js_globals: Extra globals available to component JavaScript
            analysis. Values use the same annotation convention as
            ``template_variables``.
        rule_unknown_component_js_member: Severity for a ``this.<name>`` or
            ``component.<name>`` read in component JavaScript that the
            component instance does not have. The default is ``"error"``.
        rule_vue_python_variable: Severity for a Vue expression that reads a
            name bound in Python by an enclosing ``c-for`` loop or
            ``c-fill`` binding. The browser looks that name up in Vue state,
            not in the Python loop. The default is ``"warning"``.
        rule_alpine_attribute: Severity for an Alpine ``x-*`` attribute, such
            as ``x-data`` or ``x-on:click``, on an HTML element. Citry uses
            Vue, so nothing reads the attribute. Set ``"ignore"`` when another
            library on the page reads ``x-*`` attributes. The default is
            ``"warning"``.
        rule_alpine_cloak: Severity for ``x-cloak`` on an HTML element.
            Nothing in Citry removes the attribute, so a ``[x-cloak]`` CSS
            rule keeps the element hidden. The default is ``"error"``.
        rule_invalid_attribute_value: Severity for a static HTML attribute
            value outside the keywords that attribute accepts, such as
            ``draggable="treu"`` or ``<input type="datetime">``, or for a
            boolean attribute with a value other than its own name, such as
            ``disabled="false"``, which still disables the element. For an
            enumerated value, the browser ignores it or falls back to a
            default. The default is
            ``"error"``. ``citry check --static`` and an editor that has not
            loaded the application report it as a warning, because they
            cannot read your settings.
        rule_i18n_cross_language_fallback: Severity for a ``tr()`` call, a
            ``self.i18n.tr()`` call, or a message in
            ``I18n.client_messages`` that has no translation in some
            locale, so that locale shows text from a fallback language. The
            page still renders, but the text cannot mark its own language.
            Set ``"error"`` to require complete translations. A
            ``<c-trans>`` message is always an error, because rendering it
            in another language fails. The default is ``"warning"``.
        rule_misspelled_directive: Severity for a ``c-*`` attribute on an
            HTML element or custom element that looks like a misspelled
            Citry directive, such as ``c-iff`` for ``c-if``, or ``c-show``,
            which Citry writes as ``c-if``. Citry renders it as an ordinary attribute,
            so the directive never runs; with ``c-iff`` the element always
            shows up. An attribute of the element, such as ``c-id``, is not
            reported. It also covers a ``v-*`` name that looks like a
            misspelled Vue directive, such as ``v-iff``, which Vue looks up
            as a custom directive, so the page fails in the browser. The default is
            ``"error"``.
        rule_misspelled_attribute: Severity for an attribute on an HTML
            element that is one typing slip from an attribute the element
            accepts, such as ``titel`` for ``title``. The browser ignores
            it. The default is ``"error"``.
        rule_misspelled_element: Severity for a lowercase tag that is one
            typing slip from an HTML element, such as ``<dvi>``. The
            default is ``"error"``.
        rule_unknown_aria_attribute: Severity for an ``aria-*`` attribute
            that WAI-ARIA does not define, such as ``aria-expandd``.
            Browsers and screen readers ignore it. The default is
            ``"error"``.
        rule_invalid_nesting: Severity for an element that the browser
            moves out of an open ``<p>``, such as ``<div>`` inside
            ``<p>``. The default is ``"error"``.
        rule_duplicate_id: Severity for a literal ``id`` that two elements
            of one template always render. The default is ``"error"``.
        rule_missing_image_alt: Severity for an ``<img>`` with no ``alt``
            text. The default is ``"warning"``.
        rule_invalid_model_target: Severity for ``v-model`` on an element
            that holds no value, such as ``<form>``, which fails when Vue
            compiles the page. The default is ``"error"``.
        rule_misspelled_event: Severity for a listener on an HTML element
            whose event name is one typing slip from a DOM event, such as
            ``@clik``. The listener never runs. The default is
            ``"warning"``.
        rule_invalid_vue_expression: Severity for a Vue expression, such as
            the value of ``v-if`` or ``@click``, that is not valid
            JavaScript, which fails when Vue compiles the page. The default
            is ``"error"``.
        rule_vue_compile_error: Severity for anything else Vue's compiler
            rejects in a template, such as a ``<div>`` directly inside a
            ``<table>``, a ``<button>`` inside a ``<button>``, or a
            ``v-else`` with no ``v-if`` before it. A component that uses Vue
            fails to render. The default is ``"error"``.
        rule_undeclared_component_event: Severity for a listener on a
            component tag for an event the child component does not declare
            in ``emits``, such as ``@hdie`` for ``hide``. The listener
            usually never runs. ``citry check`` reports it only with your
            application loaded. The default is ``"warning"``.
        rule_missing_component_key: Severity for a component that
            ``<c-for>`` repeats without a ``#c-key`` on a page that uses Vue,
            which fails to render once the loop has two items. ``citry
            check`` reports it only with your application loaded. The
            default is ``"error"``.
        rule_prop_assignment: Severity for a component that assigns to one
            of its own Vue props, such as ``@click="open = false"``. Props
            are read-only, so the value does not change. An assignment in the
            component's JavaScript, such as ``this.open = false``, is at most
            a warning. ``citry check`` reports it only with your application
            loaded. The default is ``"error"``.
        rule_unknown_server_event_field: Severity for an ``@c-*`` binding
            that sends a key the handler's data class does not declare, such
            as ``save({amont: 1})``. The server rejects the call. ``citry
            check`` and the editor report it only with your application
            loaded. The default is ``"error"``.
        rule_missing_server_event_field: Severity for an ``@c-*`` binding
            that leaves out a field the handler's data class requires. The
            server rejects the call. ``citry check`` and the editor report
            it only with your application loaded. The default is
            ``"error"``.
        rule_incompatible_server_event_field: Severity for an ``@c-*``
            binding that sends a literal value the handler's data class does
            not accept, such as ``save({amount: '1'})`` for an ``int``
            field. The server rejects the call. ``citry check`` and the
            editor report it only with your application loaded. The default
            is ``"error"``.
        rule_unknown_form_field: Severity for a control in a form whose
            ``@c-submit`` sends the form's fields to a server event, when
            the handler's data class does not declare the control's
            ``name``, such as ``<input name="qeury">`` for a field ``q``.
            The server rejects each submit that sends the control. ``citry
            check`` and the editor report it only with your application
            loaded. The default is ``"error"``.
        rule_missing_form_field: Severity for a form whose ``@c-submit``
            sends its fields to a server event, when no control in it is
            named after a field the handler's data class requires.
            It is reported only when the template shows every control the
            form can send. ``citry check`` and the editor report it only
            with your application loaded. The default is ``"error"``.
        rule_misspelled_css_variable: Severity for a ``var(--name)`` in a
            component's CSS that is one typing slip from a key its
            ``css_data()`` returns, such as ``var(--acent)`` for
            ``accent``. Nothing sets the property. ``citry check`` reports
            it only with your application loaded. The default is
            ``"warning"``.
        rule_misspelled_css_class: Severity for a class in a template's
            static ``class`` attribute that is one typing slip (two
            neighboring letters swapped, one doubled, or one left out) from
            a class the component's own ``css`` or ``css_file`` styles, such
            as ``bord`` for ``.board``. It is reported only when no CSS
            Citry reads declares the class as written: no registered
            component's CSS, ``Dependencies`` stylesheet, or template
            ``<style>`` element. Slips that usually name another class of
            the same family are not reported: a moved, doubled, or dropped
            digit (``col-1`` for ``.col-12``); a missing final ``s`` after a
            letter other than ``s`` (``tab`` for ``.tabs``); one of these
            short words, as the whole class or as its last word after a
            hyphen or underscore, next to its longer form: ``close``
            (``closed``), ``collapse`` (``collapsed``), ``disable``
            (``disabled``), ``enable`` (``enabled``), ``fade`` (``faded``),
            ``mute`` (``muted``), ``show`` (``shown``), ``slide``
            (``slider``), and ``toggle`` (``toggled`` or ``toggler``), as in
            ``navbar-toggle`` for ``.navbar-toggler``; and one letter typed
            twice or left out in a first hyphen-separated part of one or two
            characters (``p-4`` for ``.px-4``). ``citry check`` reports it
            only with your application loaded. The default is ``"warning"``.
        rule_undeclared_css_class: Severity for every class in a template's
            static ``class`` attribute that no CSS Citry reads declares: no
            registered component's ``css``, ``css_file``, inline or
            local-file ``Dependencies`` stylesheet, or template ``<style>``
            element. Classes from a site stylesheet or a CSS framework such
            as Tailwind, and classes used only by JavaScript or tests, are
            reported too, so the default is ``"ignore"``, which turns the
            rule off. ``citry check`` reports it only with your application
            loaded.
        rule_undeclared_css_variable: Severity for every ``var(--name)``
            without a fallback in a component's ``css`` or ``css_file``
            when nothing Citry reads sets ``--name``: no registered
            component's CSS, ``css_data()`` key, template ``style``
            attribute or binding, JavaScript, or Python module. Properties
            that a site stylesheet, a design system, or a script outside
            Citry sets are reported too, so the default is ``"ignore"``,
            which turns the rule off. ``citry check`` reports it only with
            your application loaded.
        rule_unknown_url: Severity for a literal ``href``, ``src``, or
            ``action`` path, such as ``/abuot``, that none of your app's
            routes or static files serves. ``citry check`` and the editor
            report it only with your application loaded, and only when a
            web framework integration (``citry.contrib.flask.mount()``,
            ``citry.contrib.fastapi.mount()``, or
            ``citry.contrib.django.urlpatterns()``) ran while the app loaded. A
            path another server answers, such as a reverse proxy, is
            reported too. The default is ``"warning"``.
        rule_unknown_inject_key: Severity for a ``self.inject("key")``
            call with a literal key and no default when no provider above
            the component gives that key. Citry looks for a
            ``<c-provide>`` around the component's tag in the templates
            that use it, a ``provide()`` call in the components above it
            or in the component whose ``<c-slot>`` shows it, and a literal
            key in a ``render(provides={...})`` call in your project. When
            no template uses the component, Citry compares the key with
            every key the app provides. A key passed only in a
            ``provides`` dictionary built elsewhere, or provided by a
            helper function, is reported too, so the default is
            ``"warning"``. ``citry check`` and the editor report it only
            with your application loaded.
        check_input_types: Check that each value a component receives has
            the type its annotation names. On by default, in development and
            in production. Unlike the ``rule_*`` settings, this check runs
            when a component renders, not in ``citry check`` or the editor.
            Citry compares each field of the component's ``Kwargs``,
            ``TemplateData``, ``JsData``, ``CssData``, and ``State`` with the
            field's annotation and raises ``TypeError`` for a value of the
            wrong type, so ``Card(title=123)`` against ``title: str`` fails
            with a message that names the component, the field, the expected
            type, and the value. Only the outer type is checked:
            ``list[str]`` accepts any ``list``. A field's own default always
            passes. Annotations Citry cannot test while the page runs, such
            as ``Any``, a type variable, or a name imported only for type
            checkers, are not checked, and Pydantic models and dataclasses
            that write their own ``__init__`` keep their own rules. [Inputs
            and validation](/concepts/inputs-and-validation/#typed-kwargs-checks)
            lists what each annotation accepts. A component overrides this
            for itself with ``check_input_types`` in its nested
            [`Lint`][citry.Component.Lint] class.

    Raises:
        TypeError: If a variable or global collection is not a mapping, or
            ``check_input_types`` is not a ``bool``.
        ValueError: If a severity or variable name is invalid.

    """

    rule_unknown_template_variable: LintSeverity = "error"
    rule_i18n_missing_param_type: LintSeverity = "warning"
    template_variables: Mapping[str, object] = field(default_factory=dict)
    rule_unknown_vue_variable: LintSeverity = "error"
    vue_variables: Mapping[str, object] = field(default_factory=dict)
    rule_unknown_component_js_variable: LintSeverity = "error"
    component_js_globals: Mapping[str, object] = field(default_factory=dict)
    rule_unknown_component_js_member: LintSeverity = "error"
    rule_vue_python_variable: LintSeverity = "warning"
    rule_alpine_attribute: LintSeverity = "warning"
    rule_alpine_cloak: LintSeverity = "error"
    rule_invalid_attribute_value: LintSeverity = "error"
    rule_i18n_cross_language_fallback: LintSeverity = "warning"
    rule_misspelled_directive: LintSeverity = "error"
    rule_misspelled_attribute: LintSeverity = "error"
    rule_misspelled_element: LintSeverity = "error"
    rule_unknown_aria_attribute: LintSeverity = "error"
    rule_invalid_nesting: LintSeverity = "error"
    rule_duplicate_id: LintSeverity = "error"
    rule_missing_image_alt: LintSeverity = "warning"
    rule_invalid_model_target: LintSeverity = "error"
    rule_misspelled_event: LintSeverity = "warning"
    rule_invalid_vue_expression: LintSeverity = "error"
    rule_vue_compile_error: LintSeverity = "error"
    rule_undeclared_component_event: LintSeverity = "warning"
    rule_missing_component_key: LintSeverity = "error"
    rule_prop_assignment: LintSeverity = "error"
    rule_unknown_server_event_field: LintSeverity = "error"
    rule_missing_server_event_field: LintSeverity = "error"
    rule_incompatible_server_event_field: LintSeverity = "error"
    rule_unknown_form_field: LintSeverity = "error"
    rule_missing_form_field: LintSeverity = "error"
    rule_misspelled_css_variable: LintSeverity = "warning"
    rule_misspelled_css_class: LintSeverity = "warning"
    rule_undeclared_css_class: LintSeverity = "ignore"
    rule_undeclared_css_variable: LintSeverity = "ignore"
    rule_unknown_url: LintSeverity = "warning"
    rule_unknown_inject_key: LintSeverity = "warning"
    check_input_types: bool = True

    # Hidden from type checkers so they keep checking calls against the
    # generated __init__ signature.
    if not TYPE_CHECKING:

        def __new__(cls, *_args: object, **kwargs: object) -> Self:
            # The generated __init__ rejects an unknown keyword with a
            # TypeError that suggests the replacement only on Python 3.13+.
            # __new__ sees the same keywords first, so a 0.5.1 name fails
            # with the replacement named on every supported version.
            hint = _replaced_lint_settings_hint(kwargs)
            if hint is not None:
                replaced = ", ".join(sorted(name for name in kwargs if name in _REPLACED_LINT_SETTINGS))
                msg = f"LintSettings got unexpected keyword argument(s): {replaced}. {hint}"
                raise TypeError(msg)
            return object.__new__(cls)

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
            type(self.rule_unknown_vue_variable) is not str
            or self.rule_unknown_vue_variable not in _ALLOWED_LINT_SEVERITIES
        ):
            msg = (
                "rule_unknown_vue_variable must be one of "
                f"{_ALLOWED_LINT_SEVERITIES}, got {self.rule_unknown_vue_variable!r}"
            )
            raise ValueError(msg)
        try:
            vue_variables = dict(self.vue_variables)
        except (TypeError, ValueError) as err:
            msg = "LintSettings.vue_variables must be a mapping"
            raise TypeError(msg) from err
        invalid_vue_name = next(
            (name for name in vue_variables if not _is_vue_variable_name(name)),
            None,
        )
        if invalid_vue_name is not None:
            msg = f"LintSettings.vue_variables contains invalid Vue variable name {invalid_vue_name!r}"
            raise ValueError(msg)
        object.__setattr__(self, "vue_variables", vue_variables)
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
            (name for name in component_js_globals if not _is_vue_variable_name(name)),
            None,
        )
        if invalid_component_js_name is not None:
            msg = (
                "LintSettings.component_js_globals contains invalid JavaScript identifier "
                f"{invalid_component_js_name!r}"
            )
            raise ValueError(msg)
        object.__setattr__(self, "component_js_globals", component_js_globals)
        if (
            type(self.rule_unknown_component_js_member) is not str
            or self.rule_unknown_component_js_member not in _ALLOWED_LINT_SEVERITIES
        ):
            msg = (
                "rule_unknown_component_js_member must be one of "
                f"{_ALLOWED_LINT_SEVERITIES}, got {self.rule_unknown_component_js_member!r}"
            )
            raise ValueError(msg)
        if (
            type(self.rule_vue_python_variable) is not str
            or self.rule_vue_python_variable not in _ALLOWED_LINT_SEVERITIES
        ):
            msg = (
                "rule_vue_python_variable must be one of "
                f"{_ALLOWED_LINT_SEVERITIES}, got {self.rule_vue_python_variable!r}"
            )
            raise ValueError(msg)
        # These rules take the same severities as every other rule, so one
        # loop reports the first invalid one by name.
        for rule_name in (
            "rule_alpine_attribute",
            "rule_alpine_cloak",
            "rule_invalid_attribute_value",
            "rule_misspelled_directive",
            "rule_i18n_cross_language_fallback",
            *_TEMPLATE_RULE_FIELDS,
        ):
            severity = getattr(self, rule_name)
            if type(severity) is not str or severity not in _ALLOWED_LINT_SEVERITIES:
                msg = f"{rule_name} must be one of {_ALLOWED_LINT_SEVERITIES}, got {severity!r}"
                raise ValueError(msg)
        # Every render reads this flag, so a truthy string such as "false"
        # must fail here rather than silently keep the check on.
        if type(self.check_input_types) is not bool:
            msg = f"LintSettings.check_input_types must be True or False, got {self.check_input_types!r}."
            raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class CitrySettings:
    """
    Immutable settings for a ``Citry`` instance.

    Every security mode is enforced during serialization. The defaults
    preserve established output; restrictive JavaScript modes inventory,
    omit, or reject client behavior without changing render-cache data.

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
            ``"development"``. In ``"production"``, each configured i18n
            catalog package must ship a valid compiled manifest, written by
            ``citry ext run i18n compile``; creating the ``Citry`` instance
            raises ``ValueError`` when it is missing or does not match.
            ``"development"`` turns on three things. Citry reads the Fluent
            sources directly; if the package also contains a compiled
            manifest, it must still match the sources, so delete or
            recompile it after editing translations. Turning a page into
            HTML issues a ``RuntimeWarning`` when two elements on it share
            an ``id``, naming the components that wrote them. And Citry
            logs a browser console warning when Vue's first render of a
            part Vue builds in the browser differs from the HTML the
            server sent. A production page does not load this browser
            check. An unrecognized value raises ``ValueError`` at
            construction. See [Development mode](/guides/development-mode/).
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
        lint: Template lint severities, analysis-only variables, and the
            render-time input type check. Runtime globals are discovered from
            ``Citry.template_globals`` and do not need to be repeated here.
        security_csp: Content Security Policy check for rendered output.
            Citry scans the final HTML for raw ``<script>`` and ``<style>``
            elements, inline ``on*`` attributes, and ``javascript:`` URLs.
            ``"off"`` skips the check, ``"warn"`` keeps the output and emits
            one ``RuntimeWarning`` listing what it found, and ``"strict"``
            raises instead of returning that output.
        security_javascript: JavaScript delivery policy. ``"allow"`` keeps
            current behavior, ``"warn"`` inventories client requirements,
            ``"omit"`` leaves Citry-managed JavaScript out, and ``"forbid"``
            rejects rendered subtrees that require executable client behavior.
        security_script_integrity: Script integrity policy. ``"off"`` does
            not compute security digests; ``"citry"`` collects SHA-384
            metadata for structured scripts whose bytes Citry can prove.
        ssr: Send each interactive Vue document's content in its HTML. On by
            default: the server writes the page for Vue to adopt
            ("hydrate"), and a page it cannot write that way carries Citry's
            ordinary server HTML, which Vue replaces when it mounts.
            ``False`` sends an empty mount element instead, and Vue builds
            the page in the browser. Noninteractive output is unchanged.
        ssr_element_threshold: Send small pages without their content. A page
            whose server-written HTML holds this many elements or fewer is
            sent with an empty mount element and built in the browser, which
            can be slightly faster for a small page because the browser does
            not parse the HTML and then hydrate it. The default, ``0``,
            keeps the content of every page that contains an element, which
            search engines and readers without JavaScript need. It applies
            only to pages Vue can adopt; a page Vue replaces always carries
            its server HTML. Must be a non-negative ``int``:
            another type raises ``TypeError`` and a negative value raises
            ``ValueError`` when the settings are created.
        vue_asset_max_bytes: How many bytes of compiled component code and
            stylesheets for interactive pages each process keeps in memory
            when ``cache`` is not set. Interactive pages load these files by
            URL, possibly long after the page was rendered. When the total
            grows past this limit, the files used longest ago are dropped,
            and a page that is still open gets a 404 if it later asks for
            one of them. The files of the page being rendered are never
            dropped, so the total can exceed the limit by that page's
            files. The default is 64 MiB. ``None`` removes the limit.
            When ``cache`` is set, the files are stored there instead, and
            the backend's own capacity and eviction apply, so this setting
            has no effect. Must be a
            positive ``int`` or ``None``: another type raises ``TypeError``
            and zero or a negative value raises ``ValueError`` when the
            settings are created.
        max_component_depth: How many components deep a page may nest before
            rendering stops with ``RecursionError``. The default, ``2000``, is
            far deeper than real pages nest, so it only stops a component
            that keeps rendering itself, such as a tree node whose data lists
            the node among its own children. Without the limit that render
            would run until the process runs out of memory. The error names
            the chain of components, and ``<c-error-fallback>`` cannot catch
            it. Must be a positive ``int``: another type raises ``TypeError``
            and zero or less raises ``ValueError`` when the settings are
            created. A component rendered from a ``{{ ... }}`` expression or
            through ``<c-component>`` starts a new count. Python's own
            recursion limit stops that kind of recursion much earlier, with
            an ordinary ``RecursionError`` that ``<c-error-fallback>`` can
            catch, so avoid wrapping such a recursion in one.
        id_generator: A function returning the per-render id stamped on each
            component instance (``component.id``; static output also writes it
            into each component root's ``data-cid-<id>`` attribute). Given as
            a callable or a ``"path.to.func"`` import string;
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
    ssr: bool = True
    ssr_element_threshold: int = 0
    vue_asset_max_bytes: int | None = DEFAULT_VUE_ASSET_MAX_BYTES
    max_component_depth: int = DEFAULT_MAX_COMPONENT_DEPTH

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
        if type(self.ssr) is not bool:
            raise TypeError("Citry ssr must be a bool.")
        # An exact int check keeps True/False and floats from passing as a
        # count, and a negative count has no meaning as a page size.
        if type(self.ssr_element_threshold) is not int:
            raise TypeError(
                f"Citry ssr_element_threshold must be an int, got {type(self.ssr_element_threshold).__name__}."
            )
        if self.ssr_element_threshold < 0:
            raise ValueError(f"Citry ssr_element_threshold must be 0 or greater, got {self.ssr_element_threshold}.")
        # The limit is a byte count; an exact int check keeps True/False and
        # floats out, and a limit of zero would drop every file on arrival.
        if self.vue_asset_max_bytes is not None:
            if type(self.vue_asset_max_bytes) is not int:
                raise TypeError(
                    f"Citry vue_asset_max_bytes must be an int or None, got {type(self.vue_asset_max_bytes).__name__}."
                )
            if self.vue_asset_max_bytes <= 0:
                raise ValueError(f"Citry vue_asset_max_bytes must be greater than 0, got {self.vue_asset_max_bytes}.")
        # The renderer compares every component's depth with this number, so
        # it must be a real count: an exact int check keeps True/False and
        # floats out, and a limit below 1 means nothing, since the root
        # component alone is 1 deep.
        if type(self.max_component_depth) is not int:
            raise TypeError(
                f"Citry max_component_depth must be an int, got {type(self.max_component_depth).__name__}."
            )
        if self.max_component_depth < 1:
            raise ValueError(f"Citry max_component_depth must be 1 or greater, got {self.max_component_depth}.")

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
