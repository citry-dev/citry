"""Frozen values for authored component-template dependency graphs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from citry.analysis import LspPosition, LspRange
from citry.component_registry import NotRegistered

_GRAPH_SCHEMA_VERSION = 1
_PATH_TYPE = type(Path())
_PROBLEM_CODES = {
    "foreign-source-controls-body",
    "nested-template-syntax",
    "template-declaration",
    "template-file-not-found",
    "template-file-unreadable",
    "template-language-unsupported",
    "template-namespace-unavailable",
    "template-syntax",
    "template-value-invalid",
}


def _require_text(value: object, field_name: str) -> None:
    if type(value) is not str or not value:
        msg = f"{field_name} must be a non-empty string."
        raise ValueError(msg)
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as err:
        msg = f"{field_name} must not contain unpaired Unicode surrogate code points."
        raise ValueError(msg) from err


def _require_tuple(value: object, field_name: str) -> None:
    if type(value) is not tuple:
        msg = f"{field_name} must be a tuple."
        raise TypeError(msg)


def _require_path(value: Path | None, field_name: str) -> None:
    if value is None:
        return
    if type(value) is not _PATH_TYPE or not value.is_absolute():
        msg = f"{field_name} must be an absolute pathlib.Path or None."
        raise ValueError(msg)


def _node_key(node: ComponentGraphNode) -> tuple[str, str, str]:
    return node.name, node.class_id, node.definition_id


def _location_key(location: ComponentGraphLocation) -> tuple[object, ...]:
    return (
        location.origin,
        location.source_kind,
        location.declared_on or "",
        location.declaration_file.as_posix() if location.declaration_file is not None else "",
        location.template_file.as_posix() if location.template_file is not None else "",
        location.start_index,
        location.end_index,
        location.source_range.start.line,
        location.source_range.start.character,
        location.source_range.end.line,
        location.source_range.end.character,
    )


def _reference_key(reference: ComponentGraphReference) -> tuple[object, ...]:
    return (
        reference.source_definition_id,
        *_location_key(reference.location),
        reference.target_definition_id,
        reference.registered_name,
        reference.authored_name,
        reference.syntax,
    )


def _unresolved_key(reference: UnresolvedComponentReference) -> tuple[object, ...]:
    return (
        reference.source_definition_id,
        *_location_key(reference.location),
        reference.reason,
        reference.authored_name or "",
        reference.syntax,
    )


def _problem_key(problem: ComponentGraphProblem) -> tuple[object, ...]:
    return (
        problem.component_definition_ids,
        problem.origin,
        problem.code,
        problem.message,
        *((0,) if problem.location is None else (1, *_location_key(problem.location))),
    )


@dataclass(frozen=True, slots=True)
class ComponentGraphNode:
    """
    Identify one registered component definition in an authored dependency graph.

    Use ``name`` in templates and graph queries. ``aliases`` contains the other
    registered spellings that resolve to the same component.

    Attributes:
        class_id: Stable identity for the component's Python route.
        engine_id: Runtime identity of the Citry instance that built the graph.
        definition_id: Runtime identity of this exact class generation.
        name: Canonical registered component name.
        aliases: Other registered names for the same component.
        builtin: Whether Citry created this framework component.

    Example:
        ```python
        graph = app.inspect_component_graph()
        card = graph.component("card")
        print(card.name)
        ```

    """

    class_id: str
    engine_id: str
    definition_id: str
    name: str
    aliases: tuple[str, ...]
    builtin: bool

    def __post_init__(self) -> None:
        for field_name in ("class_id", "engine_id", "definition_id", "name"):
            _require_text(getattr(self, field_name), f"ComponentGraphNode.{field_name}")
        if self.name != self.name.lower():
            msg = "ComponentGraphNode.name must be a normalized lowercase registry name."
            raise ValueError(msg)
        _require_tuple(self.aliases, "ComponentGraphNode.aliases")
        for alias in self.aliases:
            _require_text(alias, "ComponentGraphNode.aliases entry")
            if alias != alias.lower():
                msg = "ComponentGraphNode.aliases must contain normalized lowercase registry names."
                raise ValueError(msg)
        if tuple(sorted(set(self.aliases))) != self.aliases or self.name in self.aliases:
            msg = "ComponentGraphNode.aliases must be unique, sorted, and exclude the primary name."
            raise ValueError(msg)
        if type(self.builtin) is not bool:
            msg = "ComponentGraphNode.builtin must be a bool."
            raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class ComponentGraphLocation:
    """
    Point to one component reference in an authored primary template.

    ``start_index`` and ``end_index`` are half-open UTF-8 byte offsets in the
    normalized root template. ``source_range`` carries the same span as
    zero-based UTF-16 positions for editors.

    Attributes:
        origin: Human-readable template origin.
        source_kind: Whether the template is inline or file-backed.
        declared_on: Import path of the class that declared the template.
        declaration_file: Python file containing that declaration, when known.
        template_file: Resolved file-backed template path, when applicable.
        start_index: Inclusive UTF-8 byte offset in the root template.
        end_index: Exclusive UTF-8 byte offset in the root template.
        source_range: Equivalent zero-based UTF-16 editor range.

    """

    origin: str
    source_kind: Literal["inline", "file"]
    declared_on: str | None
    declaration_file: Path | None
    template_file: Path | None
    start_index: int
    end_index: int
    source_range: LspRange

    def __post_init__(self) -> None:
        _require_text(self.origin, "ComponentGraphLocation.origin")
        if self.source_kind not in {"inline", "file"}:
            msg = f"Unknown component graph source kind: {self.source_kind!r}."
            raise ValueError(msg)
        if self.declared_on is not None:
            _require_text(self.declared_on, "ComponentGraphLocation.declared_on")
        _require_path(self.declaration_file, "ComponentGraphLocation.declaration_file")
        _require_path(self.template_file, "ComponentGraphLocation.template_file")
        if self.source_kind == "inline" and self.template_file is not None:
            msg = "An inline ComponentGraphLocation must not have a template_file."
            raise ValueError(msg)
        if self.source_kind == "file" and self.template_file is None:
            msg = "A file ComponentGraphLocation requires a template_file."
            raise ValueError(msg)
        if type(self.start_index) is not int or type(self.end_index) is not int:
            msg = "ComponentGraphLocation byte offsets must be integers."
            raise TypeError(msg)
        if self.start_index < 0 or self.end_index < self.start_index:
            msg = "ComponentGraphLocation byte offsets must form a non-negative half-open range."
            raise ValueError(msg)
        if type(self.source_range) is not LspRange:
            msg = "ComponentGraphLocation.source_range must be an LspRange."
            raise TypeError(msg)
        for position in (self.source_range.start, self.source_range.end):
            if type(position) is not LspPosition or position.line < 0 or position.character < 0:
                msg = "ComponentGraphLocation.source_range must contain non-negative LspPosition values."
                raise ValueError(msg)
        start = (self.source_range.start.line, self.source_range.start.character)
        end = (self.source_range.end.line, self.source_range.end.character)
        if end < start:
            msg = "ComponentGraphLocation.source_range must be a forward half-open range."
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ComponentGraphReference:
    """
    Describe one authored component reference that resolves to a registered target.

    Repeated invocations remain separate records. Use
    [`ComponentGraph.dependencies`][citry.ComponentGraph.dependencies] when
    you need unique target components.

    Attributes:
        source_definition_id: Exact component definition that owns the source.
        target_definition_id: Exact registered target definition.
        registered_name: Normalized registry name that matched the reference.
        authored_name: Target name exactly as written by the author.
        syntax: Whether the target came from a tag or static selector.
        location: Authored source occurrence.

    """

    source_definition_id: str
    target_definition_id: str
    registered_name: str
    authored_name: str
    syntax: Literal["tag", "static-selector"]
    location: ComponentGraphLocation

    def __post_init__(self) -> None:
        for field_name in ("source_definition_id", "target_definition_id", "registered_name", "authored_name"):
            _require_text(getattr(self, field_name), f"ComponentGraphReference.{field_name}")
        if self.registered_name != self.registered_name.lower():
            msg = "ComponentGraphReference.registered_name must be normalized lowercase."
            raise ValueError(msg)
        if self.syntax not in {"tag", "static-selector"}:
            msg = f"Unknown resolved component reference syntax: {self.syntax!r}."
            raise ValueError(msg)
        if type(self.location) is not ComponentGraphLocation:
            msg = "ComponentGraphReference.location must be a ComponentGraphLocation."
            raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class UnresolvedComponentReference:
    """
    Describe an authored component reference whose target is not statically known.

    ``unknown-component`` retains the written name. ``dynamic-target`` uses
    ``authored_name=None`` because the runtime expression or spread chooses it.

    Attributes:
        source_definition_id: Exact component definition that owns the source.
        authored_name: Written target name, or ``None`` for a dynamic target.
        reason: Whether the name is unknown or the target is dynamic.
        syntax: Authored tag or selector form.
        location: Authored source occurrence.

    """

    source_definition_id: str
    authored_name: str | None
    reason: Literal["unknown-component", "dynamic-target"]
    syntax: Literal["tag", "static-selector", "dynamic-selector"]
    location: ComponentGraphLocation

    def __post_init__(self) -> None:
        _require_text(self.source_definition_id, "UnresolvedComponentReference.source_definition_id")
        if self.authored_name is not None:
            _require_text(self.authored_name, "UnresolvedComponentReference.authored_name")
        if self.reason not in {"unknown-component", "dynamic-target"}:
            msg = f"Unknown unresolved component reference reason: {self.reason!r}."
            raise ValueError(msg)
        if self.syntax not in {"tag", "static-selector", "dynamic-selector"}:
            msg = f"Unknown unresolved component reference syntax: {self.syntax!r}."
            raise ValueError(msg)
        if self.reason == "unknown-component" and self.authored_name is None:
            msg = "An unknown component reference requires its authored name."
            raise ValueError(msg)
        if self.reason == "dynamic-target" and self.authored_name is not None:
            msg = "A dynamic component reference must not claim a static authored target."
            raise ValueError(msg)
        if self.reason == "unknown-component" and self.syntax == "dynamic-selector":
            msg = "An unknown component reference must use tag or static-selector syntax."
            raise ValueError(msg)
        if self.reason == "dynamic-target" and self.syntax != "dynamic-selector":
            msg = "A dynamic component reference must use dynamic-selector syntax."
            raise ValueError(msg)
        if type(self.location) is not ComponentGraphLocation:
            msg = "UnresolvedComponentReference.location must be a ComponentGraphLocation."
            raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class ComponentGraphProblem:
    """
    Report why Citry could not inspect part of an authored template source.

    Graph construction continues after a problem, so callers can use references
    from unaffected components. ``component_definition_ids`` identifies every
    selected component that consumes the affected physical source.

    Attributes:
        component_definition_ids: Sorted exact definitions affected.
        code: Stable graph-local problem category.
        message: Human-readable explanation.
        origin: Source or declaration that failed.
        location: Authored range when the failure supplied one.

    """

    component_definition_ids: tuple[str, ...]
    code: str
    message: str
    origin: str
    location: ComponentGraphLocation | None = None

    def __post_init__(self) -> None:
        _require_tuple(self.component_definition_ids, "ComponentGraphProblem.component_definition_ids")
        if not self.component_definition_ids or any(
            type(definition_id) is not str or not definition_id for definition_id in self.component_definition_ids
        ):
            msg = "ComponentGraphProblem.component_definition_ids must contain non-empty strings."
            raise ValueError(msg)
        if tuple(sorted(set(self.component_definition_ids))) != self.component_definition_ids:
            msg = "ComponentGraphProblem.component_definition_ids must be unique and sorted."
            raise ValueError(msg)
        if self.code not in _PROBLEM_CODES:
            msg = f"Unknown component graph problem code: {self.code!r}."
            raise ValueError(msg)
        _require_text(self.message, "ComponentGraphProblem.message")
        _require_text(self.origin, "ComponentGraphProblem.origin")
        if self.location is not None and type(self.location) is not ComponentGraphLocation:
            msg = "ComponentGraphProblem.location must be a ComponentGraphLocation or None."
            raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class ComponentGraph:
    """
    Hold a versioned snapshot of authored dependencies between registered components.

    Build a graph with
    [`Citry.inspect_component_graph()`][citry.Citry.inspect_component_graph].
    Query direct dependencies or reverse references by primary name, alias, or
    a node returned from the same graph.

    Attributes:
        schema_version: Graph JSON schema version.
        citry_version: Installed Citry package version used to build the graph.
        engine_id: Runtime identity of the inspected Citry instance.
        nodes: Registered component definitions in canonical order.
        references: Resolved authored occurrences in canonical source order.
        unresolved: Unknown and dynamic authored occurrences.
        problems: Sources that could not be inspected completely.

    Example:
        ```python
        graph = app.inspect_component_graph()

        for dependency in graph.dependencies("page"):
            print(dependency.name)

        for dependent in graph.dependents("button"):
            print(dependent.name)
        ```

    """

    schema_version: int
    citry_version: str
    engine_id: str
    nodes: tuple[ComponentGraphNode, ...]
    references: tuple[ComponentGraphReference, ...]
    unresolved: tuple[UnresolvedComponentReference, ...]
    problems: tuple[ComponentGraphProblem, ...]

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != _GRAPH_SCHEMA_VERSION:
            msg = f"ComponentGraph.schema_version must be {_GRAPH_SCHEMA_VERSION}."
            raise ValueError(msg)
        _require_text(self.citry_version, "ComponentGraph.citry_version")
        _require_text(self.engine_id, "ComponentGraph.engine_id")
        for field_name in ("nodes", "references", "unresolved", "problems"):
            _require_tuple(getattr(self, field_name), f"ComponentGraph.{field_name}")
        if any(type(node) is not ComponentGraphNode for node in self.nodes):
            msg = "ComponentGraph.nodes must contain ComponentGraphNode values."
            raise TypeError(msg)
        if any(node.engine_id != self.engine_id for node in self.nodes):
            msg = "Every ComponentGraphNode must belong to the graph's engine."
            raise ValueError(msg)
        if tuple(sorted(self.nodes, key=_node_key)) != self.nodes:
            msg = "ComponentGraph.nodes must be in canonical order."
            raise ValueError(msg)
        definition_ids = tuple(node.definition_id for node in self.nodes)
        class_ids = tuple(node.class_id for node in self.nodes)
        names = tuple(name for node in self.nodes for name in (node.name, *node.aliases))
        if len(definition_ids) != len(set(definition_ids)) or len(class_ids) != len(set(class_ids)):
            msg = "ComponentGraph node definition and class IDs must be unique."
            raise ValueError(msg)
        if len(names) != len(set(names)):
            msg = "ComponentGraph registered names must be unique."
            raise ValueError(msg)
        known = set(definition_ids)
        if any(type(reference) is not ComponentGraphReference for reference in self.references):
            msg = "ComponentGraph.references must contain ComponentGraphReference values."
            raise TypeError(msg)
        if any(
            reference.source_definition_id not in known or reference.target_definition_id not in known
            for reference in self.references
        ):
            msg = "Every resolved graph reference must join two graph nodes."
            raise ValueError(msg)
        nodes_by_definition = {node.definition_id: node for node in self.nodes}
        if any(
            reference.registered_name
            not in (
                nodes_by_definition[reference.target_definition_id].name,
                *nodes_by_definition[reference.target_definition_id].aliases,
            )
            for reference in self.references
        ):
            msg = "Every resolved graph reference must name one registration of its target node."
            raise ValueError(msg)
        if tuple(sorted(self.references, key=_reference_key)) != self.references:
            msg = "ComponentGraph.references must be in canonical order."
            raise ValueError(msg)
        if any(type(reference) is not UnresolvedComponentReference for reference in self.unresolved):
            msg = "ComponentGraph.unresolved must contain UnresolvedComponentReference values."
            raise TypeError(msg)
        if any(reference.source_definition_id not in known for reference in self.unresolved):
            msg = "Every unresolved graph reference must start at a graph node."
            raise ValueError(msg)
        if tuple(sorted(self.unresolved, key=_unresolved_key)) != self.unresolved:
            msg = "ComponentGraph.unresolved must be in canonical order."
            raise ValueError(msg)
        if any(type(problem) is not ComponentGraphProblem for problem in self.problems):
            msg = "ComponentGraph.problems must contain ComponentGraphProblem values."
            raise TypeError(msg)
        if any(
            definition_id not in known
            for problem in self.problems
            for definition_id in problem.component_definition_ids
        ):
            msg = "Every component graph problem must name graph nodes."
            raise ValueError(msg)
        if tuple(sorted(self.problems, key=_problem_key)) != self.problems:
            msg = "ComponentGraph.problems must be in canonical order."
            raise ValueError(msg)

    @property
    def coverage_complete(self) -> bool:
        """Whether every selected primary template was available and parseable."""
        return not self.problems

    @property
    def fully_resolved(self) -> bool:
        """Whether source coverage is complete and every reference has a static target."""
        return self.coverage_complete and not self.unresolved

    def component(self, selector: str | ComponentGraphNode) -> ComponentGraphNode:
        """
        Return one graph node selected by registered name, alias, or retained node.

        Args:
            selector: Case-insensitive registered name or a node from this graph.

        Returns:
            The canonical node stored in this graph.

        Raises:
            TypeError: If ``selector`` is not a string or graph node.
            NotRegistered: If the selector does not identify this graph's exact
                component generation.

        """
        if type(selector) is ComponentGraphNode:
            for node in self.nodes:
                if node.engine_id == selector.engine_id and node.definition_id == selector.definition_id:
                    return node
            raise NotRegistered(f"Component {selector.name!r} is not present in this component graph.")
        if type(selector) is not str:
            msg = "ComponentGraph.component() selector must be a registered name or ComponentGraphNode."
            raise TypeError(msg)
        normalized = selector.lower()
        for node in self.nodes:
            if normalized == node.name or normalized in node.aliases:
                return node
        raise NotRegistered(f"No component registered as {normalized!r} in this component graph.")

    def dependencies(self, component: str | ComponentGraphNode) -> tuple[ComponentGraphNode, ...]:
        """Return unique registered components directly referenced by ``component``."""
        source = self.component(component)
        target_ids = {
            reference.target_definition_id
            for reference in self.references
            if reference.source_definition_id == source.definition_id
        }
        return tuple(node for node in self.nodes if node.definition_id in target_ids)

    def dependents(self, component: str | ComponentGraphNode) -> tuple[ComponentGraphNode, ...]:
        """Return unique registered components that directly reference ``component``."""
        target = self.component(component)
        source_ids = {
            reference.source_definition_id
            for reference in self.references
            if reference.target_definition_id == target.definition_id
        }
        return tuple(node for node in self.nodes if node.definition_id in source_ids)

    def references_from(self, component: str | ComponentGraphNode) -> tuple[ComponentGraphReference, ...]:
        """Return every resolved authored reference owned by ``component``."""
        source = self.component(component)
        return tuple(
            reference for reference in self.references if reference.source_definition_id == source.definition_id
        )

    def references_to(self, component: str | ComponentGraphNode) -> tuple[ComponentGraphReference, ...]:
        """Return every resolved authored reference targeting ``component``."""
        target = self.component(component)
        return tuple(
            reference for reference in self.references if reference.target_definition_id == target.definition_id
        )

    def unresolved_from(
        self,
        component: str | ComponentGraphNode | None = None,
    ) -> tuple[UnresolvedComponentReference, ...]:
        """Return unresolved references from one component, or all of them when omitted."""
        if component is None:
            return self.unresolved
        source = self.component(component)
        return tuple(
            reference for reference in self.unresolved if reference.source_definition_id == source.definition_id
        )

    def to_dict(self) -> dict[str, object]:
        """Return a fresh JSON-ready dictionary for this graph."""
        return {
            "schema_version": self.schema_version,
            "citry_version": self.citry_version,
            "engine_id": self.engine_id,
            "coverage_complete": self.coverage_complete,
            "fully_resolved": self.fully_resolved,
            "nodes": [_node_to_dict(node) for node in self.nodes],
            "references": [_reference_to_dict(reference) for reference in self.references],
            "unresolved": [_unresolved_to_dict(reference) for reference in self.unresolved],
            "problems": [_problem_to_dict(problem) for problem in self.problems],
        }

    def to_json(self, indent: int | None = None) -> str:
        """
        Serialize this graph to deterministic UTF-8 JSON text.

        Args:
            indent: Optional non-negative indentation width. ``None`` emits
                compact JSON.

        Returns:
            Deterministic JSON with recursively sorted object keys.

        Raises:
            TypeError: If ``indent`` is not an integer or ``None``.
            ValueError: If ``indent`` is negative.

        """
        if indent is not None and type(indent) is not int:
            msg = "ComponentGraph.to_json() indent must be an integer or None."
            raise TypeError(msg)
        if indent is not None and indent < 0:
            msg = "ComponentGraph.to_json() indent cannot be negative."
            raise ValueError(msg)
        if indent is None:
            return json.dumps(
                self.to_dict(),
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            indent=indent,
        )


def _position_to_dict(position: LspPosition) -> dict[str, int]:
    return {"line": position.line, "character": position.character}


def _location_to_dict(location: ComponentGraphLocation) -> dict[str, object]:
    return {
        "origin": location.origin,
        "source_kind": location.source_kind,
        "declared_on": location.declared_on,
        "declaration_file": location.declaration_file.as_posix() if location.declaration_file is not None else None,
        "template_file": location.template_file.as_posix() if location.template_file is not None else None,
        "start_index": location.start_index,
        "end_index": location.end_index,
        "range": {
            "start": _position_to_dict(location.source_range.start),
            "end": _position_to_dict(location.source_range.end),
        },
    }


def _node_to_dict(node: ComponentGraphNode) -> dict[str, object]:
    return {
        "class_id": node.class_id,
        "engine_id": node.engine_id,
        "definition_id": node.definition_id,
        "name": node.name,
        "aliases": list(node.aliases),
        "builtin": node.builtin,
    }


def _reference_to_dict(reference: ComponentGraphReference) -> dict[str, object]:
    return {
        "source_definition_id": reference.source_definition_id,
        "target_definition_id": reference.target_definition_id,
        "registered_name": reference.registered_name,
        "authored_name": reference.authored_name,
        "syntax": reference.syntax,
        "location": _location_to_dict(reference.location),
    }


def _unresolved_to_dict(reference: UnresolvedComponentReference) -> dict[str, object]:
    return {
        "source_definition_id": reference.source_definition_id,
        "authored_name": reference.authored_name,
        "reason": reference.reason,
        "syntax": reference.syntax,
        "location": _location_to_dict(reference.location),
    }


def _problem_to_dict(problem: ComponentGraphProblem) -> dict[str, object]:
    return {
        "component_definition_ids": list(problem.component_definition_ids),
        "code": problem.code,
        "message": problem.message,
        "origin": problem.origin,
        "location": _location_to_dict(problem.location) if problem.location is not None else None,
    }


__all__ = [
    "ComponentGraph",
    "ComponentGraphLocation",
    "ComponentGraphNode",
    "ComponentGraphProblem",
    "ComponentGraphReference",
    "UnresolvedComponentReference",
]
