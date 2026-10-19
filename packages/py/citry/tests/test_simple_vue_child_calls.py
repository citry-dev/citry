"""
A ``simple="vue"`` template can call child components, and each child keeps its own mode.

The parent renders without a Python instance. The children it calls render
through the ordinary render loop, so an ordinary child still gets its
instance, hooks and dependencies, and a ``simple="vue"`` child still skips
its own. Every test here renders one page twice, once with the parent's
``simple="vue"`` and once as an ordinary component, and expects the same
HTML the reader sees, apart from the per-render ids.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from citry import Citry, Component
from citry._vue.serialization import hydration_admission
from citry.component import Component as ComponentBase

ROWS = [
    {"id": "a", "title": "Alpha", "tags": ["x", "y"], "done": True},
    {"id": "b", "title": "Beta <b>", "tags": [], "done": False},
]


def _normalized(html: str) -> str:
    """Replace the per-render ids, which differ between any two renders."""
    html = re.sub(r"data-cid-[A-Za-z0-9_-]+", "data-cid-X", html)
    return re.sub(r'citry-vue-[0-9a-f]+"', 'citry-vue-X"', html)


def _host(html: str) -> str:
    """Return the Vue host's contents as the server wrote them for hydration."""
    match = re.search(r'<div id="citry-vue-[^"]+">(.*?)</div><script', html, re.DOTALL)
    assert match is not None, html[:500]
    return match.group(1)


def _outputs(page: type[Component], **kwargs: Any) -> dict[str, str]:
    """Serialize one render every way a reader can receive it."""
    rendered = page(**kwargs).render()
    document = rendered.serialize()
    admission = hydration_admission(rendered)
    assert admission is not None
    assert admission.hydrated, admission
    return {
        "static": _normalized(rendered.serialize(deps_strategy="simple")),
        "host": _host(document),
    }


def _instances(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record the class name of every Python component instance created."""
    created: list[str] = []
    component_init = ComponentBase.__init__

    def observe(self: object, *args: object, **kwargs: object) -> None:
        created.append(type(self).__name__)
        component_init(self, *args, **kwargs)

    monkeypatch.setattr(ComponentBase, "__init__", observe)
    return created


def _row_app(*, row_mode: Any, badge_mode: Any, row_template: str, badge_js: bool = True) -> type[Component]:
    """Build a page whose rows call a Badge child, with each class's own mode."""
    engine = Citry(autodiscover=False)

    class Badge(Component):
        citry = engine
        simple = badge_mode

        class Kwargs:
            label: str
            done: bool = False

        @staticmethod
        def template_data(kwargs: Any, _slots: Any) -> dict[str, Any]:
            return {"label": kwargs.label.upper(), "done": kwargs.done}

        template = """
            <span class="badge" c-data-done="'yes' if done else 'no'">{{ label }}</span>
        """
        if badge_js:
            js = "$component({data(){return {seen:false}}})"
            css = ".badge { color: red; }"

    class Row(Component):
        citry = engine
        simple = row_mode

        class Kwargs:
            row: dict

        @staticmethod
        def template_data(kwargs: Any, _slots: Any) -> dict[str, Any]:
            return {"row": kwargs.row}

        template = row_template
        js = "$component({data(){return {open:true}}})"

    class Page(Component):
        citry = engine

        class Kwargs:
            rows: list

        template = """
            <main>
              <c-Row c-for="row in rows" #c-key="row['id']" c-row="row" />
            </main>
        """

    del Badge, Row
    return Page


UNCONDITIONAL = """
    <article>
      <h3>{{ row['title'] }}</h3>
      <div v-show="open"><c-Badge c-label="row['title']" c-done="row['done']" /></div>
      <c-Badge label="static" />
    </article>
"""
CONDITIONAL = """
    <article>
      <c-if cond="row['done']"><c-Badge c-label="row['title']" /></c-if>
      <c-else><p>open</p></c-else>
    </article>
"""
DIRECT_LOOP = """
    <p>
      <c-Badge c-for="tag in row['tags']" #c-key="tag" c-label="tag" />
      <c-Badge #c-key="1" label="numbered" c-done="0" />
    </p>
"""
LOOPED = """
    <ul>
      <li c-for="tag in row['tags']"><c-Badge #c-key="tag" c-label="tag" /></li>
    </ul>
"""


@pytest.mark.parametrize("badge_mode", [False, "vue"])
@pytest.mark.parametrize(
    "row_template",
    [UNCONDITIONAL, CONDITIONAL, LOOPED, DIRECT_LOOP],
    ids=["plain", "c-if", "c-for", "c-for-on-call"],
)
def test_simple_vue_parent_writes_the_same_html_as_an_ordinary_parent(
    badge_mode: Any, row_template: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    ordinary = _outputs(_row_app(row_mode=False, badge_mode=badge_mode, row_template=row_template), rows=ROWS)
    created = _instances(monkeypatch)
    simple = _outputs(_row_app(row_mode="vue", badge_mode=badge_mode, row_template=row_template), rows=ROWS)

    assert simple == ordinary
    # The rows made no Python instance; each child's own mode decided its own.
    assert "Row" not in created
    assert ("Badge" in created) is (badge_mode is False)


def test_simple_vue_parent_with_css_variables_writes_the_same_html() -> None:
    template = """
        <article><c-Badge c-label="row['title']" /></article>
    """

    def page(*, row_mode: Any) -> type[Component]:
        page_class = _row_app(row_mode=row_mode, badge_mode="vue", row_template=template)
        row_class = page_class.citry.get("Row")
        row_class.css = "article { color: var(--tone); }"
        row_class.css_data = staticmethod(lambda _kwargs, _slots: {"tone": "blue"})
        return page_class

    assert _outputs(page(row_mode="vue"), rows=ROWS) == _outputs(page(row_mode=False), rows=ROWS)


def test_children_render_after_their_simple_vue_parent_in_template_order() -> None:
    engine = Citry(autodiscover=False)
    calls: list[str] = []

    class Leaf(Component):
        citry = engine
        simple = "vue"

        class Kwargs:
            name: str

        @staticmethod
        def template_data(kwargs: Any, _slots: Any) -> dict[str, Any]:
            calls.append(kwargs.name)
            return {"name": kwargs.name}

        template = """
            <i>{{ name }}</i>
        """

    class Middle(Component):
        citry = engine
        simple = "vue"

        class Kwargs:
            name: str

        @staticmethod
        def template_data(kwargs: Any, _slots: Any) -> dict[str, Any]:
            calls.append(kwargs.name)
            return {"first": kwargs.name + ".1", "second": kwargs.name + ".2"}

        template = """
            <b><c-Leaf c-name="first" /><c-Leaf c-name="second" /></b>
        """

    class Page(Component):
        citry = engine
        template = """
            <main><c-Middle name="m1" /><c-Middle name="m2" /></main>
        """

    html = Page().render().serialize(deps_strategy="simple")

    # Depth first, like ordinary children: each parent's children before its next sibling.
    assert calls == ["m1", "m1.1", "m1.2", "m2", "m2.1", "m2.2"]
    assert (
        re.sub(r" data-cid-[^=]+=\"\"", "", html)
        .replace("\n", "")
        .replace(" ", "")
        .endswith("<main><b><i>m1.1</i><i>m1.2</i></b><b><i>m2.1</i><i>m2.2</i></b></main>")
    )


def test_ordinary_child_of_a_simple_vue_parent_sees_the_nearest_ordinary_parent() -> None:
    engine = Citry(autodiscover=False)
    seen: list[tuple[str | None, object]] = []

    class Child(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            parent = self.parent
            seen.append((None if parent is None else type(parent).__name__, self.inject("theme").value))
            return {}

        template = """
            <em>child</em>
        """

    class Row(Component):
        citry = engine
        simple = "vue"
        template = """
            <p><c-Child /></p>
        """

    class Page(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            self.provide("theme", value="dark")
            return {}

        template = """
            <main><c-Row /></main>
        """

    Page().render().serialize()
    # Row has no instance, so the child's parent is the page, and the child
    # still receives what the page provided.
    assert seen == [("Page", "dark")]


def test_error_in_a_child_names_the_simple_vue_parent_in_the_component_path() -> None:
    engine = Citry(autodiscover=False)

    class Child(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            raise ValueError("child failed")

        template = """
            <em>child</em>
        """

    class GrandChild(Component):
        citry = engine
        template = """
            <i>{{ missing_name }}</i>
        """

    class Row(Component):
        citry = engine
        simple = "vue"
        template = """
            <p><c-Child /></p>
        """

    class Page(Component):
        citry = engine
        template = """
            <main><c-Row /></main>
        """

    with pytest.raises(ValueError, match="child failed") as raised:
        Page().render()
    assert "Page > Row > Child" in str(raised.value)

    # A deeper error walks the parent links, and still finds Row.
    def no_data(_self: Any, _kwargs: Any, _slots: Any) -> dict[str, Any]:
        return {}

    Child.template_data = no_data  # type: ignore[method-assign]
    Child.template = """
        <c-GrandChild />
    """
    with pytest.raises(Exception, match="missing_name") as raised_deeper:
        Page().render()
    assert "Page > Row > Child > GrandChild" in str(raised_deeper.value)


def test_simple_vue_root_renders_the_children_it_calls() -> None:
    def root(*, mode: Any) -> type[Component]:
        engine = Citry(autodiscover=False)

        class Child(Component):
            citry = engine

            class Kwargs:
                text: str

            template = """
                <em>{{ text }}</em>
            """
            js = "$component({})"

        class Root(Component):
            citry = engine
            simple = mode
            template = """
                <p><c-Child c-text="label" /></p>
            """

        del Child
        return Root

    simple_html = root(mode="vue")(label="hi").render().serialize(deps_strategy="simple")
    ordinary_html = root(mode=False)(label="hi").render().serialize(deps_strategy="simple")
    assert _normalized(simple_html) == _normalized(ordinary_html)
    assert '<em data-cid-X="">hi</em>' in _normalized(simple_html)
    simple_document = root(mode="vue")(label="hi").render().serialize()
    ordinary_document = root(mode=False)(label="hi").render().serialize()
    assert _host(simple_document) == _host(ordinary_document)


@pytest.mark.parametrize(
    ("call", "message"),
    [
        ('<c-Child c-bind="{}" />', "c-bind"),
        ("<c-Child>content</c-Child>", "passes content"),
        ('<c-Child @click="go" />', "Vue bindings"),
    ],
)
def test_calls_the_instance_free_template_cannot_make_are_rejected(call: str, message: str) -> None:
    engine = Citry(autodiscover=False)
    rendered: list[str] = []

    class Child(Component):
        citry = engine
        template = """
            <em>child</em>
        """

    class Row(Component):
        citry = engine
        simple = "vue"
        template = f"""
            <p>{call}</p>
        """

        @staticmethod
        def template_data(_kwargs: Any, _slots: Any) -> dict[str, Any]:
            rendered.append("Row")
            return {}

    class Page(Component):
        citry = engine
        template = """
            <main><c-Row /></main>
        """

    with pytest.raises(TypeError, match=f"Component Row simple='vue' is unsupported: .*{message}"):
        Page().render()
    # The class check fails before the data callback runs.
    assert rendered == []


@pytest.mark.parametrize("kind", ["simple", "transparent"])
def test_child_that_renders_into_its_callers_template_is_rejected(kind: str) -> None:
    engine = Citry(autodiscover=False)

    class Child(Component):
        citry = engine
        template = """
            <em>child</em>
        """
        if kind == "simple":
            simple = True
        else:
            transparent = True

    class Row(Component):
        citry = engine
        simple = "vue"
        template = """
            <p><c-Child /></p>
        """

    class Page(Component):
        citry = engine
        template = """
            <main><c-Row /></main>
        """

    with pytest.raises(TypeError, match=r"Component Row simple='vue' is unsupported: its template calls Child"):
        Page().render()


def test_children_bring_their_own_scripts_and_styles() -> None:
    page = _row_app(row_mode="vue", badge_mode="vue", row_template=UNCONDITIONAL)
    html = page(rows=ROWS).render().serialize(deps_strategy="simple")
    assert ".badge { color: red; }" in html
    ordinary = (
        _row_app(row_mode=False, badge_mode="vue", row_template=UNCONDITIONAL)(rows=ROWS)
        .render()
        .serialize(deps_strategy="simple")
    )
    assert _normalized(html) == _normalized(ordinary)


def _events_app(*, row_mode: Any) -> type[Component]:
    """Build a page whose simple rows call an ordinary child that handles Events."""
    engine = Citry(secret="simple-vue-child-events-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Counter(Component):
        citry = engine

        class Kwargs:
            start: str

        class Events:
            def bump(self) -> None:
                return None

        template = """
            <button class="counter" @c-click="bump">{{ start }}</button>
        """

    class Row(Component):
        citry = engine
        simple = row_mode

        class Kwargs:
            row: dict

        template = """
            <li><c-Counter c-start="row['title']" /></li>
        """

    class Page(Component):
        citry = engine

        class Kwargs:
            rows: list

        template = """
            <ul><c-Row c-for="row in rows" #c-key="row['id']" c-row="row" /></ul>
        """

    del Counter, Row
    return Page


def test_events_inside_a_child_of_a_simple_vue_parent_are_sent_to_the_browser() -> None:
    simple = _events_app(row_mode="vue")(rows=ROWS).render().serialize()
    ordinary = _events_app(row_mode=False)(rows=ROWS).render().serialize()

    assert _host(simple) == _host(ordinary)
    # Each counter keeps its own Events binding, addressed to its own occurrence.
    assert simple.count('"bump"') == ordinary.count('"bump"') > 0
    assert simple.count('"eventBindings"') == ordinary.count('"eventBindings"') == len(ROWS)


def test_cached_ordinary_ancestor_of_a_simple_vue_parent_renders_the_same_html() -> None:
    def page(*, row_mode: Any) -> type[Component]:
        page_class = _row_app(row_mode=row_mode, badge_mode=False, row_template=UNCONDITIONAL)

        class CachedPage(page_class):  # type: ignore[valid-type, misc]
            class Cache:
                enabled = True

        return CachedPage

    simple_page = page(row_mode="vue")
    first = _normalized(simple_page(rows=ROWS).render().serialize(deps_strategy="simple"))
    second = _normalized(simple_page(rows=ROWS).render().serialize(deps_strategy="simple"))
    ordinary = _normalized(page(row_mode=False)(rows=ROWS).render().serialize(deps_strategy="simple"))
    assert first == second == ordinary


@pytest.mark.parametrize("child_mode", [False, "vue"])
@pytest.mark.parametrize("entry", ["root", "expression"])
def test_simple_vue_root_or_embedded_parent_calls_children_of_either_mode(child_mode: Any, entry: str) -> None:
    def page(*, mode: Any) -> Any:
        engine = Citry(autodiscover=False)

        class Leaf(Component):
            citry = engine
            simple = child_mode
            template = """
                <i>{{ text }}</i>
            """

        class Row(Component):
            citry = engine
            simple = mode
            template = """
                <p><c-Leaf text="one" /><c-Leaf c-text="label" /></p>
            """
            js = "$component({data(){return {open:false}}})"

        class Page(Component):
            citry = engine

            def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
                return {"row": Row(label="two")}

            template = """
                <main>{{ row }}</main>
            """

        del Leaf
        return Row(label="two") if entry == "root" else Page()

    simple = page(mode="vue").render()
    ordinary = page(mode=False).render()
    assert _normalized(simple.serialize(deps_strategy="simple")) == _normalized(
        ordinary.serialize(deps_strategy="simple")
    )
    if entry == "root":
        # A simple='vue' element inserted from a Python expression is not yet
        # supported in interactive output, with or without child calls.
        assert _host(simple.serialize()) == _host(ordinary.serialize())
