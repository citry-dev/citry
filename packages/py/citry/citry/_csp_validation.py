"""Render-time validation for Citry's pinned Alpine CSP contract."""

from __future__ import annotations

import html as html_module
import re
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from citry._alpine_csp import ALPINE_CSP_COMPATIBILITY_VERSION, classify_alpine_csp
from citry._browser_expressions import (
    BrowserExpression,
    BrowserExpressionHost,
    BrowserExpressionTransform,
    _browser_attribute,
)
from citry.ownership import (
    AlpineHandlerClientBindingPayload,
    CitryDomEventClientBindingPayload,
    CitryPollClientBindingPayload,
    OwnershipState,
    PropsClientBindingPayload,
)
from citry_core.template_parser import HtmlAttr, TemplateElement, parse_template

if TYPE_CHECKING:
    from citry.citry_render import CitryRender
    from citry_core.template_parser import Template

_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
_ENTITY_RE = re.compile(r"&(?:#[xX][0-9A-Fa-f]+|#[0-9]+|[A-Za-z][A-Za-z0-9]+);?")
_JAVASCRIPT_URL_RE = re.compile(
    r"j[\t\n\r]*a[\t\n\r]*v[\t\n\r]*a[\t\n\r]*s[\t\n\r]*c[\t\n\r]*r[\t\n\r]*i[\t\n\r]*p[\t\n\r]*t[\t\n\r]*:",
    re.IGNORECASE,
)
_URL_ATTRIBUTES = frozenset({"action", "formaction", "href", "src", "xlink:href"})
_NATIVE_EVENT_ATTRIBUTES = frozenset(
    {
        "onabort",
        "onafterprint",
        "onanimationcancel",
        "onanimationend",
        "onanimationiteration",
        "onanimationstart",
        "onauxclick",
        "onbeforeinput",
        "onbeforematch",
        "onbeforeprint",
        "onbeforetoggle",
        "onbeforeunload",
        "onblur",
        "oncancel",
        "oncanplay",
        "oncanplaythrough",
        "onchange",
        "onclick",
        "onclose",
        "oncontextlost",
        "oncontextmenu",
        "oncontextrestored",
        "oncopy",
        "oncuechange",
        "oncut",
        "ondblclick",
        "ondrag",
        "ondragend",
        "ondragenter",
        "ondragleave",
        "ondragover",
        "ondragstart",
        "ondrop",
        "ondurationchange",
        "onemptied",
        "onended",
        "onerror",
        "onfocus",
        "onformdata",
        "ongotpointercapture",
        "onhashchange",
        "oninput",
        "oninvalid",
        "onkeydown",
        "onkeypress",
        "onkeyup",
        "onlanguagechange",
        "onload",
        "onloadeddata",
        "onloadedmetadata",
        "onloadstart",
        "onlostpointercapture",
        "onmessage",
        "onmessageerror",
        "onmousedown",
        "onmouseenter",
        "onmouseleave",
        "onmousemove",
        "onmouseout",
        "onmouseover",
        "onmouseup",
        "onoffline",
        "ononline",
        "onpagehide",
        "onpagereveal",
        "onpageshow",
        "onpageswap",
        "onpaste",
        "onpause",
        "onplay",
        "onplaying",
        "onpointercancel",
        "onpointerdown",
        "onpointerenter",
        "onpointerleave",
        "onpointermove",
        "onpointerout",
        "onpointerover",
        "onpointerrawupdate",
        "onpointerup",
        "onpopstate",
        "onprogress",
        "onratechange",
        "onrejectionhandled",
        "onreset",
        "onresize",
        "onscroll",
        "onscrollend",
        "onsecuritypolicyviolation",
        "onseeked",
        "onseeking",
        "onselect",
        "onslotchange",
        "onstalled",
        "onstorage",
        "onsubmit",
        "onsuspend",
        "ontimeupdate",
        "ontoggle",
        "ontouchcancel",
        "ontouchend",
        "ontouchmove",
        "ontouchstart",
        "ontransitioncancel",
        "ontransitionend",
        "ontransitionrun",
        "ontransitionstart",
        "onunhandledrejection",
        "onunload",
        "onvolumechange",
        "onwaiting",
        "onwheel",
    }
)
_SVG_NATIVE_EVENT_ATTRIBUTES = frozenset({"onactivate", "onbegin", "onend", "onrepeat"})


@dataclass(frozen=True, slots=True)
class _CspRenderFinding:
    """One deduplicated problem found in reached or settled render output."""

    detail: str
    component: str
    attribute: str | None
    range_kind: Literal["source", "pre-extension HTML", "settled HTML"]
    origin: str | None = None
    start_index: int | None = None
    end_index: int | None = None

    def display(self) -> str:
        source = f" ({self.origin})" if self.origin else ""
        attribute = f", attribute {self.attribute!r}" if self.attribute is not None else ""
        position = "" if self.start_index is None else f", {self.range_kind} bytes {self.start_index}:{self.end_index}"
        return f"{self.component}{source}{attribute}{position}: {self.detail}"


class _CspRenderValidator:
    """Collect CSP findings, then warn or fail once the render has settled."""

    __slots__ = ("_check_alpine", "_findings", "_mode", "_pre_extension_raw", "_seen", "_site_counts")

    def __init__(self, mode: str, *, check_alpine: bool = True) -> None:
        self._mode = mode
        self._check_alpine = check_alpine
        self._findings: list[_CspRenderFinding] = []
        self._seen: set[tuple[object, ...]] = set()
        self._site_counts: dict[tuple[str, tuple[object, ...]], int] = {}
        self._pre_extension_raw: dict[tuple[str, str], int] = {}

    def validate_reached_bindings(self, root: CitryRender) -> None:
        """Check active component-boundary expressions that do not remain as HTML attrs."""
        if not self._check_alpine:
            return
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
                location = locations.get(binding.source_location_id)
                if location is None:
                    continue
                payload = binding.payload
                if isinstance(payload, PropsClientBindingPayload):
                    source = payload.expression
                    host: BrowserExpressionHost = "citry-props"
                    transform: BrowserExpressionTransform = "identity"
                elif isinstance(payload, AlpineHandlerClientBindingPayload):
                    source = payload.expression
                    host = "alpine"
                    transform = "identity"
                elif isinstance(payload, (CitryDomEventClientBindingPayload, CitryPollClientBindingPayload)):
                    if payload.args is None:
                        continue
                    source = payload.args
                    host = "citry-event-args"
                    transform = "citry-args"
                else:
                    continue
                source_start, source_end = _located_source_range(location.source, location.span, source)
                key_start, key_end = _located_source_range(location.source, location.span, binding.key)
                expression = BrowserExpression(
                    source=source,
                    start_index=source_start,
                    end_index=source_end,
                    mode="statement" if isinstance(payload, AlpineHandlerClientBindingPayload) else "expression",
                    attribute=binding.key,
                    element=invocation.authored_tag.translate(_ASCII_LOWER),
                    host=host,
                    evaluator="raw",
                    transform=transform,
                    attribute_start_index=key_start,
                    attribute_end_index=key_end,
                )
                result = classify_alpine_csp(expression)
                if result.outcome == "incompatible":
                    self._add(
                        _compatibility_detail(result.detail),
                        class_names.get(invocation.source_render_id, location.owner_class_id),
                        result.start_index,
                        result.end_index,
                        attribute=binding.key,
                        range_kind="source",
                        origin=location.origin,
                        dedupe_key=(
                            location.owner_class_id,
                            binding.key,
                            location.byte_span,
                            result.detail,
                        ),
                    )

    def validate_settled_html(
        self,
        html: str,
        *,
        marker_prefix: str,
        trusted_tag_starts: frozenset[int],
        component_classes: dict[str, str],
    ) -> None:
        """Check the final hook output while structured dependency markers still exist."""
        try:
            template = parse_template(html)
        except Exception as error:  # noqa: BLE001 - strict mode must fail closed on ambiguous output
            self._add(
                f"the settled HTML could not be parsed for CSP validation ({error})",
                "settled render output",
                None,
                None,
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
        )

    def validate_pre_extension_html(self, html: str, *, component_classes: dict[str, str]) -> None:
        """Remember raw active tags before dependency emission can create identical markup."""
        if self._mode != "warn":
            return
        try:
            template = parse_template(html)
        except Exception:  # noqa: BLE001 - the final strict/warn pass reports malformed settled output
            return
        self._walk_pre_extension_raw(
            html,
            template,
            component_classes,
            inherited_component=None,
            inherited_instance=None,
        )

    def add_dependency_findings(self, findings: tuple[str, ...]) -> None:
        """Include migration warnings discovered while dependency descriptors were built."""
        for finding in findings:
            self._add(finding, "dependency emission", None, None)

    def report(self) -> None:
        """Emit one warning in migration mode or reject the strict render."""
        if not self._findings:
            return
        body = "\n".join(f"- {finding.display()}" for finding in self._findings)
        message = (
            f"Citry found {len(self._findings)} strict-CSP incompatibility issue(s) for Alpine "
            f"{ALPINE_CSP_COMPATIBILITY_VERSION}:\n{body}"
        )
        if self._mode == "warn":
            warnings.warn(message, RuntimeWarning, stacklevel=4)
            return
        raise ValueError(message)

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
            if tag in {"script", "style"} and not trusted:
                fingerprint = (tag, _node_html(html, node))
                remembered = self._pre_extension_raw.get(fingerprint, 0)
                if remembered:
                    self._pre_extension_raw[fingerprint] = remembered - 1
                else:
                    self._add_raw_tag(
                        tag, component, own_instance, node.start_tag.name.start_index, node.start_tag.name.end_index
                    )
            for attr in attrs:
                self._validate_attribute(tag, attr, component, own_instance)
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
            if tag in {"script", "style"}:
                fingerprint = (tag, _node_html(html, node))
                self._pre_extension_raw[fingerprint] = self._pre_extension_raw.get(fingerprint, 0) + 1
                self._add_raw_tag(
                    tag,
                    component,
                    own_instance,
                    node.start_tag.name.start_index,
                    node.start_tag.name.end_index,
                    range_kind="pre-extension HTML",
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

    def _add_raw_tag(
        self,
        tag: str,
        component: str,
        instance: str | None,
        start: int,
        end: int,
        *,
        range_kind: Literal["pre-extension HTML", "settled HTML"] = "settled HTML",
    ) -> None:
        self._add(
            f"a raw <{tag}> element; use Component.{'js' if tag == 'script' else 'css'} or a structured "
            f"{'Script' if tag == 'script' else 'Style'} dependency",
            component,
            start,
            end,
            range_kind=range_kind,
            dedupe_key=self._site_key(instance, (component, "raw-tag", tag)),
        )

    def _validate_attribute(self, tag: str, attr: HtmlAttr, component: str, instance: str | None) -> None:
        name = attr.key.content.translate(_ASCII_LOWER)
        inner = attr.inner_value
        raw_source = "" if inner is None else inner.content
        value_start = attr.key.end_index if inner is None else inner.start_index
        decoded, raw_spans = _decode_html_attribute(raw_source)
        if _is_native_event_attribute(name):
            self._add(
                f"the native inline event attribute {attr.key.content!r}; use an Alpine handler or Component.js",
                component,
                attr.key.start_index,
                attr.key.end_index,
                attribute=attr.key.content,
                dedupe_key=self._site_key(instance, (component, "native-event", name, decoded)),
            )
        if _is_url_attribute(tag, name) and _javascript_url(decoded):
            self._add(
                f"a javascript: URL in {attr.key.content!r}; use a normal URL or an Alpine handler",
                component,
                value_start,
                value_start + len(raw_source.encode()),
                attribute=attr.key.content,
                dedupe_key=self._site_key(instance, (component, "javascript-url", tag, name, decoded)),
            )
        if not self._check_alpine:
            return
        classified = _browser_attribute(name, decoded, citry_attribute=attr.key.content)
        if classified is None:
            return
        mode, relative_start, relative_end = classified
        expression_source = decoded[relative_start:relative_end]
        value_prefix = len(decoded[:relative_start].encode())
        attr_sentinel = len(expression_source.encode()) + 1
        base_name = name.split(".", 1)[0]
        transform: BrowserExpressionTransform = "citry-args" if attr.key.content.startswith("@c-") else "identity"
        host: BrowserExpressionHost = "citry-event-args" if transform == "citry-args" else "alpine"
        if base_name in {"x-model", "x-modelable"}:
            transform = "x-model"
        elif base_name == "x-for":
            transform = "x-for"
        expression = BrowserExpression(
            source=expression_source,
            start_index=0,
            end_index=len(expression_source.encode()),
            mode=mode,
            attribute=attr.key.content,
            element=tag,
            host=host,
            evaluator="normal",
            transform=transform,
            attribute_start_index=attr_sentinel,
            attribute_end_index=attr_sentinel + len(attr.key.content.encode()),
        )
        result = classify_alpine_csp(expression)
        if result.outcome != "incompatible":
            return
        if result.start_index >= attr_sentinel:
            start = attr.key.start_index
            end = attr.key.end_index
        else:
            decoded_start = value_prefix + result.start_index
            decoded_end = value_prefix + result.end_index
            raw_start, raw_end = _decoded_byte_range_to_raw(decoded, raw_spans, decoded_start, decoded_end)
            start = value_start + raw_start
            end = value_start + raw_end
        detail = _compatibility_detail(result.detail)
        self._add(
            detail,
            component,
            start,
            end,
            attribute=attr.key.content,
            dedupe_key=self._site_key(instance, (component, "alpine", tag, name, decoded, detail)),
        )

    def _site_key(self, instance: str | None, signature: tuple[object, ...]) -> tuple[object, ...]:
        owner = instance or "settled render output"
        counter_key = (owner, signature)
        ordinal = self._site_counts.get(counter_key, 0)
        self._site_counts[counter_key] = ordinal + 1
        return (owner, *signature, ordinal)

    def _add(
        self,
        detail: str,
        component: str,
        start: int | None,
        end: int | None,
        *,
        attribute: str | None = None,
        range_kind: Literal["source", "pre-extension HTML", "settled HTML"] = "settled HTML",
        origin: str | None = None,
        dedupe_key: tuple[object, ...] | None = None,
    ) -> None:
        key = dedupe_key or (detail, component, attribute, range_kind, start, end)
        if key in self._seen:
            return
        self._seen.add(key)
        self._findings.append(
            _CspRenderFinding(
                detail=detail,
                component=component,
                attribute=attribute,
                range_kind=range_kind,
                origin=origin,
                start_index=start,
                end_index=end,
            )
        )


def _located_source_range(source: str, span: tuple[int, int], needle: str) -> tuple[int, int]:
    snippet = source[span[0] : span[1]]
    relative = snippet.find(needle)
    start_char = span[0] if relative < 0 else span[0] + relative
    end_char = span[1] if relative < 0 else start_char + len(needle)
    return len(source[:start_char].encode()), len(source[:end_char].encode())


def _node_html(html: str, node: Any) -> str:
    end_tag = getattr(node, "end_tag", None)
    end = node.start_tag.token.end_index if end_tag is None else end_tag.token.end_index
    raw = html.encode()
    return raw[node.start_tag.token.start_index : end].decode()


def _compatibility_detail(detail: str | None) -> str:
    subject = detail or "this browser expression"
    return (
        f"Alpine CSP {ALPINE_CSP_COMPATIBILITY_VERSION} cannot evaluate {subject} here; "
        "move complex logic to Component.js and call a scope method"
    )


def _decode_html_attribute(source: str) -> tuple[str, tuple[tuple[int, int], ...]]:
    """Decode HTML references and map each decoded character to its raw byte span."""
    decoded: list[str] = []
    raw_spans: list[tuple[int, int]] = []
    raw_bytes = 0
    position = 0
    while position < len(source):
        match = _ENTITY_RE.match(source, position)
        raw = match.group(0) if match is not None else source[position]
        value = html_module.unescape(raw)
        if value == raw and match is not None:
            raw = source[position]
            value = raw
        raw_start = raw_bytes
        raw_bytes += len(raw.encode())
        for char in value:
            decoded.append(char)
            raw_spans.append((raw_start, raw_bytes))
        position += len(raw)
    return "".join(decoded), tuple(raw_spans)


def _decoded_byte_to_char_index(decoded: str, byte_offset: int) -> int:
    safe = max(0, min(len(decoded.encode()), byte_offset))
    prefix = decoded.encode()[:safe]
    while True:
        try:
            return len(prefix.decode())
        except UnicodeDecodeError:
            prefix = prefix[:-1]


def _decoded_byte_range_to_raw(
    decoded: str,
    raw_spans: tuple[tuple[int, int], ...],
    start: int,
    end: int,
) -> tuple[int, int]:
    start_char = _decoded_byte_to_char_index(decoded, start)
    end_char = _decoded_byte_to_char_index(decoded, end)
    if start_char < end_char and raw_spans:
        return raw_spans[start_char][0], raw_spans[end_char - 1][1]
    if start_char < len(raw_spans):
        return raw_spans[start_char][0], raw_spans[start_char][0]
    boundary = raw_spans[-1][1] if raw_spans else 0
    return boundary, boundary


def _javascript_url(value: str) -> bool:
    normalized = value.lstrip(
        "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
        "\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f "
    )
    return _JAVASCRIPT_URL_RE.match(normalized) is not None


def _is_native_event_attribute(name: str) -> bool:
    return len(name) > 2 and name.startswith("on")


def _is_url_attribute(tag: str, name: str) -> bool:
    return name in _URL_ATTRIBUTES or (tag == "object" and name == "data")


__all__ = ["_CspRenderValidator"]
