import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { build } from "esbuild";

export const VUE_VERSION = "3.5.42";
export const VUE_GENERATED_BANNER =
  "/* Citry Vue runtime. GENERATED FILE, do not edit: built from packages/js/citry-client/src/citry-vue.ts (pnpm run build there). Bundles Vue 3.5.42 runtime-only (MIT). */";
export const VUE_EVENTS_GENERATED_BANNER =
  "/* Citry Vue Events bridge. GENERATED FILE, do not edit: built from packages/js/citry-client/src/citry-events-vue.ts (pnpm run build there). */";
export const VUE_FRAGMENTS_GENERATED_BANNER =
  "/* Citry Vue fragment manager. GENERATED FILE, do not edit: built from packages/js/citry-client/src/citry-fragments.ts (pnpm run build there). */";
export const I18N_GENERATED_BANNER =
  "/* Citry Vue i18n plugin. GENERATED FILE, do not edit: built from packages/js/citry-client/src/citry-i18n-vue.ts (pnpm run build there). Bundles @fluent/bundle 0.19.1 (Apache-2.0). */";

const DELIVERY_MINIFY_OPTIONS = {
  charset: "ascii",
  keepNames: false,
  legalComments: "inline",
  minifyIdentifiers: false,
  minifySyntax: false,
  minifyWhitespace: true,
};

const rejectDeliveryOverrides = function (overrides) {
  const ownedKeys = [
    ...Object.keys(DELIVERY_MINIFY_OPTIONS),
    "drop",
    "mangleCache",
    "mangleProps",
    "mangleQuoted",
    "minify",
    "pure",
    "reserveProps",
  ];
  for (const key of ownedKeys) {
    if (Object.hasOwn(overrides, key)) {
      throw new Error("The Citry client build owns its delivery minification settings.");
    }
  }
};

const browserBuildOptions = function ({ entry, globalName, outfile, banner }, overrides = {}) {
  rejectDeliveryOverrides(overrides);
  return {
    entryPoints: [fileURLToPath(new URL(entry, import.meta.url))],
    bundle: true,
    format: "iife",
    globalName,
    platform: "browser",
    target: "es2020",
    tsconfigRaw: {},
    ...DELIVERY_MINIFY_OPTIONS,
    banner: { js: banner },
    outfile: fileURLToPath(new URL(outfile, import.meta.url)),
    ...overrides,
  };
};

export const citryVueBuildOptions = function (overrides = {}) {
  return {
    ...browserBuildOptions(
      {
        entry: "src/citry-vue.ts",
        globalName: "Vue",
        outfile: "../../py/citry/citry/_vue/vue.js",
        banner: VUE_GENERATED_BANNER,
      },
      overrides,
    ),
    define: {
      "process.env.NODE_ENV": '"production"',
      __VUE_OPTIONS_API__: "true",
      __VUE_PROD_DEVTOOLS__: "false",
      __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: "false",
    },
    minifyIdentifiers: true,
    minifySyntax: true,
  };
};

export const citryVueEventsBuildOptions = function (overrides = {}) {
  return browserBuildOptions(
    {
      entry: "src/citry-events-vue.ts",
      globalName: "CitryVueEvents",
      outfile: "../../py/citry/citry/_vue/events.js",
      banner: VUE_EVENTS_GENERATED_BANNER,
    },
    overrides,
  );
};

export const citryVueFragmentsBuildOptions = function (overrides = {}) {
  return browserBuildOptions(
    {
      entry: "src/citry-fragments.ts",
      globalName: "CitryVueFragments",
      outfile: "../../py/citry/citry/_vue/fragments.js",
      banner: VUE_FRAGMENTS_GENERATED_BANNER,
    },
    overrides,
  );
};

export const citryI18nBuildOptions = function (overrides = {}) {
  const { i18nBuildId = "CITRY_I18N_BUILD_ID_SENTINEL", ...buildOverrides } = overrides;
  return browserBuildOptions(
    {
      entry: "src/citry-i18n-vue.ts",
      globalName: undefined,
      outfile: "../../py/citry/citry/ext/i18n/client/vue-plugin.source.js",
      banner: I18N_GENERATED_BANNER,
    },
    { ...buildOverrides, define: { __CITRY_I18N_BUILD_ID__: JSON.stringify(i18nBuildId) } },
  );
};

export const buildCitryI18n = async function (overrides = {}) {
  const first = await build(citryI18nBuildOptions({ ...overrides, write: false, outfile: undefined }));
  const buildId = createHash("sha256").update(first.outputFiles[0].text).digest("hex");
  return build(citryI18nBuildOptions({ ...overrides, i18nBuildId: buildId }));
};
