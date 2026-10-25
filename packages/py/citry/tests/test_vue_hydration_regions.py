"""
Server HTML that Vue adopts on hydration: marked shells, Vue's comment anchors, and decline reasons.

With hydration on, the server runs each component's compiled Vue render over
the same prepared data the browser reads and writes the Vue host's contents
exactly as Vue's first client render builds them. A part that depends on
values only the browser knows turns its nearest enclosing element into a
shell marked ``data-allow-mismatch="children"``, whose children Vue builds in
the browser. The shell carries Citry's HTML for those children until the
browser runtime removes it right before Vue hydrates. These tests lock the
written host HTML and the recorded decision.
"""

import re
from dataclasses import replace
from typing import Any

import pytest

from citry import Citry, Component, Markup
from citry._vue.compiler import NativeCompiler
from citry._vue.direct_capture import _prepared_root_markers, _source_attribute_reads_instance
from citry._vue.serialization import HydrationAdmission, VueSerializationPlan, hydration_admission
from citry.ext.dependencies.types import Script
from citry_core import _rust


def _host(html: str) -> str:
    """Return the Vue host's contents as written by the server."""
    match = re.search(r'<div id="citry-vue-[^"]+">(.*?)</div><script', html, re.DOTALL)
    assert match is not None, html[:500]
    return match.group(1)


def _admission(render: object) -> HydrationAdmission:
    admission = hydration_admission(render)  # type: ignore[arg-type]
    assert admission is not None
    return admission


def _declines(admission: HydrationAdmission) -> list[tuple[object, ...]]:
    # The component type key carries a hash suffix, so compare its class name part.
    return [
        (item.code, item.detail, item.outcome, item.shell_tag, (item.component or "").rsplit("_", 1)[0])
        for item in admission.declines
    ]


def _without_shell_contents(host: str) -> str:
    # Vue ignores mismatches under a marked element, and the runtime empties
    # each one before Vue hydrates, so only the rest is what Vue adopts.
    return re.sub(
        r'(<([a-z0-9]+)\b[^>]*data-allow-mismatch="children"[^>]*>).*?(</\2>)', r"\1\3", host, flags=re.DOTALL
    )


def _hydrated_host(page: type[Component], **kwargs: object) -> tuple[str, HydrationAdmission]:
    """Render and serialize one page that must hydrate, returning its host and decision."""
    rendered = page(**kwargs).render()
    html = rendered.serialize()
    assert '"hydrate":true' in html
    admission = _admission(rendered)
    assert admission.hydrated
    assert admission.reason is None
    return _host(html), admission


def test_browser_only_condition_is_written_as_a_marked_shell_beside_adopted_content() -> None:
    engine = Citry(autodiscover=False)

    class Board(Component):
        citry = engine
        template = """
<main><section class="rows"><h2>Rows</h2><p>one</p></section><aside id="side"><p v-if="open">x</p></aside></main>
"""
        js = "$component({data(){return {open: true};}});"

    host, admission = _hydrated_host(Board)

    # The shell shows every branch of a condition only the browser can test,
    # until the runtime empties it.
    assert host == (
        '<main><section class="rows"><h2>Rows</h2><p>one</p></section>'
        '<aside id="side" data-allow-mismatch="children"><p>x</p></aside></main>'
    )
    # main, section, h2, p, and the aside shell itself.
    assert admission.element_count == 5
    assert admission.shell_count == 1
    assert _declines(admission) == [("browser-condition", "v-if", "shell", "aside", "Board")]
    assert [item.shell_content for item in admission.declines] == [True]


def test_browser_only_text_is_left_for_vue_to_patch_during_hydration() -> None:
    engine = Citry(autodiscover=False)

    class Label(Component):
        citry = engine
        template = """
<main><span v-text="msg"></span><p>kept</p></main>
"""
        js = "$component({data(){return {msg: 'hi'};}});"

    host, admission = _hydrated_host(Label)

    # `v-text` compiles to a dynamic `textContent` prop, which Vue sets
    # itself while hydrating, so the span is written empty and unmarked.
    assert host == "<main><span></span><p>kept</p></main>"
    assert admission.shell_count == 0
    assert admission.declines == ()


def test_v_text_the_server_knows_is_written_for_the_first_paint() -> None:
    engine = Citry(autodiscover=False)

    class Labels(Component):
        citry = engine
        template = """
<main>
  <p v-text="label"></p>
  <p v-text="count"></p>
  <p v-text="ratio"></p>
  <p v-text="info"></p>
  <p v-text="missing"></p>
  <p v-text="label">Loading...</p>
  <ul><li v-for="tag in tags" v-text="tag"></li></ul>
</main>
"""
        js = "$component({});"

        def js_data(self, kwargs, slots):
            return {
                "label": "Tom & <Jerry>",
                "count": 3,
                "ratio": 0.5,
                "info": {"a": 1},
                "missing": None,
                "tags": ["x", "y"],
            }

    host, admission = _hydrated_host(Labels)

    # Text Vue prints the same way is written escaped. A fraction or an
    # object would need Vue's own formatting, so hydration sets those; an
    # element with authored children keeps them, because hydration compares
    # them before it sets the text.
    assert host == (
        "<main><p>Tom &amp; &lt;Jerry&gt;</p><p>3</p><p></p><p></p><p></p><p>Loading...</p>"
        "<ul><!--[--><li>x</li><li>y</li><!--]--></ul></main>"
    )
    assert admission.shell_count == 0
    assert admission.declines == ()


def test_element_containing_adopted_content_is_never_marked() -> None:
    engine = Citry(autodiscover=False)

    class Mixed(Component):
        citry = engine
        template = """
<main><p>adopted on its own</p><template v-if="open"><b>x</b></template></main>
"""
        js = "$component({data(){return {open: true};}});"

    host, admission = _hydrated_host(Mixed)

    # No element separates the browser-only branch from <p>, so <main> is
    # the shell and <p> is built in the browser too. The shell carries both
    # as Citry's HTML, which the runtime removes before Vue hydrates.
    assert host == '<main data-allow-mismatch="children"><p>adopted on its own</p><b>x</b></main>'
    assert _without_shell_contents(host) == '<main data-allow-mismatch="children"></main>'
    assert _declines(admission) == [("browser-condition", "v-if", "shell", "main", "Mixed")]


def test_component_with_two_roots_hydrates_between_fragment_anchors() -> None:
    engine = Citry(autodiscover=False)

    class TwoRoots(Component):
        citry = engine
        template = """
<p>a</p><p>b</p>
"""

    class Page(Component):
        citry = engine
        template = """
<main><section><c-TwoRoots /></section><div>kept</div></main>
"""
        js = "$component({});"

    host, admission = _hydrated_host(Page)

    assert host == "<main><section><!--[--><p>a</p><p>b</p><!--]--></section><div>kept</div></main>"
    assert admission.declines == ()


def test_shell_drops_a_child_component_and_one_render_feeds_every_serialization() -> None:
    engine = Citry(autodiscover=False)
    calls = 0

    class Child(Component):
        citry = engine
        template = """
<em>child</em>
"""
        js = "$component({});"

        def template_data(self, kwargs, slots):
            nonlocal calls
            calls += 1
            return {}

    class Page(Component):
        citry = engine
        template = """
<main>
  <aside id="a">
    <c-Child />
    <p v-if="open">x</p>
  </aside>
  <p>tail  text</p>
</main>
"""
        js = "$component({data(){return {open: true};}});"

    rendered = Page().render()
    first = rendered.serialize()
    second = rendered.serialize()

    # The child component inside the shell is written only as the shell's
    # Citry HTML, which Vue does not adopt. Outside the shell, text is
    # written the way Vue's compiler condenses it.
    assert _host(first) == (
        '<main><aside id="a" data-allow-mismatch="children"><em>child</em><p>x</p></aside><p>tail text</p></main>'
    )
    assert "<em>" not in _without_shell_contents(_host(first))
    # One render feeds every serialization; no callback runs again.
    assert calls == 1
    assert first == second


def test_browser_only_part_with_no_element_around_it_mounts_the_whole_page() -> None:
    engine = Citry(autodiscover=False)

    class HostRoot(Component):
        citry = engine
        template = """
<p v-if="open">x</p><p>b</p>
"""
        js = "$component({data(){return {open: true};}});"

    rendered = HostRoot().render()
    html = rendered.serialize()

    assert '"hydrate":true' not in html
    # The page mounts in the browser, and its host carries Citry's ordinary
    # server HTML (both v-if branches' elements included) until Vue replaces it.
    assert re.fullmatch(
        r'\n<p v-if="open" data-cid-[a-z0-9_-]+="">x</p><p data-cid-[a-z0-9_-]+="">b</p>\n', _host(html)
    )
    admission = _admission(rendered)
    assert admission.reason == "host-root"
    assert admission.server_html
    assert admission.element_count is None
    assert _declines(admission) == [("browser-condition", "v-if", "page", None, "HostRoot")]


def test_authored_allow_mismatch_attribute_is_refused() -> None:
    engine = Citry(autodiscover=False)

    class AtRoot(Component):
        citry = engine
        template = """
<main data-allow-mismatch="children"><p>x</p></main>
"""
        js = "$component({});"

    class Nested(Component):
        citry = engine
        template = """
<main><section data-allow-mismatch="children"><p>x</p></section><p>k</p></main>
"""
        js = "$component({});"

    # The attribute would hide mismatches inside content the server claims
    # Vue can adopt, so the element carrying it is never written.
    rendered = AtRoot().render()
    assert '"hydrate":true' not in rendered.serialize()
    assert _declines(_admission(rendered)) == [
        ("unsupported-attribute", "data-allow-mismatch", "page", None, "AtRoot")
    ]

    host, admission = _hydrated_host(Nested)
    # The shell's Citry HTML leaves the authored marker out, so the runtime
    # only empties the shells the server wrote.
    assert host == '<main data-allow-mismatch="children"><section><p>x</p></section><p>k</p></main>'
    assert _declines(admission) == [("unsupported-attribute", "data-allow-mismatch", "shell", "main", "Nested")]


def test_component_loop_writes_one_fragment_around_its_items() -> None:
    engine = Citry(autodiscover=False)

    class Item(Component):
        citry = engine
        template = """
<li>{{ label }}</li>
"""

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class Loop(Component):
        citry = engine
        template = """
<ul><c-for each="x in xs"><c-Item #c-key="x" c-label="x" /></c-for></ul>
"""
        js = "$component({});"

        def template_data(self, kwargs, slots):
            return {"xs": kwargs["xs"]}

    observed = {count: _hydrated_host(Loop, xs=["a", "b", "c"][:count]) for count in (0, 1, 3)}

    # An empty list still writes its anchors, because Vue's list Fragment does.
    assert observed[0][0] == "<ul><!--[--><!--]--></ul>"
    assert observed[1][0] == "<ul><!--[--><li>a</li><!--]--></ul>"
    assert observed[3][0] == "<ul><!--[--><li>a</li><li>b</li><li>c</li><!--]--></ul>"
    assert [observed[count][1].element_count for count in (0, 1, 3)] == [1, 2, 4]


def test_element_loop_writes_one_fragment_around_its_items() -> None:
    engine = Citry(autodiscover=False)

    class Leaf(Component):
        citry = engine
        template = """
<ol><li c-for="x in xs">{{ x }}</li></ol>
"""
        js = "$component({});"

        def template_data(self, kwargs, slots):
            return {"xs": kwargs["xs"]}

    assert _hydrated_host(Leaf, xs=[])[0] == "<ol><!--[--><!--]--></ol>"
    assert _hydrated_host(Leaf, xs=["one"])[0] == "<ol><!--[--><li>one</li><!--]--></ol>"
    assert _hydrated_host(Leaf, xs=["a", "b", "c"])[0] == "<ol><!--[--><li>a</li><li>b</li><li>c</li><!--]--></ol>"


def test_empty_slot_empty_condition_and_empty_component_write_vue_placeholders() -> None:
    engine = Citry(autodiscover=False)

    class Slotted(Component):
        citry = engine
        template = """
<section><c-slot name="default" /></section>
"""

    class Nothing(Component):
        citry = engine
        template = ""

    class EmptySlot(Component):
        citry = engine
        template = """
<main><c-Slotted /></main>
"""
        js = "$component({});"

    class FilledSlot(Component):
        citry = engine
        template = """
<main><c-Slotted><b>fill</b></c-Slotted></main>
"""
        js = "$component({});"

    class EmptyIf(Component):
        citry = engine
        template = """
<main><c-if cond="False"><p>x</p></c-if><p>k</p></main>
"""
        js = "$component({});"

    class CallsNothing(Component):
        citry = engine
        template = """
<main><c-Nothing /><p>k</p></main>
"""
        js = "$component({});"

    # The slot choice reaches Vue as a branch, so an unfilled slot with no
    # fallback leaves Vue's empty-branch comment.
    assert _hydrated_host(EmptySlot)[0] == "<main><section><!--v-if--></section></main>"
    assert _hydrated_host(FilledSlot)[0] == "<main><section><!--[--><b>fill</b><!--]--></section></main>"
    # A false c-if is decided in Python, so the browser never sees a branch.
    assert _hydrated_host(EmptyIf)[0] == "<main><p>k</p></main>"
    # A component that renders nothing is an empty comment in Vue.
    assert _hydrated_host(CallsNothing)[0] == "<main><!----><p>k</p></main>"


def test_entities_and_void_elements_are_written_as_vue_renders_them() -> None:
    engine = Citry(autodiscover=False)

    class Entities(Component):
        citry = engine
        template = """
<main><p title="a &amp; &quot;b&quot;">x &amp; y &lt; z</p><p>{{ label }}</p></main>
"""
        js = "$component({});"

        def template_data(self, kwargs, slots):
            return {"label": "Python & entity text <tag>"}

    class Voids(Component):
        citry = engine
        template = """
<main><p>a<br>b<img src="/x.png" alt=""></p><hr/><input type="text"></main>
"""
        js = "$component({});"

    host, admission = _hydrated_host(Entities)
    assert host == (
        '<main><p title="a &amp; &quot;b&quot;">x &amp; y &lt; z</p><p>Python &amp; entity text &lt;tag&gt;</p></main>'
    )
    assert admission.declines == ()

    host, admission = _hydrated_host(Voids)
    assert host == '<main><p>a<br>b<img src="/x.png" alt=""></p><hr><input type="text"></main>'
    assert admission.element_count == 6


@pytest.mark.parametrize(
    "character", ["\x01", "\x0b", "\x1c", "\x7f", "\x80", "\x85", "\x9f", "\ufdd0", "\ufffe", "\U0010ffff"]
)
def test_control_characters_and_noncharacters_are_written_as_they_are(character: str) -> None:
    # The HTML standard calls these characters parse errors, but the browser
    # keeps them in the DOM, so the page still hydrates with them in its HTML.
    engine = Citry(autodiscover=False)

    class Page(Component):
        citry = engine

        def template_data(self, kwargs, slots):
            return {"text": f"a{character}b"}

        template = """
<main><p>{{ text }}</p></main>
"""
        js = """
$component({});
"""

    host, admission = _hydrated_host(Page)
    assert host == f"<main><p>a{character}b</p></main>"
    assert admission.declines == ()


def test_attribute_and_raw_html_holding_a_control_character_hydrate() -> None:
    # The `<c-raw>` block is complete HTML, and the browser keeps the DEL in
    # it and in the attribute value, so the render succeeds and the page
    # hydrates with no declines.
    engine = Citry(autodiscover=False)

    class Page(Component):
        citry = engine

        def template_data(self, kwargs, slots):
            return {"label": "x"}

        template = """
<main>
  <p title="a\x7fb">{{ label }}</p>
  <c-raw><b title="a\x7fb">a\x7fb</b></c-raw>
</main>
"""
        js = """
$component({});
"""

    host, admission = _hydrated_host(Page)
    assert host == '<main><p title="a\x7fb">x</p><!--[--><b title="a\x7fb">a\x7fb</b><!--]--></main>'
    assert admission.declines == ()


def test_markup_value_holding_a_control_character_hydrates() -> None:
    # A Markup value goes through the same complete-HTML check as `<c-raw>`.
    engine = Citry(autodiscover=False)

    class Page(Component):
        citry = engine

        def template_data(self, kwargs, slots):
            return {"html": Markup("<b>a\x7fb</b>")}

        template = """
<main><p>{{ html }}</p></main>
"""
        js = """
$component({});
"""

    host, admission = _hydrated_host(Page)
    assert host == "<main><p><!--[--><b>a\x7fb</b><!--]--></p></main>"
    assert admission.declines == ()


def test_attribute_values_decode_legacy_references_by_the_attribute_rule() -> None:
    # A legacy name is a named reference HTML also accepts without `;`, such
    # as `&copy`. In an attribute value the browser and Vue keep one that `=`
    # or a letter or digit follows (`&region=eu` in a URL), and decode it
    # anywhere else in the value (`&copy` at the end). In text it always
    # decodes.
    engine = Citry(autodiscover=False)

    class Link(Component):
        citry = engine
        template = """
<main><a href="/search?q=x&region=eu&copy">go</a><p :title="'a&copy=b'">t &copy</p></main>
"""
        js = """
$component({});
"""

    host, admission = _hydrated_host(Link)
    assert host == '<main><a href="/search?q=x&amp;region=eu\u00a9">go</a><p title="a&amp;copy=b">t \u00a9</p></main>'
    assert admission.declines == ()


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        ('<p class="a&region=b">t</p>', 'class: "a&region=b"'),
        ('<div v-for="i in xs" key="a&region=b&copy">t</div>', 'key: "a&region=b\u00a9"'),
        ('<C label="x&region=1&copy" />', 'label: "x&region=1\u00a9"'),
        ("<p v-html=\"'x&region=1'\"></p>", "innerHTML: 'x&region=1'"),
        ('<slot name="s&region=1"></slot>', '_renderSlot(_ctx.$slots, "s&region=1"'),
        # HTML never decodes a reference in a name.
        ('<slot data-a&copy="1"></slot>', '"dataA&copy": "1"'),
        ("<C><template #a&copy>x</template></C>", '"a&copy": _withCtx('),
    ],
)
def test_the_compiler_reads_attribute_values_and_names_as_vue_does(template: str, expected: str) -> None:
    # Each expected fragment is what @vue/compiler-dom 3.5.44 writes.
    assert expected in NativeCompiler().compile(template, type_key="T").javascript


def test_direct_capture_reads_attribute_values_by_the_attribute_rule() -> None:
    # Vue reads `a&notb` as `a & notb`. Read as text, `&not` would decode
    # and give a different expression.
    assert not _source_attribute_reads_instance(":title", ':title="a&notb"', ("a", "notb"))
    assert _prepared_root_markers(('data-x="a&region=b"',)) == (("data-x", "a&region=b"),)


def test_directive_values_decode_character_references_as_vue_does() -> None:
    # Vue decodes a directive value's references before it reads the
    # JavaScript, so the server writes what the browser computes.
    engine = Citry(autodiscover=False)

    class Text(Component):
        citry = engine
        template = """
<main><p :data-n="'a &amp; b'.length" v-text="'x &lt; y'"></p></main>
"""
        js = """
$component({});
"""

    host, admission = _hydrated_host(Text)
    assert host == '<main><p data-n="5">x &lt; y</p></main>'
    assert admission.declines == ()


@pytest.mark.parametrize(
    ("template", "host"),
    [
        # A constant `<c-if>` writes nothing, so the braces around it meet.
        ('<main><p>{<c-if cond="True">{ 1 + 1 }}</c-if></p></main>', "<main><p>{{ 1 + 1 }}</p></main>"),
        # An unrolled literal loop does the same for each item.
        ('<main><p>{<c-for each="i in [1, 2]">{ i }}</c-for></p></main>', "<main><p>{{ i }}{ i }}</p></main>"),
        # A value next to a brace stays a value, on either side.
        ('<main><p>a {{ "{" }}{ b</p></main>', "<main><p>a {{ b</p></main>"),
        ('<main><p>a {<c-if cond="True">{{ "X" }}</c-if></p></main>', "<main><p>a {X</p></main>"),
    ],
)
def test_braces_that_meet_across_a_citry_tag_stay_text(template: str, host: str) -> None:
    # Without Vue the page shows the braces as text, so Vue must not read
    # them as an interpolation and run what is between them.
    engine = Citry(autodiscover=False)
    page = type("Page", (Component,), {"citry": engine, "template": template, "js": "\n$component({});\n"})

    rendered, admission = _hydrated_host(page)
    assert rendered == host
    assert admission.declines == ()


def test_braces_that_meet_before_a_root_with_css_variables_stay_text() -> None:
    # A component with `css_data` marks its roots, which writes the text
    # before each root in its own piece.
    engine = Citry(autodiscover=False)

    class Root(Component):
        citry = engine
        template = """
{<c-if cond="True">{ 1 + 1 }}</c-if><div>x</div>
"""
        css = """
div { color: var(--tone); }
"""

        def css_data(self, kwargs, slots):
            return {"tone": "red"}

    class Page(Component):
        citry = engine
        template = """
<main><c-Root /></main>
"""
        js = """
$component({});
"""

    rendered, admission = _hydrated_host(Page)
    assert "{{ 1 + 1 }}" in rendered
    assert admission.declines == ()


def test_braces_beside_raw_html_stay_text_when_a_branch_is_chosen_on_the_server() -> None:
    # A `<c-raw>` block keeps the component off the single-program path, so
    # only the chosen branch is written and its braces meet the text before.
    engine = Citry(autodiscover=False)

    class Page(Component):
        citry = engine
        template = """
<main><p>{<c-if cond="flag">{ x }}</c-if></p><c-raw><b>r</b></c-raw></main>
"""
        js = """
$component({});
"""

        def template_data(self, kwargs, slots):
            return {"flag": True}

    rendered, admission = _hydrated_host(Page)
    assert rendered.startswith("<main><p>{{ x }}</p>")
    assert admission.declines == ()


def test_a_simple_component_that_writes_a_brace_does_not_open_an_interpolation() -> None:
    engine = Citry(autodiscover=False)

    class Brace(Component):
        citry = engine
        simple = True
        # One line on purpose: the brace must be the last character, and a
        # multiline template would end with a line break instead.
        template = """{"""

    class Page(Component):
        citry = engine
        template = """
<main><p><c-Brace />{ 'a' }}</p></main>
"""
        js = """
$component({});
"""

    rendered, admission = _hydrated_host(Page)
    assert rendered == "<main><p>{{ 'a' }}</p></main>"
    assert admission.declines == ()


def _v_pre_page(template: str, data: dict[str, object]) -> type[Component]:
    engine = Citry(autodiscover=False)

    def template_data(self: Component, kwargs: object, slots: object) -> dict[str, object]:
        return data

    return type(
        "Page",
        (Component,),
        {"citry": engine, "template": template, "js": "\n$component({});\n", "template_data": template_data},
    )


@pytest.mark.parametrize(
    ("template", "host"),
    [
        (
            '<main><div v-pre>{{ name }} and {{ "a" }}</div><p>{{ name }}</p></main>',
            "<main><div><!--[-->Ann &amp; Bo and a<!--]--></div><p>Ann &amp; Bo</p></main>",
        ),
        (
            '<main><div v-pre><p c-title="name" :x="y">t</p><c-if cond="True">yes</c-if>'
            '<c-for each="i in [1, 2]">{{ i }}</c-for></div></main>',
            '<main><div><!--[--><p title="Ann &amp; Bo" :x="y">t</p>yes12<!--]--></div></main>',
        ),
        # The element's own Citry bindings work, as on any element.
        (
            '<main><div v-pre c-title="name">x</div><br v-pre c-title="name"></main>',
            '<main><div title="Ann &amp; Bo"><!--[-->x<!--]--></div><br title="Ann &amp; Bo"></main>',
        ),
        ("<main><textarea v-pre>{{ name }}</textarea></main>", "<main><textarea>Ann &amp; Bo</textarea></main>"),
        # A component whose root holds `v-pre`. Such a template has no child
        # components, so it takes the fast path in `leaf_program.py`.
        ("<p v-pre>{{ name }}</p>", "<p><!--[-->Ann &amp; Bo<!--]--></p>"),
        # Whitespace stays as the server writes it.
        ("<main><div v-pre>{{ spaced }}</div></main>", "<main><div><!--[-->a\n\n  b<!--]--></div></main>"),
        ("<main><div v-pre>{{ closing }}</div></main>", "<main><div><!--[-->a &lt;/script&gt; b<!--]--></div></main>"),
        # The browser drops the newline written straight after `<pre>`.
        ("<main><pre v-pre>\n{{ name }}\n</pre></main>", "<main><pre><!--[-->Ann &amp; Bo\n<!--]--></pre></main>"),
        # Table rows and sections cannot hold a block of HTML, so contents
        # with no Vue syntax are compiled as usual. A nested `v-pre`
        # element there gets its own block.
        (
            "<main><table v-pre><tbody><tr><td>{{ name }}</td></tr></tbody></table></main>",
            "<main><table><tbody><tr><td>Ann &amp; Bo</td></tr></tbody></table></main>",
        ),
        (
            "<main><table v-pre><tr><td v-pre>{{ name }}</td></tr></table></main>",
            "<main><table><tbody><tr><td><!--[-->Ann &amp; Bo<!--]--></td></tr></tbody></table></main>",
        ),
        ("<main><pre v-pre>{{ crlf }}</pre></main>", "<main><pre><!--[-->A<!--]--></pre></main>"),
        # A transparent component's body is written in place, its Vue
        # attributes kept as Vue keeps them under `v-pre`.
        (
            '<main><div v-pre><c-element c-is="\'b\'" :x="y">{{ name }}</c-element><c-js /></div></main>',
            '<main><div><!--[--><b :x="y">Ann &amp; Bo</b><!--]--></div></main>',
        ),
    ],
)
def test_citry_values_inside_v_pre_are_written_as_the_server_renders_them(template: str, host: str) -> None:
    # Vue does not compile anything inside `v-pre`, so Citry writes the
    # contents as HTML that Vue inserts; a data binding would show as written.
    page = _v_pre_page(
        template, {"name": "Ann & Bo", "spaced": "a\n\n  b", "closing": "a </script> b", "crlf": "\r\nA"}
    )

    rendered, admission = _hydrated_host(page)
    assert rendered == host
    assert admission.declines == ()


@pytest.mark.parametrize(
    "template",
    [
        '<main><div v-pre :title="y"><p @click="go">static</p><c-js /></div></main>',
        '<main><table v-pre><tr><td :x="y">a</td></tr></table></main>',
        "<main><my-widget v-pre>static</my-widget></main>",
    ],
)
def test_v_pre_with_only_written_markup_is_left_to_vue(template: str, monkeypatch: pytest.MonkeyPatch) -> None:
    # Vue reads such an element and its contents as written, so Citry
    # compiles them with `v-pre` kept.
    compiled: list[str] = []
    compile_vue = _rust.vue._compile_vue

    def record(*args: Any) -> str:
        compiled.append(args[0])
        return compile_vue(*args)

    monkeypatch.setattr(_rust.vue, "_compile_vue", record)
    _v_pre_page(template, {})().render().serialize()
    assert len(compiled) == 1
    assert " v-pre" in compiled[0]
    assert "citry-opaque-html" not in compiled[0]


def test_v_pre_contents_stay_data_so_rows_share_one_compiled_template(monkeypatch: pytest.MonkeyPatch) -> None:
    compiled: list[str] = []
    compile_vue = _rust.vue._compile_vue

    def record(*args: Any) -> str:
        compiled.append(args[0])
        return compile_vue(*args)

    monkeypatch.setattr(_rust.vue, "_compile_vue", record)
    page = _v_pre_page(
        '<main><c-for each="v in values"><p #c-key="v" v-pre>{{ v }}</p></c-for></main>',
        {"values": [f"row {index}" for index in range(20)]},
    )

    rendered, admission = _hydrated_host(page)
    assert "<p><!--[-->row 19<!--]--></p>" in rendered
    assert admission.declines == ()
    assert len(compiled) == 1
    assert "row" not in compiled[0]


@pytest.mark.parametrize(
    "template",
    [
        '<main><svg v-pre viewBox="0 0 1 1"><text>{{ name }}</text></svg></main>',
        '<main><svg viewBox="0 0 1 1"><g v-pre><text>{{ name }}</text></g></svg></main>',
    ],
)
def test_v_pre_in_svg_compiles_contents_that_hold_no_vue_syntax(template: str) -> None:
    # SVG contents cannot be inserted as a block of HTML. Vue writes plain
    # SVG as written whether or not it compiles it, so Citry compiles it.
    html = _v_pre_page(template, {"name": "Ann & Bo"})().render().serialize()
    assert '<svg viewBox="0 0 1 1">' in html
    assert "<text>Ann &amp; Bo</text>" in html
    assert "v-pre" not in html


def test_a_simple_component_inside_v_pre_renders_in_place() -> None:
    engine = Citry(autodiscover=False)

    class Chip(Component):
        citry = engine
        simple = True
        template = """
<b>{{ "chip" }}</b>
"""

    class Page(Component):
        citry = engine
        template = """
<main><div v-pre><c-Chip /></div></main>
"""
        js = """
$component({});
"""

    rendered, admission = _hydrated_host(Page)
    assert rendered == "<main><div><!--[-->\n<b>chip</b>\n<!--]--></div></main>"
    assert admission.declines == ()


def test_a_simple_components_slot_content_inside_v_pre_is_written_with_it() -> None:
    engine = Citry(autodiscover=False)

    class Chip(Component):
        citry = engine
        simple = True
        template = """
<em><c-slot /></em>
"""

    class Page(Component):
        citry = engine
        template = """
<main><div v-pre><c-Chip><b :x="y">{{ "in" }}</b></c-Chip></div></main>
"""
        js = """
$component({});
"""

    rendered, admission = _hydrated_host(Page)
    assert rendered == '<main><div><!--[-->\n<em><b :x="y">in</b></em>\n<!--]--></div></main>'
    assert admission.declines == ()


def test_v_pre_rows_from_c_for_stay_data(monkeypatch: pytest.MonkeyPatch) -> None:
    # The rows a `<c-for>` writes are data, so the compiled template is the
    # same for any number of rows.
    compiled: set[str] = set()
    compile_vue = _rust.vue._compile_vue

    def record(*args: Any) -> str:
        compiled.add(args[0])
        return compile_vue(*args)

    monkeypatch.setattr(_rust.vue, "_compile_vue", record)
    template = '<main><div v-pre><c-for each="i in items"><b>r</b></c-for></div></main>'
    for count in (1, 3):
        _v_pre_page(template, {"items": list(range(count))})().render().serialize()
    assert len(compiled) == 1


def test_a_component_inside_v_pre_is_refused_with_its_name() -> None:
    engine = Citry(autodiscover=False)

    class Child(Component):
        citry = engine
        template = """
<b>child</b>
"""

    class Page(Component):
        citry = engine
        template = """
<main><div v-pre><c-Child /></div></main>
"""
        js = """
$component({});
"""

    with pytest.raises(TypeError, match=r"'v-pre' on the <div> element .* cannot hold the component Child"):
        Page().render().serialize()

    # Inside a table, Citry compiles the contents, and Vue would compile
    # the slot content the child is given, so the child is refused there too.
    class Table(Component):
        citry = engine
        template = """
<main><table v-pre><tr><td><c-Child><b :x="y">{{ "in" }}</b></c-Child></td></tr></table></main>
"""
        js = """
$component({});
"""

    with pytest.raises(TypeError, match=r"'v-pre' on the <table> element .* cannot hold the component Child"):
        Table().render().serialize()


@pytest.mark.parametrize(
    ("template", "data", "error", "match"),
    [
        (
            '<main><div v-pre :title="y">{{ name }}</div></main>',
            {"name": "Ann"},
            TypeError,
            r"also has the Vue attribute ':title'. Under 'v-pre', Vue would write it as a plain attribute",
        ),
        # A later render replaces the block, which '#c-ignore' must keep.
        (
            "<main><div v-pre><div #c-ignore>{{ name }}</div></div></main>",
            {"name": "Ann"},
            TypeError,
            r"cannot hold a '#c-ignore' element \(<div>\)",
        ),
        (
            "<main><div v-pre>{{ html }}</div></main>",
            {"html": Markup("</div><p>{{ 7*7 }}</p><div>")},
            ValueError,
            r"is not a complete HTML fragment",
        ),
        (
            "<main><div v-pre><c-slot /></div></main>",
            {},
            TypeError,
            r"cannot hold a <c-slot> outlet",
        ),
        # A built-in is named by its tag.
        (
            "<main><div v-pre><c-error-fallback>{{ name }}</c-error-fallback></div></main>",
            {"name": "Ann"},
            TypeError,
            r"cannot hold the component <c-error-fallback>",
        ),
        # Where a block of HTML cannot sit, compiling the contents would run
        # the Vue syntax that `v-pre` keeps as written.
        (
            '<main><table v-pre><tr><td :x="y">{{ name }}</td></tr></table></main>',
            {"name": "Ann"},
            TypeError,
            r"'v-pre' on the <table> element .* because the browser moves a block of HTML out of a table's rows"
            r" .* cannot hold the Vue attribute ':x' on <td>. Put 'v-pre' on a <td> or <th> inside it",
        ),
        (
            '<main><svg v-pre><path :d="y"></path>{{ name }}</svg></main>',
            {"name": "Ann"},
            TypeError,
            r"'v-pre' on the <svg> element .* SVG or MathML .* cannot hold the Vue attribute ':d' on <path>",
        ),
    ],
)
def test_v_pre_refuses_what_it_cannot_write_as_html(
    template: str, data: dict[str, object], error: type[Exception], match: str
) -> None:
    with pytest.raises(error, match=match):
        _v_pre_page(template, data)().render().serialize()


def test_spread_attributes_vary_per_row_and_follow_vue_value_rules() -> None:
    engine = Citry(autodiscover=False)

    class Spread(Component):
        citry = engine
        template = """
<div><article c-for="row in rows" c-bind="row['attrs']">{{ row['t'] }}</article></div>
"""
        js = "$component({});"

        def template_data(self, kwargs, slots):
            return {
                "rows": [
                    {"attrs": {"id": "a", "data-on": True, "data-n": 0, "data-gone": None}, "t": "x"},
                    {"attrs": {"data-other": False, "title": "t"}, "t": "y"},
                ]
            }

    host, admission = _hydrated_host(Spread)

    # Python True reaches Vue as `true`, which Vue writes as "true" on a
    # custom attribute. Citry drops None and False before the data reaches
    # the browser, so Vue never sees those names.
    assert host == '<div><article data-n="0" data-on="true" id="a">x</article><article title="t">y</article></div>'
    assert admission.declines == ()


def test_checked_is_also_written_as_an_attribute() -> None:
    engine = Citry(autodiscover=False)

    class Checked(Component):
        citry = engine
        template = """
<form><input type="checkbox" c-checked="on" value="yes"><input type="checkbox" c-checked="off" value="no"></form>
"""
        js = "$component({});"

        def template_data(self, kwargs, slots):
            return {"on": True, "off": False}

    host, _ = _hydrated_host(Checked)

    # Vue sets `checked` as a property and an attribute, so the checked box
    # carries it in the HTML and the unchecked one does not.
    assert host == '<form><input type="checkbox" value="yes" checked=""><input type="checkbox" value="no"></form>'


def test_document_page_hydrates_with_title_and_textarea() -> None:
    engine = Citry(autodiscover=False)

    class Document(Component):
        citry = engine
        template = """
<!doctype html>
<html>
<head><title>Board</title></head>
<body>
<main><h1>Board</h1><form><textarea>{{ note }}</textarea></form></main>
</body>
</html>
"""
        js = "$component({});"

        def template_data(self, kwargs, slots):
            return {"note": "a < b"}

    rendered = Document().render()
    html = rendered.serialize()

    assert '"hydrate":true' in html
    # <title> sits outside the Vue host and <textarea> text is escaped the
    # way Vue writes it; neither stops the page from hydrating.
    assert "<head><title>Board</title></head>" in html
    assert _host(html) == "<main><h1>Board</h1><form><textarea>a &lt; b</textarea></form></main>"
    # The render marker stays on <html>, outside the host, as in client mount.
    assert re.search(r'<html data-cid-[A-Za-z0-9_-]+="">', html)
    assert "data-cid" not in _host(html)
    admission = _admission(rendered)
    assert (admission.hydrated, admission.element_count, admission.declines) == (True, 4, ())


def test_page_hydrates_only_above_the_element_threshold() -> None:
    def page_for(threshold: int | None) -> tuple[object, str]:
        engine = (
            Citry(autodiscover=False)
            if threshold is None
            else Citry(ssr_element_threshold=threshold, autodiscover=False)
        )

        class Page(Component):
            citry = engine
            template = """
<main><section><p>one</p><p>two</p></section></main>
"""
            js = "$component({});"

        rendered = Page().render()
        return rendered, rendered.serialize()

    # Four elements: main, section, and two paragraphs.
    rendered, html = page_for(3)
    assert '"hydrate":true' in html
    assert _admission(rendered).element_count == 4

    rendered, html = page_for(4)
    assert '"hydrate":true' not in html
    admission = _admission(rendered)
    assert (admission.hydrated, admission.reason, admission.element_count, admission.threshold) == (
        False,
        "below-threshold",
        4,
        4,
    )
    # The threshold is an opt-out: a page below it is written exactly as
    # ordinary client mount, with an empty host and no server HTML.
    assert html == rendered.serialize(ssr=False)  # type: ignore[attr-defined]
    assert _host(html) == ""
    assert not admission.server_html

    # The default hydrates every page that writes an element.
    rendered, html = page_for(None)
    assert '"hydrate":true' in html
    assert _admission(rendered).threshold == 0


@pytest.mark.parametrize(
    "tamper",
    [
        "unchanged",
        "duplicate_host",
        "host_id_in_text",
        "host_id_in_script",
        "changed_host_content",
        "changed_start_script",
        "changed_configuration_block",
    ],
)
def test_hydrated_host_must_reach_the_page_exactly_as_written(
    tamper: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = Citry(autodiscover=False)

    class Page(Component):
        citry = engine
        template = """
<main><p>one</p><p>two</p></main>
"""
        js = "$component({});"

    # Keep the plan and the HTML the dependency hook returned, so each case
    # can hand finalize a changed copy of the same page.
    captured: list[tuple[VueSerializationPlan, str]] = []
    finalize = VueSerializationPlan.finalize

    def capture(plan: VueSerializationPlan, hooked_html: str) -> str:
        captured.append((plan, hooked_html))
        return finalize(plan, hooked_html)

    monkeypatch.setattr(VueSerializationPlan, "finalize", capture)
    assert '"hydrate":true' in Page().render().serialize()
    [(plan, hooked_html)] = captured
    assert plan._owned_host is not None
    assert plan._owned_start_scripts is not None
    [(configuration_block, configuration_text), (start_script, start_text)] = plan._owned_start_scripts

    # The browser adopts the host by its id, so a second host, or the id
    # showing up anywhere else, would let Vue adopt the wrong markup.
    if tamper == "duplicate_host":
        hooked_html += plan._owned_host
    elif tamper == "host_id_in_text":
        hooked_html += f"<p>{plan.host_id}</p>"
    elif tamper == "host_id_in_script":
        hooked_html += f"<script>const x='{plan.host_id}';</script>"
    # Changed content inside the host would no longer match what Vue expects
    # to adopt, and a changed start script or configuration block could mount
    # instead of hydrating, so all of them are rejected too.
    elif tamper == "changed_host_content":
        assert hooked_html.count("<p>one</p>") == 1
        hooked_html = hooked_html.replace("<p>one</p>", "<p>uno</p>")
    elif tamper == "changed_start_script":
        changed = Script(content=f"{start_text} console.log('started');", attrs={"type": "module"})
        scripts = tuple(changed if script is start_script else script for script in plan.scripts)
        plan = replace(plan, scripts=scripts)
    elif tamper == "changed_configuration_block":
        # Only the hydrate flag differs, so the block is otherwise a valid
        # configuration the browser would accept.
        assert configuration_text.count('"hydrate":true') == 1
        changed = Script(
            content=configuration_text.replace('"hydrate":true', '"hydrate":false'),
            attrs=dict(configuration_block.attrs),
        )
        scripts = tuple(changed if script is configuration_block else script for script in plan.scripts)
        plan = replace(plan, scripts=scripts)

    if tamper == "unchanged":
        finalize(plan, hooked_html)
    else:
        with pytest.raises(ValueError, match="must preserve the hydrated mount host"):
            finalize(plan, hooked_html)


def test_page_level_reasons_are_recorded_without_rendering_the_host() -> None:
    engine = Citry(autodiscover=False)

    class Page(Component):
        citry = engine
        template = """
<main><p>x</p></main>
"""
        js = "$component({});"

    rendered = Page().render()
    rendered.serialize(ssr=False)
    assert _admission(rendered) == HydrationAdmission(hydrated=False, reason="ssr-disabled")
    # Each serialization replaces the previous decision.
    rendered.serialize()
    assert _admission(rendered).hydrated
    # A fragment is inserted into a page that already has its app, so it
    # always mounts in the browser.
    engine.set_mounted_prefix("/citry")
    rendered.serialize(deps_strategy="fragment")
    assert _admission(rendered) == HydrationAdmission(hydrated=False, reason="not-a-document")


def test_other_asset_positions_mount_in_the_browser_instead_of_failing() -> None:
    engine = Citry(autodiscover=False)

    class Page(Component):
        citry = engine
        template = """
<main><p>x</p></main>
"""
        js = "$component({});"

    rendered = Page().render()
    # The written host is checked after the hooks place the assets, and that
    # check assumes the default placement; other placements mount instead.
    for position in ("prepend", "append"):
        html = rendered.serialize(deps_position=position)
        assert '"hydrate":true' not in html
        # The host still carries the page's content for Vue to replace.
        assert _admission(rendered) == HydrationAdmission(hydrated=False, reason="deps-position", server_html=True)
        assert re.search(r'<div id="citry-vue-[^"]+">\n?<main data-cid-[a-z0-9_-]+=""><p>x</p></main>', html)
    assert '"hydrate":true' in rendered.serialize(deps_position="smart")


def _host_between(html: str) -> str:
    """Return everything inside the Vue host, whatever follows it."""
    start = re.search(r'<div id="citry-vue-[^"]+">', html)
    assert start is not None, html[:500]
    # The host is the last element of the body; the runtime scripts follow it.
    end = html.index("</div><script", start.end())
    return html[start.end() : end]


def test_small_page_hydrates_by_default_with_its_content_in_the_html() -> None:
    engine = Citry(autodiscover=False)

    class Greeting(Component):
        citry = engine
        template = """
<p>Hello {{ name }}</p>
"""

        def template_data(self, kwargs: object, slots: object) -> dict[str, str]:
            return {"name": "Ada"}

    class Page(Component):
        citry = engine
        template = """
<main><h1>Welcome</h1><c-Greeting /></main>
"""
        js = "$component({});"

    host, admission = _hydrated_host(Page)

    # With the default settings a three-element page hydrates: its text is
    # in the served HTML and no part is left for the browser to build.
    assert host == "<main><h1>Welcome</h1><p>Hello Ada</p></main>"
    assert (admission.threshold, admission.shell_count, admission.declines) == (0, 0, ())
    assert not admission.server_html


def test_page_that_cannot_hydrate_writes_the_body_children_it_skipped() -> None:
    engine = Citry(autodiscover=False)

    class Child(Component):
        citry = engine
        template = """
<section>child content</section>
"""

    class Page(Component):
        citry = engine
        template = """
<!doctype html><html><head><title>T</title></head><body><p v-if="open">x</p><c-Child /></body></html>
"""
        js = "$component({data(){return {open: true};}});"

    rendered = Page().render()
    html = rendered.serialize()

    # A browser-only v-if at the host root cannot hydrate. A document like
    # this one normally skips its body content, so the server builds them
    # now: the host carries the child's HTML for Vue to replace.
    assert '"hydrate":true' not in html
    host = _host_between(html)
    assert "child content" in host
    assert '<p v-if="open"' in host
    admission = _admission(rendered)
    assert (admission.reason, admission.server_html) == ("host-root", True)
    # The document outside the host is unchanged.
    assert "<head><title>T</title></head><body><div id=" in html


def test_dependency_placeholders_in_the_body_stay_out_of_the_server_html() -> None:
    engine = Citry(autodiscover=False)

    class Page(Component):
        citry = engine
        template = """
<!doctype html><html><head><c-css /></head><body><p v-if="open">x</p><p>kept</p><c-js /></body></html>
"""
        js = "$component({data(){return {open: true};}});"

    rendered = Page().render()
    html = rendered.serialize()

    # Vue clears its host when it mounts, so a script placed inside the host
    # would be removed with it. The placeholder is dropped from the host as
    # it is from an empty host, and the assets go after the host instead.
    host = _host_between(html)
    assert host == '<p v-if="open">x</p><p>kept</p>'
    assert "data-citry-vue-document" in html.split(host, 1)[1]
    assert _admission(rendered).server_html


def test_csp_page_carries_server_html_and_keeps_every_script_nonced() -> None:
    engine = Citry(autodiscover=False, security_csp="strict")

    class Page(Component):
        citry = engine
        template = """
<!doctype html>
<html>
  <head><title>T</title></head>
  <body><main><h1>Secure</h1><button @click="n++">Add</button></main></body>
</html>
"""
        js = "$component({data(){return {n: 0};}});"

    rendered = Page().render()
    html = rendered.serialize(csp_nonce="cmVxdWVzdE5vbmNl")

    # A CSP page mounts in the browser, and its content is still served.
    assert '"hydrate":true' not in html
    host = _host_between(html)
    assert "<h1>Secure</h1>" in host
    assert '<button @click="n++"' in host
    # The server HTML adds no script; every script Citry writes carries the nonce.
    assert "<script" not in host
    scripts = re.findall(r"<script\b[^>]*>", html)
    assert scripts
    assert all('nonce="cmVxdWVzdE5vbmNl"' in tag for tag in scripts)
    admission = _admission(rendered)
    assert (admission.reason, admission.server_html) == ("security-policy", True)


@pytest.mark.parametrize("style", ["<style>p{color:red}</style>", '<style media="print">p{color:red}</style>'])
# The page's own CSP check warns about the raw style, as expected.
@pytest.mark.filterwarnings("ignore:Citry found 1 strict-CSP:RuntimeWarning")
def test_csp_body_with_a_raw_style_element_keeps_an_empty_host(style: str) -> None:
    engine = Citry(autodiscover=False, security_csp="warn")

    class Page(Component):
        citry = engine
        template = """
<!doctype html>
<html>
  <head><title>T</title></head>
  <body><main>{{ widget }}<p>kept</p></main></body>
</html>
"""
        js = "$component({});"

        def template_data(self, kwargs: object, slots: object) -> dict[str, object]:
            return {"widget": Markup(style)}  # noqa: S704 - the test supplies its own fixed markup

    rendered = Page().render()
    html = rendered.serialize(csp_nonce="cmVxdWVzdE5vbmNl")
    # The served copy would add a raw <style> that the CSP check reports,
    # with or without attributes, so the host stays empty.
    assert re.search(r'<div id="citry-vue-[^"]+"></div>', html)
    assert _admission(rendered).server_html is False


def test_body_with_a_script_element_keeps_an_empty_host() -> None:
    engine = Citry(autodiscover=False)

    class Page(Component):
        citry = engine
        template = """
<main><p>visible</p><div>{{ widget }}</div></main>
"""
        js = "$component({});"

        def template_data(self, kwargs: object, slots: object) -> dict[str, object]:
            return {"widget": Markup("<b>trusted</b><script>window.ran = true;</script>")}

    rendered = Page().render()
    # Another asset position keeps the page from hydrating.
    html = rendered.serialize(deps_position="append")

    # The browser would run the script while parsing the served HTML, but
    # Vue inserts trusted HTML without running its scripts, so the script
    # would run once where a client mount never runs it. The host stays empty.
    assert re.search(r'<div id="citry-vue-[^"]+"></div>', html)
    assert "visible" not in html.split("<script", 1)[0]
    admission = _admission(rendered)
    assert (admission.reason, admission.server_html) == ("deps-position", False)


@pytest.mark.parametrize("policy", [{"security_csp": "strict"}, {"security_javascript": "warn"}])
# The JavaScript policy's own inventory of the page is expected here.
@pytest.mark.filterwarnings("ignore:security_javascript='warn' found:RuntimeWarning")
def test_page_whose_served_copy_would_break_its_security_policy_keeps_an_empty_host(
    policy: dict[str, str],
) -> None:
    engine = Citry(autodiscover=False, **policy)  # type: ignore[arg-type]

    class Page(Component):
        citry = engine
        template = """
<main><a href="#top" onclick="history.back()">Back</a><button @click="n++">Add</button></main>
"""
        js = "$component({data(){return {n: 0};}});"

    rendered = Page().render()
    # A strict CSP rejects the inline handler, and a JavaScript policy
    # reports every Vue binding in served HTML. Sending the copy would make
    # a page that serialized cleanly fail or warn, so the host stays empty.
    html = rendered.serialize(csp_nonce="cmVxdWVzdE5vbmNl" if "security_csp" in policy else None)
    assert re.search(r'<div id="citry-vue-[^"]+"></div>', html)
    admission = _admission(rendered)
    assert (admission.reason, admission.server_html) == ("security-policy", False)


def test_runtime_empties_shells_only_when_one_carries_served_html() -> None:
    engine = Citry(autodiscover=False)

    class Plain(Component):
        citry = engine
        template = """
<main><p>kept</p></main>
"""
        js = "$component({});"

    class Scripted(Component):
        citry = engine
        template = """
<main><div><p v-if="open">x</p><c-raw><script>run()</script></c-raw></div><p>kept</p></main>
"""
        js = "$component({data(){return {open: true};}});"

    class Filled(Component):
        citry = engine
        template = """
<main><div><p v-if="open">x</p></div><p>kept</p></main>
"""
        js = "$component({data(){return {open: true};}});"

    # The flag tells the runtime to look for shells at all, so a page
    # without served shell HTML (the board, for one) skips that search.
    assert '"emptyShells"' not in Plain().render().serialize()
    rendered = Scripted().render()
    html = rendered.serialize()
    assert '"emptyShells"' not in html
    # A script in a shell's HTML would run once from the served page, so the
    # shell is sent empty.
    assert '<div data-allow-mismatch="children"></div>' in _host(html)
    assert [item.shell_content for item in _admission(rendered).declines] == [False]
    assert '"emptyShells":true' in Filled().render().serialize()


def test_a_lone_surrogate_escape_in_a_vue_expression_is_left_to_the_browser() -> None:
    # Vue builds strings holding U+D800 and U+DC00 from these escapes.
    # Neither Rust nor the page's UTF-8 HTML can hold them, so the server
    # leaves those values out and Vue writes them in the browser, rather
    # than the server writing U+FFFD and the hex digits.
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = r"""
<main><p v-text="'a\ud800b'"></p><p :title="'c\udc00d'">x</p><p v-text="'eéf'"></p></main>
"""
        js = """
$component({});
"""

    rendered = Card().render()
    host = _host(rendered.serialize())
    assert "\ufffd" not in host
    assert host == '<main data-allow-mismatch="children"><p></p><p>x</p><p>e\xe9f</p></main>'
    assert _declines(_admission(rendered)) == [("text-value", "title", "shell", "main", "Card")]
