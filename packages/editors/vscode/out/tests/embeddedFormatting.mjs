// src/diagnosticCatalog.ts
var FORMAT_STALE_DOCUMENT = "citry.format.stale-document";
var FORMAT_CANCELLED = "citry.format.cancelled";

// src/embeddedFormatting.ts
var embeddedFormatterTimeoutMilliseconds = 3e4;
function embeddedFormattingOptions(tabSize, insertSpaces) {
  const validTabSize = typeof tabSize === "number" && Number.isInteger(tabSize) && tabSize > 0 && tabSize <= 32;
  return {
    tabSize: validTabSize ? tabSize : 2,
    insertSpaces: typeof insertSpaces === "boolean" ? insertSpaces : true
  };
}
function embeddedFormattingDocumentIdentity(params, region, session) {
  const extension = region.language === "javascript" ? "js" : "css";
  return {
    authority: region.language,
    path: `/document.${extension}`,
    query: new URLSearchParams({
      session,
      plan: params.planId,
      region: region.id,
      source: params.textDocument.uri,
      version: String(params.textDocument.version)
    }).toString()
  };
}
var EmbeddedFormattingStaleError = class extends Error {
  constructor() {
    super(`${FORMAT_STALE_DOCUMENT}: the document changed during embedded formatting`);
    this.name = "EmbeddedFormattingStaleError";
  }
};
var EmbeddedFormattingCancelledError = class extends Error {
  constructor() {
    super(`${FORMAT_CANCELLED}: embedded formatting was cancelled`);
    this.name = "EmbeddedFormattingCancelledError";
  }
};
async function formatEmbeddedDocuments(params, environment) {
  validateParams(params);
  assertNotCancelled(environment);
  assertCurrent(params, environment);
  const results = [];
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
    providerSelection: "vscode-first-result"
  };
}
function applyProviderTextEdits(source, edits, protectedRanges = []) {
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
    if (previous === void 0 || current === void 0) {
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
async function formatRegion(planId, region, params, environment) {
  let firstEdits;
  try {
    firstEdits = await executeFormatterWithTimeout({ region, source: region.virtualSource, pass: 1 }, environment);
    assertCurrent(params, environment);
  } catch (error) {
    if (error instanceof EmbeddedFormattingStaleError || error instanceof EmbeddedFormattingCancelledError) {
      throw error;
    }
    return failed(planId, region.id, errorMessage(error));
  }
  if (firstEdits === void 0) {
    return {
      planId,
      regionId: region.id,
      status: "unavailable",
      message: `no ${region.language} formatter returned a result`
    };
  }
  if (firstEdits.length === 0) {
    return unchanged(planId, region.id);
  }
  let formatted;
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
    region.protectedRanges
  );
  let secondEdits;
  try {
    secondEdits = await executeFormatterWithTimeout({ region, source: formatted, pass: 2 }, environment);
    assertCurrent(params, environment);
  } catch (error) {
    if (error instanceof EmbeddedFormattingStaleError || error instanceof EmbeddedFormattingCancelledError) {
      throw error;
    }
    return failed(planId, region.id, `second formatter pass failed: ${errorMessage(error)}`);
  }
  if (secondEdits === void 0) {
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
    provider: null
  };
}
async function executeFormatterWithTimeout(invocation, environment) {
  const configured = environment.timeoutMilliseconds;
  const timeout = typeof configured === "number" && Number.isFinite(configured) && configured > 0 ? configured : embeddedFormatterTimeoutMilliseconds;
  const controller = new AbortController();
  let timer;
  const parentSignal = environment.cancellationSignal;
  let rejectCancellation;
  const cancelCurrentInvocation = () => {
    controller.abort();
    rejectCancellation?.(new EmbeddedFormattingCancelledError());
  };
  if (parentSignal?.aborted === true) {
    throw new EmbeddedFormattingCancelledError();
  }
  const cancellation = new Promise((_resolve, reject) => {
    rejectCancellation = reject;
    parentSignal?.addEventListener("abort", cancelCurrentInvocation, { once: true });
  });
  try {
    return await Promise.race([
      environment.executeFormatter({ ...invocation, signal: controller.signal }),
      cancellation,
      new Promise((_resolve, reject) => {
        timer = setTimeout(() => {
          controller.abort();
          reject(new Error(`embedded formatter timed out after ${timeout} ms`));
        }, timeout);
      })
    ]);
  } finally {
    if (timer !== void 0) {
      clearTimeout(timer);
    }
    parentSignal?.removeEventListener("abort", cancelCurrentInvocation);
  }
}
function assertNotCancelled(environment) {
  if (environment.cancellationSignal?.aborted === true) {
    throw new EmbeddedFormattingCancelledError();
  }
}
function validateParams(params) {
  if (typeof params !== "object" || params === null) {
    throw new Error("citry/formatEmbedded params are malformed");
  }
  if (params.version !== 1) {
    throw new Error("citry/formatEmbedded requires version 1");
  }
  if (typeof params.textDocument?.uri !== "string" || !Number.isInteger(params.textDocument.version) || params.textDocument.version < 0 || typeof params.planId !== "string" || params.planId.length === 0 || !Array.isArray(params.regions)) {
    throw new Error("citry/formatEmbedded params are malformed");
  }
  const ids = /* @__PURE__ */ new Set();
  for (const region of params.regions) {
    if (typeof region !== "object" || region === null || typeof region.id !== "string" || region.id.length === 0 || ids.has(region.id) || region.language !== "javascript" && region.language !== "css" || !regionKindMatchesLanguage(region.kind, region.language) || typeof region.source !== "string" || typeof region.virtualSource !== "string" || !Array.isArray(region.protectedRanges) || !Array.isArray(region.delimiterConstraints?.forbiddenSubstrings) || typeof region.delimiterConstraints.caseInsensitive !== "boolean") {
      throw new Error("citry/formatEmbedded contains a malformed or duplicate region");
    }
    ids.add(region.id);
    for (const range of region.protectedRanges) {
      offsetsForRange(region.virtualSource, range);
    }
    if (region.delimiterConstraints.forbiddenSubstrings.some((value) => typeof value !== "string")) {
      throw new Error("citry/formatEmbedded contains a malformed delimiter constraint");
    }
  }
}
function assertCurrent(params, environment) {
  if (environment.currentDocumentVersion(params.textDocument.uri) !== params.textDocument.version) {
    throw new EmbeddedFormattingStaleError();
  }
}
function validateDelimiterConstraints(source, region) {
  const candidate = region.delimiterConstraints.caseInsensitive ? source.toLowerCase() : source;
  for (const forbidden of region.delimiterConstraints.forbiddenSubstrings) {
    const needle = region.delimiterConstraints.caseInsensitive ? forbidden.toLowerCase() : forbidden;
    if (candidate.includes(needle)) {
      throw new Error(`formatter output contains forbidden delimiter ${JSON.stringify(forbidden)}`);
    }
  }
}
function remapProtectedRanges(source, formatted, edits, protectedRanges) {
  if (protectedRanges.length === 0) {
    return [];
  }
  const editOffsets = edits.map((edit) => {
    const offsets = offsetsForRange(source, edit.range);
    return { ...offsets, delta: edit.newText.length - (offsets.end - offsets.start) };
  });
  const shift = (boundary) => boundary + editOffsets.reduce((delta, edit) => delta + (edit.end <= boundary ? edit.delta : 0), 0);
  return protectedRanges.map((range) => {
    const original = offsetsForRange(source, range);
    return {
      start: positionAt(formatted, shift(original.start)),
      end: positionAt(formatted, shift(original.end))
    };
  });
}
function offsetsForRange(source, range) {
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
function offsetAt(source, position) {
  if (typeof position !== "object" || position === null || !Number.isInteger(position.line) || !Number.isInteger(position.character) || position.line < 0 || position.character < 0) {
    throw new Error("formatter position is malformed");
  }
  const lines = lineRanges(source);
  const line = lines[position.line];
  if (line === void 0 || position.character > line.end - line.start) {
    throw new Error("formatter position is outside the virtual document");
  }
  const offset = line.start + position.character;
  if (offset > line.start && offset < line.end && isHighSurrogate(source.charCodeAt(offset - 1)) && isLowSurrogate(source.charCodeAt(offset))) {
    throw new Error("formatter position splits a UTF-16 surrogate pair");
  }
  return offset;
}
function positionAt(source, offset) {
  if (!Number.isInteger(offset) || offset < 0 || offset > source.length) {
    throw new Error("formatter edit produced an invalid protected-range boundary");
  }
  const lines = lineRanges(source);
  if (offset > 0 && offset < source.length && isHighSurrogate(source.charCodeAt(offset - 1)) && isLowSurrogate(source.charCodeAt(offset))) {
    throw new Error("formatter edit moved a protected range into a UTF-16 surrogate pair");
  }
  for (let line = 0; line < lines.length; line += 1) {
    const range = lines[line];
    if (range !== void 0 && range.start <= offset && offset <= range.end) {
      return { line, character: offset - range.start };
    }
  }
  throw new Error("formatter edit moved a protected range into a newline sequence");
}
function lineRanges(source) {
  const lines = [];
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
function rangesConflict(left, right) {
  if (left.start === left.end) {
    return right.start <= left.start && left.start <= right.end;
  }
  return left.start < right.end && right.start < left.end;
}
function isHighSurrogate(value) {
  return value >= 55296 && value <= 56319;
}
function isLowSurrogate(value) {
  return value >= 56320 && value <= 57343;
}
function validateUtf16String(value, label) {
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
function regionKindMatchesLanguage(kind, language) {
  return language === "javascript" ? kind === "script-body" || kind === "component-js" : kind === "style-body" || kind === "component-css";
}
function unchanged(planId, regionId) {
  return { planId, regionId, status: "unchanged" };
}
function failed(planId, regionId, message) {
  return { planId, regionId, status: "error", message };
}
function errorMessage(error) {
  return error instanceof Error ? error.message : String(error);
}
export {
  EmbeddedFormattingCancelledError,
  EmbeddedFormattingStaleError,
  applyProviderTextEdits,
  embeddedFormattingDocumentIdentity,
  embeddedFormattingOptions,
  formatEmbeddedDocuments
};
