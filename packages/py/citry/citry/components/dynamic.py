"""
The ``<c-component>`` and ``<c-element>`` built-in components.

Two sibling tags that choose their render target at render time
(docs/design/component_dynamic.md):

- ``<c-component is="...">`` renders a *component*: ``is`` is a registered
  component name or a ``Component`` class. All other attributes become the
  target's kwargs, and the body (fills included) becomes its slots::

      <c-component c-is="table_comp" c-rows="rows">
        <c-fill name="pagination"><c-pagination /></c-fill>
      </c-component>

- ``<c-element is="...">`` renders a *plain HTML element*: ``is`` is the tag
  name, decided at render time. All other attributes become the element's
  HTML attributes, and the body becomes its children::

      <c-element c-is="form_content_tag" class="form-content">
        ...children...
      </c-element>

Any tag name is accepted by ``<c-element>`` (custom web components included),
the same trust statically written HTML gets. A misspelled *component* name
still fails loudly, because ``<c-component>`` never falls back to elements.

Both tags' static-`is` forms never reach these classes: the compiler turns
``<c-component is="MyComp">`` into the named component and
``<c-element is="div">`` (with no fills) into the literal element, so only
the dynamic forms (``c-is``, or ``is`` via ``c-bind``) resolve here.

Each ``Citry`` instance gets its own subclasses, created lazily by
``make_builtin_components`` (a Component class binds to one Citry instance at
class-definition time, so the built-ins cannot be shared).
"""

from __future__ import annotations

import re
import weakref
from typing import TYPE_CHECKING, Any, cast

from citry.attrs import (
    C_ELEMENT_HANDLER_FIX,
    C_ELEMENT_MARKER_FIX,
    format_attrs,
    merge_attrs,
    reject_citry_marker_attr_name,
    reject_script_capable_attr_name,
    validate_html_attr_name,
)
from citry.citry_element import CitryElement
from citry.citry_render import CitryRender
from citry.client_directives import (
    CLIENT_PROPS_ATTR,
    apply_client_props_contribution,
    has_client_props_key,
)
from citry.component import Component
from citry.component_registry import _VALID_NAME_RE, NotRegistered
from citry.constness import _ConstMapping, _restore_const_identities, const_value
from citry.util.html import _REFUSED_DYNAMIC_ELEMENT_TAGS, FOREIGN_CONTENT_TAGS, Markup
from citry_core.template_parser import HTML_VOID_ELEMENTS

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Sequence

    from citry.citry import Citry
    from citry.slots import Slot


_ELEMENT_KEY_ATTR = "data-citry-key"
# A `<script` start tag in template text, in any letter case.
_SCRIPT_START_RE = re.compile(r"<script[\s/>]", re.IGNORECASE)
_ELEMENT_MORPH_ATTR = "data-citry-morph"
# Every `element` built-in class, one per Citry instance. The body check skips
# a nested element's own tags only for these, never for a user component.
_DYNAMIC_ELEMENT_CLASSES: weakref.WeakSet[type[Component]] = weakref.WeakSet()


class _DynamicSelectorElement(CitryElement):
    """Retain authored call restrictions while selector input hooks choose a target."""

    __slots__ = ("contains_fills", "has_range_directives")
    contains_fills: bool
    has_range_directives: bool


def _simple_selector_target(component: Component, target: type[Component], kwargs: dict[str, Any]) -> CitryElement:
    """Keep the ordinary selector as owner when its selected target has no instance."""
    shape = getattr(component, "_selector_call_shape", (False, False))
    if any(shape) or component._element_morph_metadata is not None:
        raise TypeError(
            f"Component {target.__name__} uses simple=True; named fills and range directives are unsupported."
        )
    if component._component_tag_client_bindings:
        raise TypeError(f"Component {target.__name__} uses simple=True; component bindings are unsupported.")
    return CitryElement(target, kwargs, component.raw_slots)


def make_dynamic_component(citry_instance: Citry) -> type[Component]:
    """Create (and thereby register) the ``<c-component>`` component for one Citry instance."""

    class DynamicComponent(Component, _citry_builtin=citry_instance._registry._builtin_registration_token):
        """
        Render the component named by ``is`` in this tag's place.

        ``is`` (required) is a registered component name or a ``Component``
        class; every other attribute is passed to it as a kwarg, and the
        body (fills included) as its slots.
        """

        citry = citry_instance
        name = "component"
        transparent = True
        _citry_dynamic_selector = True

        def template_data(
            self,
            kwargs: Any,  # noqa: ARG002
            slots: Any,  # noqa: ARG002
        ) -> dict[str, Any]:
            data = cast("_ConstMapping", self.raw_kwargs.copy())
            _restore_const_identities(data, self._kwargs_const._const_values)
            comp_cls = _resolve_component(self, const_value(data.pop("is", None)))
            if citry_instance._is_builtin_component(comp_cls) and comp_cls.name == "mark":
                raise TypeError(
                    'Dynamic component selection cannot select <c-mark>; use a literal <c-mark name="..."> tag.'
                )
            if comp_cls.simple is True:
                return {"target": _simple_selector_target(self, comp_cls, data)}
            # The target renders in this tag's place: remaining kwargs and the
            # full slots pass through, so the target's own Kwargs/Slots
            # validation speaks for unexpected inputs.
            target = _DynamicSelectorElement(
                comp_cls,
                data,
                self.raw_slots,
                component_tag_client_bindings=self._component_tag_client_bindings,
                prepared_call_metadata=self._prepared_call_metadata,
            )
            target.contains_fills, target.has_range_directives = getattr(self, "_selector_call_shape", (False, False))
            return {"target": target}

        template = """
          {{ target }}
        """.strip()

    return DynamicComponent


def _resolve_component(component: Component, value: Any) -> type[Component]:
    """Resolve the ``is`` value of ``<c-component>`` to a component class."""
    if not value:
        msg = "<c-component> requires an 'is' value: a registered component name or a Component class."
        raise TypeError(msg)
    if isinstance(value, str):
        try:
            return component.citry.get(value)
        except NotRegistered as err:
            msg = f"{err} To render a plain HTML element, use <c-element> instead."
            raise NotRegistered(msg) from err
    if isinstance(value, type) and issubclass(value, Component):
        return value
    if isinstance(value, CitryElement):
        msg = (
            "<c-component> 'is' got an already-composed element. Embed it with '{{ ... }}' instead, or pass its class."
        )
        raise TypeError(msg)
    msg = f"<c-component> 'is' must be a component name or a Component class, got {type(value).__name__}."
    raise TypeError(msg)


def make_dynamic_element(citry_instance: Citry) -> type[Component]:
    """Create (and thereby register) the ``<c-element>`` component for one Citry instance."""

    class DynamicElement(Component, _citry_builtin=citry_instance._registry._builtin_registration_token):
        """
        Render a plain HTML element whose tag name is the ``is`` value.

        ``is`` (required) is the tag name; every other attribute becomes an
        HTML attribute of the element, and the body its children. Void
        elements (``br``, ``img``, ...) reject a body.
        """

        citry = citry_instance
        name = "element"
        transparent = True
        # The open/close tags are computed values: one generic class covers
        # every tag name, instead of a synthesized class per name
        # (docs/design/component_dynamic.md section 5.1).
        # Keep the three tokens adjacent: whitespace here would become content
        # inside or beside the selected HTML element.
        template = """\
{{ open }}<c-slot />{{ close }}\
"""

        def template_data(
            self,
            kwargs: Any,  # noqa: ARG002
            slots: Any,  # noqa: ARG002
        ) -> dict[str, Any]:
            attrs = dict(self.raw_kwargs)
            tag = const_value(_pop_html_attr(attrs, "is"))
            _validate_tag_name(tag)
            _reject_named_fills(self.raw_slots)
            # on_render reads this once the body has rendered, to check what
            # the body holds under a selected <svg> or <math>.
            self._selected_tag = tag
            # The node path (the older node classes, used when a slot renders
            # outside the page render) takes the branch below that records the
            # opening and closing tags it writes, so the check can tell them
            # from the body. The prepared branch writes typed parts instead.
            self._node_path_tags: tuple[str, str] | None = None

            resolved_attrs = _resolve_element_attrs(self, tag, attrs)

            from citry._vue.capture import prepared_render_active  # noqa: PLC0415

            if prepared_render_active():
                from citry._vue.capture import (  # noqa: PLC0415
                    PreparedDynamicElementClose,
                    UnsupportedPreparedView,
                    is_vue_directive_name,
                    prepared_dynamic_element_open,
                )

                is_void = tag.lower() in HTML_VOID_ELEMENTS
                metadata = self._element_morph_metadata
                # The parser rejects '#c-ignore' on <c-element>, so only a
                # node tree built by hand can carry it here; fail the same way.
                if metadata is not None and metadata.morph_mode is not None:
                    msg = (
                        f"'#c-ignore' is not supported on <c-element> (rendered as <{tag}>). Write the"
                        f" element as a plain HTML tag, such as <{tag} #c-ignore>, to keep its contents as"
                        " the server first rendered them."
                    )
                    raise TypeError(msg)
                authored_bindings = () if metadata is None else metadata.authored_bindings
                retained_bindings = []
                for binding in authored_bindings:
                    if (
                        binding.key in resolved_attrs
                        and type(resolved_attrs[binding.key]) is type(binding.value)
                        and resolved_attrs[binding.key] == binding.value
                    ):
                        retained_bindings.append(binding)
                        resolved_attrs.pop(binding.key)
                executable = [name for name in resolved_attrs if isinstance(name, str) and is_vue_directive_name(name)]
                # Raise the same type as every other Vue-syntax rejection, so callers catch one type.
                if executable:
                    raise UnsupportedPreparedView(
                        "prepared dynamic <c-element> does not support tag-dependent or executable Vue "
                        f"attributes: {', '.join(executable)}"
                    )
                from citry.ext.events.bindings import RUNTIME_CONTROL_ATTR, RUNTIME_EVENTS_ATTR  # noqa: PLC0415

                event_bindings = () if metadata is None else metadata.event_bindings
                poll_bindings = () if metadata is None else metadata.poll_bindings
                control_bindings = () if metadata is None else metadata.control_bindings
                normalized = None
                if (
                    event_bindings
                    or poll_bindings
                    or control_bindings
                    or (metadata is not None and metadata.runtime_events_candidate)
                    or RUNTIME_EVENTS_ATTR in resolved_attrs
                    or RUNTIME_CONTROL_ATTR in resolved_attrs
                ):
                    from citry._vue.capture import PreparedElementOpenNode  # noqa: PLC0415
                    from citry.citry_context import CitryContext  # noqa: PLC0415

                    call = self._prepared_call_metadata
                    if call is None or type(call.source) is not str:
                        raise TypeError("dynamic element Events metadata lost authored source provenance")
                    normalizer = PreparedElementOpenNode(
                        call.source,
                        call.source_span,
                        tag,
                        (),
                        (),
                        is_void,
                        False,  # noqa: FBT003
                        (),
                        event_bindings,
                        poll_bindings,
                        control_bindings,
                    )
                    normalizer._runtime_events_candidate = (
                        metadata is not None and metadata.runtime_events_candidate
                    ) or RUNTIME_EVENTS_ATTR in resolved_attrs
                    normalized = normalizer._prepared_from_resolved(
                        resolved_attrs,
                        context=CitryContext(component=self),
                        extension_validated=True,
                        owner_name=None if metadata is None else metadata.owner_name,
                    )
                    resolved_attrs = dict(normalized.data_attrs)
                if is_void and self.raw_slots:
                    msg = f"<c-element>: void element '{tag}' cannot have children."
                    raise ValueError(msg)
                return {
                    "open": prepared_dynamic_element_open(
                        tag,
                        resolved_attrs,
                        authored_bindings=tuple(retained_bindings),
                        key=None if metadata is None else metadata.key,
                        normalized=normalized,
                    ),
                    "close": "" if is_void else PreparedDynamicElementClose(tag),
                }

            attr_str = _format_resolved_element_attrs(resolved_attrs)

            # Void elements cannot have children; the empty open/close pair
            # below otherwise brackets the default slot (the tag's body).
            if tag.lower() in HTML_VOID_ELEMENTS:
                if self.raw_slots:
                    msg = f"<c-element>: void element '{tag}' cannot have children."
                    raise ValueError(msg)
                return {"open": Markup("<{}{}/>").format(tag, attr_str), "close": ""}
            open_tag = Markup("<{}{}>").format(tag, attr_str)
            close_tag = Markup("</{}>").format(tag)
            # These two values are the element's own tags, not its body. The
            # foreign-content check (`reject_trusted_html_in_selected_foreign_element`)
            # skips exactly these, first and last, so a plain-text body under a
            # selected <svg> still renders here.
            self._node_path_tags = (str.__str__(open_tag), str.__str__(close_tag))
            return {"open": open_tag, "close": close_tag}

        def on_render(self) -> Any:
            # Only a selected <svg> or <math> (or a MathML `mglyph` or
            # `malignmark`, see FOREIGN_CONTENT_TAGS) changes how the browser
            # reads the body, so every other tag skips the after-render check.
            tag = getattr(self, "_selected_tag", None)
            if not isinstance(tag, str) or tag.lower() not in FOREIGN_CONTENT_TAGS:
                return None
            # The check runs while the page renders, before Citry picks the
            # static or the Vue writer, so no writer and no fallback between
            # them can skip it.
            return _check_foreign_body_after_render(tag, self)

    _DYNAMIC_ELEMENT_CLASSES.add(DynamicElement)
    return DynamicElement


def _check_foreign_body_after_render(
    tag: str, element: Component
) -> Generator[None, tuple[CitryRender | None, Exception | None], None]:
    """Render the template as usual, then check the finished body of a selected `<svg>` or `<math>`."""
    result, error = yield
    # A failed render already carries its own error; let it bubble.
    if error is None and result is not None:
        # template_data sets it during the render, so read it only afterwards.
        own_tags = getattr(element, "_node_path_tags", None)
        reject_trusted_html_in_selected_foreign_element(tag, result.parts, node_path_tags=own_tags)


def _node_path_element_body(
    parts: Sequence[object], own_tags: tuple[str, str]
) -> tuple[Sequence[object], Component | None] | None:
    """
    Split a `<c-element>` render from the node path into its body and the component that wrote the body.

    The node path writes the element as three parts: its opening tag, its
    default slot (the body), and its closing tag. Each tag is a `Markup`
    value, or, once the element's own template has been compiled for the
    page render, a `PreparedTrustedHtmlValue`. Return `None` for any other
    shape, so the caller checks every part, tags included, and refuses
    rather than guesses.
    """
    from citry._vue.direct import DirectSlotRender  # noqa: PLC0415

    if len(parts) != 3:
        return None
    opening, body, closing = parts
    # Compare the exact type and text, and only at the first and last place,
    # so only the two values template_data wrote match, never a body value.
    if _own_tag_text(opening) != own_tags[0] or _own_tag_text(closing) != own_tags[1]:
        return None
    # The body is the default slot, rendered in the scope of the template
    # that wrote the `<c-element>` tag. Any other shape is not this layout.
    if (
        not isinstance(body, CitryRender)
        or isinstance(body, DirectSlotRender)
        or body.frame.is_component_root
        or body.frame.is_transparent_root
    ):
        return None
    return body.parts, body.context.component


def _own_tag_text(part: object) -> str | None:
    """Return the HTML of a part that can hold one of the element's own tags, or `None` for any other part."""
    from citry._vue.capture import PreparedTrustedHtmlValue  # noqa: PLC0415

    # Exact types only: a subclass is a value from somewhere else.
    if type(part) is Markup:
        return str.__str__(part)
    if type(part) is PreparedTrustedHtmlValue:
        return part.html
    return None


def reject_trusted_html_in_selected_foreign_element(
    tag: str, parts: Iterable[object], *, node_path_tags: tuple[str, str] | None = None
) -> None:
    """
    Raise `ValueError` when the body of a data-selected `<svg>` or `<math>` holds HTML Citry does not escape.

    Inside `<svg>` or `<math>`, and inside `mglyph` or `malignmark` within a
    MathML text element (`FOREIGN_CONTENT_TAGS`), the browser reads
    `<style>`, `<title>`, `<textarea>`, `<noscript>` and the other elements
    whose contents HTML keeps as text as ordinary elements, so trusted HTML
    that stays inert inside a `<div>` can run there. A tag name chosen by
    data must not put trusted HTML where the browser reads it this way, so
    the body may hold only what the template wrote: text, escaped `{{ }}`
    values, plain elements, nested `<c-element>` tags, and the control flow
    around them. A `Markup` value
    that holds a tag, a `<c-raw>` block, a child component, and slot content
    are refused, because each can carry HTML that Citry writes as is. So is
    a `<script>` the template wrote, because inside `<svg>` the browser
    decodes the escaped values in it. The
    Vue writer refuses `Markup` and `<c-raw>` under any `<svg>` or `<math>`.

    Every render path runs this one check, from the element's `on_render`
    hook while the page renders, before Citry picks the static or the Vue
    writer: the ordinary render, `simple=True`, the component cache, loops,
    components with `js`, and an Events `Render`. The older node classes
    (the node path, used for example by `str(slot)` after the page render
    or a slot rendered in a worker thread) write the element's own tags as
    trusted HTML values; `node_path_tags` names those two values so the
    check skips them and reads only the body.
    """
    from citry._vue.capture import (  # noqa: PLC0415
        PreparedDynamicElementClose,
        PreparedDynamicElementOpen,
        PreparedElementClose,
        PreparedElementOpen,
        PreparedSourceText,
        PreparedStaticRun,
        PreparedTextValue,
        PreparedTrustedHtmlValue,
        PreparedVerbatimHtml,
    )
    from citry._vue.direct import DirectSlotRender  # noqa: PLC0415

    # Template-written structure and escaped values: safe under any parent.
    template_parts = (
        PreparedSourceText,
        PreparedTextValue,
        PreparedElementOpen,
        PreparedElementClose,
        PreparedStaticRun,
        PreparedDynamicElementOpen,
        PreparedDynamicElementClose,
    )
    # The element's own output is its opening, its body (the default slot,
    # which is the fill written in the calling template), and its closing.
    top: Sequence[object] = parts if isinstance(parts, list | tuple) else list(parts)
    # On the node path the element's own tags arrive as trusted HTML, and
    # slot content arrives as an ordinary render from the component that
    # wrote the fill, so the check needs the component that wrote the body.
    on_node_path = node_path_tags is not None
    owner: Component | None = None
    if node_path_tags is not None:
        split = _node_path_element_body(top, node_path_tags)
        # An unexpected shape keeps the tags in the walk, so they are refused.
        if split is not None:
            top, owner = split
    pending: list[object] = []
    for part in top:
        pending.extend(part.parts if isinstance(part, DirectSlotRender) else (part,))
    while pending:
        part = pending.pop()
        if isinstance(part, PreparedElementOpen) and part.tag.lower() == "script":
            # Under <svg> the browser decodes character references inside
            # <script>, so an escaped `{{ }}` value there could leave a
            # JavaScript string; HTML keeps them as written.
            what = "a <script> element"
        elif type(part) is str and _SCRIPT_START_RE.search(part):
            # The older node classes write the template's own tags as plain
            # text, so a <script> the template wrote shows up here.
            what = "a <script> element"
        elif isinstance(part, template_parts) or type(part) is str:
            # A plain `str` is template text: the older node classes, used for
            # example when an extension renders a template's foreign spans,
            # write the template's own tags this way.
            continue
        elif isinstance(part, CitryRender):
            nested = part.parts
            # A nested <c-element> renders as its opening, its body (the fill
            # written in this same template), and its closing.
            if (
                part.frame.is_transparent_root
                and nested
                and isinstance(nested[0], PreparedDynamicElementOpen)
                and isinstance(nested[-1], PreparedDynamicElementClose)
            ):
                for inner in nested:
                    pending.extend(inner.parts if isinstance(inner, DirectSlotRender) else (inner,))
                continue
            # The same nested <c-element> on the node path: its own tags
            # around a body written by the same template.
            nested_component = part.context.component
            inner_tags = getattr(nested_component, "_node_path_tags", None)
            if (
                on_node_path
                and part.frame.is_transparent_root
                and type(nested_component) in _DYNAMIC_ELEMENT_CLASSES
                and inner_tags is not None
            ):
                inner_split = _node_path_element_body(nested, inner_tags)
                if inner_split is not None and inner_split[1] is owner:
                    pending.extend(inner_split[0])
                    continue
            if isinstance(part, DirectSlotRender):
                what = "slot content (a <c-slot> in the body)"
            elif part.frame.is_component_root or part.frame.is_transparent_root:
                what = "a child component"
            elif on_node_path and part.context.component is not owner:
                # A fill renders in the scope of the component that wrote it,
                # so a render owned by another component is slot content.
                what = "slot content (a <c-slot> in the body)"
            else:
                # Control flow such as <c-if> or <c-for> nests its output.
                pending.extend(nested)
                continue
        elif isinstance(part, (PreparedTrustedHtmlValue, Markup)):
            html = part.html if isinstance(part, PreparedTrustedHtmlValue) else str.__str__(part)
            # HTML without a '<' is text with character references, which
            # reads the same inside <svg> as inside a <div>. The older node
            # classes also write each escaped `{{ }}` value as such a Markup.
            if "<" not in html:
                continue
            what = "a Markup value (trusted HTML from Python)"
        elif isinstance(part, PreparedVerbatimHtml):
            what = "a <c-raw> block"
        else:
            # Anything else is a child component not written out yet, a leaf
            # program, or HTML this check cannot read: refuse it rather than guess.
            what = "content Citry cannot check"
        msg = (
            f"<c-element> rendered <{tag}> from a tag name chosen at render time, and its body holds {what}. "
            f"Inside <{tag}> the browser reads <style>, <textarea>, <noscript> and similar elements as markup, "
            "so HTML that is inert elsewhere can run there. Write the "
            f"<{tag}> element directly in the template (for example in a c-if branch), or keep the body to "
            "text, {{ }} values, and elements other than <script> written in the template."
        )
        raise ValueError(msg)


def _pop_html_attr(attrs: dict[str, Any], name: str) -> Any:
    """Pop one ASCII-case-insensitive HTML attribute, preserving authored spelling elsewhere."""
    authored_name = next((key for key in attrs if key.lower() == name), None)
    return attrs.pop(authored_name) if authored_name is not None else None


def _validate_tag_name(tag: Any) -> None:
    """
    Reject ``is`` values that are not syntactically valid tag names.

    The tag name lands verbatim in the output (the attribute *values* are
    escaped by ``format_attrs``), so this check is also what keeps the
    interpolation in ``template_data`` safe.
    """
    if not tag or not isinstance(tag, str):
        msg = f"<c-element> requires an 'is' value naming the HTML tag, got {type(tag).__name__}."
        raise TypeError(msg)
    if not _VALID_NAME_RE.fullmatch(tag):
        msg = (
            f"<c-element>: {tag!r} is not a valid HTML tag name. "
            f"Must start with a letter and contain only letters, digits, hyphens, underscores, or dots."
        )
        raise ValueError(msg)
    # The browser ignores ASCII letter case in tag names, so compare the lowercased
    # name. `str.lower()` also lowercases other letters, which can only refuse more names.
    if tag.lower() in _REFUSED_DYNAMIC_ELEMENT_TAGS:
        msg = (
            f"<c-element> cannot render a <{tag}> element, because the browser handles that element in a "
            "special way: it runs or loads it, reads its contents as raw text rather than as escaped HTML, or "
            "changes how it reads the rest of the page. "
            f"Write the <{tag}> element directly in the template, for example in a c-if branch."
        )
        raise ValueError(msg)


def _reject_named_fills(raw_slots: dict[str, Slot]) -> None:
    """
    Reject named fills: an element has children, but no named slots.

    Static named fills are already parse errors (the Rust slot rules); this
    catches the dynamic spellings (``c-name`` fills, ``c-bind`` slots) that
    only resolve at render time.
    """
    named = sorted(name for name in raw_slots if name != "default")
    if named:
        msg = f"<c-element> only accepts the default slot (the tag's body); got fills named: {', '.join(named)}."
        raise ValueError(msg)


def _resolve_element_attrs(renderer: Component, tag: str, attrs: dict[str, Any]) -> dict[str, Any]:
    """
    Format the element's attributes the way a statically written element's
    are: normalize class/style, drop ``False``/``None``, fire the
    ``on_attrs_resolved`` extension hook, escape values (``attrs.py`` is the
    shared value layer; docs/design/template_html_attrs.md).

    Returns empty ``Markup`` or trusted attributes with a leading space
    (`` class="btn"``).
    """
    contributions = {key: const_value(value) for key, value in attrs.items()}
    # Every name reaching this element arrives as a kwarg, whether a template
    # wrote it, a c-bind mapping or <c-component c-is> passed it on, or Python
    # code called the element directly, so one check here covers every route.
    from citry.nodes import _reject_reserved_events_attr  # noqa: PLC0415

    for key in contributions:
        name = validate_html_attr_name(key, where="<c-element>")
        _reject_reserved_events_attr(name, tag_name=tag)
        reject_script_capable_attr_name(name, tag_name=tag, where="<c-element>", fix=C_ELEMENT_HANDLER_FIX)
        reject_citry_marker_attr_name(name, tag_name=tag, where="<c-element>", fix=C_ELEMENT_MARKER_FIX)
    for value in contributions.values():
        # A nested-template attribute value resolves to a CitryRender, whose
        # parts may hold not-yet-rendered child components, so it cannot be
        # flattened to a string here. The static-`is` form supports it (it
        # compiles to a real element); the dynamic form rejects it.
        if isinstance(value, CitryRender):
            msg = (
                "<c-element> with a dynamic 'is' does not support nested-template attribute "
                'values. Use a static is="...", or precompute the value in template_data().'
            )
            raise TypeError(msg)

    merged = merge_attrs(contributions)
    _reject_element_metadata_conflicts(renderer, merged)
    # Validate case variants before None/False removal. The canonical key may
    # be removed, but a noncanonical spelling is always an authoring error.
    has_client_props_key(merged, tag_name=tag)
    resolved = {key: value for key, value in merged.items() if value is not None and value is not False}
    if has_client_props_key(resolved, tag_name=tag):
        apply_client_props_contribution(
            resolved,
            resolved[CLIENT_PROPS_ATTR],
            tag_name=tag,
            component_boundary=False,
        )
    # DynamicElement is the renderer that owns private morph metadata, but it
    # is transparent: bindings and every other element-level extension belong
    # to the component whose template authored the <c-element> invocation.
    # A programmatically rendered DynamicElement has no parent, so retain the
    # renderer as the only available owner in that uncommon root case.
    owner = renderer.parent or renderer
    resolved = renderer.citry.extensions.on_attrs_resolved(
        component=owner,
        tag_name=tag,
        attrs=resolved,
    )
    if has_client_props_key(resolved, tag_name=tag):
        apply_client_props_contribution(
            resolved,
            resolved[CLIENT_PROPS_ATTR],
            tag_name=tag,
            component_boundary=False,
        )
    _reject_element_metadata_conflicts(renderer, resolved)
    metadata = renderer._element_morph_metadata
    if metadata is not None:
        if metadata.key is not None:
            resolved[_ELEMENT_KEY_ATTR] = f":{metadata.key}"
        if metadata.morph_mode == "ignore":
            resolved[_ELEMENT_MORPH_ATTR] = "ignore"
    return dict(resolved)


def _format_resolved_element_attrs(resolved: dict[str, Any]) -> Markup:
    formatted = format_attrs(resolved)
    return Markup(" {}").format(formatted) if formatted else Markup("")


def _format_element_attrs(renderer: Component, tag: str, attrs: dict[str, Any]) -> Markup:
    """Compatibility wrapper for ordinary serialization and focused tests."""
    return _format_resolved_element_attrs(_resolve_element_attrs(renderer, tag, attrs))


def _reject_element_metadata_conflicts(component: Component, attrs: dict[str, Any]) -> None:
    """Keep private dynamic-element directives authoritative and single-valued."""
    metadata = component._element_morph_metadata
    if metadata is None:
        return
    protected = set()
    if metadata.key is not None:
        protected.add(_ELEMENT_KEY_ATTR)
    if metadata.morph_mode is not None:
        protected.add(_ELEMENT_MORPH_ATTR)
    for key in attrs:
        if isinstance(key, str) and key.lower() in protected:
            msg = (
                f"<c-element> attribute {key!r} conflicts with its private "
                f"#{'c-key' if key.lower() == _ELEMENT_KEY_ATTR else 'c-ignore'} metadata."
            )
            raise ValueError(msg)
