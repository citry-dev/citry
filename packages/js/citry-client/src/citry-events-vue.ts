/** Private citry-events/1 bridge for a Vue-owned component tree. */

import {
  assertValidActionList as assertProtocolActionList,
  buildOkResult,
  buildCall,
  buildCallEnvelope,
  preflightResultEnvelope,
  validateDescriptor,
  validateStrictJson,
  type EventAction,
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
  commitState(serverRenderId: string, stateToken: string, source: VueEventSource): void;
  dispatchEvent(name: string, detail: JsonValue | undefined, source: VueEventSource): void;
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

export interface VueEventTransport {
  send(envelope: unknown): Promise<unknown> | unknown;
}

export interface VueEventSend {
  source: VueEventSource;
  handler: string;
  args?: JsonObject;
  stateUpdates?: JsonObject;
  options?: { timeout?: number };
}

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
 * Create the prepared-tree bridge. Calls serialize, while
 * wait:false actions remain detached and cannot deadlock a callback send.
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
    settled: boolean;
    cancelled: Promise<never>;
    cancel(error: Error): void;
    resolve(value: JsonValue | undefined): void;
    reject(error: unknown): void;
  };
  const owners = new Map<string, Owner>();
  const queue: Job[] = [];
  let active: Job | null = null;
  let running = false;
  let disposed = false;

  const supersedeEarlier = (input: VueEventSend): void => {
    const error = stale("superseded");
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

  const delay = (milliseconds: number, state: Owner): Promise<void> =>
    new Promise((resolve, reject) => {
      if (state.retired || disposed) {
        reject(stale(state.retired ? "retired" : "disposed"));
        return;
      }
      const timer = globalThis.setTimeout(() => {
        state.timers.delete(timer);
        resolve();
      }, milliseconds);
      state.timers.set(timer, reject);
    });

  const continuationCurrent = (source: VueEventSource, state: Owner, epoch: number, job: Job): void => {
    if (disposed || epoch !== state.acceptedEpoch) {
      throw stale(disposed ? "disposed" : "epoch");
    }
    if (!job.acceptedRemount) stillCurrent(source, state, epoch);
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
      stillCurrent(source, state, epoch);
      options.host.commitState(action.targetRenderId, action.stateToken, source);
    } else if (action.action === "event") {
      stillCurrent(source, state, epoch);
      const rootTarget = `render:${current(source).serverRenderId}`;
      const callerTarget = job.callerRenderId === undefined ? undefined : `render:${job.callerRenderId}`;
      if (action.target !== undefined && action.target !== rootTarget && action.target !== callerTarget) {
        throw new Error("The experimental Vue Events bridge accepts only its current root Event target.");
      }
      if (job.external && action.target === undefined && options.host.dispatchEventGlobal)
        options.host.dispatchEventGlobal(action.eventName, action.detail);
      else options.host.dispatchEvent(action.eventName, action.detail, source);
    } else if (action.action === "redirect") {
      if (!job.external) continuationCurrent(source, state, epoch, job);
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
        stillCurrent(source, state, epoch);
        options.host.commitState(action.targetRenderId, action.stateToken, source);
        hoisted.add(index);
      }
    });
    for (const [index, action] of result.actions.entries()) {
      if (hoisted.has(index)) continue;
      const run = async () => {
        if (typeof action.delay === "number" && action.delay > 0) await delay(action.delay * 1000, state);
        await applyOne(
          action,
          source,
          state,
          epoch,
          (value) => {
            data = value;
          },
          job,
          action.action === "render" ? renderPlan : undefined,
        );
      };
      if ("wait" in action && action.wait === false) {
        void run().catch((error) => {
          if (error instanceof VueEventStale) {
            lifecycle("stale", source, job.input.handler, { reason: error.reason });
          } else if (!(error instanceof VueEventCancellation)) {
            lifecycle("error", source, job.input.handler, { error: activityError(error) as JsonObject });
          }
          console.error("[Citry] applying a detached Vue event action failed:", error);
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
    const taken = useGet
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
    // A custom transport owns the request boundary. In particular, the
    // playground transport runs inside an opaque sandbox where reading
    // document.cookie throws; it does not need an HTTP CSRF header.
    const csrf = selectedTransport ? undefined : (runtimeConfig.csrf ?? options.csrf);
    if (!useGet && csrf) {
      const token = csrf.token
        ? typeof csrf.token === "function"
          ? csrf.token()
          : csrf.token
        : readCookie(csrf.cookie ?? "csrftoken");
      if (token) headers[csrf.header ?? "X-CSRFToken"] = token;
    }
    // The Vue bridge currently serializes queued jobs and emits one-call
    // envelopes. `allowBatching` therefore selects the per-event route for
    // isolated handlers; it does not yet implement same-tick multi-call
    // envelope/dependency scheduling.
    const isolated = useGet || handlerOptions.allowBatching === false;
    const endpoint = isolated ? eventUrl(routes.eventBaseUrl ?? "", context, input.handler) : routes.endpoint;
    const callTimeout = input.options?.timeout;
    const timeoutMs = callTimeout ?? runtimeConfig.timeout ?? options.timeoutMs ?? 30_000;
    if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) throw new Error("Vue Events timeoutMs must be positive.");
    const controller = new AbortController();
    job.controller = controller;
    const operation = (async (): Promise<{ raw: unknown } | { attachment: Blob; filename: string }> => {
      if (selectedTransport) {
        try {
          return { raw: await selectedTransport.send(envelope) };
        } catch (error) {
          if (error !== null && typeof error === "object") reportableFailures.add(error);
          throw error;
        }
      }
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
      const requestInit: RequestInit = {
        method: isolated ? handlerOptions.httpMethod : "POST",
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
      state.acceptedEpoch += 1;
      continuationCurrent(input.source, state, state.acceptedEpoch, job);
      saveAttachment(received.attachment, received.filename);
      return undefined;
    }
    const raw = received.raw;
    const checked = preflightResultEnvelope(raw, envelope);
    if (!checked.ok) throw new Error(`Invalid Events response: ${checked.issue.message}`);
    stillCurrent(input.source, state);
    validateTargets(checked.results[0], input.source, context.serverRenderId);
    const preparedResult = options.host.preflightResult?.(checked.results[0], input.source) ?? {
      result: checked.results[0],
    };
    state.acceptedEpoch += 1;
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

  const runQueue = async (): Promise<void> => {
    if (running) return;
    running = true;
    try {
      while (queue.length > 0) {
        const job = queue.shift();
        if (!job || job.settled) continue;
        active = job;
        try {
          job.activity?.start(job.intent);
          const value = await sendNow(job);
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
          active = null;
        }
      }
    } finally {
      running = false;
    }
  };

  const unsupportedBrowserMethods = new Set(["HEAD", "OPTIONS", "CONNECT", "TRACE", "TRACK"]);

  const send = (input: VueEventSend): Promise<JsonValue | undefined> => {
    if (disposed) return Promise.reject(stale("disposed"));
    let activity: VueEventActivity | undefined;
    let intent: unknown;
    try {
      if (
        input.options?.timeout !== undefined &&
        (!Number.isFinite(input.options.timeout) || input.options.timeout <= 0)
      )
        throw new Error("Citry Events timeout must be a positive finite number.");
      const context = current(input.source);
      if (!Object.prototype.hasOwnProperty.call(context.descriptor.eventHandlers, input.handler))
        throw new Error(`Unknown event handler '${input.handler}'.`);
      const method = context.descriptor.eventHandlers[input.handler].httpMethod;
      if (unsupportedBrowserMethods.has(method))
        throw new Error(
          `Event handler '${input.handler}' uses HTTP ${method}, which is server-transport-only and cannot be sent by the browser bridge.`,
        );
      activity = options.activity?.(input.source, context.descriptor);
      intent = activity?.enqueue(input.handler);
      if (context.descriptor.eventHandlers[input.handler].latestCallWins === true) supersedeEarlier(input);
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
      activity,
      intent,
      activityFinished: false,
      lifecycleStarted: false,
      external: false,
      stateAccepted: false,
      settled: false,
      cancelled,
      cancel(error) {
        if (job.settled) return;
        job.controller?.abort();
        cancelPromise(error);
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
    queue.push(job);
    void runQueue();
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
        if (typeof action.delay === "number" && action.delay > 0) {
          const delay = action.delay;
          await new Promise((resolve) => globalThis.setTimeout(resolve, delay * 1000));
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
    const error = new VueEventStale("disposed");
    for (const job of queue.splice(0)) {
      lifecycle("stale", job.input.source, job.input.handler, { reason: "disposed" });
      job.cancel(error);
    }
    active?.cancel(error);
  };

  const isDeclarativeFailureHandled = (error: unknown): boolean =>
    error instanceof VueEventCancellation ||
    (error !== null && typeof error === "object" && handledFailures.has(error));

  return { send, applyActions: applyActionsExternally, retire, dispose, isDeclarativeFailureHandled };
};
