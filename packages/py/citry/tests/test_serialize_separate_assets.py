"""
``deps_position="separate"``: the serialized HTML without its asset tags, and the tags in three groups.

A host that puts several Citry renders on one page (citry-django renders each
interactive region as its own Vue app) asks for the tags apart from the HTML,
so it can write each shared tag once. These tests lock three promises: the
returned tags are exactly the tags ``"smart"`` would have inserted, with the
same nonce, integrity and security results; each tag lands in the right group;
and Vue hydrates the HTML as it does with ``"smart"``. They also lock the
``CitryRender.needs_browser_runtime()`` check and the rule that a child
component's render may be serialized as its own Vue app before its parent.
"""

import re
import warnings

import pytest

from citry import Citry, CitryRender, Component, Extension, Markup, SerializedAssets, SerializedRender
from citry._vue.serialization import hydration_admission
from citry.ext.dependencies.types import Script, Style

_NONCE = "cmVxdWVzdE5vbmNl"
_GROUPS = ("runtime_assets", "app_assets", "component_assets")


def _engine(**settings: object) -> Citry:
    engine = Citry(autodiscover=False, **settings)  # type: ignore[arg-type]
    # Mounted routes give the runtime and the component files real URLs,
    # which is how a web app serves them.
    engine.set_mounted_prefix("/citry")
    return engine


def _widgets(engine: Citry) -> tuple[type[Component], type[Component]]:
    """Return an interactive component and a static one it uses."""

    class Badge(Component):
        citry = engine
        template = """
<span class="badge">b</span>
"""
        css = """
.badge { color: red; }
"""

    class Widget(Component):
        citry = engine
        template = """
<div class="w"><c-Badge /><button @click="n++">{{ label }}</button></div>
"""
        js = """
$component({data() { return {n: 0}; }});
"""
        css = """
.w { color: blue; }
"""

        def template_data(self, kwargs: object, slots: object) -> dict[str, object]:
            return {"label": "hi"}

    return Widget, Badge


def _all_tags(result: SerializedRender) -> list[str]:
    return [tag for group in _GROUPS for tag in (*getattr(result, group).css, *getattr(result, group).js)]


def _is_preload(tag: str) -> bool:
    return tag.startswith('<link rel="preload"')


@pytest.mark.parametrize(
    "options",
    [
        {},
        {"csp_nonce": _NONCE},
        {"csp_nonce": _NONCE, "security_script_integrity": "citry"},
        {"csp_nonce": _NONCE, "security_csp": "strict"},
    ],
    ids=["default", "nonce", "integrity", "strict-csp"],
)
def test_returned_tags_are_the_tags_smart_inserts(options: dict[str, str]) -> None:
    widget, _ = _widgets(_engine())
    rendered = widget().render()
    # Later calls on the same render keep its Vue app id, so the two outputs
    # can be compared byte for byte.
    smart = rendered.serialize_result(**options)  # type: ignore[arg-type]
    separate = rendered.serialize_result(deps_position="separate", **options)  # type: ignore[arg-type]

    remaining = smart.html
    for tag in _all_tags(separate):
        if _is_preload(tag):
            # The island has no <head>, so "smart" writes no preload hints;
            # "separate" hands them over for the host's own <head>.
            continue
        assert remaining.count(tag) == 1, tag[:200]
        remaining = remaining.replace(tag, "", 1)
    assert remaining == separate.html
    assert separate.security == smart.security
    assert "<script" not in separate.html
    assert "<link" not in separate.html
    if "csp_nonce" in options:
        for tag in _all_tags(separate):
            assert f'nonce="{_NONCE}"' in tag, tag[:200]
    if "security_script_integrity" in options:
        assert separate.security.csp_script_hashes
        assert separate.security.scripts


def test_each_tag_lands_in_its_group() -> None:
    widget, _ = _widgets(_engine())
    result = widget().render().serialize_result(deps_position="separate")
    app_id = re.search(r'<div id="citry-vue-([0-9a-f]+)"', result.html)
    assert app_id is not None

    runtime = result.runtime_assets
    assert len(runtime.js) == 1
    assert re.match(r'<script src="/citry/citry\.[0-9a-f]+\.js" integrity="sha384-', runtime.js[0])
    assert runtime.css
    assert all(_is_preload(tag) for tag in runtime.css)

    app = result.app_assets
    # One stylesheet per component, each naming this app, so the runtime
    # adopts the link instead of loading the file again.
    assert len(app.css) == 2
    assert all(f'data-citry-vue-style-app="{app_id[1]}"' in tag for tag in app.css)
    assert all(' integrity="sha256-' in tag for tag in app.css)
    assert [tag.split(">", 1)[0] + ">" for tag in app.js] == [
        f'<script type="application/json" data-citry-vue-document="{app_id[1]}">',
        '<script type="module">',
    ]
    assert result.component_assets == SerializedAssets()


def test_a_separate_island_hydrates_like_smart() -> None:
    widget, _ = _widgets(_engine())
    rendered = widget().render()
    result = rendered.serialize_result(deps_position="separate")
    admission = hydration_admission(rendered)
    assert admission is not None
    assert (admission.hydrated, admission.reason) == (True, None)
    assert '"hydrate":true' in result.app_assets.js[0]
    # The host holds the HTML Vue adopts, written without Citry's markers.
    assert '<div class="w"><span class="badge">b</span><button>hi</button></div>' in result.html


def test_a_document_keeps_its_placement_tags_empty_and_hydrates() -> None:
    engine = _engine()
    _widgets(engine)

    class Page(Component):
        citry = engine
        template = """
<!doctype html>
<html>
  <head><title>T</title><c-css /></head>
  <body><main><c-Widget /></main><c-js /></body>
</html>
"""

    rendered = Page().render()
    smart = rendered.serialize_result()
    separate = rendered.serialize_result(deps_position="separate")

    assert "<script" not in separate.html
    assert "<link" not in separate.html
    assert "<head><title>T</title></head>" in separate.html
    admission = hydration_admission(rendered)
    assert admission is not None
    assert admission.hydrated
    # In a document "smart" writes the hints into <head> too, so every
    # returned tag was in the "smart" page.
    remaining = smart.html
    for tag in _all_tags(separate):
        assert remaining.count(tag) == 1, tag[:200]
        remaining = remaining.replace(tag, "", 1)
    assert remaining == separate.html


@pytest.mark.parametrize("strategy", ["document", "simple"])
def test_a_page_without_vue_returns_component_tags(strategy: str) -> None:
    engine = _engine()
    _widgets(engine)

    class Static(Component):
        citry = engine
        template = """
<p><c-Badge /></p>
"""

        class Dependencies:
            js = [Script(url="https://cdn.example.com/lib.js")]
            css = {"all": [Style(url="https://cdn.example.com/lib.css")]}

    rendered = Static().render()
    smart = rendered.serialize(deps_strategy=strategy)  # type: ignore[arg-type]
    result = rendered.serialize_result(deps_strategy=strategy, deps_position="separate")  # type: ignore[arg-type]

    assert result.runtime_assets == SerializedAssets()
    assert result.app_assets == SerializedAssets()
    css, js = result.component_assets.css, result.component_assets.js
    assert [tag.split(" ", 1)[0] for tag in css] == ["<link", "<style"]
    assert "lib.css" in css[0]
    assert ".badge { color: red; }" in css[1]
    assert js == ('<script src="https://cdn.example.com/lib.js"></script>',)
    remaining = smart
    for tag in (*css, *js):
        remaining = remaining.replace(tag, "", 1)
    assert remaining == result.html


def test_serialize_returns_the_html_without_tags() -> None:
    widget, _ = _widgets(_engine())
    html = widget().render().serialize(deps_position="separate")
    assert html.startswith('<div id="citry-vue-')
    assert "<script" not in html


def test_ignore_returns_no_tags() -> None:
    _, badge = _widgets(_engine())
    result = badge().render().serialize_result(deps_strategy="ignore", deps_position="separate")
    assert all(getattr(result, group) == SerializedAssets() for group in _GROUPS)
    assert "<style" not in result.html


def test_fragment_refuses_separate() -> None:
    widget, _ = _widgets(_engine())
    with pytest.raises(ValueError, match="deps_position='separate'"):
        widget().render().serialize_result(deps_strategy="fragment", deps_position="separate")


def test_other_positions_leave_the_asset_fields_empty() -> None:
    widget, _ = _widgets(_engine())
    result = widget().render().serialize_result()
    assert all(getattr(result, group) == SerializedAssets() for group in _GROUPS)


def test_two_islands_share_identical_runtime_tags() -> None:
    widget, _ = _widgets(_engine())
    first = widget().render().serialize_result(deps_position="separate")
    second = widget().render().serialize_result(deps_position="separate")
    # A page that keeps the first of identical tags ends up with one runtime.
    assert first.runtime_assets == second.runtime_assets
    # Every app keeps its own stylesheet links and start script.
    assert set(first.app_assets.css).isdisjoint(second.app_assets.css)
    assert set(first.app_assets.js).isdisjoint(second.app_assets.js)


def test_strict_csp_rejects_the_same_output_with_separate() -> None:
    engine = _engine(security_csp="strict")

    class Inline(Component):
        citry = engine
        template = """
<p>x</p>
"""
        css = """
p { color: red; }
"""

    # Without a nonce the inline <style> breaks a strict CSP in either position.
    with pytest.raises(ValueError, match="csp_nonce"):
        Inline().render().serialize_result()
    with pytest.raises(ValueError, match="csp_nonce"):
        Inline().render().serialize_result(deps_position="separate")


def test_javascript_warn_reports_the_same_findings() -> None:
    engine = _engine(security_javascript="warn")
    widget, _ = _widgets(engine)

    def findings(position: str) -> list[str]:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            widget().render().serialize_result(deps_position=position)  # type: ignore[arg-type]
        return [str(item.message) for item in caught]

    smart = findings("smart")
    assert smart
    assert findings("separate") == smart


def test_javascript_omit_returns_no_scripts() -> None:
    widget, _ = _widgets(_engine())
    result = widget().render().serialize_result(deps_position="separate", security_javascript="omit")
    assert not result.runtime_assets.js
    assert not result.app_assets.js
    assert not result.component_assets.js
    assert result.component_assets.css
    assert "<script" not in result.html


def test_a_wrapper_comment_in_trusted_html_stays_in_the_html() -> None:
    engine = _engine()
    # A guessed wrapper cannot carry the per-call random value, so the
    # serializer leaves it in the HTML as ordinary content.
    forged = "<!--citry-asset:0123:runtime:js--><b>kept</b><!--/citry-asset:0123-->"

    class Page(Component):
        citry = engine
        template = """
<div>{{ value }}</div>
"""

        def template_data(self, kwargs: object, slots: object) -> dict[str, object]:
            return {"value": Markup(forged)}  # noqa: S704 - the test supplies its own fixed markup

    result = Page().render().serialize_result(deps_position="separate")
    assert forged in result.html
    assert result.runtime_assets == SerializedAssets()


def test_a_hook_that_edits_a_returned_tag_is_refused() -> None:
    class Rewrite(Extension):
        name = "rewrite"

        def on_serialize(self, ctx):  # type: ignore[no-untyped-def]
            return ctx.html.replace("<!--/citry-asset:", "<!--/edited:", 1)

    engine = _engine(extensions=[Rewrite])
    _, badge = _widgets(engine)
    with pytest.raises(RuntimeError, match="on_dependencies"):
        badge().render().serialize_result(deps_position="separate")


def test_needs_browser_runtime() -> None:
    engine = _engine()
    widget, badge = _widgets(engine)

    class ScriptOnly(Component):
        citry = engine
        template = """
<p>x</p>
"""
        js = """
$component({});
"""

    class Page(Component):
        citry = engine
        template = """
<main><c-Widget /></main>
"""

    assert widget().render().needs_browser_runtime()
    assert ScriptOnly().render().needs_browser_runtime()
    assert Page().render().needs_browser_runtime()
    assert not badge().render().needs_browser_runtime()


def test_a_child_can_become_its_own_app_before_its_parent_is_serialized() -> None:
    engine = _engine()
    _widgets(engine)

    class List(Component):
        citry = engine
        template = """
<ul><li><c-Widget /></li><li><c-Widget /></li><li><c-Badge /></li></ul>
"""

    rendered = List().render()
    parts_before = list(rendered.parts)
    children = [part for part in rendered.parts if isinstance(part, CitryRender) and part.is_component_root]
    interactive = [child for child in children if child.needs_browser_runtime()]
    assert len(children) == 3
    assert len(interactive) == 2

    islands = [child.serialize_result(deps_position="separate") for child in interactive]
    app_ids = [re.findall(r'<div id="citry-vue-([0-9a-f]+)"', island.html) for island in islands]
    # Each child is its own app, with its own host and its own stylesheets.
    assert all(len(ids) == 1 for ids in app_ids)
    assert app_ids[0] != app_ids[1]
    for island, ids in zip(islands, app_ids, strict=True):
        assert len(island.app_assets.css) == 2
        assert all(f'data-citry-vue-style-app="{ids[0]}"' in tag for tag in island.app_assets.css)

    # The parent's render tree is unchanged, so it still serializes whole.
    assert rendered.parts == parts_before
    parent = rendered.serialize()
    assert parent.count('<div id="citry-vue-') == 1
    assert not any(ids[0] in parent for ids in app_ids)
    assert parent.count('class="badge"') == 3


def test_hook_scripts_on_a_page_without_vue_are_component_tags() -> None:
    class Analytics(Extension):
        name = "analytics"

        def on_dependencies(self, ctx):  # type: ignore[no-untyped-def]
            ctx.early_scripts.append(Script(url="/static/early.js", kind="extra"))
            ctx.scripts.append(Script(url="/static/analytics.js", kind="extra"))

    engine = _engine(extensions=[Analytics])
    _, badge = _widgets(engine)
    result = badge().render().serialize_result(deps_position="separate")
    assert result.component_assets.js == (
        '<script src="/static/early.js"></script>',
        '<script src="/static/analytics.js"></script>',
    )
    assert result.runtime_assets == SerializedAssets()
    assert "<script" not in result.html


def test_without_mounted_routes_citry_code_is_runtime_and_styles_are_app_tags() -> None:
    engine = Citry(autodiscover=False)

    class Widget(Component):
        citry = engine
        template = """
<div class="w"><button @click="n++">hi</button></div>
"""
        js = """
$component({data() { return {n: 0}; }});
"""
        css = """
.w { color: blue; }
"""

    result = Widget().render().serialize_result(deps_position="separate")
    # The inline runtime comes first, then the compiled component code that
    # every app using this component shares.
    assert len(result.runtime_assets.js) >= 2
    assert "Citry interactive runtime" in result.runtime_assets.js[0]
    assert not result.runtime_assets.css
    assert [tag.split(" ", 1)[0] for tag in result.app_assets.css] == ["<style"]
    assert ".w { color: blue; }" in result.app_assets.css[0]
    assert len(result.app_assets.js) == 2
    assert result.component_assets == SerializedAssets()
    assert "<script" not in result.html


def test_javascript_forbid_refuses_the_same_output_with_separate() -> None:
    widget, _ = _widgets(_engine())
    with pytest.raises(ValueError, match="forbid"):
        widget().render().serialize_result(security_javascript="forbid")
    with pytest.raises(ValueError, match="forbid"):
        widget().render().serialize_result(deps_position="separate", security_javascript="forbid")


def test_a_child_with_slot_content_from_outside_cannot_be_its_own_app() -> None:
    engine = _engine()

    class Button(Component):
        citry = engine
        template = """
<button @click="n++">hi<c-slot /></button>
"""
        js = """
$component({data() { return {n: 0}; }});
"""

    class Page(Component):
        citry = engine
        template = """
<main><c-Button>text from the page</c-Button></main>
"""

    rendered = Page().render()
    (child,) = [part for part in rendered.parts if isinstance(part, CitryRender)]
    assert child.needs_browser_runtime()
    # The page wrote the slot content, so a Vue app made from the child
    # alone has no owner for it.
    with pytest.raises(TypeError, match="slot content that a component outside it wrote"):
        child.serialize_result(deps_position="separate")
    # The parent still serializes whole.
    assert "text from the page" in rendered.serialize()
