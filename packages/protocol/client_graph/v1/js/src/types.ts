export type ClientGraphMode = "production" | "development";

export interface GraphDelimiters {
	format: "citry:g1";
}

export interface ComponentClassRecord {
	classId: string;
	className: string;
}

export interface ComponentInstanceRecord {
	instanceId: number;
	renderId: string;
	classId: string;
	invocationId: number | null;
	parentRenderId: string | null;
	transparent: boolean;
}

export interface SourceOffset {
	start: number;
	end: number;
}

export interface SourcePosition {
	line: number;
	column: number;
}

export type SourceLocationKind =
	| "component-call"
	| "component-tag-client-binding"
	| "implicit-fill"
	| "named-fill"
	| "fallback-fill"
	| "slot-outlet";

export interface SourceLocation {
	locationId: number;
	kind: SourceLocationKind;
	ownerRenderId: string;
	ownerClassId: string;
	carrierInstanceId: number;
	origin: string | null;
	sourceOffset: SourceOffset;
	sourcePos: SourcePosition;
	mappingKey: string | null;
	mappingIndex: number | null;
}

export interface ExpressionPayload {
	type: "props" | "alpine-handler";
	expression: string;
}

export interface DomEventPayload {
	type: "citry-dom-event";
	classId: string;
	event: string;
	handler: string;
	args: string | null;
	prevent: boolean;
	stop: boolean;
	self: boolean;
	once: boolean;
	key: string | null;
	debounce: number | null;
	throttle: number | null;
}

export interface PollPayload {
	type: "citry-poll";
	classId: string;
	handler: string;
	args: string | null;
	interval: number;
}

export type ClientBindingPayload =
	| ExpressionPayload
	| DomEventPayload
	| PollPayload;

export interface ComponentTagClientBinding {
	key: string;
	source: "direct" | "server-dynamic" | "spread";
	locationId: number | null;
	payload: ClientBindingPayload;
}

export interface NestedComponent {
	invocationId: number;
	sourceRenderId: string;
	sourceClassId: string;
	locationId: number | null;
	tagName: string;
	targetClassId: string;
	morphKey: string | null;
	morphMode: "ignore" | null;
	targetRenderId: string;
	parentRegionId: number | null;
	clientBindings: ComponentTagClientBinding[];
}

export interface ComponentExecutionOrderConstraint {
	invocationId: number;
	parentRenderId: string;
	childRenderId: string;
}

export interface SlotFill {
	fillId: number;
	kind: "implicit" | "named" | "fallback" | "python" | "typed-default";
	slotName: string;
	policy: "template" | "python-detached" | "typed-default-detached";
	ownerRenderId: string | null;
	ownerClassId: string | null;
	locationId: number | null;
	sourceInvocationId: number | null;
	receiverRenderId: string | null;
	receiverClassId: string | null;
	fallbackLocationId: number | null;
}

export interface SlotRegion {
	regionId: number;
	fillId: number;
	receiverRenderId: string | null;
	slotLocationId: number | null;
	ownerRenderId: string | null;
	sourceLocationId: number | null;
	parentRegionId: number | null;
	transitionFromRenderId: string | null;
	resultOwnerRenderId: string | null;
}

export interface ClientGraph {
	graphId: number;
	componentClasses: ComponentClassRecord[];
	componentInstances: ComponentInstanceRecord[];
	sourceLocations: SourceLocation[];
	nestedComponents: NestedComponent[];
	componentExecutionOrderConstraints: ComponentExecutionOrderConstraint[];
	fills: SlotFill[];
	slotRegions: SlotRegion[];
}

export interface ClientGraphManifest {
	protocol: "citry-client-graph/1";
	revision: string;
	mode: ClientGraphMode;
	graphs: ClientGraph[];
	delimiters: GraphDelimiters;
}
