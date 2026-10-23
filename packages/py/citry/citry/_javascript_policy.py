"""Call-local JavaScript delivery inventory and final-output validation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from citry import _output_policy
from citry._caller_warnings import warn_at_caller
from citry._csp_validation import _ASCII_LOWER
from citry._serialization_security import _is_executable
from citry.ext.dependencies.types import Dependency, Script, Style
from citry_core.html_transform import _classify_dependency_attribute, _is_javascript_url

if TYPE_CHECKING:
    from collections.abc import Iterable

    from citry.settings import SecurityJavascriptMode

# The bits of `_classify_dependency_attribute`'s answer.
_ACTIVATION_ATTRIBUTE = 1
_NATIVE_EVENT_ATTRIBUTE = 2
_JAVASCRIPT_URL_ATTRIBUTE = 4
_DependencyT = TypeVar("_DependencyT", bound="Dependency")


@dataclass(frozen=True, slots=True)
class _JavascriptFinding:
    """One reached, dependency, or settled-output JavaScript requirement."""

    rule: str
    detail: str
    component: str
    attribute: str | None = None
    range_kind: Literal["source", "pre-extension HTML", "settled HTML", "dependency"] = "dependency"
    start_index: int | None = None
    end_index: int | None = None
    origin: str | None = None

    def display(self) -> str:
        origin = f" ({self.origin})" if self.origin else ""
        attribute = f", attribute {self.attribute!r}" if self.attribute else ""
        position = "" if self.start_index is None else f", {self.range_kind} bytes {self.start_index}:{self.end_index}"
        return f"{self.component}{origin}{attribute}{position}: {self.detail}"


class _JavascriptPolicy:
    """Apply one serialization call's JavaScript delivery ceiling."""

    __slots__ = ("_findings", "_mode", "_pre_extension_raw", "_seen", "_site_counts")

    def __init__(self, mode: SecurityJavascriptMode) -> None:
        self._mode = mode
        self._findings: list[_JavascriptFinding] = []
        self._seen: set[tuple[object, ...]] = set()
        self._site_counts: dict[tuple[str, tuple[object, ...]], int] = {}
        # Each executable script seen before the hooks ran, by its source
        # bytes, with how many identical copies are still unmatched.
        self._pre_extension_raw: dict[bytes, int] = {}

    @property
    def mode(self) -> SecurityJavascriptMode:
        return self._mode

    def inspect_selected_requirements(self, requirements: frozenset[str]) -> None:
        """Record selected typed browser facts before whole-HTML hooks run."""
        details = {
            "events": "selected event, poll, or State control bindings require the Citry Events runtime",
            "vue_binding": "selected browser bindings require the Vue runtime",
            "js_data": "selected component js_data requires the Vue runtime",
            "component_js": "selected component JavaScript requires browser execution",
        }
        for requirement in sorted(requirements):
            detail = details.get(requirement)
            if detail is not None:
                self.add_requirement(detail, key=("selected-vue-requirement", requirement))

    def add_requirement(
        self,
        detail: str,
        *,
        component: str = "rendered subtree",
        rule: str = "managed-javascript",
        key: tuple[object, ...] | None = None,
    ) -> None:
        """Record a managed client requirement discovered outside final HTML."""
        if self._mode == "omit":
            return
        self._add(rule, detail, component, key=key)

    def process_dependencies(
        self,
        dependencies: Iterable[_DependencyT],
        *,
        position: str,
    ) -> list[_DependencyT]:
        """Inventory and, for restrictive modes, filter structured dependencies."""
        # The result holds the same kind it was given: a caller passing scripts gets
        # scripts back, so it can keep rendering them as scripts afterwards.
        retained: list[_DependencyT] = []
        for dependency in dependencies:
            emitted_dependency = dependency
            exact_style = type(dependency) is Style
            if exact_style:
                style = cast("Style", dependency)
                sanitized, active_attributes = _sanitize_structured_attributes(style)
                if active_attributes:
                    for attribute, detail in active_attributes:
                        if self._mode == "omit":
                            continue
                        self._add(
                            "executable-style-attribute",
                            f"{detail} on a Style in the {position} dependency list requires JavaScript",
                            style.origin_class_id or "dependency emission",
                            attribute=attribute,
                            key=("style-attribute", position, id(style), attribute),
                        )
                    if self._mode == "forbid":
                        continue
                    if self._mode == "omit":
                        if sanitized is None:
                            continue
                        emitted_dependency = cast("_DependencyT", sanitized)
                retained.append(emitted_dependency)
                continue
            exact_script = type(dependency) is Script
            script = cast("Script", dependency) if exact_script else None
            if script is not None:
                sanitized, active_attributes = _sanitize_structured_attributes(script)
                if active_attributes:
                    for attribute, detail in active_attributes:
                        if self._mode == "omit":
                            continue
                        self._add(
                            "executable-script-attribute",
                            f"{detail} on a Script in the {position} dependency list requires JavaScript",
                            script.origin_class_id or "dependency emission",
                            attribute=attribute,
                            key=("script-attribute", position, id(script), attribute),
                        )
                    if self._mode == "forbid":
                        continue
                    if self._mode == "omit":
                        if sanitized is None:
                            continue
                        emitted_dependency = cast("_DependencyT", sanitized)
                        script = cast("Script", emitted_dependency)
            executable, classification_error = (
                _script_executable_for_policy(script) if script is not None else (False, None)
            )
            reserved_manifest = script is not None and _is_reserved_manifest(script)
            opaque = not exact_script
            if executable or opaque:
                if self._mode != "omit":
                    origin = dependency.origin_class_id if isinstance(dependency, (Script, Style)) else None
                    kind = dependency.kind if isinstance(dependency, Dependency) else "extra"
                    detail = (
                        f"an opaque {type(dependency).__name__} in the {position} dependency list cannot be "
                        "proven JavaScript-free; return an exact Script or Style"
                        if opaque
                        else (
                            f"a {kind} Script in the {position} dependency list cannot be proven inert "
                            f"({classification_error})"
                            if classification_error is not None
                            else f"an executable {kind} Script in the {position} dependency list requires JavaScript"
                        )
                    )
                    self._add(
                        "opaque-dependency" if opaque else "executable-dependency",
                        detail,
                        origin or "dependency emission",
                        key=("dependency", position, id(dependency)),
                    )
                if self._mode in {"omit", "forbid"}:
                    continue
            if reserved_manifest and self._mode in {"omit", "forbid"}:
                manifest_script = cast("Script", script)
                if self._mode == "forbid":
                    self._add(
                        "managed-manifest",
                        f"a Citry browser manifest in the {position} dependency list requires the client manager",
                        manifest_script.origin_class_id or "dependency emission",
                        key=("managed-manifest", position, id(manifest_script)),
                    )
                continue
            retained.append(emitted_dependency)
        return retained

    def validate_settled_html(
        self,
        html: str,
        *,
        marker_prefix: str | None,
        trusted_tag_starts: frozenset[int],
        component_classes: dict[str, str],
        omit_handler_marker: str | None = None,
        check: _output_policy.OutputCheck | None = None,
    ) -> str:
        """
        Inventory active behavior after every string-level extension hook.

        Returns ``html`` with every ``omit_handler_marker`` attribute removed.
        A caller that already checked ``html`` with these options passes that
        ``check``, so the page is read once.
        """
        if check is None:
            check = _output_policy.check_output_html(
                html,
                javascript=self._mode,
                marker_prefix=marker_prefix,
                trusted_tag_starts=trusted_tag_starts,
                omit_handler_marker=omit_handler_marker,
            )
        check.require(html, pre_extension=False, csp=False, javascript=self._mode)
        if check.error is not None:
            if omit_handler_marker is not None and omit_handler_marker.lower() in html.lower():
                msg = "Citry omission handler metadata remained in unparseable settled HTML"
                raise ValueError(msg) from check.error
            self._add(
                "unparseable-output",
                f"settled HTML could not be parsed for JavaScript policy validation ({check.error})",
                "settled render output",
            )
            return html
        for event in check.events:
            if event[0] == "element":
                if event[1] == "script":
                    self._replay_settled_script(check, event, component_classes)
            elif event[0].startswith("js-"):
                self._replay_finding(event, component_classes)
        if omit_handler_marker is None:
            return html
        cleaned = html if check.cleaned_html is None else check.cleaned_html
        if omit_handler_marker.lower() in cleaned.lower():
            raise ValueError("Citry omission handler metadata escaped settled HTML cleanup")
        return cleaned

    def validate_pre_extension_html(
        self,
        html: str,
        *,
        component_classes: dict[str, str],
        check: _output_policy.OutputCheck | None = None,
    ) -> None:
        """Remember warning-mode raw scripts before identical dependencies are inserted."""
        if self._mode != "warn":
            return
        if check is None:
            check = _output_policy.check_output_html(html, pre_extension=True)
        check.require(html, pre_extension=True, csp=False, javascript=None)
        # The settled pass reports malformed output.
        if check.error is not None:
            return
        for event in check.events:
            _, tag, token_start, name_start, name_end, element_end, _, executable, _, cids = event
            if tag != "script" or not executable:
                continue
            instance = _output_policy.own_instance(cids, component_classes)
            component = component_classes.get(instance or "", "settled render output")
            fingerprint = check.element_bytes(token_start, element_end)
            self._pre_extension_raw[fingerprint] = self._pre_extension_raw.get(fingerprint, 0) + 1
            self._add(
                "raw-script",
                "a raw executable <script> remains outside Citry's dependency policy",
                component,
                range_kind="pre-extension HTML",
                start=name_start,
                end=name_end,
                key=("pre-raw-script", instance, token_start),
            )

    def report(self) -> None:
        """Emit one inventory warning or reject JavaScript-dependent output."""
        if not self._findings:
            return
        body = "\n".join(f"- {finding.display()}" for finding in self._findings)
        if self._mode == "forbid":
            raise ValueError(
                f"security_javascript='forbid' found {len(self._findings)} client behavior requirement(s):\n{body}"
            )
        # Point at the author's serialize call, wherever Citry noticed it.
        warn_at_caller(
            f"security_javascript={self._mode!r} found {len(self._findings)} client behavior requirement(s):\n{body}",
            RuntimeWarning,
        )

    def _replay_settled_script(
        self,
        check: _output_policy.OutputCheck,
        event: tuple[Any, ...],
        component_classes: dict[str, str],
    ) -> None:
        _, _, token_start, name_start, name_end, element_end, trusted, executable, has_manager, cids = event
        # An identical script seen before the hooks ran was reported then, so
        # one remembered copy is used up instead, even for a trusted tag.
        if self._pre_extension_raw:
            fingerprint = check.element_bytes(token_start, element_end)
            remembered = self._pre_extension_raw.get(fingerprint, 0)
            if remembered:
                self._pre_extension_raw[fingerprint] = remembered - 1
                return
        if trusted or not (executable or has_manager):
            return
        instance = _output_policy.own_instance(cids, component_classes)
        component = component_classes.get(instance or "", "settled render output")
        if executable:
            self._add(
                "raw-script",
                "a raw executable <script> remains outside Citry's dependency policy",
                component,
                start=name_start,
                end=name_end,
                key=self._site_key(instance, ("raw-script", token_start)),
            )
        else:
            self._add(
                "raw-manager-manifest",
                "a raw Citry browser manifest requires the client manager",
                component,
                start=name_start,
                end=name_end,
                key=self._site_key(instance, ("raw-manifest", token_start)),
            )

    def _replay_finding(self, event: tuple[Any, ...], component_classes: dict[str, str]) -> None:
        rule, tag, attribute, start, end, token_start, cids = event
        instance = _output_policy.own_instance(cids, component_classes)
        component = component_classes.get(instance or "", "settled render output")
        name = (attribute or "").translate(_ASCII_LOWER)
        if rule == "js-browser-attribute":
            finding = "browser-attribute"
            detail = f"the browser activation attribute {attribute!r} requires JavaScript"
            signature: tuple[object, ...] = ("activation", name, start)
        elif rule == "js-static-fallback":
            finding = "static-fallback"
            detail = (
                f"{attribute!r} is inert after Citry-managed JavaScript is omitted and may "
                "leave an unusable static fallback"
            )
            signature = ("fallback", name, start)
        elif rule == "js-native-handler":
            finding = "native-handler"
            detail = f"the native inline event attribute {attribute!r} remains executable browser code"
            signature = ("native", name, start)
        elif rule == "js-javascript-url":
            finding = "javascript-url"
            detail = f"a javascript: URL in {attribute!r} remains executable browser code"
            signature = ("javascript-url", tag, name, start)
        elif rule == "js-embedded-document":
            finding = "embedded-document"
            detail = f"{attribute!r} contains an embedded HTML document with executable browser code"
            signature = ("embedded-document", tag, name, start)
        else:
            finding = "handler-only-control"
            detail = "this control has a browser handler but no native navigation or submission fallback"
            signature = ("handler-only", tag, token_start)
        self._add(
            finding,
            detail,
            component,
            attribute=attribute,
            range_kind="settled HTML",
            start=start,
            end=end,
            key=self._site_key(instance, signature),
        )

    def _site_key(self, instance: str | None, signature: tuple[object, ...]) -> tuple[object, ...]:
        owner = instance or "settled render output"
        counter_key = (owner, signature)
        ordinal = self._site_counts.get(counter_key, 0)
        self._site_counts[counter_key] = ordinal + 1
        return (owner, *signature, ordinal)

    def _add(
        self,
        rule: str,
        detail: str,
        component: str,
        *,
        attribute: str | None = None,
        range_kind: Literal["source", "pre-extension HTML", "settled HTML", "dependency"] = "dependency",
        start: int | None = None,
        end: int | None = None,
        origin: str | None = None,
        key: tuple[object, ...] | None = None,
    ) -> None:
        identity = key or (rule, component, attribute, range_kind, start, end, detail)
        if identity in self._seen:
            return
        self._seen.add(identity)
        self._findings.append(
            _JavascriptFinding(
                rule=rule,
                detail=detail,
                component=component,
                attribute=attribute,
                range_kind=range_kind,
                start_index=start,
                end_index=end,
                origin=origin,
            )
        )


def _is_reserved_manifest(script: Script) -> bool:
    return any(
        isinstance(name, str) and name.translate(_ASCII_LOWER).startswith("data-citry") for name in script.attrs
    )


def _sanitize_structured_attributes(
    dependency: Script | Style,
) -> tuple[Script | Style | None, tuple[tuple[str, str], ...]]:
    """Remove active attrs from an exact inert dependency without dropping its content."""
    tag = "script" if isinstance(dependency, Script) else "link" if dependency.url is not None else "style"
    safe_attrs: dict[str, str | bool] = {}
    findings: list[tuple[str, str]] = []
    for authored_name, value in dependency.attrs.items():
        if not isinstance(authored_name, str):
            safe_attrs[authored_name] = value  # type: ignore[index]
            continue
        # A structured value is a Python string, not HTML, so it is read
        # without decoding character references.
        flags = _classify_dependency_attribute(tag, authored_name, value if isinstance(value, str) else None)
        detail: str | None = None
        if flags & _ACTIVATION_ATTRIBUTE:
            detail = "a browser activation attribute"
        elif flags & _NATIVE_EVENT_ATTRIBUTE:
            detail = "a native inline event attribute"
        elif flags & _JAVASCRIPT_URL_ATTRIBUTE:
            detail = "a javascript: URL"
        if detail is None:
            safe_attrs[authored_name] = value
        else:
            findings.append((authored_name, detail))
    if dependency.url is not None and _is_javascript_url(dependency.url):
        findings.append(("src" if isinstance(dependency, Script) else "href", "a javascript: URL"))
        return None, tuple(findings)
    if not findings:
        return dependency, ()
    return replace(dependency, attrs=safe_attrs), tuple(findings)


def _script_executable_for_policy(script: Script) -> tuple[bool, str | None]:
    try:
        return _is_executable(script.attrs), None
    except (TypeError, ValueError) as error:
        return True, str(error)


# Both validator classes exist now, so an opt-in comparison with the
# frozen Python rules can wrap them (see _output_policy).
_output_policy.install_differential_checks()

__all__ = ["_JavascriptPolicy"]
