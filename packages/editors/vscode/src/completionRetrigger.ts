import { pythonTemplatePrefixAt } from "./embedded.js";

export interface TagCompletionChange {
	startOffset: number;
	removedLength: number;
	insertedText: string;
	history: boolean;
}

export interface TagCompletionRetriggerDecision {
	pendingOffset?: number;
	triggerOffset?: number;
}

const partialTagPattern = /<\/?c-[A-Za-z0-9_.-]*$/;
// Punctuation already has native LSP triggers; recovery is only needed for word characters.
const manualRetriggerCharacterPattern = /^[A-Za-z0-9_]$/;

export function advanceTagCompletionRetrigger(
	postEditSource: string,
	change: TagCompletionChange,
	pendingOffset: number | undefined,
): TagCompletionRetriggerDecision {
	const resultingOffset = change.startOffset + change.insertedText.length;
	const remainsInPartialTag = partialTagPattern.test(postEditSource.slice(0, resultingOffset));
	if (change.history) {
		return remainsInPartialTag ? { triggerOffset: resultingOffset } : {};
	}
	if (change.removedLength > 0 && change.insertedText.length === 0) {
		return remainsInPartialTag ? { pendingOffset: resultingOffset } : {};
	}
	const continuesPendingTag =
		pendingOffset === change.startOffset &&
		change.removedLength === 0 &&
		manualRetriggerCharacterPattern.test(change.insertedText) &&
		remainsInPartialTag;
	return continuesPendingTag ? { triggerOffset: resultingOffset } : {};
}

export function advanceExpressionCompletionRetrigger(
	postEditSource: string,
	languageId: string,
	change: TagCompletionChange,
	pendingOffset?: number,
): TagCompletionRetriggerDecision {
	const resultingOffset = change.startOffset + change.insertedText.length;
	const deletion = change.removedLength > 0 && change.insertedText.length === 0;
	let insertCanTrigger = false;
	if (!change.history && !deletion) {
		const insertedCharacters = [...change.insertedText];
		if (insertedCharacters.length !== 1 || !isPythonIdentifierStart(insertedCharacters[0] ?? "")) {
			return {};
		}
		const preceding = [...postEditSource.slice(0, change.startOffset)].at(-1);
		const startsIdentifier = preceding === undefined || (!isPythonIdentifierContinue(preceding) && preceding !== " ");
		insertCanTrigger = startsIdentifier || pendingOffset === change.startOffset;
		if (!insertCanTrigger) {
			return {};
		}
	}
	const templatePrefix = templatePrefixAt(postEditSource, languageId, resultingOffset);
	const insideExpression = templatePrefix !== undefined && hasOpenPythonHost(templatePrefix);
	if (change.history) {
		return insideExpression ? { triggerOffset: resultingOffset } : {};
	}
	if (deletion) {
		return insideExpression ? { pendingOffset: resultingOffset } : {};
	}
	return insideExpression && insertCanTrigger ? { triggerOffset: resultingOffset } : {};
}

function templatePrefixAt(source: string, languageId: string, offset: number): string | undefined {
	if (languageId === "citry-html") {
		return source.slice(0, offset);
	}
	if (languageId === "python") {
		return pythonTemplatePrefixAt(source, offset);
	}
	// The client cannot prove whether an ordinary HTML document is one of the
	// registry-owned template files claimed by the server.
	return undefined;
}

function hasOpenPythonHost(source: string): boolean {
	let index = 0;
	while (index < source.length) {
		if (source.startsWith("{#", index)) {
			const end = source.indexOf("#}", index + 2);
			if (end < 0) {
				return false;
			}
			index = end + 2;
			continue;
		}
		if (source.startsWith("{{", index)) {
			const expression = scanTemplateExpression(source, index);
			if (expression.end === undefined) {
				return expression.codeAtEnd;
			}
			index = expression.end;
			continue;
		}
		if (source.startsWith("<!--", index)) {
			const end = source.indexOf("-->", index + 4);
			if (end < 0) {
				return false;
			}
			index = end + 3;
			continue;
		}
		if (source[index] !== "<") {
			index += 1;
			continue;
		}
		const end = tagEnd(source, index);
		if (end === undefined) {
			const tagText = source.slice(index);
			if (/^<\s*[A-Za-z][\w:.-]*/u.test(tagText)) {
				return unfinishedTagHasPythonValue(tagText);
			}
			index += 1;
			continue;
		}
		const tagText = source.slice(index, end + 1);
		const tag = /^<\s*(\/?)\s*([A-Za-z][\w:.-]*)/u.exec(tagText);
		const tagName = tag?.[2]?.toLowerCase();
		if (tag?.[1] !== "/" && tagName !== undefined && rawTextTagNames.has(tagName)) {
			const rawEnd = rawTextEnd(source, end + 1, tagName);
			if (rawEnd === undefined) {
				return false;
			}
			const closeEnd = tagEnd(source, rawEnd);
			if (closeEnd === undefined) {
				return false;
			}
			index = closeEnd + 1;
			continue;
		}
		index = end + 1;
	}
	return false;
}

function unfinishedTagHasPythonValue(tagText: string): boolean {
	const current = unfinishedAttributeValue(tagText);
	if (current === undefined) {
		return false;
	}
	if (current.value.trimStart().startsWith("<")) {
		return hasOpenPythonHost(current.value);
	}
	const tagName = /^<\s*([A-Za-z][\w:.-]*)/u.exec(tagText)?.[1]?.toLowerCase();
	if (tagName === "c-fill" && (current.name === "name" || current.name === "data")) {
		return true;
	}
	const expressionAttribute =
		current.name === "#c-key" || current.name === "cond" || current.name === "each" || current.name.startsWith("c-");
	const browserBaseName = current.name.split(".", 1)[0] ?? current.name;
	const browserExpressionAttribute =
		current.name === "$c-props" ||
		current.name.startsWith("@") ||
		current.name.startsWith(":") ||
		browserBaseName === "x-for" ||
		current.name.startsWith("x-bind:") ||
		current.name.startsWith("x-on:") ||
		browserBaseName.startsWith("x-intersect:") ||
		new Set([
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
			"x-text",
		]).has(browserBaseName);
	return (expressionAttribute || browserExpressionAttribute) && pythonPrefixIsCode(current.value);
}

function unfinishedAttributeValue(tagText: string): { name: string; value: string } | undefined {
	let quote: string | undefined;
	let quoteStart: number | undefined;
	let escaped = false;
	for (let index = 0; index < tagText.length; index += 1) {
		if (quote === undefined && tagText.startsWith("{#", index)) {
			const commentEnd = tagText.indexOf("#}", index + 2);
			if (commentEnd < 0) {
				return undefined;
			}
			index = commentEnd + 1;
			continue;
		}
		const character = tagText[index];
		if (escaped) {
			escaped = false;
		} else if (character === "\\") {
			escaped = true;
		} else if (quote === undefined && (character === '"' || character === "'")) {
			quote = character;
			quoteStart = index;
		} else if (character === quote) {
			quote = undefined;
			quoteStart = undefined;
		}
	}
	if (quoteStart === undefined) {
		const unquoted = /(?:^|\s)([#$@:A-Za-z_][\w:.$@#-]*)\s*=\s*([^\s>]*)$/u.exec(tagText);
		const name = unquoted?.[1];
		const value = unquoted?.[2];
		return name === undefined || value === undefined ? undefined : { name, value };
	}
	const assignment = /([#$@:A-Za-z_][\w:.$@#-]*)\s*=\s*$/u.exec(tagText.slice(0, quoteStart));
	const name = assignment?.[1];
	return name === undefined ? undefined : { name, value: tagText.slice(quoteStart + 1) };
}

function tagEnd(source: string, start: number): number | undefined {
	let quote: string | undefined;
	for (let index = start + 1; index < source.length; index += 1) {
		if (quote === undefined && source.startsWith("{#", index)) {
			const commentEnd = source.indexOf("#}", index + 2);
			if (commentEnd < 0) {
				return undefined;
			}
			index = commentEnd + 1;
			continue;
		}
		const character = source[index];
		if (character === '"' || character === "'") {
			quote = quote === character ? undefined : quote === undefined ? character : quote;
		} else if (character === ">" && quote === undefined) {
			return index;
		}
	}
	return undefined;
}

function scanTemplateExpression(source: string, start: number): { end?: number; codeAtEnd: boolean } {
	let index = start + 2;
	let quote: string | undefined;
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
		if (quote !== undefined) {
			const delimiter = quote.repeat(triple ? 3 : 1);
			if (!escaped && source.startsWith(delimiter, index)) {
				index += delimiter.length;
				quote = undefined;
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
	return { codeAtEnd: (quote === undefined && !comment) || fStringReplacementIsCode(expressionPrefix) };
}

function pythonPrefixIsCode(source: string): boolean {
	let quote: string | undefined;
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
		if (quote !== undefined) {
			const delimiter = quote.repeat(triple ? 3 : 1);
			if (!escaped && source.startsWith(delimiter, index)) {
				index += delimiter.length - 1;
				quote = undefined;
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
	return (quote === undefined && !comment) || fStringReplacementIsCode(source);
}

function fStringReplacementIsCode(source: string): boolean {
	const starts = [...source.matchAll(/(?:^|[^\p{ID_Continue}])(?:[fF][rR]?|[rR][fF])("""|'''|"|')/gu)];
	for (const match of starts.reverse()) {
		const delimiter = match[1];
		if (delimiter === undefined || match.index === undefined) {
			continue;
		}
		const quoteStart = match.index + match[0].lastIndexOf(delimiter);
		const state = scanFString(source, quoteStart + delimiter.length, delimiter);
		if (state !== undefined) {
			return state;
		}
	}
	return false;
}

function scanFString(source: string, start: number, delimiter: string): boolean | undefined {
	let depth = 0;
	let quote: string | undefined;
	let triple = false;
	let escaped = false;
	let comment = false;
	for (let index = start; index < source.length; index += 1) {
		const character = source[index];
		if (depth === 0) {
			if (source.startsWith(delimiter, index)) {
				return undefined;
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
		if (quote !== undefined) {
			const innerDelimiter = quote.repeat(triple ? 3 : 1);
			if (!escaped && source.startsWith(innerDelimiter, index)) {
				index += innerDelimiter.length - 1;
				quote = undefined;
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
	return depth > 0 && quote === undefined && !comment;
}

const rawTextTagNames = new Set(["script", "style", "textarea", "title", "c-raw"]);

function rawTextEnd(source: string, start: number, tagName: string): number | undefined {
	const match = new RegExp(`</\\s*${tagName.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&")}(?:\\s|>)`, "iu").exec(
		source.slice(start),
	);
	return match?.index === undefined ? undefined : start + match.index;
}

function isPythonIdentifierStart(character: string): boolean {
	return character === "_" || /^\p{ID_Start}$/u.test(character);
}

function isPythonIdentifierContinue(character: string): boolean {
	return character === "_" || /^\p{ID_Continue}$/u.test(character);
}
