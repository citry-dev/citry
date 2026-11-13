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

// The scheme rule of Citry 0.7.0 and earlier, kept here as the reference the shipped rule must agree
// with. It trims with a regex, which takes seconds on a long run of spaces inside a URL.
const releasedScheme = (url) => {
  // biome-ignore lint/suspicious/noControlCharactersInRegex: the released rule, copied as written.
  const text = url.replace(/^[\u0000-\u0020]+|[\u0000-\u0020]+$/g, "").replace(/[\t\n\r]/g, "");
  const match = /^([A-Za-z][A-Za-z0-9+.-]*):/.exec(text);
  return match ? match[1].toLowerCase() : null;
};

test("a redirect is followed or refused exactly as the released scheme rule decides", async () => {
  // A small fixed-seed generator, so a failure names the same URL on every run.
  let seed = 4285;
  const next = (limit) => {
    seed = (seed * 1103515245 + 12345) % 2147483648;
    return seed % limit;
  };
  const pieces = [
    "\u0000",
    "\u0001",
    " ",
    "\t",
    "\n",
    "\r",
    "!",
    " ",
    "a",
    "Z",
    "j",
    ":",
    "+",
    ".",
    "-",
    "/",
    "http",
    "s",
  ];
  for (let index = 0; index < 3000; index++) {
    let url = "";
    const length = 1 + next(12);
    for (let part = 0; part < length; part++) url += pieces[next(pieces.length)];
    const scheme = releasedScheme(url);
    await redirect(url);
    if (scheme === null || scheme === "http" || scheme === "https") {
      assert.deepEqual(assigned, [url], JSON.stringify(url));
      assert.deepEqual(errors, [], JSON.stringify(url));
    } else {
      assert.deepEqual(assigned, [], JSON.stringify(url));
      assert.equal(errors.length, 1, JSON.stringify(url));
      assert.ok(errors[0].includes(`the ${JSON.stringify(scheme)} scheme`), JSON.stringify(url));
    }
  }
});

test("a redirect URL with a long run of spaces inside is checked quickly", async () => {
  // The released rule took about 3 s on this URL; walking in from the ends takes well under 1 ms.
  for (const url of [`/a${" ".repeat(100_000)}b`, `javascript:${" ".repeat(100_000)}x`]) {
    const started = performance.now();
    await redirect(url);
    assert.ok(performance.now() - started < 500, `took ${performance.now() - started} ms`);
  }
  // Only the javascript: URL is refused, and it is the last one checked.
  assert.equal(errors.length, 1);
});
