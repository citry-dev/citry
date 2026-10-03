"""
Browser proof that Vue adopts server HTML written for hydration and ends with the DOM a client mount builds.

With the default settings the server writes the Vue host's contents as
Vue's first client render would build them, and leaves a shell
(``data-allow-mismatch="children"``) wherever a value is known only in the
browser; the runtime removes the HTML the shell carries before Vue builds
it. Each test renders one page twice: once for a plain client mount
(the reference DOM) and once for hydration. Hydration must report no
mismatch, keep every element the server wrote, and end with the same DOM and
the same behavior as the client mount.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from citry import Citry, Component
from citry._vue.serialization import hydration_admission

pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.e2e

# Walk the Vue host in document order and describe what a user can observe.
# Two things differ by design and are left out: the shell marker
# (data-allow-mismatch, only on the hydrated side) and data-cid-* ids. A style
# is described by the declarations the browser read from it, because the
# server writes the text Vue's server renderer writes while a client mount
# leaves the browser's own spelling of the same declarations.
# Empty text nodes are skipped: a client mount marks where a list or fragment
# starts and ends with empty text nodes, while hydration keeps the server's
# comment nodes in those places.
_HOST_FACTS_JS = """() => {
  const host = document.querySelector('[id^="citry-vue-"]');
  const walker = document.createTreeWalker(host, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
  const facts = [];
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    if (node.nodeType === Node.TEXT_NODE) {
      if (node.data !== '') facts.push({text: node.data});
      continue;
    }
    facts.push({
      tag: node.tagName.toLowerCase(),
      attrs: [...node.attributes]
        .filter(attr => attr.name !== 'data-allow-mismatch' && !attr.name.startsWith('data-cid-'))
        .map(attr => [attr.name, attr.name === 'style' ? node.style.cssText : attr.value])
        .sort(([a], [b]) => a.localeCompare(b)),
      checked: 'checked' in node ? node.checked : null,
      value: 'value' in node && typeof node.value === 'string' ? node.value : null,
      display: getComputedStyle(node).display,
    });
  }
  return facts;
}"""

# Remember what the server wrote before the app starts, so the test can later
# prove hydration kept those exact nodes instead of building new ones. The
# Citry HTML inside a shell is only shown until the runtime removes it, so it
# is kept apart.
_CAPTURE_SCRIPT = """<script>(() => {
  const host = document.querySelector('[id^="citry-vue-"]');
  const inShell = element => element.parentElement.closest('[data-allow-mismatch]') !== null;
  window.__serverElements = [...host.querySelectorAll('*')].filter(element => !inShell(element));
  window.__servedShellContents = [...host.querySelectorAll('[data-allow-mismatch] > *')];
})();</script>"""

_ADOPTION_JS = """() => {
  const host = document.querySelector('[id^="citry-vue-"]');
  return {
    probe: window.__citryHydrationReport,
    serverElementCount: window.__serverElements.length,
    allAdopted: (() => {
      // Each server element must still be in the host and in the same order;
      // Vue may add elements between them only inside shells.
      const current = [...host.querySelectorAll('*')];
      const positions = window.__serverElements.map(element => current.indexOf(element));
      return positions.every((position, index) => position >= 0 && (index === 0 || position > positions[index - 1]));
    })(),
    shellContentsRemoved: window.__servedShellContents.every(element => !element.isConnected),
  };
}"""


def _with_capture(html: str) -> str:
    """Insert the capture script right before the script tag that starts the app."""
    bootstrap_tag = html.rfind("<script", 0, html.index('<script type="application/json" data-citry-vue-document='))
    return html[:bootstrap_tag] + _CAPTURE_SCRIPT + html[bootstrap_tag:]


def _open(page: Any, html: str, serve_document: Any) -> tuple[list[str], list[str]]:
    """Load one page, wait until its app is ready, and return its page errors and console warnings and errors."""
    faults: list[str] = []
    console: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: console.append(message.text) if message.type in {"warning", "error"} else None)
    # The listener must exist before the runtime dispatches citry:ready.
    page.add_init_script(
        "window.__citryReadyApps = [];"
        "document.addEventListener('citry:ready', event => window.__citryReadyApps.push(event.detail.appId));"
    )
    page.goto(serve_document(html))
    page.wait_for_function("window.__citryReadyApps?.length === 1")
    return faults, console


def _compare_with_client_mount(
    element: Any,
    *,
    page: Any,
    browser: Any,
    serve_document: Any,
    monkeypatch: Any,
    interact: Any = None,
) -> dict[str, Any]:
    """
    Hydrate one render and check it against a client mount of the same render.

    Returns the admission and the adoption facts so each test can add its own
    expectations. ``interact`` runs the same user actions on both pages and
    returns what they observed; both pages must observe the same thing.
    """
    rendered = element.render()

    # The client mount of the same render is the reference DOM and behavior.
    control_html = rendered.serialize(ssr=False)
    assert '"hydrate":true' not in control_html
    control = browser.new_page()
    control_faults, control_console = _open(control, control_html, serve_document)
    control_facts = control.evaluate(_HOST_FACTS_JS)
    control_observed = interact(control) if interact else None
    control_after = control.evaluate(_HOST_FACTS_JS)
    control.close()
    assert control_faults == [], control_faults
    assert control_console == [], control_console

    # This browser flag makes the runtime publish window.__citryHydrationReport
    # when the first hydrating mount finishes.
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    hydrated_html = rendered.serialize(ssr=True)
    assert '"hydrate":true' in hydrated_html
    admission = hydration_admission(rendered)
    assert admission is not None
    assert admission.hydrated, admission
    faults, console = _open(page, _with_capture(hydrated_html), serve_document)
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    adoption = page.evaluate(_ADOPTION_JS)

    probe = adoption["probe"]
    assert probe["mountError"] is None, probe
    assert probe["mismatchCount"] == 0, probe
    assert probe["replacedElementCount"] == 0, probe
    # Every element the server wrote, shells included, is the node Vue kept.
    assert adoption["allAdopted"] is True, adoption
    assert probe["reusedElementCount"] == adoption["serverElementCount"] == admission.element_count, (
        adoption,
        admission,
    )
    assert adoption["shellContentsRemoved"] is True
    assert page.evaluate(_HOST_FACTS_JS) == control_facts
    initial_toggle = page.evaluate(
        """() => { const toggle = document.querySelector('#toggle');
          return toggle && [toggle.getAttribute('aria-expanded'),
            getComputedStyle(document.querySelector('#panel')).display]; }"""
    )
    if interact:
        assert interact(page) == control_observed
        assert page.evaluate(_HOST_FACTS_JS) == control_after
    assert faults == [], faults
    assert console == [], console
    return {"admission": admission, "adoption": adoption, "html": hydrated_html, "initial_toggle": initial_toggle}


def _rows_board(engine: Citry) -> type[Component]:
    """Build a small board: rows of ``simple="vue"`` components plus a sibling that needs a shell."""

    class Row(Component):
        citry = engine
        simple = "vue"

        class Kwargs:
            row: dict

        @staticmethod
        def template_data(kwargs: Any, slots: Any) -> dict[str, Any]:  # noqa: ARG004 - the simple='vue' contract fixes this signature
            return {"row": kwargs.row, "row_attrs": kwargs.row["attrs"]}

        template = """
<article
  c-bind="row_attrs"
  data-row-kind="output"
>
  <h4>{{ row['title'] }}</h4>
  <form class="row-form">
    <label>Note <textarea data-note>{{ row['note'] }}</textarea>
    </label>
    <label>
      <input type="checkbox" c-checked="row['done']"> Done</label>
  </form>
  <details>
    <summary>More</summary>
    <p>{{ row['more'] }}</p>
  </details>
  <button
    type="button"
    @click="open = !open"
    :aria-expanded="open"
  >
    <h3>Details</h3>
  </button>
  <div v-show="open">
    <p>{{ row['more'] }}</p>
  </div>
</article>
"""
        js = """
$component({data(){return {open: true};}});
"""

    class Counter(Component):
        citry = engine
        # The paragraph depends on browser state, so the server cannot know
        # whether it exists and writes the aside as a shell.
        template = """
<aside id="side">
  <p v-if="count > 0" id="count-line">Clicked <span v-text="count"></span> times</p>
  <button
    type="button"
    id="counter"
    @click="count += 1"
  >Count</button>
</aside>
"""
        js = """
$component({data(){return {count: 0};}});
"""

    class Board(Component):
        citry = engine

        class Kwargs:
            rows: list

        template = """
<main>
  <section id="rows">
    <h2>Rows</h2>
    <c-Row
      c-for="row in rows"
      #c-key="row['id']"
      c-row="row"
    />
  </section>
  <form id="filter">
    <label for="query">Filter</label>
    <input
      id="query"
      name="query"
      value="abc"
    >
  </form>
  <c-Counter />
</main>
"""
        js = """
$component({});
"""

    return Board


# Rows differ in which attributes their spread carries, and in text that
# needs escaping, so one compiled render has to write each row differently.
_ROWS = [
    {
        "id": "r1",
        "title": "First",
        "note": "n1",
        "more": "m1",
        "done": True,
        "attrs": {"id": "row-1", "data-row-id": "r1", "data-source-id": "s1"},
    },
    {
        "id": "r2",
        "title": "Second & <b>",
        "note": "n2 & <x>",
        "more": "m2",
        "done": False,
        "attrs": {"id": "row-2", "data-row-id": "r2"},
    },
    {
        "id": "r3",
        "title": "Third",
        "note": "",
        "more": "m3",
        "done": True,
        "attrs": {"id": "row-3", "data-row-id": "r3", "data-extra": "x", "title": 't "q"'},
    },
]


def _board_interactions(page: Any) -> dict[str, Any]:
    """Toggle one row and click the counter twice, reporting what a user would see."""
    toggle = page.locator("#row-2 > button")
    toggle.click()
    row = page.evaluate(
        """() => [document.querySelector('#row-2 > button').getAttribute('aria-expanded'),
          getComputedStyle(document.querySelector('#row-2 > div')).display]"""
    )
    page.click("#counter")
    page.click("#counter")
    page.wait_for_function("document.querySelector('#count-line')?.textContent === 'Clicked 2 times'")
    return {"row": row, "count": page.text_content("#count-line")}


def test_rows_region_hydrates_with_client_mount_parity(
    page: Any, browser: Any, serve_document: Any, monkeypatch: Any
) -> None:
    engine = Citry(autodiscover=False)
    board = _rows_board(engine)

    result = _compare_with_client_mount(
        board(rows=_ROWS),
        page=page,
        browser=browser,
        serve_document=serve_document,
        monkeypatch=monkeypatch,
        interact=_board_interactions,
    )

    admission = result["admission"]
    # Only the counter's aside needs the browser; every row is adopted as written.
    assert admission.shell_count == 1, admission
    assert [(item.code, item.outcome, item.shell_tag) for item in admission.declines] == [
        ("browser-condition", "shell", "aside")
    ]
    assert re.search(r'<aside id="side" data-allow-mismatch="children">.*?</aside>', result["html"])
    assert (
        '<article data-extra="x" data-row-id="r3" data-row-kind="output" id="row-3" title="t &quot;q&quot;">'
        in (result["html"])
    )
    # A row toggle collapses only that row, and the counter built inside the shell reacts.
    rows = page.evaluate(
        """() => [...document.querySelectorAll('#rows article')].map(row =>
          [row.id, row.querySelector(':scope > button').getAttribute('aria-expanded'),
           getComputedStyle(row.querySelector(':scope > div')).display])"""
    )
    assert rows == [["row-1", "true", "block"], ["row-2", "false", "none"], ["row-3", "true", "block"]]
    assert page.text_content("#count-line") == "Clicked 2 times"


def test_shell_without_its_marker_reports_a_mismatch(page: Any, serve_document: Any) -> None:
    # Negative control: the probe must be able to fail. Without the marker,
    # Vue finds an element with fewer children than it expects.
    engine = Citry(autodiscover=False)
    rendered = _rows_board(engine)(rows=_ROWS).render()
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    hydrated_html = rendered.serialize(ssr=True)
    unmarked = hydrated_html.replace(' data-allow-mismatch="children"', "", 1)
    assert unmarked != hydrated_html

    _open(page, unmarked, serve_document)
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    probe = page.evaluate("window.__citryHydrationReport")
    assert probe["mismatchCount"] >= 1, probe


def _input_cases(engine: Citry) -> dict[str, Any]:
    """Return one page per input shape, each built fresh on ``engine``."""

    class Items(Component):
        citry = engine

        class Kwargs:
            items: list

        template = """
<main>
  <ul>
    <li c-for="item in items">{{ item }}</li>
  </ul>
  <p>after</p>
</main>
"""
        js = """
$component({});
"""

    class Card(Component):
        citry = engine
        template = """
<section>
  <h2>Card</h2>
  <c-slot />
</section>
"""
        js = """
$component({});
"""

    class EmptySlot(Component):
        citry = engine
        template = """
<main>
  <c-Card />
  <p>after</p>
</main>
"""
        js = """
$component({});
"""

    class EmptyIf(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"flag": False}

        template = """
<main>
  <c-if cond="flag">
    <p>shown</p>
  </c-if>
  <p>after</p>
</main>
"""
        js = """
$component({});
"""

    class Nothing(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"show": False}

        template = """
<c-if cond="show">
  <p>never</p>
</c-if>
"""
        js = """
$component({});
"""

    class RendersNothing(Component):
        citry = engine
        template = """
<main>
  <c-Nothing />
  <p>after</p>
</main>
"""
        js = """
$component({});
"""

    class Entities(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"value": "a & b \"c\" <d> 'e' \u00a0"}

        template = """
<main>
  <p title="a &amp; b &quot;c&quot; &lt;d&gt; &#39;e&#39;">x &amp; y &lt; z &gt; w&nbsp;&copy; &#x1F600;</p>
  <p
    c-title="value"
    c-data-value="value"
  >{{ value }}</p>
</main>
"""
        js = """
$component({});
"""

    class Voids(Component):
        citry = engine
        template = """
<main>
  <p>a<br>b<wbr>c</p>
  <img alt="pic" src="data:,">
  <hr>
  <input name="text" value="typed">
  <input type="checkbox" checked>
  <label>One <input
    type="radio"
    name="choice"
    value="1"
    checked
  ></label>
</main>
"""
        js = """
$component({});
"""

    class Spread(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {
                "rows": [
                    {"data-a": "1"},
                    {"data-b": "2", "title": "t"},
                    {},
                    {"aria-label": "labelled", "class": "x y"},
                ]
            }

        template = """
<ul>
  <li c-for="attrs in rows" c-bind="attrs">row</li>
</ul>
"""
        js = """
$component({});
"""

    class PythonFlags(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"yes": True, "no": False, "none": None}

        template = """
<main>
  <input type="checkbox" c-checked="yes">
  <input type="checkbox" c-checked="no">
  <input type="checkbox" c-checked="none">
  <button c-disabled="yes">a</button>
  <button c-disabled="no">b</button>
  <button c-disabled="none">c</button>
  <p c-hidden="yes">hidden</p>
  <p c-hidden="no">shown</p>
  <p
    c-data-flag="yes"
    c-aria-expanded="yes"
  >x</p>
  <p
    c-data-flag="no"
    c-aria-expanded="no"
  >y</p>
  <p
    c-data-flag="none"
    c-aria-expanded="none"
  >z</p>
</main>
"""
        js = """
$component({});
"""

    class Toggle(Component):
        citry = engine

        class Kwargs:
            open: bool

        class JsData:
            open: bool

        def js_data(self, kwargs: Any, slots: Any) -> Any:
            return self.JsData(open=kwargs.open)

        # The initial `shown` exists only in the browser, so the server leaves
        # aria-expanded and v-show for hydration to set.
        template = """
<main>
  <button
    type="button"
    id="toggle"
    @click="shown = !shown"
    :aria-expanded="shown"
  >Toggle</button>
  <div id="panel" v-show="shown">panel</div>
</main>
"""
        js = """
$component({data(){return {shown: this.open};}});
"""

    class VTextValues(Component):
        citry = engine

        class JsData:
            label: str
            count: int
            ratio: float
            info: dict
            missing: str | None
            tags: list

        def js_data(self, kwargs: Any, slots: Any) -> Any:
            return self.JsData(
                label="Tom & <Jerry>",
                count=3,
                ratio=0.5,
                info={"a": 1},
                missing=None,
                tags=["x", "y"],
            )

        # The server writes the text it can print exactly as Vue does; the
        # fraction, the object and the browser-only `later` stay empty for
        # hydration to set, and authored children stay the server's text.
        template = """
<main>
  <p v-text="label"></p>
  <p v-text="count"></p>
  <p v-text="ratio"></p>
  <p v-text="info"></p>
  <p v-text="missing"></p>
  <p v-text="later"></p>
  <p v-text="label">Loading...</p>
  <ul>
    <li v-for="tag in tags" v-text="tag"></li>
  </ul>
</main>
"""
        js = """
$component({data(){return {later: 'from the browser'};}});
"""

    return {
        "loop-empty": Items(items=[]),
        "loop-one": Items(items=["only"]),
        "loop-many": Items(items=["a", "b", "c", "d"]),
        "slot-empty": EmptySlot(),
        "if-empty": EmptyIf(),
        "component-renders-nothing": RendersNothing(),
        "entities": Entities(),
        "void-elements": Voids(),
        "spread-varying-names": Spread(),
        "python-true-false-none": PythonFlags(),
        "vue-state-true": Toggle(open=True),
        "vue-state-false": Toggle(open=False),
        "v-text-values": VTextValues(),
    }


def _toggle_twice(page: Any) -> list[Any]:
    """Click the toggle twice and report aria-expanded and panel display after each click."""
    seen = []
    for _ in range(2):
        page.click("#toggle")
        seen.append(
            page.evaluate(
                """() => [document.querySelector('#toggle').getAttribute('aria-expanded'),
                  getComputedStyle(document.querySelector('#panel')).display]"""
            )
        )
    return seen


_INPUT_CASE_NAMES = [
    "loop-empty",
    "loop-one",
    "loop-many",
    "slot-empty",
    "if-empty",
    "component-renders-nothing",
    "entities",
    "void-elements",
    "spread-varying-names",
    "python-true-false-none",
    "vue-state-true",
    "vue-state-false",
    "v-text-values",
]


@pytest.mark.parametrize("case", _INPUT_CASE_NAMES)
def test_input_shape_hydrates_with_client_mount_parity(
    case: str, page: Any, browser: Any, serve_document: Any, monkeypatch: Any
) -> None:
    engine = Citry(autodiscover=False)
    cases = _input_cases(engine)
    # The parametrize list names every case once, so a new case cannot be skipped.
    assert set(cases) == set(_INPUT_CASE_NAMES)
    element = cases[case]
    result = _compare_with_client_mount(
        element,
        page=page,
        browser=browser,
        serve_document=serve_document,
        monkeypatch=monkeypatch,
        interact=_toggle_twice if case.startswith("vue-state-") else None,
    )
    # Every browser-only value here is one hydration sets itself (aria-expanded,
    # v-show), so the server writes no shell.
    assert result["admission"].shell_count == 0, result["admission"]
    assert result["admission"].declines == ()
    if case == "v-text-values":
        # The first paint already shows the text the server knows.
        assert (
            "<main><p>Tom &amp; &lt;Jerry&gt;</p><p>3</p><p></p><p></p><p></p><p></p><p>Loading...</p>"
            "<ul><!--[--><li>x</li><li>y</li><!--]--></ul></main>"
        ) in result["html"]
    if case.startswith("vue-state-"):
        # Guard against both cases silently showing the same initial state:
        # the browser-side initial value must reach the hydrated page.
        expected = ["true", "block"] if case == "vue-state-true" else ["false", "none"]
        assert result["initial_toggle"] == expected


def _merged_bindings_board(engine: Citry) -> type[Component]:
    """Build a page whose elements join a bound class or style with a static or Python one."""

    class Board(Component):
        citry = engine
        template = """
<main>
  <p
    id="known"
    class="card"
    c-class="{'card--python': True}"
    :class="{ 'card--done': done }"
    c-style="'color: red; font-weight: normal'"
    :style="{ fontWeight: weight }"
  >known</p>
  <ul id="items">
    <li
      v-for="item in items"
      :key="item.id"
      class="item"
      :class="{ 'item--dragging': dragging === item.id }"
      style="margin: 0"
      :style="{ opacity: dragging === item.id ? 0.5 : 1 }"
      v-show="item.shown"
      @click="dragging = item.id"
      v-text="item.label"
    ></li>
  </ul>
  <button
    type="button"
    id="reverse"
    @click="items.reverse()"
  >Reverse</button>
</main>
"""

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {
                "done": True,
                "weight": "bold",
                "items": [
                    {"id": 1, "label": "one", "shown": True},
                    {"id": 2, "label": "two", "shown": False},
                    {"id": 3, "label": "three", "shown": True},
                ],
            }

        js = """
$component({data(){return {dragging: null};}});
"""

    return Board


def _drag_and_reverse(page: Any) -> list[Any]:
    """Mark the first item, reverse the list, and report each item's classes and style."""
    page.click("#items > li:first-child")
    page.click("#reverse")
    return page.evaluate(
        """() => [...document.querySelectorAll('#items > li')].map(item =>
          [item.textContent, item.className, item.style.opacity, getComputedStyle(item).display])"""
    )


def test_bound_class_and_style_merge_with_static_and_python_values_on_hydration(
    page: Any, browser: Any, serve_document: Any, monkeypatch: Any
) -> None:
    engine = Citry(autodiscover=False)

    result = _compare_with_client_mount(
        _merged_bindings_board(engine)(),
        page=page,
        browser=browser,
        serve_document=serve_document,
        monkeypatch=monkeypatch,
        interact=_drag_and_reverse,
    )

    # The paragraph's values are all known to the server, so it is adopted as
    # written, with every class and the bound style after Python's.
    assert (
        '<p id="known" class="card card--python card--done" '
        'style="color:red;font-weight:normal;font-weight:bold;">known</p>'
    ) in result["html"]
    # `dragging` lives in data(), so Vue builds the list, whose served HTML
    # already showed each item's static class and style.
    assert [(item.code, item.shell_tag) for item in result["admission"].declines] == [("browser-value", "ul")]
    served = page.evaluate("window.__servedShellContents.map(item => [item.className, item.getAttribute('style')])")
    assert served == [["item", "margin:0;"], ["item", "margin:0;display: none;"], ["item", "margin:0;"]]
    # Each item keeps its own key: after reversing, the marked item moved with
    # its classes, and the hidden item stayed hidden.
    assert page.evaluate(
        """() => [...document.querySelectorAll('#items > li')].map(item =>
          [item.textContent, item.className, getComputedStyle(item).display])"""
    ) == [
        ["three", "item", "list-item"],
        ["two", "item", "none"],
        ["one", "item item--dragging", "list-item"],
    ]
