import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";
import { build } from "esbuild";

const built = await build({
  entryPoints: [new URL("../src/citry-events-vue.ts", import.meta.url).pathname],
  bundle: true,
  format: "esm",
  platform: "browser",
  target: "es2020",
  write: false,
});
const bridgeModule = await import(
  `data:text/javascript;base64,${Buffer.from(built.outputFiles[0].text).toString("base64")}`
);

const descriptor = {
  componentClassId: "Board_1",
  eventHandlers: { move: { httpMethod: "POST", usesState: true } },
};

test("Vue bridge rejects malformed occurrence credentials before transport", async () => {
  let fetched = false;
  const host = {
    appId: () => "app-1",
    revision: () => 0,
    resolve: () => ({
      serverRenderId: "server_1",
      stateToken: null,
      publicState: {},
      componentClassId: "Board_1",
      descriptor,
      unexpected: true,
    }),
  };
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async () => {
      fetched = true;
      throw new Error("transport must not run");
    },
  });
  await assert.rejects(
    bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" }),
    /stale or retired/,
  );
  assert.equal(fetched, false);
});

test("Vue bridge rejects inherited handler names before activity or transport", async () => {
  let enqueued = 0;
  let fetched = 0;
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: {
      appId: () => "app-1",
      revision: () => 0,
      resolve: () => ({
        serverRenderId: "server_1",
        stateToken: null,
        publicState: {},
        componentClassId: "Board_1",
        descriptor,
      }),
      commitState() {},
      dispatchEvent() {},
      redirect() {},
      updateUrl() {},
    },
    activity: () => ({
      enqueue() {
        enqueued += 1;
      },
      start() {},
      succeed() {},
      fail() {},
      finish() {},
    }),
    fetch: async () => {
      fetched += 1;
      throw new Error("transport must not run");
    },
  });
  const source = { stableId: "board", generation: 1 };
  await assert.rejects(bridge.send({ source, handler: "constructor" }), /Unknown event handler/);
  await assert.rejects(bridge.send({ source, handler: "toString" }), /Unknown event handler/);
  assert.equal(enqueued, 0);
  assert.equal(fetched, 0);
});

test("declarative failure classification distinguishes transport from malformed responses", async () => {
  const activity = {
    enqueue: (handler) => ({ handler }),
    start() {},
    succeed() {},
    fail() {},
    finish() {},
  };
  const networkError = new TypeError("network unavailable");
  const network = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: basicHost(),
    activity: () => activity,
    fetch: async () => {
      throw networkError;
    },
  });
  const source = { stableId: "board", generation: 1 };
  await assert.rejects(network.send({ source, handler: "move" }), (error) => error === networkError);
  assert.equal(network.isDeclarativeFailureHandled(networkError), true);

  const malformed = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: basicHost(),
    activity: () => activity,
    fetch: async () => new Response(JSON.stringify({ unexpected: true })),
  });
  let malformedError;
  await assert.rejects(malformed.send({ source, handler: "move" }), (error) => {
    malformedError = error;
    return /Invalid Events response/.test(error.message);
  });
  assert.equal(malformed.isDeclarativeFailureHandled(malformedError), false);
});

test("Vue bridge sends current credentials, commits renders, and resets sequence on remount", async () => {
  const requests = [];
  const events = [];
  let context = {
    serverRenderId: "server_1",
    stateToken: "token_1",
    publicState: { moves: 0 },
    componentClassId: "Board_1",
    descriptor,
  };
  let liveGeneration = 1;
  const host = {
    appId() {
      return "app-1";
    },
    revision() {
      return context.publicState.moves;
    },
    resolve(source) {
      return source.stableId === "board" && source.generation === liveGeneration ? context : null;
    },
    async prepareRender(action) {
      return { transaction: action.prepared };
    },
    async commitRender() {
      context = { ...context, serverRenderId: "server_2", stateToken: "token_2", publicState: { moves: 1 } };
    },
    commitState(_id, token, publicState) {
      context = { ...context, stateToken: token, publicState };
    },
    dispatchEvent(name) {
      events.push([name, context.serverRenderId, context.stateToken]);
    },
    redirect() {},
    updateUrl() {},
  };
  const fetch = async (_url, init) => {
    const callEnvelope = JSON.parse(init.body);
    requests.push(callEnvelope.calls[0]);
    const first = requests.length === 1;
    return new Response(
      JSON.stringify({
        protocol: "citry-events/1",
        requestId: callEnvelope.requestId,
        results: [
          {
            ok: true,
            sendSequence: callEnvelope.calls[0].sendSequence,
            actions: first
              ? [
                  {
                    action: "render",
                    target: "render:server_1",
                    swap: "morph",
                    renderer: "vue-prepared/1",
                    prepared: { revision: "r2" },
                  },
                  { action: "event", eventName: "moved" },
                  { action: "data", value: { ok: true } },
                ]
              : [{ action: "data", value: { ok: true } }],
          },
        ],
      }),
      { headers: { "Content-Type": "application/json" } },
    );
  };
  const bridge = bridgeModule.createVueEventsBridge({ endpoint: "/events", host, fetch, csrf: { token: "csrf" } });
  const source = { stableId: "board", generation: 1 };
  assert.deepEqual(await bridge.send({ source, handler: "move" }), { ok: true });
  assert.deepEqual(events, [["moved", "server_2", "token_2"]]);
  assert.equal(requests.length, 1);
  await bridge.send({ source, handler: "move" });
  assert.deepEqual(
    requests.map(({ callerRenderId, stateToken, sendSequence }) => ({ callerRenderId, stateToken, sendSequence })),
    [
      { callerRenderId: "server_1", stateToken: "token_1", sendSequence: 1 },
      { callerRenderId: "server_2", stateToken: "token_2", sendSequence: 2 },
    ],
  );

  liveGeneration = 2;
  await bridge.send({ source: { stableId: "board", generation: 2 }, handler: "move" });
  assert.equal(requests[2].sendSequence, 1);
  await assert.rejects(bridge.send({ source, handler: "move" }), /stale or retired/);
});

test("a custom transport does not read cookies from an opaque document", async () => {
  const priorDocument = globalThis.document;
  const opaqueDocument = {};
  Object.defineProperty(opaqueDocument, "cookie", {
    get() {
      throw new Error("opaque documents cannot expose cookies");
    },
  });
  globalThis.document = opaqueDocument;
  let sent = false;
  try {
    const bridge = bridgeModule.createVueEventsBridge({
      endpoint: "/events",
      host: basicHost(),
      csrf: { cookie: "csrftoken" },
      transport: () => ({
        send(envelope) {
          sent = true;
          return {
            protocol: "citry-events/1",
            requestId: envelope.requestId,
            results: [
              {
                ok: true,
                sendSequence: envelope.calls[0].sendSequence,
                actions: [],
              },
            ],
          };
        },
      }),
    });
    await bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" });
  } finally {
    globalThis.document = priorDocument;
  }
  assert.equal(sent, true);
});

test("a detached delayed action cannot mutate after a newer response is accepted", async () => {
  const fired = [];
  const context = {
    serverRenderId: "server_1",
    stateToken: null,
    publicState: {},
    componentClassId: "Board_1",
    descriptor,
  };
  const host = {
    appId: () => "app-1",
    revision: () => 0,
    resolve: () => context,
    async prepareRender() {
      throw new Error("unexpected render");
    },
    async commitRender() {},
    commitState() {},
    dispatchEvent(name) {
      fired.push(name);
    },
    redirect() {},
    updateUrl() {},
  };
  let count = 0;
  const fetch = async (_url, init) => {
    count += 1;
    const envelope = JSON.parse(init.body);
    return new Response(
      JSON.stringify({
        protocol: "citry-events/1",
        requestId: envelope.requestId,
        results: [
          {
            ok: true,
            sendSequence: envelope.calls[0].sendSequence,
            actions:
              count === 1
                ? [{ action: "event", eventName: "old", delay: 0.01, wait: false }]
                : [{ action: "data", value: null }],
          },
        ],
      }),
    );
  };
  const bridge = bridgeModule.createVueEventsBridge({ endpoint: "/events", host, fetch });
  const source = { stableId: "board", generation: 1 };
  const priorError = console.error;
  console.error = () => {};
  try {
    await bridge.send({ source, handler: "move" });
    await bridge.send({ source, handler: "move" });
    await new Promise((resolve) => setTimeout(resolve, 25));
  } finally {
    console.error = priorError;
  }
  assert.deepEqual(fired, []);
});

test("multiple event owners keep independent send sequences", async () => {
  const sequences = [];
  const host = {
    appId: () => "app-1",
    revision: () => 0,
    resolve(source) {
      return {
        serverRenderId: `server_${source.stableId}`,
        stateToken: null,
        publicState: {},
        componentClassId: "Board_1",
        descriptor,
      };
    },
  };
  const fetch = async (_url, init) => {
    const envelope = JSON.parse(init.body);
    sequences.push([envelope.calls[0].callerRenderId, envelope.calls[0].sendSequence]);
    return new Response(
      JSON.stringify({
        protocol: "citry-events/1",
        requestId: envelope.requestId,
        results: [{ ok: true, sendSequence: envelope.calls[0].sendSequence, actions: [] }],
      }),
    );
  };
  const bridge = bridgeModule.createVueEventsBridge({ endpoint: "/events", host, fetch });
  await bridge.send({ source: { stableId: "one", generation: 1 }, handler: "move" });
  await bridge.send({ source: { stableId: "two", generation: 1 }, handler: "move" });
  await bridge.send({ source: { stableId: "one", generation: 1 }, handler: "move" });
  assert.deepEqual(sequences, [
    ["server_one", 1],
    ["server_two", 1],
    ["server_one", 2],
  ]);
});

test("unsupported targets reject the whole result before state mutation", async () => {
  let stateCommits = 0;
  const context = {
    serverRenderId: "server_1",
    stateToken: "token_1",
    publicState: {},
    componentClassId: "Board_1",
    descriptor,
  };
  const host = {
    appId: () => "app-1",
    revision: () => 0,
    resolve: () => context,
    commitState() {
      stateCommits += 1;
    },
  };
  const fetch = async (_url, init) => {
    const envelope = JSON.parse(init.body);
    return new Response(
      JSON.stringify({
        protocol: "citry-events/1",
        requestId: envelope.requestId,
        results: [
          {
            ok: true,
            sendSequence: envelope.calls[0].sendSequence,
            actions: [
              { action: "state", targetRenderId: "server_1", stateToken: "token_2", publicState: { moves: 2 } },
              {
                action: "render",
                target: "#arbitrary-css",
                swap: "morph",
                renderer: "vue-prepared/1",
                prepared: {},
              },
            ],
          },
        ],
      }),
    );
  };
  const bridge = bridgeModule.createVueEventsBridge({ endpoint: "/events", host, fetch });
  await assert.rejects(
    bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" }),
    // The protocol check refuses a CSS selector target before any action runs.
    /A render target must be render:<renderId> or mark:<callerRenderId>:<name>/,
  );
  assert.equal(stateCommits, 0);
});

test("synchronous host preflight runs before State hoisting and carries its render plan", async () => {
  const calls = [];
  const context = contextFor("server_1");
  const source = { stableId: "board", generation: 1 };
  const plan = Object.freeze({ target: "board" });
  const host = {
    ...basicHost(() => context),
    preflightResult(result, actualSource) {
      calls.push(["preflight", actualSource]);
      return { result, renderPlan: plan };
    },
    commitState() {
      calls.push(["state"]);
    },
    async prepareRender(_action, _source, _signal, actualPlan) {
      calls.push(["prepare", actualPlan]);
      return { transaction: {} };
    },
    async commitRender() {
      calls.push(["render"]);
    },
    abortRender() {},
  };
  const fetch = async (_url, init) => {
    const envelope = JSON.parse(init.body);
    return resultResponse(envelope, [
      { action: "state", targetRenderId: "server_1", stateToken: "token_2", publicState: { moves: 2 } },
      {
        action: "render",
        target: "render:server_1",
        swap: "morph",
        renderer: "vue-prepared/1",
        prepared: {},
      },
    ]);
  };
  const bridge = bridgeModule.createVueEventsBridge({ endpoint: "/events", host, fetch });

  await bridge.send({ source, handler: "move" });

  assert.deepEqual(calls, [["preflight", source], ["state"], ["prepare", plan], ["render"]]);
});

test("synchronous target preflight failure commits no immediate State", async () => {
  let stateCommits = 0;
  const host = {
    ...basicHost(),
    preflightResult() {
      throw new Error("duplicate retained render address");
    },
    commitState() {
      stateCommits += 1;
    },
  };
  const fetch = async (_url, init) => {
    const envelope = JSON.parse(init.body);
    return resultResponse(envelope, [
      { action: "state", targetRenderId: "server_1", stateToken: "token_2", publicState: { moves: 2 } },
      {
        action: "render",
        target: "render:server_2",
        swap: "morph",
        renderer: "vue-prepared/1",
        prepared: {},
      },
    ]);
  };
  const bridge = bridgeModule.createVueEventsBridge({ endpoint: "/events", host, fetch });

  await assert.rejects(
    bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" }),
    /duplicate retained render address/,
  );
  assert.equal(stateCommits, 0);
});

test("accepted State is not restored when a later response action fails", async () => {
  const restored = [];
  const committed = [];
  const host = {
    ...basicHost(),
    takePendingState: () => ({ draft: "sent" }),
    restorePendingState: (_source, updates) => restored.push(updates),
    commitState(renderId, stateToken, publicState) {
      committed.push([renderId, stateToken, publicState]);
    },
    async prepareRender() {
      throw new Error("the later render action failed");
    },
    abortRender() {},
  };
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async (_url, init) =>
      resultResponse(JSON.parse(init.body), [
        { action: "state", targetRenderId: "server_1", stateToken: "token_2", publicState: { moves: 2 } },
        { action: "render", target: "render:server_1", swap: "morph", renderer: "vue-prepared/1", prepared: {} },
      ]),
  });

  await assert.rejects(bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" }), /later render/);
  // The host receives the public values with the token, so `$state` can show what the handler set.
  assert.deepEqual(committed, [["server_1", "token_2", { moves: 2 }]]);
  assert.deepEqual(restored, []);
});

test("a delayed State refresh is skipped once a newer result for the component was applied", async () => {
  const committed = [];
  const stale = [];
  const host = {
    ...basicHost(),
    commitState(_renderId, stateToken, publicState) {
      committed.push([stateToken, publicState]);
    },
    lifecycle(kind, _source, _event, detail) {
      if (kind === "stale") stale.push(detail);
      return true;
    },
  };
  let sent = 0;
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async (_url, init) => {
      sent += 1;
      // The first answer delays its refresh without blocking; the second answers before that delay ends.
      const actions =
        sent === 1
          ? [
              {
                action: "state",
                targetRenderId: "server_1",
                stateToken: "token_old",
                publicState: { moves: 1 },
                delay: 0.2,
                wait: false,
              },
            ]
          : [{ action: "state", targetRenderId: "server_1", stateToken: "token_new", publicState: { moves: 2 } }];
      return resultResponse(JSON.parse(init.body), actions);
    },
  });
  const source = { stableId: "board", generation: 1 };

  await bridge.send({ source, handler: "move" });
  await bridge.send({ source, handler: "move" });
  await new Promise((resolve) => setTimeout(resolve, 300));

  // The older values never replace the newer ones, and listeners hear why the refresh was dropped.
  assert.deepEqual(committed, [["token_new", { moves: 2 }]]);
  assert.deepEqual(stale, [{ reason: "epoch" }]);
});

const contextFor = (id = "server_1") => ({
  serverRenderId: id,
  stateToken: null,
  publicState: {},
  componentClassId: "Board_1",
  descriptor,
});

const resultResponse = (envelope, actions = []) =>
  new Response(
    JSON.stringify({
      protocol: "citry-events/1",
      requestId: envelope.requestId,
      results: [{ ok: true, sendSequence: envelope.calls[0].sendSequence, actions }],
    }),
  );

const basicHost = (resolve = () => contextFor()) => ({
  appId: () => "app-1",
  revision: () => 0,
  resolve,
  commitState() {},
  dispatchEvent() {},
  redirect() {},
  updateUrl() {},
});

test("Vue Events emits the complete lifecycle around a committed render", async () => {
  const source = { stableId: "board", generation: 1 };
  const lifecycle = [];
  const host = {
    ...basicHost(),
    lifecycle(kind, actualSource, event, detail) {
      lifecycle.push({ kind, source: actualSource, event, detail });
      return true;
    },
    async prepareRender(action) {
      return { transaction: action.prepared };
    },
    abortRender() {},
    async commitRender() {},
  };
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async (_url, init) =>
      resultResponse(JSON.parse(init.body), [
        { action: "render", target: "render:server_1", swap: "morph", renderer: "vue-prepared/1", prepared: {} },
        { action: "data", value: { saved: true } },
      ]),
  });

  assert.deepEqual(await bridge.send({ source, handler: "move" }), { saved: true });
  assert.deepEqual(
    lifecycle.map((item) => item.kind),
    ["before", "swapped", "after"],
  );
  assert.equal(lifecycle[0].source, source);
  assert.equal(lifecycle[0].event, "move");
  assert.deepEqual(lifecycle[1].detail, { els: [] });
  assert.deepEqual(lifecycle[2].detail, { ok: true });
});

test("a string endpoint remains the default route when no page URL is configured", async () => {
  let requestedUrl;
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events/call",
    host: basicHost(),
    fetch: async (url, init) => {
      requestedUrl = url;
      return resultResponse(JSON.parse(init.body), [{ action: "data", value: true }]);
    },
  });

  assert.equal(await bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" }), true);
  assert.equal(requestedUrl, "/events/call");
});

test("public action application keeps targetless events page-wide in a mixed action list", async () => {
  const source = { stableId: "board", generation: 1 };
  const local = [];
  const global = [];
  const host = {
    ...basicHost(),
    dispatchEvent(name) {
      local.push(name);
    },
    dispatchEventGlobal(name) {
      global.push(name);
    },
  };
  const bridge = bridgeModule.createVueEventsBridge({ endpoint: "/events", host });

  assert.equal(
    await bridge.applyActions(
      [
        { action: "event", eventName: "page-ready" },
        { action: "event", eventName: "component-ready", target: "render:server_1" },
        { action: "data", value: 7 },
      ],
      source,
    ),
    7,
  );
  assert.deepEqual(global, ["page-ready"]);
  assert.deepEqual(local, ["component-ready"]);
});

test("mounted public action application emits the ordinary lifecycle", async () => {
  const source = { stableId: "board", generation: 1 };
  const lifecycle = [];
  const host = {
    ...basicHost(),
    lifecycle(kind, actualSource, event, detail) {
      lifecycle.push({ kind, source: actualSource, event, detail });
      return true;
    },
    dispatchEvent() {},
  };
  const bridge = bridgeModule.createVueEventsBridge({ endpoint: "/events", host });

  assert.equal(
    await bridge.applyActions(
      [
        { action: "event", eventName: "component-ready", target: "render:server_1" },
        { action: "data", value: 7 },
      ],
      source,
    ),
    7,
  );
  assert.deepEqual(
    lifecycle.map((item) => item.kind),
    ["before", "after"],
  );
  assert.equal(lifecycle[0].event, "__external__");
  assert.deepEqual(lifecycle[1].detail, { ok: true });
});

test("mounted public action application reports cancellation and interpreter failures", async () => {
  const source = { stableId: "board", generation: 1 };
  const cancelledLifecycle = [];
  const cancelledHost = {
    ...basicHost(),
    lifecycle(kind, _source, event, detail) {
      cancelledLifecycle.push([kind, event, detail]);
      return kind !== "before";
    },
    dispatchEvent() {
      throw new Error("cancelled action must not run");
    },
  };
  const cancelled = bridgeModule.createVueEventsBridge({ endpoint: "/events", host: cancelledHost });
  await assert.rejects(
    cancelled.applyActions([{ action: "event", eventName: "cancelled", target: "render:server_1" }], source),
    /cancelled by citry:events:before/,
  );
  assert.deepEqual(
    cancelledLifecycle.map(([kind]) => kind),
    ["before", "after"],
  );
  assert.deepEqual(cancelledLifecycle[1][2], { ok: false });

  const failedLifecycle = [];
  const failedHost = {
    ...basicHost(),
    lifecycle(kind, _source, event, detail) {
      failedLifecycle.push([kind, event, detail]);
      return true;
    },
    dispatchEvent() {
      throw new Error("mounted action failed");
    },
  };
  const failed = bridgeModule.createVueEventsBridge({ endpoint: "/events", host: failedHost });
  await assert.rejects(
    failed.applyActions([{ action: "event", eventName: "broken", target: "render:server_1" }], source),
    /mounted action failed/,
  );
  assert.deepEqual(
    failedLifecycle.map(([kind]) => kind),
    ["before", "error", "after"],
  );
  assert.equal(failedLifecycle[1][1], "__external__");
  assert.deepEqual(failedLifecycle[2][2], { ok: false });
});

test("mounted public action application reports stale delayed actions", async () => {
  const source = { stableId: "board", generation: 1 };
  const lifecycle = [];
  const host = {
    ...basicHost(),
    lifecycle(kind, _source, event, detail) {
      lifecycle.push([kind, event, detail]);
      return true;
    },
  };
  const bridge = bridgeModule.createVueEventsBridge({ endpoint: "/events", host });
  const applied = bridge.applyActions([{ action: "data", value: 7, delay: 0.03 }], source);
  await new Promise((resolve) => setTimeout(resolve, 0));
  bridge.retire(source);
  await assert.rejects(applied, /stale or retired/);
  assert.deepEqual(
    lifecycle.map(([kind]) => kind),
    ["before", "stale", "after"],
  );
  assert.equal(lifecycle[1][2].reason, "retired");
});

test("latestCallWins supersedes an active predecessor and drops its response", async () => {
  const latestDescriptor = {
    componentClassId: "Board_1",
    eventHandlers: { move: { ...descriptor.eventHandlers.move, latestCallWins: true } },
  };
  const source = { stableId: "board", generation: 1 };
  const responses = [];
  const lifecycle = [];
  let requests = 0;
  const host = {
    ...basicHost(() => ({ ...contextFor(), descriptor: latestDescriptor })),
    lifecycle(kind, _source, event, detail) {
      lifecycle.push({ kind, event, detail });
      return true;
    },
  };
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events/call",
    host,
    fetch: async (_url, init) => {
      requests += 1;
      const envelope = JSON.parse(init.body);
      return new Promise((resolve) =>
        responses.push(() => resolve(resultResponse(envelope, [{ action: "data", value: requests }]))),
      );
    },
  });

  const first = bridge.send({ source, handler: "move" });
  await new Promise((resolve) => setTimeout(resolve, 0));
  const second = bridge.send({ source, handler: "move" });
  await assert.rejects(first, /superseded/);
  while (requests < 2) await new Promise((resolve) => setTimeout(resolve, 0));
  responses[1]();
  assert.equal(await second, 2);
  responses[0]();
  assert.deepEqual(
    lifecycle.filter((item) => item.kind === "stale").map((item) => item.detail.reason),
    ["superseded"],
  );
});

const latestWinsDescriptor = {
  componentClassId: "Board_1",
  eventHandlers: { move: { httpMethod: "POST", usesState: true, latestCallWins: true } },
};

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

// A bridge whose first call returns `firstActions` and every later call returns data 2, after
// `laterResponseMs`. The host records every page change, lifecycle event, and activity step, and
// `accepted` resolves when the first call's result has been accepted.
const supersedingBridge = (firstActions, { laterResponseMs = 0, onEvent, onState } = {}) => {
  const record = [];
  const lifecycle = [];
  const activity = [];
  let markAccepted;
  const accepted = new Promise((resolve) => {
    markAccepted = resolve;
  });
  let bridge;
  const host = {
    ...basicHost(() => ({ ...contextFor(), descriptor: latestWinsDescriptor })),
    preflightResult(result) {
      markAccepted();
      return { result };
    },
    async prepareRender() {
      record.push("render:prepared");
      return { transaction: {} };
    },
    abortRender() {},
    async commitRender() {
      record.push("render:committed");
    },
    commitState(_target, token) {
      record.push(`state:${token}`);
      onState?.(token, bridge);
    },
    dispatchEvent(name) {
      record.push(`event:${name}`);
      onEvent?.(name, bridge);
    },
    redirect(url) {
      record.push(`redirect:${url}`);
    },
    updateUrl(url, mode) {
      record.push(`url:${mode}:${url}`);
    },
    lifecycle(kind, _source, _event, detail) {
      lifecycle.push({ kind, detail });
      return true;
    },
  };
  let calls = 0;
  bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    activity: () => ({
      enqueue: (handler) => handler,
      start: () => activity.push("start"),
      succeed: () => activity.push("succeed"),
      fail: () => activity.push("fail"),
      finish: () => activity.push("finish"),
    }),
    fetch: async (_url, init) => {
      calls += 1;
      const envelope = JSON.parse(init.body);
      if (calls === 1) return resultResponse(envelope, firstActions);
      await sleep(laterResponseMs);
      return resultResponse(envelope, [{ action: "data", value: 2 }]);
    },
  });
  return { bridge, record, lifecycle, activity, accepted };
};

// Sends a first call, waits until its result is accepted and its actions have started, then sends
// the call that supersedes it.
const supersedeAfterAcceptance = async ({ bridge, accepted }) => {
  const source = { stableId: "board", generation: 1 };
  const first = bridge.send({ source, handler: "move" });
  first.catch(() => {});
  await accepted;
  await sleep(5);
  const started = Date.now();
  const second = bridge.send({ source, handler: "move" });
  const value = await second;
  return { first, value, elapsed: Date.now() - started };
};

const staleReasons = (lifecycle) => lifecycle.filter((item) => item.kind === "stale").map((item) => item.detail.reason);

test("a superseded call changes nothing on the page", async () => {
  const setup = supersedingBridge([
    { action: "event", eventName: "old", delay: 0.2 },
    { action: "state", targetRenderId: "server_1", stateToken: "old-token", publicState: {}, delay: 0.01 },
    { action: "data", value: 1 },
  ]);
  const { first, value, elapsed } = await supersedeAfterAcceptance(setup);
  await assert.rejects(first, /superseded/);
  assert.equal(value, 2);
  // The newer call does not wait for the old call's 200 ms delay.
  assert.ok(elapsed < 100, `the newer call waited ${elapsed} ms`);
  await sleep(250);
  assert.deepEqual(setup.record, []);
});

const delayedActions = {
  Dispatch: { action: "event", eventName: "old" },
  Redirect: { action: "redirect", url: "/old" },
  PushUrl: { action: "url", url: "/old", mode: "push" },
  ReplaceUrl: { action: "url", url: "/old", mode: "replace" },
  State: { action: "state", targetRenderId: "server_1", stateToken: "old-token", publicState: {} },
};

for (const [name, action] of Object.entries(delayedActions)) {
  test(`a superseded call drops its delayed ${name}`, async () => {
    const setup = supersedingBridge([
      { ...action, delay: 0.2 },
      { action: "data", value: 1 },
    ]);
    const { first, value, elapsed } = await supersedeAfterAcceptance(setup);
    await assert.rejects(first, /superseded/);
    assert.equal(value, 2);
    assert.ok(elapsed < 100, `the newer call waited ${elapsed} ms`);
    await sleep(250);
    assert.deepEqual(setup.record, []);
    assert.deepEqual(staleReasons(setup.lifecycle), ["superseded"]);
  });

  test(`a superseded call drops its delayed ${name} with wait=False`, async () => {
    // The newer call's result arrives after the old action is due, so only the supersession can
    // stop it. The old call has already finished when the newer call supersedes it.
    const setup = supersedingBridge(
      [
        { ...action, delay: 0.1, wait: false },
        { action: "data", value: 1 },
      ],
      {
        laterResponseMs: 250,
      },
    );
    const { first, value } = await supersedeAfterAcceptance(setup);
    assert.equal(await first, 1);
    assert.equal(value, 2);
    await sleep(150);
    assert.deepEqual(setup.record, []);
    assert.deepEqual(staleReasons(setup.lifecycle), ["superseded"]);
  });
}

test("a superseded call drops its delayed Render", async () => {
  const setup = supersedingBridge([
    { ...renderAction(), delay: 0.2 },
    { action: "data", value: 1 },
  ]);
  const { first, value, elapsed } = await supersedeAfterAcceptance(setup);
  await assert.rejects(first, /superseded/);
  assert.equal(value, 2);
  assert.ok(elapsed < 100, `the newer call waited ${elapsed} ms`);
  await sleep(250);
  assert.deepEqual(setup.record, []);
});

test("a superseded call drops its delayed Data", async () => {
  const setup = supersedingBridge([{ action: "data", value: 1, delay: 0.2 }]);
  const { first, value, elapsed } = await supersedeAfterAcceptance(setup);
  await assert.rejects(first, /superseded/);
  assert.equal(value, 2);
  // The newer call's result comes first, without waiting for the old call's Data.
  assert.ok(elapsed < 100, `the newer call waited ${elapsed} ms`);
});

test("a call superseded during a delay reports no success", async () => {
  const setup = supersedingBridge([
    { action: "event", eventName: "old", delay: 0.2 },
    { action: "data", value: 1 },
  ]);
  await supersedeAfterAcceptance(setup);
  await sleep(250);
  const afters = setup.lifecycle.filter((item) => item.kind === "after").map((item) => item.detail.ok);
  // One failed `after` for the superseded call and one successful `after` for the newer call.
  assert.deepEqual(afters, [false, true]);
  assert.equal(setup.activity.filter((step) => step === "succeed").length, 1);
});

test("a call superseded by its own last action reports no success", async () => {
  // The page code behind the call's last action sends the same handler again at once.
  let newer;
  const setup = supersedingBridge([{ action: "event", eventName: "old" }], {
    onEvent: (name, bridge) => {
      if (name === "old") newer = bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" });
    },
  });
  const first = setup.bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" });
  await assert.rejects(first, /superseded/);
  assert.equal(await newer, 2);
  assert.deepEqual(
    setup.lifecycle
      .filter((item) => item.kind !== "before")
      .map((item) => [item.kind, item.detail?.reason ?? item.detail?.ok]),
    [
      ["stale", "superseded"],
      ["after", false],
      ["after", true],
    ],
  );
});

test("a call superseded by its own first State commit commits no more State", async () => {
  let newer;
  const setup = supersedingBridge(
    [
      { action: "state", targetRenderId: "server_1", stateToken: "a", publicState: {} },
      { action: "state", targetRenderId: "server_1", stateToken: "b", publicState: {} },
      { action: "data", value: 1 },
    ],
    {
      onState: (token, bridge) => {
        if (token === "a") newer = bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" });
      },
    },
  );
  const first = setup.bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" });
  await assert.rejects(first, /superseded/);
  assert.equal(await newer, 2);
  assert.deepEqual(setup.record, ["state:a"]);
});

test("disposing the bridge stops a delayed applyActions made without a component", async () => {
  const record = [];
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: {
      ...basicHost(),
      redirect(url) {
        record.push(url);
      },
    },
    fetch: async () => {
      throw new Error("transport must not run");
    },
  });
  const applied = bridge.applyActions([{ action: "redirect", url: "/later", delay: 0.05 }]);
  bridge.dispose();
  await assert.rejects(applied, /disposed/);
  await sleep(80);
  assert.deepEqual(record, []);
});

const errorResponse = (envelope, error) =>
  new Response(
    JSON.stringify({
      protocol: "citry-events/1",
      requestId: envelope.requestId,
      results: [{ ok: false, sendSequence: envelope.calls[0].sendSequence, error }],
    }),
    { status: error.status },
  );

const staleStateError = {
  status: 409,
  code: "stale_state",
  message: "The state token is stale (expired or rotated out); reload the page to get a fresh one.",
};

test("a stale_state answer reports a cancelable version notification before the error", async () => {
  const lifecycle = [];
  let prompts = 0;
  const host = {
    ...basicHost(),
    lifecycle(kind, _source, event, detail) {
      lifecycle.push([kind, event, detail]);
      return true;
    },
    promptReload() {
      prompts += 1;
    },
  };
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async (_url, init) => errorResponse(JSON.parse(init.body), staleStateError),
  });
  const source = { stableId: "board", generation: 1 };
  await assert.rejects(bridge.send({ source, handler: "move" }), (error) => error.code === "stale_state");
  assert.deepEqual(
    lifecycle.map(([kind, event, detail]) => [kind, event, kind === "error" ? detail.error.code : detail]),
    [
      ["before", "move", undefined],
      ["stale", "move", { reason: "version" }],
      ["error", "move", "stale_state"],
      ["after", "move", { ok: false }],
    ],
  );
  // The bridge asks the host each time; the host keeps the once-per-page rule.
  await assert.rejects(bridge.send({ source, handler: "move" }), (error) => error.code === "stale_state");
  assert.equal(prompts, 2);
});

test("a cancelled version notification skips the reload prompt, and other errors never prompt", async () => {
  const kinds = [];
  let prompts = 0;
  let answer = staleStateError;
  const host = {
    ...basicHost(),
    lifecycle(kind, _source, _event, detail) {
      kinds.push(kind === "stale" ? `stale:${detail.reason}` : kind);
      return kind !== "stale";
    },
    promptReload() {
      prompts += 1;
    },
  };
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async (_url, init) => errorResponse(JSON.parse(init.body), answer),
  });
  const source = { stableId: "board", generation: 1 };
  await assert.rejects(bridge.send({ source, handler: "move" }), (error) => error.code === "stale_state");
  assert.equal(prompts, 0);
  answer = { status: 403, code: "invalid_state", message: "The state token is invalid." };
  await assert.rejects(bridge.send({ source, handler: "move" }), (error) => error.code === "invalid_state");
  assert.equal(prompts, 0);
  assert.deepEqual(kinds, ["before", "stale:version", "error", "after", "before", "error", "after"]);
});

test("Vue Events cancellation is reported by after without an error lifecycle", async () => {
  const lifecycle = [];
  let fetched = false;
  const host = {
    ...basicHost(),
    lifecycle(kind, _source, _event, detail) {
      lifecycle.push([kind, detail]);
      return kind !== "before";
    },
  };
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async () => {
      fetched = true;
      throw new Error("before listener should stop the request");
    },
  });
  await assert.rejects(bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" }), /cancelled/);
  assert.equal(fetched, false);
  assert.deepEqual(
    lifecycle.map(([kind]) => kind),
    ["before", "after"],
  );
  assert.deepEqual(lifecycle[1][1], { ok: false });
});

test("page configuration is read for each Vue Events bridge send", async () => {
  let configuration = { url: "/first/ext/events/", csrf: { token: "first" }, timeout: 1000 };
  const requests = [];
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/fallback/call",
    eventBaseUrl: "/fallback/e/",
    host: basicHost(),
    runtimeConfig: () => configuration,
    fetch: async (url, init) => {
      requests.push({ url, init });
      return resultResponse(JSON.parse(init.body), [{ action: "data", value: "ok" }]);
    },
  });
  const source = { stableId: "board", generation: 1 };
  await bridge.send({ source, handler: "move" });
  configuration = { url: "/second/ext/events/", csrf: { token: "second" }, timeout: 2000 };
  await bridge.send({ source, handler: "move" });
  assert.deepEqual(
    requests.map((request) => [request.url, request.init.headers["X-CSRFToken"]]),
    [
      ["/first/ext/events/call", "first"],
      ["/second/ext/events/call", "second"],
    ],
  );
});

test("registered Vue Events transports receive the protocol envelope", async () => {
  const envelopes = [];
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: basicHost(),
    runtimeConfig: () => ({ transport: "memory" }),
    transport: () => ({
      send(envelope) {
        envelopes.push(envelope);
        return {
          protocol: "citry-events/1",
          requestId: envelope.requestId,
          results: [
            { ok: true, sendSequence: envelope.calls[0].sendSequence, actions: [{ action: "data", value: 7 }] },
          ],
        };
      },
    }),
    fetch: async () => {
      throw new Error("registered transport should replace fetch");
    },
  });
  const value = await bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" });
  assert.equal(value, 7);
  assert.equal(envelopes.length, 1);
  assert.equal(envelopes[0].calls[0].handlerName, "move");
});

test("a send from a form carries the form mark and a plain send leaves it out", async () => {
  const calls = [];
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: basicHost(),
    fetch: async (_url, init) => {
      const envelope = JSON.parse(init.body);
      calls.push(envelope.calls[0]);
      return resultResponse(envelope);
    },
  });
  const source = { stableId: "board", generation: 1 };
  await bridge.send({ source, handler: "move", args: { count: "3" }, argsSource: "form" });
  await bridge.send({ source, handler: "move", args: { count: 3 } });
  assert.equal(calls[0].argsSource, "form");
  assert.deepEqual(calls[0].args, { count: "3" });
  // Without the mark the server keeps its strict JSON binding.
  assert.equal(Object.hasOwn(calls[1], "argsSource"), false);
});

test("collectFormArgs sends every value as the form's text", () => {
  const entries = [
    ["count", "3"],
    ["price", "2.5"],
    ["notify", "on"],
    ["tags", "a"],
    ["tags", "b"],
    ["avatar", { name: "photo.png" }],
    ["reserved", "x"],
  ];
  const form = {};
  const previous = globalThis.FormData;
  // Node has no DOM form, so a stand-in FormData replays the entries a
  // browser would read from a form with number, checkbox, repeated, and
  // file controls.
  globalThis.FormData = class {
    constructor(given) {
      assert.equal(given, form);
    }
    forEach(callback) {
      for (const [name, value] of entries) callback(value, name);
    }
  };
  try {
    assert.deepEqual(bridgeModule.collectFormArgs(form, new Set(["reserved"])), {
      count: "3",
      price: "2.5",
      notify: "on",
      tags: ["a", "b"],
    });
  } finally {
    globalThis.FormData = previous;
  }
});

test("collectFormArgs sends the button that submitted the form, as a post without JavaScript does", () => {
  const form = {};
  const previous = { FormData: globalThis.FormData, HTMLButtonElement: globalThis.HTMLButtonElement };
  globalThis.HTMLButtonElement = class {};
  const button = new globalThis.HTMLButtonElement();
  button.form = form;
  const otherButton = new globalThis.HTMLButtonElement();
  otherButton.form = {};
  const given = [];
  // The stand-in FormData adds the submitter's entry the way a browser does
  // when it is passed one.
  globalThis.FormData = class {
    constructor(formGiven, submitter) {
      given.push(submitter);
      this.entries = [["q", "alpha"], ...(submitter ? [["action", "save"]] : [])];
    }
    forEach(callback) {
      for (const [name, value] of this.entries) callback(value, name);
    }
  };
  try {
    assert.deepEqual(bridgeModule.collectFormArgs(form, new Set(), button), { q: "alpha", action: "save" });
    // A button of another form, or no button, is not passed to FormData.
    assert.deepEqual(bridgeModule.collectFormArgs(form, new Set(), otherButton), { q: "alpha" });
    assert.deepEqual(bridgeModule.collectFormArgs(form, new Set()), { q: "alpha" });
    assert.deepEqual(given, [button, undefined, undefined]);
  } finally {
    globalThis.FormData = previous.FormData;
    globalThis.HTMLButtonElement = previous.HTMLButtonElement;
  }
});

test("custom transports receive the request context the fetch transport sends", async () => {
  const sent = [];
  const fetched = [];
  const result = (envelope) => ({
    protocol: "citry-events/1",
    requestId: envelope.requestId,
    results: [{ ok: true, sendSequence: envelope.calls[0].sendSequence, actions: [{ action: "data", value: 1 }] }],
  });
  const create = (transport) =>
    bridgeModule.createVueEventsBridge({
      endpoint: "/events",
      host: basicHost(),
      csrf: { token: "csrf-token" },
      transport: () => transport,
      fetch: async (url, init) => {
        fetched.push({ url, method: init.method, headers: init.headers });
        return { ok: true, status: 200, headers: { get: () => null }, json: async () => result(JSON.parse(init.body)) };
      },
    });
  const source = { stableId: "board", generation: 1 };
  await create({
    send(envelope, request) {
      sent.push(request);
      // A transport may add its own headers without changing later calls.
      request.headers["X-Bridge"] = "1";
      return result(envelope);
    },
  }).send({ source, handler: "move" });
  await create(null).send({ source, handler: "move" });

  assert.equal(sent.length, 1);
  const [request] = sent;
  assert.ok(request.signal instanceof AbortSignal);
  assert.equal(request.signal.aborted, false);
  const { "X-Bridge": added, ...forwarded } = request.headers;
  assert.equal(added, "1");
  // Same URL, method and headers as the built-in fetch transport, including
  // the Vue app, occurrence and revision headers the server needs for Render.
  assert.deepEqual({ url: request.url, method: request.method, headers: forwarded }, fetched[0]);
  assert.equal(forwarded["X-Citry-Vue-App"], "app-1");
  assert.equal(forwarded["X-Citry-Vue-Occurrence"], "board");
  assert.equal(forwarded["X-Citry-Vue-Revision"], "0");
  assert.equal(forwarded["X-CSRFToken"], "csrf-token");
});

test("GET uses the exact per-event URL and flat metadata without consuming State drafts", async () => {
  const getDescriptor = {
    componentClassId: "Board_1",
    eventHandlers: { search: { httpMethod: "GET", usesState: true } },
  };
  let taken = 0;
  let csrfReads = 0;
  let batchEndpointReads = 0;
  let request;
  const host = basicHost(() => ({ ...contextFor(), stateToken: "state-token", descriptor: getDescriptor }));
  host.takePendingState = () => {
    taken += 1;
    return { draft: "unsent" };
  };
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: () => {
      batchEndpointReads += 1;
      throw new Error("GET must not resolve the batch endpoint");
    },
    eventBaseUrl: "/prefix/ext/events/e/",
    host,
    csrf: {
      token: () => {
        csrfReads += 1;
        return "csrf-secret";
      },
    },
    fetch: async (url, init) => {
      request = { url, init };
      const query = new URL(url, "https://example.test").searchParams;
      const envelope = {
        requestId: query.get("_citry_request_id"),
        calls: [{ sendSequence: Number(query.get("_citry_send_sequence")) }],
      };
      return resultResponse(envelope, [{ action: "data", value: "found" }]);
    },
  });
  const result = await bridge.send({
    source: { stableId: "board", generation: 1 },
    handler: "search",
    args: { q: "a/b", enabled: true, page: 2, tags: ["x", "y"] },
  });
  assert.equal(result, "found");
  assert.equal(taken, 0);
  assert.equal(csrfReads, 0);
  assert.equal(batchEndpointReads, 0);
  assert.equal(request.init.method, "GET");
  assert.equal(request.init.body, undefined);
  assert.equal(request.init.headers["X-CSRFToken"], undefined);
  const parsed = new URL(request.url, "https://example.test");
  assert.equal(parsed.pathname, "/prefix/ext/events/e/Board_1/search");
  assert.deepEqual(parsed.searchParams.getAll("tags"), ["x", "y"]);
  assert.equal(parsed.searchParams.get("q"), "a/b");
  assert.equal(parsed.searchParams.get("_citry_state_token"), "state-token");
  assert.equal(parsed.searchParams.get("_citry_protocol"), "citry-events/1");
  assert.deepEqual(JSON.parse(parsed.searchParams.get("_citry_capabilities")), {
    actions: ["render", "data", "state", "event", "redirect", "url"],
    renderers: ["vue-prepared/1"],
    swaps: ["morph"],
  });
});

test("GET rejects unrepresentable or reserved args before fetch and does not block the next call", async () => {
  const getDescriptor = { componentClassId: "Board_1", eventHandlers: { search: { httpMethod: "GET" } } };
  let fetched = 0;
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    eventBaseUrl: "/events/e/",
    host: basicHost(() => ({ ...contextFor(), descriptor: getDescriptor })),
    fetch: async (url) => {
      fetched += 1;
      const query = new URL(url, "https://example.test").searchParams;
      return resultResponse({
        requestId: query.get("_citry_request_id"),
        calls: [{ sendSequence: Number(query.get("_citry_send_sequence")) }],
      });
    },
  });
  const source = { stableId: "board", generation: 1 };
  await assert.rejects(bridge.send({ source, handler: "search", args: { nested: { x: 1 } } }), /flat GET/);
  await assert.rejects(bridge.send({ source, handler: "search", args: { empty: [] } }), /flat GET/);
  await assert.rejects(bridge.send({ source, handler: "search", args: { _citry_protocol: "bad" } }), /reserved/);
  await assert.rejects(bridge.send({ source, handler: "search", args: { bad: "\ud800" } }), /well-formed UTF-16/);
  await assert.rejects(
    bridge.send({ source, handler: "search", args: { bad: ["ok", "\udfff"] } }),
    /well-formed UTF-16/,
  );
  const malformedName = `bad${"\ud800"}`;
  await assert.rejects(
    bridge.send({ source, handler: "search", args: { [malformedName]: "value" } }),
    /name is not well-formed UTF-16/,
  );
  await assert.rejects(
    bridge.send({ source, handler: "search", stateUpdates: { draft: "must stay local" } }),
    /cannot send pending State/,
  );
  await bridge.send({ source, handler: "search", args: { ok: 1 } });
  assert.equal(fetched, 1);
});

test("GET preserves valid surrogate pairs", async () => {
  const getDescriptor = { componentClassId: "Board_1", eventHandlers: { search: { httpMethod: "GET" } } };
  let requestUrl;
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    eventBaseUrl: "/events/e/",
    host: basicHost(() => ({ ...contextFor(), descriptor: getDescriptor })),
    fetch: async (url) => {
      requestUrl = url;
      const query = new URL(url, "https://example.test").searchParams;
      return resultResponse({
        requestId: query.get("_citry_request_id"),
        calls: [{ sendSequence: Number(query.get("_citry_send_sequence")) }],
      });
    },
  });
  await bridge.send({
    source: { stableId: "board", generation: 1 },
    handler: "search",
    args: { emoji: "\ud83d\ude80" },
  });
  assert.equal(new URL(requestUrl, "https://example.test").searchParams.get("emoji"), "🚀");
});

test("allowBatching false POST uses the encoded per-event path", async () => {
  const isolatedDescriptor = {
    componentClassId: "Board / ü",
    eventHandlers: { "save / now": { httpMethod: "POST", allowBatching: false } },
  };
  let requested;
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/tenant/citry/ext/events/call",
    eventBaseUrl: "/tenant/citry/ext/events/e/",
    host: basicHost(() => ({ ...contextFor(), componentClassId: "Board / ü", descriptor: isolatedDescriptor })),
    fetch: async (url, init) => {
      requested = { url, init };
      return resultResponse(JSON.parse(init.body));
    },
  });
  await bridge.send({ source: { stableId: "board", generation: 1 }, handler: "save / now" });
  assert.equal(requested.url, "/tenant/citry/ext/events/e/Board%20%2F%20%C3%BC/save%20%2F%20now");
  assert.equal(requested.init.method, "POST");
});

test("isolated PUT and DELETE use their declared methods and per-event routes", async () => {
  for (const method of ["PUT", "DELETE"]) {
    const isolatedDescriptor = {
      componentClassId: "Board_1",
      eventHandlers: { change: { httpMethod: method, allowBatching: false } },
    };
    let requested;
    const bridge = bridgeModule.createVueEventsBridge({
      endpoint: "/events/call",
      eventBaseUrl: "/events/e/",
      host: basicHost(() => ({ ...contextFor(), descriptor: isolatedDescriptor })),
      csrf: { token: "csrf-token" },
      fetch: async (url, init) => {
        requested = { url, init };
        return resultResponse(JSON.parse(init.body));
      },
    });
    await bridge.send({ source: { stableId: `board-${method}`, generation: 1 }, handler: "change" });
    assert.equal(requested.url, "/events/e/Board_1/change");
    assert.equal(requested.init.method, method);
    assert.equal(requested.init.headers["X-CSRFToken"], "csrf-token");
    assert.equal(JSON.parse(requested.init.body).calls[0].handlerName, "change");
  }
});

test("browser-only forbidden methods reject before enqueue, State drafts, or fetch and leave the queue usable", async () => {
  for (const method of ["HEAD", "OPTIONS", "CONNECT", "TRACE", "TRACK"]) {
    const guardedDescriptor = {
      componentClassId: "Board_1",
      eventHandlers: {
        guarded: { httpMethod: method, usesState: true, allowBatching: false },
        valid: { httpMethod: "PUT", allowBatching: false },
      },
    };
    let enqueued = 0;
    let taken = 0;
    let fetched = 0;
    const host = basicHost(() => ({ ...contextFor(), descriptor: guardedDescriptor }));
    host.takePendingState = () => {
      taken += 1;
      return { draft: "preserved" };
    };
    const bridge = bridgeModule.createVueEventsBridge({
      endpoint: "/events/call",
      eventBaseUrl: "/events/e/",
      host,
      activity: () => ({
        enqueue() {
          enqueued += 1;
        },
        start() {},
        succeed() {},
        fail() {},
        finish() {},
      }),
      fetch: async (_url, init) => {
        fetched += 1;
        return resultResponse(JSON.parse(init.body));
      },
    });
    const source = { stableId: `board-${method}`, generation: 1 };
    await assert.rejects(bridge.send({ source, handler: "guarded" }), new RegExp(`${method}.*server-transport-only`));
    assert.equal(enqueued, 0);
    assert.equal(taken, 0);
    assert.equal(fetched, 0);
    await bridge.send({ source, handler: "valid" });
    assert.equal(enqueued, 1);
    assert.equal(fetched, 1);
  }
});

test("an attachment buffers inside the request lifetime, saves once, and rejects ordinary raw success", async () => {
  const downloadDescriptor = {
    componentClassId: "Board_1",
    eventHandlers: { download: { httpMethod: "POST", allowBatching: false } },
  };
  const clicks = [];
  const priorDocument = globalThis.document;
  const priorCreate = URL.createObjectURL;
  const priorRevoke = URL.revokeObjectURL;
  globalThis.document = {
    body: { append() {} },
    createElement: () => ({
      style: {},
      click() {
        clicks.push([this.download, this.href]);
      },
      remove() {},
    }),
  };
  URL.createObjectURL = () => "blob:test";
  URL.revokeObjectURL = (url) => clicks.push(["revoked", url]);
  let count = 0;
  try {
    const bridge = bridgeModule.createVueEventsBridge({
      endpoint: "/events",
      eventBaseUrl: "/events/e/",
      host: basicHost(() => ({ ...contextFor(), descriptor: downloadDescriptor })),
      fetch: async () => {
        count += 1;
        if (count === 1)
          return new Response("file", {
            headers: { "Content-Disposition": "attachment; filename*=UTF-8''caf%C3%A9.txt" },
          });
        if (count === 2)
          return new Response("file", { headers: { "Content-Disposition": "attachment; filename=report.txt" } });
        if (count === 3)
          return new Response("file", { headers: { "Content-Disposition": "attachment; filename*=UTF-8''bad%XX" } });
        if (count === 4)
          return new Response("not json", {
            status: 400,
            headers: { "Content-Disposition": 'attachment; filename="never.txt"' },
          });
        return new Response("plain text");
      },
    });
    const source = { stableId: "board", generation: 1 };
    assert.equal(await bridge.send({ source, handler: "download" }), undefined);
    assert.deepEqual(clicks, [
      ["café.txt", "blob:test"],
      ["revoked", "blob:test"],
    ]);
    assert.equal(await bridge.send({ source, handler: "download" }), undefined);
    assert.deepEqual(clicks.slice(2), [
      ["report.txt", "blob:test"],
      ["revoked", "blob:test"],
    ]);
    await assert.rejects(bridge.send({ source, handler: "download" }), /invalid encoded filename/);
    await assert.rejects(bridge.send({ source, handler: "download" }));
    assert.equal(clicks.length, 4);
    await assert.rejects(bridge.send({ source, handler: "download" }), /must be an attachment/);
  } finally {
    globalThis.document = priorDocument;
    URL.createObjectURL = priorCreate;
    URL.revokeObjectURL = priorRevoke;
  }
});

test("retirement while an attachment body is buffering settles without saving", async () => {
  const downloadDescriptor = {
    componentClassId: "Board_1",
    eventHandlers: { download: { httpMethod: "POST", allowBatching: false } },
  };
  let releaseBlob;
  let buffering;
  const bodyStarted = new Promise((resolve) => {
    buffering = resolve;
  });
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    eventBaseUrl: "/events/e/",
    host: basicHost(() => ({ ...contextFor(), descriptor: downloadDescriptor })),
    fetch: async () => ({
      ok: true,
      headers: new Headers({ "Content-Disposition": 'attachment; filename="report.txt"' }),
      blob: () => {
        buffering();
        return new Promise((resolve) => {
          releaseBlob = resolve;
        });
      },
    }),
  });
  const source = { stableId: "board", generation: 1 };
  const sent = bridge.send({ source, handler: "download" });
  await bodyStarted;
  bridge.retire(source);
  await assert.rejects(sent, /stale or retired/);
  releaseBlob(new Blob(["late"]));
  await new Promise((resolve) => setTimeout(resolve, 0));
});

test("timeout bounds attachment body buffering and releases the next queued call", async () => {
  const downloadDescriptor = {
    componentClassId: "Board_1",
    eventHandlers: { download: { httpMethod: "POST", allowBatching: false } },
  };
  let requests = 0;
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    eventBaseUrl: "/events/e/",
    host: basicHost(() => ({ ...contextFor(), descriptor: downloadDescriptor })),
    timeoutMs: 5,
    fetch: async (_url, init) => {
      requests += 1;
      if (requests === 1)
        return {
          ok: true,
          headers: new Headers({ "Content-Disposition": 'attachment; filename="stalled.txt"' }),
          blob: () => new Promise(() => {}),
        };
      return resultResponse(JSON.parse(init.body), [{ action: "data", value: "next" }]);
    },
  });
  const source = { stableId: "board", generation: 1 };
  const first = bridge.send({ source, handler: "download" });
  const second = bridge.send({ source, handler: "download" });
  await assert.rejects(first, /timed out/);
  assert.equal(await second, "next");
  assert.equal(requests, 2);
});

test("timeout bounds response decoding and releases the next queued call", async () => {
  let requests = 0;
  const fetch = async (_url, init) => {
    requests += 1;
    if (requests === 1) return { json: () => new Promise(() => {}) };
    return resultResponse(JSON.parse(init.body), [{ action: "data", value: "next" }]);
  };
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: basicHost(),
    fetch,
    timeoutMs: 10,
  });
  const source = { stableId: "board", generation: 1 };
  const first = bridge.send({ source, handler: "move" });
  const second = bridge.send({ source, handler: "move" });
  await assert.rejects(first, /timed out/);
  assert.equal(await second, "next");
  assert.equal(requests, 2);
});

test("retirement settles an active call when transport ignores abort", async () => {
  let started;
  const transportStarted = new Promise((resolve) => {
    started = resolve;
  });
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: basicHost(),
    fetch: async () => {
      started();
      return new Promise(() => {});
    },
  });
  const source = { stableId: "board", generation: 1 };
  const sent = bridge.send({ source, handler: "move" });
  await transportStarted;
  bridge.retire(source);
  await assert.rejects(sent, /stale or retired/);
});

test("retirement removes queued work before transport", async () => {
  let releaseFirst;
  const firstResponse = new Promise((resolve) => {
    releaseFirst = resolve;
  });
  const fetched = [];
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: basicHost((source) => contextFor(`server_${source.stableId}`)),
    fetch: async (_url, init) => {
      const envelope = JSON.parse(init.body);
      fetched.push(envelope.calls[0].callerRenderId);
      if (fetched.length === 1) return firstResponse;
      return resultResponse(envelope);
    },
  });
  const activeSource = { stableId: "one", generation: 1 };
  const retiredSource = { stableId: "two", generation: 1 };
  const active = bridge.send({ source: activeSource, handler: "move" });
  const queued = bridge.send({ source: retiredSource, handler: "move" });
  bridge.retire(retiredSource);
  await assert.rejects(queued, /stale or retired/);
  releaseFirst(resultResponse({ requestId: "vue_1", calls: [{ sendSequence: 1 }] }));
  await active;
  assert.deepEqual(fetched, ["server_one"]);
});

test("stale retirement does not cancel a replacement generation", async () => {
  let liveGeneration = 2;
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: basicHost((source) => (source.generation === liveGeneration ? contextFor() : null)),
    fetch: async (_url, init) => resultResponse(JSON.parse(init.body), [{ action: "data", value: 2 }]),
  });
  const replacement = { stableId: "board", generation: 2 };
  assert.equal(await bridge.send({ source: replacement, handler: "move" }), 2);
  bridge.retire({ stableId: "board", generation: 1 });
  assert.equal(await bridge.send({ source: replacement, handler: "move" }), 2);
  liveGeneration = 3;
});

test("retirement cancels detached delayed actions", async () => {
  const fired = [];
  const host = basicHost();
  host.dispatchEvent = (name) => fired.push(name);
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async (_url, init) =>
      resultResponse(JSON.parse(init.body), [{ action: "event", eventName: "late", delay: 0.03, wait: false }]),
  });
  const source = { stableId: "board", generation: 1 };
  const priorError = console.error;
  console.error = () => {};
  try {
    await bridge.send({ source, handler: "move" });
    bridge.retire(source);
    await new Promise((resolve) => setTimeout(resolve, 50));
  } finally {
    console.error = priorError;
  }
  assert.deepEqual(fired, []);
});

test("repeated mount and retirement resets owner sequence", async () => {
  const sequences = [];
  let generation = 1;
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: basicHost((source) => (source.generation === generation ? contextFor() : null)),
    fetch: async (_url, init) => {
      const envelope = JSON.parse(init.body);
      sequences.push(envelope.calls[0].sendSequence);
      return resultResponse(envelope);
    },
  });
  for (generation = 1; generation <= 25; generation += 1) {
    const source = { stableId: "board", generation };
    await bridge.send({ source, handler: "move" });
    bridge.retire(source);
  }
  assert.deepEqual(sequences, Array(25).fill(1));
});

test("app disposal settles queued and active work and is idempotent", async () => {
  let requests = 0;
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: basicHost(),
    fetch: async () => {
      requests += 1;
      return new Promise(() => {});
    },
  });
  const source = { stableId: "board", generation: 1 };
  const active = bridge.send({ source, handler: "move" });
  const queued = bridge.send({ source, handler: "move" });
  bridge.dispose();
  bridge.dispose();
  await assert.rejects(active, /disposed/);
  await assert.rejects(queued, /disposed/);
  await assert.rejects(bridge.send({ source, handler: "move" }), /stale or retired/);
  assert.equal(requests, 1);
});

test("an accepted render may remount its sender and still return Data", async () => {
  const source = { stableId: "board", generation: 1 };
  const transaction = {};
  let bridge;
  const host = {
    ...basicHost(),
    async prepareRender() {
      return { transaction };
    },
    abortRender() {},
    async commitRender() {
      bridge.retire(source, transaction);
    },
  };
  bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async (_url, init) =>
      resultResponse(JSON.parse(init.body), [
        { action: "render", target: "render:server_1", swap: "morph", renderer: "vue-prepared/1", prepared: {} },
        { action: "data", value: { accepted: true } },
      ]),
  });
  assert.deepEqual(await bridge.send({ source, handler: "move" }), { accepted: true });
});

test("an accepted render may remount its sender and still Dispatch from the new instance", async () => {
  // The Render retires the sender (a component-changing Render always does). The Dispatch after it
  // must still go out, and the host is told to follow the caller's place to its new instance.
  const source = { stableId: "board", generation: 1 };
  const transaction = {};
  const dispatched = [];
  let bridge;
  const host = {
    ...basicHost(),
    async prepareRender() {
      return { transaction };
    },
    abortRender() {},
    async commitRender() {
      bridge.retire(source, transaction);
    },
    dispatchEvent(name, detail, eventSource, followRemount) {
      dispatched.push({ name, detail, eventSource, followRemount });
    },
  };
  bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async (_url, init) =>
      resultResponse(JSON.parse(init.body), [
        { action: "render", target: "render:server_1", swap: "morph", renderer: "vue-prepared/1", prepared: {} },
        { action: "event", eventName: "Board:moved", detail: { to: 2 } },
      ]),
  });
  await bridge.send({ source, handler: "move" });
  assert.deepEqual(dispatched, [{ name: "Board:moved", detail: { to: 2 }, eventSource: source, followRemount: true }]);
});

// A host whose Render retires the sender, as a component-changing Render always does.
const remountingHost = (source, record, getBridge) => {
  const transaction = {};
  return {
    ...basicHost(),
    async prepareRender() {
      return { transaction };
    },
    abortRender() {},
    async commitRender() {
      getBridge().retire(source, transaction);
    },
    dispatchEvent(name, _detail, _eventSource, followRemount) {
      record.push({ action: "event", name, followRemount });
    },
    redirect(url) {
      record.push({ action: "redirect", url });
    },
    updateUrl(url) {
      record.push({ action: "url", url });
    },
  };
};
const remountingRender = {
  action: "render",
  target: "render:server_1",
  swap: "morph",
  renderer: "vue-prepared/1",
  prepared: {},
};

// A bridge whose first call replaces the caller (generation 1) with a new component
// (generation 2) and then schedules `laterActions`; every later call returns data 2. The host
// records each page change and stale event.
const replacingBridge = (laterActions) => {
  const record = [];
  const transaction = {};
  let generation = 1;
  let bridge;
  const host = {
    ...basicHost((source) =>
      source.generation === generation ? { ...contextFor(`server_${generation}`), descriptor } : null,
    ),
    async prepareRender() {
      return { transaction };
    },
    abortRender() {},
    async commitRender() {
      bridge.retire({ stableId: "board", generation: 1 }, transaction);
      generation = 2;
    },
    commitState(target, token) {
      record.push(`state:${target}:${token}`);
    },
    dispatchEvent(name) {
      record.push(`event:${name}`);
    },
    redirect(url) {
      record.push(`redirect:${url}`);
    },
    updateUrl(url, mode) {
      record.push(`url:${mode}:${url}`);
    },
    lifecycle(kind, _source, _event, detail) {
      if (kind === "stale") record.push(`stale:${detail.reason}`);
      return true;
    },
  };
  let calls = 0;
  bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async (_url, init) => {
      calls += 1;
      const envelope = JSON.parse(init.body);
      return resultResponse(
        envelope,
        calls === 1
          ? [remountingRender, ...laterActions, { action: "data", value: 1 }]
          : [{ action: "data", value: 2 }],
      );
    },
  });
  return { bridge, record };
};

// Sends the replacing call, then a call from the new component whose result is accepted before the
// first call's delayed actions are due, and returns what reached the page.
const newerResultAfterReplacement = async (laterActions) => {
  const { bridge, record } = replacingBridge(laterActions);
  assert.equal(await bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" }), 1);
  assert.equal(await bridge.send({ source: { stableId: "board", generation: 2 }, handler: "move" }), 2);
  record.push("newer result applied");
  await new Promise((resolve) => setTimeout(resolve, 400));
  return record;
};

const replacedCallerActions = {
  Dispatch: [{ action: "event", eventName: "old" }, "event:old"],
  PushUrl: [{ action: "url", url: "/old", mode: "push" }, "url:push:/old"],
  ReplaceUrl: [{ action: "url", url: "/old", mode: "replace" }, "url:replace:/old"],
  State: [
    { action: "state", targetRenderId: "server_7", stateToken: "old-token", publicState: {} },
    "state:server_7:old-token",
  ],
};

for (const [name, [action, applied]] of Object.entries(replacedCallerActions)) {
  test(`after a Render replaced the caller, a newer result drops a delayed ${name}`, async () => {
    const record = await newerResultAfterReplacement([{ ...action, delay: 0.3, wait: false }]);
    assert.deepEqual(record, ["newer result applied", "stale:epoch"]);
    assert.ok(!record.includes(applied));
  });
}

test("after a Render replaced the caller, a delayed Redirect runs even after a newer result", async () => {
  const record = await newerResultAfterReplacement([{ action: "redirect", url: "/saved", delay: 0.3, wait: false }]);
  assert.deepEqual(record, ["newer result applied", "redirect:/saved"]);
});

test("a delayed Redirect runs after a newer result for a caller that is still mounted", async () => {
  const record = [];
  const host = {
    ...basicHost(),
    redirect(url) {
      record.push(`redirect:${url}`);
    },
    dispatchEvent(name) {
      record.push(`event:${name}`);
    },
    lifecycle(kind, _source, _event, detail) {
      if (kind === "stale") record.push(`stale:${detail.reason}`);
      return true;
    },
  };
  let calls = 0;
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async (_url, init) => {
      calls += 1;
      const envelope = JSON.parse(init.body);
      return resultResponse(
        envelope,
        calls === 1
          ? [
              { action: "redirect", url: "/saved", delay: 0.3, wait: false },
              { action: "event", eventName: "old", delay: 0.3, wait: false },
              { action: "data", value: 1 },
            ]
          : [{ action: "data", value: 2 }],
      );
    },
  });
  const source = { stableId: "board", generation: 1 };
  assert.equal(await bridge.send({ source, handler: "move" }), 1);
  assert.equal(await bridge.send({ source, handler: "move" }), 2);
  record.push("newer result applied");
  await new Promise((resolve) => setTimeout(resolve, 400));
  // The newer result drops the event, but the redirect reports a result the server already
  // produced, so it still runs.
  assert.deepEqual(record, ["newer result applied", "redirect:/saved", "stale:epoch"]);
});

test("after a Render replaced the caller, applyActions on the new component counts as a newer result", async () => {
  const { bridge, record } = replacingBridge([{ action: "event", eventName: "old", delay: 0.3, wait: false }]);
  assert.equal(await bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" }), 1);
  await bridge.applyActions([{ action: "data", value: 3 }], { stableId: "board", generation: 2 });
  record.push("newer result applied");
  await new Promise((resolve) => setTimeout(resolve, 400));
  assert.deepEqual(record, ["newer result applied", "stale:epoch"]);
});

test("after a Render replaced the caller, delayed actions run when no newer result arrives", async () => {
  const { bridge, record } = replacingBridge([
    { action: "event", eventName: "saved", delay: 0.02, wait: false },
    { action: "url", url: "/saved", mode: "push", delay: 0.02, wait: false },
  ]);
  assert.equal(await bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" }), 1);
  await new Promise((resolve) => setTimeout(resolve, 60));
  assert.deepEqual(record, ["event:saved", "url:push:/saved"]);
});

test("delayed actions after a render that remounted the sender still run", async () => {
  const source = { stableId: "board", generation: 1 };
  const record = [];
  let bridge;
  bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: remountingHost(source, record, () => bridge),
    fetch: async (_url, init) =>
      resultResponse(JSON.parse(init.body), [
        remountingRender,
        { action: "event", eventName: "Board:moved", delay: 0.01 },
        { action: "url", url: "/moved", mode: "push", delay: 0.01 },
        { action: "redirect", url: "/next", delay: 0.01 },
      ]),
  });
  await bridge.send({ source, handler: "move" });
  assert.deepEqual(record, [
    { action: "event", name: "Board:moved", followRemount: true },
    { action: "url", url: "/moved" },
    { action: "redirect", url: "/next" },
  ]);
});

test("disposing the bridge cancels a delayed action that follows a remount", async () => {
  const source = { stableId: "board", generation: 1 };
  const record = [];
  let bridge;
  bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: remountingHost(source, record, () => bridge),
    fetch: async (_url, init) =>
      resultResponse(JSON.parse(init.body), [remountingRender, { action: "redirect", url: "/next", delay: 0.05 }]),
  });
  const sent = bridge.send({ source, handler: "move" });
  await new Promise((resolve) => setTimeout(resolve, 10));
  bridge.dispose();
  await assert.rejects(sent, /disposed/);
  assert.deepEqual(record, []);
});

test("page code that applies a remounting render can still Dispatch after it", async () => {
  const source = { stableId: "board", generation: 1 };
  const record = [];
  let bridge;
  bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: remountingHost(source, record, () => bridge),
  });
  await bridge.applyActions([remountingRender, { action: "event", eventName: "Board:moved" }], source);
  assert.deepEqual(record, [{ action: "event", name: "Board:moved", followRemount: true }]);
});

test("a Dispatch without an earlier remount keeps the sender's own instance", async () => {
  const source = { stableId: "board", generation: 1 };
  const dispatched = [];
  const host = {
    ...basicHost(),
    dispatchEvent(name, _detail, _eventSource, followRemount) {
      dispatched.push({ name, followRemount });
    },
  };
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async (_url, init) => resultResponse(JSON.parse(init.body), [{ action: "event", eventName: "Board:moved" }]),
  });
  await bridge.send({ source, handler: "move" });
  assert.deepEqual(dispatched, [{ name: "Board:moved", followRemount: false }]);
});

test("retirement during render preparation settles promptly and aborts a late transaction", async () => {
  const source = { stableId: "board", generation: 1 };
  let finishPrepare;
  const prepared = new Promise((resolve) => {
    finishPrepare = resolve;
  });
  const aborted = [];
  let commits = 0;
  const host = {
    ...basicHost(),
    prepareRender: () => prepared,
    abortRender(value) {
      if (value) aborted.push(value.transaction);
    },
    async commitRender() {
      commits += 1;
    },
  };
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async (_url, init) =>
      resultResponse(JSON.parse(init.body), [
        { action: "render", target: "render:server_1", swap: "morph", renderer: "vue-prepared/1", prepared: {} },
      ]),
  });
  const sent = bridge.send({ source, handler: "move" });
  await new Promise((resolve) => setTimeout(resolve, 0));
  bridge.retire(source);
  await assert.rejects(sent, /stale or retired/);
  const transaction = {};
  finishPrepare({ transaction });
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.deepEqual(aborted, [transaction]);
  assert.equal(commits, 0);
});

test("app disposal cancels an accepted render even with matching transaction attribution", async () => {
  const source = { stableId: "board", generation: 1 };
  const transaction = {};
  let bridge;
  let releaseCommit;
  const committing = new Promise((resolve) => {
    releaseCommit = resolve;
  });
  const host = {
    ...basicHost(),
    async prepareRender() {
      return { transaction };
    },
    abortRender() {},
    async commitRender() {
      bridge.retire(source, transaction);
      await committing;
    },
  };
  bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async (_url, init) =>
      resultResponse(JSON.parse(init.body), [
        { action: "render", target: "render:server_1", swap: "morph", renderer: "vue-prepared/1", prepared: {} },
      ]),
  });
  const sent = bridge.send({ source, handler: "move" });
  await new Promise((resolve) => setTimeout(resolve, 0));
  bridge.dispose();
  await assert.rejects(sent, /disposed/);
  releaseCommit();
});

test("native beforeUnmount reports the exact generation despite user cleanup failure", async () => {
  const clientSource = await readFile(new URL("../../../py/citry/citry/_vue/client.js", import.meta.url), "utf8");
  const vue = {
    reactive: (value) => value,
    shallowRef: (value) => ({ value }),
    defineComponent: (value) => value,
    createVNode() {},
    createTextVNode() {},
    resolveDirective: (name) => name,
    vModelCheckbox: {},
    vModelDynamic: {},
    vModelRadio: {},
    vModelSelect: {},
    vModelText: {},
  };
  const realm = {
    CitryVueFragments: { installFragmentManager() {} },
    document: { currentScript: null },
    queueMicrotask,
    Vue: vue,
  };
  realm.globalThis = realm;
  realm.window = realm;
  realm.structuredClone = (value) => {
    realm.__cloneJson = JSON.stringify(value);
    return vm.runInNewContext("JSON.parse(__cloneJson)", realm);
  };
  vm.runInNewContext(clientSource, realm);
  const helperContract = clientSource.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];
  const stable = realm.__citryRuntime;
  const asRealm = (value) => {
    realm.__json = JSON.stringify(value);
    return vm.runInNewContext("JSON.parse(__json)", realm);
  };
  stable.configure(
    asRealm({
      protocol: "citry-vue-prepared/1",
      appId: "app",
      revision: 0,
      rootId: "root",
      markers: [],
      occurrences: [
        {
          id: "root",
          typeKey: "Root",
          definitionId: "root-def",
          parentId: null,
          placementKey: null,
          serverData: {},
          preparedData: { calls: {}, callRuns: {} },
        },
      ],
    }),
  );
  realm.__helperContract = helperContract;
  const renderDefinition = vm.runInNewContext(
    `({
    render() {}, target: "ordinary-vnodes/1", helperContract: __helperContract,
    opaqueHtmlSites: [],
    directiveSignature: [], replacementSites: [], localCalls: [], localCallRuns: []
  })`,
    realm,
  );
  stable.registerDefinition("app", "root-def", renderDefinition);
  const incompleteHost = vm.runInNewContext("({onOccurrenceMounted() {}, beforeServerCallbacks() {}})", realm);
  assert.throws(() => stable.attachPreparedHost("app", incompleteHost), /invalid prepared host/);
  const unmounted = [];
  realm.__unmounted = unmounted;
  const preparedHost = vm.runInNewContext(
    `({
    onOccurrenceMounted() {},
    onOccurrenceUnmounted(value) { __unmounted.push({stableId: value.stableId, generation: value.generation}); },
    beforeServerCallbacks() {}
  })`,
    realm,
  );
  stable.attachPreparedHost("app", preparedHost);
  const type = stable.defineType("app", "Root", {
    beforeUnmount() {
      throw new Error("user cleanup");
    },
  });
  const instance = { citryId: "root" };
  type.beforeCreate.call(instance);
  type.created.call(instance);
  assert.throws(() => type.beforeUnmount.call(instance), /user cleanup/);
  assert.equal(unmounted.length, 1);
  assert.equal(unmounted[0].stableId, "root");
  assert.equal(unmounted[0].generation, 1);
  assert.equal(stable._apps.get("app").mounted.size, 0);
});

test("activity spans enqueue through application and normalizes retained errors", async () => {
  const calls = [];
  let reportedFailure;
  const activity = {
    enqueue(handler) {
      const intent = { handler };
      calls.push(["enqueue", handler]);
      return intent;
    },
    start(intent) {
      calls.push(["start", intent.handler]);
    },
    succeed(intent) {
      calls.push(["succeed", intent.handler]);
    },
    fail(intent, error) {
      reportedFailure = error;
      calls.push(["fail", intent.handler, error]);
    },
    finish(intent) {
      calls.push(["finish", intent.handler]);
    },
  };
  let release;
  const response = new Promise((resolve) => {
    release = resolve;
  });
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: basicHost(),
    activity: () => activity,
    fetch: async () => response,
  });
  const source = { stableId: "board", generation: 1 };
  const sent = bridge.send({ source, handler: "move" });
  assert.deepEqual(calls, [
    ["enqueue", "move"],
    ["start", "move"],
  ]);
  release(
    new Response(
      JSON.stringify({
        protocol: "citry-events/1",
        requestId: "vue_1",
        results: [
          {
            ok: false,
            sendSequence: 1,
            error: { status: 409, code: "conflict", message: "try again", fieldErrors: { move: "blocked" } },
          },
        ],
      }),
    ),
  );
  let rejection;
  await assert.rejects(sent, (error) => {
    rejection = error;
    return true;
  });
  assert.equal(bridge.isDeclarativeFailureHandled(rejection), true);
  assert.strictEqual(rejection, reportedFailure);
  assert.deepEqual(calls.slice(2), [
    ["fail", "move", { status: 409, code: "conflict", message: "try again", fieldErrors: { move: "blocked" } }],
    ["finish", "move"],
  ]);
});

test("queued retirement finishes activity without recording an error", async () => {
  const calls = [];
  const activity = {
    enqueue(handler) {
      calls.push(["enqueue", handler]);
      return { handler };
    },
    start(intent) {
      calls.push(["start", intent.handler]);
    },
    succeed(intent) {
      calls.push(["succeed", intent.handler]);
    },
    fail(intent, error) {
      calls.push(["fail", intent.handler, error]);
    },
    finish(intent) {
      calls.push(["finish", intent.handler]);
    },
  };
  let release;
  const response = new Promise((resolve) => {
    release = resolve;
  });
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: basicHost((source) => contextFor(`server_${source.stableId}`)),
    activity: () => activity,
    fetch: async () => response,
  });
  const firstSource = { stableId: "one", generation: 1 };
  const queuedSource = { stableId: "two", generation: 1 };
  const first = bridge.send({ source: firstSource, handler: "move" });
  const queued = bridge.send({ source: queuedSource, handler: "move" });
  bridge.retire(queuedSource);
  await assert.rejects(queued, /stale or retired/);
  assert.deepEqual(calls.filter((item) => item[1] === "move").slice(0, 4), [
    ["enqueue", "move"],
    ["start", "move"],
    ["enqueue", "move"],
    ["finish", "move"],
  ]);
  release(resultResponse({ requestId: "vue_1", calls: [{ sendSequence: 1 }] }));
  await first;
  assert.equal(
    calls.some((item) => item[0] === "fail"),
    false,
  );
});

test("timeout records a structured activity error and app disposal does not", async () => {
  const failures = [];
  let finishes = 0;
  const activity = {
    enqueue: (handler) => ({ handler }),
    start() {},
    succeed() {},
    fail(_intent, error) {
      failures.push(error);
    },
    finish() {
      finishes += 1;
    },
  };
  const source = { stableId: "board", generation: 1 };
  const timed = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: basicHost(),
    activity: () => activity,
    fetch: async () => new Promise(() => {}),
    timeoutMs: 5,
  });
  let timeoutFailure;
  await assert.rejects(timed.send({ source, handler: "move" }), (error) => {
    timeoutFailure = error;
    return /timed out/.test(error.message);
  });
  assert.equal(timed.isDeclarativeFailureHandled(timeoutFailure), true);
  assert.deepEqual(failures, [{ status: 0, code: "timeout", message: "The Vue event request timed out." }]);
  const disposed = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: basicHost(),
    activity: () => activity,
    fetch: async () => new Promise(() => {}),
  });
  const pending = disposed.send({ source, handler: "move" });
  disposed.dispose();
  let cancellation;
  await assert.rejects(pending, (error) => {
    cancellation = error;
    return /disposed/.test(error.message);
  });
  assert.equal(disposed.isDeclarativeFailureHandled(cancellation), true);
  assert.equal(failures.length, 1);
  assert.equal(finishes, 2);
});

test("dequeue snapshots pending State and restores it once on failure", async () => {
  const snapshots = [{ rows: [{ id: 1 }] }];
  const restored = [];
  let request;
  const host = basicHost();
  host.takePendingState = () => snapshots.shift();
  host.restorePendingState = (_source, updates) => restored.push(updates);
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async (_url, init) => {
      request = JSON.parse(init.body);
      return new Response(
        JSON.stringify({
          protocol: "citry-events/1",
          requestId: request.requestId,
          results: [{ ok: false, sendSequence: 1, error: { status: 409, code: "conflict", message: "retry" } }],
        }),
      );
    },
  });
  const pending = snapshots[0];
  await assert.rejects(bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" }));
  pending.rows[0].id = 9;
  assert.deepEqual(request.calls[0].stateUpdates, { rows: [{ id: 1 }] });
  assert.deepEqual(restored, [{ rows: [{ id: 1 }] }]);
});

const renderAction = (prepared = { occurrences: [{ serverData: { count: 1 } }] }) => ({
  action: "render",
  target: "render:server_1",
  swap: "morph",
  renderer: "vue-prepared/1",
  prepared,
});

// The prepared host freezes and keeps the result it preflights, the way client.js does.
const freezingHost = (seen) => ({
  ...basicHost(),
  preflightResult(result) {
    seen.push(result);
    const freeze = (value) => {
      if (value && typeof value === "object" && !Object.isFrozen(value)) {
        Object.freeze(value);
        for (const child of Object.values(value)) freeze(child);
      }
      return value;
    };
    return { result: freeze(result) };
  },
  async prepareRender() {
    return { transaction: {} };
  },
  abortRender() {},
  async commitRender() {},
});

test("a fetched result reaches host preflight as the parsed object, with no copy", async () => {
  const seen = [];
  let parsed;
  const fetch = async (_url, init) => {
    const envelope = JSON.parse(init.body);
    parsed = {
      protocol: "citry-events/1",
      requestId: envelope.requestId,
      results: [{ ok: true, sendSequence: envelope.calls[0].sendSequence, actions: [renderAction()] }],
    };
    return { ok: true, headers: new Headers(), json: async () => parsed };
  };
  const bridge = bridgeModule.createVueEventsBridge({ endpoint: "/events", host: freezingHost(seen), fetch });

  await bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" });

  assert.equal(seen.length, 1);
  assert.equal(seen[0], parsed.results[0]);
});

test("a transport result is copied once so the host never freezes the caller's object", async () => {
  const seen = [];
  let sent;
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: freezingHost(seen),
    transport: () => ({
      send(envelope) {
        sent = {
          protocol: "citry-events/1",
          requestId: envelope.requestId,
          results: [{ ok: true, sendSequence: envelope.calls[0].sendSequence, actions: [renderAction()] }],
        };
        return sent;
      },
    }),
    fetch: async () => {
      throw new Error("registered transport should replace fetch");
    },
  });

  await bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" });

  assert.equal(seen.length, 1);
  assert.notEqual(seen[0], sent.results[0]);
  assert.deepEqual(JSON.parse(JSON.stringify(seen[0])), JSON.parse(JSON.stringify(sent.results[0])));
  assert.equal(Object.isFrozen(seen[0].actions[0].prepared), true);
  assert.equal(Object.isFrozen(sent.results[0].actions[0].prepared), false);
  sent.results[0].actions[0].prepared.occurrences[0].serverData.count = 2;
  assert.equal(seen[0].actions[0].prepared.occurrences[0].serverData.count, 1);
});

test("a response that fails the strict JSON check reaches no host step and stays unfrozen", async () => {
  const calls = [];
  let parsed;
  const host = {
    ...basicHost(),
    preflightResult(result) {
      calls.push("preflight");
      return { result };
    },
    commitState() {
      calls.push("state");
    },
    async prepareRender() {
      calls.push("prepare");
      return { transaction: {} };
    },
    abortRender() {},
    async commitRender() {
      calls.push("render");
    },
  };
  const fetch = async (_url, init) => {
    const envelope = JSON.parse(init.body);
    // JSON.parse turns 1e999 into Infinity, which strict JSON rejects.
    parsed = {
      protocol: "citry-events/1",
      requestId: envelope.requestId,
      results: [
        {
          ok: true,
          sendSequence: envelope.calls[0].sendSequence,
          actions: [
            { action: "state", targetRenderId: "server_1", stateToken: "token_2", publicState: { moves: 2 } },
            renderAction({ occurrences: [{ serverData: { count: Number.POSITIVE_INFINITY } }] }),
          ],
        },
      ],
    };
    return { ok: true, headers: new Headers(), json: async () => parsed };
  };
  const bridge = bridgeModule.createVueEventsBridge({ endpoint: "/events", host, fetch });

  await assert.rejects(
    bridge.send({ source: { stableId: "board", generation: 1 }, handler: "move" }),
    /Invalid Events response: The value contains a non-finite number/,
  );
  assert.deepEqual(calls, []);
  assert.equal(Object.isFrozen(parsed.results[0].actions[1].prepared), false);
});

test("send options accept only timeout and a boolean wait, and reject before activity or transport", async () => {
  let enqueued = 0;
  const bodies = [];
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host: basicHost(),
    activity: () => ({
      enqueue: (handler) => {
        enqueued += 1;
        return { handler };
      },
      start() {},
      succeed() {},
      fail() {},
      finish() {},
    }),
    fetch: async (_url, init) => {
      const body = JSON.parse(init.body);
      bodies.push(body);
      return resultResponse(body, [{ action: "data", value: bodies.length }]);
    },
  });
  const source = { stableId: "board", generation: 1 };
  // `move` may render or change State, so it cannot skip the queue, and the error names the fix.
  await assert.rejects(
    bridge.send({ source, handler: "move", options: { wait: false } }),
    (error) =>
      error instanceof TypeError &&
      /'wait: false' needs a detached handler, and 'move' is not one/.test(error.message) &&
      error.message.includes("@event(detached=True)") &&
      error.message.includes("@event(latest_wins=True)"),
  );
  await assert.rejects(
    bridge.send({ source, handler: "move", options: { wait: "no" } }),
    (error) => error instanceof TypeError && /option 'wait' must be true or false/.test(error.message),
  );
  await assert.rejects(
    bridge.send({ source, handler: "move", options: { timout: 5 } }),
    /unknown option 'timout'; the options are 'timeout' and 'wait'/,
  );
  await assert.rejects(bridge.send({ source, handler: "move", options: 5 }), /send options must be an object/);
  await assert.rejects(bridge.send({ source, handler: "move", options: { timeout: 0 } }), /positive finite/);
  assert.equal(enqueued, 0);
  assert.equal(bodies.length, 0);

  // The bridge keeps its own copy, so a caller that edits its object after the call starts
  // changes nothing about that call.
  const options = { wait: true, timeout: 5_000 };
  const pending = bridge.send({ source, handler: "move", options });
  options.wait = false;
  assert.equal(await pending, 1);
  assert.equal(await bridge.send({ source, handler: "move", options: {} }), 2);
  assert.equal(enqueued, 2);
});

// `move` renders and changes State, so it stays queued; `peek` is declared detached.
const detachedDescriptor = (peek = {}) => ({
  componentClassId: "Board_1",
  eventHandlers: {
    move: { httpMethod: "POST", usesState: true },
    peek: { httpMethod: "POST", usesState: true, detached: true, ...peek },
  },
});

// A bridge whose fetch answers each handler with the actions `answers[handler]` returns, after
// waiting for `gates[handler]` when one is set. The host records page changes and lifecycle events.
const detachedBridge = ({ answers, gates = {}, peek, pending } = {}) => {
  const record = [];
  const lifecycle = [];
  const envelopes = [];
  const taken = [];
  const host = {
    ...basicHost(() => ({ ...contextFor(), descriptor: detachedDescriptor(peek) })),
    commitState(_target, token) {
      record.push(`state:${token}`);
    },
    dispatchEvent(name) {
      record.push(`event:${name}`);
    },
    redirect(url) {
      record.push(`redirect:${url}`);
    },
    lifecycle(kind, _source, event, detail) {
      lifecycle.push({ kind, event, detail });
      return true;
    },
    takePendingState(_source, handler) {
      taken.push(handler);
      return pending;
    },
  };
  const bridge = bridgeModule.createVueEventsBridge({
    endpoint: "/events",
    host,
    fetch: async (_url, init) => {
      const envelope = JSON.parse(init.body);
      envelopes.push(envelope);
      const handler = envelope.calls[0].handlerName;
      const gate = gates[handler]?.shift();
      if (gate) await gate;
      return resultResponse(envelope, answers[handler](envelope.calls[0]));
    },
  });
  return { bridge, record, lifecycle, envelopes, taken };
};

const gate = () => {
  let open;
  const promise = new Promise((resolve) => {
    open = resolve;
  });
  return { promise, open };
};

test("a wait: false call to a detached handler goes out while a queued call is in flight", async () => {
  const source = { stableId: "board", generation: 1 };
  const moveGate = gate();
  const setup = detachedBridge({
    answers: {
      move: () => [{ action: "data", value: "moved" }],
      peek: () => [{ action: "data", value: "peeked" }],
    },
    gates: { move: [moveGate.promise] },
    pending: { moves: 3 },
  });
  const move = setup.bridge.send({ source, handler: "move" });
  await sleep(5);
  // The queued call is still waiting for its response, and the detached one does not wait for it.
  assert.equal(await setup.bridge.send({ source, handler: "peek", options: { wait: false } }), "peeked");
  moveGate.open();
  assert.equal(await move, "moved");
  const [moveCall, peekCall] = setup.envelopes.map((envelope) => envelope.calls[0]);
  // The detached call still takes the next send number, so results stay ordered against each other.
  assert.deepEqual([moveCall.sendSequence, peekCall.sendSequence], [1, 2]);
  // Pending browser State writes ride only on the queued call: a detached handler returns no new
  // token, so the writes would be lost on it.
  assert.deepEqual(moveCall.stateUpdates, { moves: 3 });
  assert.equal("stateUpdates" in peekCall, false);
  assert.deepEqual(setup.taken, ["move"]);
});

test("a queued call to a detached handler waits its turn but leaves pending State alone", async () => {
  const source = { stableId: "board", generation: 1 };
  const moveGate = gate();
  const order = [];
  const setup = detachedBridge({
    answers: {
      move: () => {
        order.push("move");
        return [];
      },
      peek: () => {
        order.push("peek");
        return [{ action: "data", value: 1 }];
      },
    },
    gates: { move: [moveGate.promise] },
    pending: { moves: 3 },
  });
  const move = setup.bridge.send({ source, handler: "move" });
  const peek = setup.bridge.send({ source, handler: "peek" });
  await sleep(5);
  assert.equal(setup.envelopes.length, 1);
  moveGate.open();
  await move;
  assert.equal(await peek, 1);
  assert.deepEqual(order, ["move", "peek"]);
  assert.deepEqual(setup.taken, ["move"]);
});

test("a detached result does not drop a queued call's delayed actions", async () => {
  const source = { stableId: "board", generation: 1 };
  const setup = detachedBridge({
    answers: {
      move: () => [
        { action: "event", eventName: "moved", delay: 0.05, wait: false },
        { action: "data", value: 1 },
      ],
      peek: () => [{ action: "data", value: 2 }],
    },
  });
  assert.equal(await setup.bridge.send({ source, handler: "move" }), 1);
  // Accepted while the queued call's event waits on its delay.
  assert.equal(await setup.bridge.send({ source, handler: "peek", options: { wait: false } }), 2);
  await sleep(80);
  assert.deepEqual(setup.record, ["event:moved"]);
});

test("a newer queued result drops a detached call's delayed actions", async () => {
  const source = { stableId: "board", generation: 1 };
  const setup = detachedBridge({
    answers: {
      move: () => [{ action: "data", value: 1 }],
      peek: () => [
        { action: "event", eventName: "peeked", delay: 0.05, wait: false },
        { action: "redirect", url: "/after", delay: 0.05, wait: false },
        { action: "data", value: 2 },
      ],
    },
  });
  assert.equal(await setup.bridge.send({ source, handler: "peek", options: { wait: false } }), 2);
  assert.equal(await setup.bridge.send({ source, handler: "move" }), 1);
  await sleep(80);
  // The same rows apply as for a queued call: the event is dropped, and the redirect still runs.
  assert.deepEqual(setup.record, ["redirect:/after"]);
  assert.deepEqual(staleReasons(setup.lifecycle), ["epoch"]);
});

test("a detached result holding a render or State action is rejected before any action runs", async () => {
  const source = { stableId: "board", generation: 1 };
  for (const forbidden of [
    { action: "state", targetRenderId: "server_1", stateToken: "token_2", publicState: {} },
    { action: "render", target: "render:server_1", swap: "morph", renderer: "vue-prepared/1", prepared: {} },
  ]) {
    const setup = detachedBridge({
      answers: { move: () => [], peek: () => [{ action: "event", eventName: "first" }, forbidden] },
    });
    await assert.rejects(
      setup.bridge.send({ source, handler: "peek", options: { wait: false } }),
      new RegExp(`detached handler 'peek' returned a '${forbidden.action}' action`),
    );
    assert.deepEqual(setup.record, []);
  }
});

test("a call to a detached handler cannot carry State updates", async () => {
  const setup = detachedBridge({ answers: { move: () => [], peek: () => [] } });
  for (const options of [undefined, { wait: false }]) {
    await assert.rejects(
      setup.bridge.send({
        source: { stableId: "board", generation: 1 },
        handler: "peek",
        stateUpdates: { moves: 1 },
        options,
      }),
      (error) =>
        error instanceof TypeError &&
        /'peek' is detached, so a call to it cannot send State updates/.test(error.message),
    );
  }
  assert.equal(setup.envelopes.length, 0);
});

test("latestCallWins on a detached handler supersedes an older detached call", async () => {
  const source = { stableId: "board", generation: 1 };
  const firstGate = gate();
  let peeks = 0;
  const setup = detachedBridge({
    peek: { latestCallWins: true },
    answers: {
      move: () => [],
      peek: () => {
        peeks += 1;
        return [
          { action: "event", eventName: `peek${peeks}` },
          { action: "data", value: peeks },
        ];
      },
    },
    gates: { peek: [firstGate.promise] },
  });
  const first = setup.bridge.send({ source, handler: "peek", options: { wait: false } });
  first.catch(() => {});
  await sleep(5);
  const second = setup.bridge.send({ source, handler: "peek", options: { wait: false } });
  await assert.rejects(first, /superseded/);
  assert.equal(await second, 1);
  firstGate.open();
  await sleep(5);
  // The abandoned response changes nothing, and listeners hear why once.
  assert.deepEqual(setup.record, ["event:peek1"]);
  assert.deepEqual(staleReasons(setup.lifecycle), ["superseded"]);
});

test("retiring the caller or disposing the bridge cancels a detached call in flight", async () => {
  const source = { stableId: "board", generation: 1 };
  for (const [stop, reason] of [
    [(bridge) => bridge.retire(source), "retired"],
    [(bridge) => bridge.dispose(), "disposed"],
  ]) {
    const peekGate = gate();
    const setup = detachedBridge({
      answers: { move: () => [], peek: () => [{ action: "event", eventName: "late" }] },
      gates: { peek: [peekGate.promise] },
    });
    const peek = setup.bridge.send({ source, handler: "peek", options: { wait: false } });
    peek.catch(() => {});
    await sleep(5);
    stop(setup.bridge);
    await assert.rejects(peek, (error) => error.reason === reason);
    peekGate.open();
    await sleep(5);
    assert.deepEqual(setup.record, []);
    assert.deepEqual(staleReasons(setup.lifecycle), [reason]);
  }
});
