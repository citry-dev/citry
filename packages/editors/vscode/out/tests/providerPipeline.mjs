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
export {
  ProviderTimeoutError,
  delegatedCompletionResolveCount,
  delegatedProviderTimeoutMs,
  linearlyMappedProjectionPosition,
  projectionTimeoutMs,
  virtualDocumentTimeoutMs,
  withTimeout
};
