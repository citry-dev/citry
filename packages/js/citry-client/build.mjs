import { writeFile } from "node:fs/promises";

import { build } from "esbuild";

import {
  CITRY_DEV_CHECKS_PATH,
  CITRY_RUNTIME_PATH,
  buildCitryDevChecks,
  buildCitryI18n,
  buildCitryVueRuntime,
  citryVueBuildOptions,
  citryVueEventsBuildOptions,
  citryVueFragmentsBuildOptions,
} from "./build-support.mjs";

await Promise.all([
  build(citryVueBuildOptions()),
  build(citryVueEventsBuildOptions()),
  build(citryVueFragmentsBuildOptions()),
  buildCitryI18n(),
  buildCitryDevChecks().then((text) => writeFile(CITRY_DEV_CHECKS_PATH, text, "utf8")),
]);

// The combined runtime reads the files written above, so it is assembled only after they exist.
await writeFile(CITRY_RUNTIME_PATH, await buildCitryVueRuntime(), "utf8");
