import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

// The shipped, minified runtime is what a page loads, so the event-name rule is checked through
// it and not through the readable source.
const source = readFileSync(new URL("../../../py/citry/citry/_vue/runtime.js", import.meta.url), "utf8");

// Every event the runtime fires at the stub document, by name, and every error it logs.
const fired = [];
const errors = [];

// The runtime builds Vue and the fragment manager at load, so the stub document only has to answer
// the few calls those make; no page is ever mounted, so an Event action goes to `document`.
const document = {
  currentScript: null,
  readyState: "complete",
  documentElement: {},
  createElement: () => ({}),
  querySelector: () => null,
  querySelectorAll: () => [],
  addEventListener() {},
  removeEventListener() {},
  dispatchEvent: (event) => {
    fired.push(event.type);
    return true;
  },
  baseURI: "http://app.test/",
};
const context = {
  document,
  location: { href: "http://app.test/", origin: "http://app.test", assign() {} },
  history: { state: null, pushState() {}, replaceState() {} },
  console: { error: (...args) => errors.push(args.join(" ")), warn() {}, log() {} },
  MutationObserver: class {
    observe() {}
    disconnect() {}
    takeRecords() {
      return [];
    }
  },
  // A vm realm has no DOM events, so this stands in for the browser's `CustomEvent`.
  CustomEvent: class {
    constructor(type, init = {}) {
      this.type = type;
      this.detail = init.detail;
      this.bubbles = init.bubbles;
    }
  },
  queueMicrotask,
  setTimeout,
  clearTimeout,
  structuredClone,
  btoa,
  URL,
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

const dispatch = (eventName) =>
  context.Citry.events.applyActions(realm([{ action: "event", eventName, detail: { id: 1 } }]));

// Names the page, Vue or Citry already listen for, in the letter cases data could send.
const REFUSED = {
  "a standard element event": "click",
  "a form event": "submit",
  "a keyboard event": "keydown",
  "a standard name in another letter case": "Click",
  "a standard name in capitals": "KEYDOWN",
  "a document event written as the standard writes it": "DOMContentLoaded",
  "a window event": "message",
  "a Vue lifecycle name": "vue:mounted",
  "a Vue vnode hook name": "vnode-mounted",
  "a Vue vnode hook name in capitals": "VNODE-mounted",
  "a name with the citry: prefix in another letter case": "Citry:ready",
};

for (const [label, name] of Object.entries(REFUSED)) {
  test(`an Event action is refused before it fires: ${label}`, async () => {
    fired.length = 0;
    await assert.rejects(dispatch(name), /^Error: \[Citry\] refused to dispatch /);
    assert.deepEqual(fired, []);
  });
}

// Custom names, and names that only look like a standard one. A browser matches event names by
// exact code units, so none of these reaches a `click` or `keydown` listener.
const ALLOWED = {
  "a component-prefixed name": "MyCard:submit",
  "a hyphenated name": "order-saved",
  "a plain custom word": "saved",
  "a Vue component event name": "update:modelValue",
  "a Vue prop key, which no listener names": "onClick",
  "a leading space": " click",
  "a trailing space": "click ",
  "a Cyrillic letter in place of a Latin one": "сlick",
  "the Kelvin sign in place of K": "Keydown",
};

for (const [label, name] of Object.entries(ALLOWED)) {
  test(`an Event action with a custom name fires: ${label}`, async () => {
    fired.length = 0;
    await dispatch(name);
    assert.deepEqual(fired, [name]);
  });
}

// The protocol validator rejects an empty or non-string name before the action runs. Replacing it
// with one that accepts everything stands in for an action list that reaches the browser by a
// path the validator does not cover, so the runtime's own check is what decides.
test("an Event action whose name is not a non-empty string is refused by the runtime itself", async () => {
  const protocolEvents = context.CitryVueEvents;
  context.CitryVueEvents = { ...protocolEvents, assertValidActionList() {} };
  try {
    for (const name of ["", 42, null, "click", "citry:ready"]) {
      fired.length = 0;
      const actions = vm.runInNewContext("[{action: 'event', eventName: undefined}]", context);
      actions[0].eventName = name;
      await assert.rejects(context.Citry.events.applyActions(actions), /^Error: \[Citry\] refused /);
      assert.deepEqual(fired, [], `name ${String(name)}`);
    }
  } finally {
    context.CitryVueEvents = protocolEvents;
  }
});

test("a refused Event action marked wait: false is logged and the applyActions Promise resolves", async () => {
  fired.length = 0;
  errors.length = 0;
  await context.Citry.events.applyActions(realm([{ action: "event", eventName: "click", wait: false }]));
  // The action runs without holding up the call, so its failure arrives after the Promise settles.
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.deepEqual(fired, []);
  assert.equal(errors.length, 1);
  assert.match(errors[0], /refused to dispatch "click"/);
});
