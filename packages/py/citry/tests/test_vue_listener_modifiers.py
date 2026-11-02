"""
Listeners with Citry's own modifiers (``.outside``, ``.window``, ``.document``, ``.debounce``, ``.throttle``).

Vue's modifiers are a fixed set inside its template compiler, so the Vue
compiler rewrites such a listener into a plain listener plus a ``v-citry-on``
directive that only the browser acts on. These tests lock what that means for
a component: the server writes the element as if the listener were not there
and the page still hydrates, and the compiled definition lists the directive
so the browser registers it.
"""

import json
import re

import pytest

from citry import Citry, Component
from citry._vue.serialization import hydration_admission

from ._render_paths import render_both

# The directive's name as the browser looks it up and as the definition lists it.
DIRECTIVE = "v-citry-on"

MENU_TEMPLATE = """
<main>
  <button type="button" @click="open = !open">Menu</button>
  <div class="panel" @click.outside="open = false" @keydown.escape.window="open = false">
    <p>Panel</p>
  </div>
</main>
"""


def _menu_page() -> type[Component]:
    app = Citry(autodiscover=False)

    class Menu(Component):
        citry = app
        template = MENU_TEMPLATE
        js = """
        $component({data(){return {open: true};}});
        """

    return Menu


def _host(html: str) -> str:
    """Return the Vue host's contents as written by the server."""
    match = re.search(r'<div id="citry-vue-[^"]+">(.*?)</div><script', html, re.DOTALL)
    assert match is not None, html[:500]
    return match.group(1)


def _manifest(html: str) -> dict[str, object]:
    """Return the manifest the page hands to the browser runtime at startup."""
    payload = html.split(" data-citry-vue-document=", 1)[1].split(">", 1)[1].split("</script>", 1)[0]
    return json.loads(payload)["manifest"]


def test_a_component_with_citry_listener_modifiers_hydrates_with_no_shell() -> None:
    rendered = _menu_page()().render()
    html = rendered.serialize()

    assert '"hydrate":true' in html
    admission = hydration_admission(rendered)
    assert admission is not None
    assert admission.hydrated
    assert admission.reason is None
    # The server writes the rewritten listeners nothing, so no element is
    # marked as a shell and nothing declines.
    assert admission.shell_count == 0
    assert admission.declines == ()
    host = _host(html)
    # The page also carries the browser runtime, which names the attribute,
    # so look for a marked element in the host only.
    assert "data-allow-mismatch" not in host
    # The panel is written as the same element it would be with no listener.
    assert '<div class="panel">' in host
    assert "<p>Panel</p>" in host
    assert "citry-on" not in host.lower()
    assert "outside" not in host
    assert "escape" not in host


def test_the_server_writes_the_same_host_with_and_without_the_listeners() -> None:
    app = Citry(autodiscover=False)

    class WithListeners(Component):
        citry = app
        template = """
        <div class="panel" @click.outside="open = false" @keydown.escape.window="open = false">
          <input @input.debounce.300ms="search($event.target.value)">
        </div>
        """
        js = """
        $component({data(){return {open: true}}, methods: {search(){}}});
        """

    class WithoutListeners(Component):
        citry = app
        template = """
        <div class="panel">
          <input>
        </div>
        """
        js = """
        $component({data(){return {open: true}}});
        """

    listeners = WithListeners().render()
    plain = WithoutListeners().render()
    assert _host(listeners.serialize()) == _host(plain.serialize())
    for rendered in (listeners, plain):
        admission = hydration_admission(rendered)
        assert admission is not None
        assert admission.hydrated
        assert (admission.shell_count, admission.declines) == (0, ())


def test_the_compiled_definition_lists_the_citry_on_directive() -> None:
    html = _menu_page()().render().serialize()

    (definition,) = _manifest(html)["definitions"]
    signature = definition["directiveSignature"]
    # One entry per rewritten listener, in source order: the `.outside` click
    # listener, then the `.window` keydown listener. The site id ends in the
    # listener's position among the element's directives.
    assert [(entry["name"], entry["arg"], entry["modifiers"]) for entry in signature] == [
        (DIRECTIVE, "click", ["outside"]),
        (DIRECTIVE, "keydown", ["escape", "window"]),
    ]
    for entry, suffix in zip(signature, ("D0", "D1"), strict=True):
        assert entry["siteId"].endswith(suffix)


def test_a_plain_listener_adds_no_directive_to_the_definition() -> None:
    app = Citry(autodiscover=False)

    class Plain(Component):
        citry = app
        template = """
        <main><button @click.stop.prevent="open = !open">Menu</button></main>
        """
        js = """
        $component({data(){return {open: true};}});
        """

    (definition,) = _manifest(Plain().render().serialize())["definitions"]
    assert definition["directiveSignature"] == []


def test_a_component_with_citry_listener_modifiers_renders_the_same_on_both_render_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def render_page() -> str:
        return _menu_page()().render().serialize()

    # `render_both` runs the page through the Rust render path and the Python
    # one, and fails when the two disagree.
    rust, python = render_both(render_page, monkeypatch)
    for result in (rust.result, python.result):
        page = str(result)
        assert '"hydrate":true' in page, page[:300]
        assert "data-allow-mismatch" not in _host(page)
        assert '<div class="panel">' in _host(page)


def test_a_citry_modifier_on_a_component_tag_is_a_load_error() -> None:
    app = Citry(autodiscover=False)

    class Card(Component):
        citry = app
        template = """
        <c-card @close.window="go" />
        """

    with pytest.raises(SyntaxError, match="works only on HTML elements"):
        Card().render().serialize()


def test_a_simple_vue_leaf_with_citry_listener_modifiers_goes_through_the_rust_render_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def render_page() -> str:
        app = Citry(autodiscover=False)

        class Leaf(Component):
            citry = app
            simple = "vue"
            template = """
            <div class="panel" @click.outside="open = false" @keydown.escape.window="open = false">
              <p>x</p>
            </div>
            """
            js = """
            $component({data(){return {open: true};}});
            """

        class Page(Component):
            citry = app
            template = """
            <main><c-leaf/></main>
            """

        return Page().render().serialize()

    # `rows_read=1` shows the Rust path read the leaf, so the case cannot
    # pass with both runs on Python.
    rust, python = render_both(render_page, monkeypatch, rows_read=1)
    for result in (rust.result, python.result):
        host = _host(str(result))
        assert '<div class="panel">' in host
        assert "data-allow-mismatch" not in host
