export const ISSUE_CATEGORIES = [
	"required",
	"unknown_field",
	"type",
	"enum",
	"pattern",
	"range",
	"strict_json",
	"semantic",
	"correlation",
	"capability",
] as const;

export type IssueCategory = (typeof ISSUE_CATEGORIES)[number];

export interface ValidationIssue {
	path: string;
	category: IssueCategory;
	message: string;
}

export class ProtocolValueError extends TypeError {
	readonly issue: ValidationIssue;

	constructor(issue: ValidationIssue) {
		super(issue.message);
		this.name = "ProtocolValueError";
		this.issue = issue;
	}
}

/** ES2020-compatible own-property check used at every strict boundary. */
export const hasOwn = (value: object, key: PropertyKey): boolean =>
	// biome-ignore lint/suspicious/noPrototypeBuiltins: The browser bundle targets ES2020, before Object.hasOwn.
	Object.prototype.hasOwnProperty.call(value, key);

/** Append one RFC 6901 member to a JSON Pointer. */
export const pointer = (parent: string, member: string | number): string => {
	const escaped = String(member).replace(/~/g, "~0").replace(/\//g, "~1");
	return parent ? `${parent}/${escaped}` : `/${escaped}`;
};

/** Whether a value is a plain object JSON can carry without normalization. */
export const isPlainObject = (
	value: unknown,
): value is Record<string, unknown> => {
	if (value === null || typeof value !== "object" || Array.isArray(value))
		return false;
	const prototype = Object.getPrototypeOf(value);
	return prototype === Object.prototype || prototype === null;
};

/** Return the first unknown key in JavaScript's UTF-16 string order. */
export const firstUnknown = (
	value: Record<string, unknown>,
	allowed: ReadonlySet<string>,
): string | null =>
	Object.keys(value)
		.filter((key) => !allowed.has(key))
		.sort()[0] ?? null;

const containerIssue = (
	value: object,
	path: string,
): ValidationIssue | null => {
	if (Object.getOwnPropertySymbols(value).length) {
		return {
			path,
			category: "strict_json",
			message: "The value contains a symbol-keyed property.",
		};
	}
	for (const name of Object.getOwnPropertyNames(value)) {
		if (Array.isArray(value) && name === "length") continue;
		const descriptor = Object.getOwnPropertyDescriptor(value, name);
		if (!descriptor?.enumerable || !("value" in descriptor)) {
			return {
				path: pointer(path, name),
				category: "strict_json",
				message: "A JSON property must be an enumerable data property.",
			};
		}
	}
	return null;
};

/** Validate one in-memory strict JSON value without recursion or mutation. */
export const validateStrictJson = (
	value: unknown,
	path = "",
): ValidationIssue | null => {
	type Frame = { value: unknown; path: string; leaving: boolean };
	const stack: Frame[] = [{ value, path, leaving: false }];
	const ancestors = new Set<object>();
	while (stack.length) {
		const frame = stack.pop() as Frame;
		const current = frame.value;
		if (frame.leaving) {
			ancestors.delete(current as object);
			continue;
		}
		if (
			current === null ||
			typeof current === "string" ||
			typeof current === "boolean"
		) {
			continue;
		}
		if (typeof current === "number") {
			if (!Number.isFinite(current)) {
				return {
					path: frame.path,
					category: "strict_json",
					message: "The value contains a non-finite number.",
				};
			}
			continue;
		}
		if (typeof current !== "object") {
			return {
				path: frame.path,
				category: "strict_json",
				message: "The value contains a non-JSON value.",
			};
		}
		if (!Array.isArray(current) && !isPlainObject(current)) {
			return {
				path: frame.path,
				category: "strict_json",
				message: "The value contains a non-JSON object.",
			};
		}
		const ownIssue = containerIssue(current, frame.path);
		if (ownIssue) return ownIssue;
		if (ancestors.has(current)) {
			return {
				path: frame.path,
				category: "strict_json",
				message: "The value contains a cycle.",
			};
		}
		ancestors.add(current);
		stack.push({ value: current, path: frame.path, leaving: true });
		if (Array.isArray(current)) {
			const names = Object.keys(current);
			if (
				names.length !== current.length ||
				names.some((name, index) => name !== String(index))
			) {
				return {
					path: frame.path,
					category: "strict_json",
					message: "A JSON array must be dense and carry no named properties.",
				};
			}
			for (let index = current.length - 1; index >= 0; index -= 1) {
				stack.push({
					value: current[index],
					path: pointer(frame.path, index),
					leaving: false,
				});
			}
			continue;
		}
		const keys = Object.keys(current).sort().reverse();
		for (const key of keys) {
			stack.push({
				value: current[key],
				path: pointer(frame.path, key),
				leaving: false,
			});
		}
	}
	return null;
};

/** Whether an in-memory value is strict JSON without normalizing it. */
export const isJsonValue = (value: unknown): boolean =>
	validateStrictJson(value) === null;

/** Validate and recursively copy one application-owned JSON value. */
export const copyJson = <T>(value: T): T => {
	const issue = validateStrictJson(value);
	if (issue) throw new ProtocolValueError(issue);
	if (value === null || typeof value !== "object") return value;
	const copied: unknown = Array.isArray(value) ? new Array(value.length) : {};
	const stack: {
		source: object;
		target: Record<string, unknown> | unknown[];
	}[] = [
		{
			source: value,
			target: copied as Record<string, unknown> | unknown[],
		},
	];
	while (stack.length) {
		const { source, target } = stack.pop() as {
			source: object;
			target: Record<string, unknown> | unknown[];
		};
		for (const key of Object.keys(source)) {
			const item = (source as Record<string, unknown>)[key];
			if (item !== null && typeof item === "object") {
				const child: Record<string, unknown> | unknown[] = Array.isArray(item)
					? new Array(item.length)
					: {};
				Object.defineProperty(target, key, {
					configurable: true,
					enumerable: true,
					value: child,
					writable: true,
				});
				stack.push({ source: item, target: child });
			} else {
				Object.defineProperty(target, key, {
					configurable: true,
					enumerable: true,
					value: item,
					writable: true,
				});
			}
		}
	}
	return copied as T;
};
