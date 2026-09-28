"""Private two-phase Vue document serialization."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass, replace
from html import escape
from html.parser import HTMLParser
from secrets import token_hex
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlsplit

from citry._csp_validation import _CspRenderValidator
from citry._owned_resource import OWNED_ASSET_CROSSORIGIN
from citry._vue.capture import PreparedElementOpen
from citry._vue.document import typed_document_shell
from citry.attrs import format_attrs
from citry.citry_render import CitryRender, SimpleVueRecord, simple_vue_called_components
from citry.ext.dependencies.extension import DependenciesExtension
from citry.ext.dependencies.scripts import has_component_asset
from citry.ext.dependencies.types import DependencyRecord, Script, Style
from citry.util.html import script_json
from citry.util.id import validate_render_id
from citry_core import _rust

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from citry._javascript_policy import _JavascriptPolicy
    from citry._serialization_security import _ScriptSecurityMaterializer
    from citry.citry_context import CitryContext
    from citry.ext.events.emission import EventInstanceEntry
    from citry.extension import OnSerializeContext
    from citry.settings import SecurityCspMode, SecurityJavascriptMode


_BODY_OPEN_RE = re.compile(r"<body(?:\s[^>]*)?>", re.IGNORECASE)
_BODY_CLOSE_RE = re.compile(r"</body\s*>", re.IGNORECASE)
# The latest hydration decision for one serialization (a HydrationAdmission).
_HYDRATION_ADMISSION_EXTRA_KEY = "_citry_hydration_admission"
# Capture the supported built-in insertion methods before application code can
# replace class attributes. The hydration fast path admits no custom hook.
_BUILTIN_DEPENDENCIES_ON_SERIALIZE = DependenciesExtension.on_serialize
_BUILTIN_DEPENDENCIES_INTERNAL_ON_SERIALIZE = DependenciesExtension._on_serialize_internal
_VOID_HTML_TAGS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)


@dataclass(frozen=True, slots=True)
class _ScriptPreload:
    """One admitted initial script fetch that a head link can start early."""

    url: str
    integrity: str | None
    attrs: tuple[tuple[str, str | bool], ...] = ()


_PRELOAD_FETCH_ATTRS = frozenset({"integrity", "crossorigin", "referrerpolicy", "fetchpriority"})
_PRELOAD_HEAD_SCAN_LIMIT = 65_536
_PRELOAD_HEAD_CHUNK_SIZE = 1_024


class _PreloadHeadLocator(HTMLParser):
    """Locate one physical head without matching tag-like text inside scripts."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.head_starts: list[int] = []
        self.head_ends: list[int] = []
        self.has_base = False
        self.unsupported_head_content = False
        self._in_head = False
        self._line_starts: list[int] = [0]

    def feed_document(self, html: str) -> None:
        self._line_starts = [0]
        offset = 0
        limit = min(len(html), _PRELOAD_HEAD_SCAN_LIMIT)
        while offset < limit and not self.head_ends:
            chunk = html[offset : min(offset + _PRELOAD_HEAD_CHUNK_SIZE, limit)]
            self._line_starts.extend(offset + index + 1 for index, char in enumerate(chunk) if char == "\n")
            self.feed(chunk)
            offset += len(chunk)
        self.close()

    def _offset(self) -> int:
        line, column = self.getpos()
        return self._line_starts[line - 1] + column

    # ``attrs`` is part of the HTMLParser callback signature; the head scan only needs the tag name.
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # noqa: ARG002
        if tag == "head":
            self.head_starts.append(self._offset() + len(self.get_starttag_text() or ""))
            self._in_head = True
        elif tag == "base" and self._in_head:
            self.has_base = True
        elif tag in {"template", "noscript"} and self._in_head:
            self.unsupported_head_content = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "head":
            self.head_ends.append(self._offset())
            self._in_head = False


def _preloadable_url(url: object) -> bool:
    """Keep hints on ordinary HTTP fetches with the browser's URL rules."""
    if type(url) is not str or not url or any(char.isspace() or ord(char) < 0x20 or char == "\\" for char in url):
        return False
    try:
        parsed = urlsplit(url)
        if parsed.scheme:
            if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname or parsed.username is not None:
                return False
            _ = parsed.port
            return True
        if url.startswith("//"):
            parsed = urlsplit("https:" + url)
            if not parsed.hostname or parsed.username is not None:
                return False
            _ = parsed.port
            return True
        return bool(parsed.path)
    except ValueError:
        return False


def _sha256_sri(digest: object) -> str | None:
    if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        return None
    return "sha256-" + base64.b64encode(bytes.fromhex(digest)).decode("ascii")


def _manifest_script_preloads(manifest: dict[str, object]) -> tuple[_ScriptPreload, ...]:
    """Copy only fetch descriptors the browser's initial loader can preload."""
    output: list[_ScriptPreload] = []
    definitions = manifest.get("definitions")
    if type(definitions) is list:
        for item in definitions:
            if type(item) is not dict:
                continue
            url, integrity = item.get("url"), _sha256_sri(item.get("sha256"))
            if integrity is not None and _preloadable_url(url):
                # The runtime requests definitions with this crossorigin value;
                # a hint with another value would not be reused.
                output.append(_ScriptPreload(cast("str", url), integrity, (("crossorigin", OWNED_ASSET_CROSSORIGIN),)))

    scripts = manifest.get("scripts")
    if type(scripts) is list:
        for item in scripts:
            source = item.get("source") if type(item) is dict else None
            if type(source) is not dict:
                continue
            url, kind = source.get("url"), source.get("kind")
            raw_attrs = source.get("attrs", {})
            if (
                not _preloadable_url(url)
                or type(raw_attrs) is not dict
                or any(name not in _PRELOAD_FETCH_ATTRS for name in raw_attrs)
                or any(type(value) not in (str, bool) for value in raw_attrs.values())
            ):
                continue
            attrs = dict(raw_attrs)
            if kind == "owned":
                integrity = _sha256_sri(source.get("sha256"))
                if integrity is None:
                    continue
                # Match the runtime, which adds this value to an owned asset
                # unless the author declared crossorigin.
                attrs.setdefault("crossorigin", OWNED_ASSET_CROSSORIGIN)
            elif kind == "external":
                integrity = attrs.get("integrity")
                if integrity is not None and type(integrity) is not str:
                    continue
                if integrity is not None:
                    from citry._serialization_security import _parse_integrity  # noqa: PLC0415

                    try:
                        _parse_integrity(integrity)
                    except ValueError:
                        continue
            else:
                continue
            attrs.pop("integrity", None)
            output.append(_ScriptPreload(cast("str", url), integrity, tuple(attrs.items())))
    return tuple(output)


def _render_script_preloads(preloads: tuple[_ScriptPreload, ...], nonce: str | None) -> str:
    rendered: list[str] = []
    seen: set[tuple[object, ...]] = set()
    for preload in preloads:
        if not _preloadable_url(preload.url):
            continue
        key = (preload.url, preload.integrity, preload.attrs, nonce)
        if key in seen:
            continue
        seen.add(key)
        attrs: dict[str, str | bool] = {"rel": "preload", "as": "script", "href": preload.url}
        if preload.integrity is not None:
            attrs["integrity"] = preload.integrity
        attrs.update(preload.attrs)
        if nonce is not None:
            attrs["nonce"] = nonce
        attrs_text = str(format_attrs(attrs))
        rendered.append(f"<link {attrs_text}/>")
    return "".join(rendered)


def _insert_script_preloads(html: str, content: str) -> str:
    """Insert hints at the end of one safe physical head."""
    if not content:
        return html
    locator = _PreloadHeadLocator()
    # Preload hints are only a speed-up, so any parser failure on unusual
    # markup leaves the page exactly as rendered instead of failing it.
    try:
        locator.feed_document(html)
    except Exception:  # noqa: BLE001
        return html
    if (
        locator.has_base
        or locator.unsupported_head_content
        or len(locator.head_starts) != 1
        or len(locator.head_ends) != 1
    ):
        return html
    start, end = locator.head_starts[0], locator.head_ends[0]
    if end < start:
        return html
    return html[:end] + content + html[end:]


@dataclass(frozen=True, slots=True)
class HydrationDecline:
    """
    One part of a page the server did not write for Vue to adopt.

    ``code`` names the rule that declined the part and ``detail`` narrows it
    (a tag, an attribute name, or the construct, such as ``text`` or
    ``v-if``). ``component`` is the type key of the component whose render
    holds the part (its registered type key, such as ``Leaf_b874fa``).
    ``outcome`` says what happened because of it:
    ``"shell"`` means Vue builds the contents of the nearest enclosing
    element (``shell_tag``) in the browser; ``"page"`` means no element
    separated the part from the page root, so the whole page mounts in the
    browser. ``shell_content`` is ``True`` when that element carries Citry's
    HTML for its contents, which the browser shows until the runtime removes
    it right before Vue hydrates, and ``False`` when it is sent empty (its
    contents would hold a ``<script>`` or something else that runs or loads
    again when Vue rebuilds them, or the browser's parser would move them).

    Codes for values only the browser knows: ``browser-value`` (an attribute
    or expression reading component state, an injection or a prop),
    ``browser-text``, ``browser-condition`` (a ``v-if`` test) and
    ``browser-list`` (a ``v-for`` source). Codes for what the server does not
    write the way Vue does: ``unsupported-attribute``, ``unsupported-tag``,
    ``unsupported-directive``, ``unsupported-comment``, ``text-value`` (a NUL
    or carriage return in text or an attribute value, or a leading newline the
    parser would drop), ``parser-repair`` (an element the browser's HTML
    parser would move), ``opaque-html`` (HTML Python hands over as a finished
    string, such as ``<c-raw>`` contents, that the page's parser would change,
    that holds a ``<script>``, or that starts with a comment),
    ``component-text-root`` (a component whose render is one text node),
    ``component-attrs``
    (attributes passed to a component), ``component-lookup`` (a component
    whose occurrence or render program is missing, including one whose render
    function could not be read), ``slot-props`` (a scoped slot),
    ``dynamic-slots``, ``dynamic-component``, ``dynamic-attribute-name``,
    ``render-shape``, ``render-helper``, ``nesting-depth`` and ``host-root``
    (text directly inside the Vue host element).
    """

    code: str
    detail: str
    component: str | None
    outcome: str = "page"
    shell_tag: str | None = None
    shell_content: bool = False


@dataclass(frozen=True, slots=True)
class HydrationAdmission:
    """
    Why one serialization did or did not hydrate its server HTML.

    ``reason`` is the page-level code when the page mounts in the browser
    (``None`` when it hydrates). ``server_html`` is ``True`` when such a
    page still carries Citry's ordinary server HTML inside its Vue host,
    which Vue replaces when it mounts; it is ``False`` for a page that
    hydrates and for a page sent with an empty host (``ssr-disabled``,
    ``below-threshold``, ``not-a-document``, or a body that holds a
    ``<script>`` element, which would run once before Vue replaced it). ``element_count`` counts the elements the
    server writes for Vue to adopt, shells included, and is ``None`` when the
    page was not rendered for hydration or rendering stopped at the page
    root. ``threshold`` is the page-size setting it was compared with and
    ``shell_count`` the number of elements whose contents Vue builds in the
    browser. ``declines`` lists every part that was not written for Vue to
    adopt.

    Page codes: ``ssr-disabled``, ``not-a-document``, ``deps-position`` (assets
    placed with a ``deps_position`` other than ``"smart"``), ``security-policy``,
    ``compile-error``, ``custom-hooks``, ``host-root``, ``manifest`` (the
    manifest does not parse, or a ``js_data`` key starts with ``$`` or ``_``,
    which the browser runtime rejects),
    ``below-threshold`` and ``browser-structure`` (the browser's parser would
    build a different tree from the written HTML).
    """

    hydrated: bool
    reason: str | None
    element_count: int | None = None
    threshold: int | None = None
    shell_count: int = 0
    declines: tuple[HydrationDecline, ...] = ()
    server_html: bool = False


def _record_hydration_admission(render: CitryRender, admission: HydrationAdmission) -> None:
    """Keep the latest decision on the render so tests and diagnostics can read it."""
    render.context.extra[_HYDRATION_ADMISSION_EXTRA_KEY] = admission


def _record_hydration_page_decline(render: CitryRender, reason: str) -> None:
    """Record a page-level decline, keeping any subtree reasons already found."""
    previous = render.context.extra.get(_HYDRATION_ADMISSION_EXTRA_KEY)
    if type(previous) is HydrationAdmission:
        _record_hydration_admission(render, replace(previous, hydrated=False, reason=reason))
    else:
        _record_hydration_admission(render, HydrationAdmission(hydrated=False, reason=reason))


def hydration_admission(render: CitryRender) -> HydrationAdmission | None:
    """Return the hydration decision of this render's latest serialization, if one was made."""
    admission = render.context.extra.get(_HYDRATION_ADMISSION_EXTRA_KEY)
    return admission if type(admission) is HydrationAdmission else None


def _hydration_page_reason(render: CitryRender, citry: Any) -> str | None:
    """
    Return why no part of this page can hydrate because of its hooks, or ``None``.

    Hydration writes the host before the ``on_serialize`` hooks run, so only
    the built-in dependency insertion may touch the HTML afterward, and no
    extension or component hook may add browser behavior the manifest does
    not describe.
    """
    if _exact_builtin_dependencies_hook(citry) is None:
        return "custom-hooks"
    from citry.component import Component  # noqa: PLC0415
    from citry.ext.i18n.extension import I18nExtension  # noqa: PLC0415

    for hook_name in ("on_dependencies", "on_js_loaded", "prepare_browser_render", "browser_plugin"):
        for extension in citry.extensions._extensions_with_hook(hook_name):
            if (
                type(extension) is not I18nExtension
                or extension.configured
                or getattr(getattr(extension, hook_name), "__func__", None) is not getattr(I18nExtension, hook_name)
            ):
                return "custom-hooks"
    # Dependency emission later invokes the class hook for every selected
    # record, separately from extension hooks; only the base no-op may run.
    dependency_records = render.context.extra.get("dependencies", {})
    if type(dependency_records) is not dict:
        return "custom-hooks"
    component_classes = [
        type(selected.context.component)
        for selected in _selected_renders(render)
        if selected.context.component is not None
    ]
    for record in dependency_records:
        component_class = getattr(record, "component_class", None)
        if component_class is None:
            return "custom-hooks"
        component_classes.append(component_class)
    base_on_dependencies = getattr(Component.on_dependencies, "__func__", None)
    # A page repeats a few classes many times; each class is checked once.
    if any(
        getattr(component_class.on_dependencies, "__func__", None) is not base_on_dependencies
        for component_class in dict.fromkeys(component_classes)
    ):
        return "custom-hooks"
    return None


def _render_hydration_host(
    render: CitryRender,
    citry: Any,
    early_selected_tree: Any,
    manifest_json: str,
    tags: dict[str, str],
) -> str | None:
    """
    Write the Vue host's contents from the compiled render functions, or return ``None``.

    The native renderer runs each component's compiled render function over
    the manifest's prepared data (the same data the browser reads), so the
    HTML matches what Vue's first render in the browser creates, apart from
    values Vue sets itself while hydrating. Parts that depend on browser-only
    state, constructs the renderer does not support, and elements the
    browser's parser would move become empty marked shells. Returns ``None``
    when the page should mount in the browser, including below the
    threshold. The decision, with a reason for each declined part, is
    recorded on the render.
    """
    page_reason = _hydration_page_reason(render, citry)
    if page_reason is not None:
        _record_hydration_page_decline(render, page_reason)
        return None
    # Each definition's render function was read once, when it compiled.
    programs = {
        compiled.id: compiled.server_render
        for compiled in early_selected_tree.compiled_by_definition.values()
        if compiled.server_render is not None
    }
    threshold = citry.settings.ssr_element_threshold
    html, element_count, shell_count, declines, reason = _rust.vue._render_for_hydration(
        programs, manifest_json, tags, threshold
    )
    _record_hydration_admission(
        render,
        HydrationAdmission(
            hydrated=html is not None,
            reason=reason,
            element_count=None if reason in {"host-root", "manifest"} else element_count,
            threshold=threshold,
            shell_count=shell_count,
            declines=tuple(
                HydrationDecline(
                    code=code,
                    detail=detail,
                    component=component,
                    outcome="page" if shell_tag is None else "shell",
                    shell_tag=shell_tag,
                    shell_content=shell_content,
                )
                for code, detail, component, shell_tag, shell_content in declines
            ),
        ),
    )
    return html


def _exact_builtin_dependencies_hook(citry: Any) -> tuple[object, object, object] | None:
    """Return the sole built-in insertion hook when its method identities match."""
    try:
        hooks = citry.extensions._extensions_with_hook("on_serialize")
    except (AttributeError, TypeError):
        return None
    if len(hooks) != 1:
        return None
    extension = hooks[0]
    on_serialize = getattr(extension.on_serialize, "__func__", None)
    internal = getattr(extension._on_serialize_internal, "__func__", None)
    if (
        type(extension) is not DependenciesExtension
        or on_serialize is not _BUILTIN_DEPENDENCIES_ON_SERIALIZE
        or internal is not _BUILTIN_DEPENDENCIES_INTERNAL_ON_SERIALIZE
    ):
        return None
    return extension, on_serialize, internal


class _HostValidator(HTMLParser):
    def __init__(self, host_id: str) -> None:
        super().__init__(convert_charrefs=False)
        self.host_id = host_id
        self.count = 0
        self.depth = 0
        self.empty = True
        self.valid_attrs = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if any(name == "id" and value == self.host_id for name, value in attrs):
            self.count += 1
            if tag != "div" or attrs != [("id", self.host_id)] or self.depth:
                self.valid_attrs = False
            else:
                self.depth = 1
            return
        if self.depth:
            self.empty = False
            if tag.lower() not in _VOID_HTML_TAGS:
                self.depth += 1

    def handle_startendtag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if any(name == "id" and value == self.host_id for name, value in attrs):
            self.count += 1
            self.valid_attrs = False
        elif self.depth:
            self.empty = False

    def handle_endtag(self, _tag: str) -> None:
        if self.depth:
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.depth and data:
            self.empty = False

    # An entity, a character reference, and a comment each count as content for the
    # emptiness test, and the parser hands each of them a different string (a name
    # rather than text), so they delegate rather than alias: only presence matters.
    def handle_entityref(self, name: str) -> None:
        self.handle_data(name)

    def handle_charref(self, name: str) -> None:
        self.handle_data(name)

    def handle_comment(self, data: str) -> None:
        self.handle_data(data)


@dataclass(frozen=True, slots=True)
class VueSerializationPlan:
    """A prepared immutable app plus the exact host threaded through extension hooks."""

    shell_html: str
    host_id: str
    configuration: str
    scripts: tuple[Script, ...]
    styles: tuple[Style, ...]
    script_security: _ScriptSecurityMaterializer | None
    javascript_policy: _JavascriptPolicy | None
    render_context: CitryContext
    validate_metadata: Callable[[], None]
    hydrate: bool = False
    deferred_to_dependency_manager: bool = False
    initial_script_preloads: tuple[_ScriptPreload, ...] = ()
    # The built-in dependency hook identity a written hydration host was
    # checked against; only that hook may touch the HTML afterward.
    _hydration_hooks: tuple[object, object, object] | None = None
    _citry: Any = None
    _owned_host: str | None = None
    # The configuration data block and the start script this plan created,
    # each with the text it carried. The fast host check below trusts a
    # hydrating page only while both reach the page exactly as created.
    _owned_start_scripts: tuple[tuple[Script, str], ...] | None = None
    _allow_structural_host_validation: bool = False
    # The host carries Citry's ordinary server HTML for Vue to replace.
    _server_html: bool = False

    def _has_exact_owned_host(self, hooked_html: str) -> bool:
        hooks = self._hydration_hooks
        current = _exact_builtin_dependencies_hook(self._citry) if hooks is not None else None
        if (
            not self._allow_structural_host_validation
            or not self.hydrate
            or self.deferred_to_dependency_manager
            or hooks is None
            or current is None
            or any(actual is not expected for actual, expected in zip(current, hooks, strict=True))
            or self._owned_host is None
            or self._owned_start_scripts is None
            or self._owned_host.count(self.host_id) != 1
            or self.configuration.count(self.host_id) < 1
        ):
            return False
        # A replaced or edited start script could mount instead of hydrating,
        # so each one must still be in the plan once, with its original text.
        for owned, text in self._owned_start_scripts:
            if owned.content != text or sum(script is owned for script in self.scripts) != 1:
                return False
        # The owned host starts with the element that carries the host id,
        # so the first id occurrence tells where the host should start. When
        # that guess is wrong, `_occurs_once` falls back to counting.
        host_start = hooked_html.find(self.host_id) - len('<div id="')
        return _occurs_once(hooked_html, self._owned_host, host_start) and hooked_html.count(self.host_id) == 1

    def _has_exact_server_host(self, hooked_html: str) -> bool:
        """Whether the host carrying server HTML reached the page unchanged, through the built-in hook only."""
        hooks = _exact_builtin_dependencies_hook(self._citry)
        if hooks is None or self._owned_host is None or self.deferred_to_dependency_manager:
            return False
        host_start = hooked_html.find(self.host_id) - len('<div id="')
        return _occurs_once(hooked_html, self._owned_host, host_start) and hooked_html.count(self.host_id) == 1

    def finalize(self, hooked_html: str) -> str:
        """Validate the hook result and place the prepared assets in the document."""
        exact_owned_host = self._has_exact_owned_host(hooked_html)
        if self._hydration_hooks is not None and not exact_owned_host:
            raise ValueError("Vue serialization hooks must preserve the hydrated mount host.")
        if not exact_owned_host and self._server_html and self._has_exact_server_host(hooked_html):
            # The host reached the page exactly as written, so the whole-page
            # parse below, which costs tens of ms on a large body, is not needed.
            exact_owned_host = True
        if not exact_owned_host:
            validator = _HostValidator(self.host_id)
            validator.feed(hooked_html)
            validator.close()
            canonical_host = f'<div id="{self.host_id}"></div>'
            # A hydrating host must keep its content and an ordinary host must
            # stay empty. A host carrying server HTML may hold anything a hook
            # left there, because Vue replaces its content when it mounts.
            if self.hydrate:
                content_ok = not validator.empty
            elif self._server_html:
                content_ok = True
            else:
                content_ok = validator.empty and hooked_html.count(canonical_host) == 1
            if validator.count != 1 or validator.depth or not content_ok or not validator.valid_attrs:
                raise ValueError("Vue serialization hooks must preserve exactly one empty Citry mount host.")
        self.validate_metadata()
        if self.deferred_to_dependency_manager:
            return hooked_html
        scripts = list(self.scripts)
        first_script = scripts[0] if scripts else None
        runtime_script = (
            first_script
            if isinstance(first_script, Script)
            and first_script.url is not None
            and first_script._owned_resource is not None
            and first_script.url == first_script._owned_resource.url
            else None
        )
        from citry.ext.dependencies.emission import (  # noqa: PLC0415
            _VUE_RUNTIME_SCRIPT_KEY,
            VUE_RUNTIME_EMITTED_KEY,
        )

        runtime_emitted_by_dependencies = self.render_context.extra.get(VUE_RUNTIME_EMITTED_KEY) is True
        if runtime_emitted_by_dependencies:
            from citry.ext.dependencies.routes import runtime_url  # noqa: PLC0415

            runtime = scripts[0]
            plan_runtime_present = (
                f'src="{escape(runtime.url, quote=True)}"' in hooked_html
                if runtime.url is not None
                else "Citry interactive runtime" in hooked_html
            )
            component = self.render_context.component
            citry = component.citry if component is not None else None
            dependency_runtime_present = (
                citry is not None
                and citry.mounted_prefix is not None
                and f'src="{escape(runtime_url(citry), quote=True)}"' in hooked_html
            )
            if not plan_runtime_present and not dependency_runtime_present:
                raise ValueError("Vue serialization hooks removed the required Citry runtime asset.")
            runtime_script = runtime if isinstance(runtime, Script) else runtime_script
            scripts.pop(0)
        styles = list(self.styles)
        if self.javascript_policy is not None:
            scripts = self.javascript_policy.process_dependencies(scripts, position="Vue bootstrap")
            styles = self.javascript_policy.process_dependencies(styles, position="Vue extension stylesheet")
        rendered_styles = "".join(
            str(item.render()) if self.script_security is None else self.script_security.render_style(item)
            for item in styles
        )
        rendered = "".join(
            str(item.render()) if self.script_security is None else self.script_security.render(item)
            for item in scripts
        )
        # Keep the same default placement contract as the ordinary dependency
        # emitter.  Appending the assets after a complete document produces
        # technically invalid HTML and can make the browser execute the
        # bootstrap only after it has closed ``</html>``.  The helper also
        # preserves the established prepend/append fallback for fragments.
        from citry.ext.dependencies.emission import _insert_default  # noqa: PLC0415

        if rendered_styles:
            hooked_html = _insert_default(hooked_html, rendered_styles, kind="css")
        if rendered:
            hooked_html = _insert_default(hooked_html, rendered, kind="js")
        managed_runtime = self.render_context.extra.get(_VUE_RUNTIME_SCRIPT_KEY)
        hint_runtime = (
            managed_runtime
            if isinstance(managed_runtime, Script)
            and managed_runtime.url is not None
            and managed_runtime._owned_resource is not None
            and managed_runtime.url == managed_runtime._owned_resource.url
            and f'src="{escape(managed_runtime.url, quote=True)}"' in hooked_html
            else None
        )
        if hint_runtime is None and not runtime_emitted_by_dependencies:
            hint_runtime = (
                runtime_script
                if runtime_script is not None
                and any(script is runtime_script for script in scripts)
                and runtime_script.url is not None
                and runtime_script._owned_resource is not None
                and runtime_script.url == runtime_script._owned_resource.url
                and f'src="{escape(runtime_script.url, quote=True)}"' in hooked_html
                else None
            )
        if hint_runtime is not None:
            runtime_preloads: tuple[_ScriptPreload, ...] = ()
            # Both render paths only read these attributes, so the wider
            # read-only type covers the plain dict and the materialized view.
            raw_runtime_attrs: Mapping[str, str | bool]
            if self.script_security is None:
                _, raw_runtime_attrs, _ = hint_runtime._render()
            else:
                raw_runtime_attrs = self.script_security._materialize(hint_runtime).attrs
            runtime_attrs = dict(raw_runtime_attrs)
            runtime_attrs.pop("src", None)
            if self.script_security is not None and self.script_security.csp_nonce is not None:
                runtime_attrs.pop("nonce", None)
            integrity = runtime_attrs.pop("integrity", None)
            # The URL check is always true here (the runtime was only chosen
            # with a URL), but keeping it in the condition lets the checker
            # see it alongside the integrity narrowing.
            hint_url = hint_runtime.url
            if (
                hint_url is not None
                and all(name in _PRELOAD_FETCH_ATTRS for name in runtime_attrs)
                and all(type(value) in (str, bool) for value in runtime_attrs.values())
                and (integrity is None or type(integrity) is str)
            ):
                runtime_preloads = (_ScriptPreload(hint_url, integrity, tuple(runtime_attrs.items())),)
            candidates = (*runtime_preloads, *self.initial_script_preloads)
            preload_html = _render_script_preloads(
                candidates,
                None if self.script_security is None else self.script_security.csp_nonce,
            )
            hooked_html = _insert_script_preloads(hooked_html, preload_html)
        return hooked_html


@dataclass(frozen=True, slots=True)
class VueSerializationAnalysis:
    """Selected browser requirements shared by policy and Vue preparation."""

    runtime_requirements: frozenset[str]
    active_policy_requirements: frozenset[str]


def _component_tags_for_manifest(
    producer: Any, manifest: dict[str, Any], cached_tags: dict[str, str] | None
) -> dict[str, str]:
    tags = {} if cached_tags is None else cached_tags
    cached_type_keys = frozenset(tags)
    for item in manifest["occurrences"]:
        type_key = item["typeKey"]
        if type_key not in cached_type_keys:
            tags[type_key] = producer.component_tag(type_key)
    return tags


def _prepare_initial_result(
    producer: Any,
    render: CitryRender,
    citry: Any,
    app_id: str,
    *,
    include_extensions: bool = False,
    dependency_options: dict[str, object] | None = None,
    early_selected_tree: Any = None,
) -> tuple[Any, ...]:
    from citry._vue.events import DirectVueEventsProducer  # noqa: PLC0415

    if (
        "prepare_from_render" not in vars(producer)
        and getattr(producer.prepare_from_render, "__func__", None) is DirectVueEventsProducer.prepare_from_render
    ):
        result = producer._prepare_from_render_result(
            render,
            citry=citry,
            app_id=app_id,
            revision=0,
            dependency_options=dependency_options,
            _early_selected_tree=early_selected_tree,
        )
        base = (result.payload, result.tags, result.validate)
        return (*base, result.extensions) if include_extensions else base
    base = (producer.prepare_from_render(render, citry=citry, app_id=app_id, revision=0), None, lambda: None)
    return (*base, ()) if include_extensions else base


_APP_ID_RE = re.compile(r"[0-9a-f]{32}")


def _reserve_vue_app_id(context: CitryContext, citry: Any) -> str:
    """Reserve this render's app ID once so an admitted stream can stage its host early."""
    if "_vue_app_id" in context.extra:
        app_id = context.extra["_vue_app_id"]
        if type(app_id) is not str:
            raise TypeError("Vue render-local app ID metadata must be a string.")
        # The id is written unescaped into the host's id attribute and names
        # the app's configuration block, so it keeps the fixed 32-hex shape.
        if _APP_ID_RE.fullmatch(app_id) is None:
            raise ValueError("Vue render-local app ID metadata must be 32 lowercase hex characters.")
    elif citry.id_generator is None:
        app_id = token_hex(16)
        context.extra["_vue_app_id"] = app_id
    else:
        # Reuse the same validation as component render IDs.  The explicit
        # generator is a deterministic test/snapshot hook; hash its validated
        # value so the app protocol keeps its existing fixed 32-hex shape.
        generated = validate_render_id(citry.id_generator())
        app_id = hashlib.sha256(generated.encode("utf-8")).hexdigest()[:32]
        context.extra["_vue_app_id"] = app_id
    context.extra["_vue_style_app_id"] = app_id
    return app_id


def _selected_renders(render: CitryRender) -> list[CitryRender]:
    selected: list[CitryRender] = []
    pending = [render]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        selected.append(current)
        parts = current.parts
        pending.extend(part for part in parts if isinstance(part, CitryRender))
        # Ordinary children a simple='vue' record called are selected too.
        # Most records call nothing, so the check stays one attribute read.
        for part in parts:
            if type(part) is SimpleVueRecord and part.leaf.call_children is not None:
                pending.extend(
                    called for called in simple_vue_called_components(part) if isinstance(called, CitryRender)
                )
    return selected


def _record_component_has_js(record: DependencyRecord, render: CitryRender) -> bool:
    """Whether the class behind one dependency record carries component JavaScript."""
    # The record normally keeps the exact class that produced it, so hot replacement
    # cannot pair an old body with a new class's assets.
    component_class = record.component_class
    if component_class is None:
        # Only a class id survived, so resolve it through the registry the render
        # belongs to. A render with no component cannot reach a registry at all.
        component = render.context.component
        if component is None:
            # Leaving the runtime out would break a component that does have JS,
            # while including it only costs payload, so assume it is needed.
            return True
        component_class = component.citry.get_component_by_class_id(record.class_id)
    return has_component_asset("js", component_class)


def analyze_vue_serialization(render: CitryRender) -> VueSerializationAnalysis:
    """Inspect selected typed metadata without invoking Assembly or the native compiler."""
    renders = _selected_renders(render)
    selected_ids = frozenset(
        current.frame.render_id
        for current in renders
        if current.frame.is_component_root and current.frame.render_id is not None
    ) | frozenset(part.render_id for current in renders for part in current.parts if isinstance(part, SimpleVueRecord))
    called_ids = {
        called.render_id
        for current in renders
        for part in current.parts
        if type(part) is SimpleVueRecord and part.leaf.call_children is not None
        for called in simple_vue_called_components(part)
        if type(called) is SimpleVueRecord
    }
    if called_ids:
        selected_ids |= called_ids
    requirements: set[str] = set()
    active_policy: set[str] = set()
    if any(current.frame.is_component_root and current.context.js_data for current in renders):
        requirements.add("js_data")
        active_policy.add("js_data")
    if any(
        current.frame.is_component_root
        and current.frame.prepared_occurrence is not None
        and current.frame.prepared_occurrence.component_tag_client_bindings
        for current in renders
    ):
        requirements.add("vue_binding")
        active_policy.add("vue_binding")
    dependency_records = cast("dict[DependencyRecord, object]", render.context.extra.get("dependencies", {}))
    if any(
        record.component_id in selected_ids and _record_component_has_js(record, render)
        for record in dependency_records
    ):
        requirements.add("component_js")
    event_records = cast("dict[EventInstanceEntry, object]", render.context.extra.get("events", {}))
    if any(record.render_id in selected_ids for record in event_records):
        requirements.add("events")
    from citry._vue.leaf_program import PreparedLeafProgram  # noqa: PLC0415

    for current in renders:
        for part in current.parts:
            if isinstance(part, PreparedElementOpen):
                if (
                    part.event_bindings
                    or part.poll_bindings
                    or part.control_bindings
                    or part.runtime_event_bindings
                    or part.runtime_poll_bindings
                ):
                    requirements.add("events")
                    active_policy.add("events")
                elif part.runtime_events_candidate:
                    requirements.add("events")
                if part.browser_bindings:
                    requirements.add("vue_binding")
                    active_policy.add("vue_binding")
            if isinstance(part, PreparedLeafProgram):
                data = part.prepared_data
                if any(data.get(name) for name in ("eventBindings", "pollBindings", "controlBindings")):
                    requirements.add("events")
                    active_policy.add("events")
                requirements.update(part.fragment.browser_requirements)
    if any(
        isinstance(part, PreparedElementOpen)
        and any(attr.name.startswith(("@c-", ":c-", "v-", "@", ":", "#")) for attr in part.attrs)
        for current in renders
        for part in current.parts
    ):
        requirements.add("vue_binding")
    return VueSerializationAnalysis(frozenset(requirements), frozenset(active_policy))


def vue_serialization_requirements(render: CitryRender) -> frozenset[str]:
    return analyze_vue_serialization(render).runtime_requirements


def _reject_head_browser_activity(render: CitryRender, head_only_render_ids: frozenset[str]) -> None:
    """Reject browser behavior whose selected occurrence is excluded from the Vue body."""
    if not head_only_render_ids:
        return
    renders = _selected_renders(render)
    if any(current.frame.render_id in head_only_render_ids and current.context.js_data for current in renders):
        raise ValueError("Component js_data is unsupported in the physical document head.")
    component = render.context.component
    if component is None:
        raise ValueError("Interactive Vue document serialization requires a component-owned root.")
    dependency_records = cast("dict[DependencyRecord, object]", render.context.extra.get("dependencies", {}))
    if any(
        record.component_id in head_only_render_ids
        and has_component_asset(
            "js", record.component_class or component.citry.get_component_by_class_id(record.class_id)
        )
        for record in dependency_records
    ):
        raise ValueError("Component JavaScript is unsupported in the physical document head.")
    event_records = cast("dict[EventInstanceEntry, object]", render.context.extra.get("events", {}))
    if any(record.render_id in head_only_render_ids for record in event_records):
        raise ValueError("Events are unsupported in the physical document head.")


# The attribute that marks a document app's configuration data block. Its
# value is the app id, which the start script passes to the runtime so each
# app on a page reads exactly its own block.
DOCUMENT_CONFIGURATION_ATTR = "data-citry-vue-document"


def _occurs_once(haystack: str, needle: str, expected_start: int) -> bool:
    """
    Return whether ``needle`` occurs exactly once in ``haystack``.

    The host checks search strings of a megabyte or more for a
    needle almost as long, which costs about a millisecond each. The caller
    passes where it expects the needle; when it is there and the haystack is
    too short to hold a second non-overlapping copy, the answer is known
    without searching. Otherwise the full count decides.
    """
    if expected_start >= 0 and len(haystack) < 2 * len(needle) and haystack.startswith(needle, expected_start):
        return True
    return haystack.count(needle) == 1


def _vue_shell(html: str, host: str) -> str:
    """Preserve a document's physical shell while replacing its logical body UI."""
    openings = list(_BODY_OPEN_RE.finditer(html))
    closings = list(_BODY_CLOSE_RE.finditer(html))
    document = bool(re.search(r"<!doctype\s|<html(?:\s|>)|<head(?:\s|>)|<body(?:\s|>)", html, re.IGNORECASE))
    if not document:
        return host
    if len(openings) != 1 or len(closings) != 1 or openings[0].end() > closings[0].start():
        raise ValueError("Interactive Vue document serialization requires exactly one well-ordered body element.")
    return html[: openings[0].end()] + host + html[closings[0].start() :]


# Page-level reasons that keep an empty host: the author chose to send no
# content (``ssr=False``, ``ssr_element_threshold``), or the output is not a
# document (``not-a-document``), such as a fragment inserted into a page that
# already shows its own content.
_EMPTY_HOST_REASONS = frozenset({"ssr-disabled", "below-threshold", "not-a-document"})
# A script element inside the body would run while the browser parses the
# served HTML, but never in a page Vue builds, so such a body is not sent.
_SCRIPT_START_RE = re.compile(r"<script[\s/>]", re.IGNORECASE)


def _server_contents_pass_policies(
    contents: str, security_csp: SecurityCspMode, javascript_policy: _JavascriptPolicy | None
) -> bool:
    """
    Whether the served copy adds nothing the page's security policies would report.

    Citry's ordinary server HTML keeps Vue directive attributes and authored
    ``onclick`` or ``javascript:`` values that Vue would otherwise apply only
    in the browser. A JavaScript policy reports every Vue binding it finds in
    served HTML, and a strict CSP rejects inline handlers, so a page with such
    a policy is sent with its content only when a CSP check of the copy finds
    nothing; otherwise it keeps an empty host, as it did before.
    """
    if javascript_policy is not None:
        return False
    if security_csp == "off":
        return True
    # A private validator of the same mode collects findings without
    # reporting them, so the page's own validator is unaffected.
    checker = _CspRenderValidator(security_csp)
    checker.validate_settled_html(contents, marker_prefix="", trusted_tag_starts=frozenset(), component_classes={})
    return not checker._findings


def _server_host_contents(full_html: str, placeholders: Mapping[str, str]) -> str | None:
    """
    Return Citry's ordinary body HTML for the Vue host to carry until Vue mounts, or ``None``.

    Vue's client mount clears its host before it builds the page
    (``app.mount`` in runtime-dom sets ``textContent = ""``), so this HTML is
    only what the browser shows and indexes until then. Insertion points
    such as a dependencies placeholder are removed, as they are from the
    empty host: an asset placed inside the host would be removed with it.
    """
    openings = list(_BODY_OPEN_RE.finditer(full_html))
    closings = list(_BODY_CLOSE_RE.finditer(full_html))
    if openings and closings:
        contents = full_html[openings[0].end() : closings[0].start()]
    else:
        # Output that is not a document is the Vue host's whole content
        # (see _vue_shell), so the whole render is what the host carries.
        contents = full_html
    for placeholder_html in placeholders.values():
        contents = contents.replace(placeholder_html, "")
    if _SCRIPT_START_RE.search(contents) is not None:
        return None
    return contents


# Stands in for the manifest while the rest of the configuration is
# serialized; the manifest's own JSON replaces it (see manifest_json).
_MANIFEST_SLOT = "\x00citry-manifest\x00"


def _script_json(value: object) -> str:
    """Serialize prepared data for the configuration data block, with sorted keys so the output is repeatable."""
    return script_json(value, sort_keys=True)


def prepare_vue_serialization(
    ctx: OnSerializeContext,
    script_security: _ScriptSecurityMaterializer | None,
    _security_csp: SecurityCspMode,
    javascript_policy: _JavascriptPolicy | None,
    security_javascript: SecurityJavascriptMode,
    analysis: VueSerializationAnalysis | None = None,
    early_selected_tree: Any = None,
    hydration_candidate: bool = False,
    server_html: Callable[[], str] | None = None,
) -> VueSerializationPlan | None:
    """Prepare a browser app only when selected typed metadata requires Vue."""
    requirements = (analysis or analyze_vue_serialization(ctx.selected_render)).runtime_requirements
    if ctx.selected_render.render_target != "prepared" or not requirements:
        return None
    if ctx.deps_strategy in {"simple", "ignore"}:
        # These public strategies deliberately do not install a client
        # runtime. Keep the settled server fallback and let the call-local
        # JavaScript policy inspect that exact output.
        return None
    if ctx.deps_strategy not in {"document", "fragment"}:
        if requirements == {"component_js"}:
            return None
        raise ValueError("Interactive Vue serialization requires deps_strategy='document' or 'fragment'.")
    if security_javascript in {"omit", "forbid"}:
        return None

    from citry._vue.events import default_events_producer, definition_bundle  # noqa: PLC0415
    from citry.ext.events.routes import EVENTS_RUNTIME_SRC, RUNTIME_PATH, _runtime_resource  # noqa: PLC0415

    app_id = _reserve_vue_app_id(ctx.context, ctx.citry)
    producer = default_events_producer(ctx.citry)
    typed_shell = typed_document_shell(ctx.selected_render, f'<div id="citry-vue-{app_id}"></div>')
    if typed_shell is not None:
        _reject_head_browser_activity(ctx.selected_render, typed_shell.head_only_render_ids)
    manifest, tags, validate_metadata, prepared_extensions = _prepare_initial_result(
        producer,
        ctx.selected_render,
        ctx.citry,
        app_id,
        include_extensions=True,
        dependency_options={
            "script_security": script_security,
            "security_csp": _security_csp,
            "javascript_policy": javascript_policy,
            "security_javascript": security_javascript,
            "strategy": ctx.deps_strategy,
        },
        early_selected_tree=early_selected_tree,
    )
    browser_plugins = {item.name: item.plugin for item in prepared_extensions}
    if any(plugin is None for plugin in browser_plugins.values()):
        raise TypeError("A prepared browser extension has no registered plugin descriptor.")
    has_events = any("eventContext" in item for item in manifest["occurrences"])
    if has_events and (
        security_javascript != ctx.citry.settings.security_javascript
        or _security_csp != ctx.citry.settings.security_csp
    ):
        raise ValueError(
            "Call-local JavaScript/CSP overrides are unsupported for revisable Events apps; "
            "configure the same policy on Citry settings so later revisions retain it."
        )
    mounted = ctx.citry.mounted_prefix is not None
    if has_events and not mounted:
        raise ValueError("Components with Events require a mounted web integration for Vue serialization.")
    tags = _component_tags_for_manifest(producer, manifest, tags)
    # The manifest is serialized once. The hydration renderer reads the same
    # JSON the configuration data block carries, so it sees exactly the browser's data.
    manifest_json = _script_json(manifest)
    hydration_html = None
    if (
        hydration_candidate
        and ctx.deps_strategy == "document"
        and ctx.deps_position == "smart"
        and _security_csp == "off"
        and security_javascript == "allow"
        and script_security is None
        and javascript_policy is None
        and early_selected_tree is not None
        and early_selected_tree.error is None
    ):
        hydration_html = _render_hydration_host(
            ctx.selected_render, ctx.citry, early_selected_tree, manifest_json, tags
        )
    dependency_hooks = ctx.citry.extensions._extensions_with_hook("on_dependencies")
    from citry.ext.i18n.extension import I18nExtension  # noqa: PLC0415

    def permits_owned_late_assets(extension: Any) -> bool:
        if plugin_policies.get(extension.name) is True:
            return True
        return (
            type(extension) is I18nExtension
            and not extension.configured
            and "on_dependencies" not in vars(extension)
            and getattr(extension.on_dependencies, "__func__", None) is I18nExtension.on_dependencies
        )

    plugin_policies = {
        name: cast("Any", plugin).allows_late_component_assets for name, plugin in browser_plugins.items()
    }
    allow_lazy_type_assets = security_javascript == "allow" and all(
        permits_owned_late_assets(hook) for hook in dependency_hooks
    )
    host_id = f"citry-vue-{app_id}"
    configuration = {
        "manifest": _MANIFEST_SLOT,
        "host": f"#{host_id}",
        "tags": tags,
        "allowLazyTypeAssets": allow_lazy_type_assets,
        # Mounted applications fetch the content-addressed dependency URLs.
        # Standalone serialization emits those exact assets into the document
        # below and asks the runtime to adopt them instead.
        "loadInitialAssets": mounted,
    }
    # The browser hydrates only when the server wrote the host content for
    # Vue to adopt; every other page mounts into an empty host.
    hydrate = hydration_html is not None
    if hydrate:
        configuration["hydrate"] = True
        admission = hydration_admission(ctx.selected_render)
        if admission is not None and any(decline.shell_content for decline in admission.declines):
            # Vue keeps the attributes of elements it adopts inside a shell,
            # so the runtime removes the Citry HTML the server wrote there
            # right before Vue hydrates, and Vue builds those contents anew.
            configuration["emptyShells"] = True
    if script_security is not None and script_security.csp_nonce is not None:
        configuration["nonce"] = script_security.csp_nonce
    if mounted:
        configuration["endpoint"] = ctx.citry.build_url("ext/events/call")
        configuration["eventBaseUrl"] = ctx.citry.build_url("ext/events/e/")
    serialized = _script_json(configuration)
    manifest_slot = json.dumps(_MANIFEST_SLOT)
    if serialized.count(manifest_slot) != 1:
        raise RuntimeError("the Vue configuration lost its manifest position")
    serialized = serialized.replace(manifest_slot, manifest_json, 1)
    scripts: list[Script] = []
    if mounted:
        runtime = Script(kind="core", url=ctx.citry.build_url(RUNTIME_PATH))
        runtime._owned_resource = _runtime_resource(ctx.citry)
        scripts.append(runtime)
    else:
        scripts.append(Script(kind="core", content=EVENTS_RUNTIME_SRC.read_text()))
        for digest in dict.fromkeys(item["sha256"] for item in manifest["definitions"]):
            bundle = definition_bundle(ctx.citry, digest)
            if bundle is None:
                raise RuntimeError("A prepared Vue definition bundle was not published.")
            scripts.append(Script(kind="core", content=bundle.decode()))
        from citry._vue.events import style_asset  # noqa: PLC0415

        # Standalone HTML has no asset routes. Materialize every prepared
        # dependency before startPrepared while retaining the descriptor URL
        # as the runtime's ownership identity.
        emitted_script_sources: set[str] = set()
        for asset in manifest["scripts"]:
            source = asset["source"]
            source_identity = json.dumps(source, allow_nan=False, separators=(",", ":"), sort_keys=True)
            if source_identity in emitted_script_sources:
                continue
            emitted_script_sources.add(source_identity)
            attrs = dict(source.get("attrs", {}))
            if source["kind"] == "owned":
                body = definition_bundle(ctx.citry, source["sha256"])
                if body is None:
                    raise RuntimeError("A prepared Vue script asset was not retained for standalone serialization.")
                scripts.append(Script(kind="core", content=body.decode(), attrs=attrs))
            else:
                scripts.append(Script(kind="core", url=source["url"], attrs=attrs))
    scripts.extend(cast("Any", plugin).script for plugin in browser_plugins.values())
    initial_styles: list[Style] = []
    # A mounted document links its stylesheets in <head> so the served HTML
    # paints with them; the runtime adopts those links instead of adding its
    # own. A mounted fragment is inserted into a page later, so the runtime
    # loads its stylesheets then.
    if not mounted or ctx.deps_strategy == "document":
        emitted_style_sources: set[str] = set()
        for asset in manifest["styles"]:
            source = asset["source"]
            source_identity = json.dumps(source, allow_nan=False, separators=(",", ":"), sort_keys=True)
            if source_identity in emitted_style_sources:
                continue
            emitted_style_sources.add(source_identity)
            attrs = dict(source.get("attrs", {}))
            attrs["data-citry-css-url"] = source["url"]
            attrs["data-citry-vue-style-app"] = app_id
            if mounted:
                # The element the runtime would create for this stylesheet: its
                # own ownership attributes first, then the source's attributes.
                attrs = {
                    "data-citry-css-url": source["url"],
                    "data-citry-vue-style-app": app_id,
                    **source.get("attrs", {}),
                }
                if source["kind"] == "owned":
                    # The same integrity and CORS mode the runtime requests
                    # an owned file with, so the file is fetched once.
                    attrs["integrity"] = cast("str", _sha256_sri(source["sha256"]))
                    if not any(name.lower() == "crossorigin" for name in attrs):
                        attrs["crossorigin"] = OWNED_ASSET_CROSSORIGIN
                initial_styles.append(Style(kind="core", url=source["url"], attrs=attrs))
            elif source["kind"] == "owned":
                body = style_asset(ctx.citry, source["sha256"])
                if body is None:
                    raise RuntimeError("A prepared Vue stylesheet was not retained for standalone serialization.")
                initial_styles.append(Style(kind="core", content=body.decode(), attrs=attrs))
            else:
                initial_styles.append(Style(kind="core", url=source["url"], attrs=attrs))
    # Browser contribution assets are already represented exactly once in the
    # validated manifest. Standalone apps materialize them above, and mounted
    # documents link their stylesheets. Only the plugin registration scripts
    # remain direct.
    styles = tuple(initial_styles)
    # The configuration travels as a JSON data block the browser never runs:
    # the runtime reads it with JSON.parse, which is much cheaper than
    # compiling a megabyte-sized script, and a strict CSP does not apply to it.
    configuration_block = Script(
        kind="core",
        content=serialized,
        attrs={"type": "application/json", DOCUMENT_CONFIGURATION_ATTR: app_id},
    )
    # The start script stays a module script, which runs only after the
    # browser has parsed the whole page, so starting the app (tens of ms on a
    # large page) never delays the first paint of the server HTML. It still
    # runs after the classic runtime and plugin scripts above it, and before
    # DOMContentLoaded. It carries only the app id, so its CSP hash is short
    # to compute and its text never includes page data.
    start_script = Script(
        kind="core",
        content=f"__citryRuntime.startDocument({script_json(app_id)});",
        attrs={"type": "module"},
    )
    scripts.extend((configuration_block, start_script))
    validate_metadata()
    initial_script_preloads = (
        _manifest_script_preloads(manifest) if mounted and ctx.deps_strategy == "document" else ()
    )
    deferred = ctx.deps_strategy == "fragment"
    if deferred:
        from citry.ext.dependencies.emission import (  # noqa: PLC0415
            VUE_FRAGMENT_MOUNT_KEY,
        )

        ctx.context.extra[VUE_FRAGMENT_MOUNT_KEY] = {
            "protocol": "citry-vue-fragment/1",
            "appId": app_id,
            "host": f"#{host_id}",
            "prepared": json.loads(serialized),
        }
    else:
        from citry.ext.dependencies.emission import VUE_RUNTIME_REQUIRED_KEY  # noqa: PLC0415

        ctx.context.extra[VUE_RUNTIME_REQUIRED_KEY] = True
    # A page that cannot hydrate still sends its content, so search engines
    # and readers without JavaScript see it: the host carries Citry's
    # ordinary server HTML, and Vue's client mount replaces it. An empty host
    # is kept only when the author chose it, when the output is not a
    # document, or when the body holds a <script> element.
    server_contents = None
    if hydration_html is None and server_html is not None and ctx.deps_strategy == "document":
        admission = hydration_admission(ctx.selected_render)
        page_reason = admission.reason if admission is not None else None
        if page_reason not in _EMPTY_HOST_REASONS:
            server_contents = _server_host_contents(server_html(), ctx.placeholders)
            if server_contents is not None and not _server_contents_pass_policies(
                server_contents, _security_csp, javascript_policy
            ):
                server_contents = None
            if admission is not None:
                _record_hydration_admission(
                    ctx.selected_render, replace(admission, server_html=server_contents is not None)
                )
    if hydration_html is not None:
        owned_host = f'<div id="{host_id}">{hydration_html}</div>'
        shell_html = _vue_shell(ctx.html, owned_host)
    elif server_contents is not None:
        owned_host = f'<div id="{host_id}">{server_contents}</div>'
        shell_html = _vue_shell(ctx.html, owned_host)
    else:
        shell_html = _vue_shell(ctx.html, f'<div id="{host_id}"></div>')
        owned_host = None
    allow_structural_host_validation = (
        hydration_html is not None
        and ctx.deps_strategy == "document"
        and ctx.deps_position == "smart"
        and _security_csp == "off"
        and script_security is None
        and javascript_policy is None
    )
    return VueSerializationPlan(
        shell_html=shell_html,
        host_id=host_id,
        configuration=serialized,
        scripts=tuple(scripts),
        styles=styles,
        script_security=script_security,
        javascript_policy=javascript_policy,
        render_context=ctx.context,
        validate_metadata=validate_metadata,
        hydrate=hydrate,
        deferred_to_dependency_manager=deferred,
        initial_script_preloads=initial_script_preloads,
        _hydration_hooks=_exact_builtin_dependencies_hook(ctx.citry) if hydration_html is not None else None,
        _citry=ctx.citry,
        _owned_host=owned_host,
        _server_html=server_contents is not None,
        _owned_start_scripts=(
            ((configuration_block, serialized), (start_script, cast("str", start_script.content))) if hydrate else None
        ),
        _allow_structural_host_validation=allow_structural_host_validation,
    )
