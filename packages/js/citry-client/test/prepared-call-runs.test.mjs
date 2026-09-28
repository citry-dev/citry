import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const source = await readFile(new URL("../../../py/citry/citry/_vue/client.js", import.meta.url), "utf8");
const helperContract = source.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];

function vueStub(overrides = {}) {
  return {
    reactive: (value) => value,
    shallowRef: (value) => ({ value }),
    nextTick: async () => {},
    defineComponent: (options) => options,
    createVNode() {},
    createTextVNode() {},
    resolveDirective: (name) => name,
    vModelCheckbox: {},
    vModelDynamic: {},
    vModelRadio: {},
    vModelSelect: {},
    vModelText: {},
    ...overrides,
  };
}

function runtime({ nextTick } = {}) {
  const context = {
    CitryVueFragments: { installFragmentManager() {} },
    document: { currentScript: null },
    queueMicrotask,
    Vue: vueStub(nextTick === undefined ? {} : { nextTick }),
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
    citryRuntime: context.__citryRuntime,
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

test("the coordinator exposes its exact bundled Vue namespace as Citry.vue", () => {
  const context = {
    CitryVueFragments: { installFragmentManager() {} },
    document: { currentScript: null },
    queueMicrotask,
    Vue: vueStub(),
  };
  context.globalThis = context;
  context.window = context;
  context.structuredClone = structuredClone;
  vm.runInNewContext(source, context);
  assert.equal(context.Citry.vue, context.Vue);
  assert.equal(Object.getOwnPropertyDescriptor(context.Citry, "vue").writable, false);
});

function occurrence(id, typeKey, definitionId, parentId, calls = {}, callRuns = {}) {
  return {
    id,
    typeKey,
    definitionId,
    parentId,
    placementKey: parentId === null ? null : id,
    serverData: {},
    preparedData: { calls, callRuns },
  };
}

function occurrenceWithoutRuns(id, typeKey, definitionId, parentId, calls = {}) {
  return {
    id,
    typeKey,
    definitionId,
    parentId,
    placementKey: parentId === null ? null : id,
    serverData: {},
    preparedData: { calls },
  };
}

function definition(localCallRuns = [], replacementSites = [], localCalls = [], render = () => {}) {
  return {
    render,
    target: "ordinary-vnodes/1",
    helperContract,
    directiveSignature: [],
    replacementSites,
    localCalls: localCalls.map((call) => ({ ...call, bindings: call.bindings ?? [] })),
    localCallRuns,
    opaqueHtmlSites: [],
    runtimeEventSites: [],
  };
}

function run(runId, typeKey, componentTag) {
  return {
    runId,
    typeKey,
    componentTag,
    sourceStart: 1,
    sourceEnd: 2,
    loopSourceStart: 1,
    loopSourceEnd: 2,
    collectionExpression: "$citryPrepared.callRuns." + runId,
    idExpression: "citryOccurrenceId",
    keyExpression: "citryOccurrenceId",
  };
}

function ordinary(localId, typeKey, componentTag) {
  return { localId, typeKey, componentTag };
}

test("prepared bootstrap requires an explicit marker array", () => {
  const fixture = runtime();

  assert.throws(
    () =>
      fixture.citryRuntime.configure(
        fixture.realm({
          protocol: "citry-vue-prepared/1",
          appId: "missing-markers",
          revision: 0,
          rootId: "root",
          occurrences: [occurrence("root", "Root", "root-def", null)],
        }),
      ),
    /prepared markers must be an array/,
  );
});

test("prepared call runs exactly partition local calls by declared stable type", () => {
  const fixture = runtime();
  const { citryRuntime, realm } = fixture;
  citryRuntime.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "app",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [
        occurrence("root", "Parent", "parent-def", null, {}, { first: ["child-a"], second: ["child-b"] }),
        occurrence("child-a", "Child", "child-def", "root"),
        occurrence("child-b", "Child", "child-def", "root"),
      ],
    }),
  );
  citryRuntime.registerDefinition("app", "child-def", fixture.definition(definition()));
  citryRuntime.registerDefinition(
    "app",
    "parent-def",
    fixture.definition(definition([run("first", "Child", "citry-child"), run("second", "Child", "citry-child")])),
  );
});

test("callRuns may be absent only when the definition declares no runs", () => {
  const fixture = runtime();
  const { citryRuntime, realm } = fixture;
  citryRuntime.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "app",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [occurrenceWithoutRuns("root", "Parent", "parent-def", null)],
    }),
  );
  citryRuntime.registerDefinition("app", "parent-def", fixture.definition(definition()));

  const missing = runtime();
  missing.citryRuntime.configure(
    missing.realm({
      protocol: "citry-vue-prepared/1",
      appId: "app",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [occurrenceWithoutRuns("root", "Parent", "parent-def", null)],
    }),
  );
  assert.throws(
    () =>
      missing.citryRuntime.registerDefinition(
        "app",
        "parent-def",
        missing.definition(definition([run("items", "Child", "citry-child")])),
      ),
    /do not match definition declarations/,
  );
});

test("ordinary declarations and call-run members jointly partition mixed local calls", () => {
  const fixture = runtime();
  const { citryRuntime, realm } = fixture;
  citryRuntime.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "app",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [
        occurrence(
          "root",
          "Parent",
          "parent-def",
          null,
          {
            fixed: { id: "fixed-child", key: "fixed", parentId: "root" },
          },
          { items: ["run-child"] },
        ),
        occurrence("fixed-child", "Child", "child-def", "root"),
        occurrence("run-child", "Child", "child-def", "root"),
      ],
    }),
  );
  citryRuntime.registerDefinition("app", "child-def", fixture.definition(definition()));
  citryRuntime.registerDefinition(
    "app",
    "parent-def",
    fixture.definition(
      definition([run("items", "Child", "citry-child")], [], [ordinary("fixed", "Child", "citry-child")]),
    ),
  );
});

test("ordinary slot-fill calls retain a physical parent distinct from their lexical owner", () => {
  const fixture = runtime();
  const { citryRuntime, realm } = fixture;
  citryRuntime.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "app",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [
        occurrence("root", "Parent", "parent-def", null, {
          receiver: { id: "receiver", key: "receiver", parentId: "root" },
          fill: { id: "fill", key: "fill", parentId: "receiver" },
        }),
        occurrence("receiver", "Receiver", "receiver-def", "root"),
        occurrence("fill", "Fill", "fill-def", "receiver"),
      ],
    }),
  );
  citryRuntime.registerDefinition("app", "receiver-def", fixture.definition(definition()));
  citryRuntime.registerDefinition("app", "fill-def", fixture.definition(definition()));
  citryRuntime.registerDefinition(
    "app",
    "parent-def",
    fixture.definition(
      definition([], [], [ordinary("receiver", "Receiver", "citry-receiver"), ordinary("fill", "Fill", "citry-fill")]),
    ),
  );
});

for (const [name, callRuns, error] of [
  ["unknown run", { first: ["child-a"], second: ["child-b"], third: [] }, /do not match definition/],
]) {
  test(`prepared call runs reject ${name}`, () => {
    const fixture = runtime();
    const { citryRuntime, realm } = fixture;
    citryRuntime.configure(
      realm({
        protocol: "citry-vue-prepared/1",
        appId: "app",
        revision: 0,
        rootId: "root",
        markers: [],
        occurrences: [
          occurrence(
            "root",
            "Parent",
            "parent-def",
            null,
            {},
            {
              first: ["child-a"],
              second: ["child-b"],
            },
          ),
          occurrence("child-a", "Child", "child-def", "root"),
          occurrence("child-b", "Child", "child-def", "root"),
        ],
      }),
    );
    // Retained occurrences are frozen, so swap in a malformed copy rather than editing one.
    const occurrences = citryRuntime._apps.get("app").occurrences;
    const root = occurrences.get("root");
    occurrences.set("root", { ...root, preparedData: { ...root.preparedData, callRuns: realm(callRuns) } });
    assert.throws(
      () =>
        citryRuntime.registerDefinition(
          "app",
          "parent-def",
          fixture.definition(definition([run("first", "Child", "citry-child"), run("second", "Child", "citry-child")])),
        ),
      error,
    );
  });
}

for (const [name, callRuns, error] of [
  ["omitted child", { items: ["child-a"] }, /no local call binding/],
  ["duplicate child", { items: ["child-a", "child-a", "child-b"] }, /does not match occurrence placement/],
]) {
  test(`prepared graph rejects a run with an ${name}`, () => {
    const fixture = runtime();
    assert.throws(
      () =>
        fixture.citryRuntime.configure(
          fixture.realm({
            protocol: "citry-vue-prepared/1",
            appId: "app",
            revision: 0,
            rootId: "root",
            markers: [],
            occurrences: [
              occurrence("root", "Parent", "parent-def", null, {}, callRuns),
              occurrence("child-a", "Child", "child-def", "root"),
              occurrence("child-b", "Child", "child-def", "root"),
            ],
          }),
        ),
      error,
    );
  });
}

test("replacement sites reference declared call runs", () => {
  const fixture = runtime();
  const { citryRuntime, realm } = fixture;
  citryRuntime.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "app",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [occurrence("root", "Parent", "parent-def", null)],
    }),
  );
  assert.throws(
    () =>
      citryRuntime.registerDefinition(
        "app",
        "parent-def",
        fixture.definition(
          definition([], [{ siteId: "site", key: "key", localDescendants: [], localDescendantRuns: ["missing"] }]),
        ),
      ),
    /unknown local call run/,
  );
});

function replacementDefinition(fixture, sites, localCalls = []) {
  return fixture.definition(definition([], sites, localCalls));
}

function replacementSite(siteId, key, localDescendants = [], localDescendantRuns = []) {
  return { siteId, key, localDescendants, localDescendantRuns };
}

// Both keyed sites change, and the inner one sits inside the outer one, so the browser derives the
// shared child from each of them. It must remount the child once and skip the unmounted sibling.
test("nested changed replacement sites remount their shared mounted descendant once", async () => {
  let flush;
  const fixture = runtime({
    nextTick: async () => {
      if (flush) await flush();
    },
  });
  const { citryRuntime, realm } = fixture;
  const appId = "nested-sites";
  citryRuntime.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId,
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [
        occurrence("root", "Root", "root-old", null, {
          child: { id: "child", key: "child", parentId: "root" },
          sibling: { id: "sibling", key: "sibling", parentId: "root" },
        }),
        occurrence("child", "Child", "child-def", "root"),
        occurrence("sibling", "Sibling", "sibling-def", "root"),
      ],
    }),
  );
  citryRuntime.registerDefinition(
    appId,
    "root-old",
    replacementDefinition(
      fixture,
      [replacementSite("site-a", "inner-old", ["child"]), replacementSite("site-z", "outer-old", ["child", "sibling"])],
      [ordinary("child", "Child", "citry-child"), ordinary("sibling", "Sibling", "citry-sibling")],
    ),
  );
  citryRuntime.registerDefinition(
    appId,
    "root-new",
    replacementDefinition(
      fixture,
      [replacementSite("site-a", "inner-new", ["child"]), replacementSite("site-z", "outer-new", ["child", "sibling"])],
      [ordinary("child", "Child", "citry-child"), ordinary("sibling", "Sibling", "citry-sibling")],
    ),
  );
  citryRuntime.registerDefinition(appId, "child-def", replacementDefinition(fixture));
  citryRuntime.registerDefinition(appId, "sibling-def", replacementDefinition(fixture));
  const app = citryRuntime._apps.get(appId);
  const Root = citryRuntime.defineType(appId, "Root", {});
  const Child = citryRuntime.defineType(appId, "Child", {});
  citryRuntime.defineType(appId, "Sibling", {});
  const rootInstance = { $parent: null, $options: {}, citryId: "root" };
  Root.beforeCreate.call(rootInstance);
  Root.created.call(rootInstance);
  const childInstance = { $parent: rootInstance, $options: {}, citryId: "child" };
  Child.beforeCreate.call(childInstance);
  Child.created.call(childInstance);
  // Only the child is mounted, so a remount expected for the sibling would fail the commit.
  const priorGeneration = app.mounted.get("child").record.generation;
  // Vue replaces the child a single time, however many changed sites name it.
  let remounted = false;
  flush = async () => {
    if (remounted) return;
    remounted = true;
    Child.beforeUnmount.call(childInstance);
    const nextChild = { $parent: rootInstance, $options: {}, citryId: "child" };
    Child.beforeCreate.call(nextChild);
    Child.created.call(nextChild);
    Child.mounted.call(nextChild);
  };

  await citryRuntime.applyEnvelope(
    appId,
    realm({
      protocol: "citry-vue-prepared/1",
      appId,
      baseRevision: 0,
      revision: 1,
      rootId: "root",
      markers: [],
      scripts: [],
      styles: [],
      typePolicies: [],
      definitions: [],
      occurrences: [
        occurrence("root", "Root", "root-new", null, {
          child: { id: "child", key: "child", parentId: "root" },
          sibling: { id: "sibling", key: "sibling", parentId: "root" },
        }),
        occurrence("child", "Child", "child-def", "root"),
        occurrence("sibling", "Sibling", "sibling-def", "root"),
      ],
      updatedIds: ["root", "child", "sibling"],
    }),
  );

  assert.equal(app.revision, 1);
  assert.equal(app.mounted.get("child").record.generation, priorGeneration + 1);
  assert.equal(app.mounted.get("root").record.generation, 1);
  // The sibling was never mounted, so the update must not have mounted it either.
  assert.equal(app.mounted.has("sibling"), false);
});

test("one definition cannot bind a component tag to two stable types", () => {
  const fixture = runtime();
  const { citryRuntime, realm } = fixture;
  citryRuntime.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "app",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [occurrence("root", "Parent", "parent-def", null)],
    }),
  );
  assert.throws(
    () =>
      citryRuntime.registerDefinition(
        "app",
        "parent-def",
        fixture.definition(definition([run("a", "First", "citry-child"), run("b", "Second", "citry-child")])),
      ),
    /component tag stable-type mismatch/,
  );
  assert.equal(citryRuntime._apps.get("app").definitions.size, 0);
});

test("ordinary and run declarations cannot bind one component tag to different types across definitions", () => {
  const fixture = runtime();
  const { citryRuntime, realm } = fixture;
  citryRuntime.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "app",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [occurrence("root", "Parent", "root-def", null)],
    }),
  );
  citryRuntime.registerDefinition(
    "app",
    "first-def",
    fixture.definition(definition([], [], [ordinary("fixed", "First", "citry-child")])),
  );
  assert.throws(
    () =>
      citryRuntime.registerDefinition(
        "app",
        "second-def",
        fixture.definition(definition([run("items", "Second", "citry-child")])),
      ),
    /component tag stable-type mismatch/,
  );
});

test("rejected call-run registration leaves registries unchanged and permits a corrected retry", () => {
  const fixture = runtime();
  const { citryRuntime, realm } = fixture;
  citryRuntime.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "app",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [
        occurrence("root", "Parent", "parent-def", null, {}, { items: ["child"] }),
        occurrence("child", "Child", "child-def", "root"),
      ],
    }),
  );
  const app = citryRuntime._apps.get("app");
  const invalid = fixture.definition(definition([run("items", "Wrong", "citry-child")]));
  assert.throws(
    () => citryRuntime.registerDefinition("app", "parent-def", invalid),
    /stable-type or ownership mismatch/,
  );
  assert.equal(app.definitions.size, 0);
  assert.equal(app.callRunTags.size, 0);
  const compiled = fixture.definition(definition([run("items", "Child", "citry-child")]));
  citryRuntime.registerDefinition("app", "parent-def", compiled);
  assert.equal(app.definitions.size, 1);
  assert.equal(app.callRunTags.get("citry-child"), "Child");
});

test("self-target subtree expansion restores the mounted target placement", async () => {
  const fixture = runtime();
  const { citryRuntime, realm } = fixture;
  citryRuntime.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "app",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [
        occurrence("root", "Parent", "parent-def", null, { child: { id: "target", key: "target", parentId: "root" } }),
        occurrence("target", "Child", "child-def", "root"),
      ],
    }),
  );
  citryRuntime.registerDefinition(
    "app",
    "parent-def",
    fixture.definition(definition([], [], [ordinary("child", "Child", "citry-child")])),
  );
  citryRuntime.registerDefinition("app", "child-def", fixture.definition(definition()));

  const app = citryRuntime._apps.get("app");
  app.types.set("Parent", {});
  app.types.set("Child", {});
  const rootLive = app.snapshot.value.get("root");
  app.mounted.set("root", {
    component: { $parent: null, $options: {} },
    record: {
      callbackScope: undefined,
      callbackCleanup: undefined,
      serverKeys: new Set(),
      live: { value: rootLive },
      definition: { value: { id: "parent-def", render() {}, cache: [] } },
    },
  });

  const isolatedTarget = occurrence("target", "Child", "child-def", null);
  isolatedTarget.serverData = { revision: 1 };
  await citryRuntime.applyEnvelope(
    "app",
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "app",
      baseRevision: 0,
      revision: 1,
      rootId: "target",
      markers: [],
      scripts: [],
      styles: [],
      typePolicies: [],
      definitions: [],
      occurrences: [isolatedTarget],
      updatedIds: ["target"],
    }),
    "target",
  );

  assert.equal(app.revision, 1);
  assert.equal(app.occurrences.get("target").parentId, "root");
  assert.equal(app.occurrences.get("target").placementKey, "target");
  assert.deepEqual(JSON.parse(JSON.stringify(app.occurrences.get("target").serverData)), { revision: 1 });
});
