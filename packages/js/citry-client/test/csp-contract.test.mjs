import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { runCspContract } from "./csp-contract-runner.mjs";

test("the pinned Alpine CSP evaluator agrees with the compatibility corpus", async () => {
  const result = await runCspContract();
  assert.deepEqual(
    result.actual.map(({ id, outcome, failure, value }) => ({ id, outcome, failure, value })),
    result.expected,
  );
});

test("the pinned CSP build keeps its directive and host restrictions", async () => {
  const packageRoot = new URL("../node_modules/@alpinejs/csp/", import.meta.url);
  const [directive, evaluator] = await Promise.all([
    readFile(new URL("src/directives/x-html.js", packageRoot), "utf8"),
    readFile(new URL("src/evaluator.js", packageRoot), "utf8"),
  ]);

  assert.match(directive, /Using the x-html directive is prohibited in the CSP build/);
  assert.match(evaluator, /el instanceof HTMLIFrameElement/);
  assert.match(evaluator, /el instanceof HTMLScriptElement/);
});
