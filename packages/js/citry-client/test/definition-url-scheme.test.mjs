import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import test from "node:test";
import vm from "node:vm";

// These tests start a prepared app through the real `startPrepared` and check which component
// definition URLs the runtime accepts before it loads anything.
const source = await readFile(new URL("../../../py/citry/citry/_vue/client.js", import.meta.url), "utf8");
const helperContract = source.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];
const RealVue = createRequire(import.meta.url)("vue");

const REFUSED = /refused the script URL/;
// The runtime got past the URL check and asked the page for a script element to load the file.
const LOADING = /STOP AT LOAD/;
// The definition was already in the page, so the runtime went straight to mounting the app.
const MOUNTING = /STOP AT MOUNT/;

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

// Starts one app whose root uses a single definition served from `url`, on a page at `pageUrl`
// whose base URL is `baseUrl`. With `registered`, the definition's script already ran, as a
// document build that inlines its scripts arranges.
async function start({ pageUrl, baseUrl = pageUrl, url, registered = false }) {
  class Element {}
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
  const context = {
    CitryVueFragments: { installFragmentManager() {} },
    Element,
    Node: class {},
    location: { assign() {} },
    history: { state: null },
    queueMicrotask,
    btoa,
    // The URL check resolves each URL with the page's URL class, so the stub page needs it.
    URL,
    console,
    CustomEvent: class {},
    setTimeout,
    clearTimeout,
    Vue: { ...RealVue, createApp: () => app, createSSRApp: () => app },
  };
  context.globalThis = context;
  context.window = context;
  context.document = {
    URL: pageUrl,
    baseURI: baseUrl,
    currentScript: null,
    dispatchEvent() {},
    addEventListener() {},
    removeEventListener() {},
    // Loading a definition or its preload link starts here, so a URL that passed the check
    // stops the start at this point.
    createElement() {
      throw new Error("STOP AT LOAD");
    },
  };
  const realm = (value) => {
    context.__json = JSON.stringify(value);
    return vm.runInNewContext("JSON.parse(__json)", context);
  };
  context.structuredClone = realm;
  vm.runInNewContext(source, context);

  const asset = { id: "definition", url, sha256: "0".repeat(64), ...METADATA };
  if (registered) {
    const loaded = realm(METADATA);
    loaded.render = vm.runInNewContext("(function () {})", context);
    context.__citryRuntimeDefinitions = { [asset.id]: loaded };
  }
  const configuration = realm({
    manifest: {
      protocol: "citry-vue-prepared/1",
      appId: "url-app",
      revision: 0,
      rootId: "root",
      markers: [],
      scripts: [],
      styles: [],
      typePolicies: [],
      definitions: [asset],
      occurrences: [
        {
          id: "root",
          typeKey: "Root",
          definitionId: asset.id,
          parentId: null,
          placementKey: null,
          serverData: {},
          preparedData: { calls: {}, callRuns: {} },
        },
      ],
    },
    tags: { Root: "c-root" },
  });
  configuration.host = new Element();
  return context.__citryRuntime.startPrepared(configuration);
}

const FILE_PAGE = "file:///site/_build/index.html";
const WEB_PAGE = "https://example.test/page";

test("a page opened from disk starts with a definition it already holds", async () => {
  // A document build inlines the definition, and its root-relative URL resolves to file:.
  await assert.rejects(start({ pageUrl: FILE_PAGE, url: "/definitions/abc.js", registered: true }), MOUNTING);
});

test("a definition already in the page is not checked, because it is never loaded", async () => {
  await assert.rejects(start({ pageUrl: WEB_PAGE, url: "data:text/javascript,1", registered: true }), MOUNTING);
});

test("a page opened from disk may load a definition from a file: URL", async () => {
  await assert.rejects(start({ pageUrl: FILE_PAGE, url: "/definitions/abc.js" }), LOADING);
});

test("a page served over https still loads a definition from an https: URL", async () => {
  await assert.rejects(start({ pageUrl: WEB_PAGE, url: "/definitions/abc.js" }), LOADING);
});

test("a page served over https refuses a file: definition URL, even with a file: base URL", async () => {
  // An injected <base href="file:///"> changes the base URL but not the page's own address.
  await assert.rejects(start({ pageUrl: WEB_PAGE, url: "file:///definitions/abc.js" }), REFUSED);
  await assert.rejects(start({ pageUrl: WEB_PAGE, baseUrl: "file:///", url: "/definitions/abc.js" }), REFUSED);
});

for (const url of ["data:text/javascript,1", "javascript:1"]) {
  test(`a definition URL ${url.split(":")[0]}: is refused on a page from disk and on the web`, async () => {
    await assert.rejects(start({ pageUrl: FILE_PAGE, url }), REFUSED);
    await assert.rejects(start({ pageUrl: WEB_PAGE, url }), REFUSED);
  });
}
