import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { FluentBundle, FluentResource } from "@fluent/bundle";

const FSI = "\u2068";
const LRI = "\u2066";
const RLI = "\u2067";
const PDI = "\u2069";
const HOSTILE_NAME = "אבג <Ada&Co>";
const BIDI_CONTROLS = new Set([..."\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"]);
const BIDI_PARAGRAPH_BOUNDARIES = new Set([..."\n\r\u001c\u001d\u001e\u0085\u2029"]);
const fluentEntry = fileURLToPath(import.meta.resolve("@fluent/bundle"));
const fluentPackage = JSON.parse(
  fs.readFileSync(path.resolve(path.dirname(fluentEntry), "package.json"), "utf8"),
);


function native(value) {
  return value?.valueOf?.() ?? value;
}


function number(positional, named) {
  const value = native(positional[0]);
  const profile = native(named.profile);
  const currency = native(named.currency);
  const suffix = currency === undefined ? "" : `,currency=${currency}`;
  return `${FSI}NUM[value=${value},profile=${profile}${suffix}]${PDI}`;
}


function datetimeValue(positional, named) {
  return `${FSI}DATE[value=${native(positional[0])},profile=${native(named.profile)}]${PDI}`;
}


function isolateText(positional, named) {
  if (Object.keys(named).length !== 0) throw new TypeError("CITRY_TEXT does not accept named arguments");
  const value = String(native(positional[0]));
  if ([...value].some((char) => BIDI_CONTROLS.has(char))) {
    throw new TypeError("CITRY_TEXT rejects embedded bidi controls");
  }
  if ([...value].some((char) => BIDI_PARAGRAPH_BOUNDARIES.has(char))) {
    throw new TypeError("CITRY_TEXT rejects embedded bidi paragraph boundaries");
  }
  return `${FSI}${value}${PDI}`;
}


function keepSlot(positional, named) {
  if (Object.keys(named).length !== 0) throw new TypeError("SLOT does not accept named arguments");
  const value = native(positional[0]);
  if (typeof value !== "string" || !value.startsWith("__CITRY_SLOT_")) {
    throw new TypeError("SLOT accepts only an opaque Citry slot marker");
  }
  return value;
}


function pluralCategory(locale, positional, named) {
  const value = Number(native(positional[0]));
  const mode = named.mode === undefined ? "cardinal" : String(native(named.mode));
  if (mode === "ordinal") {
    if (locale !== "en-US" || !Number.isInteger(value)) return "other";
    if ([11, 12, 13].includes(value % 100)) return "other";
    return ({ 1: "one", 2: "two", 3: "few" })[value % 10] ?? "other";
  }
  if (mode !== "cardinal") throw new TypeError("unknown CITRY_PLURAL mode");
  if (named.exact !== undefined) {
    const matched = String(native(named.exact)).split(",").find((item) => Number(item) === value);
    if (matched !== undefined) return `exact-${matched}`;
  }
  if (Object.keys(named).some((name) => !["exact", "mode"].includes(name))) {
    throw new TypeError("unknown CITRY_PLURAL option");
  }
  if (locale === "cs-CZ") {
    if (!Number.isInteger(value)) return "many";
    return value === 1 ? "one" : value >= 2 && value <= 4 ? "few" : "other";
  }
  return value === 1 ? "one" : "other";
}


function markerFor(seed, locale) {
  return `__CITRY_SLOT_${seed}_${locale.replaceAll("-", "_")}_terms_link__`;
}


function validateCatalogSource(source) {
  if ([...source].some((char) => BIDI_CONTROLS.has(char))) {
    throw new TypeError("authored catalog contains a prohibited bidi-control character");
  }
}


function validateDecodedCatalogText(value) {
  if ([...value].some((char) => BIDI_CONTROLS.has(char))) {
    throw new TypeError("decoded catalog contains a prohibited bidi-control character");
  }
}


function isolateKnownDirectionParagraphs(value, direction) {
  const initiator = direction === "ltr" ? LRI : RLI;
  const output = [];
  let start = 0;
  let index = 0;
  while (index < value.length) {
    if (!BIDI_PARAGRAPH_BOUNDARIES.has(value[index])) {
      index += 1;
      continue;
    }
    output.push(`${initiator}${value.slice(start, index)}${PDI}`);
    let end = index + 1;
    if (value[index] === "\r" && value[end] === "\n") end += 1;
    output.push(value.slice(index, end));
    start = end;
    index = end;
  }
  output.push(`${initiator}${value.slice(start)}${PDI}`);
  return output.join("");
}


function* hostileCatalogSources(controlHex, forms) {
  for (const hexValue of controlHex) {
    for (const form of forms) {
      let encoded;
      if (form === "literal") encoded = String.fromCodePoint(Number.parseInt(hexValue, 16));
      else if (form === "u4") encoded = `{ "\\u${hexValue}" }`;
      else if (form === "U6") encoded = `{ "\\U${Number.parseInt(hexValue, 16).toString(16).toUpperCase().padStart(6, "0")}" }`;
      else throw new Error(`unknown hostile catalog escape form ${form}`);
      yield `hostile = ${encoded}`;
    }
  }
}


function bundleFor(locale, source) {
  validateCatalogSource(source);
  const bundle = new FluentBundle(locale, {
    functions: {
      NUMBER: number,
      DATETIME: datetimeValue,
      SLOT: keepSlot,
      CITRY_TEXT: isolateText,
      CITRY_PLURAL: (positional, named) => pluralCategory(locale, positional, named),
    },
    useIsolating: false,
  });
  const errors = bundle.addResource(new FluentResource(source));
  if (errors.length !== 0) throw new Error(errors.map(String).join("; "));
  return bundle;
}


function validateRuntimeContract(messageId, args, marker) {
  for (const value of Object.values(args)) {
    if (typeof value === "string" && [...value].some((char) => BIDI_CONTROLS.has(char))) {
      throw new TypeError(`${messageId} contains a prohibited bidi-control scalar`);
    }
    if (typeof value === "string" && [...value].some((char) => BIDI_PARAGRAPH_BOUNDARIES.has(char))) {
      throw new TypeError(`${messageId} contains a prohibited bidi-paragraph scalar`);
    }
  }
  if (["inbox-count", "acceptance", "invalid-plural-input", "ordinal-position"].includes(messageId)) {
    const field = messageId === "invalid-plural-input"
      ? "value"
      : messageId === "ordinal-position"
        ? "position"
        : "count";
    if (!Number.isFinite(args[field]) || Math.abs(args[field]) > Number.MAX_SAFE_INTEGER) {
      throw new TypeError(`${messageId} $${field} must be a finite safe number before resolution`);
    }
  }
  if (messageId === "acceptance" && args.terms_link !== marker) {
    throw new TypeError("acceptance $terms_link must be the current opaque Slot marker");
  }
  if (messageId === "slot-function-scalar" && args.value !== marker) {
    throw new TypeError("slot-function-scalar $value must be a Slot before resolution");
  }
}


function formatValue(bundle, messageId, args, attribute = null, options = {}) {
  if (options.validate !== false) validateRuntimeContract(messageId, args, options.marker);
  const message = bundle.getMessage(messageId);
  if (message === undefined) throw new Error(`missing message ${messageId}`);
  const pattern = attribute === null ? message.value : message.attributes[attribute];
  const errors = [];
  const value = bundle.formatPattern(pattern, args, errors);
  if (errors.length !== 0) throw new Error(errors.map(String).join("; "));
  return value;
}


function ensureNoCollision(source, args, marker) {
  if (source.includes(marker)) throw new Error("slot marker collides with a catalog resource");
  if (Object.values(args).some((value) => typeof value === "string" && value.includes(marker))) {
    throw new Error("slot marker collides with a scalar input");
  }
}


function splitSlot(value, marker) {
  const count = value.split(marker).length - 1;
  if (count === 0) throw new Error("expected at least one slot marker, received 0");
  const isolatedMarker = `${FSI}${marker}${PDI}`;
  if (value.includes(isolatedMarker)) throw new Error("slot marker was unexpectedly wrapped as scalar text");
  const parts = value.split(marker);
  const output = [];
  for (const [index, part] of parts.entries()) {
    output.push({ kind: "text", value: part });
    if (index < count) output.push({ kind: "slot", name: "terms_link", occurrence: index });
  }
  return output;
}


const fixtures = process.argv[2];
const markerSeed = process.argv[3];
const generatedLayers = fs.readFileSync(path.join(fixtures, "layered-generated.ftl"), "utf8");
const hostileConfig = JSON.parse(
  fs.readFileSync(path.join(fixtures, "hostile-bidi-control.json"), "utf8"),
);
const cases = {};
const markers = [];
let resolutionMarkersDistinct = true;
const sources = {};
for (const locale of ["en-US", "cs-CZ"]) {
  const marker = markerFor(markerSeed, locale);
  markers.push(marker);
  const source = `${fs.readFileSync(path.join(fixtures, `${locale}.ftl`), "utf8")}\n${generatedLayers}`;
  sources[locale] = source;
  const bundle = bundleFor(locale, source);
  const args = {
    account_name: HOSTILE_NAME,
    amount: 1234.5,
    count: 2,
    due_ms: 1782864000000,
    position: 2,
    terms_link: marker,
  };
  const { terms_link: _slot, ...scalarArgs } = args;
  ensureNoCollision(source, scalarArgs, marker);
  const options = { marker };
  const rich = splitSlot(formatValue(bundle, "acceptance", args, null, options), marker);
  const secondMarker = markerFor(`${markerSeed}_resolution_2`, locale);
  resolutionMarkersDistinct &&= secondMarker !== marker;
  const secondArgs = { ...args, terms_link: secondMarker };
  const { terms_link: _secondSlot, ...secondScalarArgs } = secondArgs;
  ensureNoCollision(source, secondScalarArgs, secondMarker);
  const secondRich = splitSlot(
    formatValue(bundle, "acceptance", secondArgs, null, { marker: secondMarker }),
    secondMarker,
  );
  if (JSON.stringify(secondRich) !== JSON.stringify(rich)) {
    throw new Error(`${locale} changed normalized rich output across fresh markers`);
  }
  cases[locale] = {
    summary: formatValue(bundle, "account-summary", args, null, options),
    attribute: formatValue(bundle, "account-actions", args, "aria-label", options),
    plural_0: formatValue(bundle, "inbox-count", { ...args, count: 0 }, null, options),
    plural_negative_zero: formatValue(bundle, "inbox-count", { ...args, count: -0 }, null, options),
    plural_1: formatValue(bundle, "inbox-count", { ...args, count: 1 }, null, options),
    plural_2: formatValue(bundle, "inbox-count", args, null, options),
    plural_1_5: formatValue(bundle, "inbox-count", { ...args, count: 1.5 }, null, options),
    plural_2_5: formatValue(bundle, "inbox-count", { ...args, count: 2.5 }, null, options),
    plural_5: formatValue(bundle, "inbox-count", { ...args, count: 5 }, null, options),
    ordinal_1: formatValue(bundle, "ordinal-position", { ...args, position: 1 }, null, options),
    ordinal_2: formatValue(bundle, "ordinal-position", args, null, options),
    ordinal_3: formatValue(bundle, "ordinal-position", { ...args, position: 3 }, null, options),
    ordinal_4: formatValue(bundle, "ordinal-position", { ...args, position: 4 }, null, options),
    ordinal_11: formatValue(bundle, "ordinal-position", { ...args, position: 11 }, null, options),
    ordinal_21: formatValue(bundle, "ordinal-position", { ...args, position: 21 }, null, options),
    balance: formatValue(bundle, "balance", args, null, options),
    due_date: formatValue(bundle, "due-date", args, null, options),
    layered_reference: formatValue(bundle, "citry-lib-wrapper", args, null, options),
    multiline_fallback_isolated: isolateKnownDirectionParagraphs(
      formatValue(bundle, "multiline-fallback", args, null, options),
      "ltr",
    ),
    rich,
  };
}

const marker = markers[0];
const invalid = bundleFor("en-US", fs.readFileSync(path.join(fixtures, "invalid.ftl"), "utf8"));
const rejections = {};
for (const [rejectionName, messageId, args] of [
  ["unknown-variable", "unknown-variable", {}],
  ["unknown-function", "unknown-function", { value: 1 }],
  ["slot-function-scalar", "slot-function-scalar", { value: "ordinary scalar" }],
  ["invalid-plural-input", "invalid-plural-input", { value: "not a number" }],
  ["invalid-plural-nan", "invalid-plural-input", { value: Number.NaN }],
  ["invalid-plural-infinity", "invalid-plural-input", { value: Number.POSITIVE_INFINITY }],
]) {
  try {
    formatValue(invalid, messageId, args, null, { marker });
  } catch (error) {
    rejections[rejectionName] = String(error.message);
  }
}
for (const [name, value] of [
  ["slot_marker_omitted", "marker omitted"],
  ["slot_marker_wrapped", `${FSI}${marker}${PDI}`],
]) {
  try {
    splitSlot(value, marker);
  } catch (error) {
    rejections[name] = String(error.message);
  }
}
try {
  ensureNoCollision(sources["en-US"] + marker, {}, marker);
} catch (error) {
  rejections.slot_catalog_collision = String(error.message);
}
try {
  ensureNoCollision(sources["en-US"], { hostile: marker }, marker);
} catch (error) {
  rejections.slot_scalar_collision = String(error.message);
}
const dangerousBidi = `prefix${PDI}\u202eoverride\u202c`;
const enBundle = bundleFor("en-US", sources["en-US"]);
for (const [name, messageId, badArgs] of [
  ["bidi-control-plain", "account-summary", { account_name: dangerousBidi }],
  [
    "bidi-control-rich",
    "acceptance",
    { account_name: dangerousBidi, count: 2, terms_link: marker },
  ],
]) {
  try {
    formatValue(enBundle, messageId, badArgs, null, { marker });
  } catch (error) {
    rejections[name] = String(error.message);
  }
}
const paragraphRejections = { plain: 0, rich: 0 };
for (const hexValue of hostileConfig.paragraph_boundary_hex) {
  const boundary = String.fromCodePoint(Number.parseInt(hexValue, 16));
  const badValue = `before${boundary}אבג`;
  for (const [sink, messageId, badArgs] of [
    ["plain", "account-summary", { account_name: badValue }],
    ["rich", "acceptance", { account_name: badValue, count: 2, terms_link: marker }],
  ]) {
    try {
      formatValue(enBundle, messageId, badArgs, null, { marker });
    } catch (error) {
      if (error instanceof TypeError) paragraphRejections[sink] += 1;
      else throw error;
    }
  }
}
const expectedParagraphRejections = hostileConfig.paragraph_boundary_hex.length;
for (const [sink, count] of Object.entries(paragraphRejections)) {
  if (count !== expectedParagraphRejections) {
    throw new Error(`${sink} rejected ${count} bidi paragraph boundaries, expected ${expectedParagraphRejections}`);
  }
  rejections[`paragraph-boundary-${sink}`] = `rejected all ${count} Unicode bidi paragraph boundaries`;
}

let catalogRejections = 0;
for (const hostileCatalog of hostileCatalogSources(
  hostileConfig.bidi_control_hex,
  hostileConfig.fluent_escape_forms,
)) {
  try {
    const hostileBundle = bundleFor("en-US", hostileCatalog);
    const decoded = formatValue(hostileBundle, "hostile", {}, null, { validate: false });
    validateDecodedCatalogText(decoded);
  } catch (error) {
    if (error instanceof TypeError) catalogRejections += 1;
    else throw error;
  }
}
const expectedCatalogRejections = hostileConfig.bidi_control_hex.length * hostileConfig.fluent_escape_forms.length;
if (catalogRejections !== expectedCatalogRejections) {
  throw new Error(`rejected ${catalogRejections} catalog bidi cases, expected ${expectedCatalogRejections}`);
}
rejections["bidi-control-catalog"] = `rejected all ${catalogRejections} literal and escaped bidi-control cases`;

const paragraphIsolationCases = [
  ...hostileConfig.paragraph_boundary_hex.map((value) => String.fromCodePoint(Number.parseInt(value, 16))),
  "\r\n",
];
for (const boundary of paragraphIsolationCases) {
  const actual = isolateKnownDirectionParagraphs(`left${boundary}אבג`, "ltr");
  const expected = `${LRI}left${PDI}${boundary}${LRI}אבג${PDI}`;
  if (actual !== expected) throw new Error(`paragraph isolation failed for ${JSON.stringify(boundary)}`);
}

const unsafe_runtime_behaviors = {
  slot_as_selector: formatValue(
    invalid,
    "slot-as-selector",
    { terms_link: marker },
    null,
    { marker, validate: false },
  ),
};
console.log(JSON.stringify({
  candidate: "browser",
  cases,
  runtime_versions: { "@fluent/bundle": fluentPackage.version },
  marker_properties: {
    distinct_per_locale: new Set(markers).size === markers.length,
    distinct_per_resolution: resolutionMarkersDistinct,
  },
  bidi_properties: {
    catalog_cases_rejected: catalogRejections,
    catalog_escape_forms: hostileConfig.fluent_escape_forms,
    paragraph_boundaries_rejected_per_scalar_sink: expectedParagraphRejections,
    whole_message_paragraph_cases_isolated: paragraphIsolationCases.length,
  },
  rejections,
  unsafe_runtime_behaviors,
}));
