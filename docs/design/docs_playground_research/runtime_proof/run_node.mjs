import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { pathToFileURL } from "node:url";

const required = [
  "PYODIDE_DIR",
  "RUNTIME_MANIFEST",
  "RUNTIME_TRACK",
  "SMOKE_FILE",
  "WHEELHOUSE",
];
for (const name of required) {
  if (!process.env[name]) {
    throw new Error(`Missing ${name}`);
  }
}

if (!["direct-core-1.4", "historical-public-0.2"].includes(process.env.RUNTIME_TRACK)) {
  throw new Error(`Unsupported RUNTIME_TRACK ${process.env.RUNTIME_TRACK}`);
}

const manifestBytes = fs.readFileSync(process.env.RUNTIME_MANIFEST);
const manifest = JSON.parse(manifestBytes);
if (manifest.schema_version !== 1) {
  throw new Error(`Unsupported runtime manifest schema ${manifest.schema_version}`);
}

function verifyArtifact(filename, artifact) {
  if (!artifact || path.basename(filename) !== artifact.file) {
    throw new Error(`Artifact name does not match the manifest: ${filename}`);
  }
  const bytes = fs.statSync(filename).size;
  const sha256 = crypto.createHash("sha256").update(fs.readFileSync(filename)).digest("hex");
  if (bytes !== artifact.bytes || sha256 !== artifact.sha256) {
    throw new Error(`Artifact verification failed for ${filename}`);
  }
  return filename;
}

for (const artifact of manifest.pyodide.artifacts) {
  verifyArtifact(path.join(process.env.PYODIDE_DIR, artifact.file), artifact);
}

const allWheels = new Map();
for (const artifact of manifest.custom_wheels) {
  allWheels.set(artifact.file, artifact);
}
allWheels.set(
  manifest.public_package_track.citry.file,
  manifest.public_package_track.citry,
);
for (const artifact of manifest.public_package_track.dependencies) {
  if (artifact.file) {
    allWheels.set(artifact.file, artifact);
  }
}

let wheelFiles;
if (process.env.RUNTIME_TRACK === "direct-core-1.4") {
  wheelFiles = [
    manifest.custom_wheels.find((artifact) => artifact.file.startsWith("citry_core-1.4.0-"))
      ?.file,
  ];
} else {
  wheelFiles = manifest.public_package_track.install_order;
}
if (wheelFiles.some((filename) => !filename)) {
  throw new Error(`Manifest is incomplete for ${process.env.RUNTIME_TRACK}`);
}

const wheelPaths = wheelFiles.map((filename) =>
  verifyArtifact(path.join(process.env.WHEELHOUSE, filename), allWheels.get(filename)),
);

const networkAttempts = [];
const originalFetch = globalThis.fetch;
globalThis.fetch = async (input, init) => {
  const url = typeof input === "string" || input instanceof URL
    ? String(input)
    : String(input?.url ?? input);
  if (/^https?:/u.test(url)) {
    networkAttempts.push(url);
    throw new Error(`Live network access is disabled by the sealed proof: ${url}`);
  }
  return originalFetch(input, init);
};

const timings = {};
const pyodideModule = path.join(process.env.PYODIDE_DIR, "pyodide.mjs");
const { loadPyodide } = await import(pathToFileURL(pyodideModule));

let started = performance.now();
const pyodide = await loadPyodide({
  indexURL: `${path.resolve(process.env.PYODIDE_DIR)}${path.sep}`,
});
timings.pyodide_ms = performance.now() - started;

started = performance.now();
await pyodide.loadPackage(wheelPaths);
timings.packages_ms = performance.now() - started;

started = performance.now();
const source = fs.readFileSync(process.env.SMOKE_FILE, "utf8");
const result = pyodide.runPython(source);
timings.smoke_ms = performance.now() - started;

if (networkAttempts.length !== 0) {
  throw new Error(`Sealed proof attempted network access: ${networkAttempts.join(", ")}`);
}

console.log(JSON.stringify({
  installed_artifacts: wheelFiles,
  manifest_sha256: crypto.createHash("sha256").update(manifestBytes).digest("hex"),
  network_attempts: networkAttempts,
  result: JSON.parse(result),
  runtime_track: process.env.RUNTIME_TRACK,
  timings,
}, null, 2));
