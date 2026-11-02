/**
 * Verify that Citry reads its own globals and the document's members past elements the page names.
 *
 * Node has no DOM, so a small class stands in for the document: its prototype holds the real
 * members, and own properties play the part of the named elements a browser puts on `document`
 * (`<form name="createElement">`). The bundled scripts use `src/page-dom.ts`, and the
 * hand-written coordinator `_vue/client.js` carries a copy, so every case runs against both.
 */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";
import { build } from "esbuild";

const built = await build({
  entryPoints: [new URL("../src/page-dom.ts", import.meta.url).pathname],
  bundle: true,
  format: "esm",
  platform: "browser",
  target: "es2020",
  write: false,
});
const pageDom = await import(
  `data:text/javascript;base64,${Buffer.from(built.outputFiles[0].text).toString("base64")}`
);

// Pull the helpers out of the coordinator, so the copy it ships is the one under test.
const client = await readFile(new URL("../../../py/citry/citry/_vue/client.js", import.meta.url), "utf8");
// `ownGlobal` is one line; each other helper ends where its body closes at the declaration's indent.
const helperSource = (name, terminator) => {
  const start = client.indexOf(`  const ${name} = `);
  assert.ok(start >= 0, `client.js declares ${name}`);
  return client.slice(start, client.indexOf(terminator, start) + terminator.length);
};
const clientHelpers = (global) => {
  const context = vm.createContext({ global, Object, Reflect, Proxy, WeakMap });
  vm.runInContext(
    [
      helperSource("ownGlobal", ";\n"),
      helperSource("builtInMember", "\n  };\n"),
      helperSource("callBuiltIn", "\n  };\n"),
      helperSource("documentMembers", "\n  };\n"),
      "this.helpers = {ownGlobal, callBuiltIn, documentMembers};",
    ].join("\n"),
    context,
  );
  return context.helpers;
};

class FakeDocumentBase {
  get cookie() {
    return this._cookie ?? "csrftoken=abc";
  }
  set cookie(value) {
    this._cookie = value;
  }
}
class FakeDocument extends FakeDocumentBase {
  createElement(tag) {
    assert.ok(this instanceof FakeDocument, "createElement runs on the real document");
    return { tag };
  }
}
// A document whose page named elements after its members, as `<form name="...">` does.
const clobberedDocument = () => {
  const doc = new FakeDocument();
  for (const name of ["createElement", "cookie"])
    Object.defineProperty(doc, name, { configurable: true, value: { element: name } });
  // The real document's `location` is an own getter, which no markup can create.
  Object.defineProperty(doc, "location", { get: () => "https://example.test/" });
  return doc;
};

const implementations = [
  ["page-dom.ts", pageDom.documentMembers],
  ["client.js", clientHelpers({}).documentMembers],
];

for (const [label, documentMembers] of implementations) {
  test(`${label}: a named element does not hide a document method or getter`, () => {
    const doc = clobberedDocument();
    const members = documentMembers(() => doc);
    assert.deepEqual(members.createElement("a"), { tag: "a" });
    assert.equal(members.cookie, "csrftoken=abc");
    // The same bound method comes back each time, so a hot path does not allocate one per call.
    assert.equal(members.createElement, members.createElement);
  });

  test(`${label}: an own getter that a script defined is kept`, () => {
    // Markup never creates a getter, so a stub such as a test's `document.hidden` stays in charge.
    const doc = clobberedDocument();
    Object.defineProperty(doc, "cookie", { configurable: true, get: () => "stubbed=1" });
    assert.equal(documentMembers(() => doc).cookie, "stubbed=1");
  });

  test(`${label}: a setter runs on the real document`, () => {
    const doc = clobberedDocument();
    documentMembers(() => doc).cookie = "a=b";
    assert.equal(doc._cookie, "a=b");
  });

  test(`${label}: an own getter such as location is kept, and a plain-object document still works`, () => {
    const doc = clobberedDocument();
    assert.equal(documentMembers(() => doc).location, "https://example.test/");
    // A name no prototype defines falls back to an ordinary read, which serves a test's plain object.
    const plain = {
      currentScript: null,
      dispatchEvent() {
        return this;
      },
    };
    const members = documentMembers(() => plain);
    assert.equal(members.currentScript, null);
    assert.equal(members.dispatchEvent(), plain);
  });

  test(`${label}: each read follows the current document`, () => {
    let doc = new FakeDocument();
    const members = documentMembers(() => doc);
    assert.equal(members.cookie, "csrftoken=abc");
    doc = { cookie: "csrftoken=second" };
    assert.equal(members.cookie, "csrftoken=second");
  });
}

test("ownGlobal reads only a global defined on the global object itself", () => {
  // A browser finds an element's id through the global object's prototype chain, never as an own property.
  const named = Object.create({ __citryRuntime: { element: "div" } });
  named.Citry = { vue: 1 };
  const { ownGlobal } = clientHelpers(named);
  assert.equal(ownGlobal("__citryRuntime"), undefined);
  assert.deepEqual(ownGlobal("Citry"), { vue: 1 });
  globalThis.__citryPageDomProbe = 1;
  try {
    assert.equal(pageDom.ownGlobal("__citryPageDomProbe"), 1);
    assert.equal(pageDom.ownGlobal("__citryPageDomMissing"), undefined);
  } finally {
    delete globalThis.__citryPageDomProbe;
  }
});

test("callBuiltIn calls a form's own method past a named field", () => {
  // `<form><input name="addEventListener"></form>` makes the field an own data property of the form.
  class FakeForm {
    addEventListener(type) {
      this.added = type;
    }
  }
  const form = new FakeForm();
  Object.defineProperty(form, "addEventListener", { configurable: true, value: { element: "input" } });
  const { callBuiltIn } = clientHelpers({});
  callBuiltIn(form, "addEventListener", "submit");
  assert.equal(form.added, "submit");
  // A plain-object stand-in with its own method still works.
  const plain = {
    calls: 0,
    dispatchEvent() {
      this.calls += 1;
    },
  };
  callBuiltIn(plain, "dispatchEvent");
  assert.equal(plain.calls, 1);
});
