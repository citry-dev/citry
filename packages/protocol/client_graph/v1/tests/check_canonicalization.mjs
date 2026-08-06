/** Check client-graph revision vectors with Node's standard library. */

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

const vectorsUrl = new URL("canonicalization.json", import.meta.url);

const canonicalJson = function (value) {
  if (value === null) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    if (!Number.isSafeInteger(value) || value < 0) throw new TypeError("integer is outside the client-graph range");
    return String(Object.is(value, -0) ? 0 : value);
  }
  if (typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (typeof value === "object") {
    const members = Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`);
    return `{${members.join(",")}}`;
  }
  throw new TypeError("value is not JSON");
};

const values = function (vector) {
  if (vector.manifest) {
    const { revision: _revision, ...unsigned } = vector.manifest;
    return [unsigned];
  }
  if (vector.input) return [vector.input];
  if (vector.equivalentInputJson) return vector.equivalentInputJson.map(JSON.parse);
  return [JSON.parse(vector.inputJson)];
};

const document = JSON.parse(readFileSync(vectorsUrl, "utf8"));
if (document.format !== "citry-client-graph-canonicalization/1" || !Array.isArray(document.vectors)) {
  throw new TypeError("unknown canonicalization vector format");
}

for (const vector of document.vectors) {
  let encoded;
  try {
    encoded = values(vector).map((value) => Buffer.from(canonicalJson(value), "utf8"));
  } catch (error) {
    if (vector.expect !== "reject") throw error;
    continue;
  }
  if (vector.expect === "reject") throw new Error(`${vector.name} unexpectedly passed`);
  if (!encoded.every((value) => value.equals(encoded[0]))) throw new Error(`${vector.name} equivalent inputs differ`);
  const canonical = encoded[0];
  if (vector.canonicalJson && canonical.toString("utf8") !== vector.canonicalJson) {
    throw new Error(`${vector.name} canonical JSON differs`);
  }
  if (vector.canonicalUtf8Hex && canonical.toString("hex") !== vector.canonicalUtf8Hex) {
    throw new Error(`${vector.name} canonical bytes differ`);
  }
  if (vector.sha256 && createHash("sha256").update(canonical).digest("hex") !== vector.sha256) {
    throw new Error(`${vector.name} hash differs`);
  }
}

console.log(`client-graph canonicalization: ok (${document.vectors.length} vectors)`);
