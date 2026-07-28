"""Tests for the extension (plugin) system skeleton (phase 1)."""

# ruff: noqa: ANN, D101, D102, D106, ARG002, PLC0415

from dataclasses import field

import pytest

from citry import Citry as _Citry
from citry import (
    CitryRender,
    Component,
    Extension,
    ExtensionCommand,
    Slot,
)
from citry.ext.events.openapi import OpenApiCommand


class _StringPathExt(Extension):
    name = "strext"


class TestExtensionDefinition:
    def test_class_name_derived_from_name(self):
        class MyExt(Extension):
            name = "my_extension"

        assert MyExt.class_name == "MyExtension"

    def test_explicit_class_name_kept(self):
        class MyExt(Extension):
            name = "my_extension"
            class_name = "Custom"

        assert MyExt.class_name == "Custom"

    def test_class_name_must_be_identifier(self):
        with pytest.raises(ValueError, match="class_name must be a valid Python identifier"):

            class Bad(Extension):
                name = "bad"
                class_name = "not-valid"

    def test_name_must_be_lowercase(self):
        with pytest.raises(ValueError, match="lowercase"):

            class Bad(Extension):
                name = "Bad"

    def test_name_must_be_identifier(self):
        with pytest.raises(ValueError, match="identifier"):

            class Bad(Extension):
                name = "not-an-identifier"


class TestManagerConstruction:
    def test_default_citry_has_only_builtins(self):
        c = _Citry()
        # Every instance carries the built-in extensions (prepended by the
        # manager); with no user extensions, that is all there is.
        assert [ext.name for ext in c.extensions._extensions] == ["cache", "dependencies", "events"]

    @pytest.mark.xfail(
        strict=True,
        reason="debug auto-registration in development is temporarily off "
        "(extension._AUTO_DEBUG_IN_DEVELOPMENT) pending the debug + <c-cache> "
        "ownership-graph bug; see dev_prod_mode.md section 4",
    )
    def test_development_mode_adds_debug_builtin(self):
        # The debug extension (visual boundaries) is developer-only output, so
        # it is a built-in only in development mode (dev_prod_mode.md). When the
        # cache bug is fixed and the flag is restored, this xfail turns into an
        # xpass and strict mode fails it, prompting removal of the marker.
        prod = _Citry()
        dev = _Citry(mode="development")
        assert [ext.name for ext in prod.extensions._extensions] == ["cache", "dependencies", "events"]
        assert [ext.name for ext in dev.extensions._extensions] == ["cache", "dependencies", "events", "debug"]

    def test_accepts_class_and_instance(self):
        class E1(Extension):
            name = "e1"

        class E2(Extension):
            name = "e2"

        c = _Citry(extensions=[E1, E2()])
        # Built-ins come first, then the user's extensions in spec order.
        assert [ext.name for ext in c.extensions._extensions] == ["cache", "dependencies", "events", "e1", "e2"]

    def test_accepts_string_path(self):
        spec = f"{_StringPathExt.__module__}.{_StringPathExt.__qualname__}"
        c = _Citry(extensions=[spec])
        assert c.extensions.get_extension("strext") is not None

    def test_extension_created_fires(self):
        seen = []

        class E(Extension):
            name = "e"

            def on_extension_created(self, ctx):
                seen.append(ctx.extension)

        c = _Citry(extensions=[E])
        assert seen == [c.extensions.get_extension("e")]

    def test_duplicate_names_rejected(self):
        class A(Extension):
            name = "dup"

        class B(Extension):
            name = "dup"

        with pytest.raises(ValueError, match="share the name"):
            _Citry(extensions=[A, B])

    def test_duplicate_component_config_class_names_rejected(self):
        class A(Extension):
            name = "first"
            class_name = "Shared"

        class B(Extension):
            name = "second"
            class_name = "Shared"

        with pytest.raises(ValueError, match="cannot share class_name 'Shared'"):
            _Citry(extensions=[A, B])

    @pytest.mark.parametrize(
        "class_name",
        ["Kwargs", "Slots", "TemplateData", "JsData", "CssData", "State"],
    )
    def test_special_component_declaration_names_are_reserved(self, class_name):
        class Reserved(Extension):
            name = "reserved"
            class_name = "Temporary"

        Reserved.class_name = class_name
        with pytest.raises(ValueError, match=f"reserved component declaration name {class_name!r}"):
            _Citry(extensions=[Reserved])

    def test_name_clashing_with_component_api_rejected(self):
        class Tmpl(Extension):
            name = "template"  # Component.template exists

        with pytest.raises(ValueError, match="conflicts"):
            _Citry(extensions=[Tmpl])


class TestClassAndRegistrationHooks:
    def test_class_created_and_registered(self):
        events = []

        class E(Extension):
            name = "e"

            def on_component_class_created(self, ctx):
                events.append(("created", ctx.component_class.__name__))

            def on_component_registered(self, ctx):
                events.append(("registered", ctx.name, ctx.component_class.__name__))

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app

        assert ("created", "Card") in events
        assert ("registered", "Card", "Card") in events
        # created fires before registered
        assert events.index(("created", "Card")) < events.index(("registered", "Card", "Card"))

    def test_unregistered_fires(self):
        names = []

        class E(Extension):
            name = "e"

            def on_component_unregistered(self, ctx):
                names.append(ctx.name)

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app

        app.unregister(Card)
        assert names == ["Card"]

    def test_ctx_carries_citry(self):
        captured = {}

        class E(Extension):
            name = "e"

            def on_component_registered(self, ctx):
                captured["citry"] = ctx.citry

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app

        assert captured["citry"] is app


class TestRenderHooks:
    def test_input_mutation_lands_on_raw_kwargs(self):
        captured = {}

        class E(Extension):
            name = "e"

            def on_component_input(self, ctx):
                ctx.kwargs["injected"] = 42

            def on_component_data(self, ctx):
                captured["raw"] = dict(ctx.component.raw_kwargs)

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app
            template = "<p>hi</p>"

        str(Card(title="x"))
        assert captured["raw"]["injected"] == 42

    def test_input_mutation_rebuilds_every_typed_data_input(self):
        captured = {}

        class E(Extension):
            name = "e"

            def on_component_input(self, ctx):
                ctx.kwargs["count"] = 7

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app
            template = """
            <p>{{ count }}</p>
            """

            class Kwargs:
                count: int

            def template_data(self, kwargs, slots):
                captured["template"] = kwargs
                return {"count": kwargs.count}

            def js_data(self, kwargs, slots):
                captured["js"] = kwargs
                return {}

            def css_data(self, kwargs, slots):
                captured["css"] = kwargs
                return {}

        assert str(Card(count=1)).strip() == '<p data-cid-c1="">7</p>'
        assert [captured[name].count for name in ("template", "js", "css")] == [7, 7, 7]

    def test_input_hook_can_supply_an_initially_missing_required_field(self):
        class E(Extension):
            name = "e"

            def on_component_input(self, ctx):
                ctx.kwargs["title"] = "from hook"

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app
            template = """
            <p>{{ title }}</p>
            """

            class Kwargs:
                title: str

        assert str(Card()).strip() == '<p data-cid-c1="">from hook</p>'

    def test_input_hook_added_slot_is_normalized_before_typed_construction(self):
        captured = {}

        class E(Extension):
            name = "e"

            def on_component_input(self, ctx):
                ctx.slots["content"] = "from hook"

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app
            template = """
            <c-slot name="content" />
            """

            class Slots:
                content: Slot

            def template_data(self, kwargs, slots):
                captured["slots"] = slots
                captured["raw"] = self.raw_slots
                return {}

        assert str(Card()).strip() == "from hook"
        assert isinstance(captured["slots"].content, Slot)
        assert captured["slots"].content is captured["raw"]["content"]

    def test_input_hook_invalid_mutation_fails_before_data_methods(self):
        data_called = False

        class E(Extension):
            name = "e"

            def on_component_input(self, ctx):
                ctx.kwargs["unknown"] = 1

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app
            template = """
            <p>card</p>
            """

            class Kwargs:
                title: str

            def template_data(self, kwargs, slots):
                nonlocal data_called
                data_called = True
                return {}

        with pytest.raises(TypeError, match="unexpected keyword argument 'unknown'"):
            str(Card(title="ok"))
        assert not data_called

    def test_typed_default_factories_run_once_after_input_hooks(self):
        calls = {"kwargs": 0, "slots": 0}

        def kwarg_default():
            calls["kwargs"] += 1
            return "default"

        def slot_default():
            calls["slots"] += 1
            return Slot("fallback")

        class E(Extension):
            name = "e"

            def on_component_input(self, ctx):
                assert calls == {"kwargs": 0, "slots": 0}

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app
            template = """
            <p>{{ title }}</p>
            """

            class Kwargs:
                title: str = field(default_factory=kwarg_default)

            class Slots:
                content: Slot = field(default_factory=slot_default)

        assert str(Card()).strip() == '<p data-cid-c1="">default</p>'
        assert calls == {"kwargs": 1, "slots": 1}

    def test_untyped_inputs_keep_raw_identity_after_hook_mutation(self):
        captured = {}

        class E(Extension):
            name = "e"

            def on_component_input(self, ctx):
                ctx.kwargs["added"] = 1
                ctx.slots["content"] = "slot"

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app
            template = """
            <p>card</p>
            """

            def template_data(self, kwargs, slots):
                captured["kwargs"] = kwargs is self.raw_kwargs
                captured["slots"] = slots is self.raw_slots
                captured["slot"] = slots["content"]
                return {}

        str(Card())
        assert captured["kwargs"]
        assert captured["slots"]
        assert isinstance(captured["slot"], Slot)

    def test_input_slots_and_data_payloads(self):
        captured = {}

        class E(Extension):
            name = "e"

            def on_component_input(self, ctx):
                captured["slots"] = dict(ctx.slots)

            def on_component_data(self, ctx):
                captured["js_data"] = dict(ctx.js_data)
                captured["css_data"] = dict(ctx.css_data)

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app
            template = '<p><c-slot name="content" /></p>'

            def js_data(self, kwargs, slots):
                return {"script": "console.log('Hello!')"}

            def css_data(self, kwargs, slots):
                return {"style": "body { color: blue; }"}

        str(Card(slots={"content": "Some content"}))
        # Slot fills arrive in on_component_input already normalized to Slot
        # instances, keyed by slot name.
        assert list(captured["slots"]) == ["content"]
        assert isinstance(captured["slots"]["content"], Slot)
        # The component's js/css data dicts reach a user extension's
        # on_component_data (not just the built-in dependencies extension).
        assert captured["js_data"] == {"script": "console.log('Hello!')"}
        assert captured["css_data"] == {"style": "body { color: blue; }"}

    def test_data_mutation_visible_in_render(self):
        class E(Extension):
            name = "e"

            def on_component_data(self, ctx):
                ctx.template_data["who"] = "world"

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app
            template = "<p>Hello {{ who }}</p>"

        assert str(Card()) == '<p data-cid-c1="">Hello world</p>'

    def test_rendered_replace_with_string(self):
        class E(Extension):
            name = "e"

            def on_component_rendered(self, ctx):
                return "<wrapped/>"

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app
            template = "<p>hi</p>"

        assert str(Card()) == '<wrapped data-cid-c1=""/>'

    def test_rendered_receives_citryrender(self):
        captured = {}

        class E(Extension):
            name = "e"

            def on_component_rendered(self, ctx):
                captured["render"] = ctx.render

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app
            template = "<p>hi</p>"

        str(Card())
        assert isinstance(captured["render"], CitryRender)

    def test_rendered_success_payload(self):
        captured = {}

        class E(Extension):
            name = "e"

            def on_component_rendered(self, ctx):
                captured["component"] = ctx.component
                captured["render"] = ctx.render
                captured["error"] = ctx.error

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app
            template = "<p>hi</p>"

        html = str(Card())
        assert html == '<p data-cid-c1="">hi</p>'
        # On success the hook receives the rendered component instance (its
        # id matches the data-cid instance marker), the final output, and no
        # error.
        assert isinstance(captured["component"], Card)
        assert captured["component"].id == "c1"
        assert str(captured["render"]) == html
        assert captured["error"] is None

    def test_rendered_raise_propagates(self):
        class E(Extension):
            name = "e"

            def on_component_rendered(self, ctx):
                raise ValueError("boom")

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app
            template = "<p>hi</p>"

        with pytest.raises(ValueError, match="boom"):
            str(Card())


class TestTemplateHooks:
    def test_template_loaded_modifies_string(self):
        class E(Extension):
            name = "e"

            def on_template_loaded(self, ctx):
                return ctx.content.replace("Hello", "Hi")

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app
            template = "<p>Hello</p>"

        assert str(Card()) == '<p data-cid-c1="">Hi</p>'

    def test_template_loaded_threads_in_order(self):
        class E1(Extension):
            name = "e1"

            def on_template_loaded(self, ctx):
                return ctx.content + "1"

        class E2(Extension):
            name = "e2"

            def on_template_loaded(self, ctx):
                return ctx.content + "2"

        app = _Citry(extensions=[E1, E2])

        class Card(Component):
            citry = app
            template = "x"

        assert str(Card()) == "x12"

    def test_template_compiled_receives_node_list(self):
        captured = {}

        class E(Extension):
            name = "e"

            def on_template_compiled(self, ctx):
                captured["nodes"] = list(ctx.nodes)
                captured["cls"] = ctx.component_class.__name__

        app = _Citry(extensions=[E])

        class Card(Component):
            citry = app
            template = "<p>{{ x }}</p>"

            def template_data(self, kwargs, slots):
                return {"x": "hi"}

        str(Card())
        assert isinstance(captured["nodes"], list)
        assert captured["cls"] == "Card"


class TestSmartDispatch:
    def test_only_overriding_extensions_define_the_hook(self):
        # Uses hooks the built-in dependencies extension does not implement,
        # so the expected lists are exact.
        class Partial(Extension):
            name = "partial"

            def on_component_input(self, ctx):
                pass

        app = _Citry(extensions=[Partial])
        mgr = app.extensions
        inst = mgr.get_extension("partial")
        assert mgr._extensions_with_hook("on_component_input") == (inst,)
        assert mgr._extensions_with_hook("on_component_rendered") == ()

    def test_hook_extension_list_is_cached(self):
        class E(Extension):
            name = "e"

            def on_component_data(self, ctx):
                pass

        app = _Citry(extensions=[E])
        mgr = app.extensions
        first = mgr._extensions_with_hook("on_component_data")
        assert mgr._extensions_with_hook("on_component_data") is first


class TestComponentConfig:
    def test_config_attached_to_instance(self):
        captured = {}

        class ViewExt(Extension):
            name = "view"

        app = _Citry(extensions=[ViewExt])

        class Page(Component):
            citry = app
            template = "<p>hi</p>"

            class View:
                greeting = "hello"

        # nested class rebuilt as a subclass of the extension's Config base
        assert issubclass(Page.View, ViewExt.Config)

        class Probe(Extension):
            name = "probe"

            def on_component_data(self, ctx):
                captured["view"] = ctx.component.view

        app2 = _Citry(extensions=[ViewExt, Probe])

        class Page2(Component):
            citry = app2
            template = "<p>hi</p>"

            class View:
                greeting = "hello"

        str(Page2())
        assert captured["view"].greeting == "hello"
        assert captured["view"].component_class is Page2

    def test_config_component_backref(self):
        captured = {}

        class ViewExt(Extension):
            name = "view"

            class Config(Extension.Config):
                def title(self):
                    return type(self.component).__name__

        app = _Citry(extensions=[ViewExt])

        class Page(Component):
            citry = app
            template = "<p>hi</p>"

            def template_data(self, kwargs, slots):
                captured["title"] = self.view.title()
                return {}

        str(Page())
        assert captured["title"] == "Page"

    def test_config_out_of_lifecycle_raises(self):
        class E(Extension):
            name = "e"

        cfg = E.Config(None)
        with pytest.raises(RuntimeError, match="outside a component lifecycle"):
            _ = cfg.component

    def test_nested_config_inherits_plain_parent_class(self):
        seen = {}

        class CfgExt(Extension):
            name = "cfg"

            class Config(Extension.Config):
                foo = "1"
                bar = "2"

                @classmethod
                def baz(cls):
                    return "3"

        class NestedParent:
            parent_var = "from_parent"

        app = _Citry(extensions=[CfgExt])

        class Card(Component):
            citry = app
            template = "<p>hi</p>"

            class Cfg(NestedParent):
                nested_var = "from_nested"

            def template_data(self, kwargs, slots):
                seen["values"] = (
                    self.cfg.foo,
                    self.cfg.bar,
                    self.cfg.baz(),
                    self.cfg.nested_var,
                    self.cfg.parent_var,
                )
                return {}

        str(Card())
        # The extension's factory Config attrs, the nested class's own field,
        # and its plain (non-config) parent's field all meet on the instance
        # config during render.
        assert seen["values"] == ("1", "2", "3", "from_nested", "from_parent")

    def test_child_config_automatically_inherits_parent_declaration(self):
        class ProbeExt(Extension):
            name = "probe"

        app = _Citry(extensions=[ProbeExt])

        class Parent(Component):
            citry = app

            class Probe:
                parent_value = "parent"

                def label(self):
                    return self.parent_value

        class Child(Parent):
            class Probe:
                child_value = "child"

                def label(self):
                    return super().label() + ":" + self.child_value

        config = Child.Probe(None)
        assert config.label() == "parent:child"

    def test_config_multiple_inheritance_follows_component_c3(self):
        class ProbeExt(Extension):
            name = "probe"

        app = _Citry(extensions=[ProbeExt])

        class Common(Component):
            citry = app

            class Probe:
                shared = "common"

        class Left(Common):
            class Probe:
                left = True
                shared = "left"

        class Right(Common):
            class Probe:
                right = True
                shared = "right"

        class Combined(Left, Right):
            pass

        assert Combined.Probe.shared == "left"
        assert Combined.Probe.left is True
        assert Combined.Probe.right is True

    def test_config_none_resets_component_values_but_keeps_other_default_levels(self):
        class ProbeExt(Extension):
            name = "probe"

            class Config(Extension.Config):
                factory = "factory"

        app = _Citry(extensions=[ProbeExt], extensions_defaults={"probe": {"global_value": "global"}})

        class Parent(Component):
            citry = app

            class Probe:
                parent_value = "parent"

        class Child(Parent):
            Probe = None

        assert Child.Probe.factory == "factory"
        assert Child.Probe.global_value == "global"
        assert not hasattr(Child.Probe, "parent_value")

    def test_config_none_on_first_c3_branch_shadows_later_branch(self):
        class ProbeExt(Extension):
            name = "probe"

        app = _Citry(extensions=[ProbeExt])

        class Muted(Component):
            citry = app
            Probe = None

        class Kept(Component):
            citry = app

            class Probe:
                kept = True

        class Combined(Muted, Kept):
            pass

        assert not hasattr(Combined.Probe, "kept")

    def test_class_created_context_preserves_authored_declaration_chain(self):
        seen = {}

        class ProbeExt(Extension):
            name = "probe"

            def on_component_class_created(self, ctx):
                if ctx.component_class.__name__ == "Child":
                    seen["declarations"] = ctx.nested_declarations("Probe")

        app = _Citry(extensions=[ProbeExt])

        class ParentProbe:
            parent = True

        class ChildProbe:
            child = True

        class Parent(Component):
            citry = app
            Probe = ParentProbe

        class Child(Parent):
            Probe = ChildProbe

        declarations = seen["declarations"]
        assert [(item.declaring_class, item.value) for item in declarations] == [
            (Child, ChildProbe),
            (Parent, ParentProbe),
        ]
        assert ChildProbe in Child.Probe.__mro__
        assert ParentProbe in Child.Probe.__mro__

    def test_plain_definition_base_keeps_nested_descriptor_source(self):
        owners = []

        class RecordingDescriptor:
            def __set_name__(self, owner, name):
                owners.append((owner, name))

        descriptor = RecordingDescriptor()

        class Definition:
            class Probe:
                authored = descriptor

        class ProbeExt(Extension):
            name = "probe"

        app = _Citry(extensions=[ProbeExt])

        class Bound(Definition, Component):
            citry = app

        assert Definition.Probe in Bound.Probe.__mro__
        assert owners == [(Definition.Probe, "authored")]

    def test_plain_definition_config_validates_once_per_citry_instance(self):
        calls = []

        class ProbeExt(Extension):
            name = "probe"

            def validate_config_fields(self, fields, *, component=None):
                if component is not None:
                    calls.append((component, dict(fields)))

        class Definition:
            class Probe:
                value = 1

        first_app = _Citry(extensions=[ProbeExt])

        class First(Definition, Component):
            citry = first_app

        class FirstSibling(Definition, Component):
            citry = first_app

        second_app = _Citry(extensions=[ProbeExt])

        class Second(Definition, Component):
            citry = second_app

        assert calls == [(First, {"value": 1}), (Second, {"value": 1})]

    def test_defaults_precedence(self):
        # factory < global defaults < component-level
        class CfgExt(Extension):
            name = "cfg"

            class Config(Extension.Config):
                ttl = 1

        # factory only
        app_factory = _Citry(extensions=[CfgExt])

        class A(Component):
            citry = app_factory

        assert A.Cfg.ttl == 1

        # global defaults override factory
        app_global = _Citry(extensions=[CfgExt], extensions_defaults={"cfg": {"ttl": 2}})

        class B(Component):
            citry = app_global

        assert B.Cfg.ttl == 2

        # component-level overrides global
        app_comp = _Citry(extensions=[CfgExt], extensions_defaults={"cfg": {"ttl": 2}})

        class C(Component):
            citry = app_comp

            class Cfg:
                ttl = 3

        assert C.Cfg.ttl == 3

    def test_empty_defaults_entry_is_no_op(self):
        class CfgExt(Extension):
            name = "cfg"

            class Config(Extension.Config):
                foo = "1"
                bar = "2"

                @classmethod
                def baz(cls):
                    return "3"

        app = _Citry(extensions=[CfgExt], extensions_defaults={"cfg": {}})

        class Card(Component):
            citry = app

        # An empty defaults entry changes nothing: every factory Config value,
        # the classmethod included, stays untouched.
        assert (Card.Cfg.foo, Card.Cfg.bar, Card.Cfg.baz()) == ("1", "2", "3")

    def test_defaults_override_attrs_and_classmethods(self):
        class CfgExt(Extension):
            name = "cfg"

            class Config(Extension.Config):
                foo = "1"
                bar = "2"

                @classmethod
                def baz(cls):
                    return "3"

        app = _Citry(
            extensions=[CfgExt],
            extensions_defaults={
                "cfg": {"foo": "NEW_FOO", "baz": classmethod(lambda _cls: "OVERRIDDEN")},
                # An entry naming no installed extension is silently ignored.
                "nonexistent": {"1": "2"},
            },
        )

        class Card(Component):
            citry = app

        # Defaults override a plain attr and a classmethod alike; keys not
        # listed in the defaults keep their factory values.
        assert (Card.Cfg.foo, Card.Cfg.bar, Card.Cfg.baz()) == ("NEW_FOO", "2", "OVERRIDDEN")
        # The extension factory Config itself keeps its authored values: the
        # defaults land on a per-component holder, not on the shared class.
        assert (CfgExt.Config.foo, CfgExt.Config.baz()) == ("1", "3")


class _StrictExt(Extension):
    """A toy extension whose config accepts exactly one field, ``ttl``."""

    name = "strict"

    def validate_config_fields(self, fields, *, component=None):
        for field_name in fields:
            if field_name != "ttl":
                msg = f"unknown config field {field_name!r}; the only field is 'ttl'"
                raise ValueError(msg)


class TestConfigFieldValidation:
    """Extension.validate_config_fields and its two framework call sites."""

    def test_base_accepts_any_defaults_fields(self):
        class Lax(Extension):
            name = "lax"

        # The permissive base accepts fields of any name and shape.
        c = _Citry(extensions=[Lax], extensions_defaults={"lax": {"anything": 1, "_odd": lambda: None}})
        assert c.extensions.get_extension("lax") is not None

    def test_base_accepts_any_component_fields(self):
        class Lax(Extension):
            name = "lax"

        app = _Citry(extensions=[Lax])

        class Card(Component):
            citry = app

            class Lax:
                anything = object()
                _odd = "x"

        assert Card.Lax._odd == "x"

    def test_override_rejects_bad_defaults_field_at_engine_init(self):
        with pytest.raises(ValueError, match="tll") as err:
            _Citry(extensions=[_StrictExt], extensions_defaults={"strict": {"tll": 1}})

        assert (
            "Extension 'strict': invalid config field in the 'extensions_defaults'"
            " setting. unknown config field 'tll'; the only field is 'ttl'" in str(err.value)
        )

    def test_non_mapping_defaults_entry_rejected(self):
        # The whole entry (not just a field inside it) can be wrong: a bare
        # string must fail with a pointed error at engine construction, not
        # as a confusing error from inside the extension's own validation.
        with pytest.raises(ValueError, match="events") as err:
            _Citry(extensions_defaults={"events": "oops"})

        assert (
            "Extension 'events': the entry in the 'extensions_defaults' setting must be"
            " a mapping of config field names to values; got 'oops'." in str(err.value)
        )

    def test_override_rejects_bad_component_field_at_class_creation(self):
        app = _Citry(extensions=[_StrictExt])

        with pytest.raises(ValueError, match="tll") as err:

            class Card(Component):
                citry = app

                class Strict:
                    tll = 2

        assert (
            "Component Card: invalid config field on its nested 'Strict' class (the"
            " 'strict' extension). unknown config field 'tll'; the only field is 'ttl'" in str(err.value)
        )

    def test_valid_fields_pass_both_sites(self):
        app = _Citry(extensions=[_StrictExt], extensions_defaults={"strict": {"ttl": 1}})

        class Card(Component):
            citry = app

            class Strict:
                ttl = 2

        assert Card.Strict.ttl == 2

    def test_method_receives_fields_and_declaration_site(self):
        calls = []

        class Probe(Extension):
            name = "probe"

            class Config(Extension.Config):
                factory_field = 1

            def validate_config_fields(self, fields, *, component=None):
                calls.append((dict(fields), component))

        app = _Citry(extensions=[Probe], extensions_defaults={"probe": {"ttl": 5}})

        class Card(Component):
            citry = app

            class Probe:
                size = 3

        # The defaults validate at engine construction (component=None); the
        # component's own fields validate at class definition (component set).
        # Config-base members (factory_field) are framework attributes, not
        # user-declared fields, so they never appear in the mapping.
        assert calls == [({"ttl": 5}, None), ({"size": 3}, Card)]

    def test_subclass_fields_cover_the_user_written_levels(self):
        calls = []

        class Probe(Extension):
            name = "probe"

            def validate_config_fields(self, fields, *, component=None):
                calls.append((dict(fields), component))

        app = _Citry(extensions=[Probe], extensions_defaults={"probe": {"ttl": 5}})

        class Base(Component):
            citry = app

            class Probe:
                size = 3

        class Sub(Base):
            citry = app

            class Probe(Base.Probe):
                depth = 4

        # Sub's config subclasses the parent's already-rebuilt class: the
        # fields cover the user-written levels only. The rebuilt class's own
        # bookkeeping and the defaults holder are not user fields.
        assert calls[-1] == ({"size": 3, "depth": 4}, Sub)

    def test_subclass_without_own_config_not_revalidated(self):
        calls = []

        class Probe(Extension):
            name = "probe"

            def validate_config_fields(self, fields, *, component=None):
                calls.append(component)

        app = _Citry(extensions=[Probe])

        class Base(Component):
            citry = app

            class Probe:
                size = 3

        class Sub(Base):
            citry = app

        # Sub declares no config of its own; the inherited one was already
        # validated when Base was defined.
        assert calls == [Base]


class TestCommands:
    def test_no_commands_by_default(self):
        # The default instance carries only built-in extensions; of those,
        # only the events extension declares a command (its OpenAPI export).
        assert _Citry().commands == {"events": (OpenApiCommand,)}

    def test_commands_keyed_by_extension(self):
        class Hello(ExtensionCommand):
            name = "hello"

            def handle(self, **kwargs): ...

        class Greeter(Extension):
            name = "greeter"
            commands = [Hello]

        assert _Citry(extensions=[Greeter]).commands == {
            "events": (OpenApiCommand,),
            "greeter": (Hello,),
        }

    def test_extensions_without_commands_are_omitted(self):
        class Hello(ExtensionCommand):
            name = "hello"

            def handle(self, **kwargs): ...

        class WithCmd(Extension):
            name = "withcmd"
            commands = [Hello]

        class WithoutCmd(Extension):
            name = "withoutcmd"

        # Built-ins come first; only extensions that declare commands appear.
        assert list(_Citry(extensions=[WithCmd, WithoutCmd]).commands) == ["events", "withcmd"]

    def test_get_extension_command_resolves(self):
        class Hello(ExtensionCommand):
            name = "hello"

            def handle(self, **kwargs): ...

        class Greeter(Extension):
            name = "greeter"
            commands = [Hello]

        manager = _Citry(extensions=[Greeter]).extensions
        assert manager.get_extension_command("greeter", "hello") is Hello

    def test_get_extension_command_missing_raises(self):
        class Greeter(Extension):
            name = "greeter"

        manager = _Citry(extensions=[Greeter]).extensions
        with pytest.raises(ValueError, match="not found"):
            manager.get_extension_command("greeter", "nope")
