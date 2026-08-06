import assert from "node:assert/strict";
import { createReadStream, existsSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const proofRoot = fileURLToPath(new URL("..", import.meta.url));
const mimeTypes = new Map([
  [".css", "text/css; charset=utf-8"],
  [".html", "text/html; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
]);

function startServer() {
  const server = createServer((request, response) => {
    const requestPath = new URL(request.url, "http://127.0.0.1").pathname;
    const relativePath = requestPath === "/" ? "layout/index.html" : requestPath.slice(1);
    const candidate = normalize(join(proofRoot, relativePath));
    if (!candidate.startsWith(proofRoot) || !existsSync(candidate)) {
      response.writeHead(404).end("Not found");
      return;
    }
    response.setHeader("Content-Type", mimeTypes.get(extname(candidate)) ?? "application/octet-stream");
    response.setHeader("Cache-Control", "no-store");
    createReadStream(candidate).pipe(response);
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      resolve({ server, origin: `http://127.0.0.1:${address.port}` });
    });
  });
}

async function assertNoDocumentOverflow(page) {
  const metrics = await page.evaluate(() => ({
    clientHeight: document.documentElement.clientHeight,
    clientWidth: document.documentElement.clientWidth,
    scrollHeight: document.documentElement.scrollHeight,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  assert.ok(metrics.scrollWidth <= metrics.clientWidth, JSON.stringify(metrics));
  assert.ok(metrics.scrollHeight <= metrics.clientHeight, JSON.stringify(metrics));
}

async function assertDiagnosticsDoNotCoverToolbar(page, panelId) {
  const boxes = await page.evaluate((id) => {
    const panel = document.querySelector(id);
    const toolbar = panel.querySelector(".panel-toolbar").getBoundingClientRect();
    const diagnostic = panel.querySelector(".diagnostic").getBoundingClientRect();
    return {
      diagnosticTop: diagnostic.top,
      toolbarBottom: toolbar.bottom,
      diagnosticHeight: diagnostic.height,
    };
  }, panelId);
  assert.ok(boxes.diagnosticHeight > 0, JSON.stringify(boxes));
  assert.ok(boxes.diagnosticTop >= boxes.toolbarBottom, JSON.stringify(boxes));
}

const { server, origin } = await startServer();
const browser = await chromium.launch({ headless: true });

try {
  const desktop = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await desktop.goto(`${origin}/layout/index.html`);

  assert.equal(await desktop.locator("main").count(), 1);
  assert.equal(await desktop.locator("main").getAttribute("aria-labelledby"), "playground-title");
  assert.equal(await desktop.locator("h1").count(), 1);
  assert.equal(await desktop.locator("iframe").getAttribute("title"), "Citry result preview");
  assert.equal(await desktop.locator("#workspace-separator").getAttribute("role"), "separator");
  assert.equal(await desktop.locator("#workspace-separator").getAttribute("aria-orientation"), "vertical");
  assert.ok(await desktop.locator("#workspace-separator").isVisible());
  assert.ok(await desktop.locator("#code-panel").isVisible());
  assert.ok(await desktop.locator("#result-panel").isVisible());
  await assertNoDocumentOverflow(desktop);
  await assertDiagnosticsDoNotCoverToolbar(desktop, "#code-panel");
  await assertDiagnosticsDoNotCoverToolbar(desktop, "#result-panel");

  const separator = desktop.locator("#workspace-separator");
  await separator.focus();
  await desktop.keyboard.press("ArrowRight");
  assert.equal(await separator.getAttribute("aria-valuenow"), "51");
  await desktop.keyboard.press("Shift+ArrowRight");
  assert.equal(await separator.getAttribute("aria-valuenow"), "61");
  await desktop.keyboard.press("Home");
  assert.equal(await separator.getAttribute("aria-valuenow"), "30");
  await desktop.keyboard.press("End");
  assert.equal(await separator.getAttribute("aria-valuenow"), "70");
  await desktop.keyboard.press("Enter");
  assert.equal(await separator.getAttribute("aria-valuenow"), "50");

  const separatorBox = await separator.boundingBox();
  await desktop.mouse.move(separatorBox.x + separatorBox.width / 2, separatorBox.y + 80);
  await desktop.mouse.down();
  await desktop.mouse.move(separatorBox.x + separatorBox.width / 2 + 120, separatorBox.y + 80);
  await desktop.mouse.up();
  assert.ok(Number(await separator.getAttribute("aria-valuenow")) > 50);

  const persisted = await separator.getAttribute("aria-valuenow");
  await desktop.reload();
  assert.equal(await desktop.locator("#workspace-separator").getAttribute("aria-valuenow"), persisted);
  await desktop.evaluate(() => localStorage.setItem("citry-playground-proof:split", "999"));
  await desktop.reload();
  assert.equal(await desktop.locator("#workspace-separator").getAttribute("aria-valuenow"), "70");
  await desktop.evaluate(() => localStorage.setItem("citry-playground-proof:split", "invalid"));
  await desktop.reload();
  assert.equal(await desktop.locator("#workspace-separator").getAttribute("aria-valuenow"), "50");

  await desktop.setViewportSize({ width: 1280, height: 460 });
  await desktop.waitForFunction(() => document.documentElement.style.getPropertyValue("--app-height") === "460px");
  await assertNoDocumentOverflow(desktop);

  const rtl = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await rtl.goto(`${origin}/layout/index.html?dir=rtl`);
  const rtlSeparator = rtl.locator("#workspace-separator");
  await rtlSeparator.focus();
  await rtl.keyboard.press("ArrowRight");
  assert.equal(await rtlSeparator.getAttribute("aria-valuenow"), "49");
  await rtl.keyboard.press("ArrowLeft");
  assert.equal(await rtlSeparator.getAttribute("aria-valuenow"), "50");

  const touchContext = await browser.newContext({
    hasTouch: true,
    isMobile: true,
    viewport: { width: 1000, height: 700 },
  });
  const touch = await touchContext.newPage();
  await touch.goto(`${origin}/layout/index.html`);
  const touchSeparator = touch.locator("#workspace-separator");
  const touchBox = await touchSeparator.boundingBox();
  assert.ok(touchBox.width >= 24, JSON.stringify(touchBox));
  const cdp = await touchContext.newCDPSession(touch);
  const startX = touchBox.x + touchBox.width / 2;
  const touchY = touchBox.y + 90;
  await cdp.send("Input.dispatchTouchEvent", {
    type: "touchStart",
    touchPoints: [{ x: startX, y: touchY }],
  });
  await cdp.send("Input.dispatchTouchEvent", {
    type: "touchMove",
    touchPoints: [{ x: startX + 90, y: touchY }],
  });
  await cdp.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
  assert.ok(Number(await touchSeparator.getAttribute("aria-valuenow")) > 50);
  await touchContext.close();

  const mobile = await browser.newPage({ viewport: { width: 320, height: 568 } });
  await mobile.goto(`${origin}/layout/index.html`);
  assert.ok(await mobile.locator(".mobile-pane-switch").isVisible());
  assert.ok(await mobile.locator("#code-panel").isVisible());
  assert.equal(await mobile.locator("#result-panel").isVisible(), false);
  assert.equal(await mobile.locator("#workspace-separator").isVisible(), false);
  assert.equal(await mobile.locator("#show-code").getAttribute("aria-pressed"), "true");
  await assertNoDocumentOverflow(mobile);
  await assertDiagnosticsDoNotCoverToolbar(mobile, "#code-panel");

  const textarea = mobile.locator("#source-editor");
  await textarea.evaluate((element) => {
    element.focus();
    element.setSelectionRange(24, 40);
    element.scrollTop = 120;
  });
  const beforeSwitch = await textarea.evaluate((element) => ({
    end: element.selectionEnd,
    scrollTop: element.scrollTop,
    start: element.selectionStart,
    value: element.value,
  }));
  await mobile.locator("#show-result").click();
  assert.equal(await mobile.locator("#code-panel").isVisible(), false);
  assert.ok(await mobile.locator("#result-panel").isVisible());
  assert.equal(await mobile.locator("#show-result").getAttribute("aria-pressed"), "true");
  await mobile.locator("#result-frame").focus();
  assert.equal(await mobile.evaluate(() => document.activeElement?.id), "result-frame");
  await mobile.locator("#show-code").click();
  const afterSwitch = await textarea.evaluate((element) => ({
    end: element.selectionEnd,
    scrollTop: element.scrollTop,
    start: element.selectionStart,
    value: element.value,
  }));
  assert.deepEqual(afterSwitch, beforeSwitch);

  const pageScrollBefore = await mobile.evaluate(() => window.scrollY);
  await textarea.evaluate((element) => {
    element.scrollTop = element.scrollHeight;
  });
  assert.equal(await mobile.evaluate(() => window.scrollY), pageScrollBefore);

  const menuButton = mobile.locator(".mobile-menu-button");
  assert.ok(await menuButton.isVisible());
  assert.equal(await mobile.locator("#primary-navigation").isVisible(), false);
  await menuButton.click();
  assert.ok(await mobile.locator("#primary-navigation").isVisible());
  assert.equal(await menuButton.getAttribute("aria-expanded"), "true");

  // A 1280 CSS pixel desktop at 400% browser zoom reflows into 320 CSS pixels.
  // Headless Chromium cannot drive browser chrome zoom, so this exact CSS
  // viewport is the automated WCAG reflow proxy. Stage 6 still needs a manual
  // browser-zoom and assistive-technology pass.
  assert.equal(await mobile.evaluate(() => window.innerWidth), 320);
  assert.ok(await mobile.locator(".mobile-pane-switch").isVisible());

  console.log(
    JSON.stringify(
      {
        chromium: browser.version(),
        desktop: "passed",
        dynamicViewport: "passed",
        keyboardSeparator: "passed",
        mobile320: "passed",
        pointerSeparator: "passed",
        rtl: "passed",
        touchSeparator: "passed",
        zoom400ReflowProxy: "passed",
      },
      null,
      2,
    ),
  );
} finally {
  await browser.close();
  await new Promise((resolve, reject) => server.close((error) => (error ? reject(error) : resolve())));
}
