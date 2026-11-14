import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import test from "node:test";
import vm from "node:vm";

// These tests cover the guarantees of issue 145: a component script reports whether it ran to its
// end, and `onServerRender` callbacks run in one order (children before their parent, siblings in
// the order they mounted) after the first mount and after a server render. They load the real
// client.js into a bare context with a Vue stand-in and call the hooks the way Vue does.
const source = await readFile(new URL("../../../py/citry/citry/_vue/client.js", import.meta.url), "utf8");
const helperContract = source.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];
const RealVue = createRequire(import.meta.url)("vue");

function vueStub() {
  return {
    reactive: (value) => value,
    shallowRef: (value) => ({ value }),
    nextTick: async () => {},
    // A callback runs inside an effect scope that ends with the component.
    effectScope: () => ({ run: (fn) => fn(), stop() {} }),
    defineComponent: (options) => options,
    createVNode() {},
    createTextVNode() {},
    resolveDirective: (name) => name,
    vModelCheckbox: {},
    vModelDynamic: {},
    vModelRadio: {},
    vModelSelect: {},
    vModelText: {},
  };
}

// Loads a fresh copy of client.js. `extra` adds globals to the context, such as `reportError`.
function load(extra = {}) {
  const context = {
    CitryVueFragments: { installFragmentManager() {} },
    document: { currentScript: null },
    queueMicrotask,
    console: { error() {}, warn() {} },
    Vue: vueStub(),
    ...extra,
  };
  context.globalThis = context;
  context.window = context;
  context.structuredClone = (value) => {
    context.__cloneJson = JSON.stringify(value);
    return vm.runInNewContext("JSON.parse(__cloneJson)", context);
  };
  vm.runInNewContext(source, context);
  const render = vm.runInNewContext("(function () {})", context);
  return {
    context,
    citryRuntime: context.__citryRuntime,
    // Copies a value into the client's own realm, as the browser does for parsed JSON.
    realm(value) {
      context.__json = JSON.stringify(value);
      return vm.runInNewContext("JSON.parse(__json)", context);
    },
    definition(value) {
      const result = this.realm(value);
      result.render = render;
      return result;
    },
  };
}

const KEY = "a".repeat(64);

// ---------------------------------------------------------------------------
// finishScript
// ---------------------------------------------------------------------------

test("finishScript reports a script that threw to the page, and a clean finish reports nothing", () => {
  const reported = [];
  const { citryRuntime } = load({ reportError: (error) => reported.push(error) });
  citryRuntime.finishScript(KEY);
  // The wrapper in the served script caught the error, so the browser never reported it. Without
  // this call the page's `error` event and any error monitor would never see the failure.
  assert.deepEqual(reported, [], "a script that ran to its end is not an error");
  const failure = new Error("boom");
  citryRuntime.finishScript("b".repeat(64), failure);
  assert.deepEqual(reported, [failure]);
});

test("finishScript throws the error on a microtask when the page has no reportError", () => {
  const queued = [];
  const { citryRuntime } = load({ queueMicrotask: (task) => queued.push(task) });
  const failure = new Error("boom");
  // Not every browser global has `reportError`. The fallback still ends in an uncaught error,
  // which is what the page's `error` event listens for. A real microtask would crash this test
  // process, so the stand-in holds the task and the test runs it.
  citryRuntime.finishScript(KEY, failure);
  assert.equal(queued.length, 1);
  assert.throws(queued[0], (error) => error === failure);
});

test("finishScript rejects a key that is not 64 lowercase hex characters", () => {
  const { citryRuntime } = load({ reportError() {} });
  // A script cannot choose which entry it writes to, so only a digest-shaped key is accepted.
  for (const bad of [undefined, 1, "", "a".repeat(63), "a".repeat(65), "A".repeat(64), "g".repeat(64), "__proto__"]) {
    assert.throws(() => citryRuntime.finishScript(bad), /invalid component script key/, String(bad));
  }
});

// ---------------------------------------------------------------------------
// finishKey on a prepared script asset, and the standalone finish check
// ---------------------------------------------------------------------------

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

// Starts a prepared app on a standalone page (the browser already ran every script tag) whose
// manifest lists `scripts`. Startup stops at the first check that fails, so the tests read which
// check that was from the error. A start that gets past the script checks stops at the Vue mount.
async function startWith(scripts, setup = () => {}) {
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
  const fixture = load({
    // A failed script is reported again; the stand-in keeps that from ending this test process.
    reportError() {},
    Element,
    Node: class {},
    location: { assign() {} },
    history: { state: null },
    btoa,
    URL,
    CustomEvent: class {},
    setTimeout,
    clearTimeout,
    document: {
      URL: "https://example.test/page",
      baseURI: "https://example.test/page",
      currentScript: null,
      dispatchEvent() {},
      addEventListener() {},
      removeEventListener() {},
      createElement() {
        throw new Error("STOP AT LOAD");
      },
    },
  });
  fixture.context.Vue = { ...vueStub(), ...RealVue, createApp: () => app, createSSRApp: () => app };
  setup(fixture);
  const asset = { id: "definition", url: "/definitions/abc.js", sha256: "0".repeat(64), ...METADATA };
  const loaded = fixture.realm(METADATA);
  loaded.render = vm.runInNewContext("(function () {})", fixture.context);
  fixture.context.__citryRuntimeDefinitions = { [asset.id]: loaded };
  const configuration = fixture.realm({
    manifest: {
      protocol: "citry-vue-prepared/1",
      appId: "script-app",
      revision: 0,
      rootId: "root",
      markers: [],
      scripts,
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
  return fixture.citryRuntime.startPrepared(configuration);
}

function componentScript(overrides = {}) {
  return {
    owner: { kind: "component", typeKey: "Root" },
    source: { kind: "owned", url: "https://example.test/a.js", sha256: "1".repeat(64) },
    lazyAllowed: false,
    registersOptions: true,
    finishKey: KEY,
    ...overrides,
  };
}

test("a manifest script entry accepts a finishKey on a component script the server owns", async () => {
  // The script never reported, so the start fails on the finish check. Reaching that check at all
  // shows the entry's shape was accepted.
  await assert.rejects(
    startWith([componentScript()]),
    /Citry Vue component script did not run to its end \(it may have failed to parse\): Root/,
  );
});

test("a manifest script entry rejects a finishKey that is not 64 lowercase hex characters", async () => {
  for (const finishKey of ["not-hex", "A".repeat(64), "a".repeat(63), 7]) {
    await assert.rejects(
      startWith([componentScript({ finishKey })]),
      /invalid prepared script asset/,
      String(finishKey),
    );
  }
});

test("a manifest script entry rejects a finishKey on an extension script", async () => {
  // Only the server's own wrapper on a component's `js` reports a finish, so an extension script
  // cannot claim a key and mask a failure under it.
  await assert.rejects(
    startWith([componentScript({ owner: { kind: "extension", extensionName: "ext" }, registersOptions: false })]),
    /invalid prepared script asset/,
  );
});

test("a manifest script entry rejects a finishKey on an external source", async () => {
  // An external file is not served with the wrapper, so its key could never be reported.
  await assert.rejects(
    startWith([componentScript({ source: { kind: "external", url: "https://cdn.test/a.js", attrs: {} } })]),
    /invalid prepared script asset/,
  );
});

test("a component script that threw stops standalone startup with its own error as the cause", async () => {
  const failure = new Error("script bug");
  await assert.rejects(
    startWith([componentScript()], (fixture) => {
      // The server's wrapper calls this when the script throws, before startup reads the result.
      fixture.citryRuntime.finishScript(KEY, failure);
    }),
    (error) => {
      assert.match(error.message, /Citry Vue component script threw while it ran: Root/);
      assert.equal(error.cause, failure);
      return true;
    },
  );
});

test("the finish check runs before the registration check, so a script error is not hidden", async () => {
  // A script that throws before `$component()` also registers nothing. The thrown error says more
  // than the missing registration, so it must win.
  const rejection = await startWith([componentScript()], (fixture) => {
    fixture.citryRuntime.finishScript(KEY, new Error("script bug"));
  }).catch((error) => error);
  assert.doesNotMatch(rejection.message, /were not emitted before bootstrap/);
  // And a script that finished cleanly but registered nothing reaches the registration check.
  await assert.rejects(
    startWith([componentScript()], (fixture) => {
      fixture.citryRuntime.finishScript(KEY);
    }),
    /initial Citry Vue type Options were not emitted before bootstrap/,
  );
});

// ---------------------------------------------------------------------------
// onServerRender callback order
// ---------------------------------------------------------------------------

// The occurrence for `id` in `tree` (a map from id to parent id). A parent names each child in its
// call table, which is how the browser checks that the components it mounts match the server's.
function occurrence(tree, id) {
  const calls = {};
  for (const child of Object.keys(tree).filter((other) => tree[other] === id)) {
    calls["call-" + child] = { id: child, key: child, parentId: id };
  }
  return {
    id,
    typeKey: "T-" + id,
    definitionId: "def-" + id,
    parentId: tree[id],
    placementKey: tree[id] === null ? null : id,
    serverData: {},
    preparedData: { calls, callRuns: {} },
  };
}

// The definition for `id`: it declares one local call for each child that its occurrence names.
function definitionFor(fixture, tree, id) {
  const localCalls = Object.keys(tree)
    .filter((other) => tree[other] === id)
    .map((child) => ({
      localId: "call-" + child,
      typeKey: "T-" + child,
      componentTag: "citry-" + child,
      bindings: [],
    }));
  return fixture.definition({
    target: "ordinary-vnodes/1",
    helperContract,
    directiveSignature: [],
    replacementSites: [],
    localCalls,
    localCallRuns: [],
    opaqueHtmlSites: [],
    runtimeEventSites: [],
  });
}

// A page of components named by `tree`, a map from id to parent id (null for the root). Each
// component gets its own Vue type whose `onServerRender` appends its id to `order`, or throws when
// `setup.throwIn` names it. `mountOrder` is the order Vue's `mounted` hooks run in; a component that
// is left out is created but never mounted. A component named in `viaPlain` has a plain Vue
// component (one Citry did not create) between it and its parent, as a third-party wrapper would.
function page(tree, mountOrder, { throwIn = null, viaPlain = [] } = {}) {
  const fixture = load();
  const { citryRuntime } = fixture;
  const appId = "order-app";
  const ids = Object.keys(tree);
  const rootId = ids.find((id) => tree[id] === null);
  citryRuntime.configure(
    fixture.realm({
      protocol: "citry-vue-prepared/1",
      appId,
      revision: 0,
      rootId,
      markers: [],
      occurrences: ids.map((id) => occurrence(tree, id)),
    }),
  );
  const setup = {
    fixture,
    citryRuntime,
    appId,
    app: citryRuntime._apps.get(appId),
    order: [],
    throwIn,
    rootId,
    ids,
    tree,
  };
  const types = {};
  const instances = {};
  for (const id of ids) {
    citryRuntime.registerDefinition(appId, "def-" + id, definitionFor(fixture, tree, id));
    types[id] = citryRuntime.defineType(appId, "T-" + id, {
      onServerRender() {
        setup.order.push(id);
        if (id === setup.throwIn) throw new Error("callback of " + id + " failed");
      },
    });
  }
  // Vue creates a parent before its children, so create in the order of the tree.
  const created = new Set();
  const create = (id) => {
    if (created.has(id)) return;
    if (tree[id] !== null) create(tree[id]);
    created.add(id);
    const parent = tree[id] === null ? null : instances[tree[id]];
    // `$options` is the type, as in Vue, so the coordinator finds the type's callback on it.
    instances[id] = {
      $parent: viaPlain.includes(id) ? { $parent: parent } : parent,
      $options: types[id],
      citryId: id,
    };
    types[id].beforeCreate.call(instances[id]);
    types[id].created.call(instances[id]);
  };
  ids.forEach(create);
  setup.types = types;
  setup.instances = instances;
  setup.mountAll = () => {
    for (const id of mountOrder) types[id].mounted.call(instances[id]);
  };
  // The first mount runs its own callbacks. A test about a later server render clears them first,
  // so `order` holds only what that render ran.
  setup.settleFirstMount = async () => {
    setup.mountAll();
    await citryRuntime.whenReady(appId);
    setup.order.length = 0;
  };
  return setup;
}

// A response that lists `updatedIds` in the given order and leaves every occurrence as it was.
function envelope(setup, updatedIds, { subtreeRoot = null } = {}) {
  const { fixture, ids, tree, app } = setup;
  const rootId = subtreeRoot ?? setup.rootId;
  // A subtree response holds only the target and its descendants, and the target has no parent in it.
  const inSubtree = (id) => id === rootId || (tree[id] !== null && inSubtree(tree[id]));
  const shown = subtreeRoot === null ? ids : ids.filter(inSubtree);
  return fixture.realm({
    protocol: "citry-vue-prepared/1",
    appId: setup.appId,
    baseRevision: app.revision,
    revision: app.revision + 1,
    rootId,
    markers: [],
    scripts: [],
    styles: [],
    typePolicies: [],
    definitions: [],
    occurrences: shown.map((id) => ({
      ...occurrence(tree, id),
      ...(id === rootId ? { parentId: null, placementKey: null } : {}),
    })),
    updatedIds,
  });
}

test("a server render runs sibling callbacks in mount order, whatever order the response lists them", async () => {
  // b mounts before a, as when a keyed list or a Teleport moves a's element ahead of b's.
  const setup = page({ root: null, a: "root", b: "root" }, ["b", "a", "root"]);
  await setup.settleFirstMount();
  // The response lists a before b. If the response order decided, a would run first.
  await setup.citryRuntime.applyEnvelope(setup.appId, envelope(setup, ["root", "a", "b"]));
  assert.deepEqual(setup.order, ["b", "a", "root"]);
});

test("a server render runs every descendant callback before its ancestor's", async () => {
  // The grandchild mounts first, as Vue mounts children before their parent.
  const setup = page({ root: null, a: "root", a1: "a", b: "root" }, ["a1", "a", "b", "root"]);
  await setup.settleFirstMount();
  // The response puts parents first, the opposite of the order the callbacks must run in.
  await setup.citryRuntime.applyEnvelope(setup.appId, envelope(setup, ["root", "a", "a1", "b"]));
  assert.deepEqual(setup.order, ["a1", "a", "b", "root"]);
});

test("the parent links decide, not raw mount order, which of two related components runs first", async () => {
  // Vue never mounts a parent before its child, but the walk must not rely on that: here the
  // parent has the lower mount index, and its child still runs first.
  const setup = page({ root: null, a: "root" }, ["root", "a"]);
  await setup.settleFirstMount();
  await setup.citryRuntime.applyEnvelope(setup.appId, envelope(setup, ["root", "a"]));
  assert.deepEqual(setup.order, ["a", "root"]);
});

test("a component under a plain Vue wrapper is ordered under its nearest Citry ancestor", async () => {
  // leaf's Vue parent is a component Citry did not create, so it has no callback in the pass. leaf
  // hangs from root, whose children are [sib, leaf] by mount. If leaf were treated as the start of
  // its own walk instead, it would run before sib.
  const setup = page({ root: null, sib: "root", leaf: "root" }, ["sib", "leaf", "root"], { viaPlain: ["leaf"] });
  await setup.settleFirstMount();
  await setup.citryRuntime.applyEnvelope(setup.appId, envelope(setup, ["root", "sib", "leaf"]));
  assert.deepEqual(setup.order, ["sib", "leaf", "root"]);
});

test("a server render of one subtree orders only its components, whose ancestors are not in the pass", async () => {
  // The response re-renders a and its child. root and b are kept, so they run no callback, and
  // the walk must start at a without looking for a parent that is not in the pass.
  const setup = page({ root: null, a: "root", a1: "a", b: "root" }, ["a1", "a", "b", "root"]);
  await setup.settleFirstMount();
  await setup.citryRuntime.applyEnvelope(setup.appId, envelope(setup, ["a", "a1"], { subtreeRoot: "a" }), "a");
  assert.deepEqual(setup.order, ["a1", "a"]);
});

test("a callback that throws stops the later callbacks and the app, and the server render rejects", async () => {
  const setup = page({ root: null, a: "root", b: "root" }, ["a", "b", "root"]);
  await setup.settleFirstMount();
  setup.throwIn = "a";
  await assert.rejects(
    setup.citryRuntime.applyEnvelope(setup.appId, envelope(setup, ["root", "a", "b"])),
    /callback of a failed/,
  );
  // b and root were next in line; neither ran after a failed.
  assert.deepEqual(setup.order, ["a"]);
  assert.equal(setup.app.terminal, true);
});

test("a server render fails with the component's name when its mounted hook never ran", async () => {
  // b was created but never mounted, so it has no place in the order. Running it in a guessed
  // position would hide the bug, so the render stops and names it.
  const setup = page({ root: null, a: "root", b: "root" }, ["a", "root"]);
  await setup.settleFirstMount();
  await assert.rejects(
    setup.citryRuntime.applyEnvelope(setup.appId, envelope(setup, ["root", "a", "b"])),
    /never mounted: T-b \(b\)/,
  );
  // The order is worked out before the first callback runs, so none of them ran.
  assert.deepEqual(setup.order, []);
  assert.equal(setup.app.terminal, true);
});

// ---------------------------------------------------------------------------
// onServerRender callbacks of the first mount
// ---------------------------------------------------------------------------

test("the first mount runs callbacks children first and siblings in mount order", async () => {
  const setup = page({ root: null, a: "root", a1: "a", b: "root" }, ["b", "a1", "a", "root"]);
  setup.mountAll();
  await setup.citryRuntime.whenReady(setup.appId);
  // b mounted before a's subtree here, so it runs first among root's children; a1 precedes a.
  assert.deepEqual(setup.order, ["b", "a1", "a", "root"]);
});

test("a first-mount callback that throws stops the remaining callbacks and fails startup", async () => {
  const setup = page({ root: null, a: "root", b: "root" }, ["a", "b", "root"], { throwIn: "a" });
  setup.mountAll();
  await assert.rejects(setup.citryRuntime.whenReady(setup.appId), /callback of a failed/);
  assert.deepEqual(setup.order, ["a"]);
  assert.equal(setup.app.terminal, true);
  assert.equal(setup.app.initialError.message, "callback of a failed");
});

test("the first mount orders callbacks by the parent links, not by the order the hooks ran", async () => {
  // Vue never runs a parent's `mounted` before its child's, but the order must come from the tree
  // and not depend on that: here root's hook ran first, and its child's callback still goes first.
  const setup = page({ root: null, a: "root" }, ["root", "a"]);
  setup.mountAll();
  await setup.citryRuntime.whenReady(setup.appId);
  assert.deepEqual(setup.order, ["a", "root"]);
});

test("a component that mounts after a failed first mount runs no callback", async () => {
  const setup = page({ root: null, a: "root", b: "root" }, ["a", "root"], { throwIn: "a" });
  setup.mountAll();
  await assert.rejects(setup.citryRuntime.whenReady(setup.appId), /callback of a failed/);
  // A browser-only `v-if` shows b after the app already stopped. Its pass must not start work on
  // an app that is shutting down.
  setup.types.b.mounted.call(setup.instances.b);
  await assert.rejects(setup.citryRuntime.whenReady(setup.appId), /callback of a failed/);
  assert.deepEqual(setup.order, ["a"]);
});
