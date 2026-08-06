import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

for (const name of [
  "PLAYWRIGHT_MODULE",
  "PYODIDE_DIR",
  "RUNTIME_MANIFEST",
  "WHEELHOUSE",
]) {
  if (!process.env[name]) {
    throw new Error(`Missing ${name}`);
  }
}

const playwrightModule = await import(process.env.PLAYWRIGHT_MODULE);
const playwright = playwrightModule.default ?? playwrightModule;
const proofDirectory = path.dirname(fileURLToPath(import.meta.url));
const manifest = JSON.parse(fs.readFileSync(process.env.RUNTIME_MANIFEST, "utf8"));
const browserNames = (process.env.PLAYWRIGHT_BROWSERS ?? "chromium")
  .split(",")
  .map((name) => name.trim())
  .filter(Boolean);
const coldRuns = Number(process.env.COLD_RUNS ?? 5);
const warmupRuns = Number(process.env.WARMUP_RUNS ?? 20);
const warmRuns = Number(process.env.WARM_RUNS ?? 200);

function verifyArtifact(filename, artifact) {
  const bytes = fs.statSync(filename).size;
  const sha256 = crypto.createHash("sha256").update(fs.readFileSync(filename)).digest("hex");
  if (path.basename(filename) !== artifact.file || bytes !== artifact.bytes || sha256 !== artifact.sha256) {
    throw new Error(`Artifact verification failed for ${filename}`);
  }
}

const pyodideArtifacts = new Map();
for (const artifact of manifest.pyodide.artifacts) {
  verifyArtifact(path.join(process.env.PYODIDE_DIR, artifact.file), artifact);
  pyodideArtifacts.set(artifact.file, artifact);
}

const wheelArtifacts = new Map();
for (const artifact of manifest.custom_wheels) {
  wheelArtifacts.set(artifact.file, artifact);
}
wheelArtifacts.set(manifest.public_package_track.citry.file, manifest.public_package_track.citry);
for (const artifact of manifest.public_package_track.dependencies) {
  if (artifact.file) {
    wheelArtifacts.set(artifact.file, artifact);
  }
}
for (const filename of manifest.public_package_track.install_order) {
  verifyArtifact(path.join(process.env.WHEELHOUSE, filename), wheelArtifacts.get(filename));
}

const wheelURLs = manifest.public_package_track.install_order.map(
  (filename) => `/artifacts/wheels/${filename}`,
);
const contentSecurityPolicy = [
  "default-src 'self'",
  "connect-src 'self'",
  "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'",
  "worker-src 'self'",
].join("; ");

function sendFile(response, filename, contentType) {
  response.writeHead(200, {
    "Cache-Control": "public, max-age=31536000, immutable",
    "Content-Security-Policy": contentSecurityPolicy,
    "Content-Type": contentType,
    "Cross-Origin-Embedder-Policy": "require-corp",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
  });
  fs.createReadStream(filename).pipe(response);
}

const server = http.createServer((request, response) => {
  const url = new URL(request.url, "http://127.0.0.1");
  if (url.pathname === "/") {
    const source = fs.readFileSync(path.join(proofDirectory, "performance_harness.html"), "utf8")
      .replace("<body>", `<body data-wheel-urls='${JSON.stringify(wheelURLs)}'>`);
    response.writeHead(200, {
      "Cache-Control": "no-store",
      "Content-Security-Policy": contentSecurityPolicy,
      "Content-Type": "text/html; charset=utf-8",
      "Cross-Origin-Embedder-Policy": "require-corp",
      "Cross-Origin-Opener-Policy": "same-origin",
    });
    response.end(source);
    return;
  }
  if (url.pathname === "/performance_worker.mjs") {
    sendFile(
      response,
      path.join(proofDirectory, "performance_worker.mjs"),
      "text/javascript; charset=utf-8",
    );
    return;
  }
  if (url.pathname.startsWith("/artifacts/pyodide/")) {
    const filename = path.basename(url.pathname);
    if (!pyodideArtifacts.has(filename)) {
      response.writeHead(404).end("unknown Pyodide artifact");
      return;
    }
    const contentType = filename.endsWith(".mjs")
      ? "text/javascript; charset=utf-8"
      : filename.endsWith(".wasm")
        ? "application/wasm"
        : filename.endsWith(".json")
          ? "application/json"
          : "application/octet-stream";
    sendFile(response, path.join(process.env.PYODIDE_DIR, filename), contentType);
    return;
  }
  if (url.pathname.startsWith("/artifacts/wheels/")) {
    const filename = path.basename(url.pathname);
    if (!manifest.public_package_track.install_order.includes(filename)) {
      response.writeHead(404).end("unknown wheel artifact");
      return;
    }
    sendFile(response, path.join(process.env.WHEELHOUSE, filename), "application/zip");
    return;
  }
  response.writeHead(404).end("not found");
});

await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const results = [];

try {
  for (const browserName of browserNames) {
    const browserType = playwright[browserName];
    if (!browserType) {
      throw new Error(`Unknown Playwright browser ${browserName}`);
    }
    const browser = await browserType.launch({ headless: true });
    const page = await browser.newPage();
    const pageErrors = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    try {
      await page.goto(origin, { waitUntil: "load" });
      const result = await page.evaluate(
        (options) => window.runPerformanceProbe(options),
        { coldRuns, warmupRuns, warmRuns },
      );
      assert.equal(result.cross_origin_isolated, true);
      assert.equal(result.deterministic, true);
      assert.equal(result.cold.length, coldRuns);
      assert.equal(result.warm.runs, warmRuns);
      assert.deepEqual(pageErrors, []);
      results.push({
        browser: browserName,
        browserVersion: browser.version(),
        pageErrors,
        result,
      });
    } finally {
      await page.close();
      await browser.close();
    }
  }
  console.log(JSON.stringify({
    manifest: process.env.RUNTIME_MANIFEST,
    options: { coldRuns, warmupRuns, warmRuns },
    results,
  }, null, 2));
} finally {
  await new Promise((resolve) => server.close(resolve));
}
