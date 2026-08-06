import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const manifestUrl = new URL("../package.json", import.meta.url);
const extensionSourceUrl = new URL("../src/extension.ts", import.meta.url);

test("packaging always compiles the current extension source", async () => {
	const manifest = JSON.parse(await readFile(manifestUrl, "utf8"));

	assert.match(manifest.scripts.prepackage, /pnpm run compile/);
});

test("formatter commands and native save integration are contributed", async () => {
	const manifest = JSON.parse(await readFile(manifestUrl, "utf8"));
	const commands = new Map(manifest.contributes.commands.map((item) => [item.command, item.title]));

	assert.equal(commands.get("citry.formatDocument"), "Citry: Format Document");
	assert.equal(commands.get("citry.formatAtCursor"), "Citry: Format at Cursor");
	assert.equal([...commands.keys()].filter((command) => command.startsWith("citry.format")).length, 2);
	assert.deepEqual(manifest.activationEvents.filter((event) => event.startsWith("onCommand:citry.format")).sort(), [
		"onCommand:citry.formatAtCursor",
		"onCommand:citry.formatDocument",
	]);
	assert.equal(manifest.contributes.configuration.properties["citry.formatOnSave"], undefined);
});

test("one extension-owned formatter routes all VS Code workspaces", async () => {
	const source = await readFile(extensionSourceUrl, "utf8");

	assert.equal(source.match(/registerDocumentFormattingEditProvider\(/g)?.length, 1);
	assert.equal(source.match(/registerCommand\("citry\.format(?:AtCursor|Document)"/g)?.length, 2);
	assert.match(source, /registerCommand\("citry\.formatAtCursor", formatAtCursor\)/);
	assert.match(source, /registerCommand\("citry\.formatDocument", formatCurrentDocument\)/);
	assert.match(
		source,
		/async function formatAtCursor[\s\S]*?languageId === "python"[\s\S]*?kind: "position"[\s\S]*?: \{ kind: "document" \}[\s\S]*?applyCitryFormatting/,
	);
	assert.doesNotMatch(source, /const formatTemplatesMethod|citry\/formatTemplates/);
	assert.match(source, /protocolVersion,\s*app,\s*standardFormatting: false,\s*embeddedFormatting:/);
	assert.match(source, /providerSelection: "vscode-first-result"/);
	assert.match(
		source,
		/client\.onRequest\(formatEmbeddedMethod, \(params, token\) => handleEmbeddedFormatting\(params, token\)\)/,
	);
	assert.doesNotMatch(source, /nextDocument|pass: String\(invocation\.pass\)/);
	assert.match(source, /this\.changes\.fire\(uri\)/);
	assert.match(source, /onDidChangeWorkspaceFolders\(async \(_event\) => \{\s*await restartAll\(\);\s*\}\)/);
	assert.match(source, /async provideDocumentFormattingEdits\(document, _options, token\) \{\s*const quiet = true;/);
	assert.match(source, /const prepared = await prepareVersionedEdit\(\{/);
	assert.match(
		source,
		/sendRequest<FormatResponse>\(\s*formatComponentAssetsMethod,[\s\S]*?scope: \{ kind: "document" \},[\s\S]*?token,\s*\)/,
	);
	assert.match(
		source,
		/let document = await this\.openDocument\(uri, invocation\.source, invocation\.signal\);\s*if \(invocation\.signal\.aborted\)/,
	);
	assert.match(
		source,
		/setTextDocumentLanguage\(document, invocation\.region\.language\);\s*if \(invocation\.signal\.aborted\)/,
	);
	assert.match(
		source,
		/const options = embeddedFormattingOptions[\s\S]*?if \(invocation\.signal\.aborted\)[\s\S]*?const result = await vscode\.commands\.executeCommand/,
	);
});

test("parameterless custom requests include params for pygls", async () => {
	const source = await readFile(extensionSourceUrl, "utf8");

	assert.equal(source.match(/sendRequest<ProjectStatus>\((?:statusMethod|reloadMethod), \{\}\)/g)?.length, 3);
	assert.doesNotMatch(source, /sendRequest<ProjectStatus>\((?:statusMethod|reloadMethod)\)/);
});
