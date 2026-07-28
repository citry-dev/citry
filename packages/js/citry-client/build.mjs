import { build } from "esbuild";

import { citryClientBuildOptions } from "./build-support.mjs";

await build(citryClientBuildOptions());
