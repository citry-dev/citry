import { execFile } from "node:child_process";
import path from "node:path";
import { PythonExtension } from "@vscode/python-extension";
import * as prettierBabel from "prettier/plugins/babel";
import * as prettierEstree from "prettier/plugins/estree";
import * as prettierPostcss from "prettier/plugins/postcss";
import * as prettier from "prettier/standalone";
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
import { browserProjectionCandidateAt } from "./browserRouting.js";
import {
	RestartCoordinator,
	stopLanguageClient,
	supportsLanguageServerVersion,
	WatchedFileChangeBatcher,
} from "./clientLifecycle.js";
import { advanceExpressionCompletionRetrigger, advanceTagCompletionRetrigger } from "./completionRetrigger.js";
import { FORMAT_PROVIDER_INVALID, FORMAT_STALE_DOCUMENT } from "./diagnosticCatalog.js";
import {
	type EmbeddedLanguage,
	embeddedLanguageAt,
	virtualDocumentSource,
	virtualDocumentSourceAt,
} from "./embedded.js";
import {
	type EmbeddedFormatterInvocation,
	type EmbeddedFormattingParams,
	type EmbeddedFormattingResponse,
	embeddedFormattingDocumentIdentity,
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
import {
	type HtmlProjectionCandidate,
	htmlProjectionCandidateRangeAt,
	nativeDynamicAttributeHoverProjection,
	projectNativeHtmlAttributes,
} from "./nativeHtmlAttributes.js";
import {
	delegatedCompletionResolveCount,
	delegatedProviderTimeoutMs,
	linearlyMappedProjectionPosition,
	projectionTimeoutMs,
	virtualDocumentTimeoutMs,
	withTimeout,
} from "./providerPipeline.js";
import { resolveWorkspacePath, sameWorkspacePath } from "./workspaceConfiguration.js";

const protocolVersion = 1;
const statusMethod = "citry/status";
const reloadMethod = "citry/reload";
const browserProjectionMethod = "citry/browserProjection";
const htmlProjectionMethod = "citry/htmlProjection";
const formatComponentAssetsMethod = "citry/formatComponentAssets";
const formatEmbeddedMethod = "citry/formatEmbedded";
const embeddedScheme = "citry-embedded";
const browserScheme = "citry-browser";
const embeddedFormattingScheme = "citry-embedded-format";
const prettierExtensionId = "esbenp.prettier-vscode";
const prettierCodeActionKind = vscode.CodeActionKind.SourceFixAll.append("prettier");
const nativeHtmlAttributeHoverProjection = "native-html-attribute-hover";
const sourceFormatKind = vscode.CodeActionKind.Source.append("format.citry");

interface ProjectStatus {
	protocol_version: number;
	server_version: string;
	interpreter: string;
	workspace: string;
	app: string | null;
	environment_file?: string | null;
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
	environmentFile: string | null;
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

interface ProviderProjectionResponse {
	source: string;
	position: { line: number; character: number };
	sourceRange: {
		start: { line: number; character: number };
		end: { line: number; character: number };
	};
	virtualRange: {
		start: { line: number; character: number };
		end: { line: number; character: number };
	};
}

interface BrowserProjectionResponse extends ProviderProjectionResponse {
	ownedRootNames: string[];
	citryOwnsPosition: boolean;
}

type FormatResponse = (FormatEditResponse | FormatUnchangedResponse | FormatRefusedResponse) & FormatMetadata;

const clients = new Map<string, ClientEntry>();
const restartCoordinator = new RestartCoordinator(restartAllOnce);
let statusBar: vscode.StatusBarItem;
let formatterOutput: vscode.OutputChannel;
let performanceOutput: vscode.OutputChannel;
let lastQuietFormattingFailure: string | undefined;
const activeEmbeddedFormatting = new Set<string>();
const reportedServerSetupFailures = new Set<string>();
const browserProjectionResponses = new Map<string, BrowserProjectionResponse | null>();
const htmlProjectionResponses = new Map<string, ProviderProjectionResponse | null>();
let projectionGeneration = 0;
let embeddedDocuments: EmbeddedContentProvider;
let embeddedFormattingDocuments: EmbeddedFormattingContentProvider;
let browserDocuments: BrowserContentProvider;
let pendingCompletionRetrigger: { uri: string; offset: number } | undefined;
let pendingCompletionDispatch: { uri: string; version: number; position: vscode.Position } | undefined;
let nextPerformanceRequest = 0;

function clearProjectionResponses(): void {
	projectionGeneration += 1;
	browserProjectionResponses.clear();
	htmlProjectionResponses.clear();
}

type ProviderOperation = "completion" | "hover" | "definition";

class ProviderTrace {
	private readonly started = performance.now();
	private readonly stages: Array<{ name: string; durationMs: number; outcome: string }> = [];
	private finished = false;

	constructor(
		private readonly enabled: boolean,
		private readonly request: number,
		private readonly route: "browser" | "html",
		private readonly operation: ProviderOperation,
		private readonly document: vscode.TextDocument,
		private readonly position: vscode.Position,
	) {}

	async stage<T>(name: string, action: () => Promise<T>): Promise<T> {
		const started = performance.now();
		try {
			const value = await action();
			this.stages.push({ name, durationMs: performance.now() - started, outcome: "ok" });
			return value;
		} catch (error) {
			this.stages.push({
				name,
				durationMs: performance.now() - started,
				outcome: error instanceof Error ? error.name : "error",
			});
			throw error;
		}
	}

	measure<T>(name: string, action: () => T): T {
		const started = performance.now();
		try {
			const value = action();
			this.stages.push({ name, durationMs: performance.now() - started, outcome: "ok" });
			return value;
		} catch (error) {
			this.stages.push({
				name,
				durationMs: performance.now() - started,
				outcome: error instanceof Error ? error.name : "error",
			});
			throw error;
		}
	}

	finish(outcome: string): void {
		if (!this.enabled || this.finished) {
			return;
		}
		this.finished = true;
		performanceOutput.appendLine(
			JSON.stringify({
				kind: "citry.provider-timing",
				request: this.request,
				route: this.route,
				operation: this.operation,
				uri: this.document.uri.toString(),
				version: this.document.version,
				position: { line: this.position.line, character: this.position.character },
				outcome,
				totalMs: roundedMilliseconds(performance.now() - this.started),
				stages: this.stages.map((stage) => ({
					...stage,
					durationMs: roundedMilliseconds(stage.durationMs),
				})),
			}),
		);
	}
}

function providerTrace(
	route: "browser" | "html",
	operation: ProviderOperation,
	document: vscode.TextDocument,
	position: vscode.Position,
): ProviderTrace {
	nextPerformanceRequest += 1;
	const enabled = vscode.workspace.getConfiguration("citry", document.uri).get<boolean>("trace.performance", false);
	return new ProviderTrace(enabled, nextPerformanceRequest, route, operation, document, position);
}

function roundedMilliseconds(value: number): number {
	return Math.round(value * 100) / 100;
}

class ProviderCancelledError extends Error {
	constructor() {
		super("Citry provider request was cancelled");
		this.name = "ProviderCancelledError";
	}
}

async function waitForProvider<T>(
	promise: PromiseLike<T>,
	token: vscode.CancellationToken,
	stage: string,
	timeoutMs = delegatedProviderTimeoutMs,
): Promise<T> {
	let cancellation: vscode.Disposable | undefined;
	const cancelled = new Promise<never>((_resolve, reject) => {
		cancellation = token.onCancellationRequested(() => reject(new ProviderCancelledError()));
		if (token.isCancellationRequested) {
			reject(new ProviderCancelledError());
		}
	});
	try {
		return await withTimeout(Promise.race([Promise.resolve(promise), cancelled]), timeoutMs, stage);
	} finally {
		cancellation?.dispose();
	}
}

export async function activate(context: vscode.ExtensionContext): Promise<void> {
	statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 40);
	statusBar.command = "citry.showStatus";
	statusBar.text = "$(loading~spin) Citry";
	statusBar.tooltip = "Citry language server is starting";
	statusBar.show();
	formatterOutput = vscode.window.createOutputChannel("Citry Formatter");
	performanceOutput = vscode.window.createOutputChannel("Citry Performance", { log: true });
	embeddedDocuments = new EmbeddedContentProvider();
	embeddedFormattingDocuments = new EmbeddedFormattingContentProvider();
	browserDocuments = new BrowserContentProvider();
	context.subscriptions.push(
		statusBar,
		formatterOutput,
		performanceOutput,
		embeddedDocuments,
		embeddedFormattingDocuments,
		browserDocuments,
	);
	context.subscriptions.push(...registerEmbeddedLanguageProviders());
	context.subscriptions.push(...registerBrowserLanguageProviders());
	context.subscriptions.push(
		vscode.workspace.registerTextDocumentContentProvider(embeddedFormattingScheme, embeddedFormattingDocuments),
	);
	context.subscriptions.push(registerSourceFormattingAction());
	context.subscriptions.push(registerStandaloneFormattingProvider());
	context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(handleCompletionChange));
	context.subscriptions.push(vscode.window.onDidChangeTextEditorSelection(handleCompletionSelection));

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
			if (
				event.affectsConfiguration("citry.app") ||
				event.affectsConfiguration("citry.python") ||
				event.affectsConfiguration("citry.envFile")
			) {
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
	// Let an in-flight restart finish registering its final clients before the
	// extension performs the terminal shutdown.
	await restartCoordinator.settled();
	await Promise.all([...clients.values()].map((entry) => stopEntry(entry)));
	clients.clear();
	// Projection results belong to the client generation that produced them.
	// Drop them during terminal shutdown just as restart and reload already do.
	clearProjectionResponses();
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
	const configuredEnvironmentFile = configuration.get<string>("envFile", "").trim();
	const environmentFile = configuredEnvironmentFile
		? resolveWorkspacePath(configuredEnvironmentFile, folder.uri.fsPath)
		: null;
	try {
		await probeLanguageServer(python, folder.uri.fsPath);
	} catch (error) {
		const message = `Citry could not use citry-lsp with ${python}. ${errorMessage(error)}`;
		setUnavailableStatus(message);
		notifyServerSetupFailure(folder, message);
		return;
	}
	const serverOptions: ServerOptions = {
		command: python,
		args: ["-m", "citry_lsp"],
		options: { cwd: folder.uri.fsPath },
	};
	const documentSelector: LanguageClientOptions["documentSelector"] = [
		{ language: "python", scheme: "file", pattern: { baseUri: folder.uri.toString(), pattern: "**/*.py" } },
		{ language: "citry-html", scheme: "file", pattern: { baseUri: folder.uri.toString(), pattern: "**/*" } },
		{ language: "html", scheme: "file", pattern: { baseUri: folder.uri.toString(), pattern: "**/*" } },
		// Citry accepts any css_file name; the language ID and registry ownership
		// provide the proof instead of a filename convention.
		{ language: "css", scheme: "file", pattern: { baseUri: folder.uri.toString(), pattern: "**/*" } },
		// As with css_file, registry ownership rather than an extension decides
		// whether a JavaScript document belongs to a component.
		{ language: "javascript", scheme: "file", pattern: { baseUri: folder.uri.toString(), pattern: "**/*" } },
		{ language: "fluent", scheme: "file", pattern: { baseUri: folder.uri.toString(), pattern: "**/*.ftl" } },
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
		provideReferences: (document, position, context, token, next) =>
			ownsDocument(document) ? next(document, position, context, token) : undefined,
		provideDeclaration: (document, position, token, next) =>
			ownsDocument(document) ? next(document, position, token) : undefined,
		provideTypeDefinition: (document, position, token, next) =>
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
			envFile: environmentFile,
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
	const entry: ClientEntry = { client, disposables: [], environmentFile, folder, python };
	clients.set(key, entry);
	entry.disposables.push(
		client.onRequest(formatEmbeddedMethod, (params, token) => handleEmbeddedFormatting(params, token)),
	);
	client.onNotification(statusMethod, (status: ProjectStatus) => {
		entry.status = status;
		// The authored document version does not change when a Python save
		// replaces registry, schema, event, or browser-projection facts.
		clearProjectionResponses();
		updateStatusBar();
	});
	try {
		await client.start();
		entry.disposables.push(new SettingMonitor(client, "citry.trace.server").start());
		entry.status = await client.sendRequest<ProjectStatus>(statusMethod, {});
		if (environmentFile !== null && entry.status.environment_file === undefined) {
			throw new Error(
				'Configured citry.envFile is not supported by this citry-lsp installation. Upgrade it with `python -m pip install --upgrade "citry-lsp>=0.1,<0.2"`.',
			);
		}
		if (entry.status.environment_file !== undefined && entry.status.environment_file !== null) {
			entry.environmentFile = entry.status.environment_file;
		}
		entry.disposables.push(...watchProjectFiles(entry));
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

async function probeLanguageServer(python: string, cwd: string): Promise<void> {
	const version = await new Promise<string>((resolve, reject) => {
		execFile(
			python,
			["-I", "-c", 'import importlib.metadata; print(importlib.metadata.version("citry-lsp"))'],
			{ cwd, timeout: 10_000, windowsHide: true, maxBuffer: 1024 },
			(error, stdout) => {
				if (error !== null) {
					reject(new Error('Install it in that environment with `python -m pip install "citry-lsp>=0.1,<0.2"`.'));
					return;
				}
				resolve(stdout.trim());
			},
		);
	});
	if (!supportsLanguageServerVersion(version)) {
		throw new Error(`Found citry-lsp ${version || "with no version"}; this extension requires citry-lsp 0.1.x.`);
	}
}

function notifyServerSetupFailure(folder: vscode.WorkspaceFolder, message: string): void {
	const key = `${folder.uri.toString()}\0${message}`;
	if (reportedServerSetupFailures.has(key)) {
		return;
	}
	reportedServerSetupFailures.add(key);
	void vscode.window.showWarningMessage(message, "Open setup guide").then((choice) => {
		if (choice === "Open setup guide") {
			return vscode.env.openExternal(vscode.Uri.parse("https://citry.dev/ide/vscode/"));
		}
		return undefined;
	});
}

function handleCompletionChange(event: vscode.TextDocumentChangeEvent): void {
	const document = event.document;
	const editor = vscode.window.activeTextEditor;
	const uri = document.uri.toString();
	pendingCompletionDispatch = undefined;
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
		pendingCompletionRetrigger = undefined;
		return;
	}

	const contentChange = event.contentChanges[0];
	if (contentChange === undefined) {
		pendingCompletionRetrigger = undefined;
		return;
	}
	const source = document.getText();
	const priorOffset = pendingCompletionRetrigger?.uri === uri ? pendingCompletionRetrigger.offset : undefined;
	const completionChange = {
		startOffset: contentChange.rangeOffset,
		removedLength: contentChange.rangeLength,
		insertedText: contentChange.text,
		history: event.reason !== undefined,
	};
	const tagDecision = advanceTagCompletionRetrigger(source, completionChange, priorOffset);
	const expressionDecision = advanceExpressionCompletionRetrigger(
		source,
		document.languageId,
		completionChange,
		priorOffset,
	);
	const decision =
		tagDecision.pendingOffset !== undefined || tagDecision.triggerOffset !== undefined
			? tagDecision
			: expressionDecision;
	pendingCompletionRetrigger = undefined;
	const decisionOffset = decision.pendingOffset ?? decision.triggerOffset;
	if (decisionOffset === undefined) {
		return;
	}
	// The client scan only makes a completion request timely. The LSP still
	// owns exact region and Python-host proof before returning any item.
	if (decision.pendingOffset !== undefined) {
		pendingCompletionRetrigger = { uri, offset: decision.pendingOffset };
	}
	if (decision.triggerOffset === undefined) {
		return;
	}

	const expectedVersion = document.version;
	const expectedPosition = document.positionAt(decision.triggerOffset);
	const dispatch = { uri, version: expectedVersion, position: expectedPosition };
	pendingCompletionDispatch = dispatch;
	setTimeout(() => dispatchCompletion(dispatch), 0);
	setTimeout(() => {
		if (pendingCompletionDispatch === dispatch) {
			pendingCompletionDispatch = undefined;
		}
	}, 250);
}

function handleCompletionSelection(event: vscode.TextEditorSelectionChangeEvent): void {
	const uri = event.textEditor.document.uri.toString();
	const active = event.selections.length === 1 ? event.selections[0]?.active : undefined;
	if (
		pendingCompletionRetrigger !== undefined &&
		(uri !== pendingCompletionRetrigger.uri ||
			active === undefined ||
			event.textEditor.document.offsetAt(active) !== pendingCompletionRetrigger.offset)
	) {
		pendingCompletionRetrigger = undefined;
	}
	const dispatch = pendingCompletionDispatch;
	if (dispatch === undefined) {
		return;
	}
	if (
		uri !== dispatch.uri ||
		event.textEditor.document.version !== dispatch.version ||
		active === undefined ||
		!active.isEqual(dispatch.position)
	) {
		pendingCompletionDispatch = undefined;
		return;
	}
	dispatchCompletion(dispatch);
}

function dispatchCompletion(expected: NonNullable<typeof pendingCompletionDispatch>): void {
	if (pendingCompletionDispatch !== expected) {
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
	pendingCompletionDispatch = undefined;
	void vscode.commands.executeCommand("editor.action.triggerSuggest").then(undefined, () => undefined);
}

async function stopEntry(entry: ClientEntry): Promise<void> {
	for (const disposable of entry.disposables) {
		disposable.dispose();
	}
	entry.disposables.length = 0;
	await stopLanguageClient(entry.client);
}

async function restartAll(): Promise<void> {
	return restartCoordinator.request();
}

async function restartAllOnce(): Promise<void> {
	const folders = [...(vscode.workspace.workspaceFolders ?? [])];
	clearProjectionResponses();
	await Promise.all([...clients.values()].map((entry) => stopEntry(entry)));
	clients.clear();
	for (const folder of folders) {
		await startFolder(folder);
	}
	updateStatusBar();
}

function watchProjectFiles(entry: ClientEntry): vscode.Disposable[] {
	const pythonWatcher = vscode.workspace.createFileSystemWatcher(new vscode.RelativePattern(entry.folder, "**/*.py"));
	const batcher = new WatchedFileChangeBatcher<FileChangeType>((changes) => {
		void entry.client.sendNotification(DidChangeWatchedFilesNotification.type, {
			changes,
		});
	});
	const collect = (uri: vscode.Uri, type: FileChangeType) => batcher.push(uri.toString(), type);
	const disposables: vscode.Disposable[] = [
		pythonWatcher,
		{ dispose: () => batcher.dispose() },
		pythonWatcher.onDidCreate((uri) => collect(uri, FileChangeType.Created)),
		pythonWatcher.onDidChange((uri) => collect(uri, FileChangeType.Changed)),
		pythonWatcher.onDidDelete((uri) => collect(uri, FileChangeType.Deleted)),
	];
	if (entry.environmentFile === null) {
		return disposables;
	}
	const environmentWatcher = vscode.workspace.createFileSystemWatcher(
		new vscode.RelativePattern(vscode.Uri.file(path.dirname(entry.environmentFile)), "*"),
	);
	const collectEnvironment = (uri: vscode.Uri, type: FileChangeType) => {
		if (entry.environmentFile !== null && sameWorkspacePath(uri.fsPath, entry.environmentFile)) {
			collect(uri, type);
		}
	};
	disposables.push(
		environmentWatcher,
		environmentWatcher.onDidCreate((uri) => collectEnvironment(uri, FileChangeType.Created)),
		environmentWatcher.onDidChange((uri) => collectEnvironment(uri, FileChangeType.Changed)),
		environmentWatcher.onDidDelete((uri) => collectEnvironment(uri, FileChangeType.Deleted)),
	);
	return disposables;
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
		`Environment file: ${status.environment_file ?? "not configured"}`,
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
		clearProjectionResponses();
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
			await reportFormattingFailure(`${FORMAT_STALE_DOCUMENT}: the document changed before formatting applied`, quiet);
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
		throw new Error(`${FORMAT_PROVIDER_INVALID}: recursive embedded formatting request refused`);
	}
	activeEmbeddedFormatting.add(key);
	const cancellation = new AbortController();
	if (token.isCancellationRequested) {
		cancellation.abort();
	}
	const cancellationSubscription = token.onCancellationRequested(() => cancellation.abort());
	try {
		const response = await formatEmbeddedDocuments(params, {
			currentDocumentVersion: currentDocumentVersion,
			executeFormatter: (invocation) => embeddedFormattingDocuments.execute(invocation, params),
			cancellationSignal: cancellation.signal,
		});
		for (const result of response.results) {
			const language = params.regions.find((region) => region.id === result.regionId)?.language ?? "embedded";
			const detail = result.message === undefined ? "" : `: ${result.message}`;
			formatterOutput.appendLine(
				`${language} ${result.regionId}: ${result.status} via vscode-first-result (provider identity is not carried by protocol v1)${detail}`,
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
						`${FORMAT_STALE_DOCUMENT}: the document changed before formatting applied`,
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

class EmbeddedContentProvider implements vscode.TextDocumentContentProvider, vscode.Disposable {
	private readonly changes = new vscode.EventEmitter<vscode.Uri>();
	readonly onDidChange = this.changes.event;

	dispose(): void {
		this.changes.dispose();
	}

	refresh(uri: vscode.Uri): void {
		this.changes.fire(uri);
	}

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
		if (document === undefined) {
			return "";
		}
		const source = virtualDocumentSource(document.getText(), document.languageId, language);
		return language === "html" && parameters.get("projection") === nativeHtmlAttributeHoverProjection
			? projectNativeHtmlAttributes(source).source
			: source;
	}
}

class BrowserContentProvider implements vscode.TextDocumentContentProvider, vscode.Disposable {
	private readonly sources = new Map<string, string>();
	private readonly uriByIdentity = new Map<string, vscode.Uri>();
	private readonly identityByUri = new Map<string, string>();
	private readonly changes = new vscode.EventEmitter<vscode.Uri>();
	private nextSession = 0;
	readonly onDidChange = this.changes.event;

	dispose(): void {
		this.changes.dispose();
		this.sources.clear();
		this.uriByIdentity.clear();
		this.identityByUri.clear();
	}

	provideTextDocumentContent(uri: vscode.Uri): string {
		return this.sources.get(uri.toString()) ?? "";
	}

	refresh(uri: vscode.Uri): void {
		this.changes.fire(uri);
	}

	create(identity: string, source: string, language: "javascript" | "html" = "javascript"): vscode.Uri {
		let uri = this.uriByIdentity.get(identity);
		if (uri === undefined) {
			this.nextSession += 1;
			uri = vscode.Uri.from({
				scheme: browserScheme,
				authority: language,
				path: `/projection-${this.nextSession}.${language === "html" ? "html" : "js"}`,
			});
			this.uriByIdentity.set(identity, uri);
			this.identityByUri.set(uri.toString(), identity);
		}
		const uriKey = uri.toString();
		const changed = this.sources.get(uriKey) !== source;
		this.sources.set(uriKey, source);
		if (changed) {
			this.changes.fire(uri);
		}
		while (this.sources.size > 64) {
			const oldestUri = this.sources.keys().next().value;
			if (oldestUri === undefined) {
				break;
			}
			this.sources.delete(oldestUri);
			const oldestIdentity = this.identityByUri.get(oldestUri);
			if (oldestIdentity !== undefined) {
				this.uriByIdentity.delete(oldestIdentity);
				this.identityByUri.delete(oldestUri);
			}
		}
		return uri;
	}
}

class EmbeddedFormattingContentProvider implements vscode.TextDocumentContentProvider, vscode.Disposable {
	private readonly sources = new Map<string, string>();

	dispose(): void {
		this.sources.clear();
	}

	provideTextDocumentContent(uri: vscode.Uri): string {
		return this.sources.get(uri.toString()) ?? "";
	}

	async execute(
		invocation: EmbeddedFormatterInvocation,
		params: EmbeddedFormattingParams,
	): Promise<readonly ProviderTextEdit[] | undefined> {
		if (invocation.signal.aborted) {
			throw new Error("embedded formatter invocation was cancelled");
		}
		const identity = embeddedFormattingDocumentIdentity(params, invocation.region, invocation.source);
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
			if (invocation.signal.aborted) {
				throw new Error("embedded formatter invocation was cancelled");
			}
			const selectedPrettier = await this.executePrettier(document, editor, invocation.signal);
			const result = selectedPrettier ?? (await this.executeBundledPrettier(document, invocation.signal));
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

	private async executePrettier(
		document: vscode.TextDocument,
		editor: vscode.WorkspaceConfiguration,
		signal: AbortSignal,
	): Promise<readonly vscode.TextEdit[] | null> {
		const prettier = vscode.extensions.getExtension(prettierExtensionId);
		const defaultFormatter = editor.get<string | null>("defaultFormatter");
		if (prettier === undefined || (typeof defaultFormatter === "string" && defaultFormatter !== prettierExtensionId)) {
			return null;
		}
		await prettier.activate();
		if (signal.aborted) {
			throw new Error("embedded formatter invocation was cancelled");
		}
		const documentRange = new vscode.Range(document.positionAt(0), document.positionAt(document.getText().length));
		const actions = await vscode.commands.executeCommand<readonly vscode.CodeAction[] | undefined>(
			"vscode.executeCodeActionProvider",
			document.uri,
			documentRange,
			prettierCodeActionKind.value,
		);
		if (signal.aborted) {
			throw new Error("embedded formatter invocation was cancelled");
		}
		for (const action of actions ?? []) {
			if (action.kind?.value !== prettierCodeActionKind.value) {
				continue;
			}
			return action.edit?.get(document.uri) ?? [];
		}
		return [];
	}

	private async executeBundledPrettier(
		document: vscode.TextDocument,
		signal: AbortSignal,
	): Promise<readonly vscode.TextEdit[]> {
		const source = document.getText();
		const isCss = document.languageId === "css";
		const formatted = await prettier.format(source, {
			parser: isCss ? "css" : "babel",
			plugins: isCss ? [prettierPostcss] : [prettierBabel, prettierEstree],
			tabWidth: 2,
			useTabs: false,
			endOfLine: "auto",
		});
		if (signal.aborted) {
			throw new Error("embedded formatter invocation was cancelled");
		}
		if (formatted === source) {
			return [];
		}
		return [
			vscode.TextEdit.replace(new vscode.Range(document.positionAt(0), document.positionAt(source.length)), formatted),
		];
	}

	private async openDocument(uri: vscode.Uri, source: string, signal: AbortSignal): Promise<vscode.TextDocument> {
		const key = uri.toString();
		this.sources.set(key, source);
		const document = await vscode.workspace.openTextDocument(uri);
		if (signal.aborted) {
			throw new Error("embedded formatter invocation was cancelled");
		}
		if (document.getText() !== source) {
			throw new Error("embedded formatter virtual-document identity returned a stale snapshot");
		}
		return document;
	}
}

interface MappedProviderRequest {
	projection: ProviderProjectionResponse;
	sourceDocument: vscode.TextDocument;
	sourceVersion: number;
	virtualDocument: vscode.TextDocument;
	virtualUri: vscode.Uri;
}

interface BrowserProviderRequest extends MappedProviderRequest {
	projection: BrowserProjectionResponse;
}

interface HtmlProviderRequest extends MappedProviderRequest {
	projectedAttributeRange?: vscode.Range;
	sourceAttributeRange?: vscode.Range;
	providerPosition: vscode.Position;
}

function registerBrowserLanguageProviders(): vscode.Disposable[] {
	const selector: vscode.DocumentSelector = [
		{ language: "python", scheme: "file" },
		{ language: "citry-html", scheme: "file" },
		{ language: "html", scheme: "file" },
		{ language: "javascript", scheme: "file" },
	];
	const contentProvider = vscode.workspace.registerTextDocumentContentProvider(browserScheme, browserDocuments);
	const completions = vscode.languages.registerCompletionItemProvider(
		selector,
		{
			async provideCompletionItems(document, position, token) {
				const trace = providerTrace("browser", "completion", document, position);
				try {
					const candidate = trace.measure("lexical-routing", () =>
						browserProjectionCandidateAt(document.getText(), document.languageId, document.offsetAt(position)),
					);
					if (!candidate) {
						trace.finish("not-candidate");
						return undefined;
					}
					const request = await trace.stage("projection-and-virtual-document", () =>
						browserProviderRequest(document, position, token, trace),
					);
					if (request === undefined || request.projection.citryOwnsPosition) {
						trace.finish(request?.projection.citryOwnsPosition === true ? "citry-owned" : "no-projection");
						return undefined;
					}
					const result = await trace.stage("delegated-provider", () =>
						waitForProvider(
							vscode.commands.executeCommand<vscode.CompletionList>(
								"vscode.executeCompletionItemProvider",
								request.virtualUri,
								new vscode.Position(request.projection.position.line, request.projection.position.character),
								undefined,
								delegatedCompletionResolveCount,
							),
							token,
							"browser-completion",
						),
					);
					if (token.isCancellationRequested || document.version !== request.sourceVersion) {
						trace.finish("stale-or-cancelled");
						return undefined;
					}
					const items = (result?.items ?? [])
						.filter((item) => !request.projection.ownedRootNames.includes(completionLabel(item)))
						.map((item) => mapProviderCompletion(item, request))
						.filter((item): item is vscode.CompletionItem => item !== undefined);
					trace.finish(items.length === 0 ? "no-result" : "result");
					return new vscode.CompletionList(items, result?.isIncomplete ?? false);
				} catch (error) {
					trace.finish(error instanceof Error ? error.name : "error");
					return undefined;
				}
			},
		},
		".",
		" ",
		"(",
		"[",
		"'",
		'"',
		"$",
	);
	const hovers = vscode.languages.registerHoverProvider(selector, {
		async provideHover(document, position, token) {
			const trace = providerTrace("browser", "hover", document, position);
			try {
				const candidate = trace.measure("lexical-routing", () =>
					browserProjectionCandidateAt(document.getText(), document.languageId, document.offsetAt(position)),
				);
				if (!candidate) {
					trace.finish("not-candidate");
					return undefined;
				}
				const request = await trace.stage("projection-and-virtual-document", () =>
					browserProviderRequest(document, position, token, trace),
				);
				if (request === undefined || request.projection.citryOwnsPosition) {
					trace.finish(request?.projection.citryOwnsPosition === true ? "citry-owned" : "no-projection");
					return undefined;
				}
				const results = await trace.stage("delegated-provider", () =>
					waitForProvider(
						vscode.commands.executeCommand<vscode.Hover[]>(
							"vscode.executeHoverProvider",
							request.virtualUri,
							new vscode.Position(request.projection.position.line, request.projection.position.character),
						),
						token,
						"browser-hover",
					),
				);
				if (token.isCancellationRequested || document.version !== request.sourceVersion || results === undefined) {
					trace.finish("stale-or-cancelled");
					return undefined;
				}
				const exact = results
					.map((hover) => {
						const range = hover.range === undefined ? undefined : mapProviderRange(hover.range, request);
						return hover.range === undefined || range !== undefined
							? new vscode.Hover(hover.contents, range)
							: undefined;
					})
					.filter((hover): hover is vscode.Hover => hover !== undefined);
				trace.finish(exact.length === 0 ? "no-result" : "result");
				return exact.length === 0
					? undefined
					: new vscode.Hover(
							exact.flatMap((hover) => hover.contents),
							exact.find((hover) => hover.range !== undefined)?.range,
						);
			} catch (error) {
				trace.finish(error instanceof Error ? error.name : "error");
				return undefined;
			}
		},
	});
	const definitions = vscode.languages.registerDefinitionProvider(selector, {
		async provideDefinition(document, position, token) {
			const trace = providerTrace("browser", "definition", document, position);
			try {
				const candidate = trace.measure("lexical-routing", () =>
					browserProjectionCandidateAt(document.getText(), document.languageId, document.offsetAt(position)),
				);
				if (!candidate) {
					trace.finish("not-candidate");
					return undefined;
				}
				const request = await trace.stage("projection-and-virtual-document", () =>
					browserProviderRequest(document, position, token, trace),
				);
				if (request === undefined || request.projection.citryOwnsPosition) {
					trace.finish(request?.projection.citryOwnsPosition === true ? "citry-owned" : "no-projection");
					return undefined;
				}
				const results = await trace.stage("delegated-provider", () =>
					waitForProvider(
						vscode.commands.executeCommand<vscode.Location[] | vscode.LocationLink[]>(
							"vscode.executeDefinitionProvider",
							request.virtualUri,
							new vscode.Position(request.projection.position.line, request.projection.position.character),
						),
						token,
						"browser-definition",
					),
				);
				if (token.isCancellationRequested || document.version !== request.sourceVersion || results === undefined) {
					trace.finish("stale-or-cancelled");
					return undefined;
				}
				const mapped = results
					.map((result) => mapProviderDefinition(result, request))
					.filter((result): result is vscode.Location => result !== undefined);
				trace.finish(mapped.length === 0 ? "no-result" : "result");
				return mapped;
			} catch (error) {
				trace.finish(error instanceof Error ? error.name : "error");
				return undefined;
			}
		},
	});
	return [contentProvider, completions, hovers, definitions];
}

function completionLabel(item: vscode.CompletionItem): string {
	return typeof item.label === "string" ? item.label : item.label.label;
}

async function browserProviderRequest(
	document: vscode.TextDocument,
	position: vscode.Position,
	token: vscode.CancellationToken,
	trace: ProviderTrace,
): Promise<BrowserProviderRequest | undefined> {
	if (document.uri.scheme !== "file" || token.isCancellationRequested) {
		return undefined;
	}
	const version = document.version;
	const projection = await browserProjectionAt(document, position, token, trace);
	if (projection === null || token.isCancellationRequested || document.version !== version) {
		return undefined;
	}
	const identity = JSON.stringify([
		document.uri.toString(),
		projection.sourceRange.start.line,
		projection.sourceRange.start.character,
	]);
	const virtualUri = browserDocuments.create(identity, projection.source);
	let virtualDocument = await trace.stage("virtual-document-open", () =>
		waitForProvider(
			vscode.workspace.openTextDocument(virtualUri),
			token,
			"browser-virtual-document-open",
			virtualDocumentTimeoutMs,
		),
	);
	if (virtualDocument.getText() !== projection.source) {
		try {
			virtualDocument = await trace.stage("virtual-document-refresh", () =>
				waitForBrowserDocument(virtualUri, projection.source, token),
			);
		} catch {
			return undefined;
		}
	}
	if (virtualDocument.languageId !== "javascript") {
		virtualDocument = await trace.stage("virtual-document-language", () =>
			waitForProvider(
				vscode.languages.setTextDocumentLanguage(virtualDocument, "javascript"),
				token,
				"browser-virtual-document-language",
				virtualDocumentTimeoutMs,
			),
		);
	}
	return token.isCancellationRequested
		? undefined
		: { projection, sourceDocument: document, sourceVersion: version, virtualDocument, virtualUri };
}

async function browserProjectionAt(
	document: vscode.TextDocument,
	position: vscode.Position,
	token: vscode.CancellationToken,
	trace: ProviderTrace,
): Promise<BrowserProjectionResponse | null> {
	const entry = entryForUri(document.uri);
	if (entry === undefined || !entry.client.isRunning()) {
		return null;
	}
	const generation = projectionGeneration;
	const key = JSON.stringify([
		generation,
		document.uri.toString(),
		document.version,
		position.line,
		position.character,
	]);
	if (browserProjectionResponses.has(key)) {
		return browserProjectionResponses.get(key) ?? null;
	}
	const linked = new vscode.CancellationTokenSource();
	const cancellation = token.onCancellationRequested(() => linked.cancel());
	try {
		const response = await trace.stage("projection-rpc", () =>
			withTimeout(
				entry.client.sendRequest<BrowserProjectionResponse | null>(
					browserProjectionMethod,
					{
						textDocument: { uri: document.uri.toString(), version: document.version },
						position: { line: position.line, character: position.character },
					},
					linked.token,
				),
				projectionTimeoutMs,
				"browser-projection",
				() => linked.cancel(),
			),
		);
		if (token.isCancellationRequested || generation !== projectionGeneration) {
			return null;
		}
		if (generation === projectionGeneration) {
			browserProjectionResponses.set(key, response);
			while (browserProjectionResponses.size > 256) {
				const oldest = browserProjectionResponses.keys().next().value;
				if (oldest === undefined) {
					break;
				}
				browserProjectionResponses.delete(oldest);
			}
		}
		return response;
	} catch {
		linked.cancel();
		return null;
	} finally {
		cancellation.dispose();
		linked.dispose();
	}
}

async function waitForBrowserDocument(
	uri: vscode.Uri,
	source: string,
	token: vscode.CancellationToken,
): Promise<vscode.TextDocument> {
	const key = uri.toString();
	return new Promise((resolve, reject) => {
		let documentSubscription: vscode.Disposable | undefined;
		let cancellationSubscription: vscode.Disposable | undefined;
		let timeout: NodeJS.Timeout | undefined;
		const finish = (value: vscode.TextDocument | Error): void => {
			documentSubscription?.dispose();
			cancellationSubscription?.dispose();
			if (timeout !== undefined) {
				clearTimeout(timeout);
			}
			if (value instanceof Error) {
				reject(value);
			} else {
				resolve(value);
			}
		};
		documentSubscription = vscode.workspace.onDidChangeTextDocument((event) => {
			if (event.document.uri.toString() === key && event.document.getText() === source) {
				finish(event.document);
			}
		});
		cancellationSubscription = token.onCancellationRequested(() =>
			finish(new Error("browser provider request was cancelled")),
		);
		if (token.isCancellationRequested) {
			finish(new Error("browser provider request was cancelled"));
			return;
		}
		timeout = setTimeout(
			() => finish(new Error("browser virtual document refresh timed out")),
			virtualDocumentTimeoutMs,
		);
		browserDocuments.refresh(uri);
	});
}

function mapProviderCompletion(
	item: vscode.CompletionItem,
	request: MappedProviderRequest,
): vscode.CompletionItem | undefined {
	const mapped = Object.assign(new vscode.CompletionItem(item.label, item.kind), item);
	if (item.textEdit !== undefined) {
		const range = mapProviderRange(item.textEdit.range, request);
		if (range === undefined) {
			return undefined;
		}
		mapped.textEdit = new vscode.TextEdit(range, item.textEdit.newText);
	}
	if (item.range !== undefined) {
		if (item.range instanceof vscode.Range) {
			const range = mapProviderRange(item.range, request);
			if (range === undefined) {
				return undefined;
			}
			mapped.range = range;
		} else {
			const inserting = mapProviderRange(item.range.inserting, request);
			const replacing = mapProviderRange(item.range.replacing, request);
			if (inserting === undefined || replacing === undefined) {
				return undefined;
			}
			mapped.range = { inserting, replacing };
		}
	}
	// Auto-imports and provider commands target the generated document and
	// must never escape into authored Citry source.
	mapped.additionalTextEdits = undefined;
	mapped.command = undefined;
	return mapped;
}

function mapProviderDefinition(
	result: vscode.Location | vscode.LocationLink,
	request: MappedProviderRequest,
): vscode.Location | undefined {
	if (isLocationLink(result)) {
		const selection = result.targetSelectionRange ?? result.targetRange;
		if (result.targetUri.toString() !== request.virtualUri.toString()) {
			return new vscode.Location(result.targetUri, selection);
		}
		const targetSelectionRange = mapProviderRange(selection, request);
		if (targetSelectionRange === undefined) {
			return undefined;
		}
		return new vscode.Location(request.sourceDocument.uri, targetSelectionRange);
	}
	if (result.uri.toString() !== request.virtualUri.toString()) {
		return result;
	}
	const range = mapProviderRange(result.range, request);
	return range === undefined ? undefined : new vscode.Location(request.sourceDocument.uri, range);
}

function mapProviderRange(range: vscode.Range, request: MappedProviderRequest): vscode.Range | undefined {
	const virtual = protocolRange(request.projection.virtualRange);
	if (!virtual.contains(range.start) || !virtual.contains(range.end)) {
		return undefined;
	}
	const source = protocolRange(request.projection.sourceRange);
	const virtualBase = request.virtualDocument.offsetAt(virtual.start);
	const sourceBase = request.sourceDocument.offsetAt(source.start);
	const start = sourceBase + request.virtualDocument.offsetAt(range.start) - virtualBase;
	const end = sourceBase + request.virtualDocument.offsetAt(range.end) - virtualBase;
	if (start < sourceBase || end < start || end > request.sourceDocument.offsetAt(source.end)) {
		return undefined;
	}
	return new vscode.Range(request.sourceDocument.positionAt(start), request.sourceDocument.positionAt(end));
}

function protocolRange(range: ProviderProjectionResponse["sourceRange"]): vscode.Range {
	return new vscode.Range(
		new vscode.Position(range.start.line, range.start.character),
		new vscode.Position(range.end.line, range.end.character),
	);
}

function registerEmbeddedLanguageProviders(): vscode.Disposable[] {
	const selector: vscode.DocumentSelector = [{ language: "python" }, { language: "citry-html" }];
	const contentProvider = vscode.workspace.registerTextDocumentContentProvider(embeddedScheme, embeddedDocuments);
	const completions = vscode.languages.registerCompletionItemProvider(
		selector,
		{
			async provideCompletionItems(document, position, token) {
				const trace = providerTrace("html", "completion", document, position);
				let htmlRequest: HtmlProviderRequest | null | undefined;
				try {
					htmlRequest = await trace.stage("projection-and-virtual-document", () =>
						htmlProviderRequest(document, position, token, trace),
					);
				} catch (error) {
					trace.finish(error instanceof Error ? error.name : "error");
					return undefined;
				}
				if (htmlRequest === null) {
					trace.finish("no-projection");
					return undefined;
				}
				if (htmlRequest !== undefined) {
					try {
						const result = await trace.stage("delegated-provider", () =>
							waitForProvider(
								vscode.commands.executeCommand<vscode.CompletionList>(
									"vscode.executeCompletionItemProvider",
									htmlRequest.virtualUri,
									htmlRequest.providerPosition,
									undefined,
									delegatedCompletionResolveCount,
								),
								token,
								"html-completion",
							),
						);
						if (token.isCancellationRequested || document.version !== htmlRequest.sourceVersion) {
							trace.finish("stale-or-cancelled");
							return undefined;
						}
						const items = (result?.items ?? [])
							.map((item) => mapProviderCompletion(item, htmlRequest))
							.filter((item): item is vscode.CompletionItem => item !== undefined);
						trace.finish(items.length === 0 ? "no-result" : "result");
						return new vscode.CompletionList(items, result?.isIncomplete ?? false);
					} catch {
						trace.finish("provider-error");
						return undefined;
					}
				}
				const request = embeddedRequest(document, position);
				if (request === undefined || token.isCancellationRequested) {
					trace.finish(token.isCancellationRequested ? "cancelled" : "not-embedded");
					return undefined;
				}
				if (await typedBrowserProjectionOwnsRegion(document, position, request, token, trace)) {
					trace.finish("typed-browser-owned");
					return undefined;
				}
				try {
					const prepared = await prepareEmbeddedRequest(document, request, token, trace);
					if (!prepared) {
						trace.finish("virtual-document-unavailable");
						return undefined;
					}
					const result = await trace.stage("delegated-provider", () =>
						waitForProvider(
							vscode.commands.executeCommand<vscode.CompletionList>(
								"vscode.executeCompletionItemProvider",
								request.virtualUri,
								position,
								undefined,
								delegatedCompletionResolveCount,
							),
							token,
							"embedded-completion",
						),
					);
					if (document.version !== request.sourceVersion) {
						trace.finish("stale");
						return undefined;
					}
					trace.finish(result === undefined ? "no-result" : "result");
					return token.isCancellationRequested ? undefined : result;
				} catch {
					trace.finish("provider-error");
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
			const trace = providerTrace("html", "hover", document, position);
			const version = document.version;
			let htmlRequest: HtmlProviderRequest | null | undefined;
			try {
				htmlRequest = await trace.stage("projection-and-virtual-document", () =>
					htmlProviderRequest(document, position, token, trace),
				);
			} catch (error) {
				trace.finish(error instanceof Error ? error.name : "error");
				return undefined;
			}
			if (htmlRequest === null) {
				trace.finish("no-projection");
				return undefined;
			}
			if (htmlRequest !== undefined) {
				try {
					const results = await trace.stage("delegated-provider", () =>
						waitForProvider(
							vscode.commands.executeCommand<vscode.Hover[]>(
								"vscode.executeHoverProvider",
								htmlRequest.virtualUri,
								htmlRequest.providerPosition,
							),
							token,
							"html-hover",
						),
					);
					if (
						token.isCancellationRequested ||
						document.version !== version ||
						results === undefined ||
						results.length === 0
					) {
						trace.finish(token.isCancellationRequested ? "cancelled" : "no-result");
						return undefined;
					}
					if (htmlRequest.projectedAttributeRange !== undefined && htmlRequest.sourceAttributeRange !== undefined) {
						const projectedAttributeRange = htmlRequest.projectedAttributeRange;
						const exact = results.filter(
							(hover) => hover.range !== undefined && sameRange(hover.range, projectedAttributeRange),
						);
						trace.finish(exact.length === 0 ? "no-result" : "result");
						return exact.length === 0
							? undefined
							: new vscode.Hover(
									exact.flatMap((hover) => hover.contents),
									htmlRequest.sourceAttributeRange,
								);
					}
					const mapped = results
						.map((hover) => {
							const range = hover.range === undefined ? undefined : mapProviderRange(hover.range, htmlRequest);
							return hover.range === undefined || range !== undefined
								? new vscode.Hover(hover.contents, range)
								: undefined;
						})
						.filter((hover): hover is vscode.Hover => hover !== undefined);
					trace.finish(mapped.length === 0 ? "no-result" : "result");
					return mapped.length === 0
						? undefined
						: new vscode.Hover(
								mapped.flatMap((hover) => hover.contents),
								mapped.find((hover) => hover.range !== undefined)?.range,
							);
				} catch {
					trace.finish("provider-error");
					return undefined;
				}
			}
			const request = embeddedHoverRequest(document, position);
			if (request === undefined || token.isCancellationRequested) {
				trace.finish(token.isCancellationRequested ? "cancelled" : "not-embedded");
				return undefined;
			}
			if (await typedBrowserProjectionOwnsRegion(document, position, request, token, trace)) {
				trace.finish("typed-browser-owned");
				return undefined;
			}
			try {
				const prepared = await prepareEmbeddedRequest(document, request, token, trace);
				if (!prepared) {
					trace.finish("virtual-document-unavailable");
					return undefined;
				}
				const results = await trace.stage("delegated-provider", () =>
					waitForProvider(
						vscode.commands.executeCommand<vscode.Hover[]>(
							"vscode.executeHoverProvider",
							request.virtualUri,
							request.providerPosition,
						),
						token,
						"embedded-hover",
					),
				);
				if (
					token.isCancellationRequested ||
					document.version !== version ||
					results === undefined ||
					results.length === 0
				) {
					trace.finish(token.isCancellationRequested ? "cancelled" : "no-result");
					return undefined;
				}
				if (request.projectedAttributeRange !== undefined && request.sourceAttributeRange !== undefined) {
					const projectedAttributeRange = request.projectedAttributeRange;
					const exactResults = results.filter(
						(hover) => hover.range !== undefined && sameRange(hover.range, projectedAttributeRange),
					);
					trace.finish(exactResults.length === 0 ? "no-result" : "result");
					return exactResults.length === 0
						? undefined
						: new vscode.Hover(
								exactResults.flatMap((hover) => hover.contents),
								request.sourceAttributeRange,
							);
				}
				trace.finish("result");
				return new vscode.Hover(
					results.flatMap((hover) => hover.contents),
					results.find((hover) => hover.range !== undefined)?.range,
				);
			} catch {
				trace.finish("provider-error");
				return undefined;
			}
		},
	});
	const definitions = vscode.languages.registerDefinitionProvider(selector, {
		async provideDefinition(document, position, token) {
			const trace = providerTrace("html", "definition", document, position);
			let htmlRequest: HtmlProviderRequest | null | undefined;
			try {
				htmlRequest = await trace.stage("projection-and-virtual-document", () =>
					htmlProviderRequest(document, position, token, trace),
				);
			} catch (error) {
				trace.finish(error instanceof Error ? error.name : "error");
				return undefined;
			}
			if (htmlRequest === null) {
				trace.finish("no-projection");
				return undefined;
			}
			if (htmlRequest !== undefined) {
				try {
					const results = await trace.stage("delegated-provider", () =>
						waitForProvider(
							vscode.commands.executeCommand<vscode.Location[] | vscode.LocationLink[]>(
								"vscode.executeDefinitionProvider",
								htmlRequest.virtualUri,
								htmlRequest.providerPosition,
							),
							token,
							"html-definition",
						),
					);
					if (
						token.isCancellationRequested ||
						document.version !== htmlRequest.sourceVersion ||
						results === undefined
					) {
						trace.finish(token.isCancellationRequested ? "cancelled" : "no-result");
						return undefined;
					}
					const mapped = results
						.map((result) => mapProviderDefinition(result, htmlRequest))
						.filter((result): result is vscode.Location => result !== undefined);
					trace.finish(mapped.length === 0 ? "no-result" : "result");
					return mapped;
				} catch {
					trace.finish("provider-error");
					return undefined;
				}
			}
			const request = embeddedRequest(document, position);
			if (request === undefined || token.isCancellationRequested) {
				trace.finish(token.isCancellationRequested ? "cancelled" : "not-embedded");
				return undefined;
			}
			if (await typedBrowserProjectionOwnsRegion(document, position, request, token, trace)) {
				trace.finish("typed-browser-owned");
				return undefined;
			}
			try {
				const prepared = await prepareEmbeddedRequest(document, request, token, trace);
				if (!prepared) {
					trace.finish("virtual-document-unavailable");
					return undefined;
				}
				const results = await trace.stage("delegated-provider", () =>
					waitForProvider(
						vscode.commands.executeCommand<vscode.Location[] | vscode.LocationLink[]>(
							"vscode.executeDefinitionProvider",
							request.virtualUri,
							position,
						),
						token,
						"embedded-definition",
					),
				);
				if (token.isCancellationRequested || document.version !== request.sourceVersion || results === undefined) {
					trace.finish(token.isCancellationRequested ? "cancelled" : "no-result");
					return undefined;
				}
				if (results.every(isLocationLink)) {
					const mapped = results.map((result) => mapEmbeddedDefinitionLink(result, request));
					trace.finish(mapped.length === 0 ? "no-result" : "result");
					return mapped;
				}
				const mapped = results
					.filter((result): result is vscode.Location => !isLocationLink(result))
					.map((result) => mapEmbeddedLocation(result, request));
				trace.finish(mapped.length === 0 ? "no-result" : "result");
				return mapped;
			} catch {
				trace.finish("provider-error");
				return undefined;
			}
		},
	});
	return [contentProvider, completions, hovers, definitions];
}

async function htmlProviderRequest(
	document: vscode.TextDocument,
	position: vscode.Position,
	token: vscode.CancellationToken,
	trace: ProviderTrace,
): Promise<HtmlProviderRequest | null | undefined> {
	if (document.uri.scheme !== "file" || token.isCancellationRequested) {
		return undefined;
	}
	const source = document.getText();
	const sourceOffset = document.offsetAt(position);
	const htmlSource = virtualDocumentSourceAt(source, document.languageId, "html", sourceOffset);
	if (htmlSource === undefined) {
		return undefined;
	}
	const candidate = htmlProjectionCandidateRangeAt(htmlSource, sourceOffset);
	if (candidate === undefined) {
		return undefined;
	}
	const version = document.version;
	const projection = await htmlProjectionAt(document, position, candidate, token, trace);
	if (projection === null || token.isCancellationRequested || document.version !== version) {
		return null;
	}
	const nativeProjection = projectNativeHtmlAttributes(projection.source);
	const identity = JSON.stringify([
		"html",
		document.uri.toString(),
		projection.sourceRange.start.line,
		projection.sourceRange.start.character,
	]);
	const virtualUri = browserDocuments.create(identity, nativeProjection.source, "html");
	let virtualDocument = await trace.stage("virtual-document-open", () =>
		waitForProvider(
			vscode.workspace.openTextDocument(virtualUri),
			token,
			"html-virtual-document-open",
			virtualDocumentTimeoutMs,
		),
	);
	if (virtualDocument.getText() !== nativeProjection.source) {
		try {
			virtualDocument = await trace.stage("virtual-document-refresh", () =>
				waitForBrowserDocument(virtualUri, nativeProjection.source, token),
			);
		} catch {
			return null;
		}
	}
	if (virtualDocument.languageId !== "html") {
		virtualDocument = await trace.stage("virtual-document-language", () =>
			waitForProvider(
				vscode.languages.setTextDocumentLanguage(virtualDocument, "html"),
				token,
				"html-virtual-document-language",
				virtualDocumentTimeoutMs,
			),
		);
	}
	const projectedPosition = new vscode.Position(projection.position.line, projection.position.character);
	const projectedOffset = virtualDocument.offsetAt(projectedPosition);
	const dynamicAttribute = nativeDynamicAttributeHoverProjection(projection.source, projectedOffset);
	const request: HtmlProviderRequest = {
		projection,
		sourceDocument: document,
		sourceVersion: version,
		virtualDocument,
		virtualUri,
		providerPosition:
			dynamicAttribute === undefined ? projectedPosition : virtualDocument.positionAt(dynamicAttribute.providerOffset),
	};
	if (dynamicAttribute !== undefined) {
		request.projectedAttributeRange = new vscode.Range(
			virtualDocument.positionAt(dynamicAttribute.projectedStart),
			virtualDocument.positionAt(dynamicAttribute.projectedEnd),
		);
		const sourceAttributeRange = mapProviderRange(
			new vscode.Range(
				virtualDocument.positionAt(dynamicAttribute.sourceStart),
				virtualDocument.positionAt(dynamicAttribute.sourceEnd),
			),
			request,
		);
		if (sourceAttributeRange === undefined) {
			return null;
		}
		request.sourceAttributeRange = sourceAttributeRange;
	}
	return token.isCancellationRequested ? null : request;
}

async function htmlProjectionAt(
	document: vscode.TextDocument,
	position: vscode.Position,
	candidate: HtmlProjectionCandidate,
	token: vscode.CancellationToken,
	trace: ProviderTrace,
): Promise<ProviderProjectionResponse | null> {
	const entry = entryForUri(document.uri);
	if (entry === undefined || !entry.client.isRunning()) {
		return null;
	}
	const generation = projectionGeneration;
	const key = JSON.stringify([generation, document.uri.toString(), document.version, candidate.start, candidate.end]);
	if (htmlProjectionResponses.has(key)) {
		const cached = htmlProjectionResponses.get(key);
		if (cached !== undefined && cached !== null) {
			const mapped = projectionAtCachedPosition(document, position, cached);
			if (mapped !== null) {
				return mapped;
			}
		}
	}
	const linked = new vscode.CancellationTokenSource();
	const cancellation = token.onCancellationRequested(() => linked.cancel());
	try {
		const response = await trace.stage("projection-rpc", () =>
			withTimeout(
				entry.client.sendRequest<ProviderProjectionResponse | null>(
					htmlProjectionMethod,
					{
						textDocument: { uri: document.uri.toString(), version: document.version },
						position: { line: position.line, character: position.character },
					},
					linked.token,
				),
				projectionTimeoutMs,
				"html-projection",
				() => linked.cancel(),
			),
		);
		if (token.isCancellationRequested || generation !== projectionGeneration) {
			return null;
		}
		// No-result is cursor-specific at fragment delimiters, so it cannot
		// represent every other cursor covered by the lexical candidate.
		if (response !== null && generation === projectionGeneration) {
			htmlProjectionResponses.set(key, response);
			while (htmlProjectionResponses.size > 256) {
				const oldest = htmlProjectionResponses.keys().next().value;
				if (oldest === undefined) {
					break;
				}
				htmlProjectionResponses.delete(oldest);
			}
		}
		return response;
	} catch {
		linked.cancel();
		return null;
	} finally {
		cancellation.dispose();
		linked.dispose();
	}
}

function projectionAtCachedPosition(
	document: vscode.TextDocument,
	position: vscode.Position,
	projection: ProviderProjectionResponse | null,
): ProviderProjectionResponse | null {
	if (projection === null) {
		return null;
	}
	const sourceStart = document.offsetAt(protocolRange(projection.sourceRange).start);
	const sourceEnd = document.offsetAt(protocolRange(projection.sourceRange).end);
	const sourceOffset = document.offsetAt(position);
	const mappedPosition = linearlyMappedProjectionPosition(
		projection.source,
		sourceOffset,
		sourceStart,
		sourceEnd,
		projection.virtualRange.start,
		projection.virtualRange.end,
	);
	if (mappedPosition === undefined) {
		return null;
	}
	return { ...projection, position: mappedPosition };
}

async function typedBrowserProjectionOwnsRegion(
	document: vscode.TextDocument,
	position: vscode.Position,
	request: EmbeddedRequest,
	token: vscode.CancellationToken,
	trace: ProviderTrace,
): Promise<boolean> {
	if (request.virtualUri.authority !== "javascript") {
		return false;
	}
	const version = document.version;
	if (!browserProjectionCandidateAt(document.getText(), document.languageId, document.offsetAt(position))) {
		return false;
	}
	const projection = await browserProjectionAt(document, position, token, trace);
	return projection !== null && !token.isCancellationRequested && document.version === version;
}

interface EmbeddedRequest {
	virtualUri: vscode.Uri;
	sourceUri: vscode.Uri;
	sourceVersion: number;
	providerPosition: vscode.Position;
	projectedAttributeRange?: vscode.Range;
	sourceAttributeRange?: vscode.Range;
}

function embeddedRequest(document: vscode.TextDocument, position: vscode.Position): EmbeddedRequest | undefined {
	if (document.uri.scheme === embeddedScheme) {
		return undefined;
	}
	const language = embeddedLanguageAt(document.getText(), document.languageId, document.offsetAt(position));
	if (language === undefined) {
		return undefined;
	}
	const parameters = new URLSearchParams({
		source: document.uri.toString(),
	});
	return {
		providerPosition: position,
		sourceUri: document.uri,
		sourceVersion: document.version,
		virtualUri: vscode.Uri.from({
			scheme: embeddedScheme,
			authority: language,
			path: `/document.${embeddedExtension(language)}`,
			query: parameters.toString(),
		}),
	};
}

async function prepareEmbeddedRequest(
	document: vscode.TextDocument,
	request: EmbeddedRequest,
	token: vscode.CancellationToken,
	trace: ProviderTrace,
): Promise<boolean> {
	const version = document.version;
	const language = embeddedLanguageFromAuthority(request.virtualUri.authority);
	if (language === undefined) {
		return false;
	}
	const parameters = new URLSearchParams(request.virtualUri.query);
	let expected = virtualDocumentSource(document.getText(), document.languageId, language);
	if (language === "html" && parameters.get("projection") === nativeHtmlAttributeHoverProjection) {
		expected = projectNativeHtmlAttributes(expected).source;
	}
	let virtualDocument = await trace.stage("virtual-document-open", () =>
		waitForProvider(
			vscode.workspace.openTextDocument(request.virtualUri),
			token,
			"embedded-virtual-document-open",
			virtualDocumentTimeoutMs,
		),
	);
	if (virtualDocument.getText() !== expected) {
		virtualDocument = await trace.stage("virtual-document-refresh", () =>
			waitForEmbeddedDocument(request.virtualUri, expected, token),
		);
	}
	if (virtualDocument.languageId !== language) {
		virtualDocument = await trace.stage("virtual-document-language", () =>
			waitForProvider(
				vscode.languages.setTextDocumentLanguage(virtualDocument, language),
				token,
				"embedded-virtual-document-language",
				virtualDocumentTimeoutMs,
			),
		);
	}
	return !token.isCancellationRequested && document.version === version;
}

async function waitForEmbeddedDocument(
	uri: vscode.Uri,
	source: string,
	token: vscode.CancellationToken,
): Promise<vscode.TextDocument> {
	const key = uri.toString();
	return new Promise((resolve, reject) => {
		let documentSubscription: vscode.Disposable | undefined;
		let cancellationSubscription: vscode.Disposable | undefined;
		let timeout: NodeJS.Timeout | undefined;
		const finish = (value: vscode.TextDocument | Error): void => {
			documentSubscription?.dispose();
			cancellationSubscription?.dispose();
			if (timeout !== undefined) {
				clearTimeout(timeout);
			}
			if (value instanceof Error) {
				reject(value);
			} else {
				resolve(value);
			}
		};
		documentSubscription = vscode.workspace.onDidChangeTextDocument((event) => {
			if (event.document.uri.toString() === key && event.document.getText() === source) {
				finish(event.document);
			}
		});
		cancellationSubscription = token.onCancellationRequested(() => finish(new ProviderCancelledError()));
		if (token.isCancellationRequested) {
			finish(new ProviderCancelledError());
			return;
		}
		timeout = setTimeout(
			() => finish(new Error("embedded virtual document refresh timed out")),
			virtualDocumentTimeoutMs,
		);
		embeddedDocuments.refresh(uri);
	});
}

function embeddedHoverRequest(document: vscode.TextDocument, position: vscode.Position): EmbeddedRequest | undefined {
	const request = embeddedRequest(document, position);
	if (request === undefined || request.virtualUri.authority !== "html") {
		return request;
	}
	const htmlSource = virtualDocumentSource(document.getText(), document.languageId, "html");
	const projection = nativeDynamicAttributeHoverProjection(htmlSource, document.offsetAt(position));
	if (projection === undefined) {
		return request;
	}
	const parameters = new URLSearchParams(request.virtualUri.query);
	parameters.set("projection", nativeHtmlAttributeHoverProjection);
	return {
		...request,
		providerPosition: document.positionAt(projection.providerOffset),
		projectedAttributeRange: new vscode.Range(
			document.positionAt(projection.projectedStart),
			document.positionAt(projection.projectedEnd),
		),
		sourceAttributeRange: new vscode.Range(
			document.positionAt(projection.sourceStart),
			document.positionAt(projection.sourceEnd),
		),
		virtualUri: request.virtualUri.with({ query: parameters.toString() }),
	};
}

function sameRange(left: vscode.Range, right: vscode.Range): boolean {
	return left.start.isEqual(right.start) && left.end.isEqual(right.end);
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
