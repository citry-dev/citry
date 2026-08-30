import assert from "node:assert/strict";
import test from "node:test";

import { browserProjectionCandidateAt } from "../out/tests/browserRouting.mjs";

test("routes only browser-valued template attributes", () => {
	const source = [
		'template = """<c-element is="form" c-action="\'lol\'"></c-element>',
		'<button class="plain" :disabled="busy" @c-click="save()"></button>',
		'<input :c-query.debounce.300ms="refresh" />"""',
	].join("\n");

	assert.equal(browserProjectionCandidateAt(source, "python", source.indexOf("c-action") + 2), false);
	assert.equal(browserProjectionCandidateAt(source, "python", source.indexOf("plain") + 2), false);
	assert.equal(browserProjectionCandidateAt(source, "python", source.indexOf("busy") + 2), true);
	assert.equal(browserProjectionCandidateAt(source, "python", source.indexOf("save") + 2), true);
	assert.equal(browserProjectionCandidateAt(source, "python", source.indexOf("refresh") + 2), false);
});

test("finds Alpine expressions inside nested templates", () => {
	const source = "<c-card c-body=\"<><button :disabled='busy'>Save</button></>\" />";

	assert.equal(browserProjectionCandidateAt(source, "citry-html", source.indexOf("busy") + 2), true);
	assert.equal(browserProjectionCandidateAt(source, "citry-html", source.indexOf("Save") + 2), false);
});

test("routes complete component JavaScript but not Python around it", () => {
	const source = ["class Card:", '    js = """$component(({ data }) => data)"""'].join("\n");

	assert.equal(browserProjectionCandidateAt(source, "python", source.indexOf("$component") + 2), true);
	assert.equal(browserProjectionCandidateAt(source, "python", source.indexOf("class Card") + 2), false);
	assert.equal(browserProjectionCandidateAt("const value = 1", "javascript", 4), true);
});

test("does not route browser-looking text in raw HTML bodies", () => {
	const source = "<script>const sample = \"<button :disabled='busy'>\";</script>";

	assert.equal(browserProjectionCandidateAt(source, "citry-html", source.indexOf("busy") + 2), false);
});

test("routes registry-owned standalone HTML and unquoted browser values", () => {
	const source = "<button :disabled=busy>Save</button>";

	assert.equal(browserProjectionCandidateAt(source, "html", source.indexOf("busy") + 2), true);
	assert.equal(browserProjectionCandidateAt(source, "html", source.indexOf("Save") + 2), false);
});
