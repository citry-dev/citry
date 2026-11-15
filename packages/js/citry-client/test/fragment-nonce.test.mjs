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
async function startWith({ blockNonce, clobberCurrentScript, blockAttributes = {}, manifest = MANIFEST }) {
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
    dispatchEvent: () => true,
  });
  // A named element such as <form name="currentScript"> becomes an own property of the
  // document that hides the Document.prototype getter, and it has an empty nonce.
  if (clobberCurrentScript)
    Object.defineProperty(document, "currentScript", { value: { nonce: "", getAttribute: () => null } });
  const errors = [];
  const prompts = [];
  const context = {
    Document,
    HTMLScriptElement,
    document,
    history: { state: null, pushState() {}, replaceState() {} },
    console: { error: (...args) => errors.push(args.map(String).join(" ")), warn() {}, log() {} },
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
  return { errors, prompts };
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

// A newer server during a deploy can write a fragment this runtime does not know: another
// protocol string, or a top-level field beside `vue`. The page then offers its reload prompt.
for (const [name, manifest] of [
  ["another protocol", { vue: { ...JSON.parse(MANIFEST).vue, protocol: "citry-vue-fragment/2" } }],
  ["an unknown top-level field", { ...JSON.parse(MANIFEST), styles: [] }],
]) {
  test(`a fragment with ${name} offers a reload`, async () => {
    const { errors, prompts } = await startWith({
      blockNonce: PAGE_NONCE,
      clobberCurrentScript: false,
      manifest: JSON.stringify(manifest),
    });
    assert.deepEqual(prompts, ["This page is out of date. Reload to continue?"]);
    assert.equal(errors.length, 1, errors.join("\n"));
    assert.match(errors[0], /different Citry release/);
  });
}

test("a fragment refused for its nonce does not offer a reload, whatever it carries", async () => {
  // Injected markup has no nonce under a nonce-based CSP, so it cannot raise the prompt.
  const manifest = { vue: { ...JSON.parse(MANIFEST).vue, protocol: "citry-vue-fragment/2" } };
  const { errors, prompts } = await startWith({
    blockNonce: "",
    clobberCurrentScript: false,
    manifest: JSON.stringify(manifest),
  });
  assert.deepEqual(prompts, []);
  assert.match(errors[0], NONCE_REFUSAL);
});
