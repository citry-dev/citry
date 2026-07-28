/**
 * Pinned-version canary over the Alpine private APIs the events runtime
 * touches: `addScopeToNode`, `_x_dataStack`, `_x_ignore`, `initTree`,
 * `onAttributeRemoved`, and `cloneNode`, plus the morph
 * package's export shape (WP6 spike finding F1) and its Alpine bridge.
 *
 * The events runtime's scope isolation and morph integration are coupled to
 * exact Alpine and morph versions (see the header of src/citry-events.ts).
 * This test fails loudly when a dependency bump changes any of those
 * internals, before anything reaches a browser. Behavior in a real DOM
 * (isolation truncation, magic resolution, scope purity) is covered by the
 * Playwright e2e suite in packages/py/citry/tests/e2e/.
 *
 * The packages are loaded through `require` (their CJS builds): node cannot
 * import the ESM dists directly (no "type": "module" in either package), and
 * importing the package name would go through node's CJS-to-ESM interop,
 * which reshapes the exports and would test the interop, not the package.
 * The ESM dist, the exact file esbuild bundles via the "module" field, is
 * checked by source text where its shape is the contract.
 *
 * Alpine's module wires a MutationObserver and touches window/document at
 * load time, so the few globals it needs are stubbed first; every assertion
 * below runs on plain objects, no DOM needed.
 */
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import test from "node:test";
import { build } from "esbuild";

import {
  ALPINE_VERSION as EXPECTED_VERSION,
  citryClientBuildOptions,
  instrumentAlpineDirectives,
} from "../build-support.mjs";

globalThis.MutationObserver = class {
  observe() {}
  disconnect() {}
  takeRecords() {
    return [];
  }
};
globalThis.window = { Element: class {} };
globalThis.document = { createElement: () => ({}), addEventListener: () => {} };

const require = createRequire(import.meta.url);
const Alpine = require("alpinejs").default;
const morphExports = require("@alpinejs/morph");

test("the committed browser bundle exactly matches its TypeScript source", async () => {
  const output = await build(citryClientBuildOptions({ write: false, outfile: undefined }));
  const committed = readFileSync(
    new URL("../../../py/citry/citry/ext/events/client/citry-events.js", import.meta.url),
    "utf8",
  );
  assert.equal(output.outputFiles.length, 1);
  assert.equal(output.outputFiles[0].text, committed);
});

test("the pinned Alpine directive handler is instrumented exactly", () => {
  const source = readFileSync(new URL("../node_modules/alpinejs/src/directives.js", import.meta.url), "utf8");
  const instrumented = instrumentAlpineDirectives(source);

  assert.ok(instrumented.includes("runCitryAmbientDirective(el, directive.original, utilities.cleanup, handler)"));
  assert.ok(instrumented.includes("() => handler.inline(el, directive, utilities)"));
  assert.notEqual(instrumented, source);
});

test("the Alpine and morph pins are exact", () => {
  assert.equal(Alpine.version, EXPECTED_VERSION);
  assert.equal(require("alpinejs/package.json").version, EXPECTED_VERSION);
  assert.equal(require("@alpinejs/morph/package.json").version, EXPECTED_VERSION);
});

test("the private scope APIs the runtime calls exist", () => {
  // Scope projection uses addScopeToNode and _x_dataStack. Delayed fragment
  // roots use Alpine's _x_ignore marker and initTree entry point. This is the
  // tripwire for a version drifting the callable APIs.
  assert.equal(typeof Alpine.addScopeToNode, "function");
  assert.equal(typeof Alpine.closestDataStack, "function");
  assert.equal(typeof Alpine.mergeProxies, "function");
  assert.equal(typeof Alpine.onElRemoved, "function");
  assert.equal(typeof Alpine.walk, "function");
  assert.equal(typeof Alpine.closestRoot, "function");
  assert.equal(typeof Alpine.initTree, "function");
  assert.equal(typeof Alpine.cloneNode, "function");
  // Public companions the boot sequence relies on. interceptInit is the
  // undocumented-but-stable hook (Livewire rides it too) that lets the
  // runtime attach an instance's scope from inside Alpine's own init walk.
  assert.equal(typeof Alpine.addRootSelector, "function");
  assert.equal(typeof Alpine.interceptInit, "function");
  assert.equal(typeof Alpine.onAttributeRemoved, "function");
  assert.equal(typeof Alpine.reactive, "function");
  assert.equal(typeof Alpine.magic, "function");
  assert.equal(typeof Alpine.plugin, "function");
  assert.equal(typeof Alpine.evaluateRaw, "function");
  assert.equal(typeof Alpine.effect, "function");
  assert.equal(typeof Alpine.release, "function");
  assert.equal(typeof Alpine.directive, "function");
  assert.equal(typeof Alpine.start, "function");
});

test("the lifecycle, magic, listener, and morph internals retain their pinned shape", () => {
  const lifecycleSource = readFileSync(new URL("../node_modules/alpinejs/src/lifecycle.js", import.meta.url), "utf8");
  const directivesSource = readFileSync(new URL("../node_modules/alpinejs/src/directives.js", import.meta.url), "utf8");
  const mutationSource = readFileSync(new URL("../node_modules/alpinejs/src/mutation.js", import.meta.url), "utf8");
  const forSource = readFileSync(new URL("../node_modules/alpinejs/src/directives/x-for.js", import.meta.url), "utf8");
  const showSource = readFileSync(
    new URL("../node_modules/alpinejs/src/directives/x-show.js", import.meta.url),
    "utf8",
  );
  const onSource = readFileSync(new URL("../node_modules/alpinejs/src/utils/on.js", import.meta.url), "utf8");
  const refsSource = readFileSync(new URL("../node_modules/alpinejs/src/magics/$refs.js", import.meta.url), "utf8");
  const idSource = readFileSync(new URL("../node_modules/alpinejs/src/magics/$id.js", import.meta.url), "utf8");
  const morphSource = readFileSync(new URL("../node_modules/@alpinejs/morph/src/morph.js", import.meta.url), "utf8");
  const morphIndexSource = readFileSync(
    new URL("../node_modules/@alpinejs/morph/src/index.js", import.meta.url),
    "utf8",
  );

  assert.ok(lifecycleSource.includes("intercept(el, skip)"));
  assert.ok(lifecycleSource.includes("if (el._x_marker) return"));
  assert.ok(lifecycleSource.includes("el._x_marker = markerDispenser++"));
  assert.ok(lifecycleSource.includes("delete el._x_marker"));
  assert.ok(lifecycleSource.includes("if (el._x_teleportBack)"));
  assert.ok(directivesSource.includes("el._x_ignore || el._x_ignoreSelf"));
  assert.ok(directivesSource.includes("onAttributeRemoved(el, directive.original, cleanup)"));
  assert.ok(directivesSource.includes(".sort(byPriority)"));
  assert.ok(directivesSource.includes("let directiveOrder = ["));
  assert.ok(directivesSource.includes("'data',"));
  assert.ok(directivesSource.includes("'init',"));
  assert.ok(mutationSource.includes("cleanupAttributes(el, attrs)"));
  assert.ok(forSource.includes("el._x_refreshXForScope(scope)"));
  assert.ok(forSource.includes("clone._x_refreshXForScope"));
  assert.ok(showSource.includes("el._x_isShown = false"));
  assert.ok(showSource.includes("el._x_isShown = true"));
  assert.ok(onSource.includes("el._x_isShown === false"));
  assert.ok(onSource.includes("e.target._x_pendingModelUpdates"));
  assert.ok(refsSource.includes("el._x_refs_proxy"));
  assert.ok(idSource.includes("el._x_id"));
  assert.ok(morphIndexSource.includes("Alpine.morphBetween = morphBetween"));
  assert.ok(morphSource.includes("from._x_isShown"));
  assert.ok(morphSource.includes("from._x_transition"));
});

test("the slot adapter's scope, structural, and teleport internals retain their pinned shape", () => {
  const directivesSource = readFileSync(new URL("../node_modules/alpinejs/src/directives.js", import.meta.url), "utf8");
  const ifSource = readFileSync(new URL("../node_modules/alpinejs/src/directives/x-if.js", import.meta.url), "utf8");
  const forSource = readFileSync(new URL("../node_modules/alpinejs/src/directives/x-for.js", import.meta.url), "utf8");
  const teleportSource = readFileSync(
    new URL("../node_modules/alpinejs/src/directives/x-teleport.js", import.meta.url),
    "utf8",
  );
  assert.ok(directivesSource.includes("handler.inline && handler.inline"));
  assert.ok(directivesSource.includes("'ref'"));
  assert.ok(ifSource.includes("el.content.cloneNode(true).firstElementChild"));
  assert.ok(forSource.includes("document.importNode(templateEl.content, true).firstElementChild"));
  assert.ok(teleportSource.includes("clone._x_teleportBack = el"));
  assert.ok(teleportSource.includes("el._x_teleport = clone"));
});

test("addScopeToNode writes the node's _x_dataStack with the scope first", () => {
  // Citry retains same-root local layers and then installs the component
  // scope explicitly. This assertion protects addScopeToNode's cleanup and
  // stack-shape contract, which that projection builds on.
  const node = { parentNode: null };
  const scope = { probe: 1 };
  const cleanup = Alpine.addScopeToNode(node, scope);
  assert.ok(Array.isArray(node._x_dataStack));
  assert.equal(node._x_dataStack[0], scope);
  assert.equal(typeof cleanup, "function");
  cleanup();
  assert.deepEqual(node._x_dataStack, []);
});

test("initTree still honors the private _x_ignore hold before walking", () => {
  const lifecycleSource = readFileSync(new URL("../node_modules/alpinejs/src/lifecycle.js", import.meta.url), "utf8");
  assert.ok(lifecycleSource.includes("findClosest(el, i => i._x_ignore)"));
});

test("the morph package's named export is the plugin installer (spike F1)", () => {
  // `import { morph } from "@alpinejs/morph"` binds the INSTALLER, not the
  // raw morph function; the runtime must register the plugin and use
  // Alpine.morph. The CJS build carries the same two exports, so the
  // identity is checked functionally here, and the ESM dist (the file the
  // bundle embeds) is pinned by its export block below.
  assert.equal(morphExports.default, morphExports.morph);
  assert.equal(typeof morphExports.default, "function");
  Alpine.plugin(morphExports.default);
  assert.equal(typeof Alpine.morph, "function");
  assert.notEqual(Alpine.morph, morphExports.default);
  assert.equal(typeof Alpine.morphBetween, "function");

  const esmSource = readFileSync(require.resolve("@alpinejs/morph/dist/module.esm.js"), "utf8");
  assert.ok(esmSource.includes("module_default as default"));
  assert.ok(esmSource.includes("src_default as morph"));
});

test("morph's Alpine bridge still resolves window.Alpine.cloneNode", () => {
  // The bridge (spike F3) is why scope survival through a morph is free: the
  // patch initializes incoming nodes through Alpine.cloneNode. It is wired
  // by source, not by API, so the canary checks the shipped source text.
  const esmSource = readFileSync(require.resolve("@alpinejs/morph/dist/module.esm.js"), "utf8");
  assert.ok(esmSource.includes("window.Alpine.cloneNode"));
});
