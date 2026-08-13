"""Call-local JavaScript delivery inventory and final-output validation."""

from __future__ import annotations

import warnings
from base64 import b64decode
from binascii import Error as BinasciiError
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Literal, cast
from urllib.parse import unquote_to_bytes

from citry._csp_validation import (
    _ASCII_LOWER,
    _decode_html_attribute,
    _is_native_event_attribute,
    _is_url_attribute,
    _javascript_url,
    _node_html,
)
from citry._serialization_security import _is_executable
from citry.ext.dependencies.types import Dependency, Script, Style
from citry.ownership import (
    AlpineHandlerClientBindingPayload,
    CitryDomEventClientBindingPayload,
    CitryPollClientBindingPayload,
    OwnershipState,
    PropsClientBindingPayload,
)
from citry_core.template_parser import HtmlAttr, TemplateElement, parse_template

if TYPE_CHECKING:
    from collections.abc import Iterable

    from citry.citry_render import CitryRender
    from citry.settings import SecurityJavascriptMode
    from citry_core.template_parser import Template

_EVENTS_ATTRIBUTES = frozenset({"data-cev-bind", "data-cev-on", "data-cev-poll"})
_LEADING_URL_SPACE = "".join(chr(codepoint) for codepoint in range(0x21))


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
        self._pre_extension_raw: dict[str, int] = {}

    @property
    def mode(self) -> SecurityJavascriptMode:
        return self._mode

    def inspect_reached_bindings(self, root: CitryRender) -> None:
        """Inventory active component-boundary bindings absent from settled attrs."""
        graph = root.context.ownership
        if graph is None:
            return
        snapshot = graph.snapshot()
        locations = {location.id: location for location in snapshot.source_locations}
        class_names = {instance.render_id: instance.class_name for instance in snapshot.logical_instances}
        for invocation in snapshot.component_invocations:
            if invocation.state != OwnershipState.ACTIVE:
                continue
            for binding in invocation.client_bindings:
                payload = binding.payload
                if not isinstance(
                    payload,
                    (
                        PropsClientBindingPayload,
                        AlpineHandlerClientBindingPayload,
                        CitryDomEventClientBindingPayload,
                        CitryPollClientBindingPayload,
                    ),
                ):
                    continue
                location = locations.get(binding.source_location_id)
                component = class_names.get(
                    invocation.source_render_id,
                    location.owner_class_id if location is not None else invocation.authored_tag,
                )
                detail = (
                    "an active component props binding requires the Citry browser manager"
                    if isinstance(payload, PropsClientBindingPayload)
                    else "an active component browser handler requires JavaScript"
                )
                start = None if location is None else location.byte_span[0]
                end = None if location is None else location.byte_span[1]
                self._add(
                    "component-binding",
                    detail,
                    component,
                    attribute=binding.key,
                    range_kind="source",
                    start=start,
                    end=end,
                    origin=None if location is None else location.origin,
                    key=("binding", binding.source_location_id, binding.key, type(payload).__name__),
                )

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
        dependencies: Iterable[Dependency],
        *,
        position: str,
    ) -> list[Dependency]:
        """Inventory and, for restrictive modes, filter structured dependencies."""
        retained: list[Dependency] = []
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
                        emitted_dependency = sanitized
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
                        emitted_dependency = sanitized
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
        marker_prefix: str,
        trusted_tag_starts: frozenset[int],
        component_classes: dict[str, str],
    ) -> None:
        """Inventory active behavior after every string-level extension hook."""
        try:
            template = parse_template(html)
        except Exception as error:  # noqa: BLE001 - forbid must fail closed
            self._add(
                "unparseable-output",
                f"settled HTML could not be parsed for JavaScript policy validation ({error})",
                "settled render output",
            )
            return
        self._walk_template(
            html,
            template,
            marker_prefix,
            trusted_tag_starts,
            component_classes,
            inherited_component=None,
            inherited_instance=None,
            inherited_inside_form=False,
        )

    def validate_pre_extension_html(self, html: str, *, component_classes: dict[str, str]) -> None:
        """Remember warning-mode raw scripts before identical dependencies are inserted."""
        if self._mode != "warn":
            return
        try:
            template = parse_template(html)
        except Exception:  # noqa: BLE001 - the settled pass reports malformed output
            return
        self._walk_pre_extension_raw(
            html,
            template,
            component_classes,
            inherited_component=None,
            inherited_instance=None,
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
        warnings.warn(
            f"security_javascript={self._mode!r} found {len(self._findings)} client behavior requirement(s):\n{body}",
            RuntimeWarning,
            stacklevel=4,
        )

    def _walk_template(
        self,
        html: str,
        template: Template,
        marker_prefix: str,
        trusted_tag_starts: frozenset[int],
        component_classes: dict[str, str],
        *,
        inherited_component: str | None,
        inherited_instance: str | None,
        inherited_inside_form: bool,
    ) -> None:
        for element in template.elements:
            if not isinstance(element, TemplateElement.Node):
                continue
            node = element._0
            attrs = tuple(node.start_tag.attrs)
            tag = node.start_tag.name.content.translate(_ASCII_LOWER)
            own_instance = next(
                (
                    name[len("data-cid-") :]
                    for attr in attrs
                    if (name := attr.key.content.translate(_ASCII_LOWER)).startswith("data-cid-")
                    and name[len("data-cid-") :] in component_classes
                ),
                inherited_instance,
            )
            component = component_classes.get(own_instance or "", inherited_component or "settled render output")
            trusted = node.start_tag.token.start_index in trusted_tag_starts or any(
                attr.key.content.translate(_ASCII_LOWER).startswith(marker_prefix) for attr in attrs
            )
            attr_map = _attribute_map(attrs)
            if tag == "script":
                fingerprint = _node_html(html, node)
                remembered = self._pre_extension_raw.get(fingerprint, 0)
                if remembered:
                    self._pre_extension_raw[fingerprint] = remembered - 1
                elif not trusted and _raw_script_is_executable(attrs):
                    self._add(
                        "raw-script",
                        "a raw executable <script> remains outside Citry's dependency policy",
                        component,
                        start=node.start_tag.name.start_index,
                        end=node.start_tag.name.end_index,
                        key=self._site_key(own_instance, ("raw-script", node.start_tag.token.start_index)),
                    )
                elif not trusted and any(name.startswith("data-citry") for name in attr_map):
                    self._add(
                        "raw-manager-manifest",
                        "a raw Citry browser manifest requires the client manager",
                        component,
                        start=node.start_tag.name.start_index,
                        end=node.start_tag.name.end_index,
                        key=self._site_key(own_instance, ("raw-manifest", node.start_tag.token.start_index)),
                    )

            activation_attrs: list[str] = []
            for attr in attrs:
                name = attr.key.content.translate(_ASCII_LOWER)
                decoded = _decoded_attr(attr)
                if _is_activation_attribute(name):
                    activation_attrs.append(name)
                    if self._mode in {"warn", "forbid"}:
                        self._add(
                            "browser-attribute",
                            f"the browser activation attribute {attr.key.content!r} requires JavaScript",
                            component,
                            attribute=attr.key.content,
                            range_kind="settled HTML",
                            start=attr.key.start_index,
                            end=attr.key.end_index,
                            key=self._site_key(own_instance, ("activation", name, attr.key.start_index)),
                        )
                    elif self._mode == "omit" and _is_omit_hazard(name, node, html, attr_map):
                        self._add(
                            "static-fallback",
                            f"{attr.key.content!r} is inert after Citry-managed JavaScript is omitted and may "
                            "leave an unusable static fallback",
                            component,
                            attribute=attr.key.content,
                            range_kind="settled HTML",
                            start=attr.key.start_index,
                            end=attr.key.end_index,
                            key=self._site_key(own_instance, ("fallback", name, attr.key.start_index)),
                        )
                if _is_native_event_attribute(name):
                    self._add(
                        "native-handler",
                        f"the native inline event attribute {attr.key.content!r} remains executable browser code",
                        component,
                        attribute=attr.key.content,
                        range_kind="settled HTML",
                        start=attr.key.start_index,
                        end=attr.key.end_index,
                        key=self._site_key(own_instance, ("native", name, attr.key.start_index)),
                    )
                if _is_url_attribute(tag, name) and _javascript_url(decoded):
                    inner = attr.inner_value
                    start = attr.key.end_index if inner is None else inner.start_index
                    self._add(
                        "javascript-url",
                        f"a javascript: URL in {attr.key.content!r} remains executable browser code",
                        component,
                        attribute=attr.key.content,
                        range_kind="settled HTML",
                        start=start,
                        end=start + len(("" if inner is None else inner.content).encode()),
                        key=self._site_key(own_instance, ("javascript-url", tag, name, start)),
                    )
                if _embedded_document_requires_javascript(tag, name, decoded):
                    inner = attr.inner_value
                    start = attr.key.end_index if inner is None else inner.start_index
                    self._add(
                        "embedded-document",
                        f"{attr.key.content!r} contains an embedded HTML document with executable browser code",
                        component,
                        attribute=attr.key.content,
                        range_kind="settled HTML",
                        start=start,
                        end=start + len(("" if inner is None else inner.content).encode()),
                        key=self._site_key(own_instance, ("embedded-document", tag, name, start)),
                    )

            if (
                self._mode == "omit"
                and activation_attrs
                and _handler_only_control(
                    tag,
                    attr_map,
                    activation_attrs,
                    inside_form=inherited_inside_form,
                )
            ):
                self._add(
                    "handler-only-control",
                    "this control has a browser handler but no native navigation or submission fallback",
                    component,
                    range_kind="settled HTML",
                    start=node.start_tag.name.start_index,
                    end=node.start_tag.name.end_index,
                    key=self._site_key(own_instance, ("handler-only", tag, node.start_tag.token.start_index)),
                )
            body = getattr(node, "body", None)
            if body is not None:
                self._walk_template(
                    html,
                    body,
                    marker_prefix,
                    trusted_tag_starts,
                    component_classes,
                    inherited_component=component,
                    inherited_instance=own_instance,
                    inherited_inside_form=inherited_inside_form or tag == "form",
                )

    def _walk_pre_extension_raw(
        self,
        html: str,
        template: Template,
        component_classes: dict[str, str],
        *,
        inherited_component: str | None,
        inherited_instance: str | None,
    ) -> None:
        for element in template.elements:
            if not isinstance(element, TemplateElement.Node):
                continue
            node = element._0
            attrs = tuple(node.start_tag.attrs)
            own_instance = next(
                (
                    name[len("data-cid-") :]
                    for attr in attrs
                    if (name := attr.key.content.translate(_ASCII_LOWER)).startswith("data-cid-")
                    and name[len("data-cid-") :] in component_classes
                ),
                inherited_instance,
            )
            component = component_classes.get(own_instance or "", inherited_component or "settled render output")
            if node.start_tag.name.content.translate(_ASCII_LOWER) == "script" and _raw_script_is_executable(attrs):
                fingerprint = _node_html(html, node)
                self._pre_extension_raw[fingerprint] = self._pre_extension_raw.get(fingerprint, 0) + 1
                self._add(
                    "raw-script",
                    "a raw executable <script> remains outside Citry's dependency policy",
                    component,
                    range_kind="pre-extension HTML",
                    start=node.start_tag.name.start_index,
                    end=node.start_tag.name.end_index,
                    key=("pre-raw-script", own_instance, node.start_tag.token.start_index),
                )
            body = getattr(node, "body", None)
            if body is not None:
                self._walk_pre_extension_raw(
                    html,
                    body,
                    component_classes,
                    inherited_component=component,
                    inherited_instance=own_instance,
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


def _attribute_map(attrs: tuple[HtmlAttr, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for attr in attrs:
        name = attr.key.content.translate(_ASCII_LOWER)
        result.setdefault(name, _decoded_attr(attr))
    return result


def _decoded_attr(attr: HtmlAttr) -> str:
    inner = attr.inner_value
    return _decode_html_attribute("" if inner is None else inner.content)[0]


def _raw_script_is_executable(attrs: tuple[HtmlAttr, ...]) -> bool:
    type_attrs = [attr for attr in attrs if attr.key.content.translate(_ASCII_LOWER) == "type"]
    if len(type_attrs) > 1:
        return True
    if not type_attrs:
        return True
    attr = type_attrs[0]
    value: str | bool = True if attr.inner_value is None else _decoded_attr(attr)
    return _is_executable({"type": value})


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
        name = authored_name.translate(_ASCII_LOWER)
        detail: str | None = None
        if _is_activation_attribute(name):
            detail = "a browser activation attribute"
        elif _is_native_event_attribute(name):
            detail = "a native inline event attribute"
        elif isinstance(value, str) and _is_url_attribute(tag, name) and _javascript_url(value):
            detail = "a javascript: URL"
        if detail is None:
            safe_attrs[authored_name] = value
        else:
            findings.append((authored_name, detail))
    if dependency.url is not None and _javascript_url(dependency.url):
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


def _is_activation_attribute(name: str) -> bool:
    return name.startswith(("x-", "@", ":")) or name in _EVENTS_ATTRIBUTES


def _is_omit_hazard(name: str, node: Any, html: str, attrs: dict[str, str]) -> bool:
    base = name.split(".", 1)[0]
    if base in {"x-cloak", "x-for", "x-if", "x-teleport"}:
        return True
    if base in {"x-text", "x-html"}:
        end_tag = getattr(node, "end_tag", None)
        if end_tag is None:
            return True
        raw = html.encode()
        content = raw[node.start_tag.token.end_index : end_tag.token.start_index].decode()
        return not content.strip()
    if base == "x-show":
        style = attrs.get("style", "").replace(" ", "").translate(_ASCII_LOWER)
        return "hidden" in attrs or "display:none" in style
    bound = base[1:] if base.startswith(":") else base.removeprefix("x-bind:")
    if bound == "hidden":
        return "hidden" in attrs
    if bound in {"href", "action", "formaction", "src", "value"}:
        return not attrs.get(bound)
    return False


def _handler_only_control(
    tag: str,
    attrs: dict[str, str],
    activation_attrs: list[str],
    *,
    inside_form: bool,
) -> bool:
    has_handler = any(
        name.startswith(("@", "x-on:")) or name in {"data-cev-on", "data-cev-poll"} for name in activation_attrs
    )
    if not has_handler:
        return False
    if tag == "a":
        return not attrs.get("href")
    if tag == "button":
        button_type = attrs.get("type", "submit").translate(_ASCII_LOWER)
        return button_type == "button" or (button_type == "submit" and not inside_form and not attrs.get("form"))
    if tag == "input":
        input_type = attrs.get("type", "text").translate(_ASCII_LOWER)
        return input_type in {"button", "reset"} or (not inside_form and not attrs.get("form"))
    if tag in {"select", "textarea"}:
        return not inside_form and not attrs.get("form")
    return tag in {"div", "span", "section"}


def _embedded_document_requires_javascript(tag: str, name: str, value: str) -> bool:
    if tag == "iframe" and name == "srcdoc":
        return _html_document_requires_javascript(value, depth=0)
    if (tag, name) not in {("iframe", "src"), ("object", "data"), ("embed", "src")}:
        return False
    decoded = _decode_html_data_url(value)
    return decoded is not None and _html_document_requires_javascript(decoded, depth=0)


def _decode_html_data_url(value: str) -> str | None:
    header, separator, payload = value.lstrip(_LEADING_URL_SPACE).partition(",")
    folded_header = header.translate(_ASCII_LOWER)
    media_type = folded_header.removeprefix("data:").partition(";")[0].strip(" \t\n\r\f")
    if not separator or not folded_header.startswith("data:") or media_type != "text/html":
        return None
    try:
        body = (
            b64decode(unquote_to_bytes(payload), validate=True)
            if ";base64" in folded_header
            else unquote_to_bytes(payload)
        )
        return body.decode("utf8", errors="replace")
    except (BinasciiError, ValueError, TypeError):
        return "<script>"


def _html_document_requires_javascript(html: str, *, depth: int) -> bool:
    if depth >= 4:
        return True
    try:
        template = parse_template(html)
    except Exception:  # noqa: BLE001 - ambiguous embedded markup fails closed
        return True
    return _parsed_document_requires_javascript(template, depth=depth)


def _parsed_document_requires_javascript(template: Template, *, depth: int) -> bool:
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        attrs = tuple(node.start_tag.attrs)
        tag = node.start_tag.name.content.translate(_ASCII_LOWER)
        if tag == "script" and _raw_script_is_executable(attrs):
            return True
        for attr in attrs:
            name = attr.key.content.translate(_ASCII_LOWER)
            value = _decoded_attr(attr)
            if _is_native_event_attribute(name) or (_is_url_attribute(tag, name) and _javascript_url(value)):
                return True
            if tag == "iframe" and name == "srcdoc" and _html_document_requires_javascript(value, depth=depth + 1):
                return True
            if (tag, name) in {("iframe", "src"), ("object", "data"), ("embed", "src")}:
                decoded = _decode_html_data_url(value)
                if decoded is not None and _html_document_requires_javascript(decoded, depth=depth + 1):
                    return True
        body = getattr(node, "body", None)
        if body is not None and _parsed_document_requires_javascript(body, depth=depth):
            return True
    return False


__all__ = ["_JavascriptPolicy"]
