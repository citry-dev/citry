import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

// A served stylesheet tag may name several apps in `data-citry-vue-style-app`, so a page that
// combines several apps keeps one tag per file. These tests pull the helpers out of the runtime
// source (`client.js`) and check which tags an app adopts and when a shared tag leaves the page.
const client = await readFile(new URL("../../../py/citry/citry/_vue/client.js", import.meta.url), "utf8");
const helperSource = (declaration, terminator) => {
  const start = client.indexOf(declaration);
  assert.ok(start >= 0, `client.js declares ${declaration.trim()}`);
  return client.slice(start, client.indexOf(terminator, start) + terminator.length);
};

const A = "a".repeat(32);
const B = "0123456789abcdef".repeat(2);
const C = "c".repeat(32);

function helpers(elements = []) {
  const context = vm.createContext({
    Map,
    Set,
    loadedStyleUrls: new Map(),
    pageDocument: {
      querySelectorAll: (selector) => {
        assert.equal(selector, "[data-citry-vue-style-app][data-citry-css-url]");
        return elements.filter((element) => element.connected);
      },
    },
  });
  vm.runInContext(
    [
      helperSource("  const STYLE_APP_LIST = ", ";\n"),
      helperSource("  const styleAppLists = ", ";\n"),
      helperSource("  const STYLE_APP_LISTS_KEPT = ", ";\n"),
      helperSource("  function styleNamesApp(", "\n  }\n"),
      helperSource("  function existingStyleElement(", "\n  }\n"),
      helperSource("  function removeStyleElement(", "\n  }\n"),
      helperSource("  function retireUnusedStyles(", "\n  }\n"),
      "this.helpers = {styleNamesApp, existingStyleElement, retireUnusedStyles, loadedStyleUrls, styleAppLists};",
    ].join("\n"),
    context,
  );
  return context.helpers;
}

function tag(apps, url = "/s.css") {
  const attrs = { "data-citry-vue-style-app": apps, "data-citry-css-url": url };
  const element = {
    connected: true,
    getAttribute: (name) => (Object.hasOwn(attrs, name) ? attrs[name] : null),
    remove() {
      element.connected = false;
    },
  };
  return element;
}

test("a tag names one app exactly as before, and a space-separated list names each of its apps", () => {
  const { styleNamesApp } = helpers();
  assert.equal(styleNamesApp(tag(A), A), true);
  assert.equal(styleNamesApp(tag(A), B), false);
  assert.equal(styleNamesApp(tag(`${A} ${B}`), A), true);
  assert.equal(styleNamesApp(tag(`${A} ${B}`), B), true);
  assert.equal(styleNamesApp(tag(`${A} ${B} ${C}`), C), true);
  assert.equal(styleNamesApp(tag(`${A} ${B}`), C), false);
});

test("a malformed list names no app", () => {
  const { styleNamesApp } = helpers();
  for (const value of [
    `${A}  ${B}`, // two spaces
    ` ${A} ${B}`, // leading space
    `${A} ${B} `, // trailing space
    `${A}\t${B}`, // tab
    `${A}\n${B}`, // line feed
    `${A},${B}`, // comma
    `${A} ${A}`, // repeated id
    `${A} ${B.toUpperCase()}`, // uppercase id
    `${A} ${B.slice(1)}`, // short id
    `${A} __proto__`,
    `${A} constructor`,
    "",
  ]) {
    assert.equal(styleNamesApp(tag(value), A), false, JSON.stringify(value));
    assert.equal(styleNamesApp(tag(value), B), false, JSON.stringify(value));
  }
  // A name that is not an app id is never matched by a list, whatever the list holds.
  assert.equal(styleNamesApp(tag(`${A} ${B}`), "__proto__"), false);
});

test("each app finds the shared tag by its URL", () => {
  const shared = tag(`${A} ${B}`, "/shared.css");
  const own = tag(C, "/shared.css");
  const { existingStyleElement } = helpers([shared, own]);
  assert.equal(existingStyleElement(A, "/shared.css"), shared);
  assert.equal(existingStyleElement(B, "/shared.css"), shared);
  assert.equal(existingStyleElement(C, "/shared.css"), own);
  assert.equal(existingStyleElement(A, "/other.css"), null);
});

test("a shared tag stays on the page until the last app that adopted it lets go", () => {
  const shared = tag(`${A} ${B}`);
  const { retireUnusedStyles, loadedStyleUrls } = helpers([shared]);
  const record = (app) => ({ element: shared, refs: new Map([[app, new Set(["c1"])]]), stages: new Set() });
  const recordA = record(A);
  const recordB = record(B);
  loadedStyleUrls.set(JSON.stringify([A, "/s.css"]), recordA);
  loadedStyleUrls.set(JSON.stringify([B, "/s.css"]), recordB);

  recordA.refs.clear();
  retireUnusedStyles();
  assert.equal(loadedStyleUrls.size, 1);
  assert.equal(shared.connected, true, "app B still uses the stylesheet");

  recordB.refs.clear();
  retireUnusedStyles();
  assert.equal(loadedStyleUrls.size, 0);
  assert.equal(shared.connected, false);
});

test("a tag that names one app leaves with that app, as before", () => {
  const single = tag(A);
  const { retireUnusedStyles, loadedStyleUrls } = helpers([single]);
  loadedStyleUrls.set(JSON.stringify([A, "/s.css"]), { element: single, refs: new Map(), stages: new Set() });
  retireUnusedStyles();
  assert.equal(single.connected, false);
});

test("the parsed-list cache starts over instead of growing without limit", () => {
  const { styleNamesApp, styleAppLists } = helpers();
  const hex = (i) => i.toString(16).padStart(32, "0");
  for (let i = 0; i < 200; i++) assert.equal(styleNamesApp(tag(`${hex(i)} ${hex(i + 1000)}`), hex(i)), true);
  assert.ok(styleAppLists.size <= 64, `${styleAppLists.size} lists kept`);
  // A list seen before the cache started over is parsed again and still matches.
  assert.equal(styleNamesApp(tag(`${hex(0)} ${hex(1000)}`), hex(1000)), true);
});
