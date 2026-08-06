const PROTOCOL_VERSION = __PROTOCOL_VERSION__;
const WORKER_URL = __WORKER_URL__;
const RUNTIME_LABEL = __RUNTIME_LABEL__;
const MAX_SOURCE_BYTES = 64 * 1024;
const MAX_MESSAGE_BYTES = 2 * 1024 * 1024;
const RUNS_PER_WINDOW = 10;
const RATE_WINDOW_MS = 1_000;
const EXECUTION_TIMEOUT_MS = 5_000;
const PREPARE_TIMEOUT_MS = 30_000;

const session = location.hash.slice(1);
const fault = new URLSearchParams(location.search).get("fault") || "";
let parentPort;
let parentOrigin;
let activeRunId = null;
let workerGeneration = 0;
let workerState;
let runTimes = [];

function messageBytes(value) {
  try {
    return new TextEncoder().encode(JSON.stringify(value)).byteLength;
  } catch {
    return Number.POSITIVE_INFINITY;
  }
}

function send(message) {
  if (!parentPort) return;
  const envelope = { ...message, session, version: PROTOCOL_VERSION };
  if (messageBytes(envelope) <= MAX_MESSAGE_BYTES) parentPort.postMessage(envelope);
}

function terminateWorker() {
  if (!workerState) return;
  workerState.worker.terminate();
  clearTimeout(workerState.prepareTimer);
  clearTimeout(workerState.executionTimer);
  workerState.readyReject?.(new Error("Worker terminated."));
  workerState = undefined;
  activeRunId = null;
}

function armExecutionTimeout(state, runId) {
  clearTimeout(state.executionTimer);
  state.executionTimer = setTimeout(() => {
    if (workerState !== state || activeRunId !== runId) return;
    const timedOutRun = activeRunId;
    terminateWorker();
    send({
      type: "timeout",
      runId: timedOutRun,
      message: `Python exceeded the ${EXECUTION_TIMEOUT_MS / 1000}-second limit or the Worker stopped responding.`,
    });
  }, EXECUTION_TIMEOUT_MS);
}

function newWorker() {
  terminateWorker();
  workerGeneration += 1;
  const generation = workerGeneration;
  const worker = new Worker(new URL(WORKER_URL, import.meta.url), { type: "module" });
  let readyResolve;
  let readyReject;
  const ready = new Promise((resolve, reject) => {
    readyResolve = resolve;
    readyReject = reject;
  });
  const state = {
    worker,
    generation,
    ready,
    readyResolve,
    readyReject,
    prepareTimer: setTimeout(() => {
      if (workerState !== state) return;
      send({ type: "failure", runId: activeRunId ?? 0, message: "Python runtime preparation timed out." });
      terminateWorker();
    }, PREPARE_TIMEOUT_MS),
    executionTimer: undefined,
  };
  workerState = state;

  worker.onmessage = ({ data }) => {
    if (workerState !== state || data?.generation !== generation) return;
    if (data?.type === "phase" && typeof data.phase === "string") {
      send({ type: "phase", runId: activeRunId ?? 0, phase: data.phase });
      return;
    }
    if (data?.type === "ready") {
      clearTimeout(state.prepareTimer);
      state.readyResolve();
      state.readyResolve = undefined;
      state.readyReject = undefined;
      return;
    }
    if (data?.type === "executing" && data.runId === activeRunId) {
      armExecutionTimeout(state, data.runId);
      return;
    }
    if (data?.type === "result" && data.runId === activeRunId && typeof data.result === "object") {
      clearTimeout(state.executionTimer);
      const finishedRun = activeRunId;
      activeRunId = null;
      send({ type: "result", runId: finishedRun, result: data.result, durationMs: data.durationMs });
      return;
    }
    if (data?.type === "failure" && Number.isSafeInteger(data.runId)) {
      clearTimeout(state.executionTimer);
      const failedRun = data.runId || activeRunId || 0;
      const preparing = data.runId === 0;
      if (!preparing) activeRunId = null;
      send({ type: "failure", runId: failedRun, message: String(data.message || "Python Worker failed."), details: String(data.details || "") });
      if (data.fatal || preparing) terminateWorker();
    }
  };
  worker.onerror = (event) => {
    if (workerState !== state) return;
    const failedRun = activeRunId ?? 0;
    const message = event.message || "Python Worker crashed.";
    terminateWorker();
    send({ type: "failure", runId: failedRun, message });
  };
  worker.onmessageerror = () => {
    if (workerState !== state) return;
    const failedRun = activeRunId ?? 0;
    terminateWorker();
    send({ type: "failure", runId: failedRun, message: "Python Worker sent an unreadable message." });
  };
  worker.postMessage({ type: "initialize", generation, fault });
  return state;
}

function ensureWorker() {
  return workerState ?? newWorker();
}

function rateAllowed() {
  const now = performance.now();
  runTimes = runTimes.filter((time) => now - time < RATE_WINDOW_MS);
  if (runTimes.length >= RUNS_PER_WINDOW) return false;
  runTimes.push(now);
  return true;
}

async function prepare() {
  try {
    await ensureWorker().ready;
    send({ type: "prepared", runtime: RUNTIME_LABEL });
  } catch {
    // A specific Worker failure is sent by the Worker or timeout path.
  }
}

async function run(message) {
  if (
    !Number.isSafeInteger(message.runId)
    || message.runId <= 0
    || typeof message.source !== "string"
    || new TextEncoder().encode(message.source).byteLength > MAX_SOURCE_BYTES
  ) {
    send({ type: "rejected", runId: Number.isSafeInteger(message.runId) ? message.runId : 0, message: "Run request failed schema or source-size validation." });
    return;
  }
  if (!rateAllowed()) {
    send({ type: "rejected", runId: message.runId, message: "Run request rate limit exceeded." });
    return;
  }
  if (activeRunId !== null) newWorker();
  activeRunId = message.runId;
  const state = ensureWorker();
  try {
    await state.ready;
    if (workerState !== state || activeRunId !== message.runId) return;
    armExecutionTimeout(state, message.runId);
    state.worker.postMessage({ type: "run", generation: state.generation, runId: message.runId, source: message.source });
  } catch {
    // The preparation failure has already been reported.
  }
}

function stop(message) {
  if (!Number.isSafeInteger(message.runId) || message.runId !== activeRunId) {
    send({ type: "rejected", runId: Number.isSafeInteger(message.runId) ? message.runId : 0, message: "There is no matching active run to stop." });
    return;
  }
  const stoppedRun = activeRunId;
  terminateWorker();
  send({ type: "stopped", runId: stoppedRun, message: typeof message.message === "string" ? message.message.slice(0, 512) : "Run stopped." });
}

function onPortMessage({ data }) {
  if (
    data?.version !== PROTOCOL_VERSION
    || data?.session !== session
    || typeof data?.type !== "string"
    || messageBytes(data) > MAX_MESSAGE_BYTES
  ) return;
  if (data.type === "prepare") prepare();
  else if (data.type === "run") run(data);
  else if (data.type === "stop") stop(data);
}

window.addEventListener("message", (event) => {
  if (
    parentPort
    || event.source !== parent
    || event.data?.type !== "runner-connect"
    || event.data?.version !== PROTOCOL_VERSION
    || event.data?.session !== session
    || event.ports.length !== 1
  ) return;
  parentOrigin = event.origin;
  parentPort = event.ports[0];
  parentPort.onmessage = onPortMessage;
  parentPort.start();
  send({ type: "connected", parentOrigin });
});

parent.postMessage({ type: "runner-ready", version: PROTOCOL_VERSION, session }, "*");
