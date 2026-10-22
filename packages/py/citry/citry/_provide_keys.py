"""
Work out which provide keys can reach each registered component.

A component reads a shared value with ``self.inject("key")``. The value comes
from a component rendered above it: a ``<c-provide key="...">`` around its
tag, a ``self.provide("key", ...)`` call in a component on the way, or the
``provides`` a ``render()`` call passes at the top of the page. The
``citry.template.unknown-inject-key`` rule (``rule_unknown_inject_key``)
reports an ``inject()`` whose key none of these provides.

This module reads the loaded app's templates and Python sources once and
answers, for each component class, the set of keys that can reach it. It
starts from the templates that write the component's tag and walks up to the
templates that write those components, and so on. Slot content counts the
component whose ``<c-slot>`` renders it too, because the runtime looks the key
up along the rendered page, not where the tag was written. When no template
writes the component's tag (Python renders it, or a ``<c-component c-is>``
picks it at render time), the answer is every literal key the app provides
anywhere.

Whenever a path holds something Citry cannot read, such as a ``<c-provide
c-key="...">``, slot content inside a dynamic ``<c-component>``, or a
component that Python code places inside another component, the answer is
"cannot tell" (``None``), and the rule reports nothing for that component.
``citry check`` and the editor's app worker both call `inject_key_scopes`.
"""

from __future__ import annotations

import ast
import os
import re
import sys
import sysconfig
import tokenize
from dataclasses import dataclass, field
from pathlib import Path
from types import CodeType, FunctionType
from typing import TYPE_CHECKING, Any, Literal

from citry._class_introspection import _safe_class_import_path, _safe_class_text, _static_class_dict, _static_class_mro
from citry._component_graph import _build_node, _collect_sources, _foreign_options, _nested_content
from citry._component_introspection import _group_registrations, _loaded_python_file
from citry_core.template_parser import RESERVED_TAG_NAMES, HtmlAttrKind, TemplateElement, parse_template

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

    from citry._component_graph import _Source
    from citry.citry import Citry
    from citry.component import Component


@dataclass(frozen=True, slots=True)
class InjectKeyScope:
    """
    The keys that can reach one class whose methods may call ``self.inject()``.

    Attributes:
        file: The Python file that defines the class.
        qualname: The class's qualified name in that file.
        name: The class name, as messages show it; for a mixin, the name of
            a component that runs it.
        label: The class's import path, such as ``app.components.Card``.
        provided: Every key that reaches at least one registered component
            running this class's code, or ``None`` when some path holds a
            provider Citry cannot read, so nothing may be reported.
        everywhere: True when no template renders any of those components,
            so ``provided`` is every literal key the app provides anywhere.
        components: The registered components that run this class's code:
            the class itself when it is registered, and its registered
            subclasses.

    """

    file: Path
    qualname: str
    name: str
    label: str
    provided: frozenset[str] | None
    everywhere: bool
    components: tuple[type[Component], ...]


@dataclass(frozen=True, slots=True)
class _Frame:
    """
    One element around a tag that can change which keys reach it.

    ``provide`` is a ``<c-provide>``, with its literal key or ``None`` for a key
    written as an expression. ``fill`` is slot content that the component
    ``owner`` (a registered name, or ``None`` when picked at render time)
    renders through its slot ``slot`` (``None`` when the name is an
    expression). ``opaque`` is markup passed in a component's attribute, which
    the receiving component may render anywhere.
    """

    kind: Literal["provide", "fill", "opaque"]
    key: str | None = None
    owner: str | None = None
    slot: str | None = None


_Context = tuple[_Frame, ...]


@dataclass(slots=True)
class _TemplateFacts:
    """What one template says about providing keys, read once per template even when several classes share it."""

    # Each component tag: the registered name it calls (``None`` for a
    # dynamic `<c-component>`), and the frames around it.
    sites: list[tuple[str | None, _Context]] = field(default_factory=list)
    # Each `<c-slot>`: its name (``None`` when written as an expression) and the frames around it.
    slots: list[tuple[str | None, _Context]] = field(default_factory=list)
    # Every literal `<c-provide>` key, for the comparison with every key the app provides.
    provide_keys: set[str] = field(default_factory=set)
    # A nested template could not be parsed, so a tag or provider may be hidden.
    unreadable: bool = False
    # Citry's own template. Its dynamic `<c-component>` picks one of Citry's
    # private host classes, which only pass the slot content through.
    builtin: bool = False


@dataclass(frozen=True, slots=True)
class _ClassKeys:
    """The keys one class's own methods pass to ``provide()``."""

    keys: frozenset[str]
    # A `provide()` call whose key is an expression Citry cannot resolve.
    dynamic: bool


# Names the parser reads directly; `<c-fill>` and `<c-slot>` are handled
# on their own, the others only wrap content in the same place.
_STRUCTURAL_TAGS = frozenset(RESERVED_TAG_NAMES)


# A folder with more Python files than this is usually a home folder or
# several projects. Reading all of it would make the check and the editor's
# load slow, so the rule reports nothing instead.
_MAX_PROJECT_FILES = 20_000


def inject_key_scopes(
    engine: Citry,
    registrations: Mapping[str, type[Component]],
    workspace: Path | None,
) -> tuple[InjectKeyScope, ...] | None:
    """
    Work out which keys can reach each class whose code a registered component runs.

    Returns ``None`` when the rule cannot run at all: a registered template
    could not be read or parsed, so any component may be rendered somewhere
    Citry cannot see. ``workspace`` is the project folder whose Python files
    are searched for ``render(provides={...})`` keys, next to the modules
    that define the registered components.
    """
    groups = _group_registrations(registrations)
    records = [
        (comp_cls, _build_node(engine, comp_cls, names, builtin=engine._is_builtin_component(comp_cls)))
        for comp_cls, names in groups
    ]
    sources, problems = _collect_sources(engine, tuple(records))
    # A template Citry cannot read may render any component or provide any key.
    if problems:
        return None
    facts_by_class: dict[int, _TemplateFacts] = {}
    for source in sources.values():
        facts = _source_facts(engine, source)
        if facts is None:
            return None
        for consumer in source.consumers:
            facts_by_class[id(consumer.component_class)] = facts

    by_name = {name.lower(): comp_cls for name, comp_cls in registrations.items()}
    classes = [comp_cls for comp_cls, _names in groups]
    authored = [comp_cls for comp_cls in classes if not engine._is_builtin_component(comp_cls)]
    reader = _SourceReader()
    own_keys = {id(comp_cls): reader.component_keys(comp_cls) for comp_cls in classes}
    project = _read_project_python(authored, workspace)
    render_keys = None if project is None else project[0]
    placed = frozenset() if project is None else project[1]
    resolver = _Reach(by_name, facts_by_class, own_keys, render_keys, placed)

    # Every key the app provides anywhere, for a component no template renders.
    # A source Citry cannot read may provide any key, so nothing is reported then.
    everywhere: frozenset[str] | None = None
    if render_keys is not None and all(keys is not None for keys in own_keys.values()):
        everywhere = render_keys.union(
            *(facts.provide_keys for facts in facts_by_class.values()),
            *(keys.keys for keys in own_keys.values() if keys is not None),
        )

    # The code that calls `inject()` may live on a base class or a mixin, so
    # each class whose code a registered component runs collects that
    # component's answer.
    scopes: dict[int, tuple[type, list[type[Component]]]] = {}
    for comp_cls in authored:
        for owner in _code_classes(comp_cls):
            scopes.setdefault(id(owner), (owner, []))[1].append(comp_cls)

    found: list[InjectKeyScope] = []
    for owner, components in scopes.values():
        file = _loaded_python_file(owner)
        qualname = _safe_class_text(owner, "__qualname__")
        name = _safe_class_text(owner, "__name__")
        # An installed package's code is its authors' to check, and the
        # reader cannot change it.
        if file is None or qualname is None or name is None or _installed(file):
            continue
        # A mixin is never rendered on its own, so messages name a component that runs it.
        if not any(component is owner for component in components):
            name = min(_safe_class_text(component, "__name__") or name for component in components)
        answers = [resolver.reaching(component, everywhere) for component in components]
        provided: frozenset[str] | None = None
        if all(answer[0] is not None for answer in answers):
            provided = frozenset().union(*(answer[0] for answer in answers if answer[0] is not None))
        found.append(
            InjectKeyScope(
                file=file,
                qualname=qualname,
                name=name,
                label=_safe_class_import_path(owner) or qualname,
                provided=provided,
                everywhere=all(answer[1] for answer in answers),
                components=tuple(components),
            )
        )
    found.sort(key=lambda scope: (scope.file.as_posix(), scope.qualname))
    return tuple(found)


def engine_inject_keys(engine: Citry, workspace: Path) -> dict[str, object]:
    """
    Copy the keys that reach each component class, for the editor's app worker.

    The worker exits after it answers, so the editor cannot walk the
    templates later. It receives these keys and compares them with the
    ``self.inject()`` calls in the file being edited. ``checked`` is false
    when the rule cannot run, and the editor then reports nothing.
    """
    registrations = engine.components
    scopes = inject_key_scopes(engine, registrations, workspace)
    if scopes is None:
        return {"checked": False, "classes": []}
    return {
        "checked": True,
        "classes": [
            {
                "file": scope.file.as_posix(),
                "qualname": scope.qualname,
                "name": scope.name,
                "provided": None if scope.provided is None else sorted(scope.provided),
                "everywhere": scope.everywhere,
                # The editor reads each component's `rule_unknown_inject_key`
                # severity from the lint records under these ids.
                "definition_ids": [
                    str(_static_class_dict(component).get("_definition_id")) for component in scope.components
                ],
            }
            for scope in scopes
        ],
    }


def _code_classes(comp_cls: type[Component]) -> Iterator[type]:
    """
    Yield the component class and each base class or mixin whose methods it runs.

    Citry's own classes, such as ``Component``, and the standard library's,
    such as ``typing.Generic``, are left out, because app keys are provided
    and injected only in app code.
    """
    for index, candidate in enumerate(_static_class_mro(comp_cls)):
        module = _safe_class_text(candidate, "__module__") or ""
        # A built-in component is Citry's own class, but it is registered, so
        # its own `provide()` calls still count.
        if index > 0 and (module.split(".", 1)[0] in {"citry", "builtins"} or _in_standard_library(candidate)):
            continue
        yield candidate


# Where the running Python keeps its standard library. A project package
# can share a standard module's name, such as `profile`, so the check
# looks at where the class's file is, not at its module name.
_STANDARD_LIBRARY = Path(sysconfig.get_paths()["stdlib"]).resolve()


def _in_standard_library(cls: type) -> bool:
    file = _loaded_python_file(cls)
    if file is None:
        # A class with no file, such as one written in C, comes from Python itself.
        module = sys.modules.get(_safe_class_text(cls, "__module__") or "")
        return module is not None and getattr(module, "__file__", None) is None
    return file.resolve().is_relative_to(_STANDARD_LIBRARY) and "site-packages" not in file.parts


class _Reach:
    """Combine the template facts and ``provide()`` keys into the keys that reach each component."""

    def __init__(
        self,
        by_name: Mapping[str, type[Component]],
        facts_by_class: Mapping[int, _TemplateFacts],
        own_keys: Mapping[int, _ClassKeys | None],
        render_keys: frozenset[str] | None,
        placed: frozenset[str],
    ) -> None:
        self._by_name = by_name
        self._facts = facts_by_class
        self._own_keys = own_keys
        self._render_keys = render_keys
        self._placed = placed
        # Who writes each component's tag, keyed by the written component's id.
        self._sites: dict[int, list[tuple[type[Component], _Context]]] = {}
        # Dynamic `<c-component>` tags, which may render any component.
        self._dynamic: list[tuple[type[Component], _Context]] = []
        classes = {id(comp_cls): comp_cls for comp_cls in by_name.values()}
        for class_id, facts in facts_by_class.items():
            writer = classes.get(class_id)
            if writer is None:
                continue
            for target, context in facts.sites:
                if target is None:
                    self._dynamic.append((writer, context))
                    continue
                written = by_name.get(target)
                if written is not None:
                    self._sites.setdefault(id(written), []).append((writer, context))
        self._ancestors = {class_id: self._writers_above(class_id) for class_id in classes}
        # What each component provides to each of its slots, keyed by (component id, slot name).
        self._slots = self._solve_slots(facts_by_class)
        self._reach = self._solve(classes)

    def reaching(
        self, component: type[Component], everywhere: frozenset[str] | None
    ) -> tuple[frozenset[str] | None, bool]:
        """
        Return the keys that reach ``component``, and whether that is the whole-app set.

        A component no template writes falls back to every key the app
        provides, because Citry cannot see where Python renders it. So does
        a component written only inside its own templates, such as a tree
        that renders itself: Python renders the outermost one.
        """
        class_id = id(component)
        # Python places this component inside other content, such as another
        # component's slot, where Citry cannot see the keys.
        if _safe_class_text(component, "__name__") in self._placed:
            return None, False
        if class_id not in self._sites:
            return everywhere, True
        ancestors = self._ancestors[class_id]
        if all(class_id in self._ancestors[ancestor] for ancestor in ancestors):
            return everywhere, True
        return self._reach.get(class_id), False

    def _writers_above(self, class_id: int) -> set[int]:
        """Return every component whose template writes this one's tag, directly or through others."""
        seen: set[int] = set()
        pending = [id(writer) for writer, _context in self._sites.get(class_id, ())]
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            pending.extend(id(writer) for writer, _context in self._sites.get(current, ()))
        return seen

    def _solve_slots(
        self, facts_by_class: Mapping[int, _TemplateFacts]
    ) -> dict[tuple[int, str | None], frozenset[str] | None]:
        """
        Work out what each component provides to the content of each of its slots.

        Those are its own ``provide()`` keys and the keys provided around each
        matching ``<c-slot>`` in its template. A component that renders the
        slot from Python, with no matching ``<c-slot>``, gives only its own
        keys. A ``<c-slot>`` can pass the content on into another component's
        slot, also back into itself, so the answers grow until they stop
        changing; this keeps the work proportional to the number of slots,
        however deep the content is passed on.
        """
        owners: dict[tuple[int, str | None], type[Component]] = {}
        unique_facts = {id(facts): facts for facts in facts_by_class.values()}
        for facts in unique_facts.values():
            for _name, context in (*facts.sites, *facts.slots):
                for frame in context:
                    owner = self._by_name.get(frame.owner) if frame.kind == "fill" and frame.owner else None
                    if owner is not None:
                        owners[(id(owner), frame.slot)] = owner
        answers: dict[tuple[int, str | None], frozenset[str] | None] = dict.fromkeys(owners, frozenset())
        changed = True
        while changed:
            changed = False
            for pair, owner in owners.items():
                if answers[pair] is None:
                    continue
                found = self._slot_keys(owner, pair[1], answers)
                if found != answers[pair]:
                    answers[pair] = found
                    changed = True
        return answers

    def _slot_keys(
        self,
        owner: type[Component],
        slot: str | None,
        slots: Mapping[tuple[int, str | None], frozenset[str] | None],
    ) -> frozenset[str] | None:
        """Return what ``owner`` provides to its slot ``slot``, reading other slots' answers from ``slots``."""
        own = self._own_keys.get(id(owner))
        if own is None or own.dynamic:
            return None
        keys = set(own.keys)
        facts = self._facts.get(id(owner))
        if facts is not None:
            for name, context in facts.slots:
                if name is not None and slot is not None and name != slot:
                    continue
                found = self._local(owner, context, slots)
                if found is None:
                    return None
                keys.update(found)
        return frozenset(keys)

    def _solve(self, classes: Mapping[int, type[Component]]) -> dict[int, frozenset[str] | None]:
        """
        Find every component's keys by repeating the walk up until nothing changes.

        A component's keys are the `render(provides=...)` keys, plus, for each
        place that writes its tag, the keys provided there and the keys that
        reach the writing component. Templates may write each other in a
        cycle, so the sets grow until they stop changing. Once any place
        gives ``None`` (cannot tell), the component's answer stays ``None``.
        """
        # A dynamic `<c-component>` may render any component, so the keys
        # around it count for every component; work them out once.
        dynamic_keys: frozenset[str] | None = frozenset()
        for writer, context in self._dynamic:
            found = self._local(writer, context, self._slots)
            dynamic_keys = None if dynamic_keys is None or found is None else dynamic_keys | found
        local: dict[int, frozenset[str] | None] = {}
        writers: dict[int, list[type[Component]]] = {}
        for class_id, comp_cls in classes.items():
            keys: frozenset[str] | None = (
                None if self._render_keys is None or dynamic_keys is None else self._render_keys | dynamic_keys
            )
            # Python code places this component inside other content, such
            # as another component's slot, where Citry cannot see the keys.
            if _safe_class_text(comp_cls, "__name__") in self._placed:
                keys = None
            for writer, context in self._sites.get(class_id, ()):
                found = self._local(writer, context, self._slots)
                keys = None if keys is None or found is None else keys | found
            local[class_id] = keys
            writers[class_id] = [writer for writer, _context in (*self._sites.get(class_id, ()), *self._dynamic)]
        reach = dict(local)
        changed = True
        while changed:
            changed = False
            for class_id, keys in local.items():
                combined = keys
                for writer in writers[class_id]:
                    above = reach.get(id(writer), frozenset())
                    combined = None if combined is None or above is None else combined | above
                if combined != reach[class_id]:
                    reach[class_id] = combined
                    changed = True
        return reach

    def _local(
        self,
        writer: type[Component],
        context: _Context,
        slots: Mapping[tuple[int, str | None], frozenset[str] | None],
    ) -> frozenset[str] | None:
        """Return the keys provided at one place in ``writer``'s template, not counting what reaches ``writer``."""
        own = self._own_keys.get(id(writer))
        if own is None or own.dynamic:
            return None
        keys = set(own.keys)
        for frame in context:
            if frame.kind == "opaque":
                return None
            if frame.kind == "provide":
                if frame.key is None:
                    return None
                keys.add(frame.key)
                continue
            owner = self._by_name.get(frame.owner) if frame.owner is not None else None
            if owner is None:
                return None
            # Every slot a template fills is in `slots`; a missing one means "cannot tell".
            slot_keys = slots.get((id(owner), frame.slot))
            if slot_keys is None:
                return None
            keys.update(slot_keys)
        return frozenset(keys)


def _source_facts(engine: Citry, source: _Source) -> _TemplateFacts | None:
    """Parse one template source and collect its tags, slots and providers, or ``None`` when it cannot be read."""
    content = source.content
    if content is None:
        return None
    options, problem = _foreign_options(engine, source, content, template_kind="primary")
    if problem is not None:
        return None
    try:
        template = parse_template(content, options=options)
    except (SyntaxError, ValueError, RecursionError):
        return None
    facts = _TemplateFacts(builtin=all(consumer.node.builtin for consumer in source.consumers))

    def parse_nested(value: str) -> object | None:
        nested_source, _base = _nested_content(value)
        nested_options, nested_problem = _foreign_options(engine, source, nested_source, template_kind="nested")
        if nested_problem is not None:
            return None
        try:
            return parse_template(nested_source, options=nested_options)
        except (SyntaxError, ValueError, RecursionError):
            return None

    _walk(template, (), facts, parse_nested, owner=False)
    return None if facts.unreadable else facts


def _walk(
    template: object,
    context: _Context,
    facts: _TemplateFacts,
    parse_nested: Callable[[str], object | None],
    *,
    owner: str | None | Literal[False],
) -> None:
    """
    Record the tags, slots and ``<c-provide>`` keys in one template body.

    ``owner`` is the registered name of the component whose tag holds this
    body (``None`` when it is picked at render time), so content outside a
    ``<c-fill>`` is that component's default slot content. ``False`` means
    the body belongs to no component tag.
    """
    for element in getattr(template, "elements", ()):
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        tag = node.start_tag.name.content
        lower = tag.casefold()
        attrs = node.start_tag.attrs
        body = getattr(node, "body", None)
        if lower == "c-fill" and owner is not False:
            frame = _Frame("fill", owner=owner, slot=_name_attribute(attrs, "default"))
            _walk_attributes(attrs, (*context, frame), facts, parse_nested, component=False)
            if body is not None:
                _walk(body, (*context, frame), facts, parse_nested, owner=False)
            continue
        # Content directly in a component's body, outside any `<c-fill>`, is
        # its default slot content.
        here = context if owner is False else (*context, _Frame("fill", owner=owner, slot="default"))
        if lower in _STRUCTURAL_TAGS:
            if lower == "c-slot":
                # A `<c-slot>` written in another component's body passes this
                # component's slot content into that component's default slot.
                facts.slots.append((_name_attribute(attrs, "default"), here))
                _walk_attributes(attrs, here, facts, parse_nested, component=False)
                if body is not None:
                    # Fallback content renders in place of the slot.
                    _walk(body, here, facts, parse_nested, owner=False)
                continue
            _walk_attributes(attrs, context, facts, parse_nested, component=False)
            if body is not None:
                # `<c-if>` and `<c-for>` inside a component's body still hold its fills.
                _walk(body, context, facts, parse_nested, owner=owner)
            continue
        if lower == "c-provide":
            key = _static_attribute(attrs, "key")
            if key is not None:
                facts.provide_keys.add(key)
            _walk_attributes(attrs, here, facts, parse_nested, component=True)
            if body is not None:
                _walk(body, (*here, _Frame("provide", key=key)), facts, parse_nested, owner=False)
            continue
        if not lower.startswith("c-") or lower == "c-element":
            _walk_attributes(attrs, here, facts, parse_nested, component=False)
            if body is not None:
                _walk(body, here, facts, parse_nested, owner=False)
            continue
        target: str | None = lower[len("c-") :]
        if lower == "c-component":
            # Only `is="name"` without `c-bind` names the component before render.
            spread = any(attr.key.content == "c-bind" for attr in attrs)
            target = None if spread else _static_attribute(attrs, "is")
            target = target.lower() if target is not None else None
            if target is None and facts.builtin:
                _walk_attributes(attrs, here, facts, parse_nested, component=False)
                if body is not None:
                    _walk(body, here, facts, parse_nested, owner=False)
                continue
        facts.sites.append((target, here))
        _walk_attributes(attrs, here, facts, parse_nested, component=True)
        if body is not None:
            _walk(body, here, facts, parse_nested, owner=target)


def _walk_attributes(
    attrs: Any,
    context: _Context,
    facts: _TemplateFacts,
    parse_nested: Callable[[str], object | None],
    *,
    component: bool,
) -> None:
    """Walk markup written inside attribute values, such as ``c-footer="<>...</>"``."""
    for attr in attrs:
        inner = attr.inner_value
        if attr.kind != HtmlAttrKind.Template or inner is None:
            continue
        nested = parse_nested(inner.content)
        if nested is None:
            facts.unreadable = True
            continue
        # A component receives the rendered markup as an input and may place
        # it anywhere, so the keys around it are unknown.
        inner_context = (*context, _Frame("opaque")) if component else context
        _walk(nested, inner_context, facts, parse_nested, owner=False)


def _static_attribute(attrs: Any, name: str) -> str | None:
    """Return a plain attribute's literal value, or ``None`` when it is missing or written as an expression."""
    for attr in attrs:
        if attr.key.content == name and attr.kind == HtmlAttrKind.Static and attr.inner_value is not None:
            if attr.foreign_parts:
                return None
            return attr.inner_value.content
    return None


def _name_attribute(attrs: Any, default: str) -> str | None:
    """Return a ``<c-slot>`` or ``<c-fill>`` name: ``default`` when absent, ``None`` when written as ``c-name``."""
    if any(attr.key.content == "c-name" for attr in attrs):
        return None
    value = _static_attribute(attrs, "name")
    return default if value is None else value


class _SourceReader:
    """Read component classes' Python source once per file and find their ``provide()`` keys."""

    def __init__(self) -> None:
        self._trees: dict[Path, ast.Module | None] = {}

    def class_node(self, cls: type) -> ast.ClassDef | None:
        """Return the class statement that defines ``cls``, or ``None`` when its source cannot be read."""
        file = _loaded_python_file(cls)
        qualname = _safe_class_text(cls, "__qualname__")
        if file is None or qualname is None:
            return None
        tree = self._tree(file)
        return None if tree is None else python_class_node(tree, qualname)

    def component_keys(self, comp_cls: type[Component]) -> _ClassKeys | None:
        """
        Return the ``provide()`` keys of a component's class, its base classes and its mixins.

        ``None`` means some of that code cannot be read, so the component may
        provide any key.
        """
        keys: set[str] = set()
        dynamic = False
        for owner in _code_classes(comp_cls):
            node = self.class_node(owner)
            if node is None:
                # Without the class statement, its compiled methods still
                # show whether it calls `provide()` at all.
                if _compiled_methods_call(owner, "provide"):
                    return None
                continue
            module = sys.modules.get(_safe_class_text(owner, "__module__") or "")
            found, found_dynamic = provide_call_keys(node, vars(module) if module is not None else {})
            keys.update(found)
            dynamic = dynamic or found_dynamic
        return _ClassKeys(frozenset(keys), dynamic)

    def _tree(self, file: Path) -> ast.Module | None:
        if file not in self._trees:
            try:
                with tokenize.open(file) as stream:
                    self._trees[file] = ast.parse(stream.read())
            except (OSError, SyntaxError, UnicodeError, ValueError, RecursionError):
                self._trees[file] = None
        return self._trees[file]


def _compiled_methods_call(cls: type, name: str) -> bool:
    """Return whether any function stored on the class mentions the attribute ``name``, such as ``self.provide``."""
    pending: list[CodeType] = []
    for value in _static_class_dict(cls).values():
        # `staticmethod` and `classmethod` keep the function under `__func__`.
        function = getattr(value, "__func__", value)
        if isinstance(function, FunctionType):
            pending.append(function.__code__)
    while pending:
        code = pending.pop()
        if name in code.co_names:
            return True
        # Nested functions and comprehensions are separate code objects.
        pending.extend(constant for constant in code.co_consts if isinstance(constant, CodeType))
    return False


def python_class_node(tree: ast.Module, qualname: str) -> ast.ClassDef | None:
    """Find the class statement named by ``qualname``, through the functions and classes that hold it."""
    body: list[ast.stmt] = tree.body
    current: ast.stmt | None = None
    for part in (item for item in qualname.split(".") if item != "<locals>"):
        matches = [
            statement
            for statement in body
            if isinstance(statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and statement.name == part
        ]
        # Two statements with one name: Citry cannot tell which one Python kept.
        if len(matches) != 1:
            return None
        current = matches[0]
        body = current.body
    return current if isinstance(current, ast.ClassDef) else None


def provide_call_keys(node: ast.ClassDef, module_globals: Mapping[str, object]) -> tuple[frozenset[str], bool]:
    """
    Return the keys a class's own methods pass to ``.provide()``, and whether some key is an expression.

    A key written as a name that the module binds to a string, such as
    ``FIELD_CONTEXT_KEY``, counts as that string.
    """
    keys: set[str] = set()
    dynamic = False
    for call in method_calls(node, "provide"):
        if not call.args or isinstance(call.args[0], ast.Starred):
            dynamic = True
            continue
        argument = call.args[0]
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
            keys.add(argument.value)
            continue
        value = module_globals.get(argument.id) if isinstance(argument, ast.Name) else None
        if isinstance(value, str):
            keys.add(value)
        else:
            dynamic = True
    return frozenset(keys), dynamic


def method_calls(node: ast.ClassDef, method: str) -> Iterator[ast.Call]:
    """Yield each ``<something>.<method>(...)`` call in the class's own methods, skipping nested classes."""
    stack: list[ast.AST] = [
        statement for statement in node.body if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    while stack:
        current = stack.pop()
        if isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute) and current.func.attr == method:
            yield current
        stack.extend(child for child in ast.iter_child_nodes(current) if not isinstance(child, ast.ClassDef))


def _read_project_python(
    classes: list[type[Component]], workspace: Path | None
) -> tuple[frozenset[str], frozenset[str]] | None:
    """
    Read the project's Python files for ``render(provides=...)`` keys and components Python places.

    Returns the literal ``provides`` keys and the names of the component
    classes that Python code places inside other content. The files are
    those under ``workspace``, outside hidden folders, virtual environments
    and installed packages, and the modules that define registered
    components. ``None`` means the folder holds too many files to read, so
    Citry cannot tell what the project passes.
    """
    files: set[Path] = set()
    if workspace is not None:
        for count, file in enumerate(_project_python_files(workspace)):
            if count >= _MAX_PROJECT_FILES:
                return None
            files.add(file)
    for comp_cls in classes:
        module_file = _loaded_python_file(comp_cls)
        if module_file is not None:
            files.add(module_file)
    names = _class_names(classes)
    # Parsing is the slow part, so only a file that passes `provides` or
    # calls a component class, such as `Card(`, is parsed.
    calls = b"|".join(re.escape(name.encode()) for name in sorted(names))
    matters = re.compile(rb"provides|\b(?:" + calls + rb")\s*\(" if names else rb"provides")
    keys: set[str] = set()
    placed: set[str] = set()
    modules = _ModuleConstants(workspace)
    for file in sorted(files):
        try:
            raw = file.read_bytes()
        except OSError:
            continue
        if matters.search(raw) is None:
            continue
        try:
            tree = ast.parse(raw)
        except (SyntaxError, ValueError, RecursionError):
            continue
        keys.update(provides_argument_keys(tree, modules=modules))
        # A test may place a component anywhere to try it out; that says
        # nothing about where the app renders it.
        if not _is_test_file(file):
            visitor = _PythonPlacement(names)
            visitor.visit(tree)
            placed.update(visitor.placed)
    return frozenset(keys), frozenset(placed)


def _installed(file: Path) -> bool:
    return any(part in {"site-packages", "dist-packages"} for part in file.parts)


def _is_test_file(file: Path) -> bool:
    name = file.name
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or name == "conftest.py"
        or any(part in {"tests", "test"} for part in file.parts[:-1])
    )


def _class_names(classes: list[type[Component]]) -> set[str]:
    return {name for comp_cls in classes if (name := _safe_class_text(comp_cls, "__name__")) is not None}


class _ModuleConstants:
    """
    Find the string constants of a module the project imports, by its dotted name.

    The app may never import the file that renders a page with
    ``render(provides={BOARD_KEY: ...})``, so the module that defines
    ``BOARD_KEY`` may not be loaded either. Such a module is read from the
    project folder instead.
    """

    def __init__(self, workspace: Path | None) -> None:
        self._workspace = workspace
        self._read: dict[str, dict[str, str]] = {}

    def get(self, module: str) -> Mapping[str, object]:
        """Return the module's top-level names, from the loaded module or from its file in the project."""
        loaded = sys.modules.get(module)
        if loaded is not None:
            return vars(loaded)
        if module not in self._read:
            self._read[module] = self._from_file(module)
        return self._read[module]

    def _from_file(self, module: str) -> dict[str, str]:
        if self._workspace is None:
            return {}
        base = self._workspace.joinpath(*module.split("."))
        for file in (base.with_suffix(".py"), base / "__init__.py"):
            try:
                tree = ast.parse(file.read_bytes())
            except (OSError, SyntaxError, ValueError, RecursionError):
                continue
            return _module_names(tree, None)[0]
        return {}


def provides_argument_keys(tree: ast.Module, *, modules: _ModuleConstants | None = None) -> Iterator[str]:
    """
    Yield the literal keys of each ``provides={...}`` or ``provides=dict(...)`` keyword argument.

    A key written as a module-level string constant counts as that string,
    also when the module imports it from a module the app has loaded or
    the project folder holds, as in ``from app.keys import BOARD_KEY`` or
    ``keys.BOARD_KEY``. A ``provides`` value built elsewhere, such as a
    variable, adds nothing.
    """
    constants, imported = _module_names(tree, modules)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg != "provides":
                continue
            value = keyword.value
            if isinstance(value, ast.Dict):
                for key in value.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        yield key.value
                    elif isinstance(key, ast.Name) and key.id in constants:
                        yield constants[key.id]
                    elif (
                        isinstance(key, ast.Attribute)
                        and isinstance(key.value, ast.Name)
                        and isinstance(found := imported.get(key.value.id, {}).get(key.attr), str)
                    ):
                        yield found
            elif isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "dict":
                yield from (item.arg for item in value.keywords if item.arg is not None)


def _module_names(
    tree: ast.Module, modules: _ModuleConstants | None
) -> tuple[dict[str, str], dict[str, Mapping[str, object]]]:
    """
    Return the string constants a module's top level binds, and the modules it imports by name.

    A constant assigned in the module, such as ``BOARD_KEY = "board"``, is
    read from the source. One imported with ``from ... import`` is read from
    the imported module, through ``modules``.
    """
    constants: dict[str, str] = {}
    imported: dict[str, Mapping[str, object]] = {}
    for statement in tree.body:
        if isinstance(statement, ast.ImportFrom) and statement.level == 0 and statement.module and modules:
            names = modules.get(statement.module)
            for alias in statement.names:
                value = names.get(alias.name)
                if isinstance(value, str):
                    constants[alias.asname or alias.name] = value
            continue
        if isinstance(statement, ast.Import) and modules:
            for alias in statement.names:
                # `import app.keys` binds `app`; only `import app.keys as keys` names the module itself.
                if alias.asname is not None or "." not in alias.name:
                    imported[alias.asname or alias.name] = modules.get(alias.name)
            continue
        target: ast.expr | None = None
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
        elif isinstance(statement, ast.AnnAssign):
            target = statement.target
        value = getattr(statement, "value", None)
        if isinstance(target, ast.Name) and isinstance(value, ast.Constant) and isinstance(value.value, str):
            constants[target.id] = value.value
    return constants, imported


class _PythonPlacement(ast.NodeVisitor):
    """
    Find components that Python code places inside other content.

    A component built inside a component class's methods, such as a value
    ``template_data()`` returns for ``{{ widget }}``, or passed to another
    component, such as ``Layout(slots={"default": Widget()})``, renders
    under keys Citry cannot see. A component built only to render a page,
    such as ``str(BoardPage(...))``, is not placed anywhere.
    """

    def __init__(self, names: set[str]) -> None:
        self.names = names
        self.placed: set[str] = set()
        # Variables holding a component, such as `card = Card()`, so passing
        # the variable to another component counts too.
        self._variables: dict[str, str] = {}
        self._in_component_class = 0
        self._in_component_arguments = 0

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        inside = node.name in self.names
        self._in_component_class += inside
        self.generic_visit(node)
        self._in_component_class -= inside

    def visit_Assign(self, node: ast.Assign) -> None:
        name = self._built_component(node.value)
        if name is not None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self._variables[target.id] = name
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if self._in_component_arguments and node.id in self._variables:
            self.placed.add(self._variables[node.id])

    def visit_Call(self, node: ast.Call) -> None:
        name = self._built_component(node)
        if name is not None and (self._in_component_class or self._in_component_arguments):
            self.placed.add(name)
        # Visit the called expression on its own, so the page in
        # `Page().render()` stays a page Python renders at the top.
        self.visit(node.func)
        for argument in node.args:
            self._visit_argument(argument, nested=name is not None)
        for keyword in node.keywords:
            self._visit_argument(keyword.value, nested=name is not None or keyword.arg == "slots")

    def _built_component(self, node: ast.expr) -> str | None:
        """Return the component class name a call such as ``Card(...)`` or ``ui.Card(...)`` builds."""
        if not isinstance(node, ast.Call):
            return None
        func = node.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
        return name if name in self.names else None

    def _visit_argument(self, value: ast.expr, *, nested: bool) -> None:
        self._in_component_arguments += nested
        self.visit(value)
        self._in_component_arguments -= nested


# Folders that hold installed packages or tool caches rather than the project's own code.
_SKIPPED_FOLDERS = frozenset({"node_modules", "site-packages", "dist-packages", "__pycache__"})


def _project_python_files(workspace: Path) -> Iterator[Path]:
    """Yield the ``.py`` files under ``workspace``, skipping hidden folders, virtual environments and packages."""
    for directory, folders, files in os.walk(workspace):
        current = Path(directory)
        folders[:] = sorted(
            folder
            for folder in folders
            if not folder.startswith(".")
            and folder not in _SKIPPED_FOLDERS
            # A virtual environment holds `pyvenv.cfg`, a conda environment `conda-meta`.
            and not (current / folder / "pyvenv.cfg").is_file()
            and not (current / folder / "conda-meta").is_dir()
        )
        for name in sorted(files):
            if name.endswith(".py"):
                yield current / name


__all__ = [
    "InjectKeyScope",
    "engine_inject_keys",
    "inject_key_scopes",
    "method_calls",
    "provide_call_keys",
    "provides_argument_keys",
    "python_class_node",
]
