import { isSafeRenderId, PROTOCOL } from "./calls";
import {
	firstUnknown,
	hasOwn,
	isPlainObject,
	ProtocolValueError,
	pointer,
	type ValidationIssue,
	validateStrictJson,
} from "./issue";
import type {
	EventComponentClass,
	EventComponentInstance,
	EventHandlerOptions,
	EventsManifest,
} from "./types";

const HTTP_METHOD = /^[!#$%&'*+.^_`|~0-9A-Z-]+$/;
const REVISION = /^[0-9a-f]{64}$/;
const DESCRIPTOR_FIELDS = new Set([
	"componentClassId",
	"eventHandlers",
	"writableStateFields",
]);
const HANDLER_FIELDS = new Set([
	"httpMethod",
	"usesState",
	"debounceMilliseconds",
	"throttleMilliseconds",
	"latestCallWins",
	"allowBatching",
]);
const INSTANCE_FIELDS = new Set([
	"renderId",
	"componentClassId",
	"stateToken",
	"publicState",
]);
const MANIFEST_FIELDS = new Set([
	"protocol",
	"clientGraphRevision",
	"componentClasses",
	"componentInstances",
]);

const prefixed = (base: string, issue: ValidationIssue): ValidationIssue => ({
	path: base + issue.path,
	category: issue.category,
	message: issue.message,
});

const nonNegativeIntegerIssue = (
	value: unknown,
	path: string,
	name: string,
): ValidationIssue | null => {
	if (typeof value !== "number" || !Number.isInteger(value)) {
		return {
			path,
			category:
				typeof value === "number" && !Number.isFinite(value)
					? "strict_json"
					: "type",
			message: `The ${name} hint must be an integer.`,
		};
	}
	if (value < 0) {
		return {
			path,
			category: "range",
			message: `The ${name} hint must be at least 0.`,
		};
	}
	return null;
};

export const validateHandlerDescriptor = (
	value: unknown,
	path = "",
): ValidationIssue | null => {
	const jsonIssue = validateStrictJson(value, path);
	if (jsonIssue) return jsonIssue;
	if (!isPlainObject(value)) {
		return {
			path,
			category: "type",
			message: "Event-handler hints must be an object.",
		};
	}
	if (!hasOwn(value, "httpMethod")) {
		return {
			path: pointer(path, "httpMethod"),
			category: "required",
			message: "Handler hints require 'httpMethod'.",
		};
	}
	const unknown = firstUnknown(value, HANDLER_FIELDS);
	if (unknown !== null) {
		return {
			path: pointer(path, unknown),
			category: "unknown_field",
			message: "Handler hints have an unknown field.",
		};
	}
	if (typeof value.httpMethod !== "string") {
		return {
			path: pointer(path, "httpMethod"),
			category: "type",
			message: "The HTTP method must be a string.",
		};
	}
	if (!HTTP_METHOD.test(value.httpMethod)) {
		return {
			path: pointer(path, "httpMethod"),
			category: "pattern",
			message: "The HTTP method must be an uppercase token.",
		};
	}
	if (hasOwn(value, "usesState") && value.usesState !== true) {
		return {
			path: pointer(path, "usesState"),
			category: "enum",
			message: "The usesState hint has its non-default literal value.",
		};
	}
	for (const name of [
		"debounceMilliseconds",
		"throttleMilliseconds",
	] as const) {
		if (!hasOwn(value, name)) continue;
		const issue = nonNegativeIntegerIssue(
			value[name],
			pointer(path, name),
			name,
		);
		if (issue) return issue;
	}
	if (hasOwn(value, "latestCallWins") && value.latestCallWins !== true) {
		return {
			path: pointer(path, "latestCallWins"),
			category: "enum",
			message: "The latestCallWins hint has its non-default literal value.",
		};
	}
	if (hasOwn(value, "allowBatching") && value.allowBatching !== false) {
		return {
			path: pointer(path, "allowBatching"),
			category: "enum",
			message: "The allowBatching hint has its non-default literal value.",
		};
	}
	return null;
};

export const validateDescriptor = (
	value: unknown,
	path = "",
): ValidationIssue | null => {
	const jsonIssue = validateStrictJson(value, path);
	if (jsonIssue) return jsonIssue;
	if (!isPlainObject(value)) {
		return {
			path,
			category: "type",
			message: "A component descriptor must be an object.",
		};
	}
	for (const required of ["componentClassId", "eventHandlers"]) {
		if (!hasOwn(value, required)) {
			return {
				path: pointer(path, required),
				category: "required",
				message: `The descriptor requires '${required}'.`,
			};
		}
	}
	const unknown = firstUnknown(value, DESCRIPTOR_FIELDS);
	if (unknown !== null) {
		return {
			path: pointer(path, unknown),
			category: "unknown_field",
			message: "The descriptor has an unknown field.",
		};
	}
	if (typeof value.componentClassId !== "string") {
		return {
			path: pointer(path, "componentClassId"),
			category: "type",
			message: "The component class ID must be a string.",
		};
	}
	if (!value.componentClassId) {
		return {
			path: pointer(path, "componentClassId"),
			category: "range",
			message: "The component class ID must not be empty.",
		};
	}
	if (!isPlainObject(value.eventHandlers)) {
		return {
			path: pointer(path, "eventHandlers"),
			category: "type",
			message: "Event handlers must be an object.",
		};
	}
	for (const name of Object.keys(value.eventHandlers).sort()) {
		if (!name) {
			return {
				path: pointer(path, "eventHandlers"),
				category: "range",
				message: "A handler name must not be empty.",
			};
		}
		const issue = validateHandlerDescriptor(
			value.eventHandlers[name],
			pointer(pointer(path, "eventHandlers"), name),
		);
		if (issue) return issue;
	}
	if (hasOwn(value, "writableStateFields")) {
		const fields = value.writableStateFields;
		const fieldPath = pointer(path, "writableStateFields");
		if (!Array.isArray(fields)) {
			return {
				path: fieldPath,
				category: "type",
				message: "Writable State fields must be an array.",
			};
		}
		const seen = new Set<string>();
		for (let index = 0; index < fields.length; index += 1) {
			const field = fields[index];
			if (typeof field !== "string") {
				return {
					path: pointer(fieldPath, index),
					category: "type",
					message: "A writable State field must be a string.",
				};
			}
			if (!field) {
				return {
					path: pointer(fieldPath, index),
					category: "range",
					message: "A writable State field must not be empty.",
				};
			}
			if (seen.has(field)) {
				return {
					path: fieldPath,
					category: "semantic",
					message: "Writable State fields must be unique.",
				};
			}
			seen.add(field);
		}
	}
	return null;
};

export const validateComponentInstance = (
	value: unknown,
	path = "",
): ValidationIssue | null => {
	const jsonIssue = validateStrictJson(value, path);
	if (jsonIssue) return jsonIssue;
	if (!isPlainObject(value)) {
		return {
			path,
			category: "type",
			message: "A component instance must be an object.",
		};
	}
	for (const required of INSTANCE_FIELDS) {
		if (!hasOwn(value, required)) {
			return {
				path: pointer(path, required),
				category: "required",
				message: `The instance requires '${required}'.`,
			};
		}
	}
	const unknown = firstUnknown(value, INSTANCE_FIELDS);
	if (unknown !== null) {
		return {
			path: pointer(path, unknown),
			category: "unknown_field",
			message: "The component instance has an unknown field.",
		};
	}
	if (typeof value.renderId !== "string") {
		return {
			path: pointer(path, "renderId"),
			category: "type",
			message: "The render ID must be a string.",
		};
	}
	if (!isSafeRenderId(value.renderId)) {
		return {
			path: pointer(path, "renderId"),
			category: "pattern",
			message: "The render ID has invalid characters.",
		};
	}
	if (typeof value.componentClassId !== "string") {
		return {
			path: pointer(path, "componentClassId"),
			category: "type",
			message: "The component class ID must be a string.",
		};
	}
	if (!value.componentClassId) {
		return {
			path: pointer(path, "componentClassId"),
			category: "range",
			message: "The component class ID must not be empty.",
		};
	}
	if (value.stateToken !== null && typeof value.stateToken !== "string") {
		return {
			path: pointer(path, "stateToken"),
			category: "type",
			message: "The state token must be a string or null.",
		};
	}
	if (value.stateToken === "") {
		return {
			path: pointer(path, "stateToken"),
			category: "range",
			message: "The state token must not be empty.",
		};
	}
	if (!isPlainObject(value.publicState)) {
		return {
			path: pointer(path, "publicState"),
			category: "type",
			message: "Public State must be an object.",
		};
	}
	const issue = validateStrictJson(value.publicState);
	return issue ? prefixed(pointer(path, "publicState"), issue) : null;
};

export const validateManifest = (
	value: unknown,
	path = "",
): ValidationIssue | null => {
	const jsonIssue = validateStrictJson(value, path);
	if (jsonIssue) return jsonIssue;
	if (!isPlainObject(value)) {
		return {
			path,
			category: "type",
			message: "The Events manifest must be an object.",
		};
	}
	for (const required of MANIFEST_FIELDS) {
		if (!hasOwn(value, required)) {
			return {
				path: pointer(path, required),
				category: "required",
				message: `The manifest requires '${required}'.`,
			};
		}
	}
	const unknown = firstUnknown(value, MANIFEST_FIELDS);
	if (unknown !== null) {
		return {
			path: pointer(path, unknown),
			category: "unknown_field",
			message: "The manifest has an unknown field.",
		};
	}
	if (value.protocol !== PROTOCOL) {
		return {
			path: pointer(path, "protocol"),
			category: typeof value.protocol === "string" ? "enum" : "type",
			message: "The manifest protocol must be citry-events/1.",
		};
	}
	if (
		value.clientGraphRevision !== null &&
		typeof value.clientGraphRevision !== "string"
	) {
		return {
			path: pointer(path, "clientGraphRevision"),
			category: "type",
			message: "The graph revision must be a string or null.",
		};
	}
	if (
		typeof value.clientGraphRevision === "string" &&
		!REVISION.test(value.clientGraphRevision)
	) {
		return {
			path: pointer(path, "clientGraphRevision"),
			category: "pattern",
			message: "The graph revision must be lowercase SHA-256.",
		};
	}
	if (!Array.isArray(value.componentClasses)) {
		return {
			path: pointer(path, "componentClasses"),
			category: "type",
			message: "Component classes must be an array.",
		};
	}
	for (let index = 0; index < value.componentClasses.length; index += 1) {
		const issue = validateDescriptor(
			value.componentClasses[index],
			pointer(pointer(path, "componentClasses"), index),
		);
		if (issue) return issue;
	}
	if (!Array.isArray(value.componentInstances)) {
		return {
			path: pointer(path, "componentInstances"),
			category: "type",
			message: "Component instances must be an array.",
		};
	}
	for (let index = 0; index < value.componentInstances.length; index += 1) {
		const issue = validateComponentInstance(
			value.componentInstances[index],
			pointer(pointer(path, "componentInstances"), index),
		);
		if (issue) return issue;
	}

	const classes = value.componentClasses as EventComponentClass[];
	const instances = value.componentInstances as EventComponentInstance[];
	const classIds = new Set<string>();
	for (let index = 0; index < classes.length; index += 1) {
		const descriptor = classes[index];
		if (classIds.has(descriptor.componentClassId)) {
			return {
				path: pointer(pointer(path, "componentClasses"), index),
				category: "semantic",
				message: `Duplicate component class ID '${descriptor.componentClassId}'.`,
			};
		}
		classIds.add(descriptor.componentClassId);
	}
	const renderIds = new Set<string>();
	for (let index = 0; index < instances.length; index += 1) {
		const instance = instances[index];
		if (renderIds.has(instance.renderId)) {
			return {
				path: pointer(pointer(path, "componentInstances"), index),
				category: "semantic",
				message: `Duplicate render ID '${instance.renderId}'.`,
			};
		}
		renderIds.add(instance.renderId);
	}
	for (let index = 0; index < instances.length; index += 1) {
		const instance = instances[index];
		if (!classIds.has(instance.componentClassId)) {
			return {
				path: pointer(
					pointer(pointer(path, "componentInstances"), index),
					"componentClassId",
				),
				category: "semantic",
				message: "The instance refers to an unknown component class.",
			};
		}
	}
	for (let index = 0; index < instances.length; index += 1) {
		const instance = instances[index];
		if (
			instance.stateToken === null &&
			Object.keys(instance.publicState).length > 0
		) {
			return {
				path: pointer(
					pointer(pointer(path, "componentInstances"), index),
					"publicState",
				),
				category: "semantic",
				message: "A stateless instance must have empty public State.",
			};
		}
	}
	return null;
};

export const assertValidManifest = (value: unknown): EventsManifest => {
	const issue = validateManifest(value);
	if (issue) throw new ProtocolValueError(issue);
	return value as EventsManifest;
};

export const assertValidDescriptor = (value: unknown): EventComponentClass => {
	const issue = validateDescriptor(value);
	if (issue) throw new ProtocolValueError(issue);
	return value as EventComponentClass;
};

export const assertValidHandlerDescriptor = (
	value: unknown,
): EventHandlerOptions => {
	const issue = validateHandlerDescriptor(value);
	if (issue) throw new ProtocolValueError(issue);
	return value as EventHandlerOptions;
};
