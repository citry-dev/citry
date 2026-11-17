import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import test from "node:test";
import vm from "node:vm";

// A prepared definition lists the dynamic <c-element> tags it uses. The server refuses the tags a
// browser would run or read as raw text, and an opaque HTML block under a chosen <svg> or <math>.
// These tests check that the browser runtime refuses the same things, so a definition that got past
// the server (or came from somewhere else) still cannot place them. The tag list is copied from
// the contract in packages/py/citry/tests/test_c_element_refusals.py.
const source = await readFile(new URL("../../../py/citry/citry/_vue/client.js", import.meta.url), "utf8");
const helperContract = source.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];
const RealVue = createRequire(import.meta.url)("vue");

const REFUSED_TAGS = [
  "applet",
  "base",
  "embed",
  "frame",
  "frameset",
  "iframe",
  "link",
  "meta",
  "noembed",
  "noframes",
  "noscript",
  "object",
  "plaintext",
  "script",
  "style",
  "template",
  "xmp",
];

const ALIAS = "citry-dynamic-0123456789abcdef";

const entry = (tag, alias = ALIAS) => ({ alias, tag, sourceStart: 0, sourceEnd: 10 });

// Loads client.js into a bare context with the real Vue, as the browser would have it.
function load() {
  const context = {
    CitryVueFragments: { installFragmentManager() {} },
    document: { currentScript: null },
    queueMicrotask,
    Vue: { ...RealVue },
  };
  context.globalThis = context;
  context.window = context;
  context.structuredClone = (value) => {
    context.__cloneJson = JSON.stringify(value);
    return vm.runInNewContext("JSON.parse(__cloneJson)", context);
  };
  vm.runInNewContext(source, context);
  return {
    context,
    citryRuntime: context.__citryRuntime,
    // Copies a value into the client's own realm, as the browser does for parsed JSON.
    realm(value) {
      context.__json = JSON.stringify(value);
      return vm.runInNewContext("JSON.parse(__json)", context);
    },
  };
}

// The opaque HTML component is private to client.js. Starting an app registers it with Vue under
// the name the compiled templates use, so a stand-in app that records registrations hands it over.
async function opaqueHtmlComponentOf() {
  let component = null;
  const app = {
    component(name, value) {
      if (name === "citry-opaque-html") component = value;
    },
    directive() {},
    use() {},
    config: { globalProperties: {} },
    mount() {
      throw new Error("STOP AT MOUNT");
    },
    unmount() {},
  };
  class Element {}
  const fixture = load();
  const { context } = fixture;
  Object.assign(context, {
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
  });
  context.Vue.createApp = () => app;
  context.Vue.createSSRApp = () => app;
  const metadata = {
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
  const asset = { id: "definition", url: "/definitions/abc.js", sha256: "0".repeat(64), ...metadata };
  const loaded = fixture.realm(metadata);
  loaded.render = vm.runInNewContext("(function () {})", context);
  context.__citryRuntimeDefinitions = { [asset.id]: loaded };
  const configuration = fixture.realm({
    manifest: {
      protocol: "citry-vue-prepared/1",
      appId: "dynamic-tags-app",
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
  // The start stops at the Vue mount, after the component is registered.
  await assert.rejects(fixture.citryRuntime.startPrepared(configuration), /STOP AT MOUNT/);
  assert.notEqual(component, null, "starting an app registers the opaque HTML component");
  return { fixture, opaqueHtmlComponent: component };
}

const spellings = (tag) => [tag, tag.toUpperCase(), tag[0].toUpperCase() + tag.slice(1)];

test("a dynamic element entry naming a tag the server refuses is rejected, in any letter case", () => {
  const { citryRuntime, realm } = load();
  for (const tag of REFUSED_TAGS) {
    for (const spelling of spellings(tag)) {
      assert.throws(
        () => citryRuntime.compilerRuntime.runtimeForDynamicElements(realm([entry(spelling)])),
        /invalid dynamic element entry/,
        spelling,
      );
    }
  }
});

test("a dynamic element entry naming an ordinary or foreign-content tag is accepted", () => {
  const { citryRuntime, realm } = load();
  for (const [index, tag] of ["div", "my-widget", "svg", "math", "SVG"].entries()) {
    const alias = `citry-dynamic-${String(index).repeat(16)}`;
    assert.doesNotThrow(() => citryRuntime.compilerRuntime.runtimeForDynamicElements(realm([entry(tag, alias)])), tag);
  }
});

// The children a compiled template would pass for the element's body. Each is placed directly in
// the children array and again one level down, inside an element child, because the check walks
// the whole body.
function bodies(V, opaqueHtmlComponent) {
  const staticBlock = () => V.createStaticVNode("<b>x</b>", 1);
  const opaqueBlock = () => V.createVNode(opaqueHtmlComponent, { record: { html: "<b>x</b>", nodeCount: 1 } });
  return {
    "a static block": () => [staticBlock()],
    "an opaque HTML component": () => [opaqueBlock()],
    "a static block inside an element child": () => [V.createVNode("g", null, [staticBlock()])],
    "an opaque component inside an element child": () => [V.createVNode("g", null, [opaqueBlock()])],
    "a static block in a nested array": () => [[V.createVNode("g", null, [[staticBlock()]])]],
  };
}

test("an opaque HTML block under a dynamic svg or math element is refused", async () => {
  const { fixture, opaqueHtmlComponent } = await opaqueHtmlComponentOf();
  const V = fixture.context.Vue;
  for (const tag of ["svg", "math", "SVG", "Math"]) {
    const runtime = fixture.citryRuntime.compilerRuntime.runtimeForDynamicElements(fixture.realm([entry(tag)]));
    for (const [label, makeChildren] of Object.entries(bodies(V, opaqueHtmlComponent))) {
      assert.throws(
        () => runtime.createElementVNode(ALIAS, null, makeChildren()),
        /opaque HTML block cannot sit inside a dynamic/,
        `${tag}: ${label}`,
      );
    }
  }
});

test("the same children under a div, and plain children under an svg, are not refused", async () => {
  const { fixture, opaqueHtmlComponent } = await opaqueHtmlComponentOf();
  const V = fixture.context.Vue;
  // Control: only an <svg> or <math> changes how the browser reads the block.
  const div = fixture.citryRuntime.compilerRuntime.runtimeForDynamicElements(fixture.realm([entry("div")]));
  for (const [label, makeChildren] of Object.entries(bodies(V, opaqueHtmlComponent))) {
    assert.doesNotThrow(() => div.createElementVNode(ALIAS, null, makeChildren()), label);
  }
  const svg = fixture.citryRuntime.compilerRuntime.runtimeForDynamicElements(fixture.realm([entry("svg")]));
  const plain = [V.createVNode("circle", null, []), V.createTextVNode("text"), null, [V.createVNode("g", null, [])]];
  assert.doesNotThrow(() => svg.createElementVNode(ALIAS, null, plain));
  assert.doesNotThrow(() => svg.createElementVNode(ALIAS, null, null));
});

// The definition's own list of dynamic elements is read a second time when the definition is
// registered, so it needs the same refusal.
test("registering a definition that lists a refused dynamic tag is rejected, and an ordinary tag is accepted", () => {
  const { citryRuntime, realm, context } = load();
  citryRuntime.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "dynamic-tags-register",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [
        {
          id: "root",
          typeKey: "Root",
          definitionId: "root-definition",
          parentId: null,
          placementKey: null,
          serverData: {},
          preparedData: { calls: {}, callRuns: {} },
        },
      ],
    }),
  );
  const render = vm.runInNewContext("(function () {})", context);
  const definition = (tag, alias) => {
    const value = realm({
      target: "ordinary-vnodes/1",
      helperContract,
      dynamicElements: [entry(tag, alias)],
      directiveSignature: [],
      replacementSites: [],
      localCalls: [],
      localCallRuns: [],
      opaqueHtmlSites: [],
      runtimeEventSites: [],
    });
    value.render = render;
    return value;
  };
  for (const tag of ["script", "IFRAME", "noscript", "base"]) {
    assert.throws(
      () => citryRuntime.registerDefinition("dynamic-tags-register", "root-definition", definition(tag, ALIAS)),
      /invalid dynamic element entry/,
      tag,
    );
  }
  assert.doesNotThrow(() =>
    citryRuntime.registerDefinition("dynamic-tags-register", "root-definition", definition("svg", ALIAS)),
  );
});
