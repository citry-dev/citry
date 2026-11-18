import assert from "node:assert/strict";
import test from "node:test";
import { build } from "esbuild";

// Format profiles, parser records and message entries arrive as plain JSON objects, which inherit
// `Object.prototype`. Each lookup below must find only names the server sent, so a name such as
// `constructor` fails with the same code as any other unknown name.

async function bundled(entry) {
  const result = await build({ entryPoints: [entry], bundle: true, format: "esm", platform: "browser", write: false });
  return import(`data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString("base64")}`);
}

const core = await bundled("src/citry-i18n-core.ts");
const wire = await bundled("src/citry-i18n-runtime.ts");

// Names an inherited lookup would find on `Object.prototype`.
const INHERITED = ["__proto__", "constructor", "toString", "hasOwnProperty", "valueOf"];

const fail = (code, message) => {
  const error = new TypeError(message);
  error.code = code;
  throw error;
};
const failsWith = (code) => (error) => {
  assert.equal(error.code, code, error.message);
  return true;
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

function configuredWire() {
  const runtime = wire.createI18nWireRuntime({ activeFluentFailures: null, configuration: null }, fail);
  const parser = runtime.parserArtifact(
    {
      formats_revision: "formats",
      locale: "en-US",
      number: { measurement: numberRecord },
      percent: {
        completion: {
          affix: "required",
          numbers: numberRecord,
          patterns: [
            { negative: false, prefix: "", suffix: "%" },
            { negative: true, prefix: "-", suffix: "%" },
            { negative: false, prefix: "", suffix: "%" },
          ],
        },
      },
      revision: "parser-r1",
      schema_version: 1,
    },
    "en-US",
    "formats",
  );
  const state = {
    activeFluentFailures: null,
    configuration: {
      catalogRevision: "catalog",
      formats: { number: { measurement: { input: { notation: "decimal" } } } },
      formatsRevision: "formats",
      parsers: new Map([["en-US", parser]]),
    },
  };
  // As in the plugin, a failure inside a Fluent function is recorded so the message reports its
  // code rather than Fluent's generic error.
  const live = wire.createI18nWireRuntime(state, (code, message) => {
    try {
      fail(code, message);
    } catch (error) {
      state.activeFluentFailures?.push(error);
      throw error;
    }
  });
  const internal = { state: { context: { locale: "en-US", time_zone: null } } };
  return { live, state, formatter: live.createFormatter(internal), parser: live.createParser(internal) };
}

test("a format profile is found only under a name the server configured", () => {
  const { formatter } = configuredWire();
  assert.equal(formatter.number("1234.5", { format: "measurement" }), "1,234.5");
  for (const name of ["nope", ...INHERITED]) {
    assert.throws(() => formatter.number("1", { format: name }), failsWith("I18N_FORMAT_INVALID"), name);
  }
  // A format kind with no profiles at all fails the same way, so the kind lookup reads own keys too.
  assert.throws(() => formatter.percent("1", { format: "constructor" }), failsWith("I18N_FORMAT_INVALID"));
});

test("a number or percent parser is found only under a name the parser artifact holds", () => {
  const { parser } = configuredWire();
  assert.equal(parser.number("1,234", { format: "measurement" }).value, "1234");
  for (const name of ["nope", ...INHERITED]) {
    assert.throws(() => parser.number("1", { format: name }), failsWith("I18N_PARSE_INVALID"), `number ${name}`);
    assert.throws(() => parser.percent("1%", { format: name }), failsWith("I18N_PARSE_INVALID"), `percent ${name}`);
  }
});

function messageArtifact(bundle, messages) {
  return {
    bundle_directions: { "en-US": "ltr" },
    bundles: { "en-US": bundle },
    catalog_revision: "catalog",
    formats_revision: "formats",
    messages,
    requested_locale: "en-US",
    revision: "artifact-r1",
    runtime: "@fluent/bundle@0.19.1",
    schema_version: 1,
  };
}

test("a message is formatted only under an id the artifact holds", () => {
  const { live } = configuredWire();
  const runtime = live.createMessageRuntime(
    messageArtifact("greeting = Hello\n", {
      greeting: { bundle_locale: "en-US", contract: {}, internal_id: "greeting" },
    }),
    "en-US",
  );
  assert.equal(runtime.format("greeting", {}), "Hello");
  for (const name of ["nope", ...INHERITED]) {
    assert.throws(() => runtime.format(name, {}), failsWith("I18N_MESSAGE_MISSING"), name);
  }
});

test("NUMBER in a message accepts only a profile the server configured", () => {
  const { live } = configuredWire();
  const runtime = live.createMessageRuntime(
    messageArtifact(
      'known = { NUMBER($n, profile: "measurement") }\ninherited = { NUMBER($n, profile: "constructor") }\n',
      {
        known: { bundle_locale: "en-US", contract: { n: "Decimal" }, internal_id: "known" },
        inherited: { bundle_locale: "en-US", contract: { n: "Decimal" }, internal_id: "inherited" },
      },
    ),
    "en-US",
  );
  assert.match(runtime.format("known", { n: "1234.5" }), /1,234\.5/);
  assert.throws(() => runtime.format("inherited", { n: "1" }), failsWith("I18N_NUMBER_INVALID"));
});

// The per-app service resolves a message across the provider's loaded artifacts, then reads the
// fallback bundle's direction. Both lookups take names from data.
function service(artifact) {
  const context = {
    catalog_revision: "catalog",
    direction: "ltr",
    fallback_locales: [],
    formats_revision: "formats",
    locale: "en-US",
    time_zone: null,
    tzdb_revision: "none",
  };
  const state = core.createI18nRuntimeState({ commitContext() {}, effect: () => () => {}, isAlive: () => true });
  const requirement = { artifacts: new Map([["en-US", { artifact, format: () => "text" }]]) };
  const root = { bindings: new Set(), definition: { id: "root" }, state: { context, status: {} } };
  return core.createPerAppI18nService(state, { providerRequirements: () => [requirement] }, root, {
    createFormatter: () => ({}),
    createParser: () => ({}),
    fail,
  });
}

test("the provider service resolves only message ids the artifact holds", () => {
  const i18n = service({ bundle_directions: { cs: "ltr" }, messages: { greeting: { bundle_locale: "cs" } } });
  assert.equal(i18n.tr("greeting"), "text");
  for (const name of ["nope", ...INHERITED]) {
    assert.throws(() => i18n.tr(name), failsWith("I18N_MESSAGE_MISSING"), name);
  }
});

test("a fallback bundle's direction is read only from directions the artifact lists", () => {
  // A bundle locale that names an `Object.prototype` member has no direction of its own.
  const i18n = service({ bundle_directions: {}, messages: { greeting: { bundle_locale: "constructor" } } });
  assert.throws(() => i18n.tr("greeting"), failsWith("I18N_ARTIFACT_INVALID"));
});

test("ownValue reads own keys only", () => {
  assert.equal(core.ownValue({ a: 1 }, "a"), 1);
  assert.equal(core.ownValue({ a: 1 }, "constructor"), undefined);
  assert.equal(core.ownValue(JSON.parse('{"__proto__": 2}'), "__proto__"), 2);
  assert.equal(core.ownValue(undefined, "a"), undefined);
});
