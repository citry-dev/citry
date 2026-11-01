"""
A tag with a very long run of attributes is refused, and the process keeps running.

The HTML reader behind the output checks, the fragment check for `Markup`
and `<c-raw>`, and the hydration checks nests several calls for each
attribute written as `name="value"`, and one tag with about 20,000 of them
overflowed the stack and killed the whole process. A stack overflow cannot be
caught, so every case runs in a child Python process, on a thread with a
small stack, and the test reads what the child printed. The limit is
`MAX_ATTRIBUTE_RUN` in `crates/citry_html_transform/src/html_limits.rs`.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from typing import Any

import pytest

# The most attributes in a row the Rust reader accepts; the Rust tests pin
# the constant itself.
LIMIT = 1024

# The child runs `body` on a thread with this stack, which is smaller than
# the 8 MiB of a main thread and well below what 20,000 attributes need.
STACK_KIB = 512

# Runs inside the child. `body` defines `result` as a JSON-serializable value.
_CHILD = """
import json, sys, threading, warnings

def work():
    result = None
{body}
    print("RESULT " + json.dumps(result), flush=True)

threading.stack_size({stack_kib} * 1024)
thread = threading.Thread(target=work)
thread.start()
thread.join()
"""


def _run_in_child(body: str, *, stack_kib: int = STACK_KIB) -> Any:
    """Run ``body`` in a child process and return the value it left in ``result``."""
    source = _CHILD.format(body=textwrap.indent(textwrap.dedent(body), "    "), stack_kib=stack_kib)
    # -I keeps the child from reading the test's environment or the working
    # directory, as the repository convention for scripts that run code.
    done = subprocess.run(  # noqa: S603
        [sys.executable, "-I", "-c", source],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    lines = [line for line in done.stdout.splitlines() if line.startswith("RESULT ")]
    # A stack overflow ends the child with a signal, which shows as a
    # negative return code, and prints no result.
    assert done.returncode == 0, f"the child died with {done.returncode}: {done.stderr[-2000:]}"
    assert len(lines) == 1, done.stdout[-2000:] + done.stderr[-2000:]
    return json.loads(lines[0].removeprefix("RESULT "))


# A page whose element takes its attributes from a dict, as a page does when
# it spreads data it loaded from storage or a form onto an element.
_SPREAD = """
from citry import Citry, Component

def render(count, **settings):
    engine = Citry(autodiscover=False, **settings)
    attributes = {f"k{i}": "v" for i in range(count)}

    class Profile(Component):
        citry = engine
        template = '''
          <section>
            <p c-bind="attributes">x</p>
          </section>
        '''

        def template_data(self, kwargs, slots):
            return {"attributes": attributes}

    return Profile().render().serialize()

def outcome(count, **settings):
    # Warnings are recorded so a warn mode shows what it said.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            html = render(count, **settings)
        except ValueError as error:
            return {"raised": str(error)}
    return {"html_has_last": f'k{count - 1}="v"' in html, "warnings": [str(w.message) for w in caught]}
"""


@pytest.mark.parametrize(
    ("setting", "mode", "wording"),
    [
        ("security_csp", "strict", "could not be parsed for CSP validation"),
        ("security_javascript", "forbid", "could not be parsed for JavaScript policy validation"),
    ],
)
def test_a_raising_output_check_refuses_a_spread_with_20000_attributes(setting: str, mode: str, wording: str) -> None:
    result = _run_in_child(
        _SPREAD
        + f"""
result = outcome(20000, {setting}={mode!r})
"""
    )
    assert wording in result["raised"]
    assert f"more than {LIMIT} attributes in a row" in result["raised"]


@pytest.mark.parametrize(
    ("setting", "mode"),
    [("security_csp", "warn"), ("security_javascript", "warn")],
)
def test_a_warning_output_check_warns_and_still_returns_the_page(setting: str, mode: str) -> None:
    result = _run_in_child(
        _SPREAD
        + f"""
result = outcome(20000, {setting}={mode!r})
"""
    )
    assert result["html_has_last"] is True
    assert len(result["warnings"]) == 1
    assert f"more than {LIMIT} attributes in a row" in result["warnings"][0]


@pytest.mark.parametrize(
    ("setting", "mode"),
    [("security_csp", "strict"), ("security_javascript", "forbid")],
)
def test_a_spread_at_the_limit_passes_the_output_checks_on_a_small_stack(setting: str, mode: str) -> None:
    result = _run_in_child(
        _SPREAD
        + f"""
result = outcome({LIMIT}, {setting}={mode!r})
"""
    )
    assert result == {"html_has_last": True, "warnings": []}


def test_a_spread_one_over_the_limit_is_refused_by_the_output_check() -> None:
    result = _run_in_child(
        _SPREAD
        + f"""
result = outcome({LIMIT + 1}, security_csp="strict")
"""
    )
    assert f"more than {LIMIT} attributes in a row" in result["raised"]


def test_a_hydrating_component_with_a_document_tag_in_its_data_still_renders() -> None:
    # A value holding `<body>` makes the hydration check read the written
    # HTML with the tokenizer.
    result = _run_in_child(
        """
from citry import Citry, Component

engine = Citry(autodiscover=False)
attributes = {f"k{i}": "v" for i in range(20000)}
attributes["data-X"] = "<body>"

class Card(Component):
    citry = engine
    template = '''
      <main>
        <p
          c-bind="attributes"
          :class="{ open: open }"
        >x</p>
      </main>
    '''

    def template_data(self, kwargs, slots):
        return {"attributes": attributes}

    def js_data(self, kwargs, slots):
        return {"open": True}

html = Card().render().serialize()
result = {"has_last": "k19999" in html}
"""
    )
    assert result == {"has_last": True}


def test_the_fragment_checks_refuse_a_tag_with_20000_attributes() -> None:
    result = _run_in_child(
        """
from citry._vue.opaque_html import reject_cross_boundary_html
from citry_core.html_transform import (
    browser_fragment_matches_nodes,
    scan_output_html,
    static_html_node_count,
    validate_html_fragment_boundary,
)

html = "<p" + "".join(f' a{i}="v"' for i in range(20000)) + ">x</p>"
result = {}
for name, call in (("validate", validate_html_fragment_boundary), ("scan", scan_output_html)):
    try:
        call(html)
        result[name] = "accepted"
    except ValueError as error:
        result[name] = str(error)
result["nodes"] = browser_fragment_matches_nodes(html, "div", [("open", "p", []), ("close", "p", [])])
result["count"] = static_html_node_count(html)
try:
    reject_cross_boundary_html(html, origin="A Markup value")
    result["reject"] = "accepted"
except ValueError as error:
    result["reject"] = str(error)
"""
    )
    assert result["validate"].startswith(f"opaque HTML has a tag with more than {LIMIT} attributes in a row")
    assert result["scan"].startswith(f"HTML has a tag with more than {LIMIT} attributes in a row")
    assert result["nodes"] is False
    # html5ever's own parse, used for the count, reads attributes in a loop.
    assert result["count"] == 1
    assert result["reject"].startswith("A Markup value is not accepted. HTML has a tag with more than")
    assert "Spread the attributes over several elements" in result["reject"]


def test_attributes_that_do_not_nest_are_read_without_a_limit() -> None:
    # Single-quoted, unquoted and bare attributes, and double-quoted ones
    # with no space before the next name, return to the reader's main loop
    # after each attribute, so a long tag of them was always safe.
    result = _run_in_child(
        """
from citry_core.html_transform import scan_output_html, validate_html_fragment_boundary

shapes = {
    "single": lambda i: f" a{i}='v'",
    "unquoted": lambda i: f" a{i}=v",
    "bare": lambda i: f" a{i}",
}
result = {}
for name, shape in shapes.items():
    html = "<p" + "".join(shape(i) for i in range(5000)) + ">x</p>"
    validate_html_fragment_boundary(html)
    result[name] = len(scan_output_html(html)[0]["attributes"])
# The next name starts right after the closing quote.
html = "<p " + "".join(f'a{i}="v"' for i in range(5000)) + ">x</p>"
result["no space"] = len(scan_output_html(html)[0]["attributes"])
"""
    )
    assert result == {"single": 5000, "unquoted": 5000, "bare": 5000, "no space": 5000}


def test_a_page_with_many_ordinary_tags_is_not_counted_as_one_run() -> None:
    # 50,000 double-quoted attributes spread over 10,000 tags: the count
    # starts again at every tag.
    result = _run_in_child(
        """
from citry_core.html_transform import scan_output_html

html = "".join(f'<p a="1" b="2" c="3" d="4" e="5">{i}</p>' for i in range(10000))
result = len(scan_output_html(html))
"""
    )
    assert result == 10000
