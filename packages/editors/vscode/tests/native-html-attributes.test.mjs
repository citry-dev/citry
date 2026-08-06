import assert from "node:assert/strict";
import test from "node:test";

import {
	nativeDynamicAttributeHoverProjection,
	projectNativeHtmlAttributes,
} from "../out/tests/nativeHtmlAttributes.mjs";

test("projects a dynamic native attribute without moving source coordinates", () => {
	const source = '<form c-class="classes"></form>';
	const projected = projectNativeHtmlAttributes(source);
	const attributeStart = source.indexOf("c-class");

	assert.equal(projected.source, '<form   class="classes"></form>');
	assert.equal(projected.source.length, source.length);
	assert.deepEqual(projected.attributes, [
		{
			authoredName: "c-class",
			nativeName: "class",
			sourceStart: attributeStart,
			sourceEnd: attributeStart + "c-class".length,
			projectedStart: attributeStart + 2,
			projectedEnd: attributeStart + "c-class".length,
		},
	]);
});

test("maps every authored name position into the projected suffix interior", () => {
	const source = '<form c-class="classes"></form>';
	const start = source.indexOf("c-class");
	const expectedProviderOffsets = [start + 2, start + 2, start + 2, start + 3, start + 4];

	for (const [relativeOffset, expectedProviderOffset] of expectedProviderOffsets.entries()) {
		const projection = nativeDynamicAttributeHoverProjection(source, start + relativeOffset);
		assert.ok(projection);
		assert.equal(projection.providerOffset, expectedProviderOffset);
		assert.equal(projection.sourceStart, start);
		assert.equal(projection.sourceEnd, start + "c-class".length);
	}

	const atEnd = nativeDynamicAttributeHoverProjection(source, start + "c-class".length);
	assert.ok(atEnd);
	assert.equal(atEnd.providerOffset, start + "c-class".length - 1);
});

test("uses ASCII-insensitive HTML identity and removes exactly one Citry prefix", () => {
	const source = '<form c-CLASS="classes" c-c-foo="value" C-class="literal"></form>';
	const projected = projectNativeHtmlAttributes(source);

	assert.equal(projected.source, '<form   class="classes"   c-foo="value" C-class="literal"></form>');
	assert.deepEqual(
		projected.attributes.map(({ authoredName, nativeName }) => [authoredName, nativeName]),
		[
			["c-CLASS", "class"],
			["c-c-foo", "c-foo"],
		],
	);
});

test("uses exact Citry prefix and directive casing before HTML suffix normalization", () => {
	const source = '<label c-for="item in items" c-FOR="control" C-class="literal"></label>';
	const projected = projectNativeHtmlAttributes(source);

	assert.equal(projected.source, '<label c-for="item in items"   for="control" C-class="literal"></label>');
	assert.deepEqual(
		projected.attributes.map(({ authoredName, nativeName }) => [authoredName, nativeName]),
		[["c-FOR", "for"]],
	);
});

test("excludes Citry directives and every Citry tag boundary", () => {
	const source = [
		'<div c-if="ready" c-elif="other" c-else c-for="item in items" c-empty c-bind="attrs"></div>',
		'<c-Card c-class="classes"></c-Card>',
		'<c-element is="form" c-action="submit"></c-element>',
	].join("\n");

	const projected = projectNativeHtmlAttributes(source);

	assert.equal(projected.source, source);
	assert.deepEqual(projected.attributes, []);
});

test("scans only direct start-tag attribute names", () => {
	const source = [
		'{# <form c-class="comment"></form> #}',
		'{{ "<form c-class=expression></form>" }}',
		'<!-- <form c-class="html-comment"></form> -->',
		'<!DOCTYPE html PUBLIC "<form c-class=doctype></form>">',
		'<?example "<form c-class=processing></form>"?>',
		"<script>const example = '<form c-class=\"script\"></form>';</script>",
		"<style>.x::before { content: '<form c-class=\"style\">'; }</style>",
		'<textarea><form c-class="textarea"></form></textarea>',
		'<title><form c-class="title"></form></title>',
		'<c-raw><form c-class="raw"></form></c-raw>',
		'<div title="<form c-class=nested></form>"></div>',
		'</div title="<form c-class=nested-end></form>">',
		'<form c-class="direct"></form>',
	].join("\n");
	const directStart = source.lastIndexOf("c-class");

	const projected = projectNativeHtmlAttributes(source);

	assert.equal(projected.attributes.length, 1);
	assert.equal(projected.attributes[0].sourceStart, directStart);
	assert.equal(projected.source.slice(directStart, directStart + "c-class".length), "  class");
});

test("preserves CRLF, astral characters, UTF-16 length, and duplicate native attributes", () => {
	const source = '😀<div class="static"\r\n  c-class="dynamic" c-aria-BUSY="busy"></div>';
	const projected = projectNativeHtmlAttributes(source);

	assert.equal(projected.source.length, source.length);
	assert.equal(projected.source.split("\r\n").length, source.split("\r\n").length);
	assert.equal(projected.source, '😀<div class="static"\r\n    class="dynamic"   aria-busy="busy"></div>');
	assert.deepEqual(
		projected.attributes.map(({ nativeName }) => nativeName),
		["class", "aria-busy"],
	);
});

test("declines comments, values, whitespace, and uncertain unterminated regions", () => {
	const source = [
		'<form title="c-class" c-class="direct"></form>',
		'<div foo=x{# c-class #} c-title="ok"></div>',
		'<div\fc-class="not-an-attribute"></div>',
		"{# c-class #}",
		"{{ c-class",
		'<form c-href="after-uncertain"></form>',
	].join("\n");
	const valueOffset = source.indexOf("c-class");
	const directOffset = source.indexOf("c-class", valueOffset + 1);

	assert.equal(nativeDynamicAttributeHoverProjection(source, valueOffset + 2), undefined);
	assert.ok(nativeDynamicAttributeHoverProjection(source, directOffset + 2));
	assert.deepEqual(
		projectNativeHtmlAttributes(source).attributes.map(({ authoredName }) => authoredName),
		["c-class", "c-title"],
	);
});
