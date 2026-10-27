import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import test from "node:test";
import vm from "node:vm";

// The `citry-on` directive runs the Vue listeners that carry Citry's own modifiers (`.outside`, `.window`,
// `.document`, `.debounce`, `.throttle`). These tests load the real `client.js` coordinator, start a prepared app
// through the real `startPrepared`, and take the directive from the registration it makes on the Vue app. Then they
// call its hooks (`mounted`, `beforeUpdate`, `updated`, `beforeUnmount`) the way Vue does, on a small DOM stand-in
// that dispatches events through the capture and bubble phases. Vue's own `withModifiers`, `withKeys` and
// `callWithAsyncErrorHandling` are the real ones from the installed `vue` package, so key names, `.stop`, `.prevent`
// and error reporting behave as in a browser. What Node cannot show is a real layout: visibility comes from stubs.

const require = createRequire(import.meta.url);
const RealVue = require("vue");
const source = await readFile(new URL("../../../py/citry/citry/_vue/client.js", import.meta.url), "utf8");
const helperContract = source.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];

// A clock the tests move by hand, standing in for `performance.now()`, `setTimeout` and `clearTimeout`.
function createClock() {
  let now = 1000;
  let nextId = 1;
  const timers = new Map();
  return {
    now: () => now,
    setTimeout(callback, delay) {
      const id = nextId++;
      timers.set(id, { callback, due: now + delay });
      return id;
    },
    clearTimeout(id) {
      timers.delete(id);
    },
    pending: () => timers.size,
    // Runs every timer that falls due within `milliseconds`, in order, with `now` set to its due time.
    tick(milliseconds) {
      const end = now + milliseconds;
      for (;;) {
        let nextTimer = null;
        for (const [id, timer] of timers)
          if (timer.due <= end && (!nextTimer || timer.due < nextTimer[1].due)) nextTimer = [id, timer];
        if (!nextTimer) break;
        timers.delete(nextTimer[0]);
        now = nextTimer[1].due;
        nextTimer[1].callback();
      }
      now = end;
    },
  };
}

// The listeners of each event target, with the options each was added with.
const registry = new WeakMap();
const PASSIVE_BY_DEFAULT = new Set(["touchstart", "touchmove", "wheel", "mousewheel"]);

function addListener(target, type, fn, options) {
  const normalized = typeof options === "boolean" ? { capture: options } : { ...options };
  const list = registry.get(target) ?? [];
  registry.set(target, list);
  // Like the DOM, adding the same function for the same type and phase twice does nothing.
  if (list.some((item) => item.type === type && item.fn === fn && !!item.options.capture === !!normalized.capture))
    return;
  list.push({ type, fn, options: normalized });
  if (target.isDocument && normalized.capture && normalized.passive) {
    const onWindow = registry.get(target.parent) ?? [];
    if (onWindow.some((item) => item.fn === fn && item.type === type && item.options.capture))
      numberingListeners.add(fn);
  }
}

function removeListener(target, type, fn, options) {
  const capture = typeof options === "boolean" ? options : !!options?.capture;
  const list = registry.get(target) ?? [];
  const index = list.findIndex((item) => item.type === type && item.fn === fn && !!item.options.capture === capture);
  if (index >= 0) list.splice(index, 1);
}

const allListenersOf = (target, type) => (registry.get(target) ?? []).filter((item) => !type || item.type === type);
// The runtime numbers each event in a passive capture listener that it adds once per event type on both `window`
// and `document`. The tests look at the listeners each directive adds, so those are left out.
const numberingListeners = new WeakSet();
const listenersOf = (target, type) => allListenersOf(target, type).filter((item) => !numberingListeners.has(item.fn));

class FakeNode {
  constructor(name, parent = null) {
    this.name = name;
    this.parent = parent;
    this.visibleCalls = [];
    this.hidden = false;
  }
  addEventListener(type, fn, options) {
    addListener(this, type, fn, options);
  }
  removeEventListener(type, fn, options) {
    removeListener(this, type, fn, options);
  }
  get isConnected() {
    let node = this;
    while (node.parent) node = node.parent;
    return node.isDocument === true || node.isWindow === true;
  }
  // The document for an element on the page; otherwise the top of its tree, such as a shadow root.
  getRootNode() {
    let node = this;
    while (node.parent && !node.isDocument) node = node.parent;
    return node;
  }
  checkVisibility(...args) {
    this.visibleCalls.push(args);
    return !this.hidden;
  }
}

// Sends an event through the capture phase (window down to the target) and then the bubble phase (target up to
// window), honoring `stopPropagation()`, `once` and `passive` the way a browser does. The path is fixed when the
// event starts, as `composedPath()` is, so a handler that detaches the target does not change it.
function dispatch(target, type, init = {}, clock) {
  const path = [];
  for (let node = target; node; node = node.parent) {
    path.push(node);
    // A `load` event never reaches `window`.
    if (node.isDocument && init.stopAtDocument) break;
  }
  const event = {
    type,
    target,
    currentTarget: null,
    timeStamp: clock.now(),
    eventPhase: 0,
    defaultPrevented: false,
    stopped: false,
    ...init,
    composedPath: () => [...path],
    stopPropagation() {
      this.stopped = true;
    },
    preventDefault() {
      if (!this.currentPassive) this.defaultPrevented = true;
    },
  };
  const run = (node, capture) => {
    event.currentTarget = node;
    for (const item of [...allListenersOf(node, type)]) {
      if (!!item.options.capture !== capture || !allListenersOf(node, type).includes(item)) continue;
      if (item.options.once) removeListener(node, type, item.fn, item.options);
      // Browsers make touch and wheel listeners on window, document and body passive unless asked otherwise.
      event.currentPassive =
        item.options.passive ?? ((node.isWindow || node.isDocument) && PASSIVE_BY_DEFAULT.has(type));
      // Like a browser, `window.event` is the event while a listener runs, and unset for a listener inside a
      // shadow root, which `hideEvent` stands in for.
      const windowNode = path.at(-1).isWindow ? path.at(-1) : null;
      const outer = windowNode?.event;
      if (windowNode) windowNode.event = init.hideEvent ? undefined : event;
      event.eventPhase = node === target ? 2 : capture ? 1 : 3;
      try {
        item.fn(event);
      } finally {
        // A nested dispatch gives the outer event back, as browsers do.
        if (windowNode) windowNode.event = outer;
      }
    }
  };
  for (const node of [...path].reverse()) {
    if (event.stopped) break;
    run(node, true);
  }
  for (const node of path) {
    if (event.stopped) break;
    run(node, false);
  }
  event.currentTarget = null;
  event.eventPhase = 0;
  return event;
}

// Builds a page: window > document > body > panel (the element under test) > inner, plus outer (a sibling of panel).
async function createPage() {
  const clock = createClock();
  const directives = new Map();
  class Element {}
  const app = {
    component() {},
    directive(name, definition) {
      directives.set(name, definition);
    },
    use() {},
    config: { globalProperties: {} },
    // Stops the start once every directive is registered; the tests need nothing past that.
    mount() {
      throw new Error("STOP AFTER REGISTRATION");
    },
    unmount() {},
  };
  const context = {
    CitryVueFragments: { installFragmentManager() {} },
    Element,
    Node: class {},
    location: { assign() {} },
    history: { state: null },
    queueMicrotask,
    btoa,
    console,
    CustomEvent: class {},
    performance: { now: clock.now },
    setTimeout: clock.setTimeout,
    clearTimeout: clock.clearTimeout,
    Vue: { ...RealVue, createApp: () => app, createSSRApp: () => app },
  };
  context.globalThis = context;
  context.window = context;
  context.isWindow = true;
  context.addEventListener = (type, fn, options) => addListener(context, type, fn, options);
  context.removeEventListener = (type, fn, options) => removeListener(context, type, fn, options);
  const document = new FakeNode("document", context);
  document.isDocument = true;
  context.document = Object.assign(document, { currentScript: null, dispatchEvent() {} });
  const realm = (value) => {
    context.__json = JSON.stringify(value);
    return vm.runInNewContext("JSON.parse(__json)", context);
  };
  context.structuredClone = realm;
  vm.runInNewContext(source, context);

  // The definition declares one `v-citry-on` directive, so starting also proves the runtime accepts what the
  // compiler writes into a directive signature.
  const signature = [
    { siteId: "citryDirective012abcD0", name: "v-citry-on", arg: "keydown", modifiers: ["escape", "window"] },
  ];
  const asset = {
    id: "listener-definition",
    url: "/listener-definition.mjs",
    sha256: "0".repeat(64),
    target: "ordinary-vnodes/1",
    helperContract,
    dynamicElements: [],
    directiveSignature: signature,
    replacementSites: [],
    localCalls: [],
    localCallRuns: [],
    opaqueHtmlSites: [],
    runtimeEventSites: [],
  };
  // The script the page would load registers this object; here it is already in place, so nothing is fetched.
  const loaded = realm({
    target: asset.target,
    helperContract,
    dynamicElements: [],
    directiveSignature: signature,
    replacementSites: [],
    localCalls: [],
    localCallRuns: [],
    opaqueHtmlSites: [],
    runtimeEventSites: [],
  });
  loaded.render = vm.runInNewContext("(function () {})", context);
  context.__citryRuntimeDefinitions = { [asset.id]: loaded };
  const configuration = realm({
    manifest: {
      protocol: "citry-vue-prepared/1",
      appId: "listener-app",
      revision: 0,
      rootId: "root",
      markers: [],
      scripts: [],
      styles: [],
      typePolicies: [],
      definitions: [asset],
      occurrences: [
        {
          id: "root",
          typeKey: "Root",
          definitionId: asset.id,
          parentId: null,
          placementKey: null,
          serverData: {},
          preparedData: { calls: {}, callRuns: {} },
        },
      ],
    },
    tags: { Root: "c-root" },
  });
  configuration.host = new Element();
  await assert.rejects(context.__citryRuntime.startPrepared(configuration), /STOP AFTER REGISTRATION/);
  const directive = directives.get("citry-on");
  assert.ok(directive, "startPrepared registers the citry-on directive");

  const body = new FakeNode("body", document);
  const panel = new FakeNode("panel", body);
  const inner = new FakeNode("inner", panel);
  const outer = new FakeNode("outer", body);
  const errors = [];
  const instance = {
    parent: null,
    proxy: { name: "component" },
    appContext: {
      config: {
        errorHandler(error, proxy, info) {
          errors.push({ error, proxy, info });
        },
      },
    },
  };

  // Mounts one `citry-on` directive the way Vue would for an element that carries
  // `@event.modifiers="handler"`: `modifiers` lists the compiler's tokens, and the handler sits in the vnode props.
  function mount({ arg = "click", modifiers = [], handler, element = panel, id = "0" } = {}) {
    const calls = [];
    const makeVnode = (fn) => ({ props: { ["onCitryOn" + id]: fn } });
    let currentId = id;
    // Vue gives each hook a new binding whose `oldValue` is the previous render's value.
    const makeBinding = (nextArg, nextModifiers, nextId = currentId) => {
      const binding = {
        arg: nextArg,
        modifiers: Object.fromEntries(nextModifiers.map((name) => [name, true])),
        value: nextId,
        oldValue: currentId,
        instance: { $: instance },
      };
      currentId = nextId;
      return binding;
    };
    const record = (event) => calls.push(event);
    let vnode = makeVnode(handler ?? record);
    let binding = makeBinding(arg, modifiers);
    binding.oldValue = undefined;
    directive.mounted(element, binding, vnode);
    return {
      calls,
      record,
      element,
      // An update as Vue runs it: `beforeUpdate`, the patch, then `updated`.
      beforeUpdate({
        handler: fn = handler ?? record,
        arg: nextArg = arg,
        modifiers: nextModifiers = modifiers,
        id: nextId = currentId,
      } = {}) {
        vnode = { props: { ["onCitryOn" + nextId]: fn } };
        binding = makeBinding(nextArg, nextModifiers, nextId);
        directive.beforeUpdate(element, binding, vnode);
      },
      updated() {
        directive.updated(element, binding, vnode);
      },
      update(options) {
        this.beforeUpdate(options);
        this.updated();
      },
      unmount() {
        directive.beforeUnmount(element, binding, vnode);
      },
    };
  }

  return {
    clock,
    context,
    window: context,
    document,
    body,
    panel,
    inner,
    outer,
    errors,
    proxy: instance.proxy,
    instance,
    mount,
    fire: (target, type, init) => dispatch(target, type, init, clock),
  };
}

test("debounce restarts on each event and runs once, with the last event", async () => {
  const page = await createPage();
  const listener = page.mount({ modifiers: ["debounce-300ms"] });
  const first = page.fire(page.panel, "click");
  page.clock.tick(200);
  const second = page.fire(page.panel, "click");
  page.clock.tick(200);
  assert.equal(listener.calls.length, 0, "400 ms after the first event, only 200 ms after the second");
  page.clock.tick(100);
  assert.deepEqual(listener.calls, [second]);
  assert.notEqual(listener.calls[0], first);
  // The event has finished by then, so a handler cannot read its current target.
  assert.equal(listener.calls[0].currentTarget, null);
  page.clock.tick(1000);
  assert.equal(listener.calls.length, 1);
});

test("throttle runs the first event and drops the rest of its interval", async () => {
  const page = await createPage();
  const listener = page.mount({ modifiers: ["throttle-250ms"] });
  const first = page.fire(page.panel, "click");
  assert.deepEqual(listener.calls, [first], "the first event runs at once");
  page.clock.tick(100);
  page.fire(page.panel, "click");
  page.clock.tick(149);
  page.fire(page.panel, "click");
  assert.equal(listener.calls.length, 1, "events inside the interval are dropped");
  page.clock.tick(1);
  const fourth = page.fire(page.panel, "click");
  assert.deepEqual(listener.calls, [first, fourth], "an event exactly one interval later runs");
});

test("debounce and throttle together drop events inside the throttle interval, then debounce", async () => {
  const page = await createPage();
  const listener = page.mount({ modifiers: ["debounce-100ms", "throttle-300ms"] });
  const first = page.fire(page.panel, "click");
  page.clock.tick(50);
  page.fire(page.panel, "click");
  page.clock.tick(50);
  assert.deepEqual(listener.calls, [first], "the second event never restarted the debounce");
  page.clock.tick(100);
  page.fire(page.panel, "click");
  assert.equal(listener.calls.length, 1, "200 ms after the first event is still inside the throttle interval");
  page.clock.tick(100);
  const fourth = page.fire(page.panel, "click");
  assert.equal(listener.calls.length, 1, "the debounced call waits");
  page.clock.tick(100);
  assert.deepEqual(listener.calls, [first, fourth]);
});

test("an update keeps a pending debounced call and runs the newest handler", async () => {
  const page = await createPage();
  const oldCalls = [];
  const newCalls = [];
  const listener = page.mount({ modifiers: ["debounce-300ms"], handler: (event) => oldCalls.push(event) });
  const event = page.fire(page.panel, "click");
  page.clock.tick(100);
  listener.update({ handler: (value) => newCalls.push(value) });
  assert.equal(page.clock.pending(), 1, "the update kept the pending call");
  page.clock.tick(199);
  assert.equal(newCalls.length, 0, "the update did not restart the wait");
  page.clock.tick(1);
  assert.deepEqual(newCalls, [event]);
  assert.deepEqual(oldCalls, []);
  assert.equal(listenersOf(page.panel, "click").length, 1, "the update kept the same listener");
});

test("an event that arrives during an update already runs the newest handler", async () => {
  const page = await createPage();
  const oldCalls = [];
  const newCalls = [];
  const plain = page.mount({ handler: (event) => oldCalls.push(event) });
  plain.beforeUpdate({ handler: (event) => newCalls.push(event) });
  // Between Vue's `beforeUpdate` and `updated` hooks, while the patch runs.
  const during = page.fire(page.panel, "click");
  plain.updated();
  assert.deepEqual(newCalls, [during]);
  assert.deepEqual(oldCalls, []);

  const debounced = await createPage();
  const staleCalls = [];
  const freshCalls = [];
  const slow = debounced.mount({ modifiers: ["debounce-100ms"], handler: (event) => staleCalls.push(event) });
  slow.beforeUpdate({ handler: (event) => freshCalls.push(event) });
  const arriving = debounced.fire(debounced.panel, "click");
  slow.updated();
  debounced.clock.tick(100);
  assert.deepEqual(freshCalls, [arriving], "the debounced call reads the handler when it runs");
  assert.deepEqual(staleCalls, []);
});

test("unmount cancels a pending call and removes the listener", async () => {
  const page = await createPage();
  const listener = page.mount({ modifiers: ["debounce-300ms"] });
  page.fire(page.panel, "click");
  assert.equal(page.clock.pending(), 1);
  listener.unmount();
  assert.equal(page.clock.pending(), 0, "the pending timer is cleared");
  assert.equal(listenersOf(page.panel).length, 0, "the listener is removed");
  page.clock.tick(1000);
  page.fire(page.panel, "click");
  assert.deepEqual(listener.calls, []);

  const outside = page.mount({ modifiers: ["outside"] });
  // An outside listener is a bubble-phase listener plus a capture-phase one that records the start of each event.
  assert.equal(listenersOf(page.document, "click").length, 2);
  outside.unmount();
  assert.equal(listenersOf(page.document, "click").length, 0, "both outside listeners on document are removed too");
});

test("two listeners on one element keep separate state", async () => {
  const page = await createPage();
  const clicks = page.mount({ arg: "click", modifiers: ["debounce-100ms"], id: "0" });
  const keys = page.mount({ arg: "keydown", modifiers: ["window"], id: "1" });
  clicks.unmount();
  assert.equal(listenersOf(page.panel, "click").length, 0);
  assert.equal(listenersOf(page.window, "keydown").length, 1, "the other listener stays");
  keys.unmount();
  assert.equal(listenersOf(page.window).length, 0);
});

test(".window and .document listen on their own target, not the element", async () => {
  const page = await createPage();
  const onWindow = page.mount({ arg: "resize", modifiers: ["window"] });
  const onDocument = page.mount({ arg: "selectionchange", modifiers: ["document"], id: "1" });
  assert.equal(listenersOf(page.window, "resize").length, 1);
  assert.equal(listenersOf(page.document, "selectionchange").length, 1);
  assert.equal(listenersOf(page.panel).length, 0);
  const resized = page.fire(page.window, "resize");
  const selected = page.fire(page.document, "selectionchange");
  assert.deepEqual(onWindow.calls, [resized]);
  assert.deepEqual(onDocument.calls, [selected]);
  // An event on the element bubbles up to both, so each still sees it as it would in a browser.
  page.fire(page.panel, "resize");
  assert.equal(onWindow.calls.length, 2);
});

test(".prevent on window or document is not passive, so it can cancel a touch or wheel event", async () => {
  const page = await createPage();
  const onWindow = page.mount({ arg: "wheel", modifiers: ["window", "prevent"], handler: () => {} });
  assert.equal(listenersOf(page.window, "wheel")[0].options.passive, false);
  assert.equal(page.fire(page.panel, "wheel").defaultPrevented, true, "the wheel event was cancelled");
  onWindow.unmount();

  const onDocument = page.mount({ arg: "touchstart", modifiers: ["document", "prevent"], handler: () => {} });
  assert.equal(listenersOf(page.document, "touchstart")[0].options.passive, false);
  assert.equal(page.fire(page.panel, "touchstart").defaultPrevented, true);
  onDocument.unmount();

  // Without `.prevent` the listener leaves the browser's passive default alone.
  page.mount({ arg: "wheel", modifiers: ["window"], handler: (event) => event.preventDefault() });
  assert.equal("passive" in listenersOf(page.window, "wheel")[0].options, false);
  assert.equal(page.fire(page.panel, "wheel").defaultPrevented, false, "a default passive listener cannot cancel");

  // On the element itself `.prevent` needs no option, and `.passive` and `.capture` become options. `.once` is not
  // one: the listener removes itself, so an event it ignores does not use it up.
  const onElement = page.mount({ arg: "click", modifiers: ["prevent"], id: "2", handler: () => {} });
  assert.equal("passive" in listenersOf(page.panel, "click")[0].options, false);
  onElement.unmount();
  page.mount({ arg: "scroll", modifiers: ["passive", "capture", "once"], id: "3" });
  assert.deepEqual(listenersOf(page.panel, "scroll")[0].options, { capture: true, passive: true });
});

test(".outside ignores an event inside the element and accepts one from outside", async () => {
  const page = await createPage();
  const listener = page.mount({ modifiers: ["outside"] });
  assert.equal(listenersOf(page.panel).length, 0, "it does not listen on the element");
  const onDocument = listenersOf(page.document, "click");
  assert.equal(onDocument.filter((item) => !item.options.capture).length, 1, "it listens in the bubble phase");
  assert.equal(onDocument.filter((item) => item.options.capture).length, 1, "and records each event's start");
  page.fire(page.panel, "click");
  page.fire(page.inner, "click");
  assert.deepEqual(listener.calls, [], "events on the element and inside it are ignored");
  const fromOuter = page.fire(page.outer, "click");
  const fromBody = page.fire(page.body, "click");
  assert.deepEqual(listener.calls, [fromOuter, fromBody]);
  // Content moved out of the element's subtree (a teleport) counts as outside.
  const teleported = new FakeNode("teleported", page.body);
  const fromTeleported = page.fire(teleported, "click");
  assert.equal(listener.calls.at(-1), fromTeleported);
});

test(".outside still sees an outside event after an inside handler stopped an inside one", async () => {
  const page = await createPage();
  const listener = page.mount({ modifiers: ["outside"] });
  page.inner.addEventListener("click", (event) => event.stopPropagation());
  page.fire(page.inner, "click");
  assert.deepEqual(listener.calls, [], "the stopped inside event never reaches document");
  const outside = page.fire(page.outer, "click");
  assert.deepEqual(listener.calls, [outside], "a later outside event is accepted");
});

test(".outside counts an event as inside when a handler removes its target from the element", async () => {
  const page = await createPage();
  const listener = page.mount({ modifiers: ["outside"] });
  page.inner.addEventListener("click", () => {
    page.inner.parent = null;
  });
  page.fire(page.inner, "click");
  assert.equal(page.inner.isConnected, false, "the handler removed its target");
  assert.deepEqual(listener.calls, [], "the event's path was fixed when it started, so it is still inside");
});

test(".outside runs after the handlers on the event's path, so a toggle button outside the element works", async () => {
  const page = await createPage();
  const order = [];
  page.outer.addEventListener("click", () => order.push("button"));
  const listener = page.mount({ modifiers: ["outside"], handler: () => order.push("outside") });
  page.fire(page.outer, "click");
  assert.deepEqual(order, ["button", "outside"]);
  // An outside handler that stops the event keeps the outside listener from running.
  page.outer.addEventListener("click", (event) => event.stopPropagation());
  page.fire(page.outer, "click");
  assert.deepEqual(order, ["button", "outside", "button"]);
  assert.equal(listener.calls.length, 0);
});

test(".outside leaves a panel open when the toggle button outside it opens it, and the button closes it again", async () => {
  const page = await createPage();
  let open = false;
  // Vue applies a state change before the next listener of the same event runs, so the panel's visibility follows
  // `open` between the button's listener and the `.outside` one.
  const setOpen = (value) => {
    open = value;
    page.panel.hidden = !open;
  };
  setOpen(false);
  page.outer.addEventListener("click", () => setOpen(!open));
  const listener = page.mount({ modifiers: ["outside"], handler: () => setOpen(false) });

  // The first click opens the panel. It was hidden when the click started, so the outside handler does not run.
  page.fire(page.outer, "click");
  assert.equal(open, true, "the button opened the panel and the outside handler did not close it");
  assert.deepEqual(listener.calls, []);

  // The second click: the panel was visible when it started, so the outside handler runs after the button closed it.
  page.fire(page.outer, "click");
  assert.equal(open, false, "the second click closed the panel");

  // A click elsewhere closes an open panel, and a click inside leaves it open.
  setOpen(true);
  page.fire(page.inner, "click");
  assert.equal(open, true);
  page.fire(page.body, "click");
  assert.equal(open, false);
});

test(".outside skips the handler while the element is hidden, checked when the event arrives", async () => {
  const page = await createPage();
  const listener = page.mount({ modifiers: ["outside"] });
  page.panel.hidden = true;
  page.fire(page.outer, "click");
  assert.deepEqual(listener.calls, [], "a hidden element does not react");
  assert.deepEqual(page.panel.visibleCalls.at(-1), [], "checkVisibility() uses its default options");
  page.panel.hidden = false;
  const shown = page.fire(page.outer, "click");
  assert.deepEqual(listener.calls, [shown], "the listener stayed attached, so showing the element is enough");
  // An element that left the page does not react either.
  const detached = new FakeNode("detached", null);
  const lone = page.mount({ modifiers: ["outside"], element: detached, id: "1" });
  page.fire(page.outer, "click");
  assert.deepEqual(lone.calls, []);
});

test(".outside falls back to the element's boxes where checkVisibility is missing", async () => {
  const page = await createPage();
  const rects = [];
  const element = new FakeNode("legacy", page.body);
  element.checkVisibility = undefined;
  element.getClientRects = () => rects;
  const listener = page.mount({ modifiers: ["outside"], element });
  page.fire(page.outer, "click");
  assert.deepEqual(listener.calls, [], "no boxes means display none, so the handler is skipped");
  rects.push({ width: 10 });
  const shown = page.fire(page.outer, "click");
  assert.deepEqual(listener.calls, [shown]);
});

test("an event that started before the listener was attached is ignored, whatever its time", async () => {
  const page = await createPage();
  // Every event has the same time, as under a paused test clock, so only the order of events can decide.
  const at = { timeStamp: 0 };
  let onWindow = null;
  let outside = null;
  // The button's handler mounts the listeners while its click is still on the way to `window`, as a `v-if` popup
  // does.
  page.outer.addEventListener("click", () => {
    onWindow ??= page.mount({ modifiers: ["window"], id: "0" });
    outside ??= page.mount({ modifiers: ["outside"], id: "1" });
  });
  page.fire(page.outer, "click", at);
  assert.deepEqual(onWindow.calls, [], "the click that mounted the element is not its event");
  assert.deepEqual(outside.calls, [], "the same check applies to .outside");
  const later = page.fire(page.body, "click", at);
  assert.deepEqual(onWindow.calls, [later]);
  assert.deepEqual(outside.calls, [later]);

  let hidden = null;
  page.inner.addEventListener("click", () => {
    hidden ??= page.mount({ modifiers: ["document"], id: "2" });
  });
  // `hideEvent` leaves `window.event` unset, as browsers do for a listener inside a shadow root.
  page.fire(page.inner, "click", { ...at, hideEvent: true });
  assert.deepEqual(hidden.calls, [], "the order decides without window.event");
  const afterHidden = page.fire(page.body, "click", at);
  assert.deepEqual(hidden.calls, [afterHidden]);

  // An element listener sees events with equal times.
  const onElement = page.mount({ element: page.outer, id: "3" });
  const next = page.fire(page.outer, "click", at);
  assert.deepEqual(onElement.calls, [next]);
});

test("a listener that an update attaches during an event does not see that event", async () => {
  const page = await createPage();
  // A dynamic event name that starts as null and becomes `ping` while a `ping` event is on its way up to the
  // element. No `ping` listener existed before, so the event was not numbered, and `window.event` decides.
  const listener = page.mount({ arg: null });
  page.inner.addEventListener("ping", () => {
    if (listenersOf(page.panel, "ping").length === 0) listener.update({ arg: "ping" });
  });
  page.fire(page.inner, "ping");
  assert.equal(listenersOf(page.panel, "ping").length, 1);
  assert.deepEqual(listener.calls, []);
  const later = page.fire(page.inner, "ping");
  assert.deepEqual(listener.calls, [later]);
});

test("an element listener runs for an event that never reaches window, such as one inside a shadow root", async () => {
  const page = await createPage();
  const root = new FakeNode("shadow-root", null);
  const element = new FakeNode("in-shadow", root);
  const listener = page.mount({ element, arg: "change" });
  const event = page.fire(element, "change");
  assert.deepEqual(listener.calls, [event]);
});

test("an event of a type that had no listener yet is ignored by a listener it mounts, even without window.event", async () => {
  const page = await createPage();
  let listener = null;
  page.inner.addEventListener("tap", () => {
    listener ??= page.mount({ arg: "tap", modifiers: ["document"] });
  });
  page.fire(page.inner, "tap", { hideEvent: true });
  assert.deepEqual(listener.calls, [], "the tap passed window and document before they numbered taps");
  const later = page.fire(page.inner, "tap", { hideEvent: true });
  assert.deepEqual(listener.calls, [later]);
});

test("an event that never reaches window is numbered on document", async () => {
  const page = await createPage();
  const listener = page.mount({ arg: "load", modifiers: ["document"] });
  const loaded = page.fire(page.panel, "load", { stopAtDocument: true });
  assert.deepEqual(listener.calls, [loaded]);
});

test("inside a shadow root, a listener that an event mounts ignores that event", async () => {
  const page = await createPage();
  const root = new FakeNode("shadow-root", null);
  const wrap = new FakeNode("wrap", root);
  const button = new FakeNode("button", wrap);
  let listener = null;
  // `change` stays inside the shadow root, and browsers leave `window.event` unset there, so only the numbering on
  // the shadow root itself can tell the events apart.
  button.addEventListener("change", () => {
    listener ??= page.mount({ arg: "change", element: wrap });
  });
  page.fire(button, "change", { hideEvent: true });
  assert.deepEqual(listener.calls, []);
  const later = page.fire(button, "change", { hideEvent: true });
  assert.deepEqual(listener.calls, [later]);
});

test("an element that moves to another root keeps its listener working", async () => {
  const page = await createPage();
  const element = new FakeNode("moved", page.body);
  const listener = page.mount({ arg: "change", element });
  // A `<Teleport>` whose target changed moves the element into a shadow root after the listener attached.
  const root = new FakeNode("shadow-root", null);
  element.parent = root;
  const first = page.fire(element, "change", { hideEvent: true });
  const second = page.fire(element, "change", { hideEvent: true });
  assert.deepEqual(listener.calls, [first, second]);
});

test(".stop and .prevent act at once under .debounce", async () => {
  const page = await createPage();
  const reached = [];
  page.body.addEventListener("click", () => reached.push("body"));
  const listener = page.mount({ modifiers: ["debounce-300ms", "stop", "prevent"] });
  const event = page.fire(page.panel, "click");
  assert.equal(event.stopped, true, "the event stopped when it arrived");
  assert.equal(event.defaultPrevented, true);
  assert.deepEqual(reached, []);
  assert.deepEqual(listener.calls, []);
  page.clock.tick(300);
  assert.deepEqual(listener.calls, [event]);
});

test(".self, button and system-key modifiers are checked before the handler", async () => {
  const page = await createPage();
  const self = page.mount({ modifiers: ["self"] });
  page.fire(page.inner, "click");
  assert.deepEqual(self.calls, [], ".self ignores an event from a child");
  const direct = page.fire(page.panel, "click");
  assert.deepEqual(self.calls, [direct]);
  self.unmount();

  const ctrl = page.mount({ modifiers: ["ctrl"], id: "1" });
  page.fire(page.panel, "click", { ctrlKey: false });
  assert.deepEqual(ctrl.calls, []);
  const withCtrl = page.fire(page.panel, "click", { ctrlKey: true });
  assert.deepEqual(ctrl.calls, [withCtrl]);
});

test("key names work with .window", async () => {
  const page = await createPage();
  const listener = page.mount({ arg: "keydown", modifiers: ["escape", "window"] });
  assert.equal(listenersOf(page.window, "keydown").length, 1);
  assert.equal(listenersOf(page.panel).length, 0);
  page.fire(page.panel, "keydown", { key: "a" });
  assert.deepEqual(listener.calls, []);
  const escapeKey = page.fire(page.panel, "keydown", { key: "Escape" });
  assert.deepEqual(listener.calls, [escapeKey]);

  // `.esc` and a hyphenated name such as `.arrow-down` follow Vue's key names too.
  const arrow = page.mount({ arg: "keydown", modifiers: ["arrow-down", "document"], id: "1" });
  const down = page.fire(page.panel, "keydown", { key: "ArrowDown" });
  assert.deepEqual(arrow.calls, [down]);
});

test(".left and .right are mouse buttons on a click and keys on a keyboard event", async () => {
  const page = await createPage();
  const mouse = page.mount({ arg: "mouseup", modifiers: ["right"] });
  page.fire(page.panel, "mouseup", { button: 0 });
  assert.deepEqual(mouse.calls, []);
  const rightButton = page.fire(page.panel, "mouseup", { button: 2 });
  assert.deepEqual(mouse.calls, [rightButton]);

  const keys = page.mount({ arg: "keydown", modifiers: ["right", "window"], id: "1" });
  const arrow = page.fire(page.panel, "keydown", { key: "ArrowRight" });
  assert.deepEqual(keys.calls, [arrow]);
});

test("a dynamic click with .right or .middle listens for contextmenu or mouseup", async () => {
  const page = await createPage();
  const right = page.mount({ arg: "click", modifiers: ["right", "debounce-50ms"] });
  assert.equal(listenersOf(page.panel, "click").length, 0);
  assert.equal(listenersOf(page.panel, "contextmenu").length, 1);
  page.fire(page.panel, "contextmenu", { button: 2 });
  page.clock.tick(50);
  assert.equal(right.calls.length, 1);
  right.unmount();

  const middle = page.mount({ arg: "click", modifiers: ["middle"], id: "1" });
  assert.equal(listenersOf(page.panel, "mouseup").length, 1);
  page.fire(page.panel, "mouseup", { button: 1 });
  assert.equal(middle.calls.length, 1);
});

test("a dynamic event name that changes moves the listener and drops the pending call", async () => {
  const page = await createPage();
  const listener = page.mount({ arg: "click", modifiers: ["debounce-100ms"] });
  page.fire(page.panel, "click");
  listener.update({ arg: "keydown" });
  assert.equal(listenersOf(page.panel, "click").length, 0, "the old listener is gone");
  assert.equal(listenersOf(page.panel, "keydown").length, 1, "the new one is attached");
  assert.equal(page.clock.pending(), 0, "the pending call of the old event is dropped");
  page.clock.tick(500);
  assert.deepEqual(listener.calls, []);
  const key = page.fire(page.panel, "keydown", { key: "x" });
  page.clock.tick(100);
  assert.deepEqual(listener.calls, [key]);
});

test("a dynamic event name of null attaches nothing and can become a name later", async () => {
  const page = await createPage();
  const listener = page.mount({ arg: null, modifiers: ["window"] });
  assert.equal(listenersOf(page.window).length, 0);
  assert.equal(listenersOf(page.panel).length, 0);
  listener.update({ arg: "resize" });
  assert.equal(listenersOf(page.window, "resize").length, 1);
  listener.update({ arg: null });
  assert.equal(listenersOf(page.window).length, 0, "a name that becomes null removes the listener");
  listener.unmount();
});

test("errors from the handler, thrown or rejected, reach the app's error handler", async () => {
  const page = await createPage();
  const boom = new Error("boom");
  const thrown = page.mount({
    handler() {
      throw boom;
    },
  });
  page.fire(page.panel, "click");
  assert.equal(page.errors.length, 1);
  assert.equal(page.errors[0].error, boom);
  assert.equal(page.errors[0].proxy, page.proxy);
  assert.equal(typeof page.errors[0].info, "string");
  thrown.unmount();

  const failure = new Error("rejected");
  page.mount({ id: "1", modifiers: ["debounce-10ms"], handler: () => Promise.reject(failure) });
  page.fire(page.panel, "click");
  page.clock.tick(10);
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(page.errors.length, 2);
  assert.equal(page.errors[1].error, failure);
});

test("a vnode without a function under the handler key reports a TypeError instead of running anything", async () => {
  const page = await createPage();
  page.mount({ handler: "not a function" });
  page.fire(page.panel, "click");
  assert.equal(page.errors.length, 1);
  // The error is made inside the runtime's own realm, so `instanceof` would compare two different TypeErrors.
  assert.equal(page.errors[0].error.name, "TypeError");
  assert.match(page.errors[0].error.message, /onCitryOn0/);
});

test(".once removes the listener after one event and an update does not attach it again", async () => {
  const page = await createPage();
  const listener = page.mount({ modifiers: ["once"] });
  const first = page.fire(page.panel, "click");
  page.fire(page.panel, "click");
  assert.deepEqual(listener.calls, [first]);
  assert.equal(listenersOf(page.panel).length, 0);
  listener.update();
  assert.equal(listenersOf(page.panel).length, 0, "an update with the same event name leaves it removed");
  page.fire(page.panel, "click");
  assert.equal(listener.calls.length, 1);
  listener.unmount();
  assert.equal(listenersOf(page.panel).length, 0);
});

test(".once on window or document is not used up by the click that mounted it", async () => {
  const page = await createPage();
  let listener = null;
  // The button's handler mounts the listener while the click is still on its way to the document, as a `v-if`
  // popup does.
  page.outer.addEventListener("click", () => {
    if (!listener) listener = page.mount({ modifiers: ["document", "once"] });
  });
  page.fire(page.outer, "click");
  assert.deepEqual(listener.calls, [], "the mounting click does not run the listener");
  assert.equal(listenersOf(page.document, "click").length, 1, "and does not remove it");
  const next = page.fire(page.body, "click");
  page.fire(page.body, "click");
  assert.deepEqual(listener.calls, [next]);
  assert.equal(listenersOf(page.document, "click").length, 0);
});

test(".outside keeps each event's visibility apart when one event is sent from inside another's handler", async () => {
  const page = await createPage();
  let open = false;
  const setOpen = (value) => {
    open = value;
    page.panel.hidden = !open;
  };
  setOpen(false);
  const other = new FakeNode("other", page.body);
  // The toggle button first sends a click of its own, then opens the panel.
  page.outer.addEventListener("click", () => {
    page.fire(other, "click");
    setOpen(!open);
  });
  page.mount({ modifiers: ["outside"], handler: () => setOpen(false) });
  page.fire(page.outer, "click");
  assert.equal(open, true, "the outer click started while the panel was hidden, so it does not close it");
});

test(".outside skips the visibility check for an event inside the element", async () => {
  const page = await createPage();
  page.mount({ modifiers: ["outside"] });
  page.fire(page.inner, "click");
  assert.equal(page.panel.visibleCalls.length, 0, "an inside event never needs the element's visibility");
  page.fire(page.outer, "click");
  assert.equal(page.panel.visibleCalls.length, 1);
});

test("a listener whose number changes on an update leaves no listener behind under the old number", async () => {
  const page = await createPage();
  const first = page.mount({ arg: "click", modifiers: ["document"], id: "0" });
  const second = page.mount({ arg: "keydown", modifiers: ["document"], id: "1" });
  // A re-render inserts a listener earlier in the template, so both move up one number. Vue runs every
  // `beforeUpdate` of the element before any `updated`.
  first.beforeUpdate({ id: "1" });
  second.beforeUpdate({ id: "2" });
  first.updated();
  second.updated();
  assert.equal(listenersOf(page.document, "click").length, 1, "one click listener, not the old one as well");
  assert.equal(listenersOf(page.document, "keydown").length, 1);
  page.fire(page.body, "click");
  page.fire(page.body, "keydown");
  assert.equal(first.calls.length, 1);
  assert.equal(second.calls.length, 1);
});

test("a vnode without a function under the handler key is reported by Vue even when the app has no error handler", async () => {
  const page = await createPage();
  const config = page.instance.appContext.config;
  const errorHandler = config.errorHandler;
  delete config.errorHandler;
  try {
    page.mount({ handler: "not a function" });
    // Vue's development build throws an error that no handler took; its production build logs it.
    assert.throws(() => page.fire(page.panel, "click"), /onCitryOn0/);
  } finally {
    config.errorHandler = errorHandler;
  }
});
