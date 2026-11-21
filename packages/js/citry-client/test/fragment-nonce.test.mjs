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
// through stops at the host lookup, which tells the two outcomes apart without mounting Vue. The
// server writes the page's nonce into the JSON (`prepared.nonce`) as well as on the tag.
// `nonce: undefined` leaves the nonce out of the JSON.
const descriptor = (options = {}) => {
  const { nonce: _nonce, manifest = {}, appId = "app", host = "#missing-host", ...prepared } = options;
  const nonce = "nonce" in options ? options.nonce : PAGE_NONCE;
  return JSON.stringify({
    vue: {
      protocol: "citry-vue-fragment/1",
      appId,
      host,
      prepared: {
        host,
        ...(nonce === undefined ? {} : { nonce }),
        ...prepared,
        manifest: { appId, ...manifest },
      },
    },
  });
};
const MANIFEST = descriptor();

// Loads the runtime into a stub page and returns what the fragment manager logged for one
// fragment data block that is already in the page when the runtime starts.
async function startWith({
  blockNonce,
  clobberCurrentScript,
  blockAttributes = {},
  manifest = MANIFEST,
  cancelStale = false,
  blockConnected = false,
  pageNonce = PAGE_NONCE,
  documentApp,
  // The address the runtime's own tag loaded it from, the page's address, its base URL, and its
  // origin. An `about:srcdoc` document shares the origin of the page that created it.
  runtimeSrc = "https://shop.example/citry/citry.js",
  pageUrl = "https://shop.example/page",
  baseUrl = pageUrl,
  pageOrigin = new URL(pageUrl).origin,
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
    get baseURI() {
      return baseUrl;
    }
    get URL() {
      return pageUrl;
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
  const runtimeScript = new HTMLScriptElement(pageNonce);
  runtimeScript.src = runtimeSrc;
  const block = new HTMLScriptElement(blockNonce);
  block.textContent = manifest;
  // A block still in the page is where the fragment's event starts.
  if (blockConnected) {
    block.isConnected = true;
    block.dispatchEvent = (event) => record("block", event);
  }
  block.attributes = { type: "application/json", "data-citry-vue-fragment": "", ...blockAttributes };
  // The configuration block of an app the page itself renders, in the mode given by `documentApp`.
  let documentBlock = null;
  if (documentApp !== undefined) {
    documentBlock = new HTMLScriptElement(pageNonce);
    documentBlock.attributes = { type: "application/json", "data-citry-vue-document": "page" };
    documentBlock.textContent = JSON.stringify({
      manifest: { appId: "page" },
      development: documentApp.development,
      ...(documentApp.jsonNonce === undefined ? { nonce: pageNonce } : { nonce: documentApp.jsonNonce }),
    });
  }
  const document = new Document();
  Object.assign(document, {
    readyState: "complete",
    documentElement: {},
    body: { contains: () => false },
    createElement: () => ({}),
    querySelector: () => null,
    querySelectorAll: (selector) => {
      if (selector === FRAGMENT_SELECTOR) return [block];
      return selector === DOCUMENT_SELECTOR && documentBlock ? [documentBlock] : [];
    },
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
    // startDocument reports a failed start by throwing from a microtask; the stub page cannot
    // start a real app, so that error is recorded instead of ending the test process.
    queueMicrotask: (callback) =>
      queueMicrotask(() => {
        try {
          callback();
        } catch (error) {
          errors.push(String(error));
        }
      }),
    setTimeout,
    clearTimeout,
    structuredClone,
    btoa,
    // The visitor declines, so the test sees the question without a reload.
    confirm: (message) => {
      prompts.push(message);
      return false;
    },
    location: { assign() {}, reload() {}, href: pageUrl, origin: pageOrigin },
    origin: pageOrigin,
    URL,
  };
  context.globalThis = context;
  context.window = context;
  context.self = context;
  vm.runInNewContext(source, context);
  // The page's own app starts before the fragment's failure is reported, as on a real page.
  if (documentApp !== undefined) {
    try {
      context.__citryRuntime.startDocument("page");
    } catch (error) {
      errors.push(String(error));
    }
  }
  // The manager reports a refused block from a rejected promise, one turn later.
  await new Promise((resolve) => setTimeout(resolve, 0));
  return { errors, prompts, warnings, events, citry: context.Citry };
}

const DOCUMENT_SELECTOR = 'script[type="application/json"][data-citry-vue-document]';
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

test("a fragment block with the page nonce on its tag but not in its JSON is refused", async () => {
  // An injected `<script type=application/json data-citry-vue-fragment x=1 x=` left open takes in
  // the genuine `<script nonce=...>` after it. The repeated `x` drops the leftover `<script` text,
  // so the tag looks clean and carries the page's nonce; only the JSON, which the attacker wrote
  // without knowing the nonce, tells it apart.
  for (const nonce of [undefined, "", "other-nonce"]) {
    const { errors } = await startWith({
      blockNonce: PAGE_NONCE,
      clobberCurrentScript: false,
      blockAttributes: { x: "1", id: "user-settings", nonce: "" },
      manifest: descriptor({ nonce }),
    });
    assert.equal(errors.length, 1, errors.join("\n"));
    assert.match(errors[0], NONCE_REFUSAL);
  }
});

test("a configuration block with the page nonce on its tag but not in its JSON is refused", async () => {
  const { errors } = await startWith({
    blockNonce: PAGE_NONCE,
    clobberCurrentScript: false,
    documentApp: { development: false, jsonNonce: "" },
  });
  assert.ok(
    errors.some((error) => /configuration block for app page does not carry the page's CSP nonce/.test(error)),
    errors.join("\n"),
  );
});

// On a page whose runtime has no nonce, injected markup can write a fragment block as well as the
// server can, so the block may name only what Citry serves itself.
const SHA = "a".repeat(64);
const OTHER_SHA = "b".repeat(64);
const OWN_DEFINITION = `/citry/ext/events/definitions/${SHA}.js`;
// The server names a fragment's app with 32 hex digits and its host `#citry-vue-<appId>`. The stub
// page has no such element, so a block the check accepts stops at the host lookup.
const APP_ID = "c".repeat(32);
// `page` sets up the stub page; the other fields of `extra` go into the block's configuration.
const withoutNonce = (manifest, { page = {}, ...extra } = {}) =>
  startWith({
    blockNonce: "",
    pageNonce: "",
    clobberCurrentScript: false,
    manifest: descriptor({ nonce: undefined, appId: APP_ID, host: `#citry-vue-${APP_ID}`, manifest, ...extra }),
    ...page,
  });
const ownScript = (url = OWN_DEFINITION, sha256 = SHA) => ({ source: { kind: "owned", url, sha256, attrs: {} } });
const WITHOUT_NONCE_REFUSAL = /refused a Vue fragment found in a page without a CSP nonce/;

test("a page without a nonce starts a fragment that names only Citry's own files and routes", async () => {
  const cases = [
    [{ definitions: [{ url: OWN_DEFINITION, sha256: SHA }], scripts: [ownScript()] }, {}],
    // The full URL of the same route, and the Events routes the server writes.
    [
      { definitions: [{ url: `https://shop.example${OWN_DEFINITION}`, sha256: SHA }], scripts: [] },
      { endpoint: "/citry/ext/events/call", eventBaseUrl: "/citry/ext/events/e/" },
    ],
    // The hashed runtime URL and a sub-path both come from the runtime's own address.
    [
      { definitions: [{ url: `/shop/citry/ext/events/definitions/${SHA}.js`, sha256: SHA }], scripts: [] },
      { page: { runtimeSrc: `https://shop.example/shop/citry/citry.${OTHER_SHA}.js` } },
    ],
  ];
  for (const [manifest, extra] of cases) {
    const { errors } = await withoutNonce(manifest, extra);
    assert.equal(errors.length, 1, errors.join("\n"));
    assert.match(errors[0], HOST_REFUSAL);
  }
});

test("a page without a nonce refuses a fragment that names another script or address", async () => {
  const cases = [
    // A same-origin file that is not one of Citry's definitions, with the hash of its bytes.
    { definitions: [{ url: "/uploads/gadget.js", sha256: SHA }], scripts: [] },
    { definitions: [], scripts: [ownScript("/uploads/gadget.js")] },
    // Citry's route, but the file name does not match the hash the browser checks.
    { definitions: [{ url: `/citry/ext/events/definitions/${OTHER_SHA}.js`, sha256: SHA }], scripts: [] },
    { definitions: [{ url: `${OWN_DEFINITION}?x=1`, sha256: SHA }], scripts: [] },
    // Another origin, and the same path outside the runtime's mount prefix.
    { definitions: [{ url: `https://evil.example${OWN_DEFINITION}`, sha256: SHA }], scripts: [] },
    { definitions: [{ url: `/other/ext/events/definitions/${SHA}.js`, sha256: SHA }], scripts: [] },
    // A script from any address the author did not serve through Citry.
    { definitions: [], scripts: [{ source: { kind: "external", url: "/gadget.js", attrs: {} } }] },
    { definitions: [], scripts: [{ source: { kind: "external", url: "https://evil.example/x.js", attrs: {} } }] },
  ];
  for (const manifest of cases) {
    const { errors } = await withoutNonce(manifest);
    assert.equal(errors.length, 1, `${JSON.stringify(manifest)}\n${errors.join("\n")}`);
    assert.match(errors[0], WITHOUT_NONCE_REFUSAL);
  }
  for (const extra of [
    { endpoint: "https://evil.example/citry/ext/events/call" },
    { endpoint: "/account/delete" },
    { eventBaseUrl: "https://evil.example/" },
    // The server never writes CSRF options into a block, and they would choose the cookie sent.
    { csrf: { cookie: "sessionid" } },
  ]) {
    const { errors } = await withoutNonce({ definitions: [], scripts: [] }, extra);
    assert.equal(errors.length, 1, errors.join("\n"));
    assert.match(errors[0], WITHOUT_NONCE_REFUSAL);
  }
});

test("a page without a nonce starts a fragment that names CSRF names, without taking them", async () => {
  // The server writes `csrfNames` from the Events settings, so the fragment is not refused; the
  // runtime drops them (checkBlockWithoutNonce), so injected markup cannot choose the cookie.
  const { errors } = await withoutNonce(
    { definitions: [], scripts: [] },
    { csrfNames: { cookie: "sessionid", header: "X-Stolen" } },
  );
  assert.equal(errors.length, 1, errors.join("\n"));
  assert.match(errors[0], HOST_REFUSAL);
});

test("Citry.pageNonce() returns the nonce of the runtime's own tag, or null without one", async () => {
  const withNonce = await startWith({ blockNonce: PAGE_NONCE });
  assert.equal(withNonce.citry.pageNonce(), PAGE_NONCE);
  const without = await startWith({ blockNonce: "", pageNonce: "" });
  assert.equal(without.citry.pageNonce(), null);
  // A named element that hides document.currentScript cannot hand page code an empty nonce.
  const clobbered = await startWith({ blockNonce: PAGE_NONCE, clobberCurrentScript: true });
  assert.equal(clobbered.citry.pageNonce(), PAGE_NONCE);
});

test("a runtime with no address of its own holds fragments to the page's origin", async () => {
  // An inline runtime, or one the docs playground loads from a blob: URL, cannot tell the prefix.
  const page = { runtimeSrc: "" };
  const accepted = await withoutNonce(
    { definitions: [{ url: `/anything/ext/events/definitions/${SHA}.js`, sha256: SHA }], scripts: [] },
    { page },
  );
  assert.match(accepted.errors[0], HOST_REFUSAL);
  const refused = await withoutNonce(
    { definitions: [{ url: `https://evil.example/ext/events/definitions/${SHA}.js`, sha256: SHA }], scripts: [] },
    { page },
  );
  assert.match(refused.errors[0], WITHOUT_NONCE_REFUSAL);
});

test("a page without a nonce starts a fragment whose component file Citry serves with local_files", async () => {
  // `local_files = "serve"` writes the component's own file as an `external` source on Citry's
  // asset route, named by the hash of its content.
  const served = (url) => ({ definitions: [], scripts: [{ source: { kind: "external", url, attrs: {} } }] });
  const accepted = await withoutNonce(served("/citry/asset/0123456789ab.js"));
  assert.match(accepted.errors[0], HOST_REFUSAL);
  for (const url of [
    "/citry/asset/0123456789ab.css",
    "/citry/asset/../uploads/0123456789ab.js",
    "/citry/asset/sub/0123456789ab.js",
    "/uploads/asset/0123456789ab.js",
    "https://evil.example/citry/asset/0123456789ab.js",
  ]) {
    const { errors } = await withoutNonce(served(url));
    assert.match(errors[0], WITHOUT_NONCE_REFUSAL, url);
  }
});

test("a page without a nonce holds Citry's routes to the page's origin when the runtime loads from another", async () => {
  // A CDN that serves only the runtime moves it to its own host, while the server still writes the
  // definition URLs and the Events routes for the app's own host, so those start.
  const page = { runtimeSrc: "https://cdn.example/citry/citry.js" };
  const routes = { endpoint: "/citry/ext/events/call", eventBaseUrl: "/citry/ext/events/e/", page };
  for (const url of [OWN_DEFINITION, `https://shop.example${OWN_DEFINITION}`]) {
    const { errors } = await withoutNonce({ definitions: [{ url, sha256: SHA }], scripts: [] }, routes);
    assert.match(errors[0], HOST_REFUSAL, url);
  }
  // The runtime's own origin is not a prefix: under a hash-based CSP a copy of the runtime may run
  // from any site. Only the same path on the page's own origin is accepted.
  for (const url of [
    `https://cdn.example${OWN_DEFINITION}`,
    `/elsewhere/ext/events/definitions/${SHA}.js`,
    `https://evil.example${OWN_DEFINITION}`,
  ]) {
    const { errors } = await withoutNonce({ definitions: [{ url, sha256: SHA }], scripts: [] }, { page });
    assert.match(errors[0], WITHOUT_NONCE_REFUSAL, url);
  }
});

test("a copy of the runtime on another site does not let that site's files or routes through", async () => {
  // Injected markup can add a tag for the genuine runtime bytes on another site before Citry's own;
  // a CSP that allows the runtime by its hash runs it, and its URL is the runtime's address.
  const page = { runtimeSrc: `https://evil.example/citry/citry.${OTHER_SHA}.js` };
  const evil = "https://evil.example/citry/";
  for (const [manifest, extra] of [
    [{ definitions: [{ url: `${evil}ext/events/definitions/${SHA}.js`, sha256: SHA }], scripts: [] }, {}],
    [{ definitions: [], scripts: [ownScript(`${evil}ext/events/definitions/${SHA}.js`)] }, {}],
    [
      { definitions: [], scripts: [{ source: { kind: "external", url: `${evil}asset/0123456789ab.js`, attrs: {} } }] },
      {},
    ],
    [{ definitions: [], scripts: [] }, { endpoint: `${evil}ext/events/call` }],
  ]) {
    const { errors } = await withoutNonce(manifest, { ...extra, page });
    assert.match(errors[0], WITHOUT_NONCE_REFUSAL, JSON.stringify(manifest));
  }
  const own = await withoutNonce({ definitions: [{ url: OWN_DEFINITION, sha256: SHA }], scripts: [] }, { page });
  assert.match(own.errors[0], HOST_REFUSAL);
});

test("an about:srcdoc page resolves a fragment's files against its base only on its own origin", async () => {
  // A srcdoc document has no address of its own, so a relative URL resolves against the base URL
  // it took from the page that created it, which a <base> element inside it can also set.
  const srcdoc = { pageUrl: "about:srcdoc", pageOrigin: "https://shop.example" };
  const definition = (url) => ({ definitions: [{ url, sha256: SHA }], scripts: [] });
  const sameOrigin = await withoutNonce(definition(OWN_DEFINITION), {
    page: { ...srcdoc, baseUrl: "https://shop.example/page" },
  });
  assert.match(sameOrigin.errors[0], HOST_REFUSAL);
  const page = { ...srcdoc, baseUrl: "https://evil.example/" };
  const moved = await withoutNonce(definition(OWN_DEFINITION), { page });
  assert.match(moved.errors[0], WITHOUT_NONCE_REFUSAL);
  // A full URL does not depend on the base, so it is still the app's own file.
  const full = await withoutNonce(definition(`https://shop.example${OWN_DEFINITION}`), { page });
  assert.match(full.errors[0], HOST_REFUSAL);
});

test("a page without a nonce accepts a served local file name only in the case Citry writes it", async () => {
  // The hash part is lower-case hex, as Citry writes it; the extension keeps the file's own case.
  const served = (url) => ({ definitions: [], scripts: [{ source: { kind: "external", url, attrs: {} } }] });
  const upper = await withoutNonce(served("/citry/asset/ABCDEF012345.js"));
  assert.match(upper.errors[0], WITHOUT_NONCE_REFUSAL);
  const extension = await withoutNonce(served("/citry/asset/abcdef012345.JS"));
  assert.match(extension.errors[0], HOST_REFUSAL);
});

test("a page without a nonce holds a fragment's i18n messages URL to Citry's route", async () => {
  const withI18n = (messagesUrl) => ({
    definitions: [],
    scripts: [],
    extensions: { i18n: { schemaVersion: 1, templateContextNames: [], payload: { messages_url: messagesUrl } } },
  });
  for (const url of ["/citry/ext/i18n/messages", null]) {
    const { errors } = await withoutNonce(withI18n(url));
    assert.match(errors[0], HOST_REFUSAL, String(url));
  }
  for (const url of [
    "/account/delete",
    "/citry/ext/i18n/messages?x=1",
    "https://evil.example/citry/ext/i18n/messages",
  ]) {
    const { errors } = await withoutNonce(withI18n(url));
    assert.match(errors[0], /its i18n messages URL is not Citry's own/, url);
  }
});

test("a page without a nonce mounts a fragment only into the host the server writes for it", async () => {
  for (const [appId, host] of [
    [APP_ID, "#login-form"],
    [APP_ID, "body"],
    ["app", "#citry-vue-app"],
  ]) {
    const { errors } = await startWith({
      blockNonce: "",
      pageNonce: "",
      clobberCurrentScript: false,
      manifest: descriptor({ nonce: undefined, appId, host, manifest: { definitions: [], scripts: [] } }),
    });
    assert.match(errors[0], /its host is not the element Citry writes for it/, host);
  }
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

test("a fragment block injected into a production page without a nonce cannot make it ask", async () => {
  // Without a nonce every fragment block starts, so injected markup can claim a development
  // server. The page's own app says it runs in production, and that decides.
  const { prompts, warnings, events } = await startWith({
    blockNonce: "",
    pageNonce: "",
    clobberCurrentScript: false,
    manifest: JSON.stringify(otherProtocol(true)),
    documentApp: { development: false },
  });
  assert.equal(events.filter((event) => event.type === FRAGMENT_STALE.type).length, 1);
  assert.deepEqual(prompts, []);
  assert.equal(warnings.length, 1, warnings.join("\n"));
});

test("a development page asks even for a fragment from a production server", async () => {
  const { prompts, warnings } = await startWith({
    blockNonce: PAGE_NONCE,
    clobberCurrentScript: false,
    manifest: JSON.stringify(otherProtocol(false)),
    documentApp: { development: true },
  });
  assert.deepEqual(prompts, [QUESTION]);
  assert.deepEqual(warnings, []);
});
