import { embeddedVirtualDocumentAt } from "./embedded.js";

const rawTextTags = new Set(["script", "style", "textarea", "title", "c-raw"]);

/**
 * Decide whether a cursor can belong to Citry's typed browser projection.
 *
 * Component JavaScript is always eligible. Template HTML is eligible only
 * inside a browser-valued attribute, including one nested inside a template
 * attribute. The language server remains authoritative after this cheap pass.
 */
export function browserProjectionCandidateAt(source: string, languageId: string, offset: number): boolean {
	if (languageId === "javascript") {
		return offset >= 0 && offset <= source.length;
	}
	const view = embeddedVirtualDocumentAt(source, languageId, offset);
	if (view?.language === "javascript") {
		return true;
	}
	const html = languageId === "html" ? source : view?.language === "html" ? view.source : undefined;
	if (html === undefined) {
		return false;
	}
	return browserRanges(html, 0, html.length).some(({ start, end }) => start <= offset && offset <= end);
}

interface BrowserRange {
	start: number;
	end: number;
}

function browserRanges(source: string, start: number, end: number): BrowserRange[] {
	const ranges: BrowserRange[] = [];
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
		if (scanned === undefined) {
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

function scanStartTag(
	source: string,
	start: number,
	limit: number,
	ranges: BrowserRange[],
): { name: string; end: number; selfClosing: boolean } | undefined {
	let index = start + 1;
	const nameStart = index;
	while (isTagNameCharacter(source[index])) {
		index += 1;
	}
	if (index === nameStart) {
		return undefined;
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
		// Nested templates use the opposite quote, so a recursive pass can
		// discover their Alpine hosts without mistaking ordinary HTML for one.
		if (source.slice(valueStart, valueEnd).trimStart().startsWith("<")) {
			ranges.push(...browserRanges(source, valueStart, valueEnd));
		}
	}
	return { name, end: limit, selfClosing: false };
}

function isBrowserAttribute(name: string): boolean {
	const base = name.split(".", 1)[0] ?? name;
	return name === "$c-props" || name.startsWith("@") || name.startsWith(":") || base.startsWith("x-");
}

function skipWhitespace(source: string, index: number): number {
	while (/\s/u.test(source[index] ?? "")) {
		index += 1;
	}
	return index;
}

function isWhitespace(character: string | undefined): boolean {
	return character !== undefined && /\s/u.test(character);
}

function isAsciiLetter(character: string | undefined): boolean {
	return character !== undefined && /[A-Za-z]/u.test(character);
}

function isTagNameCharacter(character: string | undefined): boolean {
	return character !== undefined && /[A-Za-z0-9:._-]/u.test(character);
}

function isAttributeNameCharacter(character: string | undefined): boolean {
	return character !== undefined && !/[\s=/>]/u.test(character);
}
