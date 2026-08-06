export type EmbeddedLanguage = "html" | "javascript" | "css";

export interface EmbeddedRegion {
	language: EmbeddedLanguage;
	start: number;
	end: number;
}

interface SourceSpan {
	start: number;
	end: number;
}

interface StringSpan extends SourceSpan {
	bodyStart: number;
	bodyEnd: number;
	delimiter: '"""' | "'''" | '"' | "'";
}

const assignmentPattern = /^[\t ]*(template|js|css)[\t ]*(?::[^=\r\n]+?)?[\t ]*=[\t ]*("""|''')/gm;

const languageByAttribute: Readonly<Record<string, EmbeddedLanguage>> = {
	template: "html",
	js: "javascript",
	css: "css",
};

export function pythonEmbeddedRegions(source: string): EmbeddedRegion[] {
	const { excluded, strings } = scanPython(source);
	const regions: EmbeddedRegion[] = [];
	for (const match of source.matchAll(assignmentPattern)) {
		const attribute = match[1];
		const delimiter = match[2];
		if (attribute === undefined || (delimiter !== '"""' && delimiter !== "'''")) {
			continue;
		}
		const matchStart = match.index;
		if (spanContaining(excluded, matchStart) !== undefined) {
			continue;
		}
		const quoteStart = matchStart + match[0].lastIndexOf(delimiter);
		const string = strings.find((span) => span.start === quoteStart && span.delimiter === delimiter);
		const language = languageByAttribute[attribute];
		if (string !== undefined && language !== undefined) {
			regions.push({ language, start: string.bodyStart, end: string.bodyEnd });
		}
	}
	return regions;
}

export function embeddedLanguageAt(source: string, languageId: string, offset: number): EmbeddedLanguage | undefined {
	if (languageId === "citry-html") {
		return offset >= 0 && offset <= source.length ? "html" : undefined;
	}
	if (languageId !== "python") {
		return undefined;
	}
	return pythonEmbeddedRegions(source).find((region) => region.start <= offset && offset <= region.end)?.language;
}

export function virtualDocumentSource(source: string, languageId: string, language: EmbeddedLanguage): string {
	if (languageId === "citry-html" && language === "html") {
		return source;
	}
	const masked: string[] = source
		.split("")
		.map((character) => (character === "\n" || character === "\r" ? character : " "));
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

function scanPython(source: string): { excluded: SourceSpan[]; strings: StringSpan[] } {
	const excluded: SourceSpan[] = [];
	const strings: StringSpan[] = [];
	let index = 0;
	while (index < source.length) {
		const character = source[index];
		if (character === "#") {
			const end = lineEnd(source, index);
			excluded.push({ start: index, end });
			index = end;
			continue;
		}
		if (character !== '"' && character !== "'") {
			index += 1;
			continue;
		}
		const triple = source.startsWith(character.repeat(3), index);
		const delimiter = (triple ? character.repeat(3) : character) as StringSpan["delimiter"];
		const bodyStart = index + delimiter.length;
		const closing = closingDelimiter(source, bodyStart, delimiter);
		const bodyEnd = closing ?? (triple ? source.length : lineEnd(source, bodyStart));
		const end = closing === undefined ? bodyEnd : closing + delimiter.length;
		const span = { start: index, end, bodyStart, bodyEnd, delimiter };
		strings.push(span);
		excluded.push(span);
		index = Math.max(end, index + delimiter.length);
	}
	return { excluded, strings };
}

function closingDelimiter(source: string, start: number, delimiter: StringSpan["delimiter"]): number | undefined {
	for (let index = start; index < source.length; index += 1) {
		if (delimiter.length === 1 && (source[index] === "\n" || source[index] === "\r")) {
			return undefined;
		}
		if (source.startsWith(delimiter, index) && !isEscaped(source, index)) {
			return index;
		}
	}
	return undefined;
}

function isEscaped(source: string, index: number): boolean {
	let backslashes = 0;
	for (let cursor = index - 1; cursor >= 0 && source[cursor] === "\\"; cursor -= 1) {
		backslashes += 1;
	}
	return backslashes % 2 === 1;
}

function lineEnd(source: string, start: number): number {
	const newline = source.indexOf("\n", start);
	return newline < 0 ? source.length : newline;
}

function spanContaining(spans: SourceSpan[], offset: number): SourceSpan | undefined {
	return spans.find((span) => span.start <= offset && offset < span.end);
}
