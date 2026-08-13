"""
The serialize-time half of the ``events`` extension: the events manifest and
the events client runtime.

During a render, :func:`capture_instance` records one entry per rendered
Events-declaring component instance (its minted state token and its public
State values), and the entries bubble up to the root context as nested
renders are consumed. At serialize time, :func:`emit_events_dependencies`
turns the collected entries into what the page needs:

- the ``data-citry-events`` manifest tag (design ``events.md`` 4.4): named
  component-class and component-instance records encoded as script-safe JSON.
  It is placed BEFORE the sibling ``data-citry`` manifest tag, so whenever
  the client can fire a component call, the events manifest is already
  parsed (the boot-order rule, design ``events.md`` 5.2);
- the pinned standard or CSP Alpine/Events runtime tag for every client-active
  ownership graph, including graphs with no Events instances; strict CSP
  serialization selects ``.../ext/events/runtime-csp.js`` while the other
  modes select ``.../ext/events/runtime.js``;
- an inline bootstrap script delivered the same way as other dependency
  scripts, so in a fragment it rides the ``data-citry`` manifest and runs
  synchronously while the manifest is processed (design ``events.md`` 5.2
  "Load ordering").

The emission rides the dependencies extension's ``on_dependencies`` hook, so
placement (``<c-js>`` placeholders, head/body defaults, fragment manifests)
stays in one place. Design: ``docs/design/events.md`` sections 4.4 and 5.
"""

from __future__ import annotations

import json
from dataclasses import fields
from functools import cache
from typing import TYPE_CHECKING, Literal, NamedTuple

from citry._owned_resource import _OwnedResource
from citry._protocol.events import (
    build_component_instance,
    build_descriptor,
    build_handler_descriptor,
    build_manifest,
)
from citry.constness import const_value
from citry.ext.dependencies.types import Dependency, Script
from citry.ext.events.handlers import event_options
from citry.ext.events.routes import CSP_RUNTIME_PATH, EVENTS_CSP_RUNTIME_SRC, EVENTS_RUNTIME_SRC, RUNTIME_PATH
from citry.ext.events.tokens import mint_state_token
from citry.ownership import OwnershipState
from citry.ownership_manifest import EXTRA_KEY as OWNERSHIP_MANIFEST_KEY
from citry.ownership_manifest import OwnershipManifestArtifact

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.citry_context import CitryContext
    from citry.ext.dependencies.emission import OnDependenciesContext
    from citry.ext.events.extension import EventsExtension
    from citry.extension import OnComponentDataContext

# The key under which the extension keeps its captured instance entries in
# ``CitryContext.extra`` (top-level keys there are namespaced by owner).
EXTRA_KEY = "events"


_RuntimeVariant = Literal["standard", "csp"]


@cache
def _client_runtime_js(variant: _RuntimeVariant = "standard") -> str:
    """The pinned Alpine/Events bundle used inline without a mounted route."""
    source = EVENTS_CSP_RUNTIME_SRC if variant == "csp" else EVENTS_RUNTIME_SRC
    return source.read_text(encoding="utf8")


def _runtime_resource(citry: Citry, variant: _RuntimeVariant = "standard") -> _OwnedResource:
    """Return the shared source used by mounted emission and route serving."""
    path = CSP_RUNTIME_PATH if variant == "csp" else RUNTIME_PATH
    url = citry.build_url(path) if citry.mounted_prefix is not None else path
    return _OwnedResource(
        url=url,
        content=_client_runtime_js(variant),
        content_type="text/javascript",
        headers=(("Cache-Control", "no-store"),),
    )


# The inline bootstrap script emitted alongside the runtime script tag
# (design ``events.md`` 5.2 "Load ordering"). Fragment script execution order
# is not guaranteed, so this runs before the URL-served events runtime may
# have arrived and does two things: defines a queueing ``Citry.events``
# (including Promise-preserving ``send`` and ``applyActions`` plus queued
# configuration, listeners, and transport declarations), and registers the
# context decorator through
# ``Citry.manager.decorateContext`` so every ``$component`` payload carries
# ``state`` / ``loading`` / ``error`` / ``sendEvent`` / ``onEvent`` members
# from the first call on. The
# runtime (citry/ext/events/client/citry-events.js) recognizes the stub by
# ``_stubQueue``, replaces it, and upgrades ``_decorate`` / ``_onFor`` in
# place; the member closures below delegate through ``C.events`` at call
# time, so payloads decorated in the early window keep working afterwards.
_EVENTS_BOOTSTRAP_STUB = """\
/* Citry events bootstrap stub: queues Citry.events calls until the events runtime arrives. */
(function () {
  var C = (globalThis.Citry = globalThis.Citry || {});
  if (C.events) return;
  var q = [];
  var listen = function (kind, args) {
    var entry = { kind: kind, args: args, off: null, dead: false };
    q.push(entry);
    return function () { entry.dead = true; if (entry.off) entry.off(); };
  };
  C.events = {
    _stubQueue: q,
    _decoratorHooked: false,
    send: function () {
      var args = [].slice.call(arguments);
      return new Promise(function (resolve, reject) {
        q.push({ kind: "send", args: args, resolve: resolve, reject: reject });
      });
    },
    on: function () { return listen("on", [].slice.call(arguments)); },
    configure: function (opts) { q.push({ kind: "configure", args: [opts] }); },
    registerTransport: function () { q.push({ kind: "registerTransport", args: [].slice.call(arguments) }); },
    applyActions: function () {
      var args = [].slice.call(arguments);
      return new Promise(function (resolve, reject) {
        q.push({ kind: "applyActions", args: args, resolve: resolve, reject: reject });
      });
    },
    _onFor: function (id, name, fn) { return listen("onEvent", [id, name, fn]); },
    _decorate: function (ctx) {
      ctx.state = null;
      ctx.loading = function (name) {
        return C.events._stubQueue ? false : C.events._loadingFor(ctx.id, name);
      };
      ctx.error = function (name) {
        return C.events._stubQueue ? null : C.events._errorFor(ctx.id, name);
      };
      ctx.sendEvent = function (name, args, opts) { return C.events.send(ctx.id, name, args, opts); };
      ctx.onEvent = function (name, fn) { return C.events._onFor(ctx.id, name, fn); };
    },
  };
  if (C.manager && C.manager.decorateContext) {
    C.manager.decorateContext(function (ctx, control) { C.events._decorate(ctx, control); });
    C.events._decoratorHooked = true;
  }
})();"""


class EventInstanceEntry(NamedTuple):
    """
    One rendered Events-declaring component instance, captured during render.

    The fields become one named ``componentInstances`` record in the Events
    manifest (design ``events.md`` 4.4).
    """

    render_id: str
    """The per-render instance id (``component.id``)."""
    component_class_id: str
    """``Component.class_id`` of the instance's class."""
    state_token: str | None
    """The minted state token; ``None`` for a component with no State class."""
    public_state_json: str
    """The instance's public State values, already serialized to JSON (kept
    as text so entries stay hashable for the dedup-on-insert set)."""


def capture_instance(extension: EventsExtension, ctx: OnComponentDataContext) -> None:
    """
    Record the rendered instance for the events manifest, if it declares Events.

    Builds the State instance (via ``state_data`` or the kwargs derivation),
    mints its token, gathers the ``_public`` field values, and stores the
    entry on the render context, from where it bubbles to the root as nested
    renders merge. It also keeps the fixed-name ``data-cid`` marker available
    in the no-runtime ``simple`` strategy. For graph-backed output the general
    ownership serializer owns the same marker for every client-active class.
    """
    comp_cls = type(ctx.component)
    info = extension.resolve(comp_cls)
    if info.events_cls is None:
        return

    if info.state_cls is not None and info.state_meta is not None:
        state = extension.build_state(ctx.component)
        # A kwarg written in a template arrives Const-marked (a transparent
        # proxy, citry/constness.py), and State fields are commonly filled
        # from kwargs. The JSON serializer rejects the proxy, so unwrap each
        # field before minting; the instance is freshly built for this
        # capture, so the write-back touches nothing the user holds.
        for state_field in fields(state):
            setattr(state, state_field.name, const_value(getattr(state, state_field.name)))
        meta = info.state_meta
        token = mint_state_token(
            state,
            class_id=comp_cls.class_id,
            secret=ctx.citry.settings.secret,
            max_age=meta.max_age,
            max_bytes=meta.max_bytes,
            storage=meta.storage,
            cache=ctx.citry.cache,
        )
        # Only the public fields ship in plain sight; non-public fields ride
        # inside the opaque token and appear nowhere else (design 7.2). The
        # token mint above already rejected values that do not survive JSON.
        values = {name: getattr(state, name) for name in meta.public}
    else:
        # A stateless Events component still registers its instance (the
        # client needs the instance-to-class mapping to dispatch calls), but
        # there is no State to sign or seed bindings from.
        token = None
        values = {}

    entry = EventInstanceEntry(
        render_id=ctx.component.id,
        component_class_id=comp_cls.class_id,
        state_token=token,
        public_state_json=json.dumps(values, sort_keys=True, allow_nan=False),
    )
    # An insertion-ordered set (dict keyed by the entry): entries bubble up
    # through every ancestor as renders merge, and the dedup-on-insert keeps
    # one copy per instance while preserving render order.
    entries: dict[EventInstanceEntry, None] = ctx.context.extra.setdefault(EXTRA_KEY, {})
    entries[entry] = None
    ctx.context._add_root_markers([f'data-cid="{ctx.component.id}"'])


def merge_instance_entries(parent_context: CitryContext, child_context: CitryContext) -> None:
    """Bubble a consumed nested render's captured entries into the enclosing render's context."""
    child_entries = child_context.extra.get(EXTRA_KEY)
    if child_entries:
        parent_entries: dict[EventInstanceEntry, None] = parent_context.extra.setdefault(EXTRA_KEY, {})
        parent_entries.update(child_entries)


def emit_events_dependencies(extension: EventsExtension, ctx: OnDependenciesContext) -> None:
    """
    The extension's ``on_dependencies`` implementation: inject the pinned
    runtime for every client-active graph, plus the Events manifest and
    bootstrap stub when the tree contains an Events-declaring component.

    The manifest tag goes into ``before_manifest`` so it renders before the
    sibling ``data-citry`` tag (the boot-order rule, design 5.2). The runtime
    script and the stub join the ordinary script list, in front of the
    component scripts; in a fragment they thereby ride the ``data-citry``
    manifest, where the inline stub runs synchronously during processing.
    The "simple" strategy ships no client runtime at all, so it gets none of
    the three.
    """
    if ctx.strategy not in ("document", "fragment") or ctx._security_javascript in {"omit", "forbid"}:
        return
    entries: list[EventInstanceEntry] = list(ctx.context.extra.get(EXTRA_KEY, {}))
    if ctx.context.ownership is not None:
        active_ids = {
            record.render_id
            for record in ctx.context.ownership.snapshot().logical_instances
            if record.state == OwnershipState.ACTIVE
        }
        entries = [entry for entry in entries if entry.render_id in active_ids]
    ownership = ctx.context.extra.get(OWNERSHIP_MANIFEST_KEY)
    graph_revision = ownership.revision if isinstance(ownership, OwnershipManifestArtifact) else None
    has_graph = graph_revision is not None
    if not entries and not has_graph:
        return

    if entries:
        ctx.before_manifest.append(
            _build_events_manifest(extension, ctx.citry, entries, graph_revision=graph_revision)
        )

    injected: list[Dependency] = []
    if entries:
        injected.append(Script(kind="core", content=_EVENTS_BOOTSTRAP_STUB, wrap=False))
    # A3 uses this pinned bundle as the Alpine installer for every client
    # graph, including graphs with no Events entries. Mounted pages use the
    # no-store route; zero-configuration documents receive the same bundle inline
    # so graph-linked callbacks never wait on an unavailable owner.
    runtime_variant: _RuntimeVariant = "csp" if ctx._security_csp == "strict" else "standard"
    if ctx.citry.mounted_prefix is not None:
        resource = _runtime_resource(ctx.citry, runtime_variant)
        runtime = Script(kind="core", url=resource.url)
        runtime._owned_resource = resource
        injected.append(runtime)
    else:
        injected.append(Script(kind="core", content=_client_runtime_js(runtime_variant), wrap=False))
    ctx.scripts[:0] = injected


def _build_events_manifest(
    extension: EventsExtension,
    citry: Citry,
    entries: list[EventInstanceEntry],
    *,
    graph_revision: str | None = None,
) -> Script:
    """
    The ``data-citry-events`` manifest tag for the captured instances.

    Instances keep render order and each class descriptor is built once. The
    JSON text escapes ``<`` so application State containing ``</script>``
    cannot close the inert script element; ``JSON.parse`` restores the value.
    """
    descriptors: dict[str, dict[str, object]] = {}
    for entry in entries:
        if entry.component_class_id in descriptors:
            continue
        info = extension.resolve(citry.get_component_by_class_id(entry.component_class_id))
        event_handlers: dict[str, dict[str, object]] = {}
        for handler in info.handlers.values():
            # The client-facing hints: the primary HTTP method plus the
            # resolved debounce/throttle defaults (design 3.5). The server
            # stays the authority; this is a client convenience.
            # The queue knobs the client runtime reads at queue time (design
            # 3.5 and 5.6). They exist per handler only, so the @event record
            # on the handler function is their single source, and only
            # non-default values ride the descriptor (design 4.4).
            options = event_options(handler.func)
            event_handlers[handler.name] = build_handler_descriptor(
                handler.methods[0],
                uses_state="state" in handler.params,
                debounce_milliseconds=handler.debounce,
                throttle_milliseconds=handler.throttle,
                latest_call_wins=options is not None and options.latest_wins,
                allow_batching=options is None or options.bundle,
            )
        # Omission is the compact/default wire form: every public value is
        # writable. An explicit list narrows that capability, and an empty
        # list is meaningful (read-only public State), so it must survive.
        writable = (
            info.state_meta.model
            if info.state_meta is not None and info.state_meta.model != info.state_meta.public
            else None
        )
        descriptor = build_descriptor(
            entry.component_class_id,
            event_handlers,
            writable_state_fields=writable,
        )
        descriptors[entry.component_class_id] = descriptor

    manifest = build_manifest(
        graph_revision,
        list(descriptors.values()),
        [
            build_component_instance(
                entry.render_id,
                entry.component_class_id,
                entry.state_token,
                json.loads(entry.public_state_json),
            )
            for entry in entries
        ],
    )
    return Script(
        kind="core",
        content=json.dumps(manifest, separators=(",", ":"), sort_keys=True, allow_nan=False).replace("<", "\\u003c"),
        attrs={"type": "application/json", "data-citry-events": True},
    )
