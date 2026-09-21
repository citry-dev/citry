import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import { build } from "esbuild";

import {
  buildCitryI18n,
  citryVueBuildOptions,
  citryVueEventsBuildOptions,
  citryVueFragmentsBuildOptions,
} from "./build-support.mjs";

await Promise.all([
  build(citryVueBuildOptions()),
  build(citryVueEventsBuildOptions()),
  build(citryVueFragmentsBuildOptions()),
  buildCitryI18n(),
]);

const vueDirectory = fileURLToPath(new URL("../../py/citry/citry/_vue/", import.meta.url));
const parts = await Promise.all(
  ["vue.js", "fragments.js", "client.js", "events.js"].map((name) => readFile(`${vueDirectory}/${name}`, "utf8")),
);
const helperContract = parts[2].match(/const HELPER_CONTRACT = "([0-9a-f]+)";/)?.[1];
if (!helperContract) throw new Error("Citry Vue client does not declare its helper contract");
await writeFile(
  `${vueDirectory}/runtime.js`,
  "/* Citry interactive runtime. GENERATED FILE, do not edit: Vue runtime, prepared coordinator, then Events bridge. */\n" +
    `(function (global) {\nif (!global.CitryStable) {\n` +
    parts[0] +
    "\nglobal.Vue = Vue;\n" +
    parts[1] +
    "\nglobal.CitryVueFragments = CitryVueFragments;\n" +
    parts[2] +
    `\n} else {\n  if (global.CitryStable.compilerRuntime?.helperContract !== "${helperContract}") ` +
    `throw new Error("an incompatible Citry Vue runtime is already loaded");\n` +
    `  if (!global.Vue) throw new Error("the existing Citry Vue runtime has no Vue namespace");\n}\n` +
    `if (!global.CitryVueEvents) {\n${parts[3]}\nglobal.CitryVueEvents = CitryVueEvents;\n}\n` +
    "\n})(globalThis);\n",
  "utf8",
);
