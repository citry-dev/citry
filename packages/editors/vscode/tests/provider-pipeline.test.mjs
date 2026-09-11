import assert from "node:assert/strict";
import test from "node:test";

import {
	delegatedCompletionResolveCount,
	linearlyMappedProjectionPosition,
	mappedProjectionRange,
	ProviderTimeoutError,
	prepareProjectionRangeMapper,
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

const point = (line, character) => ({ line, character });
const range = (startLine, startCharacter, endLine, endCharacter) => ({
	start: point(startLine, startCharacter),
	end: point(endLine, endCharacter),
});

test("maps dedented provider members back to their authored line and column", () => {
	const source = 'js = """\n    // comment\n    data.ab\n"""';
	const virtual = "// preamble\n// comment\ndata.ab\n";
	const mappings = [
		{ sourceRange: range(1, 4, 2, 0), virtualRange: range(1, 0, 2, 0) },
		{ sourceRange: range(2, 4, 3, 0), virtualRange: range(2, 0, 3, 0) },
	];
	assert.deepEqual(mappedProjectionRange(source, virtual, mappings, range(2, 5, 2, 7)), range(2, 9, 2, 11));
	assert.deepEqual(mappedProjectionRange(source, virtual, mappings, range(2, 0, 2, 0)), range(2, 4, 2, 4));
	assert.deepEqual(mappedProjectionRange(source, virtual, mappings, range(1, 0, 2, 0)), range(1, 4, 2, 0));
	assert.equal(mappedProjectionRange(source, virtual, mappings, range(0, 0, 0, 2)), undefined);
});

test("maps UTF16 columns and CRLF source without counting code points", () => {
	const source = "prefix\r\n  😀 data.ab\r\n";
	const virtual = "😀 data.ab\r\n";
	const mappings = [{ sourceRange: range(1, 2, 2, 0), virtualRange: range(0, 0, 1, 0) }];
	assert.deepEqual(mappedProjectionRange(source, virtual, mappings, range(0, 8, 0, 10)), range(1, 10, 1, 12));
	assert.equal(mappedProjectionRange(source, virtual, mappings, range(0, 11, 0, 12)), undefined);
});

test("allows complete escaped characters but rejects their interior positions", () => {
	const source = "\\U0001f600x";
	const virtual = "😀x";
	const mappings = [
		{ sourceRange: range(0, 0, 0, 10), virtualRange: range(0, 0, 0, 2) },
		{ sourceRange: range(0, 10, 0, 11), virtualRange: range(0, 2, 0, 3) },
	];
	assert.deepEqual(mappedProjectionRange(source, virtual, mappings, range(0, 0, 0, 2)), range(0, 0, 0, 10));
	assert.deepEqual(mappedProjectionRange(source, virtual, mappings, range(0, 2, 0, 3)), range(0, 10, 0, 11));
	assert.equal(mappedProjectionRange(source, virtual, mappings, range(0, 1, 0, 1)), undefined);
	assert.equal(mappedProjectionRange(source, virtual, mappings, range(0, 0, 0, 1)), undefined);
});

test("rejects generated gaps, malformed ranges, and ambiguous absent mappings", () => {
	const mappings = [
		{ sourceRange: range(0, 0, 0, 1), virtualRange: range(0, 0, 0, 1) },
		{ sourceRange: range(0, 1, 0, 2), virtualRange: range(0, 2, 0, 3) },
	];
	assert.equal(mappedProjectionRange("ab", "a_b", mappings, range(0, 0, 0, 3)), undefined);
	assert.equal(mappedProjectionRange("ab", "a_b", mappings, range(0, 0, 0, 4)), undefined);
	assert.equal(mappedProjectionRange("ab", "a_b", mappings, range(0, 2, 0, 1)), undefined);
	assert.equal(mappedProjectionRange("ab", "a_b", mappings.toReversed(), range(0, 0, 0, 1)), undefined);
	assert.equal(mappedProjectionRange("ab", "a_b", [], range(0, 0, 0, 0)), undefined);
	assert.equal(
		mappedProjectionRange(
			"ab",
			"a_b",
			[{ sourceRange: range(1, 0, 1, 1), virtualRange: range(0, 0, 0, 1) }],
			range(0, 0, 0, 1),
		),
		undefined,
	);
});

test("maps only the declared empty-body insertion anchor", () => {
	const mappings = [{ sourceRange: range(0, 8, 0, 8), virtualRange: range(1, 0, 1, 0) }];
	assert.deepEqual(
		mappedProjectionRange('js = """"""', "// preamble\n", mappings, range(1, 0, 1, 0)),
		range(0, 8, 0, 8),
	);
	assert.equal(mappedProjectionRange('js = """"""', "// preamble\n", mappings, range(0, 0, 0, 0)), undefined);
	assert.equal(mappedProjectionRange('js = """"""', "// preamble\n", mappings, range(0, 0, 1, 0)), undefined);
	assert.equal(mappedProjectionRange('js = """"""', "// preamble\n", [], range(1, 0, 1, 0)), undefined);
	assert.equal(
		mappedProjectionRange(
			"abc",
			"abc",
			[{ sourceRange: range(0, 0, 0, 0), virtualRange: range(0, 0, 0, 1) }],
			range(0, 0, 0, 0),
		),
		undefined,
	);
});

test("reuses a prepared source mapper across a provider response", () => {
	const mapper = prepareProjectionRangeMapper("  a\n  b", "a\nb", [
		{ sourceRange: range(0, 2, 1, 0), virtualRange: range(0, 0, 1, 0) },
		{ sourceRange: range(1, 2, 1, 3), virtualRange: range(1, 0, 1, 1) },
	]);
	assert.ok(mapper);
	assert.deepEqual(mapper(range(0, 0, 0, 1)), range(0, 2, 0, 3));
	assert.deepEqual(mapper(range(1, 0, 1, 1)), range(1, 2, 1, 3));
});
