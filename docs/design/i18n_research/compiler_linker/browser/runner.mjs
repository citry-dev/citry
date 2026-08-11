import fs from "node:fs";

import {
  FluentBundle,
  FluentResource,
} from "../../runtime_backend/browser/node_modules/@fluent/bundle/index.js";

const FSI = "\u2068";
const PDI = "\u2069";
const fluentPackage = JSON.parse(
  fs.readFileSync(
    new URL("../../runtime_backend/browser/node_modules/@fluent/bundle/package.json", import.meta.url),
    "utf8",
  ),
);

function native(value) {
  return value?.valueOf?.() ?? value;
}

function scalar(value) {
  return String(native(value));
}

function pluralCategory(locale, positional, named) {
  const value = Number(native(positional[0]));
  const mode = named.mode === undefined ? "cardinal" : scalar(named.mode);
  if (mode === "ordinal") {
    if (locale !== "en-US" || !Number.isInteger(value)) return "other";
    if ([11, 12, 13].includes(value % 100)) return "other";
    return ({ 1: "one", 2: "two", 3: "few" })[value % 10] ?? "other";
  }
  if (mode !== "cardinal") throw new TypeError("unknown plural mode");
  if (named.exact !== undefined) {
    const exact = scalar(named.exact)
      .split(",")
      .find((candidate) => Number(candidate) === value);
    if (exact !== undefined) return `exact-${exact}`;
  }
  if (locale === "cs-CZ") {
    if (!Number.isInteger(value)) return "many";
    return value === 1 ? "one" : value >= 2 && value <= 4 ? "few" : "other";
  }
  return value === 1 ? "one" : "other";
}

function functions(locale) {
  return {
    CITRY_TEXT(positional, named) {
      if (Object.keys(named).length !== 0) throw new TypeError("invalid CITRY_TEXT options");
      return `${FSI}${scalar(positional[0])}${PDI}`;
    },
    SLOT(positional, named) {
      if (Object.keys(named).length !== 0) throw new TypeError("invalid SLOT options");
      const marker = scalar(positional[0]);
      if (!marker.startsWith("__CITRY_SLOT_")) throw new TypeError("invalid Slot marker");
      return marker;
    },
    CITRY_PLURAL: (positional, named) => pluralCategory(locale, positional, named),
    NUMBER(positional, named) {
      const profile = scalar(named.profile);
      return `${FSI}NUM[value=${scalar(positional[0])},profile=${profile}]${PDI}`;
    },
  };
}

const payload = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const bundles = new Map();
for (const [locale, source] of Object.entries(payload.artifacts)) {
  const bundle = new FluentBundle(locale, {
    functions: functions(locale),
    useIsolating: false,
  });
  const errors = bundle.addResource(new FluentResource(source), { allowOverrides: false });
  if (errors.length > 0) throw new Error(errors.map(String).join("; "));
  bundles.set(locale, bundle);
}

const results = {};
for (const testCase of payload.cases) {
  const bundle = bundles.get(testCase.bundle_locale);
  const message = bundle.getMessage(testCase.internal_id);
  if (message?.value === null || message?.value === undefined) {
    throw new Error(`missing ${testCase.internal_id}`);
  }
  const errors = [];
  const value = bundle.formatPattern(message.value, testCase.args, errors);
  if (errors.length > 0) throw new Error(errors.map(String).join("; "));
  results[testCase.name] = {
    bundle_locale: testCase.bundle_locale,
    value,
  };
}

process.stdout.write(
  `${JSON.stringify({
    candidate: "browser",
    results,
    runtime_versions: { "@fluent/bundle": fluentPackage.version },
  })}\n`,
);
