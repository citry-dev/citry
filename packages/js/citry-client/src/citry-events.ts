/**
 * Citry's events client runtime (served at `ext/events/runtime.js`).
 *
 * This file is the source; the committed build output lives at
 * `packages/py/citry/citry/ext/events/client/citry-events.js` (esbuild iife
 * bundle, see this package's `build` script). The bundle embeds a pinned
 * AlpineJS 3.15.12 plus `@alpinejs/morph` 3.15.12 as the reactivity layer
 * (design: docs/design/events.md section 5, decision 14.1.10).
 *
 * What this runtime does (the v1 "Alpine layer": scopes and magics):
 *
 * 1. Installs the pinned Alpine and morph objects into citry.js's permanent
 *    hook broker. The core owns the one Citry MutationObserver, selector,
 *    init interceptor, magic dispatchers, morph entry point, and guarded
 *    startup. Events contributes removable providers before the broker marks
 *    Alpine ready; only the broker's `Alpine.start()` waits for DOM readiness.
 *
 * 2. Consumes strict `data-citry-events` manifest tags (design 4.4): named
 *    component-class records and component-instance records in script-safe
 *    JSON, linked to the matching client-graph revision when one exists.
 *
 * 3. Keeps the two component identities separate (design 5.5, the
 *    component-identity spike): the component id (`data-cid-<id>`) is the
 *    server's faithful surface and changes on every render; the anchor is a
 *    stable, client-internal identity of one interactive DOM position. The
 *    reactive State, the scope, the epoch guard, pending writes, and the
 *    state token all live on the anchor. The only tie between the two is the
 *    component-id-to-anchor index (a plain map re-linked as renders land);
 *    no anchor attribute rides the DOM and no node-keyed map is used, because
 *    a wholesale morph swap would orphan either one (spike F-CI-1/F-CI-6).
 *
 * 4. Creates each interactive instance's Alpine scope eagerly: an empty
 *    boundary entry on the instance root plus the isolation truncation, so
 *    a nested citry instance never inherits its parent's scopes, and
 *    nothing is ever written into a user's `x-data`. The attach happens at
 *    manifest time when the root is already parsed, and otherwise from
 *    Alpine's init walk just before the root initializes (a head-placed
 *    `<c-js />` makes the runtime consume the manifest while only the head
 *    exists, so there is no root to attach to yet).
 *
 * 5. Registers the magics (`$state`, `$loading`, `$error`, `$sendEvent`,
 *    `$onEvent`) and decorates every `$component` payload with `state`,
 *    `sendEvent`, and `onEvent`.
 *
 * 6. Applies result envelopes (`applyActions`, design 4.3/5.5): faithful
 *    action order with the `delay`/`wait` timing fields, morph with the
 *    composite-key callback and the `updating` hook (the `#c-ignore` marker,
 *    the focused-draft guard), the uncorrelated-id lifecycle (the caller's
 *    three-way split, reset for every other id, `#c-key` linking with the
 *    horizon cut), the applier-owned manifest-tag delivery, the anchor
 *    retirement sweep, per-action liveness, the apply-side epoch guard, the
 *    post-patch binding re-apply and busy re-stamp, and the `:swapped` and
 *    `:stale` lifecycle events through the shared dispatch helper.
 *
 * 7. Puts calls on the wire (design 4.2, 5.2, 6.1, 6.2): builds the call
 *    envelope (protocol string, minted correlation id, the advertised
 *    capabilities, calls with token, pending updates, and the send-side
 *    epoch increment), sends it through the registered transport (the
 *    built-in fetch POSTs `application/citry-events+json` with the
 *    `X-Citry-Events` header and the configured CSRF source to the
 *    per-event route or the batch endpoint, and detects Content-Disposition
 *    file answers), enforces the bounded timeout (a late response drops with
 *    reason `timeout`), surfaces version skew (reason `version`, with the
 *    soft reload prompt), settles every caller through the applier, and
 *    fires `:before` (cancellable), `:after`, and `:error`.
 *
 * 8. Queues every user-facing send through the dependency DAG (design 5.6):
 *    containment edges to overlapping unsettled events (computed at enqueue,
 *    re-verified at dequeue against the live DOM), settled-means-applied
 *    release on every settle path, dequeue-time early cancel of dead
 *    dispatchers (reason `cancelled`), eligible-together batching into one
 *    envelope honoring the `@event` knobs from the class descriptor
 *    (`bundle=False` sends alone; `latest_wins=True` supersedes queued and
 *    in-flight predecessors with reason `superseded`), the `wait: false`
 *    bypass that joins no graph, busy (`data-citry-busy` plus `$loading`)
 *    from the gesture, and the recurring-binding tick-skip rule.
 *
 * 9. Brings the compiled bindings alive (design 5.1, 5.5, 5.6): one delegated
 *    listener per DOM event type at the document root reads the `data-cev-on`
 *    specs at event time (the modifier table, key filters, debounce and
 *    throttle timing), argument expressions evaluate through Alpine against
 *    the owning element, `@c-poll` intervals ride the element-keyed timer
 *    structure of point 6's machinery (hidden-tab pause; the queue's
 *    tick-skip rule via the recurring key), and every `$component` payload
 *    carries `props` (the config form's declared props resolve and validate
 *    here, through `_resolveProps`).
 *
 * 10. Brings the compiled state bindings alive (design 5.1, 5.5, 5.6): the
 *    `data-cev-bind` specs drive two-way flushes on the control's update
 *    event (the fixed update-event table, `.lazy` and `.on:` and the key
 *    filter, debounce with a trailing throttle capture), each flush one call
 *    carrying the `$state` write plus the named handler; a draft still ahead
 *    of its flush is recorded for the patch-time guard and piggybacks onto
 *    any earlier call the instance sends (design 4.2's `stateUpdates` rule); every
 *    bound control holds one Alpine effect applying `$state.<field>` to it
 *    (re-application after a self-render is reactivity alone; after a parent
 *    or targeted render the binding scan rebinds without stacking); and a
 *    form's submit-triggered events collect the form's named controls into
 *    the args payload, mirroring the urlencoded no-JS codec.
 *
 * PINNED-VERSION PRIVATE APIs. The core Alpine broker centralizes component
 * scope projection and held-root release using Alpine internals on top of the
 * public root selector:
 *
 *     Alpine.addScopeToNode(root, componentScope); // undocumented API
 *     root._x_dataStack = localLayers.concat([componentScope]);
 *     root._x_ignore = true;                       // private hold marker
 *     Alpine.initTree(root);                       // private subtree init
 *     Alpine.onAttributeRemoved(...);              // exact directive cleanup
 *
 * The Events provider requests this through `Citry.alpine._isolateScope`.
 * This is the isolation mechanism audited in
 * docs/design/alpinejs/alpine-vuetify-audit.md (`component.ts:165-170` of the
 * audited snapshot). The general lifecycle keeps user same-root layers and
 * cuts inherited component layers before Alpine initializes ordinary
 * directives. `@alpinejs/morph`'s Alpine bridge additionally calls the
 * private `Alpine.cloneNode` during patches. These APIs are version-coupled: the
 * Alpine and morph pins are exact, and this package's canary test
 * (`test/canary.test.mjs`) fails loudly if a version bump changes any of
 * them. Do not loosen the pins without re-running the canary and the e2e
 * suite. The Alpine surface itself is typed in `src/alpine.d.ts`, a local
 * declaration scoped to the bundle and broker boundary.
 */

// The named `morph` export is the plugin installer, not the raw morph
// function (WP6 spike F1); import the default, register it as a plugin, and
// the raw function becomes `Alpine.morph`, which the actions applier calls
// per render action.
// biome-ignore lint/correctness/noUnusedImports: Biome binds the file's `Alpine` references to the `declare global` var below instead of this import; tsc resolves the shadowing correctly and the import is what the bundle evaluates.
import Alpine from "alpinejs/src/index";
import morphPlugin from "@alpinejs/morph";

// ----- the runtime's types (erased at build time; esbuild emits none of this) -----

/**
 * The value bag of one instance's State: string-keyed in the manifest, and
 * the `$state` proxy passes symbol reads/writes through untouched, so the
 * index allows both.
 */
type StateValues = Record<string | symbol, unknown>;

/**
 * Per-event wire options carried by the class descriptor (design 4.4). The
 * two queue knobs ride only when non-default: `latestCallWins` appears as
 * `true`, and `allowBatching` appears as `false`.
 */
interface EventOptions {
  httpMethod: string;
  usesState?: true;
  debounceMilliseconds?: number;
  throttleMilliseconds?: number;
  latestCallWins?: true;
  allowBatching?: false;
}

/**
 * The decoded per-class descriptor from the events manifest: which handlers
 * the class declares, plus an optional `writableStateFields` list narrowing
 * which State fields the client may write (design 7.2). Omission means every
 * public value is writable; an explicit empty list means none are.
 */
interface ClassDescriptor {
  componentClassId: string;
  eventHandlers: Record<string, EventOptions>;
  writableStateFields?: string[];
}

/**
 * Raw JSON parsed from one `data-citry-events` tag. Every field stays
 * optional and unknown until `stageEventsManifest` validates the complete
 * object. The canonical post-validation shape is documented in the Events
 * protocol spec's "TypeScript view of the JSON."
 */
interface EventsManifest {
  protocol?: unknown;
  clientGraphRevision?: unknown;
  componentClasses?: unknown;
  componentInstances?: unknown;
}

interface StagedEventsManifest {
  classes: [string, ClassDescriptor][];
  instances: {
    componentId: string;
    classId: string;
    token: string | null;
    values: StateValues;
  }[];
}

/**
 * The `$loading` bookkeeping: counts of calls that are queued or in flight,
 * overall and per handler. Counting starts at enqueue, not at the wire, so
 * busy spans the queue (design 5.6).
 */
interface LoadingBox {
  any: number;
  handlers: Record<string, number>;
}

/** The structured error contract `$error` consumers see (design 3.7). */
interface ErrorEnvelope {
  status: number;
  code: string;
  message: string;
  fieldErrors?: Record<string, unknown>;
}

/**
 * A rejection reason as received from a transport or a throw: could be
 * anything, so every member stays unknown until `toErrorEnvelope` checks it.
 */
type ErrorLike = { status?: unknown; code?: unknown; message?: unknown; fieldErrors?: unknown } | null | undefined;

/**
 * The stable, client-internal identity of one interactive DOM position
 * (design 5.5; point 3 of the header). The nullable fields are the retired
 * state: `retireAnchor` clears them when the instance leaves the DOM (a
 * plain-HTML render, a region another render replaced, or a host removal).
 */
interface Anchor {
  anchorId: string;
  componentId: string | null;
  classId: string | null;
  token: string;
  epoch: number;
  highestApplied: number;
  /**
   * Which result application set `highestApplied` (design 4.2). A later
   * action of the same response (a delayed self-render, a token refresh
   * followed by a render) compares equal on epoch and must still apply, so
   * the guard tolerates equality exactly when this token matches. The keyed
   * linking horizon cut stores null here, so a linked child's in-flight
   * responses (equal or lower epoch, different token) all drop.
   */
  epochOwner: object | null;
  /**
   * Whether this anchor's component id has ever had a live element. A
   * head-placed manifest is consumed while only the head is parsed, so the
   * anchor exists before its root does; the backstop retirement sweep must
   * not read that gap as a removal (only the dependency manager's
   * liveInstances-style "was live, now gone" is a removal).
   */
  seenInDom: boolean;
  pending: Record<string, unknown>;
  values: StateValues | null;
  /** The `$state` facade: a Proxy over `values` that gates writes. */
  stateProxy: StateValues | null;
  writable: Set<string> | null;
  loading: LoadingBox;
  errorBox: { current: ErrorEnvelope | null };
  /**
   * Interval timer ids registered to this anchor; cleared (and the intervals
   * cancelled) when the anchor retires, so a replaced `@c-poll` region never
   * leaves a dead interval firing (design 5.5 machinery item 5). The
   * bindings runtime registers its timers here.
   */
  timers: Set<number>;
  /**
   * Elements currently stamped `data-citry-busy` for this anchor's in-flight
   * calls (the event queue stamps them from the gesture and clears them when
   * the call settles). The applier re-stamps the ones that survive a patch,
   * because morph strips client-stamped attributes (design 5.5).
   */
  busyTriggers: Set<Element>;
  /** The A3 runtime-neutral stable anchor this optional Events sidecar is attached to. */
  clientAnchor?: unknown;
}

/**
 * The metadata of one incoming render, read from the fragment's events
 * manifest; the caller passes `null` for a render that carries no component
 * (plain HTML).
 */
interface RenderMeta {
  componentId: string;
  classId: string;
  token?: string;
  values?: StateValues;
}

/** What `linkRenderedInstance` reports back to its caller. */
interface RenderLink {
  branch: "plain-html" | "general-only" | "reconcile" | "adopt";
  oldComponentId: string | null;
}

/**
 * One action from a result envelope (design 4.3's table), as `applyActions`
 * receives it. Every field is optional in this untrusted-data type; the
 * boundary validator checks the complete array before the applier mutates
 * anything.
 */
interface ResultAction {
  action?: string;
  /** render / event: a CSS selector, or the `render:<render id>` form. */
  target?: string;
  swap?: string;
  html?: string;
  /** data */
  value?: unknown;
  /** state */
  targetRenderId?: string;
  stateToken?: string;
  /** event */
  eventName?: string;
  detail?: unknown;
  /** redirect / url */
  url?: string;
  mode?: string;
  /** The timing fields every action carries (design 4.3). */
  delay?: number;
  wait?: boolean;
}

var isSafeRenderId = function (value: string): boolean {
  return /^[a-z0-9_-]+$/.test(value);
};

/** Raw result input; validation proves the success or error shape before use. */
interface ResultEntry {
  ok?: boolean;
  sendSequence?: number;
  actions?: ResultAction[];
  error?: unknown;
}

/**
 * The caller-side context for applying one result: the anchor the response
 * was routed to by its correlation id (never by a component id, design 5.5),
 * the event name for lifecycle `detail`s, and the transport's hook for
 * resolving the caller's promise with a `data` action's value. The public
 * `applyActions` applies with an empty context: no caller, no epoch guard.
 */
interface ApplyContext {
  anchor?: Anchor | null;
  /**
   * The call's send-time instance id, from the transport's correlation
   * record. A self-addressed action names this id on the wire, and the
   * applier routes it through `anchor` (routing is by correlation, never by
   * a component id, design 5.5), so the action follows the anchor even when
   * a keyed link re-minted the id while the response was in flight.
   */
  instance?: string | null;
  event?: string | null;
  onData?: ((value: unknown) => void) | null;
}

/**
 * The per-application state one `applyResult` call threads through its
 * actions: the echoed epoch, an identity token for the epoch guard's
 * same-response tolerance, a once-per-result latch for the `epoch` drop
 * event, and the elements the patch-time guard kept (so the post-patch
 * re-apply never undoes the guard, design 5.5's preservation block).
 */
interface ApplyRun {
  anchor: Anchor | null;
  /** The call's send-time instance id (see `ApplyContext.instance`). */
  instance: string | null;
  event: string | null;
  onData: ((value: unknown) => void) | null;
  epoch: number | null;
  /** One object per result application; `Anchor.epochOwner` stores it. */
  token: object;
  staleEventFired: boolean;
}

/**
 * One outgoing call created by the built-in browser runtime. Browser sends
 * always have a rendered caller, so `callerRenderId` is required here even
 * though the general protocol also permits calls without one.
 */
interface TransportCall {
  componentClassId: string;
  handlerName: string;
  callerRenderId: string;
  args: Record<string, unknown>;
  stateToken?: string;
  stateUpdates?: Record<string, unknown>;
  sendSequence?: number;
}

/**
 * One send of the batch path (`_internal.sendCalls`): the target instance
 * (an instance id or an Element inside one, as `Citry.events.send` takes),
 * the event name, and the caller's args and opts.
 */
interface SendIntent {
  target: string | Element;
  name: string;
  args?: Record<string, unknown> | null;
  opts?: unknown;
}

/**
 * The internal call-level test stub set through `_internal.setTransport`:
 * takes one call plus the caller's opts and returns the caller's settled
 * value (or a promise of it). When one is set, it replaces the whole wire
 * layer below (no envelope, no correlation, no timeout), which is exactly
 * what the `$loading`/`$error` tests need; real transports register through
 * the public `registerTransport` instead.
 */
type TransportStub = (call: TransportCall, opts: unknown) => unknown;

/**
 * The built-in runtime's outgoing envelope. It always advertises explicit
 * capabilities, although the general protocol permits their omission.
 */
interface CallEnvelope {
  protocol: string;
  /** The client-minted correlation id, echoed back by the server. */
  requestId: string;
  capabilities: { swaps: string[]; actions: string[] };
  calls: TransportCall[];
}

/** Raw transport result; every field stays optional until `preflight` validates it. */
interface ResultEnvelope {
  protocol?: string;
  requestId?: string | null;
  results?: ResultEntry[];
}

/**
 * A registered transport (design 5.2/6.1): `send` takes the call envelope
 * and resolves with the matching result envelope; transports carry bytes and
 * never look inside either. `subscribe` is the server-push half (v2), stored
 * untouched until a consumer exists.
 */
interface TransportImpl {
  send(envelope: CallEnvelope): Promise<ResultEnvelope> | ResultEnvelope;
  subscribe?: unknown;
}

/**
 * Where the CSRF token comes from and which request header carries it
 * (design 5.2/7.4; the defaults are Django's). `token` (a string or a
 * zero-arg function) overrides the cookie read for non-cookie sources.
 */
interface CsrfConfig {
  cookie?: string;
  header?: string;
  token?: string | (() => string);
}

/**
 * Page-wide runtime defaults set through `Citry.events.configure(opts)`,
 * design 5.2's field table. Unknown fields are kept but mean nothing.
 */
interface EventsConfig {
  csrf?: CsrfConfig;
  /** Milliseconds before an in-flight call rejects with the timeout error (default 30000). */
  timeout?: number;
  /** Which registered transport `send` uses (default `"fetch"`). */
  transport?: string;
  /** Base URL of the events routes; normally read from the runtime script tag's own src. */
  url?: string;
  [key: string]: unknown;
}

/** A subscription callback: receives the CustomEvent's unwrapped detail. */
type EventCallback = (detail: unknown) => void;

/**
 * One decoded `data-cev-on` spec: a DOM-event binding an element carries.
 * The attribute names and payload keys are the WP12-published contract
 * documented in the Python bindings module (`citry/ext/events/bindings.py`).
 * Every field is optional because the attribute is wire-adjacent data; the
 * listener checks what it uses.
 */
interface EventBindingSpec {
  cid?: string;
  event?: string;
  handler?: string;
  args?: string | null;
  prevent?: boolean;
  stop?: boolean;
  self?: boolean;
  once?: boolean;
  key?: string | null;
  debounce?: number | null;
  throttle?: number | null;
}

/** One decoded `data-cev-poll` spec (same published contract): an interval binding. */
interface PollBindingSpec {
  cid?: string;
  handler?: string;
  args?: string | null;
  interval?: number;
}

/**
 * One decoded `data-cev-bind` spec (same published contract): a state binding
 * from `:c-<field>`. `mode` is `"one"` (apply the State field to the control)
 * or `"two"` (the value named a handler: on the control's update event, one
 * call carries the `$state` write plus that handler). The concrete update
 * event resolves from the live control (design 5.1's table); `lazy` asks for
 * the committed-value event and `on` overrides the event outright.
 */
interface StateBindingSpec {
  cid?: string;
  field?: string;
  mode?: string;
  handler?: string | null;
  lazy?: boolean;
  on?: string | null;
  key?: string | null;
  debounce?: number | null;
  throttle?: number | null;
}

/** Per-binding trigger timing: the pending debounce timer and the open throttle window. */
interface BindingTiming {
  debounceTimer: number;
  throttleUntil: number;
}

/**
 * One prop definition of the `$component` config form (design 5.5,
 * Vue-object-API style): `type` is a constructor or an array of constructors,
 * `required` defaults to false, and a function `default` is called per
 * instance. Every field stays unknown because the declaration is user JS;
 * the resolver checks each at runtime.
 */
interface PropDefinition {
  type?: unknown;
  required?: unknown;
  default?: unknown;
}

declare const contextValueType: unique symbol;
type InjectionKey<T> = symbol & { readonly [contextValueType]?: T };
type ContextKey<T = unknown> = string | InjectionKey<T>;

interface InjectContextValue {
  <T = unknown>(key: ContextKey<T>): T;
  <T = unknown, D = unknown>(key: ContextKey<T>, defaultValue: D): T | D;
}

/**
 * The payload citry.js hands every `$component` callback. Citry's core
 * lifecycle and ambient-context helpers plus the members this runtime
 * decorates are typed here; citry.js owns their implementations.
 */
interface ComponentPayload {
  id: string;
  els?: Element[];
  scope?: Record<string, unknown>;
  effect?: (callback: () => void) => () => void;
  reactive?: <T extends object>(value: T) => T;
  provide?: <T>(key: ContextKey<T>, value: T) => void;
  inject?: InjectContextValue;
  unprovide?: (key: ContextKey) => void;
  state?: StateValues | null;
  /** Declared client props resolved for this instance; an empty object under the bare callback form. */
  props?: Record<string, unknown>;
  sendEvent?: (name: string, args?: Record<string, unknown>, opts?: unknown) => Promise<unknown>;
  onEvent?: (name: string, fn: EventCallback) => () => void;
}

interface ComponentInvocationControl {
  registerCleanup(cleanup: () => void): () => void;
}

/**
 * One call queued by the bootstrap stub before this runtime replaced it. The
 * stub (defined in the Python emission module) pushes plain, untyped
 * argument arrays, so the drain below casts them per `kind`.
 */
interface StubQueueEntry {
  kind: "send" | "on" | "onEvent" | "configure" | "registerTransport" | "applyActions";
  args: unknown[];
  resolve?: (value: unknown) => void;
  reject?: (reason: unknown) => void;
  dead?: boolean;
  off?: (() => void) | null;
}

/**
 * The bootstrap stub, as far as this runtime touches it. Its `_stubQueue`
 * doubles as the discriminant between the stub and the real runtime api
 * (which declares the member `undefined`).
 */
interface BootstrapStub {
  _stubQueue: StubQueueEntry[];
  _decoratorHooked: boolean;
  _decorate(ctx: ComponentPayload, control?: ComponentInvocationControl | null): void;
}

/** The internal contract for the transport and actions layer (and for tests). */
interface EventsInternal {
  alpineStarted: boolean;
  anchors: Map<string, Anchor>;
  idToAnchor: Map<string, Anchor>;
  classes: Map<string, ClassDescriptor>;
  config: EventsConfig;
  getAnchor(componentId: string): Anchor | null;
  linkRenderedInstance(anchor: Anchor, meta: RenderMeta | null): RenderLink;
  finishRender(anchor: Anchor, oldComponentId: string | null): void;
  setTransport(fn: TransportStub | null): void;
  /**
   * The batch send path (design 4.2: several calls ride one envelope). Each
   * intent is a full send; the returned array pairs one caller promise per
   * intent. This is the direct wire path, with no queue in front; the event
   * queue's dequeue shares the same envelope machinery beneath it.
   */
  sendCalls(intents: SendIntent[]): Promise<unknown>[];
  /**
   * The bindings-runtime send entry (design 5.6): resolves the innermost
   * instance from `el` at fire time and rides the event queue with `el` as
   * the dispatching element. A fire-time miss, a class that does not declare
   * the event, and a skipped recurring tick (the private `recurringKey`, the
   * tick-skip rule) all return null instead of a promise.
   */
  sendFromElement(
    el: Element,
    name: string,
    args?: Record<string, unknown> | null,
    opts?: unknown,
    recurringKey?: string | null,
  ): Promise<unknown> | null;
  /** Dispatch a relocated component-boundary binding through its immutable source owner. */
  sendBoundary(
    componentId: string,
    name: string,
    args: Record<string, unknown> | null,
    opts: unknown,
    element: Element | null,
    carrierLive?: (() => boolean) | null,
    event?: Event | null,
  ): Promise<unknown> | null;
  /** Source-owned Citry magics used while a boundary expression runs on a child carrier. */
  boundaryScope(componentId: string, element: Element | null, carrierLive?: (() => boolean) | null): object;
  /** The event queue's introspection (tests and debugging): the unsettled nodes, oldest first, each with the seqs it waits on. */
  queue: {
    snapshot(): { seq: number; event: string; anchor: string; dispatched: boolean; waitsOn: number[] }[];
  };
  /** Aggregate live-resource counts for A10 conformance and deployment diagnostics. */
  debug(): {
    anchors: number;
    renderIds: number;
    classes: number;
    delegatedListenerTypes: number;
    polledElements: number;
    anchorIntervals: number;
    elementIntervals: number;
    boundControls: number;
    formEffects: number;
    pendingFlushes: number;
    queuedCalls: number;
  };
  /** Strictly validate and stage one manifest without mutating runtime registries. */
  stageEventsManifest(manifest: EventsManifest): StagedEventsManifest;
  processEventsManifests(): void;
  /** Apply one result envelope entry with its caller context (the transport's path into the applier). */
  applyResult(result: ResultEntry, ctx?: ApplyContext | null): Promise<void>;
  /** Apply a whole results array in envelope order; `ctxs[i]` pairs `results[i]`. */
  applyEnvelope(results: ResultEntry[], ctxs?: (ApplyContext | null)[] | null): Promise<void>;
  /** Retire one anchor now (unlink, drop from the registry, cancel its timers, null its fields). */
  retireAnchor(anchor: Anchor): void;
  /** Retire every anchor whose component id has no live element (the sweep, run synchronously). */
  sweepRetiredAnchors(): void;
  /**
   * The unsent-draft record behind the patch-time guard's `hasUnsentDraft`:
   * the forms runtime marks a two-way-bound control here while its flush
   * timer is pending (the DOM value diverging from `$state`), and clears it
   * when the flush writes the draft into `$state` (design 5.3's hook).
   */
  drafts: { mark(el: Element): void; clear(el: Element): void; has(el: Element): boolean };
  /**
   * The forms runtime's introspection (tests and debugging): how many live
   * application effects and pending flush timers one control holds. The
   * no-stacking rule (design 5.5: a control that lived through three parent
   * renders holds one binding and one timer, not three) is asserted on these.
   */
  forms: { snapshot(el: Element): { effects: number; flushes: number } };
  /**
   * The recurring-timer structure of design 5.5 machinery item 5. Anchor
   * intervals retire with the anchor; element intervals are one-per-key, so
   * a morph survivor's timer dedupes against the fresh instance's own
   * manifest-initialized interval instead of double-polling. The bindings
   * runtime registers `@c-poll` timers through these.
   */
  timers: {
    registerAnchorInterval(anchor: Anchor, intervalId: number): void;
    registerElementInterval(el: Element, key: string, intervalId: number): void;
  };
}

/**
 * The public client API installed at `Citry.events` (design 5.2's table),
 * plus the deliberately underscore-private members the transport and actions
 * layer builds on.
 */
interface CitryEventsApi {
  send(target: string | Element, name: string, args?: Record<string, unknown>, opts?: unknown): Promise<unknown>;
  on(name: string, fn: EventCallback): () => void;
  configure(opts?: EventsConfig): void;
  registerTransport(name: string, impl: TransportImpl): void;
  applyActions(actions: ResultAction[]): Promise<void>;
  _decorate(ctx: ComponentPayload, control?: ComponentInvocationControl | null): void;
  _onFor(componentId: string, name: string, fn: EventCallback): () => void;
  /**
   * The events-runtime half of the `$component` config form (design 5.5):
   * resolves and validates one instance's declared props, returning the
   * reactive resolved bag or throwing the pointed validation error. The
   * dependency manager (citry.js) calls it late-bound per instance, like
   * `_decorate`.
   */
  _resolveProps(classId: string, declarations: Record<string, PropDefinition>): Record<string, unknown>;
  _internal: EventsInternal;
  /**
   * Never present on the real runtime; declared so a plain property check
   * discriminates the stub-or-runtime union.
   */
  _stubQueue?: undefined;
  _decoratorHooked?: undefined;
}

/** The `globalThis.Citry` namespace this runtime shares with citry.js. */
interface CitryGlobal {
  /** The bootstrap stub until this runtime replaces it with the real api. */
  events?: CitryEventsApi | BootstrapStub;
  /** citry.js's dependency manager; only the payload-decorator hook is used here. */
  manager?: {
    decorateContext?: (decorator: (ctx: ComponentPayload, control?: ComponentInvocationControl | null) => void) => void;
    ownership?: {
      has(revision: string): boolean;
      whenReady(revision: string): Promise<unknown>;
      _preflightEvents(revision: string, entries: { componentId: string; classId: string }[]): unknown[];
      _attachEvents(revision: string, renderId: string, classId: string, eventsAnchor: Anchor): unknown;
      _detachEvents(generalAnchor: unknown, eventsAnchor: Anchor): void;
      _transitionEvents(generalAnchor: unknown, renderId: string, classId: string): void;
      _retireEvents(generalAnchor: unknown): void;
      _isLive(generalAnchor: unknown): boolean;
      _beginEvents(revision: string): void;
      _finishEvents(revision: string, error: unknown | null): void;
      _ownerForElement(el: Element): string | null | undefined;
      _prepareAdoption(manifest: unknown, root: DocumentFragment): unknown;
      _adoptionRoot(transaction: unknown): { componentId: string; classId: string } | null;
      _activateAdoption(transaction: unknown): void;
      _commitAdoption(transaction: unknown): unknown;
      _abortAdoption(transaction: unknown, error?: unknown): void;
      _rejectAdoption(revision: string, error: unknown): void;
      _mintPlacement(): string;
      _placementIds(generalAnchor: unknown): (string | null)[];
      _placementRoots(generalAnchor: unknown): Element[][];
      _hasPlacements(generalAnchor: unknown): boolean;
      _relatedEvents(generalAnchor: unknown): Anchor[];
      _classForRender(renderId: string): string | null;
      _correspond(fromRenderId: string, toRenderId: string): unknown;
      _morphPlacement(
        generalAnchor: unknown,
        index: number,
        html: string,
        options?: Record<string, unknown>,
      ): { end: Comment };
      _expectRetirement(renderIds: string[]): void;
      _claimTag(el: Element): void;
      _preflightDependency(manifest: unknown, revision: string): unknown;
      _applyDependency(transaction: unknown, manifest: unknown, tag: Element): Promise<void>;
    };
  };
  alpine?: {
    _install(
      alpine: import("alpinejs").AlpineGlobal,
      morph: (alpine: import("alpinejs").AlpineGlobal) => void,
    ): boolean;
    _register(options: {
      root?: () => string;
      beforeBoundary?: (el: MaybeElement) => void;
      init?: (el: MaybeElement) => void;
      mutations?: (mutations: MutationRecord[]) => void;
      beforeStart?: () => void;
      afterStart?: () => void;
    }): () => void;
    _magic(name: string, provider: (el: Element) => unknown): () => void;
    _runDirective<T>(
      el: Element,
      attributeName: string,
      registerCleanup: (cleanup: () => void) => void,
      callback: () => T,
    ): T;
    _morph(from: Element, to: Element, options?: Parameters<import("alpinejs").AlpineGlobal["morph"]>[2]): Element;
    _isolateScope(root: Element, scope: object): void;
    _drain(): void;
    _ready(): void;
    _start(): void;
    _isStarted(): boolean;
  };
}

type OwnershipBridge = NonNullable<NonNullable<CitryGlobal["manager"]>["ownership"]>;

/**
 * An element as the defensive paths type it: DOM callbacks (event targets,
 * mutation records, Alpine's init walk) can surface objects that are not
 * Elements, so every member the runtime probes is optional here and checked
 * before use. Where a passed probe proves the object is a real element, the
 * code narrows with an `as Element` cast right after the runtime check.
 */
interface MaybeElement {
  nodeType?: number;
  closest?(selector: string): Element | null;
  hasAttribute?(name: string): boolean;
  getAttribute?(name: string): string | null;
  matches?(selector: string): boolean;
  querySelectorAll?<E extends Element = Element>(selector: string): NodeListOf<E>;
}

declare global {
  /**
   * PINNED-VERSION PRIVATE API (see the header): Alpine's per-element scope
   * stack. `addScopeToNode` creates it (added scope first) and the isolation
   * truncation in `attachBoundaryScope` cuts it. Optional because only
   * elements Alpine has given a scope carry the field.
   */
  interface Element {
    _x_dataStack?: object[];
    _x_ignore?: boolean;
    _x_ignoreSelf?: boolean;
    _x_marker?: number;
  }

  /** The embedded Alpine, installed for morph's bridge and page scripts. */
  // biome-ignore lint/suspicious/noRedeclare: this global declaration types `globalThis.Alpine`; the module-scope import above shadows it locally on purpose.
  var Alpine: import("alpinejs").AlpineGlobal | undefined;
  /** The shared `Citry` namespace; citry.js and this runtime both attach to it. */
  var Citry: CitryGlobal | undefined;
}

(function () {
  // biome-ignore lint/suspicious/noRedundantUseStrict: redundant in this ES module, but load-bearing in the emitted bundle, where the iife is a classic script and the directive is what makes the runtime strict.
  "use strict";

  // biome-ignore lint/suspicious/noAssignInExpressions: the single-expression install is deliberate: create-or-reuse the namespace and capture it in one step.
  var C = (globalThis.Citry = globalThis.Citry || {});
  if (!C.alpine) throw new Error("[Citry] Alpine: the core hook broker is not loaded.");
  var alpineRuntime = C.alpine;
  // Run this before the Events duplicate guard so a second bundled runtime is
  // diagnosed and cannot silently construct another observing Alpine copy.
  if (!alpineRuntime._install(Alpine, morphPlugin)) return;
  // Already installed (e.g. a document page and a fragment both loaded the
  // runtime). The bootstrap stub is not "installed": it marks itself with
  // `_stubQueue` and is replaced below, its queue drained.
  if (C.events && !C.events._stubQueue) return;
  var bootstrapStub = C.events || null;

  // ----- state -----

  var pointedError = function (message: string) {
    return new Error("[Citry] " + message);
  };

  // classId -> the decoded class descriptor from the manifest
  // ({eventHandlers: {name: {httpMethod, debounceMilliseconds?,
  // throttleMilliseconds?}}}).
  var classes = new Map<string, ClassDescriptor>();
  // anchorId -> anchor. An anchor is the stable client identity of one
  // interactive DOM position; see the header and design 5.5.
  var anchors = new Map<string, Anchor>();
  // componentId -> anchor: THE tie between the faithful, per-render component
  // id and its stable anchor. Re-linked on every render.
  var idToAnchor = new Map<string, Anchor>();
  var anchorCounter = 0;
  // Roots whose boundary scope entry is already attached. This is an
  // idempotency guard on live nodes (several manifests can name one root),
  // not the anchor tie: a node that morph swaps out simply leaves the set,
  // and its replacement gets a fresh boundary from the fresh manifest.
  var boundaryAttached = new WeakSet<Element>();
  // A moved manifest node is idempotent, but cloneNode/outerHTML must create
  // a fresh transaction that reaches duplicate-revision validation. DOM
  // attributes cannot provide that distinction because clones copy them.
  var processedEventsManifestTags = new WeakSet<HTMLScriptElement>();
  // Runtime configuration set through `Citry.events.configure(opts)`; the
  // wire section below consumes the fields (design 5.2's table).
  var config: EventsConfig = {};
  // The internal call-level test stub (`_internal.setTransport`). When one
  // is set it replaces the whole wire layer (envelope, correlation, timeout),
  // and its resolved value settles the caller directly; tests drive
  // `$loading`/`$error` with it. Real sends go through the named-transport
  // registry in the wire section below.
  var transportImpl: TransportStub | null = null;

  var fromBase64 = function (value: string) {
    return decodeURIComponent(
      Array.prototype.map
        .call(atob(value), function (ch: string) {
          return "%" + ("00" + ch.charCodeAt(0).toString(16)).slice(-2);
        })
        .join(""),
    ); // atob alone mangles non-ASCII; this decodes the bytes as UTF-8
  };

  // ----- anchors and the reactive State -----

  var declaredEvents = function (classId: string | null) {
    // A retired anchor's null class id simply misses the map.
    var descriptor = classes.get(classId as string);
    return descriptor && descriptor.eventHandlers ? Object.keys(descriptor.eventHandlers) : [];
  };

  var eventHttpMethod = function (classId: string | null, name: string) {
    var descriptor = classes.get(classId as string);
    var options = descriptor && descriptor.eventHandlers ? descriptor.eventHandlers[name] : null;
    return options && typeof options.httpMethod === "string" ? options.httpMethod : "POST";
  };

  var eventDeclaresState = function (classId: string | null, name: string) {
    var descriptor = classes.get(classId as string);
    var options = descriptor && descriptor.eventHandlers ? descriptor.eventHandlers[name] : null;
    return Boolean(options && options.usesState === true);
  };

  var requireDeclaredEvent = function (anchor: Anchor, name: string, caller: string) {
    if (anchor.classId == null) {
      // A retired anchor: its instance was reset, replaced, or removed (the
      // retirement sweep, design 5.5 machinery item 3). A captured send must
      // fail loudly, never silently, and the plain no-such-event error would
      // name "component null" here, which hides what actually happened.
      throw pointedError(
        "this component instance was removed or replaced, so '" +
          name +
          "' cannot be sent (" +
          caller +
          ")." +
          " Keep an instance across parent re-renders with #c-key (design 5.5).",
      );
    }
    var declared = declaredEvents(anchor.classId);
    if (declared.indexOf(name) === -1) {
      throw pointedError(
        "component " +
          anchor.classId +
          " has no event '" +
          name +
          "' (" +
          caller +
          ");" +
          " declared events: " +
          (declared.join(", ") || "(none)") +
          ".",
      );
    }
  };

  // Which State fields the client may write (design 7.2, the `_model` gate).
  // Omission is the default where `_model` equals `_public`; an explicit
  // array narrows the public values, including `[]` for read-only State.
  var writableFields = function (classId: string, values: StateValues) {
    var descriptor = classes.get(classId);
    if (descriptor && Array.isArray(descriptor.writableStateFields)) {
      return new Set(descriptor.writableStateFields);
    }
    return new Set(Object.keys(values));
  };

  var dropInvalidPendingFields = function (anchor: Anchor, phase: string) {
    if (!anchor.writable) return;
    const droppedPending = Object.keys(anchor.pending).filter(function (field) {
      return !anchor.writable!.has(field);
    });
    droppedPending.forEach(function (field) {
      delete anchor.pending[field];
    });
    if (droppedPending.length) {
      console.warn(
        "[Citry] events: component " +
          anchor.classId +
          " no longer permits pending $state fields " +
          phase +
          "; dropped: " +
          droppedPending.sort().join(", ") +
          ".",
      );
    }
  };

  // A manifest may refresh a descriptor while anchors of that class already
  // exist (fragment insertion or a rolling deployment). The state proxy
  // closes over the Set object, so update it in place rather than replacing
  // the property and leaving the proxy with stale permissions.
  var refreshWritableFields = function (anchor: Anchor, dropInvalidPending?: boolean) {
    if (!anchor.values || !anchor.classId) return;
    var next = writableFields(anchor.classId, anchor.values);
    if (!anchor.writable) {
      anchor.writable = next;
      return;
    }
    anchor.writable.clear();
    next.forEach(function (field) {
      anchor.writable!.add(field);
    });
    if (dropInvalidPending) {
      dropInvalidPendingFields(anchor, "after a descriptor update");
    }
  };

  var refreshAnchorsForClasses = function (classIds: Set<string>, dropInvalidPending?: boolean) {
    anchors.forEach(function (anchor) {
      if (anchor.classId && classIds.has(anchor.classId)) {
        refreshWritableFields(anchor, dropInvalidPending);
      }
    });
  };

  // Install decoded class descriptors as one class-global operation. Both
  // ordinary manifest ingestion and render pre-staging use this path so the
  // gate is current before Alpine evaluates incoming morph expressions.
  var installClassDescriptors = function (entries: [string, ClassDescriptor][], dropInvalidPending?: boolean) {
    var classIds = new Set<string>();
    entries.forEach(function (entry) {
      classes.set(entry[0], entry[1]);
      classIds.add(entry[0]);
    });
    refreshAnchorsForClasses(classIds, dropInvalidPending);
  };

  // The `$state` facade over the anchor's reactive values: reads stay
  // reactive (they pass straight through to the Alpine.reactive object), and
  // writes are gated. A write to a writable field lands in the reactive
  // object (so effects re-run) AND queues as a pending update that rides the
  // next call from the instance (design 5.5's write rules).
  var makeStateProxy = function (anchor: Anchor) {
    // Both were just set by adoptStateContract (the only caller), so they
    // are live here even though the Anchor type allows the retired nulls.
    var values = anchor.values as StateValues;
    var writable = anchor.writable as Set<string>;
    return new Proxy(values, {
      get: function (target, key) {
        return target[key];
      },
      set: function (target, key, value) {
        if (typeof key !== "string") {
          target[key] = value;
          return true;
        }
        if (!writable.has(key)) {
          throw pointedError(
            "$state field '" +
              key +
              "' of component " +
              anchor.classId +
              " is not client-writable;" +
              " writable fields: " +
              (Array.from(writable).sort().join(", ") || "(none)") +
              "." +
              " Keep client-only UI state in your own x-data (design 7.2: _public/_model).",
          );
        }
        target[key] = value;
        anchor.pending[key] = value;
        return true;
      },
      deleteProperty: function (target, key) {
        throw pointedError(
          "State fields cannot be deleted through $state (tried to delete '" +
            String(key) +
            "');" +
            " State is the declared server contract.",
        );
      },
    });
  };

  // Give the anchor a fresh State contract for `classId`: the reactive values
  // object, the `$state` facade over it, the writable set, and the per-handler
  // loading counters. Used when the anchor is created and when a render swaps
  // it to a different component class.
  var adoptStateContract = function (anchor: Anchor, classId: string, values: StateValues) {
    anchor.classId = classId;
    anchor.values = Alpine.reactive(Object.assign({}, values));
    anchor.writable = writableFields(classId, values);
    anchor.stateProxy = makeStateProxy(anchor);
    // Seed a counter per declared handler so `$loading('name')` reads are
    // reactive from the first render on.
    var handlers: Record<string, number> = {};
    declaredEvents(classId).forEach(function (name) {
      handlers[name] = 0;
    });
    anchor.loading.handlers = handlers;
  };

  var createAnchor = function (componentId: string, classId: string, token: string, values: StateValues) {
    anchorCounter += 1;
    var anchor: Anchor = {
      anchorId: "a" + anchorCounter,
      componentId: componentId,
      classId: classId,
      token: token || "",
      // The out-of-order guard's bookkeeping (design 4.2): the counter and the
      // highest applied epoch live on the anchor, never on the component id,
      // because the id changes on every render. The transport work package
      // does the send-side increment and the receive-side compare.
      epoch: 0,
      highestApplied: 0,
      epochOwner: null,
      seenInDom: false,
      // field -> value queued by a `$state` write and not yet sent. These
      // fields win over incoming server values in the reconcile rule.
      pending: {},
      values: null,
      stateProxy: null,
      writable: null,
      loading: Alpine.reactive<LoadingBox>({ any: 0, handlers: {} }),
      errorBox: Alpine.reactive<Anchor["errorBox"]>({ current: null }),
      timers: new Set<number>(),
      busyTriggers: new Set<Element>(),
    };
    adoptStateContract(anchor, classId, values);
    anchors.set(anchor.anchorId, anchor);
    idToAnchor.set(componentId, anchor);
    return anchor;
  };

  // The reconcile rule (design 5.5): server wins per field, except fields
  // with a pending, not-yet-sent local write, which keep the local value
  // (they are still queued and reach the server on the next call). Runs only
  // on a live anchor, so its values are never the retired null.
  var reconcileValues = function (anchor: Anchor, serverValues: StateValues) {
    Object.keys(serverValues).forEach(function (key) {
      if (Object.prototype.hasOwnProperty.call(anchor.pending, key)) return;
      anchor.values![key] = serverValues[key];
    });
  };

  // Retire one anchor: the DOM position it served is gone (a plain-HTML
  // render, a region another render replaced, or a host removal). The anchor
  // leaves both maps, its interval timers stop with it (design 5.5 machinery
  // item 5), and its fields null to the retired state the magics read as
  // inert. When retirement discards pending unsent writes or a nonzero
  // loading count, a warning names the class and the dropped field keys:
  // that is the exact moment a reset discards user input, and without the
  // warning the silent revert is undiagnosable in the field (machinery item
  // 3). Instance JS cleanups are not run here; the dependency manager's
  // removal reconciler owns those when the id's elements leave the DOM.
  var retireAnchor = function (anchor: Anchor, preserveGeneral?: boolean) {
    var pendingKeys = Object.keys(anchor.pending);
    var dropped: string[] = [];
    if (pendingKeys.length || anchor.loading.any > 0) {
      if (pendingKeys.length) dropped.push("pending unsent writes (" + pendingKeys.sort().join(", ") + ")");
      if (anchor.loading.any > 0) dropped.push("a nonzero loading count (" + anchor.loading.any + " in flight)");
      console.warn(
        "[Citry] events: an instance of " +
          anchor.classId +
          " was reset or removed while holding " +
          dropped.join(" and ") +
          "; that client state is discarded. Keep it across parent re-renders with #c-key (design 5.5).",
      );
    }
    anchor.timers.forEach(function (intervalId) {
      clearInterval(intervalId);
    });
    anchor.timers.clear();
    anchor.busyTriggers.clear();
    if (anchor.clientAnchor) {
      if (!preserveGeneral) globalThis.Citry?.manager?.ownership?._retireEvents(anchor.clientAnchor);
      globalThis.Citry?.manager?.ownership?._detachEvents(anchor.clientAnchor, anchor);
      anchor.clientAnchor = null;
    }
    if (anchor.componentId != null) idToAnchor.delete(anchor.componentId);
    anchors.delete(anchor.anchorId);
    anchor.componentId = null;
    anchor.classId = null;
    anchor.token = "";
    anchor.pending = {};
    anchor.values = null;
    anchor.stateProxy = null;
    anchor.writable = new Set<string>();
  };

  // The anchor-side handling of one incoming render: the three-way state
  // split (design 5.5), chosen by comparing the anchor's current class id
  // against the incoming render's class. MUST run before the morph call
  // (spike F-CI-2): morph's Alpine bridge re-evaluates the incoming
  // fragment's bound expressions during the patch, and they resolve `$state`
  // through the fresh component id, so the id has to be in the index and the
  // State current by then. The old id's index entry stays live through the
  // patch for the same reason; `finishRender` retires it afterwards.
  //
  // `meta` is `null` for a render that carries no component (plain HTML), or
  // `{componentId, classId, token, values}` read from the incoming fragment's
  // events manifest.
  var linkRenderedInstance = function (anchor: Anchor, meta: RenderMeta | null): RenderLink {
    var oldComponentId = anchor.componentId;
    if (meta == null) {
      // Plain HTML: the anchor goes non-interactive. Its state and scope are
      // discarded and no new instance is bound; the instance's cleanup runs
      // through the dependency manager's removal reconciler when the old
      // marker leaves the DOM.
      retireAnchor(anchor);
      return { branch: "plain-html", oldComponentId: oldComponentId };
    }
    if (anchor.clientAnchor) {
      globalThis.Citry?.manager?.ownership?._transitionEvents(anchor.clientAnchor, meta.componentId, meta.classId);
    }
    var branch: RenderLink["branch"];
    if (meta.classId === anchor.classId) {
      // Same class: reconcile in place. The reactive object and the `$state`
      // facade keep their identity, so subscribers carry across the render.
      branch = "reconcile";
      reconcileValues(anchor, meta.values || {});
    } else {
      // Different class: the fields do not correspond, so the old state is
      // discarded and the server's fresh token and values adopted wholesale.
      // A later send then carries the new class's token, and the server-side
      // State rebuild succeeds instead of failing on a stale token.
      branch = "adopt";
      anchor.pending = {};
      anchor.errorBox.current = null;
      adoptStateContract(anchor, meta.classId, meta.values || {});
    }
    anchor.token = meta.token || "";
    anchor.componentId = meta.componentId;
    idToAnchor.set(meta.componentId, anchor);
    return { branch: branch, oldComponentId: oldComponentId };
  };

  // The post-morph half of a render: retire the old component id's index
  // entry once the patch no longer needs it.
  var finishRender = function (anchor: Anchor, oldComponentId: string | null) {
    if (oldComponentId == null || oldComponentId === anchor.componentId) return;
    if (idToAnchor.get(oldComponentId) === anchor) idToAnchor.delete(oldComponentId);
  };

  // ----- scope attach -----

  var attachBoundaryScope = function (root: Element) {
    boundaryAttached.add(root);
    var ids = (root.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
    var graphOwned = ids.some(function (id) {
      return Boolean(idToAnchor.get(id)?.clientAnchor);
    });
    // Graph-backed instances use the general component lifecycle. Its core
    // init interceptor must run after the pre-boundary supplier phase, so
    // Events does not install a competing empty scope here. Keep the empty
    // fallback only for legacy graph-independent Events manifests.
    if (!graphOwned) alpineRuntime._isolateScope(root, {});
  };

  var attachBoundaryScopes = function (componentId: string) {
    var roots = document.querySelectorAll("[data-cid-" + componentId + "]");
    var anchor = roots.length ? idToAnchor.get(componentId) : null;
    // The id has a live element: from here on the backstop sweep may read a
    // missing element as a removal.
    if (anchor) anchor.seenInDom = true;
    roots.forEach(function (root) {
      if (boundaryAttached.has(root)) return;
      attachBoundaryScope(root);
    });
  };

  // ----- manifest processing -----

  var isPlainObject = function (value: unknown): value is Record<string, unknown> {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  };

  var isJsonValue = function (value: unknown, ancestors?: Set<object>): boolean {
    if (value === null || typeof value === "string" || typeof value === "boolean") return true;
    if (typeof value === "number") return Number.isFinite(value);
    if (typeof value !== "object") return false;
    var seen = ancestors || new Set<object>();
    if (seen.has(value)) return false;
    seen.add(value);
    var valid: boolean;
    if (Array.isArray(value)) {
      const keys = Object.keys(value);
      valid =
        Object.getOwnPropertySymbols(value).length === 0 &&
        keys.length === value.length &&
        keys.every(function (key, index) {
          return key === String(index);
        }) &&
        value.every(function (item) {
          return isJsonValue(item, seen);
        });
    } else {
      valid =
        (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null) &&
        Object.getOwnPropertySymbols(value).length === 0 &&
        Object.getOwnPropertyNames(value).every(function (key) {
          return (
            Object.prototype.propertyIsEnumerable.call(value, key) &&
            isJsonValue((value as Record<string, unknown>)[key], seen)
          );
        });
    }
    seen.delete(value);
    return valid;
  };

  var hasExactKeys = function (value: Record<string, unknown>, required: string[], optional?: string[]): boolean {
    var allowed = new Set(required.concat(optional || []));
    return (
      required.every(function (key) {
        return Object.prototype.hasOwnProperty.call(value, key);
      }) &&
      Object.keys(value).every(function (key) {
        return allowed.has(key);
      })
    );
  };

  var stageEventsManifest = function (manifest: EventsManifest): StagedEventsManifest {
    if (!isPlainObject(manifest)) throw new TypeError("events manifest must be an object");
    if (!hasExactKeys(manifest, ["protocol", "clientGraphRevision", "componentClasses", "componentInstances"])) {
      throw new TypeError("events manifest must contain exactly the citry-events/1 fields");
    }
    if (manifest.protocol !== "citry-events/1") throw new TypeError("events manifest protocol must be citry-events/1");
    if (
      manifest.clientGraphRevision !== null &&
      (typeof manifest.clientGraphRevision !== "string" || !/^[0-9a-f]{64}$/.test(manifest.clientGraphRevision))
    ) {
      throw new TypeError("events manifest clientGraphRevision must be a lowercase 64-character digest or null");
    }
    if (!Array.isArray(manifest.componentClasses)) {
      throw new TypeError("events manifest componentClasses must be an array");
    }
    if (!Array.isArray(manifest.componentInstances)) {
      throw new TypeError("events manifest componentInstances must be an array");
    }

    var stagedClasses: [string, ClassDescriptor][] = [];
    var classIds = new Set<string>();
    manifest.componentClasses.forEach(function (candidate) {
      if (
        !isPlainObject(candidate) ||
        !hasExactKeys(candidate, ["componentClassId", "eventHandlers"], ["writableStateFields"])
      ) {
        throw new TypeError("events component class must contain exactly its protocol fields");
      }
      if (typeof candidate.componentClassId !== "string" || !candidate.componentClassId) {
        throw new TypeError("events componentClassId must be non-empty text");
      }
      if (classIds.has(candidate.componentClassId)) throw new TypeError("events manifest repeats a componentClassId");
      if (!isPlainObject(candidate.eventHandlers)) {
        throw new TypeError("events component class eventHandlers must be an object");
      }
      Object.keys(candidate.eventHandlers).forEach(function (eventName) {
        if (!eventName) throw new TypeError("events handler names must be non-empty text");
        const options = (candidate.eventHandlers as Record<string, unknown>)[eventName];
        if (!isPlainObject(options)) {
          throw new TypeError("events handler options must be an object");
        }
        if (
          !hasExactKeys(
            options,
            ["httpMethod"],
            ["usesState", "debounceMilliseconds", "throttleMilliseconds", "latestCallWins", "allowBatching"],
          )
        ) {
          throw new TypeError("events handler options contain missing or unknown fields");
        }
        if (typeof options.httpMethod !== "string" || !/^[!#$%&'*+.^_`|~0-9A-Z-]+$/.test(options.httpMethod)) {
          throw new TypeError("events handler httpMethod must be uppercase HTTP-token text");
        }
        (["debounceMilliseconds", "throttleMilliseconds"] as const).forEach(function (field) {
          if (
            Object.prototype.hasOwnProperty.call(options, field) &&
            (!Number.isInteger(options[field]) || (options[field] as number) < 0)
          ) {
            throw new TypeError("events handler " + field + " must be a non-negative integer");
          }
        });
        if (options.usesState !== undefined && options.usesState !== true) {
          throw new TypeError("events handler usesState may only be true");
        }
        if (options.latestCallWins !== undefined && options.latestCallWins !== true) {
          throw new TypeError("events handler latestCallWins may only be true");
        }
        if (options.allowBatching !== undefined && options.allowBatching !== false) {
          throw new TypeError("events handler allowBatching may only be false");
        }
      });
      if (
        candidate.writableStateFields !== undefined &&
        (!Array.isArray(candidate.writableStateFields) ||
          candidate.writableStateFields.some(function (field) {
            return typeof field !== "string" || !field;
          }) ||
          new Set(candidate.writableStateFields).size !== candidate.writableStateFields.length)
      ) {
        throw new TypeError("events writableStateFields must contain unique, non-empty strings");
      }
      var descriptor = candidate as unknown as ClassDescriptor;
      classIds.add(descriptor.componentClassId);
      stagedClasses.push([descriptor.componentClassId, descriptor]);
    });

    var componentIds = new Set<string>();
    var stagedInstances = manifest.componentInstances.map(function (candidate) {
      if (
        !isPlainObject(candidate) ||
        !hasExactKeys(candidate, ["renderId", "componentClassId", "stateToken", "publicState"])
      ) {
        throw new TypeError("events component instance must contain exactly its protocol fields");
      }
      var componentId = candidate.renderId;
      if (typeof componentId !== "string" || !componentId)
        throw new TypeError("events renderId must be non-empty text");
      if (!isSafeRenderId(componentId)) {
        throw new TypeError("events renderId must be safe for an HTML attribute name");
      }
      if (componentIds.has(componentId)) throw new TypeError("events manifest repeats a renderId");
      componentIds.add(componentId);
      if (typeof candidate.componentClassId !== "string" || !candidate.componentClassId) {
        throw new TypeError("events instance componentClassId must be non-empty text");
      }
      if (!classIds.has(candidate.componentClassId)) {
        throw new TypeError("events instance refers to an unknown componentClassId");
      }
      if (candidate.stateToken !== null && (typeof candidate.stateToken !== "string" || !candidate.stateToken)) {
        throw new TypeError("events stateToken must be non-empty text or null");
      }
      if (!isPlainObject(candidate.publicState) || !isJsonValue(candidate.publicState)) {
        throw new TypeError("events publicState must be a strict JSON object");
      }
      if (candidate.stateToken === null && Object.keys(candidate.publicState).length) {
        throw new TypeError("a stateless events instance cannot carry publicState");
      }
      return {
        componentId: componentId,
        classId: candidate.componentClassId,
        token: candidate.stateToken,
        values: candidate.publicState,
      };
    });
    return { classes: stagedClasses, instances: stagedInstances };
  };

  var applyEventsManifest = function (manifest: EventsManifest) {
    // Decode and validate every class and instance before mutating either
    // registry. A bad later entry therefore cannot expose an earlier anchor.
    var staged = stageEventsManifest(manifest);
    var graphRevision = manifest.clientGraphRevision as string | null;
    var ownership = graphRevision ? globalThis.Citry?.manager?.ownership : null;
    if (graphRevision) {
      if (!ownership) throw new Error("the ownership graph registry is unavailable");
      ownership._preflightEvents(graphRevision, staged.instances);
    }
    // A fragment usually names only its own instances, but descriptors are
    // class-global, so installation refreshes every live sibling too.
    installClassDescriptors(staged.classes, true);

    staged.instances.forEach(function (meta) {
      var existing = idToAnchor.get(meta.componentId);
      var eventsAnchor: Anchor;
      if (existing) {
        // The id is already linked: a correlated render reconciled this
        // instance before the morph, and the fragment's own manifest tag
        // lands afterwards. Values were handled there (clobbering them here
        // would replay the server values over newer local writes), so only
        // the token is refreshed.
        if (meta.token) existing.token = meta.token;
        eventsAnchor = existing;
      } else {
        // A component id appearing with no anchor: the initial page load, a
        // server push, or a host-inserted fragment. Mint a fresh anchor.
        eventsAnchor = createAnchor(meta.componentId, meta.classId, meta.token || "", meta.values);
      }
      if (graphRevision && ownership) {
        eventsAnchor.clientAnchor = ownership._attachEvents(
          graphRevision,
          meta.componentId,
          meta.classId,
          eventsAnchor,
        );
      }
      attachBoundaryScopes(meta.componentId);
    });
  };

  var EVENTS_MANIFEST_SELECTOR = 'script[type="application/json"][data-citry-events]';
  var consumedOwnershipRevisions = new Set<string>();

  var applyEventsManifestTransaction = function (manifest: EventsManifest) {
    var graphRevision = manifest.clientGraphRevision as string | null;
    var ownership = graphRevision ? globalThis.Citry?.manager?.ownership : null;
    try {
      applyEventsManifest(manifest);
      if (graphRevision) {
        consumedOwnershipRevisions.add(graphRevision);
        ownership!._finishEvents(graphRevision, null);
      }
    } catch (err) {
      if (graphRevision && ownership) ownership._finishEvents(graphRevision, err);
      throw err;
    }
  };

  var processEventsManifestTag = function (el: HTMLScriptElement) {
    if (processedEventsManifestTags.has(el)) return;
    processedEventsManifestTags.add(el);
    el.dataset.citryEventsProcessed = "";
    try {
      // A script tag's textContent is never null; the cast just says so.
      const manifest = JSON.parse(el.textContent as string) as EventsManifest;
      // A valid-looking graph revision is enough to reserve the ownership
      // gate. Deep validation happens after reservation so a malformed later
      // class or instance cannot let graph-linked callbacks run first.
      const candidateRevision = isPlainObject(manifest) ? manifest.clientGraphRevision : null;
      const preceding = el.previousElementSibling;
      let pairedRevision: string | null = null;
      if (preceding?.matches('script[type="application/json"][data-citry-graph]')) {
        const graphManifest = JSON.parse(preceding.textContent as string) as unknown;
        if (
          isPlainObject(graphManifest) &&
          typeof graphManifest.revision === "string" &&
          /^[0-9a-f]{64}$/.test(graphManifest.revision)
        ) {
          pairedRevision = graphManifest.revision;
        }
      }
      const reservationRevision =
        pairedRevision ||
        (typeof candidateRevision === "string" && /^[0-9a-f]{64}$/.test(candidateRevision) ? candidateRevision : null);
      let ownership: OwnershipBridge | null = null;
      let reservedRevision: string | null = null;
      let handedOff = false;
      if (reservationRevision) {
        ownership = globalThis.Citry?.manager?.ownership || null;
        if (!ownership) throw new Error("the ownership graph registry is unavailable");
        if (consumedOwnershipRevisions.has(reservationRevision)) {
          throw new Error(`ownership graph ${reservationRevision} already supplied an Events manifest`);
        }
        ownership._beginEvents(reservationRevision);
        reservedRevision = reservationRevision;
      }
      try {
        // applyEventsManifest validates again immediately before registry
        // mutation so direct internal callers keep the same strict boundary.
        stageEventsManifest(manifest);
        const graphRevision = manifest.clientGraphRevision as string | null;
        if (reservedRevision && graphRevision !== reservedRevision) {
          throw new TypeError("a graph-backed Events manifest must link to its paired ownership revision");
        }
        if (graphRevision) {
          if (!ownership || reservedRevision !== graphRevision) {
            throw new Error("the ownership graph registry is unavailable");
          }
          if (!ownership.has(graphRevision)) {
            ownership.whenReady(graphRevision).then(
              function () {
                try {
                  applyEventsManifestTransaction(manifest);
                } catch (err) {
                  console.error("[Citry] failed to process events manifest:", err);
                }
              },
              function (err) {
                ownership!._finishEvents(graphRevision, err);
                console.error("[Citry] failed to wait for an events manifest ownership graph:", err);
              },
            );
            handedOff = true;
            return;
          }
        }
        handedOff = true;
        applyEventsManifestTransaction(manifest);
      } catch (err) {
        if (reservedRevision && ownership && !handedOff) ownership._finishEvents(reservedRevision, err);
        throw err;
      }
    } catch (err) {
      console.error("[Citry] failed to process events manifest:", err);
    }
  };

  var processExistingEventsManifests = function () {
    document.querySelectorAll<HTMLScriptElement>(EVENTS_MANIFEST_SELECTOR).forEach(processEventsManifestTag);
  };

  // ----- magic resolution -----

  // The innermost component id above `el`: the fixed-name `data-cid` marker
  // carries the instance ids space-separated, innermost last (one element can
  // root both a wrapper component and its only child; magics resolve to the
  // child, design 5.5). Returns null when no marker exists at all, and ""
  // when a marker exists but holds no id.
  var innermostPhysicalComponentId = function (el: MaybeElement | null) {
    var root = el && el.closest ? el.closest("[data-cid]") : null;
    if (!root) return null;
    var ids = (root.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
    return ids.length ? ids[ids.length - 1] : "";
  };

  var projectedComponentId = function (el: MaybeElement | null): string | null | undefined {
    var ownership = C.manager && C.manager.ownership;
    if (el && el.nodeType === 1 && ownership && typeof ownership._ownerForElement === "function") {
      return ownership._ownerForElement(el as Element);
    }
    return undefined;
  };

  var innermostComponentId = function (el: MaybeElement | null) {
    var owner = projectedComponentId(el);
    if (owner !== undefined) return owner;
    return innermostPhysicalComponentId(el);
  };

  // The anchor a magic used on `el` resolves to. No citry marker anywhere
  // above is the hard error: the magic is meaningless there and silence would
  // hide a template mistake. A marker whose id is not (or no longer) in the
  // index yields null, and each magic then degrades to an inert value: during
  // a morph there is a moment when a marker-bearing node's id is not
  // registered yet, and both morph's Alpine bridge and Alpine's re-init can
  // evaluate bound expressions in that gap (design 5.3; the spike's
  // robustness point).
  var resolveAnchor = function (el: MaybeElement, magicName: string) {
    var id = innermostComponentId(el);
    if (id === null) {
      throw pointedError(
        "$" +
          magicName +
          " was used outside any interactive component instance" +
          " (no element with a data-cid marker encloses this one)." +
          " The magics only work inside a component that declares events.",
      );
    }
    return (id && idToAnchor.get(id)) || null;
  };

  // The inert `$state` stand-in for the mid-morph gap: every read is
  // undefined, writes are swallowed, and string coercion yields "" so a bound
  // x-text never crashes. Never a throw (design 5.3).
  var INERT_STATE = new Proxy(
    {},
    {
      get: function (target, key) {
        if (key === Symbol.toPrimitive || key === "toString" || key === "valueOf") {
          return function () {
            return "";
          };
        }
        return undefined;
      },
      set: function () {
        return true;
      },
      has: function () {
        return false;
      },
    },
  );

  // ----- sending -----

  var toErrorEnvelope = function (err: ErrorLike): ErrorEnvelope {
    // The structured error contract (design 3.7): {status, code, message,
    // fieldErrors?}. A transport that already rejects with that shape passes
    // through; anything else is wrapped so `$error` consumers always see the
    // envelope shape, with `fieldErrors` omitted unless the source supplied it.
    var structured: ErrorEnvelope;
    if (err && typeof err === "object" && (typeof err.status === "number" || typeof err.code === "string")) {
      structured = {
        status: typeof err.status === "number" ? err.status : 0,
        code: typeof err.code === "string" ? err.code : "transport_error",
        message: typeof err.message === "string" ? err.message : String(err),
      };
      if (err.fieldErrors && typeof err.fieldErrors === "object") {
        structured.fieldErrors = err.fieldErrors as Record<string, unknown>;
      }
      return structured;
    }
    return {
      status: 0,
      code: "transport_error",
      message: err && err.message ? String(err.message) : String(err),
    };
  };

  var beginLoading = function (anchor: Anchor, name: string) {
    anchor.loading.any += 1;
    var handlers = anchor.loading.handlers;
    handlers[name] = (handlers[name] || 0) + 1;
  };

  var endLoading = function (anchor: Anchor, name: string) {
    if (anchor.loading.any > 0) anchor.loading.any -= 1;
    var handlers = anchor.loading.handlers;
    if (typeof handlers[name] === "number" && handlers[name] > 0) handlers[name] -= 1;
  };

  // ----- the wire: envelope, transports, timeout, and version skew (design 4.2, 5.2, 5.6, 6.1, 6.2) -----

  // The protocol identity and what this runtime can apply (the protocol
  // package's spec, section 5): the client advertises the full v1 vocabulary,
  // which is `morph` on top of the protocol baseline (the baseline is every
  // v1 swap except morph, plus all six action kinds). The server never emits
  // outside the advertised set; it downgrades instead, which is what keeps a
  // stale cached runtime safe across a deploy (design 4.2).
  var PROTOCOL = "citry-events/1";
  var CLIENT_SWAPS = ["morph", "replace", "inner", "append", "prepend", "remove", "none"];
  var CLIENT_ACTIONS = ["render", "data", "state", "event", "redirect", "url"];
  // The protocol schema caps one envelope at sixteen calls (design 4.2); a
  // larger batch must split into successive envelopes before the wire (the
  // event queue's job).
  var MAX_CALLS_PER_ENVELOPE = 16;
  // The bounded default (design 5.6): a hung request must never hold its
  // queue dependents forever, so an unbounded setting is deliberately not
  // offered; raise the number per call or page-wide for known-slow handlers.
  var DEFAULT_TIMEOUT_MS = 30000;
  // Django's cookie and header names (design 7.4); `configure({csrf})`
  // renames either side or supplies a non-cookie token source.
  var CSRF_COOKIE_DEFAULT = "csrftoken";
  var CSRF_HEADER_DEFAULT = "X-CSRFToken";

  // The events routes' base URL, read once at evaluation time from the
  // runtime script tag's own src (`.../ext/events/runtime.js`, the URL the
  // serializer emitted): the one breadcrumb every served page carries.
  // `configure({url})` overrides it for the rare deployment where the
  // emitted URL is wrong from the browser's viewpoint (a path-rewriting
  // reverse proxy in front of the app).
  var detectEventsBase = function (): string | null {
    var current = document.currentScript;
    var tag: HTMLScriptElement | null;
    var src =
      current && typeof (current as HTMLScriptElement).src === "string" ? (current as HTMLScriptElement).src : "";
    if (!/\/runtime\.js([?#]|$)/.test(src)) {
      // Not evaluating from the served runtime tag (an inlined bundle, a
      // hand-written page): find the tag by its fixed, design-pinned path.
      tag = document.querySelector('script[src$="ext/events/runtime.js"]');
      src = tag ? tag.src : "";
    }
    var match = /^(.*\/)runtime\.js([?#].*)?$/.exec(src);
    return match ? match[1] : null;
  };
  var detectedEventsBase = detectEventsBase();

  var eventsBaseUrl = function (): string {
    var configured = config.url;
    if (typeof configured === "string" && configured) {
      return configured.charAt(configured.length - 1) === "/" ? configured : configured + "/";
    }
    if (detectedEventsBase) return detectedEventsBase;
    throw pointedError(
      "the events routes' base URL is unknown (no events runtime script tag with a src to read it from);" +
        ' set it explicitly with Citry.events.configure({url: "/<prefix>/ext/events/"}).',
    );
  };

  // Correlation ids are minted per envelope and echoed back (design 4.2).
  // The counter keeps ids unique within the page; the random tail keeps two
  // page loads from reusing a sequence in a server-side log.
  var envelopeCounter = 0;
  var mintCorrelationId = function () {
    envelopeCounter += 1;
    return "r_" + envelopeCounter.toString(36) + Math.random().toString(36).slice(2, 6);
  };

  var readCookie = function (name: string): string | null {
    var entries = document.cookie ? document.cookie.split("; ") : [];
    var found: string | null = null;
    entries.forEach(function (entry) {
      if (entry.indexOf(name + "=") === 0) found = decodeURIComponent(entry.slice(name.length + 1));
    });
    return found;
  };

  // The CSRF header to attach, resolved from `configure({csrf})` at send
  // time (design 7.4): a `token` source (a string or a zero-arg function)
  // wins over the cookie read; no token found means no header (hosts without
  // a token scheme run on the X-Citry-Events floor alone).
  var resolveCsrfHeader = function (): { header: string; token: string } | null {
    var csrf: CsrfConfig = config.csrf && typeof config.csrf === "object" ? config.csrf : {};
    var header = typeof csrf.header === "string" && csrf.header ? csrf.header : CSRF_HEADER_DEFAULT;
    var token: string | null = null;
    if (typeof csrf.token === "function") token = String(csrf.token());
    else if (typeof csrf.token === "string") token = csrf.token;
    else token = readCookie(typeof csrf.cookie === "string" && csrf.cookie ? csrf.cookie : CSRF_COOKIE_DEFAULT);
    return token ? { header: header, token: token } : null;
  };

  // A client-minted rejection: the same {status, code, message} shape as
  // server errors so one rejection handler covers both; status 0 is the
  // browser's own convention for a call that got no server verdict, and
  // `fieldErrors` stays absent (design 5.2).
  var clientError = function (code: string, message: string) {
    return { status: 0, code: code, message: message };
  };

  var encodeGetCallQuery = function (envelope: CallEnvelope, call: TransportCall) {
    var query = new URLSearchParams();
    var appendValue = function (name: string, value: unknown) {
      if (typeof value === "string" || typeof value === "boolean") {
        query.append(name, String(value));
        return;
      }
      if (typeof value === "number" && Number.isFinite(value)) {
        query.append(name, String(value));
        return;
      }
      throw clientError(
        "transport_error",
        "GET event '" +
          call.handlerName +
          "' can carry only string, boolean, finite-number, or non-empty arrays of those query values; field '" +
          name +
          "' is not representable.",
      );
    };
    Object.keys(call.args || {}).forEach(function (name) {
      var value = call.args[name];
      if (value === undefined) return;
      if (Array.isArray(value)) {
        if (!value.length) {
          throw clientError(
            "transport_error",
            "GET event '" + call.handlerName + "' cannot represent an empty array in query field '" + name + "'.",
          );
        }
        value.forEach(function (item) {
          appendValue(name, item);
        });
        return;
      }
      appendValue(name, value);
    });
    if (call.callerRenderId) query.set("_citry_caller_render_id", call.callerRenderId);
    if (call.stateToken) query.set("_citry_state_token", call.stateToken);
    if (typeof call.sendSequence === "number") query.set("_citry_send_sequence", String(call.sendSequence));
    query.set("_citry_protocol", envelope.protocol);
    query.set("_citry_request_id", envelope.requestId);
    if (envelope.capabilities) query.set("_citry_capabilities", JSON.stringify(envelope.capabilities));
    return query.toString();
  };

  // The timeout for one call: the per-call opts override, then the
  // `configure({timeout})` page default, then 30000 ms. Only a finite
  // positive number counts; anything else falls through, because an
  // unbounded timeout is deliberately not offered (design 5.6).
  var resolveTimeoutMs = function (opts: unknown): number {
    var optsTimeout = opts && typeof opts === "object" ? (opts as { timeout?: unknown }).timeout : undefined;
    var chosen = DEFAULT_TIMEOUT_MS;
    [optsTimeout, config.timeout].some(function (value) {
      if (typeof value === "number" && Number.isFinite(value) && value > 0) {
        chosen = value;
        return true;
      }
      return false;
    });
    return chosen;
  };

  // ----- version skew (design 4.5): the two signals and the soft prompt -----

  // Ask at most once per page: a deploy-time skew tends to hit every call at
  // once, and re-asking after a decline would nag.
  var versionSkewPrompted = false;

  // Surface one version-skew signal (design 4.5, 5.2): the drop event with
  // reason `version` through the shared dispatch helper (no call promise
  // rides it), then the default handling, a soft reload prompt: ask, never
  // force. The event is cancellable, which is how a page replaces the
  // default: `e.preventDefault()` in a `citry:events:stale` listener
  // suppresses the prompt.
  var surfaceVersionSkew = function (anchor: Anchor | null, eventName: string | null) {
    var unprevented = fireLifecycle("citry:events:stale", anchor, eventName, { reason: "version" }, true);
    if (!unprevented || versionSkewPrompted) return;
    versionSkewPrompted = true;
    if (
      window.confirm("This page and the server are running different versions of the app. Reload to get back in sync?")
    ) {
      window.location.reload();
    }
  };

  // ----- the send records and the envelope round trip -----

  /** One in-flight call's bookkeeping between the wire and its caller. */
  interface SendRecord {
    anchor: Anchor;
    event: string;
    call: TransportCall;
    timeoutMs: number;
    promise: Promise<unknown>;
    resolve: (value: unknown) => void;
    reject: (reason: unknown) => void;
    /** Set when the timer fired: the caller was already told it failed, so a late response drops. */
    timedOut: boolean;
    timerId: number;
    /**
     * Set when a newer `@event(latest_wins=True)` call abandoned this one
     * (design 3.5): the caller was already rejected with the `superseded`
     * reason, so the response's application drops on arrival.
     */
    superseded: boolean;
    /**
     * The queue's applied-means-settled hook (design 5.6): fired exactly once
     * when the call's client lifecycle fully ends, meaning its result's
     * actions finished applying, or it failed (timeout, transport error, an
     * error result). Fire through `fireRecordSettled`, never directly.
     */
    onSettled: (() => void) | null;
  }

  interface DownloadPayload {
    blob: Blob;
    filename: string;
  }

  // A file response becomes a synthetic ok result so it can pass through the
  // ordinary timeout and supersession checks. The blob stays private and is
  // saved only when that exact result reaches live settlement.
  var stagedDownloads = new WeakMap<ResultEntry, DownloadPayload>();

  var makeSendRecord = function (anchor: Anchor, eventName: string, call: TransportCall, timeoutMs: number) {
    var resolveFn: (value: unknown) => void = function () {};
    var rejectFn: (reason: unknown) => void = function () {};
    var promise = new Promise<unknown>(function (resolve, reject) {
      resolveFn = resolve;
      rejectFn = reject;
    });
    var record: SendRecord = {
      anchor: anchor,
      event: eventName,
      call: call,
      timeoutMs: timeoutMs,
      promise: promise,
      resolve: resolveFn,
      reject: rejectFn,
      timedOut: false,
      timerId: 0,
      superseded: false,
      onSettled: null,
    };
    return record;
  };

  var isObj = isPlainObject;
  var ERROR_STATUSES: Record<string, number | null> = {
    invalid_args: 422,
    invalid_state: 403,
    stale_state: 409,
    unknown_event: 404,
    unknown_component: 404,
    forbidden: 403,
    not_found: 404,
    conflict: 409,
    error: null,
    csrf_failed: 403,
    payload_too_large: 413,
    protocol_mismatch: 400,
    handler_error: 500,
  };
  var isWireError = function (e: unknown): e is ErrorEnvelope {
    if (!isObj(e) || !hasExactKeys(e, ["status", "code", "message"], ["fieldErrors"])) return false;
    if (!Number.isInteger(e.status) || (e.status as number) < 400 || (e.status as number) > 599) return false;
    if (typeof e.code !== "string" || !Object.prototype.hasOwnProperty.call(ERROR_STATUSES, e.code)) return false;
    if (ERROR_STATUSES[e.code] !== null && ERROR_STATUSES[e.code] !== e.status) return false;
    if (typeof e.message !== "string" || !e.message) return false;
    return (
      e.fieldErrors === undefined ||
      (isObj(e.fieldErrors) && Object.values(e.fieldErrors).every((value) => typeof value === "string"))
    );
  };

  var badReply = (reason: string) => clientError("transport_error", "invalid event response (" + reason + ").");

  var isActionTarget = function (value: unknown): value is string {
    if (typeof value !== "string" || !value) return false;
    if (value.indexOf("render:") !== 0) return true;
    return isSafeRenderId(value.slice(7));
  };

  var validateWireAction = function (candidate: unknown): candidate is ResultAction {
    if (!isObj(candidate) || typeof candidate.action !== "string") return false;
    if (
      (candidate.delay !== undefined &&
        (typeof candidate.delay !== "number" || !Number.isFinite(candidate.delay) || candidate.delay < 0)) ||
      (candidate.wait !== undefined && candidate.wait !== false)
    ) {
      return false;
    }
    var timing = ["delay", "wait"];
    if (candidate.action === "render") {
      return (
        hasExactKeys(candidate, ["action", "target", "swap", "html"], timing) &&
        isActionTarget(candidate.target) &&
        typeof candidate.swap === "string" &&
        CLIENT_SWAPS.indexOf(candidate.swap) !== -1 &&
        typeof candidate.html === "string"
      );
    }
    if (candidate.action === "data") {
      return hasExactKeys(candidate, ["action", "value"], timing) && isJsonValue(candidate.value);
    }
    if (candidate.action === "state") {
      return (
        hasExactKeys(candidate, ["action", "targetRenderId", "stateToken"], timing) &&
        typeof candidate.targetRenderId === "string" &&
        isSafeRenderId(candidate.targetRenderId) &&
        typeof candidate.stateToken === "string" &&
        !!candidate.stateToken
      );
    }
    if (candidate.action === "event") {
      return (
        hasExactKeys(candidate, ["action", "eventName"], ["detail", "target"].concat(timing)) &&
        typeof candidate.eventName === "string" &&
        !!candidate.eventName &&
        candidate.eventName.indexOf("citry:") !== 0 &&
        (candidate.detail === undefined || isJsonValue(candidate.detail)) &&
        (candidate.target === undefined || isActionTarget(candidate.target))
      );
    }
    if (candidate.action === "redirect") {
      return hasExactKeys(candidate, ["action", "url"], timing) && typeof candidate.url === "string" && !!candidate.url;
    }
    if (candidate.action === "url") {
      return (
        hasExactKeys(candidate, ["action", "url", "mode"], timing) &&
        typeof candidate.url === "string" &&
        !!candidate.url &&
        (candidate.mode === "push" || candidate.mode === "replace")
      );
    }
    return false;
  };

  var validateOkResult = function (candidate: Record<string, unknown>, expectedSequence?: number): boolean {
    if (!hasExactKeys(candidate, ["ok", "actions"], ["sendSequence"]) || candidate.ok !== true) return false;
    if (!Array.isArray(candidate.actions) || !candidate.actions.every(validateWireAction)) return false;
    if (
      candidate.actions.filter(function (action) {
        return (action as ResultAction).action === "data";
      }).length > 1
    )
      return false;
    return candidate.sendSequence === expectedSequence;
  };

  var validateErrorResult = function (
    candidate: Record<string, unknown>,
    expectedSequence?: number,
    checkSequence = true,
  ): boolean {
    if (!hasExactKeys(candidate, ["ok", "error"], ["sendSequence"]) || candidate.ok !== false) return false;
    if (!isWireError(candidate.error)) return false;
    if (
      candidate.sendSequence !== undefined &&
      (!Number.isInteger(candidate.sendSequence) || (candidate.sendSequence as number) < 0)
    ) {
      return false;
    }
    return !checkSequence || candidate.sendSequence === expectedSequence;
  };

  var preflight = function (reply: ResultEnvelope, sent: CallEnvelope): ResultEntry[] {
    if (
      !isObj(reply) ||
      !hasExactKeys(reply, ["protocol", "requestId", "results"]) ||
      reply.protocol !== PROTOCOL ||
      !Array.isArray(reply.results) ||
      !reply.results.length
    ) {
      throw badReply("header");
    }
    var results = reply.results;

    if (reply.requestId === null) {
      const edge = results[0];
      if (
        results.length !== 1 ||
        !isObj(edge) ||
        edge.sendSequence !== undefined ||
        !validateErrorResult(edge, undefined, false) ||
        !isObj(edge.error) ||
        edge.error.fieldErrors !== undefined ||
        (edge.error.code !== "protocol_mismatch" && edge.error.code !== "payload_too_large")
      ) {
        throw badReply("edge");
      }
      return sent.calls.map(() => edge);
    }

    if (reply.requestId !== sent.requestId || results.length !== sent.calls.length) throw badReply("correlation");

    results.forEach((item, slot) => {
      if (!isObj(item)) throw badReply("result " + slot);
      var expectedSequence = sent.calls[slot].sendSequence;
      if (!validateOkResult(item, expectedSequence) && !validateErrorResult(item, expectedSequence)) {
        throw badReply("result " + slot);
      }
    });
    return results;
  };

  // Fire a record's settle hook exactly once (the queue's dependent-release
  // wiring, design 5.6: every settle path releases dependents). Every path
  // that ends a call's client lifecycle funnels through here: the timeout,
  // a transport failure, and the completed application of an arrived result.
  var fireRecordSettled = function (record: SendRecord) {
    var hook = record.onSettled;
    record.onSettled = null;
    if (hook) hook();
  };

  // Settle one record from its slot of the result envelope: a timed-out
  // record's late response drops whole, an error result rejects the caller
  // (its own settlement; design 5.2's reason table), and an ok result runs
  // through the applier with the caller context (correlation routing, design
  // 5.5), resolving the caller at the `data` action or with undefined once
  // the actions finish.
  var settleRecordFromResult = function (record: SendRecord, result: ResultEntry | undefined, slot: number) {
    var error: unknown;
    var dataFired = false;
    var ctx: ApplyContext;
    var download: DownloadPayload | undefined;
    if (record.timedOut) {
      // The caller was already told it failed (the timeout rejection), so
      // the whole late application drops (design 5.6; the R3 drop table).
      fireStale(record.anchor, record.event, "timeout");
      console.debug(
        "[Citry] events: dropped the response of '" + record.event + "': it arrived after the call timed out.",
      );
      if (result) stagedDownloads.delete(result);
      return Promise.resolve();
    }
    if (record.superseded) {
      // A newer @event(latest_wins=True) call abandoned this one while it
      // was in flight (design 3.5): the caller was already rejected with the
      // superseded reason, so the response's application drops whole.
      fireStale(record.anchor, record.event, "superseded");
      console.debug(
        "[Citry] events: dropped the response of '" + record.event + "': a newer call superseded it (latest_wins).",
      );
      if (result) stagedDownloads.delete(result);
      return Promise.resolve();
    }
    if (result == null || typeof result !== "object") {
      record.reject(
        clientError(
          "transport_error",
          "the result envelope carried no result for '" + record.event + "' (results[" + slot + "] is missing).",
        ),
      );
      return Promise.resolve();
    }
    if (result.ok !== true) {
      error =
        result.error && typeof result.error === "object" ? result.error : toErrorEnvelope(result.error as ErrorLike);
      // A stale token after a deploy is the wire's version-skew signal
      // (design 4.5): surface it; the call itself still settles through its
      // own error result below, so no promise rides the skew event.
      if ((error as { code?: unknown }).code === "stale_state") surfaceVersionSkew(record.anchor, record.event);
      record.reject(error);
      return Promise.resolve();
    }
    download = stagedDownloads.get(result);
    if (download) {
      stagedDownloads.delete(result);
      try {
        saveDownload(download);
        record.resolve(undefined);
      } catch (err) {
        console.error("[Citry] events: saving the download from '" + record.event + "' failed:", err);
        record.reject(toErrorEnvelope(err as ErrorLike));
      }
      return Promise.resolve();
    }
    ctx = {
      anchor: record.anchor,
      instance: record.call.callerRenderId,
      event: record.event,
      onData: function (value) {
        // The caller resolves at the `data` action's slot in the faithful
        // order (design 5.2: "resolves with the data action's value").
        dataFired = true;
        record.resolve(value);
      },
    };
    return applyResult(result, ctx).then(
      function () {
        if (!dataFired) record.resolve(undefined);
      },
      function (err) {
        console.error("[Citry] events: applying the result of '" + record.event + "' failed:", err);
        if (!dataFired) record.reject(toErrorEnvelope(err as ErrorLike));
      },
    );
  };

  // Put one prepared batch on the wire as a single envelope (design 4.2).
  // Per-call timers enforce the bounded timeout; the resolved envelope
  // settles records in slot order through an awaited chain, so an earlier
  // result's render is already visible to a later result's liveness checks
  // (machinery item 4, the batch half).
  var sendRecordsOverWire = function (records: SendRecord[]) {
    var impl: TransportImpl;
    var dispatched: Promise<ResultEnvelope>;
    var envelope: CallEnvelope = {
      protocol: PROTOCOL,
      requestId: mintCorrelationId(),
      capabilities: { swaps: CLIENT_SWAPS.slice(), actions: CLIENT_ACTIONS.slice() },
      calls: records.map(function (record) {
        return record.call;
      }),
    };
    try {
      impl = activeTransport();
    } catch (err) {
      records.forEach(function (record) {
        record.reject(err);
        fireRecordSettled(record);
      });
      return;
    }
    try {
      dispatched = Promise.resolve(impl.send(envelope));
    } catch (err) {
      dispatched = Promise.reject(err);
    }
    var rejectRecords = function (err: unknown) {
      var error = toErrorEnvelope(err as ErrorLike);
      records.forEach(function (record) {
        window.clearTimeout(record.timerId);
        if (!record.timedOut && !record.superseded) record.reject(error);
        fireRecordSettled(record);
      });
    };
    records.forEach(function (record) {
      record.timerId = window.setTimeout(function () {
        // The server is not cancelled; the client stops waiting (design
        // 5.6). The rejection settles the caller, the settle hook releases
        // the call's queue dependents right now (a hung request must never
        // hold them, design 5.6), and the response, if it still arrives,
        // drops above.
        record.timedOut = true;
        record.reject(
          clientError(
            "timeout",
            "'" +
              record.event +
              "' timed out after " +
              record.timeoutMs +
              " ms; raise it per call (sendEvent opts) or page-wide (Citry.events.configure({timeout})).",
          ),
        );
        fireRecordSettled(record);
      }, record.timeoutMs);
    });
    dispatched.then(
      function (resultEnvelope) {
        var results: ResultEntry[];
        var chain: Promise<void> = Promise.resolve();
        // The response arrived: from here on application time does not count
        // against the timeout, so every timer stops before the chain runs.
        try {
          results = preflight(resultEnvelope, envelope);
        } catch (err) {
          rejectRecords(err);
          return;
        }
        records.forEach(function (record) {
          window.clearTimeout(record.timerId);
        });
        records.forEach(function (record, slot) {
          chain = chain.then(function () {
            return settleRecordFromResult(record, results[slot], slot).then(function () {
              // Applied means settled (design 5.6): the record's queue
              // dependents release only after its actions finished, never at
              // mere arrival. (A record that already settled early, at the
              // timeout or an abandonment, fired its hook then; this no-ops.)
              fireRecordSettled(record);
            });
          });
        });
      },
      function (err) {
        rejectRecords(err);
      },
    );
  };

  // ----- the built-in fetch transport (design 6.2, 7.4) -----

  var splitDisposition = function (disposition: string): string[] {
    var parts: string[] = [];
    var current = "";
    var quoted = false;
    var escaped = false;
    for (let index = 0; index < disposition.length; index += 1) {
      const char = disposition[index];
      if (escaped) {
        current += char;
        escaped = false;
      } else if (quoted && char === "\\") {
        current += char;
        escaped = true;
      } else if (char === '"') {
        current += char;
        quoted = !quoted;
      } else if (char === ";" && !quoted) {
        parts.push(current.trim());
        current = "";
      } else {
        current += char;
      }
    }
    parts.push(current.trim());
    return parts;
  };

  var unquoteDispositionValue = function (raw: string): string {
    var value = raw.trim();
    if (value.length < 2 || value[0] !== '"' || value[value.length - 1] !== '"') return value;
    var decoded = "";
    var escaped = false;
    for (let index = 1; index < value.length - 1; index += 1) {
      const char = value[index];
      if (escaped) {
        decoded += char;
        escaped = false;
      } else if (char === "\\") {
        escaped = true;
      } else {
        decoded += char;
      }
    }
    if (escaped) decoded += "\\";
    return decoded;
  };

  var safeDownloadFilename = function (filename: string): string {
    var safe = Array.from(filename)
      .filter(function (char) {
        const code = char.charCodeAt(0);
        return !((code >= 0 && code <= 31) || (code >= 127 && code <= 159));
      })
      .join("")
      .replace(/[\\/]/g, "_")
      .replace(/[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]/g, "")
      .trim();
    return !safe || safe === "." || safe === ".." ? "download" : safe;
  };

  // Parse an RFC 6266 attachment. Quoted semicolons and escaped quotes stay
  // inside their parameter, and RFC 8187's UTF-8 filename wins when valid.
  // A non-attachment response returns null and follows the JSON path.
  var downloadFilename = function (disposition: string): string | null {
    var parts = splitDisposition(disposition);
    if (!parts.length || parts[0].toLowerCase() !== "attachment") return null;
    var parameters = new Map<string, string>();
    parts.slice(1).forEach(function (part) {
      var equals = part.indexOf("=");
      if (equals <= 0) return;
      var name = part.slice(0, equals).trim().toLowerCase();
      if (!parameters.has(name)) parameters.set(name, unquoteDispositionValue(part.slice(equals + 1)));
    });
    var filename = parameters.get("filename") || "download";
    var extended = parameters.get("filename*");
    if (extended) {
      const match = /^([^']*)'[^']*'(.*)$/.exec(extended);
      if (match && match[1].toLowerCase() === "utf-8") {
        try {
          filename = decodeURIComponent(match[2]);
        } catch (err) {
          console.warn("[Citry] events: could not decode the download filename:", err);
        }
      }
    }
    return safeDownloadFilename(filename);
  };

  var saveDownload = function (download: DownloadPayload) {
    var objectUrl = URL.createObjectURL(download.blob);
    var link = document.createElement("a");
    try {
      link.href = objectUrl;
      link.download = download.filename;
      document.body.appendChild(link);
      link.click();
    } finally {
      link.remove();
      // Revoking synchronously can cancel a save the browser has not started
      // reading yet, so release it after the click has had time to begin.
      window.setTimeout(function () {
        URL.revokeObjectURL(objectUrl);
      }, 10000);
    }
  };

  // A successful, single-call attachment is not an envelope. Buffer its
  // blob and attach it to a synthetic result so settlement can reject a late
  // or superseded response before any browser save starts.
  var downloadResponse = function (
    response: Response,
    filename: string,
    envelope: CallEnvelope,
  ): Promise<ResultEnvelope> {
    if (!response.ok) {
      return Promise.reject({
        status: response.status,
        code: "transport_error",
        message: "the download endpoint answered " + response.status + ".",
      });
    }
    if (envelope.calls.length !== 1) {
      return Promise.reject({
        status: 0,
        code: "transport_error",
        message: "a download response can answer exactly one event call.",
      });
    }
    return response.blob().then(function (blob) {
      var call = envelope.calls[0];
      var result: ResultEntry = { ok: true, actions: [] };
      if (typeof call.sendSequence === "number") result.sendSequence = call.sendSequence;
      stagedDownloads.set(result, { blob: blob, filename: filename });
      return {
        protocol: PROTOCOL,
        requestId: envelope.requestId,
        results: [result],
      };
    });
  };

  // The built-in HTTP transport (design 6.2): one request per envelope, to
  // the per-event route for a single call (so host middleware, rate limiters,
  // and access logs see the real per-handler URL) or the POST-only batch
  // endpoint for several. A single handler declared as GET carries its flat
  // args and internal call metadata in the query string. POST uses the vendor
  // media type, the X-Citry-Events CSRF floor, and any configured host token
  // (design 7.4).
  var fetchTransport: TransportImpl = {
    send: function (envelope) {
      var base = eventsBaseUrl();
      var single = envelope.calls.length === 1 ? envelope.calls[0] : null;
      var url = single
        ? base + "e/" + encodeURIComponent(single.componentClassId) + "/" + encodeURIComponent(single.handlerName)
        : base + "call";
      var method = single && eventHttpMethod(single.componentClassId, single.handlerName) === "GET" ? "GET" : "POST";
      var request: RequestInit = { method: method, credentials: "same-origin" };
      if (method === "GET" && single) {
        const encodedQuery = encodeGetCallQuery(envelope, single);
        if (encodedQuery) url += "?" + encodedQuery;
      } else {
        const headers: Record<string, string> = {
          "Content-Type": "application/citry-events+json",
          "X-Citry-Events": "1",
        };
        const csrf = resolveCsrfHeader();
        if (csrf) headers[csrf.header] = csrf.token;
        request.headers = headers;
        request.body = JSON.stringify(envelope);
      }
      return fetch(url, request).then(function (response) {
        var disposition = response.headers.get("Content-Disposition");
        var filename = disposition ? downloadFilename(disposition) : null;
        if (filename !== null) return downloadResponse(response, filename, envelope);
        return response.text().then(function (text) {
          var parsed: unknown = null;
          try {
            parsed = JSON.parse(text);
          } catch {
            parsed = null;
          }
          if (!parsed || typeof parsed !== "object" || !Array.isArray((parsed as ResultEnvelope).results)) {
            // Not an envelope: a proxy error page, a 405 from a
            // method-restricted handler, a crashed host. The wire itself is
            // always an envelope (the per-event route only mirrors a call's
            // status onto HTTP), so this is a transport-level failure.
            return Promise.reject({
              status: response.status,
              code: "transport_error",
              message: "the events endpoint answered " + response.status + " without a result envelope.",
            });
          }
          return parsed as ResultEnvelope;
        });
      });
    },
  };

  // ----- the transport registry (design 5.2, 6.1) -----

  var transports: Record<string, TransportImpl> = {};

  var registerTransportImpl = function (name: string, impl: TransportImpl) {
    if (typeof name !== "string" || !name) {
      throw pointedError('registerTransport needs a non-empty name string (e.g. "fetch").');
    }
    if (!impl || typeof impl.send !== "function") {
      throw pointedError(
        "registerTransport('" +
          name +
          "') needs an impl object with a send(envelope) function" +
          " returning (a promise of) the result envelope (design 6.1).",
      );
    }
    transports[name] = impl;
  };
  registerTransportImpl("fetch", fetchTransport);

  // The transport `send` uses: `configure({transport})` selects by name; the
  // built-in fetch is the default.
  var activeTransport = function (): TransportImpl {
    var name = typeof config.transport === "string" && config.transport ? config.transport : "fetch";
    var impl = transports[name];
    if (!impl) {
      throw pointedError(
        "no events transport is registered under '" +
          name +
          "'; registered: " +
          Object.keys(transports).sort().join(", ") +
          ". Register one with Citry.events.registerTransport(name, {send}).",
      );
    }
    return impl;
  };

  /**
   * One call of a `sendAll` batch. The three optional members are the event
   * queue's wiring (design 5.6): `queueManaged` says the queue owns the
   * `$loading` counters (it counts from enqueue to settle, so this layer must
   * not double-count), `onSettled` is fired exactly once when the call's
   * client lifecycle fully ends (its result's actions applied, or any
   * failure), and `onRecord` hands over the wire record so the queue can
   * abandon an in-flight call under `@event(latest_wins=True)`.
   */
  interface SendEntry {
    anchor: Anchor;
    name: string;
    args?: Record<string, unknown> | null;
    opts?: unknown;
    queueManaged?: boolean;
    onSettled?: () => void;
    onRecord?: (record: SendRecord) => void;
  }

  // Send a validated batch of calls. Owns everything anchor-side per call:
  // name validation (the pointed error fires before anything could hit the
  // wire), the cancellable `citry:events:before`, the send-side epoch
  // increment (design 4.2), the pending-updates snapshot, the `$loading`
  // counters (unless the queue manages them), the `$error` set/clear rule,
  // and the `:after`/`:error` surfacing. The wire itself is one shared
  // envelope through the registered transport, or, when the call-level test
  // stub is set, one stub call per entry.
  var sendAll = function (entries: SendEntry[]): Promise<unknown>[] {
    // Validate every call before any side effect, so a bad name in a batch
    // cannot leave earlier entries half-sent.
    entries.forEach(function (entry) {
      requireDeclaredEvent(entry.anchor, entry.name, "sendEvent");
      const args = entry.args == null ? {} : entry.args;
      if (!isPlainObject(args) || !isJsonValue(args)) {
        throw pointedError("the args for event '" + entry.name + "' must be a strict JSON object.");
      }
      if (eventHttpMethod(entry.anchor.classId, entry.name) !== "GET" && !isJsonValue(entry.anchor.pending)) {
        throw pointedError("the pending State updates for event '" + entry.name + "' must be strict JSON values.");
      }
    });
    var wireRecords: SendRecord[] = [];
    var promises = entries.map(function (entry) {
      var anchor = entry.anchor;
      var name = entry.name;
      var record: SendRecord;
      var dispatched: Promise<unknown>;
      // Cancellable just before the send (design 5.2): a prevented send
      // never hits the wire and its promise rejects with the client-minted
      // `cancelled` shape. The page performed the cancel itself, so no drop
      // event, no `$error`, no error event; `:after` still fires so
      // before/after pairs stay balanced (a progress bar started on
      // `:before` must stop). The stop still settles the call, so the
      // queue's hook fires and its dependents release (design 5.6).
      if (!fireLifecycle("citry:events:before", anchor, name, {}, true)) {
        fireLifecycle("citry:events:after", anchor, name, { ok: false });
        if (entry.onSettled) entry.onSettled();
        return Promise.reject(
          clientError("cancelled", "a citry:events:before listener stopped the send of '" + name + "'."),
        );
      }
      // The send-side half of the out-of-order guard (design 4.2): every
      // send from an anchor bumps its counter and echoes it in the call;
      // the apply-side comparison reads the echo.
      anchor.epoch += 1;
      // The id casts hold because requireDeclaredEvent above already threw
      // for a retired anchor (its declared list is empty).
      var call: TransportCall = {
        componentClassId: anchor.classId as string,
        handlerName: name,
        callerRenderId: anchor.componentId as string,
        args: entry.args || {},
        sendSequence: anchor.epoch,
      };
      if (
        anchor.token &&
        (eventHttpMethod(anchor.classId, name) !== "GET" || eventDeclaresState(anchor.classId, name))
      ) {
        call.stateToken = anchor.token;
      }
      if (eventHttpMethod(anchor.classId, name) !== "GET") {
        // The updates piggyback's second stage (design 4.2): a two-way draft
        // whose flush timer is still pending rides this call too, so a poll
        // tick uploads the mid-debounce draft instead of racing it. The flush
        // writes the control's current value into `$state` here, which lands it
        // in the pending snapshot below. Read-only GET events deliberately do
        // not flush or consume pending writes; the next mutating call carries them.
        collectPendingTwoWayDrafts(anchor);
        // Defense at the wire boundary: even if a deploy refresh or another
        // future path left stale pending data, never transmit a field the
        // current class descriptor no longer permits.
        dropInvalidPendingFields(anchor, "before send");
        const pendingKeys = Object.keys(anchor.pending);
        if (pendingKeys.length) {
          // The queued `$state` writes ride this call and stop being "pending
          // unsent": from here on, incoming server values win these fields
          // again. A rejected call puts them back (the rejection handler
          // below).
          call.stateUpdates = anchor.pending;
          anchor.pending = {};
        }
      }

      // With the stub the promise settles the whole lifecycle, so the settle
      // hook fires in the settlement arms below; on the wire the record
      // carries it, and the wire layer fires it when the application (not
      // just the response) finishes (design 5.6: settled means applied).
      var viaStub = Boolean(transportImpl);
      if (transportImpl) {
        // The call-level test stub: its resolved value settles the caller
        // directly, bypassing the envelope, correlation, and timeout layers.
        try {
          dispatched = Promise.resolve(transportImpl(call, entry.opts || null));
        } catch (err) {
          dispatched = Promise.reject(err);
        }
      } else {
        record = makeSendRecord(anchor, name, call, resolveTimeoutMs(entry.opts));
        record.onSettled = entry.onSettled || null;
        if (entry.onRecord) entry.onRecord(record);
        wireRecords.push(record);
        dispatched = record.promise;
      }

      // The queue counts $loading from enqueue to settle (busy spans the
      // queue, design 5.6), so a queue-managed entry must not count again
      // here; the direct batch path (`sendCalls`) still counts per flight.
      if (!entry.queueManaged) beginLoading(anchor, name);
      return dispatched.then(
        function (result) {
          if (!entry.queueManaged) endLoading(anchor, name);
          anchor.errorBox.current = null; // cleared on the next successful call
          fireLifecycle("citry:events:after", anchor, name, { ok: true });
          if (viaStub && entry.onSettled) entry.onSettled();
          return result;
        },
        function (err) {
          if (!entry.queueManaged) endLoading(anchor, name);
          // A rejected call is treated as undelivered: its snapshotted
          // writes go back into the pending queue so a retry still carries
          // them and an incoming render cannot silently revert those
          // fields. A field the user wrote again while the call was in
          // flight keeps the newer value. (The non-null assertion re-states
          // the snapshot above; the narrowing does not reach this callback.)
          if (call.stateUpdates) {
            const droppedUpdates: string[] = [];
            Object.keys(call.stateUpdates).forEach(function (key) {
              if (!anchor.writable || !anchor.writable.has(key)) {
                droppedUpdates.push(key);
              } else if (!Object.prototype.hasOwnProperty.call(anchor.pending, key)) {
                anchor.pending[key] = call.stateUpdates![key];
              }
            });
            if (droppedUpdates.length) {
              console.warn(
                "[Citry] events: a rejected call carried $state fields that are no longer client-writable;" +
                  " they were not restored to the pending queue: " +
                  droppedUpdates.sort().join(", ") +
                  ".",
              );
            }
          }
          var structured = toErrorEnvelope(err);
          // `cancelled` and `superseded` are routine queue outcomes: the
          // rejection is their whole surface, so neither `$error` nor the
          // error event fires for them; every real failure (a transport
          // failure, an error result, a timeout) sets both (design 5.2's
          // compose-by-reason rule).
          if (structured.code !== "cancelled" && structured.code !== "superseded") {
            anchor.errorBox.current = structured;
            fireLifecycle("citry:events:error", anchor, name, { error: structured });
          }
          fireLifecycle("citry:events:after", anchor, name, { ok: false });
          if (viaStub && entry.onSettled) entry.onSettled();
          throw err;
        },
      );
    });
    if (wireRecords.length) sendRecordsOverWire(wireRecords);
    return promises;
  };

  // ----- the event queue: a dependency DAG (design 5.6) -----

  // Queued events are nodes in a DAG. At enqueue an event gains a dependency
  // edge to every not-yet-settled event whose dispatching anchor is the same
  // anchor as, an ancestor of, or a descendant of its own; containment is DOM
  // containment, resolved from the dispatching element's marker chain upward
  // and the anchor's live roots downward, and re-verified at dequeue because
  // the DOM may have changed while the event waited. An event dispatches
  // when every edge it holds is settled, so independent branches run in
  // parallel while overlapping work applies in the order the user caused it.
  // Settled means applied: a predecessor releases its dependents when its
  // result's actions have finished applying (or when it fails: a transport
  // error, an error result, and the timeout all settle), never at mere
  // response arrival.

  /** One queued event: a node of the dependency DAG (design 5.6). */
  interface QueueNode {
    /** Enqueue order; edges only ever point at lower seqs, so no cycle can form. */
    seq: number;
    /** The dispatching anchor (re-resolved from the element at fire time). */
    anchor: Anchor;
    /** Where the gesture's `$loading` count and busy stamp live; follows `anchor` on re-resolution. */
    loadingAnchor: Anchor;
    /**
     * The dispatching element, when the caller had one: the containment walk
     * starts here, the busy stamp lands here, and fire-time re-resolution
     * reads it. Null for sends addressed by instance id alone.
     */
    element: Element | null;
    /** Keep the exact authored source anchor instead of resolving ownership from `element` at dequeue. */
    ownerLocked: boolean;
    /** Re-resolve an explicit public Element target through physical markers, never fill projection. */
    physicalOwner: boolean;
    /** Optional target-group liveness check for a relocated component-boundary binding. */
    carrierLive: (() => boolean) | null;
    name: string;
    args: Record<string, unknown> | null;
    opts: unknown;
    /** The `@event` queue knobs from the class descriptor, read at enqueue (design 3.5). */
    bundle: boolean;
    latestWins: boolean;
    /** The tick-skip key for recurring bindings (design 5.6); null for ordinary sends. */
    recurringKey: string | null;
    /** True from the moment the node's call went to the send path. */
    dispatched: boolean;
    settled: boolean;
    /** The unsettled predecessors this event waits on. */
    deps: Set<QueueNode>;
    /** The wire record once dispatched (for latest_wins abandonment); null on the stub path. */
    record: SendRecord | null;
    promise: Promise<unknown>;
    resolve: (value: unknown) => void;
    reject: (reason: unknown) => void;
  }

  var queueSeq = 0;
  // Every unsettled node (queued and in flight), oldest first. Settled nodes
  // leave immediately, so scans stay proportional to outstanding work.
  var queueNodes: QueueNode[] = [];
  // Outstanding calls per recurring-binding key, `wait: false` sends
  // included: the tick-skip rule (design 5.6) holds a recurring binding to
  // at most one outstanding call.
  var recurringOutstanding = new Map<string, number>();

  var bumpRecurring = function (key: string, delta: number) {
    var next = (recurringOutstanding.get(key) || 0) + delta;
    if (next > 0) recurringOutstanding.set(key, next);
    else recurringOutstanding.delete(key);
  };

  /** The send opts fields the queue reads; everything else passes through to the wire layer. */
  var readQueueOpts = function (opts: unknown): { wait: boolean } {
    var wait = true;
    if (opts && typeof opts === "object") {
      if ((opts as { wait?: unknown }).wait === false) wait = false;
    }
    return { wait: wait };
  };

  // The `@event` queue knobs for one handler, from the class descriptor
  // (design 3.5, carried per 4.4): only non-default values ride the wire, so
  // absence means the defaults (bundling on, latest_wins off).
  var eventKnobs = function (anchor: Anchor, name: string) {
    var descriptor = classes.get(anchor.classId as string);
    var options = descriptor && descriptor.eventHandlers ? descriptor.eventHandlers[name] : null;
    return {
      bundle: !options || options.allowBatching !== false,
      latestWins: Boolean(options && options.latestCallWins === true),
    };
  };

  // Every anchor whose DOM position overlaps `anchor`'s: itself, the
  // ancestors on the `data-cid` walk upward (from the dispatching element
  // when there is one, and from each live root), and the descendants under
  // the live roots (design 5.6, resolving containment through 5.5's
  // markers). Resolved fresh from the live DOM on every call, which is what
  // makes the dequeue-time re-verification meaningful.
  var relatedAnchorsOf = function (anchor: Anchor, element: Element | null, physicalOnly?: boolean): Set<Anchor> {
    var related = new Set<Anchor>([anchor]);
    var ownership = globalThis.Citry?.manager?.ownership;
    if (!physicalOnly && anchor.clientAnchor && ownership) {
      ownership._relatedEvents(anchor.clientAnchor).forEach(function (candidate) {
        related.add(candidate);
      });
      return related;
    }
    var addIdsOf = function (el: Element) {
      (el.getAttribute("data-cid") || "")
        .trim()
        .split(/\s+/)
        .filter(Boolean)
        .forEach(function (id) {
          var found = idToAnchor.get(id);
          if (found) related.add(found);
        });
    };
    var walkUp = function (from: Element) {
      // closest() matches `from` itself first, so the walk covers the
      // starting root too (a shared root overlaps every instance it
      // carries, design 5.5).
      var el: Element | null = from.closest("[data-cid]");
      while (el) {
        addIdsOf(el);
        el = el.parentElement ? el.parentElement.closest("[data-cid]") : null;
      }
    };
    if (element && element.isConnected) walkUp(element);
    if (anchor.componentId != null) {
      document.querySelectorAll("[data-cid-" + anchor.componentId + "]").forEach(function (root) {
        walkUp(root);
        root.querySelectorAll("[data-cid]").forEach(addIdsOf);
      });
    }
    return related;
  };

  // Add the containment edges `node` holds right now: one edge to every
  // earlier, still-unsettled event whose anchor overlaps. Called at enqueue
  // (when every unsettled node is earlier) and again at dequeue, where the
  // earlier-events-only guard keeps the graph acyclic (design 5.6: a
  // later-enqueued overlap already holds its own edge to this event).
  var addContainmentEdges = function (node: QueueNode) {
    var related = relatedAnchorsOf(node.anchor, node.element, node.physicalOwner);
    queueNodes.forEach(function (other) {
      if (other === node || other.settled || other.seq >= node.seq) return;
      if (related.has(other.anchor)) node.deps.add(other);
    });
  };

  // Busy from the gesture (design 5.6): stamp `data-citry-busy` on the
  // anchor's live roots and on the triggering element the moment the event
  // enqueues, one continuous busy state through queue, flight, and apply.
  // The trigger is remembered on the anchor so the applier's re-stamp keeps
  // it visible across renders (design 5.5).
  var busyTriggerCounts = new WeakMap<Element, Map<Anchor, number>>();

  var retainBusyTrigger = function (anchor: Anchor, element: Element) {
    var counts = busyTriggerCounts.get(element);
    if (!counts) {
      counts = new Map<Anchor, number>();
      busyTriggerCounts.set(element, counts);
    }
    counts.set(anchor, (counts.get(anchor) || 0) + 1);
    anchor.busyTriggers.add(element);
    element.setAttribute("data-citry-busy", "");
  };

  var releaseBusyTrigger = function (anchor: Anchor, element: Element) {
    var counts = busyTriggerCounts.get(element);
    if (!counts) return;
    var next = (counts.get(anchor) || 0) - 1;
    if (next > 0) counts.set(anchor, next);
    else {
      counts.delete(anchor);
      anchor.busyTriggers.delete(element);
    }
    if (counts.size === 0) {
      busyTriggerCounts.delete(element);
      element.removeAttribute("data-citry-busy");
    }
  };

  var stampGestureBusy = function (anchor: Anchor, element: Element | null, physicalOnly?: boolean) {
    if (!physicalOnly && anchor.componentId != null) {
      document.querySelectorAll("[data-cid-" + anchor.componentId + "]").forEach(function (el) {
        el.setAttribute("data-citry-busy", "");
      });
    }
    if (element) {
      retainBusyTrigger(anchor, element);
    }
  };

  // Busy clears on every settle path (design 5.6). The trigger unstamps
  // unless another outstanding call still rides the same element; the roots
  // unstamp when the anchor's whole count reaches zero (several calls can
  // overlap one instance).
  var clearGestureBusy = function (anchor: Anchor, element: Element | null, physicalOnly?: boolean) {
    if (element) releaseBusyTrigger(anchor, element);
    if (!physicalOnly && anchor.loading.any <= 0 && anchor.componentId != null) {
      document.querySelectorAll("[data-cid-" + anchor.componentId + "]").forEach(function (el) {
        el.removeAttribute("data-citry-busy");
      });
    }
  };

  // Settle one node exactly once: it leaves the graph, every dependent
  // releases its edge to it, the gesture's busy surface ends, and the queue
  // re-processes (a released dependent may now dispatch). Every path an
  // event can end on funnels here: applied, an error result, a transport
  // failure, the timeout, a `citry:events:before` stop, the dequeue-time
  // cancel, and supersession.
  var settleQueueNode = function (node: QueueNode) {
    if (node.settled) return;
    node.settled = true;
    var index = queueNodes.indexOf(node);
    if (index !== -1) queueNodes.splice(index, 1);
    queueNodes.forEach(function (other) {
      other.deps.delete(node);
    });
    if (node.recurringKey) bumpRecurring(node.recurringKey, -1);
    endLoading(node.loadingAnchor, node.name);
    clearGestureBusy(node.loadingAnchor, node.element, node.ownerLocked);
    processQueue();
  };

  // The latest_wins sweep at enqueue (design 3.5/5.6): drop this handler's
  // queued-not-sent predecessors on the same anchor (never sent), and
  // abandon an in-flight one (its response's application drops on arrival);
  // either way the predecessor's promise rejects with the `superseded`
  // reason. The sweep runs before the new call computes its edges, so it
  // never waits on what it just superseded (design 5.6: "sending without
  // waiting for the abandoned response").
  var supersedeOlderCalls = function (node: QueueNode) {
    var older = queueNodes.filter(function (other) {
      return !other.settled && other.anchor === node.anchor && other.name === node.name;
    });
    older.forEach(function (other) {
      var rejection = clientError(
        "superseded",
        "'" +
          node.name +
          "' was superseded by a newer call to the same handler (@event(latest_wins=True), design 3.5).",
      );
      if (other.dispatched) {
        if (other.record) {
          // Abandon the wire record: its timer stops (a timeout firing after
          // this would misname the drop), the rejection reaches the caller
          // through the record's settlement arms, and the arrival-side drop
          // fires the stale event with reason `superseded`.
          other.record.superseded = true;
          window.clearTimeout(other.record.timerId);
          other.record.reject(rejection);
        } else {
          other.reject(rejection);
        }
        console.debug(
          "[Citry] events: abandoned the in-flight '" + other.name + "': a newer call superseded it (latest_wins).",
        );
      } else {
        other.reject(rejection);
        fireStale(other.anchor, other.name, "superseded");
        console.debug(
          "[Citry] events: dropped queued '" + other.name + "': a newer call superseded it (latest_wins); never sent.",
        );
      }
      settleQueueNode(other);
    });
  };

  // Dead at dequeue: never sent, the promise rejects with the named
  // `cancelled` reason, the drop event fires, and a debug line records it.
  // A queued click on a region that a predecessor's render just replaced
  // must not fire a ghost call at whatever now occupies the position
  // (design 5.6).
  var cancelAtDequeue = function (node: QueueNode) {
    node.reject(
      clientError(
        "cancelled",
        "'" +
          node.name +
          "' was cancelled: its dispatching element or component instance left the DOM while the call was queued (design 5.6).",
      ),
    );
    fireStale(node.anchor, node.name, "cancelled");
    console.debug(
      "[Citry] events: cancelled queued '" + node.name + "': its dispatching element or instance is gone; never sent.",
    );
    settleQueueNode(node);
  };

  // The dispatching element re-resolves to an anchor at fire time (design
  // 5.6, 5.5's machinery item 5): when the element survived into a
  // different instance, the gesture's count and busy stamp follow it, so
  // the busy surface stays one continuous state from the original gesture.
  var transferGesture = function (node: QueueNode, fresh: Anchor) {
    var old = node.loadingAnchor;
    endLoading(old, node.name);
    if (node.element) releaseBusyTrigger(old, node.element);
    if (old.loading.any <= 0 && old.componentId != null) {
      document.querySelectorAll("[data-cid-" + old.componentId + "]").forEach(function (el) {
        el.removeAttribute("data-citry-busy");
      });
    }
    node.anchor = fresh;
    node.loadingAnchor = fresh;
    beginLoading(fresh, node.name);
    stampGestureBusy(fresh, node.element);
  };

  // Re-check one dispatch-ready node against the live DOM (design 5.6):
  // re-resolve the dispatching element to an anchor, then re-verify the
  // containment its edges were computed from against the still-unsettled
  // earlier events (the DOM may have changed while the event waited).
  var verifyAtDequeue = function (node: QueueNode): "dispatch" | "hold" | "dead" {
    var anchor: Anchor | null = node.anchor;
    var physicalId: string | null;
    if (node.carrierLive && !node.carrierLive()) return "dead";
    if (node.element) {
      if (!node.element.isConnected) return "dead";
      if (!node.ownerLocked) {
        if (node.physicalOwner) {
          physicalId = innermostPhysicalComponentId(node.element);
          anchor = (physicalId && idToAnchor.get(physicalId)) || null;
        } else {
          anchor = anchorForElement(node.element);
        }
        if (!anchor) return "dead";
      }
    }
    if (node.ownerLocked) {
      if (anchor.componentId == null) return "dead";
      if (
        anchor.clientAnchor &&
        globalThis.Citry?.manager?.ownership &&
        !globalThis.Citry.manager.ownership._isLive(anchor.clientAnchor)
      ) {
        return "dead";
      }
      if (
        !anchor.clientAnchor &&
        anchor.seenInDom &&
        !document.querySelector("[data-cid-" + anchor.componentId + "]")
      ) {
        return "dead";
      }
    } else {
      if (!node.element) {
        if (anchor.componentId == null) return "dead";
        if (
          anchor.clientAnchor &&
          globalThis.Citry?.manager?.ownership &&
          !globalThis.Citry.manager.ownership._isLive(anchor.clientAnchor)
        ) {
          return "dead";
        }
        // An anchor whose root has never been in the DOM is pending, not dead
        // (a head-consumed manifest mints anchors before the body parses).
        if (anchor.seenInDom && !document.querySelector("[data-cid-" + anchor.componentId + "]")) return "dead";
      }
    }
    // A render can swap the surviving position to a class that does not
    // declare this event (the adopt branch, design 5.5); firing it would be
    // a ghost call, so it dies with the position.
    if (anchor.classId == null || declaredEvents(anchor.classId).indexOf(node.name) === -1) return "dead";
    if (anchor !== node.anchor) transferGesture(node, anchor);
    addContainmentEdges(node);
    return node.deps.size ? "hold" : "dispatch";
  };

  // Dispatch a set of events that became eligible together: bundleable ones
  // batch into shared envelopes, each call keeping its own promise and its
  // own result slot, with the sixteen-call cap splitting in order; an
  // `@event(bundle=False)` call sends alone (design 5.6/3.5).
  var dispatchReadyNodes = function (ready: QueueNode[]) {
    var chunks: QueueNode[][] = [];
    var bundled: QueueNode[] = [];
    ready.forEach(function (node) {
      if (!node.bundle) return;
      bundled.push(node);
      if (bundled.length === MAX_CALLS_PER_ENVELOPE) {
        chunks.push(bundled);
        bundled = [];
      }
    });
    if (bundled.length) chunks.push(bundled);
    ready.forEach(function (node) {
      if (!node.bundle) chunks.push([node]);
    });
    chunks.forEach(function (chunk) {
      chunk.forEach(function (node) {
        node.dispatched = true;
      });
      var entries: SendEntry[] = chunk.map(function (node) {
        return {
          anchor: node.anchor,
          name: node.name,
          args: node.args,
          opts: node.opts,
          queueManaged: true,
          onSettled: function () {
            settleQueueNode(node);
          },
          onRecord: function (record: SendRecord) {
            node.record = record;
          },
        };
      });
      var promises: Promise<unknown>[];
      try {
        promises = sendAll(entries);
      } catch (err) {
        // sendAll validates the whole chunk before any side effect, so a
        // throw (a class change racing the dispatch) sinks the chunk whole.
        chunk.forEach(function (node) {
          node.reject(err);
          settleQueueNode(node);
        });
        return;
      }
      promises.forEach(function (promise, index) {
        var node = chunk[index];
        promise.then(
          function (value) {
            // Resolution settles the caller at the `data` action; the node
            // itself settles at application-complete through `onSettled`
            // (design 5.6: settled means applied).
            node.resolve(value);
          },
          function (err) {
            node.reject(err);
            settleQueueNode(node);
          },
        );
      });
    });
  };

  // One release pass: every queued node whose edges all settled re-verifies
  // against the live DOM, and the survivors dispatch together (the roots of
  // the DAG are exactly the dispatchable set). Reentrant calls (a settle
  // inside a dispatch) fold into the loop instead of recursing.
  var queueProcessing = false;
  var queueReprocess = false;
  var processQueue = function () {
    var ready: QueueNode[];
    if (queueProcessing) {
      queueReprocess = true;
      return;
    }
    queueProcessing = true;
    do {
      queueReprocess = false;
      ready = [];
      queueNodes.slice().forEach(function (node) {
        if (node.settled || node.dispatched || node.deps.size !== 0) return;
        var verdict = verifyAtDequeue(node);
        if (verdict === "dead") cancelAtDequeue(node);
        else if (verdict === "dispatch") ready.push(node);
        // "hold": re-verification added edges to earlier unsettled events;
        // the node waits for them like any other dependency.
      });
      if (ready.length) dispatchReadyNodes(ready);
    } while (queueReprocess);
    queueProcessing = false;
  };

  // A `wait: false` send joins no graph (design 5.6): it fires immediately,
  // gains no edges, no later event gains an edge to it, and its late
  // responses are what the per-anchor epoch guard nets. The busy surface
  // still spans send to settle, which for an immediate send starts at the
  // same gesture.
  var dispatchBypass = function (
    anchor: Anchor,
    name: string,
    args: Record<string, unknown> | null,
    opts: unknown,
    element: Element | null,
    recurringKey: string | null,
    ownerLocked?: boolean,
  ): Promise<unknown> {
    beginLoading(anchor, name);
    stampGestureBusy(anchor, element, ownerLocked);
    if (recurringKey) bumpRecurring(recurringKey, 1);
    var settled = false;
    var finish = function () {
      if (settled) return;
      settled = true;
      if (recurringKey) bumpRecurring(recurringKey, -1);
      endLoading(anchor, name);
      clearGestureBusy(anchor, element, ownerLocked);
    };
    return sendAll([{ anchor: anchor, name: name, args: args, opts: opts, queueManaged: true, onSettled: finish }])[0];
  };

  // Enqueue one send (the queue's front door): validate, apply the tick-skip
  // rule and the latest_wins sweep, start the busy surface at the gesture,
  // compute the containment edges, and dispatch immediately when nothing
  // holds the event (an uncontended send goes to the wire in the same
  // tick). Returns null only for a skipped recurring tick; ordinary sends
  // always get a promise.
  var enqueueSend = function (
    anchor: Anchor,
    name: string,
    args: Record<string, unknown> | null,
    opts: unknown,
    element: Element | null,
    ownerLocked?: boolean,
    carrierLive?: (() => boolean) | null,
    physicalOwner?: boolean,
    recurringKey?: string | null,
  ): Promise<unknown> | null {
    // The pointed error fires here, before anything is queued: an unknown
    // event name fails client-side, before anything hits the wire (design
    // 5.5).
    requireDeclaredEvent(anchor, name, "sendEvent");
    var queueOpts = readQueueOpts(opts);
    if (recurringKey && (recurringOutstanding.get(recurringKey) || 0) > 0) {
      // The tick-skip rule (design 5.6): at most one outstanding call per
      // recurring binding; a tick that fires early is skipped, never queued
      // behind its predecessor.
      console.debug(
        "[Citry] events: skipped a recurring '" + name + "' tick: its previous call is still queued or in flight.",
      );
      return null;
    }
    if (!queueOpts.wait) return dispatchBypass(anchor, name, args, opts, element, recurringKey || null, ownerLocked);
    var knobs = eventKnobs(anchor, name);
    queueSeq += 1;
    var resolveFn: (value: unknown) => void = function () {};
    var rejectFn: (reason: unknown) => void = function () {};
    var promise = new Promise<unknown>(function (resolve, reject) {
      resolveFn = resolve;
      rejectFn = reject;
    });
    var node: QueueNode = {
      seq: queueSeq,
      anchor: anchor,
      loadingAnchor: anchor,
      element: element,
      ownerLocked: ownerLocked === true,
      physicalOwner: physicalOwner === true,
      carrierLive: carrierLive || null,
      name: name,
      args: args,
      opts: opts,
      bundle: knobs.bundle,
      latestWins: knobs.latestWins,
      recurringKey: recurringKey || null,
      dispatched: false,
      settled: false,
      deps: new Set<QueueNode>(),
      record: null,
      promise: promise,
      resolve: resolveFn,
      reject: rejectFn,
    };
    if (node.latestWins) supersedeOlderCalls(node);
    beginLoading(anchor, name);
    stampGestureBusy(anchor, element, node.ownerLocked);
    if (node.recurringKey) bumpRecurring(node.recurringKey, 1);
    addContainmentEdges(node);
    queueNodes.push(node);
    if (node.deps.size === 0) dispatchReadyNodes([node]);
    return node.promise;
  };

  // Send one event from an anchor: every user-facing send path lands here
  // (`Citry.events.send`, the `sendEvent` payload member, the `$sendEvent`
  // magic) and rides the event queue (design 5.6). `element` is the
  // dispatching element when the caller had one; it anchors the containment
  // walk, the busy stamp, and fire-time re-resolution.
  var sendFromAnchor = function (
    anchor: Anchor,
    name: string,
    args?: Record<string, unknown> | null,
    opts?: unknown,
    element?: Element | null,
    physicalOwner?: boolean,
  ): Promise<unknown> {
    // Only recurring sends can be skipped (a null return), and only the
    // bindings entry passes `recurring`, so the promise is always real here.
    return enqueueSend(
      anchor,
      name,
      args || null,
      opts,
      element || null,
      false,
      null,
      physicalOwner,
    ) as Promise<unknown>;
  };

  // The bindings-runtime send entry (`_internal.sendFromElement`; the
  // bindings work package wires listeners and timers onto it): resolve the
  // innermost instance from the element at fire time and ride the queue with
  // the element as the dispatching element. A fire-time miss, or a hit on a
  // class that does not declare the event, drops the send before anything
  // is sent (design 5.5 machinery item 5): the drop event fires (reason
  // `cancelled`) with a debug line, and null comes back instead of a
  // promise. The private `recurringKey` applies the tick-skip rule the same
  // way (null, with the breadcrumb); it is never read from public opts.
  var sendFromElement = function (
    el: Element,
    name: string,
    args?: Record<string, unknown> | null,
    opts?: unknown,
    recurringKey?: string | null,
  ): Promise<unknown> | null {
    var projectedOwner = projectedComponentId(el);
    if (projectedOwner !== undefined) {
      if (projectedOwner === null) {
        fireStale(null, name, "cancelled");
        console.debug("[Citry] events: dropped a source-owned '" + name + "' send: its fill source is retired.");
        return null;
      }
      return sendSourceOwned(projectedOwner, name, args || null, opts, el, function () {
        return projectedComponentId(el) === projectedOwner;
      });
    }
    var anchor = el && (el as MaybeElement).nodeType === 1 ? anchorForElement(el) : null;
    if (!anchor || anchor.classId == null || declaredEvents(anchor.classId).indexOf(name) === -1) {
      fireStale(anchor, name, "cancelled");
      console.debug(
        "[Citry] events: dropped a '" + name + "' send: its element resolves to no instance declaring the event.",
      );
      return null;
    }
    return enqueueSend(anchor, name, args || null, opts, el, false, null, false, recurringKey);
  };

  var sendSourceOwned = function (
    componentId: string,
    name: string,
    args: Record<string, unknown> | null,
    opts: unknown,
    element: Element | null,
    carrierLive?: (() => boolean) | null,
  ): Promise<unknown> | null {
    var anchor = idToAnchor.get(componentId) || null;
    if (carrierLive && !carrierLive()) {
      fireStale(anchor, name, "cancelled");
      console.debug("[Citry] events: dropped a source-owned '" + name + "' send: its exact source carrier is retired.");
      return null;
    }
    if (!anchor || anchor.classId == null || declaredEvents(anchor.classId).indexOf(name) === -1) {
      fireStale(anchor, name, "cancelled");
      console.debug(
        "[Citry] events: dropped a source-owned '" +
          name +
          "' send: its authored component instance is no longer live or does not declare the event.",
      );
      return null;
    }
    return enqueueSend(anchor, name, args || null, opts, element, true, carrierLive || null);
  };

  var sendBoundary = function (
    componentId: string,
    name: string,
    args: Record<string, unknown> | null,
    opts: unknown,
    element: Element | null,
    carrierLive?: (() => boolean) | null,
    event?: Event | null,
  ): Promise<unknown> | null {
    args = mergeSubmitFormArgs(element, event, args);
    return sendSourceOwned(componentId, name, args || null, opts, element, carrierLive || null);
  };

  var boundaryScope = function (
    componentId: string,
    element: Element | null,
    carrierLive?: (() => boolean) | null,
  ): object {
    var anchor = idToAnchor.get(componentId) || null;
    var scope: Record<string, unknown> = {};
    Object.defineProperties(scope, {
      $state: {
        enumerable: true,
        get: function () {
          return anchor ? anchor.stateProxy : INERT_STATE;
        },
      },
      $loading: {
        enumerable: true,
        value: function (name?: string) {
          if (!anchor) return false;
          if (name === undefined) return anchor.loading.any > 0;
          requireDeclaredEvent(anchor, name, "$loading");
          return (anchor.loading.handlers[name] || 0) > 0;
        },
      },
      $error: {
        enumerable: true,
        get: function () {
          return anchor ? anchor.errorBox.current : null;
        },
      },
      $sendEvent: {
        enumerable: true,
        value: function (name: string, args?: Record<string, unknown>, opts?: unknown) {
          if (!anchor) {
            return Promise.reject(
              pointedError(
                "the source component instance '" + componentId + "' is no longer registered; $sendEvent was not sent.",
              ),
            );
          }
          return sendBoundary(componentId, name, args || null, opts, element, carrierLive || null);
        },
      },
      $onEvent: {
        enumerable: true,
        value: function (name: string, fn: EventCallback) {
          return anchor ? subscribeForAnchor(anchor, name, fn) : function () {};
        },
      },
    });
    return scope;
  };

  // The `_internal.sendCalls` batch entry: resolve every intent's target
  // first (all-or-nothing, before any side effect), then send them as one
  // batch, one shared envelope (design 4.2). This is the direct wire path,
  // with no queue in front: tests and custom transports drive the batch
  // shape through it, while user-facing sends ride the event queue above.
  var sendCalls = function (intents: SendIntent[]): Promise<unknown>[] {
    if (!Array.isArray(intents) || !intents.length) return [];
    if (intents.length > MAX_CALLS_PER_ENVELOPE) {
      throw pointedError(
        "one envelope carries at most " +
          MAX_CALLS_PER_ENVELOPE +
          " calls (the protocol cap, design 4.2); split the batch before sending (" +
          intents.length +
          " given).",
      );
    }
    var entries = intents.map(function (intent) {
      var anchor = resolveSendTarget(intent.target);
      if (!anchor) {
        throw pointedError(
          "sendCalls found no interactive component instance for target " +
            (typeof intent.target === "string" ? "'" + intent.target + "'" : String(intent.target)) +
            "; pass an instance id from the events manifest or an element inside one.",
        );
      }
      return { anchor: anchor, name: intent.name, args: intent.args, opts: intent.opts };
    });
    return sendAll(entries);
  };

  // Whether an event that surfaced on `target` is aimed at the instance with
  // `componentId`: the event's nearest instance root must carry that id. The
  // actions applier dispatches server events as bubbling CustomEvents on the
  // target instance's own elements, so checking the NEAREST marker root (not
  // just any enclosing one) keeps an event aimed at a nested child from also
  // firing the enclosing parent's subscriptions, while a shared root (one
  // element carrying both ids) correctly fires both.
  var eventTargetsInstance = function (target: MaybeElement | null, componentId: string) {
    var el = target && target.nodeType === 1 ? target : null;
    var root = el && el.closest ? el.closest("[data-cid]") : null;
    return Boolean(root && root.hasAttribute("data-cid-" + componentId));
  };

  // Listen for server-dispatched events aimed at this anchor's instance. The
  // anchor's CURRENT component id is read at fire time: the id changes with
  // every render while the subscription lives on.
  var subscribeForAnchor = function (anchor: Anchor, name: string, fn: EventCallback) {
    var handler = function (e: Event) {
      if (anchor.componentId == null) return;
      // The cast bridges lib.dom's EventTarget to the defensive shape the
      // helper probes; the nodeType check inside does the real work.
      if (eventTargetsInstance(e.target as MaybeElement | null, anchor.componentId)) fn((e as CustomEvent).detail);
    };
    document.addEventListener(name, handler);
    return function () {
      document.removeEventListener(name, handler);
    };
  };

  // The same, held to a component id the caller captured while no anchor was
  // registered for it (a queued bootstrap-stub subscription): fires only if
  // elements with that id ever surface events.
  var subscribeForId = function (componentId: string, name: string, fn: EventCallback) {
    var anchor = idToAnchor.get(componentId);
    if (anchor) return subscribeForAnchor(anchor, name, fn);
    var handler = function (e: Event) {
      if (eventTargetsInstance(e.target as MaybeElement | null, componentId)) fn((e as CustomEvent).detail);
    };
    document.addEventListener(name, handler);
    return function () {
      document.removeEventListener(name, handler);
    };
  };

  // ----- lifecycle events and drop surfacing (design 5.2, the R3 contract) -----

  // The shared dispatch helper every runtime lifecycle event goes through.
  // Every detail carries `{instance, class, event}` (design 5.2) plus the
  // event-specific fields (`ok` on `:after`, `error` on `:error`, `els` on
  // `:swapped`, `reason` on `:stale`). The event bubbles from the instance's
  // first live root when one exists, so instance-scoped listeners can hear
  // it; `document` is the fallback for callers with no live DOM. A
  // cancellable event (`:before`, and `:stale` under reason `version`, where
  // preventDefault replaces a default handling) reports back whether it went
  // unprevented, which is what dispatchEvent returns.
  var fireLifecycle = function (
    type: string,
    anchor: Anchor | null,
    eventName: string | null,
    extra: Record<string, unknown>,
    cancelable?: boolean,
  ): boolean {
    var detail: Record<string, unknown> = {
      instance: anchor ? anchor.componentId : null,
      class: anchor ? anchor.classId : null,
      event: eventName,
    };
    Object.keys(extra).forEach(function (key) {
      detail[key] = extra[key];
    });
    var target: Element | null = null;
    if (anchor && anchor.componentId != null) {
      target = document.querySelector("[data-cid-" + anchor.componentId + "]");
    }
    return (target || document).dispatchEvent(
      new CustomEvent(type, { detail: detail, bubbles: true, cancelable: cancelable === true }),
    );
  };

  // The one drop event (design 5.2): every drop the runtime performs fires
  // `citry:events:stale` with a `reason` naming the cause. This layer fires
  // reasons `epoch` and `retired`; the transport and queue layers add theirs.
  var fireStale = function (anchor: Anchor | null, eventName: string | null, reason: string) {
    fireLifecycle("citry:events:stale", anchor, eventName, { reason: reason });
  };

  // ----- the anchor retirement sweep (design 5.5 machinery item 3) -----

  // Retire every anchor whose component id has no live element. The applier
  // runs this synchronously with each swap (per-action liveness must see the
  // retirement, machinery item 4); the microtask-debounced backstop below
  // catches removals the applier never saw (host JS clearing a container, a
  // parent's morph discarding children). The debounce makes a morph's
  // remove-then-add churn within one mutation batch read whole, the same
  // property the dependency manager's sweep relies on.
  var sweepRetiredAnchors = function () {
    anchorSweepScheduled = false;
    var entries: [string, Anchor][] = [];
    idToAnchor.forEach(function (anchor, componentId) {
      entries.push([componentId, anchor]);
    });
    entries.forEach(function (entry) {
      var componentId = entry[0];
      var anchor = entry[1];
      if (anchor.clientAnchor && globalThis.Citry?.manager?.ownership) {
        if (globalThis.Citry.manager.ownership._isLive(anchor.clientAnchor)) return;
        if (anchor.componentId === componentId) retireAnchor(anchor);
        else idToAnchor.delete(componentId);
        return;
      }
      // An anchor whose root has never been in the DOM is not "removed": a
      // head-consumed manifest mints anchors before the body parses.
      if (!anchor.seenInDom) return;
      if (document.querySelector("[data-cid-" + componentId + "]")) return;
      if (anchor.componentId === componentId) retireAnchor(anchor);
      // An index entry whose anchor already lives under a fresh id is a
      // leftover mid-render alias; drop the entry, keep the anchor.
      else idToAnchor.delete(componentId);
    });
  };

  var anchorSweepScheduled = false;
  var scheduleAnchorSweep = function () {
    if (anchorSweepScheduled) return;
    anchorSweepScheduled = true;
    Promise.resolve().then(sweepRetiredAnchors);
  };

  // Retire the pre-enumerated ids a swap displaced, right now (never on the
  // debounced backstop: a later action in the same result must already see
  // the retirement, machinery item 4).
  var retireDepartedIds = function (departed: Set<string>) {
    departed.forEach(function (componentId) {
      if (document.querySelector("[data-cid-" + componentId + "]")) return;
      var anchor = idToAnchor.get(componentId);
      if (!anchor) return;
      if (anchor.clientAnchor && globalThis.Citry?.manager?.ownership?._isLive(anchor.clientAnchor)) {
        return;
      }
      if (anchor.componentId === componentId) retireAnchor(anchor);
      else idToAnchor.delete(componentId);
    });
  };

  // ----- recurring timers and the unsent-draft record -----

  // Machinery item 5's structure (the bindings runtime wires `@c-poll` onto
  // it): anchor-registered intervals stop when the anchor retires (see
  // `retireAnchor`), and element-keyed intervals hold one timer per
  // (element, key) so a morph survivor's timer dedupes against the fresh
  // instance's own manifest-initialized interval instead of double-polling.
  var elementIntervals = new WeakMap<Element, Map<string, number>>();
  var registerAnchorInterval = function (anchor: Anchor, intervalId: number) {
    anchor.timers.add(intervalId);
  };
  var registerElementInterval = function (el: Element, key: string, intervalId: number) {
    var slots = elementIntervals.get(el);
    if (!slots) {
      slots = new Map<string, number>();
      elementIntervals.set(el, slots);
    }
    var existing = slots.get(key);
    if (existing != null && existing !== intervalId) clearInterval(existing);
    slots.set(key, intervalId);
  };

  // Controls holding an unflushed two-way draft (typed text whose flush
  // timer is still pending, so the DOM value diverges from `$state`). The
  // forms runtime marks and clears entries; the patch-time guard below reads
  // them as one of `hasUnsentDraft`'s two draft stages (design 5.3/5.5).
  var unsentDrafts = new WeakSet<Element>();

  // ----- the patch-time preservation guard (design 5.3's hook, 5.5's block) -----

  // One decode path for the bind channel: the shared per-element cache below
  // (`decodeCevSpecs`) keeps this a lookup on the hot paths that read it per
  // morph comparison and per DOM event.
  var decodeBindSpecs = function (el: Element): StateBindingSpec[] {
    return decodeCevSpecs(el, DATA_CEV_BIND) as StateBindingSpec[];
  };

  var isTwoWayBound = function (el: Element) {
    return decodeBindSpecs(el).some(function (spec) {
      return spec != null && spec.mode === "two";
    });
  };

  var anchorForElement = function (el: Element) {
    var id = innermostComponentId(el);
    return (id && idToAnchor.get(id)) || null;
  };

  // Both draft stages (design 5.5's preservation block): the unflushed DOM
  // draft recorded by the forms runtime, and a pending unsent `$state` write
  // on a field this control two-way binds.
  var hasUnsentDraft = function (el: Element) {
    if (unsentDrafts.has(el)) return true;
    var anchor = anchorForElement(el);
    if (!anchor) return false;
    return decodeBindSpecs(el).some(function (spec) {
      return (
        spec != null &&
        spec.mode === "two" &&
        typeof spec.field === "string" &&
        Object.prototype.hasOwnProperty.call(anchor!.pending, spec.field)
      );
    });
  };

  // Keep a focused control's live value through the patch: copy it onto the
  // incoming element so the attribute sync cannot revert it, and record the
  // element so the post-patch re-apply skips it (for this control `$state`
  // still holds the pre-draft value, and re-applying it would clobber
  // exactly what this guard preserved).
  var keepLiveValue = function (el: Element, toEl: Element, guardKept: Set<Element>) {
    var live = el as HTMLInputElement;
    var incoming = toEl as HTMLInputElement;
    if (live.type === "checkbox" || live.type === "radio") {
      incoming.checked = live.checked;
      if (live.checked) incoming.setAttribute("checked", "");
      else incoming.removeAttribute("checked");
    } else if (typeof live.value === "string") {
      incoming.value = live.value;
      incoming.setAttribute("value", live.value);
    }
    guardKept.add(el);
  };

  // The morph `key` callback: a bare attribute read of the composite key
  // `#c-key` compiles to, never the plain `key` attribute. The callback is
  // hot (keyed-morph spike F-KM-8: consulted for every comparison), so it
  // must stay a pure lookup.
  var morphKeyCallback = function (el: Element) {
    return el.getAttribute && el.getAttribute("data-citry-key");
  };

  // The pinned `updating` hook (design 5.3's morph call block): the ignore
  // marker's subtree skip, and the pending-draft focused-value guard.
  var makeUpdatingHook = function (guardKept: Set<Element>) {
    return function (el: Node, toEl: Node, childrenOnly: () => void, skip: () => void) {
      if (el.nodeType !== 1) return;
      var element = el as Element;
      if (element.getAttribute("data-citry-morph") === "ignore") {
        if (element.hasAttribute("data-cid")) {
          // Skipping an instance root would leave the old component id in
          // the DOM while the fragment's manifest introduces a fresh id that
          // never lands (registry and DOM diverge), so the marker is
          // unsupported here: warn and patch normally. Put #c-ignore on an
          // element inside the child's own template below its root, or on a
          // wrapper element (design 5.3).
          console.warn(
            '[Citry] events: #c-ignore (data-citry-morph="ignore") on a component instance root is' +
              " unsupported and was not applied; move it onto an element below the root, or onto a wrapper.",
          );
        } else {
          return skip();
        }
      }
      if (element === document.activeElement && isTwoWayBound(element) && hasUnsentDraft(element)) {
        keepLiveValue(element, toEl as Element, guardKept);
      }
    };
  };

  // ----- post-patch preservation: the binding re-apply and the busy re-stamp -----

  var applyValueToControl = function (el: Element, value: unknown) {
    // Only-when-different writes: assigning an equal string to a focused
    // input's `value` is caret-safe in practice, but the equality guard makes
    // it a guarantee (and keeps the reactive application effects from
    // touching the DOM on every unrelated `$state` change).
    var control = el as HTMLInputElement;
    var nextChecked: boolean;
    var next: string;
    if (control.type === "checkbox" || control.type === "radio") {
      nextChecked = Boolean(value);
      if (control.checked !== nextChecked) control.checked = nextChecked;
    } else if (typeof control.value === "string") {
      next = value == null ? "" : String(value);
      if (control.value !== next) control.value = next;
    }
  };

  // After a patch, re-apply `:c-*` bindings from `$state` to bound controls
  // (the application a one-way binding is, design 5.5): for a field with a
  // pending unsent write, `$state` holds the preserved draft, so this
  // restores what the patch may have visually reverted; a control the
  // patch-time guard kept is exempt (its `$state` still holds the pre-draft
  // value). The re-apply is focus-independent by design.
  var reapplyBoundControls = function (roots: Element[], guardKept: Set<Element>) {
    var seen = new Set<Element>();
    roots.forEach(function (root) {
      var els: Element[] = [];
      if (root.hasAttribute("data-cev-bind")) els.push(root);
      root.querySelectorAll("[data-cev-bind]").forEach(function (el) {
        els.push(el);
      });
      els.forEach(function (el) {
        if (seen.has(el) || guardKept.has(el)) return;
        seen.add(el);
        var anchor = anchorForElement(el);
        if (!anchor || !anchor.values) return;
        decodeBindSpecs(el).forEach(function (spec) {
          if (spec == null || typeof spec.field !== "string") return;
          if (!Object.prototype.hasOwnProperty.call(anchor!.values!, spec.field)) return;
          applyValueToControl(el, anchor!.values![spec.field]);
        });
      });
    });
  };

  // Busy display carries with the loading counters (design 5.5): a linked
  // anchor still waiting on a call re-stamps `data-citry-busy` on its new
  // roots and on the triggering elements that survived the patch (the morph
  // strips client-stamped attributes from surviving elements).
  var restampBusy = function (linkedAnchors: Anchor[]) {
    linkedAnchors.forEach(function (anchor) {
      if (anchor.loading.any <= 0 || anchor.componentId == null) return;
      document.querySelectorAll("[data-cid-" + anchor.componentId + "]").forEach(function (el) {
        el.setAttribute("data-citry-busy", "");
      });
      anchor.busyTriggers.forEach(function (el) {
        if (el.isConnected) el.setAttribute("data-citry-busy", "");
      });
    });
  };

  // ----- fragment parsing (one parse per render action) -----

  /**
   * A render action's HTML, parsed once. `roots` are the component markup's
   * top-level elements (what morph pairs against); `tags` is the fragment's
   * dependency machinery, delivered after the patch: the two manifest tags
   * plus any other top-level script (the dependency pre-loader, which
   * executes on insertion and no-ops when the runtime is already present).
   */
  interface ParsedFragment {
    fragment: DocumentFragment;
    content: Node[];
    roots: Element[];
    tags: Element[];
    graphTag: HTMLScriptElement | null;
    eventsTag: HTMLScriptElement | null;
    dependencyTag: HTMLScriptElement | null;
    graphRevision: string | null;
  }

  var GRAPH_MANIFEST_SELECTOR = 'script[type="application/json"][data-citry-graph]';
  var DEPENDENCY_MANIFEST_SELECTOR = 'script[type="application/json"][data-citry]';

  var parseFragment = function (html: string): ParsedFragment {
    var template = document.createElement("template");
    template.innerHTML = html;
    var content: Node[] = [];
    var roots: Element[] = [];
    var tags: Element[] = [];
    var graphTag: HTMLScriptElement | null = null;
    var eventsTag: HTMLScriptElement | null = null;
    var dependencyTag: HTMLScriptElement | null = null;
    var graphRevision: string | null = null;
    Array.prototype.slice.call(template.content.childNodes).forEach(function (node: Node) {
      var el = node.nodeType === 1 ? (node as Element) : null;
      if (el && el.tagName === "SCRIPT") {
        if (el.matches(GRAPH_MANIFEST_SELECTOR)) {
          if (graphTag) throw new TypeError("a render fragment carries more than one ownership graph manifest");
          graphTag = el as HTMLScriptElement;
          const graph = JSON.parse(el.textContent as string) as { revision?: unknown };
          if (typeof graph.revision !== "string") throw new TypeError("an ownership graph manifest has no revision");
          graphRevision = graph.revision;
        } else if (el.matches(EVENTS_MANIFEST_SELECTOR)) {
          if (eventsTag) throw new TypeError("a render fragment carries more than one Events manifest");
          eventsTag = el as HTMLScriptElement;
        } else if (el.matches(DEPENDENCY_MANIFEST_SELECTOR)) {
          if (dependencyTag) throw new TypeError("a render fragment carries more than one dependency manifest");
          dependencyTag = el as HTMLScriptElement;
        }
        tags.push(el);
        return;
      }
      if (el) roots.push(el);
      content.push(node);
    });
    return {
      fragment: template.content,
      content: content,
      roots: roots,
      tags: tags,
      graphTag: graphTag,
      eventsTag: eventsTag,
      dependencyTag: dependencyTag,
      graphRevision: graphRevision,
    };
  };

  // Read the fragment's events manifest without marking the tag processed:
  // the applier needs the instance metadata before the swap (machinery item
  // 1), while the tag reaches the DOM unmarked so the observer's post-swap
  // pass stays the single mechanism across swap kinds (idempotent for a
  // pre-registered id: it refreshes only the token).
  interface FragmentEventsStage {
    manifest: EventsManifest | null;
    staged: StagedEventsManifest | null;
    metas: Map<string, RenderMeta>;
  }

  var readFragmentMetas = function (parsed: ParsedFragment): FragmentEventsStage {
    var metas = new Map<string, RenderMeta>();
    if (!parsed.eventsTag) return { manifest: null, staged: null, metas: metas };
    var manifest = JSON.parse(parsed.eventsTag.textContent as string) as EventsManifest;
    var staged = stageEventsManifest(manifest);
    staged.instances.forEach(function (meta) {
      metas.set(meta.componentId, {
        componentId: meta.componentId,
        classId: meta.classId,
        token: meta.token || undefined,
        values: meta.values,
      });
    });
    return { manifest: manifest, staged: staged, metas: metas };
  };

  // The caller's own metadata inside its self-render fragment: the outermost
  // instance on the fragment's first root (when one element roots a wrapper
  // and its only child, the caller's render is the outermost). Null means
  // the render carries no component (the plain-HTML branch).
  var fragmentRootMeta = function (parsed: ParsedFragment, metas: Map<string, RenderMeta>): RenderMeta | null {
    var root = parsed.roots.length ? parsed.roots[0] : null;
    if (!root) return metas.size ? Array.from(metas.values())[0] : null;
    var ids = (root.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
    var found: RenderMeta | null = null;
    ids.some(function (id) {
      var meta = metas.get(id);
      if (meta) found = meta;
      return Boolean(meta);
    });
    return found;
  };

  // ----- keyed linking (design 5.5: the one continuity mechanism on top) -----

  /** One keyed component root: the element, its composite key, and the instance the key belongs to. */
  interface KeyedRoot {
    el: Element;
    composite: string;
    instanceId: string;
  }

  /** The bookkeeping one render action threads through its regions. */
  interface RenderApplyState {
    /** Fresh ids already linked or minted by this apply (the mirror rule links once). */
    appliedIds: Set<string>;
    /** Old ids consumed by a link (the caller's, and keyed matches). */
    linkedOldIds: Set<string>;
    /** Anchors whose old index entry retires after the swap (`finishRender`). */
    pendingFinish: { anchor: Anchor; oldComponentId: string | null }[];
    /** Anchors that carried across this apply (caller + keyed links), for the busy re-stamp. */
    linkedAnchors: Anchor[];
    /** Controls whose live value the patch-time guard kept (the re-apply exemption). */
    guardKept: Set<Element>;
    /** Instance ids on or under the old regions, retired synchronously after the swap. */
    departedIds: Set<string>;
    /** Swapped-in root elements, for `citry:events:swapped` and the re-apply pass. */
    swappedEls: Element[];
  }

  // Collect the top-most keyed component roots under `containers`: elements
  // carrying the composite key attribute with a class-id scope (a plain
  // element key's empty scope pairs in morph only, never links anchors),
  // resolved to the instance the key belongs to. Keyed roots nested inside
  // another keyed root belong to that root's own nested region (the
  // recursion), so they are filtered out here.
  var collectKeyedRoots = function (
    containers: Element[],
    classOf: (id: string) => string | null,
    exclude: Set<string>,
  ): KeyedRoot[] {
    var keyedEls = new Map<Element, string>();
    var entries: KeyedRoot[] = [];
    var seenInstances = new Set<string>();
    var consider = function (el: Element) {
      if (keyedEls.has(el)) return;
      var composite = el.getAttribute("data-citry-key") || "";
      var sep = composite.indexOf(":");
      if (sep <= 0) return;
      var classId = composite.slice(0, sep);
      var ids = (el.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
      var instanceId: string | null = null;
      ids.some(function (id) {
        // The composite's scope segment is the child's class id, so the id
        // whose class matches picks the instance even on a shared root.
        if (classOf(id) === classId) instanceId = id;
        return instanceId != null;
      });
      if (instanceId == null || exclude.has(instanceId)) return;
      keyedEls.set(el, instanceId);
      if (seenInstances.has(instanceId)) return;
      // A multi-root child carries its key on every root; one entry per instance.
      seenInstances.add(instanceId);
      entries.push({ el: el, composite: composite, instanceId: instanceId });
    };
    containers.forEach(function (container) {
      if (container.hasAttribute("data-citry-key")) consider(container);
      container.querySelectorAll("[data-citry-key]").forEach(consider);
    });
    return entries.filter(function (entry) {
      var p = entry.el.parentElement;
      while (p) {
        if (keyedEls.has(p)) return false;
        p = p.parentElement;
      }
      return true;
    });
  };

  // Link one keyed pair: the same-class reconcile carries the anchor (state
  // identity, pending writes, loading counters, subscriptions) across the
  // render, and the matched subtrees become a nested region for keyed
  // grandchildren.
  var linkKeyedPair = function (
    old: KeyedRoot,
    fresh: KeyedRoot,
    metas: Map<string, RenderMeta>,
    state: RenderApplyState,
    newContainers: Element[],
  ) {
    var anchor = idToAnchor.get(old.instanceId);
    var meta = metas.get(fresh.instanceId);
    // Capture the old instance's roots before the link re-points the index;
    // they scope the nested region below.
    var oldEls: Element[] = Array.prototype.slice.call(document.querySelectorAll("[data-cid-" + old.instanceId + "]"));
    var freshEls: Element[] = [];
    newContainers.forEach(function (container) {
      if (container.hasAttribute("data-cid-" + fresh.instanceId)) freshEls.push(container);
      container.querySelectorAll("[data-cid-" + fresh.instanceId + "]").forEach(function (el) {
        freshEls.push(el);
      });
    });
    if (!anchor || anchor.componentId !== old.instanceId || !meta) {
      const ownership = globalThis.Citry?.manager?.ownership;
      if (!ownership || !ownership._correspond(old.instanceId, fresh.instanceId)) return;
      state.linkedOldIds.add(old.instanceId);
      state.appliedIds.add(fresh.instanceId);
      matchKeyedRegion(oldEls, freshEls, metas, state);
      return;
    }
    var link = linkRenderedInstance(anchor, meta);
    // The horizon cut (design 5.5): the parent's render replaced this
    // child's token with a parent-derived one, so actions from the child's
    // own in-flight calls that would replace its HTML or State token must
    // drop when their responses
    // arrive. One assignment covers them all (the guard applies only
    // strictly greater epochs), and the null owner keeps even an equal-epoch
    // response out; the calls' `data` still resolves.
    anchor.highestApplied = anchor.epoch;
    anchor.epochOwner = null;
    state.linkedOldIds.add(old.instanceId);
    state.appliedIds.add(fresh.instanceId);
    state.pendingFinish.push({ anchor: anchor, oldComponentId: link.oldComponentId });
    state.linkedAnchors.push(anchor);
    // A linked child's subtree is itself a region for its keyed grandchildren.
    matchKeyedRegion(oldEls, freshEls, metas, state);
  };

  // Match keyed component roots between the old region and the incoming
  // fragment: same class plus same composite key links (the attribute embeds
  // the class id, so one comparison covers both). Matching is swap-agnostic
  // (attributes are read on both sides before any swap), scoped per applied
  // region, and duplicates match in document order with a debug warning.
  var matchKeyedRegion = function (
    oldContainers: Element[],
    newContainers: Element[],
    metas: Map<string, RenderMeta>,
    state: RenderApplyState,
  ) {
    var oldRoots = collectKeyedRoots(
      oldContainers,
      function (id) {
        var anchor = idToAnchor.get(id);
        return anchor ? anchor.classId : globalThis.Citry?.manager?.ownership?._classForRender(id) || null;
      },
      state.linkedOldIds,
    );
    var newRoots = collectKeyedRoots(
      newContainers,
      function (id) {
        var meta = metas.get(id);
        return meta ? meta.classId : globalThis.Citry?.manager?.ownership?._classForRender(id) || null;
      },
      state.appliedIds,
    );
    if (!oldRoots.length || !newRoots.length) return;
    var oldByKey = new Map<string, KeyedRoot[]>();
    oldRoots.forEach(function (root) {
      var queue = oldByKey.get(root.composite);
      if (!queue) {
        queue = [];
        oldByKey.set(root.composite, queue);
      }
      queue.push(root);
    });
    var newCounts = new Map<string, number>();
    newRoots.forEach(function (root) {
      newCounts.set(root.composite, (newCounts.get(root.composite) || 0) + 1);
    });
    var dupWarned = new Set<string>();
    newRoots.forEach(function (fresh) {
      var queue = oldByKey.get(fresh.composite);
      if (!queue || !queue.length) return;
      if ((queue.length > 1 || (newCounts.get(fresh.composite) || 0) > 1) && !dupWarned.has(fresh.composite)) {
        dupWarned.add(fresh.composite);
        console.warn(
          "[Citry] events: duplicate key '" +
            fresh.composite +
            "' within one applied region; matched in document order." +
            " Component keys must be unique per class within a region (design 5.3).",
        );
      }
      var old = queue.shift() as KeyedRoot;
      linkKeyedPair(old, fresh, metas, state, newContainers);
    });
  };

  // A parent's `#c-key` is stamped onto the child's root elements by the
  // PARENT's render, so the child's own self-render fragment cannot carry it
  // (the key expression lives in the parent's template, out of the child's
  // reach). Losing it would wholesale-swap the root under morph (the key
  // comparison runs before any hook, so a keyed old root against an unkeyed
  // fresh root never patches in place; caret and focus die) and strip the
  // key the next parent render links by. The applier therefore carries the
  // old root's composite key across the caller's same-class render whenever
  // the fragment's own root has none.
  var preserveCallerKey = function (oldEls: Element[], caller: Anchor, freshId: string, parsed: ParsedFragment) {
    var oldKey: string | null = null;
    oldEls.some(function (el) {
      var value = el.getAttribute("data-citry-key");
      // Only the class-id-scoped form belongs to the instance itself (design
      // 5.3): an element key authored inside the child's own template
      // re-renders with the fragment and needs no carrying, and a key scoped
      // to another class must never be re-stamped across a class change.
      if (value && caller.classId != null && value.indexOf(caller.classId + ":") === 0) oldKey = value;
      return oldKey != null;
    });
    if (oldKey == null) return;
    parsed.roots.forEach(function (root) {
      if (root.hasAttribute("data-cid-" + freshId) && !root.hasAttribute("data-citry-key")) {
        root.setAttribute("data-citry-key", oldKey as string);
      }
    });
  };

  // ----- swap application -----

  /** The element children of every region element, flattened in order. */
  var childElementsOf = function (els: Element[]): Element[] {
    var children: Element[] = [];
    els.forEach(function (el) {
      Array.prototype.slice.call(el.children).forEach(function (child: Element) {
        children.push(child);
      });
    });
    return children;
  };

  // Group instance-marker elements into runs of adjacent siblings: one run
  // is a multi-root instance's root range (patched pairwise), and several
  // runs are a mirrored instance's copies (design 5.5's multi-target rule:
  // the fragment applies to each copy independently).
  var groupAdjacentRuns = function (els: Element[]): Element[][] {
    var runs: Element[][] = [];
    els.forEach(function (el) {
      var last = runs.length ? runs[runs.length - 1] : null;
      if (last && last[last.length - 1].nextElementSibling === el) last.push(el);
      else runs.push([el]);
    });
    return runs;
  };

  var collectInstanceIds = function (els: Element[], includeSelf: boolean, out: Set<string>) {
    var record = function (el: Element) {
      (el.getAttribute("data-cid") || "")
        .trim()
        .split(/\s+/)
        .filter(Boolean)
        .forEach(function (id) {
          out.add(id);
        });
    };
    els.forEach(function (el) {
      if (includeSelf && el.hasAttribute("data-cid")) record(el);
      el.querySelectorAll("[data-cid]").forEach(record);
    });
  };

  /** What a range replacement inserted: the element roots, and the very last node (the manifest-tag anchor even when the fragment is text-only). */
  interface RangeInsert {
    roots: Element[];
    lastNode: Node | null;
  }

  var OWNERSHIP_COMMENT_PREFIX = "citry:g1";
  var OWNERSHIP_COMMENT_RE = new RegExp(
    "^" + OWNERSHIP_COMMENT_PREFIX + ":([0-9a-f]{64}):(\\d+):([ir]):(\\d+):([se])$",
  );
  var OWNERSHIP_INSTANCE_START_RE = new RegExp("^(" + OWNERSHIP_COMMENT_PREFIX + ":[0-9a-f]{64}:\\d+:i:\\d+):s$");
  var OWNERSHIP_INSTANCE_CAP_RE = new RegExp("^" + OWNERSHIP_COMMENT_PREFIX + ":[0-9a-f]{64}:\\d+:i:\\d+:[se]$");

  var rewritePlacementComment = function (comment: Comment, placementId: string) {
    var match = OWNERSHIP_COMMENT_RE.exec(comment.data.trim());
    if (!match) return;
    comment.data =
      "citry:p1:" + match[1] + ":" + placementId + ":" + match[2] + ":" + match[3] + ":" + match[4] + ":" + match[5];
  };

  var cloneForPlacement = function (node: Node, placementId: string | null): Node {
    var clone = node.cloneNode(true);
    if (placementId == null) return clone;
    if (clone instanceof Comment) rewritePlacementComment(clone, placementId);
    var walker = document.createTreeWalker(clone, NodeFilter.SHOW_COMMENT);
    var comment: Node | null = walker.nextNode();
    while (comment) {
      rewritePlacementComment(comment as Comment, placementId);
      comment = walker.nextNode();
    }
    return clone;
  };

  var graphRangeInnerHtml = function (parsed: ParsedFragment, placementId: string | null) {
    var outerStart = -1;
    var outerEnd = -1;
    var outerKey = "";
    parsed.content.some(function (node, index) {
      if (!(node instanceof Comment)) return false;
      var match = OWNERSHIP_INSTANCE_START_RE.exec(node.data.trim());
      if (!match) return false;
      outerStart = index;
      outerKey = match[1];
      return true;
    });
    if (outerStart >= 0) {
      for (let index = parsed.content.length - 1; index > outerStart; index -= 1) {
        const node = parsed.content[index];
        if (node instanceof Comment && node.data.trim() === outerKey + ":e") {
          outerEnd = index;
          break;
        }
      }
    }
    var holder = document.createElement("template");
    parsed.content.forEach(function (node, index) {
      if (index === outerStart || index === outerEnd) return;
      holder.content.append(cloneForPlacement(node, placementId));
    });
    return holder.innerHTML;
  };

  // Replace a root range wholesale: insert the fragment's content before the
  // first old root, then remove the old roots.
  var replaceRange = function (
    regionEls: Element[],
    parsed: ParsedFragment,
    placementId: string | null,
    stripOuterCaps: boolean,
  ): RangeInsert {
    var first = regionEls[0];
    var parent = first.parentNode;
    if (!parent) return { roots: [], lastNode: null };
    // The guard above does not narrow inside the closure; rebind post-guard.
    var liveParent = parent;
    var inserted: Element[] = [];
    var lastNode: Node | null = null;
    parsed.content.forEach(function (node) {
      if (stripOuterCaps && node instanceof Comment && OWNERSHIP_INSTANCE_CAP_RE.test(node.data.trim())) {
        return;
      }
      var clone = cloneForPlacement(node, placementId);
      liveParent.insertBefore(clone, first);
      lastNode = clone;
      if (clone.nodeType === 1) inserted.push(clone as Element);
    });
    regionEls.forEach(function (el) {
      el.remove();
    });
    return { roots: inserted, lastNode: lastNode };
  };

  // Insert the fragment's trailing machinery tags (both manifest tags, plus
  // the dependency pre-loader script) right after `afterNode`, unmarked
  // (machinery item 2): the single-root morph call never carries them, and
  // the post-swap observer pass stays the single mechanism across swap kinds
  // (idempotent for pre-registered ids). On a multi-target render the caller
  // passes a node from the first insertion only, so the dependency manager
  // runs one teardown-and-refire cycle rather than one per copy.
  var insertManifestTags = function (parsed: ParsedFragment, afterNode: Node | null) {
    if (!afterNode || !afterNode.parentNode) return;
    var anchorNode: Node = afterNode;
    parsed.tags.forEach(function (tag) {
      if (tag === parsed.graphTag) globalThis.Citry?.manager?.ownership?._claimTag(tag);
      if (tag === parsed.eventsTag) processedEventsManifestTags.add(tag as HTMLScriptElement);
      (anchorNode.parentNode as Node).insertBefore(tag, anchorNode.nextSibling);
      anchorNode = tag;
    });
  };

  // Apply the parsed fragment to one region with the given swap strategy.
  // Content nodes are cloned per region, so a mirrored instance's copies do
  // not steal nodes from each other; the manifest tags ride only the first
  // insertion.
  var applyFragmentToRegion = function (
    regionEls: Element[],
    parsed: ParsedFragment,
    swap: string,
    state: RenderApplyState,
    firstInsertion: boolean,
    placementId: string | null,
    stripOuterCaps: boolean,
  ) {
    var updating = makeUpdatingHook(state.guardKept);
    var insertedRoots: Element[] = [];
    var lastNode: Node | null = null;
    var rangeInsert: RangeInsert;

    if (swap === "morph") {
      if (parsed.graphRevision != null && !stripOuterCaps) {
        // A selector-targeted graph owns its outer caps too. It is a fresh
        // positional region, so land the validated complete range while the
        // precomputed keyed correspondences preserve only selected logical
        // children.
        rangeInsert = replaceRange(regionEls, parsed, placementId, false);
        insertedRoots = rangeInsert.roots;
        lastNode = rangeInsert.lastNode;
      } else if (regionEls.length === parsed.roots.length && parsed.roots.length > 0) {
        // Pairwise, root by root (design 5.3), while the counts match.
        regionEls.forEach(function (oldRoot, index) {
          var parent = oldRoot.parentNode;
          var prev = oldRoot.previousSibling;
          // Morph mutates its `to` element (id seeding, holdovers), so each
          // call gets its own clone of the parsed root.
          alpineRuntime._morph(oldRoot, cloneForPlacement(parsed.roots[index], placementId) as Element, {
            key: morphKeyCallback,
            updating: updating,
          });
          // Re-resolve by position: an in-place patch kept the node, a
          // wholesale swap left a replacement at the same spot.
          var landed = prev ? prev.nextSibling : parent ? parent.firstChild : null;
          if (landed && landed.nodeType === 1) insertedRoots.push(landed as Element);
        });
        lastNode = insertedRoots.length ? insertedRoots[insertedRoots.length - 1] : null;
      } else {
        // Root counts differ: fall back to replacing the whole range (5.3).
        rangeInsert = replaceRange(regionEls, parsed, placementId, stripOuterCaps);
        insertedRoots = rangeInsert.roots;
        lastNode = rangeInsert.lastNode;
      }
    } else if (swap === "replace") {
      rangeInsert = replaceRange(regionEls, parsed, placementId, stripOuterCaps);
      insertedRoots = rangeInsert.roots;
      lastNode = rangeInsert.lastNode;
    } else if (swap === "inner") {
      regionEls.forEach(function (el) {
        while (el.firstChild) el.removeChild(el.firstChild);
        parsed.content.forEach(function (node) {
          var clone = cloneForPlacement(node, placementId);
          el.appendChild(clone);
          if (clone.nodeType === 1) insertedRoots.push(clone as Element);
        });
        if (lastNode == null) lastNode = el.lastChild;
      });
    } else if (swap === "append" || swap === "prepend") {
      regionEls.forEach(function (el) {
        var before = swap === "prepend" ? el.firstChild : null;
        var lastClone: Node | null = null;
        parsed.content.forEach(function (node) {
          var clone = cloneForPlacement(node, placementId);
          el.insertBefore(clone, before);
          lastClone = clone;
          if (clone.nodeType === 1) insertedRoots.push(clone as Element);
        });
        if (lastNode == null) lastNode = lastClone;
      });
    } else {
      // An unknown swap strategy: the envelope negotiation keeps the server
      // inside the advertised set, so this is a public applyActions caller
      // (or a future minor); skip rather than throw.
      console.warn("[Citry] events: unknown swap strategy '" + swap + "'; the render was skipped.");
      return;
    }

    if (firstInsertion) insertManifestTags(parsed, lastNode);
    insertedRoots.forEach(function (el) {
      state.swappedEls.push(el);
    });
  };

  // ----- the epoch guard at apply time (design 4.2, 5.5) -----

  // Instance-mutating actions apply iff the response's epoch is strictly
  // greater than the anchor's highest-applied. A response's own epoch
  // becomes the highest applied the moment it applies, so a later action of
  // the same response (equal epoch, same owner token) still applies, while
  // the horizon cut's null owner drops every in-flight response at once.
  var epochAllowsApply = function (run: ApplyRun, targetAnchor: Anchor) {
    if (run.anchor !== targetAnchor || typeof run.epoch !== "number") return true;
    if (run.epoch > targetAnchor.highestApplied) return true;
    return run.epoch === targetAnchor.highestApplied && targetAnchor.epochOwner === run.token;
  };

  var markEpochApplied = function (run: ApplyRun, targetAnchor: Anchor) {
    if (run.anchor !== targetAnchor || typeof run.epoch !== "number") return;
    targetAnchor.highestApplied = run.epoch;
    targetAnchor.epochOwner = run.token;
  };

  // A stale response's caller-changing actions drop; the drop event fires
  // once per result (the drop is result-scoped), each dropped action leaves
  // a debug line.
  var dropStaleEpoch = function (run: ApplyRun, what: string) {
    if (!run.staleEventFired) {
      run.staleEventFired = true;
      fireStale(run.anchor, run.event, "epoch");
    }
    console.debug(
      "[Citry] events: dropped " +
        what +
        " of a stale response (epoch " +
        run.epoch +
        ", highest applied " +
        (run.anchor ? run.anchor.highestApplied : "?") +
        ").",
    );
  };

  var dropRetired = function (run: ApplyRun, what: string) {
    fireStale(run.anchor, run.event, "retired");
    console.debug("[Citry] events: dropped " + what + " (the instance retired, design 5.5 machinery item 4).");
  };

  // ----- the actions applier (design 4.3, 5.5) -----

  var applyStateAction = function (action: ResultAction, run: ApplyRun) {
    var instanceId = typeof action.targetRenderId === "string" ? action.targetRenderId : "";
    if (instanceId && !isSafeRenderId(instanceId)) {
      console.warn("[Citry] events: state action carried an unsafe render ID '" + instanceId + "'; skipped.");
      return;
    }
    // Self-addressed refreshes follow the caller's anchor (correlation
    // routing, design 5.5): a keyed link may have re-minted the id while
    // this response was in flight, and the epoch guard below (with the
    // horizon cut's owner reset) is what decides staleness, not the id.
    var anchor: Anchor | null;
    if (instanceId && run.anchor != null && (run.instance === instanceId || run.anchor.componentId === instanceId)) {
      anchor = run.anchor;
    } else {
      anchor = instanceId ? idToAnchor.get(instanceId) || null : null;
    }
    if (!anchor || anchor.componentId == null) {
      dropRetired(run, "a state token refresh for instance '" + instanceId + "'");
      return;
    }
    if (!epochAllowsApply(run, anchor)) {
      dropStaleEpoch(run, "a state token refresh");
      return;
    }
    if (typeof action.stateToken === "string" && action.stateToken) anchor.token = action.stateToken;
    markEpochApplied(run, anchor);
  };

  var applyEventAction = function (action: ResultAction, run: ApplyRun) {
    var name = typeof action.eventName === "string" ? action.eventName : "";
    if (!name) {
      console.warn("[Citry] events: an event action carried no name; skipped.");
      return;
    }
    var makeEvent = function () {
      return new CustomEvent(name, { detail: action.detail, bubbles: true });
    };
    var targetSpec = typeof action.target === "string" ? action.target : "";
    var id: string;
    var root: Element | null;
    if (!targetSpec) {
      // An instance-less call's dispatch (design 4.3): document-targeted.
      document.dispatchEvent(makeEvent());
      return;
    }
    if (targetSpec.indexOf("render:") === 0) {
      id = targetSpec.slice(7);
      if (!isSafeRenderId(id)) {
        console.warn("[Citry] events: event action carried an unsafe render ID '" + id + "'; skipped.");
        return;
      }
      if (run.anchor != null && (run.instance === id || run.anchor.componentId === id)) {
        // Caller-targeted: follow the caller's anchor to its current canonical root
        // (a keyed link re-mints the id while a response is in flight, and
        // the linked instance must still hear its toasts, design 5.5).
        if (run.anchor.componentId == null) {
          dropRetired(run, "an event dispatch ('" + name + "') for instance '" + id + "'");
          return;
        }
        id = run.anchor.componentId;
      }
      root = document.querySelector("[data-cid-" + id + "]");
      if (!root) {
        // An event on a dead id drops rather than falling back to a document
        // dispatch, which would change delivery semantics silently
        // (machinery item 4).
        dropRetired(run, "an event dispatch ('" + name + "') for instance '" + id + "'");
        return;
      }
      root.dispatchEvent(makeEvent());
      return;
    }
    var els = queryTargets(targetSpec);
    if (els == null) return;
    if (!els.length) {
      console.warn("[Citry] events: event target '" + targetSpec + "' matched nothing; the dispatch was skipped.");
      return;
    }
    els.forEach(function (el) {
      el.dispatchEvent(makeEvent());
    });
  };

  var queryTargets = function (selector: string): Element[] | null {
    try {
      return Array.prototype.slice.call(document.querySelectorAll(selector));
    } catch (err) {
      console.warn("[Citry] events: invalid target selector '" + selector + "':", err);
      return null;
    }
  };

  var applyRenderAction = function (action: ResultAction, run: ApplyRun) {
    var targetSpec = typeof action.target === "string" ? action.target : "";
    var swap = typeof action.swap === "string" && action.swap ? action.swap : "morph";
    if (!targetSpec) {
      console.warn("[Citry] events: a render action carried no target; skipped.");
      return;
    }

    // Resolve the target at apply time, never at response arrival (design
    // 4.3's timing-fields rule; scheduled actions re-enter here at fire time).
    var isInstanceTarget = targetSpec.indexOf("render:") === 0;
    var targetEls: Element[];
    var targetAnchor: Anchor | null = null;
    var rootlessInstanceTarget = false;
    var targetId: string;
    var liveTargetId: string | null;
    var matched: Element[] | null;
    var removed: Set<string>;
    var caller: Anchor;
    var callerMeta: RenderMeta | null;
    var callerLink: RenderLink;
    if (isInstanceTarget) {
      targetId = targetSpec.slice(7);
      if (!isSafeRenderId(targetId)) {
        console.warn("[Citry] events: render action carried an unsafe cid render ID '" + targetId + "'; skipped.");
        return;
      }
      if (run.anchor != null && (run.instance === targetId || run.anchor.componentId === targetId)) {
        // Self-addressed: the wire names the caller's send-time id, and the
        // response routes to the caller's anchor by correlation (design
        // 5.5), so the render follows the anchor even when a keyed link
        // re-minted the id while this response was in flight (the epoch
        // guard below, with the horizon cut, decides staleness).
        targetAnchor = run.anchor;
      } else {
        // A render: target of another instance. It may be non-interactive (no
        // anchor): liveness is element existence, not registry membership.
        targetAnchor = idToAnchor.get(targetId) || null;
      }
      liveTargetId = targetAnchor != null ? targetAnchor.componentId : targetId;
      targetEls =
        liveTargetId == null
          ? []
          : Array.prototype.slice.call(document.querySelectorAll("[data-cid-" + liveTargetId + "]"));
      if (!targetEls.length) {
        const targetOwnership = globalThis.Citry?.manager?.ownership;
        if (targetAnchor?.clientAnchor && targetOwnership?._hasPlacements(targetAnchor.clientAnchor)) {
          rootlessInstanceTarget = true;
        } else {
          // Instance-addressed liveness (machinery item 4): an earlier action
          // in this result, an earlier result in this envelope, or a host
          // removal retired the target.
          dropRetired(run, "a render for instance '" + targetId + "'");
          return;
        }
      }
    } else {
      matched = queryTargets(targetSpec);
      if (matched == null) return;
      if (!matched.length) {
        // A plain selector is never live or dead: the zero-match warning is
        // its whole surface (design 4.3).
        console.warn("[Citry] events: render target '" + targetSpec + "' matched nothing; the action was skipped.");
        return;
      }
      targetEls = matched;
    }

    var selfRender = run.anchor != null && targetAnchor === run.anchor;
    if (swap === "none") {
      if (selfRender) {
        if (!epochAllowsApply(run, run.anchor as Anchor)) {
          dropStaleEpoch(run, "a self-render");
          return;
        }
        markEpochApplied(run, run.anchor as Anchor);
      }
      return;
    }
    if (swap === "remove") {
      if (selfRender) {
        if (!epochAllowsApply(run, run.anchor as Anchor)) {
          dropStaleEpoch(run, "a self-render");
          return;
        }
        markEpochApplied(run, run.anchor as Anchor);
      }
      removed = new Set<string>();
      collectInstanceIds(targetEls, true, removed);
      targetEls.forEach(function (el) {
        el.remove();
      });
      retireDepartedIds(removed);
      fireLifecycle("citry:events:swapped", run.anchor, run.event, { els: [] });
      scheduleAnchorSweep();
      return;
    }

    // A stale self result is rejected before its untrusted fragment is even
    // parsed or reserves a provisional graph. The same guard runs again after
    // detached validation, immediately before the epoch is committed.
    if (selfRender && !epochAllowsApply(run, run.anchor as Anchor)) {
      dropStaleEpoch(run, "a self-render");
      return;
    }

    var parsed = parseFragment(typeof action.html === "string" ? action.html : "");
    var ownership = globalThis.Citry?.manager?.ownership;
    var ownershipTransaction: unknown = null;
    var adoptionRoot: { componentId: string; classId: string } | null = null;
    var dependencyManifest: unknown = null;
    var priorClasses: { classId: string; had: boolean; descriptor: ClassDescriptor | undefined }[] = [];
    var fragmentEvents: FragmentEventsStage;
    try {
      if (parsed.graphTag) {
        if (!ownership) throw new Error("the ownership graph registry is unavailable");
        ownershipTransaction = ownership._prepareAdoption(
          JSON.parse(parsed.graphTag.textContent as string),
          parsed.fragment,
        );
        adoptionRoot = ownership._adoptionRoot(ownershipTransaction);
      }
      fragmentEvents = readFragmentMetas(parsed);
      if (parsed.graphRevision != null) {
        if (fragmentEvents.manifest && fragmentEvents.manifest.clientGraphRevision !== parsed.graphRevision) {
          throw new TypeError("a graph-backed Events manifest must link to the same ownership revision");
        }
        if (fragmentEvents.staged) {
          ownership!._preflightEvents(parsed.graphRevision, fragmentEvents.staged.instances);
        }
      } else if (fragmentEvents.manifest?.clientGraphRevision) {
        throw new TypeError("an Events manifest refers to an ownership graph absent from the render fragment");
      }
      if (parsed.dependencyTag) {
        const dependency = JSON.parse(parsed.dependencyTag.textContent as string) as { graph?: unknown };
        dependencyManifest = dependency;
        if (parsed.graphRevision != null && dependency.graph !== parsed.graphRevision) {
          throw new TypeError("a dependency manifest is not linked to the render fragment's ownership revision");
        }
        if (parsed.graphRevision == null && dependency.graph != null) {
          throw new TypeError("a dependency manifest refers to an ownership graph absent from the render fragment");
        }
        if (parsed.graphRevision != null) {
          dependencyManifest = ownership!._preflightDependency(dependency, parsed.graphRevision);
        }
      }
    } catch (err) {
      if (ownershipTransaction && ownership) ownership._abortAdoption(ownershipTransaction, err);
      else if (parsed.graphRevision && ownership) ownership._rejectAdoption(parsed.graphRevision, err);
      throw err;
    }

    try {
      // The epoch is consumed only after the whole detached package validates.
      if (selfRender) {
        if (!epochAllowsApply(run, run.anchor as Anchor)) {
          if (ownershipTransaction && ownership) {
            ownership._abortAdoption(
              ownershipTransaction,
              new Error("the incoming render became stale before adoption"),
            );
          }
          dropStaleEpoch(run, "a self-render");
          return;
        }
        markEpochApplied(run, run.anchor as Anchor);
      }

      const metas = fragmentEvents.metas;
      if (fragmentEvents.staged) {
        fragmentEvents.staged.classes.forEach(function (entry) {
          priorClasses.push({ classId: entry[0], had: classes.has(entry[0]), descriptor: classes.get(entry[0]) });
        });
        installClassDescriptors(fragmentEvents.staged.classes);
      }
      // The outer range stays outside the root list and is transferred by the
      // ownership transaction, including every runtime mirror placement. Nested
      // caps participate in the root morph so compatible keyed child ranges can
      // keep their physical Comment nodes while adopting the incoming markers.
      const state: RenderApplyState = {
        appliedIds: new Set<string>(),
        linkedOldIds: new Set<string>(),
        pendingFinish: [],
        linkedAnchors: [],
        guardKept: new Set<Element>(),
        departedIds: new Set<string>(),
        swappedEls: [],
      };
      // Capture the currently-live physical placements before the
      // self-render correspondence transfers the stable anchor to the
      // provisional incoming revision. After that transfer the graph lookup
      // correctly names the incoming logical instance, but the DOM regions
      // this action must patch are still the outgoing placements.
      const graphTargetRegions =
        isInstanceTarget && !rootlessInstanceTarget && ownership && targetAnchor?.clientAnchor
          ? ownership._placementRoots(targetAnchor.clientAnchor)
          : null;

      // The correlated caller's own render takes the three-way split (design
      // 5.5): same class reconciles, a different class adopts wholesale, plain
      // HTML retires the anchor. Everything else in the fragment follows the
      // uncorrelated-id rule below. The split is the property of swaps that
      // replace the caller's rendering; an insert-style self-target (inner,
      // append, prepend) only adds content, so its fragment ids are all
      // uncorrelated.
      if (selfRender && (swap === "morph" || swap === "replace")) {
        caller = run.anchor as Anchor;
        callerMeta = fragmentRootMeta(parsed, metas);
        if (caller.componentId != null) state.linkedOldIds.add(caller.componentId);
        if (callerMeta) state.appliedIds.add(callerMeta.componentId);
        if (!callerMeta && adoptionRoot && caller.clientAnchor && ownership) {
          if (adoptionRoot.classId === caller.classId) {
            preserveCallerKey(targetEls, caller, adoptionRoot.componentId, parsed);
          }
          const oldComponentId = caller.componentId;
          ownership._transitionEvents(caller.clientAnchor, adoptionRoot.componentId, adoptionRoot.classId);
          retireAnchor(caller, true);
          callerLink = { branch: "general-only", oldComponentId: oldComponentId };
        } else {
          callerLink = linkRenderedInstance(caller, callerMeta);
        }
        if (callerLink.branch === "reconcile" || callerLink.branch === "adopt") {
          state.pendingFinish.push({ anchor: caller, oldComponentId: callerLink.oldComponentId });
          state.linkedAnchors.push(caller);
        }
        if (callerLink.branch === "reconcile" && callerMeta != null) {
          preserveCallerKey(targetEls, caller, callerMeta.componentId, parsed);
        }
      }

      // One region per selector match (all-matches, design 4.3), or one per
      // graph physical placement for an instance target. Placement caps,
      // not sibling adjacency, distinguish adjacent mirror copies from one
      // multi-root placement; adjacency remains only the legacy fallback.
      const regions = rootlessInstanceTarget
        ? ownership && targetAnchor?.clientAnchor
          ? ownership._placementIds(targetAnchor.clientAnchor).map(function () {
              return [] as Element[];
            })
          : []
        : isInstanceTarget
          ? graphTargetRegions
            ? graphTargetRegions
            : groupAdjacentRuns(targetEls)
          : targetEls.map(function (el) {
              return [el];
            });

      regions.forEach(function (regionEls) {
        // Pre-enumerate the ids this swap displaces; they retire synchronously
        // after the swap (machinery items 3 and 4).
        if (swap === "inner") collectInstanceIds(regionEls, false, state.departedIds);
        else if (swap === "morph" || swap === "replace") collectInstanceIds(regionEls, true, state.departedIds);
        if (rootlessInstanceTarget && liveTargetId != null && (swap === "morph" || swap === "replace")) {
          state.departedIds.add(liveTargetId);
        }

        // Link before the swap, generalized to every id in the fragment
        // (machinery item 1): keyed matches link (with the horizon cut), and
        // every other fresh id mints its anchor, so every `$state` read the
        // morph's Alpine bridge evaluates mid-patch resolves to real state.
        // The old side of the match is what the swap replaces: the region
        // elements themselves, or under `inner` their content (the container
        // survives an inner swap, so it never departs and never links).
        if (swap === "morph" || swap === "replace" || swap === "inner") {
          matchKeyedRegion(swap === "inner" ? childElementsOf(regionEls) : regionEls, parsed.roots, metas, state);
        }
      });
      if (ownershipTransaction && ownership) {
        ownership._expectRetirement(Array.from(state.departedIds));
      }
      metas.forEach(function (meta, componentId) {
        if (state.appliedIds.has(componentId) || idToAnchor.has(componentId)) return;
        createAnchor(componentId, meta.classId, meta.token || "", meta.values || {});
        state.appliedIds.add(componentId);
      });

      if (parsed.graphRevision != null && fragmentEvents.staged && ownership) {
        const liveOwnership = ownership;
        fragmentEvents.staged.instances.forEach(function (meta) {
          var eventsAnchor = idToAnchor.get(meta.componentId);
          if (!eventsAnchor) throw new TypeError("a staged Events instance has no prepared anchor");
          eventsAnchor.clientAnchor = liveOwnership._attachEvents(
            parsed.graphRevision as string,
            meta.componentId,
            meta.classId,
            eventsAnchor,
          );
        });
      }
      if (ownershipTransaction && ownership) ownership._activateAdoption(ownershipTransaction);

      const placementIds: (string | null)[] = [];
      if (parsed.graphRevision != null && ownership) {
        const placementOwnership = ownership;
        const existingPlacements =
          isInstanceTarget && targetAnchor?.clientAnchor
            ? placementOwnership._placementIds(targetAnchor.clientAnchor)
            : [];
        regions.forEach(function (_region, index) {
          placementIds.push(existingPlacements[index] ?? (index === 0 ? null : placementOwnership._mintPlacement()));
        });
      } else {
        regions.forEach(function () {
          placementIds.push(null);
        });
      }

      regions.forEach(function (regionEls, index) {
        var stripOuterCaps =
          parsed.graphRevision != null && isInstanceTarget && (swap === "morph" || swap === "replace");
        if (rootlessInstanceTarget && ownership && targetAnchor?.clientAnchor) {
          const physical = ownership._morphPlacement(
            targetAnchor.clientAnchor,
            index,
            graphRangeInnerHtml(parsed, placementIds[index]),
          );
          if (index === 0) insertManifestTags(parsed, physical.end);
          return;
        }
        applyFragmentToRegion(regionEls, parsed, swap, state, index === 0, placementIds[index], stripOuterCaps);
      });

      let adoptionReady: Promise<void> = Promise.resolve();
      if (ownershipTransaction && ownership) {
        ownership._commitAdoption(ownershipTransaction);
        consumedOwnershipRevisions.add(parsed.graphRevision as string);
        if (parsed.dependencyTag && dependencyManifest) {
          adoptionReady = ownership._applyDependency(ownershipTransaction, dependencyManifest, parsed.dependencyTag);
        }
      }

      // The post-swap half: retire the old index entries the patch no longer
      // needs, then the departed ids (synchronously: a later action in this
      // result must already see the retirement).
      state.pendingFinish.forEach(function (pending) {
        finishRender(pending.anchor, pending.oldComponentId);
      });
      retireDepartedIds(state.departedIds);

      // Preservation (design 5.5): re-apply bound controls from `$state`
      // (guard-kept controls exempt), and re-stamp busy display for linked
      // anchors still waiting on a call.
      reapplyBoundControls(state.swappedEls, state.guardKept);
      restampBusy(state.linkedAnchors);

      if (fragmentEvents.staged) {
        // Pre-staging changed the gates before Alpine's morph evaluation but
        // deliberately left pending data untouched for rollback. Once the
        // render has committed, discard drafts the new contract forbids
        // before a swapped-event listener can initiate another send.
        const committedClassIds = new Set<string>();
        fragmentEvents.staged.classes.forEach(function (entry) {
          committedClassIds.add(entry[0]);
        });
        refreshAnchorsForClasses(committedClassIds, true);
      }
      fireLifecycle("citry:events:swapped", run.anchor, run.event, { els: state.swappedEls.slice() });
      scheduleAnchorSweep();
      return adoptionReady;
    } catch (err) {
      const restoredClassIds = new Set<string>();
      priorClasses.forEach(function (entry) {
        if (entry.had) classes.set(entry.classId, entry.descriptor as ClassDescriptor);
        else classes.delete(entry.classId);
        restoredClassIds.add(entry.classId);
      });
      refreshAnchorsForClasses(restoredClassIds);
      if (ownershipTransaction && ownership) ownership._abortAdoption(ownershipTransaction, err);
      parsed.tags.forEach(function (tag) {
        ownership?._claimTag(tag);
        if (tag.isConnected) tag.remove();
      });
      if (fragmentEvents?.staged) {
        fragmentEvents.staged.instances.forEach(function (meta) {
          var failedAnchor = idToAnchor.get(meta.componentId);
          if (failedAnchor && failedAnchor !== run.anchor) retireAnchor(failedAnchor);
        });
      }
      if (selfRender && run.anchor && run.anchor.componentId != null) retireAnchor(run.anchor);
      targetEls.forEach(function (element) {
        if (element.isConnected) element.remove();
      });
      scheduleAnchorSweep();
      throw err;
    }
  };

  var applyUrlAction = function (action: ResultAction) {
    var url = typeof action.url === "string" ? action.url : "";
    if (!url || (action.mode !== "push" && action.mode !== "replace")) {
      console.warn(
        "[Citry] events: invalid url action skipped; expected a non-empty url and mode 'push' or 'replace'.",
      );
      return;
    }
    try {
      // Citry owns the address change, not the entry's application data.
      // Preserve state held by a router or another library.
      if (action.mode === "replace") history.replaceState(history.state, "", url);
      else history.pushState(history.state, "", url);
    } catch (err) {
      console.warn("[Citry] events: could not apply a url action for '" + url + "':", err);
    }
  };

  // Apply one action, resolving its target and re-checking liveness and the
  // epoch comparison now (immediate actions run inline; scheduled actions
  // re-enter here at fire time, design 4.3).
  var applyOneAction = function (action: ResultAction, run: ApplyRun) {
    var kind = action.action;
    if (kind === "render") return applyRenderAction(action, run);
    else if (kind === "data") {
      // The caller's promise resolves whatever else dropped (the R3 settle
      // table): liveness never gates `data`.
      if (run.onData) run.onData(action.value);
    } else if (kind === "state") applyStateAction(action, run);
    else if (kind === "event") applyEventAction(action, run);
    else if (kind === "redirect") {
      // Applied in place when reached; later actions still apply and merely
      // race the navigation (design 4.3: the client never drops or reorders).
      if (typeof action.url === "string" && action.url) window.location.assign(action.url);
    } else if (kind === "url") applyUrlAction(action);
    else {
      // Every transport and public-API entry point validates the complete
      // action array before application, so reaching this branch is an
      // internal contract violation rather than an extensibility hook.
      throw new TypeError("events action reached application without citry-events/1 validation");
    }
  };

  // Apply one result's actions array in faithful list order (design 4.3):
  // nothing is reordered or dropped, `delay` with the default `wait: true`
  // blocks the sequence, and `wait: false` schedules the action while later
  // actions proceed. A scheduled action re-resolves its target and re-runs
  // the liveness and epoch checks when it fires, not when its response
  // arrived.
  var applyActionsList = function (actions: ResultAction[], run: ApplyRun): Promise<void> {
    // A result's token refresh reaches the registry before the actions array
    // runs (design 4.3), so user code running mid-application (a dispatch
    // listener that immediately sends) already carries the fresh token.
    // Scheduled state actions keep their authored timing.
    var hoisted = new Set<number>();
    actions.forEach(function (action, index) {
      if (
        action != null &&
        action.action === "state" &&
        !(typeof action.delay === "number" && action.delay > 0) &&
        action.wait !== false
      ) {
        applyStateAction(action, run);
        hoisted.add(index);
      }
    });

    var chain: Promise<void> = Promise.resolve();
    actions.forEach(function (action, index) {
      if (action == null || typeof action !== "object" || hoisted.has(index)) return;
      var delayMs = typeof action.delay === "number" && action.delay > 0 ? action.delay * 1000 : 0;
      if (action.wait === false) {
        setTimeout(function () {
          try {
            Promise.resolve(applyOneAction(action, run)).catch(function (err) {
              console.error("[Citry] events: applying a scheduled action failed:", err);
            });
          } catch (err) {
            console.error("[Citry] events: applying a scheduled action failed:", err);
          }
        }, delayMs);
        return;
      }
      chain = chain.then(function () {
        if (!delayMs) {
          return applyOneAction(action, run);
        }
        return new Promise<void>(function (resolve) {
          setTimeout(resolve, delayMs);
        }).then(function () {
          return applyOneAction(action, run);
        });
      });
    });
    return chain;
  };

  // Apply one result envelope entry. The context ties the result to its
  // caller: the anchor the correlation id routed to (never a component id,
  // design 5.5), the event name for lifecycle details, and the transport's
  // `data` hook. Error results carry no actions; the transport layer owns
  // their rejection surface.
  var applyResult = function (result: ResultEntry, ctx?: ApplyContext | null): Promise<void> {
    if (!result || result.ok !== true || !Array.isArray(result.actions)) return Promise.resolve();
    var run: ApplyRun = {
      anchor: (ctx && ctx.anchor) || null,
      instance: (ctx && ctx.instance) || null,
      event: (ctx && ctx.event) || null,
      onData: (ctx && ctx.onData) || null,
      epoch: result && typeof result.sendSequence === "number" ? result.sendSequence : null,
      token: {},
      staleEventFired: false,
    };
    return applyActionsList(result.actions, run);
  };

  // Apply a whole results envelope in order, awaiting each result: liveness
  // spans results, so an earlier result's render retires a later result's
  // caller within one batch envelope (machinery item 4).
  var applyEnvelope = function (results: ResultEntry[], ctxs?: (ApplyContext | null)[] | null): Promise<void> {
    var chain: Promise<void> = Promise.resolve();
    (Array.isArray(results) ? results : []).forEach(function (result, index) {
      chain = chain.then(function () {
        return applyResult(result, ctxs ? ctxs[index] : null);
      });
    });
    return chain;
  };

  // ----- the magics -----

  alpineRuntime._magic("state", function (el) {
    var anchor = resolveAnchor(el, "state");
    return anchor ? anchor.stateProxy : INERT_STATE;
  });

  alpineRuntime._magic("loading", function (el) {
    var anchor = resolveAnchor(el, "loading");
    if (!anchor)
      return function () {
        return false;
      };
    // The assertions re-state the guard above: the checker does not carry
    // the narrowing into the returned closure. Same pattern in the other
    // magics and the payload decorator below.
    return function (name?: string) {
      if (name === undefined) return anchor!.loading.any > 0;
      requireDeclaredEvent(anchor!, name, "$loading");
      return (anchor!.loading.handlers[name] || 0) > 0;
    };
  });

  alpineRuntime._magic("error", function (el) {
    var anchor = resolveAnchor(el, "error");
    return anchor ? anchor.errorBox.current : null;
  });

  alpineRuntime._magic("sendEvent", function (el) {
    var anchor = resolveAnchor(el, "sendEvent");
    if (!anchor) {
      return function (name: string) {
        return Promise.reject(
          pointedError(
            "this element's component instance is not registered (a re-render may be mid-flight);" +
              " $sendEvent('" +
              name +
              "') was not sent.",
          ),
        );
      };
    }
    // The expression's element is the dispatching element (design 5.6): the
    // queue's containment walk, the per-trigger busy stamp, and fire-time
    // re-resolution all start from it.
    var dispatchingEl = el && (el as MaybeElement).nodeType === 1 ? (el as Element) : null;
    var projectedOwner = projectedComponentId(dispatchingEl);
    return function (name: string, args?: Record<string, unknown>, opts?: unknown) {
      var promise: Promise<unknown> | null;
      if (projectedOwner !== undefined) {
        if (projectedOwner === null) {
          return Promise.reject(pointedError("$sendEvent cannot send because its fill has no live lexical source."));
        }
        promise = sendSourceOwned(projectedOwner, name, args || null, opts, dispatchingEl, function () {
          return projectedComponentId(dispatchingEl) === projectedOwner;
        });
        return promise || Promise.reject(pointedError("$sendEvent source retired before the call could be queued."));
      }
      return sendFromAnchor(anchor!, name, args, opts, dispatchingEl);
    };
  });

  alpineRuntime._magic("onEvent", function (el) {
    var anchor = resolveAnchor(el, "onEvent");
    // In the mid-morph gap a subscription has no instance to bind to; an
    // inert unsubscribe keeps the expression from throwing, matching $state.
    if (!anchor)
      return function () {
        return function () {};
      };
    return function (name: string, fn: EventCallback) {
      return subscribeForAnchor(anchor!, name, fn);
    };
  });

  // ----- the event bindings: delegated listeners and @c-poll timers (design 5.1, 5.5, 5.6) -----

  // The compiled `data-cev-*` specs this layer reads are the WP12-published
  // contract documented in the Python bindings module
  // (`citry/ext/events/bindings.py`): each attribute value is standard base64
  // of UTF-8 JSON, and the decoded value is an array of spec objects.
  var DATA_CEV_ON = "data-cev-on";
  var DATA_CEV_POLL = "data-cev-poll";
  var DATA_CEV_BIND = "data-cev-bind";

  // Decoding is cached per element on the raw attribute string, so the
  // event-time read stays a lookup while a morph that rewrites the attribute
  // still re-decodes.
  var cevSpecCache = new WeakMap<Element, Map<string, { raw: string; specs: unknown[] }>>();

  var decodeCevSpecs = function (el: Element, attrName: string): unknown[] {
    var raw = el.getAttribute(attrName);
    var parsed: unknown;
    if (!raw) return [];
    var perAttr = cevSpecCache.get(el);
    if (!perAttr) {
      perAttr = new Map<string, { raw: string; specs: unknown[] }>();
      cevSpecCache.set(el, perAttr);
    }
    var cached = perAttr.get(attrName);
    if (cached && cached.raw === raw) return cached.specs;
    var specs: unknown[] = [];
    try {
      parsed = JSON.parse(fromBase64(raw));
      if (Array.isArray(parsed)) specs = parsed;
    } catch (err) {
      console.error("[Citry] events: failed to decode a " + attrName + " spec:", err);
    }
    perAttr.set(attrName, { raw: raw, specs: specs });
    return specs;
  };

  // Evaluate a binding's authored argument expression as an ordinary Alpine
  // expression bound to the owning element (design 5.1: it sees `$state`,
  // `$el`, `$event`, and any user scope in play; citry never parses it). The
  // result's keys become the wire args payload, so anything but an object is
  // the author's bug: the pointed error names the binding.
  var evaluateBindingArgs = function (
    el: Element,
    bindingName: string,
    handler: string,
    expression: string,
    event: Event | null,
  ): Record<string, unknown> {
    var scope: Record<string, unknown> = {};
    var got: string;
    if (event) scope.$event = event;
    // The added parentheses make `{...}` parse as an object literal, exactly
    // as it read between the binding's own parentheses in the template.
    var result = Alpine.evaluate(el, "(" + expression + ")", { scope: scope });
    if (result == null || typeof result !== "object" || Array.isArray(result)) {
      got =
        result === null
          ? "null"
          : result === undefined
            ? "undefined"
            : Array.isArray(result)
              ? "an array"
              : "a " + typeof result;
      throw pointedError(
        "the argument expression of the '" +
          bindingName +
          "' binding for handler '" +
          handler +
          "' must evaluate to an object (its keys become the event's args); got " +
          got +
          ": (" +
          expression +
          ")",
      );
    }
    return result as Record<string, unknown>;
  };

  // A binding's effective debounce/throttle in milliseconds: the spec's own
  // value (the server-side rewrite already merges the `@event(debounce=...)`
  // handler default into it), with the class descriptor's per-event value as
  // the fallback for a spec that carries none. Serves the event channel and
  // the two-way state channel alike (both carry the same timing keys).
  var bindingTimingMs = function (
    spec: EventBindingSpec | StateBindingSpec,
    field: "debounce" | "throttle",
  ): number | null {
    var own = spec[field];
    if (typeof own === "number" && Number.isFinite(own) && own > 0) return own;
    var descriptor = typeof spec.cid === "string" ? classes.get(spec.cid) : undefined;
    var options =
      descriptor && descriptor.eventHandlers && typeof spec.handler === "string"
        ? descriptor.eventHandlers[spec.handler]
        : undefined;
    var fallback = options
      ? field === "debounce"
        ? options.debounceMilliseconds
        : options.throttleMilliseconds
      : undefined;
    if (typeof fallback === "number" && Number.isFinite(fallback) && fallback > 0) return fallback;
    return null;
  };

  // Per-element, per-binding trigger state: the debounce/throttle bookkeeping
  // and the `.once` exhaustion record. Both key by the binding's slot in the
  // decoded array, so an element carrying several bindings times each
  // independently, and both die with the element: a morph survivor keeps its
  // history, a replaced element starts fresh (design 5.1 scopes `.once` to
  // the element's lifetime).
  var bindingTiming = new WeakMap<Element, Map<string, BindingTiming>>();
  var onceExhausted = new WeakMap<Element, Set<string>>();

  var timingStateFor = function (el: Element, key: string): BindingTiming {
    var perEl = bindingTiming.get(el);
    if (!perEl) {
      perEl = new Map<string, BindingTiming>();
      bindingTiming.set(el, perEl);
    }
    var state = perEl.get(key);
    if (!state) {
      state = { debounceTimer: 0, throttleUntil: 0 };
      perEl.set(key, state);
    }
    return state;
  };

  // Send one event binding now. The anchor resolves from the element at fire
  // time, never from anything captured when the listener or timer was set up
  // (design 5.5 machinery item 5): `sendFromElement` owns the fire-time miss
  // and the undeclared-event drop (the drop event plus a debug line, never a
  // throw), and a disconnected element skips its argument expression too, so
  // author code never runs against a detached tree.
  var fireEventBinding = function (el: Element, spec: EventBindingSpec, event: Event | null) {
    var handler = typeof spec.handler === "string" ? spec.handler : "";
    if (!handler) return;
    var args: Record<string, unknown> | null = null;
    if (el.isConnected && typeof spec.args === "string" && spec.args) {
      args = evaluateBindingArgs(el, "@c-" + (spec.event || ""), handler, spec.args, event);
    }
    // A submit-triggered event collects the form's named controls into the
    // args payload (design 5.1): the JS path and the no-JS form post deliver
    // the same call, and explicit expression args win on collision.
    args = mergeSubmitFormArgs(el, event, args);
    var promise = sendFromElement(el, handler, args, undefined);
    // A binding send has no caller holding the promise: failures already
    // surface through `$error` and the lifecycle events, and the routine
    // queue outcomes (cancelled, superseded) are not errors, so the
    // rejection is absorbed here instead of left as an unhandled-rejection
    // log (design 5.5 machinery item 5).
    if (promise) promise.then(null, function () {});
  };

  // Apply a binding's trigger timing and send (design 5.1's modifier table):
  // `.throttle` admits at most one trigger per window (the first one, then
  // the window closes), and `.debounce` holds the send until the trigger has
  // been idle that long, carrying the last trigger's event into the argument
  // expression.
  var scheduleEventBinding = function (el: Element, spec: EventBindingSpec, key: string, event: Event) {
    var debounceMs = bindingTimingMs(spec, "debounce");
    var throttleMs = bindingTimingMs(spec, "throttle");
    if (debounceMs == null && throttleMs == null) {
      fireEventBinding(el, spec, event);
      return;
    }
    var state = timingStateFor(el, key);
    var now = Date.now();
    if (throttleMs != null) {
      if (state.throttleUntil > now) return;
      state.throttleUntil = now + throttleMs;
    }
    if (debounceMs == null) {
      fireEventBinding(el, spec, event);
      return;
    }
    if (state.debounceTimer) window.clearTimeout(state.debounceTimer);
    state.debounceTimer = window.setTimeout(function () {
      state.debounceTimer = 0;
      fireEventBinding(el, spec, event);
    }, debounceMs);
  };

  // DOM events that do not bubble: their delegated listener rides the
  // capture phase (the capture descent still passes the document root even
  // for a non-bubbling event), and only the target element's own bindings
  // fire, matching what an element-level listener would have heard.
  var NON_BUBBLING_EVENTS: Record<string, boolean> = {
    focus: true,
    blur: true,
    mouseenter: true,
    mouseleave: true,
    pointerenter: true,
    pointerleave: true,
    scroll: true,
  };

  // The `.enter` / `.escape` key filters (design 5.1) against KeyboardEvent.key.
  var KEY_FILTER_VALUES: Record<string, string> = { enter: "Enter", escape: "Escape" };

  var keyFilterMatches = function (event: Event, filter: string) {
    var expected = KEY_FILTER_VALUES[filter];
    // An unknown filter never matches: the server-side rewrite rejects these
    // at template load, so only hand-edited HTML reaches here.
    if (!expected) return false;
    return (event as KeyboardEvent).key === expected;
  };

  // Run one element's `data-cev-on` specs for one DOM event (the delegated
  // walk visits elements target-first). Returns whether a fired binding
  // carried `.stop`, which ends the walk: ancestors' bindings must not see a
  // stopped event, while this element's remaining bindings still run, the
  // same split element-level listeners get from stopPropagation.
  var runElementEventBindings = function (el: Element, event: Event, type: string): boolean {
    var stopped = false;
    (decodeCevSpecs(el, DATA_CEV_ON) as EventBindingSpec[]).forEach(function (spec, index) {
      var fired: Set<string> | undefined;
      if (spec == null || typeof spec !== "object" || spec.event !== type) return;
      if (typeof spec.key === "string" && spec.key && !keyFilterMatches(event, spec.key)) return;
      if (spec.self === true && event.target !== el) return;
      var key = type + ":" + index;
      if (spec.once === true) {
        fired = onceExhausted.get(el);
        if (fired && fired.has(key)) return;
        if (!fired) {
          fired = new Set<string>();
          onceExhausted.set(el, fired);
        }
        fired.add(key);
      }
      // The synchronous modifiers act during the dispatch, whatever timing
      // the send itself carries (a debounced `.prevent` still prevents now).
      if (spec.prevent === true) event.preventDefault();
      if (spec.stop === true) {
        event.stopPropagation();
        stopped = true;
      }
      scheduleEventBinding(el, spec, key, event);
    });
    return stopped;
  };

  // The elements the delegated walk visits: one element can carry an `@c-*`
  // event binding, a `:c-*` state binding, or both channels at once.
  var DELEGATED_SELECTOR = "[" + DATA_CEV_ON + "],[" + DATA_CEV_BIND + "]";

  // Run both channels of one element for one DOM event. The on-channel's
  // `.stop` verdict ends the ancestor walk, but the element's own state
  // bindings still run first, the same split element-level listeners get
  // from stopPropagation (design 5.1).
  var runElementBindings = function (el: Element, event: Event, type: string): boolean {
    var stopped = false;
    if (el.hasAttribute(DATA_CEV_ON)) stopped = runElementEventBindings(el, event, type);
    if (el.hasAttribute(DATA_CEV_BIND)) runElementStateBindings(el, event, type);
    return stopped;
  };

  var handleDelegatedEvent = function (event: Event) {
    var type = event.type;
    var start: Element | null =
      event.target && (event.target as MaybeElement).nodeType === 1 ? (event.target as Element) : null;
    if (!start || !start.closest) return;
    var el: Element | null = start.closest(DELEGATED_SELECTOR);
    if (NON_BUBBLING_EVENTS[type] === true) {
      // Non-bubbling: only the target's own bindings (see the set above).
      if (el === start) runElementBindings(el as Element, event, type);
      return;
    }
    while (el) {
      if (runElementBindings(el, event, type)) return;
      el = el.parentElement ? el.parentElement.closest(DELEGATED_SELECTOR) : null;
    }
  };

  // One delegated listener per DOM event type at the document root (design
  // 5.1): installed when a scan first sees the type in a spec, then kept for
  // the page's lifetime. The spec is data on the element and the listener
  // re-reads it at event time, so bindings survive morphs with nothing bound
  // per element.
  var installedListenerTypes = new Set<string>();

  var installDelegatedListener = function (type: string) {
    if (installedListenerTypes.has(type)) return;
    installedListenerTypes.add(type);
    document.addEventListener(type, handleDelegatedEvent, NON_BUBBLING_EVENTS[type] === true);
  };

  // `@c-poll` timers are keyed to the element, one timer per binding slot
  // (design 5.5 machinery item 5, the element-keyed form): a morph survivor
  // keeps its running timer and the re-scan dedupes against it instead of
  // double-polling, and a replaced region's element leaves the DOM, where
  // the scan's sweep (and, between scans, the tick's own liveness check)
  // stops its timers for good.
  var polledElements = new Set<Element>();
  var pollElementSeq = new WeakMap<Element, number>();
  var pollSeqCounter = 0;
  var POLL_KEY_PREFIX = "poll:";

  var pollKeySeq = function (el: Element): number {
    var seq = pollElementSeq.get(el);
    if (seq == null) {
      pollSeqCounter += 1;
      seq = pollSeqCounter;
      pollElementSeq.set(el, seq);
    }
    return seq;
  };

  // Stop the poll timers registered for one element: all of them, or, with
  // `keep`, only the slots no longer expected. Reaches into the
  // element-interval structure the timers section owns, touching only the
  // poll-prefixed keys this layer registers there.
  var clearPollTimers = function (el: Element, keep?: Map<string, PollBindingSpec>) {
    var slots = elementIntervals.get(el);
    var stale: string[] = [];
    if (slots) {
      slots.forEach(function (intervalId, key) {
        if (key.indexOf(POLL_KEY_PREFIX) !== 0) return;
        if (keep && keep.has(key)) return;
        window.clearInterval(intervalId);
        stale.push(key);
      });
      stale.forEach(function (key) {
        (slots as Map<string, number>).delete(key);
      });
    }
    if (!keep) polledElements.delete(el);
  };

  var pollTick = function (el: Element, spec: PollBindingSpec, recurringKey: string) {
    if (!el.isConnected || !el.hasAttribute(DATA_CEV_POLL)) {
      // The region this timer polled for is gone (replaced, removed, or its
      // binding dropped by a morph): the timer dies with it (design 5.5
      // machinery item 5), so a replaced region never leaves a dead interval
      // firing.
      clearPollTimers(el);
      console.debug("[Citry] events: a @c-poll region left the DOM; its timer stopped.");
      return;
    }
    if (document.hidden) return; // polling pauses on hidden tabs (design 5.1)
    var handler = typeof spec.handler === "string" ? spec.handler : "";
    if (!handler) return;
    var args: Record<string, unknown> | null = null;
    if (typeof spec.args === "string" && spec.args) {
      args = evaluateBindingArgs(el, "@c-poll", handler, spec.args, null);
    }
    // The recurring key rides the queue's tick-skip rule (design 5.6): a
    // tick firing while the binding's previous call is still queued or in
    // flight is skipped there, with the debug breadcrumb.
    var promise = sendFromElement(el, handler, args, undefined, recurringKey);
    if (promise) promise.then(null, function () {});
  };

  var syncElementPollTimers = function (el: Element) {
    var expected = new Map<string, PollBindingSpec>();
    (decodeCevSpecs(el, DATA_CEV_POLL) as PollBindingSpec[]).forEach(function (spec, index) {
      if (spec == null || typeof spec !== "object") return;
      if (typeof spec.handler !== "string" || !spec.handler) return;
      if (typeof spec.interval !== "number" || !Number.isFinite(spec.interval) || spec.interval <= 0) return;
      // The slot key carries the handler and the interval, so a binding a
      // morph rewrote retires its old timer below and starts fresh at the
      // new cadence.
      expected.set(POLL_KEY_PREFIX + index + ":" + spec.handler + ":" + spec.interval, spec);
    });
    clearPollTimers(el, expected);
    var slots = elementIntervals.get(el);
    expected.forEach(function (spec, key) {
      if (slots && slots.get(key) != null) return; // the running timer survives a re-scan (the no-double-poll dedupe)
      var recurringKey = "cev-" + POLL_KEY_PREFIX + pollKeySeq(el) + ":" + key;
      var intervalId = window.setInterval(function () {
        pollTick(el, spec, recurringKey);
      }, spec.interval as number);
      registerElementInterval(el, key, intervalId);
    });
    if (expected.size) polledElements.add(el);
    else polledElements.delete(el);
  };

  // ----- the state bindings: two-way flushes, one-way effects, and form collection (design 5.1, 5.5, 5.6) -----

  // The client half of design 5.1's update-event table: which DOM event a
  // two-way binding listens to, resolved from the live control. `.on:` wins
  // outright; `.lazy` asks for the committed-value event. The server-side
  // rewrite already rejected the statically-decidable errors (`.lazy` on a
  // committed-value control, a two-way file input, an unknown control with no
  // `.on:`), so a null here is a dynamically-typed control the runtime cannot
  // bind; the scan warns about it below.
  var resolveUpdateEventType = function (el: Element, spec: StateBindingSpec): string | null {
    var inputType: string;
    if (typeof spec.on === "string" && spec.on) return spec.on;
    var tag = el.tagName;
    if (tag === "SELECT") return "change";
    if (tag === "TEXTAREA") return spec.lazy === true ? "change" : "input";
    if (tag === "INPUT") {
      // The `type` property is the browser-normalized effective type (an
      // unknown authored type reads as "text"), matching what the control
      // actually does.
      inputType = (el as HTMLInputElement).type;
      if (inputType === "file") return null; // files cannot live in State (design 5.1)
      if (inputType === "checkbox" || inputType === "radio") return "change";
      return spec.lazy === true ? "change" : "input";
    }
    return null;
  };

  // The earliest browser event that proves the live control has diverged
  // from server state, independent of `.lazy` or an `.on:` override. Those
  // modifiers choose when the value flushes; they must not leave the draft
  // unprotected before that later trigger (design 5.5's preservation pole).
  var resolveNaturalDraftEventType = function (el: Element): string | null {
    var tag = el.tagName;
    if (tag === "SELECT") return "change";
    if (tag === "TEXTAREA") return "input";
    if (tag !== "INPUT") return null;
    var inputType = (el as HTMLInputElement).type;
    if (inputType === "file") return null;
    if (inputType === "checkbox" || inputType === "radio") return "change";
    return "input";
  };

  // A control's current value, typed for the wire: checkboxes and radios are
  // their checked state (the write model `applyValueToControl` applies in
  // reverse), and numeric controls produce numbers because a State field
  // declared `int`/`float` takes JSON numbers and the server checks types
  // without coercing (design 7.2). Everything else is the value string.
  var readControlValue = function (el: Element): unknown {
    var control = el as HTMLInputElement;
    var numeric: number;
    if (control.type === "checkbox" || control.type === "radio") return control.checked;
    if (control.type === "number" || control.type === "range") {
      numeric = control.valueAsNumber;
      return Number.isFinite(numeric) ? numeric : control.value;
    }
    return control.value;
  };

  /**
   * One two-way binding's flush bookkeeping: the pending flush timer (a
   * debounce hold or a trailing throttle capture), the open throttle window,
   * and the spec the flush will act on (refreshed per trigger, because a
   * morph can rewrite the attribute under a surviving element).
   */
  interface TwoWayFlushState {
    el: Element;
    spec: StateBindingSpec;
    flushTimer: number;
    throttleUntil: number;
  }

  // Per-element, per-binding-slot flush state. Keying by the element keeps
  // one timer per control however many renders it lives through (the
  // no-stacking rule, design 5.5): a morph survivor keeps its single entry,
  // and a replaced element's entry dies with it.
  var twoWayFlushStates = new WeakMap<Element, Map<string, TwoWayFlushState>>();
  // Every state whose flush timer is armed, iterable for the updates
  // piggyback (design 4.2): an outgoing call from the instance collects
  // these drafts before its pending-writes snapshot.
  var pendingTwoWayFlushes = new Set<TwoWayFlushState>();

  var twoWayStateFor = function (el: Element, key: string, spec: StateBindingSpec): TwoWayFlushState {
    var perEl = twoWayFlushStates.get(el);
    if (!perEl) {
      perEl = new Map<string, TwoWayFlushState>();
      twoWayFlushStates.set(el, perEl);
    }
    var state = perEl.get(key);
    if (!state) {
      state = { el: el, spec: spec, flushTimer: 0, throttleUntil: 0 };
      perEl.set(key, state);
    }
    state.spec = spec;
    return state;
  };

  // Flush one two-way binding now: the draft stops being a draft (the mark
  // clears), the control's value writes into `$state` (which queues it as a
  // pending update), and the named handler sends, so one call carries the
  // field update and the event together (design 5.1). The anchor resolves
  // from the element at fire time, never from anything captured when the
  // timer was armed (design 5.5 machinery item 5); `sendFromElement` owns
  // the fire-time miss surface (the drop event plus a debug line).
  var flushTwoWayBinding = function (state: TwoWayFlushState) {
    if (state.flushTimer) {
      window.clearTimeout(state.flushTimer);
      state.flushTimer = 0;
    }
    pendingTwoWayFlushes.delete(state);
    var el = state.el;
    var spec = state.spec;
    unsentDrafts.delete(el);
    var anchor = el.isConnected ? anchorForElement(el) : null;
    if (anchor && anchor.stateProxy != null && typeof spec.field === "string") {
      try {
        anchor.stateProxy[spec.field] = readControlValue(el);
      } catch (err) {
        // The server-side rewrite only compiles two-way bindings to writable
        // fields, so a throw here means the page and the descriptor disagree
        // (a deploy skew); surface it without breaking the walk.
        console.error("[Citry] events: a two-way binding could not write $state." + spec.field + ":", err);
      }
    }
    var handler = typeof spec.handler === "string" ? spec.handler : "";
    if (!handler) return;
    var promise = sendFromElement(el, handler, null, undefined);
    // A binding send has no caller holding the promise (same absorption as
    // the event channel): failures surface through `$error` and the
    // lifecycle events.
    if (promise) promise.then(null, function () {});
  };

  // Arm the flush timer. A trailing throttle flush is itself a send, so it
  // opens the next window when it fires.
  var armTwoWayFlush = function (state: TwoWayFlushState, delayMs: number, throttleMs: number | null) {
    pendingTwoWayFlushes.add(state);
    state.flushTimer = window.setTimeout(function () {
      state.flushTimer = 0;
      if (throttleMs != null) state.throttleUntil = Date.now() + throttleMs;
      flushTwoWayBinding(state);
    }, delayMs);
  };

  // One two-way trigger: mark the draft, then flush now or hold per the
  // binding's timing. Throttle admits the first trigger and captures the
  // rest of the window into one trailing flush at the window's close, so a
  // burst still delivers its final value while the rate stays at one send
  // per window (a two-way binding must never silently drop the user's last
  // input; the preservation contract of design 5.5 is built on that).
  var scheduleTwoWayUpdate = function (el: Element, spec: StateBindingSpec, key: string, event: Event) {
    if (typeof spec.key === "string" && spec.key && !keyFilterMatches(event, spec.key)) return;
    var state = twoWayStateFor(el, key, spec);
    // From this trigger until a flush hands the value over, the DOM diverges
    // from `$state`: the patch-time guard reads this mark as the unflushed
    // draft stage of `hasUnsentDraft` (design 5.3/5.5).
    unsentDrafts.add(el);
    var debounceMs = bindingTimingMs(spec, "debounce");
    var throttleMs = bindingTimingMs(spec, "throttle");
    var now = Date.now();
    if (throttleMs != null) {
      if (state.throttleUntil > now) {
        if (!state.flushTimer) armTwoWayFlush(state, state.throttleUntil - now, throttleMs);
        return;
      }
      state.throttleUntil = now + throttleMs;
    }
    if (debounceMs == null) {
      flushTwoWayBinding(state);
      return;
    }
    if (state.flushTimer) window.clearTimeout(state.flushTimer);
    armTwoWayFlush(state, debounceMs, throttleMs);
  };

  // Run one element's two-way specs for one DOM event (the delegated walk's
  // state-channel half).
  var runElementStateBindings = function (el: Element, event: Event, type: string) {
    decodeBindSpecs(el).forEach(function (spec, index) {
      if (spec == null || typeof spec !== "object" || spec.mode !== "two") return;
      var updateType = resolveUpdateEventType(el, spec);
      if (updateType !== type) {
        if (resolveNaturalDraftEventType(el) === type) unsentDrafts.add(el);
        return;
      }
      scheduleTwoWayUpdate(el, spec, "bind:" + index, event);
    });
  };

  // The piggyback collector `sendAll` calls per outgoing call (design 4.2:
  // "when another call from the instance fires while an update's debounce
  // timer is still pending, that call carries the update too"). Each
  // registered mid-flush draft belonging to this anchor writes into `$state`
  // now, which queues it for the pending snapshot the caller takes right
  // after, and its draft mark clears because the server is about to see the
  // value. The flush timer stays armed: the binding's named handler is still
  // the designed flush and runs when the timer expires.
  var collectPendingTwoWayDrafts = function (anchor: Anchor) {
    pendingTwoWayFlushes.forEach(function (state) {
      var el = state.el;
      if (!el.isConnected || anchorForElement(el) !== anchor) return;
      if (anchor.stateProxy == null || typeof state.spec.field !== "string") return;
      unsentDrafts.delete(el);
      try {
        anchor.stateProxy[state.spec.field] = readControlValue(el);
      } catch (err) {
        console.error("[Citry] events: could not piggyback the two-way draft of $state." + state.spec.field + ":", err);
      }
    });
  };

  /** One bound control's live application record: the effects and the identities they subscribed to. */
  interface ControlBindingRecord {
    anchor: Anchor;
    /** The anchor's reactive values object the effects read. A class adopt replaces it, so identity is part of the reuse check. */
    values: StateValues;
    /** The raw attribute string the record was built from (the spec identity). */
    raw: string;
    effects: object[];
  }

  // Per-control application state: which effects are live, and a page-level
  // set for the release sweep (a WeakMap alone cannot be iterated).
  var controlBindings = new WeakMap<Element, ControlBindingRecord>();
  var boundControls = new Set<Element>();
  // Two-way controls whose update event cannot be resolved (a dynamically
  // typed control without `.on:`); warned once per element.
  var warnedUnresolvedUpdate = new WeakSet<Element>();

  var releaseControlBindings = function (el: Element) {
    var record = controlBindings.get(el);
    if (record) {
      record.effects.forEach(function (effectRef) {
        Alpine.release(effectRef);
      });
      controlBindings.delete(el);
    }
    boundControls.delete(el);
  };

  // The application a `:c-*` binding is (design 5.5): a reactive effect over
  // `$state.<field>` applying the value to the control, for one-way and
  // two-way bindings alike, so a server reconcile or a local `$state` write
  // reaches the control through reactivity alone. A control holding an
  // unflushed two-way draft is left alone: the DOM value is newer than
  // `$state` until the flush hands it over (the same exemption the
  // patch-time guard enforces during morphs).
  var makeApplicationEffect = function (el: Element, anchor: Anchor, field: string) {
    return Alpine.effect(function () {
      var values = anchor.values;
      if (values == null) return; // retired mid-scan: the next binding scan rebinds this control
      if (!Object.prototype.hasOwnProperty.call(values, field)) return;
      var value = values[field]; // the reactive read this effect subscribes to
      if (unsentDrafts.has(el)) return;
      applyValueToControl(el, value);
    });
  };

  // Bring one control's application effects in line with the live DOM: reuse
  // the record when nothing moved, otherwise tear the old effects down first
  // and rebuild, so a control that lived through three parent renders holds
  // one binding, not three (design 5.5's rebind rule). A parent or targeted
  // render re-minted the innermost id under the control (reset or link), and
  // effects subscribed to a retired anchor's values object would never fire
  // again; the identity checks below catch exactly that.
  var syncControlBindings = function (el: Element) {
    var raw = el.getAttribute(DATA_CEV_BIND) || "";
    var anchor = el.isConnected ? anchorForElement(el) : null;
    var record = controlBindings.get(el);
    if (!raw || !anchor || anchor.values == null) {
      if (record) releaseControlBindings(el);
      return;
    }
    if (record && record.anchor === anchor && record.values === anchor.values && record.raw === raw) return;
    if (record) releaseControlBindings(el);
    var effects: object[] = [];
    var liveAnchor = anchor;
    decodeBindSpecs(el).forEach(function (spec) {
      if (spec == null || typeof spec !== "object" || typeof spec.field !== "string") return;
      effects.push(makeApplicationEffect(el, liveAnchor, spec.field));
    });
    controlBindings.set(el, {
      anchor: liveAnchor,
      values: liveAnchor.values as StateValues,
      raw: raw,
      effects: effects,
    });
    boundControls.add(el);
  };

  // The scan's per-element entry for the bind channel: make sure the update
  // events' delegated listeners exist, warn once for a two-way control the
  // table cannot resolve, and sync the application effects.
  var syncStateBindings = function (el: Element) {
    decodeBindSpecs(el).forEach(function (spec) {
      var draftType: string | null;
      if (spec == null || typeof spec !== "object" || spec.mode !== "two") return;
      var type = resolveUpdateEventType(el, spec);
      if (type) {
        installDelegatedListener(type);
        draftType = resolveNaturalDraftEventType(el);
        if (draftType && draftType !== type) installDelegatedListener(draftType);
      } else if (!warnedUnresolvedUpdate.has(el)) {
        warnedUnresolvedUpdate.add(el);
        console.warn(
          "[Citry] events: the two-way :c-" +
            (typeof spec.field === "string" ? spec.field : "?") +
            " binding has no update event for this control; name one with '.on:<event>' (design 5.1).",
        );
      }
    });
    syncControlBindings(el);
  };

  // ----- form collection on submit (design 5.1, mirroring the urlencoded no-JS codec) -----

  // The reserved field names of the no-JS form codec: hand-written form
  // posts carry the token and the instance in these, and the runtime's
  // envelope already carries both, so they never enter the args payload.
  var RESERVED_FORM_FIELDS: Record<string, boolean> = {
    _citry_state_token: true,
    _citry_caller_render_id: true,
  };

  // The one type coercion in the collection: a numeric control's single
  // value is a number, because a schema field declared `int`/`float` takes
  // JSON numbers and the JSON path never string-binds (the urlencoded
  // codec's string-to-number binding is source-aware and does not apply to
  // envelope calls, design 3.3). Repeated fields stay lists of strings,
  // exactly like the codec's repeated-field rule.
  var coerceFormValue = function (form: HTMLFormElement, name: string, value: string): unknown {
    var control = form.elements.namedItem(name);
    var input = control && (control as MaybeElement).nodeType === 1 ? (control as HTMLInputElement) : null;
    var numeric: number;
    if (input && input.tagName === "INPUT" && (input.type === "number" || input.type === "range")) {
      numeric = input.valueAsNumber;
      if (Number.isFinite(numeric)) return numeric;
    }
    return value;
  };

  // Serialize a form's named controls into an args payload the way the
  // browser itself would serialize the form (FormData: named and enabled
  // controls, checkboxes and radios only when checked, one entry per
  // selected option): a field sent once arrives as its value, a repeated
  // field as the list of its values, matching the urlencoded codec's shape.
  // File entries are skipped: files cannot ride the JSON envelope (no
  // multipart in v1, design 6.2); collect a file through event args instead.
  var collectFormArgs = function (form: HTMLFormElement): Record<string, unknown> {
    var entries = new Map<string, string[]>();
    new FormData(form).forEach(function (value, name) {
      if (RESERVED_FORM_FIELDS[name] === true) return;
      if (typeof value !== "string") return;
      var bucket = entries.get(name);
      if (!bucket) {
        bucket = [];
        entries.set(name, bucket);
      }
      bucket.push(value);
    });
    var out: Record<string, unknown> = {};
    entries.forEach(function (values, name) {
      out[name] = values.length === 1 ? coerceFormValue(form, name, values[0]) : values.slice();
    });
    return out;
  };

  var mergeSubmitFormArgs = function (
    element: Element | null,
    event: Event | null | undefined,
    args: Record<string, unknown> | null,
  ): Record<string, unknown> | null {
    if (!event || event.type !== "submit") return args;
    var target = event.target as MaybeElement | null;
    var form =
      target && target.nodeType === 1 && (target as Element).tagName === "FORM"
        ? (target as HTMLFormElement)
        : element && element.tagName === "FORM"
          ? (element as HTMLFormElement)
          : null;
    if (!form || !form.isConnected) return args;
    var collected = collectFormArgs(form);
    return args ? (Object.assign(collected, args) as Record<string, unknown>) : collected;
  };

  // One scan pass: install the delegated listener for every DOM event type
  // the page's `data-cev-on` specs name, and bring each `data-cev-poll`
  // element's timers in line with its specs. Runs at boot and again
  // (microtask debounced) after every DOM mutation batch, so bindings
  // inserted with a fragment come alive with no per-element wiring.
  var scanBindings = function () {
    bindingScanScheduled = false;
    document.querySelectorAll("[" + DATA_CEV_ON + "]").forEach(function (el) {
      (decodeCevSpecs(el, DATA_CEV_ON) as EventBindingSpec[]).forEach(function (spec) {
        if (spec != null && typeof spec === "object" && typeof spec.event === "string" && spec.event) {
          installDelegatedListener(spec.event);
        }
      });
    });
    document.querySelectorAll("[" + DATA_CEV_POLL + "]").forEach(syncElementPollTimers);
    // Elements that no longer poll (removed with their region, or their
    // binding gone after a morph) release their timers here; the tick's own
    // liveness check is the backstop between scans.
    polledElements.forEach(function (el) {
      if (!el.isConnected || !el.hasAttribute(DATA_CEV_POLL)) clearPollTimers(el);
    });
    // The bind channel: update-event listeners plus the application effects,
    // rebound (never stacked) when a render moved the instance under a
    // control. This scan is the rebind walk of design 5.5's one-way rule; it
    // covers the whole document, which subsumes "under the applied region"
    // and stays idempotent through the reuse check.
    document.querySelectorAll("[" + DATA_CEV_BIND + "]").forEach(syncStateBindings);
    boundControls.forEach(function (el) {
      if (!el.isConnected || !el.hasAttribute(DATA_CEV_BIND)) releaseControlBindings(el);
    });
  };

  var bindingScanScheduled = false;
  var scheduleBindingScan = function () {
    if (bindingScanScheduled) return;
    bindingScanScheduled = true;
    Promise.resolve().then(scanBindings);
  };

  // ----- client props: the `$component` config form's resolution (design 5.5) -----

  var propTypeName = function (ctor: unknown): string {
    if (typeof ctor === "function" && (ctor as { name?: string }).name) return (ctor as { name: string }).name;
    return String(ctor);
  };

  var matchesPropType = function (value: unknown, ctor: unknown): boolean {
    // The primitive constructors match by typeof (a declared `String` means
    // "a string value", the Vue object-API convention), `Array` by isArray,
    // `Object` by any non-null object, and any other constructor by
    // instanceof.
    if (ctor === String) return typeof value === "string";
    if (ctor === Number) return typeof value === "number";
    if (ctor === Boolean) return typeof value === "boolean";
    if (ctor === Function) return typeof value === "function";
    if (ctor === Symbol) return typeof value === "symbol";
    if (ctor === BigInt) return typeof value === "bigint";
    if (ctor === Array) return Array.isArray(value);
    if (ctor === Object) return typeof value === "object" && value !== null;
    if (typeof ctor === "function") return value instanceof (ctor as new (...args: unknown[]) => unknown);
    return false;
  };

  // A prop's accepted constructors: the declared `type`, or its array form
  // (`type: [String, Boolean]` accepts either). A non-constructor entry is
  // the author's bug and fails loudly, naming the component and the prop.
  var declaredTypeList = function (classId: string, name: string, type: unknown): unknown[] {
    var list = Array.isArray(type) ? type : [type];
    list.forEach(function (entry) {
      if (typeof entry !== "function") {
        throw pointedError(
          "component " +
            classId +
            " prop '" +
            name +
            "': `type` must be a constructor (String, Number, ...) or an array of constructors (design 5.5).",
        );
      }
    });
    return list;
  };

  // Resolve and validate one instance's declared props (the `$component`
  // config form, design 5.5). The passing side is design-open (events.md
  // 16.1), so in v1 every value comes from the declaration's `default`; a
  // function default is called per instance, so object and array defaults
  // are never shared between instances. Validation runs at instance
  // initialization, before init, and fails loudly naming the
  // component and the prop. The resolved bag is Alpine-reactive, so effects
  // reading `props.<name>` re-run when a future supplier writes.
  var resolveDeclaredProps = function (
    classId: string,
    declarations: Record<string, PropDefinition>,
  ): Record<string, unknown> {
    var resolved: Record<string, unknown> = {};
    Object.keys(declarations || {}).forEach(function (name) {
      var def = declarations[name];
      var accepted: unknown[];
      var matched: boolean;
      if (def == null || typeof def !== "object") {
        throw pointedError(
          "component " +
            classId +
            " prop '" +
            name +
            "': the definition must be an object with `type`, `required`, and/or `default` (design 5.5).",
        );
      }
      var value: unknown;
      if (Object.prototype.hasOwnProperty.call(def, "default")) {
        value = typeof def.default === "function" ? (def.default as () => unknown)() : def.default;
      }
      if (value === undefined) {
        if (def.required === true) {
          throw pointedError(
            "component " +
              classId +
              " prop '" +
              name +
              "' is required, but no value was supplied and it declares no default.",
          );
        }
        resolved[name] = undefined;
        return;
      }
      // A null value is a present-but-empty supply and skips the type check,
      // so `default: null` works for any declared type.
      if (value !== null && def.type != null) {
        accepted = declaredTypeList(classId, name, def.type);
        matched = accepted.some(function (ctor) {
          return matchesPropType(value, ctor);
        });
        if (!matched) {
          throw pointedError(
            "component " +
              classId +
              " prop '" +
              name +
              "': the value does not match the declared type; expected " +
              accepted.map(propTypeName).join(" or ") +
              ", got " +
              (Array.isArray(value) ? "an array" : "a " + typeof value) +
              ".",
          );
        }
      }
      resolved[name] = value;
    });
    return Alpine.reactive(resolved);
  };

  // ----- the $component payload decoration -----

  var decorateComponentContext = function (ctx: ComponentPayload, control?: ComponentInvocationControl | null) {
    // Drain manifests the observer has not been told about yet: citry.js
    // processes manifest tags during page parse, so a component call can
    // flush while our observer's mutation record is still queued behind it
    // (WP6 spike F2's companion rule).
    processExistingEventsManifests();
    // Every payload carries `props` (design 5.5): an empty object under the
    // bare callback form. A config-form registration overrides it per
    // callback with the values `_resolveProps` resolves from its declaration
    // (the props section above; the registration shape lives in citry.js).
    ctx.props = {};
    var anchor = idToAnchor.get(ctx.id) || null;
    if (anchor) {
      ctx.state = anchor.stateProxy;
      ctx.sendEvent = function (name, args, opts) {
        // The payload member keeps the promise contract even for a bad name.
        // (anchor! as in the magics: the if-guard does not reach in here.)
        try {
          return sendFromAnchor(anchor!, name, args, opts);
        } catch (err) {
          return Promise.reject(err);
        }
      };
      ctx.onEvent = function (name, fn) {
        var off = subscribeForAnchor(anchor!, name, fn);
        return control ? control.registerCleanup(off) : off;
      };
    } else {
      // Not an interactive instance (no Events declared): the members exist
      // on every payload, and say plainly why they cannot do more here.
      ctx.state = null;
      ctx.sendEvent = function (name) {
        return Promise.reject(
          pointedError(
            "component instance '" +
              ctx.id +
              "' declares no events, so sendEvent('" +
              name +
              "')" +
              " has nothing to call; add a `class Events` to the component.",
          ),
        );
      };
      ctx.onEvent = function () {
        throw pointedError(
          "component instance '" +
            ctx.id +
            "' declares no events, so onEvent cannot target it;" +
            " add a `class Events` to the component.",
        );
      };
    }
  };

  // ----- the public surface (`Citry.events`) -----

  var resolveSendTarget = function (target: string | Element) {
    if (typeof target === "string") return idToAnchor.get(target) || null;
    if (target && target.nodeType === 1) {
      // biome-ignore lint/correctness/noInnerDeclarations: var hoists to the function scope; block-scoped var is part of the file's ES5-flavored style.
      var id = innermostPhysicalComponentId(target);
      return (id && idToAnchor.get(id)) || null;
    }
    return null;
  };

  // The literal gains `_internal` two assignments below, before it is
  // published at `C.events`; the assertion covers that gap.
  var api = {
    /**
     * Send an event to any instance on the page. `target` is an instance id
     * or an Element inside one; same promise contract as the scoped
     * `sendEvent` (design 5.2).
     */
    send: function (target: string | Element, name: string, args?: Record<string, unknown>, opts?: unknown) {
      var anchor = resolveSendTarget(target);
      if (!anchor) {
        return Promise.reject(
          pointedError(
            "send() found no interactive component instance for target " +
              (typeof target === "string" ? "'" + target + "'" : String(target)) +
              "; pass an instance id from the events manifest or an element inside one.",
          ),
        );
      }
      // An Element target is the dispatching element (design 5.6): the
      // queue's containment walk, busy stamp, and fire-time re-resolution
      // start from it; an id target rides the anchor's own roots.
      var element = typeof target !== "string" && target && target.nodeType === 1 ? (target as Element) : null;
      try {
        return sendFromAnchor(anchor, name, args, opts, element, element != null);
      } catch (err) {
        return Promise.reject(err);
      }
    },

    /**
     * Listen for server-dispatched events under their raw name, from any
     * instance; sugar over document.addEventListener that unwraps e.detail.
     * Returns the unsubscribe function.
     */
    on: function (name: string, fn: EventCallback) {
      var handler = function (e: Event) {
        fn((e as CustomEvent).detail);
      };
      document.addEventListener(name, handler);
      return function () {
        document.removeEventListener(name, handler);
      };
    },

    /** Set page-wide runtime defaults once (design 5.2's field table). */
    configure: function (opts?: EventsConfig) {
      Object.assign(config, opts || {});
    },

    /**
     * Register a transport under a name (design 5.2/6.1): `impl` is
     * `{send(envelope) -> Promise<resultEnvelope>, subscribe?}` (`subscribe`
     * is the v2 push half). The built-in fetch transport registers through
     * this same function; selection is `configure({transport: name})`.
     */
    registerTransport: registerTransportImpl,

    /**
     * The action interpreter as a public entry point (design 5.2's table):
     * apply a result envelope's `actions` array to the page, firing the same
     * lifecycle events. Exposed for tests, custom transports, and pages that
     * override what an action does. Applied with no caller context: no
     * caller promise, no epoch guard, liveness checks as always.
     */
    applyActions: function (actions: ResultAction[]) {
      if (!Array.isArray(actions)) {
        return Promise.reject(
          pointedError("applyActions expects a result's `actions` array (design 4.3), got " + typeof actions + "."),
        );
      }
      if (
        !actions.every(validateWireAction) ||
        actions.filter(function (action) {
          return action.action === "data";
        }).length > 1
      ) {
        return Promise.reject(pointedError("applyActions received an invalid citry-events/1 action array."));
      }
      return applyResult({ ok: true, actions: actions }, null);
    },

    // The hook the $component payload decorator delegates to. The bootstrap
    // stub registers the decorator wrapper with citry.js and routes it here
    // the moment this runtime replaces the stub.
    _decorate: decorateComponentContext,

    // Instance-scoped subscribe by component id. Payloads the bootstrap stub
    // decorated before this runtime arrived hold `onEvent` closures that
    // delegate here at call time, so a late subscription still lands on the
    // live runtime instead of the stub's drained queue.
    _onFor: subscribeForId,

    // The events-runtime half of the `$component` config form (design
    // 5.5): the dependency manager resolves a registration's declared props
    // through this, late-bound like `_decorate`, so prop validation and
    // reactivity live here while the registration shape lives in citry.js.
    _resolveProps: resolveDeclaredProps,
  } as CitryEventsApi;

  // Internal contract for the transport and actions layer (and for tests).
  // Everything here is deliberately underscore-private: the public client API
  // is the design 5.2 table, nothing else.
  api._internal = {
    alpineStarted: false,
    anchors: anchors,
    idToAnchor: idToAnchor,
    classes: classes,
    config: config,
    getAnchor: function (componentId: string) {
      return idToAnchor.get(componentId) || null;
    },
    linkRenderedInstance: linkRenderedInstance,
    finishRender: finishRender,
    setTransport: function (fn: TransportStub | null) {
      transportImpl = fn;
    },
    sendCalls: sendCalls,
    sendFromElement: sendFromElement,
    sendBoundary: sendBoundary,
    boundaryScope: boundaryScope,
    queue: {
      snapshot: function () {
        return queueNodes.map(function (node) {
          var waitsOn: number[] = [];
          node.deps.forEach(function (dep) {
            waitsOn.push(dep.seq);
          });
          waitsOn.sort(function (a, b) {
            return a - b;
          });
          return {
            seq: node.seq,
            event: node.name,
            anchor: node.anchor.anchorId,
            dispatched: node.dispatched,
            waitsOn: waitsOn,
          };
        });
      },
    },
    debug: function () {
      var anchorIntervals = 0;
      var elementIntervalCount = 0;
      var formEffects = 0;
      anchors.forEach(function (anchor) {
        anchorIntervals += anchor.timers.size;
      });
      polledElements.forEach(function (el) {
        var intervals = elementIntervals.get(el);
        if (intervals) elementIntervalCount += intervals.size;
      });
      boundControls.forEach(function (el) {
        var record = controlBindings.get(el);
        if (record) formEffects += record.effects.length;
      });
      return Object.freeze({
        anchors: anchors.size,
        renderIds: idToAnchor.size,
        classes: classes.size,
        delegatedListenerTypes: installedListenerTypes.size,
        polledElements: polledElements.size,
        anchorIntervals: anchorIntervals,
        elementIntervals: elementIntervalCount,
        boundControls: boundControls.size,
        formEffects: formEffects,
        pendingFlushes: pendingTwoWayFlushes.size,
        queuedCalls: queueNodes.length,
      });
    },
    stageEventsManifest: stageEventsManifest,
    processEventsManifests: processExistingEventsManifests,
    applyResult: applyResult,
    applyEnvelope: applyEnvelope,
    retireAnchor: retireAnchor,
    sweepRetiredAnchors: sweepRetiredAnchors,
    drafts: {
      mark: function (el: Element) {
        unsentDrafts.add(el);
      },
      clear: function (el: Element) {
        unsentDrafts.delete(el);
      },
      has: function (el: Element) {
        return unsentDrafts.has(el);
      },
    },
    forms: {
      snapshot: function (el: Element) {
        var record = controlBindings.get(el);
        var flushes = 0;
        pendingTwoWayFlushes.forEach(function (state) {
          if (state.el === el && state.flushTimer) flushes += 1;
        });
        return { effects: record ? record.effects.length : 0, flushes: flushes };
      },
    },
    timers: {
      registerAnchorInterval: registerAnchorInterval,
      registerElementInterval: registerElementInterval,
    },
  };

  C.events = api;

  // ----- boot -----

  // Register replaceable providers with the core's permanent broker. Alpine
  // sees one selector and one init interceptor for the page lifetime; Events
  // arrival, fragments, and duplicate runtime loads cannot stack hooks.
  alpineRuntime._register({
    root: function () {
      return "[data-citry-root],[data-cid]";
    },
    init: function (el: MaybeElement) {
      if (!el.hasAttribute || !el.hasAttribute("data-cid")) return;
      if (boundaryAttached.has(el as Element)) return;
      processExistingEventsManifests();
      if (boundaryAttached.has(el as Element)) return;
      var ids = ((el as Element).getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
      var known = false;
      ids.forEach(function (id) {
        var anchor = idToAnchor.get(id);
        if (anchor) {
          known = true;
          anchor.seenInDom = true;
        }
      });
      if (known) attachBoundaryScope(el as Element);
    },
    mutations: function (mutations: MutationRecord[]) {
      if (!mutations.length) processExistingEventsManifests();
      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node: MaybeElement) {
          if (node.nodeType !== 1) return;
          if (node.matches && node.matches(EVENTS_MANIFEST_SELECTOR)) {
            processEventsManifestTag(node as HTMLScriptElement);
          } else if (node.querySelectorAll) {
            node.querySelectorAll<HTMLScriptElement>(EVENTS_MANIFEST_SELECTOR).forEach(processEventsManifestTag);
          }
        });
      });
      scheduleAnchorSweep();
      scheduleBindingScan();
    },
    beforeStart: function () {
      processExistingEventsManifests();
      scheduleBindingScan();
    },
    afterStart: function () {
      api._internal.alpineStarted = true;
    },
  });

  // Manifests already parsed before this script evaluated (the serializer
  // emits the events manifest before the data-citry manifest, so on a
  // document page every instance above this script tag is caught here).
  processExistingEventsManifests();
  // Bindings already parsed before this script evaluated come alive the same
  // way; everything parsed after arrives through the observer above.
  scheduleBindingScan();

  // Adopt whatever the bootstrap stub queued before this runtime arrived.
  // The stub pushes plain argument arrays, so the drain casts them per kind
  // (the shapes are pinned by the stub's body in the Python emission module).
  if (bootstrapStub && bootstrapStub._stubQueue) {
    // Transport registrations are declarations, not calls: install every
    // one first so an earlier queued configure/send can select it safely.
    bootstrapStub._stubQueue.forEach(function (entry) {
      if (entry.kind !== "registerTransport") return;
      try {
        api.registerTransport(entry.args[0] as string, entry.args[1] as TransportImpl);
      } catch (err) {
        if (entry.reject) entry.reject(err);
        else console.error("[Citry] a queued transport registration failed while the runtime booted:", err);
      }
    });
    bootstrapStub._stubQueue.forEach(function (entry) {
      try {
        if (entry.kind === "registerTransport") {
          return;
        } else if (entry.kind === "send") {
          api.send.apply(null, entry.args as Parameters<CitryEventsApi["send"]>).then(entry.resolve, entry.reject);
        } else if (entry.kind === "applyActions") {
          api.applyActions(entry.args[0] as ResultAction[]).then(entry.resolve, entry.reject);
        } else if (entry.kind === "on") {
          if (!entry.dead) entry.off = api.on(entry.args[0] as string, entry.args[1] as EventCallback);
        } else if (entry.kind === "onEvent") {
          if (!entry.dead)
            entry.off = subscribeForId(
              entry.args[0] as string,
              entry.args[1] as string,
              entry.args[2] as EventCallback,
            );
        } else if (entry.kind === "configure") {
          api.configure(entry.args[0] as EventsConfig);
        }
      } catch (err) {
        if (entry.reject) entry.reject(err);
        else console.error("[Citry] a queued events call failed while the runtime booted:", err);
      }
    });
    bootstrapStub._stubQueue.length = 0;
  }

  // Register the payload decorator unless the bootstrap stub already did:
  // its wrapper reads `Citry.events._decorate` at call time, which now
  // resolves to this runtime's decorator (the assertion below matches that:
  // the runtime installed C.events above, and the read stays late-bound on
  // purpose so a newer runtime instance wins).
  if (C.manager && typeof C.manager.decorateContext === "function") {
    if (!(bootstrapStub && bootstrapStub._decoratorHooked)) {
      C.manager.decorateContext(function (ctx, control) {
        C.events!._decorate(ctx, control);
      });
    }
  }

  alpineRuntime._ready();
  alpineRuntime._start();
})();
