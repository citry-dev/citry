export const delegatedCompletionResolveCount = 0;
export const projectionTimeoutMs = 2_000;
export const virtualDocumentTimeoutMs = 1_000;
export const delegatedProviderTimeoutMs = 2_000;

export class ProviderTimeoutError extends Error {
	constructor(readonly stage: string) {
		super(`Citry provider stage timed out: ${stage}`);
		this.name = "ProviderTimeoutError";
	}
}

/** Stop waiting for an editor provider that cannot accept Citry's token. */
export async function withTimeout<T>(
	promise: Promise<T>,
	timeoutMs: number,
	stage: string,
	onTimeout?: () => void,
): Promise<T> {
	let timer: NodeJS.Timeout | undefined;
	const timeout = new Promise<never>((_resolve, reject) => {
		timer = setTimeout(() => {
			onTimeout?.();
			reject(new ProviderTimeoutError(stage));
		}, timeoutMs);
	});
	try {
		return await Promise.race([promise, timeout]);
	} finally {
		if (timer !== undefined) {
			clearTimeout(timer);
		}
	}
}

export interface ProtocolPosition {
	line: number;
	character: number;
}

/** Map another cursor inside a cached same-length provider fragment. */
export function linearlyMappedProjectionPosition(
	source: string,
	sourceOffset: number,
	sourceStart: number,
	sourceEnd: number,
	virtualStart: ProtocolPosition,
	virtualEnd: ProtocolPosition,
): ProtocolPosition | undefined {
	const virtualStartOffset = textOffsetAt(source, virtualStart);
	const virtualEndOffset = textOffsetAt(source, virtualEnd);
	const virtualOffset = virtualStartOffset + sourceOffset - sourceStart;
	if (
		sourceOffset < sourceStart ||
		sourceOffset > sourceEnd ||
		virtualOffset < virtualStartOffset ||
		virtualOffset > virtualEndOffset
	) {
		return undefined;
	}
	return textPositionAt(source, virtualOffset);
}

export interface ProtocolRange {
	start: ProtocolPosition;
	end: ProtocolPosition;
}

/**
 * One piece of a projection whose virtual text differs from the authored text.
 *
 * A projection is the virtual document the language server builds from one
 * embedded region so the editor's own language provider can answer for it.
 *
 * The language server removes a Python literal's indentation and decodes its
 * escapes before handing component JavaScript to the editor's JavaScript
 * provider, so one constant offset cannot map a result back. Each segment is
 * either a run of unchanged characters on one line (same width on both sides)
 * or one changed piece (a line break with the indentation it dropped, or one
 * escape) that only maps at its two ends.
 */
export interface ProjectionSegment {
	sourceRange: ProtocolRange;
	virtualRange: ProtocolRange;
}

const comparePositions = (left: ProtocolPosition, right: ProtocolPosition): number =>
	left.line - right.line || left.character - right.character;

const isLinearSegment = (segment: ProjectionSegment): boolean =>
	segment.sourceRange.start.line === segment.sourceRange.end.line &&
	segment.virtualRange.start.line === segment.virtualRange.end.line &&
	segment.sourceRange.end.character - segment.sourceRange.start.character ===
		segment.virtualRange.end.character - segment.virtualRange.start.character;

/**
 * Map one position across a segmented projection.
 *
 * `edge` settles a position shared by two segments. A range start takes the
 * segment that begins there, so a result at the start of a dedented virtual
 * line lands after the authored indentation; a range end takes the segment
 * that ends there. A position inside a changed piece has no authored
 * equivalent and maps to undefined.
 */
export function mapSegmentedPosition(
	position: ProtocolPosition,
	segments: readonly ProjectionSegment[],
	from: "sourceRange" | "virtualRange",
	edge: "start" | "end",
): ProtocolPosition | undefined {
	const to = from === "virtualRange" ? "sourceRange" : "virtualRange";
	const containing = segments.filter(
		(segment) =>
			comparePositions(segment[from].start, position) <= 0 && comparePositions(position, segment[from].end) <= 0,
	);
	const preferred =
		containing.find((segment) => comparePositions(segment[from][edge], position) === 0) ?? containing[0];
	if (preferred === undefined) {
		return undefined;
	}
	if (isLinearSegment(preferred)) {
		return {
			line: preferred[to].start.line,
			character: preferred[to].start.character + position.character - preferred[from].start.character,
		};
	}
	if (comparePositions(position, preferred[from].start) === 0) {
		return { ...preferred[to].start };
	}
	if (comparePositions(position, preferred[from].end) === 0) {
		return { ...preferred[to].end };
	}
	return undefined;
}

/** Map a provider result range back to authored source through segments. */
export function mapSegmentedRange(
	range: ProtocolRange,
	segments: readonly ProjectionSegment[],
): ProtocolRange | undefined {
	const start = mapSegmentedPosition(range.start, segments, "virtualRange", "start");
	// An empty range is one cursor, so both ends share the start mapping.
	const end =
		comparePositions(range.start, range.end) === 0
			? start
			: mapSegmentedPosition(range.end, segments, "virtualRange", "end");
	if (start === undefined || end === undefined || comparePositions(start, end) > 0) {
		return undefined;
	}
	return { start, end };
}

function textOffsetAt(source: string, position: ProtocolPosition): number {
	let line = 0;
	let offset = 0;
	while (line < position.line) {
		const newline = source.indexOf("\n", offset);
		if (newline < 0) {
			return source.length;
		}
		offset = newline + 1;
		line += 1;
	}
	return Math.min(source.length, offset + position.character);
}

function textPositionAt(source: string, requestedOffset: number): ProtocolPosition {
	const offset = Math.max(0, Math.min(source.length, requestedOffset));
	const prefix = source.slice(0, offset);
	const line = prefix.split("\n").length - 1;
	const lastNewline = prefix.lastIndexOf("\n");
	return { line, character: offset - lastNewline - 1 };
}

export interface ProtocolRange {
	start: ProtocolPosition;
	end: ProtocolPosition;
}

export interface ProjectionSourceMapping {
	sourceRange: ProtocolRange;
	virtualRange: ProtocolRange;
}

/** Map provider ranges through exact source copies and decoded character boundaries. */
export function mappedProjectionRange(
	source: string,
	virtual: string,
	mappings: readonly ProjectionSourceMapping[],
	range: ProtocolRange,
): ProtocolRange | undefined {
	return prepareProjectionRangeMapper(source, virtual, mappings)?.(range);
}

export type ProjectionRangeMapper = (range: ProtocolRange) => ProtocolRange | undefined;

/** Index one provider document once for every completion, hover, or definition range in its response. */
export function prepareProjectionRangeMapper(
	source: string,
	virtual: string,
	mappings: readonly ProjectionSourceMapping[],
): ProjectionRangeMapper | undefined {
	const sourceLines = indexedLines(source);
	const virtualLines = indexedLines(virtual);
	const runs: { sourceStart: number; sourceEnd: number; virtualStart: number; virtualEnd: number }[] = [];
	for (const mapping of mappings) {
		const sourceStart = exactOffset(sourceLines, mapping.sourceRange.start);
		const sourceEnd = exactOffset(sourceLines, mapping.sourceRange.end);
		const virtualStart = exactOffset(virtualLines, mapping.virtualRange.start);
		const virtualEnd = exactOffset(virtualLines, mapping.virtualRange.end);
		const prior = runs.at(-1);
		if (
			sourceStart === undefined ||
			sourceEnd === undefined ||
			virtualStart === undefined ||
			virtualEnd === undefined ||
			sourceStart > sourceEnd ||
			virtualStart > virtualEnd ||
			((sourceStart === sourceEnd || virtualStart === virtualEnd) &&
				!(mappings.length === 1 && sourceStart === sourceEnd && virtualStart === virtualEnd)) ||
			(prior !== undefined && (sourceStart < prior.sourceEnd || virtualStart < prior.virtualEnd))
		)
			return undefined;
		runs.push({ sourceStart, sourceEnd, virtualStart, virtualEnd });
	}
	// At a dedented line boundary the next copy owns an insertion; the previous copy owns a range end.
	const reverseRuns = [...runs].reverse();
	const mapOffset = (offset: number, rightBias: boolean): number | undefined => {
		const candidates = rightBias ? reverseRuns : runs;
		for (const run of candidates) {
			if (offset < run.virtualStart || offset > run.virtualEnd) continue;
			if (offset === run.virtualStart) return run.sourceStart;
			if (offset === run.virtualEnd) return run.sourceEnd;
			if (run.virtualEnd - run.virtualStart !== run.sourceEnd - run.sourceStart) return undefined;
			return run.sourceStart + offset - run.virtualStart;
		}
		return undefined;
	};
	return (range) => {
		const start = exactOffset(virtualLines, range.start);
		const end = exactOffset(virtualLines, range.end);
		if (start === undefined || end === undefined || start > end) return undefined;
		const sourceStart = mapOffset(start, true);
		const sourceEnd = start === end ? sourceStart : mapOffset(end, false);
		if (sourceStart === undefined || sourceEnd === undefined || sourceStart > sourceEnd) return undefined;
		// A range cannot bridge generated text even when both of its endpoints map.
		let coveredUntil = start;
		for (const run of runs) {
			if (run.virtualEnd <= coveredUntil) continue;
			if (run.virtualStart > coveredUntil) break;
			coveredUntil = run.virtualEnd;
			if (coveredUntil >= end) break;
		}
		if (coveredUntil < end) return undefined;
		return { start: indexedPosition(sourceLines, sourceStart), end: indexedPosition(sourceLines, sourceEnd) };
	};
}

interface IndexedLines {
	starts: number[];
	ends: number[];
}

function indexedLines(text: string): IndexedLines {
	const starts = [0];
	const ends: number[] = [];
	for (let index = 0; index < text.length; index += 1) {
		if (text[index] !== "\r" && text[index] !== "\n") continue;
		ends.push(index);
		if (text[index] === "\r" && text[index + 1] === "\n") index += 1;
		starts.push(index + 1);
	}
	ends.push(text.length);
	return { starts, ends };
}

function exactOffset(lines: IndexedLines, position: ProtocolPosition): number | undefined {
	if (
		!Number.isInteger(position.line) ||
		!Number.isInteger(position.character) ||
		position.line < 0 ||
		position.character < 0
	)
		return undefined;
	const start = lines.starts[position.line];
	const end = lines.ends[position.line];
	return start === undefined || end === undefined || start + position.character > end
		? undefined
		: start + position.character;
}

function indexedPosition(lines: IndexedLines, offset: number): ProtocolPosition {
	let line = lines.starts.length - 1;
	while (line > 0 && (lines.starts[line] ?? 0) > offset) line -= 1;
	return { line, character: offset - (lines.starts[line] ?? 0) };
}
