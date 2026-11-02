import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

// The shipped, minified runtime is what a page loads, so the redirect rule is checked through it
// and not through the readable source.
const source = readFileSync(new URL("../../../py/citry/citry/_vue/runtime.js", import.meta.url), "utf8");

const assigned = [];
const errors = [];

// The runtime builds Vue and the fragment manager at load, so the stub document only has to answer
// the few calls those make; no page is ever mounted.
const document = {
  currentScript: null,
  readyState: "complete",
  documentElement: {},
  createElement: () => ({}),
  querySelector: () => null,
  querySelectorAll: () => [],
  addEventListener() {},
  removeEventListener() {},
  dispatchEvent: () => true,
};
const context = {
  document,
  location: { assign: (url) => assigned.push(url) },
  history: { state: null, pushState() {}, replaceState() {} },
  console: { error: (...args) => errors.push(args.join(" ")), warn() {}, log() {} },
  MutationObserver: class {
    observe() {}
    disconnect() {}
    takeRecords() {
      return [];
    }
  },
  queueMicrotask,
  setTimeout,
  clearTimeout,
  structuredClone,
  btoa,
};
context.globalThis = context;
context.window = context;
context.self = context;
vm.runInNewContext(source, context);

// The protocol validator checks that an action list is made of plain objects from the runtime's
// own realm, so a list built here is rebuilt inside the vm first.
const realm = (value) => {
  context.__json = JSON.stringify(value);
  return vm.runInNewContext("JSON.parse(__json)", context);
};

async function redirect(url) {
  assigned.length = 0;
  errors.length = 0;
  await context.Citry.events.applyActions(realm([{ action: "redirect", url }]));
}

// Escapes, so that no control character sits in the source file.
const REFUSED = {
  "javascript scheme": "javascript:void 0",
  "uppercase scheme": "JAVASCRIPT:void 0",
  "tab inside the scheme": "java\tscript:void 0",
  "newline inside the scheme": "java\nscript:void 0",
  "carriage return inside the scheme": "java\rscript:void 0",
  "leading space": " javascript:void 0",
  "leading C0 control": "\u0001javascript:void 0",
  "data scheme": "data:text/plain,x",
  "vbscript scheme": "vbscript:x",
};

for (const [name, url] of Object.entries(REFUSED)) {
  test(`a redirect to a scheme other than http(s) is refused: ${name}`, async () => {
    await redirect(url);
    assert.deepEqual(assigned, []);
    assert.equal(errors.length, 1);
    assert.match(errors[0], /^\[Citry\] refused a redirect to a URL with the "[a-z]+" scheme/);
  });
}

const FOLLOWED = {
  "absolute path": "/a",
  "relative path": "a/b",
  "query only": "?x=1",
  "fragment only": "#top",
  https: "https://example.com/",
  "uppercase http": "HTTP://example.com/",
};

for (const [name, url] of Object.entries(FOLLOWED)) {
  test(`a redirect to http(s) or a URL with no scheme is followed unchanged: ${name}`, async () => {
    await redirect(url);
    assert.deepEqual(assigned, [url]);
    assert.deepEqual(errors, []);
  });
}

// The protocol validator already rejects a non-string URL before the redirect runs. Replacing it
// with one that accepts everything stands in for an action list that reaches the browser by a path
// the validator does not cover, so the redirect's own check is what decides.
test("a redirect whose URL is not a string is refused with its own message", async () => {
  const protocolEvents = context.CitryVueEvents;
  context.CitryVueEvents = { ...protocolEvents, assertValidActionList() {} };
  try {
    for (const url of [42, null, undefined, { href: "/a" }]) {
      assigned.length = 0;
      errors.length = 0;
      const actions = vm.runInNewContext("[{action: 'redirect', url: undefined}]", context);
      actions[0].url = url;
      await context.Citry.events.applyActions(actions);
      assert.deepEqual(assigned, [], `url ${String(url)}`);
      assert.deepEqual(errors, ["[Citry] refused a redirect because its URL is not a string."], `url ${String(url)}`);
    }
  } finally {
    context.CitryVueEvents = protocolEvents;
  }
});
