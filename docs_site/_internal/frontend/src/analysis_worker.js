// This Worker proves browser-native Citry analysis without sharing mutable
// state with visitor code in the disposable execution Worker.
const SCHEMA_VERSION = 1;
const MAX_SOURCE_BYTES = 64 * 1024;
const MAX_RESPONSE_BYTES = 256 * 1024;
const DIAGNOSTIC_DELAY_MS = 100;

const encoder = new TextEncoder();
let pyodide;
let latestDocument = null;
let diagnosticTimer = null;
let unavailable = null;
let appliedCatalogDocument = null;
let appliedCatalog = null;

function exactObject(value, fields) {
  return value !== null
    && typeof value === "object"
    && !Array.isArray(value)
    && Object.keys(value).length === fields.length
    && fields.every((field) => Object.hasOwn(value, field));
}

function validPosition(value) {
  return exactObject(value, ["line", "character"])
    && Number.isSafeInteger(value.line)
    && value.line >= 0
    && Number.isSafeInteger(value.character)
    && value.character >= 0;
}

function validRegion(value) {
  return exactObject(value, ["id", "source"])
    && typeof value.id === "string"
    && value.id.length > 0
    && value.id.length <= 128
    && typeof value.source === "string";
}

function send(message) {
  const serialized = JSON.stringify(message);
  if (encoder.encode(serialized).byteLength > MAX_RESPONSE_BYTES) {
    self.postMessage({
      schemaVersion: SCHEMA_VERSION,
      type: "unavailable",
      message: "Citry analysis returned an oversized response.",
    });
    return;
  }
  self.postMessage(message);
}

async function fetchText(relativeUrl) {
  const response = await fetch(new URL(relativeUrl, import.meta.url), { cache: "no-cache" });
  if (!response.ok) throw new Error(`${relativeUrl} returned HTTP ${response.status}.`);
  return response.text();
}

async function initialize() {
  try {
    if (typeof WebAssembly !== "object") throw new Error("This browser does not support WebAssembly.");
    const [runtimeText, portableSource, adapterSource] = await Promise.all([
      fetchText("./runtime.json"),
      fetchText("./portable_ide.py"),
      fetchText("./analysis_adapter.py"),
    ]);
    const runtime = JSON.parse(runtimeText);
    if (runtime.schema_version !== 1 || !Array.isArray(runtime.packages)) {
      throw new Error("The playground runtime configuration is invalid.");
    }
    const corePackage = runtime.packages.filter((packageInfo) => packageInfo?.name === "citry-core");
    if (corePackage.length !== 1 || corePackage[0].version !== runtime.citry?.core_version) {
      throw new Error("The playground runtime must contain one matching citry-core package.");
    }

    const { loadPyodide } = await import(runtime.pyodide.module_url);
    pyodide = await loadPyodide({ indexURL: runtime.pyodide.index_url });
    await pyodide.loadPackage(new URL(corePackage[0].url, import.meta.url).href);
    pyodide.FS.writeFile("/citry_portable_ide.py", portableSource);
    pyodide.runPython("import sys\n'/' not in sys.path and sys.path.insert(0, '/')\nimport citry_portable_ide");
    pyodide.runPython(adapterSource);
    const installed = pyodide.runPython(
      "import importlib.metadata\nimportlib.metadata.version('citry-core')",
    );
    if (installed !== corePackage[0].version) {
      throw new Error(`Installed citry-core ${installed} does not match ${corePackage[0].version}.`);
    }
    send({
      schemaVersion: SCHEMA_VERSION,
      type: "ready",
      provider: `citry-core@${installed}`,
    });
  } catch (error) {
    unavailable = String(error?.message || error);
    send({ schemaVersion: SCHEMA_VERSION, type: "unavailable", message: unavailable });
    throw error;
  }
}

const ready = initialize();

function callPython(name, ...args) {
  const operation = pyodide.globals.get(name);
  try {
    return JSON.parse(operation(...args));
  } finally {
    operation.destroy();
  }
}

function synchronizeCatalog(document) {
  if (appliedCatalogDocument === document && appliedCatalog === document.catalog) return;
  callPython("update_catalog_json", JSON.stringify(document.catalog));
  appliedCatalogDocument = document;
  appliedCatalog = document.catalog;
}

async function analyze(document) {
  try {
    await ready;
    if (latestDocument !== document) return;
    synchronizeCatalog(document);
    const result = callPython(
      "analyze_regions_json",
      JSON.stringify(document.regions.map(({ id, source }) => ({ id, source }))),
    );
    if (latestDocument !== document) return;
    send({
      schemaVersion: SCHEMA_VERSION,
      type: "diagnostics",
      version: document.version,
      diagnostics: result.diagnostics,
    });
  } catch (error) {
    if (unavailable !== null || latestDocument !== document) return;
    send({
      schemaVersion: SCHEMA_VERSION,
      type: "analysis-error",
      version: document.version,
      message: String(error?.message || error),
    });
  }
}

function updateDocument(data) {
  if (
    !exactObject(data, ["schemaVersion", "type", "version", "regions"])
    || data.schemaVersion !== SCHEMA_VERSION
    || data.type !== "document"
    || !Number.isSafeInteger(data.version)
    || data.version < 0
    || !Array.isArray(data.regions)
    || !data.regions.every(validRegion)
    || encoder.encode(data.regions.map((region) => region.source).join("")).byteLength > MAX_SOURCE_BYTES
  ) {
    return;
  }
  const ids = new Set(data.regions.map((region) => region.id));
  if (ids.size !== data.regions.length) return;
  latestDocument = { ...data, catalog: null };
  clearTimeout(diagnosticTimer);
  diagnosticTimer = setTimeout(() => void analyze(latestDocument), DIAGNOSTIC_DELAY_MS);
}

function updateCatalog(data) {
  if (
    !exactObject(data, ["schemaVersion", "type", "version", "snapshot"])
    || data.schemaVersion !== SCHEMA_VERSION
    || data.type !== "catalog"
    || !Number.isSafeInteger(data.version)
    || data.version < 0
    || (data.snapshot !== null && (typeof data.snapshot !== "object" || Array.isArray(data.snapshot)))
    || encoder.encode(JSON.stringify(data.snapshot)).byteLength > MAX_RESPONSE_BYTES
    || latestDocument?.version !== data.version
  ) {
    return;
  }
  latestDocument.catalog = data.snapshot;
  clearTimeout(diagnosticTimer);
  diagnosticTimer = setTimeout(() => void analyze(latestDocument), 0);
}

async function answer(data) {
  const kind = data.type;
  try {
    await ready;
    const document = latestDocument;
    const region = document?.regions.find((candidate) => candidate.id === data.regionId);
    let value = null;
    if (document?.version === data.version && region) {
      synchronizeCatalog(document);
      const operation = kind === "completion" ? "complete_region_json" : "hover_region_json";
      value = callPython(operation, region.source, JSON.stringify(data.position));
    }
    send({
      schemaVersion: SCHEMA_VERSION,
      type: "response",
      kind,
      requestId: data.requestId,
      version: data.version,
      value,
    });
  } catch (error) {
    console.error(`Citry ${kind} request failed: ${String(error?.message || error)}`);
    send({
      schemaVersion: SCHEMA_VERSION,
      type: "response",
      kind,
      requestId: data.requestId,
      version: data.version,
      value: null,
    });
  }
}

self.onmessage = ({ data }) => {
  if (data?.type === "document") {
    updateDocument(data);
    return;
  }
  if (data?.type === "catalog") {
    updateCatalog(data);
    return;
  }
  if (
    exactObject(data, ["schemaVersion", "type", "requestId", "version", "regionId", "position"])
    && data.schemaVersion === SCHEMA_VERSION
    && ["completion", "hover"].includes(data.type)
    && typeof data.requestId === "string"
    && data.requestId.length > 0
    && data.requestId.length <= 128
    && Number.isSafeInteger(data.version)
    && data.version >= 0
    && typeof data.regionId === "string"
    && validPosition(data.position)
  ) {
    void answer(data);
  }
};
