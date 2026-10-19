// src/typeCheck.ts
var typeCheckMethod = "citry/typeCheck";
var typeCheckVersion = 1;
var categories = /* @__PURE__ */ new Set(["error", "warning", "suggestion", "message"]);
function validTypeCheckParams(params) {
  if (typeof params !== "object" || params === null) {
    return false;
  }
  const candidate = params;
  return candidate.version === typeCheckVersion && typeof candidate.textDocument?.uri === "string" && Array.isArray(candidate.files) && candidate.files.every((file) => typeof file?.id === "string" && typeof file?.source === "string");
}
function typeCheckDiagnostics(response) {
  const body = response?.body;
  if (!Array.isArray(body)) {
    return [];
  }
  const diagnostics = [];
  for (const item of body) {
    if (typeof item?.code !== "number" || typeof item.text !== "string" || !categories.has(item.category) || !validLocation(item.start) || !validLocation(item.end)) {
      continue;
    }
    diagnostics.push({
      range: {
        start: { line: item.start.line - 1, character: item.start.offset - 1 },
        end: { line: item.end.line - 1, character: item.end.offset - 1 }
      },
      code: item.code,
      message: item.text,
      category: item.category
    });
  }
  return diagnostics;
}
function validLocation(location) {
  return location !== void 0 && Number.isInteger(location.line) && Number.isInteger(location.offset) && location.line >= 1 && location.offset >= 1;
}
export {
  typeCheckDiagnostics,
  typeCheckMethod,
  typeCheckVersion,
  validTypeCheckParams
};
