import assert from "node:assert/strict";
import test from "node:test";

import {
	advanceExpressionCompletionRetrigger,
	advanceTagCompletionRetrigger,
} from "../out/tests/completionRetrigger.mjs";

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

test("triggers the first root character without requiring expression whitespace", () => {
	for (const [source, languageId, insertedOffset] of [
		['<form c-autocomplete="a">', "citry-html", '<form c-autocomplete="'.length],
		['<form c-autocomplete="autocomplete+a">', "citry-html", '<form c-autocomplete="autocomplete+'.length],
		['<form c-autocomplete="autocomplete +a">', "citry-html", '<form c-autocomplete="autocomplete +'.length],
		["{{a }}", "citry-html", "{{".length],
		["class Card:\n    template = '''{{a }}'''\n", "python", "class Card:\n    template = '''{{".length],
		["class Card:\n    template = r'''{{a }}'''\n", "python", "class Card:\n    template = r'''{{".length],
		['class Card:\n    template = "{{a }}"\n', "python", 'class Card:\n    template = "{{'.length],
		["<div c-title=a>", "citry-html", "<div c-title=".length],
		["{{\ta }}", "citry-html", "{{\t".length],
		["{{\na }}", "citry-html", "{{\n".length],
		['<button x-text="a">', "citry-html", '<button x-text="'.length],
		['<input x-model.lazy="a">', "citry-html", '<input x-model.lazy="'.length],
		['<section x-intersect.once="a">', "citry-html", '<section x-intersect.once="'.length],
		['<button @click="count+a">', "citry-html", '<button @click="count+'.length],
		['<button :class="a">', "citry-html", '<button :class="'.length],
		['<template $c-props="a">', "citry-html", '<template $c-props="'.length],
		['<c-fill name="h">', "citry-html", '<c-fill name="'.length],
		['<c-fill name="item" data="{r">', "citry-html", '<c-fill name="item" data="{'.length],
	]) {
		const decision = advanceExpressionCompletionRetrigger(source, languageId, change(insertedOffset, 0, "a"));
		assert.deepEqual(decision, { triggerOffset: insertedOffset + 1 }, source);
	}
});

test("triggers Unicode roots and roots inside f-string replacements", () => {
	for (const [source, insertedOffset, insertedText] of [
		["{{é }}", "{{".length, "é"],
		["{{ f'{a}' }}", "{{ f'{".length, "a"],
		["<div c-title=\"f'{a}'\">", "<div c-title=\"f'{".length, "a"],
	]) {
		assert.deepEqual(
			advanceExpressionCompletionRetrigger(source, "citry-html", change(insertedOffset, 0, insertedText)),
			{ triggerOffset: insertedOffset + insertedText.length },
			source,
		);
	}
});

test("retriggers expression completion after deletion and history correction", () => {
	const deleted = advanceExpressionCompletionRetrigger("{{ }}", "citry-html", change(2, 1, ""));
	assert.deepEqual(deleted, { pendingOffset: 2 });
	assert.deepEqual(
		advanceExpressionCompletionRetrigger("{{b }}", "citry-html", change(2, 0, "b"), deleted.pendingOffset),
		{ triggerOffset: 3 },
	);
	assert.deepEqual(advanceExpressionCompletionRetrigger("{{a }}", "citry-html", change(2, 0, "a", true)), {
		triggerOffset: 3,
	});
});

test("limits expression retriggers to Citry Python hosts and one authored character", () => {
	assert.deepEqual(advanceExpressionCompletionRetrigger("value = a", "python", change("value = ".length, 0, "a")), {});
	assert.deepEqual(
		advanceExpressionCompletionRetrigger('<div class="a">', "citry-html", change('<div class="'.length, 0, "a")),
		{},
	);
	assert.deepEqual(
		advanceExpressionCompletionRetrigger("<div>{{a }}</div>", "html", change("<div>{{".length, 0, "a")),
		{},
	);
	assert.deepEqual(advanceExpressionCompletionRetrigger("{# a", "citry-html", change("{# ".length, 0, "a")), {});
	assert.deepEqual(advanceExpressionCompletionRetrigger("{{ab }}", "citry-html", change("{{a".length, 0, "b")), {});
	assert.deepEqual(
		advanceExpressionCompletionRetrigger("{{alpha }}", "citry-html", change("{{".length, 0, "alpha")),
		{},
	);
	for (const [source, offset] of [
		["{{ 'a' }}", "{{ '".length],
		["{{ value # a }}", "{{ value # ".length],
		["{{ {'a': value} }}", "{{ {'".length],
		["<div c-title=\"'a'\">", "<div c-title=\"'".length],
		["<script>{{a }}</script>", "<script>{{".length],
		["<style>{{a }}</style>", "<style>{{".length],
		["<c-raw>{{a }}</c-raw>", "<c-raw>{{".length],
		["{{𐐀a }}", "{{𐐀".length],
	]) {
		assert.deepEqual(advanceExpressionCompletionRetrigger(source, "citry-html", change(offset, 0, "a")), {}, source);
	}
});

test("scopes Python activation to the current template literal", () => {
	for (const source of ["# {{ example\nordinary=a", '# <div c-title="example\nordinary=a']) {
		assert.deepEqual(
			advanceExpressionCompletionRetrigger(source, "python", change(source.length - 1, 0, "a")),
			{},
			source,
		);
	}

	for (const prefix of ['notes = """<script>"""\n', "# <!--\n", "# {#\n"]) {
		const source = `${prefix}class Card:\n    template = """{{a }}"""\n`;
		const offset = source.indexOf("{{a") + 2;
		assert.deepEqual(
			advanceExpressionCompletionRetrigger(source, "python", change(offset, 0, "a")),
			{ triggerOffset: offset + 1 },
			source,
		);
	}
});
