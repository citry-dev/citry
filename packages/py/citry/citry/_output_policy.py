"""
Run the strict-CSP and JavaScript-policy checks of finished HTML in Rust.

`serialize()` checks the page it returns when `security_csp` or
`security_javascript` is set (see `_csp_validation.py` and
`_javascript_policy.py`). Rust reads the page and returns only what the
rules found: each reported attribute or element, and every `script` and
`style` element, because a validator remembers some of those between two
checks of one page. The validators keep the message wording, the
bookkeeping that drops repeated findings, and the decision to warn or
raise.

One Rust call can serve both validators when they check the same string,
so `serialize()` reads each page once.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

from citry_core.html_transform import _check_output_html

if TYPE_CHECKING:
    from citry.settings import SecurityCspMode, SecurityJavascriptMode

# Set to 1 to compare every check with the frozen Python copy of the rules
# in `tests/_output_policy_reference.py`, across any test suite.
DIFFERENTIAL_ENVIRONMENT_VARIABLE = "CITRY_OUTPUT_POLICY_DIFFERENTIAL"

# Each event is a tuple, in the order the start tags appear. One reported
# attribute or element is
#     (rule, tag, attribute, start, end, token_start, cids)
# and one script or style element is
#     ("element", tag, token_start, name_start, name_end, element_end,
#      trusted, executable, has_manager_attribute, cids)
# where cids are the element's `data-cid-*` suffixes in attribute order.
OutputEvent = tuple[Any, ...]


class OutputCheck:
    """What one Rust check of one HTML string found."""

    __slots__ = ("_encoded", "cleaned_html", "csp", "error", "events", "html", "javascript", "pre_extension")

    def __init__(
        self,
        html: str,
        *,
        pre_extension: bool,
        csp: bool,
        javascript: SecurityJavascriptMode | None,
        events: list[OutputEvent],
        cleaned_html: str | None,
        error: Exception | None,
    ) -> None:
        self.html = html
        self.pre_extension = pre_extension
        self.csp = csp
        self.javascript = javascript
        self.events = events
        self.cleaned_html = cleaned_html
        # The check could not read the page; each validator reports it in
        # its own words.
        self.error = error
        self._encoded: bytes | None = None

    def element_bytes(self, start: int, end: int) -> bytes:
        """Return the page's bytes from `start` to `end`, the identity of a remembered element."""
        # Only warn modes remember elements, so the page is encoded at most
        # once per check and only when one of them asks.
        if self._encoded is None:
            self._encoded = self.html.encode()
        return self._encoded[start:end]

    def require(self, html: str, *, pre_extension: bool, csp: bool, javascript: str | None) -> None:
        """Fail loudly when a validator receives a check made for another string or other rules."""
        # A check made with other options would silently miss findings, so a
        # wrong caller is a bug to surface, not a case to handle.
        if (
            self.html is not html
            or self.pre_extension != pre_extension
            or (csp and not self.csp)
            or (javascript is not None and self.javascript != javascript)
        ):
            msg = "an output check was shared with a validator it was not made for"
            raise AssertionError(msg)


def check_output_html(
    html: str,
    *,
    pre_extension: bool = False,
    csp: bool = False,
    javascript: SecurityJavascriptMode | None = None,
    marker_prefix: str | None = None,
    trusted_tag_starts: frozenset[int] = frozenset(),
    omit_handler_marker: str | None = None,
) -> OutputCheck:
    """
    Check `html` once for every validator that names its rules here.

    `marker_prefix` and `trusted_tag_starts` say which tags Citry wrote
    itself (see `_CspRenderValidator.validate_settled_html`), and
    `omit_handler_marker` is the private attribute the JavaScript policy
    removes in `omit` mode.
    """
    # "allow" runs no JavaScript rules, the same as no policy.
    rust_javascript = None if javascript in (None, "allow") else cast("Literal['warn', 'omit', 'forbid']", javascript)
    try:
        events, cleaned_html = _check_output_html(
            html,
            pre_extension=pre_extension,
            csp=csp,
            javascript=rust_javascript,
            marker_prefix=marker_prefix,
            trusted_tag_starts=trusted_tag_starts,
            omit_handler_marker=omit_handler_marker,
        )
    except Exception as error:  # noqa: BLE001 - each validator reports an unreadable page itself
        # A lone surrogate in `html` cannot cross into Rust; the validators
        # report such a page as unparseable, as they report any failed read.
        return OutputCheck(
            html,
            pre_extension=pre_extension,
            csp=csp,
            javascript=javascript,
            events=[],
            cleaned_html=None,
            error=error,
        )
    return OutputCheck(
        html,
        pre_extension=pre_extension,
        csp=csp,
        javascript=javascript,
        events=events,
        cleaned_html=cleaned_html,
        error=None,
    )


def own_instance(cids: tuple[str, ...], component_classes: dict[str, str]) -> str | None:
    """Return the first `data-cid-*` suffix on an element that names a known component."""
    return next((cid for cid in cids if cid in component_classes), None)


def server_copy_passes_csp(contents: str, security_csp: SecurityCspMode) -> bool:
    """
    Whether the CSP check reports nothing in the body copy a Vue host would carry.

    Citry adds its own trusted dependency tags only after this check, so
    every raw `<script>` or `<style>` counts, whatever attributes it has.
    """
    del security_csp  # Both CSP modes report the same things here.
    # With only the CSP rules selected and no tag trusted, every event is a
    # CSP finding or a raw element the check would report.
    check = check_output_html(contents, csp=True, marker_prefix=None)
    return check.error is None and not check.events


def install_differential_checks() -> None:
    """When the environment asks for it, compare every check with the frozen Python copy of the rules."""
    if os.environ.get(DIFFERENTIAL_ENVIRONMENT_VARIABLE) != "1":
        return
    # The copy is test code, so it is read from the repository checkout this
    # package was installed from.
    path = Path(__file__).resolve().parents[1] / "tests" / "_output_policy_reference.py"
    if not path.is_file():
        msg = f"{DIFFERENTIAL_ENVIRONMENT_VARIABLE}=1 needs the citry test suite at {path}"
        raise RuntimeError(msg)
    spec = importlib.util.spec_from_file_location("citry_output_policy_reference", path)
    if spec is None or spec.loader is None:
        msg = f"cannot load {path}"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.install_differential_checks()


__all__ = [
    "DIFFERENTIAL_ENVIRONMENT_VARIABLE",
    "OutputCheck",
    "check_output_html",
    "install_differential_checks",
    "own_instance",
    "server_copy_passes_csp",
]
