const citryDirectiveNames = new Set(["c-if", "c-elif", "c-else", "c-for", "c-empty", "c-bind"]);
const rawTextTagNames = new Set(["script", "style", "textarea", "title", "c-raw"]);

export interface ProjectedNativeAttribute {
	authoredName: string;
	nativeName: string;
	sourceStart: number;
	sourceEnd: number;
	projectedStart: number;
	projectedEnd: number;
}

export interface NativeHtmlAttributeProjection {
	source: string;
	attributes: ProjectedNativeAttribute[];
}

export interface HtmlProjectionCandidate {
	start: number;
	end: number;
}

export interface NativeDynamicAttributeHoverProjection extends ProjectedNativeAttribute {
	source: string;
	providerOffset: number;
}

/**
 * Build a same-length HTML view in which candidate `c-*` attributes on
 * ordinary start tags look native to an installed HTML provider.
 *
 * This is intentionally only a lexical candidate pass. The provider decides
 * whether the projected suffix is a real attribute, and the caller accepts a
 * hover only when the provider returns that exact suffix range.
 */
export function projectNativeHtmlAttributes(source: string): NativeHtmlAttributeProjection {
	return scanHtml(source, []);
}

/**
 * Cheaply identify positions that may need the parser-backed HTML projection.
 * This is only an activation filter; the language server remains authoritative.
 */
export function htmlProjectionCandidateAt(source: string, offset: number): boolean {
	return htmlProjectionCandidateRangeAt(source, offset) !== undefined;
}

/** Return the deepest lexical host so one parser result can serve that range. */
export function htmlProjectionCandidateRangeAt(source: string, offset: number): HtmlProjectionCandidate | undefined {
	if (offset < 0 || offset > source.length) {
		return undefined;
	}
	const candidates: HtmlProjectionCandidate[] = [];
	scanHtml(source, candidates);
	return candidates
		.filter(({ start, end }) => start <= offset && offset <= end)
		.sort((left, right) => left.end - left.start - (right.end - right.start))[0];
}

function scanHtml(source: string, htmlCandidates: HtmlProjectionCandidate[]): NativeHtmlAttributeProjection {
	const projected = source.split("");
	const attributes: ProjectedNativeAttribute[] = [];
	let index = 0;

	while (index < source.length) {
		if (source.startsWith("{#", index)) {
			const end = skipDelimited(source, index + 2, "#}");
			if (end === undefined) {
				break;
			}
			index = end;
			continue;
		}
		if (source.startsWith("{{", index)) {
			const end = skipPythonExpression(source, index + 2);
			if (end === undefined) {
				break;
			}
			index = end;
			continue;
		}
		if (source.startsWith("<!--", index)) {
			const end = skipDelimited(source, index + 4, "-->");
			if (end === undefined) {
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
			if (end === undefined) {
				break;
			}
			index = end;
			continue;
		}

		const tag = scanStartTag(source, index, projected, attributes, htmlCandidates);
		if (tag === undefined) {
			index += 1;
			continue;
		}
		index = tag.end;
		if (!tag.selfClosing && rawTextTagNames.has(tag.name)) {
			const closingStart = findRawTextClosingTag(source, index, tag.name);
			if (closingStart === undefined) {
				break;
			}
			index = closingStart;
		}
	}

	return { source: projected.join(""), attributes };
}

export function nativeDynamicAttributeHoverProjection(
	source: string,
	offset: number,
): NativeDynamicAttributeHoverProjection | undefined {
	const projection = projectNativeHtmlAttributes(source);
	const attribute = projection.attributes.find(
		(candidate) => candidate.sourceStart <= offset && offset <= candidate.sourceEnd,
	);
	if (attribute === undefined) {
		return undefined;
	}
	const lastProviderOffset = attribute.projectedEnd - 1;
	const providerOffset = Math.max(attribute.projectedStart, Math.min(offset, lastProviderOffset));
	return { ...attribute, source: projection.source, providerOffset };
}

interface ScannedStartTag {
	name: string;
	end: number;
	selfClosing: boolean;
}

function scanStartTag(
	source: string,
	start: number,
	projected: string[],
	attributes: ProjectedNativeAttribute[],
	htmlCandidates: HtmlProjectionCandidate[],
): ScannedStartTag | undefined {
	let index = start + 1;
	if (!isAsciiLetter(source[index])) {
		return undefined;
	}
	const nameStart = index;
	while (isTagNameCharacter(source[index])) {
		index += 1;
	}
	const authoredTagName = source.slice(nameStart, index);
	const name = asciiLowercase(authoredTagName);
	const eligibleTag = !authoredTagName.startsWith("c-");
	const cElementCandidateStart =
		authoredTagName.startsWith("c-") && asciiLowercase(authoredTagName.slice(2)) === "element" ? index : undefined;

	while (index < source.length) {
		index = skipWhitespace(source, index);
		if (source.startsWith("{#", index)) {
			const commentEnd = skipDelimited(source, index + 2, "#}");
			if (commentEnd === undefined) {
				return { name, end: source.length, selfClosing: false };
			}
			index = commentEnd;
			continue;
		}
		if (source.startsWith("/>", index)) {
			if (cElementCandidateStart !== undefined) {
				htmlCandidates.push({ start: cElementCandidateStart, end: index + 2 });
			}
			return { name, end: index + 2, selfClosing: true };
		}
		if (source[index] === ">") {
			if (cElementCandidateStart !== undefined) {
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
		if (
			eligibleTag &&
			authoredName.startsWith("c-") &&
			authoredName.length > 2 &&
			!citryDirectiveNames.has(authoredName)
		) {
			const nativeName = asciiLowercase(authoredName.slice(2));
			const projectedStart = attributeStart + 2;
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
				projectedEnd: index,
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
				// A deeper template needs its own cache identity because the server
				// selects the deepest fragment that contains the current cursor.
				const nestedCandidates: HtmlProjectionCandidate[] = [];
				scanHtml(source.slice(valueStart, closingQuote), nestedCandidates);
				for (const candidate of nestedCandidates) {
					htmlCandidates.push({
						start: valueStart + candidate.start,
						end: valueStart + candidate.end,
					});
				}
			}
			index = closingQuote + 1;
			continue;
		}
		while (
			index < source.length &&
			!isWhitespace(source[index]) &&
			source[index] !== ">" &&
			!source.startsWith("{#", index)
		) {
			index += 1;
		}
	}

	return { name, end: source.length, selfClosing: false };
}

function nestedTemplateValue(value: string): boolean {
	return (value.startsWith("<>") && value.endsWith("</>")) || /^<[A-Za-z]/.test(value);
}

function skipPythonExpression(source: string, start: number): number | undefined {
	const brackets: string[] = [];
	let index = start;
	while (index < source.length) {
		if (brackets.length === 0 && source.startsWith("}}", index)) {
			return index + 2;
		}
		const character = source[index];
		if (character === '"' || character === "'") {
			const delimiter = source.startsWith(character.repeat(3), index) ? character.repeat(3) : character;
			const stringEnd = skipPythonString(source, index + delimiter.length, delimiter);
			if (stringEnd === undefined) {
				return undefined;
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
				return undefined;
			}
			index = lineBreak + 1;
			continue;
		}
		const closing = openingBracketClose(character);
		if (closing !== undefined) {
			brackets.push(closing);
			index += 1;
			continue;
		}
		if (character === ")" || character === "]" || character === "}") {
			if (brackets.at(-1) !== character) {
				return undefined;
			}
			brackets.pop();
		}
		index += 1;
	}
	return undefined;
}

function skipPythonString(source: string, start: number, delimiter: string): number | undefined {
	for (let index = start; index < source.length; index += 1) {
		if (source.startsWith(delimiter, index) && !isEscaped(source, index)) {
			return index + delimiter.length;
		}
		if (delimiter.length === 1 && (source[index] === "\n" || source[index] === "\r")) {
			return undefined;
		}
	}
	return undefined;
}

function findRawTextClosingTag(source: string, start: number, name: string): number | undefined {
	for (let index = start; index < source.length; index += 1) {
		if (!source.startsWith("</", index)) {
			continue;
		}
		const candidate = asciiLowercase(source.slice(index + 2, index + 2 + name.length));
		const boundary = source[index + 2 + name.length];
		if (candidate === name && (boundary === undefined || isWhitespace(boundary) || boundary === ">")) {
			return index;
		}
	}
	return undefined;
}

function skipDelimited(source: string, start: number, delimiter: string): number | undefined {
	const closing = source.indexOf(delimiter, start);
	return closing < 0 ? undefined : closing + delimiter.length;
}

function skipNonStartTag(source: string, start: number): number | undefined {
	let index = start;
	while (index < source.length) {
		if (source.startsWith("{#", index)) {
			const commentEnd = skipDelimited(source, index + 2, "#}");
			if (commentEnd === undefined) {
				return undefined;
			}
			index = commentEnd;
			continue;
		}
		const quote = source[index];
		if (quote === '"' || quote === "'") {
			const closingQuote = source.indexOf(quote, index + 1);
			if (closingQuote < 0) {
				return undefined;
			}
			index = closingQuote + 1;
			continue;
		}
		if (source[index] === ">") {
			return index + 1;
		}
		index += 1;
	}
	return undefined;
}

function skipWhitespace(source: string, start: number): number {
	let index = start;
	while (isWhitespace(source[index])) {
		index += 1;
	}
	return index;
}

function nextLineBreak(source: string, start: number): number {
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

function isEscaped(source: string, index: number): boolean {
	let backslashes = 0;
	for (let cursor = index - 1; cursor >= 0 && source[cursor] === "\\"; cursor -= 1) {
		backslashes += 1;
	}
	return backslashes % 2 === 1;
}

function openingBracketClose(character: string | undefined): string | undefined {
	return character === "(" ? ")" : character === "[" ? "]" : character === "{" ? "}" : undefined;
}

function isAsciiLetter(character: string | undefined): boolean {
	return character !== undefined && /[A-Za-z]/.test(character);
}

function isTagNameCharacter(character: string | undefined): boolean {
	return character !== undefined && /[A-Za-z0-9_:.-]/.test(character);
}

function isAttributeNameCharacter(source: string, index: number): boolean {
	const character = source[index];
	return (
		character !== undefined &&
		!isWhitespace(character) &&
		character !== "=" &&
		character !== "/" &&
		character !== ">" &&
		character !== "<" &&
		!source.startsWith("{#", index)
	);
}

function isWhitespace(character: string | undefined): boolean {
	return character === " " || character === "\t" || character === "\r" || character === "\n";
}

function asciiLowercase(value: string): string {
	return value.replace(/[A-Z]/g, (character) => character.toLowerCase());
}
