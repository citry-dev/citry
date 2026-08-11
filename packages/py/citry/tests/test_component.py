"""Tests for the Component base class."""

# ruff: noqa: ANN

from dataclasses import dataclass, field, fields
from typing import Annotated, NamedTuple

import pytest

from citry import Citry, CitryElement, Component, Slot


class TestComponentFields:
    def test_template_field(self):
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>Hello</p>"

        assert MyComp.template == "<p>Hello</p>"

    def test_template_file_field(self):
        c = Citry()

        class MyComp(Component):
            citry = c
            template_file = "my_comp.html"

        assert MyComp.template_file == "my_comp.html"

    def test_lint_declarations_compose_and_reset_through_component_c3(self):
        c = Citry(autodiscover=False)

        class Base(Component):
            citry = c

            class Lint:
                rule_unknown_template_variable = "warning"
                template_variables = {"base_value": int}
                rule_unknown_alpine_variable = "warning"
                alpine_variables = {"$baseMagic": int}
                rule_unknown_component_js_variable = "warning"
                component_js_globals = {"baseClient": int}

        class Child(Base):
            class Lint:
                template_variables = {
                    "child_value": Annotated[str, "Child-only value."],
                }
                alpine_variables = {
                    "childValue": Annotated[str, "Child-only browser value."],
                }
                component_js_globals = {
                    "childClient": Annotated[str, "Child-only component JS value."],
                }

        class Reset(Child):
            Lint = None

        analysis = c.template_analysis()
        child_lint = analysis.component_lint[Child.definition_id]
        reset_lint = analysis.component_lint[Reset.definition_id]

        assert child_lint.rule_unknown_template_variable == "warning"
        assert {item.name for item in child_lint.template_variables} == {"base_value", "child_value"}
        child_value = next(item for item in child_lint.template_variables if item.name == "child_value")
        assert (child_value.type_display, child_value.description) == ("str", "Child-only value.")
        assert child_lint.rule_unknown_alpine_variable == "warning"
        assert {item.name for item in child_lint.alpine_variables} == {"$baseMagic", "childValue"}
        child_browser_value = next(item for item in child_lint.alpine_variables if item.name == "childValue")
        assert (child_browser_value.type_display, child_browser_value.description) == (
            "str",
            "Child-only browser value.",
        )
        assert child_lint.rule_unknown_component_js_variable == "warning"
        assert {item.name for item in child_lint.component_js_globals} == {"baseClient", "childClient"}
        child_client_value = next(item for item in child_lint.component_js_globals if item.name == "childClient")
        assert (child_client_value.type_display, child_client_value.description) == (
            "str",
            "Child-only component JS value.",
        )
        assert reset_lint.rule_unknown_template_variable == "error"
        assert reset_lint.template_variables == ()
        assert reset_lint.rule_unknown_alpine_variable == "error"
        assert reset_lint.alpine_variables == ()
        assert reset_lint.rule_unknown_component_js_variable == "error"
        assert reset_lint.component_js_globals == ()

    def test_lint_declaration_rejects_unknown_fields_and_invalid_values(self):
        c = Citry(autodiscover=False)

        with pytest.raises(ValueError, match="unknown setting"):

            class Unknown(Component):
                citry = c

                class Lint:
                    typo = "warning"

        with pytest.raises(ValueError, match="must be 'ignore', 'warning', or 'error'"):

            class InvalidRule(Component):
                citry = c

                class Lint:
                    rule_unknown_template_variable = "warn"

        with pytest.raises(ValueError, match="rule_unknown_alpine_variable"):

            class InvalidAlpineRule(Component):
                citry = c

                class Lint:
                    rule_unknown_alpine_variable = "warn"

    def test_kwargs_auto_dataclass(self):
        c = Citry()

        class MyComp(Component):
            citry = c

            class Kwargs:
                title: str
                size: int = 10

        from dataclasses import is_dataclass

        assert is_dataclass(MyComp.Kwargs)
        instance = MyComp.Kwargs(title="Hello")
        assert instance.title == "Hello"
        assert instance.size == 10

    def test_kwargs_already_dataclass_not_double_wrapped(self):
        c = Citry()
        from dataclasses import dataclass

        @dataclass
        class MyKwargs:
            title: str

        class MyComp(Component):
            citry = c
            Kwargs = MyKwargs

        assert MyComp.Kwargs is MyKwargs

    def test_kwargs_with_explicit_base_not_converted(self):
        c = Citry()
        from typing import NamedTuple

        class MyKwargs(NamedTuple):
            title: str

        class MyComp(Component):
            citry = c
            Kwargs = MyKwargs

        assert MyComp.Kwargs is MyKwargs

    def test_slots_auto_dataclass(self):
        c = Citry()

        class MyComp(Component):
            citry = c

            class Slots:
                header: str
                footer: str = ""

        from dataclasses import is_dataclass

        assert is_dataclass(MyComp.Slots)
        instance = MyComp.Slots(header="H")
        assert instance.header == "H"
        assert instance.footer == ""

    def test_auto_dataclass_has_slots(self):
        c = Citry()

        class MyComp(Component):
            citry = c

            class Kwargs:
                title: str

        assert hasattr(MyComp.Kwargs, "__slots__")


class TestComponentCall:
    def test_calling_component_returns_citry_element(self):
        c = Citry()

        class MyComp(Component):
            citry = c

        result = MyComp(title="Hello")
        assert isinstance(result, CitryElement)

    def test_citry_element_holds_class_and_kwargs(self):
        c = Citry()

        class MyComp(Component):
            citry = c

        ro = MyComp(title="Hello", size=10)
        assert ro.comp_cls is MyComp
        assert ro.kwargs == {"title": "Hello", "size": 10}

    def test_citry_element_repr(self):
        c = Citry()

        class MyComp(Component):
            citry = c

        ro = MyComp(title="Hello")
        assert "MyComp" in repr(ro)
        assert "title" in repr(ro)

    def test_citry_element_empty_kwargs(self):
        c = Citry()

        class MyComp(Component):
            citry = c

        ro = MyComp()
        assert ro.kwargs == {}
        assert ro.slots == {}

    def test_cls_kwarg_does_not_collide_with_metaclass(self):
        # `cls` is positional-only on ComponentMeta.__call__, so a component may
        # accept a keyword argument named `cls` (e.g. an HTML class).
        c = Citry()

        class MyComp(Component):
            citry = c

        ro = MyComp(cls="card", title="Hi")
        assert isinstance(ro, CitryElement)
        assert ro.comp_cls is MyComp
        assert ro.kwargs == {"cls": "card", "title": "Hi"}


class TestCreateInstance:
    def test_create_instance_returns_component(self):
        c = Citry()

        class MyComp(Component):
            citry = c

        inst = MyComp._create_instance()
        assert isinstance(inst, MyComp)
        assert isinstance(inst, Component)

    def test_create_instance_passes_init_kwargs(self):
        c = Citry()

        class MyComp(Component):
            citry = c

            def __init__(self, render_id=None):
                self.render_id = render_id

        inst = MyComp._create_instance(render_id="abc123")
        assert inst.render_id == "abc123"


class TestTemplateData:
    def test_default_returns_kwargs(self):
        c = Citry()

        class MyComp(Component):
            citry = c

        inst = MyComp._create_instance()
        # The base template_data returns the kwargs it is given, so a
        # component's inputs are usable in its template without an override.
        assert inst.template_data(kwargs={}, slots={}) == {}
        assert inst.template_data(kwargs={"name": "World"}, slots={}) == {"name": "World"}

    def test_override_returns_dict(self):
        c = Citry()

        class MyComp(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"greeting": f"Hello {kwargs['name']}!"}

        inst = MyComp._create_instance()
        # The framework always calls template_data with both kwargs and slots
        # (see component_render.py); this override declares the documented
        # (kwargs, slots) signature, so both must be supplied.
        data = inst.template_data(kwargs={"name": "World"}, slots={})
        assert data == {"greeting": "Hello World!"}

    def test_kwargs_resolve_in_template_without_template_data(self):
        # The default template_data returns kwargs, so an untyped component's
        # inputs are resolvable as template variables with no override.
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>{{ title }}</p>"

        assert MyComp(title="Hello").render().serialize() == '<p data-cid-c1="">Hello</p>'

    def test_typed_kwargs_resolve_in_template_without_template_data(self):
        # A typed Kwargs instance is normalized to a dict by the default, so its
        # fields resolve in the template without an override.
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>{{ title }}</p>"

            class Kwargs:
                title: str

        assert MyComp(title="Hello").render().serialize() == '<p data-cid-c1="">Hello</p>'

    def test_override_replaces_the_default_kwargs(self):
        # Overriding template_data still wins: its return is what the template
        # sees, so the default kwargs passthrough no longer applies.
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>{{ greeting }}</p>"

            class Kwargs:
                name: str

            def template_data(self, kwargs, slots):
                return {"greeting": f"Hi {kwargs.name}"}

        assert MyComp(name="World").render().serialize() == '<p data-cid-c1="">Hi World</p>'


class TestComponentRepr:
    def test_repr(self):
        c = Citry()

        class MyComp(Component):
            citry = c

        inst = MyComp._create_instance()
        assert repr(inst) == "<MyComp>"


class TestComponentName:
    def test_name_field_overrides_class_name(self):
        c = Citry()

        class MyWidget(Component):
            citry = c
            name = "fancy-widget"

        assert c.has("fancy-widget")
        assert not c.has("mywidget")

    def test_default_name_from_class(self):
        c = Citry()

        class UserCard(Component):
            citry = c

        assert c.has("usercard")
        assert c.has("user-card")


class TestInputNormalization:
    """kwargs/slots may be a dict, NamedTuple, or dataclass; all normalize to a dict."""

    def test_dict_kwargs_is_defensively_copied(self):
        c = Citry()

        class MyComp(Component):
            citry = c

        src = {"title": "Hi"}
        inst = MyComp._create_instance(kwargs=src)
        assert inst.raw_kwargs == {"title": "Hi"}
        # A re-render must not be able to mutate the caller's dict.
        assert inst.raw_kwargs is not src

    def test_namedtuple_kwargs(self):
        from typing import NamedTuple

        c = Citry()

        class MyComp(Component):
            citry = c

        class K(NamedTuple):
            title: str
            size: int = 10

        inst = MyComp._create_instance(kwargs=K(title="Hi"))
        assert inst.raw_kwargs == {"title": "Hi", "size": 10}

    def test_dataclass_kwargs(self):
        from dataclasses import dataclass

        c = Citry()

        class MyComp(Component):
            citry = c

        @dataclass
        class K:
            title: str
            size: int = 10

        inst = MyComp._create_instance(kwargs=K(title="Hi"))
        assert inst.raw_kwargs == {"title": "Hi", "size": 10}

    def test_dataclass_slots(self):
        from dataclasses import dataclass

        c = Citry()

        class MyComp(Component):
            citry = c

        @dataclass
        class S:
            header: str

        inst = MyComp._create_instance(slots=S(header="H"))
        # Slot inputs normalize to Slot values (docs/design/component_slots.md section 9.2).
        assert set(inst.raw_slots) == {"header"}
        assert isinstance(inst.raw_slots["header"], Slot)
        assert inst.raw_slots["header"]() == "H"

    def test_none_inputs_default_to_empty_dicts(self):
        c = Citry()

        class MyComp(Component):
            citry = c

        inst = MyComp._create_instance()
        assert inst.raw_kwargs == {}
        assert inst.raw_slots == {}

    def test_typed_input_rebuilt_as_declared_kwargs(self):
        # A NamedTuple input is normalized to a dict, then rebuilt as the
        # component's own declared Kwargs dataclass.
        from dataclasses import is_dataclass
        from typing import NamedTuple

        c = Citry()

        class MyComp(Component):
            citry = c

            class Kwargs:
                title: str

        class K(NamedTuple):
            title: str

        inst = MyComp._create_instance(kwargs=K(title="Hi"))
        assert is_dataclass(inst.kwargs)
        assert inst.kwargs.title == "Hi"
        assert inst.raw_kwargs == {"title": "Hi"}

    def test_untyped_accessors_are_the_raw_dicts(self):
        # With no Kwargs/Slots classes declared there is nothing to rebuild:
        # during the render, self.kwargs and self.slots are the very dicts
        # exposed as raw_kwargs/raw_slots, and slot values are invocable Slots.
        c = Citry()
        seen = {}

        class MyComp(Component):
            citry = c
            template = "<p>x</p>"

            def template_data(self, kwargs, slots):
                seen["kwargs_is_raw"] = self.kwargs is self.raw_kwargs
                seen["slots_is_raw"] = self.slots is self.raw_slots
                seen["kwargs"] = self.kwargs
                seen["slot"] = self.slots["my_slot"]
                seen["slot_value"] = self.slots["my_slot"]()

        MyComp(variable="test", another=1, slots={"my_slot": "MY_SLOT"}).render()
        assert seen["kwargs_is_raw"] is True
        assert seen["slots_is_raw"] is True
        assert seen["kwargs"] == {"variable": "test", "another": 1}
        assert isinstance(seen["slot"], Slot)
        assert seen["slot_value"] == "MY_SLOT"

    def test_dataclass_value_inside_kwargs_stays_the_same_instance(self):
        # Normalization is shallow on purpose (citry/util/misc.py `to_dict`):
        # a dataclass passed as a kwarg VALUE is never converted to a dict, so
        # both the typed kwargs and raw_kwargs hold the caller's own instance.
        from dataclasses import dataclass

        c = Citry()
        seen = {}

        @dataclass
        class User:
            name: str

        class Profile(Component):
            citry = c
            template = "<p>{{ name }}</p>"

            class Kwargs:
                user: User
                count: int

            def template_data(self, kwargs, slots):
                seen["typed"] = kwargs.user
                seen["raw"] = self.raw_kwargs["user"]
                return {"name": kwargs.user.name}

        user = User(name="John")
        assert Profile(user=user, count=5).render().serialize() == '<p data-cid-c1="">John</p>'
        assert seen["typed"] is user
        assert seen["raw"] is user


class TestKwargsRenderValidation:
    """
    A declared Kwargs dataclass validates Python-call inputs at render.

    The template-tag path is checked earlier, at parse time (see
    test_tag_rules.py); these tests lock the direct Python-call path.
    """

    def test_missing_required_kwarg_raises(self):
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>hi</p>"

            class Kwargs:
                title: str

        with pytest.raises(TypeError, match="missing 1 required positional argument: 'title'"):
            MyComp().render()

    def test_unexpected_kwarg_raises(self):
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>hi</p>"

            class Kwargs:
                title: str

        with pytest.raises(TypeError, match="got an unexpected keyword argument 'bogus'"):
            MyComp(title="x", bogus=1).render()


class TestKwargsDefaults:
    """
    Field defaults on a declared Kwargs are plain dataclass defaults: they
    apply when an input is omitted, a supplied value wins, and the default
    reaches only the typed view (never self.raw_kwargs).
    """

    def test_default_applies_when_omitted_and_supplied_value_wins(self):
        c = Citry()
        seen = {}

        class Card(Component):
            citry = c
            template = "<p>{{ title }}-{{ size }}</p>"

            class Kwargs:
                title: str
                size: int = 10

            def template_data(self, kwargs, slots):
                seen["raw"] = dict(self.raw_kwargs)
                return {"title": kwargs.title, "size": kwargs.size}

        assert Card(title="T").render().serialize() == '<p data-cid-c1="">T-10</p>'
        # raw_kwargs holds exactly what the caller passed; the default is not
        # merged in.
        assert seen["raw"] == {"title": "T"}
        assert Card(title="T", size=5).render().serialize() == '<p data-cid-c2="">T-5</p>'
        assert seen["raw"] == {"title": "T", "size": 5}

    def test_default_applies_on_the_template_tag_path(self):
        c = Citry()
        seen = {}

        class Card(Component):
            citry = c
            template = "<p>{{ title }}-{{ size }}</p>"

            class Kwargs:
                title: str
                size: int = 10

            def template_data(self, kwargs, slots):
                seen["raw"] = dict(self.raw_kwargs)
                return {"title": kwargs.title, "size": kwargs.size}

        class Page(Component):
            citry = c
            template = '<c-card title="TT" />'

        # The omitted attribute falls back to the field default; both the
        # page's and the card's render ids land on the shared root element.
        assert Page().render().serialize() == '<p data-cid-c2="" data-cid-c1="">TT-10</p>'
        assert seen["raw"] == {"title": "TT"}

    def test_default_on_a_namedtuple_kwargs_applies_too(self):
        # Same guarantees for the NamedTuple declaration form: the class is
        # kept as-is (no dataclass conversion), and its field default flows
        # through both call paths.
        c = Citry()
        seen = {}

        class Card(Component):
            citry = c
            template = "<p>{{ title }}-{{ size }}</p>"

            class Kwargs(NamedTuple):
                title: str
                size: int = 10

            def template_data(self, kwargs, slots):
                seen["typed"] = kwargs
                seen["raw"] = dict(self.raw_kwargs)
                return {"title": kwargs.title, "size": kwargs.size}

        class Page(Component):
            citry = c
            template = '<c-card title="TT" />'

        assert Card(title="T").render().serialize() == '<p data-cid-c1="">T-10</p>'
        assert isinstance(seen["typed"], Card.Kwargs)
        assert seen["raw"] == {"title": "T"}
        assert Page().render().serialize() == '<p data-cid-c3="" data-cid-c2="">TT-10</p>'
        assert seen["raw"] == {"title": "TT"}
        assert Card(title="T", size=5).render().serialize() == '<p data-cid-c4="">T-5</p>'

    def test_default_factory_gives_a_fresh_value_per_render(self):
        c = Citry()
        seen = []

        class Tally(Component):
            citry = c
            template = "<p>{{ n }}</p>"

            class Kwargs:
                items: list = field(default_factory=list)

            def template_data(self, kwargs, slots):
                seen.append(kwargs.items)
                kwargs.items.append(1)
                return {"n": len(kwargs.items)}

        # Each render starts from its own fresh list, so a mutation during one
        # render never leaks into the next.
        assert Tally().render().serialize() == '<p data-cid-c1="">1</p>'
        assert Tally().render().serialize() == '<p data-cid-c2="">1</p>'
        assert seen[0] is not seen[1]

    def test_mutable_class_level_default_fails_at_class_definition(self):
        c = Citry()

        # The auto-conversion to a dataclass applies stdlib semantics, so a
        # shared mutable default is rejected up front with a pointer to
        # field(default_factory=...).
        err = r"mutable default .* for field items is not allowed: use default_factory"
        with pytest.raises(ValueError, match=err):

            class Bad(Component):
                citry = c
                template = "<p>x</p>"

                class Kwargs:
                    items: list = []


class TestSubclassTypedInputs:
    """Nested input schemas follow their component class's C3 MRO."""

    def test_redeclared_kwargs_revalidates_with_the_subclass(self):
        c = Citry()
        seen = {}

        class Button(Component):
            citry = c
            template = "<p>hi</p>"

            class Kwargs:
                color: str

        class ButtonExtra(Button):
            class Kwargs:
                size: int

            def template_data(self, kwargs, slots):
                seen["is_extra"] = isinstance(kwargs, ButtonExtra.Kwargs)
                seen["is_parent"] = isinstance(kwargs, Button.Kwargs)
                return {}

        ButtonExtra(color="red", size=3).render()
        # A child declaration adds to the inherited schema without having to
        # spell ``class Kwargs(Button.Kwargs)`` itself.
        assert seen["is_extra"] is True
        assert seen["is_parent"] is False
        # The parent keeps its own schema: the subclass-only field is rejected.
        with pytest.raises(TypeError, match="got an unexpected keyword argument 'size'"):
            Button(color="red", size=3).render()
        # The subclass enforces its own new required field.
        with pytest.raises(TypeError, match="missing 1 required positional argument: 'size'"):
            ButtonExtra(color="red").render()

    def test_redeclared_kwargs_inherits_methods_and_supports_super(self):
        c = Citry()

        class Parent(Component):
            citry = c

            class Kwargs:
                title: str

                def label(self):
                    return self.title

        class Child(Parent):
            class Kwargs:
                suffix: str = "!"

                def label(self):
                    return super().label() + self.suffix

        kwargs = Child.Kwargs(title="Hello")
        assert kwargs.label() == "Hello!"

    def test_kwargs_merge_multiple_component_bases_in_c3_order(self):
        c = Citry()

        class Common(Component):
            citry = c

            class Kwargs:
                shared: str = "common"

        class Left(Common):
            class Kwargs:
                left: str = "left"
                shared: str = "left-shared"

        class Right(Common):
            class Kwargs:
                right: str = "right"
                shared: str = "right-shared"

        class Combined(Left, Right):
            class Kwargs:
                own: str = "combined"

        assert [field.name for field in fields(Combined.Kwargs)] == ["shared", "right", "left", "own"]
        assert Combined.Kwargs().shared == "left-shared"

    def test_unslotted_dataclass_schemas_merge_across_c3_branches(self):
        c = Citry()

        @dataclass
        class LeftSchema:
            left: str = "left"

        @dataclass
        class RightSchema:
            right: str = "right"

        class Left(Component):
            citry = c
            Kwargs = LeftSchema

        class Right(Component):
            citry = c
            Kwargs = RightSchema

        class Combined(Left, Right):
            pass

        assert [field.name for field in fields(Combined.Kwargs)] == ["right", "left"]
        assert Combined.Kwargs() == Combined.Kwargs(right="right", left="left")

    def test_frozen_unslotted_dataclass_schemas_preserve_frozen_composition(self):
        c = Citry()

        @dataclass(frozen=True)
        class LeftSchema:
            left: str = "left"

        @dataclass(frozen=True)
        class RightSchema:
            right: str = "right"

        class Left(Component):
            citry = c
            Kwargs = LeftSchema

        class Right(Component):
            citry = c
            Kwargs = RightSchema

        class Combined(Left, Right):
            pass

        assert [field.name for field in fields(Combined.Kwargs)] == ["right", "left"]
        assert Combined.Kwargs() == Combined.Kwargs(right="right", left="left")

    def test_mixed_frozen_dataclass_modes_reject_multiple_c3_branches(self):
        c = Citry()

        @dataclass(frozen=True)
        class FrozenSchema:
            frozen: str = "frozen"

        @dataclass
        class MutableSchema:
            mutable: str = "mutable"

        class Frozen(Component):
            citry = c
            Kwargs = FrozenSchema

        class Mutable(Component):
            citry = c
            Kwargs = MutableSchema

        with pytest.raises(ValueError, match=r"frozen and non-frozen dataclass Kwargs declarations"):

            class Combined(Frozen, Mutable):
                pass

    def test_slotted_dataclass_schemas_reject_multiple_c3_branches(self):
        c = Citry()

        @dataclass(slots=True)
        class LeftSchema:
            left: str = "left"

        @dataclass(slots=True)
        class RightSchema:
            right: str = "right"

        class Left(Component):
            citry = c
            Kwargs = LeftSchema

        class Right(Component):
            citry = c
            Kwargs = RightSchema

        with pytest.raises(
            ValueError,
            match=r"slotted dataclass Kwargs declarations.*incompatible instance layouts",
        ):

            class Combined(Left, Right):
                pass

    def test_namedtuple_schemas_reject_multiple_c3_branches(self):
        c = Citry()

        class LeftSchema(NamedTuple):
            left: str

        class RightSchema(NamedTuple):
            right: str

        class Left(Component):
            citry = c
            Kwargs = LeftSchema

        class Right(Component):
            citry = c
            Kwargs = RightSchema

        with pytest.raises(ValueError, match=r"NamedTuple Kwargs declarations.*silently dropping fields"):

            class Combined(Left, Right):
                pass

    def test_mixed_schema_adapters_reject_multiple_c3_branches(self):
        c = Citry()

        class PlainSchema:
            plain: str

        class TupleSchema(NamedTuple):
            tuple_value: str

        class Plain(Component):
            citry = c
            Kwargs = PlainSchema

        class Tuple(Component):
            citry = c
            Kwargs = TupleSchema

        with pytest.raises(ValueError, match=r"incompatible schema adapters \(namedtuple, plain\)"):

            class Combined(Plain, Tuple):
                pass

    def test_kwargs_none_resets_inherited_schema(self):
        c = Citry()

        class Parent(Component):
            citry = c

            class Kwargs:
                title: str

        class Child(Parent):
            Kwargs = None

        assert Child.Kwargs is None
        assert Child(anything="goes").render().serialize() == ""

    @pytest.mark.parametrize("schema_name", ["Kwargs", "Slots", "TemplateData", "JsData", "CssData"])
    def test_every_core_schema_role_uses_the_same_inheritance_rule(self, schema_name):
        c = Citry()

        class ParentSchema:
            inherited: str = "parent"

        class ChildSchema:
            own: str = "child"

        parent = type(f"{schema_name}Parent", (Component,), {"citry": c, schema_name: ParentSchema})
        child = type(f"{schema_name}Child", (parent,), {schema_name: ChildSchema})

        schema = getattr(child, schema_name)
        assert [field.name for field in fields(schema)] == ["inherited", "own"]

    @pytest.mark.parametrize("schema_name", ["Kwargs", "Slots", "TemplateData", "JsData", "CssData"])
    def test_core_schema_declaration_reopens_above_a_reset(self, schema_name):
        c = Citry()

        class RootSchema:
            root: str = "root"

        class ReopenedSchema:
            reopened: str = "reopened"

        root = type(f"{schema_name}Root", (Component,), {"citry": c, schema_name: RootSchema})
        reset = type(f"{schema_name}Reset", (root,), {schema_name: None})
        reopened = type(f"{schema_name}Reopened", (reset,), {schema_name: ReopenedSchema})

        schema = getattr(reopened, schema_name)
        assert [field.name for field in fields(schema)] == ["reopened"]

    @pytest.mark.parametrize("schema_name", ["Kwargs", "Slots", "TemplateData", "JsData", "CssData"])
    def test_core_schema_declaration_precedes_a_later_c3_branch_reset(self, schema_name):
        c = Citry()

        class LeftSchema:
            left: str = "left"

        left = type(f"{schema_name}Left", (Component,), {"citry": c, schema_name: LeftSchema})
        right = type(f"{schema_name}Right", (Component,), {"citry": c, schema_name: None})
        combined = type(f"{schema_name}Combined", (left, right), {})

        schema = getattr(combined, schema_name)
        assert [field.name for field in fields(schema)] == ["left"]

    def test_plain_definition_base_schemas_are_normalized_for_the_component(self):
        c = Citry()

        class Definition:
            class Kwargs:
                label: str

            class Slots:
                default: Slot

        class Bound(Definition, Component):
            citry = c
            template = """
            <p>{{ label }}</p>
            """

        assert [field.name for field in fields(Bound.Kwargs)] == ["label"]
        assert [field.name for field in fields(Bound.Slots)] == ["default"]
        assert Bound(label="ready", slots={"default": "body"}).render().serialize().strip() == (
            '<p data-cid-c1="">ready</p>'
        )

    def test_unredeclared_kwargs_is_inherited_by_identity(self):
        c = Citry()

        class Button(Component):
            citry = c
            template = "<p>hi</p>"

            class Kwargs:
                color: str

        class ButtonExtra(Button):
            pass

        assert ButtonExtra.Kwargs is Button.Kwargs
        assert ButtonExtra(color="red").render().serialize() == '<p data-cid-c1="">hi</p>'
        with pytest.raises(TypeError, match="missing 1 required positional argument: 'color'") as exc:
            ButtonExtra().render()
        # The error names the parent's class, showing it is the inherited
        # Kwargs doing the validating.
        assert "Button.Kwargs" in str(exc.value)


class TestTemplateDataNormalization:
    """template_data() may return a dict, NamedTuple, dataclass, or None."""

    def test_dict_template_data_renders(self):
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>hi</p>"

            def template_data(self, kwargs, slots):
                return {"title": "Hello"}

        assert MyComp(title="x").render().serialize() == '<p data-cid-c1="">hi</p>'

    def test_namedtuple_template_data_renders(self):
        # Before normalization `dict(namedtuple)` raised ValueError.
        from typing import NamedTuple

        class Data(NamedTuple):
            title: str

        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>hi</p>"

            def template_data(self, kwargs, slots):
                return Data(title="Hello")

        assert MyComp(title="x").render().serialize() == '<p data-cid-c1="">hi</p>'

    def test_dataclass_template_data_renders(self):
        from dataclasses import dataclass

        @dataclass
        class Data:
            title: str

        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>hi</p>"

            def template_data(self, kwargs, slots):
                return Data(title="Hello")

        assert MyComp(title="x").render().serialize() == '<p data-cid-c1="">hi</p>'

    def test_none_template_data_renders(self):
        # None means "no template variables"; the render still succeeds.
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>hi</p>"

            def template_data(self, kwargs, slots):
                return None

        assert MyComp(title="x").render().serialize() == '<p data-cid-c1="">hi</p>'

    def test_none_template_data_means_no_variables_not_kwargs(self):
        # None must yield an EMPTY variable set: a template referencing a
        # kwarg name raises, proving None does not fall back to passing the
        # kwargs through.
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>{{ title }}</p>"

            def template_data(self, kwargs, slots):
                return None

        with pytest.raises(KeyError):
            MyComp(title="x").render().serialize()


class TestTemplateDataValidation:
    """If a component declares a `TemplateData` schema, the data is validated against it."""

    def test_valid_data_passes(self):
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>hi</p>"

            class TemplateData:
                title: str

            def template_data(self, kwargs, slots):
                return {"title": "Hello"}

        assert MyComp(title="x").render().serialize() == '<p data-cid-c1="">hi</p>'

    def test_missing_required_field_raises(self):
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>hi</p>"

            class TemplateData:
                title: str

            def template_data(self, kwargs, slots):
                return {}

        with pytest.raises(TypeError):
            MyComp(title="x").render()

    def test_unexpected_field_raises(self):
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>hi</p>"

            class TemplateData:
                title: str

            def template_data(self, kwargs, slots):
                return {"title": "Hello", "bogus": 1}

        with pytest.raises(TypeError):
            MyComp(title="x").render()

    def test_template_data_instance_skips_revalidation(self):
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>hi</p>"

            class TemplateData:
                title: str

            def template_data(self, kwargs, slots):
                return MyComp.TemplateData(title="Hello")

        assert MyComp(title="x").render().serialize() == '<p data-cid-c1="">hi</p>'

    def test_no_template_data_schema_skips_validation(self):
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>hi</p>"

            def template_data(self, kwargs, slots):
                return {"anything": "goes", "count": 3}

        assert MyComp(title="x").render().serialize() == '<p data-cid-c1="">hi</p>'

    def test_schema_validates_kwargs_when_method_absent(self):
        # With no template_data override the base returns kwargs, so a declared
        # TemplateData now validates those kwargs. A mismatch (a kwarg the
        # schema does not declare) is reachable without writing template_data,
        # and the error names the offending field.
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>hi</p>"

            class Kwargs:
                name: str

            class TemplateData:
                title: str

        with pytest.raises(TypeError) as exc:
            MyComp(name="x").render()
        assert "name" in str(exc.value)

    def test_schema_passes_matching_kwargs_when_method_absent(self):
        # When the kwargs match the declared TemplateData, the default passes
        # validation and the fields resolve in the template with no override.
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>{{ title }}</p>"

            class Kwargs:
                title: str

            class TemplateData:
                title: str

        assert MyComp(title="Hello").render().serialize() == '<p data-cid-c1="">Hello</p>'


class TestGeneratorCaching:
    """The body-generating function is cached per component class."""

    def test_repeated_render_is_stable(self):
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>hi</p>"

        ro = MyComp(title="x")
        assert ro.render().serialize() == '<p data-cid-c1="">hi</p>'
        assert ro.render().serialize() == '<p data-cid-c2="">hi</p>'  # fresh id per render

    def test_generator_cached_on_class_and_shared(self):
        c = Citry()

        class MyComp(Component):
            citry = c
            template = "<p>hi</p>"

        assert "_citry_template" not in MyComp.__dict__

        MyComp(title="a").render()
        compiled = MyComp.__dict__["_citry_template"]
        assert callable(compiled.generate)

        # A second CitryElement reuses the same class-level compiled template.
        MyComp(title="b").render()
        assert MyComp.__dict__["_citry_template"] is compiled

    def test_subclass_template_override_gets_own_generator(self):
        c = Citry()

        class Base(Component):
            citry = c
            template = "<p>base</p>"

        class Child(Base):
            template = "<p>child</p>"

        Base(x=1).render()
        Child(x=1).render()

        assert Base.__dict__["_citry_template"] is not Child.__dict__["_citry_template"]
        assert Base(x=1).render().serialize() == '<p data-cid-c3="">base</p>'
        assert Child(x=1).render().serialize() == '<p data-cid-c4="">child</p>'


class TestRenderId:
    def test_id_readable_during_render_and_equals_the_marker(self):
        # self.id is minted per render, readable inside template_data, and is
        # the same id the serializer stamps into the data-cid marker.
        c = Citry()
        seen = []

        class MyComp(Component):
            citry = c
            template = "<p>{{ rid }}</p>"

            def template_data(self, kwargs, slots):
                seen.append(self.id)
                return {"rid": self.id}

        assert MyComp().render().serialize() == '<p data-cid-c1="">c1</p>'
        assert seen == ["c1"]


class TestParentRoot:
    def test_root_component_has_parent_none_and_root_self(self):
        c = Citry()
        seen = {}

        class Root(Component):
            citry = c
            template = "<p>x</p>"

            def template_data(self, kwargs, slots):
                seen["self"] = self
                seen["parent"] = self.parent
                seen["root"] = self.root

        Root().render()
        assert seen["parent"] is None
        assert seen["root"] is seen["self"]

    def test_accessors_stay_readable_after_the_render(self):
        # The accessors are plain instance attributes, so a captured instance
        # keeps exposing its inputs and tree links after render() returns.
        c = Citry()
        seen = {}

        class Root(Component):
            citry = c
            template = "<p>x</p>"

            def template_data(self, kwargs, slots):
                seen["self"] = self

        Root(title="Hi", slots={"body": "B"}).render()
        comp = seen["self"]
        assert comp.parent is None
        assert comp.root is comp
        assert comp.kwargs == {"title": "Hi"}
        assert isinstance(comp.slots["body"], Slot)
        assert comp.slots["body"]() == "B"
        assert list(comp.ancestors) == []

    def test_three_level_tree_resolves_root_to_outermost(self):
        c = Citry()
        seen = {}

        class Leaf(Component):
            citry = c
            template = "<i>x</i>"

            def template_data(self, kwargs, slots):
                seen["leaf"] = self

        class Middle(Component):
            citry = c
            template = "<section><c-leaf /></section>"

            def template_data(self, kwargs, slots):
                seen["middle"] = self

        class Root(Component):
            citry = c
            template = "<main><c-middle /></main>"

            def template_data(self, kwargs, slots):
                seen["root"] = self

        Root().render()
        assert seen["leaf"].parent is seen["middle"]
        assert seen["middle"].parent is seen["root"]
        assert seen["root"].parent is None
        # root is transitive through the parent links, so every level of the
        # tree resolves to the same outermost instance.
        assert seen["leaf"].root is seen["root"]
        assert seen["middle"].root is seen["root"]
        assert seen["root"].root is seen["root"]


class TestAncestors:
    def test_root_component_has_no_ancestors(self):
        c = Citry()
        seen = []

        class Root(Component):
            citry = c
            template = "<p>x</p>"

            def template_data(self, kwargs, slots):
                seen.append(list(self.ancestors))

        Root().render()
        assert seen == [[]]

    def test_yields_chain_nearest_first_including_root(self):
        c = Citry()
        seen = []

        class Leaf(Component):
            citry = c
            template = "<i>x</i>"

            def template_data(self, kwargs, slots):
                seen.append([type(a).__name__ for a in self.ancestors])

        class Middle(Component):
            citry = c
            template = "<section><c-leaf /></section>"

        class Root(Component):
            citry = c
            template = "<main><c-middle /></main>"

        Root().render()
        assert seen == [["Middle", "Root"]]

    def test_same_class_at_two_levels_keeps_distinct_instances(self):
        # CompA renders CompB, which renders CompA again as a leaf. The two
        # CompA occurrences are distinct instances, and each chain lists the
        # actual enclosing instances nearest first.
        c = Citry()
        seen = []

        class CompA(Component):
            citry = c
            template = '<c-if cond="leaf"><i>x</i></c-if><c-else><c-comp-b /></c-else>'

            def template_data(self, kwargs, slots):
                seen.append((self, list(self.ancestors)))
                return {"leaf": self.raw_kwargs.get("leaf", False)}

        class CompB(Component):
            citry = c
            template = '<section><c-comp-a c-leaf="True" /></section>'

            def template_data(self, kwargs, slots):
                seen.append((self, list(self.ancestors)))

        CompA(leaf=False).render()
        assert [type(inst).__name__ for inst, _ in seen] == ["CompA", "CompB", "CompA"]
        (root_a, root_chain), (comp_b, b_chain), (leaf_a, leaf_chain) = seen
        assert root_chain == []
        assert b_chain == [root_a]
        assert leaf_chain == [comp_b, root_a]
        assert root_a is not leaf_a
        assert leaf_a.raw_kwargs == {"leaf": True}

    def test_isinstance_check_use_case(self):
        # The use case ancestors exists for: "is this component rendered
        # inside a Theme?" The chain follows who wrote the component (the
        # `parent` contract), so this holds when Theme's own template renders
        # the widget; content passed into Theme's slots keeps its writer's
        # chain instead (see the fill test below).
        c = Citry()
        seen = []

        class Widget(Component):
            citry = c
            template = "<i>w</i>"

            def template_data(self, kwargs, slots):
                seen.append(any(type(a).__name__ == "Theme" for a in self.ancestors))

        class Theme(Component):
            citry = c
            template = "<div><c-widget /></div>"

        class Page(Component):
            citry = c
            template = "<main><c-theme /><c-widget /></main>"

        Page().render()
        assert seen == [True, False]

    def test_embedded_element_starts_a_fresh_chain(self):
        # An element rendered via {{ em }} has no parent link, so its chain
        # is empty (same contract as `parent`).
        c = Citry()
        seen = []

        class Embedded(Component):
            citry = c
            template = "<i>x</i>"

            def template_data(self, kwargs, slots):
                seen.append(list(self.ancestors))

        class Root(Component):
            citry = c
            template = "<main>{{ em }}</main>"

            def template_data(self, kwargs, slots):
                return {"em": Embedded()}

        Root().render()
        assert seen == [[]]

    def test_fill_content_follows_the_writer_chain(self):
        # A component written inside a fill has the fill's author as parent;
        # the slot owner is not in its chain (same contract as `parent`).
        c = Citry()
        seen = []

        class Inner(Component):
            citry = c
            template = "<i>x</i>"

            def template_data(self, kwargs, slots):
                seen.append([type(a).__name__ for a in self.ancestors])

        class Card(Component):
            citry = c
            template = '<div><c-slot name="body" /></div>'

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="body"><c-inner /></c-fill></c-card>'

        Page().render()
        assert seen == [["Page"]]
