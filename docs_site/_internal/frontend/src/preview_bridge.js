// The parent never writes into a result iframe directly. This bridge creates a
// fresh shell, authenticates a MessagePort, then atomically swaps it into view.
const PROTOCOL_VERSION = 1;
const MAX_MESSAGE_BYTES = 8 * 1024;
const MAX_EVENT_ENVELOPE_BYTES = 1024 * 1024;
const MAX_EVENT_RESULT_BYTES = 2 * 1024 * 1024;
const MAX_ASSET_PATHS = 32;
const MAX_ASSET_REQUEST_BYTES = 32 * 1024;
const MAX_ASSET_RESULT_BYTES = 4 * 1024 * 1024;
const RENDER_TIMEOUT_MS = 8_000;
const CONNECT_TIMEOUT_MS = 8_000;

function byteLength(value) {
  try {
    return new TextEncoder().encode(JSON.stringify(value)).byteLength;
  } catch {
    return Number.POSITIVE_INFINITY;
  }
}

function randomToken() {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return [...bytes].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function cancellationError(message = "Preview operation was cancelled.") {
  const error = new Error(message);
  error.name = "AbortError";
  return error;
}

function createState(frame, generation) {
  return {
    frame,
    generation,
    session: "",
    runId: 0,
    nonce: "",
    port: null,
    connected: false,
    shellLoaded: false,
    pendingLoad: null,
    pendingConnection: null,
    pendingRender: null,
    messageTimes: [],
    diagnostics: [],
  };
}

export class PreviewBridge {
  constructor({ iframe, onAssets, onCommit, onDiagnostic, onEvent, onNavigation }) {
    this.onAssets = onAssets;
    this.onCommit = onCommit;
    this.onDiagnostic = onDiagnostic;
    this.onEvent = onEvent;
    this.onNavigation = onNavigation;
    this.shellUrl = iframe.src;
    this.generation = 0;
    this.displayState = createState(iframe, this.generation);
    this.candidateState = null;
    this.disposed = false;
    this.onWindowMessage = this.onWindowMessage.bind(this);
    this.onFrameLoad = this.onFrameLoad.bind(this);
    window.addEventListener("message", this.onWindowMessage);
    iframe.addEventListener("load", this.onFrameLoad);
  }

  onFrameLoad(event) {
    const candidate = this.candidateState;
    if (candidate?.frame === event.currentTarget) {
      const pending = candidate.pendingLoad;
      if (!pending) return;
      clearTimeout(pending.timeout);
      candidate.pendingLoad = null;
      pending.resolve(candidate);
      return;
    }
    const displayed = this.displayState;
    if (
      displayed.frame !== event.currentTarget
      || !displayed.connected
      || !displayed.shellLoaded
    ) return;
    // A load after connection means visitor code navigated the displayed frame.
    this.onNavigation();
    this.reset();
  }

  onWindowMessage(event) {
    const state = this.candidateState;
    if (
      !state
      || event.source !== state.frame.contentWindow
      || event.data?.type !== "preview-ready"
      || event.data?.version !== PROTOCOL_VERSION
      || !state.pendingConnection
      || state.port
    ) return;
    // Window messaging is used only to transfer a private channel. All later
    // traffic carries the session identity over that MessagePort.
    const channel = new MessageChannel();
    state.port = channel.port1;
    state.port.onmessage = ({ data }) => this.onPortMessage(state, data);
    state.port.start();
    state.frame.contentWindow.postMessage(
      { type: "preview-connect", version: PROTOCOL_VERSION, session: state.session },
      "*",
      [channel.port2],
    );
  }

  onPortMessage(state, data) {
    if (
      (state !== this.displayState && state !== this.candidateState)
      || data?.version !== PROTOCOL_VERSION
      || data?.session !== state.session
    ) return;
    if (data.type === "preview-connected") {
      const pending = state.pendingConnection;
      if (!pending) return;
      state.connected = true;
      clearTimeout(pending.timeout);
      state.pendingConnection = null;
      pending.resolve();
      return;
    }
    if (data.type === "preview-loaded") {
      state.shellLoaded = true;
      return;
    }
    if (data.type === "preview-render-failed" && data.runId === state.runId && data.nonce === state.nonce) {
      const pending = state.pendingRender;
      if (!pending) return;
      clearTimeout(pending.timeout);
      state.pendingRender = null;
      pending.reject(new Error(String(data.message || "The preview could not prepare its assets.")));
      return;
    }
    if (data.type === "citry-event-call") {
      if (
        state !== this.displayState
        || data.runId !== state.runId
        || data.nonce !== state.nonce
        || typeof data.eventId !== "string"
        || !/^event-[1-9][0-9]*$/.test(data.eventId)
        || !data.envelope
        || typeof data.envelope !== "object"
        || byteLength(data.envelope) > MAX_EVENT_ENVELOPE_BYTES
      ) return;
      void this.forwardEvent(state, data);
      return;
    }
    if (data.type === "citry-assets-call") {
      const activeState = state === this.displayState || (state === this.candidateState && state.pendingRender);
      if (
        !activeState
        || data.runId !== state.runId
        || data.nonce !== state.nonce
        || typeof data.assetId !== "string"
        || !/^assets-[1-9][0-9]*$/.test(data.assetId)
        || !Array.isArray(data.paths)
        || data.paths.length === 0
        || data.paths.length > MAX_ASSET_PATHS
        || data.paths.some((path) => typeof path !== "string")
        || byteLength(data.paths) > MAX_ASSET_REQUEST_BYTES
      ) return;
      void this.forwardAssets(state, data);
      return;
    }
    if (data.type === "preview-rendered" && data.runId === state.runId && data.nonce === state.nonce) {
      const pending = state.pendingRender;
      if (!pending) return;
      clearTimeout(pending.timeout);
      state.pendingRender = null;
      pending.resolve();
      return;
    }
    if (
      data.type !== "citry-preview-diagnostic"
      || data.runId !== state.runId
      || data.nonce !== state.nonce
      || typeof data.kind !== "string"
      || typeof data.message !== "string"
      || byteLength(data) > MAX_MESSAGE_BYTES
    ) return;
    // Bound diagnostics by size and rate before showing visitor-controlled text.
    const now = performance.now();
    state.messageTimes = state.messageTimes.filter((time) => now - time < 1_000);
    if (state.messageTimes.length >= 10) return;
    state.messageTimes.push(now);
    if (state === this.displayState) this.onDiagnostic(data.kind, data.message);
    else state.diagnostics.push([data.kind, data.message]);
  }

  async forwardEvent(state, data) {
    try {
      const result = await this.onEvent(data.envelope, { runId: state.runId });
      if (state !== this.displayState || !state.port || byteLength(result) > MAX_EVENT_RESULT_BYTES) {
        throw new Error("The event response is no longer valid for this preview.");
      }
      state.port.postMessage({
        type: "citry-event-result",
        version: PROTOCOL_VERSION,
        session: state.session,
        runId: state.runId,
        nonce: state.nonce,
        eventId: data.eventId,
        result,
      });
    } catch (error) {
      if (state !== this.displayState || !state.port) return;
      state.port.postMessage({
        type: "citry-event-failure",
        version: PROTOCOL_VERSION,
        session: state.session,
        runId: state.runId,
        nonce: state.nonce,
        eventId: data.eventId,
        message: String(error?.message || error).slice(0, 4_096),
      });
    }
  }

  async forwardAssets(state, data) {
    try {
      const assets = await this.onAssets(data.paths, { runId: state.runId });
      if (
        (state !== this.displayState && state !== this.candidateState)
        || !state.port
        || state.runId !== data.runId
        || state.nonce !== data.nonce
        || !Array.isArray(assets)
        || byteLength(assets) > MAX_ASSET_RESULT_BYTES
      ) {
        throw new Error("The asset response is no longer valid for this preview.");
      }
      state.port.postMessage({
        type: "citry-assets-result",
        version: PROTOCOL_VERSION,
        session: state.session,
        runId: state.runId,
        nonce: state.nonce,
        assetId: data.assetId,
        assets,
      });
    } catch (error) {
      if ((state !== this.displayState && state !== this.candidateState) || !state.port) return;
      state.port.postMessage({
        type: "citry-assets-failure",
        version: PROTOCOL_VERSION,
        session: state.session,
        runId: state.runId,
        nonce: state.nonce,
        assetId: data.assetId,
        message: String(error?.message || error).slice(0, 4_096),
      });
    }
  }

  closeState(state, message, { removeFrame = false } = {}) {
    // Reject every waiter before closing the channel so callers never hang on
    // an iframe that Reset, Stop, or a newer render has invalidated.
    const error = cancellationError(message);
    for (const key of ["pendingLoad", "pendingConnection", "pendingRender"]) {
      const pending = state[key];
      if (!pending) continue;
      clearTimeout(pending.timeout);
      state[key] = null;
      pending.reject(error);
    }
    state.port?.postMessage({
      type: "citry-events-disabled",
      version: PROTOCOL_VERSION,
      session: state.session,
      runId: state.runId,
      nonce: state.nonce,
      message,
    });
    state.port?.close();
    state.port = null;
    state.connected = false;
    state.shellLoaded = false;
    state.frame.removeEventListener("load", this.onFrameLoad);
    if (removeFrame) state.frame.remove();
  }

  discardCandidate(message) {
    const state = this.candidateState;
    if (!state) return;
    this.candidateState = null;
    this.closeState(state, message, { removeFrame: true });
  }

  loadCandidateShell() {
    if (this.disposed) return Promise.reject(cancellationError("Preview bridge was disposed."));
    this.discardCandidate("Preview was replaced by a newer result.");
    this.generation += 1;
    const candidate = this.displayState.frame.cloneNode(false);
    candidate.id = `${this.displayState.frame.id}-candidate`;
    candidate.classList.add("citry-playground__preview--candidate");
    candidate.setAttribute("aria-hidden", "true");
    candidate.tabIndex = -1;
    const url = new URL(this.shellUrl);
    url.searchParams.set("citry-preview", randomToken());
    candidate.src = url.href;
    const state = createState(candidate, this.generation);
    candidate.addEventListener("load", this.onFrameLoad);
    this.candidateState = state;
    const promise = new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        if (state !== this.candidateState || !state.pendingLoad) return;
        state.pendingLoad = null;
        reject(new Error("Preview document load timed out."));
      }, CONNECT_TIMEOUT_MS);
      state.pendingLoad = { resolve, reject, timeout };
    });
    this.displayState.frame.after(candidate);
    return promise;
  }

  connect(state) {
    if (state !== this.candidateState) return Promise.reject(cancellationError());
    state.session = randomToken();
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        if (state !== this.candidateState || !state.pendingConnection) return;
        state.pendingConnection = null;
        reject(new Error("Preview handshake timed out."));
      }, CONNECT_TIMEOUT_MS);
      state.pendingConnection = { resolve, reject, timeout };
      state.frame.contentWindow?.postMessage({ type: "preview-probe", version: PROTOCOL_VERSION }, "*");
    });
  }

  async render(html, runId) {
    let state;
    try {
      state = await this.loadCandidateShell();
      await this.connect(state);
      if (state !== this.candidateState || !state.port) throw cancellationError();
      state.runId = runId;
      state.nonce = randomToken();
      state.messageTimes = [];
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          if (state !== this.candidateState || !state.pendingRender) return;
          state.pendingRender = null;
          reject(new Error("Rendered result acknowledgement timed out."));
        }, RENDER_TIMEOUT_MS);
        state.pendingRender = { resolve, reject, timeout };
        state.port.postMessage({
          type: "render",
          version: PROTOCOL_VERSION,
          session: state.session,
          runId,
          nonce: state.nonce,
          html,
        });
      });
      if (state !== this.candidateState) throw cancellationError();

      // Commit after the candidate acknowledges delivery. Visitor-script
      // diagnostics buffered during activation are surfaced after the swap.
      const previous = this.displayState;
      const candidate = state.frame;
      candidate.id = previous.frame.id;
      candidate.classList.remove("citry-playground__preview--candidate");
      candidate.removeAttribute("aria-hidden");
      candidate.removeAttribute("tabindex");
      previous.frame.remove();
      this.displayState = state;
      this.candidateState = null;
      this.closeState(previous, "Preview was replaced by a newer result.");
      state.port.postMessage({
        type: "citry-events-enabled",
        version: PROTOCOL_VERSION,
        session: state.session,
        runId: state.runId,
        nonce: state.nonce,
      });
      this.onCommit();
      for (const [kind, message] of state.diagnostics) this.onDiagnostic(kind, message);
      state.diagnostics = [];
    } catch (error) {
      if (!state || state === this.candidateState) this.discardCandidate("Preview update failed.");
      throw error;
    }
  }

  cancelPending(message = "Preview update was cancelled.") {
    if (this.disposed) return;
    this.discardCandidate(message);
  }

  disableDisplayedEvents(message = "This preview is no longer active.") {
    const state = this.displayState;
    if (!state.port || !state.connected) return;
    state.port.postMessage({
      type: "citry-events-disabled",
      version: PROTOCOL_VERSION,
      session: state.session,
      runId: state.runId,
      nonce: state.nonce,
      message,
    });
  }

  reset() {
    if (this.disposed) return;
    this.discardCandidate("Preview was reset.");
    const previous = this.displayState;
    this.closeState(previous, "Preview was reset.");
    this.generation += 1;
    const state = createState(previous.frame, this.generation);
    state.frame.addEventListener("load", this.onFrameLoad);
    this.displayState = state;
    const url = new URL(this.shellUrl);
    url.searchParams.set("citry-preview", randomToken());
    state.frame.src = url.href;
  }

  dispose() {
    if (this.disposed) return;
    this.disposed = true;
    window.removeEventListener("message", this.onWindowMessage);
    this.discardCandidate("Preview bridge was disposed.");
    this.closeState(this.displayState, "Preview bridge was disposed.");
  }
}
