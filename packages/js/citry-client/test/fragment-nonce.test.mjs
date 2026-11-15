import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

// The shipped, minified runtime is what a page loads, so the fragment nonce rule is checked
// through it and not through the readable source.
const source = readFileSync(new URL("../../../py/citry/citry/_vue/runtime.js", import.meta.url), "utf8");

const PAGE_NONCE = "page-nonce";
const FRAGMENT_SELECTOR = 'script[type="application/json"][data-citry-vue-fragment]';

// A well-formed descriptor whose host is missing from the page: a block the nonce check lets
// through stops at the host lookup, which tells the two outcomes apart without mounting Vue.
const MANIFEST = JSON.stringify({
  vue: {
    protocol: "citry-vue-fragment/1",
    appId: "app",
    host: "#missing-host",
    prepared: { host: "#missing-host", manifest: { appId: "app" } },
  },
});

// Loads the runtime into a stub page and returns what the fragment manager logged for one
// fragment data block that is already in the page when the runtime starts.
async function startWith({
  blockNonce,
  clobberCurrentScript,
  blockAttributes = {},
  manifest = MANIFEST,
  cancelStale = false,
  blockConnected = false,
}) {
  const events = [];
  const record = (target, event) => {
    events.push({
      type: event.type,
      target,
      reason: event.detail?.reason ?? null,
      code: event.detail?.error?.code ?? null,
    });
    return !(cancelStale && event.cancelable);
  };
  class Document {
    get currentScript() {
      return runtimeScript;
    }
  }
  class HTMLScriptElement {
    constructor(nonce) {
      this.nonce = nonce;
      this.dataset = {};
      this.textContent = "";
      this.attributes = {};
    }
    getAttributeNames() {
      return Object.keys(this.attributes);
    }
    getAttribute(name) {
      return this.attributes[name] ?? null;
    }
  }
  // The runtime's own tag carries the page nonce, as a server-rendered page writes it.
  const runtimeScript = new HTMLScriptElement(PAGE_NONCE);
  const block = new HTMLScriptElement(blockNonce);
  block.textContent = manifest;
  // A block still in the page is where the fragment's event starts.
  if (blockConnected) {
    block.isConnected = true;
    block.dispatchEvent = (event) => record("block", event);
  }
  block.attributes = { type: "application/json", "data-citry-vue-fragment": "", ...blockAttributes };
  const document = new Document();
  Object.assign(document, {
    readyState: "complete",
    documentElement: {},
    body: { contains: () => false },
    createElement: () => ({}),
    querySelector: () => null,
    querySelectorAll: (selector) => (selector === FRAGMENT_SELECTOR ? [block] : []),
    addEventListener() {},
    removeEventListener() {},
    // Records what the page hears; a listener that cancels `citry:fragments:stale` returns false.
    dispatchEvent: (event) => record("document", event),
  });
  // A named element such as <form name="currentScript"> becomes an own property of the
  // document that hides the Document.prototype getter, and it has an empty nonce.
  if (clobberCurrentScript)
    Object.defineProperty(document, "currentScript", { value: { nonce: "", getAttribute: () => null } });
  const errors = [];
  const prompts = [];
  const warnings = [];
  const context = {
    Document,
    HTMLScriptElement,
    document,
    history: { state: null, pushState() {}, replaceState() {} },
    console: {
      error: (...args) => errors.push(args.map(String).join(" ")),
      warn: (...args) => warnings.push(args.map(String).join(" ")),
      log() {},
    },
    CustomEvent: class CustomEvent {
      constructor(type, init) {
        Object.assign(this, init, { type });
      }
    },
    MutationObserver: class {
      observe() {}
      disconnect() {}
      takeRecords() {
        return [];
      }
    },
    queueMicrotask,
    setTimeout,
    clearTimeout,
    structuredClone,
    btoa,
    // The visitor declines, so the test sees the question without a reload.
    confirm: (message) => {
      prompts.push(message);
      return false;
    },
    location: { assign() {}, reload() {} },
  };
  context.globalThis = context;
  context.window = context;
  context.self = context;
  vm.runInNewContext(source, context);
  // The manager reports a refused block from a rejected promise, one turn later.
  await new Promise((resolve) => setTimeout(resolve, 0));
  return { errors, prompts, warnings, events };
}

const NONCE_REFUSAL = /does not carry the page's CSP nonce/;
const HOST_REFUSAL = /host must resolve once/;

test("a fragment block without the page nonce is refused", async () => {
  const { errors } = await startWith({ blockNonce: "", clobberCurrentScript: false });
  assert.equal(errors.length, 1, errors.join("\n"));
  assert.match(errors[0], NONCE_REFUSAL);
});

test("a fragment block with a different nonce is refused", async () => {
  const { errors } = await startWith({ blockNonce: "other-nonce", clobberCurrentScript: false });
  assert.equal(errors.length, 1, errors.join("\n"));
  assert.match(errors[0], NONCE_REFUSAL);
});

test("a fragment block with the page nonce passes the nonce check", async () => {
  const { errors } = await startWith({ blockNonce: PAGE_NONCE, clobberCurrentScript: false });
  assert.equal(errors.length, 1, errors.join("\n"));
  assert.match(errors[0], HOST_REFUSAL);
});

test("a named element that hides document.currentScript does not switch the nonce check off", async () => {
  const { errors } = await startWith({ blockNonce: "", clobberCurrentScript: true });
  assert.equal(errors.length, 1, errors.join("\n"));
  assert.match(errors[0], NONCE_REFUSAL);
});

test("a fragment block that took in the next tag's attributes is refused, nonce included", async () => {
  // An injected tag left open takes the genuine tag after it as attributes, here
  // `<script type=application/json data-citry-vue-fragment a=` before `<script nonce=...>`.
  const { errors } = await startWith({
    blockNonce: PAGE_NONCE,
    clobberCurrentScript: false,
    blockAttributes: { a: "<script", nonce: "" },
  });
  assert.equal(errors.length, 1, errors.join("\n"));
  assert.match(errors[0], NONCE_REFUSAL);
});

// A server on another Citry release can write a fragment this runtime does not know: another
// protocol string, or a top-level field beside `vue`. The page tells the app with
// `citry:fragments:stale`, and Citry itself only writes a console warning.
const FRAGMENT_STALE = { type: "citry:fragments:stale", target: "document", reason: "version", code: "stale_state" };
const QUESTION = "This page is out of date. Reload to continue?";
const otherProtocol = (development = false) => ({
  vue: {
    ...JSON.parse(MANIFEST).vue,
    protocol: "citry-vue-fragment/2",
    prepared: { ...JSON.parse(MANIFEST).vue.prepared, ...(development ? { development: true } : {}) },
  },
});

for (const [name, manifest] of [
  ["another protocol", otherProtocol()],
  ["an unknown top-level field", { ...JSON.parse(MANIFEST), styles: [] }],
]) {
  test(`a fragment with ${name} notifies the app and warns once, without asking`, async () => {
    const { errors, prompts, warnings, events } = await startWith({
      blockNonce: PAGE_NONCE,
      clobberCurrentScript: false,
      manifest: JSON.stringify(manifest),
    });
    assert.deepEqual(
      events.filter((event) => event.type === FRAGMENT_STALE.type),
      [FRAGMENT_STALE],
    );
    assert.deepEqual(prompts, []);
    assert.equal(warnings.length, 1, warnings.join("\n"));
    assert.match(warnings[0], /citry:fragments:stale/);
    assert.equal(errors.length, 1, errors.join("\n"));
    assert.match(errors[0], /different Citry release/);
  });
}

test("a fragment from a development server asks the built-in question", async () => {
  const { prompts, warnings } = await startWith({
    blockNonce: PAGE_NONCE,
    clobberCurrentScript: false,
    manifest: JSON.stringify(otherProtocol(true)),
  });
  assert.deepEqual(prompts, [QUESTION]);
  assert.deepEqual(warnings, []);
});

test("cancelling citry:fragments:stale replaces Citry's own report", async () => {
  const { prompts, warnings, events } = await startWith({
    blockNonce: PAGE_NONCE,
    clobberCurrentScript: false,
    manifest: JSON.stringify(otherProtocol(true)),
    cancelStale: true,
  });
  assert.equal(events.filter((event) => event.type === FRAGMENT_STALE.type).length, 1);
  assert.deepEqual(prompts, []);
  assert.deepEqual(warnings, []);
});

test("the fragment event starts at its data block while the block is in the page", async () => {
  const { events } = await startWith({
    blockNonce: PAGE_NONCE,
    clobberCurrentScript: false,
    manifest: JSON.stringify(otherProtocol()),
    blockConnected: true,
  });
  assert.deepEqual(
    events.filter((event) => event.type === FRAGMENT_STALE.type),
    [{ ...FRAGMENT_STALE, target: "block" }],
  );
});

test("cancelling citry:fragments:stale on a production page also skips the console warning", async () => {
  const { prompts, warnings } = await startWith({
    blockNonce: PAGE_NONCE,
    clobberCurrentScript: false,
    manifest: JSON.stringify(otherProtocol()),
    cancelStale: true,
  });
  assert.deepEqual(prompts, []);
  assert.deepEqual(warnings, []);
});

test("a fragment refused for its nonce reports nothing, whatever it carries", async () => {
  // Injected markup has no nonce under a nonce-based CSP, so it cannot raise the report.
  const { errors, prompts, warnings, events } = await startWith({
    blockNonce: "",
    clobberCurrentScript: false,
    manifest: JSON.stringify(otherProtocol(true)),
  });
  assert.deepEqual(prompts, []);
  assert.deepEqual(warnings, []);
  assert.deepEqual(
    events.filter((event) => event.type === FRAGMENT_STALE.type),
    [],
  );
  assert.match(errors[0], NONCE_REFUSAL);
});
