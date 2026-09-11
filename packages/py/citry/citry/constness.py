"""
The ``Const`` optimization: skip re-computing template parts whose inputs
never change.

``Const(value)`` marks a component input as "this will be the same on every
render". The engine uses that promise to do work once instead of on every
render: the first render computes everything in the template that depends
only on ``Const`` values (an expression like ``{{ cols }}`` becomes plain
text, an ``<c-if>`` whose condition is decided keeps only the matching
branch), and the result is cached. Later renders with the same ``Const``
values reuse the cached result and skip all of that work.

How the pieces in this module fit together:

- ``Const`` is the call-site marker. Citry consumes it at component and data
  boundaries, passes the ordinary value to user code and template expressions,
  and records the promise separately by variable name. The private proxy is
  only transport; Python identity checks and APIs that require actual built-in
  values cannot be made transparent by an object proxy.
- ``extract_const_vars`` looks at a component's template variables, picks out
  the ``Const``-marked ones, and builds a **cache key** from their names and
  values (``freeze_const`` turns each value into a stable, dict-key-safe
  form).
- ``ConstBodyCache`` is the cache: one pre-computed template per component
  class, combination of ``Const`` values, and visible variable-name set. It
  keeps a bounded number of entries (least recently used entries are dropped
  first) and lives on a ``Citry`` instance.
- ``precompute_const_parts`` does the **precomputing** (the name this module and
  docs/design/component_constness.md use for this step): it walks the compiled template
  once, replaces everything that depends only on ``Const`` values with its final
  text, and leaves the rest to render normally each time.

Guidance for using ``Const``:

- **It is a promise, not verified.** The engine takes the marker at face
  value. Mutating a value after marking it const produces stale output; that
  is the documented trade.
- **Values written in the template are const automatically.** A static
  attribute (``age="30"``, boolean ``compact=""``) or an expression attribute
  that uses no variables (``c-age="30"``, ``c-items="[1, 2]"``) on a
  component tag cannot change between renders, so the engine marks it without
  any opt-in.
- **Mark values that are stable across many renders** (layout constants,
  fixed labels, configuration). Marking a value that differs on every render
  (``Const(user.id)``) defeats the purpose: each distinct value computes and
  caches its own copy, so nothing is ever reused.
- **Slot content is never const.** A component with slot fills still benefits
  from const kwargs, but the fills themselves re-render normally.
- **Defaults:** to make a default constant, mark it explicitly in the typed
  ``Kwargs``: ``cols: int = Const(3)``. When the kwarg is omitted, the marked
  default is used and optimized; when passed, the live value renders as
  usual.
- **The default mapping preserves the promise.** When a component uses the
  base ``template_data``, Citry knows that each kwarg keeps its name and carries
  its input provenance into the template and through child-component bindings.
- **Custom data callbacks retain direct forwarding.** A marked input keeps its
  promise when the callback's final output has the same name and is the same
  object. Mark renamed or replaced stable results explicitly, for example
  ``return {"title": Const(kwargs.title.upper())}``.
- **An outer marker owns its exact builtin value graph.** At a boundary, an
  outer ``Const`` marker triggers recursive removal of nested markers in exact
  builtin containers, with aliases and mutable cycles preserved. Boundary
  normalization leaves ordinary containers untouched, even if a caller
  manually placed ``Const`` inside one. Citry does not inspect arbitrary object
  attributes. A marked graph that requires rebuilding a cyclic tuple or
  frozenset raises ``ValueError`` rather than publishing a corrupt graph.
- **Custom schemas validate plain inputs.** Their outputs recover an input
  promise only when the final same-name object identity survives, or establish
  one with an explicit ``Const`` marker.

Example:
    Mark an input constant::

        from citry import Component, Const

        class Card(Component):
            template = '''
                <p>{{ cols }}</p>
            '''

        Card(cols=Const(3)).render()

"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable, Mapping
from contextvars import ContextVar
from dataclasses import MISSING, fields, is_dataclass
from functools import lru_cache
from inspect import signature
from threading import RLock
from typing import TYPE_CHECKING, Any, Final, TypeAlias, TypeVar, cast
from weakref import ref

import wrapt
from typing_extensions import Self

from citry.citry_element import CitryElement
from citry.component_like import ComponentLike
from citry.slots import Slot
from citry.util.html import escape

if TYPE_CHECKING:
    from collections.abc import Callable, Collection
    from weakref import ReferenceType

    from citry.citry_context import CitryContext
    from citry.component import Component
    from citry.nodes import BodyItem, ElementAttrsNode, ElementKeyNode, ExprNode, FillNode, ForNode, IfNode

_T = TypeVar("_T")
_schema_factory_consts: ContextVar[dict[str, Any] | None] = ContextVar(
    "citry_schema_factory_consts",
    default=None,
)


# #########################################################
# THE CONST MARKER
# #########################################################


class _ConstProxy(wrapt.ObjectProxy):
    """
    Transport marker for a value promised constant across renders.

    Common operations delegate to the wrapped value, but Python does not let
    a proxy preserve identity or satisfy every API that requires an actual
    built-in value. Citry therefore removes an exact outer marker before
    component callbacks and expressions execute, recursively cleaning its
    exact builtin value graph. It does not search ordinary containers for a
    manually nested marker.
    Use it through the public ``Const`` name; detect an unconsumed marker with
    ``is_const(x)``.
    """

    # The memoized cache key, set by ``freeze_const`` on first use. The
    # ``_self_`` prefix is wrapt's convention for an attribute that lives on
    # the proxy itself instead of the wrapped value.
    _self_frozen: Any

    def __repr__(self) -> str:
        return repr(self.__wrapped__)


if TYPE_CHECKING:
    # To type checkers, Const(x) has x's type, so Card(cols=Const(3))
    # type-checks against `cols: int` and `cols: int = Const(3)` is a valid
    # typed default. At runtime Const is the proxy class below, so the value
    # still carries the marker. (Presenting the class itself would not work:
    # wrapt ships no type stubs, so the proxy base is `Any` to checkers, and
    # mypy does not honor a `__new__` returning a bare TypeVar.)
    def Const(wrapped: _T) -> _T: ...  # noqa: N802 (callable facade for the class below)

else:
    Const = _ConstProxy


def is_const(value: Any) -> bool:
    """Return ``True`` if ``value`` is marked ``Const``."""
    return isinstance(value, _ConstProxy)


def _is_const_marker(value: Any) -> bool:
    """Detect Citry's exact transport marker without consulting an opaque object's ``__class__``."""
    return type(value) is _ConstProxy


def _is_builtin_container(value: Any) -> bool:
    """Detect traversable exact builtins without invoking an opaque type's equality."""
    value_type = type(value)
    return (
        value_type is dict or value_type is list or value_type is tuple or value_type is set or value_type is frozenset
    )


def const_value(value: Any) -> Any:
    """Unwrap outer marker layers; leave plain values unchanged and reject marker cycles."""
    # Forwarding a constant through another constant input can add a marker layer.
    # Exact-type consumers need the underlying value, regardless of that depth.
    if isinstance(value, _ConstProxy):
        value = value.__wrapped__
    if isinstance(value, _ConstProxy):
        # Allocate cycle tracking only for nested markers; the usual one-layer
        # case stays allocation-free. Proxy targets can be rebound by callers.
        seen: set[int] = set()
        while isinstance(value, _ConstProxy):
            marker_id = id(value)
            if marker_id in seen:
                msg = "Const markers contain a cycle."
                raise ValueError(msg)
            seen.add(marker_id)
            value = value.__wrapped__
    return value


class _ConstGraphScanner:
    """Find markers in exact builtin containers without following opaque objects."""

    def __init__(self) -> None:
        self._nodes: dict[int, Any] = {}
        self._reverse: dict[int, set[int]] = {}
        self._direct: set[int] = set()
        self._reachable: set[int] = set()
        self._dirty = False

    def contains_marker(self, value: Any) -> bool:
        if _is_const_marker(value):
            return True
        if not _is_builtin_container(value):
            return False
        value_id = id(value)
        if value_id not in self._nodes:
            self._collect(value)
        if self._dirty:
            reachable = set(self._direct)
            pending = list(reachable)
            while pending:
                child_id = pending.pop()
                for parent_id in self._reverse.get(child_id, ()):
                    if parent_id not in reachable:
                        reachable.add(parent_id)
                        pending.append(parent_id)
            self._reachable = reachable
            self._dirty = False
        return value_id in self._reachable

    def _collect(self, root: Any) -> None:
        pending = [root]
        while pending:
            value = pending.pop()
            value_id = id(value)
            if value_id in self._nodes:
                continue
            self._nodes[value_id] = value
            children = value.items() if type(value) is dict else value
            flattened = (part for pair in children for part in pair) if type(value) is dict else children
            for child in flattened:
                if _is_const_marker(child):
                    self._direct.add(value_id)
                    continue
                if _is_builtin_container(child):
                    child_id = id(child)
                    self._reverse.setdefault(child_id, set()).add(value_id)
                    pending.append(child)
            self._dirty = True


class _ConstGraphConverter:
    """Remove markers while preserving converted aliases and mutable cycles."""

    def __init__(self, scanner: _ConstGraphScanner) -> None:
        self._scanner = scanner
        self._memo: dict[int, Any] = {}
        self._active_immutable: set[int] = set()

    def convert(self, value: Any) -> Any:
        marker_chain: set[int] = set()
        while _is_const_marker(value):
            marker_id = id(value)
            if marker_id in marker_chain:
                raise ValueError("Const markers contain a cycle.")
            marker_chain.add(marker_id)
            value = value.__wrapped__

        value_type = type(value)
        if not _is_builtin_container(value) or not self._scanner.contains_marker(value):
            return value

        value_id = id(value)
        if value_id in self._active_immutable:
            raise ValueError("Const markers require rebuilding a cyclic tuple or frozenset.")
        if value_id in self._memo:
            return self._memo[value_id]

        if value_type is list:
            converted_list: list[Any] = []
            self._memo[value_id] = converted_list
            converted_list.extend(self.convert(item) for item in value)
            return converted_list
        if value_type is dict:
            converted_dict: dict[Any, Any] = {}
            self._memo[value_id] = converted_dict
            converted_dict.update((self.convert(key), self.convert(item)) for key, item in value.items())
            return converted_dict
        if value_type is set:
            converted_set: set[Any] = set()
            self._memo[value_id] = converted_set
            converted_set.update(self.convert(item) for item in value)
            return converted_set

        self._active_immutable.add(value_id)
        try:
            converted_items = tuple(self.convert(item) for item in value)
            converted: Any = converted_items if value_type is tuple else frozenset(converted_items)
        finally:
            self._active_immutable.remove(value_id)
        self._memo[value_id] = converted
        return converted


def _unwrap_const_graph(values: Iterable[Any]) -> list[Any]:
    """Recursively unwrap exact marked roots together, leaving ordinary roots untouched."""
    roots = list(values)
    marked_indexes: list[int] = []
    marked_roots: list[Any] = []
    for index, value in enumerate(roots):
        if not _is_const_marker(value):
            continue
        root = value
        first_marker_id = id(root)
        root = root.__wrapped__
        if type(root) is _ConstProxy:
            marker_chain = {first_marker_id}
            while type(root) is _ConstProxy:
                marker_id = id(root)
                if marker_id in marker_chain:
                    raise ValueError("Const markers contain a cycle.")
                marker_chain.add(marker_id)
                root = root.__wrapped__
        marked_indexes.append(index)
        marked_roots.append(root)

    if not marked_indexes:
        return roots
    if not any(_is_builtin_container(root) for root in marked_roots):
        for index, root in zip(marked_indexes, marked_roots, strict=True):
            roots[index] = root
        return roots

    scanner = _ConstGraphScanner()
    # Only an explicitly marked outer root owns recursive conversion. Build
    # one graph for all such roots so their aliases and mutable cycles survive.
    for root in marked_roots:
        if _is_builtin_container(root):
            scanner.contains_marker(root)
    converter = _ConstGraphConverter(scanner)
    for index, root in zip(marked_indexes, marked_roots, strict=True):
        roots[index] = converter.convert(root)
    return roots


def _plain_schema_default(value: Any) -> Any:
    """Remove markers from one renderer-owned schema default before construction."""
    return _unwrap_const_graph((value,))[0]


def _schema_default_factory(name: str, factory: Callable[[], Any]) -> Callable[[], Any]:
    """Wrap a generated-schema factory so post-init code receives an ordinary value."""

    def make_default() -> Any:
        value = factory()
        plain = _plain_schema_default(value)
        collected = _schema_factory_consts.get()
        if collected is not None and _is_const_marker(value):
            collected[name] = plain
        return plain

    return make_default


class _ConstMapping(dict[str, Any]):
    """Private plain-value mapping with const provenance stored beside its entries."""

    __slots__ = ("_const_values",)

    def __init__(
        self,
        values: Mapping[str, Any] | Iterable[tuple[str, Any]] = (),
        *,
        const_values: Mapping[str, Any] | None = None,
    ) -> None:
        dict.__init__(self)
        self._const_values: dict[str, Any] = {}
        if type(values) is tuple and not values:
            return
        if type(values) is dict or type(values) is _ConstMapping:
            if not values:
                return
            source = cast("dict[str, Any]", values)
            dict.update(self, source)
            marked: list[tuple[str, Any]] | None = None
            for name, value in dict.items(source):
                if _is_const_marker(value):
                    if marked is None:
                        marked = []
                    marked.append((name, value))
            if const_values is not None:
                self._const_values.update((name, self[name]) for name in const_values if dict.__contains__(self, name))
            if marked is not None:
                plain_marked_roots = _unwrap_const_graph(value for _, value in marked)
                for (name, _original), plain in zip(marked, plain_marked_roots, strict=True):
                    dict.__setitem__(self, name, plain)
                    self._const_values[name] = plain
            return
        if isinstance(values, Mapping):
            if not values:
                return
            pairs = list(cast("Mapping[str, Any]", values).items())
        else:
            pairs = list(cast("Iterable[tuple[str, Any]]", values))
            if not pairs:
                return
        marked_values: list[Any] | None = None
        for _name, value in pairs:
            if _is_const_marker(value):
                if marked_values is None:
                    marked_values = []
                marked_values.append(value)
        if marked_values is None:
            dict.update(self, pairs)
            if const_values is not None:
                self._const_values.update((name, self[name]) for name, _ in pairs if name in const_values)
            return
        plain_marked_values = iter(_unwrap_const_graph(marked_values))
        for name, original in pairs:
            plain = next(plain_marked_values) if _is_const_marker(original) else original
            dict.__setitem__(self, name, plain)
            if _is_const_marker(original) or (const_values is not None and name in const_values):
                self._const_values[name] = plain
            else:
                self._const_values.pop(name, None)

    def __setitem__(self, name: str, value: Any) -> None:
        plain = _unwrap_const_graph((value,))[0] if _is_const_marker(value) else value
        dict.__setitem__(self, name, plain)
        if _is_const_marker(value):
            self._const_values[name] = plain
        else:
            self._const_values.pop(name, None)

    def __delitem__(self, name: str) -> None:
        dict.__delitem__(self, name)
        self._const_values.pop(name, None)

    def clear(self) -> None:
        dict.clear(self)
        self._const_values.clear()

    def copy(self) -> _ConstMapping:
        copied = dict.__new__(_ConstMapping)
        dict.__init__(copied, self)
        copied._const_values = dict(self._const_values)
        return copied

    def pop(self, name: str, *default: Any) -> Any:
        if len(default) > 1:
            raise TypeError(f"pop expected at most 2 arguments, got {len(default) + 1}")
        if name in self:
            self._const_values.pop(name, None)
        if default:
            return dict.pop(self, name, default[0])
        return dict.pop(self, name)

    def popitem(self) -> tuple[str, Any]:
        name, value = dict.popitem(self)
        self._const_values.pop(name, None)
        return name, value

    def setdefault(self, name: str, default: Any = None) -> Any:
        if name in self:
            return self[name]
        self[name] = default
        return self[name]

    def update(self, *args: Any, **kwargs: Any) -> None:
        if len(args) > 1:
            raise TypeError(f"update expected at most 1 argument, got {len(args)}")
        if args and not kwargs and (type(args[0]) is dict or type(args[0]) is _ConstMapping):
            source = cast("dict[str, Any]", args[0])
            if not source:
                return
            marked: list[tuple[str, Any]] | None = None
            for name, value in dict.items(source):
                if _is_const_marker(value):
                    if marked is None:
                        marked = []
                    marked.append((name, value))
            if marked is None:
                dict.update(self, source)
                if self._const_values:
                    for name in dict.keys(source):
                        self._const_values.pop(name, None)
                return
            snapshot_pairs = list(dict.items(source))
            plain_marked_roots = iter(_unwrap_const_graph(value for _, value in marked))
            for name, original in snapshot_pairs:
                plain = next(plain_marked_roots) if _is_const_marker(original) else original
                dict.__setitem__(self, name, plain)
                if _is_const_marker(original):
                    self._const_values[name] = plain
                else:
                    self._const_values.pop(name, None)
            return
        pairs: list[tuple[str, Any]] = []
        if args:
            source = args[0]
            pairs.extend(source.items() if hasattr(source, "keys") else source)
        pairs.extend(kwargs.items())
        marked_values: list[Any] | None = None
        for _name, value in pairs:
            if _is_const_marker(value):
                if marked_values is None:
                    marked_values = []
                marked_values.append(value)
        if marked_values is None:
            dict.update(self, pairs)
            if self._const_values:
                for name, _value in pairs:
                    self._const_values.pop(name, None)
            return
        plain_marked_values = iter(_unwrap_const_graph(marked_values))
        for name, original in pairs:
            plain = next(plain_marked_values) if _is_const_marker(original) else original
            dict.__setitem__(self, name, plain)
            if _is_const_marker(original):
                self._const_values[name] = plain
            else:
                self._const_values.pop(name, None)

    # Typeshed compares dict.__ior__ to the generic dict.__or__ overloads;
    # this private string-keyed subclass accepts the same runtime inputs.
    def __ior__(self, other: Any) -> Self:  # type: ignore[override,misc]
        self.update(other)
        return self


def _const_mapping(
    values: Mapping[str, Any] | Iterable[tuple[str, Any]],
    *,
    preserve: Mapping[str, Any] | None = None,
) -> _ConstMapping:
    """Build a plain-value mapping, optionally retaining trusted name provenance."""
    preserved = preserve._const_values if isinstance(preserve, _ConstMapping) else None
    return _ConstMapping(values, const_values=preserved)


def _refresh_const_mapping(values: _ConstMapping) -> None:
    """Consume exact root markers inserted through a mapping bypass."""
    if not values:
        return
    marked: list[tuple[str, Any]] | None = None
    for name, value in values.items():
        if _is_const_marker(value):
            if marked is None:
                marked = []
            marked.append((name, value))
    if marked is None:
        return
    converted = _unwrap_const_graph(value for _, value in marked)
    for (name, _original), plain in zip(marked, converted, strict=True):
        dict.__setitem__(values, name, plain)
        values._const_values[name] = plain


def _merge_const_mappings(*values: Mapping[str, Any]) -> _ConstMapping:
    """Merge renderer-owned mappings with rightmost values and provenance winning."""
    merged = _ConstMapping()
    for mapping in values:
        for name, value in mapping.items():
            dict.__setitem__(merged, name, value)
            if isinstance(mapping, _ConstMapping) and name in mapping._const_values:
                merged._const_values[name] = value
            else:
                merged._const_values.pop(name, None)
    # Every input was normalized at its external boundary. This renderer-owned
    # merge neither calls user code nor introduces new values.
    return merged


def _overlay_const_mapping(values: Mapping[str, Any], overlay: Mapping[str, Any]) -> _ConstMapping:
    """Copy trusted variables and add new dynamic bindings from a renderer scope."""
    if type(values) is _ConstMapping and (type(overlay) is dict or type(overlay) is _ConstMapping):
        source = cast("dict[str, Any]", overlay)
        if not any(_is_const_marker(value) for value in dict.values(source)):
            merged = values.copy()
            dict.update(merged, source)
            if merged._const_values:
                for name in dict.keys(source):
                    merged._const_values.pop(name, None)
            return merged
    # Marked roots can run arbitrary key hashing while their containers are
    # rebuilt. Normalize them before snapshotting the surrounding scope.
    dynamic_overlay = _const_mapping(overlay)
    dynamic_overlay._const_values.clear()
    return _merge_const_mappings(values, dynamic_overlay)


def _mapping_value_is_const(values: Mapping[str, Any], name: str) -> bool:
    """Return whether one named mapping entry has separately tracked provenance."""
    return isinstance(values, _ConstMapping) and name in values._const_values


def _restore_const_identities(values: _ConstMapping, candidates: Mapping[str, Any]) -> None:
    """Restore same-name provenance when a final value is the marked input object."""
    for name, original in candidates.items():
        if name in values and values[name] is original:
            values._const_values[name] = values[name]


# Schema classes can be defined inside request or test scopes, so bound these
# hot-path predicates rather than retaining every class for the process life.
@lru_cache(maxsize=256)
def _schema_is_inert_dataclass(schema: type) -> bool:
    """Whether Citry knows that named constructor inputs remain the same fields."""
    if not is_dataclass(schema) or schema.__dict__.get("_citry_synthesized_declaration") is not True:
        return False
    init = getattr(schema, "__init__", None)
    code = getattr(init, "__code__", None)
    if code is None or code.co_filename != "<string>":
        return False
    if any("__post_init__" in base.__dict__ for base in schema.__mro__):
        return False
    if schema.__new__ is not object.__new__ or schema.__getattribute__ is not object.__getattribute__:
        return False
    params = getattr(schema, "__dataclass_params__", None)
    return schema.__setattr__ is object.__setattr__ or getattr(params, "frozen", False)


@lru_cache(maxsize=256)
def _schema_is_inert_namedtuple(schema: type) -> bool:
    """Whether ``schema`` is the standard immutable named-tuple adapter."""
    if not issubclass(schema, tuple) or not isinstance(getattr(schema, "_fields", None), tuple):
        return False
    constructor = schema.__dict__.get("__new__")
    code = getattr(constructor, "__code__", None)
    return (
        code is not None
        and code.co_filename == "<string>"
        and code.co_name == "<lambda>"
        and schema.__getattribute__ is tuple.__getattribute__
    )


def _schema_has_generated_dataclass_init(schema: type) -> bool:
    """Whether dataclasses generated this schema's keyword constructor."""
    constructor = schema.__dict__.get("__init__")
    code = getattr(constructor, "__code__", None)
    return code is not None and code.co_filename == "<string>"


def _is_classvar_field(field: Any) -> bool:
    """Whether one private dataclass field record represents a ClassVar."""
    return getattr(getattr(field, "_field_type", None), "name", None) == "_FIELD_CLASSVAR"


def _add_schema_defaults(
    constructor_values: _ConstMapping,
    schema: type,
    dataclass_fields: dict[str, Any],
) -> _ConstMapping:
    """Materialize defaults whose generated dataclass constructor is safe to emulate."""
    missing_fields = [
        field
        for field in dataclass_fields.values()
        if field.init and not _is_classvar_field(field) and field.name not in constructor_values
    ]
    if any(field.default_factory is not MISSING for field in missing_fields):
        # Reject missing/unknown arguments before evaluating a factory that
        # the generated constructor would otherwise never reach.
        signature(schema).bind(**constructor_values)

    default_pairs: list[tuple[str, Any]] = []
    for field in missing_fields:
        if field.default is not MISSING:
            default_pairs.append((field.name, field.default))
        elif field.default_factory is not MISSING:
            default_pairs.append((field.name, field.default_factory()))
    if not default_pairs:
        return constructor_values
    with_defaults = constructor_values.copy()
    with_defaults.update(default_pairs)
    return with_defaults


def _add_marked_model_defaults(constructor_values: _ConstMapping, schema: type) -> _ConstMapping:
    """Pass declared Pydantic marker defaults as plain values into validation."""
    model_fields = getattr(schema, "model_fields", None)
    if not isinstance(model_fields, dict):
        model_fields = getattr(schema, "__fields__", None)
    if not isinstance(model_fields, dict):
        return constructor_values

    default_pairs: list[tuple[str, Any]] = []
    for name, field in model_fields.items():
        if name in constructor_values:
            continue
        default = getattr(field, "default", MISSING)
        if default is MISSING:
            continue
        if _is_const_marker(default):
            default_pairs.append((name, default))
    if not default_pairs:
        return constructor_values
    with_defaults = constructor_values.copy()
    with_defaults.update(default_pairs)
    return with_defaults


def _construct_data_schema(
    values: Mapping[str, Any],
    schema: type | None,
    *,
    provenance_only: bool = False,
) -> tuple[Any, _ConstMapping]:
    """
    Construct one data schema from plain inputs and return its named metadata view.

    With ``provenance_only``, a proven inert schema may return constructor
    provenance without rebuilding the actual field mapping; the base data
    callback snapshots those fields later. Other callers receive the schema's
    normalized, authoritative named output.
    """
    normalized = values if isinstance(values, _ConstMapping) else _const_mapping(values)
    if schema is None:
        return normalized, normalized

    # Schema constructors receive ``**`` values and cannot mutate the mapping,
    # so keep the normalized mapping until adding an omitted default requires
    # a renderer-owned copy.
    constructor_values = normalized
    dataclass_fields = getattr(schema, "__dataclass_fields__", None)
    schema_namedtuple_fields = getattr(schema, "_fields", None)
    if isinstance(dataclass_fields, dict):
        generated_init = _schema_has_generated_dataclass_init(schema)
        if generated_init:
            constructor_values = _add_schema_defaults(constructor_values, schema, dataclass_fields)
            if schema.__dict__.get("_citry_synthesized_declaration") is not True:
                marked_read_only_default = next(
                    (
                        field
                        for field in dataclass_fields.values()
                        if not field.init and not _is_classvar_field(field) and _is_const_marker(field.default)
                    ),
                    None,
                )
                if marked_read_only_default is not None:
                    msg = (
                        f"Schema {schema.__qualname__}.{marked_read_only_default.name} uses Const as an init=False "
                        "default; use a plain default or a Citry-generated input declaration."
                    )
                    raise TypeError(msg)
        else:
            marked_field = next(
                (
                    field
                    for field in dataclass_fields.values()
                    if not _is_classvar_field(field) and _is_const_marker(field.default)
                ),
                None,
            )
            if marked_field is not None:
                msg = (
                    f"Schema {schema.__qualname__}.{marked_field.name} uses Const as a default with a custom "
                    "constructor; pass an ordinary default or use a generated dataclass constructor."
                )
                raise TypeError(msg)

    elif issubclass(schema, tuple) and isinstance(schema_namedtuple_fields, tuple):
        namedtuple_fields = cast("tuple[str, ...]", schema_namedtuple_fields)
        namedtuple_defaults = getattr(schema, "_field_defaults", {})
        default_pairs = [
            (name, namedtuple_defaults[name])
            for name in namedtuple_fields
            if name not in constructor_values and name in namedtuple_defaults
        ]
        if default_pairs:
            constructor_values = constructor_values.copy()
            constructor_values.update(default_pairs)
    else:
        constructor_values = _add_marked_model_defaults(constructor_values, schema)

    factory_consts: dict[str, Any] = {}
    token = _schema_factory_consts.set(factory_consts)
    try:
        instance = schema(**constructor_values)
    finally:
        _schema_factory_consts.reset(token)

    inert_schema = _schema_is_inert_dataclass(schema) or _schema_is_inert_namedtuple(schema)
    if inert_schema and provenance_only:
        # This mapping transports provenance by field name. The base data
        # callback snapshots the instance's actual fields later, so it must
        # not use these constructor values as the rendered field view.
        output = constructor_values
    else:
        output = _normalize_data_schema_instance(
            instance,
            schema,
            preserve=constructor_values if inert_schema else None,
            require_plain_instance=True,
        )
    # A factory or custom schema may create a root marker itself. Remove that
    # wrapper from the typed field before any component callback can inspect it.
    if inert_schema:
        declared_consts = getattr(schema, "_citry_const_schema_defaults", ())
        if output is not constructor_values:
            for name in constructor_values._const_values:
                if name in output:
                    output._const_values[name] = output[name]
        if declared_consts or factory_consts:
            inert_namedtuple_fields = cast("tuple[str, ...]", getattr(schema, "_fields", ()))
            instance_field_names = (
                {field.name for field in fields(schema)} if is_dataclass(schema) else set(inert_namedtuple_fields)
            )
            for name in (*declared_consts, *factory_consts):
                if name in instance_field_names and name not in normalized:
                    value = getattr(instance, name)
                    if name not in output:
                        dict.__setitem__(output, name, value)
                    output._const_values[name] = value
    custom_namedtuple_fields = cast("tuple[str, ...] | None", getattr(schema, "_fields", None))
    if (
        not inert_schema
        and issubclass(schema, tuple)
        and custom_namedtuple_fields is not None
        and any(_is_const_marker(getattr(instance, name)) for name in custom_namedtuple_fields)
    ):
        # A custom NamedTuple constructor may have inserted markers. Bypass
        # that constructor once to publish the same schema type with the
        # already-normalized field values before component callbacks run.
        rebuilt = tuple.__new__(schema, tuple(output[name] for name in custom_namedtuple_fields))
        source_attrs = getattr(instance, "__dict__", None)
        rebuilt_attrs = getattr(rebuilt, "__dict__", None)
        if isinstance(source_attrs, dict) and isinstance(rebuilt_attrs, dict):
            rebuilt_attrs.update(source_attrs)
        instance = rebuilt
    return instance, output


def _normalize_data_schema_instance(
    instance: Any,
    schema: type,
    *,
    preserve: _ConstMapping | None = None,
    require_plain_instance: bool = False,
) -> _ConstMapping:
    """
    Return a named view with each exact root marker consumed.

    ``require_plain_instance`` also guarantees that subsequent component code
    can read a plain value from each root-marked field on the instance itself.
    A read-only field created by arbitrary schema code cannot be repaired
    without inspecting private state, so that unsupported shape raises
    ``TypeError``. Ordinary containers are not searched for nested markers.
    """
    from citry.util.misc import to_dict  # noqa: PLC0415 - avoids the module initialization cycle

    named_values = to_dict(instance)
    marked_names = {name for name, value in named_values.items() if _is_const_marker(value)}
    output = _const_mapping(
        named_values,
        preserve=preserve if _schema_is_inert_dataclass(schema) or _schema_is_inert_namedtuple(schema) else None,
    )
    namedtuple_instance = isinstance(instance, tuple) and isinstance(getattr(type(instance), "_fields", None), tuple)
    for name in marked_names:
        try:
            object.__setattr__(instance, name, output[name])
        except (AttributeError, TypeError) as error:
            if require_plain_instance and not namedtuple_instance:
                msg = (
                    f"Schema {schema.__qualname__}.{name} produced a Const value in a read-only field; "
                    "return an ordinary value from the schema instead."
                )
                raise TypeError(msg) from error
    return output


# #########################################################
# THE CONST SIGNATURE (cache key)
# #########################################################


ConstSignature: TypeAlias = "frozenset[tuple[str, Any]]"
"""
The cache key built from a render's ``Const`` variables: the set of
``(variable name, frozen value)`` pairs. Two renders with the same const
names and values get the same key (and so share one cache entry); a
different name set or different values gives a different key.
"""

_UNFREEZABLE: Final = object()
"""Returned by ``freeze_const`` for a value that cannot become a reliable cache key."""


def freeze_const(value: Any) -> Any:
    """
    Turn ``value`` into a form that can be part of the cache key.

    A cache key must work as a dictionary key (hashable) and must behave by
    VALUE: two equal values must produce the same key (so a repeat render
    finds the cached entry), and two values that would render differently
    must produce different keys (so a cached result is never reused for the
    wrong value). The rules, per ``docs/design/component_constness.md`` section 7.2:

    - Plain containers (``list``, ``tuple``, ``dict``, ``set``, ``frozenset``)
      are converted element by element into a hashable equivalent, tagged
      with the container kind so for example a list and a tuple of the same
      items do not collide.
    - Any other hashable value is kept as-is, paired with its exact type.
      The type matters because values that compare equal can still render
      differently: ``True == 1`` but they render as ``"True"`` and ``"1"``.
    - Anything else (an unhashable non-container) returns ``_UNFREEZABLE``:
      the variable is then treated as if it were never marked, and renders
      normally, rather than risk a wrong or unstable key.

    ``Const`` wrappers are unwrapped at every level, so a marker nested inside
    a container does not leak the wrapper type into the key.

    The frozen form is computed once per marker and stored on it for reuse
    (the same marker object usually flows through every render of a usage,
    and ``Const`` is a promise the value does not change, so freezing once is
    part of the contract). The ``_self_`` prefix is wrapt's convention for
    storing an attribute on the wrapper itself instead of the wrapped value.
    """
    if _is_const_marker(value):
        try:
            return value._self_frozen
        except AttributeError:
            pass
        frozen = _freeze_plain(value)
        if frozen is not _UNFREEZABLE:
            value._self_frozen = frozen
        return frozen
    return _freeze_plain(value)


def _freeze_plain(value: Any) -> Any:
    """The uncached freeze. Containers recurse through ``freeze_const``."""
    while _is_const_marker(value):
        value = value.__wrapped__
    if isinstance(value, dict):
        pairs = tuple((freeze_const(k), freeze_const(v)) for k, v in value.items())
        if any(k is _UNFREEZABLE or v is _UNFREEZABLE for k, v in pairs):
            return _UNFREEZABLE
        return ("dict", frozenset(pairs))
    if isinstance(value, (list, tuple)):
        items = tuple(freeze_const(item) for item in value)
        if any(item is _UNFREEZABLE for item in items):
            return _UNFREEZABLE
        return ("tuple" if isinstance(value, tuple) else "list", items)
    if isinstance(value, (set, frozenset)):
        members = frozenset(freeze_const(item) for item in value)
        if any(member is _UNFREEZABLE for member in members):
            return _UNFREEZABLE
        return ("set", members)
    try:
        hash(value)
    except TypeError:
        return _UNFREEZABLE
    return (type(value), value)


def extract_const_vars(
    variables: Mapping[str, Any],
    used_vars: Collection[str] | None = None,
) -> tuple[dict[str, Any], ConstSignature]:
    """
    Pick out the ``Const``-marked template variables and build the cache key.

    Returns ``(const_vars, signature)``:

    - ``const_vars``: name -> ordinary value for every
      variable that is marked const AND could be turned into a cache key.
      ``precompute_const_parts`` evaluates against this mapping when it pre-computes the
      constant parts of the template.
    - ``signature``: the cache key over those same variables (see
      ``ConstSignature``).

    A ``Const`` value that cannot become a cache key (see ``freeze_const``)
    is left out of BOTH, so the cache key and the pre-computing step always
    agree on which variables count as const; the variable simply renders
    normally on every render.

    ``used_vars``, when given, is the set of variables the template actually
    uses; const variables outside it are left out the same way. They cannot
    affect the output, so keying on them would only create duplicate cache
    entries. The renderer retains their separate name provenance for child
    component bindings. Leaving a variable out is always safe: it just renders
    normally.
    """
    const_vars: dict[str, Any] = {}
    items: list[tuple[str, Any]] = []
    for name, value in variables.items():
        marked = isinstance(variables, _ConstMapping) and name in variables._const_values
        if not marked and not _is_const_marker(value):
            continue
        if used_vars is not None and name not in used_vars:
            continue
        plain = _unwrap_const_graph((value,))[0] if _is_const_marker(value) else value
        frozen = freeze_const(plain)
        if frozen is _UNFREEZABLE:
            continue
        const_vars[name] = plain
        items.append((name, frozen))
    return const_vars, frozenset(items)


# #########################################################
# THE BODY CACHE
# #########################################################


DEFAULT_MAX_ENTRIES: Final = 512
"""
How many entries the cache holds before it starts dropping old ones. One
entry is one (component class, combination of Const values); ordinary apps
use one entry per component class plus a few per const usage, so the default
leaves ample headroom while still capping misuse (see the ``ConstBodyCache``
docstring).
"""

_CacheKey: TypeAlias = "tuple[ReferenceType[type[Component]], ConstSignature, frozenset[str]]"


class ConstBodyCache:
    """
    The cache of pre-computed template bodies, one per set of ``Const`` values.

    A "body" is what a template compiles to: a list of static strings and
    node objects. The entry stored for a render that had ``Const`` inputs has
    been through ``precompute_const_parts``, so the parts depending on those inputs are
    already computed; the entry for a render with no ``Const`` inputs is the
    plain compiled body that all such renders share. Keys are
    ``(weak component-class reference, ConstSignature, visible variable
    names)``. The weak reference lets an unregistered component class be
    collected without waiting for this cache's LRU limit. Variable names
    participate because Citry binders reject an already-visible name; two
    otherwise equal renders with different context shapes may therefore need
    different optimized bodies.

    The cache lives on a ``Citry`` instance (``Citry._const_body_cache``), but
    holds each component class weakly. A class can therefore be collected
    after its final registry alias and the caller's references are gone;
    calling ``Citry.clear()`` releases every entry immediately. The cache
    holds at most ``max_entries`` entries and drops the least recently used
    one when full; that way, marking ever-changing values ``Const`` (a
    mistake, but possible) wastes some work instead of growing memory without
    limit.

    A single lock guards lookups and builds, so when two threads render the
    same new combination at once, it is computed once. The lock is re-entrant
    (the same thread may re-enter it) because building evaluates user
    expressions, which may render nested content and consult this cache
    again.
    """

    def __init__(self, max_entries: int = DEFAULT_MAX_ENTRIES) -> None:
        self._max_entries = max_entries
        self._lock = RLock()
        # The pre-computed body for each (component class, Const values): the
        # template's list of static strings and nodes after the parts that
        # depend only on constant inputs have been computed (see precompute_const_parts).
        self._entries: OrderedDict[_CacheKey, list[BodyItem]] = OrderedDict()
        self._has_collected_components = False

    def _component_collected(self, _component_ref: object) -> None:
        """Flag dead class keys without releasing cached bodies from a GC callback."""
        self._has_collected_components = True

    def get_or_build(
        self,
        comp_cls: type[Component],
        signature: ConstSignature,
        build: Callable[[], list[BodyItem]],
        *,
        visible_names: Collection[str] = (),
    ) -> list[BodyItem]:
        """
        Return the cached body for this const signature and visible-name set.

        On a hit the entry is marked most-recently-used. On a miss ``build()``
        runs under the lock and the result is stored; if it raises, nothing is
        cached and the error propagates (so the next render retries).
        """
        key = (ref(comp_cls), signature, frozenset(visible_names))
        with self._lock:
            self._prune_collected_components()
            body = self._entries.get(key)
            if body is not None:
                self._entries.move_to_end(key)
                return body
            body = build()
            stored_key = (ref(comp_cls, self._component_collected), signature, key[2])
            self._entries[stored_key] = body
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)
            return body

    def evict_component(self, comp_cls: type[Component]) -> None:
        """Drop every entry of one component class during reset or final unregistration."""
        with self._lock:
            self._prune_collected_components()
            stale = [key for key in self._entries if key[0]() is comp_cls]
            for key in stale:
                self._entries.pop(key, None)

    def _prune_collected_components(self) -> None:
        """Drop dead weak-reference entries during an ordinary cache operation."""
        if not self._has_collected_components:
            return
        # Clear before scanning. A class collected during the scan sets the
        # flag again so the next ordinary operation handles that later key.
        self._has_collected_components = False
        stale = [key for key in self._entries if key[0]() is None]
        for key in stale:
            self._entries.pop(key, None)

    def clear(self) -> None:
        """Drop all entries."""
        with self._lock:
            self._entries.clear()
            self._has_collected_components = False

    def values(self) -> list[list[BodyItem]]:
        """A snapshot of the cached bodies (mainly for tests and debugging)."""
        with self._lock:
            self._prune_collected_components()
            return list(self._entries.values())

    def __len__(self) -> int:
        with self._lock:
            self._prune_collected_components()
            return len(self._entries)

    def __repr__(self) -> str:
        return f"ConstBodyCache(entries={len(self._entries)}, max_entries={self._max_entries})"


# #########################################################
# PRECOMPUTING (the pre-computing step)
# #########################################################

# NOTE: Precomputing needs the runtime node classes and CitryRender for its
# isinstance checks, but citry_render imports this module (for const_value)
# and citry.nodes imports citry_render, so importing either at the top here
# would be circular. They are imported inside the precomputing functions instead;
# precomputing runs once per cache entry, so the cost is a few dictionary lookups
# per cache miss.


_MAX_UNROLL_ITERATIONS: Final = 1000
"""
The most loop iterations precomputing will run ahead of time (see
``_try_unroll_for``). The pre-computed text is exactly what every render
would produce anyway, so output size is not the concern; the cap guards
against huge or never-ending const iterables. Past it, the loop just renders
normally each time.
"""


def precompute_const_parts(
    body: list[BodyItem],
    const_vars: dict[str, Any],
    *,
    precompute_attrs: bool = True,
    sandboxed: bool = True,
    visible_names: Collection[str] | None = None,
) -> list[BodyItem]:
    """
    Pre-compute the parts of ``body`` that depend only on ``const_vars``.

    This is the step this module calls **precomputing**: given a compiled template
    (``body``, a list of static strings and node objects) and the variables
    promised to be constant (``const_vars``), do the work that depends only
    on those variables right now, once, and return a new body where that work
    is already done. The result goes into ``ConstBodyCache``, so every later
    render with the same const values reuses it. What gets pre-computed:

    - A ``{{ expr }}`` node whose variables are all const is evaluated once
      and replaced with its escaped text.
    - An HTML element's dynamic attribute region (``ElementAttrsNode``) whose
      variables are all const is rendered once and replaced with its text.
      Pass ``precompute_attrs=False`` to keep these regions live: the caller does
      that when an installed extension implements ``on_attrs_resolved``,
      because baking the region would hide it from the extension. A region
      holding a nested-template attribute value also stays live (it renders
      fresh parts each time).
    - An element ``#c-key`` whose variables are all const is evaluated once.
      This remains safe even when ordinary attribute precomputation is off,
      because framework metadata never enters ``on_attrs_resolved``.
    - A ``<c-if>`` whose branch conditions use only const variables is
      decided once: only the matching branch's content remains (itself
      precomputed), the other branches are dropped.
    - A ``<c-if>`` whose conditions use non-const variables is kept (it must
      be decided on every render), but constant expressions INSIDE its
      branches still precompute.
    - A ``<c-for>`` over a const iterable whose body precomputes entirely to text
      is run once here, and the per-iteration text is baked in (within one
      iteration, the loop variables count as const). Capped at
      ``_MAX_UNROLL_ITERATIONS``.
    - A ``<c-for>`` that cannot be pre-run is kept, but constant expressions
      inside its body still precompute: an expression that does not touch the loop
      variables produces the same text on every iteration. The loop branch
      masks its introduced variables while the ``<c-empty>`` branch keeps the
      surrounding scope.
    - Static strings that end up next to each other are joined.

    Everything else stays in place as a normal node and re-evaluates on every
    render. That matters because the precomputed body is SHARED by every render
    with the same const values, while their other (non-const) variables
    differ, so anything not pre-computed must still work for all of them.

    What is never pre-computed, and why (docs/design/component_constness.md sections
    5, 9, 10):

    - ``ComponentNode`` (a child component tag): every render of a child gets
      a fresh component instance and a fresh render id, and its slot content
      captures the surrounding render's state. Its BODY does precompute, though:
      fill bodies and the implicit default-slot body render against this
      component's variables, so const expressions inside slot content are
      pre-computed even while the tag itself stays.
    - ``SlotNode``: which fill it renders comes from the live component
      instance, which changes per render even when the tag itself uses no
      template variables. It also fires the ``on_slot_rendered`` hook. Its
      fallback body precomputes in place, same as a fill body.
    - ``FillNode``: stays (it is consumed when fills are collected, each
      render), but its body precomputes in place.
    - An expression whose VALUE is a ``Slot``, ``CitryElement``, or
      ``CitryRender``: rendering those produces per-render state (render
      ids, collected dependencies), so only values that become plain text
      may be baked in.
    - Node types this step does not know (an extension may inject custom
      nodes via ``on_template_compiled``): kept as-is, to be safe.

    **Precomputing never raises.** A const expression or condition that fails here
    is kept as a normal node, so the error (if any) surfaces during a render,
    through the normal path, exactly as it would without the optimization.
    The trade-off of precomputing inside kept ``<c-if>`` branches is WHEN a const
    expression runs: it is evaluated once here even if the branch it sits in
    is not taken by this particular render (a later render sharing the cache
    entry may take it). Citry expressions are expected to have no side effects
    (the sandbox enforces it by default), so running one early should not be
    observable.

    One sharp edge of pre-running loops: a one-shot iterable (a generator)
    marked const is consumed by the attempt. If the attempt then has to back
    out (a value deep in the body turns out to be a ``Slot``/element), the
    kept loop node re-iterates the exhausted generator and renders empty.
    A const generator is already broken across renders (the second render
    would find it exhausted either way), so this is the same misuse,
    surfacing one render earlier.

    ``const_vars`` maps the const template-variable names to ordinary values,
    as produced by ``extract_const_vars`` from the renderer's side metadata.
    With no const variables the pass still precomputes
    expressions that use no variables at all and joins static strings.

    ``visible_names`` is the complete set of names in the live render context.
    It lets loop precomputing preserve the runtime no-shadowing rule even when
    the colliding outer value is not const. Production callers always pass it;
    direct callers that omit it get the names from ``const_vars``.

    The input list and its nodes are not modified; a kept node whose interior
    changed is rebuilt (nodes hold no per-render state, so sharing the
    unchanged ones is safe).
    """
    const_names = frozenset(const_vars)
    root_visible_names = frozenset(const_vars if visible_names is None else visible_names)
    # Precompute-time evaluation must use the same sandbox mode as the live render, so
    # a node's evaluator is compiled once in the right mode (see _precompute_expr).
    from citry.citry_context import CitryContext  # noqa: PLC0415 - context imports const mapping helpers

    precompute_context = CitryContext(
        variables=_ConstMapping(const_vars, const_values=const_vars),
        sandboxed=sandboxed,
    )
    return _precompute_into(
        body,
        const_names,
        precompute_context,
        visible_names=root_visible_names,
        precompute_attrs=precompute_attrs,
    )


def _precompute_into(
    body: list[BodyItem],
    const_names: frozenset[str],
    precompute_context: CitryContext,
    *,
    visible_names: frozenset[str] | None,
    precompute_attrs: bool,
) -> list[BodyItem]:
    """Precompute one body list (the recursion step of ``precompute_const_parts``)."""
    precomputed: list[BodyItem] = []
    for item in body:
        _precompute_item(
            item,
            const_names,
            precompute_context,
            precomputed,
            visible_names=visible_names,
            precompute_attrs=precompute_attrs,
        )
    return _merge_static(precomputed)


def _precompute_item(
    item: BodyItem,
    const_names: frozenset[str],
    precompute_context: CitryContext,
    out: list[BodyItem],
    *,
    visible_names: frozenset[str] | None,
    precompute_attrs: bool,
) -> None:
    """Precompute one body item, appending the result(s) to ``out``."""
    # Imported lazily to break the import cycle; see the NOTE above precompute_const_parts.
    from citry.nodes import (  # noqa: PLC0415
        ComponentNode,
        ElementAttrsNode,
        ElementKeyNode,
        ExprNode,
        FillNode,
        ForNode,
        IfNode,
        SlotNode,
    )

    if isinstance(item, str):
        out.append(item)
        return

    if isinstance(item, ExprNode) and set(item.used_vars) <= const_names:
        out.append(_precompute_expr(item, precompute_context))
        return

    if isinstance(item, ElementAttrsNode):
        if precompute_attrs and set(item.used_vars) <= const_names:
            out.append(_precompute_element_attrs(item, precompute_context))
        else:
            out.append(item)
        return

    if isinstance(item, ElementKeyNode):
        if set(item.used_vars) <= const_names:
            out.append(_precompute_element_key(item, precompute_context))
        else:
            out.append(item)
        return

    if isinstance(item, ComponentNode):
        # The component tag itself never precomputes (each render makes a fresh
        # child), but its body does: fill bodies and the implicit default
        # slot body render against THIS component's variables (the fill
        # writer's scope), so const expressions inside them precompute like any
        # other. Each FillNode below applies its own binding scope before its
        # body is precomputed.
        precomputed = _precompute_into(
            item.body,
            const_names,
            precompute_context,
            visible_names=visible_names,
            precompute_attrs=precompute_attrs,
        )
        if _body_changed(item.body, precomputed):
            item = ComponentNode(
                item.source,
                item.position,
                item.attrs,
                precomputed,
                item.used_vars,
                item.name,
                item.contains_fills,
                item.metadata,
            )
        out.append(item)
        return

    if isinstance(item, FillNode):
        # A fill's data/fallback names apply only to its body. Direct names
        # mask matching outer constants. A c-bind that may still supply either
        # name makes every variable-dependent expression unsafe to precompute.
        fill_const_names, fill_visible_names = _fill_body_scope(item, const_names, visible_names)
        precomputed = _precompute_into(
            item.body,
            fill_const_names,
            precompute_context,
            visible_names=fill_visible_names,
            precompute_attrs=precompute_attrs,
        )
        if _body_changed(item.body, precomputed):
            item = FillNode(item.source, item.position, item.attrs, precomputed, item.used_vars, item.introduced_vars)
        out.append(item)
        return

    if isinstance(item, SlotNode):
        # A slot's fallback body stays in the surrounding component scope.
        precomputed = _precompute_into(
            item.body,
            const_names,
            precompute_context,
            visible_names=visible_names,
            precompute_attrs=precompute_attrs,
        )
        if _body_changed(item.body, precomputed):
            item = SlotNode(item.source, item.position, item.attrs, precomputed, item.used_vars, item.introduced_vars)
        out.append(item)
        return

    if isinstance(item, IfNode):
        if _conds_are_const(item, const_names):
            try:
                branch_body = item.active_branch_body(precompute_context)
            except Exception:  # noqa: BLE001, S110 (deliberate: defer the error to render, see precompute_const_parts)
                pass
            else:
                # The same branch wins on every render that shares this cache
                # entry: keep only the matching branch's content (precomputed),
                # drop the rest. None means no branch matched, so nothing
                # remains at all.
                if branch_body is not None:
                    for child in branch_body:
                        _precompute_item(
                            child,
                            const_names,
                            precompute_context,
                            out,
                            visible_names=visible_names,
                            precompute_attrs=precompute_attrs,
                        )
                return
        # Dynamic (or failing) conditions: keep the node, precompute inside the
        # branch bodies.
        out.append(
            _precompute_branch_bodies(
                item,
                const_names,
                precompute_context,
                visible_names=visible_names,
                precompute_attrs=precompute_attrs,
            )
        )
        return

    if isinstance(item, ForNode):
        unrolled = _try_unroll_for(
            item,
            const_names,
            precompute_context,
            visible_names=visible_names,
            precompute_attrs=precompute_attrs,
        )
        if unrolled is not None:
            out.append(unrolled)
            return
        out.append(
            _precompute_branch_bodies(
                item,
                const_names,
                precompute_context,
                visible_names=visible_names,
                precompute_attrs=precompute_attrs,
            )
        )
        return

    out.append(item)


def _precompute_expr(node: ExprNode, precompute_context: CitryContext) -> BodyItem:
    """
    Evaluate an all-const expression; replace it with text when possible.

    Mirrors the value rules of ``ExprNode.render`` / ``_render_value``:
    ``None`` becomes the empty string and a plain value becomes its escaped
    text (the same result every time, so safe to bake in). A ``Slot``,
    ``CitryElement``, or ``CitryRender`` value must render fresh each time
    (it produces render ids and collected dependencies), so the node is kept
    and renders normally. A failing evaluation also keeps the node, so the
    error surfaces at render time through the normal path (see
    ``precompute_const_parts``).
    """
    # Imported lazily to break the import cycle; see the NOTE above precompute_const_parts.
    from citry.citry_render import CitryRender  # noqa: PLC0415

    try:
        # Unwrap a Const marker so the identity check sees the real value, the
        # same rule as ``_render_value``.
        value = const_value(node.evaluate(precompute_context.variables, sandboxed=precompute_context.sandboxed))
        if value is None:
            return ""
        if isinstance(value, (Slot, CitryElement, CitryRender, ComponentLike)):
            return node
        return str(escape(value))
    except Exception:  # noqa: BLE001 (deliberate: defer the error to render, see precompute_const_parts)
        return node


def _precompute_element_attrs(node: ElementAttrsNode, precompute_context: CitryContext) -> BodyItem:
    """
    Render an all-const attribute region once; replace it with text when possible.

    Mirrors ``_precompute_expr``: the region renders to the same string on every
    render that shares the cache entry, so it is safe to bake in. A region
    holding a nested-template attribute value renders to a ``CitryRender``
    (fresh parts each render), so the node is kept; a failing resolve also
    keeps the node, so the error surfaces at render time through the normal
    path. The ``on_attrs_resolved`` hook is not a concern here: the caller
    only precomputes these regions when no installed extension implements it.
    """
    try:
        rendered = node.render(precompute_context)
    except Exception:  # noqa: BLE001 (deliberate: defer the error to render, see precompute_const_parts)
        return node
    if isinstance(rendered, str):
        return str(rendered)
    return node


def _precompute_element_key(node: ElementKeyNode, precompute_context: CitryContext) -> BodyItem:
    """Render an all-const element key once, deferring any evaluation error."""
    try:
        return str(node.render(precompute_context))
    except Exception:  # noqa: BLE001 (defer the error to the normal render path)
        return node


def _body_changed(old: list[BodyItem], new: list[BodyItem]) -> bool:
    """True when precomputing produced a different body list (so the node must be rebuilt)."""
    return len(new) != len(old) or any(n is not o for n, o in zip(new, old, strict=True))


def _fill_body_scope(
    node: FillNode,
    const_names: frozenset[str],
    visible_names: frozenset[str] | None,
) -> tuple[frozenset[str], frozenset[str] | None]:
    """Return the const and visible names in scope inside one fill body."""
    binding_is_dynamic = {"data": False, "fallback": False}
    for attr in node.attrs:
        if attr.key == "c-bind":
            binding_is_dynamic = {"data": True, "fallback": True}
        elif attr.key in binding_is_dynamic:
            binding_is_dynamic[attr.key] = False

    if any(binding_is_dynamic.values()):
        # A spread may choose any binding name at render time. Variable-free
        # expressions remain safe, but a nested binder cannot be removed
        # because its eventual outer-name set is not yet known.
        return frozenset(), None

    introduced = frozenset(node.introduced_vars)
    body_visible_names = None if visible_names is None else visible_names | introduced
    return const_names.difference(introduced), body_visible_names


def _precompute_branch_bodies(
    node: IfNode | ForNode,
    const_names: frozenset[str],
    precompute_context: CitryContext,
    *,
    visible_names: frozenset[str] | None,
    precompute_attrs: bool,
) -> BodyItem:
    """
    Precompute inside a kept ``IfNode``/``ForNode``: same node, precomputed branch bodies.

    Each branch is the compiler's ``(position, attrs, body, introduced_vars)``
    tuple. A loop branch masks the variables it introduces before its body is
    precomputed; its ``<c-empty>`` branch introduces nothing and therefore
    keeps the surrounding const names. If nothing inside changed, the original
    node is returned; otherwise a rebuilt node of the same type takes its place
    (nodes hold no per-render state, so the swap is safe).
    """
    new_branches = []
    changed = False
    for branch in node.branches:
        body: list[BodyItem] = branch[2]
        introduced = frozenset(branch[3])
        branch_const_names = const_names.difference(introduced)
        branch_visible_names = None if visible_names is None else visible_names | introduced
        precomputed = _precompute_into(
            body,
            branch_const_names,
            precompute_context,
            visible_names=branch_visible_names,
            precompute_attrs=precompute_attrs,
        )
        if _body_changed(body, precomputed):
            changed = True
            new_branches.append((branch[0], branch[1], precomputed, branch[3]))
        else:
            new_branches.append(branch)
    if not changed:
        return node
    return type(node)(node.source, tuple(new_branches), node.used_vars)


def _try_unroll_for(
    node: ForNode,
    const_names: frozenset[str],
    precompute_context: CitryContext,
    *,
    visible_names: frozenset[str] | None,
    precompute_attrs: bool,
) -> ForNode | None:
    """
    Run an all-const loop once, ahead of time; retain a guarded node, or ``None``.

    Requirements, checked before touching the iterable: the loop's ``each``
    clause uses only const variables, and every branch body looks precomputable
    from its shape alone, with the loop variables counted as const (only
    text, expressions, and ``<c-if>`` chains whose variables all fit). A
    component, slot, or unknown node disqualifies the loop: pre-computing
    would repeat the same node object once per iteration, and the copies
    would all lose their own iteration's loop-variable values.

    The loop then runs once here, through the node's own ``iter_bodies`` (the
    same evaluation a render uses), precomputing each iteration's body with that
    iteration's loop-variable values. Gives up (returns ``None``) when an
    iteration produces anything but text, when evaluation fails, or past
    ``_MAX_UNROLL_ITERATIONS`` iterations. The returned ``ForNode`` keeps a
    live binding check around the baked text: an earlier expression can mutate
    the render context after this cache entry was built.
    """
    # Imported lazily to break the import cycle; see the NOTE above precompute_const_parts.
    from citry.nodes import _find_attr  # noqa: PLC0415

    loop_branch = node.branches[0]
    targets: tuple[str, ...] = tuple(loop_branch[3])
    target_names = frozenset(targets)
    if visible_names is None or target_names & visible_names:
        return None

    each_attr = _find_attr(loop_branch[1], "each")
    each_used = getattr(each_attr, "used_vars", None) if each_attr is not None else None
    if each_used is None or not set(each_used) <= const_names:
        return None

    inner_names = const_names | target_names
    inner_visible_names = visible_names | target_names
    if not all(
        _statically_precomputable(branch[2], inner_names, precompute_attrs=precompute_attrs)
        for branch in node.branches
    ):
        return None

    parts: list[str] = []
    try:
        for count, (body, body_context) in enumerate(node.iter_bodies(precompute_context), start=1):
            if count > _MAX_UNROLL_ITERATIONS:
                return None
            precomputed = _precompute_into(
                body,
                inner_names,
                body_context,
                visible_names=inner_visible_names,
                precompute_attrs=precompute_attrs,
            )
            for part in precomputed:
                if not isinstance(part, str):
                    # A value turned out to need per-render rendering (a Slot
                    # or element in a const variable); the static check cannot
                    # see values, so this is found here.
                    return None
                parts.append(part)
    except Exception:  # noqa: BLE001 (deliberate: defer the error to render, see precompute_const_parts)
        return None
    return node._with_precomputed_text("".join(parts))


def _statically_precomputable(body: list[BodyItem], names: frozenset[str], *, precompute_attrs: bool) -> bool:
    """
    True when every item in ``body`` can precompute to text given const ``names``.

    A shape check only (no evaluation): text always fits; an expression or an
    attribute region fits when its variables fit (and, for attribute regions,
    when precomputing them is allowed at all); an ``<c-if>`` fits when its
    conditions and every branch body fit. Any other node kind (component,
    slot, fill, nested template, extension-injected) does not precompute to text,
    so the body fails.
    """
    # Imported lazily to break the import cycle; see the NOTE above precompute_const_parts.
    from citry.nodes import ElementAttrsNode, ElementKeyNode, ExprNode, IfNode  # noqa: PLC0415

    for item in body:
        if isinstance(item, str):
            continue
        if isinstance(item, ExprNode) and set(item.used_vars) <= names:
            continue
        if precompute_attrs and isinstance(item, ElementAttrsNode) and set(item.used_vars) <= names:
            continue
        if isinstance(item, ElementKeyNode) and set(item.used_vars) <= names:
            continue
        if (
            isinstance(item, IfNode)
            and _conds_are_const(item, names)
            and all(
                _statically_precomputable(branch[2], names, precompute_attrs=precompute_attrs)
                for branch in item.branches
            )
        ):
            continue
        return False
    return True


def _conds_are_const(node: IfNode, const_names: frozenset[str]) -> bool:
    """
    True when every branch condition of ``node`` uses only const variables.

    Then the same branch wins on every render that shares the cache entry,
    so the choice can be made once, ahead of time. A condition attribute
    without a readable ``used_vars`` (a custom attribute type injected by an
    extension) counts as non-const, to be safe. The ``c-else`` branch has no
    condition and rules out nothing.
    """
    # Imported lazily to break the import cycle; see the NOTE above precompute_const_parts.
    from citry.nodes import _find_attr  # noqa: PLC0415

    for branch in node.branches:
        cond_attr = _find_attr(branch[1], "cond")
        if cond_attr is None:
            continue
        used_vars = getattr(cond_attr, "used_vars", None)
        if used_vars is None or not set(used_vars) <= const_names:
            return False
    return True


def _merge_static(items: list[BodyItem]) -> list[BodyItem]:
    """Join static strings that ended up next to each other; drop empty ones."""
    merged: list[BodyItem] = []
    for item in items:
        if isinstance(item, str):
            if not item:
                continue
            if merged and isinstance(merged[-1], str):
                merged[-1] = merged[-1] + item
                continue
        merged.append(item)
    return merged
