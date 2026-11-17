"""
Rules for the attribute names `ref`, `ref_for`, and `ref_key` when data chooses them.

Given one of these names, Vue does not set an attribute. It stores the element
in the component's own value of that name (a `setup()` value), which could
replace a value the component shows with `v-html` or uses to decide whether to
show something. So a name from data (a `c-bind` mapping key, or a name an
`on_attrs_resolved` hook adds) may not be one, in any letter case, on any
render path. A `ref="x"` the author wrote on a plain element is not data, so
it keeps working.
"""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, Component, Extension
from citry._vue import leaf_program

if TYPE_CHECKING:
    from collections.abc import Callable

REF_KEYS = ["ref", "REF", "Ref", "ref_for", "Ref_For", "ref_key", "REF_KEY"]
REFUSAL = "srcdoc, ref, ref_for, or ref_key"

# Paths: the static writer, `simple=True`, the component cache, a `<c-for>` loop, and the Vue writer.
PATHS = ("static", "simple", "cache", "loop", "vue")

_names = itertools.count()


def _data_method(values: dict[str, Any], *, simple: bool) -> Any:
    """Return a `template_data` that gives the template `values`, in the form the component kind needs."""
    if simple:

        def simple_data(kwargs, slots):
            return dict(values)

        # A `simple=True` component calls `template_data` without an instance.
        return staticmethod(simple_data)

    def template_data(self, kwargs, slots):
        return dict(values)

    return template_data


def _render(
    path: str,
    body: str,
    data: dict[str, Any],
    *,
    extensions: list[type[Extension]] | None = None,
    data_from_app: Callable[[Citry], dict[str, Any]] | None = None,
) -> str:
    """Render `body` as a child component on one path and return the page HTML. A cached component renders twice."""
    app = Citry(autodiscover=False, extensions=extensions or [], secret="ref-name-test-secret" * 2)
    app.set_mounted_prefix("/citry")
    app.initialize()
    values = dict(data)
    if data_from_app is not None:
        # Some values, such as an element built from a built-in, need the engine itself.
        values.update(data_from_app(app))
    if path == "loop":
        # A <c-for> around the element makes it render inside a loop.
        body = '<c-for each="n in one">' + body + "</c-for>"
        values["one"] = [1]
    attrs: dict[str, Any] = {
        "citry": app,
        "template": body,
        "template_data": _data_method(values, simple=path == "simple"),
    }
    if path == "simple":
        attrs["simple"] = True
    if path == "vue":
        # The `js` makes the component a Vue component, so it takes the Vue writer.
        attrs["js"] = """
            $component({});
        """
    if path == "cache":
        attrs["Cache"] = type("Cache", (), {"enabled": True, "ttl": 300, "version": 1})
    inner = type(f"Inner{next(_names)}", (Component,), attrs)
    page = type(
        f"Page{next(_names)}",
        (Component,),
        {"citry": app, "template": f"<main><c-{inner.__name__} /></main>"},
    )
    html = page().render().serialize()
    if path == "cache":
        # The second render replays the first from the cache.
        html = page().render().serialize()
    return html


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("key", REF_KEYS)
@pytest.mark.parametrize(
    "template",
    ['<a c-bind="attrs">x</a>', '<c-element c-is="t" c-bind="attrs">x</c-element>'],
    ids=["plain-element", "c-element"],
)
def test_spread_keys_may_not_be_vue_ref_names(template: str, key: str, path: str) -> None:
    # Every path reaches the same check, so a path that skipped it would let data pick a Vue ref.
    with pytest.raises(ValueError, match=REFUSAL):
        _render(path, template, {"attrs": {key: "html"}, "t": "a"})


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("key", ["key", "reference", "data-ref", "referrer", "refs"])
@pytest.mark.parametrize(
    "template",
    ['<a c-bind="attrs">x</a>', '<c-element c-is="t" c-bind="attrs">x</c-element>'],
    ids=["plain-element", "c-element"],
)
def test_spread_keys_that_only_look_like_ref_still_render(template: str, key: str, path: str) -> None:
    # Control: the refusal covers the three exact names, not names that merely start with `ref`.
    html = _render(path, template, {"attrs": {key: "html"}, "t": "a"})

    # A Vue page ships its markup for the browser to build, so only the static paths show the attribute.
    if path != "vue":
        assert f'{key}="html"' in html


@pytest.mark.parametrize("path", PATHS)
def test_an_is_key_in_a_spread_still_renders(path: str) -> None:
    # Control: `is` is an ordinary attribute on a plain element, and on a `<c-element>` it picks the tag.
    _render(path, '<a c-bind="attrs">x</a>', {"attrs": {"is": "html"}})
    _render(path, '<c-element c-bind="attrs">x</c-element>', {"attrs": {"is": "section"}})


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("key", ["ref", "REF", "ref_for", "ref_key"])
@pytest.mark.parametrize(
    "template",
    ['<a c-{key}="r">x</a>', '<c-element c-is="t" c-{key}="r">x</c-element>'],
    ids=["plain-element", "c-element"],
)
def test_a_c_ref_attribute_may_not_take_its_value_from_data(template: str, key: str, path: str) -> None:
    # The author wrote the name, but the value would choose which `setup()` value Vue replaces.
    with pytest.raises((ValueError, RuntimeError), match=r"Vue replaces|came from Python data|ref_key"):
        _render(path, template.format(key=key), {"r": "html", "t": "a"})


@pytest.mark.parametrize("path", PATHS)
def test_a_ref_written_in_the_template_on_a_c_element_still_renders(path: str) -> None:
    # Citry UI's CSidebar writes `ref="root"` on its `<c-element>`; a plain text ref is the author's.
    html = _render(path, '<c-element c-is="t" ref="mine">x</c-element>', {"t": "a"})

    assert "x</a>" in html


@pytest.mark.parametrize("path", PATHS)
def test_a_python_call_of_the_element_builtin_may_not_pass_a_ref(path: str) -> None:
    # A direct call has no template, so no `ref` it passes was written as plain text on a tag.
    def element_value(app: Citry) -> dict[str, Any]:
        return {"el": app.get("element")(**{"is": "a", "ref": "html", "href": "x:y"})}

    with pytest.raises(ValueError, match=REFUSAL):
        _render(path, "<div>{{ el }}</div>", {}, data_from_app=element_value)


@pytest.mark.parametrize("path", ["static", "vue"])
def test_a_ref_written_in_the_template_on_a_plain_element_still_renders(path: str) -> None:
    # The author wrote the name, so it is not data. Only a name chosen at render time is refused.
    html = _render(path, '<a ref="mine">x</a>', {})

    assert "x</a>" in html


_HOOK_TEMPLATES = {
    # A dynamic attribute makes the element go through the attribute hooks.
    "plain": '<a c-title="t">x</a>',
    "c-element": '<c-element c-is="t" c-title="t">x</c-element>',
}


def _render_with_hook(template: str, name: str, *, vue: bool) -> str:
    """Render `template` with an extension whose `on_attrs_resolved` hook adds the attribute `name`."""

    class Hook(Extension):
        name = "refhook"

        def on_attrs_resolved(self, ctx):
            # The hook returns normally, so a refusal can only come from Citry's own check.
            return {**ctx.attrs, name: "x"}

    app = Citry(autodiscover=False, extensions=[Hook])

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return {"t": "a"}

    Page.template = template
    if vue:
        Page.js = """
            $component({});
        """
    return str(Page())


@pytest.mark.parametrize("vue", [False, True], ids=["static", "vue"])
@pytest.mark.parametrize("shape", list(_HOOK_TEMPLATES))
@pytest.mark.parametrize("name", ["ref", "REF", "ref_for", "ref_key"])
def test_attrs_hooks_may_not_add_vue_ref_names(shape: str, name: str, vue: bool) -> None:
    # A hook is extension code, not the template author, so a name it adds is data.
    with pytest.raises(ValueError, match=REFUSAL):
        _render_with_hook(_HOOK_TEMPLATES[shape], name, vue=vue)


@pytest.mark.parametrize("shape", list(_HOOK_TEMPLATES))
def test_attrs_hooks_may_still_add_a_name_that_only_looks_like_ref(shape: str) -> None:
    # Control: the same hook with a harmless name renders.
    assert 'reference="x"' in _render_with_hook(_HOOK_TEMPLATES[shape], "reference", vue=False)


# A `simple="vue"` component whose root element holds a `c-bind` takes a shortcut: it works out the
# attribute names once per set of keys and reuses the result. The shortcut must refuse the same
# names as the full per-row merge, so it is run both ways.
ROW_TEMPLATE = """
<article c-bind="row_attrs">{{ title }}</article>
"""


def _build_rows(attrs_per_row: list[dict[str, object]]) -> tuple[type[Component], list[dict[str, Any]]]:
    counter = itertools.count()
    app = Citry(autodiscover=False, id_generator=lambda: f"r{next(counter)}")
    app.set_mounted_prefix("/citry")

    class Row(Component):
        citry = app
        simple = "vue"
        template = ROW_TEMPLATE
        js = """
            $component({data(){return {open: true};}});
        """

        class Kwargs:
            row: dict

        @staticmethod
        def template_data(kwargs: Any, _slots: Any) -> dict[str, Any]:
            return {"title": "t", "row_attrs": kwargs.row}

    class Page(Component):
        citry = app
        template = """<main><c-Row c-for="row in rows" #c-key="row['id']" c-row="row" /></main>"""

    rows = [{"id": f"r{index}", **attrs} for index, attrs in enumerate(attrs_per_row)]
    return Page, rows


def _outcome(function: Any) -> tuple[str, str]:
    """Return ("ok", output) or the error type and message, for side-by-side comparison."""
    try:
        return ("ok", function())
    except Exception as error:  # noqa: BLE001 - the comparison covers every error type
        return (type(error).__name__, str(error))


@pytest.mark.usefixtures("python_render_path")
@pytest.mark.parametrize("key", REF_KEYS)
def test_root_spread_plans_refuse_vue_ref_names_like_the_full_merge(monkeypatch: pytest.MonkeyPatch, key: str) -> None:
    def render() -> tuple[str, str]:
        page, rows = _build_rows([{"title": "ok"}, {key: "x"}])
        return _outcome(lambda: page(rows=rows).render().serialize())

    planned = render()
    # A plan limit of zero sends every row through the full per-row merge.
    monkeypatch.setattr(leaf_program, "_ROOT_SPREAD_PLAN_LIMIT", 0)
    full_merge = render()

    assert planned[0] != "ok"
    assert planned == full_merge
