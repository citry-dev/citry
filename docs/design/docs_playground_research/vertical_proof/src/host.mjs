import starterSource from "./starter.py";
import { autocompletion, closeBrackets, closeBracketsKeymap } from "@codemirror/autocomplete";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
import { css, cssLanguage } from "@codemirror/lang-css";
import { html, htmlLanguage } from "@codemirror/lang-html";
import { javascript, javascriptLanguage } from "@codemirror/lang-javascript";
import { python, pythonLanguage } from "@codemirror/lang-python";
import {
  LanguageSupport,
  bracketMatching,
  defaultHighlightStyle,
  foldGutter,
  indentOnInput,
  syntaxHighlighting,
} from "@codemirror/language";
import { highlightSelectionMatches, searchKeymap } from "@codemirror/search";
import { EditorState } from "@codemirror/state";
import {
  EditorView,
  drawSelection,
  dropCursor,
  highlightActiveLine,
  highlightActiveLineGutter,
  highlightSpecialChars,
  keymap,
  lineNumbers,
  rectangularSelection,
} from "@codemirror/view";
import { parseMixed } from "@lezer/common";

const PROTOCOL_VERSION = __PROTOCOL_VERSION__;
const MAX_PARENT_MESSAGE_BYTES = 2 * 1024 * 1024;
const MAX_PREVIEW_MESSAGE_BYTES = 8 * 1024;
const AUTO_RUN_KEY = "citry-playground:auto-run:v1";
const DIVIDER_KEY = "citry-playground:divider:v1";
const candidate = new URLSearchParams(location.search).get("candidate") === "on-demand"
  ? "on-demand"
  : "guided";
const debounceMs = candidate === "guided" ? 500 : 800;

const elements = {
  announcer: document.querySelector("#announcer"),
  autoRun: document.querySelector("#auto-run"),
  codePanel: document.querySelector("#code-panel"),
  codeTab: document.querySelector("#code-tab"),
  dismissPreview: document.querySelector("#dismiss-preview"),
  dismissPython: document.querySelector("#dismiss-python"),
  divider: document.querySelector("#divider"),
  editor: document.querySelector("#editor"),
  fallback: document.querySelector("#editor-fallback"),
  playground: document.querySelector(".playground"),
  preview: document.querySelector("#preview"),
  previewDetails: document.querySelector("#preview-diagnostic-details"),
  previewDiagnostic: document.querySelector("#preview-diagnostic"),
  previewSummary: document.querySelector("#preview-diagnostic-summary"),
  reset: document.querySelector("#reset-button"),
  resultPanel: document.querySelector("#result-panel"),
  resultTab: document.querySelector("#result-tab"),
  run: document.querySelector("#run-button"),
  runner: document.querySelector("#runner-frame"),
  stale: document.querySelector("#stale-status"),
  status: document.querySelector("#run-status"),
  stop: document.querySelector("#stop-button"),
  pythonDetails: document.querySelector("#python-diagnostic-details"),
  pythonDiagnostic: document.querySelector("#python-diagnostic"),
  pythonSummary: document.querySelector("#python-diagnostic-summary"),
};

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

function announce(message) {
  elements.announcer.textContent = "";
  requestAnimationFrame(() => { elements.announcer.textContent = message; });
}

function setStatus(message) {
  elements.status.textContent = message;
}

function showDiagnostic(owner, summary, details = "") {
  const diagnostic = elements[`${owner}Diagnostic`];
  elements[`${owner}Summary`].textContent = summary;
  elements[`${owner}Details`].textContent = details;
  diagnostic.hidden = false;
  announce(summary);
}

function hideDiagnostic(owner) {
  elements[`${owner}Diagnostic`].hidden = true;
}

function setRunning(running) {
  elements.run.disabled = running;
  elements.stop.hidden = !running;
}

function setStale(stale) {
  elements.stale.hidden = !stale;
}

const embeddedParsers = {
  template: htmlLanguage.parser,
  js: javascriptLanguage.parser,
  css: cssLanguage.parser,
};

function mixedCitryRegion(node, input) {
  if (node.name !== "String") return null;
  const prefix = input.read(Math.max(0, node.from - 180), node.from);
  const line = prefix.slice(prefix.lastIndexOf("\n") + 1);
  const match = line.match(/\b(template|js|css)(?:\s*:\s*[^=\n]+)?\s*=\s*$/);
  if (!match) return null;
  const quoted = input.read(node.from, node.to);
  const opener = quoted.startsWith('\"\"\"') ? '\"\"\"' : quoted.startsWith("'''") ? "'''" : null;
  if (!opener || !quoted.endsWith(opener) || node.to - node.from < 6) return null;
  return { parser: embeddedParsers[match[1]], overlay: [{ from: node.from + 3, to: node.to - 3 }] };
}

const citryPython = new LanguageSupport(
  pythonLanguage.configure({ wrap: parseMixed(mixedCitryRegion) }, "Citry Python"),
  [python().support, html().support, javascript().support, css().support],
);

let editorView;
let editorFailed = false;
let sourceChanged = () => {};
try {
  editorView = new EditorView({
    parent: elements.editor,
    state: EditorState.create({
      doc: starterSource,
      extensions: [
        lineNumbers(),
        highlightActiveLineGutter(),
        highlightSpecialChars(),
        history(),
        foldGutter(),
        drawSelection(),
        dropCursor(),
        EditorState.allowMultipleSelections.of(true),
        indentOnInput(),
        syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
        bracketMatching(),
        closeBrackets(),
        autocompletion(),
        rectangularSelection(),
        highlightActiveLine(),
        highlightSelectionMatches(),
        citryPython,
        EditorView.contentAttributes.of({
          "aria-label": "Citry Python module",
          spellcheck: "false",
        }),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) sourceChanged();
        }),
        keymap.of([
          ...closeBracketsKeymap,
          ...defaultKeymap,
          ...searchKeymap,
          ...historyKeymap,
          indentWithTab,
        ]),
      ],
    }),
  });
} catch (error) {
  editorFailed = true;
  elements.editor.hidden = true;
  elements.fallback.hidden = false;
  elements.fallback.value = starterSource;
  elements.fallback.addEventListener("input", () => sourceChanged());
  showDiagnostic("python", "The rich editor did not load. Plain-text editing is active.", String(error));
}

function getSource() {
  return editorFailed ? elements.fallback.value : editorView.state.doc.toString();
}

function setSource(source, focus = true) {
  if (editorFailed) {
    elements.fallback.value = source;
    if (focus) elements.fallback.focus();
    sourceChanged();
    return;
  }
  editorView.dispatch({
    changes: { from: 0, to: editorView.state.doc.length, insert: source },
    selection: { anchor: 0 },
    scrollIntoView: true,
  });
  if (focus) editorView.focus();
}

let runnerPort;
let connectionPromise;
let latestRunId = 0;
let activeRunId = null;
let lastSuccessfulHtml = null;
let autoRunPaused = false;
let autoRunTimer;
let previewRunId = 0;
let previewNonce = "";
let previewMessageTimes = [];
const previewDebug = [];
let previewPort;
let previewConnectionPromise;
let previewSession;
let previewURL;
let previewNavigationArmed = false;
let previewLoadObserved = false;
let previewShellReportedLoaded = false;
const previewRenderWaiters = new Map();

function validRunnerMessage(data, session) {
  if (
    data?.version !== PROTOCOL_VERSION
    || data?.session !== session
    || typeof data?.type !== "string"
    || byteLength(data) > MAX_PARENT_MESSAGE_BYTES
  ) return false;
  if (data.type === "connected") return typeof data.parentOrigin === "string";
  if (data.type === "prepared") return typeof data.runtime === "string";
  if (!Number.isSafeInteger(data.runId)) return false;
  if (data.type === "phase") return typeof data.phase === "string";
  if (["failure", "rejected", "timeout", "stopped"].includes(data.type)) {
    return typeof data.message === "string";
  }
  return data.type === "result" && typeof data.result === "object" && data.result !== null;
}

async function handleRunnerMessage(data) {
  if (data.type === "connected") {
    setStatus(candidate === "guided" ? "Loading Python runtime" : "Ready to run");
    return;
  }
  if (data.type === "prepared") {
    setStatus(`Runtime ready (${data.runtime})`);
    return;
  }
  if (data.runId !== latestRunId) return;
  if (data.type === "phase") {
    setStatus(data.phase);
    return;
  }
  activeRunId = null;
  setRunning(false);
  if (data.type === "result") {
    if (data.result.ok) {
      hideDiagnostic("python");
      lastSuccessfulHtml = data.result.html;
      setStale(false);
      setStatus("Updating rendered result");
      await renderPreview(data.result.html, data.runId);
      if (data.runId !== latestRunId) return;
      setStatus(`Rendered in ${Math.round(data.durationMs)} ms`);
      announce("Rendered result updated");
    } else {
      const problem = data.result.diagnostic ?? {};
      showDiagnostic(
        "python",
        problem.message || "Python execution failed.",
        problem.traceback || data.result.stderr || "",
      );
      setStale(lastSuccessfulHtml !== null);
      setStatus("Run failed");
    }
    return;
  }
  const hardFailure = ["timeout", "stopped", "failure"].includes(data.type);
  if (hardFailure) autoRunPaused = true;
  setStale(lastSuccessfulHtml !== null);
  showDiagnostic("python", data.message, data.details || "");
  setStatus(data.type === "stopped" ? "Stopped" : "Runner unavailable");
}

function connectRunner() {
  if (connectionPromise) return connectionPromise;
  connectionPromise = new Promise((resolve, reject) => {
    const runnerURL = new URL(elements.playground.dataset.runnerUrl);
    const proofFault = new URLSearchParams(location.search).get("fault");
    if (proofFault) runnerURL.searchParams.set("fault", proofFault);
    const session = randomToken();
    runnerURL.searchParams.set("session", session);
    runnerURL.hash = session;
    elements.runner.src = runnerURL.href;
    const timeout = setTimeout(() => reject(new Error("Runner handshake timed out.")), 8_000);
    const onMessage = (event) => {
      if (
        event.origin !== runnerURL.origin
        || event.source !== elements.runner.contentWindow
        || event.data?.type !== "runner-ready"
        || event.data?.version !== PROTOCOL_VERSION
        || event.data?.session !== session
      ) return;
      window.removeEventListener("message", onMessage);
      const channel = new MessageChannel();
      runnerPort = channel.port1;
      runnerPort.onmessage = ({ data }) => {
        if (validRunnerMessage(data, session)) void handleRunnerMessage(data);
      };
      runnerPort.start();
      elements.runner.contentWindow.postMessage(
        { type: "runner-connect", version: PROTOCOL_VERSION, session },
        runnerURL.origin,
        [channel.port2],
      );
      clearTimeout(timeout);
      resolve({ session });
    };
    window.addEventListener("message", onMessage);
  }).catch((error) => {
    connectionPromise = undefined;
    setRunning(false);
    showDiagnostic("python", error.message, String(error.stack || ""));
    throw error;
  });
  return connectionPromise;
}

async function send(message) {
  const { session } = await connectRunner();
  runnerPort.postMessage({ ...message, version: PROTOCOL_VERSION, session });
}

async function prepare() {
  try {
    await send({ type: "prepare" });
  } catch {
    setStatus("Runner unavailable");
  }
}

async function run({ explicit = false } = {}) {
  clearTimeout(autoRunTimer);
  if (activeRunId !== null) return;
  if (explicit) autoRunPaused = false;
  latestRunId += 1;
  activeRunId = latestRunId;
  setRunning(true);
  hideDiagnostic("python");
  setStatus("Running Python");
  try {
    await send({ type: "run", runId: latestRunId, source: getSource() });
  } catch {
    activeRunId = null;
    setRunning(false);
  }
}

async function stop(message = "Run stopped by the visitor.") {
  clearTimeout(autoRunTimer);
  if (activeRunId === null) return;
  autoRunPaused = true;
  try {
    await send({ type: "stop", runId: activeRunId, message });
  } catch {
    activeRunId = null;
    setRunning(false);
  }
}

sourceChanged = () => {
  if (!elements.autoRun.checked || autoRunPaused) return;
  clearTimeout(autoRunTimer);
  autoRunTimer = setTimeout(() => run(), debounceMs);
};

function validPreviewDiagnostic(data) {
  return data?.type === "citry-preview-diagnostic"
    && data?.version === PROTOCOL_VERSION
    && data?.session === previewSession
    && data?.runId === previewRunId
    && data?.nonce === previewNonce
    && typeof data?.kind === "string"
    && typeof data?.message === "string"
    && byteLength(data) <= MAX_PREVIEW_MESSAGE_BYTES;
}

function connectPreview() {
  if (previewConnectionPromise) return previewConnectionPromise;
  previewConnectionPromise = new Promise((resolve, reject) => {
    previewSession = randomToken();
    const runnerURL = new URL(elements.playground.dataset.runnerUrl);
    previewURL = new URL("./preview.html", runnerURL);
    previewURL.hash = previewSession;
    previewNavigationArmed = false;
    previewLoadObserved = false;
    previewShellReportedLoaded = false;
    const timeout = setTimeout(() => reject(new Error("Preview handshake timed out.")), 8_000);
    const onMessage = (event) => {
      if (event.source !== elements.preview.contentWindow) return;
      previewDebug.push({ origin: event.origin, type: event.data?.type, kind: event.data?.kind });
      if (
        event.data?.type !== "preview-ready"
        || event.data?.version !== PROTOCOL_VERSION
        || event.data?.session !== previewSession
      ) return;
      window.removeEventListener("message", onMessage);
      const channel = new MessageChannel();
      previewPort = channel.port1;
      previewPort.onmessage = ({ data }) => {
        if (data?.type === "preview-connected") {
          clearTimeout(timeout);
          resolve();
          return;
        }
        if (
          data?.type === "preview-loaded"
          && data?.version === PROTOCOL_VERSION
          && data?.session === previewSession
        ) {
          previewShellReportedLoaded = true;
          if (previewLoadObserved) previewNavigationArmed = true;
          return;
        }
        if (
          data?.type === "preview-rendered"
          && data?.version === PROTOCOL_VERSION
          && data?.session === previewSession
          && data?.nonce === previewNonce
        ) {
          previewRenderWaiters.get(data.runId)?.();
          previewRenderWaiters.delete(data.runId);
          return;
        }
        if (!validPreviewDiagnostic(data)) return;
        const now = performance.now();
        previewMessageTimes = previewMessageTimes.filter((time) => now - time < 1_000);
        if (previewMessageTimes.length >= 10) return;
        previewMessageTimes.push(now);
        showDiagnostic("preview", `Client ${data.kind.replaceAll("_", " ")}`, data.message);
      };
      previewPort.start();
      elements.preview.contentWindow.postMessage(
        { type: "preview-connect", version: PROTOCOL_VERSION, session: previewSession },
        "*",
        [channel.port2],
      );
    };
    window.addEventListener("message", onMessage);
    elements.preview.src = previewURL.href;
  }).catch((error) => {
    previewConnectionPromise = undefined;
    showDiagnostic("preview", error.message, String(error.stack || ""));
    throw error;
  });
  return previewConnectionPromise;
}

async function renderPreview(html, runId) {
  previewRunId = runId;
  previewNonce = randomToken();
  previewMessageTimes = [];
  hideDiagnostic("preview");
  try {
    await connectPreview();
    const rendered = new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        previewRenderWaiters.delete(runId);
        reject(new Error("Rendered result acknowledgement timed out."));
      }, 3_000);
      previewRenderWaiters.set(runId, () => {
        clearTimeout(timeout);
        resolve();
      });
    });
    previewPort.postMessage({
      type: "render",
      version: PROTOCOL_VERSION,
      session: previewSession,
      runId,
      nonce: previewNonce,
      html,
    });
    await rendered;
  } catch {
    setStale(true);
  }
}

elements.preview.addEventListener("load", () => {
  previewDebug.push({ load: true, observed: previewLoadObserved, armed: previewNavigationArmed, reported: previewShellReportedLoaded });
  if (!previewLoadObserved) {
    previewLoadObserved = true;
    if (previewShellReportedLoaded) previewNavigationArmed = true;
    return;
  }
  if (!previewNavigationArmed) return;
  previewDebug.push({ unexpectedNavigation: true });
  previewNavigationArmed = false;
  showDiagnostic("preview", "The rendered page navigated unexpectedly and was restored.");
  previewPort?.close();
  previewPort = undefined;
  previewConnectionPromise = undefined;
  previewLoadObserved = false;
  previewShellReportedLoaded = false;
  elements.preview.src = "about:blank";
});

window.addEventListener("message", (event) => {
  const data = event.data;
  if (event.source === elements.preview.contentWindow && previewDebug.length < 50) {
    previewDebug.push({ origin: event.origin, type: data?.type, kind: data?.kind });
  }
  if (data?.type === "citry-preview-diagnostic") previewDebug.push({ rejectedWindowDiagnostic: true });
});

elements.run.addEventListener("click", () => run({ explicit: true }));
elements.stop.addEventListener("click", () => stop());
elements.reset.addEventListener("click", async () => {
  if (activeRunId !== null) await stop("Run stopped while resetting the starter.");
  hideDiagnostic("python");
  hideDiagnostic("preview");
  setSource(starterSource);
  setStatus("Starter restored");
  if (candidate === "guided") run({ explicit: true });
});
elements.autoRun.addEventListener("change", () => {
  localStorage.setItem(AUTO_RUN_KEY, elements.autoRun.checked ? "on" : "off");
  if (elements.autoRun.checked && !autoRunPaused) sourceChanged();
});
elements.dismissPython.addEventListener("click", () => hideDiagnostic("python"));
elements.dismissPreview.addEventListener("click", () => hideDiagnostic("preview"));

function setActivePanel(name, focus = false) {
  const codeActive = name === "code";
  elements.codeTab.setAttribute("aria-selected", String(codeActive));
  elements.resultTab.setAttribute("aria-selected", String(!codeActive));
  elements.codeTab.tabIndex = codeActive ? 0 : -1;
  elements.resultTab.tabIndex = codeActive ? -1 : 0;
  elements.codePanel.hidden = !codeActive;
  elements.resultPanel.hidden = codeActive;
  if (focus) (codeActive ? elements.codeTab : elements.resultTab).focus();
}

elements.codeTab.addEventListener("click", () => setActivePanel("code"));
elements.resultTab.addEventListener("click", () => setActivePanel("result"));
for (const tab of [elements.codeTab, elements.resultTab]) {
  tab.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
    event.preventDefault();
    setActivePanel(tab === elements.codeTab ? "result" : "code", true);
  });
}

const compactQuery = matchMedia("(max-width: 700px), (max-height: 500px)");
function applyCompactMode(event = compactQuery) {
  if (event.matches) setActivePanel(elements.resultTab.getAttribute("aria-selected") === "true" ? "result" : "code");
  else {
    elements.codePanel.hidden = false;
    elements.resultPanel.hidden = false;
  }
}
compactQuery.addEventListener("change", applyCompactMode);
applyCompactMode();

function clampDivider(value) { return Math.max(25, Math.min(75, value)); }
function setDivider(value, persist = true) {
  const bounded = clampDivider(value);
  document.documentElement.style.setProperty("--code-width", `${bounded}%`);
  elements.divider.setAttribute("aria-valuenow", String(Math.round(bounded)));
  if (persist) localStorage.setItem(DIVIDER_KEY, String(bounded));
}

const storedDivider = Number(localStorage.getItem(DIVIDER_KEY));
setDivider(Number.isFinite(storedDivider) && storedDivider ? storedDivider : 50, false);

elements.divider.addEventListener("pointerdown", (event) => {
  elements.divider.setPointerCapture(event.pointerId);
});
elements.divider.addEventListener("pointermove", (event) => {
  if (!elements.divider.hasPointerCapture(event.pointerId)) return;
  const rect = elements.playground.getBoundingClientRect();
  const fraction = (event.clientX - rect.left) / rect.width;
  setDivider((document.dir === "rtl" ? 1 - fraction : fraction) * 100);
});
elements.divider.addEventListener("dblclick", () => setDivider(50));
elements.divider.addEventListener("keydown", (event) => {
  const current = Number(elements.divider.getAttribute("aria-valuenow"));
  const rtl = getComputedStyle(elements.divider).direction === "rtl";
  const increments = {
    ArrowLeft: rtl ? 2 : -2,
    ArrowRight: rtl ? -2 : 2,
    ArrowUp: 2,
    ArrowDown: -2,
  };
  if (event.key in increments) {
    event.preventDefault();
    setDivider(current + increments[event.key]);
  } else if (event.key === "Home") {
    event.preventDefault();
    setDivider(25);
  } else if (event.key === "End") {
    event.preventDefault();
    setDivider(75);
  } else if (event.key === "Enter") {
    event.preventDefault();
    setDivider(50);
  }
});

const storedAutoRun = localStorage.getItem(AUTO_RUN_KEY);
elements.autoRun.checked = storedAutoRun === null ? candidate === "guided" : storedAutoRun === "on";
setStatus(candidate === "guided" ? "Preparing playground" : "Ready to run");

window.verticalProof = {
  candidate,
  debounceMs,
  getSource,
  isAutoRunPaused: () => autoRunPaused,
  lastSuccessfulHtml: () => lastSuccessfulHtml,
  latestRunId: () => latestRunId,
  run: () => run({ explicit: true }),
  previewDebug,
  setActivePanel,
  setDivider,
  setSource,
  stop,
};

if (candidate === "guided") {
  requestAnimationFrame(async () => {
    await prepare();
    await run({ explicit: true });
  });
}
