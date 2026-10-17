import assert from "node:assert/strict";
import test from "node:test";

import { formatRuntimeLabel } from "../src/runtime_label.js";

test("runtime label identifies the published and workspace tuple", () => {
  const runtime = "Pyodide 314.0.3, Python 3.14.2, Citry 0.5.1, Citry UI 0.2.2";

  assert.equal(formatRuntimeLabel(runtime, "published"), "Citry 0.5.1 · Citry UI 0.2.2 · published");
  assert.equal(formatRuntimeLabel(runtime, "workspace"), "Citry 0.5.1 · Citry UI 0.2.2 · workspace");
});

test("runtime label does not silently claim an unknown source", () => {
  assert.equal(formatRuntimeLabel("Citry 0.5.1", ""), "Citry 0.5.1 · unknown source");
});
