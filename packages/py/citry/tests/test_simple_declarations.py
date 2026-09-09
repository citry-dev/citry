"""Qualify declaration checks before connecting them to simple rendering."""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from inspect import Signature
from typing import ClassVar

import pytest

from citry import Citry, Component, ComponentLibrary, LibraryComponent, Slot
from citry._simple_declarations import validate_simple_declaration


def test_default_data_and_static_callback_use_effective_schemas() -> None:
    app = Citry()

    class Label(Component):
        citry = app

        class Kwargs:
            text: str

        template = """
            <span>{{ text }}</span>
        """

    declaration = validate_simple_declaration(Label, Component)
    assert declaration.callback is None
    assert declaration.kwargs_schema is Label.Kwargs

    class UpperLabel(Label):
        class Slots:
            default: Slot | None = None

        @staticmethod
        def template_data(kwargs, slots):
            return {"text": kwargs.text.upper(), "has_content": slots.default is not None}

    declaration = validate_simple_declaration(UpperLabel, Component)
    assert declaration.callback(UpperLabel.Kwargs("label"), UpperLabel.Slots()) == {
        "text": "LABEL",
        "has_content": False,
    }


@pytest.mark.parametrize("asset", ["js", "js_file", "css", "css_file", "messages", "messages_file"])
def test_inherited_assets_are_rejected_even_when_empty(asset: str) -> None:
    base = type("AssetBase", (Component,), {"citry": Citry(), asset: ""})
    child = type("AssetChild", (base,), {})
    with pytest.raises(ValueError, match=f"declares {asset}"):
        validate_simple_declaration(child, Component)


def test_descriptors_are_inspected_without_execution() -> None:
    reads = []

    class Descriptor:
        def __get__(self, instance, owner):
            reads.append(owner)
            raise AssertionError("validation executed a descriptor")

    class Label(Component):
        citry = Citry()
        helper = Descriptor()

    with pytest.raises(TypeError, match="descriptor helper"):
        validate_simple_declaration(Label, Component)
    assert reads == []


@pytest.mark.parametrize(
    "method", ["on_render", "js_data", "css_data", "provide", "inject", "__init__", "__new__", "__getattribute__"]
)
def test_core_methods_cannot_be_overridden_or_disabled(method: str) -> None:
    component = type("Overridden", (Component,), {"citry": Citry(), method: None})
    with pytest.raises(TypeError, match=f"overrides {method}"):
        validate_simple_declaration(component, Component)


def test_callback_form_and_actual_signature_are_checked() -> None:
    def instance_method(self, kwargs, slots):
        return kwargs

    def wrong_static_method(kwargs):
        return kwargs

    # Advertised introspection cannot make a one-input function accept two.
    wrong_static_method.__signature__ = Signature()

    async def async_method(kwargs, slots):
        return kwargs

    def generator_method(kwargs, slots):
        yield kwargs

    async def async_generator_method(kwargs, slots):
        yield kwargs

    cases = (
        (instance_method, "static method"),
        (classmethod(instance_method), "static method"),
        (staticmethod(wrong_static_method), "accept kwargs and slots"),
        (staticmethod(async_method), "synchronous"),
        (staticmethod(generator_method), "synchronous"),
        (staticmethod(async_generator_method), "synchronous"),
    )
    for callback, message in cases:
        component = type("BadCallback", (Component,), {"citry": Citry(), "template_data": callback})
        with pytest.raises(TypeError, match=message):
            validate_simple_declaration(component, Component)


def test_authored_extension_config_is_distinct_from_synthesized_defaults() -> None:
    class Plain(Component):
        citry = Citry()

    validate_simple_declaration(Plain, Component, extension_names=("Events", "Dependencies", "Cache", "I18n"))

    class WithConfig(Plain):
        class Dependencies:
            pass

    class InheritedConfig(WithConfig):
        pass

    with pytest.raises(ValueError, match="declares Dependencies"):
        validate_simple_declaration(InheritedConfig, Component)

    class ResetConfig(WithConfig):
        Dependencies = None

    validate_simple_declaration(ResetConfig, Component)


def test_slot_schema_rejects_names_required_values_and_factories() -> None:
    schemas = (
        type("Slots", (), {"__annotations__": {"header": Slot}, "header": None}),
        type("Slots", (), {"__annotations__": {"default": Slot}}),
        type("Slots", (), {"__annotations__": {"default": Slot}, "default": "fallback"}),
        type("Slots", (), {"__annotations__": {"default": Slot}, "default": field(default_factory=lambda: None)}),
    )
    for schema in schemas:
        component = type("WithSlots", (Component,), {"citry": Citry(), "Slots": schema})
        with pytest.raises(
            (TypeError, ValueError), match=r"plain field declarations|optional default field with None"
        ):
            validate_simple_declaration(component, Component)


def test_inherited_instance_helper_is_rejected_but_static_helper_is_allowed() -> None:
    class HelperMixin:
        def helper(self):
            return "instance"

    class Label(HelperMixin, Component):
        citry = Citry()

    with pytest.raises(TypeError, match="descriptor helper"):
        validate_simple_declaration(Label, Component)

    class StaticLabel(Label):
        @staticmethod
        def helper():
            return "static"

    validate_simple_declaration(StaticLabel, Component)


@pytest.mark.parametrize(("inline", "file"), [("css", "css_file"), ("js", "js_file"), ("messages", "messages_file")])
def test_resetting_either_asset_field_resets_the_whole_pair(inline: str, file: str) -> None:
    for original, reset in ((inline, file), (file, inline)):
        base = type("AssetBase", (Component,), {"citry": Citry(), original: "unused"})
        child = type("ResetAsset", (base,), {reset: None})
        validate_simple_declaration(child, Component)


def test_private_prefix_does_not_hide_authored_instance_methods() -> None:
    class PrivateHelper(Component):
        citry = Citry()

        def _citry_helper(self):
            return self.id

    with pytest.raises(TypeError, match="descriptor _citry_helper"):
        validate_simple_declaration(PrivateHelper, Component)


def test_helper_metaclass_and_class_property_are_not_executed() -> None:
    class Meta(type):
        def __getattribute__(cls, name):
            if name == "__get__":
                raise AssertionError("metaclass executed")
            return super().__getattribute__(name)

    class Helper(metaclass=Meta):
        @property
        def __class__(self):
            raise AssertionError("class property executed")

    class Label(Component):
        citry = Citry()
        helper = Helper()

    validate_simple_declaration(Label, Component)


def test_authored_slot_constructor_behavior_is_rejected() -> None:
    @dataclass
    class Slots:
        default: Slot | None = None

        def __post_init__(self):
            self.default = "hidden content"

    component = type("HiddenDefault", (Component,), {"citry": Citry(), "Slots": Slots})
    with pytest.raises(TypeError, match="plain field declarations"):
        validate_simple_declaration(component, Component)


@pytest.mark.parametrize("annotation", [InitVar[Slot], ClassVar[Slot]])
def test_slot_field_must_store_a_supplied_value(annotation: object) -> None:
    schema = type("Slots", (), {"__annotations__": {"default": annotation}, "default": None})
    component = type("NonStoredSlot", (Component,), {"citry": Citry(), "Slots": schema})
    with pytest.raises(TypeError, match="InitVar or ClassVar"):
        validate_simple_declaration(component, Component)


def test_slot_field_must_accept_a_constructor_input() -> None:
    schema = type("Slots", (), {"__annotations__": {"default": Slot}, "default": field(default=None, init=False)})
    component = type("NonInputSlot", (Component,), {"citry": Citry(), "Slots": schema})
    with pytest.raises(ValueError, match="optional default field"):
        validate_simple_declaration(component, Component)


@pytest.mark.parametrize("name", ["Kwargs", "TemplateData"])
def test_data_schema_is_a_class_or_none(name: str) -> None:
    component = type("InvalidSchema", (Component,), {"citry": Citry(), name: 42})
    with pytest.raises(TypeError, match=f"{name} must be a class or None"):
        validate_simple_declaration(component, Component)


@pytest.mark.parametrize("name", ["__dict__", "__weakref__"])
def test_authored_instance_metadata_properties_are_rejected(name: str) -> None:
    descriptor = property(lambda _self: None)
    component = type("InstanceMetadata", (Component,), {"citry": Citry(), name: descriptor})
    with pytest.raises(TypeError, match=f"descriptor {name}"):
        validate_simple_declaration(component, Component)


def test_slot_constructor_hooks_are_rejected_regardless_of_descriptor_type() -> None:
    class PostInit:
        def __get__(self, instance, owner):
            return lambda: setattr(instance, "default", "hidden")

    for hook in (None, PostInit()):
        schema = type(
            "Slots",
            (),
            {"__annotations__": {"default": Slot}, "default": None, "__post_init__": hook},
        )
        component = type("HookedSlot", (Component,), {"citry": Citry(), "Slots": schema})
        with pytest.raises(TypeError, match="plain field declarations"):
            validate_simple_declaration(component, Component)


def test_class_valued_descriptors_are_rejected_without_binding() -> None:
    bindings = []

    class DescriptorMeta(type):
        def __get__(cls, instance, owner):
            bindings.append(owner)
            return "bound"

    class DescriptorClass(metaclass=DescriptorMeta):
        pass

    class Label(Component):
        citry = Citry()
        helper = DescriptorClass

    with pytest.raises(TypeError, match="descriptor helper"):
        validate_simple_declaration(Label, Component)
    assert bindings == []


def test_library_materializations_are_validated_with_their_effective_schemas() -> None:
    class Label(LibraryComponent):
        class Kwargs:
            text: str

        @staticmethod
        def template_data(kwargs, _slots):
            return {"text": kwargs.text.upper()}

        template = """
            <span>{{ text }}</span>
        """

    library = ComponentLibrary(name="simple-declaration-probe", components=(Label,))
    concrete_classes = []
    for _index in range(2):
        app = Citry()
        concrete = app.register_library(library).component(Label)
        declaration = validate_simple_declaration(concrete, Component)
        assert declaration.kwargs_schema is concrete.Kwargs
        assert declaration.callback(concrete.Kwargs("label"), {}) == {"text": "LABEL"}
        concrete_classes.append(concrete)
    assert concrete_classes[0] is not concrete_classes[1]
