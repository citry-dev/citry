import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

// Pull single helpers out of the coordinator, so the copy it ships is the one under test. Each
// helper ends where its body closes at the declaration's indent, or at the end of its one line.
const client = await readFile(new URL("../../../py/citry/citry/_vue/client.js", import.meta.url), "utf8");
const helperSource = (declaration, terminator) => {
  const start = client.indexOf(declaration);
  assert.ok(start >= 0, `client.js declares ${declaration.trim()}`);
  return client.slice(start, client.indexOf(terminator, start) + terminator.length);
};
const run = (globals, sources, names) => {
  const context = vm.createContext({ Object, Reflect, URL, ...globals });
  vm.runInContext([...sources, `this.helpers = {${names.join(", ")}};`].join("\n"), context);
  return context.helpers;
};

function csrfHelpers({ cookie, href = "http://app.test/page/" }) {
  const address = new URL(href);
  return run(
    {
      global: { origin: address.origin, location: { href, origin: address.origin } },
      pageDocument: { cookie, baseURI: href },
      pageCsrf: {},
    },
    [
      helperSource("  const readCsrfCookie = ", "\n  };\n"),
      helperSource("  const pageCsrfToken = ", "\n  };\n"),
      helperSource("  const pageCsrfHeader = ", ";\n"),
      helperSource("  const csrfHeaders = ", "\n  };\n"),
    ],
    ["readCsrfCookie", "csrfHeaders"],
  );
}

test("the CSRF cookie is read past a cookie of the same name whose value does not decode", () => {
  assert.equal(
    csrfHelpers({ cookie: "csrftoken=%E0%A4%A; csrftoken=good%20token" }).readCsrfCookie("csrftoken"),
    "good token",
  );
  assert.equal(csrfHelpers({ cookie: "other=1; csrftoken=%zz" }).readCsrfCookie("csrftoken"), "");
  assert.equal(csrfHelpers({ cookie: "csrftoken=abc" }).readCsrfCookie("csrftoken"), "abc");
});

test("a prop named __proto__ is left out of the copied input props", () => {
  const { editableValueProps } = run(
    {
      EDITABLE_VALUE_TAGS: new Set(["input"]),
      own: (target, key) => Object.prototype.hasOwnProperty.call(target, key),
      valueComparedByVNode: () => true,
      valueSource: () => null,
      restoreUneditedValue() {},
    },
    [helperSource("  function editableValueProps(", "\n  }\n")],
    ["editableValueProps"],
  );
  const props = JSON.parse('{"__proto__": {"injected": true}, "type": "text", "value": "v"}');
  const prepared = editableValueProps("input", props, props, 0, null);
  // The copy is a plain object of the vm realm, whose prototype is that realm's `Object.prototype`.
  assert.equal(Object.getPrototypeOf(Object.getPrototypeOf(prepared)), null);
  assert.equal(prepared.injected, undefined);
  assert.deepEqual(Object.keys(prepared), ["type", ".value"]);
});

test("nodeConnected and callBuiltIn read past a form field with the member's name", () => {
  const { nodeConnected, callBuiltIn } = run(
    {},
    [
      helperSource("  const builtInMember = ", "\n  };\n"),
      helperSource("  const readBuiltIn = ", "\n  };\n"),
      helperSource("  const callBuiltIn = ", ";\n"),
      helperSource("  const nodeConnected = ", ";\n"),
    ],
    ["nodeConnected", "callBuiltIn"],
  );
  class FakeNode {
    get isConnected() {
      return false;
    }
    contains(other) {
      return other === "child";
    }
    dispatchEvent(event) {
      return event === "event";
    }
  }
  // A form shows each named field as an own data property that hides the prototype's member.
  const form = new FakeNode();
  for (const name of ["isConnected", "contains", "dispatchEvent"])
    Object.defineProperty(form, name, { configurable: true, value: { field: name } });
  assert.equal(nodeConnected(form), false);
  assert.equal(callBuiltIn(form, "contains", "child"), true);
  assert.equal(callBuiltIn(form, "dispatchEvent", "event"), true);
  // A plain-object stand-in, as the unit tests use, is read directly.
  assert.equal(nodeConnected({ isConnected: true }), true);
});
