import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { chromium, firefox, webkit } from "playwright";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dist = path.join(root, "dist");
const buildManifest = JSON.parse(fs.readFileSync(path.join(dist, "build-manifest.json"), "utf8"));
const docsOrigin = "http://localhost:43173";
const runnerOrigin = "http://127.0.0.1:43174";
const browserNames = (process.env.PLAYWRIGHT_BROWSERS ?? "chromium,firefox,webkit")
  .split(",")
  .map((value) => value.trim())
  .filter(Boolean);
const browserTypes = { chromium, firefox, webkit };
const requestLog = [];

const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".wasm": "application/wasm",
  ".whl": "application/zip",
  ".zip": "application/zip",
};

function safeFile(rootDirectory, requestPath) {
  const decoded = decodeURIComponent(requestPath);
  const relative = decoded.replace(/^\/+/, "");
  const candidate = path.resolve(rootDirectory, relative);
  if (!candidate.startsWith(`${path.resolve(rootDirectory)}${path.sep}`)) return null;
  if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) return path.join(candidate, "index.html");
  return candidate;
}

function serveFile(response, filename, headers = {}) {
  if (!filename || !fs.existsSync(filename) || !fs.statSync(filename).isFile()) {
    response.writeHead(404, { "Content-Type": "text/plain" }).end("not found");
    return;
  }
  response.writeHead(200, {
    "Cache-Control": filename.endsWith(".html") ? "no-cache" : "public, max-age=31536000, immutable",
    "Content-Type": contentTypes[path.extname(filename)] ?? "application/octet-stream",
    ...headers,
  });
  fs.createReadStream(filename).pipe(response);
}

const docsServer = http.createServer((request, response) => {
  const url = new URL(request.url, docsOrigin);
  requestLog.push({ host: "docs", cookie: request.headers.cookie ?? "", method: request.method, path: url.pathname });
  if (url.pathname === "/") {
    response.writeHead(302, { Location: "/playground/", "Set-Cookie": "docs_secret=present; Path=/; HttpOnly; SameSite=Lax" }).end();
    return;
  }
  if (url.pathname === "/docs-sensitive") {
    response.writeHead(200, { "Content-Type": "application/json", "Set-Cookie": "docs_secret=present; Path=/; HttpOnly; SameSite=Lax" });
    response.end(JSON.stringify({ cookie: request.headers.cookie ?? "" }));
    return;
  }
  const filename = safeFile(path.join(dist, "docs"), url.pathname);
  serveFile(response, filename, {
    "Content-Security-Policy": `default-src 'self'; script-src 'self'; style-src 'self'; frame-src ${runnerOrigin}; connect-src 'self'`,
    "Set-Cookie": "docs_secret=present; Path=/; HttpOnly; SameSite=Lax",
  });
});

const runnerPolicy = [
  "default-src 'self'",
  "script-src 'self' blob: 'unsafe-eval' 'wasm-unsafe-eval'",
  "worker-src 'self'",
  "connect-src 'self'",
  `frame-ancestors ${docsOrigin}`,
].join("; ");
const previewPolicy = [
  "default-src 'none'",
  `script-src ${runnerOrigin} 'unsafe-inline'`,
  "style-src 'unsafe-inline'",
  "img-src data: blob:",
  "font-src data:",
  "connect-src 'none'",
  "media-src 'none'",
  "frame-src 'none'",
  "object-src 'none'",
  "base-uri 'none'",
  "form-action 'none'",
  `frame-ancestors ${docsOrigin}`,
].join("; ");
const runnerServer = http.createServer((request, response) => {
  const url = new URL(request.url, runnerOrigin);
  requestLog.push({ host: "runner", cookie: request.headers.cookie ?? "", method: request.method, path: url.pathname });
  const filename = safeFile(path.join(dist, "runner"), url.pathname);
  const previewAsset = /\/preview(?:\.|\.html)/.test(url.pathname);
  serveFile(response, filename, {
    ...(previewAsset ? { "Access-Control-Allow-Origin": "*" } : {}),
    "Content-Security-Policy": previewAsset ? previewPolicy : runnerPolicy,
    "Cross-Origin-Resource-Policy": previewAsset ? "cross-origin" : "same-site",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
  });
});

async function listen(server, port) {
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, "127.0.0.1", resolve);
  });
}

async function close(server) {
  await new Promise((resolve) => server.close(resolve));
}

async function waitForStatus(page, pattern, timeout = 35_000) {
  await page.waitForFunction(
    (expected) => (document.querySelector("#run-status")?.textContent ?? "").startsWith(expected),
    pattern,
    { timeout },
  );
}

async function previewText(page) {
  return page.frameLocator("#preview").locator("body").innerText();
}

async function waitForPreviewDiagnostic(page, text) {
  await page.waitForFunction(
    (expected) => !document.querySelector("#preview-diagnostic")?.hidden
      && (document.querySelector("#preview-diagnostic-details")?.textContent ?? "").includes(expected),
    text,
    { timeout: 10_000 },
  );
}

async function setSource(page, source) {
  await page.evaluate((value) => window.verticalProof.setSource(value, false), source);
}

function htmlSource(html) {
  return `html = ${JSON.stringify(html)}\nhtml`;
}

function exactTupleSource() {
  const citryVersion = JSON.stringify(buildManifest.runtimeLock.citry);
  const coreVersion = JSON.stringify(buildManifest.runtimeLock.citryCore);
  return `from importlib.metadata import version
from citry import Component

assert version("citry") == ${citryVersion}
assert version("citry-core") == ${coreVersion}

class TupleChild(Component):
    template = "<span>exact browser tuple</span>"

class TupleParent(Component):
    template = "<section><c-tuple-child #c-key=\\"'stable'\\" /></section>"

TupleParent()`;
}

async function runSource(page, source, expectedStatus = "Rendered") {
  const beforeRun = await page.evaluate(() => window.verticalProof.latestRunId());
  await setSource(page, source);
  await page.getByRole("button", { name: "Run", exact: true }).click();
  await page.waitForFunction(
    ({ beforeRun, expectedStatus }) => {
      const status = document.querySelector("#run-status")?.textContent ?? "";
      const expected = expectedStatus === "Rendered" ? "Rendered in" : expectedStatus;
      return window.verticalProof.latestRunId() > beforeRun && status.startsWith(expected);
    },
    { beforeRun, expectedStatus },
    { timeout: 35_000 },
  ).catch(async (error) => {
    const state = await page.evaluate(() => ({
      diagnostic: document.querySelector("#python-diagnostic-summary")?.textContent,
      diagnosticHidden: document.querySelector("#python-diagnostic")?.hidden,
      latestRunId: window.verticalProof.latestRunId(),
      status: document.querySelector("#run-status")?.textContent,
    }));
    throw new Error(`Run did not reach ${expectedStatus}: ${JSON.stringify(state)}`, { cause: error });
  });
}

async function openProof(browser, options = {}) {
  const context = await browser.newContext({ viewport: options.viewport ?? { width: 1280, height: 800 } });
  const page = await context.newPage();
  const failedRequests = [];
  const pageErrors = [];
  page.on("requestfailed", (request) => failedRequests.push({ url: request.url(), error: request.failure()?.errorText }));
  page.on("pageerror", (error) => pageErrors.push(error.message));
  const url = `${docsOrigin}${options.basePath ?? "/"}playground/?candidate=${options.candidate ?? "guided"}${options.fault ? `&fault=${options.fault}` : ""}`;
  await page.goto(url, { waitUntil: "load" });
  return { context, failedRequests, page, pageErrors, url };
}

async function testRuntime(browser, browserName) {
  const opened = await openProof(browser);
  const { context, failedRequests, page, pageErrors } = opened;
  const started = performance.now();
  let workerCloseRecovered = null;
  try {
    await waitForStatus(page, "Rendered");
    const coldMs = performance.now() - started;
    const initialPreview = await previewText(page);
    assert.match(
      initialPreview,
      /Welcome, Ada Lovelace/,
      `Host HTML: ${await page.evaluate(() => window.verticalProof.lastSuccessfulHtml())}; frame: ${await page.frameLocator("#preview").locator("html").innerHTML()}; debug: ${JSON.stringify(await page.evaluate(() => window.verticalProof.previewDebug))}`,
    );
    assert.equal(await page.getByRole("button", { name: "Run", exact: true }).isVisible(), true);
    assert.equal(await page.getByRole("checkbox", { name: "Auto-run" }).isChecked(), true);
    await page.getByRole("checkbox", { name: "Auto-run" }).uncheck();

    const warmStarted = performance.now();
    await runSource(page, htmlSource('<h1 id="warm">Warm render</h1>'));
    const warmMs = performance.now() - warmStarted;
    assert.match(await previewText(page), /Warm render/);

    await runSource(page, exactTupleSource());
    assert.match(await previewText(page), /exact browser tuple/);
    assert.equal(await page.frameLocator("#preview").locator("[data-citry-key]").count(), 1);

    await page.getByRole("checkbox", { name: "Auto-run" }).check();
    const beforeRapid = await page.evaluate(() => window.verticalProof.latestRunId());
    await setSource(page, htmlSource("<p>rapid one</p>"));
    await page.waitForTimeout(100);
    await setSource(page, htmlSource("<p>rapid two</p>"));
    await page.waitForTimeout(100);
    await setSource(page, htmlSource("<p>rapid final</p>"));
    await page.waitForFunction(
      (expectedRunId) => window.verticalProof.latestRunId() === expectedRunId
        && document.querySelector("#run-status")?.textContent.includes("Rendered"),
      beforeRapid + 1,
      { timeout: 35_000 },
    );
    assert.match(await previewText(page), /rapid final/);
    assert.equal(await page.evaluate(() => window.verticalProof.latestRunId()), beforeRapid + 1);
    await page.getByRole("checkbox", { name: "Auto-run" }).uncheck();

    await runSource(page, "def broken(:\n    pass", "Run failed");
    assert.equal(await page.locator("#python-diagnostic").isVisible(), true);
    assert.match(await page.locator("#python-diagnostic-summary").innerText(), /invalid syntax|expected/i);
    assert.equal(await page.locator("#stale-status").isVisible(), true);

    await runSource(page, "None", "Run failed");
    assert.match(await page.locator("#python-diagnostic-summary").innerText(), /returned None/);
    await runSource(page, "42", "Run failed");
    assert.match(await page.locator("#python-diagnostic-summary").innerText(), /Cannot preview int/);
    await runSource(page, "raise RuntimeError('x' * 20000)\n'<p>never</p>'", "Run failed");
    assert.match(
      `${await page.locator("#python-diagnostic-summary").innerText()}\n${await page.locator("#python-diagnostic-details").innerText()}`,
      /output truncated/,
    );

    await runSource(page, htmlSource('<script>throw new Error("preview sync")</script><p>Client test</p>'));
    const expectedSyncDiagnostic = browserName === "webkit" ? "Script error." : "preview sync";
    await waitForPreviewDiagnostic(page, expectedSyncDiagnostic).catch(async (error) => {
      const debug = await page.evaluate(() => ({
        events: window.verticalProof.previewDebug,
        hidden: document.querySelector("#preview-diagnostic")?.hidden,
        summary: document.querySelector("#preview-diagnostic-summary")?.textContent,
        details: document.querySelector("#preview-diagnostic-details")?.textContent,
      }));
      throw new Error(`Preview diagnostic was not delivered: ${JSON.stringify(debug)}`, { cause: error });
    });
    await runSource(page, htmlSource('<script>Promise.reject(new Error("preview rejection"))</script>'));
    await waitForPreviewDiagnostic(page, "preview rejection");
    await runSource(page, htmlSource('<script>console.error("citry caught client error")</script>'));
    await waitForPreviewDiagnostic(page, "citry caught client error");
    await runSource(page, htmlSource('<img src="https://example.invalid/missing.png">'));
    await page.locator("#preview-diagnostic").waitFor({ state: "visible" });

    const previewFetchesBefore = requestLog.filter((entry) => entry.path === "/docs-sensitive").length;
    const previewSecurityScript = `<script>(() => {
      const result = {};
      try { result.parentReadable = Boolean(parent.document); } catch { result.parentReadable = false; }
      try { localStorage.setItem("citry", "x"); result.storage = true; } catch { result.storage = false; }
      result.popup = false;
      result.fetch = false;
      try { fetch(${JSON.stringify(`${docsOrigin}/docs-sensitive`)}, { credentials: "include" }).then(() => { result.fetch = true; }).catch(() => {}); } catch {}
      for (let index = 0; index < 250; index += 1) parent.postMessage({ type: "malformed", index }, "*");
      document.body.dataset.security = JSON.stringify(result);
      console.error("security:" + JSON.stringify(result));
    })();</script>`;
    await runSource(page, htmlSource(previewSecurityScript));
    await page.frameLocator("#preview").locator("body[data-security]").waitFor({ state: "attached" }).catch(async (error) => {
      const state = await page.evaluate(() => ({
        summary: document.querySelector("#preview-diagnostic-summary")?.textContent,
        details: document.querySelector("#preview-diagnostic-details")?.textContent,
      }));
      throw new Error(`Preview security script did not finish: ${JSON.stringify(state)}`, { cause: error });
    });
    await page.waitForTimeout(250);
    const previewSecurity = JSON.parse(await page.frameLocator("#preview").locator("body").getAttribute("data-security"));
    assert.deepEqual(previewSecurity, { parentReadable: false, storage: false, popup: false, fetch: false });
    assert.equal(requestLog.filter((entry) => entry.path === "/docs-sensitive").length, previewFetchesBefore);

    await page.waitForTimeout(1_100);
    const pagesBeforeActions = context.pages().length;
    await runSource(page, htmlSource('<script>try { open("about:blank", "_blank"); } catch {} try { const link = document.createElement("a"); link.download = "citry.html"; link.href = "data:text/plain,citry"; link.click(); } catch {} console.error("popup-download-attempted")</script>'));
    await page.waitForTimeout(500);
    const previewActionPagesCreated = context.pages().length - pagesBeforeActions;
    assert.equal(previewActionPagesCreated, 0);

    await page.waitForTimeout(1_100);
    await runSource(page, htmlSource('<script>setTimeout(() => { location.href = "about:blank"; }, 500)</script><p>Navigation probe</p>'));
    await page.locator("#preview-diagnostic-summary").filter({ hasText: "navigated unexpectedly" }).waitFor({ timeout: 5_000 });
    await runSource(page, htmlSource("<p>Recovered preview</p>"));
    assert.match(await previewText(page), /Recovered preview/);

    await page.waitForTimeout(1_100);
    await runSource(page, "import builtins\nbuiltins.citry_stage6_probe = 'persisted'\n'<p>set state</p>'");
    await runSource(page, "import builtins\nf'<p id=\"state\">{getattr(builtins, \"citry_stage6_probe\", \"clean\")}</p>'");
    const builtinsPersisted = /persisted/.test(await previewText(page));
    await runSource(page, "from pathlib import Path\nPath('/tmp/citry-stage6').write_text('persisted')\n'<p>wrote file</p>'");
    await runSource(page, "from pathlib import Path\nf'<p>{Path(\"/tmp/citry-stage6\").read_text() if Path(\"/tmp/citry-stage6\").exists() else \"clean\"}</p>'");
    const filesystemPersisted = /persisted/.test(await previewText(page));
    await runSource(page, "import sys, types\nmodule = types.ModuleType('citry_stage6_module')\nmodule.value = 'persisted'\nsys.modules['citry_stage6_module'] = module\n'<p>set module</p>'");
    await runSource(page, "import sys\nf'<p>{getattr(sys.modules.get(\"citry_stage6_module\"), \"value\", \"clean\")}</p>'");
    const modulePersisted = /persisted/.test(await previewText(page));
    await runSource(page, "from js import globalThis\nglobalThis.citry_stage6_js_probe = 'persisted'\n'<p>set JavaScript state</p>'");
    await runSource(page, "from js import globalThis\nf'<p>{str(globalThis.citry_stage6_js_probe)}</p>'");
    const workerJavaScriptPersisted = /persisted/.test(await previewText(page));

    await page.waitForTimeout(1_100);
    const docsFetchesBefore = requestLog.filter((entry) => entry.path === "/docs-sensitive").length;
    await runSource(page, `from js import fetch\nfetch(${JSON.stringify(`${docsOrigin}/docs-sensitive`)})\n'<p>fetch attempted</p>'`);
    await page.waitForTimeout(250);
    const pythonDocsFetchReached = requestLog.filter((entry) => entry.path === "/docs-sensitive").length > docsFetchesBefore;
    assert.equal(pythonDocsFetchReached, false);
    await runSource(page, "from js import postMessage\nfor index in range(250):\n    postMessage(f'untrusted:{index}')\n'<p>flood survived</p>'");
    assert.match(await previewText(page), /flood survived/);
    await runSource(page, "payload = bytearray(16 * 1024 * 1024)\n'<p>large allocation survived</p>'");
    assert.match(await previewText(page), /large allocation survived/);

    if (browserName === "chromium") {
      await runSource(page, "payload = '<p>' + ('x' * (2 * 1024 * 1024)) + '</p>'\npayload", "Runner unavailable");
      assert.match(await page.locator("#python-diagnostic-summary").innerText(), /exceeded/);
      await runSource(page, htmlSource("<p>Recovered after oversized output</p>"));
      await runSource(page, "from js import close\nclose()\n'<p>Worker close requested</p>'");
      await setSource(page, htmlSource("<p>Probe closed Worker</p>"));
      await page.getByRole("button", { name: "Run", exact: true }).click();
      await waitForStatus(page, "Runner unavailable", 10_000);
      await runSource(page, htmlSource("<p>Recovered after Worker close</p>"));
      workerCloseRecovered = /Recovered after Worker close/.test(await previewText(page));
    }

    await setSource(page, "while True:\n    pass\n'<p>never</p>'");
    await page.getByRole("button", { name: "Run", exact: true }).click();
    await page.getByRole("button", { name: "Stop" }).waitFor();
    await page.getByRole("button", { name: "Stop" }).click();
    await waitForStatus(page, "Stopped");
    assert.equal(await page.evaluate(() => window.verticalProof.isAutoRunPaused()), true);
    await runSource(page, htmlSource("<p>Recovered after stop</p>"));
    assert.match(await previewText(page), /Recovered after stop/);
    assert.equal(await page.evaluate(() => window.verticalProof.isAutoRunPaused()), false);

    await setSource(page, "while True:\n    pass\n'<p>never</p>'");
    await page.getByRole("button", { name: "Run", exact: true }).click();
    await waitForStatus(page, "Runner unavailable", 10_000);
    assert.match(await page.locator("#python-diagnostic-summary").innerText(), /5-second limit/);
    await runSource(page, htmlSource("<p>Recovered after timeout</p>"), "Rendered");

    await page.getByRole("separator").focus();
    await page.keyboard.press("Home");
    assert.equal(await page.getByRole("separator").getAttribute("aria-valuenow"), "25");
    await page.keyboard.press("End");
    assert.equal(await page.getByRole("separator").getAttribute("aria-valuenow"), "75");
    await page.keyboard.press("Enter");
    assert.equal(await page.getByRole("separator").getAttribute("aria-valuenow"), "50");
    await page.evaluate(() => window.verticalProof.setDivider(63));
    await page.reload({ waitUntil: "load" });
    assert.equal(await page.getByRole("separator").getAttribute("aria-valuenow"), "63");
    assert.match(await page.evaluate(() => window.verticalProof.getSource()), /class WelcomeCard/);
    await waitForStatus(page, "Rendered");

    assert.deepEqual(
      pageErrors.filter((message) => !message.includes("preview sync") && !message.includes("preview rejection")),
      [],
    );
    assert.deepEqual(failedRequests.filter(({ url }) => !url.includes("example.invalid")), []);
    return {
      browser: browserName,
      browserVersion: browser.version(),
      builtinsPersisted,
      coldMs,
      failedRequests,
      filesystemPersisted,
      modulePersisted,
      pageErrors,
      previewActionPagesCreated,
      previewSecurity,
      pythonDocsFetchReached,
      warmMs,
      exactTupleVerified: true,
      workerCloseRecovered,
      workerJavaScriptPersisted,
    };
  } finally {
    await context.close();
  }
}

async function testLayoutAndModes(browser) {
  const results = {};
  {
    const { context, page } = await openProof(browser, { candidate: "on-demand", viewport: { width: 375, height: 760 } });
    try {
      assert.equal(await page.getByRole("checkbox", { name: "Auto-run" }).isChecked(), false);
      assert.equal(await page.locator("#run-status").innerText(), "Ready to run");
      assert.equal(await page.getByRole("tab", { name: "Code" }).getAttribute("aria-selected"), "true");
      await page.getByRole("tab", { name: "Result" }).click();
      assert.equal(await page.locator("#result-panel").isVisible(), true);
      assert.equal(await page.locator("#code-panel").isHidden(), true);
      await page.getByRole("tab", { name: "Result" }).press("ArrowLeft");
      assert.equal(await page.locator("#code-panel").isVisible(), true);
      await page.getByRole("checkbox", { name: "Auto-run" }).check();
      await page.reload({ waitUntil: "load" });
      assert.equal(await page.getByRole("checkbox", { name: "Auto-run" }).isChecked(), true);
      results.phone = true;
    } finally { await context.close(); }
  }
  {
    const { context, page } = await openProof(browser, { candidate: "on-demand", basePath: "/citry-docs/", viewport: { width: 900, height: 700 } });
    try {
      assert.match(await page.locator("script[type=module]").getAttribute("src"), /^\/citry-docs\/assets\//);
      assert.equal(await page.getByRole("separator").isVisible(), true);
      const dividerBox = await page.getByRole("separator").boundingBox();
      await page.mouse.move(dividerBox.x + dividerBox.width / 2, dividerBox.y + dividerBox.height / 2);
      await page.mouse.down();
      await page.mouse.move(dividerBox.x + 80, dividerBox.y + dividerBox.height / 2);
      await page.mouse.up();
      assert.notEqual(await page.getByRole("separator").getAttribute("aria-valuenow"), "50");
      await page.evaluate(() => window.verticalProof.setDivider(50));
      await page.evaluate(() => { document.documentElement.dir = "rtl"; });
      await page.getByRole("separator").focus();
      await page.keyboard.press("ArrowLeft");
      assert.equal(await page.getByRole("separator").getAttribute("aria-valuenow"), "52");
      results.nestedBaseAndRtl = true;
    } finally { await context.close(); }
  }
  {
    const { context, page } = await openProof(browser, { candidate: "on-demand" });
    try {
      await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
      assert.equal(await page.evaluate(() => matchMedia("(prefers-color-scheme: dark)").matches), true);
      assert.equal(await page.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches), true);
      assert.equal(await page.getByRole("main").count(), 1);
      assert.equal(await page.getByRole("heading", { level: 1 }).count(), 1);
      assert.equal(await page.getByTitle("Rendered Citry result").count(), 1);
      assert.equal(await page.getByRole("button", { name: "Run", exact: true }).count(), 1);
      assert.equal(await page.locator(".site-header nav a").count(), 5);
      await page.emulateMedia({ forcedColors: "active" });
      assert.equal(await page.evaluate(() => matchMedia("(forced-colors: active)").matches), true);
      results.themeAndNames = true;
    } finally { await context.close(); }
  }
  return results;
}

async function testSlowLoad(browser) {
  const { context, page } = await openProof(browser, { candidate: "on-demand", fault: "slow-load" });
  const started = performance.now();
  try {
    await page.getByRole("button", { name: "Run", exact: true }).click();
    await waitForStatus(page, "Rendered", 35_000);
    return performance.now() - started;
  } finally { await context.close(); }
}

async function testOfflineRecovery(browser) {
  const { context, page } = await openProof(browser, { candidate: "on-demand" });
  try {
    await context.setOffline(true);
    await page.getByRole("button", { name: "Run", exact: true }).click();
    await page.locator("#python-diagnostic-summary").filter({ hasText: "handshake timed out" }).waitFor({ timeout: 12_000 });
    const message = await page.locator("#python-diagnostic-summary").innerText();
    await context.setOffline(false);
    await page.waitForTimeout(500);
    await page.getByRole("button", { name: "Run", exact: true }).click();
    await waitForStatus(page, "Rendered", 35_000);
    return { message, recovered: true };
  } finally {
    await context.setOffline(false);
    await context.close();
  }
}

async function testFault(browser, fault, expected) {
  const { context, page } = await openProof(browser, { candidate: "on-demand", fault });
  try {
    await page.getByRole("button", { name: "Run", exact: true }).click();
    await page.locator("#python-diagnostic").waitFor({ state: "visible", timeout: 35_000 });
    const summary = await page.locator("#python-diagnostic-summary").innerText();
    assert.match(summary, expected);
    return summary;
  } finally { await context.close(); }
}

await listen(docsServer, 43173);
await listen(runnerServer, 43174);
const results = {
  generatedOn: new Date().toISOString(),
  build: {
    bundleId: buildManifest.bundleId,
    packageTrack: buildManifest.runtimeLock.packageTrack,
    citry: buildManifest.runtimeLock.citry,
    citryCore: buildManifest.runtimeLock.citryCore,
    fileCount: buildManifest.files.length,
    hostBytes: buildManifest.files.find(({ file }) => /docs\/assets\/playground\..*\.mjs$/.test(file))?.bytes,
    cssBytes: buildManifest.files.find(({ file }) => /docs\/assets\/playground\..*\.css$/.test(file))?.bytes,
    runtimeBytes: buildManifest.runtimeLock.artifacts.reduce((total, artifact) => total + artifact.bytes, 0),
  },
  faults: {},
  layouts: {},
  loading: {},
  runtime: [],
};

try {
  for (const browserName of browserNames) {
    const browserType = browserTypes[browserName];
    if (!browserType) throw new Error(`Unknown browser ${browserName}`);
    const browser = await browserType.launch({ headless: true });
    try {
      results.runtime.push(await testRuntime(browser, browserName));
      if (browserName === "chromium") {
        results.layouts = await testLayoutAndModes(browser);
        results.faults.missingWheel = await testFault(browser, "missing-wheel", /HTTP 404/);
        results.faults.hashMismatch = await testFault(browser, "hash-mismatch", /SHA-256/);
        results.faults.importFailure = await testFault(browser, "import-failure", /does_not_exist|No module named/);
        results.faults.noWasm = await testFault(browser, "no-wasm", /WebAssembly/);
        results.loading.slowLoadMs = await testSlowLoad(browser);
        results.loading.offline = await testOfflineRecovery(browser);
      }
    } finally { await browser.close(); }
  }
  results.security = {
    docsCookieReachedRunner: requestLog.some((entry) => entry.host === "runner" && entry.cookie.includes("docs_secret")),
    runnerRequests: requestLog.filter((entry) => entry.host === "runner").length,
  };
  assert.equal(results.security.docsCookieReachedRunner, false);
  fs.mkdirSync(path.join(root, "results"), { recursive: true });
  fs.writeFileSync(path.join(root, "results", "browser-results.json"), `${JSON.stringify(results, null, 2)}\n`);
  console.log(JSON.stringify(results, null, 2));
} finally {
  await close(docsServer);
  await close(runnerServer);
}
