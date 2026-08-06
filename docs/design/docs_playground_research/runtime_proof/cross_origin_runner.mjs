const PROTOCOL_VERSION = 1;
const MAX_SOURCE_BYTES = 64 * 1024;
const MAX_RESULT_BYTES = 2 * 1024 * 1024;
const RUNS_PER_WINDOW = 10;
const RATE_WINDOW_MS = 1_000;
const WORKER_TIMEOUT_MS = 300;
const PYODIDE_WORKER_TIMEOUT_MS = 15_000;

const session = location.hash.slice(1);
const sourceBytes = (source) => new TextEncoder().encode(source).byteLength;
const messageBytes = (value) => new TextEncoder().encode(JSON.stringify(value)).byteLength;
let parentPort;
let parentOrigin;
let activeWorker;
let activeRunId = 0;
let runTimes = [];

function send(message) {
  const envelope = { ...message, session, version: PROTOCOL_VERSION };
  if (messageBytes(envelope) <= MAX_RESULT_BYTES) {
    parentPort.postMessage(envelope);
  }
}

function reject(runId, reason) {
  send({ type: "rejected", runId, reason });
}

function rateAllowed() {
  const now = performance.now();
  runTimes = runTimes.filter((time) => now - time < RATE_WINDOW_MS);
  if (runTimes.length >= RUNS_PER_WINDOW) {
    return false;
  }
  runTimes.push(now);
  return true;
}

function handleRun(message) {
  if (
    !Number.isSafeInteger(message.runId) ||
    message.runId <= activeRunId ||
    typeof message.source !== "string" ||
    ![
      "echo", "flood", "infinite", "network", "parent-flood", "pyodide",
    ].includes(message.mode)
  ) {
    reject(message.runId, "schema-or-order");
    return;
  }
  if (sourceBytes(message.source) > MAX_SOURCE_BYTES) {
    reject(message.runId, "source-size");
    return;
  }
  if (!rateAllowed()) {
    reject(message.runId, "rate-limit");
    return;
  }

  activeRunId = message.runId;
  activeWorker?.terminate();
  if (message.mode === "parent-flood") {
    for (let index = 0; index < 250; index += 1) {
      send({
        type: "phase",
        runId: message.runId,
        phase: `untrusted-runner-message:${index}`,
      });
    }
    return;
  }
  const worker = new Worker("/cross_origin_worker.mjs", { type: "module" });
  activeWorker = worker;
  let droppedWorkerMessages = 0;
  const timeout = setTimeout(() => {
    if (worker === activeWorker) {
      worker.terminate();
      activeWorker = undefined;
      send({ type: "timeout", runId: message.runId });
    }
  }, message.mode === "pyodide" ? PYODIDE_WORKER_TIMEOUT_MS : WORKER_TIMEOUT_MS);

  worker.onmessage = ({ data }) => {
    if (worker !== activeWorker) {
      return;
    }
    if (data?.type === "loop-started") {
      send({ type: "phase", runId: message.runId, phase: "loop-started" });
      return;
    }
    if (data?.type !== "result" || data.runId !== message.runId) {
      droppedWorkerMessages += 1;
      return;
    }
    clearTimeout(timeout);
    worker.terminate();
    activeWorker = undefined;
    send({
      type: "result",
      runId: message.runId,
      droppedWorkerMessages,
      result: data.result,
    });
  };
  worker.onerror = () => {
    clearTimeout(timeout);
    worker.terminate();
    activeWorker = undefined;
    send({ type: "failure", runId: message.runId, message: "Worker failed" });
  };
  worker.postMessage({
    type: "start",
    runId: message.runId,
    mode: message.mode,
    source: message.source,
    docsOrigin: message.docsOrigin,
  });
}

function onPortMessage({ data }) {
  if (
    data?.version !== PROTOCOL_VERSION ||
    data?.session !== session ||
    data?.type !== "run"
  ) {
    return;
  }
  handleRun(data);
}

window.addEventListener("message", (event) => {
  if (
    parentPort ||
    event.source !== parent ||
    event.data?.type !== "runner-connect" ||
    event.data?.version !== PROTOCOL_VERSION ||
    event.data?.session !== session ||
    event.ports.length !== 1
  ) {
    return;
  }
  parentOrigin = event.origin;
  parentPort = event.ports[0];
  parentPort.onmessage = onPortMessage;
  parentPort.start();
  send({ type: "connected", parentOrigin });
});

parent.postMessage(
  { type: "runner-ready", version: PROTOCOL_VERSION, session },
  "*",
);
