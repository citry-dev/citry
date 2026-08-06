import { createCitryEditor } from "./citry_editor.js";
import { PreviewBridge } from "./preview_bridge.js";
import { CitryBrowserSession } from "./worker_session.js";

// This module coordinates the full-page UI. Python execution and iframe
// delivery stay in shared classes also used by inline live-code examples.
const SETTINGS_KEY = "citry.playground.settings.v1";
const AUTO_RUN_DELAY_MS = 500;
const MIN_SPLIT = 30;
const MAX_SPLIT = 70;

// IDs are emitted by PlaygroundWorkspace and are the stable DOM contract for
// the full-page client.
const elements = {
  root: document.querySelector(".citry-playground"),
  announcer: document.querySelector("#citry-playground-announcer"),
  autoRun: document.querySelector("#citry-playground-auto-run"),
  closeHelpButtons: document.querySelectorAll("[data-citry-playground-close-help]"),
  codePanel: document.querySelector("#citry-playground-code-panel"),
  codeTab: document.querySelector("#citry-playground-code-tab"),
  copyCode: document.querySelector("#citry-playground-copy-code"),
  copyPreviewError: document.querySelector("#citry-playground-copy-preview-error"),
  copyPythonError: document.querySelector("#citry-playground-copy-python-error"),
  dismissPreview: document.querySelector("#citry-playground-dismiss-preview"),
  dismissPython: document.querySelector("#citry-playground-dismiss-python"),
  divider: document.querySelector("#citry-playground-divider"),
  downloadCode: document.querySelector("#citry-playground-download-code"),
  editor: document.querySelector("#citry-playground-editor"),
  fallback: document.querySelector("#citry-playground-editor-fallback"),
  help: document.querySelector("#citry-playground-help"),
  helpDialog: document.querySelector("#citry-playground-help-dialog"),
  preview: document.querySelector("#citry-playground-preview"),
  previewDetails: document.querySelector("#citry-playground-preview-details"),
  previewDiagnostic: document.querySelector("#citry-playground-preview-diagnostic"),
  previewSummary: document.querySelector("#citry-playground-preview-summary"),
  pythonDetails: document.querySelector("#citry-playground-python-details"),
  pythonDiagnostic: document.querySelector("#citry-playground-python-diagnostic"),
  pythonSummary: document.querySelector("#citry-playground-python-summary"),
  reset: document.querySelector("#citry-playground-reset"),
  resultPanel: document.querySelector("#citry-playground-result-panel"),
  resultTab: document.querySelector("#citry-playground-result-tab"),
  run: document.querySelector("#citry-playground-run"),
  runtime: document.querySelector("#citry-playground-runtime"),
  stale: document.querySelector("#citry-playground-stale"),
  status: document.querySelector("#citry-playground-status"),
  stop: document.querySelector("#citry-playground-stop"),
  empty: document.querySelector("#citry-playground-empty"),
};

function announce(message) {
  // Clearing first makes repeated status text announce again to screen readers.
  elements.announcer.textContent = "";
  requestAnimationFrame(() => { elements.announcer.textContent = message; });
}

function setStatus(message, { announceChange = true } = {}) {
  elements.status.textContent = message;
  if (announceChange) announce(message);
}

function setRunning(running) {
  elements.run.disabled = running;
  elements.stop.disabled = !running;
}

function setStale(stale) {
  elements.stale.hidden = !stale;
}

function showDiagnostic(owner, summary, details = "") {
  elements[`${owner}Summary`].textContent = summary;
  elements[`${owner}Details`].textContent = details;
  elements[`${owner}Diagnostic`].hidden = false;
  announce(summary);
}

function hideDiagnostic(owner) {
  elements[`${owner}Diagnostic`].hidden = true;
}

function diagnosticText(owner) {
  return [elements[`${owner}Summary`].textContent, elements[`${owner}Details`].textContent]
    .filter(Boolean)
    .join("\n\n");
}

function clampSplit(value) {
  return Math.max(MIN_SPLIT, Math.min(MAX_SPLIT, Number(value) || 50));
}

function readSettings() {
  try {
    const value = JSON.parse(localStorage.getItem(SETTINGS_KEY) || "null");
    if (!value || typeof value !== "object") return { autoRun: true, splitPercent: 50 };
    return {
      autoRun: value.autoRun !== false,
      splitPercent: clampSplit(value.splitPercent),
    };
  } catch {
    return { autoRun: true, splitPercent: 50 };
  }
}

let settings = readSettings();
function saveSettings(update) {
  settings = { ...settings, ...update };
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch {
    // Storage can be unavailable in privacy modes; controls still work in-memory.
  }
}

async function copyText(value) {
  try {
    await navigator.clipboard.writeText(value);
  } catch {
    const helper = document.createElement("textarea");
    helper.value = value;
    helper.style.position = "fixed";
    helper.style.opacity = "0";
    document.body.append(helper);
    helper.select();
    document.execCommand("copy");
    helper.remove();
  }
}

const initialSource = elements.fallback.value;
// Revisions and generations let late Worker or iframe messages become harmless
// after an edit, Stop, Reset, or a newer run.
let sourceRevision = 0;
let editor;
let autoRunTimer;
let queuedAutoRun = false;
let autoRunPaused = false;
let nextRunId = 0;
let activeRun = null;
let lastSuccessfulHtml = null;
let uiGeneration = 0;

function getSource() {
  return editor ? editor.getSource() : elements.fallback.value;
}

function sourceChanged() {
  sourceRevision += 1;
  if (lastSuccessfulHtml !== null) setStale(true);
  if (!elements.autoRun.checked || autoRunPaused) return;
  clearTimeout(autoRunTimer);
  autoRunTimer = setTimeout(() => requestRun({ explicit: false }), AUTO_RUN_DELAY_MS);
}

function setSource(source, focus = true) {
  if (editor) {
    editor.setSource(source, focus);
  } else {
    elements.fallback.value = source;
    sourceChanged();
    if (focus) elements.fallback.focus();
  }
}

// Keep the textarea operational when CodeMirror is unavailable.
try {
  editor = createCitryEditor({
    parent: elements.editor,
    initialSource: elements.fallback.value,
    onChange: sourceChanged,
    onRun: () => requestRun({ explicit: true }),
  });
  elements.editor.hidden = false;
  elements.fallback.hidden = true;
} catch (error) {
  elements.fallback.addEventListener("input", sourceChanged);
  showDiagnostic("python", "The rich editor could not start. Plain-text editing is active.", String(error));
}

function isActiveRun(run) {
  return Boolean(run) && activeRun === run && run.generation === uiGeneration;
}

function finishRun(run) {
  if (!isActiveRun(run)) return;
  activeRun = null;
  setRunning(false);
  if (queuedAutoRun && elements.autoRun.checked && !autoRunPaused) {
    queuedAutoRun = false;
    requestAnimationFrame(() => requestRun({ explicit: false }));
  }
}

const preview = new PreviewBridge({
  iframe: elements.preview,
  onAssets(paths, { runId }) {
    return session.loadAssets(runId, paths);
  },
  onCommit() {
    hideDiagnostic("preview");
  },
  onDiagnostic(kind, message) {
    showDiagnostic("preview", `Client ${kind.replaceAll("_", " ")}`, message);
  },
  onEvent(envelope, { runId }) {
    return session.dispatchEvent(runId, envelope);
  },
  onNavigation() {
    showDiagnostic("preview", "The rendered page navigated unexpectedly and was restored.");
    setStale(lastSuccessfulHtml !== null);
  },
});

async function handleResult(runId, result, durationMs) {
  if (!activeRun || activeRun.id !== runId) return;
  const finished = activeRun;
  if (!result.ok) {
    const problem = result.diagnostic || {};
    if (problem.kind === "execution_stopped") autoRunPaused = true;
    const location = problem.line ? `Line ${problem.line}${problem.column !== null ? `:${problem.column + 1}` : ""}\n` : "";
    const streams = [result.stdout && `stdout:\n${result.stdout}`, result.stderr && `stderr:\n${result.stderr}`]
      .filter(Boolean)
      .join("\n\n");
    showDiagnostic(
      "python",
      problem.message || "Python execution failed.",
      [location + (problem.traceback || ""), streams].filter(Boolean).join("\n\n"),
    );
    setStale(lastSuccessfulHtml !== null);
    setStatus(problem.kind === "execution_stopped" ? "Stopped" : "Run failed", { announceChange: false });
    finishRun(finished);
    return;
  }

  if (result.stdout || result.stderr) {
    const output = [
      result.stdout && `stdout (${result.stdout.length} characters):\n${result.stdout}`,
      result.stderr && `stderr (${result.stderr.length} characters):\n${result.stderr}`,
    ].filter(Boolean).join("\n\n");
    showDiagnostic("python", "The program wrote console output.", output);
  } else {
    hideDiagnostic("python");
  }

  const isCurrentSource = finished.revision === sourceRevision;
  setStale(lastSuccessfulHtml !== null);
  setStatus("Updating rendered result");
  hideDiagnostic("preview");
  try {
    await preview.render(result.html, runId);
    if (!isActiveRun(finished)) return;
    lastSuccessfulHtml = result.html;
    setStale(!isCurrentSource);
    elements.empty.hidden = true;
    setStatus(`Rendered in ${Math.round(durationMs)} ms`);
    announce("Rendered result updated");
    if (finished.explicit && compactQuery.matches) setActivePanel("result");
  } catch (error) {
    if (!isActiveRun(finished)) return;
    showDiagnostic("preview", error.message || "The rendered result could not be displayed.", String(error.stack || ""));
    setStale(lastSuccessfulHtml !== null);
    setStatus("Preview unavailable", { announceChange: false });
  }
  finishRun(finished);
}

function handleFailure(runId, message, details) {
  if (activeRun && runId !== 0 && activeRun.id !== runId) return;
  if (!activeRun && runId !== 0) return;
  const failed = activeRun;
  autoRunPaused = true;
  queuedAutoRun = false;
  clearTimeout(autoRunTimer);
  setStale(lastSuccessfulHtml !== null);
  showDiagnostic("python", message, details);
  setStatus("Runner unavailable", { announceChange: false });
  if (failed) finishRun(failed);
  else setRunning(false);
}

const session = new CitryBrowserSession({
  workerUrl: new URL("./worker.js", import.meta.url),
  onPhase: setStatus,
  onReady(runtime) {
    elements.runtime.textContent = runtime
      .split(", ")
      .filter((part) => part.startsWith("Citry "))
      .join(" · ");
    setStatus("Python runtime ready");
  },
  onResult: (runId, result, durationMs) => void handleResult(runId, result, durationMs),
  onFailure: handleFailure,
  onTimeout(runId, message) {
    handleFailure(runId, message, "The Worker was stopped. Run again to start a fresh runtime.");
  },
  onStopped(runId, message) {
    if (!activeRun || activeRun.id !== runId) return;
    const stopped = activeRun;
    autoRunPaused = true;
    queuedAutoRun = false;
    setStale(lastSuccessfulHtml !== null);
    showDiagnostic("python", message);
    setStatus("Stopped", { announceChange: false });
    finishRun(stopped);
  },
});

function requestRun({ explicit }) {
  clearTimeout(autoRunTimer);
  if (activeRun) {
    if (!explicit) queuedAutoRun = true;
    return;
  }
  if (explicit) autoRunPaused = false;
  hideDiagnostic("python");
  nextRunId += 1;
  const source = getSource();
  activeRun = { id: nextRunId, revision: sourceRevision, source, explicit, generation: uiGeneration };
  preview.disableDisplayedEvents(
    "This result is inactive while newer code runs. Run the module successfully to enable events again.",
  );
  setRunning(true);
  setStatus("Loading Python runtime");
  session.run(activeRun.id, source);
}

function stopRun(message = "Run stopped by the visitor.") {
  clearTimeout(autoRunTimer);
  if (!activeRun) return;
  const stopped = activeRun;
  if (session.stop(stopped.id, message)) return;
  session.cancelAssetRequests(stopped.id, message);
  uiGeneration += 1;
  activeRun = null;
  preview.cancelPending(message);
  autoRunPaused = true;
  queuedAutoRun = false;
  setRunning(false);
  setStale(lastSuccessfulHtml !== null);
  showDiagnostic("python", message);
  setStatus("Stopped", { announceChange: false });
}

// Manual and automatic runs converge on requestRun so only one run owns the UI.
elements.run.addEventListener("click", () => requestRun({ explicit: true }));
elements.stop.addEventListener("click", () => stopRun());
elements.autoRun.checked = settings.autoRun;
elements.autoRun.addEventListener("change", () => {
  saveSettings({ autoRun: elements.autoRun.checked });
  if (elements.autoRun.checked) {
    autoRunPaused = false;
    sourceChanged();
  } else {
    clearTimeout(autoRunTimer);
    queuedAutoRun = false;
  }
});

elements.reset.addEventListener("click", () => {
  clearTimeout(autoRunTimer);
  queuedAutoRun = false;
  const resetting = activeRun;
  uiGeneration += 1;
  activeRun = null;
  if (resetting) session.stop(resetting.id, "Run stopped while resetting the starter.");
  session.dispose();
  preview.reset();
  lastSuccessfulHtml = null;
  elements.empty.hidden = false;
  setRunning(false);
  autoRunPaused = false;
  hideDiagnostic("python");
  hideDiagnostic("preview");
  setSource(initialSource);
  setStale(false);
  setStatus("Starter restored");
});

elements.copyCode.addEventListener("click", async () => {
  await copyText(getSource());
  announce("Python copied");
});
elements.downloadCode.addEventListener("click", () => {
  const url = URL.createObjectURL(new Blob([getSource()], { type: "text/x-python;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "citry_playground.py";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
  announce("Python download started");
});
elements.copyPythonError.addEventListener("click", async () => {
  await copyText(diagnosticText("python"));
  announce("Python diagnostic copied");
});
elements.copyPreviewError.addEventListener("click", async () => {
  await copyText(diagnosticText("preview"));
  announce("Result diagnostic copied");
});
elements.dismissPython.addEventListener("click", () => hideDiagnostic("python"));
elements.dismissPreview.addEventListener("click", () => hideDiagnostic("preview"));

elements.help.addEventListener("click", () => {
  if (typeof elements.helpDialog.showModal === "function") elements.helpDialog.showModal();
  else elements.helpDialog.setAttribute("open", "");
});

function closeHelp() {
  if (typeof elements.helpDialog.close === "function") elements.helpDialog.close();
  else elements.helpDialog.removeAttribute("open");
}

for (const button of elements.closeHelpButtons) button.addEventListener("click", closeHelp);
elements.helpDialog.addEventListener("click", (event) => {
  if (event.target === elements.helpDialog) closeHelp();
});

const compactQuery = matchMedia("(max-width: 56rem), (max-height: 28rem)");
// Wide layouts show both panels; compact layouts expose the same pair as tabs.
let activePanel = "code";
function setActivePanel(name, focus = false) {
  activePanel = name;
  const codeActive = name === "code";
  elements.codeTab.classList.toggle("is-active", codeActive);
  elements.resultTab.classList.toggle("is-active", !codeActive);
  elements.codePanel.classList.toggle("is-active", codeActive);
  elements.resultPanel.classList.toggle("is-active", !codeActive);
  elements.codeTab.setAttribute("aria-selected", String(codeActive));
  elements.resultTab.setAttribute("aria-selected", String(!codeActive));
  elements.codeTab.tabIndex = codeActive ? 0 : -1;
  elements.resultTab.tabIndex = codeActive ? -1 : 0;
  if (compactQuery.matches) {
    elements.codePanel.hidden = !codeActive;
    elements.resultPanel.hidden = codeActive;
  } else {
    elements.codePanel.hidden = false;
    elements.resultPanel.hidden = false;
  }
  if (focus) (codeActive ? elements.codeTab : elements.resultTab).focus();
}

elements.codeTab.addEventListener("click", () => setActivePanel("code"));
elements.resultTab.addEventListener("click", () => setActivePanel("result"));
for (const tab of [elements.codeTab, elements.resultTab]) {
  tab.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
    event.preventDefault();
    setActivePanel(activePanel === "code" ? "result" : "code", true);
  });
}
compactQuery.addEventListener("change", () => setActivePanel(activePanel));
setActivePanel("code");

function setDivider(value, persist = true) {
  const bounded = clampSplit(value);
  elements.root.style.setProperty("--citry-playground-code-width", `${bounded}%`);
  elements.divider.setAttribute("aria-valuenow", String(Math.round(bounded)));
  if (persist) saveSettings({ splitPercent: bounded });
}

setDivider(settings.splitPercent, false);
// Pointer capture keeps dragging stable when the pointer leaves the divider.
elements.divider.addEventListener("pointerdown", (event) => {
  elements.divider.setPointerCapture(event.pointerId);
});
elements.divider.addEventListener("pointermove", (event) => {
  if (!elements.divider.hasPointerCapture(event.pointerId)) return;
  const rect = elements.root.getBoundingClientRect();
  const fraction = (event.clientX - rect.left) / rect.width;
  setDivider((document.dir === "rtl" ? 1 - fraction : fraction) * 100);
});
elements.divider.addEventListener("dblclick", () => setDivider(50));
elements.divider.addEventListener("keydown", (event) => {
  const current = Number(elements.divider.getAttribute("aria-valuenow"));
  const rtl = getComputedStyle(elements.divider).direction === "rtl";
  const step = event.shiftKey ? 10 : 1;
  const increments = {
    ArrowLeft: rtl ? step : -step,
    ArrowRight: rtl ? -step : step,
    ArrowUp: step,
    ArrowDown: -step,
  };
  if (event.key in increments) {
    event.preventDefault();
    setDivider(current + increments[event.key]);
  } else if (event.key === "Home") {
    event.preventDefault();
    setDivider(MIN_SPLIT);
  } else if (event.key === "End") {
    event.preventDefault();
    setDivider(MAX_SPLIT);
  } else if (event.key === "Enter") {
    event.preventDefault();
    setDivider(50);
  }
});

elements.fallback.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    requestRun({ explicit: true });
  }
});

window.addEventListener("beforeunload", () => {
  session.dispose();
  preview.dispose();
});

// Browser tests and local debugging use this narrow control surface without
// reaching into private editor, Worker, or preview state.
window.citryPlayground = {
  getSource,
  run: () => requestRun({ explicit: true }),
  setActivePanel,
  setDivider,
  setSource,
  stop: stopRun,
};

if (elements.autoRun.checked) {
  requestAnimationFrame(() => requestRun({ explicit: false }));
} else {
  setStatus("Ready to run");
}
