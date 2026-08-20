const assert = require("node:assert/strict");
const path = require("node:path");
const vscode = require("vscode");

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function structuralCompletions(document) {
	const position = new vscode.Position(0, document.lineAt(0).text.length);
	for (let attempt = 0; attempt < 60; attempt += 1) {
		const result = await vscode.commands.executeCommand(
			"vscode.executeCompletionItemProvider",
			document.uri,
			position,
			"-",
		);
		if (result?.items?.some((item) => (typeof item.label === "string" ? item.label : item.label.label) === "c-for")) {
			return result;
		}
		await sleep(500);
	}
	throw new Error("citry-lsp did not return structural completion within 30 seconds");
}

async function exerciseFormatting(folder) {
	const fixture = process.env.CITRY_VSCODE_SMOKE_FORMATTING_FIXTURE;
	const source = fixture
		? Buffer.from(await vscode.workspace.fs.readFile(vscode.Uri.file(fixture))).toString("utf8")
		: [
				"from citry import Component",
				"",
				"class Card(Component):",
				'    template = """<main  ><script>const  inline=1;</script><style>.inline{color:red}</style></main>"""',
				'    js = """const  answer={value:41+1};"""',
				'    css = """.card{color:red;padding:0  1rem;}"""',
				"",
			].join("\n");
	const uri = vscode.Uri.joinPath(folder.uri, "format-smoke.py");
	// A standalone CSS preference must not send Citry's embedded virtual
	// documents back through VS Code's ambiguous first-nonempty provider loop.
	await vscode.workspace
		.getConfiguration(undefined, uri)
		.update(
			"[css]",
			{ "editor.defaultFormatter": "vscode.css-language-features" },
			vscode.ConfigurationTarget.WorkspaceFolder,
		);
	const cssEditor = vscode.workspace.getConfiguration("editor", { uri, languageId: "css" });
	assert.equal(cssEditor.get("defaultFormatter"), "vscode.css-language-features");
	await vscode.workspace.fs.writeFile(uri, Buffer.from(source, "utf8"));
	let document = await vscode.workspace.openTextDocument(uri);
	document = await vscode.languages.setTextDocumentLanguage(document, "python");
	await vscode.window.showTextDocument(document);
	await vscode.commands.executeCommand("citry.formatDocument", uri, true);
	const formatted = (await vscode.workspace.openTextDocument(uri)).getText();
	assert.notEqual(formatted, source, "Citry formatting did not change the deliberately untidy fixture");
	if (fixture) {
		assert.match(formatted, /<article class="card" x-data="/);
		assert.doesNotMatch(formatted, /<article class=\\"card\\"/);
		assert.ok(
			formatted.includes(
				[
					'    js = """',
					"      $component(({ els, data }) => {",
					"        const cardEl = els[0];",
					"        animateLikes(cardEl, data.likes);",
					"      });",
					'    """',
				].join("\n"),
			),
			"Citry did not apply canonical Python framing to ProductCard.js",
		);
		assert.ok(
			formatted.includes(
				[
					'    css = """',
					"      .card {",
					"        border-left: 3px solid var(--accent);",
					"      }",
					"      .tag--active {",
					"        color: var(--accent);",
					"      }",
					'    """',
				].join("\n"),
			),
			"Citry did not apply canonical Python framing to ProductCard.css",
		);
	} else {
		assert.match(formatted, /const answer = \{ value: 41 \+ 1 \};/);
		assert.match(formatted, /\.card \{/);
	}
	await vscode.commands.executeCommand("citry.formatDocument", uri, true);
	const repeated = (await vscode.workspace.openTextDocument(uri)).getText();
	assert.equal(repeated, formatted, "Citry formatting was not idempotent across commands");
}

async function run() {
	const python = process.env.CITRY_VSCODE_SMOKE_PYTHON;
	const expectedExtensionPath = process.env.CITRY_VSCODE_EXTENSION_DIR;
	assert.ok(python, "CITRY_VSCODE_SMOKE_PYTHON must be set");
	assert.ok(expectedExtensionPath, "CITRY_VSCODE_EXTENSION_DIR must be set");

	const folder = vscode.workspace.workspaceFolders?.[0];
	assert.ok(folder, "smoke test must open one file-backed workspace");
	await vscode.workspace
		.getConfiguration("citry", folder.uri)
		.update("python", python, vscode.ConfigurationTarget.WorkspaceFolder);

	const source = vscode.Uri.joinPath(folder.uri, "smoke.citry-html");
	await vscode.workspace.fs.writeFile(source, Buffer.from("<c-", "utf8"));
	let document = await vscode.workspace.openTextDocument(source);
	document = await vscode.languages.setTextDocumentLanguage(document, "citry-html");
	await vscode.window.showTextDocument(document);

	const extension = vscode.extensions.getExtension("citry-dev.citry");
	assert.ok(extension, "qualified citry-dev.citry extension is not installed");
	assert.equal(extension.packageJSON.version, "0.1.0");
	assert.equal(path.resolve(extension.extensionPath), path.resolve(expectedExtensionPath));
	await extension.activate();
	assert.equal(extension.isActive, true);
	if (process.env.CITRY_VSCODE_EXPECT_UNAVAILABLE === "1") {
		await sleep(500);
		return;
	}

	const completion = await structuralCompletions(document);
	const labels = new Set(
		completion.items.map((item) => (typeof item.label === "string" ? item.label : item.label.label)),
	);
	assert.ok(labels.has("c-if"));
	assert.ok(labels.has("c-for"));
	assert.ok(labels.has("c-slot"));
	if (process.env.CITRY_VSCODE_SMOKE_FORMATTING === "1") {
		await exerciseFormatting(folder);
	}
}

module.exports = { run };
