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
function embeddedVirtualDocumentAt(source, languageId, offset) {
  if (languageId === "citry-html") {
    return offset >= 0 && offset <= source.length ? { language: "html", source } : void 0;
  }
  if (languageId !== "python") {
    return void 0;
  }
  const regions = pythonEmbeddedRegions(source);
  const region = regions.find((candidate) => candidate.start <= offset && offset <= candidate.end);
  return region === void 0 ? void 0 : { language: region.language, source: virtualDocumentSourceFromRegions(source, region.language, regions) };
}
function virtualDocumentSourceFromRegions(source, language, regions) {
  const masked = source.split("").map((character) => character === "\n" || character === "\r" ? character : " ");
  for (const region of regions) {
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

// src/browserRouting.ts
var rawTextTags = /* @__PURE__ */ new Set(["script", "style", "textarea", "title", "c-raw"]);
function browserProjectionCandidateAt(source, languageId, offset) {
  if (languageId === "javascript") {
    return offset >= 0 && offset <= source.length;
  }
  const view = embeddedVirtualDocumentAt(source, languageId, offset);
  if (view?.language === "javascript") {
    return true;
  }
  const html = languageId === "html" ? source : view?.language === "html" ? view.source : void 0;
  if (html === void 0) {
    return false;
  }
  return browserRanges(html, 0, html.length).some(({ start, end }) => start <= offset && offset <= end);
}
function browserRanges(source, start, end) {
  const ranges = [];
  let index = start;
  while (index < end) {
    const tagStart = source.indexOf("<", index);
    if (tagStart < 0 || tagStart >= end) {
      break;
    }
    if (source.startsWith("<!--", tagStart)) {
      const close = source.indexOf("-->", tagStart + 4);
      index = close < 0 ? end : close + 3;
      continue;
    }
    if (!isAsciiLetter(source[tagStart + 1])) {
      index = tagStart + 1;
      continue;
    }
    const scanned = scanStartTag(source, tagStart, end, ranges);
    if (scanned === void 0) {
      index = tagStart + 1;
      continue;
    }
    index = scanned.end;
    if (rawTextTags.has(scanned.name) && !scanned.selfClosing) {
      const closing = source.toLowerCase().indexOf(`</${scanned.name}`, index);
      index = closing < 0 ? end : closing;
    }
  }
  return ranges;
}
function scanStartTag(source, start, limit, ranges) {
  let index = start + 1;
  const nameStart = index;
  while (isTagNameCharacter(source[index])) {
    index += 1;
  }
  if (index === nameStart) {
    return void 0;
  }
  const name = source.slice(nameStart, index).toLowerCase();
  while (index < limit) {
    index = skipWhitespace(source, index);
    if (source.startsWith("{#", index)) {
      const close = source.indexOf("#}", index + 2);
      if (close < 0 || close >= limit) {
        return { name, end: limit, selfClosing: false };
      }
      index = close + 2;
      continue;
    }
    if (source.startsWith("/>", index)) {
      return { name, end: index + 2, selfClosing: true };
    }
    if (source[index] === ">") {
      return { name, end: index + 1, selfClosing: false };
    }
    const attributeStart = index;
    while (isAttributeNameCharacter(source[index])) {
      index += 1;
    }
    if (index === attributeStart) {
      index += 1;
      continue;
    }
    const attributeName = source.slice(attributeStart, index);
    index = skipWhitespace(source, index);
    if (source[index] !== "=") {
      continue;
    }
    index = skipWhitespace(source, index + 1);
    const quote = source[index];
    let valueStart = index;
    let valueEnd = index;
    if (quote === '"' || quote === "'") {
      valueStart = index + 1;
      const close = source.indexOf(quote, valueStart);
      valueEnd = close < 0 || close > limit ? limit : close;
      index = valueEnd < limit ? valueEnd + 1 : limit;
    } else {
      valueStart = index;
      while (index < limit && !isWhitespace(source[index]) && source[index] !== ">") {
        index += 1;
      }
      valueEnd = index;
    }
    if (isBrowserAttribute(attributeName)) {
      ranges.push({ start: valueStart, end: valueEnd });
    }
    if (source.slice(valueStart, valueEnd).trimStart().startsWith("<")) {
      ranges.push(...browserRanges(source, valueStart, valueEnd));
    }
  }
  return { name, end: limit, selfClosing: false };
}
function isBrowserAttribute(name) {
  const base = name.split(".", 1)[0] ?? name;
  return name === "$c-props" || name.startsWith("@") || name.startsWith(":") && !name.startsWith(":c-") || base.startsWith("x-");
}
function skipWhitespace(source, index) {
  while (/\s/u.test(source[index] ?? "")) {
    index += 1;
  }
  return index;
}
function isWhitespace(character) {
  return character !== void 0 && /\s/u.test(character);
}
function isAsciiLetter(character) {
  return character !== void 0 && /[A-Za-z]/u.test(character);
}
function isTagNameCharacter(character) {
  return character !== void 0 && /[A-Za-z0-9:._-]/u.test(character);
}
function isAttributeNameCharacter(character) {
  return character !== void 0 && !/[\s=/>]/u.test(character);
}
export {
  browserProjectionCandidateAt
};
