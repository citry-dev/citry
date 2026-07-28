const PROTOCOL_VERSION = 1;
const MAX_PARENT_MESSAGE_BYTES = 2 * 1024 * 1024;
const MAX_PARENT_MESSAGES_PER_WINDOW = 100;
const PARENT_RATE_WINDOW_MS = 1_000;

const delay = (milliseconds) =>
  new Promise((resolve) => setTimeout(resolve, milliseconds));

function messageBytes(value) {
  try {
    return new TextEncoder().encode(JSON.stringify(value)).byteLength;
  } catch {
    return Number.POSITIVE_INFINITY;
  }
}

function validRunnerMessage(data, session) {
  if (
    data?.version !== PROTOCOL_VERSION ||
    data?.session !== session ||
    typeof data?.type !== "string"
  ) {
    return false;
  }
  if (data.type === "connected") {
    return typeof data.parentOrigin === "string";
  }
  if (!Number.isSafeInteger(data.runId)) {
    return false;
  }
  if (data.type === "failure") {
    return typeof data.message === "string";
  }
  if (data.type === "phase") {
    return typeof data.phase === "string";
  }
  if (data.type === "rejected") {
    return typeof data.reason === "string";
  }
  if (data.type === "result") {
    return typeof data.result === "object" && data.result !== null;
  }
  return data.type === "timeout";
}

function randomSession() {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return [...bytes].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function waitFor(predicate, timeout = 5_000) {
  const started = performance.now();
  return new Promise((resolve, reject) => {
    const check = () => {
      const value = predicate();
      if (value !== undefined) {
        resolve(value);
        return;
      }
      if (performance.now() - started > timeout) {
        reject(new Error("Timed out waiting for proof state"));
        return;
      }
      setTimeout(check, 10);
    };
    check();
  });
}

async function connectRunner(runnerOrigin, attackerOrigin) {
  const frames = document.querySelector("#frames");
  const session = randomSession();
  const rejectedWindowMessages = [];
  const received = [];
  let droppedParentMessages = 0;
  let parentMessageTimes = [];
  let runnerPort;

  const attacker = document.createElement("iframe");
  attacker.hidden = true;
  attacker.src = `${attackerOrigin}/attacker.html#${session}`;
  frames.append(attacker);

  const runner = document.createElement("iframe");
  runner.id = "runner-frame";
  runner.sandbox = "allow-scripts allow-same-origin";
  runner.referrerPolicy = "no-referrer";
  runner.src = `${runnerOrigin}/runner.html#${session}`;
  frames.append(runner);

  const ready = new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error("Runner handshake timed out")), 5_000);
    let runnerConnected = false;
    const finishIfComplete = (onMessage) => {
      const attackerRejected = rejectedWindowMessages.some(
        (message) => message.origin === attackerOrigin,
      );
      if (!runnerConnected || !attackerRejected) {
        return;
      }
      clearTimeout(timeout);
      window.removeEventListener("message", onMessage);
      resolve();
    };
    const onMessage = (event) => {
      const valid =
        event.origin === runnerOrigin &&
        event.source === runner.contentWindow &&
        event.data?.type === "runner-ready" &&
        event.data?.version === PROTOCOL_VERSION &&
        event.data?.session === session;
      if (!valid) {
        rejectedWindowMessages.push({
          origin: event.origin,
          type: event.data?.type ?? typeof event.data,
        });
        finishIfComplete(onMessage);
        return;
      }
      if (runnerConnected) {
        return;
      }
      runnerConnected = true;
      const channel = new MessageChannel();
      runnerPort = channel.port1;
      runnerPort.onmessage = ({ data }) => {
        const now = performance.now();
        parentMessageTimes = parentMessageTimes.filter(
          (time) => now - time < PARENT_RATE_WINDOW_MS,
        );
        if (
          parentMessageTimes.length >= MAX_PARENT_MESSAGES_PER_WINDOW ||
          messageBytes(data) > MAX_PARENT_MESSAGE_BYTES
        ) {
          droppedParentMessages += 1;
          return;
        }
        parentMessageTimes.push(now);
        if (!validRunnerMessage(data, session)) {
          droppedParentMessages += 1;
          return;
        }
        received.push(data);
      };
      runnerPort.start();
      runner.contentWindow.postMessage(
        { type: "runner-connect", version: PROTOCOL_VERSION, session },
        runnerOrigin,
        [channel.port2],
      );
      finishIfComplete(onMessage);
    };
    window.addEventListener("message", onMessage);
  });

  await ready;
  await waitFor(() => received.find((message) => message.type === "connected"));

  return {
    get droppedParentMessages() {
      return droppedParentMessages;
    },
    received,
    rejectedWindowMessages,
    runner,
    send(message) {
      runnerPort.postMessage({
        ...message,
        session,
        version: PROTOCOL_VERSION,
      });
    },
  };
}

async function previewNavigationProbe(runnerOrigin) {
  const frames = document.querySelector("#frames");
  const diagnostic = document.querySelector("#diagnostic");
  const iframe = document.createElement("iframe");
  iframe.id = "preview-frame";
  iframe.sandbox = "allow-scripts";
  let loads = 0;
  let recovered = false;

  const completed = new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error("Preview navigation probe timed out")), 5_000);
    iframe.addEventListener("load", () => {
      loads += 1;
      if (loads < 2) {
        return;
      }
      const inert = document.createElement("iframe");
      inert.id = "preview-frame";
      inert.title = "Rendered result unavailable";
      inert.sandbox = "allow-scripts";
      inert.srcdoc = "<!doctype html><p>Preview reset after unexpected navigation.</p>";
      iframe.replaceWith(inert);
      diagnostic.value = "Preview navigated unexpectedly and was reset.";
      recovered = true;
      clearTimeout(timeout);
      resolve();
    });
  });

  iframe.title = "Rendered result";
  iframe.srcdoc = `<!doctype html><script>
    setTimeout(() => { location.href = ${JSON.stringify(`${runnerOrigin}/preview-nav`)}; }, 50);
  <\/script>`;
  frames.append(iframe);
  await completed;
  return {
    diagnostic: diagnostic.value,
    loads,
    recovered,
    replacementTitle: document.querySelector("#preview-frame").title,
  };
}

window.runCrossOriginProbe = async ({
  attackerOrigin,
  docsOrigin,
  includePyodide = false,
  runnerOrigin,
}) => {
  const connection = await connectRunner(runnerOrigin, attackerOrigin);
  const { received, send } = connection;

  send({ type: "run", runId: 1, mode: "echo", source: "'<p>first</p>'" });
  const first = await waitFor(() => received.find(
    (message) => message.type === "result" && message.runId === 1,
  ));

  send({ type: "run", runId: 2, mode: "infinite", source: "while True: pass" });
  const timeout = await waitFor(() => received.find(
    (message) => message.type === "timeout" && message.runId === 2,
  ));

  send({ type: "run", runId: 3, mode: "network", source: "network probe", docsOrigin });
  const recovery = await waitFor(() => received.find(
    (message) => message.type === "result" && message.runId === 3,
  ));

  send({ type: "run", runId: 4, mode: "flood", source: "message flood" });
  const flood = await waitFor(() => received.find(
    (message) => message.type === "result" && message.runId === 4,
  ));

  send({ type: "run", runId: 5, mode: "echo", source: "x".repeat(70 * 1024) });
  const oversize = await waitFor(() => received.find(
    (message) => message.type === "rejected" && message.runId === 5,
  ));

  await delay(1_100);
  for (let runId = 10; runId < 35; runId += 1) {
    send({ type: "run", runId, mode: "echo", source: `run ${runId}` });
  }
  const rateLimited = await waitFor(() => {
    const matches = received.filter(
      (message) => message.type === "rejected" && message.reason === "rate-limit",
    );
    return matches.length > 0 ? matches : undefined;
  });

  let pyodide;
  if (includePyodide) {
    await delay(1_100);
    send({
      type: "run",
      runId: 100,
      mode: "pyodide",
      source: "direct citry_core smoke",
      docsOrigin,
    });
    pyodide = await waitFor(() => received.find(
      (message) => message.type === "result" && message.runId === 100,
    ), 20_000);
  }

  await delay(1_100);
  const droppedBeforeParentFlood = connection.droppedParentMessages;
  send({
    type: "run",
    runId: 101,
    mode: "parent-flood",
    source: "runner to parent message flood",
  });
  await delay(250);
  const parentFloodDropped =
    connection.droppedParentMessages - droppedBeforeParentFlood;

  const previewNavigation = await previewNavigationProbe(runnerOrigin);
  return {
    first,
    flood,
    iframe: {
      referrerPolicy: connection.runner.referrerPolicy,
      sandbox: connection.runner.getAttribute("sandbox"),
    },
    parentMessageCount: received.length,
    parentFloodDropped,
    previewNavigation,
    pyodide,
    rateLimited: rateLimited.length,
    recovery,
    rejectedWindowMessages: connection.rejectedWindowMessages,
    timeout,
    oversize,
  };
};
