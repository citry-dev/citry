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

- ``Const`` is the marker. It is a transparent wrapper (a ``wrapt.ObjectProxy``
  subclass): it behaves exactly like the value inside, so user code and
  template expressions never notice it, while the engine can still ask
  ``is_const(x)``. The marker stays on the value as it travels into child
  components, so each component along the way gets the optimization too.
- ``extract_const_vars`` looks at a component's template variables, picks out
  the ``Const``-marked ones, and builds a **cache key** from their names and
  values (``freeze_const`` turns each value into a stable, dict-key-safe
  form).
- ``ConstBodyCache`` is the cache: one pre-computed template per component
  class and per combination of ``Const`` values. It keeps a bounded number of
  entries (least recently used entries are dropped first) and lives on a
  ``Citry`` instance.
- ``fold_body`` is the pre-computing step, called **folding** in this module
  and in docs/design/constness.md: it walks the compiled template once,
  replaces everything that depends only on ``Const`` values with its final
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
- **The marker flows through plain containers and dataclasses.** The
  auto-converted ``Kwargs`` dataclass stores values as-is, so reading the
  typed view keeps the marker. A validating model (a Pydantic ``Kwargs``)
  accepts a marked input but produces a new value, stripping the marker; the
  value then safely renders un-optimized. To keep const-ness with a
  validating model, read the marked value from ``raw_kwargs``.
- **Transformations drop the marker.** ``Const("hi")`` passed through
  unchanged stays const; ``kwargs["title"].upper()`` returns a plain value.
  Mark the final value if it is the transformed form that is stable.

Example:
    Mark an input constant::

        from citry import Component, Const

        class Card(Component):
            template = "<p>{{ cols }}</p>"

            def template_data(self, kwargs, slots=None):
                return {"cols": kwargs["cols"]}  # the marker flows through

        Card(cols=Const(3)).render()

"""

from __future__ import annotations

from collections import OrderedDict
from threading import RLock
from typing import TYPE_CHECKING, Any, Final, TypeAlias, TypeVar

import wrapt

from citry.citry_context import CitryContext
from citry.citry_element import CitryElement
from citry.slots import Slot
from citry.util.html import escape

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Mapping

    from citry.component import Component
    from citry.nodes import BodyItem, ExprNode, ForNode, IfNode

_T = TypeVar("_T")


# #########################################################
# THE CONST MARKER
# #########################################################

class _ConstProxy(wrapt.ObjectProxy):
    """
    A transparent marker that a value is constant across renders.

    Behaves exactly like the wrapped value: arithmetic, attribute and item
    access, method calls, comparisons, ``str``, and ``repr`` (forwarded, so a
    marked value inside a container reprs identically to the plain value;
    the engine marks template literals without the user opting in, so reprs
    must not betray the marker in user-visible output). Use through the
    public ``Const`` name; detect with ``is_const(x)``.
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


def const_value(value: Any) -> Any:
    """Return the underlying value if ``value`` is ``Const``, else ``value``."""
    return value.__wrapped__ if isinstance(value, _ConstProxy) else value


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
    wrong value). The rules, per ``docs/design/constness.md`` section 7.2:

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
    if isinstance(value, _ConstProxy):
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
    while isinstance(value, _ConstProxy):
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

    - ``const_vars``: name -> value (still wrapped in ``Const``) for every
      variable that is marked const AND could be turned into a cache key.
      ``fold_body`` evaluates against this mapping when it pre-computes the
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
    entries. (They stay ``Const``-marked in ``variables``, so they still
    flow down to child components.) Leaving a variable out is always safe:
    it just renders normally.
    """
    const_vars: dict[str, Any] = {}
    items: list[tuple[str, Any]] = []
    for name, value in variables.items():
        if not is_const(value):
            continue
        if used_vars is not None and name not in used_vars:
            continue
        frozen = freeze_const(value)
        if frozen is _UNFREEZABLE:
            continue
        const_vars[name] = value
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

_CacheKey: TypeAlias = "tuple[type[Component], ConstSignature]"


class ConstBodyCache:
    """
    The cache of pre-computed template bodies, one per set of ``Const`` values.

    A "body" is what a template compiles to: a list of static strings and
    node objects. The entry stored for a render that had ``Const`` inputs has
    been through ``fold_body``, so the parts depending on those inputs are
    already computed; the entry for a render with no ``Const`` inputs is the
    plain compiled body that all such renders share. Keys are
    ``(component class, ConstSignature)``.

    The cache lives on a ``Citry`` instance (``Citry._const_body_cache``), so
    deleting the instance or calling ``Citry.clear()`` releases everything.
    It holds at most ``max_entries`` entries and drops the least recently
    used one when full; that way, marking ever-changing values ``Const`` (a
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
        self._entries: OrderedDict[_CacheKey, list[BodyItem]] = OrderedDict()

    def get_or_build(
        self,
        comp_cls: type[Component],
        signature: ConstSignature,
        build: Callable[[], list[BodyItem]],
    ) -> list[BodyItem]:
        """
        Return the cached body for ``(comp_cls, signature)``, building it once.

        On a hit the entry is marked most-recently-used. On a miss ``build()``
        runs under the lock and the result is stored; if it raises, nothing is
        cached and the error propagates (so the next render retries).
        """
        key = (comp_cls, signature)
        with self._lock:
            body = self._entries.get(key)
            if body is not None:
                self._entries.move_to_end(key)
                return body
            body = build()
            self._entries[key] = body
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)
            return body

    def evict_component(self, comp_cls: type[Component]) -> None:
        """Drop every entry of one component class (hot reload invalidation)."""
        with self._lock:
            stale = [key for key in self._entries if key[0] is comp_cls]
            for key in stale:
                del self._entries[key]

    def clear(self) -> None:
        """Drop all entries."""
        with self._lock:
            self._entries.clear()

    def values(self) -> list[list[BodyItem]]:
        """A snapshot of the cached bodies (mainly for tests and debugging)."""
        with self._lock:
            return list(self._entries.values())

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return f"ConstBodyCache(entries={len(self._entries)}, max_entries={self._max_entries})"


# #########################################################
# FOLDING (the pre-computing step)
# #########################################################

# NOTE: Folding needs the runtime node classes and CitryRender for its
# isinstance checks, but citry_render imports this module (for const_value)
# and citry.nodes imports citry_render, so importing either at the top here
# would be circular. They are imported inside the folding functions instead;
# folding runs once per cache entry, so the cost is a few dictionary lookups
# per cache miss.


_MAX_UNROLL_ITERATIONS: Final = 1000
"""
The most loop iterations folding will run ahead of time (see
``_try_unroll_for``). The pre-computed text is exactly what every render
would produce anyway, so output size is not the concern; the cap guards
against huge or never-ending const iterables. Past it, the loop just renders
normally each time.
"""


def fold_body(body: list[BodyItem], const_vars: dict[str, Any]) -> list[BodyItem]:
    """
    Pre-compute the parts of ``body`` that depend only on ``const_vars``.

    This is the step this module calls **folding**: given a compiled template
    (``body``, a list of static strings and node objects) and the variables
    promised to be constant (``const_vars``), do the work that depends only
    on those variables right now, once, and return a new body where that work
    is already done. The result goes into ``ConstBodyCache``, so every later
    render with the same const values reuses it. What gets pre-computed:

    - A ``{{ expr }}`` node whose variables are all const is evaluated once
      and replaced with its escaped text.
    - A ``<c-if>`` whose branch conditions use only const variables is
      decided once: only the matching branch's content remains (itself
      folded), the other branches are dropped.
    - A ``<c-if>`` whose conditions use non-const variables is kept (it must
      be decided on every render), but constant expressions INSIDE its
      branches still fold.
    - A ``<c-for>`` over a const iterable whose body folds entirely to text
      is run once here, and the per-iteration text is baked in (within one
      iteration, the loop variables count as const). Capped at
      ``_MAX_UNROLL_ITERATIONS``.
    - A ``<c-for>`` that cannot be pre-run is kept, but constant expressions
      inside its body still fold: an expression that does not touch the loop
      variables produces the same text on every iteration. (Loop variables
      themselves are never const; the parser forbids them from reusing an
      outer variable's name, so there is no overlap to worry about.)
    - Static strings that end up next to each other are joined.

    Everything else stays in place as a normal node and re-evaluates on every
    render. That matters because the folded body is SHARED by every render
    with the same const values, while their other (non-const) variables
    differ, so anything not pre-computed must still work for all of them.

    What is never pre-computed, and why (docs/design/constness.md sections
    5, 9, 10):

    - ``ComponentNode`` (a child component tag): every render of a child gets
      a fresh component instance and a fresh render id, and its slot content
      captures the surrounding render's state. Its BODY does fold, though:
      fill bodies and the implicit default-slot body render against this
      component's variables, so const expressions inside slot content are
      pre-computed even while the tag itself stays.
    - ``SlotNode``: which fill it renders comes from the live component
      instance, which changes per render even when the tag itself uses no
      template variables. It also fires the ``on_slot_rendered`` hook. Its
      fallback body folds in place, same as a fill body.
    - ``FillNode``: stays (it is consumed when fills are collected, each
      render), but its body folds in place.
    - An expression whose VALUE is a ``Slot``, ``CitryElement``, or
      ``CitryRender``: rendering those produces per-render state (render
      ids, collected dependencies), so only values that become plain text
      may be baked in.
    - Node types this step does not know (an extension may inject custom
      nodes via ``on_template_compiled``): kept as-is, to be safe.

    **Folding never raises.** A const expression or condition that fails here
    is kept as a normal node, so the error (if any) surfaces during a render,
    through the normal path, exactly as it would without the optimization.
    The trade-off of folding inside kept ``<c-if>`` branches is WHEN a const
    expression runs: it is evaluated once here even if the branch it sits in
    is not taken by this particular render (a later render sharing the cache
    entry may take it). Citry expressions are sandboxed and expected to have
    no side effects, so running one early should not be observable.

    One sharp edge of pre-running loops: a one-shot iterable (a generator)
    marked const is consumed by the attempt. If the attempt then has to back
    out (a value deep in the body turns out to be a ``Slot``/element), the
    kept loop node re-iterates the exhausted generator and renders empty.
    A const generator is already broken across renders (the second render
    would find it exhausted either way), so this is the same misuse,
    surfacing one render earlier.

    ``const_vars`` maps the const template variables to their values (still
    wrapped in ``Const``; the wrapper behaves like the value), as produced by
    ``extract_const_vars``. With no const variables the pass still folds
    expressions that use no variables at all and joins static strings.

    The input list and its nodes are not modified; a kept node whose interior
    changed is rebuilt (nodes hold no per-render state, so sharing the
    unchanged ones is safe).
    """
    const_names = frozenset(const_vars)
    fold_context = CitryContext(variables=dict(const_vars))
    return _fold_into(body, const_names, fold_context)


def _fold_into(
    body: list[BodyItem],
    const_names: frozenset[str],
    fold_context: CitryContext,
) -> list[BodyItem]:
    """Fold one body list (the recursion step of ``fold_body``)."""
    folded: list[BodyItem] = []
    for item in body:
        _fold_item(item, const_names, fold_context, folded)
    return _merge_static(folded)


def _fold_item(
    item: BodyItem,
    const_names: frozenset[str],
    fold_context: CitryContext,
    out: list[BodyItem],
) -> None:
    """Fold one body item, appending the result(s) to ``out``."""
    # Imported lazily to break the import cycle; see the NOTE above fold_body.
    from citry.nodes import ComponentNode, ExprNode, FillNode, ForNode, IfNode, SlotNode  # noqa: PLC0415

    if isinstance(item, str):
        out.append(item)
        return

    if isinstance(item, ExprNode) and set(item.used_vars) <= const_names:
        out.append(_fold_expr(item, fold_context))
        return

    if isinstance(item, ComponentNode):
        # The component tag itself never folds (each render makes a fresh
        # child), but its body does: fill bodies and the implicit default
        # slot body render against THIS component's variables (the fill
        # writer's scope), so const expressions inside them fold like any
        # other. A fill's own data/fallback variables can never be const
        # names (the parser rejects reusing an outer variable's name), so
        # expressions using them stay live.
        folded = _fold_into(item.body, const_names, fold_context)
        if _body_changed(item.body, folded):
            item = ComponentNode(
                item.source, item.position, item.attrs, folded, item.used_vars, item.name, item.contains_fills
            )
        out.append(item)
        return

    if isinstance(item, (FillNode, SlotNode)):
        # Same reasoning: the node stays (which fill a slot renders is
        # per-render state), but a fill's body and a slot's fallback body
        # render against this component's variables, so their insides fold.
        folded = _fold_into(item.body, const_names, fold_context)
        if _body_changed(item.body, folded):
            item = type(item)(item.source, item.position, item.attrs, folded, item.used_vars, item.introduced_vars)
        out.append(item)
        return

    if isinstance(item, IfNode):
        if _conds_are_const(item, const_names):
            try:
                branch_body = item.active_branch_body(fold_context)
            except Exception:  # noqa: BLE001, S110 (deliberate: defer the error to render, see fold_body)
                pass
            else:
                # The same branch wins on every render that shares this cache
                # entry: keep only the matching branch's content (folded),
                # drop the rest. None means no branch matched, so nothing
                # remains at all.
                if branch_body is not None:
                    for child in branch_body:
                        _fold_item(child, const_names, fold_context, out)
                return
        # Dynamic (or failing) conditions: keep the node, fold inside the
        # branch bodies.
        out.append(_fold_branch_bodies(item, const_names, fold_context))
        return

    if isinstance(item, ForNode):
        unrolled = _try_unroll_for(item, const_names, fold_context)
        if unrolled is not None:
            out.extend(unrolled)
            return
        out.append(_fold_branch_bodies(item, const_names, fold_context))
        return

    out.append(item)


def _fold_expr(node: ExprNode, fold_context: CitryContext) -> BodyItem:
    """
    Evaluate an all-const expression; replace it with text when possible.

    Mirrors the value rules of ``ExprNode.render`` / ``_render_value``:
    ``None`` becomes the empty string and a plain value becomes its escaped
    text (the same result every time, so safe to bake in). A ``Slot``,
    ``CitryElement``, or ``CitryRender`` value must render fresh each time
    (it produces render ids and collected dependencies), so the node is kept
    and renders normally. A failing evaluation also keeps the node, so the
    error surfaces at render time through the normal path (see
    ``fold_body``).
    """
    # Imported lazily to break the import cycle; see the NOTE above fold_body.
    from citry.citry_render import CitryRender  # noqa: PLC0415

    try:
        # Unwrap a Const marker so the identity check sees the real value, the
        # same rule as ``_render_value``.
        value = const_value(node.evaluate(fold_context.variables))
        if value is None:
            return ""
        if isinstance(value, (Slot, CitryElement, CitryRender)):
            return node
        return str(escape(value))
    except Exception:  # noqa: BLE001 (deliberate: defer the error to render, see fold_body)
        return node


def _body_changed(old: list[BodyItem], new: list[BodyItem]) -> bool:
    """True when folding produced a different body list (so the node must be rebuilt)."""
    return len(new) != len(old) or any(n is not o for n, o in zip(new, old, strict=True))


def _fold_branch_bodies(
    node: IfNode | ForNode,
    const_names: frozenset[str],
    fold_context: CitryContext,
) -> BodyItem:
    """
    Fold inside a kept ``IfNode``/``ForNode``: same node, folded branch bodies.

    Each branch is the compiler's ``(position, attrs, body, introduced_vars)``
    tuple; the body list is folded against the same const variables. For a
    loop this is safe because a const expression that does not use the loop
    variables produces the same text on every iteration, and a loop variable
    can never share a name with a const one (the parser rejects a loop
    variable that reuses an outer variable's name). When nothing inside
    changed, the original node is returned; otherwise a rebuilt node of the
    same type takes its place (nodes hold no per-render state, so the swap is
    safe).
    """
    new_branches = []
    changed = False
    for branch in node.branches:
        body: list[BodyItem] = branch[2]
        folded = _fold_into(body, const_names, fold_context)
        if _body_changed(body, folded):
            changed = True
            new_branches.append((branch[0], branch[1], folded, branch[3]))
        else:
            new_branches.append(branch)
    if not changed:
        return node
    return type(node)(node.source, tuple(new_branches), node.used_vars)


def _try_unroll_for(
    node: ForNode,
    const_names: frozenset[str],
    fold_context: CitryContext,
) -> list[BodyItem] | None:
    """
    Run an all-const loop once, ahead of time; return its text, or ``None``.

    Requirements, checked before touching the iterable: the loop's ``each``
    clause uses only const variables, and every branch body looks foldable
    from its shape alone, with the loop variables counted as const (only
    text, expressions, and ``<c-if>`` chains whose variables all fit). A
    component, slot, or unknown node disqualifies the loop: pre-computing
    would repeat the same node object once per iteration, and the copies
    would all lose their own iteration's loop-variable values.

    The loop then runs once here, through the node's own ``iter_bodies`` (the
    same evaluation a render uses), folding each iteration's body with that
    iteration's loop-variable values. Gives up (returns ``None``) when an
    iteration produces anything but text, when evaluation fails, or past
    ``_MAX_UNROLL_ITERATIONS`` iterations.
    """
    # Imported lazily to break the import cycle; see the NOTE above fold_body.
    from citry.nodes import _find_attr  # noqa: PLC0415

    loop_branch = node.branches[0]
    targets: tuple[str, ...] = tuple(loop_branch[3])
    each_attr = _find_attr(loop_branch[1], "each")
    each_used = getattr(each_attr, "used_vars", None) if each_attr is not None else None
    if each_used is None or not set(each_used) <= const_names:
        return None

    inner_names = const_names | set(targets)
    if not all(_statically_foldable(branch[2], inner_names) for branch in node.branches):
        return None

    parts: list[BodyItem] = []
    try:
        for count, (body, body_context) in enumerate(node.iter_bodies(fold_context), start=1):
            if count > _MAX_UNROLL_ITERATIONS:
                return None
            folded = _fold_into(body, inner_names, body_context)
            if not all(isinstance(part, str) for part in folded):
                # A value turned out to need per-render rendering (a Slot or
                # element in a const variable); the static check cannot see
                # values, so this is found here.
                return None
            parts.extend(folded)
    except Exception:  # noqa: BLE001 (deliberate: defer the error to render, see fold_body)
        return None
    return parts


def _statically_foldable(body: list[BodyItem], names: frozenset[str]) -> bool:
    """
    True when every item in ``body`` can fold to text given const ``names``.

    A shape check only (no evaluation): text always fits; an expression fits
    when its variables fit; an ``<c-if>`` fits when its conditions and every
    branch body fit. Any other node kind (component, slot, fill, nested
    template, extension-injected) does not fold to text, so the body fails.
    """
    # Imported lazily to break the import cycle; see the NOTE above fold_body.
    from citry.nodes import ExprNode, IfNode  # noqa: PLC0415

    for item in body:
        if isinstance(item, str):
            continue
        if isinstance(item, ExprNode) and set(item.used_vars) <= names:
            continue
        if (
            isinstance(item, IfNode)
            and _conds_are_const(item, names)
            and all(_statically_foldable(branch[2], names) for branch in item.branches)
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
    # Imported lazily to break the import cycle; see the NOTE above fold_body.
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
