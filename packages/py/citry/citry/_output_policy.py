"""
Run the strict-CSP and JavaScript-policy checks of finished HTML in Rust.

`serialize()` checks the page it returns when `security_csp` or
`security_javascript` is set (see `_csp_validation.py` and
`_javascript_policy.py`). Rust reads the page and returns only what the
rules found: each reported attribute or element, and the `script` and
`style` elements the selected rules look at (only scripts when only the
JavaScript policy runs), because a validator remembers some of those
between two checks of one page. The validators keep the message wording,
the bookkeeping that drops repeated findings, and the decision to warn or
raise.

When both validators check the same string, one Rust call serves both. The
exception is a page the JavaScript policy removed omit markers from:
removing them moves the tags after them, so the CSP check reads the
cleaned page again.
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
# where cids are the element's own `data-cid-*` suffixes in attribute order,
# then those of the elements the browser put around it, nearest first.
OutputEvent = tuple[Any, ...]


class OutputCheck:
    """What one Rust check of one HTML string found."""

    __slots__ = (
        "_encoded",
        "cleaned_html",
        "csp",
        "error",
        "events",
        "html",
        "javascript",
        "marker_prefix",
        "omit_handler_marker",
        "pre_extension",
        "trusted_tag_starts",
    )

    def __init__(
        self,
        html: str,
        *,
        pre_extension: bool,
        csp: bool,
        javascript: SecurityJavascriptMode | None,
        marker_prefix: str | None,
        trusted_tag_starts: frozenset[int],
        omit_handler_marker: str | None,
        events: list[OutputEvent],
        cleaned_html: str | None,
        error: Exception | None,
    ) -> None:
        self.html = html
        self.pre_extension = pre_extension
        self.csp = csp
        self.javascript = javascript
        self.marker_prefix = marker_prefix
        self.trusted_tag_starts = trusted_tag_starts
        self.omit_handler_marker = omit_handler_marker
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

    def require_pre_extension(self, html: str) -> None:
        """Fail loudly unless this is the pre-extension check of `html`."""
        if self.html is not html or not self.pre_extension:
            raise AssertionError(_MISMATCH)

    def require_settled(
        self,
        html: str,
        *,
        csp: bool,
        javascript: str | None,
        marker_prefix: str | None,
        trusted_tag_starts: frozenset[int],
        omit_handler_marker: str | None = None,
    ) -> None:
        """Fail loudly unless this check of `html` used the rules and trust the validator asks for."""
        # A check made with other options would silently report the wrong
        # findings, so a wrong caller is a bug to surface, not a case to
        # handle. The omit marker matters only to the JavaScript policy.
        if not isinstance(trusted_tag_starts, frozenset):
            trusted_tag_starts = frozenset(trusted_tag_starts)
        if (
            self.html is not html
            or self.pre_extension
            or (csp and not self.csp)
            or (javascript is not None and self.javascript != javascript)
            or self.marker_prefix != marker_prefix
            or self.trusted_tag_starts != trusted_tag_starts
            or (javascript is not None and self.omit_handler_marker != omit_handler_marker)
        ):
            raise AssertionError(_MISMATCH)


_MISMATCH = "an output check was shared with a validator it was not made for"


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
    Run the rules that `csp` and `javascript` select over `html` in one Rust call.

    One result can serve both validators. `marker_prefix` and
    `trusted_tag_starts` say which tags Citry wrote itself (see
    `_CspRenderValidator.validate_settled_html`), and `omit_handler_marker`
    is the private attribute the JavaScript policy removes in `omit` mode.
    A page Rust cannot read does not raise: the result's `error` holds the
    exception, and each validator reports it.
    """
    # "allow" runs no JavaScript rules, the same as no policy.
    rust_javascript = None if javascript in (None, "allow") else cast("Literal['warn', 'omit', 'forbid']", javascript)
    # The Rust binding takes a set, and callers may hold the starts in any
    # collection.
    trusted = trusted_tag_starts if isinstance(trusted_tag_starts, frozenset) else frozenset(trusted_tag_starts)

    def result(events: list[OutputEvent], cleaned_html: str | None, error: Exception | None) -> OutputCheck:
        return OutputCheck(
            html,
            pre_extension=pre_extension,
            csp=csp,
            javascript=javascript,
            marker_prefix=marker_prefix,
            trusted_tag_starts=trusted,
            omit_handler_marker=omit_handler_marker,
            events=events,
            cleaned_html=cleaned_html,
            error=error,
        )

    try:
        events, cleaned_html = _check_output_html(
            html,
            pre_extension=pre_extension,
            csp=csp,
            javascript=rust_javascript,
            marker_prefix=marker_prefix,
            trusted_tag_starts=trusted,
            omit_handler_marker=omit_handler_marker,
        )
    except UnicodeEncodeError as error:
        # A lone surrogate in `html` cannot cross into Rust.
        return result([], None, error)
    except ValueError as error:
        # The binding turns a Rust panic into this error. Any other
        # ValueError, such as an unknown mode, is a bug in the caller.
        if not str(error).startswith("citry output check failed:"):
            raise
        return result([], None, error)
    return result(events, cleaned_html, None)


def own_instance(cids: tuple[str, ...], component_classes: dict[str, str]) -> str | None:
    """
    Return the `data-cid-*` suffix of the nearest known component that contains an element, or None.

    `cids` lists the element's own suffixes first, then those of the
    elements that contain it, nearest first, so the first known one is
    the nearest component.
    """
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
    # The copy is test code, so it is read from the repository checkout an
    # editable install points at. The package's own pyproject.toml next to
    # `tests/` shows that this is that checkout and not, for example, a
    # `tests` folder another package put in site-packages.
    root = Path(__file__).resolve().parents[1]
    path = root / "tests" / "_output_policy_reference.py"
    if not (root / "pyproject.toml").is_file() or not path.is_file():
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
