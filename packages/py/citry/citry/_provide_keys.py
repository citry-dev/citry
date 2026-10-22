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
c-key="...">`` or a dynamic ``<c-component>``, the answer is "cannot tell"
(``None``), and the rule reports nothing for that component. ``citry check``
and the editor's app worker both call `inject_key_scopes`.
"""

from __future__ import annotations

import ast
import os
import sys
import tokenize
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from citry._class_introspection import _safe_class_import_path, _safe_class_text, _static_class_dict, _static_class_mro
from citry._component_graph import _build_node, _collect_sources, _foreign_options, _nested_content
from citry._component_introspection import _group_registrations, _loaded_python_file
from citry.component import Component
from citry_core.template_parser import RESERVED_TAG_NAMES, HtmlAttrKind, TemplateElement, parse_template

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

    from citry._component_graph import _Source
    from citry.citry import Citry


@dataclass(frozen=True, slots=True)
class InjectKeyScope:
    """
    The keys that can reach one class whose methods may call ``self.inject()``.

    Attributes:
        file: The Python file that defines the class.
        qualname: The class's qualified name in that file.
        name: The class name, as messages show it.
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
    """What one template says about providing keys, read once per physical template."""

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


def inject_key_scopes(
    engine: Citry,
    registrations: Mapping[str, type[Component]],
    workspace: Path | None,
) -> tuple[InjectKeyScope, ...] | None:
    """
    Answer which keys can reach each class that registered components run.

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
    reader = _SourceReader()
    own_keys = {id(comp_cls): reader.component_keys(comp_cls) for comp_cls in classes}
    render_keys = _render_provides_keys(classes, workspace)
    resolver = _Reach(by_name, facts_by_class, own_keys, render_keys)

    # Every key the app provides anywhere, for a component no template renders.
    # A source Citry cannot read may provide any key, so nothing is reported then.
    everywhere: frozenset[str] | None = None
    if all(keys is not None for keys in own_keys.values()):
        everywhere = render_keys.union(
            *(facts.provide_keys for facts in facts_by_class.values()),
            *(keys.keys for keys in own_keys.values() if keys is not None),
        )

    # The code that calls `inject()` may live on a base class, so each class
    # in a registered component's MRO collects that component's answer.
    scopes: dict[int, tuple[type, list[type[Component]]]] = {}
    for comp_cls in classes:
        if engine._is_builtin_component(comp_cls):
            continue
        for owner in _component_classes(comp_cls):
            scopes.setdefault(id(owner), (owner, []))[1].append(comp_cls)

    found: list[InjectKeyScope] = []
    for owner, components in scopes.values():
        file = _loaded_python_file(owner)
        qualname = _safe_class_text(owner, "__qualname__")
        name = _safe_class_text(owner, "__name__")
        if file is None or qualname is None or name is None:
            continue
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


def _component_classes(comp_cls: type[Component]) -> Iterator[type]:
    """Yield the component class and each component base whose methods it runs, without `Component` itself."""
    for candidate in _static_class_mro(comp_cls):
        if candidate is Component or not issubclass(candidate, Component):
            continue
        yield candidate


class _Reach:
    """Combine the template facts and ``provide()`` keys into the keys that reach each component."""

    def __init__(
        self,
        by_name: Mapping[str, type[Component]],
        facts_by_class: Mapping[int, _TemplateFacts],
        own_keys: Mapping[int, _ClassKeys | None],
        render_keys: frozenset[str],
    ) -> None:
        self._by_name = by_name
        self._facts = facts_by_class
        self._own_keys = own_keys
        self._render_keys = render_keys
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
        self._reach = self._solve(classes)

    def reaching(
        self, component: type[Component], everywhere: frozenset[str] | None
    ) -> tuple[frozenset[str] | None, bool]:
        """
        Return the keys that reach ``component``, and whether that is the whole-app set.

        A component no template writes falls back to every key the app
        provides, because Citry cannot see where Python renders it.
        """
        if id(component) not in self._sites:
            return everywhere, True
        return self._reach.get(id(component)), False

    def _solve(self, classes: Mapping[int, type[Component]]) -> dict[int, frozenset[str] | None]:
        """
        Find every component's keys by repeating the walk up until nothing changes.

        A component's keys are the `render(provides=...)` keys, plus, for each
        place that writes its tag, the keys provided there and the keys that
        reach the writing component. Templates may write each other in a
        cycle, so the sets grow until they stop changing; ``None`` (cannot
        tell) absorbs everything.
        """
        local: dict[int, frozenset[str] | None] = {}
        writers: dict[int, list[type[Component]]] = {}
        for class_id in classes:
            places = [*self._sites.get(class_id, ()), *self._dynamic]
            keys: frozenset[str] | None = self._render_keys
            for writer, context in places:
                found = self._local(writer, context, ())
                keys = None if keys is None or found is None else keys | found
            local[class_id] = keys
            writers[class_id] = [writer for writer, _context in places]
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
        visiting: tuple[tuple[int, str | None], ...],
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
            slot_keys = self._slot_keys(owner, frame.slot, visiting)
            if slot_keys is None:
                return None
            keys.update(slot_keys)
        return frozenset(keys)

    def _slot_keys(
        self,
        owner: type[Component],
        slot: str | None,
        visiting: tuple[tuple[int, str | None], ...],
    ) -> frozenset[str] | None:
        """
        Return the keys the component ``owner`` provides to the content of its slot ``slot``.

        Those are its own ``provide()`` keys and the keys provided around each
        matching ``<c-slot>`` in its template. A component that renders the
        slot from Python, with no matching ``<c-slot>``, gives only its own keys.
        """
        marker = (id(owner), slot)
        # A slot passed back into the same component adds nothing new.
        if marker in visiting:
            return frozenset()
        own = self._own_keys.get(id(owner))
        if own is None or own.dynamic:
            return None
        keys = set(own.keys)
        facts = self._facts.get(id(owner))
        if facts is not None:
            for name, context in facts.slots:
                if name is not None and slot is not None and name != slot:
                    continue
                found = self._local(owner, context, (*visiting, marker))
                if found is None:
                    return None
                keys.update(found)
        return frozenset(keys)


def _source_facts(engine: Citry, source: _Source) -> _TemplateFacts | None:
    """Parse one physical template and collect its tags, slots and providers, or ``None`` when it cannot be read."""
    content = source.content
    if content is None:
        return None
    options, problem = _foreign_options(engine, source, content, template_kind="primary")
    if problem is not None:
        return None
    try:
        template = parse_template(content, options=options)
    except (SyntaxError, ValueError):
        return None
    facts = _TemplateFacts(builtin=all(consumer.node.builtin for consumer in source.consumers))

    def parse_nested(value: str) -> object | None:
        nested_source, _base = _nested_content(value)
        nested_options, nested_problem = _foreign_options(engine, source, nested_source, template_kind="nested")
        if nested_problem is not None:
            return None
        try:
            return parse_template(nested_source, options=nested_options)
        except (SyntaxError, ValueError):
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
        if lower in _STRUCTURAL_TAGS:
            if lower == "c-slot":
                facts.slots.append((_name_attribute(attrs, "default"), context))
            _walk_attributes(attrs, context, facts, parse_nested, component=False)
            if body is not None:
                # `<c-if>` and `<c-for>` inside a component's body still hold
                # its fills; a `<c-slot>` body is fallback content in place.
                inner_owner = owner if lower != "c-slot" else False
                _walk(body, context, facts, parse_nested, owner=inner_owner)
            continue
        # Content directly in a component's body, outside any `<c-fill>`, is
        # its default slot content.
        here = context if owner is False else (*context, _Frame("fill", owner=owner, slot="default"))
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
        Return the ``provide()`` keys of a component's class and its component bases.

        ``None`` means some of that code cannot be read, so the component may
        provide any key.
        """
        keys: set[str] = set()
        dynamic = False
        for owner in _component_classes(comp_cls):
            node = self.class_node(owner)
            if node is None:
                return None
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
            except (OSError, SyntaxError, UnicodeError, ValueError):
                self._trees[file] = None
        return self._trees[file]


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


def _render_provides_keys(classes: list[type[Component]], workspace: Path | None) -> frozenset[str]:
    """
    Collect the literal keys of every ``provides=`` argument in the project's Python files.

    The files are those under ``workspace``, outside virtual environments and
    installed packages, and the modules that define registered components.
    A ``provides`` value built elsewhere, such as a variable, adds nothing.
    """
    files: set[Path] = set()
    if workspace is not None:
        files.update(_project_python_files(workspace))
    for comp_cls in classes:
        file = _loaded_python_file(comp_cls)
        if file is not None:
            files.add(file)
    keys: set[str] = set()
    for file in sorted(files):
        try:
            raw = file.read_bytes()
        except OSError:
            continue
        # Most files never mention it, and parsing every file is the slow part.
        if b"provides" not in raw:
            continue
        try:
            tree = ast.parse(raw)
        except (SyntaxError, ValueError):
            continue
        keys.update(provides_argument_keys(tree))
    return frozenset(keys)


def provides_argument_keys(tree: ast.AST) -> Iterator[str]:
    """Yield the literal keys of each ``provides={...}`` or ``provides=dict(...)`` keyword argument."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg != "provides":
                continue
            value = keyword.value
            if isinstance(value, ast.Dict):
                yield from (
                    key.value for key in value.keys if isinstance(key, ast.Constant) and isinstance(key.value, str)
                )
            elif isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "dict":
                yield from (item.arg for item in value.keywords if item.arg is not None)


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
            and not (current / folder / "pyvenv.cfg").is_file()
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
