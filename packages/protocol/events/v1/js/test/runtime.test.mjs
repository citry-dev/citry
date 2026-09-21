import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { build } from "esbuild";

import {
	applyOperations,
	CASE_FORMAT,
	parseCaseFile,
} from "../../../../_tooling/conformance.mjs";

const testsDirectory = new URL("../../tests/", import.meta.url);
const buildResult = await build({
	entryPoints: [new URL("../src/index.ts", import.meta.url).pathname],
	bundle: true,
	format: "esm",
	platform: "node",
	target: "node22",
	write: false,
});
const protocol = await import(
	`data:text/javascript;base64,${Buffer.from(buildResult.outputFiles[0].text).toString("base64")}`
);

const readJson = async (url) => JSON.parse(await readFile(url, "utf8"));

const validatorFor = (schema) => {
	if (schema === "call.schema.json") return protocol.validateCallEnvelope;
	if (schema === "descriptor.schema.json") return protocol.validateDescriptor;
	if (schema === "manifest.schema.json") return protocol.validateManifest;
	if (schema === "result.schema.json") return protocol.validateResultEnvelope;
	throw new Error(`No JavaScript validator for ${schema}`);
};

test("replays shared conformance mutations against the runtime validators", async () => {
	const payload = await readJson(
		new URL("conformance-cases.json", testsDirectory),
	);
	const cases = parseCaseFile(payload);
	assert.ok(cases.length > 0);
	for (const entry of cases) {
		assert.ok(entry.implementations.includes("javascript"), entry.id);
		const seed = await readJson(new URL(entry.seed, testsDirectory));
		const before = structuredClone(seed);
		const mutated = applyOperations(seed, entry.operations);
		assert.deepEqual(seed, before, `${entry.id} mutated its seed`);
		const issue = validatorFor(entry.schema)(mutated);
		assert.ok(issue, `${entry.id} was accepted`);
		assert.deepEqual(
			{ path: issue.path, category: issue.category },
			entry.expected,
			entry.id,
		);
	}
});

test("accepts every valid fixture and rejects every invalid fixture", async () => {
	for (const [directory, validator] of [
		["descriptors", protocol.validateDescriptor],
		["manifests", protocol.validateManifest],
	]) {
		const base = new URL(`${directory}/`, testsDirectory);
		for (const entry of await readJson(new URL("index.json", base))) {
			const issue = validator(await readJson(new URL(entry.file, base)));
			assert.equal(issue === null, entry.valid, `${directory}/${entry.file}`);
		}
	}

	for (const entry of await readJson(new URL("index.json", testsDirectory))) {
		const rawCall = await readJson(new URL(entry.call, testsDirectory));
		const result = await readJson(new URL(entry.result, testsDirectory));
		const call = structuredClone(rawCall);
		const resultErrorCode = result.results?.[0]?.error?.code;
		if (resultErrorCode === "protocol_mismatch") {
			assert.notEqual(rawCall.protocol, protocol.PROTOCOL, entry.call);
			call.protocol = protocol.PROTOCOL;
		} else if (resultErrorCode === "payload_too_large") {
			assert.ok(rawCall.calls.length > protocol.CALLS_LIMIT, entry.call);
			call.calls = rawCall.calls.slice(0, protocol.CALLS_LIMIT);
		}
		assert.equal(protocol.validateCallEnvelope(call), null, entry.call);
		assert.equal(protocol.validateResultEnvelope(result), null, entry.result);
		if (resultErrorCode !== "payload_too_large") {
			assert.equal(protocol.validateExchange(call, result), null, entry.result);
		}
	}
});

test("builders return validated copies instead of caller-owned containers", () => {
	const args = { nested: { count: 1 } };
	const updates = { name: "Ada" };
	const call = protocol.buildCall({
		componentClassId: "Counter",
		handlerName: "increment",
		callerRenderId: "counter_1",
		args,
		stateToken: "token",
		stateUpdates: updates,
		sendSequence: 3,
	});
	args.nested.count = 2;
	updates.name = "Grace";
	assert.deepEqual(call.args, { nested: { count: 1 } });
	assert.deepEqual(call.stateUpdates, { name: "Ada" });

	const envelope = protocol.buildCallEnvelope(
		"request-1",
		[call],
		protocol.fullClientCapabilities(),
	);
	call.args.nested.count = 9;
	assert.deepEqual(envelope.calls[0].args, { nested: { count: 1 } });
	assert.equal(protocol.validateCallEnvelope(envelope), null);
});

test("builders preserve __proto__ as data without changing prototypes", () => {
	const args = JSON.parse('{"__proto__":{"polluted":true}}');
	const call = protocol.buildCall({
		componentClassId: "Counter",
		handlerName: "increment",
		args,
	});
	assert.equal(Object.getPrototypeOf(call.args), Object.prototype);
	assert.equal(protocol.hasOwn(call.args, "__proto__"), true);
	assert.deepEqual(
		Object.getOwnPropertyDescriptor(call.args, "__proto__")?.value,
		{
			polluted: true,
		},
	);
	assert.equal({}.polluted, undefined);
});

test("exports the transport carrier field names", () => {
	assert.deepEqual(protocol.CARRIER_FIELDS, {
		callerRenderId: "_citry_caller_render_id",
		stateToken: "_citry_state_token",
		sendSequence: "_citry_send_sequence",
		protocol: "_citry_protocol",
		requestId: "_citry_request_id",
		capabilities: "_citry_capabilities",
	});
});

test("strict JSON checks reject browser-only invalid values", () => {
	const cyclic = {};
	cyclic.self = cyclic;
	for (const value of [
		Number.NaN,
		Number.POSITIVE_INFINITY,
		Number.NEGATIVE_INFINITY,
		cyclic,
		undefined,
	]) {
		assert.ok(protocol.validateStrictJson(value));
	}
	const sparse = [];
	sparse.length = 1;
	assert.ok(protocol.validateStrictJson(sparse));
	assert.equal(protocol.validateStrictJson({ nested: [1, true, null] }), null);
});

test("public validators reject object shapes JSON text cannot carry", () => {
	const resultEnvelope = protocol.buildResultEnvelope("request-1", [
		protocol.buildOkResult([]),
	]);
	Object.defineProperty(resultEnvelope, "unexpected", {
		configurable: true,
		enumerable: false,
		value: true,
	});
	assert.deepEqual(protocol.validateResultEnvelope(resultEnvelope), {
		path: "/unexpected",
		category: "strict_json",
		message: "A JSON property must be an enumerable data property.",
	});
	delete resultEnvelope.unexpected;

	const symbol = Symbol("unexpected");
	resultEnvelope[symbol] = true;
	assert.deepEqual(protocol.validateResultEnvelope(resultEnvelope), {
		path: "",
		category: "strict_json",
		message: "The value contains a symbol-keyed property.",
	});
	delete resultEnvelope[symbol];

	let getterCalls = 0;
	Object.defineProperty(resultEnvelope, "requestId", {
		configurable: true,
		enumerable: true,
		get() {
			getterCalls += 1;
			return "request-1";
		},
	});
	assert.deepEqual(protocol.validateResultEnvelope(resultEnvelope), {
		path: "/requestId",
		category: "strict_json",
		message: "A JSON property must be an enumerable data property.",
	});
	assert.equal(getterCalls, 0);

	const call = protocol.buildCall({
		componentClassId: "Counter",
		handlerName: "increment",
		args: {},
	});
	call.args.self = call.args;
	assert.deepEqual(protocol.validateCall(call), {
		path: "/args/self",
		category: "strict_json",
		message: "The value contains a cycle.",
	});
});

test("every public validator checks strict JSON before record shape", () => {
	const call = { componentClassId: "C", handlerName: "save", args: {} };
	call.args = { self: call };
	const capabilities = {};
	capabilities.actions = capabilities;
	const callEnvelope = {
		protocol: protocol.PROTOCOL,
		requestId: "r1",
		calls: [],
	};
	callEnvelope.calls.push(callEnvelope);
	const handler = { httpMethod: "POST" };
	handler.self = handler;
	const descriptor = { componentClassId: "C", eventHandlers: {} };
	descriptor.eventHandlers.loop = descriptor;
	const instance = {
		renderId: "c1",
		componentClassId: "C",
		stateToken: null,
		publicState: {},
	};
	instance.publicState = { self: instance };
	const manifest = {
		protocol: protocol.PROTOCOL,
		componentClasses: [],
		componentInstances: [],
	};
	manifest.componentClasses.push(manifest);
	const action = { action: "data", value: null };
	action.value = { self: action };
	const error = { status: 500, code: "handler_error", message: "broken" };
	error.fieldErrors = { self: error };
	const result = { ok: true, actions: [] };
	result.actions.push(result);
	const resultEnvelope = {
		protocol: protocol.PROTOCOL,
		requestId: "r1",
		results: [],
	};
	resultEnvelope.results.push(resultEnvelope);

	for (const [validator, value, path] of [
		[protocol.validateCall, call, "/args/self"],
		[protocol.validateCapabilities, capabilities, "/capabilities/actions"],
		[protocol.validateCallEnvelope, callEnvelope, "/calls/0"],
		[protocol.validateHandlerDescriptor, handler, "/self"],
		[protocol.validateDescriptor, descriptor, "/eventHandlers/loop"],
		[protocol.validateComponentInstance, instance, "/publicState/self"],
		[protocol.validateManifest, manifest, "/componentClasses/0"],
		[protocol.validateAction, action, "/value/self"],
		[protocol.validateError, error, "/fieldErrors/self"],
		[protocol.validateResult, result, "/actions/0"],
		[protocol.validateResultEnvelope, resultEnvelope, "/results/0"],
	]) {
		const issue = validator(value);
		assert.ok(issue);
		assert.equal(issue.path, path);
		assert.equal(issue.category, "strict_json");
	}
});

test("mathematically integral numbers satisfy integer fields", () => {
	assert.equal(
		protocol.validateCallEnvelope({
			protocol: protocol.PROTOCOL,
			requestId: "r1",
			calls: [
				{
					componentClassId: "C",
					handlerName: "save",
					args: {},
					sendSequence: 1.0,
				},
			],
		}),
		null,
	);
	assert.equal(
		protocol.validateHandlerDescriptor({
			httpMethod: "POST",
			debounceMilliseconds: 1.0,
			throttleMilliseconds: 2.0,
		}),
		null,
	);
	assert.equal(
		protocol.validateResultEnvelope({
			protocol: protocol.PROTOCOL,
			requestId: "r1",
			results: [{ ok: true, sendSequence: 1.0, actions: [] }],
		}),
		null,
	);
	assert.equal(
		protocol.validateResultEnvelope({
			protocol: protocol.PROTOCOL,
			requestId: "r1",
			results: [
				{
					ok: false,
					error: {
						status: 500.0,
						code: "handler_error",
						message: "broken",
					},
				},
			],
		}),
		null,
	);
});

test("result preflight validates an entire batch before returning any result", () => {
	const calls = protocol.buildCallEnvelope("request-1", [
		protocol.buildCall({
			componentClassId: "Counter",
			handlerName: "increment",
			args: {},
		}),
		protocol.buildCall({
			componentClassId: "Counter",
			handlerName: "decrement",
			args: {},
		}),
	]);
	const reply = {
		protocol: protocol.PROTOCOL,
		requestId: "request-1",
		results: [
			{ ok: true, actions: [] },
			{ ok: true, actions: [{ action: "redirect", url: "" }] },
		],
	};
	const checked = protocol.preflightResultEnvelope(reply, calls);
	assert.equal(checked.ok, false);
	assert.equal(checked.reason, "result 1");
	assert.equal(checked.issue.path, "/results/1/actions/0/url");
});

test("result validators keep strict-JSON precedence and caller path prefixes", () => {
	const invalid = {
		requestId: "request-1",
		results: [
			{
				ok: true,
				actions: [{ action: "data", value: { nested: Number.NaN } }],
			},
		],
	};
	assert.deepEqual(protocol.validateResultEnvelope(invalid, "/reply"), {
		path: "/reply/results/0/actions/0/value/nested",
		category: "strict_json",
		message: "The value contains a non-finite number.",
	});
	assert.deepEqual(
		protocol.validateAction(
			{ action: "event", eventName: "changed", detail: { value: undefined } },
			"/action",
		),
		{
			path: "/action/detail/value",
			category: "strict_json",
			message: "The value contains a non-JSON value.",
		},
	);
});

test("result preflight validates nested accessors once without invoking them", () => {
	const calls = protocol.buildCallEnvelope("request-1", [
		protocol.buildCall({
			componentClassId: "Counter",
			handlerName: "increment",
			args: {},
		}),
	]);
	let getterCalls = 0;
	const detail = {};
	Object.defineProperty(detail, "value", {
		enumerable: true,
		get() {
			getterCalls += 1;
			return "hidden";
		},
	});
	const checked = protocol.preflightResultEnvelope(
		{
			protocol: protocol.PROTOCOL,
			requestId: "request-1",
			results: [
				{
					ok: true,
					actions: [{ action: "event", eventName: "changed", detail }],
				},
			],
		},
		calls,
	);
	assert.equal(checked.ok, false);
	assert.deepEqual(checked.issue, {
		path: "/results/0/actions/0/detail/value",
		category: "strict_json",
		message: "A JSON property must be an enumerable data property.",
	});
	assert.equal(getterCalls, 0);
});

test("successful result preflight preserves the validated result array identity", () => {
	const calls = protocol.buildCallEnvelope("request-1", [
		protocol.buildCall({
			componentClassId: "Counter",
			handlerName: "increment",
			args: {},
		}),
	]);
	const reply = {
		protocol: protocol.PROTOCOL,
		requestId: "request-1",
		results: [{ ok: true, actions: [{ action: "data", value: { count: 1 } }] }],
	};
	const checked = protocol.preflightResultEnvelope(reply, calls);
	assert.equal(checked.ok, true);
	assert.equal(checked.results, reply.results);
	assert.equal(checked.results[0], reply.results[0]);
});

test("exchange validation enforces advertised actions, swaps, and renderers", () => {
	const call = protocol.buildCall({
		componentClassId: "Counter",
		handlerName: "increment",
		args: {},
	});
	const actionLimited = protocol.buildCallEnvelope("request-action", [call], {
		actions: ["data"],
		swaps: ["replace"],
	});
	const redirectReply = protocol.buildResultEnvelope("request-action", [
		protocol.buildOkResult([{ action: "redirect", url: "/next" }]),
	]);
	assert.deepEqual(protocol.validateExchange(actionLimited, redirectReply), {
		path: "/results/0/actions/0/action",
		category: "capability",
		message: "The result uses an action the caller did not advertise.",
	});
	const actionPreflight = protocol.preflightResultEnvelope(
		redirectReply,
		actionLimited,
	);
	assert.equal(actionPreflight.ok, false);
	assert.equal(actionPreflight.reason, "result 0");

	const swapLimited = protocol.buildCallEnvelope("request-swap", [call], {
		actions: ["render"],
		swaps: ["replace"],
	});
	const morphReply = protocol.buildResultEnvelope("request-swap", [
		protocol.buildOkResult([
			{ action: "render", target: "#out", swap: "morph", html: "<p>ok</p>" },
		]),
	]);
	assert.deepEqual(protocol.validateExchange(swapLimited, morphReply), {
		path: "/results/0/actions/0/swap",
		category: "capability",
		message: "The result uses a swap the caller did not advertise.",
	});

	const prepared = {
		action: "render",
		target: "render:counter_1",
		swap: "none",
		renderer: "vue-prepared/1",
		prepared: { revision: "r1" },
	};
	assert.equal(protocol.validateAction(prepared), null);
	assert.deepEqual(
		protocol.validateAction({
			...prepared,
			prepared: { missingSchemaField: true, nested: Number.NaN },
		}),
		{
			path: "/prepared/nested",
			category: "strict_json",
			message: "The value contains a non-finite number.",
		},
	);
	for (const invalid of [
		{ ...prepared, html: "<p>mixed</p>" },
		{ ...prepared, prepared: [] },
		{ ...prepared, renderer: "unknown/1" },
	])
		assert.ok(protocol.validateAction(invalid));
	const htmlOnly = protocol.buildCallEnvelope("request-renderer", [call], {
		actions: ["render"],
		swaps: ["none"],
		renderers: ["html-fragment/1"],
	});
	const preparedReply = protocol.buildResultEnvelope("request-renderer", [
		protocol.buildOkResult([prepared]),
	]);
	assert.deepEqual(protocol.validateExchange(htmlOnly, preparedReply), {
		path: "/results/0/actions/0/renderer",
		category: "capability",
		message: "The result uses a renderer the caller did not advertise.",
	});
});

test("edge errors fan out only after their special shape validates", () => {
	const calls = protocol.buildCallEnvelope("request-1", [
		protocol.buildCall({
			componentClassId: "Counter",
			handlerName: "increment",
			args: {},
		}),
		protocol.buildCall({
			componentClassId: "Counter",
			handlerName: "decrement",
			args: {},
		}),
	]);
	const edge = {
		protocol: protocol.PROTOCOL,
		requestId: null,
		results: [
			{
				ok: false,
				error: {
					status: 413,
					code: "payload_too_large",
					message: "Too large",
				},
			},
		],
	};
	const checked = protocol.preflightResultEnvelope(edge, calls);
	assert.equal(checked.ok, true);
	assert.equal(checked.results.length, 2);
	assert.strictEqual(checked.results[0], checked.results[1]);

	const invalid = structuredClone(edge);
	invalid.results[0].sendSequence = 0;
	const rejected = protocol.preflightResultEnvelope(invalid, calls);
	assert.equal(rejected.ok, false);
	assert.equal(rejected.reason, "edge");
});

test("case parser rejects non-finite operation values", () => {
	const payload = (value) => ({
		format: CASE_FORMAT,
		cases: [
			{
				constraint: "/type",
				expected: { category: "type", path: "" },
				id: "non-finite",
				implementations: ["javascript"],
				operations: [{ op: "replace", path: "", value }],
				schema: "value.schema.json",
				seed: "valid.json",
			},
		],
	});
	for (const value of [
		Number.NaN,
		Number.POSITIVE_INFINITY,
		Number.NEGATIVE_INFINITY,
	]) {
		assert.throws(
			() => parseCaseFile(payload(value)),
			/non-finite number is not strict JSON/u,
		);
	}
});
