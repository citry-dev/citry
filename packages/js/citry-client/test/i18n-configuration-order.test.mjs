import assert from "node:assert/strict";
import test from "node:test";
import { build } from "esbuild";

// An Events Render of a region with `<c-i18n c-client>` sends the project's i18n configuration
// again. The server may write its keys in another order than the page did, so the runtime must
// compare the two by content (#660).

const result = await build({
  entryPoints: ["src/citry-i18n-runtime.ts"],
  bundle: true,
  format: "esm",
  platform: "browser",
  write: false,
});
const wire = await import(`data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString("base64")}`);

const fail = (code, message) => {
  const error = new TypeError(message);
  error.code = code;
  throw error;
};

const numberRecord = {
  decimal: ".",
  digits: ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
  grouping: ",",
  minus_prefix: "-",
  minus_suffix: "",
  notation: "decimal",
  plus_prefix: "",
  plus_suffix: "",
  primary_group: 3,
  secondary_group: 3,
};

const context = (locale, direction) => ({
  catalog_revision: "catalog",
  direction,
  fallback_locales: [],
  formats_revision: "formats",
  locale,
  time_zone: null,
  tzdb_revision: "none",
});

const parser = (locale) => ({
  formats_revision: "formats",
  locale,
  number: { measurement: numberRecord },
  percent: {},
  revision: `parser-${locale}`,
  schema_version: 1,
});

function manifest({ formats, parsers, locales = ["en-US", "ar"] }) {
  return {
    catalog_revision: "catalog",
    contexts: { "en-US": context("en-US", "ltr"), ar: context("ar", "rtl") },
    formats,
    formats_revision: "formats",
    locales,
    messages_url: null,
    parsers,
    providers: [],
    requirements: [],
    runtime: "@fluent/bundle@0.19.1",
    schema_version: 1,
  };
}

function configuredOnce(first) {
  const state = { activeFluentFailures: null, configuration: null };
  const runtime = wire.createI18nWireRuntime(state, fail);
  state.configuration = runtime.configureManifest(first)[1];
  return runtime;
}

const pageManifest = manifest({
  formats: {
    number: { measurement: { input: { notation: "decimal" } } },
    percent: { completion: { input: { affix: "required" } } },
  },
  parsers: { "en-US": parser("en-US"), ar: parser("ar") },
});

test("a configuration with the same content in another key order is the same project", () => {
  const runtime = configuredOnce(pageManifest);
  const reordered = manifest({
    formats: {
      percent: { completion: { input: { affix: "required" } } },
      number: { measurement: { input: { notation: "decimal" } } },
    },
    parsers: { ar: parser("ar"), "en-US": parser("en-US") },
    locales: ["ar", "en-US"],
  });
  assert.doesNotThrow(() => runtime.configureManifest(reordered));
});

test("a configuration with different content is still refused", () => {
  const runtime = configuredOnce(pageManifest);
  const changedFormat = manifest({
    formats: {
      number: { measurement: { input: { notation: "decimal_or_scientific" } } },
      percent: { completion: { input: { affix: "required" } } },
    },
    parsers: { "en-US": parser("en-US"), ar: parser("ar") },
  });
  assert.throws(() => runtime.configureManifest(changedFormat), /different project/);
  const changedParser = manifest({
    formats: pageManifest.formats,
    parsers: { "en-US": parser("en-US"), ar: { ...parser("ar"), percent: {}, number: {} } },
  });
  assert.throws(() => runtime.configureManifest(changedParser), /different project/);
  const fewerLocales = {
    ...manifest({ formats: pageManifest.formats, parsers: { "en-US": parser("en-US") }, locales: ["en-US"] }),
    contexts: { "en-US": context("en-US", "ltr") },
  };
  assert.throws(() => runtime.configureManifest(fewerLocales), /different project/);
});

test("sameJsonContent ignores object key order and keeps array order", async () => {
  const coreBuild = await build({
    entryPoints: ["src/citry-i18n-core.ts"],
    bundle: true,
    format: "esm",
    platform: "browser",
    write: false,
  });
  const core = await import(
    `data:text/javascript;base64,${Buffer.from(coreBuild.outputFiles[0].text).toString("base64")}`
  );
  assert.ok(core.sameJsonContent({ a: 1, b: { c: [1, 2] } }, { b: { c: [1, 2] }, a: 1 }));
  assert.ok(!core.sameJsonContent({ a: [1, 2] }, { a: [2, 1] }), "array order counts");
  assert.ok(!core.sameJsonContent({ a: 1 }, { a: 1, b: 2 }));
  assert.ok(!core.sameJsonContent({ a: undefined }, { b: undefined }), "keys are compared, not only values");
  assert.ok(!core.sameJsonContent({ a: null }, { a: {} }));
  assert.ok(!core.sameJsonContent([], {}));
});
