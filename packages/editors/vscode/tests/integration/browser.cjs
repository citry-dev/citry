const assert = require("node:assert/strict");
const vscode = require("vscode");

async function eventually(label, probe) {
	for (let attempt = 0; attempt < 80; attempt += 1) {
		const result = await probe();
		if (result) return result;
		await new Promise((resolve) => setTimeout(resolve, 250));
	}
	throw new Error(`Browser integration timed out: ${label}`);
}

async function exerciseBrowser(folder) {
	for (const className of ["Inferred", "Declared"]) {
		const source = [
			"from citry import Citry, Component",
			"engine = Citry(autodiscover=False)",
			"",
			`class ${className}(Component):`,
			"    citry = engine",
			...(className === "Declared" ? ["    class JsData:", "        a: str", "        ab: str", "        b: int"] : []),
			"    def js_data(self, kwargs, slots):",
			// Only the first fixture sends this key. The second fixture must not be
			// offered it, which proves each projection is typed on its own.
			className === "Inferred"
				? '        return {"a": "str", "ab": "longer", "b": 1, "inferredOnly": 2}'
				: '        return {"a": "str", "ab": "longer", "b": 1}',
			'    js = """',
			"      $component(({ component, revision }) => {",
			"        // Completion should offer the js_data() keys after component.",
			"        // The string key is component.a and the numeric key is component.b.",
			"        // Several indented lines must preserve the authored edit position.",
			"        console.log(component.b, revision);",
			"        console.log(component.c);",
			"        window.setTimeout(() => {}, 0);",
			"      });",
			'    """',
			"",
		].join("\n");
		const moduleName = `browser_fixture_${className.toLowerCase()}`;
		const uri = vscode.Uri.joinPath(folder.uri, `${moduleName}.py`);
		await vscode.workspace.fs.writeFile(uri, Buffer.from(source));
		await vscode.workspace
			.getConfiguration("citry", uri)
			.update("app", `${moduleName}:engine`, vscode.ConfigurationTarget.WorkspaceFolder);
		const document = await vscode.workspace.openTextDocument(uri);
		await vscode.window.showTextDocument(document);
		const classStart = source.indexOf(`class ${className}`);
		const access = source.indexOf("console.log(component.b", classStart) + "console.log(".length;
		const position = document.positionAt(access + "component.".length);
		const itemsAt = async (cursor) => {
			const result = await vscode.commands.executeCommand("vscode.executeCompletionItemProvider", uri, cursor);
			return result?.items ?? [];
		};
		const labelsAt = async (cursor) => {
			return new Set(
				(await itemsAt(cursor)).map((item) => (typeof item.label === "string" ? item.label : item.label.label)),
			);
		};
		// Wait for the selected app schema before testing unsaved authoring.
		await eventually(`${className} completion before existing member`, async () => {
			const labels = await labelsAt(position);
			return (
				labels.has("a") &&
				labels.has("ab") &&
				labels.has("b") &&
				labels.has("inferredOnly") === (className === "Inferred")
			);
		});
		// Remove complete spellings so each request must complete an unfinished
		// identifier in the unsaved document.
		for (const [name, marker, prefixLength] of [
			["console", "console.log", 4],
			["window", "window.setTimeout", 3],
			["revision", "revision })", 3],
		]) {
			const prefix = name.slice(0, prefixLength);
			const incompleteSource = source.replaceAll(name, prefix);
			const incomplete = new vscode.WorkspaceEdit();
			incomplete.replace(
				uri,
				new vscode.Range(document.positionAt(0), document.positionAt(document.getText().length)),
				incompleteSource,
			);
			assert.equal(await vscode.workspace.applyEdit(incomplete), true);
			assert.equal(document.isDirty, true);
			assert.equal(document.getText().includes(name), false);
			const offset = incompleteSource.indexOf(
				marker.replace(name, prefix),
				incompleteSource.indexOf(`class ${className}`),
			);
			assert.ok(offset >= 0);
			const cursor = document.positionAt(offset + prefixLength);
			try {
				await eventually(`${className} unsaved ${prefix} completes to ${name}`, async () =>
					(await labelsAt(cursor)).has(name),
				);
			} finally {
				const restoreSource = new vscode.WorkspaceEdit();
				restoreSource.replace(
					uri,
					new vscode.Range(document.positionAt(0), document.positionAt(document.getText().length)),
					source,
				);
				assert.equal(await vscode.workspace.applyEdit(restoreSource), true);
				assert.equal(document.getText(), source);
			}
		}
		// The prefix is itself an owned field, but longer members must remain available.
		const erase = new vscode.WorkspaceEdit();
		erase.delete(uri, new vscode.Range(position, position.translate(0, 1)));
		await vscode.workspace.applyEdit(erase);
		await eventually(`${className} incomplete component.`, async () => (await labelsAt(position)).has("ab"));
		const edit = new vscode.WorkspaceEdit();
		edit.insert(uri, position, "a");
		await vscode.workspace.applyEdit(edit);
		const cursor = position.translate(0, 1);
		const completion = await eventually(`${className} component.a completion includes ab`, async () =>
			(await itemsAt(cursor)).find((item) => (typeof item.label === "string" ? item.label : item.label.label) === "ab"),
		);
		// VS Code discards suggestions whose edit range is on another source line,
		// even when executeCompletionItemProvider returns their labels.
		const replacing = completion.range?.replacing ?? completion.range;
		const inserting = completion.range?.inserting ?? completion.range;
		for (const range of [inserting, replacing]) {
			assert.ok(range, "member completion must provide an authored edit range");
			assert.equal(range.start.line, cursor.line);
			assert.equal(range.end.line, cursor.line);
			assert.ok(range.contains(cursor));
		}
		assert.ok(inserting.start.isEqual(replacing.start));
		assert.ok(replacing.contains(inserting));
		assert.equal(completion.insertText, "ab");
		const accepted = new vscode.WorkspaceEdit();
		accepted.replace(uri, replacing, completion.insertText);
		assert.equal(await vscode.workspace.applyEdit(accepted), true);
		assert.equal(document.getText(), source.replace("console.log(component.b", "console.log(component.ab"));
		const restore = new vscode.WorkspaceEdit();
		restore.replace(uri, new vscode.Range(position, position.translate(0, 2)), "b");
		await vscode.workspace.applyEdit(restore);
		await eventually(`${className} property hover`, async () => {
			const hovers = await vscode.commands.executeCommand("vscode.executeHoverProvider", uri, position);
			const text = (hovers ?? [])
				.flatMap((hover) => hover.contents)
				.map((content) => (typeof content === "string" ? content : content.value))
				.join("\n");
			return /\(property\) b: (?:number|1)\b/.test(text);
		});
		const bindingOffset = source.indexOf("component, revision", classStart);
		await eventually(`${className} callback definition`, async () => {
			const locations = await vscode.commands.executeCommand(
				"vscode.executeDefinitionProvider",
				uri,
				document.positionAt(access + 1),
			);
			return locations?.some((location) => {
				const target = location.targetUri ?? location.uri;
				const range = location.targetSelectionRange ?? location.range;
				return target.toString() === uri.toString() && document.offsetAt(range.start) === bindingOffset;
			});
		});
		const unknownOffset = source.indexOf("component.c", classStart) + "component.".length;
		await eventually(`${className} unknown member diagnostic`, async () =>
			vscode.languages
				.getDiagnostics(uri)
				.some(
					(diagnostic) =>
						diagnostic.range.start.isEqual(document.positionAt(unknownOffset)) &&
						diagnostic.range.end.isEqual(document.positionAt(unknownOffset + 1)) &&
						(typeof diagnostic.code === "object" ? diagnostic.code.value : diagnostic.code) ===
							"citry.component-js.unknown-member",
				),
		);
		const corrected = new vscode.WorkspaceEdit();
		const unknownPosition = document.positionAt(unknownOffset);
		corrected.replace(uri, new vscode.Range(unknownPosition, unknownPosition.translate(0, 1)), "a");
		await vscode.workspace.applyEdit(corrected);
		await eventually(
			`${className} corrected member clears diagnostic`,
			async () =>
				!vscode.languages
					.getDiagnostics(uri)
					.some(
						(diagnostic) =>
							diagnostic.range.contains(unknownPosition) &&
							(typeof diagnostic.code === "object" ? diagnostic.code.value : diagnostic.code) ===
								"citry.component-js.unknown-member",
					),
		);
		const restoreUnknown = new vscode.WorkspaceEdit();
		restoreUnknown.replace(uri, new vscode.Range(unknownPosition, unknownPosition.translate(0, 1)), "c");
		await vscode.workspace.applyEdit(restoreUnknown);
		assert.equal(document.getText(), source);
	}
	await exerciseStateBindingTarget(folder);
	await exerciseOptionsInstance(folder);
}

// `this` in an Options function and a template name both read the live
// instance, so both must know every member and open its declaration.
async function exerciseOptionsInstance(folder) {
	const moduleName = "browser_fixture_options";
	const uri = vscode.Uri.joinPath(folder.uri, `${moduleName}.py`);
	const source = [
		"from citry import Citry, Component",
		"engine = Citry(autodiscover=False)",
		"",
		"class Options(Component):",
		"    citry = engine",
		"    class JsData:",
		"        title: str",
		'    template = """',
		'      <button @click="toggle()" v-text="count"></button>',
		'    """',
		'    js = """',
		"      $component({",
		"        emits: ['toggled'],",
		"        data() { return { count: 1 }; },",
		"        methods: {",
		"          toggle() {",
		"            this.count += 1;",
		"            this.$emit('toggled', this.$el);",
		"            this.$emit('toggeld');",
		"            this.$el.fooBar;",
		"            return this.title;",
		"          },",
		"        },",
		"      });",
		'    """',
		"",
	].join("\n");
	await vscode.workspace.fs.writeFile(uri, Buffer.from(source));
	await vscode.workspace
		.getConfiguration("citry", uri)
		.update("app", `${moduleName}:engine`, vscode.ConfigurationTarget.WorkspaceFolder);
	const document = await vscode.workspace.openTextDocument(uri);
	await vscode.window.showTextDocument(document);
	const at = (marker, offset) => document.positionAt(source.indexOf(marker) + offset);
	const hoverText = async (position) =>
		((await vscode.commands.executeCommand("vscode.executeHoverProvider", uri, position)) ?? [])
			.flatMap((hover) => hover.contents)
			.map((content) => (typeof content === "string" ? content : content.value))
			.join("\n");
	const definitionsAt = async (position) =>
		((await vscode.commands.executeCommand("vscode.executeDefinitionProvider", uri, position)) ?? []).map(
			(location) => ({
				uri: (location.targetUri ?? location.uri).toString(),
				offset: document.offsetAt((location.targetSelectionRange ?? location.range).start),
			}),
		);
	const opens = async (position, marker) =>
		(await definitionsAt(position)).some(
			(target) => target.uri === uri.toString() && target.offset === source.indexOf(marker),
		);

	const memberStart = at("this.count += 1", "this.".length);
	await eventually("Options this completion", async () => {
		const result = await vscode.commands.executeCommand("vscode.executeCompletionItemProvider", uri, memberStart);
		const labels = new Set(
			(result?.items ?? []).map((item) => (typeof item.label === "string" ? item.label : item.label.label)),
		);
		return ["count", "toggle", "title", "$sendEvent"].every((name) => labels.has(name));
	});
	await eventually("Options this hover", async () =>
		/\(property\) count: number\b/.test(await hoverText(at("this.count += 1", "this.c".length))),
	);
	await eventually("Options this data() definition", async () =>
		opens(at("this.count += 1", "this.c".length), "count: 1"),
	);
	await eventually("Options this js_data() definition", async () =>
		opens(at("this.title", "this.t".length), "title: str"),
	);
	await eventually("template instance hover", async () =>
		/count: number\b/.test(await hoverText(at('v-text="count"', 'v-text="c'.length))),
	);
	await eventually("template data() definition", async () =>
		opens(at('v-text="count"', 'v-text="c'.length), "count: 1"),
	);
	await eventually("template method definition", async () =>
		opens(at('@click="toggle', '@click="t'.length), "toggle() {"),
	);
	// `$el` is typed from the template's root element.
	await eventually("root element hover", async () =>
		/\$el: HTMLButtonElement\b/.test(await hoverText(at("this.$el", "this.$e".length))),
	);
	// `$emit` offers the declared event names, like Vue's defineComponent().
	await eventually("declared emit completion", async () => {
		const result = await vscode.commands.executeCommand(
			"vscode.executeCompletionItemProvider",
			uri,
			at("this.$emit('toggled'", "this.$emit('".length),
		);
		return (result?.items ?? []).some(
			(item) => (typeof item.label === "string" ? item.label : item.label.label) === "toggled",
		);
	});
	const typo = source.indexOf("toggeld");
	await eventually("undeclared emit diagnostic", async () =>
		vscode.languages
			.getDiagnostics(uri)
			.some(
				(diagnostic) =>
					(typeof diagnostic.code === "object" ? diagnostic.code.value : diagnostic.code) ===
						"citry.browser.undeclared-emit" &&
					diagnostic.severity === vscode.DiagnosticSeverity.Error &&
					diagnostic.range.start.isEqual(document.positionAt(typo)) &&
					diagnostic.range.end.isEqual(document.positionAt(typo + "toggeld".length)),
			),
	);
	// TypeScript's own errors reach the Python file: `$el` is the <button>.
	const unknownMember = source.indexOf("fooBar");
	const codeOf = (diagnostic) => (typeof diagnostic.code === "object" ? diagnostic.code.value : diagnostic.code);
	await eventually("forwarded TypeScript diagnostic", async () =>
		vscode.languages
			.getDiagnostics(uri)
			.some(
				(diagnostic) =>
					codeOf(diagnostic) === "citry.typescript.ts2339" &&
					diagnostic.source === "Citry (ts)" &&
					diagnostic.severity === vscode.DiagnosticSeverity.Error &&
					diagnostic.range.start.isEqual(document.positionAt(unknownMember)) &&
					diagnostic.range.end.isEqual(document.positionAt(unknownMember + "fooBar".length)),
			),
	);
	// Citry already reports the undeclared event name, so TypeScript does not report it again.
	assert.equal(
		vscode.languages
			.getDiagnostics(uri)
			.some(
				(diagnostic) =>
					String(codeOf(diagnostic)).startsWith("citry.typescript.") &&
					diagnostic.range.contains(document.positionAt(typo + 1)),
			),
		false,
	);
}

async function exerciseStateBindingTarget(folder) {
	const uri = vscode.Uri.joinPath(folder.uri, "state_binding_target.py");
	const key = ":c-query.debounce.300ms";
	const source = [
		"from citry import Component",
		"class InvalidTarget(Component):",
		'    template = """',
		`        <head title="😀" ${key}="refresh"></head>`,
		'    """',
		"",
	].join("\n");
	await vscode.workspace.fs.writeFile(uri, Buffer.from(source));
	const document = await vscode.workspace.openTextDocument(uri);
	await vscode.window.showTextDocument(document);
	const offset = source.indexOf(key);
	const diagnostics = () =>
		vscode.languages
			.getDiagnostics(uri)
			.filter(
				(diagnostic) =>
					(typeof diagnostic.code === "object" ? diagnostic.code.value : diagnostic.code) ===
					"citry.browser.invalid-state-binding-target",
			);
	await eventually("invalid state binding target diagnostic", async () =>
		diagnostics().some(
			(diagnostic) =>
				diagnostic.severity === vscode.DiagnosticSeverity.Error &&
				diagnostic.range.start.isEqual(document.positionAt(offset)) &&
				diagnostic.range.end.isEqual(document.positionAt(offset + key.length)),
		),
	);
	const edit = new vscode.WorkspaceEdit();
	edit.replace(
		uri,
		new vscode.Range(document.positionAt(0), document.positionAt(source.length)),
		source.replace("<head title=", "<input title=").replace("</head>", ""),
	);
	assert.equal(await vscode.workspace.applyEdit(edit), true);
	await eventually("valid input clears state binding target diagnostic", async () => diagnostics().length === 0);
}

module.exports = { exerciseBrowser };
