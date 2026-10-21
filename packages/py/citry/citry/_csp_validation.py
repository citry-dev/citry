"""Render-time validation for Citry's strict CSP contract."""

from __future__ import annotations

import html as html_module
import re
from dataclasses import dataclass
from typing import Any, Literal

from citry._caller_warnings import warn_at_caller
from citry._output_html import OutputAttr, OutputTemplate, scan_output_html

_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
_ENTITY_RE = re.compile(r"&(?:#[xX][0-9A-Fa-f]+|#[0-9]+|[A-Za-z][A-Za-z0-9]+);?")
_JAVASCRIPT_URL_RE = re.compile(
    r"j[\t\n\r]*a[\t\n\r]*v[\t\n\r]*a[\t\n\r]*s[\t\n\r]*c[\t\n\r]*r[\t\n\r]*i[\t\n\r]*p[\t\n\r]*t[\t\n\r]*:",
    re.IGNORECASE,
)
_URL_ATTRIBUTES = frozenset({"action", "formaction", "href", "src", "xlink:href"})


@dataclass(frozen=True, slots=True)
class _CspRenderFinding:
    """One deduplicated problem found in the render output."""

    detail: str
    component: str
    attribute: str | None
    range_kind: Literal["pre-extension HTML", "settled HTML"]
    start_index: int | None = None
    end_index: int | None = None

    def display(self) -> str:
        attribute = f", attribute {self.attribute!r}" if self.attribute is not None else ""
        position = "" if self.start_index is None else f", {self.range_kind} bytes {self.start_index}:{self.end_index}"
        return f"{self.component}{attribute}{position}: {self.detail}"


class _CspRenderValidator:
    """Collect CSP findings, then warn or fail once the render has settled."""

    __slots__ = ("_findings", "_mode", "_pre_extension_raw", "_seen", "_site_counts")

    def __init__(self, mode: str) -> None:
        self._mode = mode
        self._findings: list[_CspRenderFinding] = []
        self._seen: set[tuple[object, ...]] = set()
        self._site_counts: dict[tuple[str, tuple[object, ...]], int] = {}
        self._pre_extension_raw: dict[tuple[str, str], int] = {}

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

    def add_dependency_findings(self, findings: tuple[str, ...]) -> None:
        """Include migration warnings discovered while dependency descriptors were built."""
        for finding in findings:
            self._add(finding, "dependency emission", None, None)

    def report(self) -> None:
        """Emit one warning in migration mode or reject the strict render."""
        if not self._findings:
            return
        body = "\n".join(f"- {finding.display()}" for finding in self._findings)
        message = f"Citry found {len(self._findings)} strict-CSP incompatibility issue(s):\n{body}"
        if self._mode == "warn":
            # Point at the author's serialize call, wherever Citry noticed it.
            warn_at_caller(message, RuntimeWarning)
            return
        raise ValueError(message)

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
        range_kind: Literal["pre-extension HTML", "settled HTML"] = "settled HTML",
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
                start_index=start,
                end_index=end,
            )
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
        value = html_module.unescape(raw)
        # An unknown reference such as `&bogus;` stays literal, so step past
        # only its `&` and keep scanning the rest as ordinary text.
        if value == raw and match is not None:
            raw = source[position]
            value = raw
        decoded.append(value)
        position += len(raw)
    return "".join(decoded)


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


__all__ = ["_CspRenderValidator"]
