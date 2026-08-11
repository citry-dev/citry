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
