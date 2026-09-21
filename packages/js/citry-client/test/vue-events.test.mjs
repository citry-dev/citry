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
    commitState(_id, token) {
      context = { ...context, stateToken: token };
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
              { action: "state", targetRenderId: "server_1", stateToken: "token_2" },
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
    /marker targets are not implemented/,
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
      { action: "state", targetRenderId: "server_1", stateToken: "token_2" },
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
      { action: "state", targetRenderId: "server_1", stateToken: "token_2" },
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
  const stable = realm.CitryStable;
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
