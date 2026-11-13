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
  // A `<base>` element that points at another site. Redirects resolve against the page's own
  // address (`location.href` below), so this value must never show up in a followed URL.
  baseURI: "http://other.test/",
};
const context = {
  document,
  location: {
    href: "http://app.test/shop/list?x=1",
    origin: "http://app.test",
    assign: (url) => assigned.push(url),
  },
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
  // Redirects resolve their URL with the URL parser, which a vm realm does not have on its own.
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

// Each URL and the address the page goes to: relative ones resolve against the page's own
// address, as the browser would without a `<base>` element and as the no-JavaScript form path does.
const FOLLOWED = {
  "absolute path": ["/a", "http://app.test/a"],
  "relative path": ["a/b", "http://app.test/shop/a/b"],
  "query only": ["?x=2", "http://app.test/shop/list?x=2"],
  "fragment only": ["#top", "http://app.test/shop/list?x=1#top"],
  https: ["https://example.com/", "https://example.com/"],
  "uppercase http": ["HTTP://example.com/", "http://example.com/"],
};

test("a redirect in an about:srcdoc frame uses the inherited base URL only on its own origin", async () => {
  const saved = { ...context.location };
  const savedBase = document.baseURI;
  Object.assign(context.location, { href: "about:srcdoc" });
  context.origin = "http://app.test";
  try {
    document.baseURI = "http://app.test/parent/";
    await redirect("next");
    assert.deepEqual(assigned, ["http://app.test/parent/next"]);
    document.baseURI = "http://other.test/";
    await redirect("next");
    assert.deepEqual(assigned, []);
    assert.match(errors[0], /does not resolve to this page's origin/);
  } finally {
    Object.assign(context.location, saved);
    document.baseURI = savedBase;
    delete context.origin;
  }
});

for (const [name, [url, landing]] of Object.entries(FOLLOWED)) {
  test(`a redirect to http(s) or a URL with no scheme is followed against the page's address: ${name}`, async () => {
    await redirect(url);
    assert.deepEqual(assigned, [landing]);
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
  // The multiplier keeps every product below 2^53, so JavaScript numbers hold it exactly and each
  // piece gets picked.
  let seed = 4285;
  const next = (limit) => {
    seed = (seed * 48271) % 2147483647;
    return seed % limit;
  };
  // Counts of each outcome, so a generator that stops reaching one fails the test.
  let followed = 0;
  let unresolvable = 0;
  let refused = 0;
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
      // A followed URL goes to its address resolved against the page's own address. One the URL
      // parser cannot resolve there (such as `http://` with no host) is refused for its origin.
      let landing = null;
      try {
        landing = new URL(url, context.location.href).href;
      } catch {}
      if (landing === null) {
        unresolvable++;
        assert.deepEqual(assigned, [], JSON.stringify(url));
        assert.equal(errors.length, 1, JSON.stringify(url));
        // The scheme rule let it through; only the page-address resolution refused it.
        assert.ok(!errors[0].includes("scheme"), JSON.stringify(url));
      } else {
        followed++;
        assert.deepEqual(assigned, [landing], JSON.stringify(url));
        assert.deepEqual(errors, [], JSON.stringify(url));
      }
    } else {
      refused++;
      assert.deepEqual(assigned, [], JSON.stringify(url));
      assert.equal(errors.length, 1, JSON.stringify(url));
      assert.ok(errors[0].includes(`the ${JSON.stringify(scheme)} scheme`), JSON.stringify(url));
    }
  }
  assert.ok(followed >= 100 && refused >= 100, `followed ${followed}, refused ${refused}`);
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
