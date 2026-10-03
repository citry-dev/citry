import { writeFile } from "node:fs/promises";

import { build } from "esbuild";

import {
  CITRY_RUNTIME_PATH,
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
]);

// The combined runtime reads the files written above, so it is assembled only after they exist.
await writeFile(CITRY_RUNTIME_PATH, await buildCitryVueRuntime(), "utf8");
