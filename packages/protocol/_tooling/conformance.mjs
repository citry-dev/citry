/** Development-only reader and operation applier for protocol conformance cases. */

export const CASE_FORMAT = "citry-protocol-conformance-cases/1";

const CASE_FIELDS = [
	"constraint",
	"expected",
	"id",
	"implementations",
	"operations",
	"schema",
	"seed",
];

export function parseCaseFile(value) {
	strictJson(value);
	strictRecord(value, ["cases", "format"], "conformance case file");
	if (value.format !== CASE_FORMAT) {
		throw new Error(
			`unsupported conformance case format ${JSON.stringify(value.format)}`,
		);
	}
	if (!Array.isArray(value.cases)) {
		throw new Error("conformance case file cases must be an array");
	}
	const ids = new Set();
	return value.cases.map((item) => {
		const fields = Object.hasOwn(item, "rule")
			? [...CASE_FIELDS, "rule"]
			: CASE_FIELDS;
		strictRecord(item, fields, "conformance case");
		for (const field of ["constraint", "id", "schema", "seed"]) {
			nonemptyString(item[field], `conformance case ${field}`);
		}
		if (Object.hasOwn(item, "rule")) {
			nonemptyString(item.rule, "conformance case handwritten rule");
		}
		if (ids.has(item.id)) {
			throw new Error(
				`duplicate conformance case id ${JSON.stringify(item.id)}`,
			);
		}
		ids.add(item.id);
		strictRecord(item.expected, ["category", "path"], "expected issue");
		pointer(item.expected.path, "expected issue path");
		nonemptyString(item.expected.category, "expected issue category");
		if (!Array.isArray(item.operations) || item.operations.length === 0) {
			throw new Error("conformance case operations must be a non-empty array");
		}
		const operations = item.operations.map(parseOperation);
		if (
			!Array.isArray(item.implementations) ||
			item.implementations.length === 0
		) {
			throw new Error(
				"conformance case implementations must be a non-empty array",
			);
		}
		const implementations = item.implementations.map((entry) =>
			nonemptyString(entry, "implementation"),
		);
		if (new Set(implementations).size !== implementations.length) {
			throw new Error("conformance case implementations must be unique");
		}
		return structuredClone({ ...item, implementations, operations });
	});
}

export function applyOperations(document, operations) {
	strictJson(document);
	let result = structuredClone(document);
	for (const rawOperation of operations) {
		const operation = parseOperation(rawOperation);
		const tokens = pointer(operation.path, "operation path");
		if (tokens.length === 0) {
			if (operation.op === "remove") {
				throw new Error("the document root cannot be removed");
			}
			result = structuredClone(operation.value);
			continue;
		}
		let parent = result;
		for (const token of tokens.slice(0, -1)) {
			parent = member(parent, token);
		}
		const pathSegment = tokens.at(-1);
		if (Array.isArray(parent)) {
			if (operation.op === "add") {
				const index =
					pathSegment === "-"
						? parent.length
						: arrayIndex(pathSegment, parent.length, true);
				parent.splice(index, 0, structuredClone(operation.value));
			} else {
				const index = arrayIndex(pathSegment, parent.length, false);
				if (operation.op === "remove") {
					parent.splice(index, 1);
				} else {
					parent[index] = structuredClone(operation.value);
				}
			}
		} else if (isRecord(parent)) {
			if (operation.op !== "add" && !Object.hasOwn(parent, pathSegment)) {
				throw new Error(
					`operation path does not exist: ${JSON.stringify(operation.path)}`,
				);
			}
			if (operation.op === "remove") {
				delete parent[pathSegment];
			} else {
				Object.defineProperty(parent, pathSegment, {
					configurable: true,
					enumerable: true,
					value: structuredClone(operation.value),
					writable: true,
				});
			}
		} else {
			throw new Error(
				`operation parent is not a container: ${JSON.stringify(operation.path)}`,
			);
		}
	}
	return result;
}

function parseOperation(value) {
	if (!isRecord(value)) {
		throw new Error("operation must be an object");
	}
	const operation = nonemptyString(value.op, "operation op");
	if (!["add", "remove", "replace"].includes(operation)) {
		throw new Error(`unsupported operation ${JSON.stringify(operation)}`);
	}
	const fields =
		operation === "remove" ? ["op", "path"] : ["op", "path", "value"];
	strictRecord(value, fields, "operation");
	pointer(value.path, "operation path");
	if (operation !== "remove") {
		strictJson(value.value);
	}
	return structuredClone(value);
}

function strictJson(value, ancestors = new Set()) {
	if (
		value === null ||
		typeof value === "string" ||
		typeof value === "boolean"
	) {
		return;
	}
	if (typeof value === "number") {
		if (!Number.isFinite(value)) {
			throw new Error("non-finite number is not strict JSON");
		}
		return;
	}
	if (!Array.isArray(value) && !isRecord(value)) {
		throw new Error(`${typeof value} is not strict JSON`);
	}
	if (ancestors.has(value)) {
		throw new Error("cyclic value is not strict JSON");
	}
	ancestors.add(value);
	if (Array.isArray(value)) {
		if (Object.keys(value).length !== value.length) {
			throw new Error(
				"sparse arrays and extra array fields are not strict JSON",
			);
		}
		for (const child of value) {
			strictJson(child, ancestors);
		}
	} else {
		for (const key of Reflect.ownKeys(value)) {
			if (typeof key !== "string") {
				throw new Error("symbol object keys are not strict JSON");
			}
			const descriptor = Object.getOwnPropertyDescriptor(value, key);
			if (!descriptor?.enumerable || !("value" in descriptor)) {
				throw new Error("hidden fields and accessors are not strict JSON");
			}
			strictJson(descriptor.value, ancestors);
		}
	}
	ancestors.delete(value);
}

function strictRecord(value, fields, description) {
	if (!isRecord(value)) {
		throw new Error(`${description} must be an object`);
	}
	const actual = Object.keys(value).sort();
	const expected = [...fields].sort();
	if (
		actual.length !== expected.length ||
		actual.some((field, index) => field !== expected[index])
	) {
		throw new Error(
			`${description} must have exactly these fields: ${expected.join(", ")}`,
		);
	}
}

function isRecord(value) {
	if (value === null || typeof value !== "object" || Array.isArray(value)) {
		return false;
	}
	const prototype = Object.getPrototypeOf(value);
	return prototype === Object.prototype || prototype === null;
}

function nonemptyString(value, description) {
	if (typeof value !== "string" || value.length === 0) {
		throw new Error(`${description} must be a non-empty string`);
	}
	return value;
}

function pointer(value, description) {
	if (typeof value !== "string" || (value !== "" && !value.startsWith("/"))) {
		throw new Error(`${description} must be an RFC 6901 JSON Pointer`);
	}
	if (value === "") {
		return [];
	}
	return value
		.slice(1)
		.split("/")
		.map((raw) => {
			if (/~(?:[^01]|$)/u.test(raw)) {
				throw new Error(`${description} has an invalid JSON Pointer escape`);
			}
			return raw.replaceAll("~1", "/").replaceAll("~0", "~");
		});
}

function member(container, pathSegment) {
	if (Array.isArray(container)) {
		return container[arrayIndex(pathSegment, container.length, false)];
	}
	if (isRecord(container) && Object.hasOwn(container, pathSegment)) {
		return container[pathSegment];
	}
	throw new Error(
		`operation path segment does not exist: ${JSON.stringify(pathSegment)}`,
	);
}

function arrayIndex(value, length, allowEnd) {
	if (!/^(?:0|[1-9][0-9]*)$/u.test(value)) {
		throw new Error(`invalid array index ${JSON.stringify(value)}`);
	}
	const index = Number(value);
	const upper = allowEnd ? length : length - 1;
	if (!Number.isSafeInteger(index) || index > upper) {
		throw new Error(`array index ${index} is out of range`);
	}
	return index;
}
