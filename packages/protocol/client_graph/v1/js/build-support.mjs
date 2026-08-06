/** Deterministically replace the one generated protocol region in citry.js. */

export const REGION_START = "/*<citry-client-graph-v1>*/";
export const REGION_END = "/*</citry-client-graph-v1>*/";

const count = (source, token) => source.split(token).length - 1;

/** Insert the initial region or refresh the existing region without touching other bytes. */
export const composeCoreRuntime = (
	source,
	generated,
	{ initialize = false } = {},
) => {
	const starts = count(source, REGION_START);
	const ends = count(source, REGION_END);
	if (starts === 0 && ends === 0) {
		if (!initialize)
			throw new Error("citry.js has no generated client-graph region");
		const strict = '  "use strict";';
		const first = source.indexOf(strict);
		if (first === -1 || source.indexOf(strict, first + strict.length) !== -1) {
			throw new Error('citry.js must contain one outer "use strict" directive');
		}
		const region = `  ${REGION_START}\n  ${generated.replaceAll("\n", "\n  ")}\n  ${REGION_END}`;
		return (
			source.slice(0, first + strict.length) +
			`\n\n${region}` +
			source.slice(first + strict.length)
		);
	}
	if (starts !== 1 || ends !== 1) {
		throw new Error(
			"citry.js must contain exactly one generated client-graph region",
		);
	}
	const start = source.indexOf(REGION_START);
	const end = source.indexOf(REGION_END);
	if (end < start)
		throw new Error(
			"citry.js generated client-graph region markers are reversed",
		);
	const strictEnd =
		source.indexOf('  "use strict";') + '  "use strict";'.length;
	if (
		strictEnd < '  "use strict";'.length ||
		source.slice(strictEnd, start).trim() !== ""
	) {
		throw new Error(
			'citry.js generated client-graph region must follow outer "use strict"',
		);
	}
	const replacement = `${REGION_START}\n  ${generated.replaceAll("\n", "\n  ")}\n  `;
	return source.slice(0, start) + replacement + source.slice(end);
};
