"""Checked server-to-browser translation bindings for ``$c-tr``."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, cast
from weakref import ref

from citry._i18n_directives import (
    I18N_BINDING_ATTRIBUTE_TARGETS,
    I18N_BINDING_PREFIX,
    looks_like_i18n_binding,
    parse_i18n_binding_name,
)
from citry.attrs import merge_attrs, validate_html_attr_name
from citry.citry_render import _render_value
from citry.client_directives import (
    CLIENT_PROPS_ATTR,
    apply_client_props_contribution,
    has_client_props_key,
)
from citry.constness import const_value
from citry.nodes import ElementAttrsNode, ExprNode, Node, _reject_dynamic_events_compiler_attr

from .usage import CLIENT_CONTEXT_KEY

if TYPE_CHECKING:
    from collections.abc import Iterator

    from citry.citry_context import CitryContext
    from citry.component import Component


DIRECTIVE_PREFIX = I18N_BINDING_PREFIX
MARKER_ATTRIBUTE = "data-citry-i18n-binding"
ATTRIBUTE_TARGETS = I18N_BINDING_ATTRIBUTE_TARGETS


class CapturedTranslationText(str):
    """Identity-bearing ``str`` returned only while a binding contribution resolves."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class I18nBindingTarget:
    """The complete DOM destination owned by one declarative binding."""

    kind: Literal["attribute", "text"]
    name: str | None = None


@dataclass(frozen=True, slots=True)
class I18nBindingRecord:
    """One checked binding serialized inside its logical provider requirement."""

    id: str
    owner: str
    message: str
    output: str | None
    values: tuple[tuple[str, tuple[str, str]], ...]
    values_expression: str | None
    target: I18nBindingTarget


@dataclass(frozen=True, slots=True)
class _CapturedTranslation:
    message: str
    output: str | None
    values: dict[str, object]
    text: CapturedTranslationText


@dataclass(frozen=True, slots=True)
class _Declaration:
    message: str
    output: str | None
    target: I18nBindingTarget
    values_expression: str | None


@dataclass(slots=True)
class _PendingText:
    declaration: _Declaration
    binding_id: str | None
    owner: str | None


class I18nBindingCollector:
    """Mutable render-local binding state owned by one component config."""

    __slots__ = (
        "_cache_text_replacements",
        "_component",
        "_counter",
        "_pending_text",
        "_sealed",
        "markers",
        "records",
    )

    def __init__(self, component: Component | None) -> None:
        self._component = ref(component) if component is not None else lambda: None
        self._counter = 0
        self._pending_text: dict[int, _PendingText] = {}
        self._sealed = False
        self._cache_text_replacements: tuple[tuple[str, str], ...] = ()
        self.records: list[I18nBindingRecord] = []
        self.markers: list[tuple[str, ...]] = []

    @classmethod
    def restored(
        cls,
        records: list[I18nBindingRecord],
        markers: list[tuple[str, ...]],
    ) -> I18nBindingCollector:
        """Build already-checked state remapped from one render-cache artifact."""
        collector = cls(None)
        collector.records.extend(records)
        collector.markers.extend(markers)
        collector._counter = len(records)
        collector._sealed = True
        return collector

    @contextmanager
    def capture(self) -> Iterator[list[_CapturedTranslation]]:
        component = self._component()
        if component is None:
            raise RuntimeError("The component owning an i18n binding was released during render.")
        config = cast("Any", component).i18n
        previous = config._translation_capture
        captures: list[_CapturedTranslation] = []

        def record(message: str, output: str | None, values: dict[str, object], text: CapturedTranslationText) -> None:
            captures.append(_CapturedTranslation(message, output, values, text))

        config._translation_capture = record
        try:
            yield captures
        finally:
            config._translation_capture = previous

    def allocate_id(self) -> str:
        component = self._component()
        if component is None:
            raise RuntimeError("The component owning an i18n binding was released during render.")
        value = f"{component.id}~i18n-{self._counter}"
        self._counter += 1
        return value

    def begin_text(self, ordinal: int, declaration: _Declaration, *, owner: str | None) -> str | None:
        if ordinal in self._pending_text:
            raise RuntimeError("An i18n text destination was registered twice during one render.")
        binding_id = self.allocate_id() if owner is not None else None
        self._pending_text[ordinal] = _PendingText(declaration, binding_id, owner)
        return binding_id

    def finish_text(self, ordinal: int, capture: _CapturedTranslation) -> None:
        try:
            pending = self._pending_text.pop(ordinal)
        except KeyError as error:
            raise RuntimeError("An i18n text binding rendered without its start-tag declaration.") from error
        _check_capture(pending.declaration, capture, destination="textContent")
        if pending.binding_id is not None:
            assert pending.owner is not None  # noqa: S101 - allocated IDs always have an owner
            self.records.append(_binding_record(pending.binding_id, pending.owner, pending.declaration, capture))

    def has_pending_text(self, ordinal: int) -> bool:
        """Whether the resolved start tag declared a text binding for this expression."""
        return ordinal in self._pending_text

    def add_attribute(
        self,
        declaration: _Declaration,
        capture: _CapturedTranslation,
        *,
        owner: str | None,
    ) -> str | None:
        assert declaration.target.name is not None  # noqa: S101 - attribute target invariant
        _check_capture(declaration, capture, destination=declaration.target.name)
        if owner is None:
            return None
        binding_id = self.allocate_id()
        self.records.append(_binding_record(binding_id, owner, declaration, capture))
        return binding_id

    def add_marker(self, ids: list[str]) -> None:
        if ids:
            self.markers.append(tuple(ids))

    def seal(self) -> None:
        if self._pending_text:
            ordinals = ", ".join(str(value) for value in sorted(self._pending_text))
            raise RuntimeError(f"i18n text binding(s) {ordinals} did not render a complete translated body.")
        self._sealed = True

    def assert_ready(self) -> None:
        if not self._sealed:
            raise RuntimeError("i18n binding metadata was read before its component render completed.")
        if self._pending_text:
            raise RuntimeError("i18n binding metadata contains an unfinished text destination.")


class I18nBindingElementAttrsNode(Node):
    """Resolve one ordinary attribute region while consuming checked ``$c-tr`` declarations."""

    def __init__(self, original: ElementAttrsNode, *, ordinal: int, text_eligible: bool) -> None:
        self.original = original
        self.ordinal = ordinal
        self.text_eligible = text_eligible
        self.used_vars = original.used_vars

    def render(self, context: CitryContext) -> Any:
        component = context.component
        if component is None:
            raise RuntimeError("$c-tr requires a component-owned HTML element.")
        collector = cast("Any", component).i18n._bindings
        declarations: OrderedDict[tuple[str, str | None], _Declaration] = OrderedDict()
        contributions: list[Mapping[str, Any]] = []
        provenance: dict[str, _CapturedTranslation | None] = {}

        for attr in self.original.attrs:
            with collector.capture() as captures:
                raw = const_value(attr.resolve(context))
            if attr.key == "c-bind":
                if raw is None:
                    continue
                if not isinstance(raw, Mapping):
                    raise TypeError(
                        f"c-bind on <{self.original.tag_name}> must resolve to a mapping of attributes, "
                        f"got {type(raw).__name__}"
                    )
                contribution: dict[str, Any] = {}
                for key, value in raw.items():
                    resolved_key = validate_html_attr_name(key, where=f"c-bind on <{self.original.tag_name}>")
                    if _apply_directive(
                        declarations,
                        resolved_key,
                        const_value(value),
                        dynamic=True,
                    ):
                        continue
                    _reject_dynamic_events_compiler_attr(
                        resolved_key,
                        tag_name=self.original.tag_name,
                    )
                    _reject_reserved_output(resolved_key, self.original.tag_name)
                    normalized = const_value(value)
                    contribution[resolved_key] = normalized
                    provenance[_html_identity(resolved_key)] = _capture_for_value(captures, normalized)
                contributions.append(contribution)
                continue

            resolved_key = attr.key.removeprefix("c-")
            if _apply_directive(
                declarations,
                resolved_key,
                raw,
                dynamic=attr.key.startswith("c-"),
            ):
                if captures:
                    raise RuntimeError("A $c-tr values expression cannot itself call server tr().")
                continue
            if attr.key.startswith("c-"):
                _reject_dynamic_events_compiler_attr(
                    resolved_key,
                    tag_name=self.original.tag_name,
                )
            _reject_reserved_output(resolved_key, self.original.tag_name)
            contributions.append({resolved_key: raw})
            provenance[_html_identity(resolved_key)] = _capture_for_value(captures, raw)

        resolved = merge_attrs(*contributions)
        for key in resolved:
            if key.startswith("#c-"):
                raise RuntimeError(
                    f"{key!r} arrived on <{self.original.tag_name}> through an attribute spread or a "
                    "dynamic attribute. '#c-*' framework attributes are template-authored only: "
                    "write the attribute directly on the tag in the template."
                )
        if has_client_props_key(resolved, tag_name=self.original.tag_name):
            apply_client_props_contribution(
                resolved,
                resolved[CLIENT_PROPS_ATTR],
                tag_name=self.original.tag_name,
                component_boundary=False,
            )
        resolved = {key: value for key, value in resolved.items() if value is not None and value is not False}
        resolved = component.citry.extensions.on_attrs_resolved(
            component=component,
            tag_name=self.original.tag_name,
            attrs=resolved,
        )
        if has_client_props_key(resolved, tag_name=self.original.tag_name):
            apply_client_props_contribution(
                resolved,
                resolved[CLIENT_PROPS_ATTR],
                tag_name=self.original.tag_name,
                component_boundary=False,
            )

        owner = context.provides.get(CLIENT_CONTEXT_KEY)
        if owner is not None and (type(owner) is not str or not owner):
            raise TypeError(f"The internal {CLIENT_CONTEXT_KEY!r} render provide must be a render ID.")
        marker_ids: list[str] = []

        for declaration in declarations.values():
            if declaration.target.kind == "text":
                if not self.text_eligible:
                    raise RuntimeError(
                        f"$c-tr:{declaration.message} owns textContent, but <{self.original.tag_name}> does not "
                        "contain exactly one translated {{ ... }} expression."
                    )
                binding_id = collector.begin_text(self.ordinal, declaration, owner=cast("str | None", owner))
                if binding_id is not None:
                    marker_ids.append(binding_id)
                continue
            target_name = cast("str", declaration.target.name)
            winning_key = next((key for key in resolved if _html_identity(key) == target_name), None)
            if winning_key is None:
                raise RuntimeError(
                    f"$c-tr:{declaration.message}[{target_name}] has no final server-rendered {target_name!r} value."
                )
            value = resolved[winning_key]
            capture = provenance.get(target_name)
            if capture is None or value is not capture.text:
                raise RuntimeError(
                    f"$c-tr:{declaration.message}[{target_name}] must pair with the complete winning "
                    f"{target_name!r} value returned directly by tr()."
                )
            binding_id = collector.add_attribute(declaration, capture, owner=cast("str | None", owner))
            if binding_id is not None:
                marker_ids.append(binding_id)

        if marker_ids:
            if MARKER_ATTRIBUTE in resolved:
                raise RuntimeError(f"{MARKER_ATTRIBUTE!r} is compiler-owned and cannot be authored.")
            resolved[MARKER_ATTRIBUTE] = " ".join(marker_ids)
            collector.add_marker(marker_ids)
        return self.original._format(resolved, context)


class I18nBoundExprNode(Node):
    """Capture one complete text expression selected by its start-tag binding."""

    def __init__(self, original: ExprNode, *, ordinal: int) -> None:
        self.original = original
        self.ordinal = ordinal
        self.used_vars = original.used_vars

    def render(self, context: CitryContext) -> Any:
        component = context.component
        if component is None:
            raise RuntimeError("$c-tr textContent requires a component-owned expression.")
        collector = cast("Any", component).i18n._bindings
        if not collector.has_pending_text(self.ordinal):
            value = self.original.evaluate(context.variables, sandboxed=context.sandboxed)
            return _render_value(value, provides=context.provides, citry=component.citry)
        with collector.capture() as captures:
            value = self.original.evaluate(context.variables, sandboxed=context.sandboxed)
        if len(captures) != 1 or value is not captures[0].text:
            raise RuntimeError(
                "$c-tr textContent must contain exactly one complete {{ tr(...) }} expression, with no composition."
            )
        collector.finish_text(self.ordinal, captures[0])
        return _render_value(value, provides=context.provides, citry=component.citry)


def compile_template_bindings(nodes: list[Any], *, component_name: str) -> list[Any]:
    """Wrap literal final HTML destinations and reject direct non-HTML placement."""
    ordinal = [0]
    return _transform_body(nodes, component_name=component_name, ordinal=ordinal)


def reject_translation_binding_key(key: object, *, tag_name: str) -> None:
    """Reject a resolved ``$c-tr`` key on a node that is not final plain HTML."""
    if isinstance(key, str) and looks_like_i18n_binding(key):
        raise RuntimeError(
            f"{key!r} resolved on <{tag_name}>, but $c-tr is valid only on a literal final plain HTML element."
        )


def _transform_body(nodes: list[Any], *, component_name: str, ordinal: list[int]) -> list[Any]:
    from citry.nodes import ComponentNode, FillNode, ForNode, IfNode, SlotNode  # noqa: PLC0415

    result = list(nodes)
    for item in result:
        if isinstance(item, ComponentNode):
            _reject_direct_structural(item.attrs, tag_name=f"c-{item.name}")
            item.body = _transform_body(item.body, component_name=component_name, ordinal=ordinal)
        elif isinstance(item, (SlotNode, FillNode)):
            _reject_direct_structural(item.attrs, tag_name=type(item).__name__.removesuffix("Node").lower())
            item.body = _transform_body(item.body, component_name=component_name, ordinal=ordinal)
        elif isinstance(item, (IfNode, ForNode)):
            branches = []
            for branch in item.branches:
                _reject_direct_structural(branch[1], tag_name="c-if/c-for control-flow branch")
                branches.append(
                    (
                        branch[0],
                        branch[1],
                        _transform_body(branch[2], component_name=component_name, ordinal=ordinal),
                        branch[3],
                    )
                )
            item.branches = tuple(branches)

    index = 0
    while index < len(result):
        item = result[index]
        if not isinstance(item, ElementAttrsNode) or not _may_bind(item):
            index += 1
            continue
        current_ordinal = ordinal[0]
        ordinal[0] += 1
        text_eligible = _complete_text_expression(result, index, item.tag_name)
        for attr in item.attrs:
            resolved_key = attr.key.removeprefix("c-")
            if looks_like_i18n_binding(resolved_key):
                declaration = _parse_directive(resolved_key)
                if declaration.target.kind == "text" and not text_eligible:
                    raise ValueError(
                        f"{resolved_key!r} in {component_name} targets textContent, but the element body is not "
                        "exactly one translated expression."
                    )
        result[index] = I18nBindingElementAttrsNode(item, ordinal=current_ordinal, text_eligible=text_eligible)
        if text_eligible:
            result[index + 2] = I18nBoundExprNode(cast("ExprNode", result[index + 2]), ordinal=current_ordinal)
        index += 1
    return result


def _may_bind(node: ElementAttrsNode) -> bool:
    return any(
        attr.key == "c-bind"
        or looks_like_i18n_binding(attr.key)
        or (attr.key.startswith("c-") and looks_like_i18n_binding(attr.key.removeprefix("c-")))
        for attr in node.attrs
    )


def _complete_text_expression(body: list[Any], index: int, tag_name: str) -> bool:
    return (
        index + 3 < len(body)
        and body[index + 1] == ">"
        and isinstance(body[index + 2], ExprNode)
        and isinstance(body[index + 3], str)
        and body[index + 3].startswith(f"</{tag_name}>")
    )


def _reject_direct_structural(attrs: tuple[Any, ...], *, tag_name: str) -> None:
    for attr in attrs:
        if attr.key == "c-bind":
            continue
        reject_translation_binding_key(attr.key.removeprefix("c-"), tag_name=tag_name)


def _apply_directive(
    declarations: OrderedDict[tuple[str, str | None], _Declaration],
    key: str,
    value: object,
    *,
    dynamic: bool,
) -> bool:
    if not looks_like_i18n_binding(key):
        return False
    declaration = _parse_directive(key)
    destination = (declaration.target.kind, declaration.target.name)
    if dynamic and (value is None or value is False):
        declarations.pop(destination, None)
        return True
    if value is True:
        expression = None
    elif isinstance(value, str):
        expression = value.strip() or None
    else:
        raise TypeError(f"{key} must resolve to a string, True, None, or False; got {type(value).__name__}.")
    if expression is not None:
        _validate_values_expression(expression, key=key)
    declaration = _Declaration(
        declaration.message,
        declaration.output,
        declaration.target,
        expression,
    )
    declarations.pop(destination, None)
    declarations[destination] = declaration
    return True


def _parse_directive(key: str) -> _Declaration:
    parsed = parse_i18n_binding_name(key)
    attribute = parsed.target
    if attribute is None:
        target = I18nBindingTarget("text")
    else:
        target = I18nBindingTarget("attribute", attribute)
    return _Declaration(parsed.message, parsed.output, target, None)


def _validate_values_expression(expression: str, *, key: str) -> None:
    from citry._browser_expressions import BrowserExpression, analyze_browser_expression  # noqa: PLC0415

    checked = analyze_browser_expression(BrowserExpression(expression, 0, len(expression.encode()), "expression", key))
    if not checked.valid:
        raise ValueError(f"{key} has an invalid Alpine named-values expression.")


def _capture_for_value(captures: list[_CapturedTranslation], value: object) -> _CapturedTranslation | None:
    matching = [capture for capture in captures if value is capture.text]
    if len(matching) > 1:
        raise RuntimeError("One HTML attribute value ambiguously matches multiple tr() calls.")
    return matching[0] if matching else None


def _check_capture(declaration: _Declaration, capture: _CapturedTranslation, *, destination: str) -> None:
    if declaration.message != capture.message or declaration.output != capture.output:
        expected = declaration.message if declaration.output is None else f"{declaration.message}.{declaration.output}"
        actual = capture.message if capture.output is None else f"{capture.message}.{capture.output}"
        raise RuntimeError(f"$c-tr for {destination} names {expected!r}, but its server tr() resolved {actual!r}.")


def _binding_record(
    binding_id: str,
    owner: str,
    declaration: _Declaration,
    capture: _CapturedTranslation,
) -> I18nBindingRecord:
    from .extension import I18nExtension  # noqa: PLC0415

    component_values = tuple(
        (name, (tagged["type"], tagged["value"]))
        for name, tagged in sorted(
            ((name, I18nExtension._tag_value(name, value)) for name, value in capture.values.items()),
            key=lambda item: item[0],
        )
    )
    return I18nBindingRecord(
        id=binding_id,
        owner=owner,
        message=declaration.message,
        output=declaration.output,
        values=component_values,
        values_expression=declaration.values_expression,
        target=declaration.target,
    )


def _reject_reserved_output(key: str, tag_name: str) -> None:
    if key.lower() == MARKER_ATTRIBUTE:
        raise RuntimeError(f"{key!r} on <{tag_name}> is compiler-owned; author $c-tr instead of a binding marker.")


def _html_identity(key: str) -> str:
    return key.translate(str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"))


__all__ = [
    "ATTRIBUTE_TARGETS",
    "DIRECTIVE_PREFIX",
    "MARKER_ATTRIBUTE",
    "I18nBindingCollector",
    "I18nBindingRecord",
    "I18nBindingTarget",
    "compile_template_bindings",
    "reject_translation_binding_key",
]
