const RUNTIME = __RUNTIME_CONFIG__;
const EXECUTOR_SOURCE = __EXECUTOR_SOURCE__;
const MAX_RESULT_BYTES = 2 * 1024 * 1024;

let generation = 0;
let pyodide;

function send(message) {
  self.postMessage({ ...message, generation });
}

function bytesToHex(bytes) {
  return [...bytes].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function verifyArtifact(artifact, fault) {
  let url = new URL(artifact.path, import.meta.url);
  let expectedHash = artifact.sha256;
  if (fault === "missing-wheel" && artifact.kind === "wheel" && artifact.name.startsWith("citry_core")) {
    url = new URL("./runtime/missing-wheel.whl", import.meta.url);
  }
  if (fault === "hash-mismatch" && artifact.kind === "wheel" && artifact.name.startsWith("citry_core")) {
    expectedHash = "0".repeat(64);
  }
  if (fault === "slow-load") await new Promise((resolve) => setTimeout(resolve, 350));
  const response = await fetch(url, { cache: "force-cache", credentials: "omit" });
  if (!response.ok) throw new Error(`Runtime artifact ${artifact.name} returned HTTP ${response.status}.`);
  const buffer = await response.arrayBuffer();
  if (buffer.byteLength !== artifact.bytes) {
    throw new Error(`Runtime artifact ${artifact.name} has ${buffer.byteLength} bytes, expected ${artifact.bytes}.`);
  }
  const actualHash = bytesToHex(new Uint8Array(await crypto.subtle.digest("SHA-256", buffer)));
  if (actualHash !== expectedHash) throw new Error(`Runtime artifact ${artifact.name} failed SHA-256 verification.`);
  return { artifact, buffer, url };
}

async function initialize(data) {
  generation = data.generation;
  try {
    if (data.fault === "no-wasm" || typeof WebAssembly !== "object") {
      throw new Error("This browser does not provide the required WebAssembly runtime.");
    }
    send({ type: "phase", phase: "Verifying pinned runtime" });
    const verified = [];
    for (const artifact of RUNTIME.artifacts) verified.push(await verifyArtifact(artifact, data.fault));
    const pyodideModule = verified.find(({ artifact }) => artifact.name === "pyodide.mjs");
    const blobURL = URL.createObjectURL(new Blob([pyodideModule.buffer], { type: "text/javascript" }));
    try {
      send({ type: "phase", phase: "Starting Python" });
      const { loadPyodide } = await import(blobURL);
      pyodide = await loadPyodide({ indexURL: new URL(RUNTIME.pyodideIndex, import.meta.url).href });
    } finally {
      URL.revokeObjectURL(blobURL);
    }
    send({ type: "phase", phase: "Installing pinned Citry" });
    const wheelURLs = RUNTIME.artifacts
      .filter((artifact) => artifact.kind === "wheel")
      .map((artifact) => new URL(artifact.path, import.meta.url).href);
    await pyodide.loadPackage(wheelURLs);
    if (data.fault === "import-failure") await pyodide.runPythonAsync("import citry_package_that_does_not_exist");
    pyodide.runPython(EXECUTOR_SOURCE);
    send({ type: "ready" });
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

async function run(data) {
  send({ type: "executing", runId: data.runId });
  const started = performance.now();
  try {
    pyodide.globals.set("__citry_playground_source", data.source);
    const serialized = pyodide.runPython("run_source_json(__citry_playground_source)");
    const resultBytes = new TextEncoder().encode(serialized).byteLength;
    if (resultBytes > MAX_RESULT_BYTES) throw new Error(`Rendered result exceeded the ${MAX_RESULT_BYTES}-byte limit.`);
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
    try { pyodide.globals.delete("__citry_playground_source"); } catch {}
  }
}

self.onmessage = ({ data }) => {
  if (data?.type === "initialize" && Number.isSafeInteger(data.generation)) initialize(data);
  else if (
    data?.type === "run"
    && data.generation === generation
    && Number.isSafeInteger(data.runId)
    && typeof data.source === "string"
  ) run(data);
};
