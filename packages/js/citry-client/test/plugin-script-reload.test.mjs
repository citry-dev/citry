import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import test from "node:test";
import vm from "node:vm";

// A page served from a cache can name a browser plugin script that a later deploy removed, so the
// plugin never registers and the app cannot start. These tests start an app through the real
// `startDocument` and `startPrepared` and check when the runtime asks the server whether the
// script is gone (a HEAD request) and reloads the page once.
const source = await readFile(new URL("../../../py/citry/citry/_vue/client.js", import.meta.url), "utf8");
const helperContract = source.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];
const RealVue = createRequire(import.meta.url)("vue");

const SCRIPT_URL = "/citry/ext/i18n/runtime.abc123.js";
const STORAGE_KEY = "citry:runtime-reload";
const METADATA = {
  target: "ordinary-vnodes/1",
  helperContract,
  dynamicElements: [],
  directiveSignature: [],
  replacementSites: [],
  localCalls: [],
  localCallRuns: [],
  opaqueHtmlSites: [],
  runtimeEventSites: [],
};

// Builds a page with the runtime loaded. `navigationType` is what the Navigation Timing entry
// reports ("navigate" or "reload"); `legacyType` is `performance.navigation.type` for a browser
// without that entry; with neither, the page has no way to tell. `fetchResult` is the HEAD
// response status, or an Error to reject with. `storage` is the initial session storage, or
// "throw" for a browser where reading and writing it throws.
function page({
  navigationType = "navigate",
  legacyType,
  noPerformance = false,
  fetchResult = 404,
  storage = {},
  flagSet = false,
} = {}) {
  class Element {}
  const host = new Element();
  const app = {
    component() {},
    directive() {},
    use() {},
    config: { globalProperties: {} },
    mount() {
      throw new Error("STOP AT MOUNT");
    },
    unmount() {},
  };
  const record = { fetches: [], reloads: 0, errors: [], reported: [], stored: { ...storage } };
  const sessionStorage =
    storage === "throw"
      ? {
          getItem() {
            throw new Error("storage blocked");
          },
          setItem() {
            throw new Error("storage blocked");
          },
        }
      : {
          getItem: (key) => (key in record.stored ? record.stored[key] : null),
          setItem: (key, value) => {
            record.stored[key] = String(value);
          },
        };
  let performance;
  if (!noPerformance) {
    performance =
      legacyType === undefined
        ? { getEntriesByType: (kind) => (kind === "navigation" ? [{ type: navigationType }] : []) }
        : { getEntriesByType: () => [], navigation: { type: legacyType } };
  }
  const context = {
    CitryVueFragments: { installFragmentManager() {} },
    Element,
    Node: class {},
    location: {
      assign() {},
      reload() {
        record.reloads += 1;
      },
    },
    history: { state: null },
    // Capture the rethrown start error instead of letting it crash the test process.
    queueMicrotask: (callback) => {
      try {
        callback();
      } catch (error) {
        record.reported.push(error);
      }
    },
    btoa,
    URL,
    console: { ...console, error: (...args) => record.errors.push(args.join(" ")) },
    CustomEvent: class {},
    setTimeout,
    clearTimeout,
    sessionStorage,
    fetch: async (url, options) => {
      record.fetches.push({ url, options: { ...options } });
      if (fetchResult instanceof Error) throw fetchResult;
      return { status: fetchResult };
    },
    Vue: { ...RealVue, createApp: () => app, createSSRApp: () => app },
  };
  if (performance) context.performance = performance;
  if (flagSet) context.__citryRuntimeMissing = true;
  context.globalThis = context;
  context.window = context;
  let block = null;
  context.document = {
    URL: "https://example.test/page",
    baseURI: "https://example.test/page",
    currentScript: null,
    dispatchEvent() {},
    addEventListener() {},
    removeEventListener() {},
    createElement() {
      throw new Error("STOP AT LOAD");
    },
    querySelector: (selector) => (selector === "#app" ? host : null),
    querySelectorAll: () => (block ? [block] : []),
  };
  const realm = (value) => {
    context.__json = JSON.stringify(value);
    return vm.runInNewContext("JSON.parse(__json)", context);
  };
  context.structuredClone = realm;
  vm.runInNewContext(source, context);
  // The definition is already in the page, so the start reaches the plugin check without loading it.
  const loaded = realm(METADATA);
  loaded.render = vm.runInNewContext("(function () {})", context);
  context.__citryRuntimeDefinitions = { definition: loaded };

  const runtime = context.__citryRuntime;
  return {
    context,
    record,
    runtime,
    // Registers a plugin named "i18n" whose factory stops the start, which shows the plugin check passed.
    register(schemaVersion = 1) {
      runtime.registerBrowserPlugin("i18n", schemaVersion, () => {
        throw new Error("STOP AT FACTORY");
      });
    },
    configuration({
      extension = { payload: {}, schemaVersion: 1, templateContextNames: [], scriptUrl: SCRIPT_URL },
      canReload,
    } = {}) {
      const value = {
        manifest: {
          protocol: "citry-vue-prepared/1",
          appId: "app",
          revision: 0,
          rootId: "root",
          markers: [],
          scripts: [],
          styles: [],
          typePolicies: [],
          extensions: { i18n: extension },
          definitions: [{ id: "definition", url: "/definitions/abc.js", sha256: "0".repeat(64), ...METADATA }],
          occurrences: [
            {
              id: "root",
              typeKey: "Root",
              definitionId: "definition",
              parentId: null,
              placementKey: null,
              serverData: {},
              preparedData: { calls: {}, callRuns: {} },
            },
          ],
        },
        tags: { Root: "c-root" },
        host: "#app",
      };
      if (canReload !== undefined) value.canReload = canReload;
      // The runtime checks for plain objects of its own realm, as JSON.parse in the page makes them.
      return realm(value);
    },
    // Starts the app the way the server's start script does, then lets the HEAD request settle.
    async startDocument(options) {
      const text = JSON.stringify(this.configuration(options));
      block = { getAttribute: (name) => (name === "data-citry-vue-document" ? "app" : null), textContent: text };
      runtime.startDocument("app");
      for (let index = 0; index < 5; index += 1) await new Promise((resolve) => setImmediate(resolve));
    },
  };
}

const MISSING = /missing or incompatible Citry browser plugin: i18n/;

test("an extension wrapper may carry a scriptUrl string", async () => {
  const fixture = page();
  fixture.register();
  await assert.rejects(fixture.runtime.startPrepared(fixture.configuration()), /STOP AT FACTORY/);
});

test("an extension wrapper without scriptUrl still starts, as a page from Citry 0.8.0 does", async () => {
  const fixture = page();
  fixture.register();
  const configuration = fixture.configuration({
    extension: { payload: {}, schemaVersion: 1, templateContextNames: [] },
  });
  await assert.rejects(fixture.runtime.startPrepared(configuration), /STOP AT FACTORY/);
});

test("a scriptUrl that is not a non-empty string is refused", async () => {
  for (const scriptUrl of [42, "", null, ["/a.js"]]) {
    const fixture = page();
    fixture.register();
    const configuration = fixture.configuration({
      extension: { payload: {}, schemaVersion: 1, templateContextNames: [], scriptUrl },
    });
    await assert.rejects(fixture.runtime.startPrepared(configuration), /invalid prepared extension wrapper/);
  }
});

test("an unregistered plugin whose script is gone reloads the page once and stores its URL", async () => {
  const fixture = page();
  await fixture.startDocument({ canReload: true });
  assert.deepEqual(fixture.record.fetches, [{ url: SCRIPT_URL, options: { method: "HEAD", cache: "no-store" } }]);
  assert.equal(fixture.record.reloads, 1);
  assert.equal(fixture.record.stored[STORAGE_KEY], SCRIPT_URL);
  assert.equal(fixture.context.__citryRuntimeMissing, true);
  // The start error is still reported as an uncaught error.
  assert.equal(fixture.record.reported.length, 1);
  assert.match(fixture.record.reported[0].message, MISSING);
});

test("a script the server still has does not reload the page", async () => {
  const fixture = page({ fetchResult: 200 });
  await fixture.startDocument({ canReload: true });
  assert.equal(fixture.record.fetches.length, 1);
  assert.equal(fixture.record.reloads, 0);
  assert.equal(fixture.record.stored[STORAGE_KEY], undefined);
  assert.deepEqual(fixture.record.errors, [`Citry could not load a browser plugin script: ${SCRIPT_URL}`]);
});

test("a failed HEAD request does not reload the page", async () => {
  const fixture = page({ fetchResult: new Error("offline") });
  await fixture.startDocument({ canReload: true });
  assert.equal(fixture.record.fetches.length, 1);
  assert.equal(fixture.record.reloads, 0);
  assert.deepEqual(fixture.record.errors, [`Citry could not load a browser plugin script: ${SCRIPT_URL}`]);
});

test("a load that is already a reload does not probe again", async () => {
  for (const options of [{ navigationType: "reload" }, { legacyType: 1 }, { noPerformance: true }]) {
    const fixture = page(options);
    await fixture.startDocument({ canReload: true });
    assert.equal(fixture.record.fetches.length, 0, JSON.stringify(options));
    assert.equal(fixture.record.reloads, 0);
    assert.deepEqual(fixture.record.errors, [`Citry could not load a browser plugin script: ${SCRIPT_URL}`]);
  }
});

test("an older browser that reports a fresh navigation still probes", async () => {
  const fixture = page({ legacyType: 0 });
  await fixture.startDocument({ canReload: true });
  assert.equal(fixture.record.fetches.length, 1);
  assert.equal(fixture.record.reloads, 1);
});

test("a URL already stored in session storage does not probe again", async () => {
  const fixture = page({ storage: { [STORAGE_KEY]: SCRIPT_URL } });
  await fixture.startDocument({ canReload: true });
  assert.equal(fixture.record.fetches.length, 0);
  assert.equal(fixture.record.reloads, 0);
});

test("session storage that throws still lets the page probe and reload once", async () => {
  const fixture = page({ storage: "throw" });
  await fixture.startDocument({ canReload: true });
  assert.equal(fixture.record.fetches.length, 1);
  assert.equal(fixture.record.reloads, 1);
});

test("a page the server did not allow to reload never probes", async () => {
  for (const canReload of [false, undefined, "true"]) {
    const fixture = page();
    await fixture.startDocument({ canReload });
    assert.equal(fixture.record.fetches.length, 0, String(canReload));
    assert.equal(fixture.record.reloads, 0);
    assert.equal(fixture.record.reported.length, 1);
  }
});

test("a registered plugin that does not match never probes", async () => {
  const fixture = page();
  fixture.register(2);
  await fixture.startDocument({ canReload: true });
  assert.equal(fixture.record.fetches.length, 0);
  assert.equal(fixture.record.reloads, 0);
  assert.match(fixture.record.reported[0].message, MISSING);
});

test("a page where another app already handled a missing script does not probe", async () => {
  const fixture = page({ flagSet: true });
  await fixture.startDocument({ canReload: true });
  assert.equal(fixture.record.fetches.length, 0);
  assert.equal(fixture.record.reloads, 0);
});

test("a fragment start through startPrepared never probes", async () => {
  const fixture = page();
  await assert.rejects(fixture.runtime.startPrepared(fixture.configuration({ canReload: true })), MISSING);
  for (let index = 0; index < 5; index += 1) await new Promise((resolve) => setImmediate(resolve));
  assert.equal(fixture.record.fetches.length, 0);
  assert.equal(fixture.record.reloads, 0);
  assert.equal(fixture.context.__citryRuntimeMissing, undefined);
});
