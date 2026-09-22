import assert from "node:assert/strict";
import test from "node:test";
import vm from "node:vm";
import { build } from "esbuild";
import * as Vue from "vue";

async function coreModule() {
  const result = await build({
    entryPoints: ["src/citry-i18n-core.ts"],
    bundle: true,
    format: "esm",
    platform: "browser",
    write: false,
  });
  return import(`data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString("base64")}`);
}

async function wireModule() {
  const result = await build({
    entryPoints: ["src/citry-i18n-runtime.ts"],
    bundle: true,
    format: "esm",
    platform: "browser",
    write: false,
  });
  return import(`data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString("base64")}`);
}

async function vuePluginHarness() {
  const result = await build({
    entryPoints: ["src/citry-i18n-vue.ts"],
    bundle: true,
    define: { __CITRY_I18N_BUILD_ID__: JSON.stringify("i18n-node-tests") },
    format: "iife",
    platform: "browser",
    write: false,
  });
  let factory;
  const context = {
    console,
    fetch: async () => {
      throw new Error("unexpected i18n test fetch");
    },
    window: {
      CitryStable: {
        registerBrowserPlugin(_name, _version, registeredFactory) {
          factory = registeredFactory;
        },
      },
    },
  };
  context.structuredClone = (value) => {
    context.__clone = JSON.stringify(value);
    return vm.runInNewContext("JSON.parse(__clone)", context);
  };
  const realm = (value) => {
    context.__fixture = JSON.stringify(value);
    return vm.runInNewContext("JSON.parse(__fixture)", context);
  };
  vm.runInNewContext(result.outputFiles[0].text, context);
  assert.equal(typeof factory, "function");
  return {
    createPlugin(occurrences = []) {
      const byId = new Map(occurrences.map((item) => [item.id, item]));
      return factory({
        vue: Vue,
        occurrence: (id) => byId.get(id) ?? null,
        occurrenceId: () => null,
      });
    },
    realm,
  };
}

const vueI18n = await vuePluginHarness();

function configuredPayload() {
  const context = {
    catalog_revision: "catalog-r1",
    direction: "ltr",
    fallback_locales: [],
    formats_revision: "formats-r1",
    locale: "en-US",
    time_zone: null,
    tzdb_revision: "none",
  };
  return {
    barriers: [],
    catalog_revision: "catalog-r1",
    contexts: { "en-US": context },
    formats: {},
    formats_revision: "formats-r1",
    locales: ["en-US"],
    messages_url: null,
    parsers: {
      "en-US": {
        formats_revision: "formats-r1",
        locale: "en-US",
        number: {},
        percent: {},
        revision: "parser-r1",
        schema_version: 1,
      },
    },
    providers: [],
    requirements: [],
    runtime: "@fluent/bundle@0.19.1",
  };
}

function revisionOccurrences() {
  return [
    { id: "app", parentId: null },
    { id: "layout", parentId: "app" },
    { id: "target-a", parentId: "layout" },
    { id: "nested", parentId: "target-a" },
    { id: "leaf", parentId: "nested" },
    { id: "target-b", parentId: "layout" },
    { id: "untouched", parentId: "layout" },
  ];
}

function replacementOccurrences() {
  return revisionOccurrences()
    .filter((item) => item.id !== "nested")
    .map((item) => (item.id === "leaf" ? { ...item, parentId: "target-a" } : item));
}

function providersPayload(providers = []) {
  return { barriers: [], providers, requirements: [] };
}

function initialProviderPayload() {
  return providersPayload([
    { id: "app", parent: null, serverProviderId: "server-app" },
    { id: "layout", parent: "app", serverProviderId: "server-layout" },
    { id: "target-a", parent: "layout", serverProviderId: "server-target-a" },
    { id: "nested", parent: "target-a", serverProviderId: "server-nested" },
    { id: "target-b", parent: "layout", serverProviderId: "server-target-b" },
    { id: "untouched", parent: "layout", serverProviderId: "server-untouched" },
  ]);
}

function replacementEntries(
  first = providersPayload([
    { id: "leaf", parent: { serverProviderId: "server-layout" }, serverProviderId: "server-leaf" },
  ]),
) {
  return [
    { payload: first, rootId: "target-a" },
    { payload: providersPayload(), rootId: "target-b" },
  ];
}

function seededProviderPlugin() {
  const occurrences = revisionOccurrences();
  const plugin = vueI18n.createPlugin(occurrences);
  const initial = plugin.prepareRevision(vueI18n.realm(initialProviderPayload()), vueI18n.realm({ occurrences }));
  plugin.activateRevision(initial);
  return { initialProviderIds: [...initial.providers.keys()].sort(), occurrences, plugin };
}

test("i18n artifact validation uses staged configuration without mutating live state", async () => {
  const { createI18nWireRuntime } = await wireModule();
  const live = { catalogRevision: "old-catalog", formats: {}, formatsRevision: "old-formats" };
  const staged = { catalogRevision: "new-catalog", formats: {}, formatsRevision: "new-formats" };
  const state = { activeFluentFailures: null, configuration: live };
  const fail = (code, message) => {
    const error = new TypeError(message);
    error.code = code;
    throw error;
  };
  const wire = createI18nWireRuntime(state, fail);
  const artifact = {
    bundles: {},
    catalog_revision: "new-catalog",
    formats_revision: "new-formats",
    messages: {},
    requested_locale: "en-US",
    revision: "artifact-revision",
    runtime: "@fluent/bundle@0.19.1",
    schema_version: 1,
  };

  assert.equal(wire.browserArtifact(artifact, "en-US", staged).revision, "artifact-revision");
  assert.throws(() => wire.browserArtifact({ ...artifact, catalog_revision: "stale" }, "en-US", staged), /stale/);
  assert.equal(state.configuration, live);
});

test("i18n staged records must match the staged locale and revisions", async () => {
  const { createI18nWireRuntime } = await wireModule();
  const live = {
    catalogRevision: "old-catalog",
    formats: {},
    formatsRevision: "old-formats",
    locales: new Set(),
  };
  const staged = {
    catalogRevision: "new-catalog",
    formats: {},
    formatsRevision: "new-formats",
    locales: new Set(["en-US"]),
  };
  const state = { activeFluentFailures: null, configuration: live };
  const fail = (_code, message) => {
    throw new TypeError(message);
  };
  const wire = createI18nWireRuntime(state, fail);
  const context = {
    catalog_revision: "new-catalog",
    direction: "ltr",
    fallback_locales: [],
    formats_revision: "new-formats",
    locale: "en-US",
    time_zone: null,
    tzdb_revision: "none",
  };
  const provider = {
    context,
    id: "provider",
    parent: null,
    policy: {
      direction: { mode: "inherit" },
      locale: { mode: "inherit" },
      time_zone: { mode: "inherit" },
    },
  };
  const requirement = {
    artifacts: {},
    bindings: [],
    messages: [],
    outputs: [],
    owner: "owner",
    provider: "provider",
    rendered_locale: "zz",
  };

  assert.equal(wire.providerDefinition(provider, staged).context.locale, "en-US");
  assert.throws(
    () => wire.providerDefinition({ ...provider, context: { ...context, locale: "zz" } }, staged),
    /selectable/,
  );
  assert.throws(
    () => wire.providerDefinition({ ...provider, context: { ...context, catalog_revision: "old-catalog" } }, staged),
    /stale/,
  );
  assert.throws(() => wire.requirementRecord(requirement, staged), /selectable/);
  assert.equal(state.configuration, live);
});

test("i18n revision batches validate each configured target before merging its manifest", () => {
  const plugin = vueI18n.createPlugin();
  const valid = configuredPayload();
  const malformed = configuredPayload();
  delete malformed.runtime;

  const validStage = plugin.prepareRevision(vueI18n.realm(valid), vueI18n.realm({ occurrences: [] }));
  assert.equal(validStage.configuration.catalogRevision, "catalog-r1");
  assert.throws(
    () => plugin.prepareRevision(vueI18n.realm(malformed), vueI18n.realm({ occurrences: [] })),
    /unknown or missing fields/,
    "a configured target with a missing manifest field is invalid on its own",
  );

  const extraMetadata = providersPayload();
  extraMetadata.protocol = "citry-i18n/1";
  assert.throws(
    () => plugin.prepareRevision(vueI18n.realm(extraMetadata), vueI18n.realm({ occurrences: [] })),
    /unknown or missing fields/,
    "array-only payloads do not accept unrecognized protocol metadata",
  );

  const occurrences = [
    { id: "target-a", parentId: null },
    { id: "target-b", parentId: null },
  ];
  const entries = [
    { payload: valid, rootId: "target-a" },
    { payload: malformed, rootId: "target-b" },
  ];
  assert.throws(
    () => plugin.prepareRevisionBatch(vueI18n.realm(entries), vueI18n.realm({ baseRevision: 1, occurrences })),
    /unknown or missing fields/,
    "a valid first manifest must not fill a missing field in the second target",
  );
  assert.throws(
    () =>
      plugin.prepareRevisionBatch(
        vueI18n.realm([
          { payload: valid, rootId: "target-a" },
          { payload: extraMetadata, rootId: "target-b" },
        ]),
        vueI18n.realm({ baseRevision: 1, occurrences }),
      ),
    /unknown or missing fields/,
    "configured metadata cannot legitimize an unknown field in another target",
  );
});

test("i18n batches allow dormant targets beside a configured target", () => {
  const occurrences = revisionOccurrences();
  for (const entries of [
    [
      { payload: providersPayload(), rootId: "target-a" },
      { payload: configuredPayload(), rootId: "target-b" },
    ],
    [
      { payload: configuredPayload(), rootId: "target-a" },
      { payload: providersPayload(), rootId: "target-b" },
    ],
  ]) {
    const plugin = vueI18n.createPlugin(occurrences);
    const stage = plugin.prepareRevisionBatch(vueI18n.realm(entries), vueI18n.realm({ baseRevision: 1, occurrences }));
    assert.equal(stage.configuration.catalogRevision, "catalog-r1");
  }
});

test("i18n batches retain providers outside the target union and fall back around removed nested providers", () => {
  const { plugin } = seededProviderPlugin();
  const occurrences = replacementOccurrences();
  const stage = plugin.prepareRevisionBatch(
    vueI18n.realm(replacementEntries()),
    vueI18n.realm({ baseRevision: 1, occurrences }),
  );

  assert.deepEqual([...stage.providers.keys()].sort(), ["app", "layout", "leaf", "untouched"]);
  assert.equal(stage.providers.get("leaf").parent, "layout");
  assert.equal(stage.providers.get("leaf").serverProviderId, "server-leaf");
  assert.equal(stage.previous.view.providers.has("nested"), true);
  assert.equal(stage.providers.has("nested"), false);
  assert.equal(stage.providers.has("target-a"), false);
  assert.equal(stage.providers.has("target-b"), false);
});

test("i18n batch staging and abort leave the active provider view unchanged", () => {
  const { initialProviderIds, plugin } = seededProviderPlugin();
  const occurrences = replacementOccurrences();
  const stage = plugin.prepareRevisionBatch(
    vueI18n.realm(replacementEntries()),
    vueI18n.realm({ baseRevision: 1, occurrences }),
  );
  assert.deepEqual([...stage.previous.view.providers.keys()].sort(), initialProviderIds);

  plugin.abortRevision(stage);

  const retry = plugin.prepareRevisionBatch(
    vueI18n.realm(replacementEntries()),
    vueI18n.realm({ baseRevision: 1, occurrences }),
  );
  assert.deepEqual([...retry.previous.view.providers.keys()].sort(), initialProviderIds);
  assert.equal(retry.previous.view.providers.has("leaf"), false);
});

test("single-subtree i18n revisions still retain sibling providers", () => {
  const { plugin } = seededProviderPlugin();
  const occurrences = replacementOccurrences();
  const stage = plugin.prepareRevision(
    vueI18n.realm(
      providersPayload([
        { id: "leaf", parent: { serverProviderId: "server-layout" }, serverProviderId: "server-leaf" },
      ]),
    ),
    vueI18n.realm({ baseRevision: 1, rootId: "target-a", occurrences }),
  );

  assert.deepEqual([...stage.providers.keys()].sort(), ["app", "layout", "leaf", "target-b", "untouched"]);
  assert.equal(stage.providers.get("leaf").parent, "layout");
  assert.equal(stage.providers.has("nested"), false);
});

test("i18n runtime state factories isolate app catalogs, providers, and failures", async () => {
  const { createI18nRuntimeState, createProviderTreeCore } = await coreModule();
  const adapter = { effect: () => () => {}, isAlive: () => true, commitContext: () => {} };
  const first = createI18nRuntimeState(adapter),
    second = createI18nRuntimeState(adapter);
  first.configuration = { locales: new Set(["en"]) };
  second.configuration = { locales: new Set(["cs"]) };
  first.definitions.set("provider", { locale: "en" });
  first.requirementsByProvider.set("provider", new Set([{ message: "hello" }]));
  first.activeFluentFailures = [];
  assert.deepEqual([...first.configuration.locales], ["en"]);
  assert.deepEqual([...second.configuration.locales], ["cs"]);
  assert.equal(second.definitions.size, 0);
  assert.equal(second.requirementsByProvider.size, 0);
  assert.equal(second.activeFluentFailures, null);

  const root = {
    children: new Set(),
    definition: {
      id: "root",
      context: { locale: "en", direction: "ltr", time_zone: null, tzdb_revision: "none", fallback_locales: [] },
      policy: {
        locale: { mode: "explicit", value: "en" },
        direction: { mode: "inherit" },
        time_zone: { mode: "inherit" },
      },
    },
    plannedContexts: new Map(),
    plannedOwners: new Map(),
    state: { context: null, status: { phase: "ready" } },
  };
  root.state.context = root.definition.context;
  first.configuration.contexts = new Map([["en", root.definition.context]]);
  const tree = createProviderTreeCore(
    first,
    () => {
      throw new Error("invalid");
    },
    () => root,
  );
  tree.planProviderSubtree(root, root.definition.context, 7);
  assert.equal(tree.plannedTree(root).length, 1);
  assert.equal(root.plannedOwners.get(root), 7);
  assert.equal(second.definitions.size, 0);
});

test("per-app service resolves messages, commits latest locale switch, and restores failed plans", async () => {
  const { createI18nRuntimeState, createPerAppI18nService, createProviderTreeCore } = await coreModule();
  const context = (locale) => ({
    catalog_revision: "catalog",
    direction: "ltr",
    fallback_locales: [],
    formats_revision: "formats",
    locale,
    time_zone: null,
    tzdb_revision: "none",
  });
  let resolveCs;
  let rejectCs = false;
  const csResponse = new Promise((resolve) => {
    resolveCs = resolve;
  });
  let scopeDispose;
  let effectStopped = false;
  const adapter = {
    effect: (callback) => {
      callback();
      return () => {
        effectStopped = true;
      };
    },
    isAlive: () => true,
    commitContext: () => {},
    onScopeDispose: (callback) => {
      scopeDispose = callback;
    },
  };
  const state = createI18nRuntimeState(adapter);
  state.configuration = {
    catalogRevision: "catalog",
    contexts: new Map([
      ["en", context("en")],
      ["cs", context("cs")],
    ]),
    locales: new Set(["en", "cs"]),
    messagesUrl: "/messages",
  };
  const runtime = (locale) => ({
    artifact: { messages: { hello: { bundle_locale: locale } } },
    format: () => (locale === "en" ? "Hello" : "Ahoj"),
  });
  const requirement = {
    artifacts: new Map([["en", runtime("en")]]),
    bindings: [],
    messages: new Set(["hello"]),
    outputs: new Set(),
  };
  const root = {
    bindings: new Set(),
    children: new Set(),
    definition: {
      id: "root",
      context: context("en"),
      policy: {
        direction: { mode: "inherit" },
        locale: { mode: "explicit", value: "en" },
        time_zone: { mode: "inherit" },
      },
    },
    generation: 0,
    parent: null,
    plannedContexts: new Map(),
    plannedOwners: new Map(),
    state: { context: context("en"), status: { phase: "ready" } },
    subscribers: new Set(),
    switchGeneration: 0,
  };
  state.requirementsByProvider.set("root", new Set([requirement]));
  const tree = createProviderTreeCore(
    state,
    (code, message) => {
      const error = new Error(message);
      error.code = code;
      throw error;
    },
    () => root,
    {
      createMessageRuntime: (_value, locale) => runtime(locale),
      fetch: async () => {
        await csResponse;
        if (rejectCs) return { ok: false, status: 503 };
        return { ok: true, json: async () => ({}) };
      },
    },
  );
  const fail = (code, message) => {
    const error = new Error(message);
    error.code = code;
    throw error;
  };
  const service = createPerAppI18nService(state, tree, root, {
    addRequirement: () => {},
    bindingValues: (value) => value,
    createFormatter: () => ({}),
    createParser: () => ({}),
    exactString: (value) => value,
    fail,
    reportBindingError: () => {},
    sameContext: (left, right) => left.locale === right.locale,
    stringList: () => {},
    treeRoot: () => root,
  });
  assert.equal(service.tr("hello"), "Hello");
  service.bind({ message: "hello", values: () => ({}), onChange: () => {} });
  assert.equal(root.bindings.size, 1);
  scopeDispose();
  assert.equal(root.bindings.size, 0);
  assert.equal(effectStopped, true);
  const old = service.switchLocale("cs");
  const latest = await service.switchLocale("en");
  assert.equal(latest.status, "committed");
  resolveCs();
  assert.equal((await old).status, "stale");
  assert.equal(service.context.locale, "en");

  requirement.artifacts.delete("cs");
  rejectCs = true;
  await assert.rejects(service.switchLocale("cs"), /503/);
  assert.equal(service.context.locale, "en");
  assert.equal(service.status.phase, "error");
  assert.equal(root.plannedContexts.size, 0);
});
