"""Check which component declarations can render without a component instance."""

from __future__ import annotations

from dataclasses import MISSING, dataclass, fields
from inspect import isasyncgenfunction, iscoroutinefunction, isgeneratorfunction, signature
from types import FunctionType, GetSetDescriptorType
from typing import TYPE_CHECKING, Any, cast

from citry._class_introspection import _safe_class_text, _static_class_dict, _static_class_mro
from citry._nested_declarations import _active_nested_class_declarations
from citry.assets import _find_pair_declaration

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


_ASSET_PAIRS = (("js", "js_file"), ("css", "css_file"), ("messages", "messages_file"))
_INSTANCE_CONFIGS = ("State", "Events", "Cache", "Dependencies", "I18n", "JsData", "CssData")
_ANNOTATION_CACHE_NAMES = frozenset({"__annotations__", "__annotate__", "__annotate_func__", "__annotations_cache__"})
_SLOT_DECLARATION_METADATA = frozenset(
    {
        "__module__",
        "__doc__",
        "__qualname__",
        "__annotations__",
        "__annotate__",
        "__annotate_func__",
        "__annotations_cache__",
        "__dict__",
        "__weakref__",
        "__firstlineno__",
        "__static_attributes__",
        "__type_params__",
    }
)


@dataclass(frozen=True, slots=True)
class SimpleDeclaration:
    """Keep the checked callback and input schemas for one effective class definition."""

    callback: Callable[[Any, Any], Any] | None
    kwargs_schema: type | None
    slots_schema: type | None
    data_schema: type | None
    slot_namespaces: tuple[tuple[type, tuple[tuple[str, object], ...]], ...] = ()

    def check_slots_unchanged(self) -> None:
        """Reject schema rebinding that could change the checked slot constructor."""
        if self.slots_schema is not None:
            current_mro = tuple(cls for cls in _static_class_mro(self.slots_schema) if cls is not object)
            if current_mro != tuple(cls for cls, _namespace in self.slot_namespaces):
                raise TypeError("A simple component's Slots declaration changed; define a new component subclass.")
        for cls, expected in self.slot_namespaces:
            namespace = _static_class_dict(cls)
            # Python may materialize annotation caches after class creation;
            # generated dataclass fields and constructors are already fixed.
            actual_count = len(namespace) - sum(name in namespace for name in _ANNOTATION_CACHE_NAMES)
            if actual_count != len(expected) or any(namespace.get(name) is not value for name, value in expected):
                raise TypeError("A simple component's Slots declaration changed; define a new component subclass.")


def validate_simple_declaration(
    component_class: type,
    component_base: type,
    *,
    extension_names: Iterable[str] = (),
) -> SimpleDeclaration:
    """
    Reject declarations that require an independent component instance.

    The caller checks the boolean opt-in and invokes this after schema and
    extension composition, before registration. Inspect descriptors without
    binding them: checking a class must not execute an authored property.
    """
    name = _safe_class_text(component_class, "__name__") or "Component"
    effective: dict[str, object] = {}
    for base in reversed(_static_class_mro(component_class)):
        effective.update(_static_class_dict(base))
    ordinary = _static_class_dict(component_base)
    object_members = _static_class_dict(object)

    for inline, file in _ASSET_PAIRS:
        _owner, inline_value, file_value = _find_pair_declaration(component_class, inline, file)
        for asset, value in ((inline, inline_value), (file, file_value)):
            if value is not None:
                msg = f"Component {name} uses simple=True but declares {asset}."
                raise ValueError(msg)
    if effective.get("transparent", False) is not False:
        msg = f"Component {name} uses simple=True; transparent must be False."
        raise ValueError(msg)
    for schema_name in ("Kwargs", "TemplateData"):
        schema = effective.get(schema_name)
        if schema is not None and not issubclass(type(schema), type):
            msg = f"Component {name} uses simple=True; {schema_name} must be a class or None."
            raise TypeError(msg)

    # Extensions synthesize default configuration classes even when authors
    # requested nothing. Only the active authored declarations opt into them.
    for config in dict.fromkeys((*_INSTANCE_CONFIGS, *extension_names)):
        if _active_nested_class_declarations(component_class, config):
            msg = f"Component {name} uses simple=True but declares {config}."
            raise ValueError(msg)

    callback: Callable[[Any, Any], Any] | None = None
    data_method = effective.get("template_data")
    if data_method is not ordinary.get("template_data"):
        if type(data_method) is not staticmethod or type(data_method.__func__) is not FunctionType:
            msg = f"Component {name} uses simple=True; template_data must be a static method."
            raise TypeError(msg)
        function = data_method.__func__
        if iscoroutinefunction(function) or isgeneratorfunction(function) or isasyncgenfunction(function):
            msg = f"Component {name} uses simple=True; template_data must be a synchronous function."
            raise TypeError(msg)
        try:
            # Ignore a decorator's advertised signature; rendering calls the
            # actual function with these two positional arguments.
            signature_function = FunctionType(
                function.__code__, function.__globals__, argdefs=function.__defaults__, closure=function.__closure__
            )
            signature_function.__kwdefaults__ = function.__kwdefaults__
            signature(signature_function, follow_wrapped=False).bind(object(), object())
        except TypeError as error:
            msg = f"Component {name} uses simple=True; template_data must accept kwargs and slots positionally."
            raise TypeError(msg) from error
        callback = function

    for member, value in effective.items():
        if member == "template_data" or member in _ANNOTATION_CACHE_NAMES:
            continue
        if member in {"__dict__", "__weakref__"} and type(value) is GetSetDescriptorType:
            continue
        if member in ordinary and value is ordinary[member]:
            continue
        if member in object_members and value is object_members[member]:
            continue
        if type(ordinary.get(member)) in (FunctionType, staticmethod, classmethod, property):
            msg = f"Component {name} uses simple=True but overrides {member}."
            raise TypeError(msg)
        if member in object_members and (
            callable(object_members[member]) or hasattr(type(object_members[member]), "__get__")
        ):
            msg = f"Component {name} uses simple=True but overrides {member}."
            raise TypeError(msg)
        # A user helper may be a static function or plain data. An instance
        # descriptor would expose behavior that this mode never constructs.
        if type(value) is staticmethod and type(value.__func__) is FunctionType:
            if member in ordinary:
                msg = f"Component {name} uses simple=True but overrides {member}."
                raise TypeError(msg)
            continue
        if type(value) in (FunctionType, classmethod, property) or (
            any("__get__" in _static_class_dict(base) for base in _static_class_mro(type(value)))
        ):
            msg = f"Component {name} uses simple=True but declares unsupported method or descriptor {member}."
            raise TypeError(msg)

    slots_schema = effective.get("Slots")
    if slots_schema is not None:
        # Default content has no named-slot selection or schema coercion. Keep
        # its initial schema explicit so a factory cannot create hidden fills.
        if type(slots_schema) is not type:
            msg = f"Component {name} uses simple=True; Slots must be a plain field class."
            raise TypeError(msg)
        for declaration in _active_nested_class_declarations(component_class, "Slots"):
            for base in _static_class_mro(cast("type", declaration.value)):
                if base is object:
                    continue
                namespace = _static_class_dict(base)
                unexpected = namespace.keys() - _SLOT_DECLARATION_METADATA - {"default"}
                if unexpected:
                    msg = f"Component {name} uses simple=True; Slots must contain plain field declarations only."
                    raise TypeError(msg)
        schema_fields = _static_class_dict(slots_schema).get("__dataclass_fields__")
        if type(schema_fields) is not dict:
            msg = f"Component {name} uses simple=True; Slots must be a plain field class."
            raise TypeError(msg)
        # Only ordinary fields store the supplied content on the instance.
        # InitVar and ClassVar declarations must not masquerade as an outlet.
        instance_fields = fields(slots_schema)
        if len(instance_fields) != len(schema_fields):
            msg = f"Component {name} uses simple=True; Slots does not support InitVar or ClassVar declarations."
            raise TypeError(msg)
        for field in instance_fields:
            if (
                field.name != "default"
                or field.default_factory is not MISSING
                or field.default is not None
                or not field.init
            ):
                msg = f"Component {name} uses simple=True; Slots supports only an optional default field with None."
                raise ValueError(msg)

    return SimpleDeclaration(
        callback=callback,
        kwargs_schema=cast("type | None", effective.get("Kwargs")),
        slots_schema=cast("type | None", slots_schema),
        data_schema=cast("type | None", effective.get("TemplateData")),
        slot_namespaces=(
            tuple(
                (
                    cls,
                    tuple(
                        (name, value)
                        for name, value in _static_class_dict(cls).items()
                        if name not in _ANNOTATION_CACHE_NAMES
                    ),
                )
                for cls in _static_class_mro(slots_schema)
                if cls is not object
            )
            if slots_schema is not None
            else ()
        ),
    )
