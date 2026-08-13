import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { loadWASM, OnigScanner, OnigString } = require("vscode-oniguruma");
const { INITIAL, Registry } = require("vscode-textmate");

const TEST_DIR = path.dirname(fileURLToPath(import.meta.url));
const EXTENSION_DIR = path.dirname(TEST_DIR);
const FIXTURE_DIR = path.resolve(EXTENSION_DIR, "../syntax-fixtures");
const FORMATTER_FIXTURE_DIR = path.resolve(
	EXTENSION_DIR,
	"../../../crates/citry_template_formatter/tests/fixtures/v1/embedded",
);

const GRAMMAR_PATHS = new Map([
	["text.html.citry", path.join(EXTENSION_DIR, "syntaxes/citry-html.tmLanguage.json")],
	["citry.html.injection", path.join(EXTENSION_DIR, "syntaxes/citry-html.injection.tmLanguage.json")],
	[
		"citry.html.attributes.injection",
		path.join(EXTENSION_DIR, "syntaxes/citry-html-attributes.injection.tmLanguage.json"),
	],
	["citry.python.injection", path.join(EXTENSION_DIR, "syntaxes/citry-python.injection.tmLanguage.json")],
	["text.html.basic", path.join(TEST_DIR, "grammars/html.tmLanguage.json")],
	["source.python", path.join(TEST_DIR, "grammars/python.tmLanguage.json")],
	["source.js", path.join(TEST_DIR, "grammars/javascript.tmLanguage.json")],
	["source.css", path.join(TEST_DIR, "grammars/css.tmLanguage.json")],
	["source.ftl", path.join(EXTENSION_DIR, "syntaxes/fluent.tmLanguage.json")],
]);

const INJECTIONS = new Map([["source.python", ["citry.python.injection", "citry.html.attributes.injection"]]]);

const wasmPath = require.resolve("vscode-oniguruma/release/onig.wasm");
await loadWASM(await readFile(wasmPath));

const registry = new Registry({
	onigLib: Promise.resolve({
		createOnigScanner: (patterns) => {
			try {
				return new OnigScanner(patterns);
			} catch (error) {
				throw new Error(`${error.message}: ${JSON.stringify(patterns)}`, { cause: error });
			}
		},
		createOnigString: (value) => new OnigString(value),
	}),
	getInjections: (scopeName) => INJECTIONS.get(scopeName) ?? [],
	loadGrammar: async (scopeName) => {
		const grammarPath = GRAMMAR_PATHS.get(scopeName);
		if (!grammarPath) return null;
		return JSON.parse(await readFile(grammarPath, "utf8"));
	},
});

const [corpus, roleScopes, manifest] = await Promise.all([
	readJson(path.join(FIXTURE_DIR, "template.json")),
	readJson(path.join(TEST_DIR, "role-scopes.json")),
	readJson(path.join(EXTENSION_DIR, "package.json")),
]);

async function readJson(filePath) {
	return JSON.parse(await readFile(filePath, "utf8"));
}

async function tokenize(scopeName, source) {
	const grammar = await registry.loadGrammar(scopeName);
	assert.ok(grammar, `grammar ${scopeName} must load`);

	const tokens = [];
	let offset = 0;
	let ruleStack = INITIAL;
	for (const line of source.split("\n")) {
		const result = grammar.tokenizeLine(line, ruleStack);
		for (const token of result.tokens) {
			tokens.push({
				start: offset + token.startIndex,
				end: offset + token.endIndex,
				scopes: token.scopes,
			});
		}
		ruleStack = result.ruleStack;
		offset += line.length + 1;
	}
	return tokens;
}

function findOccurrence(source, needle, occurrence = 1) {
	let at = -1;
	let from = 0;
	for (let index = 0; index < occurrence; index += 1) {
		at = source.indexOf(needle, from);
		assert.notEqual(at, -1, `missing occurrence ${occurrence} of ${JSON.stringify(needle)}`);
		from = at + needle.length;
	}
	return at;
}

function tokenAt(tokens, offset) {
	return tokens.find((token) => token.start <= offset && offset < token.end);
}

function scopeMatches(scope, expected) {
	return scope === expected || scope.startsWith(`${expected}.`);
}

function scopeHasRole(scope, role) {
	const expected = roleScopes[role];
	const expectedScopes = Array.isArray(expected) ? expected : [expected];
	return expectedScopes.some((candidate) => scopeMatches(scope, candidate));
}

function hasRole(token, role) {
	const expected = roleScopes[role];
	assert.ok(expected, `fixture uses unmapped role ${role}`);
	if (role === "text") {
		const semanticScope = token.scopes.some(
			(scope) =>
				scopeHasRole(scope, "tag") ||
				scopeHasRole(scope, "attribute") ||
				scopeHasRole(scope, "python") ||
				scopeHasRole(scope, "javascript") ||
				scopeHasRole(scope, "css") ||
				scopeHasRole(scope, "message-id") ||
				scopeHasRole(scope, "message-variable") ||
				scopeHasRole(scope, "handler") ||
				scopeHasRole(scope, "comment"),
		);
		return !semanticScope && token.scopes.some((scope) => scope.startsWith("text"));
	}
	return token.scopes.some((scope) => scopeHasRole(scope, role));
}

function formatToken(token) {
	return token ? token.scopes.join(" ") : "<no token>";
}

test("the Citry Template language makes no automatic standalone filename claim", () => {
	assert.equal(manifest.main, "./out/extension.js");
	assert.equal(manifest.browser, undefined);
	const language = manifest.contributes.languages.find(({ id }) => id === "citry-html");
	assert.ok(language);
	assert.equal(language.extensions, undefined);
	assert.equal(language.filenamePatterns, undefined);
	assert.equal(language.filenames, undefined);
});

test("the Fluent language owns standalone .ftl files", () => {
	const language = manifest.contributes.languages.find(({ id }) => id === "fluent");
	assert.ok(language);
	assert.deepEqual(language.extensions, [".ftl"]);
	assert.ok(manifest.activationEvents.includes("onLanguage:fluent"));
});

test("every contributed grammar file loads", async () => {
	for (const contribution of manifest.contributes.grammars) {
		const grammar = await registry.loadGrammar(contribution.scopeName);
		assert.ok(grammar, `${contribution.scopeName} must load`);
	}
});

for (const fixture of corpus.cases) {
	test(`shared syntax fixture: ${fixture.name}`, async () => {
		const scopeName = fixture.language === "citry" ? "source.python" : "text.html.citry";
		const tokens = await tokenize(scopeName, fixture.source);

		for (const assertion of fixture.assertions) {
			const offset = findOccurrence(fixture.source, assertion.text, assertion.occurrence);
			const token = tokenAt(tokens, offset);
			assert.ok(
				token && hasRole(token, assertion.role),
				`${fixture.name}: ${JSON.stringify(assertion.text)} expected ${assertion.role}, got ${formatToken(token)}`,
			);
		}

		if (!fixture.allow_errors) {
			const error = tokens.find((token) =>
				token.scopes.some((scope) => /(?:^|\.)(?:invalid|error)(?:\.|$)/.test(scope)),
			);
			assert.equal(error, undefined, `${fixture.name}: unexpected error scope ${formatToken(error)}`);
		}
	});
}

test("Python template attributes preserve Citry channel precedence", async () => {
	const source = [
		"class Controls(Component):",
		'    template = """',
		"      <div",
		'        c-body="<span>{{ nested_value }}</span>"',
		'        c-title="server_value"',
		'        c-@click="server_handler"',
		'        @click="client_open = !client_open"',
		'        @c-submit="save({ draft: event_draft })"',
		'        :c-status="refresh"',
		"      >{# template note #}</div>",
		"      <c-raw>{{ raw_value }}</c-raw>",
		'    """',
	].join("\n");
	const tokens = await tokenize("source.python", source);

	for (const [needle, role] of [
		["nested_value", "python"],
		["server_value", "python"],
		["server_handler", "python"],
		["client_open", "javascript"],
		["save", "handler"],
		["event_draft", "javascript"],
		["refresh", "handler"],
		["{# template note #}", "comment"],
		["raw_value", "text"],
	]) {
		const token = tokenAt(tokens, findOccurrence(source, needle));
		assert.ok(token && hasRole(token, role), `${needle} expected ${role}, got ${formatToken(token)}`);
	}
});

test("Python call targets receive standard function and method scopes", async () => {
	const template = [
		'<p>{{ tr("hello") }}</p>',
		'<p>{{ fmt.currency(amount, "USD") }}</p>',
		'<c-if cond="is_visible (amount)"></c-if>',
		'<c-for each="item in build_items()"></c-for>',
		'<c-Card c-title="format_title(amount)" c-value=fmt.number(amount)></c-Card>',
		"<p>{{ fmt.currency }}</p>",
		'<p>{{ "quoted_call()" }}</p>',
	].join("\n");
	const sources = [
		{ scopeName: "text.html.citry", source: template },
		{
			scopeName: "source.python",
			source: ["class Card(Component):", '    template = """', template, '    """'].join("\n"),
		},
	];

	for (const { scopeName, source } of sources) {
		const tokens = await tokenize(scopeName, source);
		for (const needle of ["tr", "is_visible", "build_items", "format_title"]) {
			const token = tokenAt(tokens, findOccurrence(source, needle));
			assert.ok(token && hasRole(token, "function"), `${needle} expected function, got ${formatToken(token)}`);
		}
		for (const needle of ["currency", "number"]) {
			const token = tokenAt(tokens, findOccurrence(source, needle));
			assert.ok(token && hasRole(token, "method"), `${needle} expected method, got ${formatToken(token)}`);
		}

		const plainMember = tokenAt(tokens, findOccurrence(source, "currency", 2));
		assert.equal(hasRole(plainMember, "method"), false, formatToken(plainMember));
		const quotedText = tokenAt(tokens, findOccurrence(source, "quoted_call"));
		assert.equal(hasRole(quotedText, "function"), false, formatToken(quotedText));
	}
});

test("typed and triple-single-quoted component attributes embed", async () => {
	const source = [
		"class Card(Component):",
		"    template: ClassVar[str] = '''<c-Card>{{ title }}</c-Card>'''",
		"    js: str = '''const enabled = true;'''",
		"    css: str = '''.card { color: red; }'''",
		"    messages: str = '''account-title = Welcome, { $name }.'''",
	].join("\n");
	const tokens = await tokenize("source.python", source);

	for (const [needle, role] of [
		["c-Card", "tag"],
		["title", "python"],
		["true", "javascript"],
		["red", "css"],
		["account-title", "message-id"],
		["$name", "message-variable"],
	]) {
		const token = tokenAt(tokens, findOccurrence(source, needle));
		assert.ok(token && hasRole(token, role), `${needle} expected ${role}, got ${formatToken(token)}`);
	}
});

test("standalone Fluent highlights messages, attributes, selectors, and variables", async () => {
	const source = [
		"# @param {int} $count - Item count.",
		"account-count = { $count ->",
		"  [one] One item",
		" *[other] { NUMBER($count) } items",
		"}",
		"    .aria-label = Items for { $count }",
		"-brand = Citry",
		"account-summary = { account-count.aria-label } by { -brand }",
	].join("\n");
	const tokens = await tokenize("source.ftl", source);

	for (const [needle, role, occurrence = 1] of [
		["# @param", "comment"],
		["account-count", "message-id"],
		["$count", "message-variable", 2],
	]) {
		const token = tokenAt(tokens, findOccurrence(source, needle, occurrence));
		assert.ok(token && hasRole(token, role), `${needle} expected ${role}, got ${formatToken(token)}`);
	}
	assert.ok(
		tokenAt(tokens, findOccurrence(source, "aria-label"))?.scopes.some((scope) =>
			scopeMatches(scope, "entity.other.attribute-name.fluent"),
		),
	);
	assert.ok(
		tokenAt(tokens, findOccurrence(source, "other"))?.scopes.some((scope) =>
			scopeMatches(scope, "constant.other.variant.fluent"),
		),
	);
	assert.ok(
		tokenAt(tokens, findOccurrence(source, "account-count", 2))?.scopes.some((scope) =>
			scopeMatches(scope, "variable.other.message.fluent"),
		),
	);
	assert.ok(
		tokenAt(tokens, findOccurrence(source, "brand", 2))?.scopes.some((scope) =>
			scopeMatches(scope, "variable.other.term.fluent"),
		),
	);
});

test("Fluent prose that contains an equals sign is not a message definition", async () => {
	const source = "actual = Plain text where not-a-message = remains prose";
	const tokens = await tokenize("source.ftl", source);
	const prose = tokenAt(tokens, findOccurrence(source, "not-a-message"));

	assert.equal(hasRole(prose, "message-id"), false);
});

test("escaped triple delimiters do not end component embeds", async () => {
	for (const source of [
		String.raw`template = """<div title="say \""" now">{{ double_value }}</div>"""`,
		String.raw`template = '''<div title="say \''' now">{{ single_value }}</div>'''`,
	]) {
		const tokens = await tokenize("source.python", source);
		const value = source.includes("double_value") ? "double_value" : "single_value";
		assert.equal(hasRole(tokenAt(tokens, findOccurrence(source, value)), "python"), true);
	}
});

test("triple-string ends respect odd and even backslash runs", async () => {
	const variants = [
		{ assignment: "template", marker: "{{ parity_value }}", needle: "parity_value", role: "python" },
		{ assignment: "js", marker: "const parityValue = true;", needle: "parityValue", role: "javascript" },
		{ assignment: "css", marker: ".parity-value { color: red; }", needle: "parity-value", role: "css" },
		{
			assignment: "messages",
			marker: "hello = { $parity_value }",
			needle: "$parity_value",
			role: "message-variable",
		},
	];

	for (const { assignment, marker, needle, role } of variants) {
		for (const delimiter of ['"""', "'''"]) {
			for (const slashCount of [1, 2, 3, 4]) {
				const slashes = "\\".repeat(slashCount);
				const escapedEnd = slashCount % 2 === 1;
				const source = escapedEnd
					? `${assignment} = ${delimiter}body ${slashes}${delimiter} ${marker}${delimiter}\nsentinel = 1`
					: `${assignment} = ${delimiter}body ${slashes}${delimiter}\nsentinel = 1`;
				const tokens = await tokenize("source.python", source);
				const sentinel = tokenAt(tokens, findOccurrence(source, "sentinel"));
				assert.ok(
					sentinel && !sentinel.scopes.some((scope) => scope.startsWith("meta.embedded.block")),
					`${assignment} ${delimiter} with ${slashCount} backslashes must end before sentinel: ${formatToken(sentinel)}`,
				);

				if (escapedEnd) {
					const markerToken = tokenAt(tokens, findOccurrence(source, needle));
					assert.ok(
						markerToken && hasRole(markerToken, role),
						`${assignment} ${delimiter} with ${slashCount} backslashes must retain ${role}: ${formatToken(markerToken)}`,
					);
				}
			}
		}
	}
});

test("JavaScript line comments stop before Python triple-string ends", async () => {
	for (const delimiter of ['"""', "'''"]) {
		const source = `js = ${delimiter}const value = 1; // comment${delimiter}\nsentinel = 1`;
		const tokens = await tokenize("source.python", source);
		const sentinel = tokenAt(tokens, findOccurrence(source, "sentinel"));

		assert.ok(sentinel && !sentinel.scopes.some((scope) => scope.startsWith("meta.embedded.block")));
		assert.equal(hasRole(tokenAt(tokens, findOccurrence(source, "// comment")), "comment"), true);
	}
});

test("CSS tokenization is bounded before Python triple-string ends", async () => {
	for (const delimiter of ['"""', "'''"]) {
		for (const body of ["body", ".card", "color: red;", `body ${"\\".repeat(2)}`, `body ${"\\".repeat(4)}`]) {
			const source = `css = ${delimiter}${body}${delimiter}\nsentinel = 1`;
			const tokens = await tokenize("source.python", source);
			const bodyToken = tokenAt(tokens, findOccurrence(source, body.replaceAll("\\", "").trim()));
			const sentinel = tokenAt(tokens, findOccurrence(source, "sentinel"));

			assert.ok(bodyToken && hasRole(bodyToken, "css"), formatToken(bodyToken));
			assert.ok(
				sentinel && !sentinel.scopes.some((scope) => scope.startsWith("meta.embedded.block")),
				`${delimiter} ${JSON.stringify(body)} must return to Python: ${formatToken(sentinel)}`,
			);
		}
	}
});

test("template comments can immediately follow every specialized tag name", async () => {
	for (const { source, name } of [
		{ source: "<c-Card{# component note #}></c-Card>", name: "c-Card" },
		{ source: '<c-if{# condition note #} cond="ready"></c-if>', name: "c-if" },
		{ source: '<c-for{# loop note #} each="item in items"></c-for>', name: "c-for" },
		{ source: "<c-raw{# raw note #}>{{ untouched }}</c-raw{# end note #}>", name: "c-raw" },
	]) {
		const tokens = await tokenize("text.html.citry", source);
		const tag = tokenAt(tokens, findOccurrence(source, name));
		const comment = tokenAt(tokens, findOccurrence(source, "{#"));

		assert.ok(
			tag?.scopes.some((scope) => scopeMatches(scope, "entity.name.tag.citry")),
			formatToken(tag),
		);
		assert.equal(hasRole(comment, "comment"), true);
	}

	const permissiveName = "<c-a{b></c-a{b>";
	const permissiveTokens = await tokenize("text.html.citry", permissiveName);
	const tag = tokenAt(permissiveTokens, findOccurrence(permissiveName, "c-a{b"));
	assert.ok(
		tag?.scopes.some((scope) => scopeMatches(scope, "entity.name.tag.citry")),
		formatToken(tag),
	);
});

test("ordinary Python strings and static HTML attributes stay in their host language", async () => {
	const python = 'message = "<c-Card>{{ title }}</c-Card>"';
	const pythonTokens = await tokenize("source.python", python);
	assert.equal(hasRole(tokenAt(pythonTokens, findOccurrence(python, "c-Card")), "tag"), false);

	const html = '<div title="{{ title }}">plain</div>';
	const htmlTokens = await tokenize("text.html.citry", html);
	assert.equal(hasRole(tokenAt(htmlTokens, findOccurrence(html, "title", 2)), "python"), false);
});

test("embedded line comments stop before template host delimiters", async () => {
	for (const source of [
		"<p>{{ value # interpolation comment }}</p>\n<p>after</p>",
		'<div c-if="value # attribute comment"></div>\n<p>after</p>',
		"<c-for each='item in items # loop comment'></c-for>\n<p>after</p>",
		'<button @click="run() // event comment"></button>\n<p>after</p>',
		"<div x-data='{ ready: true } // state comment'></div>\n<p>after</p>",
	]) {
		const tokens = await tokenize("text.html.citry", source);
		const after = tokenAt(tokens, findOccurrence(source, "after"));
		const comment = tokenAt(tokens, source.indexOf("comment") - 2);

		assert.ok(
			after?.scopes.some((scope) => scopeMatches(scope, "text.html")),
			formatToken(after),
		);
		assert.equal(hasRole(comment, "comment"), true, formatToken(comment));
	}
});

test("interpolation comment text cannot hide the first host delimiter", async () => {
	for (const source of [
		"{{ user.name # show the person's name }}",
		"{{ value # } note }}",
		"{{ value # { note }}",
		'{{ value # say "}}" then stop }}',
	]) {
		const tokens = await tokenize("text.html.citry", source);
		const closeStart = source.indexOf("}}");
		const close = tokenAt(tokens, closeStart);
		const commentTokens = tokens.filter(
			(token) => token.start >= source.indexOf("#") && token.start < closeStart && hasRole(token, "comment"),
		);

		assert.ok(
			close?.scopes.some((scope) => scopeMatches(scope, "punctuation.section.embedded.end.citry")),
			formatToken(close),
		);
		assert.ok(commentTokens.length > 0, source);
		assert.equal(Math.max(...commentTokens.map((token) => token.end)), closeStart, source);
	}
});

test("Python injection uses exact assignment names but cannot prove component inheritance", async () => {
	const source = [
		'payload = """<input c-checked="ordinary.value"><c-Plain>{{ ordinary }}</c-Plain>"""',
		'template = """<c-Highlighted>{{ embedded }}</c-Highlighted>"""',
	].join("\n");
	const tokens = await tokenize("source.python", source);

	assert.equal(hasRole(tokenAt(tokens, findOccurrence(source, "c-Plain")), "tag"), false);
	assert.equal(hasRole(tokenAt(tokens, findOccurrence(source, "ordinary.value")), "python"), false);
	assert.equal(hasRole(tokenAt(tokens, findOccurrence(source, "c-Highlighted")), "tag"), true);
});

test("standalone templates inherit HTML script and style embedding", async () => {
	const source = [
		"<script>const scriptReady = true;</script>",
		"<style>.card { border-color: rebeccapurple; }</style>",
	].join("\n");
	const tokens = await tokenize("text.html.citry", source);

	assert.equal(hasRole(tokenAt(tokens, findOccurrence(source, "scriptReady")), "javascript"), true);
	assert.equal(hasRole(tokenAt(tokens, findOccurrence(source, "rebeccapurple")), "css"), true);
});

test("formatted script/style fixture retains tag and embedded-language scopes", async () => {
	const source = await readFile(path.join(FORMATTER_FIXTURE_DIR, "script-style.expected.citry-html"), "utf8");
	const tokens = await tokenize("text.html.citry", source);

	for (const [needle, role] of [
		["script", "tag"],
		["const", "javascript"],
		["style", "tag"],
		["card", "css"],
	]) {
		const token = tokenAt(tokens, findOccurrence(source, needle));
		assert.ok(token && hasRole(token, role), `${needle} expected ${role}, got ${formatToken(token)}`);
	}
});

test("Citry event arguments keep JavaScript scope through nested parentheses", async () => {
	const source = '<button @c-click="save({ value: (1 + 2), tail: open })"></button>';
	const tokens = await tokenize("text.html.citry", source);

	assert.equal(hasRole(tokenAt(tokens, findOccurrence(source, "save")), "handler"), true);
	assert.equal(hasRole(tokenAt(tokens, findOccurrence(source, "tail")), "javascript"), true);
	assert.equal(hasRole(tokenAt(tokens, findOccurrence(source, "open")), "javascript"), true);
});
