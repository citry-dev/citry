/**
 * Answer the language server's `citry/typeCheck` request with VS Code's own TypeScript.
 *
 * The server sends one generated JavaScript file per template region and per
 * component JavaScript region. The extension writes each file to disk, asks
 * VS Code's TypeScript server for its diagnostics, and returns them unchanged.
 * The server keeps the useful kinds, drops findings in generated text or ones
 * Citry already reports, and moves the rest onto the authored source.
 */

export const typeCheckMethod = "citry/typeCheck";
export const typeCheckVersion = 1;

export interface TypeCheckFile {
	id: string;
	source: string;
}

export interface TypeCheckParams {
	version: number;
	textDocument: { uri: string; version: number | null };
	files: TypeCheckFile[];
}

export interface TypeCheckDiagnostic {
	range: {
		start: { line: number; character: number };
		end: { line: number; character: number };
	};
	code: number;
	message: string;
	category: "error" | "warning" | "suggestion" | "message";
}

export interface TypeCheckResponse {
	version: number;
	files: Array<{ id: string; diagnostics: TypeCheckDiagnostic[] }>;
}

/** One diagnostic as TypeScript's server reports it: lines and offsets start at 1. */
interface TsServerDiagnostic {
	start: { line: number; offset: number };
	end: { line: number; offset: number };
	text: string;
	code?: number;
	category: string;
}

const categories = new Set(["error", "warning", "suggestion", "message"]);

/** Check the request's shape so a newer server's request is refused instead of misread. */
export function validTypeCheckParams(params: unknown): params is TypeCheckParams {
	if (typeof params !== "object" || params === null) {
		return false;
	}
	const candidate = params as Partial<TypeCheckParams>;
	return (
		candidate.version === typeCheckVersion &&
		typeof candidate.textDocument?.uri === "string" &&
		Array.isArray(candidate.files) &&
		candidate.files.every((file) => typeof file?.id === "string" && typeof file?.source === "string")
	);
}

/**
 * Turn a `semanticDiagnosticsSync` or `syntacticDiagnosticsSync` answer into the wire shape.
 *
 * The TypeScript extension answers `typescript.tsserverRequest` with the
 * server's response object, whose `body` holds the diagnostics. Anything else
 * (a cancelled request, an older TypeScript) gives no diagnostics.
 */
export function typeCheckDiagnostics(response: unknown): TypeCheckDiagnostic[] {
	const body = (response as { body?: unknown } | undefined)?.body;
	if (!Array.isArray(body)) {
		return [];
	}
	const diagnostics: TypeCheckDiagnostic[] = [];
	for (const item of body as TsServerDiagnostic[]) {
		if (
			typeof item?.code !== "number" ||
			typeof item.text !== "string" ||
			!categories.has(item.category) ||
			!validLocation(item.start) ||
			!validLocation(item.end)
		) {
			continue;
		}
		diagnostics.push({
			range: {
				start: { line: item.start.line - 1, character: item.start.offset - 1 },
				end: { line: item.end.line - 1, character: item.end.offset - 1 },
			},
			code: item.code,
			message: item.text,
			category: item.category as TypeCheckDiagnostic["category"],
		});
	}
	return diagnostics;
}

function validLocation(location: { line: number; offset: number } | undefined): boolean {
	return (
		location !== undefined &&
		Number.isInteger(location.line) &&
		Number.isInteger(location.offset) &&
		location.line >= 1 &&
		location.offset >= 1
	);
}
