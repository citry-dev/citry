import { createCitryEditor } from "./citry_editor.js";
import { PreviewBridge } from "./preview_bridge.js";
import { CitryBrowserSession } from "./worker_session.js";

// One activated inline example combines the shared editor, Worker session, and
// iframe bridge while leaving page-level activation to live_code.js.
const AUTO_RUN_DELAY_MS = 500;

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

export function createLiveCodeRuntime({ root, initialSource, authoredSource, onClose, onReset }) {
  // Data attributes form the stable contract with the server-rendered component.
  const query = (selector) => root.querySelector(selector);
  const elements = {
    activate: query("[data-live-activate]"),
    announcer: query("[data-live-announcer]"),
    autoRun: query("[data-live-auto-run]"),
    close: query("[data-live-close]"),
    editor: query("[data-live-editor]"),
    empty: query("[data-live-empty]"),
    fallback: query("[data-live-fallback]"),
    previewDiagnostic: query("[data-live-preview-diagnostic]"),
    previewDetails: query("[data-live-preview-details]"),
    previewSummary: query("[data-live-preview-summary]"),
    pythonDiagnostic: query("[data-live-python-diagnostic]"),
    pythonDetails: query("[data-live-python-details]"),
    pythonSummary: query("[data-live-python-summary]"),
    reset: query("[data-live-reset]"),
    run: query("[data-live-run]"),
    static: query("[data-live-static]"),
    status: query("[data-live-status]"),
    stale: query("[data-live-stale]"),
    stop: query("[data-live-stop]"),
    workspace: query("[data-live-workspace]"),
  };
  const abort = new AbortController();
  const listen = (element, type, handler) => element.addEventListener(type, handler, { signal: abort.signal });
  let disposed = false;
  let operationEpoch = 0;
  let sourceRevision = 0;
  let nextRunId = 0;
  let activeRun = null;
  let autoRunTimer = null;
  let queuedAutoRun = false;
  let autoRunPaused = false;
  let lastSuccessfulHtml = null;
  let editor = null;
  let preview = null;
  let session;

  // Clearing first makes repeated status text announce again to screen readers.
  function announce(message) {
    if (disposed) return;
    elements.announcer.textContent = "";
    requestAnimationFrame(() => {
      if (!disposed) elements.announcer.textContent = message;
    });
  }

  function setStatus(message) {
    if (disposed) return;
    elements.status.textContent = message;
    announce(message);
  }

  function setRunning(running) {
    if (disposed) return;
    elements.run.disabled = running;
    elements.stop.disabled = !running;
  }

  function setStale(stale) {
    if (!disposed) elements.stale.hidden = !stale;
  }

  function showDiagnostic(owner, summary, details = "") {
    if (disposed) return;
    elements[`${owner}Summary`].textContent = summary;
    elements[`${owner}Details`].textContent = details;
    elements[`${owner}Diagnostic`].hidden = false;
    announce(summary);
  }

  function hideDiagnostic(owner) {
    if (!disposed) elements[`${owner}Diagnostic`].hidden = true;
  }

  function diagnosticText(owner) {
    return [elements[`${owner}Summary`].textContent, elements[`${owner}Details`].textContent]
      .filter(Boolean)
      .join("\n\n");
  }

  function getSource() {
    return editor ? editor.getSource() : elements.fallback.value;
  }

  function sourceChanged() {
    if (disposed) return;
    sourceRevision += 1;
    if (lastSuccessfulHtml !== null) {
      setStale(true);
      preview?.disableDisplayedEvents("This result is inactive because the code has changed.");
    }
    if (!elements.autoRun.checked || autoRunPaused) return;
    clearTimeout(autoRunTimer);
    autoRunTimer = setTimeout(() => requestRun({ explicit: false }), AUTO_RUN_DELAY_MS);
  }

  elements.fallback.value = initialSource;
  // The bundled textarea remains usable if CodeMirror loads but construction fails.
  try {
    editor = createCitryEditor({
      parent: elements.editor,
      initialSource,
      onChange: sourceChanged,
      onRun: () => requestRun({ explicit: true }),
    });
    elements.editor.hidden = false;
    elements.fallback.hidden = true;
  } catch (error) {
    listen(elements.fallback, "input", sourceChanged);
    showDiagnostic("python", "The rich editor could not start. Plain-text editing is active.", String(error));
  }

  const frame = document.createElement("iframe");
  frame.className = "citry-live-code__preview";
  frame.title = "Rendered Citry result";
  frame.src = new URL("./preview.html", import.meta.url);
  frame.sandbox.add("allow-forms", "allow-scripts");
  query("[data-live-preview-shell]").prepend(frame);

  // The bridge swaps complete sandboxed documents and forwards their Events
  // calls to the Python session that produced the displayed result.
  preview = new PreviewBridge({
    iframe: frame,
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
    },
  });

  function isActiveRun(run) {
    return !disposed && Boolean(run) && activeRun === run && run.epoch === operationEpoch;
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

  async function handleResult(runId, result, durationMs) {
    if (!activeRun || activeRun.id !== runId) return;
    const finished = activeRun;
    if (!result.ok) {
      const problem = result.diagnostic || {};
      const location = problem.line ? `Line ${problem.line}${problem.column !== null ? `:${problem.column + 1}` : ""}\n` : "";
      const streams = [result.stdout && `stdout:\n${result.stdout}`, result.stderr && `stderr:\n${result.stderr}`]
        .filter(Boolean)
        .join("\n\n");
      showDiagnostic(
        "python",
        problem.message || "Python execution failed.",
        [location + (problem.traceback || ""), streams].filter(Boolean).join("\n\n"),
      );
      setStatus(problem.kind === "execution_stopped" ? "Stopped" : "Run failed");
      finishRun(finished);
      return;
    }

    if (result.stdout || result.stderr) {
      showDiagnostic(
        "python",
        "The program wrote console output.",
        [result.stdout && `stdout:\n${result.stdout}`, result.stderr && `stderr:\n${result.stderr}`]
          .filter(Boolean)
          .join("\n\n"),
      );
    } else {
      hideDiagnostic("python");
    }

    setStatus("Updating rendered result");
    try {
      await preview.render(result.html, runId);
      if (!isActiveRun(finished)) return;
      lastSuccessfulHtml = result.html;
      elements.empty.hidden = true;
      setStatus(`Rendered in ${Math.round(durationMs)} ms`);
      const stale = finished.revision !== sourceRevision;
      setStale(stale);
      if (stale) preview.disableDisplayedEvents("This result is inactive because newer code is waiting to run.");
    } catch (error) {
      if (!isActiveRun(finished)) return;
      showDiagnostic("preview", error.message || "The rendered result could not be displayed.", String(error.stack || ""));
      setStatus("Preview unavailable");
    }
    finishRun(finished);
  }

  function handleFailure(runId, message, details) {
    if (disposed || (activeRun && runId !== 0 && activeRun.id !== runId) || (!activeRun && runId !== 0)) return;
    const failed = activeRun;
    autoRunPaused = true;
    queuedAutoRun = false;
    clearTimeout(autoRunTimer);
    showDiagnostic("python", message, details);
    setStatus("Runner unavailable");
    if (failed) finishRun(failed);
    else setRunning(false);
  }

  // The session owns the long-lived Pyodide Worker. It survives ordinary
  // reruns, but Stop, timeout, or a new run overlapping an event call ends it.
  session = new CitryBrowserSession({
    workerUrl: new URL("./worker.js", import.meta.url),
    onPhase: setStatus,
    onReady: () => setStatus("Python runtime ready"),
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
      showDiagnostic("python", message);
      setStatus("Stopped");
      finishRun(stopped);
    },
  });

  function requestRun({ explicit }) {
    if (disposed) return;
    clearTimeout(autoRunTimer);
    if (activeRun) {
      if (!explicit) queuedAutoRun = true;
      return;
    }
    if (explicit) autoRunPaused = false;
    hideDiagnostic("python");
    nextRunId += 1;
    activeRun = { id: nextRunId, revision: sourceRevision, explicit, epoch: operationEpoch };
    preview.disableDisplayedEvents("This result is inactive while newer code runs.");
    setStale(lastSuccessfulHtml !== null);
    setRunning(true);
    setStatus("Loading Python runtime");
    session.run(activeRun.id, getSource());
  }

  function stopRun() {
    clearTimeout(autoRunTimer);
    if (!activeRun) return;
    const stopped = activeRun;
    if (session.stop(stopped.id)) return;
    session.cancelAssetRequests(stopped.id, "Run stopped by the visitor.");
    operationEpoch += 1;
    activeRun = null;
    preview.cancelPending("Run stopped by the visitor.");
    autoRunPaused = true;
    queuedAutoRun = false;
    setRunning(false);
    showDiagnostic("python", "Run stopped by the visitor.");
    setStatus("Stopped");
  }

  // Inline examples keep the visitor's selected tab across runs and resets.
  let activePanel = root.querySelector('[data-live-tab][aria-selected="true"]')?.dataset.liveTab || "code";
  function setActivePanel(name, focus = false) {
    if (disposed) return;
    activePanel = name;
    for (const tab of root.querySelectorAll("[data-live-tab]")) {
      const selected = tab.dataset.liveTab === name;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
      tab.classList.toggle("is-active", selected);
    }
    for (const panel of root.querySelectorAll("[data-live-panel]")) {
      const selected = panel.dataset.livePanel === name;
      panel.hidden = !selected;
      panel.classList.toggle("is-active", selected);
    }
    if (focus) query(`[data-live-tab="${name}"]`).focus();
  }

  listen(elements.run, "click", () => requestRun({ explicit: true }));
  listen(elements.stop, "click", stopRun);
  listen(elements.autoRun, "change", () => {
    if (elements.autoRun.checked) {
      autoRunPaused = false;
      sourceChanged();
    } else {
      clearTimeout(autoRunTimer);
      queuedAutoRun = false;
    }
  });
  // Reset destroys the Python and preview state before restoring authored code,
  // so no event handler from the discarded result can remain callable.
  listen(elements.reset, "click", () => {
    clearTimeout(autoRunTimer);
    queuedAutoRun = false;
    operationEpoch += 1;
    activeRun = null;
    session.dispose();
    preview.reset();
    lastSuccessfulHtml = null;
    setStale(false);
    elements.empty.hidden = false;
    setRunning(false);
    autoRunPaused = false;
    hideDiagnostic("python");
    hideDiagnostic("preview");
    if (editor) editor.setSource(authoredSource, false);
    else {
      elements.fallback.value = authoredSource;
      sourceChanged();
    }
    clearTimeout(autoRunTimer);
    onReset();
    setStatus("Original code restored");
    if (elements.autoRun.checked) requestAnimationFrame(() => requestRun({ explicit: false }));
  });
  listen(elements.close, "click", onClose);
  listen(query("[data-live-copy-python]"), "click", () => void copyText(diagnosticText("python")));
  listen(query("[data-live-copy-preview]"), "click", () => void copyText(diagnosticText("preview")));
  listen(query("[data-live-dismiss-python]"), "click", () => hideDiagnostic("python"));
  listen(query("[data-live-dismiss-preview]"), "click", () => hideDiagnostic("preview"));
  for (const tab of root.querySelectorAll("[data-live-tab]")) {
    listen(tab, "click", () => setActivePanel(tab.dataset.liveTab));
    listen(tab, "keydown", (event) => {
      const order = ["code", "result"];
      let index = order.indexOf(activePanel);
      if (event.key === "ArrowLeft" || event.key === "ArrowUp") index -= 1;
      else if (event.key === "ArrowRight" || event.key === "ArrowDown") index += 1;
      else if (event.key === "Home") index = 0;
      else if (event.key === "End") index = order.length - 1;
      else return;
      event.preventDefault();
      setActivePanel(order[(index + order.length) % order.length], true);
    });
  }
  listen(elements.fallback, "keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      requestRun({ explicit: true });
    }
  });

  elements.activate.hidden = true;
  query("[data-live-draft]").hidden = true;
  elements.static.hidden = true;
  elements.workspace.hidden = false;
  setActivePanel(activePanel);
  setRunning(false);
  requestAnimationFrame(() => {
    if (activePanel === "code") editor?.focus();
    else query(`[data-live-tab="${activePanel}"]`)?.focus();
  });
  requestAnimationFrame(() => requestRun({ explicit: false }));

  // live_code.js uses this controller to preserve drafts and retire the one
  // active editor without knowing its internal resources.
  return {
    getSource,
    isDirty: () => getSource() !== authoredSource,
    dispose() {
      if (disposed) return;
      disposed = true;
      operationEpoch += 1;
      clearTimeout(autoRunTimer);
      queuedAutoRun = false;
      activeRun = null;
      abort.abort();
      session.dispose();
      preview.dispose();
      editor?.destroy();
      for (const previewFrame of root.querySelectorAll(".citry-live-code__preview")) previewFrame.remove();
    },
  };
}
