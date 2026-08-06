import assert from "node:assert/strict";
import { createReadStream, existsSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const proofRoot = fileURLToPath(new URL("..", import.meta.url));
const prefix = "/nested/editor-proof/";
const mimeTypes = new Map([
  [".css", "text/css; charset=utf-8"],
  [".html", "text/html; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
]);
const requestedWorkers = [];

function startServer() {
  const server = createServer((request, response) => {
    const requestPath = new URL(request.url, "http://127.0.0.1").pathname;
    if (!requestPath.startsWith(prefix)) {
      response.writeHead(404).end("Not found");
      return;
    }
    const relativePath = requestPath.slice(prefix.length);
    const candidate = normalize(join(proofRoot, relativePath));
    if (!candidate.startsWith(proofRoot) || !existsSync(candidate)) {
      response.writeHead(404).end("Not found");
      return;
    }
    if (/worker/i.test(relativePath)) requestedWorkers.push(relativePath);
    response.setHeader("Content-Type", mimeTypes.get(extname(candidate)) ?? "application/octet-stream");
    response.setHeader("Cache-Control", "no-store");
    response.setHeader(
      "Content-Security-Policy",
      "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; worker-src 'self'; img-src 'self' data:; font-src 'self' data:",
    );
    createReadStream(candidate).pipe(response);
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      resolve({ server, origin: `http://127.0.0.1:${address.port}` });
    });
  });
}

async function loadProof(browser, origin, name) {
  const page = await browser.newPage({ viewport: { width: 1000, height: 720 } });
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.stack ?? error.message));
  const response = await page.goto(`${origin}${prefix}${name}/index.html`);
  assert.equal(response.status(), 200);
  await page.waitForFunction(() => window.editorProof?.ready === true);
  await page.waitForTimeout(300);
  assert.deepEqual(errors, [], `${name}: ${errors.join("\n")}`);
  return page;
}

const { server, origin } = await startServer();
const browser = await chromium.launch({ headless: true });

try {
  const codeMirror = await loadProof(browser, origin, "codemirror");
  assert.equal(await codeMirror.locator("main").getAttribute("aria-labelledby"), "proof-title");
  assert.equal(await codeMirror.locator("h1").count(), 1);
  assert.equal(await codeMirror.locator(".cm-content").getAttribute("role"), "textbox");
  assert.equal(await codeMirror.locator(".cm-content").getAttribute("aria-label"), "Citry Python module");
  assert.match(await codeMirror.evaluate(() => window.editorProof.syntaxAt("class CounterCard")), /class|Class|Definition/);
  assert.match(await codeMirror.evaluate(() => window.editorProof.syntaxAt("const label")), /const|Declaration|Variable/);
  assert.match(await codeMirror.evaluate(() => window.editorProof.syntaxAt("display: grid")), /Declaration|Property|Value|Block/);
  assert.ok((await codeMirror.evaluate(() => window.editorProof.citryDecorationCount())) >= 4);
  await codeMirror.evaluate(() => window.editorProof.setValue("class C:\n    js = '''const x = 1;'''\n"));
  assert.match(await codeMirror.evaluate(() => window.editorProof.syntaxAt("const x")), /const|Declaration/);
  await codeMirror.locator("#restore-button").click();
  await codeMirror.evaluate(() => window.editorProof.append("\n# undo probe"));
  assert.match(await codeMirror.evaluate(() => window.editorProof.getValue()), /undo probe/);
  await codeMirror.evaluate(() => window.editorProof.undo());
  assert.doesNotMatch(await codeMirror.evaluate(() => window.editorProof.getValue()), /undo probe/);
  await codeMirror.locator("#search-button").click();
  assert.ok(await codeMirror.locator(".cm-search").isVisible());
  await codeMirror.locator("#diagnostic-button").click();
  assert.ok(await codeMirror.locator("#editor-diagnostic").isVisible());
  await codeMirror.waitForSelector(".cm-lintRange-error");
  assert.equal(await codeMirror.evaluate(() => window.editorProof.workerResources()), 0);

  const monaco = await loadProof(browser, origin, "monaco");
  assert.equal(await monaco.locator("main").getAttribute("aria-labelledby"), "proof-title");
  assert.equal(await monaco.locator("h1").count(), 1);
  assert.equal(
    await monaco.locator(".monaco-editor [role='textbox']").first().getAttribute("aria-label"),
    "Citry Python module",
  );
  const jsToken = await monaco.evaluate(() => window.editorProof.tokenAt("const label"));
  const cssToken = await monaco.evaluate(() => window.editorProof.tokenAt("display: grid"));
  const interpolationToken = await monaco.evaluate(() => window.editorProof.tokenAt("self.title"));
  const pythonToken = await monaco.evaluate(() => window.editorProof.tokenAt("class CounterCard"));
  assert.match(`${pythonToken?.language} ${pythonToken?.type}`, /python.*keyword/);
  assert.match(`${jsToken?.language} ${jsToken?.type}`, /javascript|keyword|identifier/);
  assert.match(`${cssToken?.language} ${cssToken?.type}`, /css|attribute|tag|identifier/);
  assert.match(`${interpolationToken?.language} ${interpolationToken?.type}`, /python/);
  await monaco.evaluate(() => window.editorProof.setValue("class C:\n    js = '''const x = 1;'''\n"));
  assert.match(
    `${(await monaco.evaluate(() => window.editorProof.tokenAt("const x")))?.language}`,
    /javascript/,
  );
  await monaco.locator("#restore-button").click();
  await monaco.evaluate(() => window.editorProof.append("\n# undo probe"));
  assert.match(await monaco.evaluate(() => window.editorProof.getValue()), /undo probe/);
  await monaco.evaluate(() => window.editorProof.undo());
  assert.doesNotMatch(await monaco.evaluate(() => window.editorProof.getValue()), /undo probe/);
  await monaco.locator("#search-button").click();
  assert.ok(await monaco.locator(".find-widget").isVisible());
  await monaco.locator("#diagnostic-button").click();
  assert.ok(await monaco.locator("#editor-diagnostic").isVisible());
  assert.equal(await monaco.evaluate(() => window.editorProof.markers().length), 1);
  assert.equal(await monaco.evaluate(() => window.editorProof.workerExecuted()), true);
  assert.ok((await monaco.evaluate(() => window.editorProof.workerRequests())) >= 1);
  assert.ok(requestedWorkers.includes("dist/monaco-editor-worker.js"));

  console.log(
    JSON.stringify(
      {
        basePath: prefix,
        csp: "self scripts and workers; inline styles allowed",
        codemirror: {
          accessibility: "passed",
          diagnostics: "passed",
          mixedParsing: "passed",
          searchUndo: "passed",
          workers: 0,
        },
        monaco: {
          accessibility: "passed",
          diagnostics: "passed",
          mixedTokenization: "passed",
          searchUndo: "passed",
          workerRequests: requestedWorkers.length,
        },
      },
      null,
      2,
    ),
  );
} finally {
  await browser.close();
  await new Promise((resolve, reject) => server.close((error) => (error ? reject(error) : resolve())));
}
