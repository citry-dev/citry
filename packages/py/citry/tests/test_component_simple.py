"""Exercise the public simple flag through real component composition."""

from __future__ import annotations

import pytest

from citry import Citry, Component, ComponentLibrary, LibraryComponent, Slot


def test_simple_attribute_spreads_preserve_merging_and_text_expressions() -> None:
    app = Citry()

    class Label(Component):
        citry = app
        simple = True

        template = """
            <span class="base" c-bind="attrs">{{ text }}</span>
        """

    for attrs, expected in (
        ({"class": "extra", "title": "<x>"}, 'class="base extra" title="&lt;x&gt;"'),
        (None, 'class="base"'),
    ):
        html = Label(attrs=attrs, text="<value>").render().serialize()
        assert expected in html
        assert "&lt;value&gt;</span>" in html


@pytest.mark.parametrize(
    "directive", ["$c-tr:save[title]", 'c-$c-tr:save[title]="False"', "$c-tr:save[title]=`value`"]
)
@pytest.mark.parametrize("tag", ["span", "c-missing"])
def test_simple_rejects_literal_translation_bindings_in_inactive_branches(directive: str, tag: str) -> None:
    app = Citry()

    class Label(Component):
        citry = app
        simple = True

        template = f"""
            <section c-if="False"><{tag} {directive}>hidden</{tag}></section>
        """

    with pytest.raises(TypeError, match=r"Label uses simple=True; \$c-tr bindings are unsupported"):
        Label().render()


def test_simple_rejects_translation_binding_in_later_attribute_spread() -> None:
    app = Citry()

    class Label(Component):
        citry = app
        simple = True

        template = """
            <span c-bind="attrs">{{ text }}</span>
        """

    assert "first</span>" in Label(attrs={"title": "ok"}, text="first").render().serialize()
    with pytest.raises(TypeError, match=r"Label uses simple=True; \$c-tr bindings are unsupported"):
        Label(attrs={"$c-tr:save[title]": False}, text="second").render()


def test_simple_spread_keeps_callers_translation_bindings_separate() -> None:
    import json
    import re

    app = Citry(extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}})

    class Label(Component):
        citry = app
        simple = True

        template = """
            <span c-bind="attrs">{{ text }}</span>
        """

    class Page(Component):
        citry = app

        template = """
            <c-i18n c-client="True" tag="main">
                <p $c-tr:save>{{ tr('save') }}</p>
                <c-label c-attrs="attrs" text="plain" />
                <p $c-tr:save>{{ tr('save') }}</p>
            </c-i18n>
        """
        messages = """
            save = Save
        """

    html = Page(attrs={"title": "ordinary"}).render().serialize()
    assert 'title="ordinary">plain</span>' in html
    wire = re.search(r'<script type="application/json" data-citry-i18n>(.*?)</script>', html, re.DOTALL)
    assert wire is not None
    bindings = [binding for requirement in json.loads(wire[1])["requirements"] for binding in requirement["bindings"]]
    assert len(bindings) == 2
    assert len({binding["id"] for binding in bindings}) == 2
    with pytest.raises(TypeError, match=r"Label uses simple=True; \$c-tr bindings are unsupported"):
        Page(attrs={"$c-tr:save[title]": False}).render()


def test_simple_root_and_direct_tag_render_without_a_simple_instance() -> None:
    app = Citry()

    class Label(Component):
        citry = app
        simple = True

        template = """
            <span>{{ text }}</span>
        """

    class Page(Component):
        citry = app

        template = """
            <main><c-label c-text="text" /></main>
        """

    root = Label(text="<value>").render()
    assert "<span>&lt;value&gt;</span>" in root.serialize()
    assert type(root.context.component) is not Label
    nested = Page(text="<value>").render()
    assert "<span>&lt;value&gt;</span>" in nested.serialize()
    assert all(record.class_id != Label.class_id for record in nested.context.ownership.snapshot().logical_instances)


def test_default_content_preserves_caller_variables_and_receives_a_real_slot() -> None:
    app = Citry()
    calls = []

    class Box(Component):
        citry = app
        simple = True

        class Slots:
            default: Slot | None = None

        @staticmethod
        def template_data(_kwargs, slots):
            calls.append(isinstance(slots.default, Slot))
            return {"text": "box"}

        template = """
            <section>{{ text }}:<c-slot /></section>
        """

    class Page(Component):
        citry = app

        template = """
            <main><c-box>{{ text }}</c-box></main>
        """

    assert "<section>box:caller</section>" in Page(text="caller").render().serialize()
    assert calls == [True]


def test_simple_data_runs_again_for_changed_inputs_and_globals() -> None:
    app = Citry(template_globals={"suffix": "engine"})
    calls = []

    class Label(Component):
        citry = app
        simple = True

        @staticmethod
        def template_data(kwargs, _slots):
            calls.append(kwargs["text"])
            return kwargs

        template = """
            <span>{{ text }}:{{ suffix }}</span>
        """

    assert "a:engine" in Label(text="a").render().serialize()
    assert "b:render" in Label(text="b").render(template_globals={"suffix": "render"}).serialize()
    assert "c:data" in Label(text="c", suffix="data").render(template_globals={"suffix": "render"}).serialize()
    assert calls == ["a", "b", "c"]


@pytest.mark.parametrize("simple", [1, None, "true", property(lambda _self: True)])
def test_invalid_flag_rejected_before_registration(simple: object) -> None:
    app = Citry()
    with pytest.raises(ValueError, match="simple must be an exact bool"):
        type("BadFlag", (Component,), {"citry": app, "simple": simple})
    assert not app.has("BadFlag")


def test_invalid_simple_declaration_is_not_registered() -> None:
    app = Citry()
    with pytest.raises(ValueError, match="declares css"):

        class Bad(Component):
            citry = app
            simple = True
            css = """
                .bad { color: red; }
            """

    assert not app.has("Bad")


def test_simple_inherits_but_each_subclass_is_validated_and_can_opt_out() -> None:
    app = Citry()

    class Base(Component):
        citry = app
        simple = True
        template = """
            text
        """

    class Child(Base):
        pass

    assert Child.simple is True
    with pytest.raises(TypeError, match="on_render"):

        class Invalid(Base):
            def on_render(self):
                return "replacement"

    class Ordinary(Base):
        simple = False

        def on_render(self):
            return "replacement"

    assert str(Ordinary()) == "replacement"
    with pytest.raises(AttributeError, match="Cannot change simple component"):
        Base.template = "changed"


def test_inactive_unsupported_outlet_is_rejected() -> None:
    class BadTemplate(Component):
        citry = Citry()
        simple = True
        template = """
            <c-if cond="False"><c-slot name="header" /></c-if>
        """

    with pytest.raises(TypeError, match="empty default slot"):
        BadTemplate().render()


def test_python_value_uses_its_insertion_owner() -> None:
    app = Citry()

    class Label(Component):
        citry = app
        simple = True
        template = """
            <span>{{ text }}</span>
        """

    class Page(Component):
        citry = app
        template = """
            <main>{{ label }}</main>
        """

    rendered = Page(label=Label(text="value")).render()
    assert "<span>value</span>" in rendered.serialize()
    assert len(rendered.context.ownership.snapshot().logical_instances) == 1


def test_library_simple_definition_works_as_a_python_value() -> None:
    class Label(LibraryComponent):
        simple = True
        template = """
            <span>{{ text }}</span>
        """

    app = Citry()
    installation = app.register_library(ComponentLibrary(name="simple-label", components=(Label,)))
    assert installation.component(Label).simple is True
    assert "<span>library</span>" in Label(text="library").render(citry=app).serialize()


def test_deferred_callbacks_and_ordinary_children_keep_their_order_and_parent() -> None:
    app = Citry()
    calls = []
    parents = []

    class Box(Component):
        citry = app
        simple = True

        @staticmethod
        def template_data(kwargs, _slots):
            calls.append("box")
            return kwargs

        template = """
            <section><c-slot /></section>
        """

    class Child(Component):
        citry = app

        def template_data(self, kwargs, slots):
            calls.append("child")
            parents.append(type(self.parent))
            return {}

        template = """
            <span>child</span>
        """

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            calls.append("page")
            return {"observe": lambda: calls.append("expression") or ""}

        template = """
            <main><c-box><c-child /></c-box>{{ observe() }}</main>
        """

    result = Page().render()
    assert "child</span>" in result.serialize()
    assert calls == ["page", "expression", "box", "child"]
    assert parents == [Page]


def test_simple_call_stays_live_inside_a_pure_parent() -> None:
    app = Citry()
    calls = []

    class Label(Component):
        citry = app
        simple = True

        @staticmethod
        def template_data(kwargs, _slots):
            calls.append("label")
            return kwargs

        template = """
            <span>value</span>
        """

    class PureWrapper(Component):
        citry = app
        pure = True
        template = """
            <c-label />
        """

    class Page(Component):
        citry = app
        template = """
            <c-pure-wrapper /><c-pure-wrapper />
        """

    assert Page().render().serialize().count("value</span>") == 2
    assert calls == ["label", "label"]


def test_template_reset_rechecks_a_file_before_rendering(tmp_path) -> None:
    path = tmp_path / "label.citry"
    path.write_text("<span>{{ text }}</span>")

    class Label(Component):
        citry = Citry()
        simple = True
        template_file = str(path)

    assert "old</span>" in Label(text="old").render().serialize()
    path.write_text('<c-slot name="header" />')
    Label.reset_template()
    with pytest.raises(TypeError, match="empty default slot"):
        Label(text="new").render()


def test_inherited_callback_is_frozen_when_a_simple_subclass_is_defined() -> None:
    class Base(Component):
        citry = Citry()

        @staticmethod
        def template_data(_kwargs, _slots):
            return {"text": "original"}

        template = """
            <span>{{ text }}</span>
        """

    class Simple(Base):
        simple = True

    Base.template_data = staticmethod(lambda _kwargs, _slots: {"text": "changed"})
    assert "original</span>" in Simple().render().serialize()


def test_pure_simple_outlets_do_not_reuse_absent_content_for_filled_calls() -> None:
    app = Citry()

    class Box(Component):
        citry = app
        simple = True
        pure = True
        template = """
            <section><c-if cond="True"><c-slot /></c-if></section>
        """

    class Page(Component):
        citry = app
        template = """
            <c-box /><c-box>filled</c-box><c-box />
        """

    html = Page().render().serialize()
    assert html.count("filled") == 1
    assert ">filled</section>" in html


def test_simple_inheritance_uses_the_merged_c3_order() -> None:
    class Common:
        simple = False

    class Left(Common):
        pass

    class Right(Common):
        simple = True

    class Diamond(Left, Right, Component):
        citry = Citry()
        template = """
            <span>diamond</span>
        """

    assert Diamond.simple is True
    assert "<span>diamond</span>" in Diamond().render().serialize()


def test_python_default_content_simple_value_keeps_the_insertion_owner() -> None:
    app = Citry()

    class Label(Component):
        citry = app
        simple = True
        template = """
            <span>label</span>
        """

    class Box(Component):
        citry = app
        simple = True
        template = """
            <section><c-slot /></section>
        """

    class Page(Component):
        citry = app
        template = """
            <main>{{ box }}</main>
        """

    result = Page(box=Box(slots={"default": Label()})).render()
    assert "<section><span>label</span></section>" in result.serialize().replace("\n", "")
    assert len(result.context.ownership.snapshot().logical_instances) == 1


def test_simple_source_locations_and_error_headers_name_the_lexical_class() -> None:
    app = Citry()

    class Leaf(Component):
        citry = app
        template = """
            <span>leaf</span>
        """

    class Shell(Component):
        citry = app
        simple = True
        template = """
            <section><c-leaf />{{ 1 / divisor }}</section>
        """

    class Page(Component):
        citry = app
        template = """
            <main><c-shell c-divisor="divisor" /></main>
        """

    rendered = Page(divisor=1).render()
    locations = rendered.context.ownership.snapshot().source_locations
    assert any(location.origin.endswith("::Shell") for location in locations)
    with pytest.raises(ZeroDivisionError, match="In template of 'Shell'"):
        Page(divisor=0).render()


def test_callback_can_return_default_content_without_a_literal_outlet() -> None:
    class Box(Component):
        citry = Citry()
        simple = True

        @staticmethod
        def template_data(_kwargs, slots):
            return {"body": slots["default"]}

        template = """
            <section>{{ body }}</section>
        """

    assert "<section>content</section>" in Box(slots={"default": "content"}).render().serialize()


def test_mutated_slot_constructor_is_rejected_before_it_executes() -> None:
    calls = []

    class Box(Component):
        citry = Citry()
        simple = True

        class Slots:
            default: Slot | None = None

        template = """
            <section><c-slot /></section>
        """

    def replacement(self, **kwargs):
        calls.append("changed constructor")

    Box.Slots.__init__ = replacement
    with pytest.raises(TypeError, match="Slots declaration changed"):
        Box().render()
    assert calls == []


def test_deep_simple_composition_finishes_serialization_without_recursion() -> None:
    class Chain(Component):
        citry = Citry()
        simple = True
        template = """
            <c-if cond="depth">
                <div><c-chain c-depth="depth - 1" /></div>
            </c-if>
            <c-else>end</c-else>
        """

    html = Chain(depth=1100).render().serialize()
    assert html.count("<div>") == 1100
    assert "end" in html


@pytest.mark.parametrize("expression", ["value", "value()"])
@pytest.mark.parametrize("pure", [False, True])
def test_python_slot_expression_uses_the_insertion_owner(expression: str, pure: bool) -> None:
    app = Citry()

    class Label(Component):
        citry = app
        simple = True
        template = """
            <span>label</span>
        """

    page_class = type("Page", (Component,), {"citry": app, "pure": pure, "template": "{{ " + expression + " }}"})
    rendered = page_class(value=Slot(Label())).render()
    assert "<span" in rendered.serialize()
    assert len(rendered.context.ownership.snapshot().logical_instances) == 1


@pytest.mark.parametrize("wrap_result", [False, True])
def test_python_slot_explicit_provides_reaches_simple_descendants(wrap_result: bool) -> None:
    app = Citry()

    class Child(Component):
        citry = app

        def template_data(self, _kwargs, _slots):
            return {"value": self.inject("x")}

        template = """
            <span>{{ value }}</span>
        """

    class Box(Component):
        citry = app
        simple = True
        template = """
            <c-child />
        """

    class Page(Component):
        citry = app
        template = """
            {{ value }}
        """

    inner = Slot(lambda _ctx: Slot(Box())) if wrap_result else Slot(Box())
    outer = Slot(lambda _ctx: inner(provides={"x": "override"}))
    html = Page(value=outer).render(provides={"x": "original"}).serialize()
    assert ">override</span>" in html
    assert "original" not in html


def test_explicit_nested_root_replaces_the_ambient_slot_context() -> None:
    outer_app = Citry()
    inner_app = Citry()

    class Label(Component):
        citry = inner_app
        simple = True
        template = """
            <span>inner</span>
        """

    class Inner(Component):
        citry = inner_app
        template = """
            <aside>{{ value() }}</aside>
        """

    class Outer(Component):
        citry = outer_app
        template = """
            <main>{{ value }}</main>
        """

    value = Slot(lambda _ctx: Inner(value=Slot(Label())).render())
    assert ">inner</span>" in Outer(value=value).render().serialize()


def test_simple_slots_allow_eager_runtime_annotations() -> None:
    namespace = {"Component": Component, "Slot": Slot, "app": Citry()}
    source = '''
class Box(Component):
    citry = app
    simple = True

    class Slots:
        default: Slot | None = None

    template = """
        <section><c-slot /></section>
    """
'''
    exec(compile(source, "<simple runtime annotations>", "exec", dont_inherit=True), namespace)  # noqa: S102
    box = namespace["Box"]
    assert "content</section>" in box(slots={"default": "content"}).render().serialize()
    _ = box.Slots.__annotations__
    assert "again</section>" in box(slots={"default": "again"}).render().serialize()


def test_rebinding_slot_schema_bases_is_rejected_before_execution() -> None:
    app = Citry()
    events = []

    class Box(Component):
        citry = app
        simple = True

        class Slots:
            default: Slot | None = None

    class ChangedBase:
        def __setattr__(self, name, value):
            events.append(name)
            object.__setattr__(self, name, value)

    Box.Slots.__bases__ = (ChangedBase,)
    with pytest.raises(TypeError, match="Slots declaration changed"):
        Box().render()
    assert events == []


def test_library_simple_flag_uses_the_merged_mro() -> None:
    class Shared:
        simple = False

    class Left(Shared):
        pass

    class Right(Shared):
        simple = True

    class Label(Left, Right, LibraryComponent):
        template = """
            <span>label</span>
        """

    assert Label.simple is True


def test_simple_interiors_and_fills_share_the_transparent_callers_boundary() -> None:
    import json
    import re

    app = Citry()

    class Receiver(Component):
        citry = app
        template = """
            <section><c-slot /></section>
        """
        js = """
            $component(() => {});
        """

    class Box(Component):
        citry = app
        simple = True
        template = """
            <div><c-receiver><b x-data="{name: 'hello'}" x-text="name"></b></c-receiver></div>
        """

    class Page(Component):
        citry = app
        transparent = True
        template = """
            <c-box />
        """

    html = Page().render().serialize()
    match = re.search(r'<script type="application/json" data-citry-graph>(.*?)</script>', html, re.DOTALL)
    assert match is not None
    manifest = json.loads(match.group(1))
    graph = manifest["graphs"][0]
    assert len(graph["componentInstances"]) == 2
    instance = next(record for record in graph["componentInstances"] if record["transparent"])
    for side in ("s", "e"):
        assert html.count(f"<!--citry:g1:{manifest['revision'][:8]}:0:i:{instance['instanceId']}:{side}-->") == 1


@pytest.mark.parametrize("use_name", [False, True])
def test_dynamic_selector_can_own_a_simple_target(use_name: bool) -> None:
    app = Citry()

    class Label(Component):
        citry = app
        simple = True
        template = """
            <span>{{ text }}:<c-slot /></span>
        """

    class Page(Component):
        citry = app
        template = """
            <main><c-component c-is="target" text="label">content</c-component></main>
        """

    rendered = Page(target="Label" if use_name else Label).render()
    assert "label:" in rendered.serialize()
    snapshot = rendered.context.ownership.snapshot()
    assert [record.class_name for record in snapshot.logical_instances] == ["Page", "DynamicComponent"]
    (invocation,) = snapshot.component_invocations
    assert invocation.target_render_id == snapshot.logical_instances[1].render_id
    assert snapshot.render_queue[0].state.value == "settled"


@pytest.mark.parametrize("attribute", ['#c-key="None"', "#c-ignore", '@click="pressed = true"'])
def test_dynamic_simple_target_rejects_instance_directives(attribute: str) -> None:
    app = Citry()

    class Label(Component):
        citry = app
        simple = True
        template = """
            <span>label</span>
        """

    page = type("Page", (Component,), {"citry": app, "template": f'<c-component c-is="target" {attribute} />'})
    with pytest.raises(TypeError, match="simple=True"):
        page(target=Label).render()


def test_dynamic_simple_target_rejects_explicit_default_fills() -> None:
    app = Citry()

    class Box(Component):
        citry = app
        simple = True
        template = """
            <section><c-slot /></section>
        """

    class Page(Component):
        citry = app
        template = """
            <c-component c-is="target"><c-fill name="default">content</c-fill></c-component>
        """

    with pytest.raises(TypeError, match="named fills"):
        Page(target=Box).render()


def test_dynamic_input_hooks_choose_simple_target_before_its_callback() -> None:
    from citry import Extension

    calls = []

    class Select(Extension):
        name = "select_simple"

        def on_component_input(self, context):
            if getattr(type(context.component), "name", None) == "component":
                calls.append("selector-input")
                context.kwargs["is"] = Label
                context.kwargs["text"] = "hook"

    app = Citry(extensions=[Select])

    class Label(Component):
        citry = app
        simple = True

        @staticmethod
        def template_data(kwargs, _slots):
            calls.append("simple-data")
            return kwargs

        template = """
            <span>{{ text }}</span>
        """

    class Page(Component):
        citry = app
        template = """
            <c-component c-is="initial" />
        """

    assert "hook</span>" in Page(initial=None).render().serialize()
    assert calls == ["selector-input", "simple-data"]


@pytest.mark.parametrize(
    "call",
    [
        '<c-custom c-is="target" #c-key="None" />',
        '<c-custom c-is="target"><c-fill name="default">text</c-fill></c-custom>',
    ],
)
def test_selector_subclasses_retain_simple_call_restrictions(call: str) -> None:
    app = Citry()

    class Custom(app.get("component")):
        name = "custom"

    class Label(Component):
        citry = app
        simple = True
        template = """
            <span><c-slot /></span>
        """

    page = type("Page", (Component,), {"citry": app, "template": call})
    with pytest.raises(TypeError, match="simple=True"):
        page(target=Label).render()


def test_python_root_selector_binds_default_supply_once() -> None:
    app = Citry()

    class Label(Component):
        citry = app
        simple = True
        template = """
            <span><c-slot /></span>
        """

    rendered = app.get("component")(**{"is": Label, "slots": {"default": "text"}}).render()
    assert "text</span>" in rendered.serialize()
    assert len(rendered.context.ownership.snapshot().logical_fills) == 1


def test_manual_selector_metadata_is_rejected_for_simple_target() -> None:
    from citry.citry_element import CitryElement, _ElementMorphMetadata

    app = Citry()

    class Label(Component):
        citry = app
        simple = True
        template = """
            <span>text</span>
        """

    element = CitryElement(
        app.get("component"), {"is": Label}, element_morph_metadata=_ElementMorphMetadata(key="key", morph_mode=None)
    )
    with pytest.raises(TypeError, match="range directives"):
        element.render()


def test_library_simple_flag_is_fixed_before_publication() -> None:
    class Label(LibraryComponent):
        simple = True
        template = """
            <span>text</span>
        """

    with pytest.raises(AttributeError, match="simple-component declaration"):
        Label.simple = False
    with pytest.raises(AttributeError, match="simple-component declaration"):
        del Label.simple


def test_kwargs_adapter_cannot_replace_the_checked_slot_constructor() -> None:
    app = Citry()
    calls = []

    def changed(_self, **_kwargs):
        calls.append("changed constructor")

    class Box(Component):
        citry = app
        simple = True

        class Kwargs:
            def __post_init__(self):
                Box.Slots.__init__ = changed

        class Slots:
            default: Slot | None = None

        template = """
            <span><c-slot /></span>
        """

    with pytest.raises(TypeError, match="Slots declaration changed"):
        Box().render()
    assert calls == []
