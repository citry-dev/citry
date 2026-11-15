"""
Every server-side URL check in citry reads a scheme as the shared table says.

The table, ``crates/citry_html_transform/tests/fixtures/url_schemes.json``,
lists URLs and the scheme the browser's URL parser reads from each. The
Rust reader, the browser copies and Citry UI read the same table, so a
check that starts reading a scheme its own way fails here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from citry._urls import url_scheme, url_scheme_and_rest
from citry.ext.events import actions
from citry.ext.events.routes import _URL_LEADING_STRIP, _resolve_redirect_url
from citry.util.routing import RouteHeaders, RouteRequest
from citry_core.html_transform import _is_javascript_url, _read_url_scheme

# Read by repository path, as the VS Code tests read the formatter fixtures.
# A missing file fails the test rather than skipping it.
_TABLE = Path(__file__).resolve().parents[4] / "crates/citry_html_transform/tests/fixtures/url_schemes.json"
_ROWS: list[dict[str, Any]] = json.loads(_TABLE.read_text(encoding="utf-8"))["rows"]


def _row_id(row: dict[str, Any]) -> str:
    return ascii(row["url"])


@pytest.mark.parametrize("row", _ROWS, ids=_row_id)
def test_the_binding_reads_each_row_as_the_table_says(row: dict[str, Any]) -> None:
    expected = None if row["scheme"] is None else (row["scheme"], row["rest"])
    assert _read_url_scheme(row["url"]) == expected
    assert url_scheme_and_rest(row["url"]) == expected
    assert url_scheme(row["url"]) == row["scheme"]
    assert _is_javascript_url(row["url"]) == (row["scheme"] == "javascript")


@pytest.mark.parametrize("row", _ROWS, ids=_row_id)
def test_a_redirect_accepts_a_row_only_with_an_http_scheme_or_none(row: dict[str, Any]) -> None:
    url = row["url"]
    assert actions.redirect_url_scheme(url) == row["scheme"]
    # The control-character and empty-URL rules run before the scheme rule,
    # so only the rows they let through can show the scheme decision.
    if not url or any(ord(char) < 0x20 or ord(char) == 0x7F for char in url):
        with pytest.raises(ValueError, match=r"non-empty|control character"):
            actions.Redirect(url)
    elif row["scheme"] in (None, *actions.REDIRECT_SCHEMES):
        assert actions.Redirect(url).url == url
    else:
        with pytest.raises(ValueError, match=f"the {re.escape(repr(row['scheme']))} scheme"):
            actions.Redirect(url)


@pytest.mark.parametrize("row", _ROWS, ids=_row_id)
def test_the_form_redirect_resolves_a_row_only_when_it_has_no_scheme(row: dict[str, Any]) -> None:
    # A Referer from the same host makes the resolver join every URL that
    # depends on the page, so an unchanged URL means it read a scheme (or a
    # leading `/` or `\`).
    request = RouteRequest(
        method="POST",
        path="/citry/events/x",
        headers=RouteHeaders([("Host", "app.test"), ("Referer", "http://app.test/shop/list")]),
    )
    stripped = row["url"].lstrip(_URL_LEADING_STRIP).translate({9: None, 10: None, 13: None})
    passes_through = row["scheme"] is not None or stripped.startswith(("/", "\\"))
    assert (_resolve_redirect_url(row["url"], request) == row["url"]) == passes_through
