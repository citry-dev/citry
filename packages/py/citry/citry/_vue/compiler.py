"""Persistent native compiler client for prepared Vue definitions."""

from __future__ import annotations

import hashlib
import html
import json
import re
import threading
from collections import OrderedDict
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, TypedDict

from typing_extensions import NotRequired, Self

from citry.client_directives import _ONCE_MEMO_HINT
from citry_core import _rust

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

from .capture import prepared_spread_index
from .prepared import (
    ComponentCall,
    ElementClose,
    ElementOpen,
    ForwardedSlot,
    Html,
    LocalComponentCall,
    PreparedNode,
    PreparedSlotOutlet,
    PreparedView,
    RuntimeDirective,
    SlotOutlet,
    TextBinding,
    replace_definition_ids,
)


def _generated_vue_attr(name: str, value: str) -> str:
    """
    Serialize one compiler-owned Vue attribute without changing its expression.

    Every caller builds a call expression or a plain binding value. The native
    compiler decodes character references in those expressions, so the escaped
    text compiles back to exactly ``value``. A handler written as statements
    is compiled from the raw attribute text instead, so authored bindings use
    ``_authored_vue_attr``.
    """
    return f'{name}="{html.escape(value, quote=True)}"'


def _generated_event_args(args: object, *, el_expression: str = "$event.currentTarget") -> str:
    """
    Evaluate authored server-event arguments with an explicit Citry ``$el``.

    Native element listeners use Vue's event ``currentTarget``. Component
    listeners are different: Vue invokes them from the parent render scope,
    and an emitted payload may be an arbitrary value (including an ``Event``
    whose ``currentTarget`` is ``null``). The component capture path therefore
    supplies the child's physical root through an authenticated runtime
    relationship instead of reading it from the payload.
    """
    if args is None:
        return ""
    if not isinstance(args, str):
        raise TypeError("generated event arguments must be a string or None")
    return f", (($el) => ({args}))({el_expression})"


def _authored_vue_attr(name: str, value: str) -> str:
    """
    Write one authored Vue binding exactly as its template text reads.

    ``value`` is the author's raw attribute text, so Vue reads it the same way
    it reads the binding on a plain element. Escaping it would break a handler
    written as statements (``x = a < 3``): the native compiler compiles that
    form from the raw text and would see ``&lt;`` as code.

    Raises:
        ValueError: The value holds both quote characters, so no delimiter can
            enclose it. One authored attribute value cannot hold both.

    """
    if '"' not in value:
        return f'{name}="{value}"'
    if "'" not in value:
        return f"{name}='{value}'"
    msg = f"Vue binding {name!r} holds both quote characters and cannot be written as one attribute"
    raise ValueError(msg)


class _LocalCallBindingDeclaration(TypedDict):
    kind: str
    name: str
    value: str
    sourceStart: int
    sourceEnd: int


class _LocalCallDeclaration(TypedDict):
    localId: str
    typeKey: str
    componentTag: str
    sourceStart: int
    sourceEnd: int
    bindings: list[_LocalCallBindingDeclaration]


class _LocalCallRunDeclaration(TypedDict):
    runId: str
    typeKey: str
    componentTag: str
    sourceStart: int
    sourceEnd: int
    loopSourceStart: int
    loopSourceEnd: int


class _ElementBindingDeclaration(TypedDict):
    sourceStart: int
    sourceEnd: int
    attrsBindingKey: str | None
    keyBindingKey: str | None
    browserBindingKeys: NotRequired[list[str]]
    runtimeEventsBindingKey: NotRequired[str | None]


@dataclass(slots=True)
class _SlotKeyScope:
    """One active keyed element whose native slot descendants need stable keys."""

    expression: str
    ordinal: int = 0


def _next_slot_key(scopes: list[_SlotKeyScope]) -> str | None:
    """Return a stable key for one native slot under the nearest keyed element."""
    if not scopes:
        return None
    scope = scopes[-1]
    ordinal = scope.ordinal
    scope.ordinal += 1
    return f"JSON.stringify([{scope.expression}, {ordinal}])"


def _slot_key_attr(expression: str | None) -> str:
    # A slot outlet under a keyed element carries a key derived from that
    # element, so Vue moves the slot content with its row instead of by position.
    return "" if expression is None else f' :key="{expression}"'


class _DynamicElementDeclaration(TypedDict):
    alias: str
    tag: str
    sourceStart: int
    sourceEnd: int


class _OpaqueHtmlDeclaration(TypedDict):
    key: str
    sourceStart: int
    sourceEnd: int
    origin: str


class _RuntimeEventDeclaration(TypedDict):
    sourceStart: int
    sourceEnd: int
    bindingKey: str
    steps: list[dict[str, object]]


@dataclass(frozen=True, slots=True)
class CompiledRender:
    id: str
    javascript: str
    source_map: str | None
    target: str
    directive_signature: tuple[RuntimeDirective, ...]
    replacement_sites: tuple[dict[str, object], ...]
    local_call_runs: tuple[dict[str, object], ...] = ()
    local_calls: tuple[dict[str, object], ...] = ()
    dynamic_elements: tuple[dict[str, object], ...] = ()
    opaque_html_sites: tuple[dict[str, object], ...] = ()
    runtime_event_sites: tuple[dict[str, object], ...] = ()
    authored_text_plan: AuthoredTextPlan | None = None
    hydration_plan: HydrationPlan | None = None
    # The render function read once for the server, which runs it against
    # prepared data to write HTML Vue adopts; `None` when it cannot be read.
    server_render: _rust.vue.ServerRenderProgram | None = None
    # What the render function returns at its root: "element", "component",
    # "empty", "fragment", "text", "opaque-html", or "unknown". A caller's `v-show` or custom
    # directive only reaches the page through an element root (see `events.check_directive_roots`).
    root_shape: str = "unknown"


@dataclass(frozen=True, slots=True)
class AuthoredTextAction:
    type: str
    source_start: int
    source_end: int
    original_start: int | None
    original_end: int | None
    rule: str
    content: str | None = None


@dataclass(frozen=True, slots=True)
class AuthoredTextPlan:
    source: str
    source_sha256: str
    original_source_sha256: str
    status: str
    actions: tuple[AuthoredTextAction, ...]
    reason_code: str | None = None


@dataclass(frozen=True, slots=True)
class HydrationAnchor:
    """
    One Fragment or placeholder comment the compiled render function creates.

    A `fragment` is written as `<!--[-->` before and `<!--]-->` after its
    content; a `comment` is written as `<!--{comment}-->` in place of content.
    Spans are UTF-8 byte offsets covering the construct's opening tag, or the
    whole template for `root` and `empty-render`.
    """

    kind: str
    origin: str
    comment: str | None
    source_start: int
    source_end: int
    original_start: int | None
    original_end: int | None
    path: tuple[str, ...] | None


@dataclass(frozen=True, slots=True)
class HydrationAttribute:
    """How Vue's hydration treats one authored attribute of an element."""

    kind: str
    name: str | None
    prop_key: str | None
    hydration: str
    source_start: int
    source_end: int
    original_start: int | None
    original_end: int | None


@dataclass(frozen=True, slots=True)
class HydrationElement:
    """
    One element or component call in the compiled render function.

    `original_*` is `None` for an element the template parser adds without an
    authored tag, such as the `tbody` around a table's direct rows.
    """

    vnode: str
    tag: str
    source_start: int
    source_end: int
    original_start: int | None
    original_end: int | None
    path: tuple[str, ...] | None
    patch_flag: int
    dynamic_props: tuple[str, ...] | None
    attributes: tuple[HydrationAttribute, ...]


@dataclass(frozen=True, slots=True)
class HydrationPlan:
    """
    Markers and attribute rules the server needs to write hydratable HTML.

    `source_*` spans index `transformedTemplate`; `original_*` spans index
    the template passed to the compiler. An `unsupported` plan has no facts.
    """

    source: str
    source_sha256: str
    original_source_sha256: str
    status: str
    anchors: tuple[HydrationAnchor, ...]
    elements: tuple[HydrationElement, ...]
    reason_code: str | None = None


@dataclass(frozen=True, slots=True)
class DefinitionCompileInput:
    template: str
    local_calls: tuple[dict[str, object], ...]
    element_bindings: tuple[dict[str, object], ...]
    local_call_runs: tuple[dict[str, object], ...] = ()
    dynamic_elements: tuple[dict[str, object], ...] = ()
    template_context_names: tuple[str, ...] = ()
    opaque_html_sites: tuple[dict[str, object], ...] = ()
    runtime_event_sites: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class CompiledView:
    view: PreparedView
    definitions: Mapping[str, CompiledRender]

    def __post_init__(self) -> None:
        object.__setattr__(self, "definitions", MappingProxyType(dict(self.definitions)))


ORDINARY_TARGET = "ordinary-vnodes/1"
_NATIVE_COMPILER_IDENTITY = {"name": "vize_atelier_dom", "version": "0.420.0+citry.2"}
_TEXT_ACTION_RULES = {
    "rewrite": {"condense.whitespace"},
    "drop": {"condense.drop-whitespace", "drop.comment", "drop.branch-gap"},
}
_TEXT_PLAN_REASON_CODES = {
    "atelier_text_mismatch",
    "invalid_source_spans",
    "source_edit_overlap",
    "s1_parse_or_lower_diagnostic",
    "unsupported_ast_shape",
}
_HYDRATION_REASON_CODES = {
    "attribute_key_mismatch",
    "source_edit_overlap",
    "source_too_large",
    "unsupported_render_shape",
}
_HYDRATION_ANCHOR_ORIGINS = {
    "fragment": {"root", "v-for", "v-for-item", "v-if-branch", "slot"},
    "comment": {"v-if", "empty-render"},
}
_HYDRATION_ATTRIBUTE_KINDS = {
    "attr",
    "bind",
    "class",
    "compiler",
    "content",
    "directive",
    "dynamic-name",
    "listener",
    "model",
    "prop",
    "reserved",
    "show",
    "spread",
    "static",
    "structural",
    "style",
}
_HYDRATION_RULES = {"patched", "checked", "per-key", "directive", "component", "none"}
_ALLOWED_HELPERS = {
    "Fragment",
    "createBlock",
    "createCommentVNode",
    "createElementBlock",
    "createElementVNode",
    "createVNode",
    "createTextVNode",
    "guardReactiveProps",
    "mergeProps",
    "normalizeClass",
    "normalizeProps",
    "normalizeStyle",
    "openBlock",
    "renderList",
    "resolveDirective",
    "resolveDynamicComponent",
    "resolveComponent",
    "renderSlot",
    "toDisplayString",
    "toHandlers",
    "vModelCheckbox",
    "vModelDynamic",
    "vModelRadio",
    "vModelSelect",
    "vModelText",
    "vShow",
    "withCtx",
    "withDirectives",
    "withKeys",
    "withModifiers",
}
_ROOT_SHAPES = frozenset({"element", "component", "empty", "fragment", "text", "opaque-html", "unknown"})
_FORBIDDEN_CODE = ("_cache[", "createStaticVNode", "setBlockTracking", "withMemo")
_FORBIDDEN_TEMPLATE = re.compile(r"<(?:script|style)(?:\s|>|/)|\bv-(?:once|memo)\b", re.IGNORECASE)
# The descriptor also names the browser globals the definition code writes to and reads from,
# so a definition built for other global names gets a different contract hash: the artifact
# cache does not find it, and the browser runtime rejects it.
HELPER_CONTRACT_DESCRIPTOR = (
    "ordinary-vnodes/1;globals=__citryRuntime,__citryRuntimeDefinitions;Fragment=pass;openBlock=noop;createBlock=createVNode-ignore-hints;"
    "createElementBlock=createVNode-ignore-hints;createElementVNode=createVNode-ignore-hints;"
    "createVNode=createVNode-ignore-hints;createCommentVNode=pass;createTextVNode=ignore-hints;"
    "pass=guardReactiveProps,normalizeClass,normalizeProps,normalizeStyle,renderList,"
    "renderSlot,resolveComponent,resolveDirective,resolveDynamicComponent,toDisplayString,toHandlers,"
    "vModelCheckbox,vModelDynamic,vModelRadio,vModelSelect,vModelText,vShow,withCtx,withDirectives,"
    "withKeys,withModifiers;"
    "localCalls=declared,componentCallBindings;"
    "localCallRuns=citryOccurrenceId,directComponentVFor,$citryPrepared.callRuns;"
    "dynamicElements=definitionScopedAlias,createVNodeFamily;"
    "opaqueHtml=declaredSites,exactDataRecord,staticVNode;"
    "editableValue=constantAndServerValueComparedByVNode,uneditedSelectRestored;mergeProps=marksValueSource"
)
HELPER_CONTRACT = hashlib.sha256(HELPER_CONTRACT_DESCRIPTOR.encode()).hexdigest()


class NativeCompiler:
    def __init__(self) -> None:
        self._binary_sha256 = "pyo3"
        self._lock = threading.Lock()
        self._cache: OrderedDict[str, CompiledRender] = OrderedDict()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        pass

    def compile(
        self,
        template: str,
        *,
        type_key: str,
        directive_signature: tuple[RuntimeDirective, ...] = (),
        replacement_sites: tuple[dict[str, object], ...] = (),
        local_calls: tuple[dict[str, object], ...] = (),
        element_bindings: tuple[dict[str, object], ...] = (),
        local_call_runs: tuple[dict[str, object], ...] = (),
        dynamic_elements: tuple[dict[str, object], ...] = (),
        template_context_names: tuple[str, ...] = (),
        opaque_html_sites: tuple[dict[str, object], ...] = (),
        runtime_event_sites: tuple[dict[str, object], ...] = (),
        source_map: bool = False,
    ) -> CompiledRender:
        if source_map:
            raise ValueError("ordinary target source maps are not implemented by this compiler adapter")
        forbidden = _FORBIDDEN_TEMPLATE.search(template)
        if forbidden is not None:
            # The template parser names `v-once` and `v-memo` with their
            # position; this names them for a template that reached here another way.
            if forbidden.group(0).lower().startswith("v-"):
                msg = (
                    f"The Vue template contains '{forbidden.group(0)}'. {_ONCE_MEMO_HINT} To keep an element's"
                    " contents as the server first rendered them, put '#c-ignore' on the element."
                )
                raise ValueError(msg)
            raise ValueError("ordinary target template contains an unsupported raw-text or cached construct")
        identity = json.dumps(
            {
                "binary": self._binary_sha256,
                "target": ORDINARY_TARGET,
                "prefixIdentifiers": True,
                "hoistStatic": False,
                "cacheHandlers": False,
                "directiveSignature": _signature_json(directive_signature),
                "replacementSites": replacement_sites,
                "helperContract": HELPER_CONTRACT,
                "typeKey": type_key,
                "sourceMap": source_map,
                "template": template,
                "localCalls": local_calls,
                "elementBindings": element_bindings,
                "localCallRuns": local_call_runs,
                "dynamicElements": dynamic_elements,
                "templateContextNames": template_context_names,
                "opaqueHtmlSites": opaque_html_sites,
                "runtimeEventSites": runtime_event_sites,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        cache_key = hashlib.sha256(identity.encode()).hexdigest()
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached is not None:
                self._cache.move_to_end(cache_key)
                return cached
            response = json.loads(
                _rust.vue._compile_vue(
                    template,
                    json.dumps(local_calls, separators=(",", ":")),
                    json.dumps(element_bindings, separators=(",", ":")),
                    json.dumps(local_call_runs, separators=(",", ":")),
                    json.dumps(dynamic_elements, separators=(",", ":")),
                )
            )
            if response.get("schema") != "citry-vue-compiler/1" or response.get("target") != ORDINARY_TARGET:
                raise RuntimeError("native compiler returned an incompatible artifact")
            expected_options = {"prefixIdentifiers": True, "hoistStatic": False, "cacheHandlers": False}
            if response.get("options") != expected_options:
                raise RuntimeError("native compiler did not confirm ordinary target options")
            authored_text_plan = _validate_authored_text_plan(response, template)
            preamble = str(response.get("preamble", ""))
            code = str(response.get("code", ""))
            diagnostics = response.get("diagnostics", [])
            discovered_signature = tuple(
                RuntimeDirective(
                    site_id=f"{element['siteId']}D{directive['ordinal']}",
                    name=f"v-{directive['name']}",
                    arg=directive.get("argument"),
                    modifiers=tuple(sorted(directive.get("modifiers", []))),
                )
                for element in response.get("elements", [])
                for directive in element.get("directives", [])
                if directive.get("runtimeLifecycle") is True
            )
            discovered_sites = tuple(
                {
                    "siteId": element["siteId"],
                    "replacementKey": element["replacementKey"],
                    "localDescendants": element.get("localDescendants", []),
                    "localDescendantRuns": element.get("localDescendantRuns", []),
                    # Only a site with slot outlets carries the key, so definitions
                    # without slots keep their exact bytes.
                    **({"slotOutlets": element["slotOutlets"]} if element.get("slotOutlets") else {}),
                }
                for element in response.get("elements", [])
                if element.get("replacementKey") is not None
            )
            # Every emitted `withDirectives` call has a runtime implementation.
            # A component call's `v-show` or custom directive has one without
            # joining the lifecycle signature, because the call's own Vue key
            # covers its changes.
            directive_element_count = sum(
                1
                for element in response.get("elements", [])
                if any(item.get("runtimeImplementation") is not None for item in element.get("directives", []))
            )
            discovered_runs = _normalize_local_call_runs(response.get("localCallRuns", []), local_call_runs)
            discovered_calls = _normalize_local_calls(response.get("elements", []), local_calls)
            discovered_opaque = _normalize_opaque_html_sites(response.get("elements", []), opaque_html_sites)
            discovered_runtime_events = _normalize_runtime_event_sites(
                response.get("elements", []), runtime_event_sites
            )
            if diagnostics:
                raise ValueError(f"Vue compiler diagnostics: {diagnostics!r}")
            # Read after diagnostics so a rejected template reports its
            # diagnostics rather than a plan built from rejected output.
            hydration_plan = _validate_hydration_plan(response, template)
            discovered_dynamic = tuple(response.get("dynamicElements", ()))
            if discovered_dynamic != dynamic_elements:
                raise RuntimeError("native compiler dynamic element metadata does not match request")
            if "function render" not in code:
                raise ValueError("native compiler did not emit a render function")
            helpers = set(re.findall(r"([A-Za-z][A-Za-z0-9]*):\s*_[A-Za-z][A-Za-z0-9]*", preamble))
            unsupported = helpers - _ALLOWED_HELPERS
            if unsupported:
                raise ValueError(f"ordinary target emitted unsupported helpers: {sorted(unsupported)!r}")
            if any(token in preamble or token in code for token in _FORBIDDEN_CODE):
                raise ValueError("ordinary target emitted cached or static compiler constructs")
            emits_directives = "withDirectives" in helpers
            if emits_directives != bool(directive_element_count):
                raise ValueError("runtime directive metadata does not match the emitted compiler helpers")
            if code.count("_withDirectives(") != directive_element_count:
                raise ValueError("runtime directive metadata count does not match emitted sites")
            discovered_sites = _normalize_replacement_sites(discovered_sites)
            content_id = _compiled_content_id(
                identity, response, preamble, code, discovered_signature, discovered_sites
            )
            js_id = json.dumps(content_id)
            signature_json = json.dumps(_signature_json(discovered_signature), separators=(",", ":"))
            replacement_json = json.dumps(discovered_sites, separators=(",", ":"))
            call_runs_json = json.dumps(discovered_runs, separators=(",", ":"))
            compiled_local_calls = tuple(
                {
                    "localId": value["localId"],
                    "typeKey": value["typeKey"],
                    "componentTag": value["componentTag"],
                    "bindings": value.get("bindings", []),
                    **({"fills": value["fills"]} if "fills" in value else {}),
                }
                for value in discovered_calls
            )
            local_calls_json = json.dumps(compiled_local_calls, separators=(",", ":"))
            dynamic_elements_json = json.dumps(discovered_dynamic, separators=(",", ":"))
            opaque_html_json = json.dumps(discovered_opaque, separators=(",", ":"))
            runtime_events_json = json.dumps(discovered_runtime_events, separators=(",", ":"))
            javascript = (
                f"(function(Vue){{\n{preamble}\n{code}\n"
                "window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};\n"
                f"window.__citryRuntimeDefinitions[{js_id}]={{render:render,target:{json.dumps(ORDINARY_TARGET)},"
                f"helperContract:{json.dumps(HELPER_CONTRACT)},directiveSignature:{signature_json},"
                f"replacementSites:{replacement_json},localCallRuns:{call_runs_json},"
                f"localCalls:{local_calls_json},dynamicElements:{dynamic_elements_json},"
                f"opaqueHtmlSites:{opaque_html_json},runtimeEventSites:{runtime_events_json}}};\n"
                f"}})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements({dynamic_elements_json}));\n"
            )
            root_shape = response.get("rootShape")
            if root_shape not in _ROOT_SHAPES:
                raise RuntimeError("native compiler returned an unknown render root shape")
            try:
                server_render = _rust.vue._read_server_render_program(code, dynamic_elements_json)
            except ValueError:
                # A render function this reader does not know keeps working
                # in the browser; its pages simply mount there.
                server_render = None
            compiled = CompiledRender(
                content_id,
                javascript,
                None,
                ORDINARY_TARGET,
                discovered_signature,
                discovered_sites,
                discovered_runs,
                compiled_local_calls,
                discovered_dynamic,
                discovered_opaque,
                discovered_runtime_events,
                authored_text_plan,
                hydration_plan,
                server_render,
                str(root_shape),
            )
            self._cache[cache_key] = compiled
            if len(self._cache) > 256:
                self._cache.popitem(last=False)
            return compiled


def _normalize_opaque_html_sites(
    elements: object, expected: tuple[dict[str, object], ...]
) -> tuple[dict[str, object], ...]:
    if type(elements) is not list:
        raise RuntimeError("native compiler opaque HTML metadata is missing")
    by_span = {
        (item.get("sourceStart"), item.get("sourceEnd")): item
        for item in elements
        if type(item) is dict and item.get("tag") == "citry-opaque-html"
    }
    normalized: list[dict[str, object]] = []
    for site in expected:
        if type(site) is not dict or set(site) != {"key", "sourceStart", "sourceEnd", "origin"}:
            raise ValueError("opaque HTML site metadata has an invalid shape")
        key, start, end, origin = (site[name] for name in ("key", "sourceStart", "sourceEnd", "origin"))
        if (
            type(key) is not str
            or re.fullmatch(r"citryOpaque[0-9A-Za-z]+", key) is None
            or type(start) is not int
            or type(end) is not int
            or not 0 <= start < end
            or origin not in {"raw", "markup"}
        ):
            raise ValueError("opaque HTML site metadata is invalid")
        element = by_span.get((start, end))
        directives = element.get("directives") if type(element) is dict else None
        if (
            type(directives) is not list
            or len(directives) != 1
            or directives[0].get("name") != "bind"
            or directives[0].get("argument") != "record"
        ):
            raise RuntimeError("native compiler opaque HTML operand does not match prepared metadata")
        normalized.append(dict(site))
    if len(by_span) != len(normalized):
        raise RuntimeError("native compiler emitted an undeclared opaque HTML helper")
    return tuple(normalized)


def _validate_authored_text_plan(response: dict[str, object], original_source: str) -> AuthoredTextPlan:
    """Check that text actions index the exact UTF-8 compiler source."""
    if response.get("compiler") != _NATIVE_COMPILER_IDENTITY:
        raise RuntimeError("native compiler returned an unknown compiler identity")
    source = response.get("transformedTemplate")
    source_hash = response.get("transformedSourceSha256")
    if type(source) is not str or type(source_hash) is not str:
        raise RuntimeError("native compiler transformed source is missing")
    source_bytes = source.encode("utf-8")
    expected_hash = hashlib.sha256(source_bytes).hexdigest()
    if source_hash != expected_hash:
        raise RuntimeError("native compiler transformed source hash does not match its bytes")
    original_bytes = original_source.encode("utf-8")
    original_source_hash = hashlib.sha256(original_bytes).hexdigest()

    plan = response.get("authoredTextPlan")
    if type(plan) is not dict:
        raise RuntimeError("native compiler authored text plan is missing")
    status = plan.get("status")
    expected_keys = {
        "source",
        "sourceSha256",
        "originalSourceSha256",
        "status",
        "actions",
    }
    if status == "unsupported":
        expected_keys.add("reasonCode")
    if set(plan) != expected_keys:
        raise RuntimeError("native compiler authored text plan has an invalid shape")
    if (
        type(status) is not str
        or plan.get("source") != "transformedTemplate"
        or plan.get("sourceSha256") != source_hash
        or plan.get("originalSourceSha256") != original_source_hash
        or status not in {"complete", "unsupported"}
    ):
        raise RuntimeError("native compiler authored text plan targets a different source")
    reason_code = plan.get("reasonCode")
    if status == "unsupported" and (type(reason_code) is not str or reason_code not in _TEXT_PLAN_REASON_CODES):
        raise RuntimeError("native compiler authored text plan has no recognized unsupported reason")

    actions = plan.get("actions")
    if type(actions) is not list:
        raise RuntimeError("native compiler authored text actions are missing")
    previous_end = 0
    previous_original_end = 0
    has_original_spans: bool | None = None
    normalized_actions: list[AuthoredTextAction] = []
    for action in actions:
        if type(action) is not dict:
            raise RuntimeError("native compiler authored text action has an invalid shape")
        action_type = action.get("type")
        expected_action_keys = {"type", "sourceStart", "sourceEnd", "rule"}
        has_original_start = "originalStart" in action
        has_original_end = "originalEnd" in action
        if has_original_start != has_original_end:
            raise RuntimeError("native compiler authored text action has incomplete original spans")
        if has_original_start:
            expected_action_keys.update({"originalStart", "originalEnd"})
        if action_type == "rewrite":
            expected_action_keys.add("content")
        if (
            set(action) != expected_action_keys
            or type(action_type) is not str
            or action_type not in _TEXT_ACTION_RULES
        ):
            raise RuntimeError("native compiler authored text action has an invalid shape")
        start = action.get("sourceStart")
        end = action.get("sourceEnd")
        rule = action.get("rule")
        if (
            type(start) is not int
            or type(end) is not int
            or not 0 <= start < end <= len(source_bytes)
            or start < previous_end
            or type(rule) is not str
            or rule not in _TEXT_ACTION_RULES[action_type]
        ):
            raise RuntimeError("native compiler authored text action has invalid spans or rule")
        try:
            authored = source_bytes[start:end].decode("utf-8")
        except UnicodeDecodeError as error:
            raise RuntimeError("native compiler authored text span splits a UTF-8 character") from error
        if action_type == "rewrite":
            content = action.get("content")
            if type(content) is not str or content == authored:
                raise RuntimeError("native compiler authored text rewrite is not a changed string")
        else:
            content = None
        original_start = action.get("originalStart") if has_original_start else None
        original_end = action.get("originalEnd") if has_original_end else None
        if has_original_spans is None:
            has_original_spans = has_original_start
        elif has_original_spans != has_original_start:
            raise RuntimeError("native compiler authored text actions mix mapped and unmapped spans")
        if has_original_start:
            if (
                type(original_start) is not int
                or type(original_end) is not int
                or not 0 <= original_start < original_end <= len(original_bytes)
                or original_start < previous_original_end
            ):
                raise RuntimeError("native compiler authored text action has invalid original spans")
            try:
                original_bytes[original_start:original_end].decode("utf-8")
            except UnicodeDecodeError as error:
                raise RuntimeError("native compiler original text span splits a UTF-8 character") from error
            if original_bytes[original_start:original_end] != source_bytes[start:end]:
                raise RuntimeError("native compiler original text span does not map to transformed bytes")
            previous_original_end = original_end
        normalized_actions.append(
            AuthoredTextAction(
                action_type,
                start,
                end,
                original_start,
                original_end,
                rule,
                content,
            )
        )
        previous_end = end
    if status == "complete" and normalized_actions and has_original_spans is not True:
        raise RuntimeError("native compiler complete text plan has no original source spans")
    return AuthoredTextPlan(
        source="transformedTemplate",
        source_sha256=source_hash,
        original_source_sha256=original_source_hash,
        status=status,
        actions=tuple(normalized_actions),
        reason_code=reason_code if type(reason_code) is str else None,
    )


def _hydration_span(
    record: dict[str, object], source_bytes: bytes, original_bytes: bytes
) -> tuple[int, int, int | None, int | None]:
    """Read one record's transformed span and optional compiler-input span."""
    start, end = record.get("sourceStart"), record.get("sourceEnd")
    if type(start) is not int or type(end) is not int or not 0 <= start <= end <= len(source_bytes):
        raise RuntimeError("native compiler hydration plan has an invalid source span")
    # The callers' key-set checks already require both original keys or neither.
    if "originalStart" not in record:
        return start, end, None, None
    original_start, original_end = record["originalStart"], record["originalEnd"]
    if (
        type(original_start) is not int
        or type(original_end) is not int
        or not 0 <= original_start <= original_end <= len(original_bytes)
    ):
        raise RuntimeError("native compiler hydration plan has an invalid original span")
    return start, end, original_start, original_end


def _require_opening_tag(original_bytes: bytes, original_start: int | None) -> None:
    # Element and construct positions are opening tags, so a mapped start
    # that is not a `<` points at the wrong bytes.
    if original_start is not None and original_bytes[original_start : original_start + 1] != b"<":
        raise RuntimeError("native compiler hydration position is not an opening tag")


def _hydration_path(value: object) -> tuple[str, ...] | None:
    if value is None:
        return None
    if type(value) is not list or any(type(item) is not str for item in value):
        raise RuntimeError("native compiler hydration plan has an invalid element path")
    return tuple(value)


def _validate_hydration_plan(response: dict[str, object], original_source: str) -> HydrationPlan:
    """
    Check the hydration plan's shape and that its spans fit both sources.

    The server writes Fragment markers and exact attribute values from these
    facts, so a malformed plan is a compiler defect rather than a reason to
    guess: it raises instead of degrading.
    """
    source = response.get("transformedTemplate")
    source_hash = response.get("transformedSourceSha256")
    if type(source) is not str or type(source_hash) is not str:
        raise RuntimeError("native compiler transformed source is missing")
    source_bytes = source.encode("utf-8")
    original_bytes = original_source.encode("utf-8")
    plan = response.get("hydrationPlan")
    if type(plan) is not dict:
        raise RuntimeError("native compiler hydration plan is missing")
    status = plan.get("status")
    expected_keys = {"source", "sourceSha256", "originalSourceSha256", "status", "anchors", "elements"}
    if status == "unsupported":
        expected_keys.add("reasonCode")
    if set(plan) != expected_keys:
        raise RuntimeError("native compiler hydration plan has an invalid shape")
    if (
        plan.get("source") != "transformedTemplate"
        or plan.get("sourceSha256") != source_hash
        or plan.get("originalSourceSha256") != hashlib.sha256(original_bytes).hexdigest()
        or status not in {"complete", "unsupported"}
    ):
        raise RuntimeError("native compiler hydration plan targets a different source")
    reason_code = plan.get("reasonCode")
    if status == "unsupported" and reason_code not in _HYDRATION_REASON_CODES:
        raise RuntimeError("native compiler hydration plan has no recognized unsupported reason")
    raw_anchors, raw_elements = plan.get("anchors"), plan.get("elements")
    if type(raw_anchors) is not list or type(raw_elements) is not list:
        raise RuntimeError("native compiler hydration plan facts are missing")
    if status == "unsupported" and (raw_anchors or raw_elements):
        raise RuntimeError("native compiler unsupported hydration plan carries facts")

    anchors: list[HydrationAnchor] = []
    for anchor in raw_anchors:
        if type(anchor) is not dict:
            raise RuntimeError("native compiler hydration anchor has an invalid shape")
        kind, origin = anchor.get("kind"), anchor.get("origin")
        anchor_keys = {"kind", "origin", "sourceStart", "sourceEnd", "path"}
        if "originalStart" in anchor:
            anchor_keys.update({"originalStart", "originalEnd"})
        if kind == "comment":
            anchor_keys.add("comment")
        if (
            set(anchor) != anchor_keys
            or type(kind) is not str
            or kind not in _HYDRATION_ANCHOR_ORIGINS
            or origin not in _HYDRATION_ANCHOR_ORIGINS[kind]
            or (kind == "comment" and anchor.get("comment") != ("v-if" if origin == "v-if" else ""))
        ):
            raise RuntimeError("native compiler hydration anchor has an invalid shape")
        start, end, original_start, original_end = _hydration_span(anchor, source_bytes, original_bytes)
        if origin not in {"root", "empty-render"}:
            _require_opening_tag(original_bytes, original_start)
        anchors.append(
            HydrationAnchor(
                kind,
                str(origin),
                # The check above pinned a comment anchor's text to a string.
                str(anchor["comment"]) if kind == "comment" else None,
                start,
                end,
                original_start,
                original_end,
                _hydration_path(anchor.get("path")),
            )
        )

    elements: list[HydrationElement] = []
    for element in raw_elements:
        element_keys = {
            "vnode",
            "tag",
            "sourceStart",
            "sourceEnd",
            "path",
            "patchFlag",
            "dynamicProps",
            "attributes",
        }
        if type(element) is dict and "originalStart" in element:
            element_keys.update({"originalStart", "originalEnd"})
        if (
            type(element) is not dict
            or set(element) != element_keys
            or element.get("vnode") not in {"element", "component"}
            or type(element.get("tag")) is not str
            or type(element.get("patchFlag")) is not int
            or type(element.get("attributes")) is not list
        ):
            raise RuntimeError("native compiler hydration element has an invalid shape")
        dynamic_props = element.get("dynamicProps")
        if dynamic_props is not None and (
            type(dynamic_props) is not list or any(type(item) is not str for item in dynamic_props)
        ):
            raise RuntimeError("native compiler hydration element has invalid dynamic props")
        start, end, original_start, original_end = _hydration_span(element, source_bytes, original_bytes)
        _require_opening_tag(original_bytes, original_start)
        attributes: list[HydrationAttribute] = []
        for attribute in element["attributes"]:
            attribute_keys = {"kind", "name", "propKey", "hydration", "sourceStart", "sourceEnd"}
            if type(attribute) is dict and "originalStart" in attribute:
                attribute_keys.update({"originalStart", "originalEnd"})
            if (
                type(attribute) is not dict
                or set(attribute) != attribute_keys
                or attribute.get("kind") not in _HYDRATION_ATTRIBUTE_KINDS
                or attribute.get("hydration") not in _HYDRATION_RULES
                or any(type(attribute.get(key)) not in {str, type(None)} for key in ("name", "propKey"))
            ):
                raise RuntimeError("native compiler hydration attribute has an invalid shape")
            attribute_span = _hydration_span(attribute, source_bytes, original_bytes)
            # An authored attribute's two spans must name the same bytes;
            # the server looks attributes up by their compiler-input span.
            if attribute_span[2] is not None and (
                original_bytes[attribute_span[2] : attribute_span[3]]
                != source_bytes[attribute_span[0] : attribute_span[1]]
            ):
                raise RuntimeError("native compiler hydration attribute span does not map to transformed bytes")
            attributes.append(
                HydrationAttribute(
                    str(attribute["kind"]),
                    attribute["name"],
                    attribute["propKey"],
                    str(attribute["hydration"]),
                    *attribute_span,
                )
            )
        elements.append(
            HydrationElement(
                str(element["vnode"]),
                element["tag"],
                start,
                end,
                original_start,
                original_end,
                _hydration_path(element.get("path")),
                element["patchFlag"],
                None if dynamic_props is None else tuple(dynamic_props),
                tuple(attributes),
            )
        )
    return HydrationPlan(
        source="transformedTemplate",
        source_sha256=source_hash,
        original_source_sha256=hashlib.sha256(original_bytes).hexdigest(),
        status=status,
        anchors=tuple(anchors),
        elements=tuple(elements),
        reason_code=reason_code if type(reason_code) is str else None,
    )


def _normalize_runtime_event_sites(
    elements: object, expected: tuple[dict[str, object], ...]
) -> tuple[dict[str, object], ...]:
    if type(elements) is not list:
        raise RuntimeError("native compiler runtime event metadata is missing")
    by_span = {
        (item.get("sourceStart"), item.get("sourceEnd")): item
        for item in elements
        if type(item) is dict and item.get("runtimeEventsBindingKey") is not None
    }
    normalized: list[dict[str, object]] = []
    for declaration in expected:
        element = by_span.get((declaration.get("sourceStart"), declaration.get("sourceEnd")))
        if element is None or element.get("runtimeEventsBindingKey") != declaration.get("bindingKey"):
            raise ValueError("native compiler changed a runtime event site declaration")
        directives = element.get("directives")
        if type(directives) is not list:
            raise RuntimeError("native compiler runtime event directive metadata is missing")
        runtime_directives = [
            directive
            for directive in directives
            if type(directive) is dict
            and directive.get("name") == "citry-runtime-events"
            and directive.get("argument") is None
            and directive.get("modifiers") == []
            and directive.get("runtimeLifecycle") is True
            and type(directive.get("ordinal")) is int
            and directive["ordinal"] >= 0
        ]
        if len(runtime_directives) != 1:
            raise ValueError("native compiler changed a runtime event directive declaration")
        normalized.append(
            {
                "siteId": f"{element['siteId']}D{runtime_directives[0]['ordinal']}",
                "steps": declaration.get("steps", []),
                "bindingKey": declaration["bindingKey"],
            }
        )
    if len(normalized) != len(by_span):
        raise ValueError("native compiler returned undeclared runtime event sites")
    return tuple(normalized)


def _normalize_replacement_sites(
    sites: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    # Each entry keeps its validated site id beside the record so the sort below
    # orders by a value already proven to be a string.
    normalized: list[tuple[str, dict[str, object]]] = []
    seen: set[str] = set()
    for site in sites:
        site_id = site.get("siteId")
        descendants = site.get("localDescendants")
        descendant_runs = site.get("localDescendantRuns", [])
        if (
            type(site_id) is not str
            or not site_id
            or type(descendants) is not list
            or type(descendant_runs) is not list
        ):
            raise ValueError("native compiler returned invalid replacement-site metadata")
        if site_id in seen or any(type(item) is not str for item in descendants):
            raise ValueError("native compiler returned duplicate or invalid replacement-site metadata")
        ordered = sorted(descendants)
        ordered_runs = sorted(descendant_runs)
        if len(set(ordered)) != len(ordered):
            raise ValueError("native compiler returned duplicate local replacement descendants")
        seen.add(site_id)
        if any(type(item) is not str for item in ordered_runs) or len(set(ordered_runs)) != len(ordered_runs):
            raise ValueError("native compiler returned duplicate or invalid replacement descendant runs")
        if "slotOutlets" in site:
            _validate_slot_names(site["slotOutlets"], "replacement-site slot outlets")
        normalized.append((site_id, {**site, "localDescendants": ordered, "localDescendantRuns": ordered_runs}))
    # Generated output is cache-keyed, so the order has to be stable.
    normalized.sort(key=lambda item: item[0])
    return tuple(record for _, record in normalized)


def _normalize_local_call_runs(
    returned: object, requested: tuple[dict[str, object], ...]
) -> tuple[dict[str, object], ...]:
    declaration_keys = (
        "runId",
        "typeKey",
        "componentTag",
        "sourceStart",
        "sourceEnd",
        "loopSourceStart",
        "loopSourceEnd",
    )
    expression_keys = ("collectionExpression", "idExpression", "keyExpression")
    if type(returned) is not list or len(returned) != len(requested):
        raise ValueError("native compiler returned mismatched local call runs")
    normalized: list[dict[str, object]] = []
    for actual, expected in zip(returned, requested, strict=True):
        if type(actual) is not dict or set(actual) != {*declaration_keys, *expression_keys}:
            raise ValueError("native compiler returned invalid local call-run metadata")
        if any(actual[key] != expected.get(key) for key in declaration_keys):
            raise ValueError("native compiler changed a local call-run declaration")
        expected_expressions = {
            "collectionExpression": f"$citryPrepared.callRuns.{actual['runId']}",
            "idExpression": "citryOccurrenceId",
            "keyExpression": "citryOccurrenceId",
        }
        if any(actual[key] != value for key, value in expected_expressions.items()):
            raise ValueError("native compiler returned invalid local call-run expressions")
        normalized.append(dict(actual))
    return tuple(normalized)


def _normalize_local_calls(
    elements: object, requested: tuple[dict[str, object], ...]
) -> tuple[dict[str, object], ...]:
    if type(elements) is not list:
        raise ValueError("native compiler returned invalid element metadata")
    returned = [element.get("localCall") for element in elements if type(element) is dict and element.get("localCall")]
    if len(returned) != len(requested):
        raise ValueError("native compiler returned mismatched local calls")
    # The fills written inside each call, which the browser follows when a replaced element in the
    # called component holds a slot outlet.
    fills_by_id = {
        element["localCall"].get("localId"): element.get("fills", [])
        for element in elements
        if type(element) is dict and type(element.get("localCall")) is dict
    }
    by_id = {value.get("localId"): value for value in returned if type(value) is dict}
    normalized: list[dict[str, object]] = []
    for expected in requested:
        local_id = expected.get("localId")
        actual = by_id.get(local_id)
        if type(actual) is not dict or set(actual) != {
            "localId",
            "typeKey",
            "idExpression",
            "keyExpression",
            "bindings",
        }:
            raise ValueError("native compiler returned invalid local-call metadata")
        if actual["typeKey"] != expected.get("typeKey") or actual["bindings"] != expected.get("bindings", []):
            raise ValueError("native compiler changed a local-call declaration")
        if (
            actual["idExpression"] != f"$citryPrepared.calls.{local_id}.id"
            or actual["keyExpression"] != f"$citryPrepared.calls.{local_id}.key"
        ):
            raise ValueError("native compiler returned invalid local-call expressions")
        record = dict(expected)
        fills = _normalize_slot_fills(fills_by_id.get(local_id))
        # A call without fills keeps its exact bytes.
        if fills:
            record["fills"] = fills
        normalized.append(record)
    return tuple(normalized)


def _validate_slot_names(names: object, label: str) -> None:
    # Generated output is cache-keyed, so the compiler sorts these names and the check keeps it so.
    if (
        type(names) is not list
        or any(type(name) is not str or not name for name in names)
        or names != sorted(set(names))
    ):
        raise ValueError(f"native compiler returned invalid {label}")


def _normalize_slot_fills(fills: object) -> list[dict[str, object]]:
    if type(fills) is not list:
        raise ValueError("native compiler returned invalid local-call fills")
    normalized: list[dict[str, object]] = []
    for fill in fills:
        if type(fill) is not dict or set(fill) != {"name", "localDescendants", "localDescendantRuns", "slotOutlets"}:
            raise ValueError("native compiler returned invalid local-call fill")
        name = fill["name"]
        if type(name) is not str or not name:
            raise ValueError("native compiler returned an invalid fill name")
        _validate_slot_names(fill["slotOutlets"], "fill slot outlets")
        descendants = fill["localDescendants"]
        runs = fill["localDescendantRuns"]
        if (
            type(descendants) is not list
            or type(runs) is not list
            or any(type(item) is not str for item in (*descendants, *runs))
            or len(set(descendants)) != len(descendants)
            or len(set(runs)) != len(runs)
        ):
            raise ValueError("native compiler returned invalid fill descendants")
        normalized.append(
            {
                "name": name,
                "localDescendants": sorted(descendants),
                "localDescendantRuns": sorted(runs),
                "slotOutlets": list(fill["slotOutlets"]),
            }
        )
    names = [str(fill["name"]) for fill in normalized]
    if names != sorted(set(names)):
        raise ValueError("native compiler returned duplicate or unsorted local-call fills")
    return normalized


def _signature_json(signature: tuple[RuntimeDirective, ...]) -> list[dict[str, object]]:
    return [
        {"siteId": item.site_id, "name": item.name, "arg": item.arg, "modifiers": list(item.modifiers)}
        for item in signature
    ]


def _compiled_content_id(
    identity: str,
    response: dict[str, object],
    preamble: str,
    code: str,
    signature: tuple[RuntimeDirective, ...],
    replacement_sites: tuple[dict[str, object], ...],
) -> str:
    """Bind a definition ID to every executable and compatibility-bearing byte."""
    payload = {
        "requestIdentity": identity,
        "compiler": response.get("compiler"),
        "compilerVersion": response.get("compilerVersion"),
        "options": response.get("options"),
        "transformedSourceSha256": response.get("transformedSourceSha256"),
        "authoredTextPlan": response.get("authoredTextPlan"),
        "hydrationPlan": response.get("hydrationPlan"),
        "codeSha256": response.get("codeSha256"),
        "preamble": preamble,
        "code": code,
        "directiveSignature": _signature_json(signature),
        "replacementSites": replacement_sites,
        "localCallRuns": response.get("localCallRuns"),
        "elements": response.get("elements"),
        "helperContract": HELPER_CONTRACT,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def definition_templates(view: PreparedView, *, tag_for_type: Callable[[str], str]) -> dict[str, str]:
    """Compose the supported prepared tree into templates for native compilation."""
    occurrences = {item.id: item for item in view.occurrences}
    definitions = {item.id: item for item in view.definitions}
    tags = {item.type_key: tag_for_type(item.type_key) for item in view.occurrences}
    if len(set(tags.values())) != len(tags):
        raise ValueError("component tag mapping is not injective")
    if any(re.fullmatch(r"[a-z][a-z0-9.-]*-[a-z0-9.-]+", tag) is None for tag in tags.values()):
        raise ValueError("component tag mapping returned an unsafe custom-element name")

    def render_nodes(nodes: tuple[PreparedNode, ...], owner_id: str) -> str:
        output: list[str] = []

        def render(current_nodes: tuple[PreparedNode, ...]) -> None:
            for node in current_nodes:
                render_one(node)

        def render_one(node: PreparedNode) -> None:
            if isinstance(node, Html):
                if node.source != "template":
                    raise ValueError("only explicitly template-authored HTML may be compiled")
                output.append(node.text)
            elif isinstance(node, TextBinding):
                output.append(f"{{{{ $citryPrepared[{node.key!r}] }}}}")
            elif isinstance(node, SlotOutlet):
                fill = node.selected
                if any(isinstance(child, SlotOutlet) for child in fill.children):
                    raise ValueError("nested ownership transitions need the generated fallback bridge")
                body = render_nodes(fill.children, fill.lexical_owner_id or owner_id)
                if fill.lexical_owner_id == owner_id:
                    output.append(f'<slot name="{node.site_id}">{body}</slot>')
                else:
                    output.append(f'<slot name="{node.site_id}"></slot>')
            elif isinstance(node, ComponentCall):
                child = occurrences[node.occurrence_id]
                child_definition = definitions[child.definition_id]
                tag = tags[child.type_key]
                escaped_id = html.escape(child.id, quote=True)
                slots: list[str] = []
                for candidate in _walk_slots(child_definition.children):
                    fill = candidate.selected
                    if fill.lexical_owner_id == owner_id:
                        slots.append(
                            f"<template v-slot:['{candidate.site_id}']>"
                            f"{render_nodes(fill.children, owner_id)}</template>"
                        )
                output.append(f'<{tag} citry-id="{escaped_id}" key="{escaped_id}">' + "".join(slots) + f"</{tag}>")
            else:
                # This path composes whole-definition templates, where an element,
                # a local call, or a forwarded slot has no compiled form yet. Name
                # the node instead of failing later on a missing attribute.
                raise TypeError(f"prepared node {type(node).__name__} has no definition-template form")

        render(nodes)
        return "".join(output)

    return {
        definition.id: render_nodes(definition.children, occurrence.id)
        for occurrence in view.occurrences
        for definition in (definitions[occurrence.definition_id],)
    }


def definition_compile_input(nodes: tuple[PreparedNode, ...]) -> DefinitionCompileInput:
    """Compose one reusable direct-capture definition and its provenance."""
    parts: list[str] = []
    local_calls: list[dict[str, object]] = []
    element_bindings: list[dict[str, object]] = []
    element_stack: list[tuple[str, _SlotKeyScope | None]] = []
    slot_key_scopes: list[_SlotKeyScope] = []
    byte_position = 0

    def append(value: str) -> None:
        nonlocal byte_position
        parts.append(value)
        byte_position += len(value.encode())

    def render(current_nodes: tuple[PreparedNode, ...]) -> None:
        for node in current_nodes:
            if isinstance(node, Html):
                if node.source != "template":
                    raise ValueError("only explicitly template-authored HTML may be compiled")
                append(node.text)
            elif isinstance(node, TextBinding):
                append(f"{{{{ $citryPrepared.{node.key} }}}}")
            elif isinstance(node, ElementOpen):
                start = byte_position
                attrs = list(node.authored_attrs)
                if node.attrs_binding_key is not None:
                    spread = f'v-bind="$citryPrepared.{node.attrs_binding_key}"'
                    spread_index = prepared_spread_index(node.authored_attrs)
                    if spread_index is None:
                        attrs.append(spread)
                    else:
                        attrs.insert(spread_index, spread)
                if node.key_binding_key is not None:
                    attrs.append(f':key="$citryPrepared.{node.key_binding_key}"')
                # Keep the compatibility composer on the same native-state
                # contract as the direct assembler.  ``ElementOpen`` predates
                # the typed ``has_spread`` field, so its generated attrs
                # binding is the only spread provenance available here.
                if node.tag.casefold() in {"input", "textarea", "select", "option"}:
                    from .capture import (  # noqa: PLC0415
                        vue_owned_native_marker,
                        vue_owned_native_properties,
                    )

                    attrs.append(
                        vue_owned_native_marker(
                            vue_owned_native_properties(
                                node.tag,
                                node.authored_attrs,
                                has_spread=node.attrs_binding_key is not None,
                            )
                        )
                    )
                seen_events: set[str] = set()
                for binding in node.event_bindings:
                    event = str(binding["event"])
                    if event in seen_events:
                        raise ValueError("prepared Vue target supports one Events binding per DOM event")
                    seen_events.add(event)
                    modifiers = [name for name in ("prevent", "stop", "self", "once") if binding[name] is True]
                    if binding["key"] is not None:
                        modifiers.append(str(binding["key"]))
                    suffix = "" if not modifiers else "." + ".".join(modifiers)
                    binding_id = str(binding["id"])
                    args = binding["args"]
                    authored_args = _generated_event_args(args)
                    attrs.append(
                        _generated_vue_attr(
                            f"v-on:{event}{suffix}",
                            f"$citryEvents.dispatch('{binding_id}', $event{authored_args})",
                        )
                    )
                rendered_attrs = "" if not attrs else " " + " ".join(attrs)
                append(f"<{node.tag}{rendered_attrs}>")
                if node.attrs_binding_key is not None or node.key_binding_key is not None:
                    element_bindings.append(
                        {
                            "sourceStart": start,
                            "sourceEnd": byte_position,
                            "attrsBindingKey": node.attrs_binding_key,
                            "keyBindingKey": node.key_binding_key,
                        }
                    )
                element_scope = (
                    None if node.key_binding_key is None else _SlotKeyScope(f"$citryPrepared.{node.key_binding_key}")
                )
                element_stack.append((node.tag, element_scope))
                if element_scope is not None:
                    slot_key_scopes.append(element_scope)
            elif isinstance(node, ElementClose):
                if not element_stack or element_stack[-1][0].lower() != node.tag.lower():
                    raise ValueError("prepared element close has no matching opening")
                _, element_scope = element_stack.pop()
                if element_scope is not None:
                    if not slot_key_scopes or slot_key_scopes[-1] is not element_scope:
                        raise ValueError("prepared element key scope changed before its close")
                    slot_key_scopes.pop()
                append(f"</{node.tag}>")
            elif isinstance(node, LocalComponentCall):
                start = byte_position
                append(
                    f'<{node.component_tag} :citry-id="$citryPrepared.calls.{node.local_id}.id" '
                    f':key="$citryPrepared.calls.{node.local_id}.key">'
                )
                opening_end = byte_position
                for fill in node.fills:
                    append(f"<template v-slot:['{fill.site_id}']>")
                    render(fill.children)
                    append("</template>")
                append(f"</{node.component_tag}>")
                local_calls.append(
                    {
                        "localId": node.local_id,
                        "typeKey": node.type_key,
                        "componentTag": node.component_tag,
                        "sourceStart": start,
                        "sourceEnd": opening_end,
                        "bindings": [],
                    }
                )
            elif isinstance(node, PreparedSlotOutlet):
                slot_key = _next_slot_key(slot_key_scopes)
                append(
                    f'<slot v-if="$citryPrepared.selectedSlots[{node.site_id!r}] === '
                    f'\'supplied\'" name="{node.site_id}"{_slot_key_attr(slot_key)}></slot>'
                )
                if node.fallback:
                    append(f"<template v-else-if=\"$citryPrepared.selectedSlots[{node.site_id!r}] === 'fallback'\">")
                    render(node.fallback)
                    append("</template>")
            elif isinstance(node, ForwardedSlot):
                slot_key = _next_slot_key(slot_key_scopes)
                append(f'<slot name="{node.site_id}"{_slot_key_attr(slot_key)}></slot>')
            elif isinstance(node, (ComponentCall, SlotOutlet)):
                raise TypeError("legacy absolute calls and unlocalized slot ownership cannot be compiled directly")
            else:
                raise TypeError(f"unsupported prepared node {type(node).__name__}")

    render(nodes)
    return DefinitionCompileInput("".join(parts), tuple(local_calls), tuple(element_bindings))


def definition_compile_inputs(view: PreparedView) -> dict[str, DefinitionCompileInput]:
    """Compose reusable direct-capture definitions and compiler provenance."""
    return {definition.id: definition_compile_input(definition.children) for definition in view.definitions}


def compile_view(view: PreparedView, compiler: NativeCompiler) -> CompiledView:
    """Compile every reusable definition and bind occurrences to content identities."""
    inputs = definition_compile_inputs(view)
    definitions_by_id = {item.id: item for item in view.definitions}
    compiled = {
        definition_id: compiler.compile(
            item.template,
            type_key=definitions_by_id[definition_id].type_key,
            local_calls=item.local_calls,
            element_bindings=item.element_bindings,
            local_call_runs=item.local_call_runs,
            dynamic_elements=item.dynamic_elements,
            runtime_event_sites=item.runtime_event_sites,
        )
        for definition_id, item in inputs.items()
    }
    replacements = {definition_id: item.id for definition_id, item in compiled.items()}
    return CompiledView(replace_definition_ids(view, replacements), compiled)


def _walk_slots(nodes: tuple[PreparedNode, ...]) -> Iterator[SlotOutlet]:
    for node in nodes:
        if isinstance(node, SlotOutlet):
            yield node
        elif isinstance(node, ComponentCall):
            continue
