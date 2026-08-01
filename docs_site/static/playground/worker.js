// The Worker keeps Pyodide and the rendered module's Citry instance off the UI
// thread. The parent identifies every message by Worker generation and run ID.
const MAX_RESULT_BYTES = 2 * 1024 * 1024;
const MAX_EVENT_ENVELOPE_BYTES = 1024 * 1024;

let generation = 0;
let pyodide;

function send(message) {
  self.postMessage({ ...message, generation });
}

async function fetchText(relativeUrl) {
  // These files form one runtime and keep stable public URLs across docs
  // deploys. Revalidate each one so a newer Worker does not reuse an older
  // browser-cached Python adapter or Events client.
  const response = await fetch(new URL(relativeUrl, import.meta.url), { cache: "no-cache" });
  if (!response.ok) throw new Error(`${relativeUrl} returned HTTP ${response.status}.`);
  return response.text();
}

async function initialize(data) {
  generation = data.generation;
  try {
    if (typeof WebAssembly !== "object") throw new Error("This browser does not support WebAssembly.");
    send({ type: "phase", phase: "Loading runtime configuration" });
    // Fetch every required input before starting Python so a missing asset
    // fails initialization rather than interrupting a later run.
    const [runtimeText, executorSource, eventsRuntimeSource] = await Promise.all([
      fetchText("./runtime.json"),
      fetchText("./executor.py"),
      fetchText("./citry-events.js"),
    ]);
    const runtime = JSON.parse(runtimeText);
    if (runtime.schema_version !== 1 || runtime.protocol_version !== 1 || !Array.isArray(runtime.packages)) {
      throw new Error("The playground runtime configuration is invalid.");
    }

    send({ type: "phase", phase: "Starting Python" });
    const { loadPyodide } = await import(runtime.pyodide.module_url);
    pyodide = await loadPyodide({ indexURL: runtime.pyodide.index_url });

    send({ type: "phase", phase: `Installing Citry ${runtime.citry.version}` });
    // URLs may be public CDN wheels or local authoring-server wheels.
    await pyodide.loadPackage(
      runtime.packages.map((packageInfo) => new URL(packageInfo.url, import.meta.url).href),
    );
    // executor.py installs the stable functions used by later run and event messages.
    pyodide.runPython(executorSource);
    pyodide.globals.set("__citry_playground_events_runtime", eventsRuntimeSource);
    pyodide.runPython("install_events_client_runtime(__citry_playground_events_runtime)");
    pyodide.globals.delete("__citry_playground_events_runtime");
    send({ type: "phase", phase: "Verifying installed versions" });
    // Fail initialization before accepting source if the installed tuple does
    // not match the manifest the UI reports.
    const installed = JSON.parse(pyodide.runPython(`
import importlib.metadata
import json
import sys
versions = {
    "python": ".".join(str(part) for part in sys.version_info[:3]),
    "citry": importlib.metadata.version("citry"),
    "citry_core": importlib.metadata.version("citry-core"),
}
if ${runtime.citry.ui_version ? "True" : "False"}:
    versions["citry_ui"] = importlib.metadata.version("citry-ui")
json.dumps(versions)
    `));
    if (
      installed.python !== runtime.pyodide.python
      || installed.citry !== runtime.citry.version
      || installed.citry_core !== runtime.citry.core_version
      || (runtime.citry.ui_version && installed.citry_ui !== runtime.citry.ui_version)
    ) {
      throw new Error(
        `Installed runtime versions do not match runtime.json: ${JSON.stringify(installed)}.`,
      );
    }
    send({
      type: "ready",
      runtime: [
        `Pyodide ${runtime.pyodide.version}`,
        `Python ${runtime.pyodide.python}`,
        `Citry ${runtime.citry.version}`,
        runtime.citry.ui_version ? `Citry UI ${runtime.citry.ui_version}` : "",
      ].filter(Boolean).join(", "),
    });
  } catch (error) {
    send({
      type: "failure",
      runId: 0,
      fatal: true,
      message: String(error?.message || error),
      details: String(error?.stack || ""),
    });
  }
}

function run(data) {
  // Python returns one bounded JSON envelope containing HTML or a diagnostic.
  send({ type: "executing", runId: data.runId });
  const started = performance.now();
  try {
    pyodide.globals.set("__citry_playground_source", data.source);
    pyodide.globals.set("__citry_playground_run_id", data.runId);
    const serialized = pyodide.runPython(
      "run_source_json(__citry_playground_source, __citry_playground_run_id)",
    );
    if (new TextEncoder().encode(serialized).byteLength > MAX_RESULT_BYTES) {
      throw new Error(`Rendered result exceeded the ${MAX_RESULT_BYTES / 1024 / 1024} MiB limit.`);
    }
    send({
      type: "result",
      runId: data.runId,
      result: JSON.parse(serialized),
      durationMs: performance.now() - started,
    });
  } catch (error) {
    send({
      type: "failure",
      runId: data.runId,
      fatal: false,
      message: String(error?.message || error),
      details: String(error?.stack || ""),
    });
  } finally {
    try {
      pyodide.globals.delete("__citry_playground_source");
      pyodide.globals.delete("__citry_playground_run_id");
    } catch {
      // A failed interpreter may no longer expose its globals proxy.
    }
  }
}

function dispatchEvent(data) {
  // The live Citry instance retained by executor.py handles calls from the
  // currently displayed iframe without rerunning the module.
  const started = performance.now();
  try {
    const envelopeJson = JSON.stringify(data.envelope);
    if (new TextEncoder().encode(envelopeJson).byteLength > MAX_EVENT_ENVELOPE_BYTES) {
      throw new Error("The event envelope exceeds the 1 MiB playground limit.");
    }
    pyodide.globals.set("__citry_playground_event_envelope", envelopeJson);
    pyodide.globals.set("__citry_playground_event_run_id", data.runId);
    const serialized = pyodide.runPython(
      "dispatch_event_json(__citry_playground_event_envelope, __citry_playground_event_run_id)",
    );
    if (new TextEncoder().encode(serialized).byteLength > MAX_RESULT_BYTES) {
      throw new Error("The event response exceeds the 2 MiB playground limit.");
    }
    send({
      type: "event-result",
      runId: data.runId,
      eventId: data.eventId,
      result: JSON.parse(serialized),
      durationMs: performance.now() - started,
    });
  } catch (error) {
    send({
      type: "event-failure",
      runId: data.runId,
      eventId: data.eventId,
      message: String(error?.message || error),
      details: String(error?.stack || ""),
    });
  } finally {
    try {
      pyodide.globals.delete("__citry_playground_event_envelope");
      pyodide.globals.delete("__citry_playground_event_run_id");
    } catch {
      // A failed interpreter may no longer expose its globals proxy.
    }
  }
}

// Keep the Worker protocol closed to known message shapes and the active generation.
self.onmessage = ({ data }) => {
  if (data?.type === "initialize" && Number.isSafeInteger(data.generation)) {
    void initialize(data);
  } else if (
    data?.type === "run"
    && data.generation === generation
    && Number.isSafeInteger(data.runId)
    && typeof data.source === "string"
  ) {
    run(data);
  } else if (
    data?.type === "event"
    && data.consumer === "playground"
    && data.generation === generation
    && Number.isSafeInteger(data.runId)
    && typeof data.eventId === "string"
    && data.eventId.length <= 128
    && data.envelope
  ) {
    dispatchEvent(data);
  }
};
