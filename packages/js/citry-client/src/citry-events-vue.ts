/** Private citry-events/1 bridge for a Vue-owned component tree. */

import {
  assertValidActionList as assertProtocolActionList,
  buildOkResult,
  buildCall,
  buildCallEnvelope,
  copyJson,
  preflightResultEnvelope,
  validateDescriptor,
  validateStrictJson,
  type EventAction,
  type EventArgsSource,
  type EventComponentClass,
  type EventResult,
  type JsonObject,
  type JsonValue,
} from "@citry/protocol-events-v1";
export { collectFormArgs } from "./citry-events-shared";

/** Validate and copy a public action list before a caller can apply any item. */
export const assertValidActionList = (actions: unknown): EventAction[] => assertProtocolActionList(actions);

export interface VueEventContext {
  serverRenderId: string;
  stateToken: string | null;
  publicState: JsonObject;
  componentClassId: string;
  descriptor: EventComponentClass;
}

export interface VueEventSource {
  stableId: string;
  generation: number;
}

export interface PreparedVueRender {
  /** Opaque validated transaction retained by the Vue coordinator. */
  readonly transaction: unknown;
}

export interface PreparedVueResult {
  readonly result: EventResult;
  readonly renderPlan?: unknown;
}

export interface VueEventsHost {
  appId(source: VueEventSource): string;
  resolve(source: VueEventSource): VueEventContext | null;
  revision(source: VueEventSource): number;
  /**
   * Checks a result before any of its actions run. The bridge passes a result that no other code
   * holds, so the host may freeze its data in place and keep it without copying.
   */
  preflightResult?(result: EventResult, source: VueEventSource): PreparedVueResult;
  prepareRender(
    action: EventAction,
    source: VueEventSource,
    signal: AbortSignal,
    renderPlan?: unknown,
  ): Promise<PreparedVueRender>;
  /** Releases a transaction, or the exact active preparation when `prepared` is undefined. */
  abortRender(prepared: PreparedVueRender | undefined, source: VueEventSource): void;
  /** Publishes credentials after Vue flush/generation checks and before callbacks. */
  commitRender(prepared: PreparedVueRender, source: VueEventSource): Promise<void>;
  /**
   * Stores a State refresh: the new token and the public values that `$state` shows. The host keeps
   * any field the browser changed but has not sent yet, so a refresh never discards a local write.
   */
  commitState(serverRenderId: string, stateToken: string, publicState: JsonObject, source: VueEventSource): void;
  /**
   * Delivers a Dispatch action from the calling component. `followRemount` is true when a Render
   * earlier in the same response remounted the caller: the host then delivers the event from the
   * instance mounted at the caller's place now, because the one that made the call is gone.
   */
  dispatchEvent(name: string, detail: JsonValue | undefined, source: VueEventSource, followRemount?: boolean): void;
  dispatchEventGlobal?(name: string, detail: JsonValue | undefined): void;
  redirect(url: string): void;
  updateUrl(url: string, mode: "push" | "replace"): void;
  resolveTarget?(target: string): VueEventSource | null;
  lifecycle?(
    kind: "before" | "after" | "error" | "swapped" | "stale",
    source: VueEventSource,
    event: string,
    detail?: JsonObject,
  ): boolean | undefined;
  /**
   * Offers the user a reload after a call failed because the page and the server run different app
   * versions. The bridge calls it only when no `stale` listener cancelled the version notification.
   */
  promptReload?(): void;
  takePendingState?(source: VueEventSource, handler: string): JsonObject | undefined;
  restorePendingState?(source: VueEventSource, updates: JsonObject): void;
}

export interface VueEventsBridgeOptions {
  endpoint: string | ((context: VueEventContext, handler: string) => string);
  eventBaseUrl?: string;
  host: VueEventsHost;
  csrf?: { cookie?: string; header?: string; token?: string | (() => string) };
  fetch?: typeof globalThis.fetch;
  timeoutMs?: number;
  runtimeConfig?: () => VueEventRuntimeConfig;
  transport?: () => VueEventTransport | null;
  activity?: (source: VueEventSource, descriptor: EventComponentClass) => VueEventActivity;
}

export interface VueEventRuntimeConfig {
  csrf?: { cookie?: string; header?: string; token?: string | (() => string) };
  timeout?: number;
  url?: string;
}

/**
 * The request the built-in fetch transport would send for one call.
 *
 * A custom transport receives it beside the envelope so a server-side bridge
 * can rebuild the same HTTP request: the Vue app, occurrence and revision
 * headers are what let the server answer with a Render action.
 */
export interface VueEventTransportRequest {
  url: string;
  method: string;
  headers: Record<string, string>;
  signal: AbortSignal;
}

export interface VueEventTransport {
  send(envelope: unknown, request: VueEventTransportRequest): Promise<unknown> | unknown;
}

export interface VueEventSend {
  source: VueEventSource;
  handler: string;
  args?: JsonObject;
  /**
   * `"form"` when the runtime read `args` from a form's controls, so the server binds their text
   * like a form posted without JavaScript. Page code that writes its own JSON args leaves it out.
   */
  argsSource?: EventArgsSource;
  stateUpdates?: JsonObject;
  /** The caller's `opts` as given; `send` checks it and keeps its own copy. */
  options?: unknown;
}

/** Name a value for an error message without a step that could throw on it, as JSON.stringify can. */
const describeValue = (value: unknown): string =>
  typeof value === "string" ? JSON.stringify(value) : typeof value === "number" ? String(value) : `a ${typeof value}`;

/** The `opts` values the bridge keeps after `checkSendOptions` accepted them. */
interface CheckedSendOptions {
  timeout?: number;
  /** `false` sends the call at once, outside the queue; only a detached handler accepts it. */
  wait?: false;
}

/**
 * Check the `opts` a page passed to `$sendEvent` or `Citry.events.send` and copy the values the
 * bridge reads, so a caller that changes its object while the call waits in line changes nothing.
 *
 * `wait` is `true` (the default) or `false`. This function checks only the type: `send` checks that
 * the handler is declared `@event(detached=True)`, because only `send` has the handler's descriptor.
 */
const checkSendOptions = (value: unknown): CheckedSendOptions | undefined => {
  if (value === undefined) return undefined;
  if (value === null || typeof value !== "object" || Array.isArray(value))
    throw new TypeError("Citry Events send options must be an object, such as {timeout: 5000}.");
  for (const key of Object.keys(value)) {
    if (key !== "timeout" && key !== "wait")
      throw new TypeError(`Citry Events send got an unknown option '${key}'; the options are 'timeout' and 'wait'.`);
  }
  const { timeout, wait } = value as { timeout?: unknown; wait?: unknown };
  if (wait !== undefined && wait !== true && wait !== false)
    throw new TypeError(`Citry Events option 'wait' must be true or false; got ${describeValue(wait)}.`);
  if (timeout !== undefined && (typeof timeout !== "number" || !Number.isFinite(timeout) || timeout <= 0))
    throw new Error("Citry Events timeout must be a positive finite number.");
  const checked: CheckedSendOptions = {};
  if (timeout !== undefined) checked.timeout = timeout;
  if (wait === false) checked.wait = false;
  return checked;
};

/**
 * The TypeError for `wait: false` on a handler that may render or change State. Queued calls go
 * out one at a time because each server render is built on the app revision the browser held when
 * it sent the call, and each call carries the State token the previous call returned. A call that
 * skipped ahead could come back built on a page state that no longer exists.
 */
const queuedHandlerError = (handler: string): TypeError =>
  new TypeError(
    `Citry Events option 'wait: false' needs a detached handler, and '${handler}' is not one. Calls ` +
      "from one Vue app are sent one at a time, in order, because each render and State change builds " +
      "on the one before it. Remove 'wait: false', or declare the handler with @event(detached=True) " +
      "if it never renders or changes State. To replace an older call to the same handler instead, " +
      "declare it with @event(latest_wins=True).",
  );

export interface VueEventActivity {
  enqueue(handler: string): unknown;
  start(intent: unknown): void;
  succeed(intent: unknown): void;
  fail(
    intent: unknown,
    error: { status: number; code: string; message: string; fieldErrors?: Record<string, string> },
  ): void;
  finish(intent: unknown): void;
}

const validContext = (value: VueEventContext): boolean =>
  value !== null &&
  typeof value === "object" &&
  Object.keys(value).sort().join("|") === "componentClassId|descriptor|publicState|serverRenderId|stateToken" &&
  validateStrictJson(value) === null &&
  typeof value.serverRenderId === "string" &&
  value.serverRenderId.length > 0 &&
  (value.stateToken === null || (typeof value.stateToken === "string" && value.stateToken.length > 0)) &&
  typeof value.componentClassId === "string" &&
  value.componentClassId.length > 0 &&
  validateDescriptor(value.descriptor) === null &&
  value.descriptor.componentClassId === value.componentClassId;

class VueEventCancellation extends Error {}
class VueEventStale extends VueEventCancellation {
  readonly reason: string;

  constructor(reason: string) {
    super(
      reason === "disposed"
        ? "The Vue Events bridge was disposed; the source is stale or retired."
        : reason === "superseded"
          ? "The Vue event call was superseded by a newer call."
          : "The Vue event source is stale or retired.",
    );
    this.reason = reason;
  }
}
const stale = (reason = "retired"): Error => new VueEventStale(reason);

const activityError = (error: unknown) => {
  if (
    error !== null &&
    typeof error === "object" &&
    "status" in error &&
    typeof error.status === "number" &&
    "code" in error &&
    typeof error.code === "string" &&
    "message" in error &&
    typeof error.message === "string"
  )
    return error as { status: number; code: string; message: string; fieldErrors?: Record<string, string> };
  const message = error instanceof Error ? error.message : "The Vue event request failed.";
  return { status: 0, code: message === "The Vue event request timed out." ? "timeout" : "transport", message };
};

const eventUrl = (base: string, context: VueEventContext, handler: string): string => {
  if (typeof base !== "string" || !base.endsWith("/") || base.includes("?") || base.includes("#")) {
    throw new Error("Vue Events eventBaseUrl must be a path ending in '/'.");
  }
  return `${base}${encodeURIComponent(context.componentClassId)}/${encodeURIComponent(handler)}`;
};

const configuredEventRoutes = (url: string, endpoint: string, eventBaseUrl: string | undefined) => {
  if (typeof url !== "string" || url.length === 0) return { endpoint, eventBaseUrl };
  if (url.includes("?") || url.includes("#")) throw new Error("Citry Events url must not contain a query or fragment.");
  const normalized = url.endsWith("/") ? url : `${url}/`;
  if (normalized.endsWith("/call/")) {
    return { endpoint: normalized.slice(0, -1), eventBaseUrl: `${normalized.slice(0, -5)}e/` };
  }
  if (normalized.endsWith("/e/")) {
    return { endpoint: `${normalized.slice(0, -2)}call`, eventBaseUrl: normalized };
  }
  return { endpoint: `${normalized}call`, eventBaseUrl: `${normalized}e/` };
};

const readCookie = (name: string): string => {
  if (typeof document === "undefined" || typeof document.cookie !== "string") return "";
  const item = document.cookie
    .split(";")
    .map((value) => value.trim())
    .find((value) => value.startsWith(`${name}=`));
  return item ? decodeURIComponent(item.slice(name.length + 1)) : "";
};

const isWellFormedUtf16 = (value: string): boolean => {
  for (let index = 0; index < value.length; index += 1) {
    const unit = value.charCodeAt(index);
    if (unit >= 0xd800 && unit <= 0xdbff) {
      const next = value.charCodeAt(index + 1);
      if (!(next >= 0xdc00 && next <= 0xdfff)) return false;
      index += 1;
    } else if (unit >= 0xdc00 && unit <= 0xdfff) return false;
  }
  return true;
};

const flatQuery = (args: JsonObject): URLSearchParams => {
  const query = new URLSearchParams();
  const append = (key: string, value: JsonValue): void => {
    if (typeof value === "string") {
      if (!isWellFormedUtf16(value)) throw new Error(`Event argument '${key}' is not well-formed UTF-16.`);
      query.append(key, value);
    } else if (typeof value === "boolean") query.append(key, String(value));
    else if (typeof value === "number" && Number.isFinite(value)) query.append(key, String(value));
    else throw new Error(`Event argument '${key}' has no flat GET query representation.`);
  };
  for (const [key, value] of Object.entries(args)) {
    if (!isWellFormedUtf16(key)) throw new Error("Event argument name is not well-formed UTF-16.");
    if (key.startsWith("_citry_")) throw new Error(`Event argument '${key}' uses a reserved GET query name.`);
    if (Array.isArray(value)) {
      if (value.length === 0) throw new Error(`Event argument '${key}' has no flat GET query representation.`);
      for (const item of value) append(key, item);
    } else append(key, value);
  }
  return query;
};

const attachmentFilename = (value: string): string => {
  const extended = /(?:^|;)\s*filename\*\s*=\s*([^;]+)/i.exec(value)?.[1]?.trim();
  if (extended !== undefined) {
    const encoded = /^UTF-8''(.+)$/i.exec(extended)?.[1];
    if (!encoded) throw new Error("The attachment response has an unsupported encoded filename.");
    try {
      return decodeURIComponent(encoded);
    } catch {
      throw new Error("The attachment response has an invalid encoded filename.");
    }
  }
  const quoted = /(?:^|;)\s*filename\s*=\s*"((?:\\.|[^"\\])*)"/i.exec(value)?.[1];
  if (quoted !== undefined) return quoted.replace(/\\(.)/g, "$1") || "download";
  const token = /(?:^|;)\s*filename\s*=\s*([!#$%&'*+.^_`|~0-9A-Za-z-]+)/i.exec(value)?.[1];
  return token || "download";
};

const saveAttachment = (blob: Blob, filename: string): void => {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  try {
    anchor.href = url;
    anchor.download = filename;
    anchor.style.display = "none";
    document.body.append(anchor);
    anchor.click();
  } finally {
    anchor.remove();
    URL.revokeObjectURL(url);
  }
};

/**
 * Create the prepared-tree bridge. Queued calls go out one at a time. A call made with
 * `wait: false` to a detached handler goes out at once, outside the queue. An action the server
 * marked `wait: false` runs on its own, so a callback that sends a new call cannot wait on itself.
 */
export const createVueEventsBridge = (options: VueEventsBridgeOptions) => {
  const reportableFailures = new WeakSet<object>();
  const handledFailures = new WeakSet<object>();
  const fetchImpl = options.fetch ?? globalThis.fetch.bind(globalThis);
  let correlation = 0;
  type Owner = {
    generation: number;
    sendSequence: number;
    acceptedEpoch: number;
    retired: boolean;
    timers: Map<ReturnType<typeof globalThis.setTimeout>, (error: Error) => void>;
  };
  type Job = {
    input: VueEventSend;
    owner?: Owner;
    controller?: AbortController;
    committingTransaction?: unknown;
    acceptedRemount: boolean;
    activity?: VueEventActivity;
    intent?: unknown;
    activityFinished: boolean;
    lifecycleStarted: boolean;
    external: boolean;
    callerRenderId?: string;
    stateUpdates?: JsonObject;
    stateAccepted: boolean;
    // How many results the bridge had accepted at the caller's spot on the page, this call's own
    // included, when this call's result was accepted (see `acceptedAtSpot`).
    acceptedAtSpotWhenAccepted?: number;
    settled: boolean;
    // The error the call was cancelled with (superseded, retired, or disposed). Once set, none of
    // the call's remaining actions start.
    cancelError?: Error;
    // How many of the call's `wait: false` actions are scheduled and have not finished yet.
    noWaitPending: number;
    // The handler is declared `@event(detached=True)`; set once the call is sent.
    detachedHandler?: boolean;
    cancelled: Promise<never>;
    cancel(error: Error): void;
    resolve(value: JsonValue | undefined): void;
    reject(error: unknown): void;
  };
  const owners = new Map<string, Owner>();
  // How many results the bridge accepted at each spot on the page (`stableId`), whichever component
  // instance was mounted there. A call whose own Render replaced the caller compares this count,
  // because the new component's results raise only the new instance's `acceptedEpoch`.
  const acceptedAtSpot = new Map<string, number>();
  const acceptAtSpot = (source: VueEventSource, job: Job): void => {
    const count = (acceptedAtSpot.get(source.stableId) ?? 0) + 1;
    acceptedAtSpot.set(source.stableId, count);
    job.acceptedAtSpotWhenAccepted = count;
  };
  const queue: Job[] = [];
  let active: Job | null = null;
  // Calls that page code applies with `applyActions` run outside the queue, so `active` never names them.
  const externalJobs = new Set<Job>();
  // Calls, finished or not, whose `wait: false` actions have not finished yet. A newer call under
  // `latestCallWins` cancels these too, so those actions never start.
  const jobsWithNoWaitActions = new Set<Job>();
  // Calls sent with `wait: false` to a detached handler that have not settled yet. They run outside
  // the queue, so `active` never names them, and retire, dispose and supersede reach them here.
  const detachedCalls = new Set<Job>();
  let running = false;
  let disposed = false;

  const supersedeEarlier = (input: VueEventSend): void => {
    const error = stale("superseded");
    const sameCall = (job: Job): boolean =>
      job.input.source.stableId === input.source.stableId &&
      job.input.source.generation === input.source.generation &&
      job.input.handler === input.handler;
    // Each pending action of these calls reports its own `stale` when its delay is cancelled.
    for (const job of jobsWithNoWaitActions) if (sameCall(job)) job.cancel(error);
    // A detached call in flight reports its own `stale` when its send rejects.
    for (const job of detachedCalls) if (sameCall(job)) job.cancel(error);
    for (let index = queue.length - 1; index >= 0; index -= 1) {
      const job = queue[index];
      if (
        job.input.source.stableId === input.source.stableId &&
        job.input.source.generation === input.source.generation &&
        job.input.handler === input.handler
      ) {
        queue.splice(index, 1);
        lifecycle("stale", job.input.source, job.input.handler, { reason: "superseded" });
        job.cancel(error);
      }
    }
    if (
      active &&
      active.input.source.stableId === input.source.stableId &&
      active.input.source.generation === input.source.generation &&
      active.input.handler === input.handler
    )
      active.cancel(error);
  };

  const lifecycle = (
    kind: "before" | "after" | "error" | "swapped" | "stale",
    source: VueEventSource,
    event: string,
    detail?: JsonObject,
  ): boolean => {
    try {
      return options.host.lifecycle?.(kind, source, event, detail) !== false;
    } catch (error) {
      // A lifecycle observer is an integration hook. Its failure must not
      // turn a committed server result into a failed Events call.
      console.error(`[Citry] citry:events:${kind} listener failed:`, error);
      return true;
    }
  };

  const ownerState = (source: VueEventSource) => {
    const existing = owners.get(source.stableId);
    if (existing?.generation === source.generation) return existing;
    const state: Owner = {
      generation: source.generation,
      sendSequence: 0,
      acceptedEpoch: 0,
      retired: false,
      timers: new Map(),
    };
    owners.set(source.stableId, state);
    return state;
  };

  const current = (source: VueEventSource): VueEventContext => {
    const context = options.host.resolve(source);
    if (context === null || !validContext(context)) throw stale("retired");
    return context;
  };

  const stillCurrent = (source: VueEventSource, state: Owner, epoch?: number): void => {
    if (
      state.retired ||
      owners.get(source.stableId) !== state ||
      state.generation !== source.generation ||
      (epoch !== undefined && epoch !== state.acceptedEpoch)
    ) {
      throw stale(state.retired ? "retired" : "epoch");
    }
    current(source);
  };

  // Timers of a call whose own Render remounted its sender. The retired sender's timers are
  // cancelled with it, but this call's response was accepted, so its later actions keep their
  // timers here. When each fires, `continuationCurrent` drops it if a newer result arrived at the
  // sender's spot (a redirect still runs). Only disposing the bridge cancels these timers.
  const remountTimers = new Map<ReturnType<typeof globalThis.setTimeout>, (error: unknown) => void>();
  // Timers of `applyActions` calls made without a component, which no component record owns; only
  // disposing the bridge stops them.
  const sourcelessTimers = new Map<ReturnType<typeof globalThis.setTimeout>, (error: unknown) => void>();

  const delay = (milliseconds: number, state: Owner, job: Job): Promise<void> =>
    new Promise((resolve, reject) => {
      if (job.cancelError) {
        reject(job.cancelError);
        return;
      }
      if (disposed || (state.retired && !job.acceptedRemount)) {
        reject(stale(disposed ? "disposed" : "retired"));
        return;
      }
      const timers = job.acceptedRemount ? remountTimers : state.timers;
      const timer = globalThis.setTimeout(() => {
        timers.delete(timer);
        resolve();
      }, milliseconds);
      timers.set(timer, reject);
      // A cancelled call stops waiting at once: a blocking delay would otherwise hold back the
      // newer call queued behind it, and a detached one would still run its action later.
      void job.cancelled.catch((error: unknown) => {
        if (!timers.delete(timer)) return;
        globalThis.clearTimeout(timer);
        reject(error);
      });
    });

  const continuationCurrent = (
    source: VueEventSource,
    state: Owner,
    epoch: number,
    job: Job,
    survivesNewerResult = false,
  ): void => {
    // The accepted-result count does not move when a newer call supersedes this one, because the
    // newer call is still waiting in the queue, so the cancellation itself is checked first.
    if (job.cancelError) throw job.cancelError;
    if (disposed) throw stale("disposed");
    // A redirect reports a result the server already produced, such as "saved, now go to the
    // list", which a newer result does not replace, so it runs even after one. The other actions
    // only adjust a page that the newer result has already replaced, so they are dropped.
    if (!survivesNewerResult && epoch !== state.acceptedEpoch) throw stale("epoch");
    if (!job.acceptedRemount) {
      stillCurrent(source, state, survivesNewerResult ? undefined : epoch);
      return;
    }
    // This call's own Render replaced the caller, so the new component's results raise only the
    // new instance's count; the count for the spot on the page shows them.
    if (!survivesNewerResult && acceptedAtSpot.get(source.stableId) !== job.acceptedAtSpotWhenAccepted) {
      throw stale("epoch");
    }
  };

  const validateTargets = (result: EventResult, source: VueEventSource, serverRenderId: string): void => {
    if (!result.ok) return;
    const componentTarget = `render:${serverRenderId}`;
    for (const action of result.actions) {
      if (action.action === "render" && !options.host.preflightResult && action.target !== componentTarget) {
        throw new Error("Vue Events accepts the current component target; marker targets are not implemented.");
      }
      if (action.action === "event" && action.target !== undefined && action.target !== componentTarget) {
        throw new Error("Vue Events accepts the current component Event target; marker targets are not implemented.");
      }
    }
    current(source);
  };

  const applyOne = async (
    action: EventAction,
    source: VueEventSource,
    state: Owner,
    epoch: number,
    onData: (value: JsonValue) => void,
    job: Job,
    renderPlan?: unknown,
  ) => {
    if (action.action === "data") {
      if (!job.external) continuationCurrent(source, state, epoch, job);
      onData(action.value);
      return;
    }
    if (action.action === "render") {
      if (job.cancelError) throw job.cancelError;
      stillCurrent(source, state, epoch);
      const context = current(source);
      if (!renderPlan && action.target !== `render:${context.serverRenderId}`) {
        throw new Error("The experimental Vue Events bridge accepts only its current root Render target.");
      }
      if (!("renderer" in action) || action.renderer !== "vue-prepared/1") {
        throw new Error("The Vue Events bridge requires a vue-prepared/1 Render action.");
      }
      const preparing = options.host.prepareRender(
        action,
        source,
        job.controller?.signal ?? new AbortController().signal,
        renderPlan,
      );
      let prepared: PreparedVueRender;
      try {
        prepared = await Promise.race([preparing, job.cancelled]);
        stillCurrent(source, state, epoch);
      } catch (error) {
        try {
          options.host.abortRender(undefined, source);
        } catch (cleanupError) {
          console.error("[Citry] aborting a prepared Vue render failed:", cleanupError);
        }
        void preparing.then(
          (value) => {
            try {
              options.host.abortRender(value, source);
            } catch (cleanupError) {
              console.error("[Citry] aborting a late prepared Vue render failed:", cleanupError);
            }
          },
          () => undefined,
        );
        throw error;
      }
      job.committingTransaction = prepared.transaction;
      try {
        await Promise.race([options.host.commitRender(prepared, source), job.cancelled]);
        // The host replaces the placeholder with the actual roots after the
        // commit. Keeping the field here preserves the bridge contract for
        // hosts that do not have a DOM-specific implementation.
        lifecycle("swapped", source, job.input.handler, { els: [] });
      } finally {
        job.committingTransaction = undefined;
      }
    } else if (action.action === "state") {
      // After an accepted remount the host stores the refresh only if an instance still carries
      // this render ID, so a refresh for a component the Render replaced changes nothing.
      continuationCurrent(source, state, epoch, job);
      options.host.commitState(action.targetRenderId, action.stateToken, action.publicState, source);
    } else if (action.action === "event") {
      // A Render earlier in this response may have remounted the caller, possibly as another
      // component. That retires the calling instance, but the response was accepted, so the event
      // still goes out, from whatever the page now shows at the caller's place, unless a newer
      // result arrived there first.
      continuationCurrent(source, state, epoch, job);
      const followRemount = job.acceptedRemount;
      // The retired instance has no current context, so after a remount only the caller's own
      // render ID from the call identifies the caller.
      const rootTarget = followRemount ? undefined : `render:${current(source).serverRenderId}`;
      const callerTarget = job.callerRenderId === undefined ? undefined : `render:${job.callerRenderId}`;
      if (action.target !== undefined && action.target !== rootTarget && action.target !== callerTarget) {
        throw new Error("The experimental Vue Events bridge accepts only its current root Event target.");
      }
      if (job.external && action.target === undefined && options.host.dispatchEventGlobal)
        options.host.dispatchEventGlobal(action.eventName, action.detail);
      else options.host.dispatchEvent(action.eventName, action.detail, source, followRemount);
    } else if (action.action === "redirect") {
      if (!job.external) continuationCurrent(source, state, epoch, job, true);
      options.host.redirect(action.url);
    } else {
      if (!job.external) continuationCurrent(source, state, epoch, job);
      options.host.updateUrl(action.url, action.mode);
    }
  };

  const applyActions = async (
    result: EventResult,
    source: VueEventSource,
    state: Owner,
    epoch: number,
    job: Job,
    renderPlan?: unknown,
  ): Promise<JsonValue | undefined> => {
    if (!result.ok) {
      reportableFailures.add(result.error);
      throw result.error;
    }
    let data: JsonValue | undefined;
    const hoisted = new Set<number>();
    result.actions.forEach((action, index) => {
      if (
        action.action === "state" &&
        !(typeof action.delay === "number" && action.delay > 0) &&
        action.wait !== false
      ) {
        // A State commit can run page code that supersedes this call.
        if (job.cancelError) throw job.cancelError;
        stillCurrent(source, state, epoch);
        options.host.commitState(action.targetRenderId, action.stateToken, action.publicState, source);
        hoisted.add(index);
      }
    });
    for (const [index, action] of result.actions.entries()) {
      if (hoisted.has(index)) continue;
      const run = async () => {
        const seconds = typeof action.delay === "number" ? action.delay : 0;
        const delayed = seconds > 0;
        if (delayed) await delay(seconds * 1000, state, job);
        // A detached result renders nothing and changes no State, so a queued result accepted between
        // its actions does not replace it, and its actions without a delay still run. An action that
        // waited on a delay follows the usual newer-result rule.
        const actionEpoch = job.detachedHandler && !delayed ? state.acceptedEpoch : epoch;
        await applyOne(
          action,
          source,
          state,
          actionEpoch,
          (value) => {
            data = value;
          },
          job,
          action.action === "render" ? renderPlan : undefined,
        );
      };
      if ("wait" in action && action.wait === false) {
        job.noWaitPending += 1;
        jobsWithNoWaitActions.add(job);
        void run()
          .catch((error) => {
            if (error instanceof VueEventStale) {
              // An expected outcome, reported to listeners; nothing failed.
              lifecycle("stale", source, job.input.handler, { reason: error.reason });
              return;
            }
            if (!(error instanceof VueEventCancellation)) {
              lifecycle("error", source, job.input.handler, { error: activityError(error) as JsonObject });
            }
            console.error("[Citry] applying a Vue event action marked wait: false failed:", error);
          })
          .finally(() => {
            job.noWaitPending -= 1;
            if (job.noWaitPending === 0) jobsWithNoWaitActions.delete(job);
          });
      } else await run();
    }
    return data;
  };

  const sendNow = async (job: Job): Promise<JsonValue | undefined> => {
    const input = job.input;
    if (disposed) throw stale("disposed");
    const context = current(input.source);
    const state = ownerState(input.source);
    job.owner = state;
    const appId = options.host.appId(input.source);
    if (typeof appId !== "string" || appId.length === 0) throw stale("retired");
    const committedRevision = options.host.revision(input.source);
    if (!Number.isInteger(committedRevision) || committedRevision < 0) throw stale("retired");
    if (!Object.prototype.hasOwnProperty.call(context.descriptor.eventHandlers, input.handler))
      throw new Error(`Unknown event handler '${input.handler}'.`);
    const handlerOptions = context.descriptor.eventHandlers[input.handler];
    // A detached handler can neither replace the caller's HTML nor its State, so its result never
    // counts as a newer result for the caller, whether the call went out queued or not.
    const detachedHandler = handlerOptions.detached === true;
    job.detachedHandler = detachedHandler;
    job.callerRenderId = context.serverRenderId;
    job.lifecycleStarted = true;
    if (!lifecycle("before", input.source, input.handler))
      throw new VueEventCancellation(`Citry Events send '${input.handler}' was cancelled by citry:events:before.`);
    const useGet = handlerOptions.httpMethod === "GET";
    const runtimeConfig = options.runtimeConfig?.() ?? {};
    const configuredEndpoint =
      typeof options.endpoint === "function" && !useGet
        ? options.endpoint(context, input.handler)
        : typeof options.endpoint === "string"
          ? options.endpoint
          : "";
    const routes = configuredEventRoutes(runtimeConfig.url ?? "", configuredEndpoint, options.eventBaseUrl);
    if (useGet && input.stateUpdates !== undefined) throw new Error("GET events cannot send pending State updates.");
    // A detached handler returns no new State token, so pending browser State writes stay pending
    // for the next call to a handler that is not detached instead of riding on this one and being lost.
    const taken =
      useGet || detachedHandler
        ? undefined
        : (input.stateUpdates ?? options.host.takePendingState?.(input.source, input.handler));
    job.stateUpdates = taken === undefined ? undefined : structuredClone(taken);
    state.sendSequence += 1;
    correlation += 1;
    const call = buildCall({
      componentClassId: context.componentClassId,
      handlerName: input.handler,
      callerRenderId: context.serverRenderId,
      args: input.args ?? {},
      // A GET query leaves the mark out: the server already reads every
      // query value as text, so only the JSON call needs to say so.
      argsSource: input.argsSource,
      stateToken: context.stateToken ?? undefined,
      stateUpdates: job.stateUpdates,
      sendSequence: state.sendSequence,
    });
    const envelope = buildCallEnvelope(`vue_${correlation}`, [call], {
      actions: ["render", "data", "state", "event", "redirect", "url"],
      swaps: ["morph"],
      renderers: ["vue-prepared/1"],
    });
    const headers: Record<string, string> = {
      "Content-Type": "application/citry-events+json",
      "X-Citry-Events": "1",
      "X-Citry-Vue-App": appId,
      "X-Citry-Vue-Occurrence": input.source.stableId,
      "X-Citry-Vue-Revision": String(committedRevision),
    };
    const selectedTransport = options.transport?.() ?? null;
    const csrf = runtimeConfig.csrf ?? options.csrf;
    if (!useGet && csrf) {
      // A custom transport forwards only a token the page configured. The
      // playground transport runs inside an opaque sandbox where reading
      // document.cookie throws, so the cookie fallback is for fetch alone.
      const token = csrf.token
        ? typeof csrf.token === "function"
          ? csrf.token()
          : csrf.token
        : selectedTransport
          ? undefined
          : readCookie(csrf.cookie ?? "csrftoken");
      if (token) headers[csrf.header ?? "X-CSRFToken"] = token;
    }
    // The Vue bridge currently serializes queued jobs and emits one-call
    // envelopes. `allowBatching` therefore selects the per-event route for
    // isolated handlers; it does not yet implement same-tick multi-call
    // envelope/dependency scheduling.
    const isolated = useGet || handlerOptions.allowBatching === false;
    const endpoint = isolated ? eventUrl(routes.eventBaseUrl ?? "", context, input.handler) : routes.endpoint;
    // `send` replaced the caller's options with the checked copy.
    const callTimeout = (input.options as { timeout?: number } | undefined)?.timeout;
    const timeoutMs = callTimeout ?? runtimeConfig.timeout ?? options.timeoutMs ?? 30_000;
    if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) throw new Error("Vue Events timeoutMs must be positive.");
    const controller = new AbortController();
    job.controller = controller;
    let requestUrl = endpoint;
    if (useGet) {
      const query = flatQuery(input.args ?? {});
      query.append("_citry_protocol", envelope.protocol);
      query.append("_citry_request_id", envelope.requestId);
      query.append("_citry_capabilities", JSON.stringify(envelope.capabilities));
      query.append("_citry_caller_render_id", call.callerRenderId ?? "");
      query.append("_citry_send_sequence", String(call.sendSequence));
      if (handlerOptions.usesState === true && call.stateToken !== undefined)
        query.append("_citry_state_token", call.stateToken);
      requestUrl += `?${query.toString()}`;
    }
    const requestHeaders = useGet
      ? Object.fromEntries(Object.entries(headers).filter(([name]) => name !== "Content-Type"))
      : headers;
    const requestMethod = isolated ? handlerOptions.httpMethod : "POST";
    const operation = (async (): Promise<
      { raw: unknown; transported?: true } | { attachment: Blob; filename: string }
    > => {
      if (selectedTransport) {
        // The server needs the same app, occurrence and revision headers the
        // fetch path sends to build a Render action, so a custom transport
        // gets its own copy of that request to forward.
        const request: VueEventTransportRequest = {
          url: requestUrl,
          method: requestMethod,
          headers: { ...requestHeaders },
          signal: controller.signal,
        };
        try {
          return { raw: await selectedTransport.send(envelope, request), transported: true };
        } catch (error) {
          if (error !== null && typeof error === "object") reportableFailures.add(error);
          throw error;
        }
      }
      const requestInit: RequestInit = {
        method: requestMethod,
        credentials: "same-origin",
        headers: requestHeaders,
        ...(useGet ? {} : { body: JSON.stringify(envelope) }),
        signal: controller.signal,
      };
      let response: Response;
      try {
        response = await fetchImpl(requestUrl, requestInit);
      } catch (error) {
        if (error !== null && typeof error === "object") reportableFailures.add(error);
        throw error;
      }
      const disposition = response.headers?.get?.("Content-Disposition") ?? null;
      if (response.ok && disposition && /^\s*attachment(?:;|$)/i.test(disposition)) {
        return { attachment: await response.blob(), filename: attachmentFilename(disposition) };
      }
      try {
        const raw: unknown = await response.json();
        return { raw };
      } catch (error) {
        if (response.ok) throw new Error("A successful raw Event response must be an attachment.");
        throw error;
      }
    })();
    let timeoutId = 0;
    const received = await Promise.race([
      operation,
      job.cancelled,
      new Promise<never>((_resolve, reject) => {
        timeoutId = globalThis.setTimeout(() => {
          controller.abort();
          const error = new Error("The Vue event request timed out.");
          reportableFailures.add(error);
          reject(error);
        }, timeoutMs);
      }),
    ]).finally(() => globalThis.clearTimeout(timeoutId));
    if ("attachment" in received) {
      stillCurrent(input.source, state);
      if (!detachedHandler) {
        state.acceptedEpoch += 1;
        acceptAtSpot(input.source, job);
      }
      continuationCurrent(input.source, state, state.acceptedEpoch, job);
      saveAttachment(received.attachment, received.filename);
      return undefined;
    }
    const raw = received.raw;
    const checked = preflightResultEnvelope(raw, envelope);
    if (!checked.ok) throw new Error(`Invalid Events response: ${checked.issue.message}`);
    // The host may freeze and keep the result it is given. The browser's fetch parses a fresh object
    // for this call, but code behind a custom transport may still hold its object, so copy that one.
    const [result] = received.transported ? copyJson(checked.results) : checked.results;
    if (detachedHandler && result.ok) {
      // Checked before any action runs: the server should never send these, and applying one
      // would replace HTML or a State token that a queued call may already have changed.
      const forbidden = result.actions.find((action) => action.action === "render" || action.action === "state");
      if (forbidden)
        throw new Error(
          `Invalid Events response: detached handler '${input.handler}' returned a '${forbidden.action}' action.`,
        );
    }
    stillCurrent(input.source, state);
    validateTargets(result, input.source, context.serverRenderId);
    const preparedResult = options.host.preflightResult?.(result, input.source) ?? { result };
    // Preflight runs page code, which may supersede this call. Checked before the counts move, so
    // a cancelled result does not count as a newer result for the component.
    if (job.cancelError) throw job.cancelError;
    if (!detachedHandler) {
      state.acceptedEpoch += 1;
      acceptAtSpot(input.source, job);
    }
    // The server has consumed the dequeued State draft once the complete
    // response/result/target preflight succeeds.  Mark that transaction
    // accepted before interpreting its actions: a later action may fail after
    // an earlier State or Render action has already reached the browser, and
    // restoring the draft in that case would resend data the server already
    // processed.
    if (preparedResult.result.ok) job.stateAccepted = true;
    return applyActions(
      preparedResult.result,
      input.source,
      state,
      state.acceptedEpoch,
      job,
      preparedResult.renderPlan,
    );
  };

  // Sends one call and settles its promise. The queue runs queued calls through it one at a time,
  // and `send` runs a detached call through it at once.
  const runJob = async (job: Job): Promise<void> => {
    try {
      job.activity?.start(job.intent);
      const value = await sendNow(job);
      // A call cancelled after its last action ran still reports as cancelled, not as a
      // success: its caller's promise has already rejected.
      if (job.cancelError) throw job.cancelError;
      job.stateAccepted = true;
      job.activity?.succeed(job.intent);
      if (job.lifecycleStarted) lifecycle("after", job.input.source, job.input.handler, { ok: true });
      job.resolve(value);
    } catch (error) {
      if (!job.stateAccepted && job.stateUpdates !== undefined)
        options.host.restorePendingState?.(job.input.source, job.stateUpdates);
      if (job.lifecycleStarted) {
        if (error instanceof VueEventStale) {
          lifecycle("stale", job.input.source, job.input.handler, { reason: error.reason });
        } else if (!(error instanceof VueEventCancellation)) {
          // The server answers `stale_state` when the page's State token no longer verifies, which is
          // what a deploy does to an open page. Reported before `error`, and a listener may cancel it
          // to replace the reload prompt; the call still rejects with the server's error either way.
          if (
            activityError(error).code === "stale_state" &&
            lifecycle("stale", job.input.source, job.input.handler, { reason: "version" })
          )
            options.host.promptReload?.();
          lifecycle("error", job.input.source, job.input.handler, {
            error: activityError(error) as JsonObject,
          });
        }
        lifecycle("after", job.input.source, job.input.handler, { ok: false });
      }
      if (!(error instanceof VueEventCancellation)) {
        job.activity?.fail(job.intent, activityError(error));
        if (job.activity && error !== null && typeof error === "object" && reportableFailures.has(error))
          handledFailures.add(error);
      }
      job.reject(error);
    } finally {
      if (!job.activityFinished) {
        job.activityFinished = true;
        job.activity?.finish(job.intent);
      }
    }
  };

  const runQueue = async (): Promise<void> => {
    if (running) return;
    running = true;
    try {
      while (queue.length > 0) {
        const job = queue.shift();
        if (!job || job.settled) continue;
        active = job;
        try {
          await runJob(job);
        } finally {
          active = null;
        }
      }
    } finally {
      running = false;
    }
  };

  const unsupportedBrowserMethods = new Set(["HEAD", "OPTIONS", "CONNECT", "TRACE", "TRACK"]);

  const send = (given: VueEventSend): Promise<JsonValue | undefined> => {
    if (disposed) return Promise.reject(stale("disposed"));
    let activity: VueEventActivity | undefined;
    let intent: unknown;
    let input = given;
    let outsideQueue = false;
    try {
      // Checked before the call is queued, so a bad option rejects without reaching the server.
      input = { ...given, options: checkSendOptions(given.options) };
      const context = current(input.source);
      if (!Object.prototype.hasOwnProperty.call(context.descriptor.eventHandlers, input.handler))
        throw new Error(`Unknown event handler '${input.handler}'.`);
      const method = context.descriptor.eventHandlers[input.handler].httpMethod;
      if (unsupportedBrowserMethods.has(method))
        throw new Error(
          `Event handler '${input.handler}' uses HTTP ${method}, which is server-transport-only and cannot be sent by the browser bridge.`,
        );
      const handlerOptions = context.descriptor.eventHandlers[input.handler];
      outsideQueue = (input.options as CheckedSendOptions | undefined)?.wait === false;
      if (outsideQueue && handlerOptions.detached !== true) throw queuedHandlerError(input.handler);
      // The server would refuse these, since a detached handler cannot change State.
      if (handlerOptions.detached === true && input.stateUpdates !== undefined)
        throw new TypeError(`Event handler '${input.handler}' is detached, so a call to it cannot send State updates.`);
      activity = options.activity?.(input.source, context.descriptor);
      intent = activity?.enqueue(input.handler);
      if (handlerOptions.latestCallWins === true) supersedeEarlier(input);
    } catch (error) {
      return Promise.reject(error);
    }
    let resolvePromise!: (value: JsonValue | undefined) => void;
    let rejectPromise!: (error: unknown) => void;
    let cancelPromise!: (error: Error) => void;
    const promise = new Promise<JsonValue | undefined>((resolve, reject) => {
      resolvePromise = resolve;
      rejectPromise = reject;
    });
    const cancelled = new Promise<never>((_resolve, reject) => {
      cancelPromise = reject;
    });
    void cancelled.catch(() => undefined);
    const job: Job = {
      input,
      acceptedRemount: false,
      noWaitPending: 0,
      activity,
      intent,
      activityFinished: false,
      lifecycleStarted: false,
      external: false,
      stateAccepted: false,
      settled: false,
      cancelled,
      cancel(error) {
        // A finished call can still have `wait: false` actions waiting on their delay; stopping
        // `cancelled` cancels those delays too.
        if (job.cancelError === undefined) {
          job.cancelError = error;
          cancelPromise(error);
        }
        if (job.settled) return;
        job.controller?.abort();
        if (!job.activityFinished) {
          job.activityFinished = true;
          job.activity?.finish(job.intent);
        }
        job.reject(error);
      },
      resolve(value) {
        if (job.settled) return;
        job.settled = true;
        resolvePromise(value);
      },
      reject(error) {
        if (job.settled) return;
        job.settled = true;
        rejectPromise(error);
      },
    };
    if (outsideQueue) {
      detachedCalls.add(job);
      void runJob(job).finally(() => detachedCalls.delete(job));
    } else {
      queue.push(job);
      void runQueue();
    }
    return promise;
  };

  const applyActionsExternally = async (
    actions: readonly EventAction[],
    source?: VueEventSource,
  ): Promise<JsonValue | undefined> => {
    const result = buildOkResult(actions);
    if (!source) {
      let data: JsonValue | undefined;
      for (const action of result.actions) {
        if (disposed) throw stale("disposed");
        if (typeof action.delay === "number" && action.delay > 0) {
          const milliseconds = action.delay * 1000;
          await new Promise<void>((resolve, reject) => {
            const timer = globalThis.setTimeout(() => {
              sourcelessTimers.delete(timer);
              resolve();
            }, milliseconds);
            sourcelessTimers.set(timer, reject);
          });
          if (disposed) throw stale("disposed");
        }
        if (action.action === "data") data = action.value;
        else if (action.action === "redirect") options.host.redirect(action.url);
        else if (action.action === "url") options.host.updateUrl(action.url, action.mode);
        else if (action.action === "event") {
          if (action.target !== undefined || !options.host.dispatchEventGlobal)
            throw new Error("Citry.events.applyActions needs a mounted component for targeted Event actions.");
          options.host.dispatchEventGlobal(action.eventName, action.detail);
        } else {
          throw new Error("Citry.events.applyActions needs a mounted component for Render and State actions.");
        }
      }
      return data;
    }
    const externalContext = current(source);
    const state = ownerState(source);
    state.acceptedEpoch += 1;
    const cancelled = new Promise<never>(() => undefined);
    const job = {
      input: { source, handler: "__external__" },
      acceptedRemount: false,
      noWaitPending: 0,
      activityFinished: true,
      lifecycleStarted: true,
      external: true,
      callerRenderId: externalContext.serverRenderId,
      stateAccepted: true,
      settled: true,
      cancelled,
      cancel() {},
      resolve() {},
      reject() {},
    } satisfies Job;
    const prepared = options.host.preflightResult?.(result, source) ?? { result };
    if (!lifecycle("before", source, job.input.handler)) {
      const error = new VueEventCancellation("Citry Events applyActions was cancelled by citry:events:before.");
      lifecycle("after", source, job.input.handler, { ok: false });
      throw error;
    }
    // Counted only once the actions will be applied, so a cancelled `applyActions` does not drop
    // another call's delayed actions.
    acceptAtSpot(source, job);
    // retire() marks this job when its own Render remounts the source, as it does for a sent call.
    externalJobs.add(job);
    try {
      const value = await applyActions(prepared.result, source, state, state.acceptedEpoch, job, prepared.renderPlan);
      lifecycle("after", source, job.input.handler, { ok: true });
      return value;
    } catch (error) {
      if (error instanceof VueEventStale) {
        lifecycle("stale", source, job.input.handler, { reason: error.reason });
      } else if (!(error instanceof VueEventCancellation)) {
        lifecycle("error", source, job.input.handler, { error: activityError(error) as JsonObject });
      }
      lifecycle("after", source, job.input.handler, { ok: false });
      throw error;
    } finally {
      externalJobs.delete(job);
    }
  };

  const retire = (source: VueEventSource, acceptedTransaction?: unknown): void => {
    const state = owners.get(source.stableId);
    if (state?.generation === source.generation) {
      state.retired = true;
      for (const [timer, reject] of state.timers) {
        globalThis.clearTimeout(timer);
        reject(stale("retired"));
      }
      state.timers.clear();
      owners.delete(source.stableId);
    }
    const error = new VueEventStale("retired");
    for (let index = queue.length - 1; index >= 0; index -= 1) {
      const job = queue[index];
      if (job.input.source.stableId === source.stableId && job.input.source.generation === source.generation) {
        queue.splice(index, 1);
        lifecycle("stale", source, job.input.handler, { reason: "retired" });
        job.cancel(error);
      }
    }
    // A detached call never renders, so its own render cannot be what retired the source.
    for (const job of detachedCalls)
      if (job.input.source.stableId === source.stableId && job.input.source.generation === source.generation)
        job.cancel(error);
    for (const job of externalJobs) {
      if (
        acceptedTransaction !== undefined &&
        job.committingTransaction === acceptedTransaction &&
        job.input.source.stableId === source.stableId &&
        job.input.source.generation === source.generation
      )
        job.acceptedRemount = true;
    }
    if (
      active?.input.source.stableId === source.stableId &&
      active.input.source.generation === source.generation &&
      acceptedTransaction !== undefined &&
      active.committingTransaction === acceptedTransaction
    ) {
      active.acceptedRemount = true;
    } else if (
      active?.input.source.stableId === source.stableId &&
      active.input.source.generation === source.generation
    )
      active.cancel(error);
  };

  const dispose = (): void => {
    if (disposed) return;
    disposed = true;
    for (const state of owners.values()) {
      state.retired = true;
      for (const [timer, reject] of state.timers) {
        globalThis.clearTimeout(timer);
        reject(stale("disposed"));
      }
      state.timers.clear();
    }
    owners.clear();
    acceptedAtSpot.clear();
    for (const timers of [remountTimers, sourcelessTimers]) {
      for (const [timer, reject] of timers) {
        globalThis.clearTimeout(timer);
        reject(stale("disposed"));
      }
      timers.clear();
    }
    const error = new VueEventStale("disposed");
    for (const job of queue.splice(0)) {
      lifecycle("stale", job.input.source, job.input.handler, { reason: "disposed" });
      job.cancel(error);
    }
    active?.cancel(error);
    for (const job of detachedCalls) job.cancel(error);
  };

  const isDeclarativeFailureHandled = (error: unknown): boolean =>
    error instanceof VueEventCancellation ||
    (error !== null && typeof error === "object" && handledFailures.has(error));

  return { send, applyActions: applyActionsExternally, retire, dispose, isDeclarativeFailureHandled };
};
