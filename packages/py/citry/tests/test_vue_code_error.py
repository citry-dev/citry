"""
Python data cannot set an attribute name that Vue reads as code.

A name starting with `v-`, `:`, `.`, `^`, `@`, or `#` (in any letter case)
is a Vue directive, binding, listener, or slot. When such a name comes from a
`c-bind` mapping, a `c-*` attribute, or an `on_attrs_resolved` hook, the
template fails while it renders with `citry.VueCodeError`, on HTML elements
and component tags, whether or not the page starts Vue. Every test calls
`render()` only, so each proves the error comes before any serialization.
"""

from __future__ import annotations

import traceback
from enum import Enum
from pathlib import Path
from typing import Any

import pytest

from citry import Citry, Component, Extension, VueCodeError
from citry._vue import leaf_program

# One key per Vue prefix, plus an uppercase spelling: HTML names ignore case.
VUE_KEYS = ["v-if", ":title", ".prop", "^title", "@click", "#item", "V-ON:click"]

# Names that look close to Vue syntax but are plain attributes.
PLAIN_KEYS = ["x-on:click", "x-bind:class", "data-v-x", "aria-label", "hx-on:click", "hx-on::after-request"]

_I18N = {"i18n": {"source_locale": "en-US", "locales": ("en-US", "cs-CZ")}}


def _page(
    template: str,
    data: dict[str, Any],
    *,
    vue: bool,
    app: Citry | None = None,
    simple: object = None,
    messages: str | None = None,
) -> type[Component]:
    """Build a page whose template reads ``data``; ``vue`` adds component JS so the page starts Vue."""
    app = app or Citry(autodiscover=False)

    class Child(Component):
        citry = app
        template = """
            <span>child</span>
        """

    body: dict[str, Any] = {
        "citry": app,
        "template": template,
        "template_data": staticmethod(lambda _kwargs, _slots: dict(data)),
    }
    if vue:
        body["js"] = "$component({})"
    if simple is not None:
        body["simple"] = simple
    if messages is not None:
        body["messages"] = messages
    return type("Page", (Component,), body)


def _render_error(page: type[Component]) -> VueCodeError:
    """Render ``page`` and return the VueCodeError that render() raised."""
    with pytest.raises(VueCodeError) as caught:
        page().render()
    # Code that catches the TypeError raised before this class existed keeps working.
    assert isinstance(caught.value, TypeError)
    return caught.value


def test_vue_code_error_is_public_and_a_type_error() -> None:
    import citry

    assert "VueCodeError" in citry.__all__
    assert issubclass(citry.VueCodeError, TypeError)


class TestHtmlElement:
    @pytest.mark.parametrize("vue", [False, True], ids=["no-vue", "vue"])
    @pytest.mark.parametrize("key", VUE_KEYS)
    def test_c_bind_key_fails_at_render(self, key: str, vue: bool) -> None:
        page = _page('<div c-bind="attrs">x</div>', {"attrs": {key: "go()"}}, vue=vue)
        assert f"c-bind on <div> sets {key!r}, which Vue would read as code." in str(_render_error(page))

    @pytest.mark.parametrize("vue", [False, True], ids=["no-vue", "vue"])
    @pytest.mark.parametrize("key", VUE_KEYS)
    def test_c_attribute_fails_at_render(self, key: str, vue: bool) -> None:
        page = _page(f'<div c-{key}="value">x</div>', {"value": "go()"}, vue=vue)
        assert f"'c-{key}' on <div> sets {key!r}, which Vue would read as code." in str(_render_error(page))

    @pytest.mark.parametrize("removed", [None, False])
    def test_c_bind_key_fails_even_with_a_removing_value(self, removed: object) -> None:
        # None would remove the listener the template wrote, so the key fails
        # whatever its value.
        page = _page('<div @click="save()" c-bind="attrs">x</div>', {"attrs": {"@click": removed}}, vue=True)
        assert "c-bind on <div> sets '@click'" in str(_render_error(page))

    def test_message_names_the_key_the_tag_and_the_fix(self) -> None:
        page = _page('<div c-bind="attrs">x</div>', {"attrs": {"@click": "go()"}}, vue=False)
        message = str(_render_error(page)).split("\n")[1]
        assert message == (
            "c-bind on <div> sets '@click', which Vue would read as code. Python data from c-bind, "
            "c-* attributes, and extension hooks may not set a name that starts with v-, :, ., ^, @, or #, "
            "even on a page that does not use Vue. Write Vue directives, bindings, and listeners directly "
            "in the template."
        )

    def test_citry_events_binding_from_c_bind_is_not_vue_code(self) -> None:
        # `@c-*` is Citry's own Events binding, which the Events extension
        # turns into its own markup, so c-bind may still carry it.
        app = Citry(autodiscover=False)

        class Page(Component):
            citry = app
            template = """
                <button c-bind="attrs">go</button>
            """

            class Events:
                def go(self) -> None:
                    return None

            def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
                return {"attrs": {"@c-click": "go"}}

        Page().render()

    @pytest.mark.parametrize("key", ["@C-click", ":C-value", "#C-key"])
    def test_uppercase_citry_prefix_is_vue_code(self, key: str) -> None:
        # Only the exact lowercase `@c-`, `:c-`, and `#c-` name Citry's own
        # bindings; Vue reads `@C-click` as a listener for `C-click`.
        page = _page('<div c-bind="attrs">x</div>', {"attrs": {key: "go"}}, vue=False)
        assert f"c-bind on <div> sets {key!r}" in str(_render_error(page))

    def test_str_enum_key_is_checked_like_its_text(self) -> None:
        # `StrEnum` needs Python 3.11. A `str` mixin enum member holds the same
        # text, which is all this check reads.
        class Name(str, Enum):
            CLICK = "@click"

        page = _page('<div c-bind="attrs">x</div>', {"attrs": {Name.CLICK: "go()"}}, vue=False)
        assert "c-bind on <div> sets '@click'" in str(_render_error(page))

    @pytest.mark.parametrize("vue", [False, True], ids=["no-vue", "vue"])
    def test_str_subclass_cannot_hide_its_text_from_the_check(self, vue: bool) -> None:
        # A subclass that lies through `casefold` or `startswith` still names
        # `@click` in the HTML, so the check must read the real text.
        class Disguised(str):
            __slots__ = ()

            def casefold(self) -> str:
                return "title"

            def startswith(self, *_args: object, **_kwargs: object) -> bool:
                return False

        page = _page('<div c-bind="attrs">x</div>', {"attrs": {Disguised("@click"): "go()"}}, vue=vue)
        assert "c-bind on <div> sets '@click'" in str(_render_error(page))

    def test_a_key_checked_once_does_not_let_a_later_key_through(self) -> None:
        # Good keys are cached on the node after their first check. A later
        # render of the same node with a Vue name must still fail, every time.
        app = Citry(autodiscover=False)

        class Page(Component):
            citry = app
            template = """
                <div c-bind="attrs">x</div>
            """

            def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
                return {"attrs": kwargs["attrs"]}

        assert 'title="ok"' in Page(attrs={"title": "ok"}).render().serialize(deps_strategy="ignore")
        for _ in range(2):
            with pytest.raises(VueCodeError, match="c-bind on <div> sets '@click'"):
                Page(attrs={"title": "ok", "@click": "go()"}).render()

    @pytest.mark.parametrize("key", PLAIN_KEYS)
    def test_plain_names_close_to_vue_syntax_still_render(self, key: str) -> None:
        page = _page('<div c-bind="attrs">x</div>', {"attrs": {key: "go()"}}, vue=False)
        html = page().render().serialize(deps_strategy="ignore")
        assert f'{key}="go()"' in html


class TestComponentTag:
    @pytest.mark.parametrize("vue", [False, True], ids=["no-vue", "vue"])
    @pytest.mark.parametrize("key", VUE_KEYS)
    def test_c_bind_key_fails_at_render(self, key: str, vue: bool) -> None:
        page = _page('<div><c-child c-bind="attrs" /></div>', {"attrs": {key: "go()"}}, vue=vue)
        assert f"c-bind on <c-child> sets {key!r}, which Vue would read as code." in str(_render_error(page))

    @pytest.mark.parametrize("vue", [False, True], ids=["no-vue", "vue"])
    @pytest.mark.parametrize("key", ["v-if", ":title", "@click"])
    def test_c_attribute_fails_at_render(self, key: str, vue: bool) -> None:
        # The template parser already rejects the `c-` form of a directive a
        # component tag can never carry (`c-#item`, `c-.prop`, `c-^title`), so
        # only the forms it lets through reach the render.
        page = _page(f'<div><c-child c-{key}="value" /></div>', {"value": "go()"}, vue=vue)
        assert f"'c-{key}' on <c-child> sets {key!r}" in str(_render_error(page))

    @pytest.mark.parametrize(
        ("key", "hint"),
        [
            ("#item", "Pass slot content with '<c-fill name=\"...\">' inside the component tag."),
            (".prop", "Pass the value as a component prop with ':name=\"...\"'."),
            ("^title", "Pass the value as a component prop with ':name=\"...\"'."),
            ("v-for", "Repeat the component with '<c-for>'."),
            ("@click", "Write Vue directives, bindings, and listeners directly in the template."),
        ],
    )
    def test_message_names_the_fix_for_a_component_tag(self, key: str, hint: str) -> None:
        page = _page('<div><c-child c-bind="attrs" /></div>', {"attrs": {key: "go()"}}, vue=False)
        assert str(_render_error(page)).split("\n")[1].endswith(hint)


class TestDynamicElement:
    @pytest.mark.parametrize("vue", [False, True], ids=["no-vue", "vue"])
    @pytest.mark.parametrize("key", VUE_KEYS)
    def test_c_bind_key_fails_at_render(self, key: str, vue: bool) -> None:
        page = _page(
            '<div><c-element c-is="tag" c-bind="attrs" /></div>',
            {"tag": "p", "attrs": {key: "go()"}},
            vue=vue,
        )
        assert f"c-bind on <c-element> sets {key!r}" in str(_render_error(page))

    @pytest.mark.parametrize("key", VUE_KEYS)
    def test_c_attribute_fails_at_render(self, key: str) -> None:
        page = _page(f'<div><c-element c-is="tag" c-{key}="value" /></div>', {"tag": "p", "value": "go()"}, vue=False)
        assert f"'c-{key}' on <c-element> sets {key!r}" in str(_render_error(page))


class TestOtherRenderPaths:
    @pytest.mark.parametrize("key", VUE_KEYS)
    def test_simple_true_component(self, key: str) -> None:
        page = _page('<div c-bind="attrs">x</div>', {"attrs": {key: "go()"}}, vue=False, simple=True)
        assert f"c-bind on <div> sets {key!r}" in str(_render_error(page))

    @pytest.mark.parametrize("key", VUE_KEYS)
    def test_simple_vue_component(self, key: str) -> None:
        page = _page('<div c-bind="attrs">x</div>', {"attrs": {key: "go()"}}, vue=False, simple="vue")
        assert f"c-bind on <div> sets {key!r}" in str(_render_error(page))

    @pytest.mark.parametrize("plan_limit", [None, 0], ids=["planned-rows", "full-merge"])
    def test_simple_vue_rows_from_a_list(self, monkeypatch: pytest.MonkeyPatch, plan_limit: int | None) -> None:
        # Rows of a simple='vue' child resolve their root c-bind through a
        # per-key-set plan; a limit of 0 sends each row through the full merge.
        if plan_limit is not None:
            monkeypatch.setattr(leaf_program, "_ROOT_SPREAD_PLAN_LIMIT", plan_limit)
        app = Citry(autodiscover=False)

        class Row(Component):
            citry = app
            simple = "vue"
            template = """
                <article c-bind="attrs">{{ title }}</article>
            """
            js = """
                $component({data(){return {open: true};}});
            """

            @staticmethod
            def template_data(kwargs: Any, _slots: Any) -> dict[str, Any]:
                return {"attrs": kwargs["attrs"], "title": kwargs["title"]}

        class Page(Component):
            citry = app
            template = """
                <main><c-Row c-for="row in rows" c-attrs="row" title="t" /></main>
            """

            def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
                return {"rows": kwargs["rows"]}

        good = [{"id": "a"}, {"id": "b"}]
        bad = [*good, {"@click": "go()"}]
        # The first render stores a plan for the good key set; later renders
        # reuse it, and the bad key set must still fail on every render.
        assert 'id="a"' in Page(rows=good).render().serialize(deps_strategy="ignore")
        for _ in range(2):
            with pytest.raises(VueCodeError, match="c-bind on <article> sets '@click'"):
                Page(rows=bad).render()

    def test_i18n_attribute_binding_path(self) -> None:
        # A `$c-tr` binding sends the element through the i18n resolver, which
        # reads c-bind and c-* itself instead of the ordinary node.
        for template, expected in [
            ("""<button c-title="tr('save')" $c-tr:save[title] c-bind="attrs"></button>""", "c-bind on <button>"),
            ("""<button c-title="tr('save')" $c-tr:save[title] c-v-if="value"></button>""", "'c-v-if' on <button>"),
        ]:
            page = _page(
                template,
                {"attrs": {"@click": "go()"}, "value": "go()"},
                vue=False,
                app=Citry(autodiscover=False, extensions_defaults=_I18N),
                messages="save = Save",
            )
            error = _render_error(page)
            assert expected in str(error)
            raised_in = traceback.extract_tb(error.__traceback__)
            assert any(Path(frame.filename).parts[-2:] == ("i18n", "bindings.py") for frame in raised_in)


class TestExtensionHook:
    @staticmethod
    def _app(hook: Any) -> Citry:
        class Hook(Extension):
            name = "vue_code_hook"
            on_attrs_resolved = hook

        return Citry(autodiscover=False, extensions=[Hook])

    @pytest.mark.parametrize("vue", [False, True], ids=["no-vue", "vue"])
    def test_hook_that_adds_a_vue_name_fails(self, vue: bool) -> None:
        def add(_self: Any, ctx: Any) -> None:
            ctx.attrs["@click"] = "go()"

        page = _page('<div c-title="title">x</div>', {"title": "t"}, vue=vue, app=self._app(add))
        message = str(_render_error(page)).split("\n")[1]
        assert message == (
            "An on_attrs_resolved extension hook sets '@click' on <div>, which Vue would read as code. "
            "Python data from c-bind, c-* attributes, and extension hooks may not set a name that starts with "
            "v-, :, ., ^, @, or #, even on a page that does not use Vue. Return only plain attribute names "
            "from the hook, and write Vue directives, bindings, and listeners directly in the template."
        )

    def test_hook_that_changes_a_written_vue_binding_fails(self) -> None:
        def change(_self: Any, ctx: Any) -> dict[str, Any]:
            return {**ctx.attrs, "@click": "attack()"}

        page = _page('<div @click="save()" c-title="title">x</div>', {"title": "t"}, vue=False, app=self._app(change))
        assert "extension hook sets '@click' on <div>" in str(_render_error(page))

    def test_hook_may_keep_or_remove_a_written_vue_binding(self) -> None:
        def keep(_self: Any, ctx: Any) -> dict[str, Any]:
            return {**ctx.attrs, "data-x": "1"}

        def remove(_self: Any, ctx: Any) -> None:
            ctx.attrs.pop("@click", None)

        template = '<div @click="save()" c-title="title">x</div>'
        kept = _page(template, {"title": "t"}, vue=False, app=self._app(keep))
        removed = _page(template, {"title": "t"}, vue=False, app=self._app(remove))
        # Both render; neither puts Python data into Vue code.
        kept_html = kept().render().serialize(deps_strategy="ignore")
        removed_html = removed().render().serialize(deps_strategy="ignore")
        assert '@click="save()"' in kept_html
        assert 'data-x="1"' in kept_html
        assert "@click" not in removed_html
