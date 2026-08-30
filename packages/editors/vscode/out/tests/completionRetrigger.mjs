// src/embedded.ts
var templateLiteralAssignmentPattern = /^[\t ]*template[\t ]*(?::[^=\r\n]+?)?[\t ]*=[\t ]*[rRuU]?("""|'''|"|')/gm;
function pythonTemplatePrefixAt(source, offset) {
  if (offset < 0 || offset > source.length) {
    return void 0;
  }
  const { excluded, strings } = scanPython(source);
  for (const match of source.matchAll(templateLiteralAssignmentPattern)) {
    const delimiter = match[1];
    if (match.index === void 0 || delimiter !== '"""' && delimiter !== "'''" && delimiter !== '"' && delimiter !== "'" || spanContaining(excluded, match.index) !== void 0) {
      continue;
    }
    const quoteStart = match.index + match[0].lastIndexOf(delimiter);
    const string = strings.find((span) => span.start === quoteStart && span.delimiter === delimiter);
    if (string !== void 0 && string.bodyStart <= offset && offset <= string.bodyEnd) {
      return source.slice(string.bodyStart, offset);
    }
  }
  return void 0;
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

// src/completionRetrigger.ts
var partialTagPattern = /<\/?c-[A-Za-z0-9_.-]*$/;
var manualRetriggerCharacterPattern = /^[A-Za-z0-9_]$/;
function advanceTagCompletionRetrigger(postEditSource, change, pendingOffset) {
  const resultingOffset = change.startOffset + change.insertedText.length;
  const remainsInPartialTag = partialTagPattern.test(postEditSource.slice(0, resultingOffset));
  if (change.history) {
    return remainsInPartialTag ? { triggerOffset: resultingOffset } : {};
  }
  if (change.removedLength > 0 && change.insertedText.length === 0) {
    return remainsInPartialTag ? { pendingOffset: resultingOffset } : {};
  }
  const continuesPendingTag = pendingOffset === change.startOffset && change.removedLength === 0 && manualRetriggerCharacterPattern.test(change.insertedText) && remainsInPartialTag;
  return continuesPendingTag ? { triggerOffset: resultingOffset } : {};
}
function advanceExpressionCompletionRetrigger(postEditSource, languageId, change, pendingOffset) {
  const resultingOffset = change.startOffset + change.insertedText.length;
  const deletion = change.removedLength > 0 && change.insertedText.length === 0;
  let insertCanTrigger = false;
  if (!change.history && !deletion) {
    const insertedCharacters = [...change.insertedText];
    if (insertedCharacters.length !== 1 || !isPythonIdentifierStart(insertedCharacters[0] ?? "")) {
      return {};
    }
    const preceding = [...postEditSource.slice(0, change.startOffset)].at(-1);
    const startsIdentifier = preceding === void 0 || !isPythonIdentifierContinue(preceding) && preceding !== " ";
    insertCanTrigger = startsIdentifier || pendingOffset === change.startOffset;
    if (!insertCanTrigger) {
      return {};
    }
  }
  const templatePrefix = templatePrefixAt(postEditSource, languageId, resultingOffset);
  const insideExpression = templatePrefix !== void 0 && hasOpenPythonHost(templatePrefix);
  if (change.history) {
    return insideExpression ? { triggerOffset: resultingOffset } : {};
  }
  if (deletion) {
    return insideExpression ? { pendingOffset: resultingOffset } : {};
  }
  return insideExpression && insertCanTrigger ? { triggerOffset: resultingOffset } : {};
}
function templatePrefixAt(source, languageId, offset) {
  if (languageId === "citry-html") {
    return source.slice(0, offset);
  }
  if (languageId === "python") {
    return pythonTemplatePrefixAt(source, offset);
  }
  return void 0;
}
function hasOpenPythonHost(source) {
  let index = 0;
  while (index < source.length) {
    if (source.startsWith("{#", index)) {
      const end2 = source.indexOf("#}", index + 2);
      if (end2 < 0) {
        return false;
      }
      index = end2 + 2;
      continue;
    }
    if (source.startsWith("{{", index)) {
      const expression = scanTemplateExpression(source, index);
      if (expression.end === void 0) {
        return expression.codeAtEnd;
      }
      index = expression.end;
      continue;
    }
    if (source.startsWith("<!--", index)) {
      const end2 = source.indexOf("-->", index + 4);
      if (end2 < 0) {
        return false;
      }
      index = end2 + 3;
      continue;
    }
    if (source[index] !== "<") {
      index += 1;
      continue;
    }
    const end = tagEnd(source, index);
    if (end === void 0) {
      const tagText2 = source.slice(index);
      if (/^<\s*[A-Za-z][\w:.-]*/u.test(tagText2)) {
        return unfinishedTagHasPythonValue(tagText2);
      }
      index += 1;
      continue;
    }
    const tagText = source.slice(index, end + 1);
    const tag = /^<\s*(\/?)\s*([A-Za-z][\w:.-]*)/u.exec(tagText);
    const tagName = tag?.[2]?.toLowerCase();
    if (tag?.[1] !== "/" && tagName !== void 0 && rawTextTagNames.has(tagName)) {
      const rawEnd = rawTextEnd(source, end + 1, tagName);
      if (rawEnd === void 0) {
        return false;
      }
      const closeEnd = tagEnd(source, rawEnd);
      if (closeEnd === void 0) {
        return false;
      }
      index = closeEnd + 1;
      continue;
    }
    index = end + 1;
  }
  return false;
}
function unfinishedTagHasPythonValue(tagText) {
  const current = unfinishedAttributeValue(tagText);
  if (current === void 0) {
    return false;
  }
  if (current.value.trimStart().startsWith("<")) {
    return hasOpenPythonHost(current.value);
  }
  const tagName = /^<\s*([A-Za-z][\w:.-]*)/u.exec(tagText)?.[1]?.toLowerCase();
  if (tagName === "c-fill" && (current.name === "name" || current.name === "data")) {
    return true;
  }
  const expressionAttribute = current.name === "#c-key" || current.name === "cond" || current.name === "each" || current.name.startsWith("c-");
  const citryHandlerAttribute = current.name.startsWith("@c-") || current.name.startsWith(":c-");
  const browserBaseName = current.name.split(".", 1)[0] ?? current.name;
  const browserExpressionAttribute = current.name === "$c-props" || current.name.startsWith("@") || current.name.startsWith(":") && !current.name.startsWith(":c-") || browserBaseName === "x-for" || current.name.startsWith("x-bind:") || current.name.startsWith("x-on:") || browserBaseName.startsWith("x-intersect:") || (/* @__PURE__ */ new Set([
    "x-bind",
    "x-data",
    "x-effect",
    "x-html",
    "x-id",
    "x-if",
    "x-init",
    "x-intersect",
    "x-model",
    "x-modelable",
    "x-on",
    "x-show",
    "x-text"
  ])).has(browserBaseName);
  return (expressionAttribute || citryHandlerAttribute || browserExpressionAttribute) && pythonPrefixIsCode(current.value);
}
function unfinishedAttributeValue(tagText) {
  let quote;
  let quoteStart;
  let escaped = false;
  for (let index = 0; index < tagText.length; index += 1) {
    if (quote === void 0 && tagText.startsWith("{#", index)) {
      const commentEnd = tagText.indexOf("#}", index + 2);
      if (commentEnd < 0) {
        return void 0;
      }
      index = commentEnd + 1;
      continue;
    }
    const character = tagText[index];
    if (escaped) {
      escaped = false;
    } else if (character === "\\") {
      escaped = true;
    } else if (quote === void 0 && (character === '"' || character === "'")) {
      quote = character;
      quoteStart = index;
    } else if (character === quote) {
      quote = void 0;
      quoteStart = void 0;
    }
  }
  if (quoteStart === void 0) {
    const unquoted = /(?:^|\s)([#$@:A-Za-z_][\w:.$@#-]*)\s*=\s*([^\s>]*)$/u.exec(tagText);
    const name2 = unquoted?.[1];
    const value = unquoted?.[2];
    return name2 === void 0 || value === void 0 ? void 0 : { name: name2, value };
  }
  const assignment = /([#$@:A-Za-z_][\w:.$@#-]*)\s*=\s*$/u.exec(tagText.slice(0, quoteStart));
  const name = assignment?.[1];
  return name === void 0 ? void 0 : { name, value: tagText.slice(quoteStart + 1) };
}
function tagEnd(source, start) {
  let quote;
  for (let index = start + 1; index < source.length; index += 1) {
    if (quote === void 0 && source.startsWith("{#", index)) {
      const commentEnd = source.indexOf("#}", index + 2);
      if (commentEnd < 0) {
        return void 0;
      }
      index = commentEnd + 1;
      continue;
    }
    const character = source[index];
    if (character === '"' || character === "'") {
      quote = quote === character ? void 0 : quote === void 0 ? character : quote;
    } else if (character === ">" && quote === void 0) {
      return index;
    }
  }
  return void 0;
}
function scanTemplateExpression(source, start) {
  let index = start + 2;
  let quote;
  let triple = false;
  let escaped = false;
  let comment = false;
  let roundDepth = 0;
  let squareDepth = 0;
  let curlyDepth = 0;
  while (index < source.length) {
    if (comment) {
      if (source.startsWith("}}", index)) {
        return { end: index + 2, codeAtEnd: false };
      }
      if (source[index] === "\r" || source[index] === "\n") {
        comment = false;
      }
      index += 1;
      continue;
    }
    if (quote !== void 0) {
      const delimiter = quote.repeat(triple ? 3 : 1);
      if (!escaped && source.startsWith(delimiter, index)) {
        index += delimiter.length;
        quote = void 0;
        triple = false;
        continue;
      }
      if (escaped) {
        escaped = false;
      } else if (source[index] === "\\") {
        escaped = true;
      }
      index += 1;
      continue;
    }
    if (source.startsWith("}}", index) && roundDepth === 0 && squareDepth === 0 && curlyDepth === 0) {
      return { end: index + 2, codeAtEnd: false };
    }
    const character = source[index];
    if (character === "#") {
      comment = true;
    } else if (character === '"' || character === "'") {
      quote = character;
      triple = source.startsWith(character.repeat(3), index);
      if (triple) {
        index += 2;
      }
    } else if (character === "(") {
      roundDepth += 1;
    } else if (character === ")" && roundDepth > 0) {
      roundDepth -= 1;
    } else if (character === "[") {
      squareDepth += 1;
    } else if (character === "]" && squareDepth > 0) {
      squareDepth -= 1;
    } else if (character === "{") {
      curlyDepth += 1;
    } else if (character === "}" && curlyDepth > 0) {
      curlyDepth -= 1;
    }
    index += 1;
  }
  const expressionPrefix = source.slice(start + 2);
  return { codeAtEnd: quote === void 0 && !comment || fStringReplacementIsCode(expressionPrefix) };
}
function pythonPrefixIsCode(source) {
  let quote;
  let triple = false;
  let escaped = false;
  let comment = false;
  for (let index = 0; index < source.length; index += 1) {
    const character = source[index];
    if (comment) {
      if (character === "\r" || character === "\n") {
        comment = false;
      }
      continue;
    }
    if (quote !== void 0) {
      const delimiter = quote.repeat(triple ? 3 : 1);
      if (!escaped && source.startsWith(delimiter, index)) {
        index += delimiter.length - 1;
        quote = void 0;
        triple = false;
        continue;
      }
      if (escaped) {
        escaped = false;
      } else if (character === "\\") {
        escaped = true;
      }
      continue;
    }
    if (character === "#") {
      comment = true;
    } else if (character === '"' || character === "'") {
      quote = character;
      triple = source.startsWith(character.repeat(3), index);
      if (triple) {
        index += 2;
      }
    }
  }
  return quote === void 0 && !comment || fStringReplacementIsCode(source);
}
function fStringReplacementIsCode(source) {
  const starts = [...source.matchAll(/(?:^|[^\p{ID_Continue}])(?:[fF][rR]?|[rR][fF])("""|'''|"|')/gu)];
  for (const match of starts.reverse()) {
    const delimiter = match[1];
    if (delimiter === void 0 || match.index === void 0) {
      continue;
    }
    const quoteStart = match.index + match[0].lastIndexOf(delimiter);
    const state = scanFString(source, quoteStart + delimiter.length, delimiter);
    if (state !== void 0) {
      return state;
    }
  }
  return false;
}
function scanFString(source, start, delimiter) {
  let depth = 0;
  let quote;
  let triple = false;
  let escaped = false;
  let comment = false;
  for (let index = start; index < source.length; index += 1) {
    const character = source[index];
    if (depth === 0) {
      if (source.startsWith(delimiter, index)) {
        return void 0;
      }
      if (source.startsWith("{{", index) || source.startsWith("}}", index)) {
        index += 1;
        continue;
      }
      if (character === "{") {
        depth = 1;
      }
      continue;
    }
    if (comment) {
      if (character === "\r" || character === "\n") {
        comment = false;
      }
      continue;
    }
    if (quote !== void 0) {
      const innerDelimiter = quote.repeat(triple ? 3 : 1);
      if (!escaped && source.startsWith(innerDelimiter, index)) {
        index += innerDelimiter.length - 1;
        quote = void 0;
        triple = false;
        continue;
      }
      if (escaped) {
        escaped = false;
      } else if (character === "\\") {
        escaped = true;
      }
      continue;
    }
    if (character === "#") {
      comment = true;
    } else if (character === '"' || character === "'") {
      quote = character;
      triple = source.startsWith(character.repeat(3), index);
      if (triple) {
        index += 2;
      }
    } else if (character === "{") {
      depth += 1;
    } else if (character === "}") {
      depth -= 1;
    }
  }
  return depth > 0 && quote === void 0 && !comment;
}
var rawTextTagNames = /* @__PURE__ */ new Set(["script", "style", "textarea", "title", "c-raw"]);
function rawTextEnd(source, start, tagName) {
  const match = new RegExp(`</\\s*${tagName.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&")}(?:\\s|>)`, "iu").exec(
    source.slice(start)
  );
  return match?.index === void 0 ? void 0 : start + match.index;
}
function isPythonIdentifierStart(character) {
  return character === "_" || new RegExp("^\\p{ID_Start}$", "u").test(character);
}
function isPythonIdentifierContinue(character) {
  return character === "_" || new RegExp("^\\p{ID_Continue}$", "u").test(character);
}
export {
  advanceExpressionCompletionRetrigger,
  advanceTagCompletionRetrigger
};
