// src/nativeHtmlAttributes.ts
var citryDirectiveNames = /* @__PURE__ */ new Set(["c-if", "c-elif", "c-else", "c-for", "c-empty", "c-bind"]);
var rawTextTagNames = /* @__PURE__ */ new Set(["script", "style", "textarea", "title", "c-raw"]);
function projectNativeHtmlAttributes(source) {
  return scanHtml(source, []);
}
function htmlProjectionCandidateAt(source, offset) {
  return htmlProjectionCandidateRangeAt(source, offset) !== void 0;
}
function htmlProjectionCandidateRangeAt(source, offset) {
  if (offset < 0 || offset > source.length) {
    return void 0;
  }
  const candidates = [];
  scanHtml(source, candidates);
  return candidates.filter(({ start, end }) => start <= offset && offset <= end).sort((left, right) => left.end - left.start - (right.end - right.start))[0];
}
function scanHtml(source, htmlCandidates) {
  const projected = source.split("");
  const attributes = [];
  let index = 0;
  while (index < source.length) {
    if (source.startsWith("{#", index)) {
      const end = skipDelimited(source, index + 2, "#}");
      if (end === void 0) {
        break;
      }
      index = end;
      continue;
    }
    if (source.startsWith("{{", index)) {
      const end = skipPythonExpression(source, index + 2);
      if (end === void 0) {
        break;
      }
      index = end;
      continue;
    }
    if (source.startsWith("<!--", index)) {
      const end = skipDelimited(source, index + 4, "-->");
      if (end === void 0) {
        break;
      }
      index = end;
      continue;
    }
    if (source[index] !== "<") {
      index += 1;
      continue;
    }
    if (source.startsWith("</", index) || source.startsWith("<!", index) || source.startsWith("<?", index)) {
      const end = skipNonStartTag(source, index + 2);
      if (end === void 0) {
        break;
      }
      index = end;
      continue;
    }
    const tag = scanStartTag(source, index, projected, attributes, htmlCandidates);
    if (tag === void 0) {
      index += 1;
      continue;
    }
    index = tag.end;
    if (!tag.selfClosing && rawTextTagNames.has(tag.name)) {
      const closingStart = findRawTextClosingTag(source, index, tag.name);
      if (closingStart === void 0) {
        break;
      }
      index = closingStart;
    }
  }
  return { source: projected.join(""), attributes };
}
function nativeDynamicAttributeHoverProjection(source, offset) {
  const projection = projectNativeHtmlAttributes(source);
  const attribute = projection.attributes.find(
    (candidate) => candidate.sourceStart <= offset && offset <= candidate.sourceEnd
  );
  if (attribute === void 0) {
    return void 0;
  }
  const lastProviderOffset = attribute.projectedEnd - 1;
  const providerOffset = Math.max(attribute.projectedStart, Math.min(offset, lastProviderOffset));
  return { ...attribute, source: projection.source, providerOffset };
}
function scanStartTag(source, start, projected, attributes, htmlCandidates) {
  let index = start + 1;
  if (!isAsciiLetter(source[index])) {
    return void 0;
  }
  const nameStart = index;
  while (isTagNameCharacter(source[index])) {
    index += 1;
  }
  const authoredTagName = source.slice(nameStart, index);
  const name = asciiLowercase(authoredTagName);
  const eligibleTag = !authoredTagName.startsWith("c-");
  const cElementCandidateStart = authoredTagName.startsWith("c-") && asciiLowercase(authoredTagName.slice(2)) === "element" ? index : void 0;
  while (index < source.length) {
    index = skipWhitespace(source, index);
    if (source.startsWith("{#", index)) {
      const commentEnd = skipDelimited(source, index + 2, "#}");
      if (commentEnd === void 0) {
        return { name, end: source.length, selfClosing: false };
      }
      index = commentEnd;
      continue;
    }
    if (source.startsWith("/>", index)) {
      if (cElementCandidateStart !== void 0) {
        htmlCandidates.push({ start: cElementCandidateStart, end: index + 2 });
      }
      return { name, end: index + 2, selfClosing: true };
    }
    if (source[index] === ">") {
      if (cElementCandidateStart !== void 0) {
        htmlCandidates.push({ start: cElementCandidateStart, end: index + 1 });
      }
      return { name, end: index + 1, selfClosing: false };
    }
    if (source[index] === "<" || source.startsWith("{{", index)) {
      return { name, end: index + 1, selfClosing: false };
    }
    const attributeStart = index;
    while (index < source.length && isAttributeNameCharacter(source, index)) {
      index += 1;
    }
    if (index === attributeStart) {
      index += 1;
      continue;
    }
    const authoredName = source.slice(attributeStart, index);
    const nativeAttribute = eligibleTag ? nativeAttributeProjection(authoredName) : void 0;
    if (nativeAttribute !== void 0) {
      const { nativeName, prefixLength } = nativeAttribute;
      const projectedStart = attributeStart + prefixLength;
      for (let cursor = attributeStart; cursor < projectedStart; cursor += 1) {
        projected[cursor] = " ";
      }
      for (let cursor = projectedStart; cursor < index; cursor += 1) {
        projected[cursor] = asciiLowercase(source[cursor] ?? "");
      }
      attributes.push({
        authoredName,
        nativeName,
        sourceStart: attributeStart,
        sourceEnd: index,
        projectedStart,
        projectedEnd: index
      });
    }
    index = skipWhitespace(source, index);
    if (source[index] !== "=") {
      continue;
    }
    index = skipWhitespace(source, index + 1);
    const quote = source[index];
    if (quote === '"' || quote === "'") {
      const closingQuote = source.indexOf(quote, index + 1);
      if (closingQuote < 0) {
        return { name, end: source.length, selfClosing: false };
      }
      const valueStart = index + 1;
      const value = source.slice(valueStart, closingQuote).trim();
      if (authoredName.startsWith("c-") && nestedTemplateValue(value)) {
        htmlCandidates.push({ start: valueStart, end: closingQuote });
        const nestedCandidates = [];
        scanHtml(source.slice(valueStart, closingQuote), nestedCandidates);
        for (const candidate of nestedCandidates) {
          htmlCandidates.push({
            start: valueStart + candidate.start,
            end: valueStart + candidate.end
          });
        }
      }
      index = closingQuote + 1;
      continue;
    }
    while (index < source.length && !isWhitespace(source[index]) && source[index] !== ">" && !source.startsWith("{#", index)) {
      index += 1;
    }
  }
  return { name, end: source.length, selfClosing: false };
}
function nativeAttributeProjection(authoredName) {
  if (authoredName.startsWith("c-") && authoredName.length > 2 && !citryDirectiveNames.has(authoredName)) {
    return { nativeName: asciiLowercase(authoredName.slice(2)), prefixLength: 2 };
  }
  if (authoredName.startsWith(":c-")) {
    return void 0;
  }
  const alpineName = authoredName.startsWith(":") ? authoredName.slice(1) : "";
  if (!/^[A-Za-z_:][A-Za-z0-9_:-]*$/.test(alpineName)) {
    return void 0;
  }
  return { nativeName: asciiLowercase(alpineName), prefixLength: 1 };
}
function nestedTemplateValue(value) {
  return value.startsWith("<>") && value.endsWith("</>") || /^<[A-Za-z]/.test(value);
}
function skipPythonExpression(source, start) {
  const brackets = [];
  let index = start;
  while (index < source.length) {
    if (brackets.length === 0 && source.startsWith("}}", index)) {
      return index + 2;
    }
    const character = source[index];
    if (character === '"' || character === "'") {
      const delimiter = source.startsWith(character.repeat(3), index) ? character.repeat(3) : character;
      const stringEnd = skipPythonString(source, index + delimiter.length, delimiter);
      if (stringEnd === void 0) {
        return void 0;
      }
      index = stringEnd;
      continue;
    }
    if (character === "#") {
      const lineBreak = nextLineBreak(source, index + 1);
      const expressionEnd = brackets.length === 0 ? source.indexOf("}}", index + 1) : -1;
      if (expressionEnd >= 0 && (lineBreak < 0 || expressionEnd < lineBreak)) {
        return expressionEnd + 2;
      }
      if (lineBreak < 0) {
        return void 0;
      }
      index = lineBreak + 1;
      continue;
    }
    const closing = openingBracketClose(character);
    if (closing !== void 0) {
      brackets.push(closing);
      index += 1;
      continue;
    }
    if (character === ")" || character === "]" || character === "}") {
      if (brackets.at(-1) !== character) {
        return void 0;
      }
      brackets.pop();
    }
    index += 1;
  }
  return void 0;
}
function skipPythonString(source, start, delimiter) {
  for (let index = start; index < source.length; index += 1) {
    if (source.startsWith(delimiter, index) && !isEscaped(source, index)) {
      return index + delimiter.length;
    }
    if (delimiter.length === 1 && (source[index] === "\n" || source[index] === "\r")) {
      return void 0;
    }
  }
  return void 0;
}
function findRawTextClosingTag(source, start, name) {
  for (let index = start; index < source.length; index += 1) {
    if (!source.startsWith("</", index)) {
      continue;
    }
    const candidate = asciiLowercase(source.slice(index + 2, index + 2 + name.length));
    const boundary = source[index + 2 + name.length];
    if (candidate === name && (boundary === void 0 || isWhitespace(boundary) || boundary === ">")) {
      return index;
    }
  }
  return void 0;
}
function skipDelimited(source, start, delimiter) {
  const closing = source.indexOf(delimiter, start);
  return closing < 0 ? void 0 : closing + delimiter.length;
}
function skipNonStartTag(source, start) {
  let index = start;
  while (index < source.length) {
    if (source.startsWith("{#", index)) {
      const commentEnd = skipDelimited(source, index + 2, "#}");
      if (commentEnd === void 0) {
        return void 0;
      }
      index = commentEnd;
      continue;
    }
    const quote = source[index];
    if (quote === '"' || quote === "'") {
      const closingQuote = source.indexOf(quote, index + 1);
      if (closingQuote < 0) {
        return void 0;
      }
      index = closingQuote + 1;
      continue;
    }
    if (source[index] === ">") {
      return index + 1;
    }
    index += 1;
  }
  return void 0;
}
function skipWhitespace(source, start) {
  let index = start;
  while (isWhitespace(source[index])) {
    index += 1;
  }
  return index;
}
function nextLineBreak(source, start) {
  const newline = source.indexOf("\n", start);
  const carriageReturn = source.indexOf("\r", start);
  if (newline < 0) {
    return carriageReturn;
  }
  if (carriageReturn < 0) {
    return newline;
  }
  return Math.min(newline, carriageReturn);
}
function isEscaped(source, index) {
  let backslashes = 0;
  for (let cursor = index - 1; cursor >= 0 && source[cursor] === "\\"; cursor -= 1) {
    backslashes += 1;
  }
  return backslashes % 2 === 1;
}
function openingBracketClose(character) {
  return character === "(" ? ")" : character === "[" ? "]" : character === "{" ? "}" : void 0;
}
function isAsciiLetter(character) {
  return character !== void 0 && /[A-Za-z]/.test(character);
}
function isTagNameCharacter(character) {
  return character !== void 0 && /[A-Za-z0-9_:.-]/.test(character);
}
function isAttributeNameCharacter(source, index) {
  const character = source[index];
  return character !== void 0 && !isWhitespace(character) && character !== "=" && character !== "/" && character !== ">" && character !== "<" && !source.startsWith("{#", index);
}
function isWhitespace(character) {
  return character === " " || character === "	" || character === "\r" || character === "\n";
}
function asciiLowercase(value) {
  return value.replace(/[A-Z]/g, (character) => character.toLowerCase());
}
export {
  htmlProjectionCandidateAt,
  htmlProjectionCandidateRangeAt,
  nativeDynamicAttributeHoverProjection,
  projectNativeHtmlAttributes
};
