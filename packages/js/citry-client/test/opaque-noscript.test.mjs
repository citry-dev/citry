import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import test from "node:test";
import vm from "node:vm";

// A prepared page lists its opaque HTML blocks (trusted HTML that Vue inserts as one piece). Vue
// parses a block inside a <template>, where Chromium and WebKit run with scripting off, so the
// markup inside a <noscript> becomes real elements. The server refuses a Markup value that holds a
// <noscript>; the browser runtime checks each block again before the app starts, so metadata that
// got past the server still cannot place one. A block from <c-raw> or #c-ignore is written in the
// template, so only a block whose site origin is "markup" is checked.
const source = await readFile(new URL("../../../py/citry/citry/_vue/client.js", import.meta.url), "utf8");
const helperContract = source.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];
const RealVue = createRequire(import.meta.url)("vue");

const SITE_KEY = "citryOpaque0";
const REFUSAL = /holds a <noscript> element/;

// Starts a prepared app whose root declares one opaque HTML site and carries `record` for it. The
// start stops at the Vue mount, so a start that gets past the preflight rejects with STOP AT MOUNT.
// With `documentStub` set to null the context has no `document` at all, as in node:vm; otherwise
// the stub stands in for the page's document.
async function startWithOpaqueBlock({ origin, html, documentStub = null }) {
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
    queueMicrotask,
    console: { error() {}, warn() {} },
    Vue: { ...RealVue, createApp: () => app, createSSRApp: () => app },
    Element,
    Node: class {},
    btoa,
    URL,
    CustomEvent: class {},
    setTimeout,
    clearTimeout,
    reportError() {},
    location: { assign() {} },
    history: { state: null },
  };
  // The client loads with a minimal document and reads the document again on every use, so the
  // one a test wants is swapped in after the load.
  context.document = { currentScript: null };
  context.globalThis = context;
  context.window = context;
  context.structuredClone = (value) => {
    context.__cloneJson = JSON.stringify(value);
    return vm.runInNewContext("JSON.parse(__cloneJson)", context);
  };
  vm.runInNewContext(source, context);
  if (documentStub === null) delete context.document;
  else context.document = documentStub;

  const realm = (value) => {
    context.__json = JSON.stringify(value);
    return vm.runInNewContext("JSON.parse(__json)", context);
  };
  const metadata = {
    target: "ordinary-vnodes/1",
    helperContract,
    dynamicElements: [],
    directiveSignature: [],
    replacementSites: [],
    localCalls: [],
    localCallRuns: [],
    opaqueHtmlSites: [{ key: SITE_KEY, origin, sourceStart: 0, sourceEnd: 16 }],
    runtimeEventSites: [],
  };
  const asset = { id: "definition", url: "/definitions/abc.js", sha256: "0".repeat(64), ...metadata };
  const loaded = realm(metadata);
  loaded.render = vm.runInNewContext("(function () {})", context);
  context.__citryRuntimeDefinitions = { [asset.id]: loaded };
  const configuration = realm({
    manifest: {
      protocol: "citry-vue-prepared/1",
      appId: "opaque-noscript-app",
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
          preparedData: { calls: {}, callRuns: {}, opaqueHtml: { [SITE_KEY]: { html, nodeCount: 1 } } },
        },
      ],
    },
    tags: { Root: "c-root" },
  });
  configuration.host = new Element();
  return context.__citryRuntime.startPrepared(configuration);
}

// A document whose <template> parse reports a <noscript> element only when `parsedNoscript` is
// true, whatever the HTML says. It stands in for the browser's parser, so these tests check what
// the runtime does with the parser's answer, not the parser.
function documentWhoseParserFinds(parsedNoscript) {
  return {
    currentScript: null,
    createElement() {
      return {
        content: {
          querySelector: (selector) => (selector === "noscript" && parsedNoscript ? {} : null),
          querySelectorAll: () => [],
        },
      };
    },
  };
}

const NOSCRIPT_HTML = "<noscript><img src=x></noscript>";

test("a Markup block that holds a noscript is refused before the app starts", async () => {
  // Without a document there is no parser to read the block with, so any block that names
  // noscript is refused rather than guessed at.
  await assert.rejects(startWithOpaqueBlock({ origin: "markup", html: NOSCRIPT_HTML }), REFUSAL);
});

test("a Markup block is refused when the page's own parser finds a noscript element", async () => {
  await assert.rejects(
    startWithOpaqueBlock({ origin: "markup", html: NOSCRIPT_HTML, documentStub: documentWhoseParserFinds(true) }),
    REFUSAL,
  );
});

test("a Markup block that only mentions noscript starts when the parser finds no noscript element", async () => {
  // The word appears (in an attribute value, say) but no element does.
  await assert.rejects(
    startWithOpaqueBlock({
      origin: "markup",
      html: '<b title="<noscript>">x</b>',
      documentStub: documentWhoseParserFinds(false),
    }),
    /STOP AT MOUNT/,
  );
});

test("a Markup block that does not name noscript starts without a document", async () => {
  await assert.rejects(startWithOpaqueBlock({ origin: "markup", html: "<b>bold</b>" }), /STOP AT MOUNT/);
});

test("a raw-origin block is not checked again, because the server checks its Markup values", async () => {
  // `<c-raw>` and `#c-ignore` contents are author-only by design, so they are not checked here.
  for (const documentStub of [null, documentWhoseParserFinds(true)]) {
    await assert.rejects(startWithOpaqueBlock({ origin: "raw", html: NOSCRIPT_HTML, documentStub }), /STOP AT MOUNT/);
  }
});
