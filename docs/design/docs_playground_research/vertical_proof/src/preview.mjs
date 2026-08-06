const PROTOCOL_VERSION = __PROTOCOL_VERSION__;
const MAX_HTML_BYTES = 2 * 1024 * 1024;
const MAX_MESSAGES_PER_SECOND = 10;
const session = location.hash.slice(1);
let hostPort;
let runId = 0;
let nonce = "";
let messageTimes = [];
let documentLoaded = document.readyState === "complete";

function byteLength(value) {
  return new TextEncoder().encode(value).byteLength;
}

function send(kind, value) {
  if (!hostPort) return;
  const now = performance.now();
  messageTimes = messageTimes.filter((time) => now - time < 1_000);
  if (messageTimes.length >= MAX_MESSAGES_PER_SECOND) return;
  messageTimes.push(now);
  let message;
  try {
    message = typeof value === "string" ? value : String(value?.message ?? value);
  } catch {
    message = "Unprintable client error";
  }
  hostPort.postMessage({
    type: "citry-preview-diagnostic",
    version: PROTOCOL_VERSION,
    session,
    runId,
    nonce,
    kind,
    message: message.slice(0, 4_096),
  });
}

addEventListener("error", (event) => {
  if (event.target && event.target !== window) {
    send("resource_error", event.target.currentSrc || event.target.src || event.target.href || event.target.tagName);
  } else {
    send("error", event.error || event.message);
  }
}, true);
addEventListener("unhandledrejection", (event) => send("unhandled_rejection", event.reason));
const originalConsoleError = console.error.bind(console);
console.error = (...values) => {
  originalConsoleError(...values);
  send("console_error", values.join(" "));
};

addEventListener("load", () => {
  documentLoaded = true;
  hostPort?.postMessage({ type: "preview-loaded", version: PROTOCOL_VERSION, session });
});

async function activateScripts(scripts) {
  for (const oldScript of scripts) {
    const script = document.createElement("script");
    for (const attribute of oldScript.attributes) script.setAttribute(attribute.name, attribute.value);
    script.textContent = oldScript.textContent;
    oldScript.replaceWith(script);
    if (script.src && !script.async) {
      await new Promise((resolve) => {
        script.addEventListener("load", resolve, { once: true });
        script.addEventListener("error", resolve, { once: true });
      });
    }
  }
}

async function render(message) {
  if (
    !Number.isSafeInteger(message.runId)
    || typeof message.nonce !== "string"
    || typeof message.html !== "string"
    || byteLength(message.html) > MAX_HTML_BYTES
  ) return;
  runId = message.runId;
  nonce = message.nonce;
  messageTimes = [];
  const parsed = new DOMParser().parseFromString(message.html, "text/html");
  const visitorScripts = [...parsed.querySelectorAll("script")];
  for (const node of document.head.querySelectorAll("[data-citry-preview-content]")) node.remove();
  for (const node of [...parsed.head.childNodes]) {
    if (node.nodeType === Node.ELEMENT_NODE) node.setAttribute("data-citry-preview-content", "");
    document.head.append(node);
  }
  document.body.replaceChildren(...[...parsed.body.childNodes]);
  await activateScripts(visitorScripts);
  hostPort.postMessage({
    type: "preview-rendered",
    version: PROTOCOL_VERSION,
    session,
    runId,
    nonce,
  });
}

addEventListener("message", (event) => {
  if (
    hostPort
    || event.source !== parent
    || event.data?.type !== "preview-connect"
    || event.data?.version !== PROTOCOL_VERSION
    || event.data?.session !== session
    || event.ports.length !== 1
  ) return;
  hostPort = event.ports[0];
  hostPort.onmessage = ({ data }) => {
    if (
      data?.type === "render"
      && data?.version === PROTOCOL_VERSION
      && data?.session === session
    ) render(data);
  };
  hostPort.start();
  hostPort.postMessage({ type: "preview-connected", version: PROTOCOL_VERSION, session });
  if (documentLoaded) {
    hostPort.postMessage({ type: "preview-loaded", version: PROTOCOL_VERSION, session });
  }
});

parent.postMessage({ type: "preview-ready", version: PROTOCOL_VERSION, session }, "*");
