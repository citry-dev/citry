export type EmbeddedFormattingLanguage = "javascript" | "css";

export type EmbeddedFormattingRegionKind = "script-body" | "style-body" | "component-js" | "component-css";

export interface TextPosition {
	line: number;
	character: number;
}

export interface TextRange {
	start: TextPosition;
	end: TextPosition;
}

export interface ProviderTextEdit {
	range: TextRange;
	newText: string;
}

export interface EmbeddedFormattingRegion {
	id: string;
	language: EmbeddedFormattingLanguage;
	kind: EmbeddedFormattingRegionKind;
	source: string;
	virtualSource: string;
	protectedRanges: readonly TextRange[];
	delimiterConstraints: {
		forbiddenSubstrings: readonly string[];
		caseInsensitive: boolean;
	};
}

export interface EmbeddedFormattingParams {
	version: 1;
	textDocument: { uri: string; version: number };
	planId: string;
	regions: readonly EmbeddedFormattingRegion[];
}

export interface EmbeddedFormattingResult {
	planId: string;
	regionId: string;
	status: "formatted" | "unchanged" | "unavailable" | "error";
	text?: string;
	provider?: null;
	message?: string;
}

export interface EmbeddedFormattingResponse {
	version: 1;
	textDocument: { uri: string; version: number };
	planId: string;
	results: EmbeddedFormattingResult[];
	providerSelection: "vscode-first-result";
}

export interface EmbeddedFormatterInvocation {
	region: EmbeddedFormattingRegion;
	source: string;
	pass: 1 | 2;
	signal: AbortSignal;
}

export interface EmbeddedFormattingEnvironment {
	currentDocumentVersion: (uri: string) => number | undefined;
	executeFormatter: (invocation: EmbeddedFormatterInvocation) => Promise<readonly ProviderTextEdit[] | undefined>;
	timeoutMilliseconds?: number;
	cancellationSignal?: AbortSignal;
}

export interface EmbeddedFormattingOptions {
	tabSize: number;
	insertSpaces: boolean;
}

export interface EmbeddedFormattingDocumentIdentity {
	authority: EmbeddedFormattingLanguage;
	path: string;
	query: string;
}

const embeddedFormatterTimeoutMilliseconds = 30_000;

/** Resolve the language-scoped editor indentation settings with safe defaults. */
export function embeddedFormattingOptions(tabSize: unknown, insertSpaces: unknown): EmbeddedFormattingOptions {
	const validTabSize = typeof tabSize === "number" && Number.isInteger(tabSize) && tabSize > 0 && tabSize <= 32;
	return {
		tabSize: validTabSize ? tabSize : 2,
		insertSpaces: typeof insertSpaces === "boolean" ? insertSpaces : true,
	};
}

/** Build one pass-independent virtual-document identity for a formatter region. */
export function embeddedFormattingDocumentIdentity(
	params: EmbeddedFormattingParams,
	region: EmbeddedFormattingRegion,
	session: string,
): EmbeddedFormattingDocumentIdentity {
	const extension = region.language === "javascript" ? "js" : "css";
	return {
		authority: region.language,
		path: `/document.${extension}`,
		query: new URLSearchParams({
			session,
			plan: params.planId,
			region: region.id,
			source: params.textDocument.uri,
			version: String(params.textDocument.version),
		}).toString(),
	};
}

/** Raised when an editor document changes during an embedded provider round trip. */
export class EmbeddedFormattingStaleError extends Error {
	constructor() {
		super("citry.format.stale-document: the document changed during embedded formatting");
		this.name = "EmbeddedFormattingStaleError";
	}
}

/** Raised when the originating language-server request is cancelled. */
export class EmbeddedFormattingCancelledError extends Error {
	constructor() {
		super("citry.format.cancelled: embedded formatting was cancelled");
		this.name = "EmbeddedFormattingCancelledError";
	}
}

/**
 * Format immutable virtual documents and return one classified reply per region.
 *
 * VS Code does not reveal which registered formatter supplied the first result,
 * so successful replies deliberately leave the provider identity unknown.
 */
export async function formatEmbeddedDocuments(
	params: EmbeddedFormattingParams,
	environment: EmbeddedFormattingEnvironment,
): Promise<EmbeddedFormattingResponse> {
	validateParams(params);
	assertNotCancelled(environment);
	assertCurrent(params, environment);
	const results: EmbeddedFormattingResult[] = [];
	for (const region of params.regions) {
		assertNotCancelled(environment);
		assertCurrent(params, environment);
		results.push(await formatRegion(params.planId, region, params, environment));
	}
	assertNotCancelled(environment);
	assertCurrent(params, environment);
	return {
		version: 1,
		textDocument: { ...params.textDocument },
		planId: params.planId,
		results,
		providerSelection: "vscode-first-result",
	};
}

/** Apply a formatter's UTF-16 edits only when every range is exact and disjoint. */
export function applyProviderTextEdits(
	source: string,
	edits: readonly ProviderTextEdit[],
	protectedRanges: readonly TextRange[] = [],
): string {
	const protectedOffsets = protectedRanges.map((range) => offsetsForRange(source, range));
	const resolved = edits.map((edit, index) => {
		if (typeof edit !== "object" || edit === null || typeof edit.newText !== "string") {
			throw new Error(`formatter edit ${index} is malformed`);
		}
		validateUtf16String(edit.newText, `formatter edit ${index}`);
		const offsets = offsetsForRange(source, edit.range);
		if (protectedOffsets.some((protectedRange) => rangesConflict(offsets, protectedRange))) {
			throw new Error(`formatter edit ${index} intersects a protected range`);
		}
		return { ...offsets, newText: edit.newText, index };
	});
	resolved.sort((left, right) => left.start - right.start || left.end - right.end);
	for (let index = 1; index < resolved.length; index += 1) {
		const previous = resolved[index - 1];
		const current = resolved[index];
		if (previous === undefined || current === undefined) {
			continue;
		}
		if (current.start < previous.end || current.start === previous.start) {
			throw new Error(`formatter edits ${previous.index} and ${current.index} overlap`);
		}
	}

	let result = source;
	for (const edit of [...resolved].reverse()) {
		result = `${result.slice(0, edit.start)}${edit.newText}${result.slice(edit.end)}`;
	}
	return result;
}

async function formatRegion(
	planId: string,
	region: EmbeddedFormattingRegion,
	params: EmbeddedFormattingParams,
	environment: EmbeddedFormattingEnvironment,
): Promise<EmbeddedFormattingResult> {
	let firstEdits: readonly ProviderTextEdit[] | undefined;
	try {
		firstEdits = await executeFormatterWithTimeout({ region, source: region.virtualSource, pass: 1 }, environment);
		assertCurrent(params, environment);
	} catch (error) {
		if (error instanceof EmbeddedFormattingStaleError || error instanceof EmbeddedFormattingCancelledError) {
			throw error;
		}
		return failed(planId, region.id, errorMessage(error));
	}
	if (firstEdits === undefined) {
		return {
			planId,
			regionId: region.id,
			status: "unavailable",
			message: `no ${region.language} formatter returned a result`,
		};
	}
	if (firstEdits.length === 0) {
		return unchanged(planId, region.id);
	}

	let formatted: string;
	try {
		formatted = applyProviderTextEdits(region.virtualSource, firstEdits, region.protectedRanges);
		validateDelimiterConstraints(formatted, region);
	} catch (error) {
		return failed(planId, region.id, errorMessage(error));
	}
	if (formatted === region.virtualSource) {
		return unchanged(planId, region.id);
	}
	const secondProtectedRanges = remapProtectedRanges(
		region.virtualSource,
		formatted,
		firstEdits,
		region.protectedRanges,
	);

	let secondEdits: readonly ProviderTextEdit[] | undefined;
	try {
		secondEdits = await executeFormatterWithTimeout({ region, source: formatted, pass: 2 }, environment);
		assertCurrent(params, environment);
	} catch (error) {
		if (error instanceof EmbeddedFormattingStaleError || error instanceof EmbeddedFormattingCancelledError) {
			throw error;
		}
		return failed(planId, region.id, `second formatter pass failed: ${errorMessage(error)}`);
	}
	if (secondEdits === undefined) {
		return failed(planId, region.id, "the formatter became unavailable during its idempotence check");
	}

	try {
		const second = applyProviderTextEdits(formatted, secondEdits, secondProtectedRanges);
		validateDelimiterConstraints(second, region);
		if (second !== formatted) {
			return failed(planId, region.id, "the formatter did not reach an idempotent result after two passes");
		}
	} catch (error) {
		return failed(planId, region.id, `second formatter pass was invalid: ${errorMessage(error)}`);
	}
	return {
		planId,
		regionId: region.id,
		status: "formatted",
		text: formatted,
		provider: null,
	};
}

async function executeFormatterWithTimeout(
	invocation: Omit<EmbeddedFormatterInvocation, "signal">,
	environment: EmbeddedFormattingEnvironment,
): Promise<readonly ProviderTextEdit[] | undefined> {
	const configured = environment.timeoutMilliseconds;
	const timeout =
		typeof configured === "number" && Number.isFinite(configured) && configured > 0
			? configured
			: embeddedFormatterTimeoutMilliseconds;
	const controller = new AbortController();
	let timer: ReturnType<typeof setTimeout> | undefined;
	const parentSignal = environment.cancellationSignal;
	let rejectCancellation: ((error: EmbeddedFormattingCancelledError) => void) | undefined;
	const cancelCurrentInvocation = (): void => {
		controller.abort();
		rejectCancellation?.(new EmbeddedFormattingCancelledError());
	};
	if (parentSignal?.aborted === true) {
		throw new EmbeddedFormattingCancelledError();
	}
	const cancellation = new Promise<never>((_resolve, reject) => {
		rejectCancellation = reject;
		parentSignal?.addEventListener("abort", cancelCurrentInvocation, { once: true });
	});
	try {
		return await Promise.race([
			environment.executeFormatter({ ...invocation, signal: controller.signal }),
			cancellation,
			new Promise<never>((_resolve, reject) => {
				timer = setTimeout(() => {
					controller.abort();
					reject(new Error(`embedded formatter timed out after ${timeout} ms`));
				}, timeout);
			}),
		]);
	} finally {
		if (timer !== undefined) {
			clearTimeout(timer);
		}
		parentSignal?.removeEventListener("abort", cancelCurrentInvocation);
	}
}

function assertNotCancelled(environment: EmbeddedFormattingEnvironment): void {
	if (environment.cancellationSignal?.aborted === true) {
		throw new EmbeddedFormattingCancelledError();
	}
}

function validateParams(params: EmbeddedFormattingParams): void {
	if (typeof params !== "object" || params === null) {
		throw new Error("citry/formatEmbedded params are malformed");
	}
	if (params.version !== 1) {
		throw new Error("citry/formatEmbedded requires version 1");
	}
	if (
		typeof params.textDocument?.uri !== "string" ||
		!Number.isInteger(params.textDocument.version) ||
		params.textDocument.version < 0 ||
		typeof params.planId !== "string" ||
		params.planId.length === 0 ||
		!Array.isArray(params.regions)
	) {
		throw new Error("citry/formatEmbedded params are malformed");
	}
	const ids = new Set<string>();
	for (const region of params.regions) {
		if (
			typeof region !== "object" ||
			region === null ||
			typeof region.id !== "string" ||
			region.id.length === 0 ||
			ids.has(region.id) ||
			(region.language !== "javascript" && region.language !== "css") ||
			!regionKindMatchesLanguage(region.kind, region.language) ||
			typeof region.source !== "string" ||
			typeof region.virtualSource !== "string" ||
			!Array.isArray(region.protectedRanges) ||
			!Array.isArray(region.delimiterConstraints?.forbiddenSubstrings) ||
			typeof region.delimiterConstraints.caseInsensitive !== "boolean"
		) {
			throw new Error("citry/formatEmbedded contains a malformed or duplicate region");
		}
		ids.add(region.id);
		for (const range of region.protectedRanges) {
			offsetsForRange(region.virtualSource, range);
		}
		if (region.delimiterConstraints.forbiddenSubstrings.some((value: unknown) => typeof value !== "string")) {
			throw new Error("citry/formatEmbedded contains a malformed delimiter constraint");
		}
	}
}

function assertCurrent(params: EmbeddedFormattingParams, environment: EmbeddedFormattingEnvironment): void {
	if (environment.currentDocumentVersion(params.textDocument.uri) !== params.textDocument.version) {
		throw new EmbeddedFormattingStaleError();
	}
}

function validateDelimiterConstraints(source: string, region: EmbeddedFormattingRegion): void {
	const candidate = region.delimiterConstraints.caseInsensitive ? source.toLowerCase() : source;
	for (const forbidden of region.delimiterConstraints.forbiddenSubstrings) {
		const needle = region.delimiterConstraints.caseInsensitive ? forbidden.toLowerCase() : forbidden;
		if (candidate.includes(needle)) {
			throw new Error(`formatter output contains forbidden delimiter ${JSON.stringify(forbidden)}`);
		}
	}
}

function remapProtectedRanges(
	source: string,
	formatted: string,
	edits: readonly ProviderTextEdit[],
	protectedRanges: readonly TextRange[],
): TextRange[] {
	if (protectedRanges.length === 0) {
		return [];
	}
	const editOffsets = edits.map((edit) => {
		const offsets = offsetsForRange(source, edit.range);
		return { ...offsets, delta: edit.newText.length - (offsets.end - offsets.start) };
	});
	const shift = (boundary: number): number =>
		boundary + editOffsets.reduce((delta, edit) => delta + (edit.end <= boundary ? edit.delta : 0), 0);
	return protectedRanges.map((range) => {
		const original = offsetsForRange(source, range);
		return {
			start: positionAt(formatted, shift(original.start)),
			end: positionAt(formatted, shift(original.end)),
		};
	});
}

function offsetsForRange(source: string, range: TextRange): { start: number; end: number } {
	if (typeof range !== "object" || range === null) {
		throw new Error("formatter range is malformed");
	}
	const start = offsetAt(source, range.start);
	const end = offsetAt(source, range.end);
	if (end < start) {
		throw new Error("formatter range ends before it starts");
	}
	return { start, end };
}

function offsetAt(source: string, position: TextPosition): number {
	if (
		typeof position !== "object" ||
		position === null ||
		!Number.isInteger(position.line) ||
		!Number.isInteger(position.character) ||
		position.line < 0 ||
		position.character < 0
	) {
		throw new Error("formatter position is malformed");
	}
	const lines = lineRanges(source);
	const line = lines[position.line];
	if (line === undefined || position.character > line.end - line.start) {
		throw new Error("formatter position is outside the virtual document");
	}
	const offset = line.start + position.character;
	if (
		offset > line.start &&
		offset < line.end &&
		isHighSurrogate(source.charCodeAt(offset - 1)) &&
		isLowSurrogate(source.charCodeAt(offset))
	) {
		throw new Error("formatter position splits a UTF-16 surrogate pair");
	}
	return offset;
}

function positionAt(source: string, offset: number): TextPosition {
	if (!Number.isInteger(offset) || offset < 0 || offset > source.length) {
		throw new Error("formatter edit produced an invalid protected-range boundary");
	}
	const lines = lineRanges(source);
	if (
		offset > 0 &&
		offset < source.length &&
		isHighSurrogate(source.charCodeAt(offset - 1)) &&
		isLowSurrogate(source.charCodeAt(offset))
	) {
		throw new Error("formatter edit moved a protected range into a UTF-16 surrogate pair");
	}
	for (let line = 0; line < lines.length; line += 1) {
		const range = lines[line];
		if (range !== undefined && range.start <= offset && offset <= range.end) {
			return { line, character: offset - range.start };
		}
	}
	throw new Error("formatter edit moved a protected range into a newline sequence");
}

function lineRanges(source: string): Array<{ start: number; end: number }> {
	const lines: Array<{ start: number; end: number }> = [];
	let start = 0;
	let index = 0;
	while (index < source.length) {
		if (source[index] === "\r" || source[index] === "\n") {
			lines.push({ start, end: index });
			if (source[index] === "\r" && source[index + 1] === "\n") {
				index += 1;
			}
			start = index + 1;
		}
		index += 1;
	}
	lines.push({ start, end: source.length });
	return lines;
}

function rangesConflict(left: { start: number; end: number }, right: { start: number; end: number }): boolean {
	if (left.start === left.end) {
		return right.start <= left.start && left.start <= right.end;
	}
	return left.start < right.end && right.start < left.end;
}

function isHighSurrogate(value: number): boolean {
	return value >= 0xd800 && value <= 0xdbff;
}

function isLowSurrogate(value: number): boolean {
	return value >= 0xdc00 && value <= 0xdfff;
}

function validateUtf16String(value: string, label: string): void {
	for (let index = 0; index < value.length; index += 1) {
		const unit = value.charCodeAt(index);
		if (isHighSurrogate(unit)) {
			if (!isLowSurrogate(value.charCodeAt(index + 1))) {
				throw new Error(`${label} contains an unpaired UTF-16 surrogate`);
			}
			index += 1;
			continue;
		}
		if (isLowSurrogate(unit)) {
			throw new Error(`${label} contains an unpaired UTF-16 surrogate`);
		}
	}
}

function regionKindMatchesLanguage(kind: EmbeddedFormattingRegionKind, language: EmbeddedFormattingLanguage): boolean {
	return language === "javascript"
		? kind === "script-body" || kind === "component-js"
		: kind === "style-body" || kind === "component-css";
}

function unchanged(planId: string, regionId: string): EmbeddedFormattingResult {
	return { planId, regionId, status: "unchanged" };
}

function failed(planId: string, regionId: string, message: string): EmbeddedFormattingResult {
	return { planId, regionId, status: "error", message };
}

function errorMessage(error: unknown): string {
	return error instanceof Error ? error.message : String(error);
}
