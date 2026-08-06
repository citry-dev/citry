import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { build } from "esbuild";

import {
	applyOperations,
	parseCaseFile,
} from "../../../../_tooling/conformance.mjs";

const testsDirectory = new URL("../../tests/", import.meta.url);
const buildResult = await build({
	entryPoints: [new URL("../src/index.ts", import.meta.url).pathname],
	bundle: true,
	format: "esm",
	platform: "node",
	target: "node22",
	write: false,
});
const protocol = await import(
	`data:text/javascript;base64,${Buffer.from(buildResult.outputFiles[0].text).toString("base64")}`
);

const readJson = async (url) => JSON.parse(await readFile(url, "utf8"));

const canonicalValues = (vector) => {
	if (vector.manifest) {
		const { revision: _revision, ...unsigned } = vector.manifest;
		return [unsigned];
	}
	if (vector.input) return [vector.input];
	if (vector.equivalentInputJson)
		return vector.equivalentInputJson.map(JSON.parse);
	return [JSON.parse(vector.inputJson)];
};

test("replays shared conformance mutations against the runtime validator", async () => {
	const payload = await readJson(
		new URL("conformance-cases.json", testsDirectory),
	);
	const cases = parseCaseFile(payload);
	assert.ok(cases.length > 0);
	for (const entry of cases) {
		assert.ok(entry.implementations.includes("javascript"), entry.id);
		assert.equal(entry.schema, "manifest.schema.json", entry.id);
		const seed = await readJson(new URL(entry.seed, testsDirectory));
		const before = structuredClone(seed);
		const mutated = applyOperations(seed, entry.operations);
		assert.deepEqual(seed, before, `${entry.id} mutated its seed`);
		const issue = protocol.validateManifest(mutated);
		assert.ok(issue, `${entry.id} was accepted`);
		assert.deepEqual(
			{ path: issue.path, category: issue.category },
			entry.expected,
			entry.id,
		);
	}
});

test("accepts every valid fixture and rejects every invalid fixture", async () => {
	const entries = await readJson(new URL("index.json", testsDirectory));
	assert.equal(entries.length, 47);
	for (const entry of entries) {
		const manifest = await readJson(new URL(entry.manifest, testsDirectory));
		const issue = protocol.validateManifest(manifest);
		assert.equal(issue === null, entry.expect === "valid", entry.manifest);
	}
});

test("accepts the closed component range morph mode", async () => {
	const manifest = await readJson(
		new URL("component_tag_client_bindings.manifest.json", testsDirectory),
	);
	const nested = structuredClone(manifest.graphs[0].nestedComponents[0]);
	nested.morphMode = "ignore";
	assert.equal(protocol.validateNestedComponent(nested), null);
});

test("matches every canonical JSON and SHA-256 vector", async () => {
	const document = await readJson(
		new URL("canonicalization.json", testsDirectory),
	);
	assert.equal(document.format, "citry-client-graph-canonicalization/1");
	assert.ok(document.vectors.length > 0);
	for (const vector of document.vectors) {
		let canonical;
		try {
			canonical = canonicalValues(vector).map(protocol.canonicalJson);
		} catch (_error) {
			assert.equal(vector.expect, "reject", vector.name);
			continue;
		}
		assert.notEqual(vector.expect, "reject", vector.name);
		assert.ok(
			canonical.every((value) => value === canonical[0]),
			`${vector.name} equivalent inputs differ`,
		);
		if (vector.canonicalJson)
			assert.equal(canonical[0], vector.canonicalJson, vector.name);
		if (vector.canonicalUtf8Hex)
			assert.equal(
				Buffer.from(canonical[0], "utf8").toString("hex"),
				vector.canonicalUtf8Hex,
				vector.name,
			);
		if (vector.sha256)
			assert.equal(protocol.sha256(canonical[0]), vector.sha256, vector.name);
	}
});

test("strict JSON checks reject browser-only invalid values", async () => {
	const valid = await readJson(
		new URL("minimal.manifest.json", testsDirectory),
	);
	const cases = [];

	for (const value of [
		Number.NaN,
		Number.POSITIVE_INFINITY,
		Number.NEGATIVE_INFINITY,
	]) {
		const manifest = structuredClone(valid);
		manifest.graphs[0].graphId = value;
		cases.push(manifest);
	}

	const cyclic = structuredClone(valid);
	cyclic.graphs[0].self = cyclic.graphs[0];
	cases.push(cyclic);

	const sparse = structuredClone(valid);
	sparse.graphs.length = 2;
	cases.push(sparse);

	const symbol = structuredClone(valid);
	symbol[Symbol("unexpected")] = true;
	cases.push(symbol);

	const hidden = structuredClone(valid);
	Object.defineProperty(hidden, "unexpected", {
		configurable: true,
		enumerable: false,
		value: true,
	});
	cases.push(hidden);

	const accessor = structuredClone(valid);
	let getterCalls = 0;
	Object.defineProperty(accessor, "protocol", {
		configurable: true,
		enumerable: true,
		get() {
			getterCalls += 1;
			return protocol.PROTOCOL;
		},
	});
	cases.push(accessor);

	for (const manifest of cases) {
		const issue = protocol.validateManifest(manifest);
		assert.equal(issue?.category, "strict_json");
	}
	assert.equal(getterCalls, 0);
});

test("assertValidManifest returns the input or throws its protocol issue", async () => {
	const valid = await readJson(
		new URL("minimal.manifest.json", testsDirectory),
	);
	assert.equal(protocol.assertValidManifest(valid), valid);

	const invalid = structuredClone(valid);
	invalid.mode = "debug";
	assert.throws(
		() => protocol.assertValidManifest(invalid),
		(error) =>
			error instanceof protocol.ProtocolValueError &&
			error.issue.path === "/mode" &&
			error.issue.category === "enum",
	);
});
