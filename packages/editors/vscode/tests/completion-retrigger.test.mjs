import assert from "node:assert/strict";
import test from "node:test";

import { advanceTagCompletionRetrigger } from "../out/tests/completionRetrigger.mjs";

const change = (startOffset, removedLength, insertedText, history = false) => ({
	startOffset,
	removedLength,
	insertedText,
	history,
});

test("retriggers once after repeated backspaces leave a corrected tag prefix", () => {
	let decision = advanceTagCompletionRetrigger("<c-oop", change(6, 1, ""), undefined);
	assert.deepEqual(decision, { pendingOffset: 6 });

	decision = advanceTagCompletionRetrigger("<c-", change(3, 3, ""), decision.pendingOffset);
	assert.deepEqual(decision, { pendingOffset: 3 });

	decision = advanceTagCompletionRetrigger("<c-i", change(3, 0, "i"), decision.pendingOffset);
	assert.deepEqual(decision, { triggerOffset: 4 });
});

test("supports closing tags and every word-character component-name continuation", () => {
	for (const [before, inserted, after] of [
		["</c-", "C", "</c-C"],
		["<c-card", "2", "<c-card2"],
		["<c-my", "_", "<c-my_"],
	]) {
		const pendingOffset = before.length;
		const decision = advanceTagCompletionRetrigger(after, change(pendingOffset, 0, inserted), pendingOffset);
		assert.deepEqual(decision, { triggerOffset: after.length }, after);
	}
});

test("does not retrigger ordinary typing, moved cursors, replacements, or paste", () => {
	assert.deepEqual(advanceTagCompletionRetrigger("<c-i", change(3, 0, "i"), undefined), {});
	assert.deepEqual(advanceTagCompletionRetrigger("<c-i", change(3, 0, "i"), 2), {});
	assert.deepEqual(advanceTagCompletionRetrigger("<c-i", change(3, 1, "i"), 3), {});
	assert.deepEqual(advanceTagCompletionRetrigger("<c-if", change(3, 0, "if"), 3), {});
	assert.deepEqual(advanceTagCompletionRetrigger("value", change(5, 1, ""), undefined), {});
	assert.deepEqual(advanceTagCompletionRetrigger("<c-ui.", change(5, 0, "."), 5), {});
	assert.deepEqual(advanceTagCompletionRetrigger("<c-my-", change(5, 0, "-"), 5), {});
});

test("history operations retrigger only when they land in a partial Citry tag", () => {
	assert.deepEqual(advanceTagCompletionRetrigger("<c-", change(3, 4, "", true), undefined), {
		triggerOffset: 3,
	});
	assert.deepEqual(advanceTagCompletionRetrigger("<c-card", change(3, 0, "card", true), undefined), {
		triggerOffset: 7,
	});
	assert.deepEqual(advanceTagCompletionRetrigger("ordinary", change(0, 0, "ordinary", true), undefined), {});
});
