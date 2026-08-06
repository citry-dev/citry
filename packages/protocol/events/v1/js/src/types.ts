export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | JsonObject;

export interface JsonObject {
	[key: string]: JsonValue;
}

export type EventSwap =
	| "morph"
	| "replace"
	| "inner"
	| "append"
	| "prepend"
	| "remove"
	| "none";

export type EventActionKind =
	| "render"
	| "data"
	| "state"
	| "event"
	| "redirect"
	| "url";

export interface EventsCapabilities {
	swaps?: EventSwap[];
	actions?: EventActionKind[];
}

export interface EventCall {
	componentClassId: string;
	handlerName: string;
	callerRenderId?: string;
	args: JsonObject;
	stateToken?: string;
	stateUpdates?: JsonObject;
	sendSequence?: number;
}

export interface EventsCallEnvelope {
	protocol: "citry-events/1";
	requestId: string;
	capabilities?: EventsCapabilities;
	calls: EventCall[];
}

export type EventErrorCode =
	| "invalid_args"
	| "invalid_state"
	| "stale_state"
	| "unknown_event"
	| "unknown_component"
	| "forbidden"
	| "not_found"
	| "conflict"
	| "error"
	| "csrf_failed"
	| "payload_too_large"
	| "protocol_mismatch"
	| "handler_error";

export interface EventProtocolError {
	status: number;
	code: EventErrorCode;
	message: string;
	fieldErrors?: Record<string, string>;
}

export interface ActionTiming {
	delay?: number;
	wait?: false;
}

export interface RenderAction extends ActionTiming {
	action: "render";
	target: string;
	swap: EventSwap;
	html: string;
}

export interface DataAction {
	action: "data";
	value: JsonValue;
	delay?: number;
}

export interface StateAction extends ActionTiming {
	action: "state";
	targetRenderId: string;
	stateToken: string;
}

export interface DispatchEventAction extends ActionTiming {
	action: "event";
	eventName: string;
	detail?: JsonValue;
	target?: string;
}

export interface RedirectAction extends ActionTiming {
	action: "redirect";
	url: string;
}

export interface UpdateUrlAction extends ActionTiming {
	action: "url";
	url: string;
	mode: "push" | "replace";
}

export type EventAction =
	| RenderAction
	| DataAction
	| StateAction
	| DispatchEventAction
	| RedirectAction
	| UpdateUrlAction;

export interface EventSuccessResult {
	ok: true;
	sendSequence?: number;
	actions: EventAction[];
}

export interface EventErrorResult {
	ok: false;
	sendSequence?: number;
	error: EventProtocolError;
}

export type EventResult = EventSuccessResult | EventErrorResult;

export interface EventsAnsweredResultEnvelope {
	protocol: "citry-events/1";
	requestId: string;
	results: EventResult[];
}

export interface EventEarlyErrorResult {
	ok: false;
	error: EventEarlyProtocolError;
}

export type EventEarlyProtocolError =
	| { status: 400; code: "protocol_mismatch"; message: string }
	| { status: 413; code: "payload_too_large"; message: string };

export interface EventsEarlyErrorEnvelope {
	protocol: "citry-events/1";
	requestId: null;
	results: [EventEarlyErrorResult];
}

export type EventsResultEnvelope =
	| EventsAnsweredResultEnvelope
	| EventsEarlyErrorEnvelope;

export interface EventHandlerOptions {
	httpMethod: string;
	usesState?: true;
	debounceMilliseconds?: number;
	throttleMilliseconds?: number;
	latestCallWins?: true;
	allowBatching?: false;
}

export interface EventComponentClass {
	componentClassId: string;
	eventHandlers: Record<string, EventHandlerOptions>;
	writableStateFields?: string[];
}

export interface EventComponentInstance {
	renderId: string;
	componentClassId: string;
	stateToken: string | null;
	publicState: JsonObject;
}

export interface EventsManifest {
	protocol: "citry-events/1";
	clientGraphRevision: string | null;
	componentClasses: EventComponentClass[];
	componentInstances: EventComponentInstance[];
}
