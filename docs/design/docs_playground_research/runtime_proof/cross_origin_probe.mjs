import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createReadStream, readFileSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { basename, dirname, extname, join, normalize } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

if (!process.env.PLAYWRIGHT_MODULE) {
  throw new Error("Missing PLAYWRIGHT_MODULE");
}

const playwrightModule = await import(process.env.PLAYWRIGHT_MODULE);
const playwright = playwrightModule.default ?? playwrightModule;
const playwrightPackage = JSON.parse(
  readFileSync(
    join(dirname(process.env.PLAYWRIGHT_MODULE), "package.json"),
    "utf8",
  ),
);
if (playwrightPackage.version !== "1.61.0") {
  throw new Error(`Expected Playwright 1.61.0, received ${playwrightPackage.version}`);
}

const proofDirectory = dirname(fileURLToPath(import.meta.url));
const includePyodide = process.env.CROSS_ORIGIN_PYODIDE === "1";
const browserNames = (process.env.PLAYWRIGHT_BROWSERS ?? "chromium")
  .split(",")
  .map((name) => name.trim())
  .filter(Boolean);
const logs = { attacker: [], docs: [], runner: [] };
const origins = { attacker: "", docs: "", runner: "" };
const mimeTypes = new Map([
  [".html", "text/html; charset=utf-8"],
  [".json", "application/json"],
  [".mjs", "text/javascript; charset=utf-8"],
  [".wasm", "application/wasm"],
  [".whl", "application/zip"],
]);
let coreArtifact;
let allowedPyodideArtifacts = new Set();
let manifest;

function verifyArtifact(filename, expected) {
  const bytes = statSync(filename).size;
  const sha256 = createHash("sha256").update(readFileSync(filename)).digest("hex");
  if (bytes !== expected.bytes || sha256 !== expected.sha256) {
    throw new Error(`Artifact verification failed for ${filename}`);
  }
}

if (includePyodide) {
  for (const name of ["PYODIDE_DIR", "CITRY_CORE_WHEEL", "RUNTIME_MANIFEST"]) {
    if (!process.env[name]) {
      throw new Error(`Missing ${name} for the cross-origin Pyodide proof`);
    }
  }
  manifest = JSON.parse(readFileSync(process.env.RUNTIME_MANIFEST, "utf8"));
  for (const artifact of manifest.pyodide.artifacts) {
    verifyArtifact(join(process.env.PYODIDE_DIR, artifact.file), artifact);
  }
  allowedPyodideArtifacts = new Set(
    manifest.pyodide.artifacts.map((artifact) => artifact.file),
  );
  coreArtifact = manifest.custom_wheels.find((artifact) =>
    artifact.file.startsWith("citry_core-1.4.0-"),
  );
  if (!coreArtifact || basename(process.env.CITRY_CORE_WHEEL) !== coreArtifact.file) {
    throw new Error("CITRY_CORE_WHEEL does not match the selected manifest");
  }
  verifyArtifact(process.env.CITRY_CORE_WHEEL, coreArtifact);
}

function requestRecord(request, pathname) {
  return {
    cookie: request.headers.cookie ?? null,
    origin: request.headers.origin ?? null,
    pathname,
    referer: request.headers.referer ?? null,
    secFetchSite: request.headers["sec-fetch-site"] ?? null,
  };
}

function sendFile(response, filename, headers) {
  response.writeHead(200, {
    "Cache-Control": "no-store",
    "Content-Type": mimeTypes.get(extname(filename)) ?? "application/octet-stream",
    ...headers,
  });
  createReadStream(filename).pipe(response);
}

function staticFile(pathname, mapping) {
  const filename = mapping.get(pathname);
  if (!filename) {
    return undefined;
  }
  const candidate = normalize(join(proofDirectory, filename));
  if (!candidate.startsWith(proofDirectory) || basename(candidate) !== filename) {
    return undefined;
  }
  return candidate;
}

const docsFiles = new Map([
  ["/", "cross_origin_parent.html"],
  ["/cross_origin_parent.mjs", "cross_origin_parent.mjs"],
]);
const runnerFiles = new Map([
  ["/runner.html", "cross_origin_runner.html"],
  ["/cross_origin_runner.mjs", "cross_origin_runner.mjs"],
  ["/cross_origin_worker.mjs", "cross_origin_worker.mjs"],
]);
const attackerFiles = new Map([
  ["/attacker.html", "cross_origin_attacker.html"],
  ["/cross_origin_attacker.mjs", "cross_origin_attacker.mjs"],
]);

const docsServer = createServer((request, response) => {
  const url = new URL(request.url, origins.docs || "http://127.0.0.1");
  logs.docs.push(requestRecord(request, url.pathname));
  if (url.pathname === "/docs-sensitive") {
    response.writeHead(200, {
      "Access-Control-Allow-Credentials": "true",
      "Access-Control-Allow-Origin": origins.runner,
      "Cache-Control": "no-store",
      "Content-Type": "application/json",
      Vary: "Origin",
    });
    response.end(JSON.stringify({
      cookie: request.headers.cookie ?? null,
      origin: request.headers.origin ?? null,
    }));
    return;
  }
  const filename = staticFile(url.pathname, docsFiles);
  if (filename) {
    const headers = {
      "Content-Security-Policy": [
        "default-src 'none'",
        "script-src 'self' 'unsafe-inline'",
        `frame-src ${origins.runner} ${origins.attacker}`,
        "connect-src 'self'",
        "img-src data:",
        "style-src 'none'",
        "object-src 'none'",
        "base-uri 'none'",
      ].join("; "),
    };
    if (url.pathname === "/") {
      headers["Set-Cookie"] = "docs_secret=credential; Path=/; HttpOnly; SameSite=Strict";
    }
    sendFile(response, filename, headers);
    return;
  }
  response.writeHead(404).end("not found");
});

const runnerServer = createServer((request, response) => {
  const url = new URL(request.url, origins.runner || "http://127.0.0.2");
  logs.runner.push(requestRecord(request, url.pathname));
  if (url.pathname === "/runner-observe") {
    response.writeHead(200, {
      "Cache-Control": "no-store",
      "Content-Type": "application/json",
    });
    response.end(JSON.stringify({
      cookie: request.headers.cookie ?? null,
      origin: request.headers.origin ?? null,
    }));
    return;
  }
  if (url.pathname === "/preview-nav") {
    response.writeHead(200, {
      "Content-Security-Policy": `default-src 'none'; frame-ancestors ${origins.docs}`,
      "Content-Type": "text/html; charset=utf-8",
    });
    response.end("<!doctype html><title>unexpected preview navigation</title>");
    return;
  }
  if (includePyodide && url.pathname.startsWith("/artifacts/pyodide/")) {
    const artifactName = basename(url.pathname);
    if (!allowedPyodideArtifacts.has(artifactName)) {
      response.writeHead(404).end("artifact is not present in the selected manifest");
      return;
    }
    sendFile(response, join(process.env.PYODIDE_DIR, artifactName), {
      "Content-Security-Policy": "default-src 'none'",
      "Cross-Origin-Resource-Policy": "same-origin",
    });
    return;
  }
  if (includePyodide && url.pathname === `/artifacts/${coreArtifact.file}`) {
    sendFile(response, process.env.CITRY_CORE_WHEEL, {
      "Content-Security-Policy": "default-src 'none'",
      "Cross-Origin-Resource-Policy": "same-origin",
    });
    return;
  }
  const filename = staticFile(url.pathname, runnerFiles);
  if (filename) {
    sendFile(response, filename, {
      "Content-Security-Policy": [
        "default-src 'none'",
        "script-src 'self' 'wasm-unsafe-eval'",
        "worker-src 'self'",
        `connect-src 'self' ${origins.docs}`,
        `frame-ancestors ${origins.docs}`,
        "object-src 'none'",
        "base-uri 'none'",
      ].join("; "),
      "Cross-Origin-Resource-Policy": "same-origin",
    });
    return;
  }
  response.writeHead(404).end("not found");
});

const attackerServer = createServer((request, response) => {
  const url = new URL(request.url, origins.attacker || "http://127.0.0.3");
  logs.attacker.push(requestRecord(request, url.pathname));
  const filename = staticFile(url.pathname, attackerFiles);
  if (filename) {
    sendFile(response, filename, {
      "Content-Security-Policy": [
        "default-src 'none'",
        "script-src 'self'",
        `frame-ancestors ${origins.docs}`,
      ].join("; "),
    });
    return;
  }
  response.writeHead(404).end("not found");
});

async function listen(server, host) {
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, host, resolve);
  });
  return server.address().port;
}

const docsPort = await listen(docsServer, "127.0.0.1");
const runnerPort = await listen(runnerServer, "127.0.0.1");
const attackerPort = await listen(attackerServer, "127.0.0.1");
origins.docs = `http://127.0.0.1:${docsPort}`;
origins.runner = `http://localhost:${runnerPort}`;
origins.attacker = `http://localhost:${attackerPort}`;

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
    page.on("console", (message) => {
      if (message.type() === "error") {
        pageErrors.push(message.text());
      }
    });
    page.on("pageerror", (error) => pageErrors.push(error.message));
    try {
      await page.goto(origins.docs, { waitUntil: "load" });
      const result = await page.evaluate(
        (input) => window.runCrossOriginProbe(input),
        {
          attackerOrigin: origins.attacker,
          docsOrigin: origins.docs,
          includePyodide,
          runnerOrigin: origins.runner,
        },
      );
      const cookies = await page.context().cookies(origins.docs);

      assert.equal(result.first.result.source, "'<p>first</p>'");
      assert.equal(result.timeout.type, "timeout");
      assert.equal(result.recovery.result.workerOrigin, origins.runner);
      assert.equal(result.recovery.result.runner.cookie, null);
      assert.equal(result.recovery.result.docs.cookie, null);
      assert.equal(result.flood.droppedWorkerMessages, 250);
      assert.ok(result.parentFloodDropped >= 150);
      assert.equal(result.oversize.reason, "source-size");
      assert.ok(result.rateLimited > 0);
      assert.ok(result.rejectedWindowMessages.some(
        (message) => message.origin === origins.attacker,
      ));
      assert.equal(result.iframe.sandbox, "allow-scripts allow-same-origin");
      assert.equal(result.iframe.referrerPolicy, "no-referrer");
      assert.equal(result.previewNavigation.recovered, true);
      assert.equal(result.previewNavigation.loads, 2);
      assert.equal(result.previewNavigation.replacementTitle, "Rendered result unavailable");
      if (includePyodide) {
        assert.equal(result.pyodide.result.workerOrigin, origins.runner);
        assert.equal(result.pyodide.result.docs.cookie, null);
        assert.equal(result.pyodide.result.python.compiled, true);
        assert.equal(result.pyodide.result.python.safe_eval, 42);
        assert.equal(
          result.pyodide.result.python.marked,
          '<main data-citry="">Hello</main>',
        );
        assert.deepEqual(result.pyodide.result.python.used_variables, ["title"]);
      }
      assert.equal(page.url(), `${origins.docs}/`);
      assert.ok(cookies.some((cookie) => cookie.name === "docs_secret"));
      assert.equal(logs.runner.some((entry) => entry.cookie !== null), false);
      assert.equal(
        logs.runner.find((entry) => entry.pathname === "/runner.html")?.referer ?? null,
        null,
      );
      assert.equal(
        logs.docs.find((entry) => entry.pathname === "/docs-sensitive")?.cookie ?? null,
        null,
      );
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
    logs,
    origins,
    playwright: playwrightPackage.version,
    results,
  }, null, 2));
} finally {
  await Promise.all(
    [docsServer, runnerServer, attackerServer].map(
      (server) => new Promise((resolve) => server.close(resolve)),
    ),
  );
}
