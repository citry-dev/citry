"""The first executable contract for public instance-free Vue leaves."""

from __future__ import annotations

import gc
import itertools
import json
import re
import weakref
from pathlib import Path
from typing import Any

import pytest

from citry import Citry, Component, Extension, component_render
from citry.component_like import ComponentLike


def test_simple_vue_static_leaf_has_distinct_occurrences_and_component_js(monkeypatch: pytest.MonkeyPatch) -> None:
    app = Citry()
    callback_calls: list[tuple[object, object]] = []

    class Leaf(Component):
        citry = app
        simple = "vue"
        template = "<button>open</button>"
        js = "$component({data(){return {open:true}}})"

        class Slots:
            pass

        @staticmethod
        def template_data(kwargs: object, slots: object) -> dict[str, object]:
            callback_calls.append((kwargs, slots))
            return {}

    class Page(Component):
        citry = app
        template = "<main><c-leaf/><c-leaf/></main>"

    from citry.component import Component as ComponentBase

    component_init = ComponentBase.__init__
    leaf_instances: list[object] = []

    def observe_init(self: object, *args: object, **kwargs: object) -> None:
        if type(self) is Leaf:
            leaf_instances.append(self)
        component_init(self, *args, **kwargs)

    monkeypatch.setattr(ComponentBase, "__init__", observe_init)

    rendered = Page().render()
    html = rendered.serialize()

    assert len(callback_calls) == 2
    assert leaf_instances == []
    occurrence_ids = re.findall(
        r'"renderId":"([^"]+)","serverData":\{\},"typeKey":"Leaf_[^"]+"',
        html,
    )
    assert len(occurrence_ids) == 2
    assert len(set(occurrence_ids)) == 2
    assert "registerTypeOptions" in html
    assert "open:true" in html


def test_simple_vue_rejects_reserved_js_data_key_without_an_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    app = Citry()

    class Leaf(Component):
        citry = app
        simple = "vue"
        template = "<button>open</button>"

        class Slots:
            pass

        @staticmethod
        def js_data(_kwargs: object, _slots: object) -> dict[str, object]:
            return {"_open": True}

    class Page(Component):
        citry = app
        template = "<main><c-leaf/></main>"

    from citry.component import Component as ComponentBase

    component_init = ComponentBase.__init__
    leaf_instances: list[object] = []

    def observe_init(self: object, *args: object, **kwargs: object) -> None:
        if type(self) is Leaf:
            leaf_instances.append(self)
        component_init(self, *args, **kwargs)

    monkeypatch.setattr(ComponentBase, "__init__", observe_init)

    with pytest.raises(ValueError, match=r"component Leaf .*contains the key '_open'.*'open'"):
        Page().render()
    # No Leaf instance means the instance-free simple='vue' path raised.
    assert leaf_instances == []


def test_simple_true_remains_caller_owned_static_html() -> None:
    app = Citry()

    class Inline(Component):
        citry = app
        simple = True
        template = "<span>inline</span>"

    class Page(Component):
        citry = app
        template = "<main><c-inline/></main>"

    html = Page().render().serialize(deps_strategy="ignore")
    assert re.fullmatch(r'<main data-cid-[^=]+=""><span>inline</span></main>', html)


def test_simple_vue_direct_root_keeps_owning_engine_and_policy() -> None:
    app = Citry()

    class Root(Component):
        citry = app
        simple = "vue"
        template = "<main>root fallback</main>"
        js = "globalThis.rootReady = true;"

    rendered = Root().render()

    assert rendered.owner_citry is app
    assert rendered.context.component is None
    result = rendered.serialize_result()
    html = result.html
    assert "root fallback" in html
    assert "rootReady" in html
    assert "registerTypeOptions" in html
    assert re.search(r'"renderId":"[^"]+","serverData":\{\},"typeKey":"Root_', html)
    assert rendered.serialize(deps_strategy="simple").find("root fallback") >= 0
    assert "rootReady" not in rendered.serialize(deps_strategy="simple")
    assert rendered.serialize(deps_strategy="ignore").find("root fallback") >= 0
    assert "rootReady" not in rendered.serialize(deps_strategy="ignore")

    omitted = Citry(security_javascript="omit")

    class OmittedRoot(Component):
        citry = omitted
        simple = "vue"
        template = "<main>root fallback</main>"
        js = "globalThis.rootReady = true;"

    omitted_html = OmittedRoot().render().serialize()
    assert "root fallback" in omitted_html
    assert "rootReady" not in omitted_html
    assert re.search(r"data-cid-[A-Za-z0-9_-]+=\"\"", omitted_html)
    assert "registerTypeOptions" not in omitted_html
    assert "<script" not in omitted_html

    forbidden = Citry(security_javascript="forbid")

    class ForbiddenRoot(Component):
        citry = forbidden
        simple = "vue"
        template = "<main>root fallback</main>"
        js = "globalThis.rootReady = true;"

    with pytest.raises(ValueError, match="executable component Script"):
        ForbiddenRoot().render().serialize()


def test_simple_vue_direct_root_hydrates_a_bound_title_that_replaces_the_static_one() -> None:
    app = Citry(autodiscover=False)

    class Root(Component):
        citry = app
        simple = "vue"
        template = '<main><button title="server-only" :title="title">x</button></main>'
        js = "$component({data(){return {title:null}}});"

    rendered = Root().render()
    ssr_html = rendered.serialize(ssr=True)
    csr_html = rendered.serialize(ssr=False)
    plain_html = rendered.serialize(deps_strategy="simple")

    # Vue's render keeps only the bound `title` (null, so no attribute), and
    # the key is in the render's dynamic props, which Vue sets itself while
    # hydrating. The server leaves the attribute out, as Vue's render does.
    assert '"hydrate":true' in ssr_html
    assert re.search(r'<div id="citry-vue-[^"]+"><main><button>x</button></main></div>', ssr_html)
    assert "server-only" not in ssr_html.split("<script", 1)[0]
    assert '"hydrate":true' not in csr_html
    assert '<button title="server-only" :title="title">x</button>' in plain_html


def test_simple_vue_direct_root_shells_crlf_text_for_ssr_without_rewriting_source() -> None:
    app = Citry(autodiscover=False)

    class Root(Component):
        citry = app
        simple = "vue"
        template = "<main>left{{ value }}right</main>"
        js = "$component({});"

    source_value = "\r\n"
    rendered = Root(value=source_value).render()
    ssr_html = rendered.serialize(ssr=True)
    plain_html = rendered.serialize(deps_strategy="simple")

    # The HTML parser turns CR into LF, so the server cannot write text Vue
    # would read back unchanged: <main> is a shell Vue fills in. Until then
    # it shows the text as the parser reads it.
    assert '"hydrate":true' in ssr_html
    assert re.search(
        r'<div id="citry-vue-[^"]+"><main data-allow-mismatch="children">left\r\nright</main></div>', ssr_html
    )
    assert f"left{source_value}right" in plain_html


def test_simple_vue_compiles_transformed_leaf_plan_once() -> None:
    compiled_leaves: list[str] = []

    class CountCompiledLeaf(Extension):
        name = "count_simple_vue_compiled_leaf"

        def on_template_compiled(self, ctx: Any) -> None:
            if ctx.component_class.__name__ == "Leaf":
                compiled_leaves.append(ctx.template_id)

    app = Citry(extensions=[CountCompiledLeaf])

    class Leaf(Component):
        citry = app
        simple = "vue"
        template = "<button>open</button>"
        js = "$component({data(){return {open:true}}})"

    class Page(Component):
        citry = app
        template = "<main><c-leaf/><c-leaf/></main>"

    html = Page().render().serialize(deps_strategy="ignore")
    assert "open" in html
    assert len(compiled_leaves) == 1


def test_simple_vue_evaluates_context_free_text_control_flow_and_attrs() -> None:
    app = Citry(template_globals={"site": "from engine"})

    class Root(Component):
        citry = app
        simple = "vue"
        template = (
            '<main c-title="title">{{ title }} {{ site }}'
            '<c-if cond="show"><b>shown</b></c-if>'
            '<c-for each="item in items"><i>{{ item }}</i></c-for></main>'
        )

    html = (
        Root(title="hello", show=True, items=["a", "b"])
        .render(template_globals={"site": "from render"})
        .serialize(deps_strategy="simple")
    )

    assert re.fullmatch(
        r'<main title="hello" data-cid-[A-Za-z0-9_-]+="">hello from render<b>shown</b><i>a</i><i>b</i></main>',
        html,
    )


def test_simple_vue_plain_json_c_bind_matches_ordinary_static_projection() -> None:
    app = Citry()
    simple_calls = 0
    ordinary_calls = 0
    attrs = {
        "id": "from-spread",
        "class": "spread-class",
        "title": "<escaped>",
        "data-fixed": "spread-value",
        "disabled": True,
    }

    class SimpleRoot(Component):
        citry = app
        simple = "vue"
        template = '<article c-bind="attrs" data-fixed="source-value">row</article>'

        @staticmethod
        def template_data(_kwargs: object, _slots: object) -> dict[str, object]:
            nonlocal simple_calls
            simple_calls += 1
            return {"attrs": attrs}

    class OrdinaryRoot(Component):
        citry = app
        template = '<article c-bind="attrs" data-fixed="source-value">row</article>'

        @staticmethod
        def template_data(_kwargs: object, _slots: object) -> dict[str, object]:
            nonlocal ordinary_calls
            ordinary_calls += 1
            return {"attrs": attrs}

    simple_html = SimpleRoot().render().serialize(deps_strategy="simple")
    ordinary_html = OrdinaryRoot().render().serialize(deps_strategy="simple")

    def strip_identity(value: str) -> str:
        return re.sub(r' data-cid-[^=]+=""', "", value)

    assert strip_identity(simple_html) == strip_identity(ordinary_html)
    assert 'data-fixed="source-value"' in simple_html
    assert 'title="&lt;escaped&gt;"' in simple_html
    assert simple_calls == ordinary_calls == 1


def test_simple_vue_c_bind_rejects_reserved_and_unsafe_attributes_once() -> None:
    app = Citry()
    calls = 0

    class Root(Component):
        citry = app
        simple = "vue"
        template = '<article c-bind="attrs">row</article>'

        @staticmethod
        def template_data(kwargs: object, _slots: object) -> dict[str, object]:
            nonlocal calls
            calls += 1
            return {"attrs": kwargs["attrs"]}  # type: ignore[index]

    with pytest.raises((RuntimeError, TypeError), match=r"unsafe|reserved|Events"):
        Root(attrs={"data-cev-private": "x"}).render()
    assert calls == 1


def test_simple_vue_spread_with_custom_attrs_hook_renders_ordinarily() -> None:
    callback_calls = 0

    class MutateAttrs(Extension):
        name = "simple_vue_spread_mutate_attrs"

        def on_attrs_resolved(self, ctx: Any) -> None:
            ctx.attrs["data-mutated"] = "yes"

    app = Citry(extensions=[MutateAttrs])

    class Root(Component):
        citry = app
        simple = "vue"
        template = '<article c-bind="attrs">row</article>'

        @staticmethod
        def template_data(_kwargs: object, _slots: object) -> dict[str, object]:
            nonlocal callback_calls
            callback_calls += 1
            return {"attrs": {"title": "safe"}}

    # The hook belongs to the engine, not to Root, so Root renders as an
    # ordinary component and the hook sees its attributes.
    html = Root().render().serialize(deps_strategy="ignore")
    assert 'data-mutated="yes"' in html
    assert callback_calls == 1


def test_simple_vue_rejects_authored_i18n_directive_before_callback() -> None:
    app = Citry()
    callback_calls = 0

    class Root(Component):
        citry = app
        simple = "vue"
        template = '<p $c-tr:hello[title]="label">Hello</p>'

        @staticmethod
        def template_data(_kwargs: object, _slots: object) -> dict[str, object]:
            nonlocal callback_calls
            callback_calls += 1
            return {"label": "translated"}

    with pytest.raises(TypeError, match="simple='vue'"):
        Root().render()
    assert callback_calls == 0


def test_simple_vue_c_bind_rejects_framework_attributes_once() -> None:
    app = Citry()
    callback_calls = 0

    class Root(Component):
        citry = app
        simple = "vue"
        template = '<article c-bind="attrs">row</article>'

        @staticmethod
        def template_data(_kwargs: object, _slots: object) -> dict[str, object]:
            nonlocal callback_calls
            callback_calls += 1
            return {"attrs": {"#c-key": "row"}}

    with pytest.raises(RuntimeError, match=r"#c-.*framework attributes"):
        Root().render()
    assert callback_calls == 1


def test_simple_vue_renders_actual_project_output_template() -> None:
    app = Citry()
    repo_root = Path(__file__).resolve().parents[4]
    project_template = (repo_root / "benchmarks/web/apps/citry_vue/project_output.html").read_text()

    class ProjectOutput(Component):
        citry = app
        simple = "vue"
        js = "$component({data(){return {open:false}}})"
        template = project_template

    row = {
        "id": "row-7",
        "title": "Weekly report",
        "status": "open",
        "badge": "Ready",
        "description": "Needs <review>",
        "completed": False,
        "select_action": "select-7",
        "dependencies": [{"id": "dep-1", "title": "Input", "completed": True}],
        "attachments": [{"id": "file-2", "name": "Brief", "url": "/brief", "tags": ["source"]}],
    }
    rendered = ProjectOutput(
        row=row,
        row_attrs={"id": "row-7", "class": "output-row", "data-row-id": "row-7"},
    ).render()
    html = rendered.serialize()
    static_html = rendered.serialize(deps_strategy="simple")

    assert 'id="row-7"' in static_html
    assert 'data-output-expanded="true"' in static_html
    assert 'value="row-7"' in static_html
    assert 'checked=""' not in static_html
    assert ':aria-expanded="open"' in static_html
    assert "v-show" in static_html
    assert "Weekly report" in static_html
    assert "Input" in static_html
    assert "Brief" in static_html
    assert "data-cid-" not in html
    assert '"typeKey":"ProjectOutput_' in html


def test_simple_vue_static_js_css_data_and_root_css_marker() -> None:
    app = Citry()
    js_calls = 0
    css_calls = 0

    class Root(Component):
        citry = app
        simple = "vue"
        template = "<button>{{ label }}</button>"
        js = "$component({data(){return {open:false}}})"
        css = "button { color: var(--tone); }"

        @staticmethod
        def js_data(kwargs: object, _slots: object) -> dict[str, object]:
            nonlocal js_calls
            js_calls += 1
            return {"isOpen": kwargs["open"]}  # type: ignore[index]

        @staticmethod
        def css_data(kwargs: object, _slots: object) -> dict[str, object]:
            nonlocal css_calls
            css_calls += 1
            return {"tone": kwargs["tone"]}  # type: ignore[index]

    rendered = Root(label="hello", open=True, tone="red").render()
    static_html = rendered.serialize(deps_strategy="simple")
    assert re.search(
        r'<button data-cid-[A-Za-z0-9_-]+="" data-ccss-[a-f0-9]+="">hello</button>',
        static_html,
    )
    assert "--tone: red" in static_html
    assert "isOpen" not in static_html

    document_html = rendered.serialize()
    assert "isOpen" in document_html
    assert '"isOpen":true' in document_html
    assert "data-ccss-" in document_html
    assert js_calls == 1
    assert css_calls == 1


def test_simple_vue_nested_prepared_view_projects_css_marker_per_occurrence() -> None:
    app = Citry()
    css_calls = 0

    class Leaf(Component):
        citry = app
        simple = "vue"
        template = "<button>{{ label }}</button>"
        js = "$component({data(){return {open:true}}})"
        css = "button { color: var(--tone); }"

        @staticmethod
        def css_data(_kwargs: object, _slots: object) -> dict[str, object]:
            nonlocal css_calls
            css_calls += 1
            return {"tone": "blue"}

    class Page(Component):
        citry = app
        template = '<main><c-leaf label="one"/><c-leaf label="two"/></main>'

    html = Page().render().serialize()
    ids = re.findall(r'"renderId":"([^"]+)","serverData":\{\},"typeKey":"Leaf_', html)
    assert len(ids) == 2
    assert len(set(ids)) == 2
    assert "data-ccss-" in html
    assert "--tone: blue" in html
    assert "data-cid-" not in html
    assert css_calls == 2


def test_simple_vue_rejects_unsafe_template_data_without_callback_replay() -> None:
    app = Citry()
    callback_calls = 0

    class Root(Component):
        citry = app
        simple = "vue"
        template = "<span>{{ label }}</span>"

        @staticmethod
        def template_data(_kwargs: object, _slots: object) -> dict[str, object]:
            nonlocal callback_calls
            callback_calls += 1
            return {"label": []}

    with pytest.raises(TypeError, match="template data is not safe") as error:
        Root().render().serialize(deps_strategy="ignore")

    assert callback_calls == 1
    assert "Root" in str(error.value)
    assert "ProjectOutput" not in str(error.value)


def test_simple_vue_url_security_uses_instance_free_occurrence_owner() -> None:
    app = Citry(security_javascript="warn")

    class Leaf(Component):
        citry = app
        simple = "vue"
        template = '<a c-href="url">unsafe</a>'

    class Page(Component):
        citry = app
        template = '<main><c-leaf url="javascript:globalThis.bad=true"/></main>'

    with pytest.warns(RuntimeWarning, match="Leaf"):
        Page().render().serialize(deps_strategy="ignore")


def test_simple_vue_rejects_inherited_instance_behavior_before_callback() -> None:
    app = Citry()
    callback_calls = 0

    class InstanceMixin:
        def __init__(self) -> None:
            pass

    class Root(InstanceMixin, Component):
        citry = app
        simple = "vue"
        template = "<span>leaf</span>"

        @staticmethod
        def template_data(_kwargs: object, _slots: object) -> dict[str, object]:
            nonlocal callback_calls
            callback_calls += 1
            return {}

    with pytest.raises(TypeError, match="instance member __init__ is not supported"):
        Root().render()
    assert callback_calls == 0


def test_simple_vue_with_unknown_component_data_hook_renders_ordinarily() -> None:
    callback_calls = 0
    hook_components: list[str] = []

    class MutateData(Extension):
        name = "mutate_simple_vue_component_data"

        def on_component_data(self, ctx: Any) -> None:
            hook_components.append(type(ctx.component).__name__)

    app = Citry(extensions=[MutateData])

    class Root(Component):
        citry = app
        simple = "vue"
        template = "<span>leaf</span>"

        @staticmethod
        def template_data(_kwargs: object, _slots: object) -> dict[str, object]:
            nonlocal callback_calls
            callback_calls += 1
            return {}

    # An extension hook is engine state, so the call falls back to ordinary
    # rendering before any callback runs, and the hook sees the instance.
    html = Root().render().serialize(deps_strategy="ignore")
    assert "leaf" in html
    assert hook_components == ["Root"]
    assert callback_calls == 1


def _count_admissions(monkeypatch: pytest.MonkeyPatch) -> list[type]:
    """Record each class whose simple='vue' admission record is (re)computed."""
    computed: list[type] = []
    compute = component_render._compute_simple_vue_admission

    def counting(component_class: type, key: tuple[object, ...]) -> object:
        computed.append(component_class)
        return compute(component_class, key)

    monkeypatch.setattr(component_render, "_compute_simple_vue_admission", counting)
    return computed


def _keyed_rows_app() -> tuple[type[Component], type[Component]]:
    app = Citry()

    class Leaf(Component):
        citry = app
        simple = "vue"
        template = """
          <span>{{ label }}</span>
        """
        js = "$component({data(){return {open:true}}})"

        class Kwargs:
            label: str

    class Page(Component):
        citry = app
        template = """
          <main>
            <c-leaf
              c-for="item in items"
              #c-key="item"
              c-label="item"
            />
          </main>
        """

    return Leaf, Page


def test_simple_vue_admission_is_computed_once_across_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    computed = _count_admissions(monkeypatch)
    _leaf, page = _keyed_rows_app()

    page(items=[f"row-{index}" for index in range(40)]).render().serialize()
    page(items=[f"row-{index}" for index in range(40)]).render().serialize()

    assert len(computed) == 1


def test_simple_vue_admission_recomputes_when_its_inputs_change(monkeypatch: pytest.MonkeyPatch) -> None:
    computed = _count_admissions(monkeypatch)
    leaf, page = _keyed_rows_app()
    page(items=["a"]).render().serialize()
    assert len(computed) == 1

    # Any ABC registration can change value dispatch through ComponentLike.
    class LaterComponentLike:
        pass

    ComponentLike.register(LaterComponentLike)
    page(items=["a"]).render().serialize()
    assert len(computed) == 2

    leaf.reset_files()
    page(items=["a"]).render().serialize()
    assert len(computed) == 3

    # A template reload is seen on the next render, not just recounted.
    leaf.template = """
      <b>{{ label }}</b>
    """
    leaf.reset_template()
    assert "<b " in page(items=["a"]).render().serialize(deps_strategy="ignore")
    assert len(computed) == 4

    class LaterRegistered(Component):
        citry = leaf.citry
        template = """
          <p>later</p>
        """

    page(items=["a"]).render().serialize()
    assert len(computed) == 5


def test_simple_vue_rechecks_declarations_assigned_after_first_render() -> None:
    leaf, page = _keyed_rows_app()
    page(items=["a"]).render().serialize()

    def on_render(self: object) -> None:
        pass

    leaf.on_render = on_render  # type: ignore[attr-defined]
    with pytest.raises(TypeError, match="instance member on_render is not supported"):
        page(items=["a"]).render()


def test_simple_vue_rechecks_plain_mixin_members_assigned_after_first_render() -> None:
    app = Citry()

    class PlainMixin:
        pass

    class Root(PlainMixin, Component):
        citry = app
        simple = "vue"
        template = """
          <span>leaf</span>
        """

    Root().render()

    def on_render(self: object) -> None:
        pass

    # A plain base does not go through the component metaclass, so this write
    # is found by comparing the base's recorded members on the next call.
    PlainMixin.on_render = on_render  # type: ignore[attr-defined]
    with pytest.raises(TypeError, match="instance member on_render is not supported"):
        Root().render()


def test_simple_vue_admission_does_not_keep_a_cleared_class_alive() -> None:
    app = Citry()

    def define() -> weakref.ref[type]:
        class Leaf(Component):
            citry = app
            simple = "vue"
            template = """
              <span>{{ name }}</span>
            """

            # The callback refers to its own class, so a cache that holds the
            # callback strongly from outside the class would keep it alive.
            @staticmethod
            def template_data(_kwargs: object, _slots: object) -> dict[str, object]:
                return {"name": Leaf.__name__}

        Leaf().render()
        return weakref.ref(Leaf)

    leaf_ref = define()
    app.clear()
    gc.collect()
    assert leaf_ref() is None


def _observe_leaf_instances(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    """Collect every Component instance whose class is named Leaf."""
    from citry.component import Component as ComponentBase

    component_init = ComponentBase.__init__
    leaf_instances: list[object] = []

    def observe_init(self: object, *args: object, **kwargs: object) -> None:
        if type(self).__name__ == "Leaf":
            leaf_instances.append(self)
        component_init(self, *args, **kwargs)

    monkeypatch.setattr(ComponentBase, "__init__", observe_init)
    return leaf_instances


def _messages_fallback_app(
    simple: object,
    *,
    config: dict[str, object] | None = None,
    other_messages: bool = False,
) -> tuple[type[Component], list[int]]:
    """Build a two-row page whose leaf counts its data callback calls."""
    render_ids = itertools.count()
    app = Citry(
        id_generator=lambda: f"r{next(render_ids)}",
        extensions_defaults={"i18n": config} if config is not None else {},
    )
    callback_calls: list[int] = []

    def template_data(_kwargs: object, _slots: object) -> dict[str, object]:
        callback_calls.append(1)
        return {"label": "row"}

    type(
        "Leaf",
        (Component,),
        {
            "__module__": __name__,
            "__qualname__": "Leaf",
            "citry": app,
            "simple": simple,
            "template": "<span>{{ label }}</span>",
            "template_data": staticmethod(template_data),
        },
    )
    if other_messages:

        class Other(Component):
            citry = app
            template = """
              <p>other</p>
            """

            class I18n:
                messages_locale = "en"

            messages = """
              hello = Hello
            """

    class Page(Component):
        citry = app
        template = """
          <main><c-leaf/><c-leaf/></main>
        """

    return Page, callback_calls


@pytest.mark.parametrize(
    ("config", "other_messages"),
    [
        (None, True),
        ({"source_locale": "en-US", "locales": ("en-US",)}, False),
    ],
    ids=["other-component-messages", "configured-i18n"],
)
def test_simple_vue_renders_ordinarily_under_app_wide_i18n(
    monkeypatch: pytest.MonkeyPatch,
    config: dict[str, object] | None,
    other_messages: bool,
) -> None:
    leaf_instances = _observe_leaf_instances(monkeypatch)
    page, callback_calls = _messages_fallback_app(simple="vue", config=config, other_messages=other_messages)
    html = page().render().serialize(deps_strategy="ignore")
    ordinary_page, _ordinary_calls = _messages_fallback_app(simple=False, config=config, other_messages=other_messages)
    ordinary_html = ordinary_page().render().serialize(deps_strategy="ignore")

    assert html == ordinary_html
    assert len(callback_calls) == 2
    # Two ordinary Leaf instances per page: the simple='vue' page fell back.
    assert len(leaf_instances) == 4


def test_simple_vue_falls_back_when_messages_register_after_first_render(monkeypatch: pytest.MonkeyPatch) -> None:
    leaf_instances = _observe_leaf_instances(monkeypatch)
    page, callback_calls = _messages_fallback_app("vue")
    page().render().serialize(deps_strategy="ignore")
    assert leaf_instances == []
    assert len(callback_calls) == 2

    class LaterMessages(Component):
        citry = page.citry
        template = """
          <p>later</p>
        """

        class I18n:
            messages_locale = "en"

        messages = """
          hello = Hello
        """

    callback_calls.clear()
    html = page().render().serialize(deps_strategy="ignore")
    assert html.count("row") == 2
    assert len(callback_calls) == 2
    assert len(leaf_instances) == 2


def test_simple_vue_rejects_its_own_messages() -> None:
    app = Citry()

    class Root(Component):
        citry = app
        simple = "vue"
        template = """
          <span>leaf</span>
        """
        messages = """
          hello = Hello
        """

    # Messages declared by the component itself stay a named error; only
    # messages on other components are treated as engine state.
    with pytest.raises(TypeError, match="component messages are not supported"):
        Root().render()


def test_simple_vue_leaf_from_python_expression_gets_interactive_occurrences() -> None:
    app = Citry(autodiscover=False)

    class Leaf(Component):
        citry = app
        simple = "vue"
        template = """
          <b class="leaf">{{ x }}</b>
        """
        js = "$component({data(){return {n:0}}})"

        class Kwargs:
            x: int

        class Slots:
            pass

        @staticmethod
        def template_data(kwargs: Any, _slots: object) -> dict[str, object]:
            return {"x": kwargs.x}

    class Wrap(Component):
        citry = app
        template = """
          <div><c-slot /></div>
        """

    class Page(Component):
        citry = app
        # An authored tag, Python-created elements in a loop, and one passed
        # as slot content: each needs its own Vue occurrence.
        template = """
          <main>
            <c-leaf c-x="0" />
            <c-for each="i in items">{{ Leaf(x=i) }}</c-for>
            <c-wrap>{{ Leaf(x=3) }}</c-wrap>
          </main>
        """

        def template_data(self, kwargs: object, slots: object) -> dict[str, object]:
            return {"Leaf": Leaf, "items": [1, 2]}

    # A Python-created element has no parser call record; the assembler
    # still gives it its own occurrence.
    html = Page().render().serialize()

    host = re.search(r'<div id="citry-vue-[^"]+">(.*?)</div><script', html, re.DOTALL)
    assert host is not None
    assert re.findall(r'<b class="leaf">(\d)</b>', host.group(1)) == ["0", "1", "2", "3"]
    block = re.search(r"<script\b[^>]*data-citry-vue-document[^>]*>(.*?)</script>", html, re.DOTALL)
    assert block is not None
    occurrences = json.loads(block.group(1))["manifest"]["occurrences"]
    leaf_ids = {item["renderId"] for item in occurrences if item["typeKey"].startswith("Leaf_")}
    assert len(leaf_ids) == 4
