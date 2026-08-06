// src/embedded.ts
var assignmentPattern = /^[\t ]*(template|js|css)[\t ]*(?::[^=\r\n]+?)?[\t ]*=[\t ]*("""|''')/gm;
var languageByAttribute = {
  template: "html",
  js: "javascript",
  css: "css"
};
function pythonEmbeddedRegions(source) {
  const { excluded, strings } = scanPython(source);
  const regions = [];
  for (const match of source.matchAll(assignmentPattern)) {
    const attribute = match[1];
    const delimiter = match[2];
    if (attribute === void 0 || delimiter !== '"""' && delimiter !== "'''") {
      continue;
    }
    const matchStart = match.index;
    if (spanContaining(excluded, matchStart) !== void 0) {
      continue;
    }
    const quoteStart = matchStart + match[0].lastIndexOf(delimiter);
    const string = strings.find((span) => span.start === quoteStart && span.delimiter === delimiter);
    const language = languageByAttribute[attribute];
    if (string !== void 0 && language !== void 0) {
      regions.push({ language, start: string.bodyStart, end: string.bodyEnd });
    }
  }
  return regions;
}
function embeddedLanguageAt(source, languageId, offset) {
  if (languageId === "citry-html") {
    return offset >= 0 && offset <= source.length ? "html" : void 0;
  }
  if (languageId !== "python") {
    return void 0;
  }
  return pythonEmbeddedRegions(source).find((region) => region.start <= offset && offset <= region.end)?.language;
}
function virtualDocumentSource(source, languageId, language) {
  if (languageId === "citry-html" && language === "html") {
    return source;
  }
  const masked = source.split("").map((character) => character === "\n" || character === "\r" ? character : " ");
  if (languageId !== "python") {
    return masked.join("");
  }
  for (const region of pythonEmbeddedRegions(source)) {
    if (region.language !== language) {
      continue;
    }
    for (let index = region.start; index < region.end; index += 1) {
      masked[index] = source[index] ?? " ";
    }
  }
  return masked.join("");
}
function scanPython(source) {
  const excluded = [];
  const strings = [];
  let index = 0;
  while (index < source.length) {
    const character = source[index];
    if (character === "#") {
      const end2 = lineEnd(source, index);
      excluded.push({ start: index, end: end2 });
      index = end2;
      continue;
    }
    if (character !== '"' && character !== "'") {
      index += 1;
      continue;
    }
    const triple = source.startsWith(character.repeat(3), index);
    const delimiter = triple ? character.repeat(3) : character;
    const bodyStart = index + delimiter.length;
    const closing = closingDelimiter(source, bodyStart, delimiter);
    const bodyEnd = closing ?? (triple ? source.length : lineEnd(source, bodyStart));
    const end = closing === void 0 ? bodyEnd : closing + delimiter.length;
    const span = { start: index, end, bodyStart, bodyEnd, delimiter };
    strings.push(span);
    excluded.push(span);
    index = Math.max(end, index + delimiter.length);
  }
  return { excluded, strings };
}
function closingDelimiter(source, start, delimiter) {
  for (let index = start; index < source.length; index += 1) {
    if (delimiter.length === 1 && (source[index] === "\n" || source[index] === "\r")) {
      return void 0;
    }
    if (source.startsWith(delimiter, index) && !isEscaped(source, index)) {
      return index;
    }
  }
  return void 0;
}
function isEscaped(source, index) {
  let backslashes = 0;
  for (let cursor = index - 1; cursor >= 0 && source[cursor] === "\\"; cursor -= 1) {
    backslashes += 1;
  }
  return backslashes % 2 === 1;
}
function lineEnd(source, start) {
  const newline = source.indexOf("\n", start);
  return newline < 0 ? source.length : newline;
}
function spanContaining(spans, offset) {
  return spans.find((span) => span.start <= offset && offset < span.end);
}
export {
  embeddedLanguageAt,
  pythonEmbeddedRegions,
  virtualDocumentSource
};
