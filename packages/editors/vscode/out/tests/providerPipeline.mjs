// src/providerPipeline.ts
var delegatedCompletionResolveCount = 0;
var projectionTimeoutMs = 2e3;
var virtualDocumentTimeoutMs = 1e3;
var delegatedProviderTimeoutMs = 2e3;
var ProviderTimeoutError = class extends Error {
  constructor(stage) {
    super(`Citry provider stage timed out: ${stage}`);
    this.stage = stage;
    this.name = "ProviderTimeoutError";
  }
  stage;
};
async function withTimeout(promise, timeoutMs, stage, onTimeout) {
  let timer;
  const timeout = new Promise((_resolve, reject) => {
    timer = setTimeout(() => {
      onTimeout?.();
      reject(new ProviderTimeoutError(stage));
    }, timeoutMs);
  });
  try {
    return await Promise.race([promise, timeout]);
  } finally {
    if (timer !== void 0) {
      clearTimeout(timer);
    }
  }
}
function linearlyMappedProjectionPosition(source, sourceOffset, sourceStart, sourceEnd, virtualStart, virtualEnd) {
  const virtualStartOffset = textOffsetAt(source, virtualStart);
  const virtualEndOffset = textOffsetAt(source, virtualEnd);
  const virtualOffset = virtualStartOffset + sourceOffset - sourceStart;
  if (sourceOffset < sourceStart || sourceOffset > sourceEnd || virtualOffset < virtualStartOffset || virtualOffset > virtualEndOffset) {
    return void 0;
  }
  return textPositionAt(source, virtualOffset);
}
function textOffsetAt(source, position) {
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
function textPositionAt(source, requestedOffset) {
  const offset = Math.max(0, Math.min(source.length, requestedOffset));
  const prefix = source.slice(0, offset);
  const line = prefix.split("\n").length - 1;
  const lastNewline = prefix.lastIndexOf("\n");
  return { line, character: offset - lastNewline - 1 };
}
function mappedProjectionRange(source, virtual, mappings, range) {
  return prepareProjectionRangeMapper(source, virtual, mappings)?.(range);
}
function prepareProjectionRangeMapper(source, virtual, mappings) {
  const sourceLines = indexedLines(source);
  const virtualLines = indexedLines(virtual);
  const runs = [];
  for (const mapping of mappings) {
    const sourceStart = exactOffset(sourceLines, mapping.sourceRange.start);
    const sourceEnd = exactOffset(sourceLines, mapping.sourceRange.end);
    const virtualStart = exactOffset(virtualLines, mapping.virtualRange.start);
    const virtualEnd = exactOffset(virtualLines, mapping.virtualRange.end);
    const prior = runs.at(-1);
    if (sourceStart === void 0 || sourceEnd === void 0 || virtualStart === void 0 || virtualEnd === void 0 || sourceStart > sourceEnd || virtualStart > virtualEnd || (sourceStart === sourceEnd || virtualStart === virtualEnd) && !(mappings.length === 1 && sourceStart === sourceEnd && virtualStart === virtualEnd) || prior !== void 0 && (sourceStart < prior.sourceEnd || virtualStart < prior.virtualEnd))
      return void 0;
    runs.push({ sourceStart, sourceEnd, virtualStart, virtualEnd });
  }
  const reverseRuns = [...runs].reverse();
  const mapOffset = (offset, rightBias) => {
    const candidates = rightBias ? reverseRuns : runs;
    for (const run of candidates) {
      if (offset < run.virtualStart || offset > run.virtualEnd) continue;
      if (offset === run.virtualStart) return run.sourceStart;
      if (offset === run.virtualEnd) return run.sourceEnd;
      if (run.virtualEnd - run.virtualStart !== run.sourceEnd - run.sourceStart) return void 0;
      return run.sourceStart + offset - run.virtualStart;
    }
    return void 0;
  };
  return (range) => {
    const start = exactOffset(virtualLines, range.start);
    const end = exactOffset(virtualLines, range.end);
    if (start === void 0 || end === void 0 || start > end) return void 0;
    const sourceStart = mapOffset(start, true);
    const sourceEnd = start === end ? sourceStart : mapOffset(end, false);
    if (sourceStart === void 0 || sourceEnd === void 0 || sourceStart > sourceEnd) return void 0;
    let coveredUntil = start;
    for (const run of runs) {
      if (run.virtualEnd <= coveredUntil) continue;
      if (run.virtualStart > coveredUntil) break;
      coveredUntil = run.virtualEnd;
      if (coveredUntil >= end) break;
    }
    if (coveredUntil < end) return void 0;
    return { start: indexedPosition(sourceLines, sourceStart), end: indexedPosition(sourceLines, sourceEnd) };
  };
}
function indexedLines(text) {
  const starts = [0];
  const ends = [];
  for (let index = 0; index < text.length; index += 1) {
    if (text[index] !== "\r" && text[index] !== "\n") continue;
    ends.push(index);
    if (text[index] === "\r" && text[index + 1] === "\n") index += 1;
    starts.push(index + 1);
  }
  ends.push(text.length);
  return { starts, ends };
}
function exactOffset(lines, position) {
  if (!Number.isInteger(position.line) || !Number.isInteger(position.character) || position.line < 0 || position.character < 0)
    return void 0;
  const start = lines.starts[position.line];
  const end = lines.ends[position.line];
  return start === void 0 || end === void 0 || start + position.character > end ? void 0 : start + position.character;
}
function indexedPosition(lines, offset) {
  let line = lines.starts.length - 1;
  while (line > 0 && (lines.starts[line] ?? 0) > offset) line -= 1;
  return { line, character: offset - (lines.starts[line] ?? 0) };
}
export {
  ProviderTimeoutError,
  delegatedCompletionResolveCount,
  delegatedProviderTimeoutMs,
  linearlyMappedProjectionPosition,
  mappedProjectionRange,
  prepareProjectionRangeMapper,
  projectionTimeoutMs,
  virtualDocumentTimeoutMs,
  withTimeout
};
