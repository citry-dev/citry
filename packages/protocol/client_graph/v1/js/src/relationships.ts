import { pointer, type ValidationIssue } from "./issue";
import type {
	ClientBindingPayload,
	ClientGraphManifest,
	ComponentTagClientBinding,
} from "./types";

const cycle = <T>(nodes: ReadonlyMap<T, T | null>): boolean => {
	const visiting = new Set<T>();
	const visited = new Set<T>();
	for (const start of nodes.keys()) {
		let current: T | null | undefined = start;
		const path: T[] = [];
		while (
			current !== null &&
			current !== undefined &&
			nodes.has(current) &&
			!visited.has(current)
		) {
			if (visiting.has(current)) return true;
			visiting.add(current);
			path.push(current);
			const next = nodes.get(current);
			if (next === undefined) break;
			current = next;
		}
		for (const item of path) {
			visiting.delete(item);
			visited.add(item);
		}
	}
	return false;
};

const executionCycle = (edges: ReadonlyMap<string, string[]>): boolean => {
	const visiting = new Set<string>();
	const visited = new Set<string>();
	const stack: [string, boolean][] = Array.from(edges.keys())
		.reverse()
		.map((node) => [node, false]);
	while (stack.length) {
		const [node, leaving] = stack.pop() as [string, boolean];
		if (leaving) {
			visiting.delete(node);
			visited.add(node);
			continue;
		}
		if (visiting.has(node)) return true;
		if (visited.has(node)) continue;
		visiting.add(node);
		stack.push([node, true]);
		for (const child of [...(edges.get(node) ?? [])].reverse())
			stack.push([child, false]);
	}
	return false;
};

const semantic = (path: string, message: string): ValidationIssue => ({
	path,
	category: "semantic",
	message,
});

const bindingKeyIssue = (
	payload: ClientBindingPayload,
	bindingKey: string,
	path: string,
): ValidationIssue | null => {
	if (payload.type === "props" && bindingKey !== "$c-props")
		return semantic(path, "A props client binding must use the $c-props key.");
	if (
		payload.type === "alpine-handler" &&
		!(
			(bindingKey.startsWith("@") && !bindingKey.startsWith("@c-")) ||
			bindingKey.startsWith("x-on:")
		)
	)
		return semantic(
			path,
			"An Alpine-handler client binding has a non-Alpine key.",
		);
	if (payload.type === "citry-dom-event") {
		if (
			!bindingKey.startsWith("@c-") ||
			bindingKey.slice(3).split(".")[0] === "poll"
		)
			return semantic(
				path,
				"A Citry DOM-event client binding has a non-event key.",
			);
		if (bindingKey.slice(3).split(".")[0] !== payload.event)
			return semantic(
				path,
				"A Citry DOM-event client binding disagrees with its key.",
			);
	}
	if (payload.type === "citry-poll" && !bindingKey.startsWith("@c-poll."))
		return semantic(
			path,
			"A Citry poll client binding must use an @c-poll key.",
		);
	return null;
};

/** Return the first cross-record problem in a structurally valid manifest. */
export const validateRelationships = (
	manifest: ClientGraphManifest,
	path = "",
): ValidationIssue | null => {
	const development = manifest.mode === "development";
	const allRenderIds = new Set<string>();

	for (
		let graphIndex = 0;
		graphIndex < manifest.graphs.length;
		graphIndex += 1
	) {
		const graph = manifest.graphs[graphIndex];
		const graphPath = pointer(pointer(path, "graphs"), graphIndex);
		if (graph.graphId !== graphIndex)
			return semantic(
				pointer(graphPath, "graphId"),
				`graphs[${graphIndex}].graphId is not dense and ordered.`,
			);

		const idFields = [
			["componentInstances", "instanceId"],
			["sourceLocations", "locationId"],
			["nestedComponents", "invocationId"],
			["fills", "fillId"],
			["slotRegions", "regionId"],
		] as const;
		const ids = new Map<string, Set<number>>();
		for (const [collection, idField] of idFields) {
			const records = graph[collection] as readonly unknown[];
			const values = records.map(
				(record) => (record as Record<string, number>)[idField],
			);
			const selected = new Set(values);
			ids.set(collection, selected);
			if (values.length !== selected.size)
				return semantic(
					pointer(graphPath, collection),
					`graphs[${graphIndex}].${collection} has duplicate ids.`,
				);
		}

		if (!development) {
			if (graph.sourceLocations.length)
				return semantic(
					pointer(graphPath, "sourceLocations"),
					`graphs[${graphIndex}] production manifest has sourceLocations.`,
				);
			for (let index = 0; index < graph.nestedComponents.length; index += 1) {
				const invocation = graph.nestedComponents[index];
				const invocationPath = pointer(
					pointer(graphPath, "nestedComponents"),
					index,
				);
				if (invocation.locationId !== null)
					return semantic(
						pointer(invocationPath, "locationId"),
						`graphs[${graphIndex}] production invocation has a location reference.`,
					);
				for (
					let bindingIndex = 0;
					bindingIndex < invocation.clientBindings.length;
					bindingIndex += 1
				) {
					if (invocation.clientBindings[bindingIndex].locationId !== null) {
						const bindingPath = pointer(
							pointer(invocationPath, "clientBindings"),
							bindingIndex,
						);
						return semantic(
							pointer(bindingPath, "locationId"),
							`graphs[${graphIndex}] production client binding has a location reference.`,
						);
					}
				}
			}
			for (let index = 0; index < graph.fills.length; index += 1) {
				const fill = graph.fills[index];
				for (const field of ["locationId", "fallbackLocationId"] as const)
					if (fill[field] !== null)
						return semantic(
							pointer(pointer(pointer(graphPath, "fills"), index), field),
							`graphs[${graphIndex}] production fill has a location reference.`,
						);
			}
			for (let index = 0; index < graph.slotRegions.length; index += 1) {
				const region = graph.slotRegions[index];
				for (const field of ["slotLocationId", "sourceLocationId"] as const)
					if (region[field] !== null)
						return semantic(
							pointer(pointer(pointer(graphPath, "slotRegions"), index), field),
							`graphs[${graphIndex}] production slot region has a location reference.`,
						);
			}
		}

		const classIds = new Set<string>();
		for (let index = 0; index < graph.componentClasses.length; index += 1) {
			const classId = graph.componentClasses[index].classId;
			if (classIds.has(classId))
				return semantic(
					pointer(
						pointer(pointer(graphPath, "componentClasses"), index),
						"classId",
					),
					`graphs[${graphIndex}] has duplicate class ids.`,
				);
			classIds.add(classId);
		}

		const renderIds = new Set<string>();
		const classesByRender = new Map<string, string>();
		const instancesById = new Map<number, string>();
		const instancesByInvocation = new Map<
			number,
			[string, string | null, number | null][]
		>();
		const instanceRecords: [string, string | null, number | null][] = [];
		const instanceParents = new Map<string, string | null>();
		for (let index = 0; index < graph.componentInstances.length; index += 1) {
			const instance = graph.componentInstances[index];
			const instancePath = pointer(
				pointer(graphPath, "componentInstances"),
				index,
			);
			if (!classIds.has(instance.classId))
				return semantic(
					pointer(instancePath, "classId"),
					`graphs[${graphIndex}] component instance classId is unknown.`,
				);
			if (renderIds.has(instance.renderId))
				return semantic(
					pointer(instancePath, "renderId"),
					`graphs[${graphIndex}] has duplicate render ids.`,
				);
			if (allRenderIds.has(instance.renderId))
				return semantic(
					pointer(instancePath, "renderId"),
					`render id '${instance.renderId}' appears in more than one graph.`,
				);
			renderIds.add(instance.renderId);
			allRenderIds.add(instance.renderId);
			classesByRender.set(instance.renderId, instance.classId);
			instancesById.set(instance.instanceId, instance.renderId);
			instanceParents.set(instance.renderId, instance.parentRenderId);
			const record: [string, string | null, number | null] = [
				instance.renderId,
				instance.parentRenderId,
				instance.invocationId,
			];
			instanceRecords.push(record);
			if (instance.invocationId !== null) {
				const targets = instancesByInvocation.get(instance.invocationId) ?? [];
				targets.push(record);
				instancesByInvocation.set(instance.invocationId, targets);
			}
		}
		for (let index = 0; index < graph.componentInstances.length; index += 1) {
			const parent = graph.componentInstances[index].parentRenderId;
			if (parent !== null && !renderIds.has(parent))
				return semantic(
					pointer(
						pointer(pointer(graphPath, "componentInstances"), index),
						"parentRenderId",
					),
					`graphs[${graphIndex}] component instance parentRenderId is unknown.`,
				);
		}

		const locationOwners = new Map<number, [string, string]>();
		const locationKinds = new Map<number, string>();
		if (development) {
			for (let index = 0; index < graph.sourceLocations.length; index += 1) {
				const location = graph.sourceLocations[index];
				const locationPath = pointer(
					pointer(graphPath, "sourceLocations"),
					index,
				);
				if (
					!(ids.get("componentInstances") as Set<number>).has(
						location.carrierInstanceId,
					)
				)
					return semantic(
						pointer(locationPath, "carrierInstanceId"),
						`graphs[${graphIndex}] location has an unknown carrier.`,
					);
				if (location.sourceOffset.start > location.sourceOffset.end)
					return semantic(
						pointer(locationPath, "sourceOffset"),
						`graphs[${graphIndex}] location has a reversed byte range.`,
					);
				if (
					!renderIds.has(location.ownerRenderId) ||
					classesByRender.get(location.ownerRenderId) !== location.ownerClassId
				)
					return semantic(
						pointer(locationPath, "ownerRenderId"),
						`graphs[${graphIndex}] location owner is unknown or mismatched.`,
					);
				if (
					instancesById.get(location.carrierInstanceId) !==
					location.ownerRenderId
				)
					return semantic(
						pointer(locationPath, "carrierInstanceId"),
						`graphs[${graphIndex}] location carrier is mismatched.`,
					);
				locationOwners.set(location.locationId, [
					location.ownerRenderId,
					location.ownerClassId,
				]);
				locationKinds.set(location.locationId, location.kind);
			}
		}

		const invocationEdges = new Map<number, [string, string]>();
		for (let index = 0; index < graph.nestedComponents.length; index += 1) {
			const invocation = graph.nestedComponents[index];
			const invocationPath = pointer(
				pointer(graphPath, "nestedComponents"),
				index,
			);
			if (
				!renderIds.has(invocation.sourceRenderId) ||
				classesByRender.get(invocation.sourceRenderId) !==
					invocation.sourceClassId
			)
				return semantic(
					pointer(invocationPath, "sourceRenderId"),
					`graphs[${graphIndex}] invocation source is unknown or mismatched.`,
				);
			if (
				!renderIds.has(invocation.targetRenderId) ||
				classesByRender.get(invocation.targetRenderId) !==
					invocation.targetClassId
			)
				return semantic(
					pointer(invocationPath, "targetRenderId"),
					`graphs[${graphIndex}] invocation target is unknown or mismatched.`,
				);
			if (development) {
				if (
					!(ids.get("sourceLocations") as Set<number>).has(
						invocation.locationId as number,
					)
				)
					return semantic(
						pointer(invocationPath, "locationId"),
						`graphs[${graphIndex}] invocation has an unknown location.`,
					);
				const owner = locationOwners.get(invocation.locationId as number);
				if (
					!owner ||
					owner[0] !== invocation.sourceRenderId ||
					owner[1] !== invocation.sourceClassId
				)
					return semantic(
						pointer(invocationPath, "locationId"),
						`graphs[${graphIndex}] invocation location owner is mismatched.`,
					);
				if (
					locationKinds.get(invocation.locationId as number) !==
					"component-call"
				)
					return semantic(
						pointer(invocationPath, "locationId"),
						`graphs[${graphIndex}] invocation location kind is mismatched.`,
					);
			}
			if (
				invocation.parentRegionId !== null &&
				!(ids.get("slotRegions") as Set<number>).has(invocation.parentRegionId)
			)
				return semantic(
					pointer(invocationPath, "parentRegionId"),
					`graphs[${graphIndex}] nested component parentRegionId references an unknown slot region.`,
				);
			invocationEdges.set(invocation.invocationId, [
				invocation.sourceRenderId,
				invocation.targetRenderId,
			]);
			for (
				let bindingIndex = 0;
				bindingIndex < invocation.clientBindings.length;
				bindingIndex += 1
			) {
				const binding = invocation.clientBindings[
					bindingIndex
				] as ComponentTagClientBinding;
				const bindingPath = pointer(
					pointer(invocationPath, "clientBindings"),
					bindingIndex,
				);
				if (development) {
					if (
						!(ids.get("sourceLocations") as Set<number>).has(
							binding.locationId as number,
						)
					)
						return semantic(
							pointer(bindingPath, "locationId"),
							`graphs[${graphIndex}] client binding has an unknown location.`,
						);
					const owner = locationOwners.get(binding.locationId as number);
					if (
						!owner ||
						owner[0] !== invocation.sourceRenderId ||
						owner[1] !== invocation.sourceClassId
					)
						return semantic(
							pointer(bindingPath, "locationId"),
							`graphs[${graphIndex}] client-binding location owner is mismatched.`,
						);
					if (
						locationKinds.get(binding.locationId as number) !==
						"component-tag-client-binding"
					)
						return semantic(
							pointer(bindingPath, "locationId"),
							`graphs[${graphIndex}] client-binding location kind is mismatched.`,
						);
				}
				if (
					(binding.payload.type === "citry-dom-event" ||
						binding.payload.type === "citry-poll") &&
					binding.payload.classId !== invocation.sourceClassId
				)
					return semantic(
						pointer(pointer(bindingPath, "payload"), "classId"),
						`graphs[${graphIndex}] Citry client-binding class is not its source parent.`,
					);
				const keyIssue = bindingKeyIssue(
					binding.payload,
					binding.key,
					pointer(bindingPath, "key"),
				);
				if (keyIssue) return keyIssue;
			}
		}

		for (let index = 0; index < graph.componentInstances.length; index += 1) {
			const invocationId = graph.componentInstances[index].invocationId;
			if (
				invocationId !== null &&
				!(ids.get("nestedComponents") as Set<number>).has(invocationId)
			)
				return semantic(
					pointer(
						pointer(pointer(graphPath, "componentInstances"), index),
						"invocationId",
					),
					`graphs[${graphIndex}] instance has an unknown invocation.`,
				);
		}
		for (let index = 0; index < instanceRecords.length; index += 1) {
			const [render, parent, invocationId] = instanceRecords[index];
			const instancePath = pointer(
				pointer(graphPath, "componentInstances"),
				index,
			);
			if (invocationId === null) {
				if (parent !== null)
					return semantic(
						pointer(instancePath, "parentRenderId"),
						`graphs[${graphIndex}] uninvoked instance has a parent.`,
					);
				continue;
			}
			const edge = invocationEdges.get(invocationId);
			if (!edge || edge[0] !== parent || edge[1] !== render)
				return semantic(
					pointer(instancePath, "invocationId"),
					`graphs[${graphIndex}] instance endpoints do not match their invocation.`,
				);
		}
		for (let index = 0; index < graph.nestedComponents.length; index += 1) {
			const id = graph.nestedComponents[index].invocationId;
			if ((instancesByInvocation.get(id) ?? []).length !== 1)
				return semantic(
					pointer(
						pointer(pointer(graphPath, "nestedComponents"), index),
						"invocationId",
					),
					`graphs[${graphIndex}] invocation does not bind exactly one target instance.`,
				);
		}

		const fillRecords = new Map<
			number,
			[string | null, string | null, number | null]
		>();
		for (let index = 0; index < graph.fills.length; index += 1) {
			const fill = graph.fills[index];
			const fillPath = pointer(pointer(graphPath, "fills"), index);
			if (
				(fill.ownerRenderId === null) !== (fill.ownerClassId === null) ||
				(fill.ownerRenderId !== null &&
					classesByRender.get(fill.ownerRenderId) !== fill.ownerClassId)
			)
				return semantic(
					pointer(fillPath, "ownerRenderId"),
					`graphs[${graphIndex}] fill owner and class are mismatched.`,
				);
			if (
				(fill.receiverRenderId === null) !== (fill.receiverClassId === null) ||
				(fill.receiverRenderId !== null &&
					classesByRender.get(fill.receiverRenderId) !== fill.receiverClassId)
			)
				return semantic(
					pointer(fillPath, "receiverRenderId"),
					`graphs[${graphIndex}] fill receiver and class are mismatched.`,
				);
			if (
				fill.sourceInvocationId !== null &&
				!(ids.get("nestedComponents") as Set<number>).has(
					fill.sourceInvocationId,
				)
			)
				return semantic(
					pointer(fillPath, "sourceInvocationId"),
					`graphs[${graphIndex}] fill has an unknown sourceInvocation.`,
				);
			const sourceKind =
				fill.locationId === null
					? undefined
					: locationKinds.get(fill.locationId);
			const fallbackKind =
				fill.fallbackLocationId === null
					? undefined
					: locationKinds.get(fill.fallbackLocationId);
			if (fill.policy === "template") {
				if (
					fill.ownerRenderId === null ||
					fill.receiverRenderId === null ||
					!new Set(["implicit", "named", "fallback"]).has(fill.kind)
				)
					return semantic(
						pointer(fillPath, "policy"),
						`graphs[${graphIndex}] template fill ownership is inconsistent.`,
					);
			} else if (fill.policy === "python-detached") {
				if (
					fill.kind !== "python" ||
					fill.ownerRenderId !== null ||
					fill.receiverRenderId === null ||
					fill.sourceInvocationId !== null ||
					fill.fallbackLocationId !== null
				)
					return semantic(
						pointer(fillPath, "policy"),
						`graphs[${graphIndex}] detached Python fill ownership is inconsistent.`,
					);
			} else if (
				fill.kind !== "typed-default" ||
				fill.ownerRenderId !== null ||
				fill.receiverRenderId === null ||
				fill.sourceInvocationId !== null ||
				fill.fallbackLocationId !== null
			)
				return semantic(
					pointer(fillPath, "policy"),
					`graphs[${graphIndex}] detached typed-default fill ownership is inconsistent.`,
				);
			if (development) {
				for (const [field, location] of [
					["locationId", fill.locationId],
					["fallbackLocationId", fill.fallbackLocationId],
				] as const)
					if (
						location !== null &&
						!(ids.get("sourceLocations") as Set<number>).has(location)
					)
						return semantic(
							pointer(fillPath, field),
							`graphs[${graphIndex}] fill has an unknown ${field}.`,
						);
				const sourceOwner =
					fill.locationId === null
						? undefined
						: locationOwners.get(fill.locationId);
				const fallbackOwner =
					fill.fallbackLocationId === null
						? undefined
						: locationOwners.get(fill.fallbackLocationId);
				if ((fill.ownerRenderId === null) !== (sourceOwner === undefined))
					return semantic(
						pointer(fillPath, "locationId"),
						`graphs[${graphIndex}] fill owner and source location are inconsistent.`,
					);
				if (
					sourceOwner &&
					(sourceOwner[0] !== fill.ownerRenderId ||
						sourceOwner[1] !== fill.ownerClassId)
				)
					return semantic(
						pointer(fillPath, "locationId"),
						`graphs[${graphIndex}] fill source location owner is mismatched.`,
					);
				if (
					fallbackOwner &&
					(fallbackOwner[0] !== fill.receiverRenderId ||
						fallbackOwner[1] !== fill.receiverClassId)
				)
					return semantic(
						pointer(fillPath, "fallbackLocationId"),
						`graphs[${graphIndex}] fill fallback location receiver is mismatched.`,
					);
			}
			if (fill.policy === "template") {
				if (development) {
					const expectedKind = {
						implicit: "implicit-fill",
						named: "named-fill",
						fallback: "fallback-fill",
					}[fill.kind as "implicit" | "named" | "fallback"];
					if (sourceKind !== expectedKind)
						return semantic(
							pointer(fillPath, "locationId"),
							`graphs[${graphIndex}] template fill source location kind is mismatched.`,
						);
					if (
						fill.kind === "fallback" &&
						(fill.fallbackLocationId === null || fallbackKind !== "slot-outlet")
					)
						return semantic(
							pointer(fillPath, "fallbackLocationId"),
							`graphs[${graphIndex}] fallback location kind is mismatched.`,
						);
					if (fill.kind !== "fallback" && fill.fallbackLocationId !== null)
						return semantic(
							pointer(fillPath, "fallbackLocationId"),
							`graphs[${graphIndex}] supplied fill carrier is inconsistent.`,
						);
				}
				if (fill.kind === "fallback") {
					if (fill.sourceInvocationId !== null)
						return semantic(
							pointer(fillPath, "sourceInvocationId"),
							`graphs[${graphIndex}] fallback fill carrier is inconsistent.`,
						);
				} else if (fill.sourceInvocationId === null)
					return semantic(
						pointer(fillPath, "sourceInvocationId"),
						`graphs[${graphIndex}] supplied fill carrier is inconsistent.`,
					);
				else if (
					invocationEdges.get(fill.sourceInvocationId)?.[0] !==
					fill.ownerRenderId
				)
					return semantic(
						pointer(fillPath, "sourceInvocationId"),
						`graphs[${graphIndex}] supplied fill source invocation owner is mismatched.`,
					);
			}
			fillRecords.set(fill.fillId, [
				fill.ownerRenderId,
				fill.receiverRenderId,
				fill.locationId,
			]);
		}

		const slotRegionRecords = new Map<
			number,
			[string | null, string | null, number | null, string | null]
		>();
		for (let index = 0; index < graph.slotRegions.length; index += 1) {
			const region = graph.slotRegions[index];
			const regionPath = pointer(pointer(graphPath, "slotRegions"), index);
			if (!(ids.get("fills") as Set<number>).has(region.fillId))
				return semantic(
					pointer(regionPath, "fillId"),
					`graphs[${graphIndex}] slot region has an unknown fill.`,
				);
			if (
				region.parentRegionId !== null &&
				!(ids.get("slotRegions") as Set<number>).has(region.parentRegionId)
			)
				return semantic(
					pointer(regionPath, "parentRegionId"),
					`graphs[${graphIndex}] slot region has an unknown parent.`,
				);
			for (const [field, renderId] of Object.entries({
				receiverRenderId: region.receiverRenderId,
				ownerRenderId: region.ownerRenderId,
				transitionFromRenderId: region.transitionFromRenderId,
				resultOwnerRenderId: region.resultOwnerRenderId,
			}))
				if (renderId !== null && !renderIds.has(renderId))
					return semantic(
						pointer(regionPath, field),
						`graphs[${graphIndex}] slot region.${field} is unknown.`,
					);
			if (development) {
				for (const [field, location] of [
					["slotLocationId", region.slotLocationId],
					["sourceLocationId", region.sourceLocationId],
				] as const)
					if (
						location !== null &&
						!(ids.get("sourceLocations") as Set<number>).has(location)
					)
						return semantic(
							pointer(regionPath, field),
							`graphs[${graphIndex}] slot region has an unknown ${field}.`,
						);
				const slotOwner =
					region.slotLocationId === null
						? undefined
						: locationOwners.get(region.slotLocationId);
				if (slotOwner && slotOwner[0] !== region.receiverRenderId)
					return semantic(
						pointer(regionPath, "slotLocationId"),
						`graphs[${graphIndex}] slot region slot location receiver is mismatched.`,
					);
				if (
					region.slotLocationId !== null &&
					locationKinds.get(region.slotLocationId) !== "slot-outlet"
				)
					return semantic(
						pointer(regionPath, "slotLocationId"),
						`graphs[${graphIndex}] slot region slot location kind is mismatched.`,
					);
			}
			const fill = fillRecords.get(region.fillId);
			if (
				!fill ||
				fill[0] !== region.ownerRenderId ||
				fill[1] !== region.receiverRenderId ||
				fill[2] !== region.sourceLocationId
			)
				return semantic(
					pointer(regionPath, "fillId"),
					`graphs[${graphIndex}] slot region ownership does not match its fill.`,
				);
			slotRegionRecords.set(region.regionId, [
				region.ownerRenderId,
				region.receiverRenderId,
				region.parentRegionId,
				region.transitionFromRenderId,
			]);
		}
		if (
			cycle(
				new Map(
					Array.from(slotRegionRecords, ([id, record]) => [id, record[2]]),
				),
			)
		)
			return semantic(
				pointer(graphPath, "slotRegions"),
				`graphs[${graphIndex}] slot region ancestry contains a cycle.`,
			);
		for (let index = 0; index < graph.slotRegions.length; index += 1) {
			const region = graph.slotRegions[index];
			const expected =
				region.parentRegionId === null
					? region.receiverRenderId
					: (slotRegionRecords.get(region.parentRegionId)?.[0] ?? null);
			if (region.transitionFromRenderId !== expected)
				return semantic(
					pointer(
						pointer(pointer(graphPath, "slotRegions"), index),
						"transitionFromRenderId",
					),
					`graphs[${graphIndex}] slot region scope transition does not match its ancestry.`,
				);
		}

		const executionEdges = new Map<string, string[]>();
		for (
			let index = 0;
			index < graph.componentExecutionOrderConstraints.length;
			index += 1
		) {
			const constraint = graph.componentExecutionOrderConstraints[index];
			const constraintPath = pointer(
				pointer(graphPath, "componentExecutionOrderConstraints"),
				index,
			);
			const edge = invocationEdges.get(constraint.invocationId);
			if (
				!edge ||
				edge[0] !== constraint.parentRenderId ||
				edge[1] !== constraint.childRenderId
			)
				return semantic(
					pointer(constraintPath, "invocationId"),
					`graphs[${graphIndex}] component execution order constraint does not match its invocation.`,
				);
			const children = executionEdges.get(constraint.parentRenderId) ?? [];
			children.push(constraint.childRenderId);
			executionEdges.set(constraint.parentRenderId, children);
		}
		if (executionCycle(executionEdges))
			return semantic(
				pointer(graphPath, "componentExecutionOrderConstraints"),
				`graphs[${graphIndex}] component execution order contains a cycle.`,
			);
		if (cycle(instanceParents))
			return semantic(
				pointer(graphPath, "componentInstances"),
				`graphs[${graphIndex}] logical instance ancestry contains a cycle.`,
			);
	}
	return null;
};
