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
    stable: context.CitryStable,
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
    collectionExpression: "preparedData.callRuns." + runId,
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
      fixture.stable.configure(
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
  const { stable, realm } = fixture;
  stable.configure(
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
  stable.registerDefinition("app", "child-def", fixture.definition(definition()));
  stable.registerDefinition(
    "app",
    "parent-def",
    fixture.definition(definition([run("first", "Child", "citry-child"), run("second", "Child", "citry-child")])),
  );
});

test("callRuns may be absent only when the definition declares no runs", () => {
  const fixture = runtime();
  const { stable, realm } = fixture;
  stable.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "app",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [occurrenceWithoutRuns("root", "Parent", "parent-def", null)],
    }),
  );
  stable.registerDefinition("app", "parent-def", fixture.definition(definition()));

  const missing = runtime();
  missing.stable.configure(
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
      missing.stable.registerDefinition(
        "app",
        "parent-def",
        missing.definition(definition([run("items", "Child", "citry-child")])),
      ),
    /do not match definition declarations/,
  );
});

test("ordinary declarations and call-run members jointly partition mixed local calls", () => {
  const fixture = runtime();
  const { stable, realm } = fixture;
  stable.configure(
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
  stable.registerDefinition("app", "child-def", fixture.definition(definition()));
  stable.registerDefinition(
    "app",
    "parent-def",
    fixture.definition(
      definition([run("items", "Child", "citry-child")], [], [ordinary("fixed", "Child", "citry-child")]),
    ),
  );
});

test("ordinary slot-fill calls retain a physical parent distinct from their lexical owner", () => {
  const fixture = runtime();
  const { stable, realm } = fixture;
  stable.configure(
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
  stable.registerDefinition("app", "receiver-def", fixture.definition(definition()));
  stable.registerDefinition("app", "fill-def", fixture.definition(definition()));
  stable.registerDefinition(
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
    const { stable, realm } = fixture;
    stable.configure(
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
    stable._apps.get("app").occurrences.get("root").preparedData.callRuns = realm(callRuns);
    assert.throws(
      () =>
        stable.registerDefinition(
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
        fixture.stable.configure(
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
  const { stable, realm } = fixture;
  stable.configure(
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
      stable.registerDefinition(
        "app",
        "parent-def",
        fixture.definition(
          definition([], [{ siteId: "site", key: "key", localDescendants: [], localDescendantRuns: ["missing"] }]),
        ),
      ),
    /unknown local call run/,
  );
});

function keyedReplacementDefinition(fixture, key) {
  return fixture.definition(
    definition(
      [],
      [
        {
          siteId: "site",
          key,
          localDescendants: ["child"],
          localDescendantRuns: [],
        },
      ],
      [ordinary("child", "Child", "citry-child")],
    ),
  );
}

function replacementDefinition(fixture, sites, localCalls = []) {
  return fixture.definition(definition([], sites, localCalls));
}

function replacementSite(siteId, key, localDescendants = [], localDescendantRuns = []) {
  return { siteId, key, localDescendants, localDescendantRuns };
}

function mountedRoot(app, definitionId = "root-old") {
  const live = app.snapshot.value.get("root");
  app.mounted.set("root", {
    component: { $parent: null, $options: {} },
    record: {
      app,
      occurrenceId: "root",
      parentId: null,
      generation: 1,
      callbackScope: undefined,
      callbackCleanup: undefined,
      serverKeys: new Set(),
      live: { value: live },
      definition: { value: { id: definitionId, render() {}, cache: [] } },
    },
  });
}

function multiOwnerRevision(appId) {
  const fixture = runtime();
  const { stable, realm } = fixture;
  stable.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId,
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [
        occurrence("root", "Root", "root-def", null, {
          z: { id: "owner-z", key: "z", parentId: "root" },
          a: { id: "owner-a", key: "a", parentId: "root" },
        }),
        occurrence("owner-z", "OwnerZ", "owner-z-old", "root"),
        occurrence("owner-a", "OwnerA", "owner-a-old", "root"),
      ],
    }),
  );
  stable.registerDefinition(
    appId,
    "root-def",
    replacementDefinition(
      fixture,
      [],
      [ordinary("z", "OwnerZ", "citry-owner-z"), ordinary("a", "OwnerA", "citry-owner-a")],
    ),
  );
  stable.registerDefinition(
    appId,
    "owner-z-old",
    replacementDefinition(fixture, [replacementSite("site-a", "z-old-a"), replacementSite("site-z", "z-old-z")]),
  );
  stable.registerDefinition(
    appId,
    "owner-z-new",
    replacementDefinition(fixture, [replacementSite("site-a", "z-new-a"), replacementSite("site-z", "z-new-z")]),
  );
  stable.registerDefinition(appId, "owner-a-old", replacementDefinition(fixture, [replacementSite("site-a", "a-old")]));
  stable.registerDefinition(appId, "owner-a-new", replacementDefinition(fixture, [replacementSite("site-a", "a-new")]));
  const app = stable._apps.get(appId);
  for (const typeKey of ["Root", "OwnerZ", "OwnerA"]) app.types.set(typeKey, {});
  mountedRoot(app, "root-def");
  return {
    fixture,
    stable,
    realm,
    app,
    envelope(replacements) {
      return realm({
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
          occurrence("root", "Root", "root-def", null, {
            z: { id: "owner-z", key: "z", parentId: "root" },
            a: { id: "owner-a", key: "a", parentId: "root" },
          }),
          // Deliberately preserve nonlexicographic occurrence traversal.
          occurrence("owner-z", "OwnerZ", "owner-z-new", "root"),
          occurrence("owner-a", "OwnerA", "owner-a-new", "root"),
        ],
        updatedIds: ["root", "owner-z", "owner-a"],
        replacements,
      });
    },
  };
}

test("replacement compatibility canonicalizes owners and sites without relaxing wire order", async () => {
  const fixture = multiOwnerRevision("replacement-order");
  const { stable, app } = fixture;
  await stable.applyEnvelope(
    "replacement-order",
    fixture.envelope([
      { ownerId: "owner-a", siteId: "site-a", expectedRemountIds: [] },
      { ownerId: "owner-z", siteId: "site-a", expectedRemountIds: [] },
      { ownerId: "owner-z", siteId: "site-z", expectedRemountIds: [] },
    ]),
  );
  assert.equal(app.revision, 1);
  assert.equal(app.occurrences.get("owner-z").definitionId, "owner-z-new");
});

test("replacement compatibility still rejects a supplied list in noncanonical order", async () => {
  const fixture = multiOwnerRevision("replacement-order-reject");
  const { stable, app } = fixture;
  await assert.rejects(
    stable.applyEnvelope(
      "replacement-order-reject",
      fixture.envelope([
        { ownerId: "owner-z", siteId: "site-a", expectedRemountIds: [] },
        { ownerId: "owner-a", siteId: "site-a", expectedRemountIds: [] },
        { ownerId: "owner-z", siteId: "site-z", expectedRemountIds: [] },
      ]),
    ),
    /replacement sites must be sorted/,
  );
  assert.equal(app.revision, 0);
});

test("nested changed sites assign an actually mounted descendant to the outer site once", async () => {
  let flush;
  const fixture = runtime({
    nextTick: async () => {
      if (flush) await flush();
    },
  });
  const { stable, realm } = fixture;
  const appId = "nested-replacements";
  stable.configure(
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
  stable.registerDefinition(
    appId,
    "root-old",
    replacementDefinition(
      fixture,
      [replacementSite("site-a", "inner-old", ["child"]), replacementSite("site-z", "outer-old", ["child", "sibling"])],
      [ordinary("child", "Child", "citry-child"), ordinary("sibling", "Sibling", "citry-sibling")],
    ),
  );
  stable.registerDefinition(
    appId,
    "root-new",
    replacementDefinition(
      fixture,
      [replacementSite("site-a", "inner-new", ["child"]), replacementSite("site-z", "outer-new", ["child", "sibling"])],
      [ordinary("child", "Child", "citry-child"), ordinary("sibling", "Sibling", "citry-sibling")],
    ),
  );
  stable.registerDefinition(appId, "child-def", replacementDefinition(fixture));
  stable.registerDefinition(appId, "sibling-def", replacementDefinition(fixture));
  const app = stable._apps.get(appId);
  const Root = stable.defineType(appId, "Root", {});
  const Child = stable.defineType(appId, "Child", {});
  stable.defineType(appId, "Sibling", {});
  const rootInstance = { $parent: null, $options: {}, citryId: "root" };
  Root.beforeCreate.call(rootInstance);
  Root.created.call(rootInstance);
  const childInstance = { $parent: rootInstance, $options: {}, citryId: "child" };
  Child.beforeCreate.call(childInstance);
  Child.created.call(childInstance);
  const priorGeneration = app.mounted.get("child").record.generation;
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

  await stable.applyEnvelope(
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
      replacements: [
        { ownerId: "root", siteId: "site-a", expectedRemountIds: [] },
        { ownerId: "root", siteId: "site-z", expectedRemountIds: ["child"] },
      ],
    }),
  );

  assert.equal(app.revision, 1);
  assert.equal(app.mounted.get("child").record.generation, priorGeneration + 1);
  assert.equal(app.mounted.get("root").record.generation, 1);
});

test("replacement declarations derive from the browser baseline without server history", async () => {
  const fixture = runtime();
  const { stable, realm } = fixture;
  stable.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "derived-replacements",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [
        occurrence("root", "Parent", "root-old", null, { child: { id: "child", key: "child", parentId: "root" } }),
        occurrence("child", "Child", "child-def", "root"),
      ],
    }),
  );
  stable.registerDefinition("derived-replacements", "child-def", fixture.definition(definition()));
  stable.registerDefinition("derived-replacements", "root-old", keyedReplacementDefinition(fixture, "old"));
  stable.registerDefinition("derived-replacements", "root-new", keyedReplacementDefinition(fixture, "new"));
  const app = stable._apps.get("derived-replacements");
  app.types.set("Parent", {});
  app.types.set("Child", {});
  mountedRoot(app);

  await stable.applyEnvelope(
    "derived-replacements",
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "derived-replacements",
      baseRevision: 0,
      revision: 1,
      rootId: "root",
      markers: [],
      scripts: [],
      styles: [],
      typePolicies: [],
      definitions: [],
      occurrences: [
        occurrence("root", "Parent", "root-new", null, { child: { id: "child", key: "child", parentId: "root" } }),
        occurrence("child", "Child", "child-def", "root"),
      ],
      updatedIds: ["child", "root"],
      replacements: [],
    }),
  );

  assert.equal(app.revision, 1);
  assert.equal(app.occurrences.get("root").definitionId, "root-new");
});

test("supplied replacement declarations must agree with browser derivation", async () => {
  const fixture = runtime();
  const { stable, realm } = fixture;
  stable.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "reject-server-history",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [
        occurrence("root", "Parent", "root-old", null, { child: { id: "child", key: "child", parentId: "root" } }),
        occurrence("child", "Child", "child-def", "root"),
      ],
    }),
  );
  stable.registerDefinition("reject-server-history", "child-def", fixture.definition(definition()));
  stable.registerDefinition("reject-server-history", "root-old", keyedReplacementDefinition(fixture, "old"));
  stable.registerDefinition("reject-server-history", "root-new", keyedReplacementDefinition(fixture, "new"));
  const app = stable._apps.get("reject-server-history");
  mountedRoot(app);

  await assert.rejects(
    stable.applyEnvelope(
      "reject-server-history",
      realm({
        protocol: "citry-vue-prepared/1",
        appId: "reject-server-history",
        baseRevision: 0,
        revision: 1,
        rootId: "root",
        markers: [],
        scripts: [],
        styles: [],
        typePolicies: [],
        definitions: [],
        occurrences: [
          occurrence("root", "Parent", "root-new", null, { child: { id: "child", key: "child", parentId: "root" } }),
          occurrence("child", "Child", "child-def", "root"),
        ],
        updatedIds: ["child", "root"],
        replacements: [{ ownerId: "root", siteId: "site", expectedRemountIds: ["child"] }],
      }),
    ),
    /client derivation/,
  );
  assert.equal(app.revision, 0);
});

test("one definition cannot bind a component tag to two stable types", () => {
  const fixture = runtime();
  const { stable, realm } = fixture;
  stable.configure(
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
      stable.registerDefinition(
        "app",
        "parent-def",
        fixture.definition(definition([run("a", "First", "citry-child"), run("b", "Second", "citry-child")])),
      ),
    /component tag stable-type mismatch/,
  );
  assert.equal(stable._apps.get("app").definitions.size, 0);
});

test("ordinary and run declarations cannot bind one component tag to different types across definitions", () => {
  const fixture = runtime();
  const { stable, realm } = fixture;
  stable.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "app",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [occurrence("root", "Parent", "root-def", null)],
    }),
  );
  stable.registerDefinition(
    "app",
    "first-def",
    fixture.definition(definition([], [], [ordinary("fixed", "First", "citry-child")])),
  );
  assert.throws(
    () =>
      stable.registerDefinition(
        "app",
        "second-def",
        fixture.definition(definition([run("items", "Second", "citry-child")])),
      ),
    /component tag stable-type mismatch/,
  );
});

test("rejected call-run registration leaves registries unchanged and permits a corrected retry", () => {
  const fixture = runtime();
  const { stable, realm } = fixture;
  stable.configure(
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
  const app = stable._apps.get("app");
  const invalid = fixture.definition(definition([run("items", "Wrong", "citry-child")]));
  assert.throws(() => stable.registerDefinition("app", "parent-def", invalid), /stable-type or ownership mismatch/);
  assert.equal(app.definitions.size, 0);
  assert.equal(app.callRunTags.size, 0);
  const compiled = fixture.definition(definition([run("items", "Child", "citry-child")]));
  stable.registerDefinition("app", "parent-def", compiled);
  assert.equal(app.definitions.size, 1);
  assert.equal(app.callRunTags.get("citry-child"), "Child");
});

test("self-target subtree expansion restores the mounted target placement", async () => {
  const fixture = runtime();
  const { stable, realm } = fixture;
  stable.configure(
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
  stable.registerDefinition(
    "app",
    "parent-def",
    fixture.definition(definition([], [], [ordinary("child", "Child", "citry-child")])),
  );
  stable.registerDefinition("app", "child-def", fixture.definition(definition()));

  const app = stable._apps.get("app");
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
  await stable.applyEnvelope(
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
      replacements: [],
    }),
    "target",
  );

  assert.equal(app.revision, 1);
  assert.equal(app.occurrences.get("target").parentId, "root");
  assert.equal(app.occurrences.get("target").placementKey, "target");
  assert.deepEqual(JSON.parse(JSON.stringify(app.occurrences.get("target").serverData)), { revision: 1 });
});
