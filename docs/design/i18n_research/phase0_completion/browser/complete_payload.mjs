import { FluentBundle, FluentResource } from "@fluent/bundle";

import "../../provider_runtime/browser/candidate.js";
import "../../rich_client_relocation/browser/candidate.js";

export const FORMAT = "citry-i18n-client-research/1";

function reject(code, message) {
  const error = new TypeError(`[Citry] i18n client: ${message}`);
  error.code = code;
  throw error;
}

function exactObject(value, name) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    reject("I18N_WIRE_INVALID", `${name} must be an object.`);
  }
  return value;
}

function exactKeys(value, keys, name) {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) {
    reject("I18N_WIRE_INVALID", `${name} has unknown or missing fields.`);
  }
}

function decimalString(value, name) {
  if (typeof value !== "string" || !/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$/.test(value)) {
    reject("I18N_WIRE_INVALID", `${name} must be a canonical decimal string.`);
  }
  return value;
}

function integer(value, name, minimum, maximum) {
  if (!Number.isSafeInteger(value) || value < minimum || value > maximum) {
    reject("I18N_WIRE_INVALID", `${name} is outside its supported range.`);
  }
  return value;
}

export function decodeWire(input) {
  const value = exactObject(input, "a tagged value");
  if (value.type === "null") {
    exactKeys(value, ["type"], "a null value");
    return null;
  }
  if (value.type === "bool") {
    exactKeys(value, ["type", "value"], "a boolean value");
    if (typeof value.value !== "boolean") reject("I18N_WIRE_INVALID", "a boolean value must contain a boolean.");
    return value.value;
  }
  if (value.type === "text") {
    exactKeys(value, ["type", "value"], "a text value");
    if (typeof value.value !== "string") reject("I18N_WIRE_INVALID", "a text value must contain text.");
    return value.value;
  }
  if (value.type === "int" || value.type === "decimal") {
    exactKeys(value, ["type", "value"], `a ${value.type} value`);
    return Object.freeze({ type: value.type, value: decimalString(value.value, value.type) });
  }
  if (value.type === "f64") {
    exactKeys(value, ["bits", "type"], "a binary64 value");
    if (typeof value.bits !== "string" || !/^[0-9a-f]{16}$/.test(value.bits)) {
      reject("I18N_WIRE_INVALID", "a binary64 value needs exactly 16 lowercase hexadecimal digits.");
    }
    const bytes = Uint8Array.from(value.bits.match(/../g), (part) => Number.parseInt(part, 16));
    const number = new DataView(bytes.buffer).getFloat64(0, false);
    if (!Number.isFinite(number)) reject("I18N_WIRE_INVALID", "a binary64 value must be finite.");
    return number;
  }
  if (value.type === "date") {
    exactKeys(value, ["calendar", "day", "month", "type", "year"], "a date value");
    if (typeof value.calendar !== "string" || value.calendar.length === 0) {
      reject("I18N_WIRE_INVALID", "a date value needs a calendar.");
    }
    return Object.freeze({
      calendar: value.calendar,
      day: integer(value.day, "date.day", 1, 31),
      month: integer(value.month, "date.month", 1, 13),
      year: integer(value.year, "date.year", -999999, 999999),
    });
  }
  if (value.type === "time") {
    exactKeys(value, ["hour", "microsecond", "minute", "second", "type"], "a time value");
    return Object.freeze({
      hour: integer(value.hour, "time.hour", 0, 23),
      microsecond: integer(value.microsecond, "time.microsecond", 0, 999999),
      minute: integer(value.minute, "time.minute", 0, 59),
      second: integer(value.second, "time.second", 0, 59),
    });
  }
  if (value.type === "instant") {
    exactKeys(value, ["epochMilliseconds", "timeZone", "type"], "an instant value");
    const milliseconds = decimalString(value.epochMilliseconds, "instant.epochMilliseconds");
    if (!/^-?(?:0|[1-9][0-9]*)$/.test(milliseconds) || typeof value.timeZone !== "string") {
      reject("I18N_WIRE_INVALID", "an instant needs integer milliseconds and a time-zone ID.");
    }
    const numeric = Number(milliseconds);
    if (!Number.isSafeInteger(numeric) || Math.abs(numeric) > 8_640_000_000_000_000) {
      reject("I18N_WIRE_INVALID", "an instant is outside ECMA Date's exact range.");
    }
    return Object.freeze({ date: new Date(numeric), timeZone: value.timeZone });
  }
  if (value.type === "list") {
    exactKeys(value, ["items", "type"], "a list value");
    if (!Array.isArray(value.items)) reject("I18N_WIRE_INVALID", "a list value needs an item array.");
    return Object.freeze(value.items.map(decodeWire));
  }
  reject("I18N_WIRE_INVALID", `unknown tagged value type '${String(value.type)}'.`);
}

export function createMessageRuntime(artifact) {
  const value = exactObject(artifact, "the client artifact");
  exactKeys(value, ["locale", "messages", "publicIds", "revision"], "the client artifact");
  if (
    typeof value.locale !== "string"
    || typeof value.messages !== "string"
    || typeof value.revision !== "string"
    || !Array.isArray(value.publicIds)
  ) {
    reject("I18N_ARTIFACT_INVALID", "the client artifact fields have invalid types.");
  }
  const resource = new FluentResource(value.messages);
  const bundle = new FluentBundle(value.locale, { useIsolating: false });
  const errors = bundle.addResource(resource, { allowOverrides: false });
  if (errors.length !== 0) reject("I18N_ARTIFACT_INVALID", `the client artifact has ${errors.length} syntax errors.`);
  for (const id of value.publicIds) {
    if (typeof id !== "string" || bundle.getMessage(id)?.value === null || bundle.getMessage(id) === undefined) {
      reject("I18N_ARTIFACT_INVALID", `the client artifact is missing public message '${String(id)}'.`);
    }
  }
  return Object.freeze({
    format(id, rawArgs = {}) {
      if (!value.publicIds.includes(id)) reject("I18N_MESSAGE_INVALID", `message '${id}' is not public.`);
      const message = bundle.getMessage(id);
      if (message?.value === null || message === undefined) reject("I18N_MESSAGE_INVALID", `message '${id}' is absent.`);
      const args = Object.fromEntries(Object.entries(rawArgs).map(([name, item]) => [name, decodeWire(item)]));
      const formatErrors = [];
      const output = bundle.formatPattern(message.value, args, formatErrors);
      if (formatErrors.length !== 0) reject("I18N_MESSAGE_INVALID", `message '${id}' failed to format.`);
      return output;
    },
    locale: value.locale,
    revision: value.revision,
  });
}

export const providerFormat = globalThis.CitryI18nProviderCandidate.FORMAT;
export const richRelocationFormat = globalThis.CitryRichRelocationCandidate.FORMAT;
