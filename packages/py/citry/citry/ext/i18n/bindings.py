"""Checked server-to-browser translation bindings for ``$c-tr``."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Literal, TypeGuard, cast
from weakref import ref

from citry._i18n_directives import (
    I18N_BINDING_ATTRIBUTE_TARGETS,
    I18N_BINDING_PREFIX,
    looks_like_i18n_binding,
    parse_i18n_binding_name,
)
from citry._vue.capture import (
    PreparedBrowserBinding,
    PreparedElementOpen,
    PreparedTextValue,
    prepared_browser_binding,
    prepared_render_active,
)
from citry._walk import Call, run
from citry.attrs import (
    merge_attrs,
    reject_script_capable_attr_name,
    reject_vue_code_attr_name,
    template_attr_value,
    validate_html_attr_name,
    vue_code_error,
)
from citry.citry_render import _render_value
from citry.client_directives import (
    CLIENT_PROPS_ATTR,
    apply_client_props_contribution,
    has_client_props_key,
)
from citry.constness import const_value
from citry.nodes import ElementAttrsNode, ExprNode, Node, StaticHtmlAttr, _reject_reserved_events_attr
from citry.util.html import Markup, decode_attribute_entities, decode_character_references
from citry.util.id import validate_render_id

from .usage import CLIENT_CONTEXT_KEY

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator

    from citry.citry_context import CitryContext
    from citry.component import Component


DIRECTIVE_PREFIX = I18N_BINDING_PREFIX
MARKER_ATTRIBUTE = "data-citry-i18n-binding"
ATTRIBUTE_TARGETS = I18N_BINDING_ATTRIBUTE_TARGETS
# The name of the browser function that receives a binding ID. The render cache
# also uses it to find this extension's bindings among the parts it stores.
BINDING_HELPER = "$citryI18nBinding"
# Between the owning component's render ID and the binding's number in an ID.
_BINDING_ID_SEPARATOR = "~i18n-"
# No component allocates a billion bindings, so a longer number in a stored ID
# is not one this collector wrote. The limit also keeps `int()` away from the
# huge digit strings that Python refuses to convert.
_BINDING_NUMBER_MAX_DIGITS = 9


def split_binding_id(value: object) -> tuple[str, int] | None:
    """
    Split an ID that `I18nBindingCollector.allocate_id` could have written.

    Returns the render ID of the component that allocated it and its number, or
    `None` for any other value. The shape is a render ID, then `~i18n-`, then a
    number. Replay uses this to refuse a cache entry whose binding ID this
    collector could not have written.
    """
    if type(value) is not str:
        return None
    owner, separator, number = value.rpartition(_BINDING_ID_SEPARATOR)
    # `isdecimal` also accepts digits of other scripts, which `allocate_id` never writes.
    if not separator or len(number) > _BINDING_NUMBER_MAX_DIGITS or not number.isascii() or not number.isdecimal():
        return None
    try:
        validate_render_id(owner)
    except (TypeError, ValueError):
        return None
    return owner, int(number)


def is_binding_id(value: object) -> TypeGuard[str]:
    """Return `True` when `value` has the shape `split_binding_id` accepts."""
    return split_binding_id(value) is not None


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
    # Whether the values expression contains a `null` token. Only such an
    # expression can ask the browser to keep the server text, so only its
    # destination may hold something other than a matching `tr()` result.
    allows_untranslated: bool = False


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
        "marker_by_id",
        "markers",
        "record_by_id",
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
        # Lookups over the two lists above. The render cache needs the binding
        # and the marker for one ID without scanning every one this component
        # allocated, since a page can hold many cached parts that each ask.
        self.record_by_id: dict[str, I18nBindingRecord] = {}
        self.marker_by_id: dict[str, tuple[str, ...]] = {}

    @classmethod
    def restored(
        cls,
        records: list[I18nBindingRecord],
        markers: list[tuple[str, ...]],
    ) -> I18nBindingCollector:
        """Build already-checked state remapped from one render-cache artifact."""
        collector = cls(None)
        for record in records:
            collector._add_record(record)
        for marker in markers:
            collector._add_marker(marker)
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
        value = f"{component.id}{_BINDING_ID_SEPARATOR}{self._counter}"
        self._counter += 1
        return value

    def begin_text(self, ordinal: int, declaration: _Declaration, *, owner: str | None) -> str | None:
        if ordinal in self._pending_text:
            raise RuntimeError("An i18n text destination was registered twice during one render.")
        binding_id = self.allocate_id() if owner is not None else None
        self._pending_text[ordinal] = _PendingText(declaration, binding_id, owner)
        return binding_id

    def finish_text(self, ordinal: int, capture: _CapturedTranslation) -> _PendingText:
        try:
            pending = self._pending_text.pop(ordinal)
        except KeyError as error:
            raise RuntimeError("An i18n text binding rendered without its start-tag declaration.") from error
        _check_capture(pending.declaration, capture, destination="textContent")
        if pending.binding_id is not None:
            assert pending.owner is not None  # noqa: S101 - allocated IDs always have an owner
            self._add_record(_binding_record(pending.binding_id, pending.owner, pending.declaration, capture))
        return pending

    def finish_untranslated_text(self, ordinal: int) -> _PendingText:
        """
        Close a text destination whose body is not a `tr()` call.

        Only a binding whose values expression contains `null` allows that.
        """
        try:
            pending = self._pending_text.pop(ordinal)
        except KeyError as error:
            raise RuntimeError("An i18n text binding rendered without its start-tag declaration.") from error
        if pending.binding_id is not None:
            assert pending.owner is not None  # noqa: S101 - allocated IDs always have an owner
            self._add_record(_binding_record(pending.binding_id, pending.owner, pending.declaration, None))
        return pending

    def pending_declaration(self, ordinal: int) -> _Declaration:
        """Return the start-tag declaration waiting for this text expression."""
        return self._pending_text[ordinal].declaration

    def has_pending_text(self, ordinal: int) -> bool:
        """Whether the resolved start tag declared a text binding for this expression."""
        return ordinal in self._pending_text

    def add_attribute(
        self,
        declaration: _Declaration,
        capture: _CapturedTranslation | None,
        *,
        owner: str | None,
    ) -> str | None:
        assert declaration.target.name is not None  # noqa: S101 - attribute target invariant
        # `None` is a value that no `tr()` call produced; the caller allows
        # it only under a values expression that can return `null`.
        if capture is not None:
            _check_capture(declaration, capture, destination=declaration.target.name)
        if owner is None:
            return None
        binding_id = self.allocate_id()
        self._add_record(_binding_record(binding_id, owner, declaration, capture))
        return binding_id

    def add_marker(self, ids: list[str]) -> None:
        if ids:
            self._add_marker(tuple(ids))

    def _add_record(self, record: I18nBindingRecord) -> None:
        self.records.append(record)
        self.record_by_id[record.id] = record

    def _add_marker(self, marker: tuple[str, ...]) -> None:
        self.markers.append(marker)
        for binding_id in marker:
            self.marker_by_id[binding_id] = marker

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
        self.has_static_binding = any(
            looks_like_i18n_binding(attr.key)
            or (attr.key.startswith("c-") and looks_like_i18n_binding(attr.key.removeprefix("c-")))
            for attr in original.attrs
        )

    def render(self, context: CitryContext) -> Any:
        component = context.component
        if component is None:
            raise RuntimeError("$c-tr requires a component-owned HTML element.")
        component_i18n = cast("Any", component).i18n
        if not self.has_static_binding and component_i18n._extension._compiled_catalog is None:
            return self.original.render(context)
        # This path resolves the attributes itself instead of calling the
        # wrapped node, so it repeats that node's check for `c-v-if`-style names.
        if self.original._vue_code_attr_key is not None:
            raise vue_code_error(
                self.original._vue_code_attr_key,
                tag_name=self.original.tag_name,
                origin="c-attr",
            )
        collector = cast("Any", component).i18n._bindings
        declarations: OrderedDict[tuple[str, str | None], _Declaration] = OrderedDict()
        contributions: list[Mapping[str, Any]] = []
        provenance: dict[str, _CapturedTranslation | None] = {}
        # Attributes whose value called `tr()` but is not exactly its result,
        # such as `tr('a') + '!'`. Those never count as untranslated text.
        composed: set[str] = set()

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
                    # A spread key is Python data, and a `$c-tr` key would make
                    # its value browser code, so this rejects every `$c-tr`
                    # spelling before the binding parser could see it.
                    reject_vue_code_attr_name(resolved_key, tag_name=self.original.tag_name, origin="c-bind")
                    reject_script_capable_attr_name(resolved_key, tag_name=self.original.tag_name, where="c-bind")
                    _reject_reserved_events_attr(
                        resolved_key,
                        tag_name=self.original.tag_name,
                    )
                    _reject_reserved_output(resolved_key, self.original.tag_name)
                    normalized = const_value(value)
                    contribution[resolved_key] = normalized
                    _note_provenance(provenance, composed, _html_identity(resolved_key), captures, normalized)
                contributions.append(contribution)
                continue

            resolved_key = attr.key.removeprefix("c-")
            # Only a literal template attribute declares a binding. A
            # `c-$c-tr:...` attribute was already rejected above through
            # `_vue_code_attr_key`, because its value would be Python data.
            if type(attr) is StaticHtmlAttr and _apply_directive(declarations, attr.key, raw):
                continue
            if attr.key.startswith("c-"):
                _reject_reserved_events_attr(
                    resolved_key,
                    tag_name=self.original.tag_name,
                )
            _reject_reserved_output(resolved_key, self.original.tag_name)
            if type(attr) is StaticHtmlAttr:
                # A written empty class or style joins the merge as an empty
                # marker, as on a plain element, instead of a rejected `True`.
                raw = template_attr_value(resolved_key, raw)
            contributions.append({resolved_key: raw})
            _note_provenance(provenance, composed, _html_identity(resolved_key), captures, raw)

        resolved = merge_attrs(*contributions)
        for key in resolved:
            if str.startswith(key, "#c-"):
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
        extensions = component.citry.extensions
        runtime_candidate = self.original._runtime_extension_candidate(resolved)
        validate_extension_output = extensions.has_attrs_resolved_hook(
            runtime_candidate=runtime_candidate,
        )
        if validate_extension_output:
            resolved = extensions.on_attrs_resolved(
                component=component,
                tag_name=self.original.tag_name,
                attrs=resolved,
                runtime_candidate=runtime_candidate,
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
        browser_bindings: list[PreparedBrowserBinding] = []

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
                # A values expression that contains `null` already says "this
                # element may keep what the server rendered". When the server
                # rendered no such attribute at all (an `aria-labelledby`
                # label, say), there is nothing to translate, so the binding
                # is dropped. Python only decided whether the attribute
                # exists; the expression is still the author's own text, and
                # no binding is sent to the browser.
                if declaration.allows_untranslated:
                    continue
                raise RuntimeError(
                    f"$c-tr:{declaration.message}[{target_name}] has no final server-rendered {target_name!r} value."
                )
            value = resolved[winning_key]
            capture = provenance.get(target_name)
            # A values expression with a `null` token may keep the server
            # text, so its attribute may hold text that no `tr()` produced,
            # such as an author's own label. Every other binding pairs with
            # the exact `tr()` result.
            untranslated = capture is None and declaration.allows_untranslated and target_name not in composed
            if untranslated and not isinstance(value, str):
                raise TypeError(
                    f"$c-tr:{declaration.message}[{target_name}] keeps a server {target_name!r} value that is "
                    f"not text; got {type(value).__name__}. Pass a string."
                )
            if not untranslated and (capture is None or value is not capture.text):
                raise RuntimeError(
                    f"$c-tr:{declaration.message}[{target_name}] must pair with the complete winning "
                    f"{target_name!r} value returned directly by tr()."
                )
            binding_id = collector.add_attribute(
                declaration,
                None if untranslated else capture,
                owner=cast("str | None", owner),
            )
            if binding_id is not None:
                marker_ids.append(binding_id)
                browser_bindings.append(
                    prepared_browser_binding(
                        helper=BINDING_HELPER,
                        operand=binding_id,
                        target="attribute",
                        name=target_name,
                        values_expression=declaration.values_expression,
                        # The browser shows this text when the expression
                        # returns `null`; it travels as JSON data, not code.
                        fallback=None if declaration.values_expression is None else str(value),
                    )
                )

        if marker_ids:
            if MARKER_ATTRIBUTE in resolved:
                raise RuntimeError(f"{MARKER_ATTRIBUTE!r} is compiler-owned and cannot be authored.")
            resolved[MARKER_ATTRIBUTE] = " ".join(marker_ids)
            collector.add_marker(marker_ids)
        normalized = resolved
        for key, value in resolved.items():
            if type(value) is not CapturedTranslationText:
                continue
            if normalized is resolved:
                normalized = dict(resolved)
            normalized[key] = str(value)
        rendered = self.original._format(normalized, context, validate_keys=validate_extension_output)
        if browser_bindings:
            if not isinstance(rendered, PreparedElementOpen):
                raise RuntimeError("prepared i18n attribute binding lost its typed element opening")
            rendered = replace(rendered, browser_bindings=tuple(browser_bindings))
        return rendered


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
            rendered = _render_value(value, provides=context.provides, citry=component.citry, context=context)
            if prepared_render_active() and isinstance(rendered, Markup) and "<" not in str(rendered):
                text = decode_character_references(str(rendered))
                return PreparedTextValue(self.original.source, self.original.position, text)
            return rendered
        with collector.capture() as captures:
            value = self.original.evaluate(context.variables, sandboxed=context.sandboxed)
        if not captures and collector.pending_declaration(self.ordinal).allows_untranslated:
            return self._render_untranslated(value, context, collector)
        if len(captures) != 1 or value is not captures[0].text:
            raise RuntimeError(
                "$c-tr textContent must contain exactly one complete {{ tr(...) }} expression, with no composition."
            )
        pending = collector.finish_text(self.ordinal, captures[0])
        if prepared_render_active():
            return PreparedTextValue(
                self.original.source,
                self.original.position,
                str(value),
                browser_binding=_text_browser_binding(pending, str(value)),
            )
        return _render_value(value, provides=context.provides, citry=component.citry, context=context)

    def _render_untranslated(self, value: object, context: CitryContext, collector: Any) -> Any:
        """Render a body that no `tr()` call produced, under a values expression that can return `null`."""
        component = cast("Component", context.component)
        rendered = _render_value(value, provides=context.provides, citry=component.citry, context=context)
        pending = collector.finish_untranslated_text(self.ordinal)
        if not prepared_render_active():
            return rendered
        # The browser can put back only plain text, so the binding needs the
        # body's exact text, the same text a plain `{{ }}` would send.
        if not isinstance(rendered, Markup) or "<" in str(rendered):
            raise RuntimeError(
                f"$c-tr:{pending.declaration.message} owns textContent, but its body renders HTML markup, "
                "which the browser cannot keep as the server text. Render plain text in the element, "
                "or move the markup outside it."
            )
        text = decode_character_references(str(rendered))
        return PreparedTextValue(
            self.original.source,
            self.original.position,
            text,
            browser_binding=_text_browser_binding(pending, text),
        )


def _text_browser_binding(pending: _PendingText, server_text: str) -> PreparedBrowserBinding | None:
    """Build the browser projection for one finished text destination, if a client provider owns it."""
    if pending.binding_id is None:
        return None
    return prepared_browser_binding(
        helper=BINDING_HELPER,
        operand=pending.binding_id,
        target="text",
        values_expression=pending.declaration.values_expression,
        # The browser shows this text when the expression returns `null`;
        # it travels as JSON data, not code.
        fallback=None if pending.declaration.values_expression is None else server_text,
    )


def compile_template_bindings(nodes: list[Any], *, component_name: str) -> list[Any]:
    """Wrap literal final HTML destinations and reject direct non-HTML placement."""
    ordinal = [0]
    # The walk runs as generators on one driver loop, so Python's call depth
    # does not grow with how deeply the template nests. Each nested body is
    # transformed completely where it is reached, so a nested body's bindings
    # are numbered before this body's own elements, in source order.
    return run(_transform_body(nodes, component_name=component_name, ordinal=ordinal))


def reject_translation_binding_key(key: object, *, tag_name: str) -> None:
    """Reject a resolved ``$c-tr`` key on a node that is not final plain HTML."""
    if isinstance(key, str) and looks_like_i18n_binding(key):
        raise RuntimeError(
            f"{key!r} resolved on <{tag_name}>, but $c-tr is valid only on a literal final plain HTML element."
        )


def _transform_body(nodes: list[Any], *, component_name: str, ordinal: list[int]) -> Generator[Call, Any, list[Any]]:
    from citry.nodes import ComponentNode, FillNode, ForNode, IfNode, SlotNode  # noqa: PLC0415

    result = list(nodes)
    for item in result:
        if isinstance(item, ComponentNode):
            _reject_direct_structural(item.attrs, tag_name=f"c-{item.name}")
            item.body = yield Call(_transform_body, item.body, component_name=component_name, ordinal=ordinal)
        elif isinstance(item, (SlotNode, FillNode)):
            _reject_direct_structural(item.attrs, tag_name=type(item).__name__.removesuffix("Node").lower())
            item.body = yield Call(_transform_body, item.body, component_name=component_name, ordinal=ordinal)
        elif isinstance(item, (IfNode, ForNode)):
            branches = []
            for branch in item.branches:
                _reject_direct_structural(branch[1], tag_name="c-if/c-for control-flow branch")
                transformed = yield Call(_transform_body, branch[2], component_name=component_name, ordinal=ordinal)
                branches.append((branch[0], branch[1], transformed, branch[3]))
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
            # A `c-$c-tr:...` spelling fails at render with `VueCodeError`,
            # like `c-v-if`, so only the literal template form is checked here.
            if looks_like_i18n_binding(attr.key):
                declaration = _parse_directive(attr.key)
                if declaration.target.kind == "text" and not text_eligible:
                    raise ValueError(
                        f"{attr.key!r} in {component_name} targets textContent, but the element body is not "
                        "exactly one translated expression."
                    )
        result[index] = I18nBindingElementAttrsNode(item, ordinal=current_ordinal, text_eligible=text_eligible)
        if text_eligible:
            expression_index = index + 1 if isinstance(result[index + 1], ExprNode) else index + 2
            result[expression_index] = I18nBoundExprNode(
                cast("ExprNode", result[expression_index]), ordinal=current_ordinal
            )
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
    from citry._vue.capture import PreparedElementCloseNode, PreparedSourceTextNode  # noqa: PLC0415

    opening = body[index + 1] if index + 1 < len(body) else None
    if isinstance(opening, ExprNode):
        closing = body[index + 2] if index + 2 < len(body) else None
        return isinstance(closing, PreparedElementCloseNode) and closing.tag == tag_name
    closing = body[index + 3] if index + 3 < len(body) else None
    return (
        index + 3 < len(body)
        and (opening == ">" or (isinstance(opening, PreparedSourceTextNode) and opening.text == ">"))
        and isinstance(body[index + 2], ExprNode)
        and (
            (isinstance(closing, str) and closing.startswith(f"</{tag_name}>"))
            or (isinstance(closing, PreparedElementCloseNode) and closing.tag == tag_name)
        )
    )


def _reject_direct_structural(attrs: tuple[Any, ...], *, tag_name: str) -> None:
    for attr in attrs:
        # A `c-` attribute carries Python data, so the render checks its name
        # instead: `c-$c-tr:...`, or a `$c-tr` key in a `c-bind` spread,
        # raises `VueCodeError` there.
        if attr.key.startswith("c-"):
            continue
        reject_translation_binding_key(attr.key, tag_name=tag_name)


def _apply_directive(
    declarations: OrderedDict[tuple[str, str | None], _Declaration],
    key: str,
    value: object,
) -> bool:
    """Record one `$c-tr` attribute written literally in the template."""
    if not looks_like_i18n_binding(key):
        return False
    declaration = _parse_directive(key)
    destination = (declaration.target.kind, declaration.target.name)
    # The parser gives a bare `$c-tr:msg` the value `True` and a written
    # value its exact text, so nothing here can come from Python data.
    if value is True:
        expression = None
    elif type(value) is str:
        # A `$c-tr:` value is an attribute value, which Vue reads with its
        # character references decoded, so `'a &amp; b'` means `'a & b'`.
        expression = decode_attribute_entities(value).strip() or None
    else:
        raise TypeError(f"{key} must be written in the template; got a {type(value).__name__} value.")
    if expression is not None:
        _validate_values_expression(expression, key=key)
        # The render cache replays a stored values expression only when a
        # template in this process wrote the same one.
        _AUTHORED_VALUES_EXPRESSIONS.add(expression)
    declaration = _Declaration(
        declaration.message,
        declaration.output,
        declaration.target,
        expression,
        expression is not None and _may_evaluate_to_null(expression),
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


# Every `$c-tr` values expression a template in this process wrote, after
# the character-reference decoding above. It grows with the templates, not the renders.
_AUTHORED_VALUES_EXPRESSIONS: set[str] = set()


def is_authored_values_expression(expression: str) -> bool:
    """Return whether a template in this process wrote this `$c-tr` values expression."""
    return expression in _AUTHORED_VALUES_EXPRESSIONS


def _may_evaluate_to_null(expression: str) -> bool:
    """Return whether a values expression contains a `null` keyword token."""
    from citry._browser_expressions import javascript_tokens  # noqa: PLC0415

    # A tokenizer, not a substring search, so `"null"` in a string, a
    # comment, or a name such as `nullable` does not count. A member name
    # (`x.null`) is a property read, not the keyword.
    tokens = javascript_tokens(expression)
    return any(
        token.kind == "identifier"
        and token.source == "null"
        and (index == 0 or tokens[index - 1].source not in {".", "?."})
        for index, token in enumerate(tokens)
    )


def _validate_values_expression(expression: str, *, key: str) -> None:
    from citry._browser_expressions import BrowserExpression, analyze_browser_expression  # noqa: PLC0415

    checked = analyze_browser_expression(BrowserExpression(expression, 0, len(expression.encode()), "expression", key))
    if not checked.valid:
        raise ValueError(f"{key} has an invalid browser named-values expression.")


def _note_provenance(
    provenance: dict[str, _CapturedTranslation | None],
    composed: set[str],
    identity: str,
    captures: list[_CapturedTranslation],
    value: object,
) -> None:
    """Record which `tr()` call, if any, produced the latest value of one attribute."""
    capture = _capture_for_value(captures, value)
    provenance[identity] = capture
    if capture is None and captures:
        composed.add(identity)
    else:
        composed.discard(identity)


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
    capture: _CapturedTranslation | None,
) -> I18nBindingRecord:
    from .extension import I18nExtension  # noqa: PLC0415

    # A destination that no `tr()` call filled has no server values; the
    # browser then translates only with what its values expression returns.
    captured_values = {} if capture is None else capture.values
    component_values = tuple(
        (name, (tagged["type"], tagged["value"]))
        for name, tagged in sorted(
            ((name, I18nExtension._tag_value(name, value)) for name, value in captured_values.items()),
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
