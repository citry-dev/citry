import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const source = await readFile(new URL("../../../py/citry/citry/_vue/client.js", import.meta.url), "utf8");
const helperContract = source.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];

function runtime() {
  const context = {
    CitryVueFragments: { installFragmentManager() {} },
    document: { currentScript: null },
    queueMicrotask,
    btoa,
    Element: class Element {},
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
    element() {
      return vm.runInNewContext("new Element()", context);
    },
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

const eventSpec = (id, overrides = {}) => ({
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

const pollSpec = (id, overrides = {}) => ({
  id,
  handler: "refresh",
  args: null,
  interval: 1000,
  ...overrides,
});

function ownerFor({ eventBindings = {}, pollBindings = {}, declaredHandlers = ["refresh", "save"] } = {}) {
  const fixture = runtime();
  const { stable, realm } = fixture;
  const eventHandlers = Object.fromEntries(declaredHandlers.map((name) => [name, { httpMethod: "POST" }]));
  stable.configure(
    realm({
      protocol: "citry-vue-prepared/1",
      appId: "runtime-polls-owner",
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
          preparedData: { calls: {}, callRuns: {}, eventBindings, pollBindings },
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
  stable.registerDefinition("runtime-polls-owner", "root-definition", fixture.definition());
  const type = stable.defineType("runtime-polls-owner", "Root", {});
  const instance = { citryId: "root" };
  type.beforeCreate.call(instance);
  return { fixture, instance };
}

const SITE_ID = "citryDirective012abcD0";
const BINDING_KEY = "citryRuntimeEvents0";
const EVENT_ID = "citryRuntimeEvent012abc";
const POLL_ID = "citryRuntimePoll456def";

function runtimePollSite() {
  return { siteId: SITE_ID, bindingKey: BINDING_KEY, steps: [] };
}

function definitionAsset(runtimeEventSites = [runtimePollSite()]) {
  return {
    id: "runtime-poll-definition",
    url: "/runtime-poll-definition.mjs",
    sha256: "0".repeat(64),
    target: "ordinary-vnodes/1",
    helperContract,
    dynamicElements: [],
    directiveSignature: runtimeEventSites.map(({ siteId }) => ({
      siteId,
      name: "v-citry-runtime-events",
      arg: null,
      modifiers: [],
    })),
    replacementSites: [],
    localCalls: [],
    localCallRuns: [],
    opaqueHtmlSites: [],
    runtimeEventSites,
  };
}

function bootstrap({
  appId = "runtime-poll-bootstrap",
  selectedIds = POLL_ID,
  eventBindings = {},
  pollBindings = { [POLL_ID]: pollSpec(POLL_ID) },
  eventHandlers = ["refresh", "save"],
  serverData = {},
} = {}) {
  const eventHandlersByName = Object.fromEntries(eventHandlers.map((name) => [name, { httpMethod: "POST" }]));
  return {
    protocol: "citry-vue-prepared/1",
    appId,
    revision: 0,
    rootId: "root",
    markers: [],
    definitions: [definitionAsset()],
    occurrences: [
      {
        id: "root",
        typeKey: "Root",
        definitionId: "runtime-poll-definition",
        parentId: null,
        placementKey: null,
        serverData,
        preparedData: {
          calls: {},
          callRuns: {},
          [BINDING_KEY]: selectedIds,
          eventBindings,
          pollBindings,
        },
        eventContext: {
          serverRenderId: "server-root",
          stateToken: null,
          publicState: {},
          componentClassId: "Root_1",
          descriptor: { componentClassId: "Root_1", eventHandlers: eventHandlersByName },
        },
      },
    ],
  };
}

async function assertInitialPreflightRejects(manifest, matcher) {
  const fixture = runtime();
  const configuration = fixture.realm({ manifest, tags: {} });
  configuration.host = fixture.element();

  await assert.rejects(fixture.stable.startPrepared(configuration), matcher, manifest.appId);
  assert.equal(fixture.stable._apps.has(manifest.appId), false, "rejected initial metadata must not publish an app");
}

test("one runtime site resolves event and poll ids from their separate typed tables", () => {
  const authoredPollId = "citryPoll765432";
  const { instance } = ownerFor({
    eventBindings: { [EVENT_ID]: eventSpec(EVENT_ID) },
    pollBindings: {
      [authoredPollId]: { id: authoredPollId, handler: "refresh", args: null, interval: 5000 },
      [POLL_ID]: pollSpec(POLL_ID),
    },
  });

  const handles = instance.$citryEvents.runtimeEvents(`${EVENT_ID},${POLL_ID}`);

  assert.equal(handles.length, 2);
  assert.equal(handles[0].kind, "event");
  assert.equal(handles[0].id, EVENT_ID);
  assert.equal(handles[0].spec.handler, "save");
  assert.equal(handles[1].kind, "poll");
  assert.equal(handles[1].id, POLL_ID);
  assert.equal(handles[1].spec.handler, "refresh");
  assert.equal(handles[1].spec.args, null);
  assert.equal(Object.isFrozen(handles), true);
  assert.equal(Object.isFrozen(handles[1]), true);
});

test("runtime poll handles accept handler-only metadata and reject malformed specs", () => {
  const { instance } = ownerFor({ pollBindings: { [POLL_ID]: pollSpec(POLL_ID) } });
  const [handle] = instance.$citryEvents.runtimeEvents(POLL_ID);

  assert.equal(handle.kind, "poll");
  assert.equal(handle.spec.args, null);
  assert.equal(handle.spec.interval, 1000);

  const malformed = [
    ["argument expression", pollSpec(POLL_ID, { args: "globalThis.__ran = true" })],
    ["zero interval", pollSpec(POLL_ID, { interval: 0 })],
    ["negative interval", pollSpec(POLL_ID, { interval: -1 })],
    ["fractional interval", pollSpec(POLL_ID, { interval: 0.5 })],
    ["unsafe interval", pollSpec(POLL_ID, { interval: Number.MAX_SAFE_INTEGER + 1 })],
    ["boolean interval", pollSpec(POLL_ID, { interval: true })],
    ["empty handler", pollSpec(POLL_ID, { handler: "" })],
    ["unknown handler", pollSpec(POLL_ID, { handler: "missing" })],
    ["extra field", pollSpec(POLL_ID, { unexpected: true })],
    ["missing field", Object.fromEntries(Object.entries(pollSpec(POLL_ID)).filter(([key]) => key !== "args"))],
    ["mismatched spec id", pollSpec(POLL_ID, { id: "citryRuntimePoll012abc" })],
  ];

  for (const [label, spec] of malformed) {
    const owner = ownerFor({ pollBindings: { [POLL_ID]: spec }, declaredHandlers: ["refresh"] });
    assert.throws(
      () => owner.instance.$citryEvents.runtimeEvents(POLL_ID),
      /runtime poll binding is missing, stale, or invalid/,
      label,
    );
  }
});

test("empty runtime poll-site references resolve to no handles", () => {
  const { instance } = ownerFor();
  const handles = instance.$citryEvents.runtimeEvents("");

  assert.equal(handles.length, 0);
  assert.equal(Object.isFrozen(handles), true);
});

test("initial preflight rejects malformed, swapped, and orphan runtime poll metadata", async () => {
  const malformedSpecs = [
    [
      "arguments",
      pollSpec(POLL_ID, { args: "globalThis.__ran = true" }),
      /runtime poll binding is missing, stale, or invalid/,
    ],
    ["zero interval", pollSpec(POLL_ID, { interval: 0 }), /runtime poll binding is missing, stale, or invalid/],
    ["fractional interval", pollSpec(POLL_ID, { interval: 0.5 }), /runtime poll binding is missing, stale, or invalid/],
    [
      "unsafe interval",
      pollSpec(POLL_ID, { interval: Number.MAX_SAFE_INTEGER + 1 }),
      /runtime poll binding is missing, stale, or invalid/,
    ],
    [
      "unknown handler",
      pollSpec(POLL_ID, { handler: "missing" }),
      /runtime poll binding is missing, stale, or invalid/,
    ],
    ["extra field", pollSpec(POLL_ID, { unexpected: true }), /runtime poll binding is missing, stale, or invalid/],
  ];

  for (const [label, spec, matcher] of malformedSpecs) {
    await assertInitialPreflightRejects(
      bootstrap({
        appId: `runtime-poll-invalid-spec-${label.replaceAll(" ", "-")}`,
        pollBindings: { [POLL_ID]: spec },
        eventHandlers: ["refresh"],
        serverData: { count: 3 },
      }),
      matcher,
    );
  }

  const invalidReferences = [
    [
      "malformed id",
      { selectedIds: "citryRuntimePollnothex" },
      /runtime event site references invalid or duplicate ids/,
    ],
    [
      "duplicate id",
      { selectedIds: `${POLL_ID},${POLL_ID}` },
      /runtime event site references invalid or duplicate ids/,
    ],
    ["missing poll entry", { pollBindings: {} }, /runtime event references do not match definition sites/],
    [
      "poll id in event table",
      { eventBindings: { [POLL_ID]: pollSpec(POLL_ID) }, pollBindings: {} },
      /runtime event references do not match definition sites/,
    ],
    [
      "event id in poll table",
      { selectedIds: EVENT_ID, pollBindings: { [EVENT_ID]: eventSpec(EVENT_ID) }, eventBindings: {} },
      /runtime event references do not match definition sites/,
    ],
    ["orphan poll entry", { selectedIds: "" }, /runtime event references do not match definition sites/],
    [
      "orphan event entry",
      { selectedIds: "", eventBindings: { [EVENT_ID]: eventSpec(EVENT_ID) }, pollBindings: {} },
      /runtime event references do not match definition sites/,
    ],
  ];

  for (const [label, overrides, matcher] of invalidReferences) {
    await assertInitialPreflightRejects(
      bootstrap({ appId: `runtime-poll-invalid-reference-${label.replaceAll(" ", "-")}`, ...overrides }),
      matcher,
    );
  }
});

test("applyEnvelope rejects an invalid poll before publishing its accompanying State update", async () => {
  const fixture = runtime();
  const { stable, realm } = fixture;
  const appId = "runtime-poll-apply-atomicity";
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
          serverData: { count: 3 },
          preparedData: { calls: {}, callRuns: {} },
        },
      ],
    }),
  );
  stable.registerDefinition(appId, "root-definition", fixture.definition());

  const app = stable._apps.get(appId);
  const before = {
    revision: app.revision,
    snapshot: app.snapshot.value,
    occurrences: app.occurrences,
    definitions: app.definitions,
    liveOccurrence: app.occurrences.get("root"),
    serverData: app.snapshot.value.get("root").serverData,
  };
  const nextRoot = {
    id: "root",
    typeKey: "Root",
    definitionId: "runtime-poll-definition",
    parentId: null,
    placementKey: null,
    serverData: { count: 4 },
    preparedData: {
      calls: {},
      callRuns: {},
      [BINDING_KEY]: POLL_ID,
      pollBindings: { [POLL_ID]: pollSpec(POLL_ID, { args: "globalThis.__ran = true" }) },
    },
    eventContext: {
      serverRenderId: "server-root",
      stateToken: null,
      publicState: { count: 4 },
      componentClassId: "Root_1",
      descriptor: { componentClassId: "Root_1", eventHandlers: { refresh: { httpMethod: "POST" } } },
    },
  };

  await assert.rejects(
    stable.applyEnvelope(
      appId,
      realm({
        protocol: "citry-vue-prepared/1",
        appId,
        baseRevision: 0,
        revision: 1,
        rootId: "root",
        markers: [],
        definitions: [definitionAsset()],
        occurrences: [nextRoot],
        updatedIds: ["root"],
        replacements: [],
      }),
      "root",
    ),
    /runtime poll binding is missing, stale, or invalid/,
  );

  assert.equal(app.busy, false);
  assert.equal(app.revision, before.revision);
  assert.equal(app.snapshot.value, before.snapshot);
  assert.equal(app.occurrences, before.occurrences);
  assert.equal(app.definitions, before.definitions);
  assert.equal(app.occurrences.get("root"), before.liveOccurrence);
  assert.equal(app.snapshot.value.get("root").serverData, before.serverData);
  assert.deepEqual(JSON.parse(JSON.stringify(before.serverData)), { count: 3 });
});
