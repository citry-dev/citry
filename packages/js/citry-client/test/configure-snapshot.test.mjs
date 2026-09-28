import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const source = await readFile(new URL("../../../py/citry/citry/_vue/client.js", import.meta.url), "utf8");

function runtime() {
  const context = {
    CitryVueFragments: { installFragmentManager() {} },
    document: { currentScript: null },
    queueMicrotask,
    structuredClone,
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
  vm.runInNewContext(source, context);
  return context;
}

function bootstrap(context, appId = "configure-snapshot") {
  return vm.runInNewContext(
    `(() => {
    const shared = {value: 1};
    return {
      protocol: "citry-vue-prepared/1",
      appId: ${JSON.stringify(appId)},
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [{
        id: "root",
        typeKey: "Root",
        definitionId: "root-definition",
        parentId: null,
        placementKey: null,
        serverData: {nested: shared},
        preparedData: {shared},
      }],
      shared,
    };
  })()`,
    context,
  );
}

test("configure avoids redundant server-data cloning while preserving alias isolation", () => {
  const context = runtime();
  const input = bootstrap(context);
  context.__citryRuntime.configure(input);

  const app = context.__citryRuntime._apps.get("configure-snapshot");
  const snapshot = app.occurrences.get("root");
  const live = app.snapshot.value.get("root");
  assert.equal(Object.isFrozen(snapshot), true);
  // Retained occurrences are frozen whole, because later combined envelopes share them.
  assert.equal(Object.isFrozen(snapshot.serverData.nested), true);
  assert.equal(Object.isFrozen(snapshot.preparedData.shared), true);
  assert.equal(Object.isFrozen(input.shared), false);
  assert.deepEqual(Object.keys(snapshot), [
    "id",
    "typeKey",
    "definitionId",
    "parentId",
    "placementKey",
    "serverData",
    "preparedData",
  ]);
  assert.notEqual(snapshot.serverData.nested, snapshot.preparedData.shared);
  assert.notEqual(snapshot.serverData.nested, input.shared);
  assert.notEqual(live.serverData.nested, snapshot.serverData.nested);

  input.shared.value = 2;
  assert.equal(snapshot.serverData.nested.value, 1);
  assert.equal(snapshot.preparedData.shared.value, 1);
  live.serverData.nested.value = 3;
  assert.equal(snapshot.serverData.nested.value, 1);
  assert.equal(snapshot.preparedData.shared.value, 1);
});

test("configure rejects a malformed prepared graph before registering its app", () => {
  const context = runtime();
  const input = bootstrap(context, "configure-invalid-graph");
  input.occurrences[0].parentId = "missing";

  assert.throws(() => context.__citryRuntime.configure(input), /invalid prepared root/);
  assert.equal(context.__citryRuntime._apps.has("configure-invalid-graph"), false);
});
