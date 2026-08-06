import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
	applyOperations,
	CASE_FORMAT,
	parseCaseFile,
} from "../../../../_tooling/conformance.mjs";

const testsDirectory = new URL("../../tests/", import.meta.url);

test("client-graph JavaScript replays every shared conformance mutation", async () => {
	const payload = JSON.parse(
		await readFile(new URL("conformance-cases.json", testsDirectory), "utf8"),
	);
	const cases = parseCaseFile(payload);
	assert.ok(cases.length > 0);
	for (const entry of cases) {
		assert.ok(entry.implementations.includes("javascript"), entry.id);
		const seed = JSON.parse(
			await readFile(new URL(entry.seed, testsDirectory), "utf8"),
		);
		const before = structuredClone(seed);
		const mutated = applyOperations(seed, entry.operations);
		assert.deepEqual(seed, before, `${entry.id} mutated its seed`);
		assert.notDeepEqual(mutated, seed, `${entry.id} did not change its seed`);
	}
});

test("object mutation keeps __proto__ as an ordinary JSON member", () => {
	const mutated = applyOperations({}, [
		{ op: "add", path: "/__proto__", value: { polluted: true } },
	]);
	assert.equal(Object.getPrototypeOf(mutated), Object.prototype);
	assert.equal(Object.hasOwn(mutated, "__proto__"), true);
	assert.deepEqual(
		Object.getOwnPropertyDescriptor(mutated, "__proto__")?.value,
		{ polluted: true },
	);
	assert.equal({}.polluted, undefined);
});

test("array mutation accepts only ASCII indexes", () => {
	assert.throws(
		() => applyOperations([0, 1], [{ op: "replace", path: "/١", value: 2 }]),
		/invalid array index/u,
	);
});

test("case data rejects every non-finite JavaScript number", () => {
	const payload = (value) => ({
		format: CASE_FORMAT,
		cases: [
			{
				constraint: "/type",
				expected: { category: "type", path: "" },
				id: "non-finite",
				implementations: ["javascript"],
				operations: [{ op: "replace", path: "", value }],
				schema: "value.schema.json",
				seed: "valid.json",
			},
		],
	});
	for (const value of [
		Number.NaN,
		Number.POSITIVE_INFINITY,
		Number.NEGATIVE_INFINITY,
		JSON.parse("1e999"),
	]) {
		assert.throws(
			() => parseCaseFile(payload(value)),
			/non-finite number is not strict JSON/u,
		);
	}
});
