import assert from "node:assert/strict";
import test from "node:test";

import {appendServerTiming} from "./benchmark-timing.mjs";

test("appends whole-request timing without replacing route timing", () => {
  assert.equal(
    appendServerTiming("prepare;dur=1.250", ["application;dur=4.500"]),
    "prepare;dur=1.250, application;dur=4.500",
  );
});

test("preserves multiple existing Server-Timing header values", () => {
  assert.equal(
    appendServerTiming(["db;dur=1", "prepare;dur=2"], ["application;dur=3"]),
    "db;dur=1, prepare;dur=2, application;dur=3",
  );
});

test("creates a header when the route did not provide one", () => {
  assert.equal(
    appendServerTiming(undefined, ["application;dur=3", "render;dur=3"]),
    "application;dur=3, render;dur=3",
  );
});
