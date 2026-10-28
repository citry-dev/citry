"""
Choose the kind of class Citry generates from plain schema declarations.

A component's plain ``class Kwargs:`` (and ``TemplateData``, ``JsData``,
``CssData``, ``State``, and Events ``data`` classes) becomes a class Citry
generates. By default that is a slotted dataclass. ``CitrySettings.model_base``
names another kind, and a base the generated classes share:

- a dataclass, whose options (``frozen``, ``kw_only``, ...) the generated
  dataclasses copy;
- a Pydantic v2 or v1 model, which every generated model subclasses, so its
  ``model_config`` (or ``class Config``) and validators are shared;
- ``typing.NamedTuple``, which makes Citry generate named tuples.

This module reads the setting once, when the ``Citry`` instance is built,
and builds each generated class for the kind it names.
"""

from __future__ import annotations

import collections
import functools
import typing
from dataclasses import MISSING, Field, dataclass, is_dataclass
from importlib import import_module
from types import FunctionType, new_class
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from citry._class_introspection import (
    _safe_class_text,
    _static_class_dict,
    _static_class_mro,
    _static_class_namespace_copy,
)

if TYPE_CHECKING:
    from collections.abc import Callable

ModelKindName = Literal["dataclass", "pydantic-v2", "pydantic-v1", "namedtuple"]

# One example per kind, for the errors that list what `model_base` accepts.
_KIND_EXAMPLES = (
    "a dataclass such as `@dataclass(kw_only=True) class Model: ...`",
    "a Pydantic v2 model class such as `pydantic.BaseModel` or a subclass of it",
    "a Pydantic v1 model class such as `pydantic.v1.BaseModel`",
    "`typing.NamedTuple`, to generate named tuples",
)

# Names a class body always has. They describe the authored class, so a
# generated model or named tuple must not copy them.
_CLASS_BOOKKEEPING_NAMES = frozenset(
    {
        "__dict__",
        "__weakref__",
        "__module__",
        "__qualname__",
        "__annotations__",
        "__annotate__",
        "__annotate_func__",
        "__annotations_cache__",
        "__firstlineno__",
        "__static_attributes__",
        "__orig_bases__",
        "__parameters__",
        "__slots__",
        "__classcell__",
        # The generated class writes its own constructor, as a generated
        # dataclass does.
        "__init__",
        "__new__",
    }
)


@dataclass(frozen=True, slots=True)
class ModelBase:
    """The resolved ``model_base`` setting: its kind and the class it names."""

    kind: ModelKindName
    # The class every generated class subclasses. For the NamedTuple kind it
    # is `typing.NamedTuple`, which only names the kind.
    base: Any

    @property
    def label(self) -> str:
        """Name the kind in an error message."""
        return {
            "dataclass": "a dataclass",
            "pydantic-v2": "a Pydantic v2 model",
            "pydantic-v1": "a Pydantic v1 model",
            "namedtuple": "a NamedTuple",
        }[self.kind]


def _class_lookup(cls: type, name: str) -> object:
    """Read a class attribute through the MRO namespaces, without calling metaclass hooks."""
    for klass in _static_class_mro(cls):
        namespace = _static_class_dict(klass)
        if name in namespace:
            return namespace[name]
    return None


def _describe(value: object) -> str:
    """Name a value in an error message by its qualified name when it has one."""
    if isinstance(value, type):
        module = _safe_class_text(value, "__module__")
        qualname = _safe_class_text(value, "__qualname__") or _safe_class_text(value, "__name__") or "<class>"
        return f"{module}.{qualname}" if module and module != "builtins" else qualname
    return repr(value)


def _kinds_sentence() -> str:
    return "model_base accepts " + "; ".join(_KIND_EXAMPLES) + "."


def _pydantic_kind(value: type) -> ModelKindName | None:
    """Tell a Pydantic v2 model class from a v1 one, without importing Pydantic."""
    for klass in _static_class_mro(value):
        if _safe_class_text(klass, "__name__") != "BaseModel":
            continue
        module = _safe_class_text(klass, "__module__") or ""
        if module == "pydantic.v1.main":
            return "pydantic-v1"
        if module == "pydantic.main":
            # The 1.x package keeps its BaseModel in `pydantic.main` too; only
            # v2 models carry `model_fields`.
            return "pydantic-v2" if "model_fields" in dir(klass) else "pydantic-v1"
    return None


def _generated_init(init: object) -> bool:
    """Whether a dataclass ``__init__`` is the one ``@dataclass`` wrote."""
    code = getattr(init, "__code__", None)
    return code is not None and code.co_filename == "<string>"


def check_model_base(value: object) -> ModelBase | None:
    """
    Check a ``model_base`` value that is already a class, or ``None``, and return its kind.

    An import string is resolved by [`resolve_model_base`] instead, when the
    ``Citry`` instance is built, so a settings module can name the base
    without importing it.

    Raises:
        TypeError: The value names none of the four kinds, a root model, a
            Pydantic dataclass, a NamedTuple class with fields, or a dataclass
            with a hand-written ``__init__``.

    """
    if value is None:
        return None
    # `typing.NamedTuple` is a function in current Python, so check it by
    # identity before requiring a class.
    if value is typing.NamedTuple:
        return ModelBase("namedtuple", typing.NamedTuple)
    if not isinstance(value, type):
        msg = f"CitrySettings.model_base must be a class or an import string, got {value!r}. {_kinds_sentence()}"
        raise TypeError(msg)
    pydantic_kind = _pydantic_kind(value)
    if pydantic_kind is not None:
        # A root model holds one value, not named fields, so no schema fits it.
        if any(
            _safe_class_text(klass, "__name__") == "RootModel"
            and (_safe_class_text(klass, "__module__") or "").startswith("pydantic")
            for klass in _static_class_mro(value)
        ):
            msg = (
                f"CitrySettings.model_base got the root model {_describe(value)}, which holds one value, not named"
                " fields. Pass a BaseModel subclass instead."
            )
            raise TypeError(msg)
        return ModelBase(pydantic_kind, value)
    if issubclass(value, tuple) and isinstance(_class_lookup(value, "_fields"), tuple):
        msg = (
            f"CitrySettings.model_base got the named tuple {_describe(value)}, but a named tuple cannot be"
            " extended. Pass `typing.NamedTuple` to generate named tuples."
        )
        raise TypeError(msg)
    if is_dataclass(value):
        # A Pydantic dataclass validates in its own constructor, which the
        # generated dataclass would replace.
        if (
            _class_lookup(value, "__pydantic_validator__") is not None
            or _class_lookup(value, "__pydantic_fields__")
            or _class_lookup(value, "__pydantic_model__") is not None
        ):
            msg = (
                f"CitrySettings.model_base got the Pydantic dataclass {_describe(value)}, which is not a kind Citry"
                " can generate. Pass a pydantic.BaseModel subclass to generate Pydantic models."
            )
            raise TypeError(msg)
        # The generated dataclass writes its own constructor, so one the base
        # wrote by hand would never run. Only the constructor the base itself
        # uses counts: a mixin's `__init__` that the dataclass replaced is fine.
        init_owner = next(
            (klass for klass in _static_class_mro(value) if "__init__" in _static_class_dict(klass)), object
        )
        if init_owner is not object and not _generated_init(_static_class_dict(init_owner)["__init__"]):
            whose = "defines `__init__`" if init_owner is value else f"uses the `__init__` of {_describe(init_owner)}"
            msg = (
                f"CitrySettings.model_base {_describe(value)} {whose}, but Citry generates the constructor of each"
                " schema, so it would never run. Move the logic to `__post_init__`."
            )
            raise TypeError(msg)
        return ModelBase("dataclass", value)
    msg = (
        f"CitrySettings.model_base got {_describe(value)}, which is not a kind Citry can generate. {_kinds_sentence()}"
    )
    raise TypeError(msg)


def resolve_model_base(value: object) -> ModelBase | None:
    """
    Resolve the ``model_base`` setting, importing it when it is a string.

    Raises:
        ImportError: An import string names a module that cannot be imported,
            or a name that module does not have.
        TypeError: The value is not one of the four kinds (see
            [`check_model_base`]).

    """
    if not isinstance(value, str):
        return check_model_base(value)
    module_path, _, attr_name = value.rpartition(".")
    if not module_path or not attr_name:
        msg = (
            f"CitrySettings.model_base import string {value!r} must name a module and a class,"
            " such as 'pydantic.BaseModel'."
        )
        raise TypeError(msg)
    try:
        module = import_module(module_path)
    except ImportError as error:
        # A typo, a missing package, and a module whose own imports fail all
        # land here, so name what failed rather than guess.
        msg = (
            f"CitrySettings.model_base names {value!r}, but {module_path!r} could not be imported ({error})."
            " Check the spelling, or install the package that provides it."
        )
        raise ImportError(msg) from error
    try:
        resolved = getattr(module, attr_name)
    except AttributeError as error:
        msg = f"CitrySettings.model_base names {value!r}, but {module_path!r} has no {attr_name!r}."
        raise ImportError(msg) from error
    return check_model_base(resolved)


def _calls_super(member: object) -> str | None:
    """Return the name of a function in ``member`` that calls ``super()``."""
    functions: list[object] = []
    if isinstance(member, (staticmethod, classmethod)):
        functions.append(member.__func__)
    elif isinstance(member, property):
        functions.extend((member.fget, member.fset, member.fdel))
    elif isinstance(member, functools.cached_property):
        functions.append(member.func)
    else:
        functions.append(member)
    for candidate in functions:
        # A decorator built with `functools.wraps` keeps the real function.
        function = candidate
        wrapped = getattr(function, "__wrapped__", None)
        while isinstance(wrapped, FunctionType):
            function = wrapped
            wrapped = getattr(function, "__wrapped__", None)
        # Python gives every function that mentions `super` a closure cell
        # named `__class__`, which still names the authored class after
        # copying, and the authored bases are not in the generated class's MRO.
        if isinstance(function, FunctionType) and "__class__" in function.__code__.co_freevars:
            return function.__name__
        # A decorator without `functools.wraps` keeps the function only in
        # its closure.
        for cell in getattr(function, "__closure__", None) or ():
            try:
                inner = cell.cell_contents
            except ValueError:
                continue
            if isinstance(inner, FunctionType) and "__class__" in inner.__code__.co_freevars:
                return inner.__name__
    return None


@dataclass(frozen=True, slots=True)
class BuildInput:
    """What every kind's build step receives for one plain declaration."""

    # The authored class and the component that declares it, for messages.
    user_cls: type
    component_name: str | None
    schema_name: str
    # Annotations in field order, resolved in the module of the class that
    # wrote each one, with that class. `field_names` leaves out `ClassVar`s.
    annotations: dict[str, Any]
    field_owners: dict[str, type]
    field_names: tuple[str, ...]
    module: str
    qualname: str
    class_name: str


def _copied_members(build: BuildInput) -> dict[str, Any]:
    """
    Collect the authored class's methods and other members for a class that cannot inherit it.

    A generated model or named tuple does not have the authored class as a
    base (Pydantic rejects or warns on that), so its members are copied.

    Raises:
        TypeError: A copied function calls ``super()``, which would still
            name the authored class.

    """
    members: dict[str, Any] = {}
    for klass in reversed(_static_class_mro(build.user_cls)):
        if klass is object:
            continue
        # A copy: another thread may store a computed value on the class.
        for member_name, member in _static_class_namespace_copy(klass).items():
            if member_name in _CLASS_BOOKKEEPING_NAMES or member_name in build.field_names:
                continue
            calls_super = _calls_super(member)
            if calls_super is not None:
                raise _super_error(build, klass, member_name, member)
            members[member_name] = member
    return members


def _super_error(build: BuildInput, owner: type, member_name: str, member: object) -> TypeError:
    """Explain why a copied method cannot call ``super()``, naming the parent method to call instead."""
    prefix = f"Component {build.component_name}: " if build.component_name else ""
    owner_name = _safe_class_text(owner, "__name__") or build.schema_name
    where = build.schema_name if owner is build.user_cls else owner_name
    mro = _static_class_mro(build.user_cls)
    # The class `super()` would have reached: the next one after the class
    # that wrote the method.
    following = mro[mro.index(owner) + 1 :] if owner in mro else ()
    parent = next(
        (klass for klass in following if klass is not object and member_name in _static_class_dict(klass)), None
    )
    if parent is None:
        parent_call = "on its parent class"
    else:
        accessor = ".fget" if isinstance(member, property) else ""
        parent_call = f"such as {_safe_class_text(parent, '__name__')}.{member_name}{accessor}(self)"
    return TypeError(
        f"{prefix}{where}.{member_name} calls super(), which cannot work in the class Citry generates for"
        f" model_base for {build.schema_name}, because that class does not inherit the class you wrote. Call the"
        f" parent method directly, {parent_call}, or decorate {build.schema_name} with @dataclass to keep it a"
        " dataclass."
    )


def _field_default(build: BuildInput, field_name: str) -> object:
    """Return the default the authored classes give one field, or ``MISSING``."""
    for klass in _static_class_mro(build.user_cls):
        namespace = _static_class_dict(klass)
        if field_name in namespace:
            return namespace[field_name]
    return MISSING


def _pydantic_package(model_base: ModelBase) -> Any:
    """Return the Pydantic package the base comes from: ``pydantic``, or ``pydantic.v1`` under Pydantic 2."""
    for klass in _static_class_mro(model_base.base):
        if _safe_class_text(klass, "__name__") == "BaseModel":
            module = _safe_class_text(klass, "__module__") or "pydantic.main"
            return import_module(module.rsplit(".", 1)[0])
    return import_module("pydantic")


def _pydantic_field(build: BuildInput, model_base: ModelBase, field_name: str, default: Field[Any]) -> object:
    """
    Turn a dataclass ``field(...)`` default into the matching Pydantic ``Field``.

    Raises:
        TypeError: The field uses ``init=False``, which a model has no way to
            express: every model field is an input.

    """
    if not default.init:
        prefix = f"Component {build.component_name}: " if build.component_name else ""
        msg = (
            f"{prefix}{build.schema_name}.{field_name} uses field(init=False), but every field of a Pydantic model"
            " is an input. Compute the value in a method or a property, or decorate"
            f" {build.schema_name} with @dataclass to keep it a dataclass."
        )
        raise TypeError(msg)
    pydantic = _pydantic_package(model_base)
    options: dict[str, Any] = {}
    # Citry and the editor read a field's description from its metadata.
    description = default.metadata.get("description") if default.metadata else None
    if isinstance(description, str):
        options["description"] = description
    if default.default_factory is not MISSING:
        return pydantic.Field(default_factory=default.default_factory, **options)
    if default.default is not MISSING:
        return pydantic.Field(default=default.default, **options)
    return pydantic.Field(**options)


def build_pydantic_model(build: BuildInput, model_base: ModelBase) -> type:
    """
    Generate a Pydantic model that subclasses the base, from a plain declaration.

    A ``Const`` default stays as the field's default, which is how an
    authored model declares one; Citry's authored-model path then carries it
    through validation.

    Raises:
        TypeError: A copied method calls ``super()``, a field starts with an
            underscore or uses ``field(init=False)``, or Pydantic cannot build
            a validator for a field.

    """
    prefix = f"Component {build.component_name}: " if build.component_name else ""
    for field_name in build.field_names:
        # Pydantic keeps an underscore name as a private attribute, which an
        # input would silently skip.
        if field_name.startswith("_"):
            msg = (
                f"{prefix}{build.schema_name}.{field_name} starts with an underscore, which Pydantic keeps as a"
                " private attribute, not an input. Rename the field, or decorate"
                f" {build.schema_name} with @dataclass to keep it a dataclass."
            )
            raise TypeError(msg)
    namespace: dict[str, Any] = _copied_members(build)
    annotations = dict(build.annotations)
    for member_name, member in namespace.items():
        if member_name.startswith("_") or member_name in annotations:
            continue
        if isinstance(member, functools.cached_property) and model_base.kind == "pydantic-v1":
            msg = (
                f"{prefix}{build.schema_name}.{member_name} is a cached_property, which a Pydantic v1 model cannot"
                f" hold. Use a property, or decorate {build.schema_name} with @dataclass to keep it a dataclass."
            )
            raise TypeError(msg)
        # Anything but a method or property is a class member, not an input:
        # Pydantic v1 would make it a field, and v2 would refuse it.
        if not _is_method(member):
            annotations[member_name] = ClassVar[Any]
    for field_name in build.annotations:
        default = _field_default(build, field_name)
        if isinstance(default, Field):
            namespace[field_name] = _pydantic_field(build, model_base, field_name, default)
        elif default is not MISSING:
            namespace[field_name] = default
    namespace.update(
        {
            "__annotations__": annotations,
            "__module__": build.module,
            "__qualname__": build.qualname,
        }
    )
    # Pydantic v2 reads names from the frame that creates the class, which is
    # Citry's here; the annotations are already resolved where they were written.
    keywords = {"__pydantic_reset_parent_namespace__": False} if model_base.kind == "pydantic-v2" else {}
    try:
        model = new_class(
            build.class_name, (model_base.base,), keywords, exec_body=lambda attrs: attrs.update(namespace)
        )
    except Exception as error:
        raise _model_build_error(build, model_base, error) from error
    type.__setattr__(model, "__qualname__", build.qualname)
    return model


def _is_method(member: object) -> bool:
    """Whether a copied member is one Pydantic keeps as behaviour: a function, method wrapper, or property."""
    return isinstance(member, (FunctionType, staticmethod, classmethod, property, functools.cached_property))


def _model_build_error(build: BuildInput, model_base: ModelBase, error: Exception) -> TypeError:
    """Name the field whose annotation Pydantic could not read, beside Pydantic's own message."""
    prefix = f"Component {build.component_name}: " if build.component_name else ""
    field_name = next((name for name in build.annotations if _field_fails(build, model_base, name)), None)
    field = f" field {field_name!r}" if field_name is not None else ""
    advice = (
        f" Use a type Pydantic can validate for{field}, allow it with `arbitrary_types_allowed=True` in the base's"
        f" model_config, or decorate {build.schema_name} with @dataclass to keep it a dataclass."
        if field_name is not None
        else f" Decorate {build.schema_name} with @dataclass to keep it a dataclass."
    )
    return TypeError(
        f"{prefix}could not generate {model_base.label} for {build.schema_name}{field}"
        f" (model_base is {_describe(model_base.base)}).{advice}\nPydantic said: {error}"
    )


def _field_fails(build: BuildInput, model_base: ModelBase, field_name: str) -> bool:
    """Whether a model holding only this one field also fails to build."""
    namespace = {
        "__annotations__": {field_name: build.annotations[field_name]},
        "__module__": build.module,
    }
    keywords = {"__pydantic_reset_parent_namespace__": False} if model_base.kind == "pydantic-v2" else {}
    try:
        new_class(build.class_name, (model_base.base,), keywords, exec_body=lambda attrs: attrs.update(namespace))
    except Exception:  # noqa: BLE001 - any failure points at this field
        return True
    return False


def build_named_tuple(build: BuildInput, plain_default: Callable[[object], object]) -> tuple[type, dict[str, Any]]:
    """
    Generate one named tuple class from a plain declaration.

    It is one class, not a subclass: Citry's input check and its ``Const``
    handling look for the named tuple's generated ``__new__`` in the class's
    own namespace. Returns the class and the ``Const`` defaults Citry keeps
    beside it, which the caller stores.

    Raises:
        TypeError: A copied method calls ``super()``, a required field follows
            one with a default, or a field uses ``field(default_factory=...)``,
            none of which a named tuple can express.

    """
    from citry.constness import is_const  # noqa: PLC0415 - constness imports component modules

    members = _copied_members(build)
    field_names = list(build.field_names)
    prefix = f"Component {build.component_name}: " if build.component_name else ""
    defaults: list[object] = []
    const_defaults: dict[str, Any] = {}
    for field_name in field_names:
        default = _field_default(build, field_name)
        if isinstance(default, Field):
            # A named tuple stores defaults once, so a factory has no place.
            if default.default_factory is not MISSING or not default.init:
                msg = (
                    f"{prefix}{build.schema_name}.{field_name} uses field(default_factory=...) or field(init=False),"
                    " which a named tuple cannot express. Give it a plain default, or set model_base to another"
                    " kind."
                )
                raise TypeError(msg)
            default = default.default
        # Every instance shares a named tuple's default, so a list or dict
        # would carry values from one render to the next. This is the rule
        # `@dataclass` applies.
        if default is not MISSING and type(default).__hash__ is None:
            msg = (
                f"{prefix}{build.schema_name}.{field_name} has a {type(default).__name__} default, which every"
                " render would share in a named tuple. Use a tuple or a frozenset, or set model_base to another"
                " kind."
            )
            raise TypeError(msg)
        if default is MISSING:
            if defaults:
                msg = (
                    f"{prefix}{build.schema_name}.{field_name} has no default but follows a field with one, which"
                    " a named tuple cannot express. Give it a default, move it before the fields with defaults, or"
                    " set model_base to another kind."
                )
                raise TypeError(msg)
            continue
        if is_const(default):
            const_defaults[field_name] = plain_default(default)
        defaults.append(plain_default(default))
    # The names come from the declaration, so this is the functional form.
    make_named_tuple: Any = collections.namedtuple  # noqa: PYI024 - built at run time from the declaration
    try:
        named = make_named_tuple(build.class_name, field_names, defaults=defaults, module=build.module)
    except ValueError as error:
        # For example a field name that starts with an underscore.
        msg = f"{prefix}could not generate a named tuple for {build.schema_name}: {error}."
        raise TypeError(msg) from error
    type.__setattr__(named, "__qualname__", build.qualname)
    # Schema tools read the field types from the annotations, as they do for
    # an authored `typing.NamedTuple`. Python 3.14 keeps a class's assigned
    # annotations outside its namespace, so they also go on the generated
    # constructor, where `typing.NamedTuple` puts them.
    field_types = {name: build.annotations[name] for name in field_names}
    type.__setattr__(named, "__annotations__", field_types)
    named.__new__.__annotations__ = dict(field_types)
    # Methods, special methods such as `__str__`, and `ClassVar` values all
    # belong on the class; only the constructor stays the named tuple's own.
    for member_name, member in members.items():
        type.__setattr__(named, member_name, member)
    return named, const_defaults


def dataclass_options(model_base: ModelBase) -> dict[str, Any]:
    """
    Return the dataclass options the base sets, for each generated dataclass.

    ``slots`` is left out: generated classes are always slotted. Python 3.11
    does not record ``kw_only`` or ``match_args``, so on 3.11 those options
    have no effect.
    """
    params = _class_lookup(model_base.base, "__dataclass_params__")
    options: dict[str, Any] = {}
    for option in ("eq", "order", "unsafe_hash", "frozen", "repr", "match_args", "kw_only"):
        value = getattr(params, option, None)
        if isinstance(value, bool):
            options[option] = value
    return options


__all__ = [
    "BuildInput",
    "ModelBase",
    "build_named_tuple",
    "build_pydantic_model",
    "check_model_base",
    "dataclass_options",
    "resolve_model_base",
]
