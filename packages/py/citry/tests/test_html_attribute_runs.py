"""
A tag with a very long run of attributes is refused, and the process keeps running.

The HTML reader behind the output checks, the fragment check for `Markup`
and `<c-raw>`, and the hydration checks is html5gum. An html5gum release that
nests a few calls for each attribute written as `name="value"` overflows the
stack on a long tag and kills the whole process: version 0.8.4 did so at
about 50,000 attributes on the 8 MiB main-thread stack in a release build
(about 3,000 on a 512 KiB thread), and version 0.9.1 does not nest. A stack
overflow cannot be caught, so every case runs in a child Python process, on a
thread with a small stack, and the test reads what the child printed.

Citry also refuses a tag with more than 1,024 attributes, HTML with more
than 16 `<html>`, `<head>` or `<body>` start tags of one name, HTML that
keeps more than 512 elements open at once, and HTML that leaves formatting
tags such as `<b>` open or misnested so often that the parser would copy
more than 250,000 elements and attributes. html5ever, which builds the
tree, takes time that grows with the square of an attribute count, of a
repeated `<html>` or `<body>` count and of the nesting depth, and builds a
tree the size of the input times the length of its formatting list when
formatting tags are misnested
(`crates/citry_html_transform/src/html_limits.rs`). html5gum still reads
the whole input, so the long tags below still test the tokenizer.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from typing import Any

import pytest

# The child runs `body` on a thread with this stack, which is smaller than
# the 8 MiB of a main thread. `run_tokenizer` moves html5gum from it to a
# 2.25 MiB segment.
STACK_KIB = 512

# More attributes than html5gum 0.8.4 read on that 2.25 MiB segment.
MANY = 20000

# The limits in `html_limits.rs`; the Rust tests pin the constants.
ATTRIBUTE_LIMIT = 1024
DOCUMENT_TAG_LIMIT = 16
OPEN_ELEMENT_LIMIT = 512
REOPEN_LIMIT = 250_000

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
    # -I makes the child ignore `PYTHON*` variables, the user site directory
    # and the working directory, following the repository convention for
    # scripts that run code.
    done = subprocess.run(
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
    # Warnings are recorded so a warn mode shows anything it said.
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
def test_a_raising_output_check_refuses_a_spread_with_many_attributes(setting: str, mode: str, wording: str) -> None:
    result = _run_in_child(
        _SPREAD
        + f"""
result = outcome({MANY}, {setting}={mode!r})
"""
    )
    assert wording in result["raised"]
    assert f"more than {ATTRIBUTE_LIMIT} attributes" in result["raised"]


@pytest.mark.parametrize("setting", ["security_csp", "security_javascript"])
def test_a_warning_output_check_warns_and_still_returns_the_page(setting: str) -> None:
    result = _run_in_child(
        _SPREAD
        + f"""
result = outcome({MANY}, {setting}="warn")
"""
    )
    assert result["html_has_last"] is True
    assert len(result["warnings"]) == 1
    assert f"more than {ATTRIBUTE_LIMIT} attributes" in result["warnings"][0]


@pytest.mark.parametrize(
    ("setting", "mode"),
    [("security_csp", "strict"), ("security_javascript", "forbid")],
)
def test_a_spread_at_the_limit_passes_the_output_checks(setting: str, mode: str) -> None:
    result = _run_in_child(
        _SPREAD
        + f"""
result = (outcome({ATTRIBUTE_LIMIT}, {setting}={mode!r}), outcome({ATTRIBUTE_LIMIT + 1}, {setting}={mode!r}))
"""
    )
    at_limit, over = result
    assert at_limit == {"html_has_last": True, "warnings": []}
    assert f"more than {ATTRIBUTE_LIMIT} attributes" in over["raised"]


def test_a_hydrating_component_with_a_stray_quote_in_its_text_still_renders() -> None:
    # An independent review found this shape: the `="` in the text and the
    # values that end in `=` threw off a count of the attributes made before
    # the tokenizer ran. The `<body>` value makes the hydration check read
    # the written HTML with the tokenizer, which now refuses the long tag,
    # so the server leaves its HTML out and the page still renders.
    result = _run_in_child(
        f"""
from citry import Citry, Component

engine = Citry(autodiscover=False)
attributes = {{f"k{{i}}": "x=" for i in range({MANY})}}
attributes["data-X"] = "<body>"

class Card(Component):
    citry = engine
    template = '''
      <main>
        <span>{{{{ note }}}}</span>
        <p
          c-bind="attributes"
          :class="{{ open: open }}"
        >x</p>
      </main>
    '''

    def template_data(self, kwargs, slots):
        return {{"attributes": attributes, "note": '="'}}

    def js_data(self, kwargs, slots):
        return {{"open": True}}

html = Card().render().serialize()
result = {{"has_last": 'k{MANY - 1}' in html}}
"""
    )
    assert result == {"has_last": True}


def test_the_fragment_checks_refuse_a_tag_with_many_attributes() -> None:
    result = _run_in_child(
        f"""
from citry._vue.opaque_html import reject_cross_boundary_html
from citry_core.html_transform import (
    browser_fragment_matches_nodes,
    scan_output_html,
    static_html_node_count,
    validate_html_fragment_boundary,
)

# The stray `="` before the tag is the review's shape for `Markup` HTML.
html = '="<p' + "".join(f' a{{i}}="x="' for i in range({MANY})) + ">x</p>"
result = {{}}
for name, call in (
    ("validate", validate_html_fragment_boundary),
    ("scan", scan_output_html),
    ("count", static_html_node_count),
    ("reject", lambda html: reject_cross_boundary_html(html, origin="A Markup value")),
):
    try:
        call(html)
        result[name] = "accepted"
    except ValueError as error:
        result[name] = str(error)
result["nodes"] = browser_fragment_matches_nodes(html, "div", [("open", "p", []), ("close", "p", [])])
"""
    )
    limit = f"more than {ATTRIBUTE_LIMIT} attributes; Citry reads at most {ATTRIBUTE_LIMIT} on one tag"
    assert result["validate"] == f"opaque HTML has a tag with {limit}"
    assert result["scan"] == f"HTML has a tag with {limit}"
    assert result["count"] == f"HTML has a tag with {limit}"
    assert result["reject"].startswith(f"A Markup value is not accepted. HTML has a tag with {limit}.")
    assert result["reject"].endswith("Spread the attributes over several elements.")
    assert result["nodes"] is False


def test_repeated_document_tags_are_refused_with_their_name() -> None:
    result = _run_in_child(
        f"""
from citry._vue.opaque_html import reject_cross_boundary_html
from citry_core.html_transform import scan_output_html, static_html_node_count

result = {{}}
for name in ("html", "head", "body"):
    at_limit = f"<{{name}}>" * {DOCUMENT_TAG_LIMIT}
    over = f"<{{name}}>" * {DOCUMENT_TAG_LIMIT + 1}
    scan_output_html(at_limit)
    static_html_node_count(at_limit)
    try:
        reject_cross_boundary_html(over, origin="The <c-raw> block at line 1, column 1")
    except ValueError as error:
        result[name] = str(error)
"""
    )
    for name in ("html", "head", "body"):
        assert result[name] == (
            f"The <c-raw> block at line 1, column 1 is not accepted. HTML has more than"
            f" {DOCUMENT_TAG_LIMIT} <{name}> start tags; Citry reads at most {DOCUMENT_TAG_LIMIT} of each. Inside"
            " an interactive component, Vue inserts this HTML as one block, and Citry reads it first to"
            " check it. A fragment needs no <html>, <head> or <body> tag, so remove them."
        )


def test_elements_nested_too_deep_are_refused_with_the_limit_named() -> None:
    result = _run_in_child(
        f"""
from citry._vue.opaque_html import reject_cross_boundary_html

depth = {OPEN_ELEMENT_LIMIT + 1}
html = "<div>" * depth + "</div>" * depth
try:
    reject_cross_boundary_html(html, origin="A Markup value")
    result = "accepted"
except ValueError as error:
    result = str(error)
"""
    )
    assert result == (
        "A Markup value is not accepted. HTML keeps more than"
        f" {OPEN_ELEMENT_LIMIT} elements open at once; Citry reads at most {OPEN_ELEMENT_LIMIT}. Inside an"
        " interactive component, Vue inserts this HTML as one block, and Citry reads it first to check it."
        " Nest the elements less deeply."
    )


def test_formatting_tags_that_the_parser_reopens_too_often_are_refused_with_the_limit_named() -> None:
    # Each `<div><b a="i"></div>` leaves a `<b>` the parser reopens at the
    # next text or tag, and each `<div>x</div>` after them reopens all of
    # the 25 that are waiting.
    result = _run_in_child(
        """
from citry._vue.opaque_html import reject_cross_boundary_html

html = "".join(f'<div><b a="{i}"></div>' for i in range(25)) + "<div>x</div>" * 6000
try:
    reject_cross_boundary_html(html, origin="A Markup value")
    result = "accepted"
except ValueError as error:
    result = str(error)
"""
    )
    assert result == (
        "A Markup value is not accepted. HTML leaves formatting tags such as <b> and <i> open or misnested"
        f" so often that the parser would copy more than {REOPEN_LIMIT} elements and attributes; Citry reads"
        f" at most {REOPEN_LIMIT}. Inside an interactive component, Vue inserts this HTML as one block, and"
        " Citry reads it first to check it. Close each formatting tag such as <b>, <i> or <a> inside the element"
        " where it was opened, so the browser does not have to reopen it."
    )


def test_a_tag_hidden_from_a_document_parse_is_refused_where_vue_parses_it() -> None:
    # Inside `<template>`, where Vue parses the block, a `<col>` makes the
    # parser ignore `<style>`, so the wide tag after it is a real tag there.
    result = _run_in_child(
        f"""
from citry._vue.opaque_html import reject_cross_boundary_html

html = "<col><style><p" + "".join(f" a{{i}}" for i in range({MANY})) + "></style>"
try:
    reject_cross_boundary_html(html, origin="A Markup value")
    result = "accepted"
except ValueError as error:
    result = str(error)
"""
    )
    assert result.startswith(f"A Markup value is not accepted. HTML has a tag with more than {ATTRIBUTE_LIMIT}")
    assert result.endswith("Spread the attributes over several elements.")


@pytest.mark.parametrize("markers", [1, 2])
def test_a_root_tag_near_the_limit_is_refused_with_the_markers_named(markers: int) -> None:
    # The root has room for one attribute fewer than the markers need.
    result = _run_in_child(
        f"""
from citry._vue.opaque_html import mark_opaque_html, reject_cross_boundary_html

html = "<p" + "".join(f" a{{i}}" for i in range({ATTRIBUTE_LIMIT - markers + 1})) + ">x</p>"
reject_cross_boundary_html(html, origin="A Markup value")
try:
    mark_opaque_html(html, tuple((f"data-cid-m{{i}}", True) for i in range({markers})))
    result = "accepted"
except ValueError as error:
    result = str(error)
"""
    )
    assert result.startswith(f"HTML has a tag with more than {ATTRIBUTE_LIMIT} attributes")
    assert f"Citry adds {markers} attribute(s)" in result
    assert result.endswith("so a root element can hold one attribute fewer for each marker.")
