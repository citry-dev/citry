import assert from "node:assert/strict";
import test from "node:test";

import {
	delegatedCompletionResolveCount,
	linearlyMappedProjectionPosition,
	ProviderTimeoutError,
	withTimeout,
} from "../out/tests/providerPipeline.mjs";

test("delegated completion does not eagerly resolve provider items", () => {
	assert.equal(delegatedCompletionResolveCount, 0);
});

test("reuses a linear projection only inside its proven source range", () => {
	const source = 'const prefix = 1;\n<form action="save">';
	const virtualStart = { line: 1, character: 0 };
	const virtualEnd = { line: 1, character: 20 };

	assert.deepEqual(linearlyMappedProjectionPosition(source, 105, 100, 120, virtualStart, virtualEnd), {
		line: 1,
		character: 5,
	});
	assert.equal(linearlyMappedProjectionPosition(source, 99, 100, 120, virtualStart, virtualEnd), undefined);
	assert.equal(linearlyMappedProjectionPosition(source, 121, 100, 120, virtualStart, virtualEnd), undefined);
});

test("provider deadlines return successful work and reject stalled work", async () => {
	assert.equal(await withTimeout(Promise.resolve("ready"), 20, "provider"), "ready");
	let cancelled = false;
	await assert.rejects(
		withTimeout(new Promise(() => {}), 5, "provider", () => (cancelled = true)),
		(error) => {
			assert.ok(error instanceof ProviderTimeoutError);
			assert.equal(error.stage, "provider");
			return true;
		},
	);
	assert.equal(cancelled, true);
});
