import {
	ACTION_KINDS,
	CAPABILITIES_BASELINE_V1,
	isSafeRenderId,
	PROTOCOL,
	SWAPS,
} from "./calls";
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
	EventAction,
	EventActionKind,
	EventErrorCode,
	EventProtocolError,
	EventResult,
	EventSuccessResult,
	EventsAnsweredResultEnvelope,
	EventsCallEnvelope,
	EventsResultEnvelope,
} from "./types";

export const ERROR_STATUS_BY_CODE: Record<EventErrorCode, number | null> = {
	invalid_args: 422,
	invalid_state: 403,
	stale_state: 409,
	unknown_event: 404,
	unknown_component: 404,
	forbidden: 403,
	not_found: 404,
	conflict: 409,
	error: null,
	csrf_failed: 403,
	payload_too_large: 413,
	protocol_mismatch: 400,
	handler_error: 500,
};

const RESULT_ENVELOPE_FIELDS = new Set(["protocol", "requestId", "results"]);
const OK_RESULT_FIELDS = new Set(["ok", "sendSequence", "actions"]);
const ERROR_RESULT_FIELDS = new Set(["ok", "sendSequence", "error"]);
const ERROR_FIELDS = new Set(["status", "code", "message", "fieldErrors"]);
const ACTION_FIELDS: Record<EventActionKind, ReadonlySet<string>> = {
	render: new Set(["action", "target", "swap", "html", "delay", "wait"]),
	data: new Set(["action", "value", "delay"]),
	state: new Set(["action", "targetRenderId", "stateToken", "delay", "wait"]),
	event: new Set(["action", "eventName", "detail", "target", "delay", "wait"]),
	redirect: new Set(["action", "url", "delay", "wait"]),
	url: new Set(["action", "url", "mode", "delay", "wait"]),
};
const ACTION_REQUIRED: Record<EventActionKind, readonly string[]> = {
	render: ["action", "target", "swap", "html"],
	data: ["action", "value"],
	state: ["action", "targetRenderId", "stateToken"],
	event: ["action", "eventName"],
	redirect: ["action", "url"],
	url: ["action", "url", "mode"],
};

const prefixed = (base: string, issue: ValidationIssue): ValidationIssue => ({
	path: base + issue.path,
	category: issue.category,
	message: issue.message,
});

const validateNonNegativeInteger = (
	value: unknown,
	path: string,
	message: string,
): ValidationIssue | null => {
	if (typeof value !== "number" || !Number.isInteger(value)) {
		return {
			path,
			category:
				typeof value === "number" && !Number.isFinite(value)
					? "strict_json"
					: "type",
			message,
		};
	}
	if (value < 0) return { path, category: "range", message };
	return null;
};

const validateTiming = (
	value: Record<string, unknown>,
	path: string,
): ValidationIssue | null => {
	if (hasOwn(value, "delay")) {
		const delay = value.delay;
		if (typeof delay !== "number") {
			return {
				path: pointer(path, "delay"),
				category: "type",
				message: "The action delay must be a finite number.",
			};
		}
		if (!Number.isFinite(delay)) {
			return {
				path: pointer(path, "delay"),
				category: "strict_json",
				message: "The action delay must be finite.",
			};
		}
		if (delay < 0) {
			return {
				path: pointer(path, "delay"),
				category: "range",
				message: "The action delay must be at least 0.",
			};
		}
	}
	if (hasOwn(value, "wait") && value.wait !== false) {
		return {
			path: pointer(path, "wait"),
			category: "enum",
			message: "The action wait flag, when present, must be false.",
		};
	}
	return null;
};

const validateTarget = (
	value: unknown,
	path: string,
): ValidationIssue | null => {
	if (typeof value !== "string") {
		return {
			path,
			category: "type",
			message: "An action target must be a non-empty string.",
		};
	}
	if (!value) {
		return {
			path,
			category: "range",
			message: "An action target must be a non-empty string.",
		};
	}
	if (value.startsWith("render:") && !isSafeRenderId(value.slice(7))) {
		return {
			path,
			category: "pattern",
			message: "A render target must contain a valid render ID.",
		};
	}
	return null;
};

export const validateAction = (
	value: unknown,
	path = "",
): ValidationIssue | null => {
	const jsonIssue = validateStrictJson(value, path);
	if (jsonIssue) return jsonIssue;
	if (!isPlainObject(value)) {
		return { path, category: "type", message: "An action must be an object." };
	}
	if (!hasOwn(value, "action")) {
		return {
			path: pointer(path, "action"),
			category: "required",
			message: "The action kind is required.",
		};
	}
	if (typeof value.action !== "string") {
		return {
			path: pointer(path, "action"),
			category: "type",
			message: "The action kind must be a string.",
		};
	}
	if (!(ACTION_KINDS as readonly string[]).includes(value.action)) {
		return {
			path: pointer(path, "action"),
			category: "enum",
			message: `Unknown action kind '${value.action}'.`,
		};
	}
	const kind = value.action as EventActionKind;
	for (const required of ACTION_REQUIRED[kind]) {
		if (!hasOwn(value, required)) {
			return {
				path: pointer(path, required),
				category: "required",
				message: `The ${kind} action requires '${required}'.`,
			};
		}
	}
	const unknown = firstUnknown(value, ACTION_FIELDS[kind]);
	if (unknown !== null) {
		return {
			path: pointer(path, unknown),
			category: "unknown_field",
			message: `The ${kind} action has an unknown field.`,
		};
	}
	if (kind === "render") {
		const targetIssue = validateTarget(value.target, pointer(path, "target"));
		if (targetIssue) return targetIssue;
		if (!(SWAPS as readonly unknown[]).includes(value.swap)) {
			return {
				path: pointer(path, "swap"),
				category: typeof value.swap === "string" ? "enum" : "type",
				message: "The render swap is not a v1 swap.",
			};
		}
		if (typeof value.html !== "string") {
			return {
				path: pointer(path, "html"),
				category: "type",
				message: "The render HTML must be a string.",
			};
		}
	} else if (kind === "data") {
		const issue = validateStrictJson(value.value);
		if (issue) return prefixed(pointer(path, "value"), issue);
	} else if (kind === "state") {
		if (typeof value.targetRenderId !== "string") {
			return {
				path: pointer(path, "targetRenderId"),
				category: "type",
				message: "The state target must be a render ID.",
			};
		}
		if (!isSafeRenderId(value.targetRenderId)) {
			return {
				path: pointer(path, "targetRenderId"),
				category: "pattern",
				message: "The state target must be a valid render ID.",
			};
		}
		if (typeof value.stateToken !== "string") {
			return {
				path: pointer(path, "stateToken"),
				category: "type",
				message: "The state token must be a string.",
			};
		}
		if (!value.stateToken) {
			return {
				path: pointer(path, "stateToken"),
				category: "range",
				message: "The state token must not be empty.",
			};
		}
	} else if (kind === "event") {
		if (typeof value.eventName !== "string") {
			return {
				path: pointer(path, "eventName"),
				category: "type",
				message: "The event name must be a string.",
			};
		}
		if (!value.eventName) {
			return {
				path: pointer(path, "eventName"),
				category: "range",
				message: "The event name must not be empty.",
			};
		}
		if (value.eventName.startsWith("citry:")) {
			return {
				path: pointer(path, "eventName"),
				category: "pattern",
				message: "The event name is reserved.",
			};
		}
		if (hasOwn(value, "detail")) {
			const issue = validateStrictJson(value.detail);
			if (issue) return prefixed(pointer(path, "detail"), issue);
		}
		if (hasOwn(value, "target")) {
			const issue = validateTarget(value.target, pointer(path, "target"));
			if (issue) return issue;
		}
	} else if (kind === "redirect") {
		if (typeof value.url !== "string") {
			return {
				path: pointer(path, "url"),
				category: "type",
				message: "The redirect URL must be a string.",
			};
		}
		if (!value.url) {
			return {
				path: pointer(path, "url"),
				category: "range",
				message: "The redirect URL must not be empty.",
			};
		}
	} else {
		if (typeof value.url !== "string") {
			return {
				path: pointer(path, "url"),
				category: "type",
				message: "The URL action URL must be a string.",
			};
		}
		if (!value.url) {
			return {
				path: pointer(path, "url"),
				category: "range",
				message: "The URL action URL must not be empty.",
			};
		}
		if (value.mode !== "push" && value.mode !== "replace") {
			return {
				path: pointer(path, "mode"),
				category: typeof value.mode === "string" ? "enum" : "type",
				message: "The URL action mode must be push or replace.",
			};
		}
	}
	return validateTiming(value, path);
};

export const validateError = (
	value: unknown,
	path = "",
): ValidationIssue | null => {
	const jsonIssue = validateStrictJson(value, path);
	if (jsonIssue) return jsonIssue;
	if (!isPlainObject(value)) {
		return {
			path,
			category: "type",
			message: "The result error must be an object.",
		};
	}
	for (const required of ["status", "code", "message"]) {
		if (!hasOwn(value, required)) {
			return {
				path: pointer(path, required),
				category: "required",
				message: `The error requires '${required}'.`,
			};
		}
	}
	const unknown = firstUnknown(value, ERROR_FIELDS);
	if (unknown !== null) {
		return {
			path: pointer(path, unknown),
			category: "unknown_field",
			message: "The result error has an unknown field.",
		};
	}
	if (typeof value.status !== "number" || !Number.isInteger(value.status)) {
		return {
			path: pointer(path, "status"),
			category:
				typeof value.status === "number" && !Number.isFinite(value.status)
					? "strict_json"
					: "type",
			message: "The error status must be an integer.",
		};
	}
	if (value.status < 400 || value.status > 599) {
		return {
			path: pointer(path, "status"),
			category: "range",
			message: "The error status must be from 400 to 599.",
		};
	}
	if (typeof value.code !== "string") {
		return {
			path: pointer(path, "code"),
			category: "type",
			message: "The error code must be a string.",
		};
	}
	if (!hasOwn(ERROR_STATUS_BY_CODE, value.code)) {
		return {
			path: pointer(path, "code"),
			category: "enum",
			message: "The error code is not a v1 code.",
		};
	}
	if (typeof value.message !== "string") {
		return {
			path: pointer(path, "message"),
			category: "type",
			message: "The error message must be a string.",
		};
	}
	if (!value.message) {
		return {
			path: pointer(path, "message"),
			category: "range",
			message: "The error message must not be empty.",
		};
	}
	if (hasOwn(value, "fieldErrors")) {
		if (!isPlainObject(value.fieldErrors)) {
			return {
				path: pointer(path, "fieldErrors"),
				category: "type",
				message: "Field errors must be an object.",
			};
		}
		for (const name of Object.keys(value.fieldErrors).sort()) {
			if (typeof value.fieldErrors[name] !== "string") {
				return {
					path: pointer(pointer(path, "fieldErrors"), name),
					category: "type",
					message: "Field errors map strings.",
				};
			}
		}
	}
	const expected = ERROR_STATUS_BY_CODE[value.code as EventErrorCode];
	if (expected !== null && value.status !== expected) {
		return {
			path: pointer(path, "status"),
			category: "semantic",
			message: "The error status does not match its code.",
		};
	}
	return null;
};

export const validateResult = (
	value: unknown,
	path = "",
): ValidationIssue | null => {
	const jsonIssue = validateStrictJson(value, path);
	if (jsonIssue) return jsonIssue;
	if (!isPlainObject(value)) {
		return { path, category: "type", message: "A result must be an object." };
	}
	if (!hasOwn(value, "ok")) {
		return {
			path: pointer(path, "ok"),
			category: "required",
			message: "The result requires 'ok'.",
		};
	}
	if (typeof value.ok !== "boolean") {
		return {
			path: pointer(path, "ok"),
			category: "type",
			message: "The result's 'ok' field must be a boolean.",
		};
	}
	const required = value.ok ? ["ok", "actions"] : ["ok", "error"];
	for (const field of required) {
		if (!hasOwn(value, field)) {
			return {
				path: pointer(path, field),
				category: "required",
				message: `The result requires '${field}'.`,
			};
		}
	}
	const unknown = firstUnknown(
		value,
		value.ok ? OK_RESULT_FIELDS : ERROR_RESULT_FIELDS,
	);
	if (unknown !== null) {
		return {
			path: pointer(path, unknown),
			category: "unknown_field",
			message: "The result has an unknown field.",
		};
	}
	if (hasOwn(value, "sendSequence")) {
		const issue = validateNonNegativeInteger(
			value.sendSequence,
			pointer(path, "sendSequence"),
			"The send sequence must be an integer.",
		);
		if (issue) return issue;
	}
	if (!value.ok) return validateError(value.error, pointer(path, "error"));
	if (!Array.isArray(value.actions)) {
		return {
			path: pointer(path, "actions"),
			category: "type",
			message: "The result actions must be an array.",
		};
	}
	for (let index = 0; index < value.actions.length; index += 1) {
		const issue = validateAction(value.actions[index]);
		if (issue) return prefixed(pointer(pointer(path, "actions"), index), issue);
	}
	if (
		value.actions.filter(
			(action) => isPlainObject(action) && action.action === "data",
		).length > 1
	) {
		return {
			path: pointer(path, "actions"),
			category: "semantic",
			message: "Each result may carry at most one data action.",
		};
	}
	return null;
};

export const validateResultEnvelope = (
	value: unknown,
	path = "",
): ValidationIssue | null => {
	const jsonIssue = validateStrictJson(value, path);
	if (jsonIssue) return jsonIssue;
	if (!isPlainObject(value)) {
		return {
			path,
			category: "type",
			message: "The result envelope must be an object.",
		};
	}
	for (const required of ["protocol", "requestId", "results"]) {
		if (!hasOwn(value, required)) {
			return {
				path: pointer(path, required),
				category: "required",
				message: `The result envelope requires '${required}'.`,
			};
		}
	}
	const unknown = firstUnknown(value, RESULT_ENVELOPE_FIELDS);
	if (unknown !== null) {
		return {
			path: pointer(path, unknown),
			category: "unknown_field",
			message: "The result envelope has an unknown field.",
		};
	}
	if (value.protocol !== PROTOCOL) {
		return {
			path: pointer(path, "protocol"),
			category: typeof value.protocol === "string" ? "enum" : "type",
			message: "The result protocol must be citry-events/1.",
		};
	}
	if (value.requestId !== null && typeof value.requestId !== "string") {
		return {
			path: pointer(path, "requestId"),
			category: "type",
			message: "The result request ID must be a string or null.",
		};
	}
	if (value.requestId === "") {
		return {
			path: pointer(path, "requestId"),
			category: "range",
			message: "The result request ID must not be empty.",
		};
	}
	if (!Array.isArray(value.results)) {
		return {
			path: pointer(path, "results"),
			category: "type",
			message: "The results must be an array.",
		};
	}
	if (!value.results.length) {
		return {
			path: pointer(path, "results"),
			category: "range",
			message: "The results array must not be empty.",
		};
	}
	for (let index = 0; index < value.results.length; index += 1) {
		const issue = validateResult(value.results[index]);
		if (issue) return prefixed(pointer(pointer(path, "results"), index), issue);
	}
	if (value.requestId === null) {
		if (value.results.length !== 1) {
			return {
				path: pointer(path, "results"),
				category: "correlation",
				message: "An edge error has exactly one result.",
			};
		}
		const result = value.results[0] as Record<string, unknown>;
		const error = result.error as Record<string, unknown>;
		if (
			result.ok !== false ||
			hasOwn(result, "sendSequence") ||
			(error.code !== "protocol_mismatch" &&
				error.code !== "payload_too_large") ||
			hasOwn(error, "fieldErrors")
		) {
			return {
				path: pointer(path, "results"),
				category: "correlation",
				message: "A null request ID is only for one transport-edge error.",
			};
		}
	}
	return null;
};

export const validateExchange = (
	callEnvelope: EventsCallEnvelope,
	resultEnvelope: unknown,
): ValidationIssue | null => {
	const issue = validateResultEnvelope(resultEnvelope);
	if (issue) return issue;
	const result = resultEnvelope as EventsResultEnvelope;
	if (result.requestId !== callEnvelope.requestId) {
		return {
			path: "/requestId",
			category: "correlation",
			message: "The result request ID does not match the call.",
		};
	}
	if (result.results.length !== callEnvelope.calls.length) {
		return {
			path: "/results",
			category: "correlation",
			message: "The result count does not match the call count.",
		};
	}
	const advertised = callEnvelope.capabilities ?? {};
	const actions = new Set(
		advertised.actions ?? CAPABILITIES_BASELINE_V1.actions,
	);
	const swaps = new Set(advertised.swaps ?? CAPABILITIES_BASELINE_V1.swaps);
	for (let index = 0; index < result.results.length; index += 1) {
		const call = callEnvelope.calls[index];
		const answer = result.results[index];
		if (
			answer.sendSequence !== call.sendSequence ||
			hasOwn(answer, "sendSequence") !== hasOwn(call, "sendSequence")
		) {
			return {
				path: `/results/${index}/sendSequence`,
				category: "correlation",
				message: "The result does not echo the call's send sequence.",
			};
		}
		if (!answer.ok) continue;
		for (
			let actionIndex = 0;
			actionIndex < answer.actions.length;
			actionIndex += 1
		) {
			const action = answer.actions[actionIndex];
			if (!actions.has(action.action)) {
				return {
					path: `/results/${index}/actions/${actionIndex}/action`,
					category: "capability",
					message: "The result uses an action the caller did not advertise.",
				};
			}
			if (action.action === "render" && !swaps.has(action.swap)) {
				return {
					path: `/results/${index}/actions/${actionIndex}/swap`,
					category: "capability",
					message: "The result uses a swap the caller did not advertise.",
				};
			}
		}
	}
	return null;
};

export const validateActionList = (actions: unknown): ValidationIssue | null =>
	validateResult({ ok: true, actions });

export const buildOkResult = (
	actions: readonly EventAction[],
	sendSequence?: number,
): EventSuccessResult => {
	const result: Record<string, unknown> = {
		ok: true,
		actions: copyJson(actions),
	};
	if (sendSequence !== undefined) result.sendSequence = sendSequence;
	const issue = validateResult(result);
	if (issue) throw new ProtocolValueError(issue);
	return result as unknown as EventSuccessResult;
};

export const buildResultEnvelope = (
	requestId: string,
	results: readonly EventResult[],
): EventsAnsweredResultEnvelope => {
	const envelope = {
		protocol: PROTOCOL,
		requestId,
		results: copyJson([...results]),
	};
	const issue = validateResultEnvelope(envelope);
	if (issue) throw new ProtocolValueError(issue);
	return envelope;
};

export interface ResultPreflightSuccess {
	ok: true;
	results: EventResult[];
}

export interface ResultPreflightFailure {
	ok: false;
	issue: ValidationIssue;
	reason: string;
}

export type ResultPreflight = ResultPreflightSuccess | ResultPreflightFailure;

const resultIndex = (path: string): number | null => {
	const match = /^\/results\/(\d+)(?:\/|$)/.exec(path);
	return match ? Number(match[1]) : null;
};

export const preflightResultEnvelope = (
	reply: unknown,
	sent: EventsCallEnvelope,
): ResultPreflight => {
	const structural = validateResultEnvelope(reply);
	if (structural) {
		const edge = isPlainObject(reply) && reply.requestId === null;
		const index = resultIndex(structural.path);
		return {
			ok: false,
			issue: structural,
			reason:
				edge && structural.path.startsWith("/results")
					? "edge"
					: index === null
						? "header"
						: `result ${index}`,
		};
	}
	const envelope = reply as EventsResultEnvelope;
	if (envelope.requestId === null) {
		const edge = envelope.results[0];
		return { ok: true, results: sent.calls.map(() => edge) };
	}
	const relationship = validateExchange(sent, envelope);
	if (relationship) {
		const index = resultIndex(relationship.path);
		return {
			ok: false,
			issue: relationship,
			reason:
				relationship.path === "/requestId" ||
				(relationship.path === "/results" &&
					relationship.category === "correlation")
					? "correlation"
					: `result ${index ?? 0}`,
		};
	}
	return { ok: true, results: envelope.results };
};

export const assertValidActionList = (actions: unknown): EventAction[] => {
	const issue = validateActionList(actions);
	if (issue) throw new ProtocolValueError(issue);
	return actions as EventAction[];
};

export const assertValidResultEnvelope = (
	value: unknown,
): EventsResultEnvelope => {
	const issue = validateResultEnvelope(value);
	if (issue) throw new ProtocolValueError(issue);
	return value as EventsResultEnvelope;
};

export const asProtocolError = (value: unknown): EventProtocolError | null =>
	validateError(value) === null ? (value as EventProtocolError) : null;
