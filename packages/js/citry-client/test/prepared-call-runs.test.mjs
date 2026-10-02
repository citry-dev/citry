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

function runtime({ nextTick, vue = {} } = {}) {
  const context = {
    CitryVueFragments: { installFragmentManager() {} },
    document: { currentScript: null },
    queueMicrotask,
    Vue: vueStub(nextTick === undefined ? vue : { ...vue, nextTick }),
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

// A component-changing Render (#164) keeps the occurrence ID and gives it another component. These
// fixtures start from Parent (the app's top-level component) calling Form under the ID "target".
function componentChangingFixture({ mountForm = true } = {}) {
  let flush;
  const fixture = runtime({
    nextTick: async () => {
      if (flush) await flush();
    },
  });
  const { citryRuntime, realm } = fixture;
  const appId = "component-change";
  citryRuntime.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId,
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [
        occurrence("root", "Parent", "parent-def", null, { form: { id: "target", key: "target", parentId: "root" } }),
        occurrence("target", "Form", "form-def", "root"),
      ],
    }),
  );
  citryRuntime.registerDefinition(
    appId,
    "parent-def",
    replacementDefinition(fixture, [], [ordinary("form", "Form", "citry-form")]),
  );
  citryRuntime.registerDefinition(appId, "form-def", replacementDefinition(fixture));
  citryRuntime.registerDefinition(appId, "done-def", replacementDefinition(fixture));
  const app = citryRuntime._apps.get(appId);
  const registered = [];
  app.vueApp = { component: (tag, type) => registered.push([tag, type]) };
  const Parent = citryRuntime.defineType(appId, "Parent", {});
  const Form = citryRuntime.defineType(appId, "Form", {});
  let forcedUpdates = 0;
  const rootInstance = {
    $parent: null,
    $options: {},
    citryId: "root",
    $forceUpdate() {
      forcedUpdates += 1;
    },
  };
  Parent.beforeCreate.call(rootInstance);
  Parent.created.call(rootInstance);
  const formInstance = { $parent: rootInstance, $options: {}, citryId: "target" };
  if (mountForm) {
    Form.beforeCreate.call(formInstance);
    Form.created.call(formInstance);
  }
  return {
    fixture,
    citryRuntime,
    realm,
    appId,
    app,
    registered,
    forcedUpdates: () => forcedUpdates,
    // Vue swaps the instance only when the caller renders again; the stub does it on the next tick.
    remountTargetAs(typeKey) {
      flush = async () => {
        flush = undefined;
        if (mountForm) Form.beforeUnmount.call(formInstance);
        const type = app.types.get(typeKey);
        const next = { $parent: rootInstance, $options: {}, citryId: "target" };
        type.beforeCreate.call(next);
        type.created.call(next);
        type.mounted.call(next);
      };
    },
    envelope(occurrences, updatedIds, definitions = []) {
      return realm({
        protocol: "citry-vue-prepared/1",
        appId,
        baseRevision: app.revision,
        revision: app.revision + 1,
        rootId: occurrences[0].id,
        markers: [],
        scripts: [],
        styles: [],
        typePolicies: [],
        definitions,
        occurrences,
        updatedIds,
      });
    },
  };
}

test("a Render may give a nested component another component while its kept caller names the old one", async () => {
  const setup = componentChangingFixture();
  const { citryRuntime, appId, app } = setup;
  const priorGeneration = app.mounted.get("target").record.generation;
  setup.remountTargetAs("Done");

  // The Render's own envelope holds only the new component; the caller is kept unchanged.
  await citryRuntime.applyEnvelope(
    appId,
    setup.envelope([occurrence("target", "Done", "done-def", null)], ["target"]),
    "target",
  );

  assert.equal(app.revision, 1);
  assert.equal(app.occurrences.get("target").typeKey, "Done");
  assert.equal(app.occurrences.get("target").parentId, "root");
  // The kept caller still names Form, so the browser remembers the replacement.
  assert.deepEqual([...app.replacedTypeIds], ["target"]);
  // No template calls Done by tag, so its Vue type is registered without one.
  assert.deepEqual([...app.untaggedTypes], ["Done"]);
  assert.deepEqual(setup.registered, []);
  // The caller renders again to build the new component's VNode, and the old instance is replaced.
  assert.equal(setup.forcedUpdates(), 1);
  assert.equal(app.mounted.get("target").record.generation, priorGeneration + 1);
});

test("a component change is rejected for a component the server did not list as updated", async () => {
  // Only a component the server rendered in this response may arrive with another component. A
  // response that updates several targets at once is checked as a whole page, which is where an
  // unlisted component can appear.
  const setup = componentChangingFixture();
  const { citryRuntime, appId, app } = setup;
  await assert.rejects(
    citryRuntime.applyEnvelope(
      appId,
      setup.envelope(
        [
          occurrence("root", "Parent", "parent-def", null, { form: { id: "target", key: "target", parentId: "root" } }),
          occurrence("target", "Done", "done-def", "root"),
        ],
        [],
      ),
      "root",
      { combined: true, activate() {}, callbackOwnerIds: [] },
    ),
    /changed the component of an occurrence it did not update/,
  );
  assert.equal(app.revision, 0);
  assert.equal(app.occurrences.get("target").typeKey, "Form");
});

test("a component change is rejected for the app's top-level component", async () => {
  const setup = componentChangingFixture();
  const { citryRuntime, appId, app } = setup;
  citryRuntime.registerDefinition(appId, "other-root-def", setup.fixture.definition(definition()));
  await assert.rejects(
    citryRuntime.applyEnvelope(
      appId,
      setup.envelope([occurrence("root", "OtherRoot", "other-root-def", null)], ["root"]),
      "root",
    ),
    /changed the component of the app's top-level component/,
  );
  assert.equal(app.occurrences.get("root").typeKey, "Parent");
});

test("a caller the server renders again must name its child's new component", async () => {
  // The server wrote this caller's call table in the same response, so a Form declaration for a
  // Done child is a malformed response, not a replacement.
  const setup = componentChangingFixture();
  const { citryRuntime, appId, app } = setup;
  await assert.rejects(
    citryRuntime.applyEnvelope(
      appId,
      setup.envelope(
        [
          occurrence("root", "Parent", "parent-def", null, { form: { id: "target", key: "target", parentId: "root" } }),
          occurrence("target", "Done", "done-def", "root"),
        ],
        ["root", "target"],
      ),
      "root",
    ),
    /stable-type mismatch/,
  );
  assert.equal(app.revision, 0);
  assert.deepEqual([...app.replacedTypeIds], []);
});

test("a component change below the Render target follows the target's new call table", async () => {
  // The Render targets Panel. Panel's child changes component inside the same response, and Panel's
  // new call table names the new component, so the change is ordinary and leaves no replacement.
  const fixture = runtime();
  const { citryRuntime, realm } = fixture;
  const appId = "nested-change";
  citryRuntime.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId,
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [
        occurrence("root", "Parent", "parent-def", null, { panel: { id: "panel", key: "panel", parentId: "root" } }),
        occurrence("panel", "Panel", "panel-form-def", "root", {
          inner: { id: "inner", key: "inner", parentId: "panel" },
        }),
        occurrence("inner", "Form", "form-def", "panel"),
      ],
    }),
  );
  citryRuntime.registerDefinition(
    appId,
    "parent-def",
    replacementDefinition(fixture, [], [ordinary("panel", "Panel", "citry-panel")]),
  );
  citryRuntime.registerDefinition(
    appId,
    "panel-form-def",
    replacementDefinition(fixture, [], [ordinary("inner", "Form", "citry-form")]),
  );
  citryRuntime.registerDefinition(
    appId,
    "panel-done-def",
    replacementDefinition(fixture, [], [ordinary("inner", "Done", "citry-done")]),
  );
  citryRuntime.registerDefinition(appId, "form-def", replacementDefinition(fixture));
  citryRuntime.registerDefinition(appId, "done-def", replacementDefinition(fixture));
  const app = citryRuntime._apps.get(appId);
  const registered = [];
  app.vueApp = { component: (tag) => registered.push(tag) };
  const [Parent] = ["Parent", "Panel", "Form"].map((typeKey) => citryRuntime.defineType(appId, typeKey, {}));
  // Only the top-level component is mounted; the commit requires it.
  const rootInstance = { $parent: null, $options: {}, citryId: "root", $forceUpdate() {} };
  Parent.beforeCreate.call(rootInstance);
  Parent.created.call(rootInstance);

  await citryRuntime.applyEnvelope(
    appId,
    realm({
      protocol: "citry-vue-prepared/1",
      appId,
      baseRevision: 0,
      revision: 1,
      rootId: "panel",
      markers: [],
      scripts: [],
      styles: [],
      typePolicies: [],
      definitions: [],
      occurrences: [
        occurrence("panel", "Panel", "panel-done-def", null, {
          inner: { id: "inner", key: "inner", parentId: "panel" },
        }),
        occurrence("inner", "Done", "done-def", "panel"),
      ],
      updatedIds: ["panel", "inner"],
    }),
    "panel",
  );

  assert.equal(app.occurrences.get("inner").typeKey, "Done");
  // Panel's template calls Done by tag now, so the tag is registered and nothing stays replaced.
  assert.deepEqual(registered, ["citry-done"]);
  assert.deepEqual([...app.replacedTypeIds], []);
  assert.deepEqual([...app.untaggedTypes], []);
});

test("a replacement-only component gets its tag once a later caller names it", async () => {
  const setup = componentChangingFixture({ mountForm: false });
  const { citryRuntime, appId, app, fixture } = setup;
  await citryRuntime.applyEnvelope(
    appId,
    setup.envelope([occurrence("target", "Done", "done-def", null)], ["target"]),
    "target",
  );
  const doneType = app.types.get("Done");
  assert.deepEqual([...app.untaggedTypes], ["Done"]);

  // The server renders the caller again, and its new template calls Done by tag.
  citryRuntime.registerDefinition(
    appId,
    "parent-done-def",
    replacementDefinition(fixture, [], [ordinary("done", "Done", "citry-done")]),
  );
  await citryRuntime.applyEnvelope(
    appId,
    setup.envelope(
      [
        occurrence("root", "Parent", "parent-done-def", null, {
          done: { id: "target", key: "target", parentId: "root" },
        }),
        occurrence("target", "Done", "done-def", "root"),
      ],
      ["root", "target"],
    ),
    "root",
  );

  // The Vue type stays the same object, so a mounted Done instance stays valid under its new tag.
  assert.deepEqual(setup.registered, [["citry-done", doneType]]);
  assert.deepEqual([...app.untaggedTypes], []);
  // The caller now names Done itself, so the occurrence is no longer a replacement.
  assert.deepEqual([...app.replacedTypeIds], []);
});

test("$component() options that Citry cannot check fail with a message naming the fix", () => {
  const { citryRuntime, realm } = runtime();
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
  // A mixin hides names from the js_data clash check, so the type is rejected.
  assert.throws(
    () => citryRuntime.defineType("app", "Card_abc123", { mixins: [{}] }),
    /\$component\(\) options for Card_abc123 use mixins.*Define those data, methods, and computed values directly/,
  );
  assert.throws(
    () => citryRuntime.defineType("app", "Card_abc124", { extends: {} }),
    /\$component\(\) options for Card_abc124 use extends/,
  );
  // An Events helper name is taken; the message says which option to rename.
  assert.throws(
    () => citryRuntime.defineType("app", "Card_abc125", { methods: { $loading() {} } }),
    /\$component\(\) options for Card_abc125 define "\$loading", a name Citry's event helpers/,
  );
});

test("a custom directive nobody registered stops the render with the component's name", () => {
  // Vue's production build returns nothing for an unknown directive; this stub does the same.
  const directives = { tooltip: { mounted() {} } };
  let instance = { type: { name: "OrderPanel" }, proxy: {}, ctx: {} };
  const { citryRuntime } = runtime({
    vue: {
      resolveDirective: (name) => directives[name],
      getCurrentInstance: () => instance,
    },
  });
  const { compilerRuntime } = citryRuntime;

  // A registered directive, global or local, resolves to what Vue found.
  assert.equal(compilerRuntime.resolveDirective("tooltip"), directives.tooltip);
  // A component Citry rendered is named by its type key (the browser test covers that); without
  // Citry's record for the instance, the Vue name stands in.
  assert.throws(() => compilerRuntime.resolveDirective("tooltipp"), {
    message:
      "Component OrderPanel uses the directive 'v-tooltipp', but no directive named 'tooltipp' " +
      "is registered, so Vue would skip it. Register it in the component's `directives` option in its " +
      "$component() options, or for every component with Citry.vue.use(plugin), where the plugin's " +
      'install(app) calls app.directive("tooltipp", ...).',
  });
  instance = null;
  assert.throws(() => compilerRuntime.resolveDirective("focus"), /Component \(unknown\) uses the directive 'v-focus'/);
});
