// This parent-side session owns exactly one Pyodide Worker generation. It
// matches replies to runs and event calls, and terminates stalled generations.
const MAX_SOURCE_BYTES = 64 * 1024;
const MAX_MESSAGE_BYTES = 2 * 1024 * 1024;
const EXECUTION_TIMEOUT_MS = 5_000;
const EVENT_TIMEOUT_MS = 5_000;
const PREPARE_TIMEOUT_MS = 30_000;
const MAX_PENDING_EVENTS = 16;

function messageBytes(value) {
  try {
    return new TextEncoder().encode(JSON.stringify(value)).byteLength;
  } catch {
    return Number.POSITIVE_INFINITY;
  }
}

export class CitryBrowserSession {
  constructor({ workerUrl, onPhase, onReady, onResult, onFailure, onTimeout, onStopped }) {
    this.workerUrl = workerUrl;
    this.onPhase = onPhase;
    this.onReady = onReady;
    this.onResult = onResult;
    this.onFailure = onFailure;
    this.onTimeout = onTimeout;
    this.onStopped = onStopped;
    this.generation = 0;
    this.activeRunId = null;
    this.eventSequence = 0;
    this.state = null;
  }

  terminate(reason = "Worker terminated.") {
    const state = this.state;
    if (!state) return;
    const error = reason instanceof Error ? reason : new Error(reason);
    this.state = null;
    this.activeRunId = null;
    state.worker.terminate();
    clearTimeout(state.prepareTimer);
    clearTimeout(state.executionTimer);
    state.rejectReady?.(error);
    for (const pending of state.eventRequests.values()) {
      clearTimeout(pending.timeout);
      pending.reject(error);
    }
    state.eventRequests.clear();
  }

  dispose() {
    this.terminate();
  }

  armExecutionTimeout(state, runId) {
    clearTimeout(state.executionTimer);
    state.executionTimer = setTimeout(() => {
      if (this.state !== state || this.activeRunId !== runId) return;
      this.terminate();
      this.onTimeout(runId, `Python exceeded the ${EXECUTION_TIMEOUT_MS / 1000}-second limit.`);
    }, EXECUTION_TIMEOUT_MS);
  }

  createWorker() {
    this.terminate();
    this.generation += 1;
    const generation = this.generation;
    const worker = new Worker(this.workerUrl, { type: "module" });
    let resolveReady;
    let rejectReady;
    const ready = new Promise((resolve, reject) => {
      resolveReady = resolve;
      rejectReady = reject;
    });
    const state = {
      worker,
      generation,
      ready,
      resolveReady,
      rejectReady,
      executionTimer: undefined,
      prepareTimer: undefined,
      eventRequests: new Map(),
    };
    state.prepareTimer = setTimeout(() => {
      if (this.state !== state) return;
      const runId = this.activeRunId ?? 0;
      this.terminate();
      this.onFailure(runId, "Python runtime preparation timed out.", "");
    }, PREPARE_TIMEOUT_MS);
    this.state = state;

    // Generation and size checks make late or malformed Worker messages inert.
    worker.onmessage = ({ data }) => {
      if (this.state !== state || data?.generation !== generation || messageBytes(data) > MAX_MESSAGE_BYTES) return;
      if (data.type === "phase" && typeof data.phase === "string") {
        this.onPhase(data.phase);
      } else if (data.type === "ready") {
        clearTimeout(state.prepareTimer);
        state.resolveReady();
        state.resolveReady = null;
        state.rejectReady = null;
        this.onReady(data.runtime || "Citry runtime ready");
      } else if (data.type === "executing" && data.runId === this.activeRunId) {
        this.armExecutionTimeout(state, data.runId);
        this.onPhase("Running Python");
      } else if (data.type === "result" && data.runId === this.activeRunId && data.result) {
        clearTimeout(state.executionTimer);
        this.activeRunId = null;
        this.onResult(data.runId, data.result, Number(data.durationMs) || 0);
      } else if (data.type === "event-result" || data.type === "event-failure") {
        const pending = state.eventRequests.get(data.eventId);
        if (!pending || pending.runId !== data.runId) return;
        clearTimeout(pending.timeout);
        state.eventRequests.delete(data.eventId);
        if (data.type === "event-result" && data.result) {
          pending.resolve(data.result);
        } else {
          const error = new Error(String(data.message || "The Python event handler failed."));
          error.cause = String(data.details || "");
          pending.reject(error);
        }
      } else if (data.type === "failure") {
        const runId = Number.isSafeInteger(data.runId) ? data.runId : this.activeRunId ?? 0;
        if (runId !== 0 && runId !== this.activeRunId) return;
        clearTimeout(state.executionTimer);
        if (runId !== 0) this.activeRunId = null;
        this.onFailure(runId, String(data.message || "Python Worker failed."), String(data.details || ""));
        if (data.fatal || runId === 0) this.terminate();
      }
    };
    worker.onerror = (event) => {
      if (this.state !== state) return;
      const runId = this.activeRunId ?? 0;
      const message = event.message || "Python Worker crashed.";
      this.terminate();
      this.onFailure(runId, message, "");
    };
    worker.onmessageerror = () => {
      if (this.state !== state) return;
      const runId = this.activeRunId ?? 0;
      this.terminate();
      this.onFailure(runId, "Python Worker sent an unreadable message.", "");
    };
    worker.postMessage({ type: "initialize", generation });
    return state;
  }

  ensureWorker() {
    return this.state ?? this.createWorker();
  }

  async prepare() {
    await this.ensureWorker().ready;
  }

  async run(runId, source) {
    if (!Number.isSafeInteger(runId) || runId <= 0 || typeof source !== "string") {
      this.onFailure(runId, "Run request was invalid.", "");
      return;
    }
    if (new TextEncoder().encode(source).byteLength > MAX_SOURCE_BYTES) {
      this.onFailure(runId, `The Python module exceeds the ${MAX_SOURCE_BYTES / 1024} KiB limit.`, "");
      return;
    }
    // A run or event call still in flight cannot safely overlap new module
    // execution, so start that module in a fresh Worker. Idle Workers stay warm.
    if (this.activeRunId !== null || this.state?.eventRequests.size) {
      this.terminate("The displayed event was cancelled by a new Python run.");
    }
    const state = this.ensureWorker();
    this.activeRunId = runId;
    try {
      await state.ready;
      if (this.state !== state || this.activeRunId !== runId) return;
      this.armExecutionTimeout(state, runId);
      state.worker.postMessage({ type: "run", generation: state.generation, runId, source });
    } catch {
      // Initialization reports its specific failure through onFailure.
    }
  }

  async dispatchEvent(runId, envelope) {
    if (!Number.isSafeInteger(runId) || runId <= 0 || !envelope || typeof envelope !== "object") {
      throw new Error("The preview sent an invalid event request.");
    }
    if (this.activeRunId !== null) {
      throw new Error("Wait for the current Python run to finish before calling an event handler.");
    }
    const state = this.state;
    if (!state) throw new Error("The Python runtime is no longer active. Run the module again.");
    if (state.eventRequests.size >= MAX_PENDING_EVENTS) {
      throw new Error(`The playground allows at most ${MAX_PENDING_EVENTS} pending event requests.`);
    }

    await state.ready;
    if (this.state !== state || this.activeRunId !== null) {
      throw new Error("The Python runtime changed before the event could run.");
    }

    // Event IDs match one response to one Promise within this Worker generation.
    this.eventSequence += 1;
    const eventId = `event-${state.generation}-${this.eventSequence}`;
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        if (this.state !== state || !state.eventRequests.has(eventId)) return;
        this.terminate(
          new Error(`The Python event handler exceeded the ${EVENT_TIMEOUT_MS / 1000}-second limit.`),
        );
      }, EVENT_TIMEOUT_MS);
      state.eventRequests.set(eventId, { resolve, reject, timeout, runId });
      state.worker.postMessage({
        type: "event",
        consumer: "playground",
        generation: state.generation,
        runId,
        eventId,
        envelope,
      });
    });
  }

  stop(runId, message = "Run stopped by the visitor.") {
    if (runId !== this.activeRunId) return false;
    this.terminate();
    this.onStopped(runId, message);
    return true;
  }
}
