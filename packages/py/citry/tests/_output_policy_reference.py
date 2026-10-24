"""
A frozen Python copy of Citry's strict-CSP and JavaScript-policy output rules.

Rust runs these rules for `serialize()` (`citry/_output_policy.py`). This
copy keeps the Python version they replaced, so a test can compare the two
on the same input: `test_output_policy_differential.py` on generated pages,
and, with `CITRY_OUTPUT_POLICY_DIFFERENTIAL=1`, every check that any test
suite runs. Both comparisons go through `outcomes_match`, which allows only the
two differences that reading the browser's tree makes on purpose. It
reads tags with the Python wrapper of the same Rust tokenizer, because
only the rules moved, and it keeps its own copy of every helper the rules
use, so the comparison never checks Rust against itself.

Do not edit this copy to match a Rust bug. When a rule changes on
purpose, change both copies the same way, or delete this copy and its
comparison test.
"""

from __future__ import annotations

import dataclasses
import html as html_module
import re
import traceback
from base64 import b64decode
from binascii import Error as BinasciiError
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import unquote_to_bytes

from citry import _output_policy
from citry._csp_validation import _CspRenderValidator
from citry._javascript_policy import _JavascriptPolicy
from citry._output_html import OutputAttr, OutputTemplate, scan_output_html

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from citry.settings import SecurityCspMode

_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
_ENTITY_RE = re.compile(r"&(?:#[xX][0-9A-Fa-f]+|#[0-9]+|[A-Za-z][A-Za-z0-9]+);?")
_JAVASCRIPT_URL_RE = re.compile(
    r"j[\t\n\r]*a[\t\n\r]*v[\t\n\r]*a[\t\n\r]*s[\t\n\r]*c[\t\n\r]*r[\t\n\r]*i[\t\n\r]*p[\t\n\r]*t[\t\n\r]*:",
    re.IGNORECASE,
)
_URL_ATTRIBUTES = frozenset({"action", "formaction", "href", "src", "xlink:href"})
# A decimal reference this short converts to an int directly: `&#` plus
# twelve digits plus `;`.
_MAX_PLAIN_DECIMAL_REFERENCE = 15
_LEADING_URL_SPACE = "".join(chr(codepoint) for codepoint in range(0x21))
# Whole groups of four, then at most one group that ends in the padding its
# length needs. Python 3.12 and later accept exactly this with
# `b64decode(validate=True)`.
_STRICT_BASE64_RE = re.compile(rb"(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?")

_JAVASCRIPT_MIME_TYPES = frozenset(
    {
        "text/javascript",
        "application/javascript",
        "application/ecmascript",
        "application/x-ecmascript",
        "application/x-javascript",
        "text/ecmascript",
        "text/javascript1.0",
        "text/javascript1.1",
        "text/javascript1.2",
        "text/javascript1.3",
        "text/javascript1.4",
        "text/javascript1.5",
        "text/jscript",
        "text/livescript",
        "text/x-ecmascript",
        "text/x-javascript",
    }
)


class ReferenceCspValidator(_CspRenderValidator):
    """The CSP validator with its Python rules."""

    __slots__ = ()

    def validate_settled_html(
        self,
        html: str,
        *,
        marker_prefix: str | None,
        trusted_tag_starts: frozenset[int],
        component_classes: dict[str, str],
    ) -> None:
        """
        Check the final hook output while structured dependency markers still exist.

        A tag is trusted when it starts at one of ``trusted_tag_starts`` or
        carries an attribute whose name starts with ``marker_prefix``. With
        ``marker_prefix=None``, no attribute makes a tag trusted.
        """
        try:
            template = scan_output_html(html)
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
            template = scan_output_html(html)
        except Exception:  # noqa: BLE001 - the final strict/warn pass reports malformed settled output
            return
        self._walk_pre_extension_raw(
            html,
            template,
            component_classes,
            inherited_component=None,
            inherited_instance=None,
        )

    def _walk_template(
        self,
        html: str,
        template: OutputTemplate,
        marker_prefix: str | None,
        trusted_tag_starts: frozenset[int],
        component_classes: dict[str, str],
        *,
        inherited_component: str | None,
        inherited_instance: str | None,
    ) -> None:
        for element in template.elements:
            node = element
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
            trusted = node.start_tag.token.start_index in trusted_tag_starts or (
                marker_prefix is not None
                and any(attr.key.content.translate(_ASCII_LOWER).startswith(marker_prefix) for attr in attrs)
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
        template: OutputTemplate,
        component_classes: dict[str, str],
        *,
        inherited_component: str | None,
        inherited_instance: str | None,
    ) -> None:
        for element in template.elements:
            node = element
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

    def _validate_attribute(self, tag: str, attr: OutputAttr, component: str, instance: str | None) -> None:
        name = attr.key.content.translate(_ASCII_LOWER)
        inner = attr.inner_value
        raw_source = "" if inner is None else inner.content
        value_start = attr.key.end_index if inner is None else inner.start_index
        decoded = _decode_html_attribute(raw_source)
        if _is_native_event_attribute(name):
            self._add(
                f"the native inline event attribute {attr.key.content!r}; use a Vue handler or Component.js",
                component,
                attr.key.start_index,
                attr.key.end_index,
                attribute=attr.key.content,
                dedupe_key=self._site_key(instance, (component, "native-event", name, decoded)),
            )
        if _is_url_attribute(tag, name) and _javascript_url(decoded):
            self._add(
                f"a javascript: URL in {attr.key.content!r}; use a normal URL or a Vue handler",
                component,
                value_start,
                value_start + len(raw_source.encode()),
                attribute=attr.key.content,
                dedupe_key=self._site_key(instance, (component, "javascript-url", tag, name, decoded)),
            )


class ReferenceJavascriptPolicy(_JavascriptPolicy):
    """The JavaScript policy with its Python rules."""

    __slots__ = ()

    def validate_settled_html(
        self,
        html: str,
        *,
        marker_prefix: str,
        trusted_tag_starts: frozenset[int],
        component_classes: dict[str, str],
        omit_handler_marker: str | None = None,
    ) -> str:
        """Inventory active behavior after every string-level extension hook."""
        try:
            template = scan_output_html(html)
        except Exception as error:
            if omit_handler_marker is not None and omit_handler_marker.lower() in html.lower():
                raise ValueError("Citry omission handler metadata remained in unparseable settled HTML") from error
            self._add(
                "unparseable-output",
                f"settled HTML could not be parsed for JavaScript policy validation ({error})",
                "settled render output",
            )
            return html
        marker_spans: list[tuple[int, int]] = []
        settled_bytes = html.encode()
        self._walk_template(
            html,
            template,
            marker_prefix,
            trusted_tag_starts,
            component_classes,
            inherited_component=None,
            inherited_instance=None,
            inherited_inside_form=False,
            omit_handler_marker=omit_handler_marker,
            omit_handler_spans=marker_spans,
            settled_bytes=settled_bytes,
        )
        if omit_handler_marker is None:
            return html
        merged_spans: list[tuple[int, int]] = []
        for start, end in sorted(marker_spans):
            if merged_spans and start <= merged_spans[-1][1]:
                previous_start, previous_end = merged_spans[-1]
                merged_spans[-1] = (previous_start, max(previous_end, end))
            else:
                merged_spans.append((start, end))
        retained: list[bytes] = []
        cursor = 0
        for start, end in merged_spans:
            retained.append(settled_bytes[cursor:start])
            cursor = end
        retained.append(settled_bytes[cursor:])
        cleaned = b"".join(retained).decode()
        if omit_handler_marker.lower() in cleaned.lower():
            raise ValueError("Citry omission handler metadata escaped settled HTML cleanup")
        return cleaned

    def validate_pre_extension_html(self, html: str, *, component_classes: dict[str, str]) -> None:
        """Remember warning-mode raw scripts before identical dependencies are inserted."""
        if self._mode != "warn":
            return
        try:
            template = scan_output_html(html)
        except Exception:  # noqa: BLE001 - the settled pass reports malformed output
            return
        self._walk_pre_extension_raw(
            html,
            template,
            component_classes,
            inherited_component=None,
            inherited_instance=None,
        )

    def _walk_template(
        self,
        html: str,
        template: OutputTemplate,
        marker_prefix: str,
        trusted_tag_starts: frozenset[int],
        component_classes: dict[str, str],
        *,
        inherited_component: str | None,
        inherited_instance: str | None,
        inherited_inside_form: bool,
        omit_handler_marker: str | None = None,
        omit_handler_spans: list[tuple[int, int]] | None = None,
        settled_bytes: bytes | None = None,
    ) -> None:
        for element in template.elements:
            node = element
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
            has_managed_handler = False
            if omit_handler_marker is not None:
                marker = omit_handler_marker.lower()
                for attr in attrs:
                    if attr.key.content.lower() != marker:
                        continue
                    has_managed_handler = True
                    start = attr.key.start_index
                    assert settled_bytes is not None
                    raw = settled_bytes
                    while start > node.start_tag.token.start_index and raw[start - 1] in b" \t\r\n\f":
                        start -= 1
                    end = attr.key.end_index
                    if attr.inner_value is not None:
                        inner = attr.inner_value
                        end = inner.end_index
                        if inner.start_index > 0 and raw[inner.start_index - 1] in b"\"'":
                            quote = raw[inner.start_index - 1]
                            if end < len(raw) and raw[end] == quote:
                                end += 1
                    if end < node.start_tag.token.end_index and raw[end] not in b" \t\r\n\f/>":
                        # A hook may place another attribute immediately after
                        # this one. Retain our leading separator so removing
                        # the marker cannot merge that neighbor into the tag
                        # name or previous attribute.
                        start = attr.key.start_index
                    assert omit_handler_spans is not None
                    omit_handler_spans.append((start, end))
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
                    inner_value = attr.inner_value
                    start = attr.key.end_index if inner_value is None else inner_value.start_index
                    self._add(
                        "javascript-url",
                        f"a javascript: URL in {attr.key.content!r} remains executable browser code",
                        component,
                        attribute=attr.key.content,
                        range_kind="settled HTML",
                        start=start,
                        end=start + len(("" if inner_value is None else inner_value.content).encode()),
                        key=self._site_key(own_instance, ("javascript-url", tag, name, start)),
                    )
                if _embedded_document_requires_javascript(tag, name, decoded):
                    inner_value = attr.inner_value
                    start = attr.key.end_index if inner_value is None else inner_value.start_index
                    self._add(
                        "embedded-document",
                        f"{attr.key.content!r} contains an embedded HTML document with executable browser code",
                        component,
                        attribute=attr.key.content,
                        range_kind="settled HTML",
                        start=start,
                        end=start + len(("" if inner_value is None else inner_value.content).encode()),
                        key=self._site_key(own_instance, ("embedded-document", tag, name, start)),
                    )

            if (
                self._mode == "omit"
                and (activation_attrs or has_managed_handler)
                and _handler_only_control(
                    tag,
                    attr_map,
                    activation_attrs,
                    has_managed_handler=has_managed_handler,
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
                    omit_handler_marker=omit_handler_marker,
                    omit_handler_spans=omit_handler_spans,
                    settled_bytes=settled_bytes,
                )

    def _walk_pre_extension_raw(
        self,
        html: str,
        template: OutputTemplate,
        component_classes: dict[str, str],
        *,
        inherited_component: str | None,
        inherited_instance: str | None,
    ) -> None:
        for element in template.elements:
            node = element
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


def _node_html(html: str, node: Any) -> str:
    end_tag = getattr(node, "end_tag", None)
    end = node.start_tag.token.end_index if end_tag is None else end_tag.token.end_index
    raw = html.encode()
    return raw[node.start_tag.token.start_index : end].decode()


def _decode_html_attribute(source: str) -> str:
    """Decode HTML character references in an attribute value so the checks see roughly what the browser sees."""
    decoded: list[str] = []
    position = 0
    while position < len(source):
        match = _ENTITY_RE.match(source, position)
        raw = match.group(0) if match is not None else source[position]
        value = html_module.unescape(_bounded_decimal_reference(raw))
        # An unknown reference such as `&bogus;` stays literal, so step past
        # only its `&` and keep scanning the rest as ordinary text.
        if value == raw and match is not None:
            raw = source[position]
            value = raw
        decoded.append(value)
        position += len(raw)
    return "".join(decoded)


def _bounded_decimal_reference(raw: str) -> str:
    """Shorten a long decimal reference to one that names the same code point, or U+110000 when it is larger."""
    # Python refuses to turn more than about 4,300 digits into an int, so a
    # long reference would raise from html.unescape. Leading zeros do not
    # change the code point, and any value with more than seven digits is
    # already past U+10FFFF, which decodes to U+FFFD like 1114112 does.
    if len(raw) <= _MAX_PLAIN_DECIMAL_REFERENCE or not raw.startswith("&#") or raw[2] in "xX":
        return raw
    semicolon = ";" if raw.endswith(";") else ""
    digits = raw[2 : len(raw) - len(semicolon)].lstrip("0") or "0"
    if len(digits) > 7:
        digits = "1114112"
    return f"&#{digits}{semicolon}"


def _javascript_url(value: str) -> bool:
    normalized = value.lstrip(
        "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
        "\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f "
    )
    return _JAVASCRIPT_URL_RE.match(normalized) is not None


def _is_native_event_attribute(name: str) -> bool:
    # Any name longer than `on` that starts with `on` counts, so event names
    # that browsers add later are caught too.
    return len(name) > 2 and name.startswith("on")


def _is_url_attribute(tag: str, name: str) -> bool:
    return name in _URL_ATTRIBUTES or (tag == "object" and name == "data")


def _attribute_map(attrs: tuple[OutputAttr, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for attr in attrs:
        name = attr.key.content.translate(_ASCII_LOWER)
        result.setdefault(name, _decoded_attr(attr))
    return result


def _decoded_attr(attr: OutputAttr) -> str:
    inner = attr.inner_value
    return _decode_html_attribute("" if inner is None else inner.content)


def _raw_script_is_executable(attrs: tuple[OutputAttr, ...]) -> bool:
    type_attrs = [attr for attr in attrs if attr.key.content.translate(_ASCII_LOWER) == "type"]
    if len(type_attrs) > 1:
        return True
    if not type_attrs:
        return True
    attr = type_attrs[0]
    value: str | bool = True if attr.inner_value is None else _decoded_attr(attr)
    return _is_executable({"type": value})


def _is_activation_attribute(name: str) -> bool:
    # Vue directive spellings in settled HTML need the browser runtime to mean anything.
    return name.startswith(("v-", "@", ":"))


def _is_omit_hazard(name: str, node: Any, html: str, attrs: dict[str, str]) -> bool:
    del node, html
    base = name.split(".", 1)[0]
    if base in {"v-for", "v-if", "v-show"}:
        return True
    if base in {"v-text", "v-html"}:
        # The HTML5 scanner deliberately exposes active source tokens rather
        # than reconstructing DOM parentage. Conservatively warn because a
        # source token cannot prove that the browser-visible fallback survives.
        return True
    bound = base[1:] if base.startswith(":") else base.removeprefix("v-bind:")
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
    has_managed_handler: bool,
    inside_form: bool,
) -> bool:
    # A Citry-managed handler is marked on the element by the omission scan,
    # while an authored Vue handler, including the object form `v-on="..."`,
    # appears as its own activation attribute.
    has_handler = has_managed_handler or any(
        name == "v-on" or name.startswith(("@", "v-on:")) for name in activation_attrs
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
            _decode_strict_base64(unquote_to_bytes(payload))
            if ";base64" in folded_header
            else unquote_to_bytes(payload)
        )
        return body.decode("utf8", errors="replace")
    except (BinasciiError, ValueError, TypeError):
        return "<script>"


def _decode_strict_base64(data: bytes) -> bytes:
    """Decode base64 that uses only the standard alphabet and exactly the padding it needs."""
    # `b64decode(validate=True)` accepts different padding on Python 3.10,
    # 3.11 and later versions, so the accepted form is spelled out here and
    # every Python version reads a document the same way.
    if _STRICT_BASE64_RE.fullmatch(data) is None:
        msg = "base64 data must use the standard alphabet and canonical padding"
        raise BinasciiError(msg)
    return b64decode(data)


def _html_document_requires_javascript(html: str, *, depth: int) -> bool:
    if depth >= 4:
        return True
    try:
        template = scan_output_html(html)
    except Exception:  # noqa: BLE001 - ambiguous embedded markup fails closed
        return True
    return _parsed_document_requires_javascript(template, depth=depth)


def _parsed_document_requires_javascript(template: OutputTemplate, *, depth: int) -> bool:
    for node in template.elements:
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


def _is_executable(attrs: Mapping[str, object]) -> bool:
    """Classify a script from its browser-canonical MIME essence."""
    aliases = [key for key in attrs if isinstance(key, str) and key.translate(_ASCII_LOWER) == "type"]
    if len(aliases) > 1:
        raise ValueError("A Script cannot declare the type attribute more than once with different casing.")
    value = None if not aliases else attrs[aliases[0]]
    if value is None or isinstance(value, bool):
        return True
    if type(value) is not str:
        raise ValueError("A Script type attribute must be a string or boolean.")
    normalized = value.strip(" \t\n\r\f").translate(_ASCII_LOWER)
    essence = normalized.partition(";")[0].rstrip(" \t\n\r\f")
    if essence in {"module", "importmap", "speculationrules"}:
        return ";" not in normalized
    return essence == "" or essence in _JAVASCRIPT_MIME_TYPES


def reference_server_copy_passes_csp(contents: str, security_csp: SecurityCspMode) -> bool:
    """Decide with the Python rules whether a Vue host may carry this body copy."""
    checker = ReferenceCspValidator(security_csp)
    checker.validate_settled_html(contents, marker_prefix=None, trusted_tag_starts=frozenset(), component_classes={})
    return not checker._findings


# ---------------------------------------------------------------------------
# Comparing every check with this copy (CITRY_OUTPUT_POLICY_DIFFERENTIAL=1)
# ---------------------------------------------------------------------------

# Each validator's copy, keyed by id(). The validator is kept alive with
# its copy so that its id cannot be reused by another validator.
_COPIES: dict[int, tuple[object, Any]] = {}
_INSTALLED: list[bool] = []


def _copy_of(validator: Any) -> Any:
    entry = _COPIES.get(id(validator))
    if entry is None or entry[0] is not validator:
        factory = ReferenceCspValidator if isinstance(validator, _CspRenderValidator) else ReferenceJavascriptPolicy
        entry = (validator, factory(validator._mode))
        _COPIES[id(validator)] = entry
    return entry[1]


def _outcome(call: Callable[[], object]) -> tuple[tuple[object, ...], BaseException | None]:
    try:
        return ("value", call()), None
    except Exception as error:  # noqa: BLE001 - both sides' errors are compared, then the real one is raised
        return ("error", type(error), str(error)), error


# ---------------------------------------------------------------------------
# What the comparison ignores on purpose
# ---------------------------------------------------------------------------

# This copy reads tags as a flat list, so it never sees which elements
# enclose a tag. The Rust check reads the tree the browser builds, so it
# makes two changes on purpose, and the comparison allows exactly those:
#
# 1. A finding on an element without a known component of its own names
#    the nearest known component that contains it, where this copy gives
#    the name for an element with no component (the name "settled render
#    output", or what `component_classes` maps the empty id to). When this
#    copy names any other component, Rust must name the same one. So a
#    Rust walk that picks the wrong ancestor passes here; the Rust unit
#    tests on that walk catch it.
# 2. Rust does not report a submit button, an input not of type `button`
#    or `reset`, a select, or a textarea that a `<form>` owns, because the
#    form gives it a fallback. Rust may leave out such a handler-only
#    finding that this copy reports, but only when a `<form>` start tag
#    comes before the control in the page, and it never adds one. Every
#    other handler-only finding must match.
#
# Everything else must match exactly: the findings, their order and
# offsets, the result, and whether a check warns or raises.
_GENERIC_OWNER = "settled render output"
_HANDLER_ONLY_DETAIL = "this control has a browser handler but no native navigation or submission fallback"
_REPORT_PREFIXES = ("Citry found ", "security_javascript=")
_REPORT_LINE = re.compile(r"- (?P<component>.*?)(?P<rest>(?: \(|, |: ).*)", re.DOTALL)
_REPORT_SPAN = re.compile(r", (?P<kind>settled HTML|pre-extension HTML) bytes (?P<start>\d+):")
_REPORT_COUNT = re.compile(r" found (\d+) ")


class _Pages:
    """The pages a comparison's findings point into, and the names this copy gives an element with no component."""

    def __init__(self, settled: str, pre_extension: str | None, component_classes: Mapping[str, str]) -> None:
        self._pages = {
            "settled HTML": settled,
            "pre-extension HTML": settled if pre_extension is None else pre_extension,
        }
        self._controls: dict[str, dict[int, bool]] = {}
        # The rules look up a missing id as the empty one, so a test
        # registry that names the empty id gives that name to elements
        # with no component.
        self.unowned = frozenset({_GENERIC_OWNER, component_classes.get("", _GENERIC_OWNER)})

    def may_have_form_fallback(self, range_kind: str, start: int | None) -> bool:
        """Say whether the control whose tag name starts at `start` would submit an enclosing form."""
        page = self._pages.get(range_kind)
        if page is None or start is None:
            return False
        if page not in self._controls:
            self._controls[page] = _form_controls(page)
        return self._controls[page].get(start, False)


def _form_controls(page: str) -> dict[int, bool]:
    # Each control's tag name start, and whether a form could own it and
    # give it a fallback. Only a form that starts earlier in the page can
    # contain a control or be the one the parser ties it to. A button of
    # type `button`, and an input of type `button` or `reset`, never
    # submits a form, so its verdict cannot depend on one.
    controls: dict[int, bool] = {}
    form_seen = False
    try:
        template = scan_output_html(page)
    except Exception:  # noqa: BLE001 - an unreadable page has no controls to excuse
        return controls
    for node in template.elements:
        tag = node.start_tag.name.content.translate(_ASCII_LOWER)
        kind = _attribute_map(node.start_tag.attrs).get("type", "").translate(_ASCII_LOWER)
        form_seen = form_seen or tag == "form"
        controls[node.start_tag.name.start_index] = form_seen and (
            (tag == "button" and kind != "button")
            or (tag == "input" and kind not in {"button", "reset"})
            or tag in {"select", "textarea"}
        )
    return controls


def _is_findings(value: list[Any]) -> bool:
    return bool(value) and all(dataclasses.is_dataclass(item) and hasattr(item, "component") for item in value)


def _finding_matches(real: Any, copy: Any, pages: _Pages) -> bool:
    if type(real) is not type(copy):
        return False
    # Only a finding this copy gives no component may name one on the
    # Rust side.
    component = real.component if copy.component in pages.unowned else copy.component
    return dataclasses.replace(copy, component=component) == real


def _finding_may_be_left_out(copy: Any, pages: _Pages) -> bool:
    return getattr(copy, "rule", None) == "handler-only-control" and pages.may_have_form_fallback(
        copy.range_kind, copy.start_index
    )


def _line_matches(real: str, copy: str, pages: _Pages) -> bool:
    real_parts, copy_parts = _REPORT_LINE.fullmatch(real), _REPORT_LINE.fullmatch(copy)
    if real_parts is None or copy_parts is None:
        return real == copy
    if copy_parts["component"] not in pages.unowned and copy_parts["component"] != real_parts["component"]:
        return False
    return real_parts["rest"] == copy_parts["rest"]


def _line_may_be_left_out(copy: str, pages: _Pages) -> bool:
    span = _REPORT_SPAN.search(copy)
    return (
        _HANDLER_ONLY_DETAIL in copy
        and span is not None
        and pages.may_have_form_fallback(span["kind"], int(span["start"]))
    )


def _report_matches(real: str, copy: str, pages: _Pages) -> bool:
    real_header, *real_lines = real.split("\n")
    copy_header, *copy_lines = copy.split("\n")
    # Each header counts its own lines, which differ when Rust leaves some
    # out, so the count is checked against the lines and the rest of the
    # header must match.
    for header, lines in ((real_header, real_lines), (copy_header, copy_lines)):
        count = _REPORT_COUNT.search(header)
        if count is None or int(count[1]) != len(lines):
            return real == copy
    if _REPORT_COUNT.sub(" found N ", real_header) != _REPORT_COUNT.sub(" found N ", copy_header):
        return False
    return _aligned(
        real_lines,
        copy_lines,
        lambda one, other: _line_matches(one, other, pages),
        lambda line: _line_may_be_left_out(line, pages),
    )


def _report_may_be_left_out(value: object, pages: _Pages) -> bool:
    # A warning whose every line Rust may leave out disappears on its side.
    if not (isinstance(value, tuple) and value[:1] == ("RuntimeWarning",)):
        return False
    message = value[-1]
    if not (len(value) == 2 and isinstance(message, str) and message.startswith(_REPORT_PREFIXES)):
        return False
    return all(_line_may_be_left_out(line, pages) for line in message.split("\n")[1:])


def _aligned(
    real: list[Any],
    copy: list[Any],
    matches: Callable[[Any, Any], bool],
    may_be_left_out: Callable[[Any], bool],
) -> bool:
    # Rust keeps this copy's order and only leaves items out, so each Rust
    # item must match the next copy item, after skipping copy items that
    # Rust may leave out. Matching greedily is enough because each item
    # that may be left out carries its own byte offset, so it never also
    # matches a later Rust item.
    index = 0
    for item in real:
        while index < len(copy) and not matches(item, copy[index]) and may_be_left_out(copy[index]):
            index += 1
        if index == len(copy) or not matches(item, copy[index]):
            return False
        index += 1
    return all(may_be_left_out(item) for item in copy[index:])


def _matches(real: object, copy: object, pages: _Pages) -> bool:
    if isinstance(real, list) and isinstance(copy, list):
        if _is_findings(real) or _is_findings(copy):
            return _aligned(
                real,
                copy,
                lambda one, other: _finding_matches(one, other, pages),
                lambda item: _finding_may_be_left_out(item, pages),
            )
        return _aligned(
            real,
            copy,
            lambda one, other: _matches(one, other, pages),
            lambda item: _report_may_be_left_out(item, pages),
        )
    if isinstance(real, tuple) and isinstance(copy, tuple):
        return len(real) == len(copy) and all(
            _matches(one, other, pages) for one, other in zip(real, copy, strict=True)
        )
    if isinstance(real, str) and isinstance(copy, str) and copy.startswith(_REPORT_PREFIXES):
        return _report_matches(real, copy, pages)
    return real == copy


def outcomes_match(
    real: object,
    copy: object,
    settled: str,
    pre_extension: str | None = None,
    component_classes: Mapping[str, str] | None = None,
) -> bool:
    """
    Say whether a Rust outcome matches this copy's, allowing only the two differences described above.

    Args:
        real: What the Rust check returned, raised, or warned, in any
            nesting of lists and tuples.
        copy: The same for this copy.
        settled: The page the settled-HTML offsets point into.
        pre_extension: The page the pre-extension offsets point into,
            when it differs from `settled`.
        component_classes: The component names the checks were given.

    """
    return _matches(real, copy, _Pages(settled, pre_extension, component_classes or {}))


def compare_calls(
    label: str,
    validator: Any,
    copy: Any,
    real_call: Callable[[], object],
    copy_call: Callable[[], object],
    html: str = "",
    component_classes: Mapping[str, str] | None = None,
) -> object:
    """
    Run one check on both sides and fail when the findings, result, or error differ.

    `html` is the page the check reads. The findings' offsets point into
    it, and the comparison reads its controls to tell which handler-only
    findings Rust may leave out (see `outcomes_match`).
    """
    real_before = len(validator._findings)
    copy_before = len(copy._findings)
    copy_outcome, _ = _outcome(copy_call)
    real_outcome, real_error = _outcome(real_call)
    real_new = validator._findings[real_before:]
    copy_new = copy._findings[copy_before:]
    if not outcomes_match((real_outcome, real_new), (copy_outcome, copy_new), html, None, component_classes):
        stack = "".join(traceback.format_stack(limit=8))
        msg = (
            f"{label}: the Rust output check differs from the Python rules\n"
            f"Rust result: {real_outcome!r}\nPython result: {copy_outcome!r}\n"
            f"Rust findings: {real_new!r}\nPython findings: {copy_new!r}\n{stack}"
        )
        raise AssertionError(msg)
    if real_error is not None:
        raise real_error
    return real_outcome[1]


def install_differential_checks() -> None:
    """Wrap every validator check and the Vue body check so each also runs this copy."""
    if _INSTALLED:
        return
    _INSTALLED.append(True)
    for cls in (_CspRenderValidator, _JavascriptPolicy):
        _wrap(cls, "validate_settled_html")
        _wrap(cls, "validate_pre_extension_html")
    real_gate = _output_policy.server_copy_passes_csp

    def compared_gate(contents: str, security_csp: SecurityCspMode) -> bool:
        real = real_gate(contents, security_csp)
        expected = reference_server_copy_passes_csp(contents, security_csp)
        if real != expected:
            msg = f"Vue body check: Rust says {real}, the Python rules say {expected} for {contents[:500]!r}"
            raise AssertionError(msg)
        return real

    _output_policy.server_copy_passes_csp = compared_gate


def _wrap(cls: type, name: str) -> None:
    real_method = getattr(cls, name)

    def compared(self: Any, html: str, **kwargs: Any) -> object:
        if isinstance(self, (ReferenceCspValidator, ReferenceJavascriptPolicy)):
            return real_method(self, html, **kwargs)
        copy = _copy_of(self)
        copy_kwargs = {key: value for key, value in kwargs.items() if key != "check"}
        return compare_calls(
            f"{cls.__name__}.{name}",
            self,
            copy,
            lambda: real_method(self, html, **kwargs),
            lambda: getattr(copy, name)(html, **copy_kwargs),
            html,
            kwargs.get("component_classes"),
        )

    setattr(cls, name, compared)


__all__ = [
    "ReferenceCspValidator",
    "ReferenceJavascriptPolicy",
    "compare_calls",
    "install_differential_checks",
    "outcomes_match",
    "reference_server_copy_passes_csp",
]
