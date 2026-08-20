import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
	applyProviderTextEdits,
	EmbeddedFormattingCancelledError,
	EmbeddedFormattingStaleError,
	embeddedFormattingDocumentIdentity,
	embeddedFormattingOptions,
	formatEmbeddedDocuments,
} from "../out/tests/embeddedFormatting.mjs";

const document = { uri: "file:///workspace/card.py", version: 7 };
const corpusRoot = new URL("../../../../crates/citry_template_formatter/tests/fixtures/v1/", import.meta.url);

test("uses valid language-scoped editor indentation and safe fallbacks", () => {
	assert.deepEqual(embeddedFormattingOptions(4, false), { tabSize: 4, insertSpaces: false });
	assert.deepEqual(embeddedFormattingOptions("auto", "yes"), { tabSize: 2, insertSpaces: true });
	assert.deepEqual(embeddedFormattingOptions(0, false), { tabSize: 2, insertSpaces: false });
});

test("content-addresses immutable virtual documents across passes and requests", () => {
	const first = embeddedFormattingDocumentIdentity(params(), region(), "const  answer=41+1;");
	const second = embeddedFormattingDocumentIdentity(params(), region(), "const answer = 41 + 1;\n");
	const repeated = embeddedFormattingDocumentIdentity(params(), region(), "const  answer=41+1;");
	const otherSource = embeddedFormattingDocumentIdentity(params(), region(), "const other = 42;\n");

	assert.deepEqual(repeated, first);
	assert.notDeepEqual(second, first);
	assert.notDeepEqual(otherSource, first);
	assert.match(first.path, /^\/python-component-asset-0-0\/[a-f0-9]{64}\/document\.js$/);
	assert.equal(new URLSearchParams(first.query).get("source"), document.uri);
});

function region(overrides = {}) {
	return {
		id: "python-component-asset-0-0",
		language: "javascript",
		kind: "component-js",
		source: "const  answer=41+1;",
		virtualSource: "const  answer=41+1;",
		protectedRanges: [],
		delimiterConstraints: { forbiddenSubstrings: [], caseInsensitive: true },
		...overrides,
	};
}

function params(regions = [region()]) {
	return { version: 1, textDocument: document, planId: "sha256:plan", regions };
}

function wholeDocumentEdit(source, newText) {
	const lines = source.split("\n");
	return {
		range: {
			start: { line: 0, character: 0 },
			end: { line: lines.length - 1, character: lines.at(-1).length },
		},
		newText,
	};
}

test("returns an idempotent two-pass result without inventing provider identity", async () => {
	const calls = [];
	const response = await formatEmbeddedDocuments(params(), {
		currentDocumentVersion: () => 7,
		executeFormatter: async ({ source, pass }) => {
			calls.push([source, pass]);
			return pass === 1 ? [wholeDocumentEdit(source, "const answer = 41 + 1;\n")] : [];
		},
	});

	assert.deepEqual(calls, [
		["const  answer=41+1;", 1],
		["const answer = 41 + 1;\n", 2],
	]);
	assert.deepEqual(response, {
		version: 1,
		textDocument: document,
		planId: "sha256:plan",
		providerSelection: "vscode-first-result",
		results: [
			{
				planId: "sha256:plan",
				regionId: "python-component-asset-0-0",
				status: "formatted",
				text: "const answer = 41 + 1;\n",
				provider: null,
			},
		],
	});
});

test("accepts VS Code's zero-edit second-pass response", async () => {
	const response = await formatEmbeddedDocuments(params(), {
		currentDocumentVersion: () => 7,
		executeFormatter: async ({ source, pass }) =>
			pass === 1 ? [wholeDocumentEdit(source, "const answer = 41 + 1;\n")] : undefined,
	});

	assert.deepEqual(response.results, [
		{
			planId: "sha256:plan",
			regionId: "python-component-asset-0-0",
			status: "formatted",
			text: "const answer = 41 + 1;\n",
			provider: null,
		},
	]);
});

test("accepts a fixed point after provider activation changes the second result", async () => {
	const calls = [];
	const response = await formatEmbeddedDocuments(params(), {
		currentDocumentVersion: () => 7,
		executeFormatter: async ({ source, pass }) => {
			calls.push([source, pass]);
			if (pass === 1) {
				return [wholeDocumentEdit(source, "function answer() {\n  return 42;\n}\n")];
			}
			if (pass === 2) {
				return [wholeDocumentEdit(source, "function answer() {\n    return 42;\n}\n")];
			}
			return undefined;
		},
	});

	assert.equal(calls.length, 3);
	assert.equal(response.results[0].status, "formatted");
	assert.equal(response.results[0].text, "function answer() {\n    return 42;\n}\n");
});

test("consumes every applicable shared embedded formatter case", async () => {
	const index = JSON.parse(readFileSync(new URL("index.json", corpusRoot), "utf8"));
	const exercised = new Set();
	const serverValidated = new Set();
	for (const fixture of index.embedded_cases) {
		if (fixture.category === "result-validation" && fixture.id !== "embedded-formatting.results.delimiter-conflict") {
			serverValidated.add(fixture.id);
			continue;
		}
		const regions = fixture.requests.map((request, position) => ({
			id: `fixture-${position}`,
			language: request.language,
			kind: request.kind,
			source: request.source,
			virtualSource: request.virtual_source,
			protectedRanges: [],
			delimiterConstraints: {
				forbiddenSubstrings: request.kind === "script-body" ? ["</script", "{{", "{#"] : ["</style", "{{", "{#"],
				caseInsensitive: true,
			},
		}));
		const response = await formatEmbeddedDocuments(params(regions), {
			currentDocumentVersion: () => 7,
			executeFormatter: async ({ region: fixtureRegion, source, pass }) => {
				const position = Number.parseInt(fixtureRegion.id.slice("fixture-".length), 10);
				const result = fixture.results.find((candidate) => candidate.region === position);
				if (result === undefined || result.status === "unavailable") {
					return undefined;
				}
				if (result.status === "error") {
					throw new Error(result.message);
				}
				if (result.status === "formatted") {
					return pass === 1 ? [wholeDocumentEdit(source, result.text)] : [];
				}
				throw new Error(`unsupported editor corpus result ${result.status}`);
			},
		});
		assert.equal(response.results.length, fixture.results.length, fixture.id);
		for (const [position, expected] of fixture.results.entries()) {
			const actual = response.results[position];
			if (expected.status === "formatted" && fixture.expected_error === undefined) {
				assert.equal(actual.status, "formatted", fixture.id);
				assert.equal(actual.text, expected.text, fixture.id);
			} else if (expected.status === "unavailable") {
				assert.equal(actual.status, "unavailable", fixture.id);
			} else {
				assert.equal(actual.status, "error", fixture.id);
				assert.match(actual.message, new RegExp(fixture.expected_error.contains), fixture.id);
			}
		}
		exercised.add(fixture.id);
	}

	assert.deepEqual(
		new Set([...exercised, ...serverValidated]),
		new Set(index.embedded_cases.map((fixture) => fixture.id)),
	);
	assert.deepEqual(
		serverValidated,
		new Set([
			"embedded-formatting.results.stale",
			"embedded-formatting.results.duplicate",
			"embedded-formatting.results.missing",
		]),
	);
});

test("distinguishes no applicable provider from an unchanged provider result", async () => {
	const unavailable = await formatEmbeddedDocuments(params(), {
		currentDocumentVersion: () => 7,
		executeFormatter: async () => undefined,
	});
	const unchanged = await formatEmbeddedDocuments(params(), {
		currentDocumentVersion: () => 7,
		executeFormatter: async () => [],
	});

	assert.equal(unavailable.results[0].status, "unavailable");
	assert.match(unavailable.results[0].message, /no javascript formatter/);
	assert.deepEqual(unchanged.results, [
		{ planId: "sha256:plan", regionId: "python-component-asset-0-0", status: "unchanged" },
	]);
});

test("times out and cancels a provider that never resolves", async () => {
	let signal;
	const response = await formatEmbeddedDocuments(params(), {
		currentDocumentVersion: () => 7,
		timeoutMilliseconds: 5,
		executeFormatter: ({ signal: invocationSignal }) => {
			signal = invocationSignal;
			return new Promise(() => {});
		},
	});

	assert.equal(signal.aborted, true);
	assert.equal(response.results[0].status, "error");
	assert.match(response.results[0].message, /timed out/);
});

test("request cancellation aborts the current invocation and starts no later pass or region", async () => {
	const cancellation = new AbortController();
	const calls = [];
	let signal;
	const formatting = formatEmbeddedDocuments(params([region(), region({ id: "second" })]), {
		currentDocumentVersion: () => 7,
		cancellationSignal: cancellation.signal,
		executeFormatter: ({ region: current, pass, signal: invocationSignal }) => {
			calls.push([current.id, pass]);
			signal = invocationSignal;
			return new Promise(() => {});
		},
	});

	cancellation.abort();
	await assert.rejects(formatting, EmbeddedFormattingCancelledError);
	assert.equal(signal.aborted, true);
	assert.deepEqual(calls, [["python-component-asset-0-0", 1]]);
});

test("rejects provider output that keeps changing through the third pass", async () => {
	const response = await formatEmbeddedDocuments(params(), {
		currentDocumentVersion: () => 7,
		executeFormatter: async ({ source, pass }) => [wholeDocumentEdit(source, `let answer = ${41 + pass};`)],
	});

	assert.equal(response.results[0].status, "error");
	assert.match(response.results[0].message, /idempotent result after three passes/);
	assert.equal(response.results[0].text, undefined);
});

test("refuses delimiter conflicts before sending provider text to the server", async () => {
	const script = region({
		kind: "script-body",
		delimiterConstraints: { forbiddenSubstrings: ["</script"], caseInsensitive: true },
	});
	const response = await formatEmbeddedDocuments(params([script]), {
		currentDocumentVersion: () => 7,
		executeFormatter: async ({ source }) => [wholeDocumentEdit(source, "const value = '</ScRiPt>';\n")],
	});

	assert.equal(response.results[0].status, "error");
	assert.match(response.results[0].message, /forbidden delimiter/);
});

test("applies exact UTF-16 ranges and preserves CRLF outside edits", () => {
	const source = "😀 value\r\nnext";
	const result = applyProviderTextEdits(source, [
		{
			range: { start: { line: 0, character: 3 }, end: { line: 0, character: 8 } },
			newText: "answer",
		},
	]);

	assert.equal(result, "😀 answer\r\nnext");
	assert.throws(
		() =>
			applyProviderTextEdits(source, [
				{
					range: { start: { line: 0, character: 1 }, end: { line: 0, character: 2 } },
					newText: "x",
				},
			]),
		/surrogate pair/,
	);
});

test("rejects overlapping and protected provider edits", () => {
	const source = "const value = 1;";
	assert.throws(
		() =>
			applyProviderTextEdits(source, [
				{
					range: { start: { line: 0, character: 0 }, end: { line: 0, character: 5 } },
					newText: "let",
				},
				{
					range: { start: { line: 0, character: 4 }, end: { line: 0, character: 9 } },
					newText: "answer",
				},
			]),
		/overlap/,
	);
	assert.throws(
		() =>
			applyProviderTextEdits(
				source,
				[
					{
						range: { start: { line: 0, character: 6 }, end: { line: 0, character: 11 } },
						newText: "answer",
					},
				],
				[{ start: { line: 0, character: 8 }, end: { line: 0, character: 10 } }],
			),
		/protected range/,
	);
});

test("remaps protected ranges before validating the idempotence pass", async () => {
	const protectedRegion = region({
		source: "aa KEEP",
		virtualSource: "aa KEEP",
		protectedRanges: [{ start: { line: 0, character: 3 }, end: { line: 0, character: 7 } }],
	});
	const response = await formatEmbeddedDocuments(params([protectedRegion]), {
		currentDocumentVersion: () => 7,
		executeFormatter: async ({ pass }) =>
			pass === 1
				? [
						{
							range: { start: { line: 0, character: 0 }, end: { line: 0, character: 2 } },
							newText: "prefix\n",
						},
					]
				: [
						{
							range: { start: { line: 1, character: 1 }, end: { line: 1, character: 5 } },
							newText: "DROP",
						},
					],
	});

	assert.equal(response.results[0].status, "error");
	assert.match(response.results[0].message, /protected range/);
});

test("aborts the complete round trip when the source document becomes stale", async () => {
	let version = 7;
	await assert.rejects(
		formatEmbeddedDocuments(params(), {
			currentDocumentVersion: () => version,
			executeFormatter: async ({ source }) => {
				version = 8;
				return [wholeDocumentEdit(source, "const answer = 42;")];
			},
		}),
		EmbeddedFormattingStaleError,
	);
});

test("rejects duplicate region IDs before invoking a provider", async () => {
	let calls = 0;
	await assert.rejects(
		formatEmbeddedDocuments(params([region(), region()]), {
			currentDocumentVersion: () => 7,
			executeFormatter: async () => {
				calls += 1;
				return [];
			},
		}),
		/duplicate region/,
	);
	assert.equal(calls, 0);
});

test("rejects malformed region kinds and provider UTF-16", async () => {
	await assert.rejects(
		formatEmbeddedDocuments(params([region({ language: "css", kind: "script-body" })]), {
			currentDocumentVersion: () => 7,
			executeFormatter: async () => [],
		}),
		/malformed or duplicate region/,
	);
	const response = await formatEmbeddedDocuments(params(), {
		currentDocumentVersion: () => 7,
		executeFormatter: async ({ source }) => [wholeDocumentEdit(source, "bad\ud800text")],
	});
	assert.equal(response.results[0].status, "error");
	assert.match(response.results[0].message, /unpaired UTF-16 surrogate/);
});
