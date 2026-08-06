import {
	copyJson,
	firstUnknown,
	hasOwn,
	isPlainObject,
	ProtocolValueError,
	pointer,
	type ValidationIssue,
	validateStrictJson,
} from "./issue";
import type {
	EventActionKind,
	EventCall,
	EventSwap,
	EventsCallEnvelope,
	EventsCapabilities,
	JsonObject,
} from "./types";

export const PROTOCOL = "citry-events/1" as const;
export const CALLS_LIMIT = 16;
export const ACTION_KINDS = [
	"render",
	"data",
	"state",
	"event",
	"redirect",
	"url",
] as const satisfies readonly EventActionKind[];
export const SWAPS = [
	"morph",
	"replace",
	"inner",
	"append",
	"prepend",
	"remove",
	"none",
] as const satisfies readonly EventSwap[];
export const CAPABILITIES_BASELINE_V1 = {
	swaps: ["replace", "inner", "append", "prepend", "remove", "none"],
	actions: ACTION_KINDS,
} as const;
export const CARRIER_FIELDS = {
	callerRenderId: "_citry_caller_render_id",
	stateToken: "_citry_state_token",
	sendSequence: "_citry_send_sequence",
	protocol: "_citry_protocol",
	requestId: "_citry_request_id",
	capabilities: "_citry_capabilities",
} as const;

const ENVELOPE_FIELDS = new Set([
	"protocol",
	"requestId",
	"capabilities",
	"calls",
]);
const CALL_FIELDS = new Set([
	"componentClassId",
	"handlerName",
	"callerRenderId",
	"args",
	"stateToken",
	"stateUpdates",
	"sendSequence",
]);

export const isSafeRenderId = (value: unknown): value is string =>
	typeof value === "string" && /^[a-z0-9_-]+$/.test(value);

const nonEmptyStringIssue = (
	value: unknown,
	path: string,
	message: string,
): ValidationIssue | null => {
	if (typeof value !== "string") return { path, category: "type", message };
	if (!value) return { path, category: "range", message };
	return null;
};

const integerIssue = (
	value: unknown,
	path: string,
	message: string,
): ValidationIssue | null => {
	if (typeof value !== "number" || !Number.isInteger(value)) {
		if (typeof value === "number" && !Number.isFinite(value)) {
			return { path, category: "strict_json", message };
		}
		return { path, category: "type", message };
	}
	if (value < 0) return { path, category: "range", message };
	return null;
};

export const validateCall = (
	value: unknown,
	path = "",
): ValidationIssue | null => {
	const jsonIssue = validateStrictJson(value, path);
	if (jsonIssue) return jsonIssue;
	if (!isPlainObject(value)) {
		return {
			path,
			category: "type",
			message: "Each entry of 'calls' must be a call object.",
		};
	}
	for (const required of ["componentClassId", "handlerName", "args"]) {
		if (!hasOwn(value, required)) {
			return {
				path: pointer(path, required),
				category: "required",
				message: `The call is missing required field '${required}'.`,
			};
		}
	}
	const unknown = firstUnknown(value, CALL_FIELDS);
	if (unknown !== null) {
		return {
			path: pointer(path, unknown),
			category: "unknown_field",
			message: `The call carries unknown field '${unknown}'.`,
		};
	}
	for (const field of ["componentClassId", "handlerName"] as const) {
		const issue = nonEmptyStringIssue(
			value[field],
			pointer(path, field),
			`The call's '${field}' must be a non-empty string.`,
		);
		if (issue) return issue;
	}
	if (hasOwn(value, "callerRenderId")) {
		const issue = nonEmptyStringIssue(
			value.callerRenderId,
			pointer(path, "callerRenderId"),
			"The call's 'callerRenderId' must be a non-empty string.",
		);
		if (issue) return issue;
		if (!isSafeRenderId(value.callerRenderId)) {
			return {
				path: pointer(path, "callerRenderId"),
				category: "pattern",
				message:
					"The call's 'callerRenderId' must use only lowercase ASCII letters, digits, hyphens, and underscores.",
			};
		}
	}
	if (!isPlainObject(value.args)) {
		return {
			path: pointer(path, "args"),
			category: "type",
			message: "The call's 'args' must be an object.",
		};
	}
	const argsIssue = validateStrictJson(value.args);
	if (argsIssue) {
		return {
			path: pointer(path, "args") + argsIssue.path,
			category: "strict_json",
			message:
				"The call's 'args' must contain only strict JSON values under string keys.",
		};
	}
	if (hasOwn(value, "stateToken")) {
		const issue = nonEmptyStringIssue(
			value.stateToken,
			pointer(path, "stateToken"),
			"The call's 'stateToken' must be a non-empty string.",
		);
		if (issue) return issue;
	}
	if (hasOwn(value, "stateUpdates")) {
		if (!isPlainObject(value.stateUpdates)) {
			return {
				path: pointer(path, "stateUpdates"),
				category: "type",
				message: "The call's 'stateUpdates' must be an object.",
			};
		}
		const stateIssue = validateStrictJson(value.stateUpdates);
		if (stateIssue) {
			return {
				path: pointer(path, "stateUpdates") + stateIssue.path,
				category: "strict_json",
				message:
					"The call's 'stateUpdates' must contain only strict JSON values under string keys.",
			};
		}
	}
	if (hasOwn(value, "sendSequence")) {
		return integerIssue(
			value.sendSequence,
			pointer(path, "sendSequence"),
			"The call's 'sendSequence' must be an integer of at least 0.",
		);
	}
	return null;
};

export const validateCapabilities = (
	value: unknown,
	path = "/capabilities",
): ValidationIssue | null => {
	const jsonIssue = validateStrictJson(value, path);
	if (jsonIssue) return jsonIssue;
	const message =
		"The envelope's 'capabilities' must contain only 'swaps' and 'actions'; each value must be a duplicate-free array of known v1 names.";
	if (!isPlainObject(value)) return { path, category: "type", message };
	const unknown = firstUnknown(value, new Set(["swaps", "actions"]));
	if (unknown !== null) {
		return { path: pointer(path, unknown), category: "unknown_field", message };
	}
	for (const [name, known] of [
		["swaps", SWAPS],
		["actions", ACTION_KINDS],
	] as const) {
		if (!hasOwn(value, name)) continue;
		const items = value[name];
		const itemPath = pointer(path, name);
		if (!Array.isArray(items))
			return { path: itemPath, category: "type", message };
		for (let index = 0; index < items.length; index += 1) {
			if (typeof items[index] !== "string") {
				return { path: pointer(itemPath, index), category: "type", message };
			}
			if (!(known as readonly string[]).includes(items[index])) {
				return { path: pointer(itemPath, index), category: "enum", message };
			}
		}
		if (new Set(items).size !== items.length) {
			return { path: itemPath, category: "semantic", message };
		}
	}
	return null;
};

export const validateCallEnvelope = (
	value: unknown,
): ValidationIssue | null => {
	const jsonIssue = validateStrictJson(value);
	if (jsonIssue) return jsonIssue;
	if (!isPlainObject(value)) {
		return {
			path: "",
			category: "type",
			message: "The request body is not a call envelope object.",
		};
	}
	for (const required of ["protocol", "requestId", "calls"]) {
		if (!hasOwn(value, required)) {
			return {
				path: pointer("", required),
				category: "required",
				message: `The envelope requires '${required}'.`,
			};
		}
	}
	const unknown = firstUnknown(value, ENVELOPE_FIELDS);
	if (unknown !== null) {
		return {
			path: pointer("", unknown),
			category: "unknown_field",
			message: `The envelope carries unknown field '${unknown}'.`,
		};
	}
	if (value.protocol !== PROTOCOL) {
		return {
			path: "/protocol",
			category: typeof value.protocol === "string" ? "enum" : "type",
			message: "The envelope protocol must be citry-events/1.",
		};
	}
	const requestIssue = nonEmptyStringIssue(
		value.requestId,
		"/requestId",
		"The envelope carries no 'requestId' string.",
	);
	if (requestIssue) return requestIssue;
	if (hasOwn(value, "capabilities")) {
		const issue = validateCapabilities(value.capabilities);
		if (issue) return issue;
	}
	if (!Array.isArray(value.calls)) {
		return {
			path: "/calls",
			category: "type",
			message: "The envelope calls must be an array.",
		};
	}
	if (!value.calls.length || value.calls.length > CALLS_LIMIT) {
		return {
			path: "/calls",
			category: "range",
			message: `The envelope must carry 1 to ${CALLS_LIMIT} calls.`,
		};
	}
	for (let index = 0; index < value.calls.length; index += 1) {
		const issue = validateCall(value.calls[index], `/calls/${index}`);
		if (issue) return issue;
	}
	return null;
};

export interface BuildCallInput {
	componentClassId: string;
	handlerName: string;
	callerRenderId?: string;
	args: Record<string, unknown>;
	stateToken?: string;
	stateUpdates?: Record<string, unknown>;
	sendSequence?: number;
}

export const buildCall = (input: BuildCallInput): EventCall => {
	const call: Record<string, unknown> = {
		componentClassId: input.componentClassId,
		handlerName: input.handlerName,
		args: copyJson(input.args),
	};
	for (const field of [
		"callerRenderId",
		"stateToken",
		"sendSequence",
	] as const) {
		if (input[field] !== undefined) call[field] = input[field];
	}
	if (input.stateUpdates !== undefined) {
		call.stateUpdates = copyJson(input.stateUpdates);
	}
	const issue = validateCall(call);
	if (issue) throw new ProtocolValueError(issue);
	return call as unknown as EventCall;
};

export const buildCallEnvelope = (
	requestId: string,
	calls: readonly EventCall[],
	capabilities?: EventsCapabilities,
): EventsCallEnvelope => {
	const envelope: Record<string, unknown> = {
		protocol: PROTOCOL,
		requestId,
		calls: copyJson(calls),
	};
	if (capabilities !== undefined)
		envelope.capabilities = copyJson(capabilities);
	const issue = validateCallEnvelope(envelope);
	if (issue) throw new ProtocolValueError(issue);
	return envelope as unknown as EventsCallEnvelope;
};

export const fullClientCapabilities = (): EventsCapabilities => ({
	swaps: [...SWAPS],
	actions: [...ACTION_KINDS],
});

export const asJsonObject = (value: Record<string, unknown>): JsonObject =>
	copyJson(value) as JsonObject;
