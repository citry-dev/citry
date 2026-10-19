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

import pytest

from citry import Citry, Component, Markup
from citry._vue.serialization import HydrationAdmission, VueSerializationPlan, hydration_admission
from citry.ext.dependencies.types import Script


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
    # this one normally skips its body children, so the server builds them
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
