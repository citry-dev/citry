"""
A tag with a very long run of attributes is read, and the process keeps running.

The HTML reader behind the output checks, the fragment check for `Markup`
and `<c-raw>`, and the hydration checks is html5gum. Upstream html5gum 0.8.4
nested a few calls for each attribute written as `name="value"`, so one tag
with about 50,000 of them overflowed the 8 MiB main-thread stack in a release
build and killed the whole process (about 3,000 on a 512 KiB thread). Citry
builds a patched copy (`third_party/rust/html5gum`) that does not nest. A
stack overflow cannot be caught, so every case runs in a child Python
process, on a thread with a small stack, and the test reads what the child
printed.
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

# More attributes than upstream html5gum read on that 2.25 MiB segment.
MANY = 20000

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
        html = render(count, **settings)
    return {"html_has_last": f'k{count - 1}="v"' in html, "warnings": [str(w.message) for w in caught]}
"""


@pytest.mark.parametrize(
    ("setting", "mode"),
    [
        ("security_csp", "strict"),
        ("security_csp", "warn"),
        ("security_javascript", "forbid"),
        ("security_javascript", "warn"),
    ],
)
def test_the_output_checks_read_a_spread_with_many_attributes(setting: str, mode: str) -> None:
    result = _run_in_child(
        _SPREAD
        + f"""
result = outcome({MANY}, {setting}={mode!r})
"""
    )
    assert result == {"html_has_last": True, "warnings": []}


def test_a_hydrating_component_with_a_stray_quote_in_its_text_still_renders() -> None:
    # An independent review found this shape: the `="` in the text and the
    # values that end in `=` threw off a count of the attributes made before
    # the tokenizer ran. The `<body>` value makes the hydration check read
    # the written HTML with the tokenizer.
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
result = {{"has_last": 'k{MANY - 1}="x="' in html, "has_note": "=&#34;" in html or '="</span>' in html}}
"""
    )
    assert result == {"has_last": True, "has_note": True}


def test_the_fragment_checks_read_a_tag_with_many_attributes() -> None:
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
validate_html_fragment_boundary(html)
reject_cross_boundary_html(html, origin="A Markup value")
result = {{
    "attributes": len(scan_output_html(html)[0]["attributes"]),
    "nodes": browser_fragment_matches_nodes(html, "div", [("open", "p", []), ("close", "p", [])]),
    "count": static_html_node_count(html),
}}
"""
    )
    # The expected nodes leave out the attributes, so the comparison reads
    # the whole tag and answers that it does not match.
    assert result == {"attributes": MANY, "nodes": False, "count": 2}
