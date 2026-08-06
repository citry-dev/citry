import {
	firstUnknown,
	hasOwn,
	isPlainObject,
	pointer,
	type ValidationIssue,
	validateStrictJson,
} from "./issue";

const RENDER_ID = /^[a-z0-9_-]+$/;
const LOCATION_KINDS = new Set([
	"component-call",
	"component-tag-client-binding",
	"implicit-fill",
	"named-fill",
	"fallback-fill",
	"slot-outlet",
]);
const BINDING_SOURCES = new Set(["direct", "server-dynamic", "spread"]);
const FILL_KINDS = new Set([
	"implicit",
	"named",
	"fallback",
	"python",
	"typed-default",
]);
const SOURCE_POLICIES = new Set([
	"template",
	"python-detached",
	"typed-default-detached",
]);
const MORPH_MODES = new Set(["ignore"]);

const COMPONENT_CLASS_FIELDS = ["classId", "className"] as const;
const COMPONENT_INSTANCE_FIELDS = [
	"instanceId",
	"renderId",
	"classId",
	"invocationId",
	"parentRenderId",
	"transparent",
] as const;
const SOURCE_LOCATION_FIELDS = [
	"locationId",
	"kind",
	"ownerRenderId",
	"ownerClassId",
	"carrierInstanceId",
	"origin",
	"sourceOffset",
	"sourcePos",
	"mappingKey",
	"mappingIndex",
] as const;
const EXPRESSION_PAYLOAD_FIELDS = ["type", "expression"] as const;
const DOM_PAYLOAD_FIELDS = [
	"type",
	"classId",
	"event",
	"handler",
	"args",
	"prevent",
	"stop",
	"self",
	"once",
	"key",
	"debounce",
	"throttle",
] as const;
const POLL_PAYLOAD_FIELDS = [
	"type",
	"classId",
	"handler",
	"args",
	"interval",
] as const;
const CLIENT_BINDING_FIELDS = [
	"key",
	"source",
	"locationId",
	"payload",
] as const;
const NESTED_COMPONENT_FIELDS = [
	"invocationId",
	"sourceRenderId",
	"sourceClassId",
	"locationId",
	"tagName",
	"targetClassId",
	"morphKey",
	"morphMode",
	"targetRenderId",
	"parentRegionId",
	"clientBindings",
] as const;
const EXECUTION_CONSTRAINT_FIELDS = [
	"invocationId",
	"parentRenderId",
	"childRenderId",
] as const;
const FILL_FIELDS = [
	"fillId",
	"kind",
	"slotName",
	"policy",
	"ownerRenderId",
	"ownerClassId",
	"locationId",
	"sourceInvocationId",
	"receiverRenderId",
	"receiverClassId",
	"fallbackLocationId",
] as const;
const SLOT_REGION_FIELDS = [
	"regionId",
	"fillId",
	"receiverRenderId",
	"slotLocationId",
	"ownerRenderId",
	"sourceLocationId",
	"parentRegionId",
	"transitionFromRenderId",
	"resultOwnerRenderId",
] as const;
export const GRAPH_FIELDS = [
	"graphId",
	"componentClasses",
	"componentInstances",
	"sourceLocations",
	"nestedComponents",
	"componentExecutionOrderConstraints",
	"fills",
	"slotRegions",
] as const;

const recordIssue = (
	value: unknown,
	path: string,
	fields: readonly string[],
	label: string,
	strict: boolean,
): ValidationIssue | null => {
	if (strict) {
		const issue = validateStrictJson(value, path);
		if (issue) return issue;
	}
	if (!isPlainObject(value)) {
		return { path, category: "type", message: `${label} must be an object.` };
	}
	for (const required of fields) {
		if (!hasOwn(value, required)) {
			return {
				path: pointer(path, required),
				category: "required",
				message: `${label} requires '${required}'.`,
			};
		}
	}
	const unknown = firstUnknown(value, new Set(fields));
	return unknown === null
		? null
		: {
				path: pointer(path, unknown),
				category: "unknown_field",
				message: `${label} has an unknown field.`,
			};
};

const stringIssue = (
	value: unknown,
	path: string,
	label: string,
): ValidationIssue | null =>
	typeof value === "string"
		? null
		: { path, category: "type", message: `${label} must be a string.` };

const nullableStringIssue = (
	value: unknown,
	path: string,
	label: string,
): ValidationIssue | null =>
	value === null || typeof value === "string"
		? null
		: {
				path,
				category: "type",
				message: `${label} must be a string or null.`,
			};

const integerIssue = (
	value: unknown,
	path: string,
	label: string,
	minimum: number,
): ValidationIssue | null => {
	if (typeof value !== "number" || !Number.isInteger(value)) {
		return {
			path,
			category:
				typeof value === "number" && !Number.isFinite(value)
					? "strict_json"
					: "type",
			message: `${label} must be an integer.`,
		};
	}
	if (!Number.isSafeInteger(value) || value < minimum) {
		return {
			path,
			category: "range",
			message: `${label} is outside the client-graph range.`,
		};
	}
	return null;
};

const nullableIntegerIssue = (
	value: unknown,
	path: string,
	label: string,
	minimum: number,
): ValidationIssue | null =>
	value === null ? null : integerIssue(value, path, label, minimum);

const enumIssue = (
	value: unknown,
	path: string,
	choices: ReadonlySet<string>,
	label: string,
): ValidationIssue | null => {
	if (typeof value !== "string")
		return { path, category: "type", message: `${label} must be a string.` };
	return choices.has(value)
		? null
		: {
				path,
				category: "enum",
				message: `${label} is not a client-graph v1 value.`,
			};
};

const nullableEnumIssue = (
	value: unknown,
	path: string,
	choices: ReadonlySet<string>,
	label: string,
): ValidationIssue | null =>
	value === null ? null : enumIssue(value, path, choices, label);

export const validateComponentClass = (
	value: unknown,
	path = "",
	strict = true,
): ValidationIssue | null => {
	const issue = recordIssue(
		value,
		path,
		COMPONENT_CLASS_FIELDS,
		"A component-class record",
		strict,
	);
	if (issue) return issue;
	const record = value as Record<string, unknown>;
	for (const field of COMPONENT_CLASS_FIELDS) {
		const fieldIssue = stringIssue(
			record[field],
			pointer(path, field),
			`The component ${field}`,
		);
		if (fieldIssue) return fieldIssue;
	}
	return null;
};

export const validateComponentInstance = (
	value: unknown,
	path = "",
	strict = true,
): ValidationIssue | null => {
	const issue = recordIssue(
		value,
		path,
		COMPONENT_INSTANCE_FIELDS,
		"A component-instance record",
		strict,
	);
	if (issue) return issue;
	const record = value as Record<string, unknown>;
	const checks = [
		integerIssue(
			record.instanceId,
			pointer(path, "instanceId"),
			"The instance ID",
			1,
		),
		stringIssue(record.renderId, pointer(path, "renderId"), "The render ID"),
		stringIssue(record.classId, pointer(path, "classId"), "The class ID"),
		nullableIntegerIssue(
			record.invocationId,
			pointer(path, "invocationId"),
			"The invocation ID",
			1,
		),
		nullableStringIssue(
			record.parentRenderId,
			pointer(path, "parentRenderId"),
			"The parent render ID",
		),
	];
	for (const check of checks) if (check) return check;
	if (!RENDER_ID.test(record.renderId as string)) {
		return {
			path: pointer(path, "renderId"),
			category: "pattern",
			message: "The component renderId is not safe for an HTML attribute name.",
		};
	}
	return typeof record.transparent === "boolean"
		? null
		: {
				path: pointer(path, "transparent"),
				category: "type",
				message: "The transparent flag must be a boolean.",
			};
};

export const validateSourceLocation = (
	value: unknown,
	path = "",
	strict = true,
): ValidationIssue | null => {
	const issue = recordIssue(
		value,
		path,
		SOURCE_LOCATION_FIELDS,
		"A source-location record",
		strict,
	);
	if (issue) return issue;
	const record = value as Record<string, unknown>;
	const checks = [
		integerIssue(
			record.locationId,
			pointer(path, "locationId"),
			"The location ID",
			1,
		),
		enumIssue(
			record.kind,
			pointer(path, "kind"),
			LOCATION_KINDS,
			"The location kind",
		),
		stringIssue(
			record.ownerRenderId,
			pointer(path, "ownerRenderId"),
			"The location owner render ID",
		),
		stringIssue(
			record.ownerClassId,
			pointer(path, "ownerClassId"),
			"The location owner class ID",
		),
		integerIssue(
			record.carrierInstanceId,
			pointer(path, "carrierInstanceId"),
			"The carrier instance ID",
			1,
		),
		nullableStringIssue(
			record.origin,
			pointer(path, "origin"),
			"The source origin",
		),
	];
	for (const check of checks) if (check) return check;
	const offsetPath = pointer(path, "sourceOffset");
	let nestedIssue = recordIssue(
		record.sourceOffset,
		offsetPath,
		["start", "end"],
		"A source-offset record",
		false,
	);
	if (nestedIssue) return nestedIssue;
	const offset = record.sourceOffset as Record<string, unknown>;
	for (const field of ["start", "end"] as const) {
		nestedIssue = integerIssue(
			offset[field],
			pointer(offsetPath, field),
			`The source-offset ${field}`,
			0,
		);
		if (nestedIssue) return nestedIssue;
	}
	const positionPath = pointer(path, "sourcePos");
	nestedIssue = recordIssue(
		record.sourcePos,
		positionPath,
		["line", "column"],
		"A source-position record",
		false,
	);
	if (nestedIssue) return nestedIssue;
	const position = record.sourcePos as Record<string, unknown>;
	for (const field of ["line", "column"] as const) {
		nestedIssue = integerIssue(
			position[field],
			pointer(positionPath, field),
			`The source-position ${field}`,
			1,
		);
		if (nestedIssue) return nestedIssue;
	}
	nestedIssue = nullableStringIssue(
		record.mappingKey,
		pointer(path, "mappingKey"),
		"The mapping key",
	);
	if (nestedIssue) return nestedIssue;
	return nullableIntegerIssue(
		record.mappingIndex,
		pointer(path, "mappingIndex"),
		"The mapping index",
		0,
	);
};

export const validateClientBindingPayload = (
	value: unknown,
	path = "",
	strict = true,
): ValidationIssue | null => {
	if (strict) {
		const issue = validateStrictJson(value, path);
		if (issue) return issue;
	}
	if (!isPlainObject(value))
		return {
			path,
			category: "type",
			message: "A client-binding payload must be an object.",
		};
	if (!hasOwn(value, "type")) {
		return {
			path: pointer(path, "type"),
			category: "required",
			message: "A client-binding payload requires 'type'.",
		};
	}
	if (typeof value.type !== "string") {
		return {
			path: pointer(path, "type"),
			category: "type",
			message: "The client-binding payload type must be a string.",
		};
	}
	const fields =
		value.type === "props" || value.type === "alpine-handler"
			? EXPRESSION_PAYLOAD_FIELDS
			: value.type === "citry-dom-event"
				? DOM_PAYLOAD_FIELDS
				: value.type === "citry-poll"
					? POLL_PAYLOAD_FIELDS
					: null;
	if (fields === null) {
		return {
			path: pointer(path, "type"),
			category: "enum",
			message: "The client-binding payload type is not a v1 value.",
		};
	}
	const issue = recordIssue(
		value,
		path,
		fields,
		"A client-binding payload",
		false,
	);
	if (issue) return issue;
	if (value.type === "props" || value.type === "alpine-handler")
		return stringIssue(
			value.expression,
			pointer(path, "expression"),
			"The Alpine expression",
		);
	if (value.type === "citry-poll") {
		for (const field of ["classId", "handler"] as const) {
			const fieldIssue = stringIssue(
				value[field],
				pointer(path, field),
				`The poll ${field}`,
			);
			if (fieldIssue) return fieldIssue;
		}
		const argsIssue = nullableStringIssue(
			value.args,
			pointer(path, "args"),
			"The poll arguments",
		);
		return (
			argsIssue ??
			integerIssue(
				value.interval,
				pointer(path, "interval"),
				"The poll interval",
				1,
			)
		);
	}
	for (const field of ["classId", "event", "handler"] as const) {
		const fieldIssue = stringIssue(
			value[field],
			pointer(path, field),
			`The DOM-event ${field}`,
		);
		if (fieldIssue) return fieldIssue;
	}
	let fieldIssue = nullableStringIssue(
		value.args,
		pointer(path, "args"),
		"The DOM-event args",
	);
	if (fieldIssue) return fieldIssue;
	for (const field of ["prevent", "stop", "self", "once"] as const) {
		if (typeof value[field] !== "boolean") {
			return {
				path: pointer(path, field),
				category: "type",
				message: `The DOM-event ${field} flag must be a boolean.`,
			};
		}
	}
	fieldIssue = nullableStringIssue(
		value.key,
		pointer(path, "key"),
		"The DOM-event key",
	);
	if (fieldIssue) return fieldIssue;
	for (const field of ["debounce", "throttle"] as const) {
		fieldIssue = nullableIntegerIssue(
			value[field],
			pointer(path, field),
			`The DOM-event ${field} delay`,
			0,
		);
		if (fieldIssue) return fieldIssue;
	}
	return null;
};

export const validateClientBinding = (
	value: unknown,
	path = "",
	strict = true,
): ValidationIssue | null => {
	const issue = recordIssue(
		value,
		path,
		CLIENT_BINDING_FIELDS,
		"A component-tag client-binding record",
		strict,
	);
	if (issue) return issue;
	const record = value as Record<string, unknown>;
	const checks = [
		stringIssue(record.key, pointer(path, "key"), "The client-binding key"),
		enumIssue(
			record.source,
			pointer(path, "source"),
			BINDING_SOURCES,
			"The client-binding source",
		),
		nullableIntegerIssue(
			record.locationId,
			pointer(path, "locationId"),
			"The client-binding location ID",
			1,
		),
	];
	for (const check of checks) if (check) return check;
	return validateClientBindingPayload(
		record.payload,
		pointer(path, "payload"),
		false,
	);
};

export const validateNestedComponent = (
	value: unknown,
	path = "",
	strict = true,
): ValidationIssue | null => {
	const issue = recordIssue(
		value,
		path,
		NESTED_COMPONENT_FIELDS,
		"A nested-component record",
		strict,
	);
	if (issue) return issue;
	const record = value as Record<string, unknown>;
	const checks = [
		integerIssue(
			record.invocationId,
			pointer(path, "invocationId"),
			"The invocation ID",
			1,
		),
		stringIssue(
			record.sourceRenderId,
			pointer(path, "sourceRenderId"),
			"The source render ID",
		),
		stringIssue(
			record.sourceClassId,
			pointer(path, "sourceClassId"),
			"The source class ID",
		),
		nullableIntegerIssue(
			record.locationId,
			pointer(path, "locationId"),
			"The location ID",
			1,
		),
		stringIssue(
			record.tagName,
			pointer(path, "tagName"),
			"The nested-component tag name",
		),
		stringIssue(
			record.targetClassId,
			pointer(path, "targetClassId"),
			"The target class ID",
		),
		nullableStringIssue(
			record.morphKey,
			pointer(path, "morphKey"),
			"The component morph key",
		),
		nullableEnumIssue(
			record.morphMode,
			pointer(path, "morphMode"),
			MORPH_MODES,
			"The component morph mode",
		),
		stringIssue(
			record.targetRenderId,
			pointer(path, "targetRenderId"),
			"The target render ID",
		),
		nullableIntegerIssue(
			record.parentRegionId,
			pointer(path, "parentRegionId"),
			"The parent slot-region ID",
			1,
		),
	];
	for (const check of checks) if (check) return check;
	if (!Array.isArray(record.clientBindings)) {
		return {
			path: pointer(path, "clientBindings"),
			category: "type",
			message: "Client bindings must be an array.",
		};
	}
	for (let index = 0; index < record.clientBindings.length; index += 1) {
		const bindingIssue = validateClientBinding(
			record.clientBindings[index],
			pointer(pointer(path, "clientBindings"), index),
			false,
		);
		if (bindingIssue) return bindingIssue;
	}
	return null;
};

export const validateExecutionConstraint = (
	value: unknown,
	path = "",
	strict = true,
): ValidationIssue | null => {
	const issue = recordIssue(
		value,
		path,
		EXECUTION_CONSTRAINT_FIELDS,
		"An execution-order constraint",
		strict,
	);
	if (issue) return issue;
	const record = value as Record<string, unknown>;
	return (
		integerIssue(
			record.invocationId,
			pointer(path, "invocationId"),
			"The invocation ID",
			1,
		) ??
		stringIssue(
			record.parentRenderId,
			pointer(path, "parentRenderId"),
			"The parent render ID",
		) ??
		stringIssue(
			record.childRenderId,
			pointer(path, "childRenderId"),
			"The child render ID",
		)
	);
};

export const validateFill = (
	value: unknown,
	path = "",
	strict = true,
): ValidationIssue | null => {
	const issue = recordIssue(value, path, FILL_FIELDS, "A fill record", strict);
	if (issue) return issue;
	const record = value as Record<string, unknown>;
	const checks = [
		integerIssue(record.fillId, pointer(path, "fillId"), "The fill ID", 1),
		enumIssue(record.kind, pointer(path, "kind"), FILL_KINDS, "The fill kind"),
		stringIssue(
			record.slotName,
			pointer(path, "slotName"),
			"The fill slot name",
		),
		enumIssue(
			record.policy,
			pointer(path, "policy"),
			SOURCE_POLICIES,
			"The fill source policy",
		),
		nullableStringIssue(
			record.ownerRenderId,
			pointer(path, "ownerRenderId"),
			"The fill owner render ID",
		),
		nullableStringIssue(
			record.ownerClassId,
			pointer(path, "ownerClassId"),
			"The fill owner class ID",
		),
		nullableIntegerIssue(
			record.locationId,
			pointer(path, "locationId"),
			"The fill location ID",
			1,
		),
		nullableIntegerIssue(
			record.sourceInvocationId,
			pointer(path, "sourceInvocationId"),
			"The source invocation ID",
			1,
		),
		nullableStringIssue(
			record.receiverRenderId,
			pointer(path, "receiverRenderId"),
			"The fill receiver render ID",
		),
		nullableStringIssue(
			record.receiverClassId,
			pointer(path, "receiverClassId"),
			"The fill receiver class ID",
		),
		nullableIntegerIssue(
			record.fallbackLocationId,
			pointer(path, "fallbackLocationId"),
			"The fallback location ID",
			1,
		),
	];
	return checks.find((check) => check !== null) ?? null;
};

export const validateSlotRegion = (
	value: unknown,
	path = "",
	strict = true,
): ValidationIssue | null => {
	const issue = recordIssue(
		value,
		path,
		SLOT_REGION_FIELDS,
		"A slot-region record",
		strict,
	);
	if (issue) return issue;
	const record = value as Record<string, unknown>;
	const checks = [
		integerIssue(
			record.regionId,
			pointer(path, "regionId"),
			"The slot-region ID",
			1,
		),
		integerIssue(record.fillId, pointer(path, "fillId"), "The fill ID", 1),
		nullableStringIssue(
			record.receiverRenderId,
			pointer(path, "receiverRenderId"),
			"The receiver render ID",
		),
		nullableIntegerIssue(
			record.slotLocationId,
			pointer(path, "slotLocationId"),
			"The slot location ID",
			1,
		),
		nullableStringIssue(
			record.ownerRenderId,
			pointer(path, "ownerRenderId"),
			"The owner render ID",
		),
		nullableIntegerIssue(
			record.sourceLocationId,
			pointer(path, "sourceLocationId"),
			"The source location ID",
			1,
		),
		nullableIntegerIssue(
			record.parentRegionId,
			pointer(path, "parentRegionId"),
			"The parent slot-region ID",
			1,
		),
		nullableStringIssue(
			record.transitionFromRenderId,
			pointer(path, "transitionFromRenderId"),
			"The transition source render ID",
		),
		nullableStringIssue(
			record.resultOwnerRenderId,
			pointer(path, "resultOwnerRenderId"),
			"The result owner render ID",
		),
	];
	return checks.find((check) => check !== null) ?? null;
};

export const validateGraph = (
	value: unknown,
	path = "",
	strict = true,
): ValidationIssue | null => {
	const issue = recordIssue(
		value,
		path,
		GRAPH_FIELDS,
		"A graph record",
		strict,
	);
	if (issue) return issue;
	const graph = value as Record<string, unknown>;
	const graphIdIssue = integerIssue(
		graph.graphId,
		pointer(path, "graphId"),
		"The graph ID",
		0,
	);
	if (graphIdIssue) return graphIdIssue;
	const collections: readonly [
		string,
		(value: unknown, path?: string, strict?: boolean) => ValidationIssue | null,
	][] = [
		["componentClasses", validateComponentClass],
		["componentInstances", validateComponentInstance],
		["sourceLocations", validateSourceLocation],
		["nestedComponents", validateNestedComponent],
		["componentExecutionOrderConstraints", validateExecutionConstraint],
		["fills", validateFill],
		["slotRegions", validateSlotRegion],
	];
	for (const [field, validator] of collections) {
		const records = graph[field];
		const fieldPath = pointer(path, field);
		if (!Array.isArray(records)) {
			return {
				path: fieldPath,
				category: "type",
				message: `The graph's ${field} must be an array.`,
			};
		}
		for (let index = 0; index < records.length; index += 1) {
			const recordValidationIssue = validator(
				records[index],
				pointer(fieldPath, index),
				false,
			);
			if (recordValidationIssue) return recordValidationIssue;
		}
	}
	return null;
};
