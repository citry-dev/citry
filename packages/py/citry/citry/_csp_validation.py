"""Render-time validation for Citry's strict CSP contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from citry import _output_policy
from citry._caller_warnings import warn_at_caller

_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


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
        # Each raw element seen before the hooks ran, by tag and source
        # bytes, with how many identical copies are still unmatched.
        self._pre_extension_raw: dict[tuple[str, bytes], int] = {}

    def validate_settled_html(
        self,
        html: str,
        *,
        marker_prefix: str | None,
        trusted_tag_starts: frozenset[int],
        component_classes: dict[str, str],
        check: _output_policy.OutputCheck | None = None,
    ) -> None:
        """
        Check the final hook output while structured dependency markers still exist.

        A tag is trusted when it starts at one of ``trusted_tag_starts`` or
        carries an attribute whose name starts with ``marker_prefix``. With
        ``marker_prefix=None``, no attribute makes a tag trusted. A caller
        that already checked ``html`` with these options passes that
        ``check``, so the page is read once.
        """
        if check is None:
            check = _output_policy.check_output_html(
                html, csp=True, marker_prefix=marker_prefix, trusted_tag_starts=trusted_tag_starts
            )
        check.require(html, pre_extension=False, csp=True, javascript=None)
        if check.error is not None:
            self._add(
                f"the settled HTML could not be parsed for CSP validation ({check.error})",
                "settled render output",
                None,
                None,
            )
            return
        for event in check.events:
            if event[0] == "element":
                self._replay_settled_element(check, event, component_classes)
            elif event[0].startswith("csp-"):
                self._replay_attribute(event, component_classes)

    def validate_pre_extension_html(
        self,
        html: str,
        *,
        component_classes: dict[str, str],
        check: _output_policy.OutputCheck | None = None,
    ) -> None:
        """Remember raw active tags before dependency emission can create identical markup."""
        if self._mode != "warn":
            return
        if check is None:
            check = _output_policy.check_output_html(html, pre_extension=True)
        check.require(html, pre_extension=True, csp=False, javascript=None)
        # The settled pass reports malformed output.
        if check.error is not None:
            return
        for event in check.events:
            _, tag, token_start, name_start, name_end, element_end, _, _, _, cids = event
            instance = _output_policy.own_instance(cids, component_classes)
            component = component_classes.get(instance or "", "settled render output")
            fingerprint = (tag, check.element_bytes(token_start, element_end))
            self._pre_extension_raw[fingerprint] = self._pre_extension_raw.get(fingerprint, 0) + 1
            self._add_raw_tag(tag, component, instance, name_start, name_end, range_kind="pre-extension HTML")

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

    def _replay_settled_element(
        self,
        check: _output_policy.OutputCheck,
        event: _output_policy.OutputEvent,
        component_classes: dict[str, str],
    ) -> None:
        _, tag, token_start, name_start, name_end, element_end, trusted, _, _, cids = event
        # Citry's own dependency tags are the raw elements it allows.
        if trusted:
            return
        instance = _output_policy.own_instance(cids, component_classes)
        component = component_classes.get(instance or "", "settled render output")
        # An identical element seen before the hooks ran was reported then,
        # so one remembered copy is used up instead of reporting it again.
        if self._pre_extension_raw:
            fingerprint = (tag, check.element_bytes(token_start, element_end))
            remembered = self._pre_extension_raw.get(fingerprint, 0)
            if remembered:
                self._pre_extension_raw[fingerprint] = remembered - 1
                return
        self._add_raw_tag(tag, component, instance, name_start, name_end)

    def _replay_attribute(self, event: _output_policy.OutputEvent, component_classes: dict[str, str]) -> None:
        rule, tag, attribute, start, end, _, cids = event
        instance = _output_policy.own_instance(cids, component_classes)
        component = component_classes.get(instance or "", "settled render output")
        name = (attribute or "").translate(_ASCII_LOWER)
        if rule == "csp-native-event":
            detail = f"the native inline event attribute {attribute!r}; use a Vue handler or Component.js"
            signature: tuple[object, ...] = (component, "native-event", name)
        else:
            detail = f"a javascript: URL in {attribute!r}; use a normal URL or a Vue handler"
            signature = (component, "javascript-url", tag, name)
        self._add(
            detail,
            component,
            start,
            end,
            attribute=attribute,
            dedupe_key=self._site_key(instance, signature),
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

    def _site_key(self, instance: str | None, signature: tuple[object, ...]) -> tuple[object, ...]:
        # The counter makes each reported site's key unique, so two sites
        # with the same text are both reported.
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


__all__ = ["_CspRenderValidator"]
