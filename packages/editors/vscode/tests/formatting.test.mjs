import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
	applyVersionedEdit,
	documentVersionIsCurrent,
	formattingFailureDelivery,
	sourceFormattingAction,
	workspaceOwnsDocument,
} from "../out/tests/formatting.mjs";

test("rejects a formatter result after the document generation changes", () => {
	assert.equal(documentVersionIsCurrent(7, 7), true);
	assert.equal(documentVersionIsCurrent(7, 8), false);
});

test("does not apply an edit when the generation changes during asynchronous conversion", async () => {
	let currentVersion = 7;
	let applyCalls = 0;
	const outcome = await applyVersionedEdit({
		requestedVersion: 7,
		currentVersion: () => currentVersion,
		protocolEdit: { edits: [] },
		validate: () => true,
		convert: async () => {
			currentVersion = 8;
			return { converted: true };
		},
		apply: async () => {
			applyCalls += 1;
			return true;
		},
	});

	assert.equal(outcome, "stale");
	assert.equal(applyCalls, 0);
});

test("applies every shared formatter corpus result without client-side rewriting", async () => {
	const corpusUrl = new URL("../../../../crates/citry_template_formatter/tests/fixtures/v1/", import.meta.url);
	const index = JSON.parse(await readFile(new URL("index.json", corpusUrl), "utf8"));
	const fixtures = [...index.cases, ...index.python_hosts];

	for (const fixture of fixtures) {
		if (fixture.expected_error !== undefined) continue;
		const expected = fixture.expected_text ?? (await readFile(new URL(fixture.expected, corpusUrl), "utf8"));
		let applied;
		const outcome = await applyVersionedEdit({
			requestedVersion: 7,
			currentVersion: () => 7,
			protocolEdit: { newText: expected },
			validate: () => true,
			convert: async (edit) => edit.newText,
			apply: async (edit) => {
				applied = edit;
				return true;
			},
		});

		assert.equal(outcome, "applied", fixture.id);
		assert.equal(applied, expected, fixture.id);
	}
});

test("coalesces repeated quiet failures without hiding explicit command failures", () => {
	assert.deepEqual(formattingFailureDelivery("refused", true, undefined), {
		appendToOutput: true,
		showWarning: false,
		nextQuietFailure: "refused",
	});
	assert.deepEqual(formattingFailureDelivery("refused", true, "refused"), {
		appendToOutput: false,
		showWarning: false,
		nextQuietFailure: "refused",
	});
	assert.deepEqual(formattingFailureDelivery("refused", false, "refused"), {
		appendToOutput: true,
		showWarning: true,
		nextQuietFailure: "refused",
	});
});

test("builds the quiet whole-file source action used by format-on-save", () => {
	assert.deepEqual(sourceFormattingAction("file:///workspace/card.py"), {
		title: "Format Citry document",
		command: "citry.formatDocument",
		arguments: ["file:///workspace/card.py", true],
		isPreferred: true,
	});
});

test("routes a nested workspace document only through its selected workspace", () => {
	const outer = "file:///workspace";
	const inner = "file:///workspace/packages/ui";

	assert.equal(workspaceOwnsDocument(outer, inner), false);
	assert.equal(workspaceOwnsDocument(inner, inner), true);
	assert.equal(workspaceOwnsDocument(outer, outer), true);
	assert.equal(workspaceOwnsDocument(outer, undefined), false);
});
