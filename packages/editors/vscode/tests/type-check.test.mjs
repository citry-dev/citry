import assert from "node:assert/strict";
import test from "node:test";

import { typeCheckDiagnostics, validTypeCheckParams } from "../out/tests/typeCheck.mjs";

test("TypeScript server diagnostics become zero-based wire diagnostics", () => {
	const response = {
		type: "response",
		success: true,
		body: [
			{
				start: { line: 10, offset: 7 },
				end: { line: 10, offset: 27 },
				text: "Type 'boolean' is not assignable to type '() => void'.",
				code: 2322,
				category: "error",
			},
			// A diagnostic without a numeric code or with an unknown category is skipped.
			{ start: { line: 1, offset: 1 }, end: { line: 1, offset: 2 }, text: "x", category: "error" },
			{ start: { line: 1, offset: 1 }, end: { line: 1, offset: 2 }, text: "x", code: 1, category: "fatal" },
		],
	};

	assert.deepEqual(typeCheckDiagnostics(response), [
		{
			range: { start: { line: 9, character: 6 }, end: { line: 9, character: 26 } },
			code: 2322,
			message: "Type 'boolean' is not assignable to type '() => void'.",
			category: "error",
		},
	]);
});

test("a cancelled or missing TypeScript answer gives no diagnostics", () => {
	assert.deepEqual(typeCheckDiagnostics(undefined), []);
	assert.deepEqual(typeCheckDiagnostics({ type: "response", success: false }), []);
});

test("only the version 1 request shape is accepted", () => {
	const valid = { version: 1, textDocument: { uri: "file:///a.py", version: 3 }, files: [{ id: "js:0", source: "" }] };
	assert.equal(validTypeCheckParams(valid), true);
	assert.equal(validTypeCheckParams({ ...valid, version: 2 }), false);
	assert.equal(validTypeCheckParams({ ...valid, files: [{ id: 1, source: "" }] }), false);
	assert.equal(validTypeCheckParams(null), false);
});
