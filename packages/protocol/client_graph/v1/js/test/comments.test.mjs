import assert from "node:assert/strict";
import test from "node:test";

import { build } from "esbuild";

import {
	composeCoreRuntime,
	REGION_END,
	REGION_START,
} from "../build-support.mjs";

const result = await build({
	entryPoints: [new URL("../src/comments.ts", import.meta.url).pathname],
	bundle: true,
	format: "esm",
	platform: "node",
	target: "node22",
	write: false,
});
const source = result.outputFiles[0].text;
const comments = await import(
	`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
);

test("parses one canonical ownership comment", () => {
	const revision = "a".repeat(64);
	assert.deepEqual(
		comments.parseOwnershipComment(` citry:g1:${revision}:0:i:3:s `),
		{
			revision,
			graphId: "0",
			kind: "i",
			recordId: "3",
			side: "s",
			key: `citry:g1:${revision}:0:i:3`,
		},
	);
});

test("preserves decimal spelling for later canonicality checks", () => {
	const revision = "0".repeat(64);
	const parsed = comments.parseOwnershipComment(
		`citry:g1:${revision}:01:r:004:e`,
	);
	assert.equal(parsed.graphId, "01");
	assert.equal(parsed.recordId, "004");
	assert.equal(parsed.key, `citry:g1:${revision}:01:r:004`);
});

test("rejects text outside the client-graph comment format", () => {
	const revision = "b".repeat(64);
	for (const value of [
		`citry:g1:${revision}:0:x:1:s`,
		`citry:g1:${revision.toUpperCase()}:0:i:1:s`,
		`citry:g1:${revision}:0:i:1:x`,
		`citry:g1:${revision}:0:i:1`,
		`citry:p1:${revision}:root:0:i:1:s`,
		`before citry:g1:${revision}:0:i:1:s after`,
	]) {
		assert.equal(comments.parseOwnershipComment(value), null, value);
	}
});

test("initializes then refreshes exactly one generated region", () => {
	const source =
		'(function () {\n  "use strict";\n  var product = true;\n})();\n';
	const initialized = composeCoreRuntime(source, "var generated = 1;", {
		initialize: true,
	});
	assert.equal(initialized.split(REGION_START).length - 1, 1);
	assert.equal(initialized.split(REGION_END).length - 1, 1);
	assert.ok(
		initialized.indexOf(REGION_START) < initialized.indexOf("var product"),
	);

	const refreshed = composeCoreRuntime(initialized, "var generated = 2;");
	assert.ok(refreshed.includes("var generated = 2;"));
	assert.ok(!refreshed.includes("var generated = 1;"));
	assert.equal(refreshed.split(REGION_START).length - 1, 1);
	const surrounding = (value) => {
		const start = value.indexOf(REGION_START);
		const end = value.indexOf(REGION_END) + REGION_END.length;
		return value.slice(0, start) + value.slice(end);
	};
	assert.equal(surrounding(refreshed), surrounding(initialized));
	assert.throws(
		() => composeCoreRuntime(source, "var generated = 3;"),
		/no generated/,
	);
});

test("rejects duplicate, reversed, and moved generated markers", () => {
	const source =
		'(function () {\n  "use strict";\n  var product = true;\n})();\n';
	const initialized = composeCoreRuntime(source, "var generated = 1;", {
		initialize: true,
	});
	assert.throws(
		() => composeCoreRuntime(initialized.replace(REGION_END, REGION_START), ""),
		/exactly one generated/,
	);
	assert.throws(
		() => composeCoreRuntime(initialized.replace(REGION_START, REGION_END), ""),
		/exactly one generated/,
	);

	const reversed = initialized
		.replace(REGION_START, "temporary-marker")
		.replace(REGION_END, REGION_START)
		.replace("temporary-marker", REGION_END);
	assert.throws(() => composeCoreRuntime(reversed, ""), /markers are reversed/);

	const start = initialized.indexOf(`  ${REGION_START}`);
	const end = initialized.indexOf(REGION_END) + REGION_END.length;
	const region = initialized.slice(start, end);
	const moved =
		initialized.slice(0, start) +
		initialized
			.slice(end)
			.replace("  var product = true;", `  var product = true;\n${region}`);
	assert.throws(() => composeCoreRuntime(moved, ""), /must follow outer/);
});

test("initialization requires one outer strict directive", () => {
	const duplicateStrict =
		'(function () {\n  "use strict";\n  function nested() {\n  "use strict";\n  }\n})();\n';
	assert.throws(
		() =>
			composeCoreRuntime(duplicateStrict, "var generated = true;", {
				initialize: true,
			}),
		/one outer/,
	);
});
