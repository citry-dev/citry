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

function csrfHeadersOnPage({ cookie, href = "http://app.test/page/" }) {
  const address = new URL(href);
  const context = vm.createContext({
    URL,
    global: { origin: address.origin, location: { href, origin: address.origin } },
    pageDocument: { cookie, baseURI: href },
    pageCsrf: {},
  });
  vm.runInContext(
    [
      helperSource("  const readCsrfCookie = ", "\n  };\n"),
      helperSource("  const pageCsrfToken = ", "\n  };\n"),
      helperSource("  const pageCsrfHeader = ", ";\n"),
      helperSource("  const csrfHeaders = ", "\n  };\n"),
      "this.csrfHeaders = csrfHeaders;",
    ].join("\n"),
    context,
  );
  return context.csrfHeaders;
}

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
