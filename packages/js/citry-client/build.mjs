import { build } from "esbuild";

import { citryClientBuildOptions, citryCspClientBuildOptions, citryI18nBuildOptions } from "./build-support.mjs";

await Promise.all([
  build(citryClientBuildOptions()),
  build(citryCspClientBuildOptions()),
  build(citryI18nBuildOptions()),
]);
