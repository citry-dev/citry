import { PythonExtension } from "@vscode/python-extension";
import * as vscode from "vscode";
import {
	DidChangeWatchedFilesNotification,
	FileChangeType,
	LanguageClient,
	type LanguageClientOptions,
	type WorkspaceEdit as ProtocolWorkspaceEdit,
	type ServerOptions,
	SettingMonitor,
} from "vscode-languageclient/node";
import { advanceTagCompletionRetrigger } from "./completionRetrigger.js";
import { type EmbeddedLanguage, embeddedLanguageAt, virtualDocumentSource } from "./embedded.js";
import {
	type EmbeddedFormatterInvocation,
	type EmbeddedFormattingParams,
	type EmbeddedFormattingResponse,
	embeddedFormattingDocumentIdentity,
	embeddedFormattingOptions,
	formatEmbeddedDocuments,
	type ProviderTextEdit,
} from "./embeddedFormatting.js";
import {
	applyVersionedEdit,
	formattingFailureDelivery,
	prepareVersionedEdit,
	sourceFormattingAction,
	workspaceOwnsDocument,
} from "./formatting.js";

const protocolVersion = 1;
const statusMethod = "citry/status";
const reloadMethod = "citry/reload";
const formatComponentAssetsMethod = "citry/formatComponentAssets";
const formatEmbeddedMethod = "citry/formatEmbedded";
const embeddedScheme = "citry-embedded";
const embeddedFormattingScheme = "citry-embedded-format";
const sourceFormatKind = vscode.CodeActionKind.Source.append("format.citry");

interface ProjectStatus {
	protocol_version: number;
	server_version: string;
	interpreter: string;
	workspace: string;
	app: string | null;
	mode: "registry" | "syntax-only" | "unavailable";
	registry_ready: boolean;
	citry_version: string | null;
	catalog_schema_version: number | null;
	python_expression_provider?: string | null;
	embedded_formatting?: {
		version: number;
		languages: string[];
		provider_selection: string;
		provider_identity: string | null;
		provider_version: string | null;
	} | null;
	message: string | null;
}

interface ClientEntry {
	client: LanguageClient;
	disposables: vscode.Disposable[];
	folder: vscode.WorkspaceFolder;
	python: string;
	status?: ProjectStatus;
}

interface FormatDocumentScope {
	kind: "document";
}

interface FormatPositionScope {
	kind: "position";
	position: { line: number; character: number };
}

type FormatScope = FormatDocumentScope | FormatPositionScope;

interface FormatEditResponse {
	kind: "edit";
	edit: ProtocolWorkspaceEdit;
}

interface FormatUnchangedResponse {
	kind: "unchanged";
}

interface FormatRefusedResponse {
	kind: "refused";
	code: string;
	message: string;
	range: { start: { line: number; character: number }; end: { line: number; character: number } } | null;
}

interface FormatMetadata {
	notices?: Array<{ code: string; message: string; regionId?: string | null; language?: string | null }>;
	providers?: string[];
	embeddedFormatting?: {
		version: number;
		languages: string[];
		providerSelection: string;
		providerIdentity: string | null;
		providerVersion: string | null;
	};
}

type FormatResponse = (FormatEditResponse | FormatUnchangedResponse | FormatRefusedResponse) & FormatMetadata;

const clients = new Map<string, ClientEntry>();
let statusBar: vscode.StatusBarItem;
let formatterOutput: vscode.OutputChannel;
let lastQuietFormattingFailure: string | undefined;
const activeEmbeddedFormatting = new Set<string>();
let embeddedFormattingDocuments: EmbeddedFormattingContentProvider;
let pendingTagCompletionRetrigger: { uri: string; offset: number } | undefined;
let pendingTagCompletionDispatch: { uri: string; version: number; position: vscode.Position } | undefined;

export async function activate(context: vscode.ExtensionContext): Promise<void> {
	statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 40);
	statusBar.command = "citry.showStatus";
	statusBar.text = "$(loading~spin) Citry";
	statusBar.tooltip = "Citry language server is starting";
	statusBar.show();
	formatterOutput = vscode.window.createOutputChannel("Citry Formatter");
	embeddedFormattingDocuments = new EmbeddedFormattingContentProvider();
	context.subscriptions.push(statusBar, formatterOutput, embeddedFormattingDocuments);
	context.subscriptions.push(...registerEmbeddedLanguageProviders());
	context.subscriptions.push(
		vscode.workspace.registerTextDocumentContentProvider(embeddedFormattingScheme, embeddedFormattingDocuments),
	);
	context.subscriptions.push(registerSourceFormattingAction());
	context.subscriptions.push(registerStandaloneFormattingProvider());
	context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(handleTagCompletionChange));
	context.subscriptions.push(vscode.window.onDidChangeTextEditorSelection(handleTagCompletionSelection));

	for (const folder of vscode.workspace.workspaceFolders ?? []) {
		await startFolder(folder);
	}
	if ((vscode.workspace.workspaceFolders?.length ?? 0) === 0) {
		setUnavailableStatus("Open a file-backed workspace to start citry-lsp.");
	}

	context.subscriptions.push(
		vscode.workspace.onDidChangeWorkspaceFolders(async (_event) => {
			await restartAll();
		}),
		vscode.workspace.onDidChangeConfiguration(async (event) => {
			if (event.affectsConfiguration("citry.app") || event.affectsConfiguration("citry.python")) {
				await restartAll();
			}
		}),
		vscode.window.onDidChangeActiveTextEditor(() => updateStatusBar()),
		vscode.commands.registerCommand("citry.restartServer", restartAll),
		vscode.commands.registerCommand("citry.showStatus", showStatus),
		vscode.commands.registerCommand("citry.formatAtCursor", formatAtCursor),
		vscode.commands.registerCommand("citry.formatDocument", formatCurrentDocument),
	);

	try {
		const api = await PythonExtension.api();
		context.subscriptions.push(
			api.environments.onDidChangeActiveEnvironmentPath(async () => {
				await restartAll();
			}),
		);
	} catch {
		// An explicit citry.python setting remains available when the adapter fails.
	}
}

export async function deactivate(): Promise<void> {
	await Promise.all([...clients.values()].map((entry) => stopEntry(entry)));
	clients.clear();
}

async function startFolder(folder: vscode.WorkspaceFolder): Promise<void> {
	if (folder.uri.scheme !== "file") {
		return;
	}
	const key = folder.uri.toString();
	if (clients.has(key)) {
		return;
	}
	let python: string;
	try {
		python = await resolvePython(folder);
	} catch (error) {
		setUnavailableStatus(errorMessage(error));
		return;
	}
	const configuration = vscode.workspace.getConfiguration("citry", folder.uri);
	const app = configuration.get<string>("app", "").trim() || null;
	const serverOptions: ServerOptions = {
		command: python,
		args: ["-m", "citry_lsp"],
		options: { cwd: folder.uri.fsPath },
	};
	const documentSelector: LanguageClientOptions["documentSelector"] = [
		{ language: "python", scheme: "file", pattern: { baseUri: folder.uri.toString(), pattern: "**/*.py" } },
		{ language: "citry-html", scheme: "file", pattern: { baseUri: folder.uri.toString(), pattern: "**/*" } },
		{ language: "html", scheme: "file", pattern: { baseUri: folder.uri.toString(), pattern: "**/*" } },
	];
	const ownsDocument = (document: vscode.TextDocument): boolean =>
		workspaceOwnsDocument(key, vscode.workspace.getWorkspaceFolder(document.uri)?.uri.toString());
	const middleware: NonNullable<LanguageClientOptions["middleware"]> = {
		didOpen: (document, next) => (ownsDocument(document) ? next(document) : Promise.resolve()),
		didChange: (event, next) => (ownsDocument(event.document) ? next(event) : Promise.resolve()),
		didClose: (document, next) => (ownsDocument(document) ? next(document) : Promise.resolve()),
		provideCompletionItem: (document, position, context, token, next) =>
			ownsDocument(document) ? next(document, position, context, token) : undefined,
		provideHover: (document, position, token, next) =>
			ownsDocument(document) ? next(document, position, token) : undefined,
		provideDefinition: (document, position, token, next) =>
			ownsDocument(document) ? next(document, position, token) : undefined,
		provideDocumentSymbols: (document, token, next) => (ownsDocument(document) ? next(document, token) : undefined),
	};
	const clientOptions: LanguageClientOptions = {
		documentSelector,
		middleware,
		diagnosticCollectionName: `Citry (${folder.name})`,
		initializationOptions: {
			protocolVersion,
			app,
			standardFormatting: false,
			embeddedFormatting: {
				version: 1,
				languages: ["javascript", "css"],
				providerSelection: "vscode-first-result",
			},
		},
		workspaceFolder: folder,
		outputChannelName: `Citry (${folder.name})`,
		initializationFailedHandler: (error) => {
			setUnavailableStatus(
				`Could not start citry-lsp with ${python}. Install or upgrade citry-lsp in that environment. ${errorMessage(error)}`,
			);
			return false;
		},
	};
	const client = new LanguageClient(`citry-${folder.index}`, `Citry (${folder.name})`, serverOptions, clientOptions);
	const entry: ClientEntry = { client, disposables: [], folder, python };
	clients.set(key, entry);
	entry.disposables.push(
		client.onRequest(formatEmbeddedMethod, (params, token) => handleEmbeddedFormatting(params, token)),
	);
	client.onNotification(statusMethod, (status: ProjectStatus) => {
		entry.status = status;
		updateStatusBar();
	});
	try {
		await client.start();
		entry.disposables.push(new SettingMonitor(client, "citry.trace.server").start());
		entry.status = await client.sendRequest<ProjectStatus>(statusMethod, {});
		entry.disposables.push(...watchPythonFiles(entry));
	} catch (error) {
		clients.delete(key);
		await stopEntry(entry);
		setUnavailableStatus(
			`Could not start citry-lsp with ${python}. Install citry-lsp in the selected project environment. ${errorMessage(error)}`,
		);
		return;
	}
	updateStatusBar();
}

function handleTagCompletionChange(event: vscode.TextDocumentChangeEvent): void {
	const document = event.document;
	const editor = vscode.window.activeTextEditor;
	const uri = document.uri.toString();
	pendingTagCompletionDispatch = undefined;
	const supportedLanguage =
		document.languageId === "python" || document.languageId === "citry-html" || document.languageId === "html";
	const entry = entryForUri(document.uri);
	if (
		editor?.document.uri.toString() !== uri ||
		editor.selections.length !== 1 ||
		event.contentChanges.length !== 1 ||
		!supportedLanguage ||
		entry === undefined ||
		!entry.client.isRunning()
	) {
		pendingTagCompletionRetrigger = undefined;
		return;
	}

	const contentChange = event.contentChanges[0];
	if (contentChange === undefined) {
		pendingTagCompletionRetrigger = undefined;
		return;
	}
	const source = document.getText();
	const priorOffset = pendingTagCompletionRetrigger?.uri === uri ? pendingTagCompletionRetrigger.offset : undefined;
	const decision = advanceTagCompletionRetrigger(
		source,
		{
			startOffset: contentChange.rangeOffset,
			removedLength: contentChange.rangeLength,
			insertedText: contentChange.text,
			history: event.reason !== undefined,
		},
		priorOffset,
	);
	pendingTagCompletionRetrigger = undefined;
	const decisionOffset = decision.pendingOffset ?? decision.triggerOffset;
	if (decisionOffset === undefined) {
		return;
	}
	// The LSP owns Python template-region proof; duplicating its AST rules here
	// would exclude valid raw, ordinary, or concatenated template literals.
	if (decision.pendingOffset !== undefined) {
		pendingTagCompletionRetrigger = { uri, offset: decision.pendingOffset };
	}
	if (decision.triggerOffset === undefined) {
		return;
	}

	const expectedVersion = document.version;
	const expectedPosition = document.positionAt(decision.triggerOffset);
	const dispatch = { uri, version: expectedVersion, position: expectedPosition };
	pendingTagCompletionDispatch = dispatch;
	setTimeout(() => dispatchTagCompletion(dispatch), 0);
	setTimeout(() => {
		if (pendingTagCompletionDispatch === dispatch) {
			pendingTagCompletionDispatch = undefined;
		}
	}, 250);
}

function handleTagCompletionSelection(event: vscode.TextEditorSelectionChangeEvent): void {
	const uri = event.textEditor.document.uri.toString();
	const active = event.selections.length === 1 ? event.selections[0]?.active : undefined;
	if (
		pendingTagCompletionRetrigger !== undefined &&
		(uri !== pendingTagCompletionRetrigger.uri ||
			active === undefined ||
			event.textEditor.document.offsetAt(active) !== pendingTagCompletionRetrigger.offset)
	) {
		pendingTagCompletionRetrigger = undefined;
	}
	const dispatch = pendingTagCompletionDispatch;
	if (dispatch === undefined) {
		return;
	}
	if (
		uri !== dispatch.uri ||
		event.textEditor.document.version !== dispatch.version ||
		active === undefined ||
		!active.isEqual(dispatch.position)
	) {
		pendingTagCompletionDispatch = undefined;
		return;
	}
	dispatchTagCompletion(dispatch);
}

function dispatchTagCompletion(expected: NonNullable<typeof pendingTagCompletionDispatch>): void {
	if (pendingTagCompletionDispatch !== expected) {
		return;
	}
	const activeEditor = vscode.window.activeTextEditor;
	if (
		activeEditor?.document.uri.toString() !== expected.uri ||
		activeEditor.document.version !== expected.version ||
		activeEditor.selections.length !== 1 ||
		!activeEditor.selection.active.isEqual(expected.position) ||
		entryForUri(activeEditor.document.uri)?.client.isRunning() !== true
	) {
		return;
	}
	pendingTagCompletionDispatch = undefined;
	void vscode.commands.executeCommand("editor.action.triggerSuggest").then(undefined, () => undefined);
}

async function stopEntry(entry: ClientEntry): Promise<void> {
	for (const disposable of entry.disposables) {
		disposable.dispose();
	}
	entry.disposables.length = 0;
	if (entry.client.needsStop()) {
		await entry.client.stop();
	}
}

async function restartAll(): Promise<void> {
	const folders = [...(vscode.workspace.workspaceFolders ?? [])];
	await Promise.all([...clients.values()].map((entry) => stopEntry(entry)));
	clients.clear();
	for (const folder of folders) {
		await startFolder(folder);
	}
	updateStatusBar();
}

function watchPythonFiles(entry: ClientEntry): vscode.Disposable[] {
	const watcher = vscode.workspace.createFileSystemWatcher(new vscode.RelativePattern(entry.folder, "**/*.py"));
	const send = (uri: vscode.Uri, type: FileChangeType) => {
		void entry.client.sendNotification(DidChangeWatchedFilesNotification.type, {
			changes: [{ uri: uri.toString(), type }],
		});
	};
	return [
		watcher,
		watcher.onDidCreate((uri) => send(uri, FileChangeType.Created)),
		watcher.onDidChange((uri) => send(uri, FileChangeType.Changed)),
		watcher.onDidDelete((uri) => send(uri, FileChangeType.Deleted)),
	];
}

async function resolvePython(folder: vscode.WorkspaceFolder): Promise<string> {
	const configured = vscode.workspace.getConfiguration("citry", folder.uri).get<string>("python", "").trim();
	if (configured) {
		const workspaceToken = `$${"{workspaceFolder}"}`;
		return configured.replaceAll(workspaceToken, folder.uri.fsPath);
	}
	try {
		const api = await PythonExtension.api();
		await api.ready;
		const selected = api.environments.getActiveEnvironmentPath(folder);
		const resolved = await api.environments.resolveEnvironment(selected);
		if (resolved?.executable.uri !== undefined) {
			return resolved.executable.uri.fsPath;
		}
	} catch (error) {
		throw new Error(
			`The Python extension could not resolve an interpreter. Set citry.python explicitly. ${errorMessage(error)}`,
		);
	}
	throw new Error("The selected Python environment has no executable. Set citry.python explicitly.");
}

async function showStatus(): Promise<void> {
	const entry = activeEntry() ?? [...clients.values()][0];
	if (entry === undefined) {
		await vscode.window.showWarningMessage("Citry language server is not running for this workspace.");
		return;
	}
	let status = entry.status;
	try {
		status = await entry.client.sendRequest<ProjectStatus>(statusMethod, {});
		entry.status = status;
	} catch {
		// Show the last reported status if the process is currently restarting.
	}
	if (status === undefined) {
		await vscode.window.showWarningMessage(`Citry language server is starting for ${entry.folder.name}.`);
		return;
	}
	const detail = [
		`Workspace: ${status.workspace}`,
		`Interpreter: ${status.interpreter}`,
		`App: ${status.app ?? "not configured"}`,
		`Mode: ${status.mode}`,
		`Citry: ${status.citry_version ?? "unavailable"}`,
		`Python expressions: ${status.python_expression_provider ?? "unavailable"}`,
		status.embedded_formatting === undefined || status.embedded_formatting === null
			? "Embedded JavaScript/CSS: unavailable"
			: `Embedded JavaScript/CSS: ${status.embedded_formatting.provider_selection} (provider identity unknown)`,
		`Server: ${status.server_version} (protocol ${status.protocol_version})`,
		status.message,
	]
		.filter((value): value is string => Boolean(value))
		.join("\n");
	const choice = await vscode.window.showInformationMessage(detail, { modal: true }, "Reload registry");
	if (choice === "Reload registry") {
		entry.status = await entry.client.sendRequest<ProjectStatus>(reloadMethod, {});
		updateStatusBar();
	}
}

function activeEntry(): ClientEntry | undefined {
	const uri = vscode.window.activeTextEditor?.document.uri;
	if (uri === undefined) {
		return undefined;
	}
	const folder = vscode.workspace.getWorkspaceFolder(uri);
	return folder === undefined ? undefined : clients.get(folder.uri.toString());
}

function entryForUri(uri: vscode.Uri): ClientEntry | undefined {
	const folder = vscode.workspace.getWorkspaceFolder(uri);
	return folder === undefined ? undefined : clients.get(folder.uri.toString());
}

async function formatAtCursor(): Promise<void> {
	const editor = vscode.window.activeTextEditor;
	if (editor === undefined) {
		await vscode.window.showWarningMessage("Open a Python or Citry template document to format it.");
		return;
	}
	const scope: FormatScope =
		editor.document.languageId === "python"
			? {
					kind: "position",
					position: { line: editor.selection.active.line, character: editor.selection.active.character },
				}
			: { kind: "document" };
	await applyCitryFormatting(editor.document, scope, false);
}

async function formatCurrentDocument(resource?: vscode.Uri, quiet = false): Promise<void> {
	const document = await resolveFormatDocument(resource);
	if (document === undefined) {
		await reportFormattingFailure("Open a Python or Citry template document to format it.", quiet);
		return;
	}
	await applyCitryFormatting(document, { kind: "document" }, quiet);
}

async function resolveFormatDocument(resource?: vscode.Uri): Promise<vscode.TextDocument | undefined> {
	if (resource !== undefined) {
		return vscode.workspace.openTextDocument(resource);
	}
	return vscode.window.activeTextEditor?.document;
}

async function applyCitryFormatting(document: vscode.TextDocument, scope: FormatScope, quiet: boolean): Promise<void> {
	if (document.languageId !== "python" && document.languageId !== "citry-html" && document.languageId !== "html") {
		await reportFormattingFailure("Citry formatting is available for Python and Citry Template documents.", quiet);
		return;
	}
	const entry = entryForUri(document.uri);
	if (entry === undefined || !entry.client.isRunning()) {
		await reportFormattingFailure("The Citry language server is not running for this document.", quiet);
		return;
	}
	const version = document.version;
	try {
		const response = await entry.client.sendRequest<FormatResponse>(formatComponentAssetsMethod, {
			textDocument: { uri: document.uri.toString(), version },
			scope,
		});
		recordFormatMetadata(response);
		if (response.kind === "refused") {
			await reportFormattingFailure(`${response.code}: ${response.message}`, quiet);
			return;
		}
		if (response.kind === "unchanged") {
			lastQuietFormattingFailure = undefined;
			return;
		}
		const outcome = await applyVersionedEdit({
			requestedVersion: version,
			currentVersion: () => document.version,
			protocolEdit: response.edit,
			validate: (edit) => entry.client.validateWorkspaceEdit(edit),
			convert: (edit) => entry.client.protocol2CodeConverter.asWorkspaceEdit(edit),
			apply: (edit) => vscode.workspace.applyEdit(edit),
		});
		if (outcome === "stale") {
			await reportFormattingFailure(
				"citry.format.stale-document: the document changed before formatting applied",
				quiet,
			);
			return;
		}
		if (outcome === "invalid") {
			await reportFormattingFailure("Citry returned an invalid formatter edit.", quiet);
			return;
		}
		if (outcome === "not-applied") {
			await reportFormattingFailure("Citry could not apply the formatter edit.", quiet);
			return;
		}
		lastQuietFormattingFailure = undefined;
	} catch (error) {
		await reportFormattingFailure(`Citry formatting failed: ${errorMessage(error)}`, quiet);
	}
}

async function reportFormattingFailure(message: string, quiet: boolean): Promise<void> {
	const delivery = formattingFailureDelivery(message, quiet, lastQuietFormattingFailure);
	lastQuietFormattingFailure = delivery.nextQuietFailure;
	if (delivery.appendToOutput) {
		formatterOutput.appendLine(message);
	}
	if (delivery.showWarning) {
		await vscode.window.showWarningMessage(message);
	}
}

function recordFormatMetadata(response: FormatMetadata): void {
	for (const notice of response.notices ?? []) {
		const region = notice.regionId === undefined || notice.regionId === null ? "" : ` (${notice.regionId})`;
		formatterOutput.appendLine(`${notice.code}${region}: ${notice.message}`);
	}
}

async function handleEmbeddedFormatting(
	params: EmbeddedFormattingParams,
	token: vscode.CancellationToken,
): Promise<EmbeddedFormattingResponse> {
	const key = `${params.textDocument?.uri ?? ""}\u0000${String(params.textDocument?.version)}\u0000${params.planId ?? ""}`;
	if (activeEmbeddedFormatting.has(key)) {
		throw new Error("citry.format.provider-invalid: recursive embedded formatting request refused");
	}
	activeEmbeddedFormatting.add(key);
	const formattingSession = embeddedFormattingDocuments.createSession();
	const cancellation = new AbortController();
	if (token.isCancellationRequested) {
		cancellation.abort();
	}
	const cancellationSubscription = token.onCancellationRequested(() => cancellation.abort());
	try {
		const response = await formatEmbeddedDocuments(params, {
			currentDocumentVersion: currentDocumentVersion,
			executeFormatter: (invocation) => embeddedFormattingDocuments.execute(invocation, params, formattingSession),
			cancellationSignal: cancellation.signal,
		});
		for (const result of response.results) {
			const language = params.regions.find((region) => region.id === result.regionId)?.language ?? "embedded";
			const detail = result.message === undefined ? "" : `: ${result.message}`;
			formatterOutput.appendLine(
				`${language} ${result.regionId}: ${result.status} via vscode-first-result (provider identity unavailable)${detail}`,
			);
		}
		return response;
	} finally {
		cancellationSubscription.dispose();
		activeEmbeddedFormatting.delete(key);
	}
}

function currentDocumentVersion(uri: string): number | undefined {
	return vscode.workspace.textDocuments.find((document) => document.uri.toString() === uri)?.version;
}

function registerStandaloneFormattingProvider(): vscode.Disposable {
	return vscode.languages.registerDocumentFormattingEditProvider([{ language: "citry-html", scheme: "file" }], {
		async provideDocumentFormattingEdits(document, _options, token) {
			const quiet = true;
			const entry = entryForUri(document.uri);
			if (entry === undefined || !entry.client.isRunning()) {
				await reportFormattingFailure("The Citry language server is not running for this document.", quiet);
				return undefined;
			}
			const version = document.version;
			try {
				const response = await entry.client.sendRequest<FormatResponse>(
					formatComponentAssetsMethod,
					{
						textDocument: { uri: document.uri.toString(), version },
						scope: { kind: "document" },
					},
					token,
				);
				recordFormatMetadata(response);
				if (response.kind === "refused") {
					await reportFormattingFailure(`${response.code}: ${response.message}`, quiet);
					return undefined;
				}
				if (response.kind === "unchanged") {
					lastQuietFormattingFailure = undefined;
					return [];
				}
				const prepared = await prepareVersionedEdit({
					requestedVersion: version,
					currentVersion: () => document.version,
					protocolEdit: response.edit,
					validate: (edit) => entry.client.validateWorkspaceEdit(edit),
					convert: (edit) => entry.client.protocol2CodeConverter.asWorkspaceEdit(edit),
				});
				if (prepared.kind === "stale") {
					await reportFormattingFailure(
						"citry.format.stale-document: the document changed before formatting applied",
						quiet,
					);
					return undefined;
				}
				if (prepared.kind === "invalid") {
					await reportFormattingFailure("Citry returned an invalid formatter edit.", quiet);
					return undefined;
				}
				lastQuietFormattingFailure = undefined;
				return prepared.edit.get(document.uri);
			} catch (error) {
				await reportFormattingFailure(`Citry formatting failed: ${errorMessage(error)}`, quiet);
				return undefined;
			}
		},
	});
}

function registerSourceFormattingAction(): vscode.Disposable {
	return vscode.languages.registerCodeActionsProvider(
		[{ language: "python", scheme: "file" }],
		{
			provideCodeActions(document, _range, context) {
				if (context.only !== undefined && !context.only.contains(sourceFormatKind)) {
					return [];
				}
				const descriptor = sourceFormattingAction(document.uri);
				const action = new vscode.CodeAction(descriptor.title, sourceFormatKind);
				action.command = {
					command: descriptor.command,
					title: descriptor.title,
					arguments: descriptor.arguments,
				};
				action.isPreferred = descriptor.isPreferred;
				return [action];
			},
		},
		{ providedCodeActionKinds: [sourceFormatKind] },
	);
}

function updateStatusBar(): void {
	const entry = activeEntry() ?? [...clients.values()][0];
	if (entry?.status === undefined) {
		if (clients.size > 0) {
			statusBar.text = "$(loading~spin) Citry";
			statusBar.tooltip = "Citry language server is starting";
		}
		return;
	}
	const status = entry.status;
	statusBar.text = status.mode === "registry" ? "$(check) Citry" : "$(warning) Citry: syntax only";
	statusBar.tooltip = status.message ?? `${status.app ?? "No app"} with ${status.interpreter}`;
}

function setUnavailableStatus(message: string): void {
	statusBar.text = "$(error) Citry unavailable";
	statusBar.tooltip = message;
}

function errorMessage(error: unknown): string {
	return error instanceof Error ? error.message : String(error);
}

class EmbeddedContentProvider implements vscode.TextDocumentContentProvider {
	provideTextDocumentContent(uri: vscode.Uri): string {
		const parameters = new URLSearchParams(uri.query);
		const sourceValue = parameters.get("source");
		const language = embeddedLanguageFromAuthority(uri.authority);
		if (sourceValue === null || language === undefined) {
			return "";
		}
		const sourceUri = vscode.Uri.parse(sourceValue);
		const document = vscode.workspace.textDocuments.find(
			(candidate) => candidate.uri.toString() === sourceUri.toString(),
		);
		return document === undefined ? "" : virtualDocumentSource(document.getText(), document.languageId, language);
	}
}

class EmbeddedFormattingContentProvider implements vscode.TextDocumentContentProvider, vscode.Disposable {
	private readonly sources = new Map<string, string>();
	private readonly changes = new vscode.EventEmitter<vscode.Uri>();
	private nextSession = 0;
	readonly onDidChange = this.changes.event;

	createSession(): string {
		this.nextSession += 1;
		return String(this.nextSession);
	}

	dispose(): void {
		this.changes.dispose();
	}

	provideTextDocumentContent(uri: vscode.Uri): string {
		return this.sources.get(uri.toString()) ?? "";
	}

	async execute(
		invocation: EmbeddedFormatterInvocation,
		params: EmbeddedFormattingParams,
		session: string,
	): Promise<readonly ProviderTextEdit[] | undefined> {
		if (invocation.signal.aborted) {
			throw new Error("embedded formatter invocation was cancelled");
		}
		const identity = embeddedFormattingDocumentIdentity(params, invocation.region, session);
		const uri = vscode.Uri.from({
			scheme: embeddedFormattingScheme,
			...identity,
		});
		const key = uri.toString();
		const discardCancelledSource = (): void => {
			this.sources.delete(key);
		};
		invocation.signal.addEventListener("abort", discardCancelledSource, { once: true });
		try {
			let document = await this.openDocument(uri, invocation.source, invocation.signal);
			if (invocation.signal.aborted) {
				throw new Error("embedded formatter invocation was cancelled");
			}
			if (document.languageId !== invocation.region.language) {
				document = await vscode.languages.setTextDocumentLanguage(document, invocation.region.language);
				if (invocation.signal.aborted) {
					throw new Error("embedded formatter invocation was cancelled");
				}
			}
			const sourceUri = vscode.Uri.parse(params.textDocument.uri);
			const editor = vscode.workspace.getConfiguration("editor", {
				uri: sourceUri,
				languageId: document.languageId,
			});
			const options = embeddedFormattingOptions(editor.get("tabSize"), editor.get("insertSpaces"));
			if (invocation.signal.aborted) {
				throw new Error("embedded formatter invocation was cancelled");
			}
			const result = await vscode.commands.executeCommand<readonly vscode.TextEdit[] | undefined>(
				"vscode.executeFormatDocumentProvider",
				document.uri,
				options,
			);
			return result?.map((edit) => ({
				range: {
					start: { line: edit.range.start.line, character: edit.range.start.character },
					end: { line: edit.range.end.line, character: edit.range.end.character },
				},
				newText: edit.newText,
			}));
		} finally {
			invocation.signal.removeEventListener("abort", discardCancelledSource);
			this.sources.delete(key);
		}
	}

	private async openDocument(uri: vscode.Uri, source: string, signal: AbortSignal): Promise<vscode.TextDocument> {
		const key = uri.toString();
		this.sources.set(key, source);
		let document = await vscode.workspace.openTextDocument(uri);
		if (signal.aborted) {
			throw new Error("embedded formatter invocation was cancelled");
		}
		if (document.getText() === source) {
			return document;
		}
		document = await new Promise<vscode.TextDocument>((resolve, reject) => {
			let documentSubscription: vscode.Disposable | undefined;
			const finish = (value: vscode.TextDocument | Error): void => {
				documentSubscription?.dispose();
				signal.removeEventListener("abort", cancel);
				if (value instanceof Error) {
					reject(value);
				} else {
					resolve(value);
				}
			};
			const cancel = (): void => finish(new Error("embedded formatter invocation was cancelled"));
			documentSubscription = vscode.workspace.onDidChangeTextDocument((event) => {
				if (event.document.uri.toString() === key && event.document.getText() === source) {
					finish(event.document);
				}
			});
			signal.addEventListener("abort", cancel, { once: true });
			if (signal.aborted) {
				cancel();
				return;
			}
			this.changes.fire(uri);
		});
		return document;
	}
}

function registerEmbeddedLanguageProviders(): vscode.Disposable[] {
	const selector: vscode.DocumentSelector = [{ language: "python" }, { language: "citry-html" }];
	const contentProvider = vscode.workspace.registerTextDocumentContentProvider(
		embeddedScheme,
		new EmbeddedContentProvider(),
	);
	const completions = vscode.languages.registerCompletionItemProvider(
		selector,
		{
			async provideCompletionItems(document, position, token) {
				const request = embeddedRequest(document, position);
				if (request === undefined || token.isCancellationRequested) {
					return undefined;
				}
				try {
					const result = await vscode.commands.executeCommand<vscode.CompletionList>(
						"vscode.executeCompletionItemProvider",
						request.virtualUri,
						position,
						undefined,
						50,
					);
					return token.isCancellationRequested ? undefined : result;
				} catch {
					return undefined;
				}
			},
		},
		"<",
		'"',
		"'",
		"=",
		"/",
		"-",
		":",
		".",
		"@",
		" ",
	);
	const hovers = vscode.languages.registerHoverProvider(selector, {
		async provideHover(document, position, token) {
			const request = embeddedRequest(document, position);
			if (request === undefined || token.isCancellationRequested) {
				return undefined;
			}
			try {
				const results = await vscode.commands.executeCommand<vscode.Hover[]>(
					"vscode.executeHoverProvider",
					request.virtualUri,
					position,
				);
				if (token.isCancellationRequested || results === undefined || results.length === 0) {
					return undefined;
				}
				return new vscode.Hover(
					results.flatMap((hover) => hover.contents),
					results.find((hover) => hover.range !== undefined)?.range,
				);
			} catch {
				return undefined;
			}
		},
	});
	const definitions = vscode.languages.registerDefinitionProvider(selector, {
		async provideDefinition(document, position, token) {
			const request = embeddedRequest(document, position);
			if (request === undefined || token.isCancellationRequested) {
				return undefined;
			}
			try {
				const results = await vscode.commands.executeCommand<vscode.Location[] | vscode.LocationLink[]>(
					"vscode.executeDefinitionProvider",
					request.virtualUri,
					position,
				);
				if (token.isCancellationRequested || results === undefined) {
					return undefined;
				}
				if (results.every(isLocationLink)) {
					return results.map((result) => mapEmbeddedDefinitionLink(result, request));
				}
				return results
					.filter((result): result is vscode.Location => !isLocationLink(result))
					.map((result) => mapEmbeddedLocation(result, request));
			} catch {
				return undefined;
			}
		},
	});
	return [contentProvider, completions, hovers, definitions];
}

interface EmbeddedRequest {
	virtualUri: vscode.Uri;
	sourceUri: vscode.Uri;
}

function embeddedRequest(document: vscode.TextDocument, position: vscode.Position): EmbeddedRequest | undefined {
	const language = embeddedLanguageAt(document.getText(), document.languageId, document.offsetAt(position));
	if (language === undefined) {
		return undefined;
	}
	const parameters = new URLSearchParams({
		source: document.uri.toString(),
		version: String(document.version),
	});
	return {
		sourceUri: document.uri,
		virtualUri: vscode.Uri.from({
			scheme: embeddedScheme,
			authority: language,
			path: `/document.${embeddedExtension(language)}`,
			query: parameters.toString(),
		}),
	};
}

function mapEmbeddedDefinitionLink(definition: vscode.LocationLink, request: EmbeddedRequest): vscode.LocationLink {
	return definition.targetUri.toString() === request.virtualUri.toString()
		? { ...definition, targetUri: request.sourceUri }
		: definition;
}

function mapEmbeddedLocation(definition: vscode.Location, request: EmbeddedRequest): vscode.Location {
	return definition.uri.toString() === request.virtualUri.toString()
		? new vscode.Location(request.sourceUri, definition.range)
		: definition;
}

function isLocationLink(definition: vscode.Location | vscode.LocationLink): definition is vscode.LocationLink {
	return "targetUri" in definition;
}

function embeddedLanguageFromAuthority(value: string): EmbeddedLanguage | undefined {
	return value === "html" || value === "javascript" || value === "css" ? value : undefined;
}

function embeddedExtension(language: EmbeddedLanguage): string {
	return language === "html" ? "html" : language === "javascript" ? "js" : "css";
}
