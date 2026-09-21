import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const source = await readFile(new URL("../../../py/citry/citry/_vue/client.js", import.meta.url), "utf8");
const helperContract = source.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];

function runtime() {
  const document = {
    currentScript: null,
    dispatched: [],
    addEventListener() {},
    removeEventListener() {},
    dispatchEvent(event) {
      this.dispatched.push(event);
      return true;
    },
  };
  const context = {
    CitryVueFragments: { installFragmentManager() {} },
    document,
    location: { assign() {} },
    history: { state: null, pushState() {}, replaceState() {} },
    queueMicrotask,
    btoa,
    Vue: {
      reactive: (value) => value,
      shallowRef: (value) => ({ value }),
      defineComponent: (value) => value,
      resolveDirective: (name) => name,
      vModelCheckbox: {},
      vModelDynamic: {},
      vModelRadio: {},
      vModelSelect: {},
      vModelText: {},
    },
  };
  context.globalThis = context;
  context.window = context;
  context.structuredClone = (value) => {
    context.__cloneJson = JSON.stringify(value);
    return vm.runInNewContext("JSON.parse(__cloneJson)", context);
  };
  vm.runInNewContext(source, context);

  const realm = (value) => {
    context.__json = JSON.stringify(value);
    return vm.runInNewContext("JSON.parse(__json)", context);
  };
  const render = vm.runInNewContext("(function () {})", context);
  const stable = context.CitryStable;
  return {
    stable,
    realm,
    document,
    publicEvents: context.Citry.events,
    definition() {
      const definition = realm({
        render,
        target: "ordinary-vnodes/1",
        helperContract,
        dynamicElements: [],
        directiveSignature: [],
        replacementSites: [],
        localCalls: [],
        localCallRuns: [],
        opaqueHtmlSites: [],
        runtimeEventSites: [],
      });
      definition.render = render;
      return definition;
    },
  };
}

test("public applyActions validates the complete list before any targetless action runs", async () => {
  const fixture = runtime();
  await assert.rejects(
    fixture.publicEvents.applyActions(
      fixture.realm([
        { action: "event", eventName: "before-invalid" },
        { action: "event", eventName: "after-invalid", unexpected: true },
      ]),
    ),
    /unknown field|invalid action/i,
  );
  assert.equal(fixture.document.dispatched.length, 0);
});

const runtimeSpec = (id, overrides = {}) => ({
  id,
  event: "click",
  handler: "save",
  args: null,
  prevent: false,
  stop: false,
  self: false,
  once: false,
  key: null,
  debounce: null,
  throttle: null,
  ...overrides,
});

function ownerFor(eventBindings, declaredHandlers = ["save"]) {
  const fixture = runtime();
  const { stable, realm } = fixture;
  const eventHandlers = Object.fromEntries(declaredHandlers.map((name) => [name, { httpMethod: "POST" }]));
  stable.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "runtime-events",
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
          preparedData: { calls: {}, callRuns: {}, eventBindings },
          eventContext: {
            serverRenderId: "server-root",
            stateToken: null,
            publicState: {},
            componentClassId: "Root_1",
            descriptor: { componentClassId: "Root_1", eventHandlers },
          },
        },
      ],
    }),
  );
  stable.registerDefinition("runtime-events", "root-definition", fixture.definition());
  const type = stable.defineType("runtime-events", "Root", {});
  const instance = { citryId: "root" };
  type.beforeCreate.call(instance);
  return { instance, app: stable._apps.get("runtime-events") };
}

test("runtime event tables return immutable authenticated handles for declared handlers", () => {
  const id = "citryRuntimeEvent012abc";
  const { instance } = ownerFor({ [id]: runtimeSpec(id) });

  const handles = instance.$citryEvents.runtimeEvents(id);

  assert.equal(handles.length, 1);
  assert.equal(handles[0].id, id);
  assert.equal(handles[0].spec.handler, "save");
  assert.equal(handles[0].record.occurrenceId, "root");
  assert.equal(Object.isFrozen(handles), true);
  assert.equal(Object.isFrozen(handles[0]), true);
});

test("runtime event validation rejects malformed and forged ids and specs as one list", () => {
  const validId = "citryRuntimeEvent012abc";
  const malformed = [
    ["authored id substitution", "citryEvent012abc", runtimeSpec("citryEvent012abc")],
    ["non-hex runtime id", "citryRuntimeEventnothex", runtimeSpec("citryRuntimeEventnothex")],
    [
      "missing field",
      validId,
      Object.fromEntries(Object.entries(runtimeSpec(validId)).filter(([key]) => key !== "once")),
    ],
    ["extra field", validId, runtimeSpec(validId, { unexpected: true })],
    ["argument expression", validId, runtimeSpec(validId, { args: "globalThis.__ran = true" })],
    ["wrong event type", validId, runtimeSpec(validId, { event: 7 })],
    ["empty event", validId, runtimeSpec(validId, { event: "" })],
    ["wrong handler type", validId, runtimeSpec(validId, { handler: 7 })],
    ["unknown handler", validId, runtimeSpec(validId, { handler: "missing" })],
    ["wrong prevent type", validId, runtimeSpec(validId, { prevent: 1 })],
    ["wrong stop type", validId, runtimeSpec(validId, { stop: "false" })],
    ["wrong self type", validId, runtimeSpec(validId, { self: null })],
    ["wrong once type", validId, runtimeSpec(validId, { once: 0 })],
    ["wrong key type", validId, runtimeSpec(validId, { key: 3 })],
    ["empty key", validId, runtimeSpec(validId, { key: "" })],
    ["negative debounce", validId, runtimeSpec(validId, { debounce: -1 })],
    ["unsafe debounce", validId, runtimeSpec(validId, { debounce: Number.MAX_SAFE_INTEGER + 1 })],
    ["fractional throttle", validId, runtimeSpec(validId, { throttle: 0.5 })],
  ];

  for (const [label, id, spec] of malformed) {
    const { instance } = ownerFor({ [id]: spec });
    const message = /^citryRuntimeEvent[0-9a-f]+$/.test(id) ? /missing, stale, or invalid/ : /invalid kind/;
    assert.throws(() => instance.$citryEvents.runtimeEvents(id), message, label);
  }

  const invalidId = "citryRuntimeEvent987fed";
  const { instance } = ownerFor({
    [validId]: runtimeSpec(validId),
    [invalidId]: runtimeSpec(invalidId, { args: "globalThis.__ran = true" }),
  });
  assert.throws(
    () => instance.$citryEvents.runtimeEvents(`${validId},${invalidId}`),
    /missing, stale, or invalid/,
    "a later invalid handle rejects the whole list after an earlier valid spec",
  );

  const combined = runtimeSpec(validId, { debounce: 1, throttle: 1 });
  const { instance: combinedInstance } = ownerFor({ [validId]: combined });
  assert.equal(JSON.stringify(combinedInstance.$citryEvents.runtimeEvents(validId)[0].spec), JSON.stringify(combined));
});

test("runtime event tables reject invalid ids before resolving specs and reject duplicate ids", () => {
  const id = "citryRuntimeEvent012abc";
  const { instance } = ownerFor({ [id]: runtimeSpec(id) });

  assert.throws(() => instance.$citryEvents.runtimeEvents("citryRuntimeEvent012abz"), /invalid kind/);
  assert.throws(() => instance.$citryEvents.runtimeEvents(`${id},${id}`), /duplicated/);
});

test("applyEnvelope rejects invalid runtime-site references before publishing the revision", async () => {
  const fixture = runtime();
  const { stable, realm } = fixture;
  stable.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "runtime-event-preflight",
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
          serverData: { count: 3 },
          preparedData: { calls: {}, callRuns: {} },
        },
      ],
    }),
  );
  stable.registerDefinition("runtime-event-preflight", "root-definition", fixture.definition());

  const app = stable._apps.get("runtime-event-preflight");
  const before = {
    revision: app.revision,
    snapshot: app.snapshot.value,
    occurrences: app.occurrences,
    definitions: app.definitions,
    liveOccurrence: app.occurrences.get("root"),
    serverData: app.snapshot.value.get("root").serverData,
    mounted: app.mounted,
  };
  const siteId = "citryDirective012abcD0";
  const nextRoot = {
    id: "root",
    typeKey: "Root",
    definitionId: "runtime-event-definition",
    parentId: null,
    placementKey: null,
    serverData: { count: 4 },
    preparedData: {
      calls: {},
      callRuns: {},
      citryRuntimeEvents0: "citryRuntimeEventnothex",
    },
  };
  const asset = {
    id: "runtime-event-definition",
    url: "/runtime-event-definition.mjs",
    sha256: "0".repeat(64),
    target: "ordinary-vnodes/1",
    helperContract,
    dynamicElements: [],
    directiveSignature: [{ siteId, name: "v-citry-runtime-events", arg: null, modifiers: [] }],
    replacementSites: [],
    localCalls: [],
    localCallRuns: [],
    opaqueHtmlSites: [],
    runtimeEventSites: [{ siteId, bindingKey: "citryRuntimeEvents0", steps: [] }],
  };

  await assert.rejects(
    stable.applyEnvelope(
      "runtime-event-preflight",
      realm({
        protocol: "citry-vue-prepared/1",
        appId: "runtime-event-preflight",
        baseRevision: 0,
        revision: 1,
        rootId: "root",
        markers: [],
        definitions: [asset],
        occurrences: [nextRoot],
        updatedIds: ["root"],
        replacements: [],
      }),
      "root",
    ),
    /runtime event site references invalid or duplicate ids/,
  );

  assert.equal(app.busy, false);
  assert.equal(app.revision, before.revision);
  assert.equal(app.snapshot.value, before.snapshot);
  assert.equal(app.occurrences, before.occurrences);
  assert.equal(app.definitions, before.definitions);
  assert.equal(app.occurrences.get("root"), before.liveOccurrence);
  assert.equal(app.snapshot.value.get("root").serverData, before.serverData);
  assert.deepEqual(JSON.parse(JSON.stringify(before.serverData)), { count: 3 });
  assert.equal(app.mounted, before.mounted);
  assert.equal(app.mounted.size, 0);
});

test("runtime event routes allow one binding key at distinct paths and reject exact duplicates", () => {
  const fixture = runtime();
  const { stable, realm } = fixture;
  stable.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "runtime-event-route-identity",
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

  const eachRoute = {
    siteId: "citryDirective012abcD0",
    bindingKey: "citryRuntimeEvents0",
    steps: [{ kind: "each", key: "citryLoop0" }],
  };
  const branchEachRoute = {
    siteId: "citryDirective012abdD1",
    bindingKey: "citryRuntimeEvents0",
    steps: [
      { kind: "branch", key: "citryIf0", index: 0 },
      { kind: "each", key: "citryLoop0" },
    ],
  };
  const definitionFor = (runtimeEventSites) => {
    const definition = fixture.definition();
    definition.runtimeEventSites = realm(runtimeEventSites);
    definition.directiveSignature = realm(
      runtimeEventSites.map(({ siteId }) => ({
        siteId,
        name: "v-citry-runtime-events",
        arg: null,
        modifiers: [],
      })),
    );
    return definition;
  };

  stable.registerDefinition(
    "runtime-event-route-identity",
    "distinct-paths",
    definitionFor([eachRoute, branchEachRoute]),
  );
  assert.equal(stable._apps.get("runtime-event-route-identity").definitions.size, 1);

  assert.throws(
    () =>
      stable.registerDefinition(
        "runtime-event-route-identity",
        "duplicate-path",
        definitionFor([eachRoute, { ...eachRoute, siteId: "citryDirective012abeD2" }]),
      ),
    /runtime event site route and binding key are duplicated/,
  );
  assert.equal(stable._apps.get("runtime-event-route-identity").definitions.size, 1);
});

test("runtime event definition matching ignores JSON object key order but rejects route changes", () => {
  const fixture = runtime();
  const { stable, realm } = fixture;
  const appId = "runtime-event-definition-order";
  stable.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId,
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

  const siteId = "citryDirective012abdD1";
  const siteFor = (step) => ({ siteId, bindingKey: "citryRuntimeEvents0", steps: [step] });
  const definitionFor = (runtimeEventSite) => {
    const definition = fixture.definition();
    definition.runtimeEventSites = realm([runtimeEventSite]);
    definition.directiveSignature = realm([{ siteId, name: "v-citry-runtime-events", arg: null, modifiers: [] }]);
    return definition;
  };
  const declared = definitionFor(siteFor({ kind: "each", key: "citryLoop0" }));
  const loadedWithDifferentJsonOrder = definitionFor(siteFor({ key: "citryLoop0", kind: "each" }));

  assert.doesNotThrow(() => stable.registerDefinition(appId, "matching-route", loadedWithDifferentJsonOrder, declared));
  assert.throws(
    () =>
      stable.registerDefinition(
        appId,
        "changed-route",
        definitionFor(siteFor({ kind: "each", key: "citryLoop1" })),
        declared,
      ),
    /loaded definition metadata does not match its prepared declaration/,
  );
});
