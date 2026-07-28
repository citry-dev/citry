import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import process from "node:process";
import crypto from "node:crypto";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";

for (const name of ["PYODIDE_DIR", "CITRY_CORE_WHEEL", "PLAYWRIGHT_MODULE"]) {
  if (!process.env[name]) {
    throw new Error(`Missing ${name}`);
  }
}

const playwrightModulePath = process.env.PLAYWRIGHT_MODULE.startsWith("file:")
  ? fileURLToPath(process.env.PLAYWRIGHT_MODULE)
  : process.env.PLAYWRIGHT_MODULE;
const playwrightModule = await import(process.env.PLAYWRIGHT_MODULE);
const playwright = playwrightModule.default ?? playwrightModule;
const playwrightPackage = JSON.parse(
  fs.readFileSync(
    path.join(path.dirname(playwrightModulePath), "package.json"),
    "utf8",
  ),
);
if (playwrightPackage.version !== "1.61.0") {
  throw new Error(`Expected Playwright 1.61.0, received ${playwrightPackage.version}`);
}

const proofDirectory = path.dirname(fileURLToPath(import.meta.url));
const manifestPath = process.env.RUNTIME_MANIFEST
  ?? path.join(proofDirectory, "runtime_manifest.json");
const manifest = JSON.parse(
  fs.readFileSync(manifestPath, "utf8"),
);
const browserNames = (process.env.PLAYWRIGHT_BROWSERS ?? "chromium")
  .split(",")
  .map((name) => name.trim())
  .filter(Boolean);

function verifyArtifact(file, expected) {
  const bytes = fs.statSync(file).size;
  const sha256 = crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
  if (bytes !== expected.bytes || sha256 !== expected.sha256) {
    throw new Error(`Artifact verification failed for ${file}`);
  }
}

for (const artifact of manifest.pyodide.artifacts) {
  verifyArtifact(path.join(process.env.PYODIDE_DIR, artifact.file), artifact);
}
const allowedPyodideArtifacts = new Set(
  manifest.pyodide.artifacts.map((artifact) => artifact.file),
);
const coreArtifact = manifest.custom_wheels.find((artifact) =>
  artifact.file.startsWith("citry_core-1.4.0-"),
);
if (!coreArtifact || path.basename(process.env.CITRY_CORE_WHEEL) !== coreArtifact.file) {
  throw new Error("CITRY_CORE_WHEEL does not match the manifest filename");
}
verifyArtifact(process.env.CITRY_CORE_WHEEL, coreArtifact);

const requestLog = [];
const contentSecurityPolicy = [
  "default-src 'self'",
  "connect-src 'self'",
  "frame-src 'self'",
  "img-src 'self' data:",
  "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'",
  "worker-src 'self'",
].join("; ");

function sendFile(response, file, contentType) {
  response.writeHead(200, {
    "Content-Security-Policy": contentSecurityPolicy,
    "Content-Type": contentType,
  });
  fs.createReadStream(file).pipe(response);
}

const server = http.createServer((request, response) => {
  const url = new URL(request.url, "http://127.0.0.1");
  requestLog.push({
    cookie: request.headers.cookie ?? null,
    origin: request.headers.origin ?? null,
    path: url.pathname,
    referer: request.headers.referer ?? null,
  });

  if (url.pathname === "/") {
    response.setHeader("Set-Cookie", "probe_cookie=docs-secret; Path=/; SameSite=Lax");
    sendFile(response, path.join(proofDirectory, "browser_harness.html"), "text/html; charset=utf-8");
    return;
  }
  if (url.pathname === "/runtime_worker.mjs") {
    sendFile(response, path.join(proofDirectory, "runtime_worker.mjs"), "text/javascript; charset=utf-8");
    return;
  }
  if (url.pathname.startsWith("/artifacts/pyodide/")) {
    const artifactName = path.basename(url.pathname);
    if (!allowedPyodideArtifacts.has(artifactName)) {
      response.writeHead(404);
      response.end("artifact is not present in runtime_manifest.json");
      return;
    }
    const contentType = artifactName.endsWith(".mjs")
      ? "text/javascript; charset=utf-8"
      : artifactName.endsWith(".json")
        ? "application/json"
        : artifactName.endsWith(".wasm")
          ? "application/wasm"
          : "application/octet-stream";
    sendFile(
      response,
      path.join(process.env.PYODIDE_DIR, artifactName),
      contentType,
    );
    return;
  }
  if (url.pathname === "/artifacts/citry_core-1.4.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl") {
    sendFile(response, process.env.CITRY_CORE_WHEEL, "application/zip");
    return;
  }
  if (["/worker-fetch", "/iframe-fetch"].includes(url.pathname)) {
    response.writeHead(200, {
      "Access-Control-Allow-Origin": "*",
      "Content-Type": "application/json",
    });
    response.end(JSON.stringify({
      cookie: request.headers.cookie ?? null,
      origin: request.headers.origin ?? null,
    }));
    return;
  }
  if (url.pathname === "/pixel.png") {
    const pixel = Buffer.from(
      "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
      "base64",
    );
    response.writeHead(200, { "Content-Type": "image/png" });
    response.end(pixel);
    return;
  }
  if (["/popup", "/top-nav", "/frame-nav"].includes(url.pathname)) {
    response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    response.end(`<!doctype html><title>${url.pathname}</title>`);
    return;
  }
  if (url.pathname === "/download") {
    response.writeHead(200, {
      "Content-Disposition": "attachment; filename=probe.txt",
      "Content-Type": "text/plain",
    });
    response.end("downloaded");
    return;
  }
  response.writeHead(404);
  response.end("not found");
});

await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const address = server.address();
const origin = `http://127.0.0.1:${address.port}`;
const results = [];

try {
  for (const browserName of browserNames) {
    const browserType = playwright[browserName];
    if (!browserType) {
      throw new Error(`Unknown Playwright browser ${browserName}`);
    }
    const browser = await browserType.launch({ headless: true });
    const page = await browser.newPage();
    const consoleMessages = [];
    const requestStart = requestLog.length;
    let downloads = 0;
    let popups = 0;
    page.on("console", (message) => consoleMessages.push({
      text: message.text(),
      type: message.type(),
    }));
    page.on("download", () => { downloads += 1; });
    page.on("popup", () => { popups += 1; });

    try {
      await page.goto(origin, { waitUntil: "load" });
      const userAgent = await page.evaluate(() => navigator.userAgent);
      const worker = await page.evaluate(() => window.runWorkerSmoke());
      const termination = await page.evaluate(() => window.runWorkerTermination());
      const iframe = await page.evaluate(() => window.runIframeProbe());
      await page.waitForTimeout(500);
      const frameURLs = page.frames().map((frame) => frame.url());
      const browserRequests = requestLog.slice(requestStart);

      assert.equal(worker.result.compiled, true);
      assert.equal(worker.result.safe_eval, 42);
      assert.equal(worker.result.marked, '<main data-citry="">Hello</main>');
      assert.deepEqual(worker.result.used_variables, ["title"]);
      assert.equal(worker.result.network.cookie, "probe_cookie=docs-secret");
      assert.equal(worker.floodMessages, 250);
      for (const capability of [
        "fetch", "postMessage", "close", "WebSocket", "indexedDB", "caches",
      ]) {
        assert.equal(worker.result.capabilities[capability], true);
      }
      assert.equal(worker.result.capabilities.document, false);
      assert.equal(worker.result.capabilities.localStorage, false);
      assert.equal(termination.blockedWorkerAnsweredPing, false);
      assert.equal(termination.recovery.result.safe_eval, 42);
      assert.equal(termination.recovery.floodMessages, 250);
      assert.equal(iframe.floodMessages, 250);
      assert.equal(iframe.report.messageOrigin, "null");
      assert.equal(iframe.report.origin, "null");
      assert.equal(iframe.report.parentAccess, false);
      assert.equal(iframe.report.localStorage, false);
      assert.equal(iframe.report.indexedDB, false);
      if (browserName === "webkit") {
        assert.equal(iframe.report.fetch.ok, false);
        assert.equal(
          browserRequests.some((entry) => entry.path === "/iframe-fetch"),
          false,
        );
      } else {
        assert.equal(iframe.report.fetch.ok, true);
        assert.equal(iframe.report.fetch.server.cookie, null);
        assert.equal(iframe.report.fetch.server.origin, "null");
      }
      assert.equal(iframe.report.relativeImage, true);
      assert.equal(iframe.report.absoluteImage, true);
      assert.equal(iframe.report.externalFetch, false);
      assert.equal(iframe.report.externalImage, false);
      assert.equal(iframe.report.popup, false);
      assert.equal(iframe.report.topNavigationAssignment, false);
      assert.equal(downloads, 0);
      assert.equal(popups, 0);
      assert.equal(page.url(), `${origin}/`);
      assert.equal(frameURLs.includes(`${origin}/frame-nav`), true);
      assert.equal(browserRequests.some((entry) => entry.path === "/download"), true);
      assert.equal(browserRequests.some((entry) => entry.path === "/frame-nav"), true);

      results.push({
        browser: browserName,
        browserVersion: browser.version(),
        consoleMessages,
        downloads,
        frameURLs,
        iframe,
        parentURL: page.url(),
        popups,
        requests: browserRequests.filter((entry) => [
          "/download", "/frame-nav", "/iframe-fetch", "/pixel.png", "/popup",
          "/top-nav", "/worker-fetch",
        ].includes(entry.path)),
        termination,
        userAgent,
        worker,
      });
    } catch (error) {
      console.error(JSON.stringify({
        browser: browserName,
        consoleMessages,
        error: String(error),
        requests: requestLog.slice(requestStart),
      }, null, 2));
      throw error;
    } finally {
      await page.close();
      await browser.close();
    }
  }

  console.log(JSON.stringify({
    manifest: manifestPath,
    playwright: playwrightPackage.version,
    results,
  }, null, 2));
} finally {
  await new Promise((resolve) => server.close(resolve));
}
