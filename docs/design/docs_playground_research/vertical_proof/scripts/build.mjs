import crypto from "node:crypto";
import fs from "node:fs";
import { cp, mkdir, readFile, rename, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { build } from "esbuild";

const root = path.resolve(import.meta.dirname, "..");
const researchRoot = path.resolve(root, "..");
const dist = path.join(root, "dist");
const pyodideDirectory = process.env.PYODIDE_DIR;
const wheelhouse = process.env.WHEELHOUSE;
const runnerOrigin = process.env.RUNNER_ORIGIN ?? "http://127.0.0.1:43174";
const runtimeManifestPath = process.env.RUNTIME_MANIFEST
  ?? path.join(researchRoot, "runtime_proof", "runtime_manifest.json");
const packageTrackName = process.env.PACKAGE_TRACK ?? "current_package_track";

if (!pyodideDirectory || !wheelhouse) {
  throw new Error("PYODIDE_DIR and WHEELHOUSE are required. The build never resolves runtime packages.");
}

const sha256 = (value) => crypto.createHash("sha256").update(value).digest("hex");
const manifest = JSON.parse(await readFile(runtimeManifestPath, "utf8"));
const packageTrack = manifest[packageTrackName];
if (!packageTrack) throw new Error(`Runtime manifest has no package track named ${packageTrackName}`);
const executorSource = await readFile(path.join(root, "src", "executor.py"), "utf8");
const protocolVersion = 1;

function artifactMap() {
  const values = new Map();
  for (const artifact of manifest.pyodide.artifacts) values.set(artifact.file, artifact);
  for (const artifact of manifest.custom_wheels) values.set(artifact.file, artifact);
  for (const trackName of ["public_package_track", "current_package_track"]) {
    const track = manifest[trackName];
    if (!track) continue;
    values.set(track.citry.file, track.citry);
    for (const artifact of track.dependencies) {
      if (artifact.file) values.set(artifact.file, artifact);
    }
  }
  return values;
}

async function verify(filename, expected) {
  const contents = await readFile(filename);
  if (
    path.basename(filename) !== expected.file
    || contents.byteLength !== expected.bytes
    || sha256(contents) !== expected.sha256
  ) throw new Error(`Artifact verification failed for ${filename}`);
  return contents;
}

const knownArtifacts = artifactMap();
const selectedPyodide = manifest.pyodide.artifacts;
const selectedWheels = packageTrack.install_order.map((filename) => {
  const artifact = knownArtifacts.get(filename);
  if (!artifact) throw new Error(`Runtime manifest does not describe ${filename}`);
  return artifact;
});
const citryCore = packageTrack.dependencies.find((dependency) => dependency.name === "citry-core");
if (!citryCore) throw new Error(`${packageTrackName} has no citry-core dependency`);
const runtimeLabel = `Pyodide ${manifest.pyodide.version} / citry ${packageTrack.citry.version} / citry-core ${citryCore.version}`;
const runtimeLock = {
  schema: 1,
  protocolVersion,
  pyodide: manifest.pyodide.version,
  python: manifest.pyodide.python,
  packageTrack: packageTrackName,
  citry: packageTrack.citry.version,
  citryCore: citryCore.version,
  installOrder: packageTrack.install_order,
  artifacts: [...selectedPyodide, ...selectedWheels].map((artifact) => ({
    name: artifact.file,
    bytes: artifact.bytes,
    sha256: artifact.sha256,
  })),
};
const bundleId = sha256(JSON.stringify(runtimeLock)).slice(0, 20);

await rm(dist, { recursive: true, force: true });
const runtimeRoot = path.join(dist, "runner", bundleId, "runtime");
const pyodideTarget = path.join(runtimeRoot, "pyodide");
const wheelTarget = path.join(runtimeRoot, "wheels");
await Promise.all([
  mkdir(path.join(dist, "docs", "assets"), { recursive: true }),
  mkdir(path.join(dist, "docs", "playground"), { recursive: true }),
  mkdir(path.join(dist, "docs", "citry-docs", "assets"), { recursive: true }),
  mkdir(path.join(dist, "docs", "citry-docs", "playground"), { recursive: true }),
  mkdir(pyodideTarget, { recursive: true }),
  mkdir(wheelTarget, { recursive: true }),
]);

for (const artifact of selectedPyodide) {
  const source = path.join(pyodideDirectory, artifact.file);
  await verify(source, artifact);
  await cp(source, path.join(pyodideTarget, artifact.file));
}
for (const artifact of selectedWheels) {
  const source = path.join(wheelhouse, artifact.file);
  await verify(source, artifact);
  await cp(source, path.join(wheelTarget, artifact.file));
}

const runtimeConfig = {
  pyodideIndex: `./runtime/pyodide/`,
  artifacts: [
    ...selectedPyodide.map((artifact) => ({
      kind: "pyodide",
      name: artifact.file,
      path: `./runtime/pyodide/${artifact.file}`,
      bytes: artifact.bytes,
      sha256: artifact.sha256,
    })),
    ...selectedWheels.map((artifact) => ({
      kind: "wheel",
      name: artifact.file,
      path: `./runtime/wheels/${artifact.file}`,
      bytes: artifact.bytes,
      sha256: artifact.sha256,
    })),
  ],
};

const runnerDirectory = path.join(dist, "runner", bundleId);
const workerTemporary = path.join(runnerDirectory, "worker.tmp.mjs");
await build({
  entryPoints: [path.join(root, "src", "worker.mjs")],
  outfile: workerTemporary,
  bundle: true,
  format: "esm",
  platform: "browser",
  target: "es2022",
  minify: true,
  sourcemap: false,
  define: {
    __EXECUTOR_SOURCE__: JSON.stringify(executorSource),
    __RUNTIME_CONFIG__: JSON.stringify(runtimeConfig),
  },
});
const workerContents = await readFile(workerTemporary);
const workerName = `worker.${sha256(workerContents).slice(0, 16)}.mjs`;
await rename(workerTemporary, path.join(runnerDirectory, workerName));

const runnerTemporary = path.join(runnerDirectory, "runner.tmp.mjs");
await build({
  entryPoints: [path.join(root, "src", "runner.mjs")],
  outfile: runnerTemporary,
  bundle: true,
  format: "esm",
  platform: "browser",
  target: "es2022",
  minify: true,
  sourcemap: false,
  define: {
    __PROTOCOL_VERSION__: String(protocolVersion),
    __RUNTIME_LABEL__: JSON.stringify(runtimeLabel),
    __WORKER_URL__: JSON.stringify(`./${workerName}`),
  },
});
const runnerContents = await readFile(runnerTemporary);
const runnerName = `runner.${sha256(runnerContents).slice(0, 16)}.mjs`;
await rename(runnerTemporary, path.join(runnerDirectory, runnerName));
const previewTemporary = path.join(runnerDirectory, "preview.tmp.mjs");
await build({
  entryPoints: [path.join(root, "src", "preview.mjs")],
  outfile: previewTemporary,
  bundle: true,
  format: "esm",
  platform: "browser",
  target: "es2022",
  minify: true,
  sourcemap: false,
  define: { __PROTOCOL_VERSION__: String(protocolVersion) },
});
const previewContents = await readFile(previewTemporary);
const previewName = `preview.${sha256(previewContents).slice(0, 16)}.mjs`;
await rename(previewTemporary, path.join(runnerDirectory, previewName));
const runnerHTML = (await readFile(path.join(root, "src", "runner.html"), "utf8"))
  .replace("__RUNNER_JS__", `./${runnerName}`);
await writeFile(path.join(runnerDirectory, "runner.html"), runnerHTML);
const previewHTML = (await readFile(path.join(root, "src", "preview.html"), "utf8"))
  .replace("__PREVIEW_JS__", `./${previewName}`);
await writeFile(path.join(runnerDirectory, "preview.html"), previewHTML);
await writeFile(path.join(runnerDirectory, "runtime-lock.json"), `${JSON.stringify(runtimeLock, null, 2)}\n`);

const hostTemporary = path.join(dist, "docs", "assets", "playground.tmp.mjs");
await build({
  entryPoints: [path.join(root, "src", "host.mjs")],
  outfile: hostTemporary,
  bundle: true,
  format: "esm",
  platform: "browser",
  target: "es2022",
  minify: true,
  sourcemap: false,
  loader: { ".py": "text" },
  define: { __PROTOCOL_VERSION__: String(protocolVersion) },
});
const hostContents = await readFile(hostTemporary);
const hostName = `playground.${sha256(hostContents).slice(0, 16)}.mjs`;
await rename(hostTemporary, path.join(dist, "docs", "assets", hostName));

const cssTemporary = path.join(dist, "docs", "assets", "playground.tmp.css");
await build({
  entryPoints: [path.join(root, "src", "host.css")],
  outfile: cssTemporary,
  bundle: true,
  minify: true,
  sourcemap: false,
});
const cssContents = await readFile(cssTemporary);
const cssName = `playground.${sha256(cssContents).slice(0, 16)}.css`;
await rename(cssTemporary, path.join(dist, "docs", "assets", cssName));

const hostTemplate = await readFile(path.join(root, "src", "host.html"), "utf8");
for (const basePath of ["/", "/citry-docs/"]) {
  const nested = basePath !== "/";
  const outputRoot = nested ? path.join(dist, "docs", "citry-docs") : path.join(dist, "docs");
  if (nested) {
    await cp(path.join(dist, "docs", "assets", hostName), path.join(outputRoot, "assets", hostName));
    await cp(path.join(dist, "docs", "assets", cssName), path.join(outputRoot, "assets", cssName));
  }
  const html = hostTemplate
    .replaceAll("__BASE_PATH__", basePath)
    .replace("__HOST_CSS__", `${basePath}assets/${cssName}`)
    .replace("__HOST_JS__", `${basePath}assets/${hostName}`)
    .replace("__RUNTIME_LABEL__", runtimeLabel)
    .replace("__RUNNER_URL__", `${runnerOrigin}/${bundleId}/runner.html`);
  await writeFile(path.join(outputRoot, "playground", "index.html"), html);
}

const outputFiles = [];
function recordTree(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const filename = path.join(directory, entry.name);
    if (entry.isDirectory()) recordTree(filename);
    else {
      const contents = fs.readFileSync(filename);
      outputFiles.push({
        file: path.relative(dist, filename),
        bytes: contents.byteLength,
        sha256: sha256(contents),
      });
    }
  }
}
recordTree(dist);
await writeFile(path.join(dist, "build-manifest.json"), `${JSON.stringify({ bundleId, runnerOrigin, runtimeLock, files: outputFiles.sort((a, b) => a.file.localeCompare(b.file)) }, null, 2)}\n`);
console.log(JSON.stringify({ bundleId, files: outputFiles.length, runnerOrigin }, null, 2));
