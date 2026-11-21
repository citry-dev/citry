import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

// Pull the CSRF helpers out of the coordinator, so the copy it ships is the one under test. Each
// helper ends where its body closes at the declaration's indent, or at the end of its one line.
const client = await readFile(new URL("../../../py/citry/citry/_vue/client.js", import.meta.url), "utf8");
const helperSource = (declaration, terminator) => {
  const start = client.indexOf(declaration);
  assert.ok(start >= 0, `client.js declares ${declaration.trim()}`);
  return client.slice(start, client.indexOf(terminator, start) + terminator.length);
};

// The page's CSRF state and every helper that reads it, from `let pageCsrf` to the end of
// `publicConfigure`, run together so the precedence between them is the shipped one.
const csrfBlock = () => {
  const start = client.indexOf("  let pageCsrf = ");
  const endMarker = "    pageCsrf = Object.freeze(csrf);\n  };\n";
  const end = client.indexOf(endMarker, start);
  assert.ok(start >= 0 && end > start, "client.js keeps the page CSRF helpers together");
  return client.slice(start, end + endMarker.length);
};

function csrfOnPage({ cookie, href = "http://app.test/page/" }) {
  const address = new URL(href);
  const warnings = [];
  const context = vm.createContext({
    URL,
    console: { warn: (message) => warnings.push(message) },
    global: { origin: address.origin, location: { href, origin: address.origin } },
    pageDocument: { cookie, baseURI: href },
  });
  vm.runInContext(
    [
      helperSource("\n  const own = ", ";\n"),
      helperSource("\n  const plain = ", "\n  };\n"),
      csrfBlock(),
      "this.csrfHeaders = csrfHeaders; this.adopt = adoptServerCsrf; this.configure = publicConfigure;",
      "this.events = eventsPageCsrf; this.fromJson = (text) => JSON.parse(text);",
    ].join("\n"),
    context,
  );
  context.warnings = warnings;
  return context;
}

const csrfHeadersOnPage = (options) => csrfOnPage(options).csrfHeaders;
// A plain object made in the page's realm, as JSON.parse there makes a configuration block, so the
// runtime's plain-object check accepts it. `value` is copied as JSON.
const inPage = (page, value) => page.fromJson(JSON.stringify(value));
const block = (page, names) => inPage(page, { csrfNames: names });
// The runtime throws its realm's TypeError, which is not this realm's.
const isTypeError = (error) => error.name === "TypeError";

test("csrfHeaders reads only a string or a URL", () => {
  const csrfHeaders = csrfHeadersOnPage({ cookie: "csrftoken=abc" });
  assert.deepEqual({ ...csrfHeaders("/citry/ext/i18n/messages") }, { "X-CSRFToken": "abc" });
  assert.deepEqual({ ...csrfHeaders(new URL("http://app.test/citry/")) }, { "X-CSRFToken": "abc" });
  assert.deepEqual({ ...csrfHeaders("https://other.test/") }, {});
  // Any other object would turn into text that names a path on this page, whatever address it holds.
  const request = { url: "https://other.test/", toString: () => "/same-origin-path" };
  for (const value of [request, { href: "/a" }, 42, null, undefined]) {
    assert.deepEqual({ ...csrfHeaders(value) }, {}, String(value));
  }
});

test("the CSRF names in a configuration block choose the cookie and the header", () => {
  const page = csrfOnPage({ cookie: "csrftoken=default; site_csrf=chosen" });
  page.adopt(block(page, { cookie: "site_csrf", header: "X-Site-CSRF" }));
  assert.deepEqual({ ...page.csrfHeaders("/citry/ext/events/call") }, { "X-Site-CSRF": "chosen" });
  // The Events bridge reads the same values through its getters.
  assert.equal(page.events.header, "X-Site-CSRF");
  assert.equal(page.events.token(), "chosen");
});

test("a block without names, or with only some, leaves Django's defaults for the rest", () => {
  const page = csrfOnPage({ cookie: "csrftoken=default; other=x" });
  page.adopt(inPage(page, {}));
  assert.deepEqual({ ...page.csrfHeaders("/a") }, { "X-CSRFToken": "default" });
  const partial = csrfOnPage({ cookie: "csrftoken=default; other=x" });
  partial.adopt(block(partial, { header: "X-Other" }));
  assert.deepEqual({ ...partial.csrfHeaders("/a") }, { "X-Other": "default" });
});

test("a null cookie name sends no token until the page gives one", () => {
  const page = csrfOnPage({ cookie: "csrftoken=stale" });
  page.adopt(block(page, { cookie: null }));
  assert.deepEqual({ ...page.csrfHeaders("/a") }, {});
  page.configure(vm.runInContext("({csrf: {token: () => 'from-page'}})", page));
  assert.deepEqual({ ...page.csrfHeaders("/a") }, { "X-CSRFToken": "from-page" });
});

test("each name an explicit Citry.configure call sets wins over the block, the others stay", () => {
  // Called in either order: the call is the page's own decision.
  for (const callFirst of [true, false]) {
    const page = csrfOnPage({ cookie: "server=s; host=h" });
    const names = block(page, { cookie: "server", header: "X-Server" });
    if (!callFirst) page.adopt(names);
    page.configure(inPage(page, { csrf: { cookie: "host" } }));
    if (callFirst) page.adopt(names);
    assert.deepEqual({ ...page.csrfHeaders("/a") }, { "X-Server": "h" }, `callFirst=${callFirst}`);
  }
});

test("the first block's names stay, and a block that disagrees is reported", () => {
  const page = csrfOnPage({ cookie: "one=1; two=2" });
  page.adopt(block(page, { cookie: "one" }));
  page.adopt(block(page, { cookie: "one" }));
  assert.equal(page.warnings.length, 0);
  page.adopt(block(page, { cookie: "two", header: "X-Two" }));
  assert.equal(page.warnings.length, 1);
  assert.deepEqual({ ...page.csrfHeaders("/a") }, { "X-CSRFToken": "1" });
});

test("names of the wrong shape, or a reserved header, stop the block", () => {
  for (const names of [
    { cookie: "a b" },
    { cookie: "" },
    { cookie: 5 },
    { header: "X-Citry-Events" },
    { header: "Cookie" },
    { header: "Sec-Token" },
    { header: "bad header" },
    { header: null },
  ]) {
    const page = csrfOnPage({ cookie: "csrftoken=x" });
    assert.throws(() => page.adopt(block(page, names)), isTypeError, JSON.stringify(names));
  }
  const page = csrfOnPage({ cookie: "csrftoken=x" });
  assert.throws(() => page.adopt(inPage(page, { csrfNames: [] })), isTypeError);
});

test("names inherited from Object.prototype choose nothing", () => {
  const page = csrfOnPage({ cookie: "csrftoken=real; evil=leak" });
  vm.runInContext(
    "Object.prototype.cookie = 'evil'; Object.prototype.header = 'X-Evil'; Object.prototype.token = 'forged';" +
      "Object.prototype.csrfNames = {cookie: 'evil'};",
    page,
  );
  try {
    page.adopt(vm.runInContext("({})", page));
    page.configure(vm.runInContext("({csrf: {}})", page));
    assert.deepEqual({ ...page.csrfHeaders("/a") }, { "X-CSRFToken": "real" });
  } finally {
    vm.runInContext(
      "delete Object.prototype.cookie; delete Object.prototype.header; delete Object.prototype.token;" +
        "delete Object.prototype.csrfNames;",
      page,
    );
  }
});

test("a csrf key given as undefined counts as not given", () => {
  // `{token: window.maybeToken}` on a page without that global must still read the cookie.
  const page = csrfOnPage({ cookie: "csrftoken=from-cookie; site=s" });
  page.configure(vm.runInContext("({csrf: {token: undefined, cookie: undefined, header: undefined}})", page));
  assert.deepEqual({ ...page.csrfHeaders("/a") }, { "X-CSRFToken": "from-cookie" });
  page.adopt(block(page, { cookie: "site", header: "X-Site" }));
  assert.deepEqual({ ...page.csrfHeaders("/a") }, { "X-Site": "s" });
});
