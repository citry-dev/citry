/** Verify the committed Vue-era browser artifacts match their maintained sources. */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { build } from "esbuild";
import { version as vueVersion } from "vue";

import { VUE_VERSION, buildCitryI18n, citryVueBuildOptions, citryVueEventsBuildOptions } from "../build-support.mjs";

const assertCommittedBuild = async function (options, committedUrl) {
  const output = await build(options({ write: false, outfile: undefined }));
  const committed = readFileSync(new URL(committedUrl, import.meta.url), "utf8");
  assert.equal(output.outputFiles.length, 1);
  assert.equal(output.outputFiles[0].text, committed);
};

test("the Vue runtime dependency is exactly pinned", () => {
  assert.equal(vueVersion, VUE_VERSION);
});

test("the committed Vue runtime exactly matches its source build", async () => {
  await assertCommittedBuild(citryVueBuildOptions, "../../../py/citry/citry/_vue/vue.js");
  const runtime = readFileSync(new URL("../../../py/citry/citry/_vue/vue.js", import.meta.url), "utf8");
  assert.ok(!runtime.includes("process.env.NODE_ENV"));
  assert.ok(runtime.length < 150_000, `production Vue runtime is unexpectedly large: ${runtime.length} bytes`);
});

test("the committed Vue Events bridge exactly matches its TypeScript source", async () => {
  await assertCommittedBuild(citryVueEventsBuildOptions, "../../../py/citry/citry/_vue/events.js");
});

test("the combined interactive runtime preserves loader order", () => {
  const runtime = readFileSync(new URL("../../../py/citry/citry/_vue/runtime.js", import.meta.url), "utf8");
  const guard = runtime.indexOf("if (!global.CitryStable)");
  const vue = runtime.indexOf("Citry Vue runtime");
  const coordinator = runtime.indexOf("global.CitryStable", vue);
  const events = runtime.indexOf("Citry Vue Events bridge");
  assert.ok(guard >= 0 && vue > guard && coordinator > vue && events > coordinator);
  assert.ok(runtime.indexOf("global.Vue = Vue") > vue);
  assert.ok(runtime.indexOf("global.CitryVueEvents = CitryVueEvents") > events);
});

test("the committed Vue i18n plugin exactly matches its source build", async () => {
  const output = await buildCitryI18n({ write: false, outfile: undefined });
  const committed = readFileSync(
    new URL("../../../py/citry/citry/ext/i18n/client/vue-plugin.source.js", import.meta.url),
    "utf8",
  );
  assert.equal(output.outputFiles[0].text, committed);
});

test("delivery minification settings cannot be overridden", () => {
  assert.throws(() => citryVueBuildOptions({ minify: true }), /owns its delivery minification settings/);
});
