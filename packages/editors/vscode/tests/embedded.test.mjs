import assert from "node:assert/strict";
import test from "node:test";

import { embeddedLanguageAt, pythonEmbeddedRegions, virtualDocumentSource } from "../out/tests/embedded.mjs";

test("discovers exact typed template, JavaScript, and CSS triple-string assignments", () => {
	const source = [
		"class Card:",
		'    template: str = """<di"""',
		"    js = '''const value = 1'''",
		'    css = """article { color: red; }"""',
		'    my_template = """ignored"""',
	].join("\n");

	const regions = pythonEmbeddedRegions(source);

	assert.deepEqual(
		regions.map((region) => [region.language, source.slice(region.start, region.end)]),
		[
			["html", "<di"],
			["javascript", "const value = 1"],
			["css", "article { color: red; }"],
		],
	);
});

test("ignores assignment-shaped text in comments and other Python strings", () => {
	const source = [
		'# template = """comment"""',
		'example = """',
		'template = """ordinary string text"""',
		'"""',
		'template = """real"""',
	].join("\n");

	assert.deepEqual(
		pythonEmbeddedRegions(source).map((region) => source.slice(region.start, region.end)),
		["real"],
	);
});

test("keeps unfinished bodies available and respects escaped triple delimiters", () => {
	const unfinished = 'template = """<button';
	const escaped = String.raw`template = """say \""" still here"""`;

	assert.equal(
		unfinished.slice(pythonEmbeddedRegions(unfinished)[0].start, pythonEmbeddedRegions(unfinished)[0].end),
		"<button",
	);
	assert.equal(
		escaped.slice(pythonEmbeddedRegions(escaped)[0].start, pythonEmbeddedRegions(escaped)[0].end),
		String.raw`say \""" still here`,
	);
});

test("virtual documents retain coordinates, newlines, and only the selected language", () => {
	const source = ['lead = "😀"', 'template = """<sp😀an>"""', 'css = """a { color: red; }"""'].join("\n");
	const html = virtualDocumentSource(source, "python", "html");
	const css = virtualDocumentSource(source, "python", "css");

	assert.equal(html.length, source.length);
	assert.equal(css.length, source.length);
	assert.equal(html.split("\n").length, source.split("\n").length);
	assert.equal(html.includes("<sp😀an>"), true);
	assert.equal(html.includes("color: red"), false);
	assert.equal(css.includes("<sp😀an>"), false);
	assert.equal(css.includes("color: red"), true);
});

test("selects a provider only while the cursor is inside an embedded body", () => {
	const source = 'template = """<div>"""';
	const body = source.indexOf("<div>");

	assert.equal(embeddedLanguageAt(source, "python", body + 2), "html");
	assert.equal(embeddedLanguageAt(source, "python", source.indexOf("template")), undefined);
	assert.equal(embeddedLanguageAt("<div>", "citry-html", 2), "html");
	assert.equal(embeddedLanguageAt("<div>", "plaintext", 2), undefined);
});
