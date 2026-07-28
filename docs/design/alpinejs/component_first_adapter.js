/*
 * Research-only component-first client prototypes.
 *
 * This file does not implement the Citry product runtime. It gives two
 * competing approaches the same versioned manifest and physical DOM:
 *
 * 1. GraphFirstAlpineRuntime makes Citry's instance, lexical-location,
 *    physical-region, and binding records authoritative, then projects them
 *    into pinned Alpine plus the earlier source-link, RootGroup, and rootless
 *    spike mechanisms.
 * 2. CitryDirectiveRuntime owns `$c-*` binding discovery and expression
 *    evaluation while retaining Alpine for genuine `x-*` islands and its
 *    reactive engine.
 */
(() => {
	const MANIFEST_SELECTOR = 'script[type="application/json"][data-component-first]';
	const compiledExpressions = new Map();

	function invariant(condition, message) {
		if (!condition) throw new Error(`Component-first spike: ${message}`);
	}

	function uniqueMap(items, label) {
		const result = new Map();
		for (const item of items || []) {
			invariant(item && typeof item.id === "string" && item.id, `${label} needs a string id`);
			invariant(!result.has(item.id), `${label} id ${item.id} is duplicated`);
			result.set(item.id, item);
		}
		return result;
	}

	function assertAcyclic(locations) {
		const visiting = new Set();
		const visited = new Set();
		function visit(id) {
			if (id == null || visited.has(id)) return;
			invariant(!visiting.has(id), `lexical location cycle reaches ${id}`);
			const location = locations.get(id);
			invariant(location, `lexical location ${id} does not exist`);
			visiting.add(id);
			visit(location.lexicalParentLocationId || null);
			visiting.delete(id);
			visited.add(id);
		}
		for (const id of locations.keys()) visit(id);
	}

	function assertInstanceParentAcyclic(instances, field) {
		const visiting = new Set();
		const visited = new Set();
		function visit(id) {
			if (id == null || visited.has(id)) return;
			invariant(!visiting.has(id), `${field} cycle reaches ${id}`);
			const instance = instances.get(id);
			invariant(instance, `instance ${id} does not exist`);
			visiting.add(id);
			visit(instance[field] || null);
			visiting.delete(id);
			visited.add(id);
		}
		for (const id of instances.keys()) visit(id);
	}

	class GraphModel {
		constructor(manifest) {
			invariant(manifest?.version === 1, `unsupported manifest version ${manifest?.version}`);
			invariant(typeof manifest.runtimeId === "string" && manifest.runtimeId, "runtimeId is required");
			this.raw = manifest;
			this.runtimeId = manifest.runtimeId;
			this.instances = uniqueMap(manifest.instances, "instance");
			this.locations = uniqueMap(manifest.locations, "location");
			this.regions = uniqueMap(manifest.regions, "region");
			this.fills = uniqueMap(manifest.fills, "fill");
			this.bindings = uniqueMap(manifest.bindings, "binding");
			this.rootless = uniqueMap(manifest.rootless, "rootless record");
			this.mirrors = uniqueMap(manifest.mirrors, "mirror record");
			this.validate();
		}

		validate() {
			assertAcyclic(this.locations);
			assertInstanceParentAcyclic(this.instances, "renderParentId");
			assertInstanceParentAcyclic(this.instances, "provideParentRenderId");
			for (const instance of this.instances.values()) {
				for (const regionId of instance.regionIds || []) {
					invariant(this.regions.has(regionId), `instance ${instance.id} names missing region ${regionId}`);
				}
				for (const edge of [
					instance.renderParentId,
					instance.provideParentRenderId,
				]) {
					if (edge != null) invariant(this.instances.has(edge), `instance ${instance.id} names missing parent ${edge}`);
				}
			}
			for (const location of this.locations.values()) {
				if (location.ownerRenderId != null) {
					invariant(this.instances.has(location.ownerRenderId), `location ${location.id} has missing owner`);
				}
			}
			for (const fill of this.fills.values()) {
				invariant(this.locations.has(fill.sourceLocationId), `fill ${fill.id} has missing source`);
				for (const regionId of fill.regionIds || []) {
					invariant(this.regions.has(regionId), `fill ${fill.id} has missing region ${regionId}`);
				}
			}
			for (const binding of this.bindings.values()) {
				invariant(this.locations.has(binding.sourceLocationId), `binding ${binding.id} has missing source`);
				invariant(this.instances.has(binding.targetRenderId), `binding ${binding.id} has missing target`);
				if (binding.targetRegionId != null) {
					invariant(this.regions.has(binding.targetRegionId), `binding ${binding.id} has missing target region`);
				}
			}
			for (const mirror of this.mirrors.values()) {
				invariant((mirror.regionIds || []).length >= 2, `mirror ${mirror.id} needs two regions`);
				for (const regionId of mirror.regionIds) {
					invariant(this.rootless.has(regionId), `mirror ${mirror.id} has missing rootless region ${regionId}`);
				}
			}
		}

		instancesInRenderOrder() {
			const depth = new Map();
			const getDepth = (instance) => {
				if (depth.has(instance.id)) return depth.get(instance.id);
				const parent = instance.renderParentId
					? this.instances.get(instance.renderParentId)
					: null;
				const value = parent ? getDepth(parent) + 1 : 0;
				depth.set(instance.id, value);
				return value;
			};
			return Array.from(this.instances.values()).sort((left, right) =>
				getDepth(left) - getDepth(right),
			);
		}
	}

	function rootsForRegion(model, regionId) {
		const region = model.regions.get(regionId);
		invariant(region, `missing region ${regionId}`);
		if (!region.selector) return [];
		return Array.from(document.querySelectorAll(region.selector));
	}

	function rootsForInstance(model, instance) {
		const roots = [];
		const seen = new Set();
		for (const regionId of instance.regionIds || []) {
			for (const root of rootsForRegion(model, regionId)) {
				if (!(root instanceof Element) || seen.has(root)) continue;
				seen.add(root);
				roots.push(root);
			}
		}
		return roots;
	}

	function carriersForBinding(model, binding) {
		const roots = rootsForRegion(model, binding.targetRegionId);
		if (!binding.attribute) return roots;
		return roots.filter((root) => root.getAttribute(binding.attribute) === binding.id);
	}

	function sourceDescriptor(model, locationId, target = null) {
		const location = model.locations.get(locationId);
		invariant(location, `missing source location ${locationId}`);
		return globalThis.SlotsScopeSpike.descriptorFor(location.sourceToken, target);
	}

	function setSpaceToken(el, attribute, token) {
		const tokens = new Set((el.getAttribute(attribute) || "").trim().split(/\s+/).filter(Boolean));
		tokens.add(token);
		el.setAttribute(attribute, Array.from(tokens).join(" "));
	}

	function removeSpaceToken(el, attribute, token) {
		const tokens = (el.getAttribute(attribute) || "")
			.trim()
			.split(/\s+/)
			.filter((item) => item && item !== token);
		if (tokens.length) el.setAttribute(attribute, tokens.join(" "));
		else el.removeAttribute(attribute);
	}

	class GraphFirstAlpineRuntime {
		constructor(manifest) {
			this.model = new GraphModel(manifest);
			this.Alpine = null;
			this.instanceState = new Map();
			this.bindingStops = [];
			this.propsBindings = [];
			this.clientBindings = [];
			this.rootlessRegistry = null;
			this.rootlessState = new Map();
			this.eventLog = [];
			this.destroyed = false;
		}

		project() {
			const instanceAttribute = `data-cf-instances-${this.model.runtimeId}`;
			const memberships = new Map();
			for (const instance of this.model.instancesInRenderOrder()) {
				for (const root of rootsForInstance(this.model, instance)) {
					const ids = memberships.get(root) || [];
					ids.push(instance.id);
					memberships.set(root, ids);
				}
			}
			for (const root of document.querySelectorAll("*")) {
				if (memberships.has(root)) continue;
				if (root.hasAttribute(instanceAttribute)) root.removeAttribute(instanceAttribute);
				removeSpaceToken(root, "data-cf-root", this.model.runtimeId);
			}
			for (const [root, ids] of memberships) {
				setSpaceToken(root, "data-cf-root", this.model.runtimeId);
				root.setAttribute(instanceAttribute, ids.join(" "));
			}
			for (const fill of this.model.fills.values()) {
				const location = this.model.locations.get(fill.sourceLocationId);
				for (const regionId of fill.regionIds || []) {
					for (const root of rootsForRegion(this.model, regionId)) {
						const existing = root.getAttribute("x-cfill");
						invariant(!existing || existing === location.sourceToken, `${root.id || root.tagName} has two fill sources`);
						root.setAttribute("x-cfill", location.sourceToken);
					}
				}
			}
			for (const binding of this.model.bindings.values()) {
				if (binding.kind !== "owned-text") continue;
				for (const carrier of carriersForBinding(this.model, binding)) {
					carrier.setAttribute("x-text", binding.expression);
				}
			}
		}

		install(Alpine) {
			this.Alpine = Alpine;
			for (const instance of this.model.instances.values()) {
				this.instanceState.set(instance.id, {
					id: instance.id,
					els: [],
					props: Alpine.reactive({}),
					scope: Alpine.reactive({ ...(instance.initialScope || {}) }),
					group: null,
				});
			}
			this.project();
			Alpine.addRootSelector(() =>
				this.destroyed
					? ":not(*)"
					: `[data-cf-root~="${this.model.runtimeId}"]`,
			);
			Alpine.interceptInit((el) => {
				if (this.destroyed) return;
				if (!el.hasAttribute?.("data-cf-root")) return;
				const runtimeTokens = (el.getAttribute("data-cf-root") || "").split(/\s+/);
				if (!runtimeTokens.includes(this.model.runtimeId)) return;
				const ids = (el.getAttribute(`data-cf-instances-${this.model.runtimeId}`) || "")
					.split(/\s+/)
					.filter(Boolean);
				const innermost = ids.at(-1);
				if (!innermost) return;
				const state = this.instanceState.get(innermost);
				invariant(state, `root names missing instance ${innermost}`);
				Alpine.addScopeToNode(el, state.scope);
				el._x_dataStack = el._x_dataStack.slice(0, 1);
			});
		}

		activate() {
			invariant(this.Alpine, "Alpine runtime was not installed");
			for (const instance of this.model.instances.values()) {
				const state = this.instanceState.get(instance.id);
				const roots = rootsForInstance(this.model, instance);
				state.els.splice(0, state.els.length, ...roots);
				state.group = new globalThis.RootGroupSpike.RootGroup(roots);
			}

			for (const binding of this.model.bindings.values()) {
				if (binding.kind === "props") this.activateProps(binding);
				if (
					binding.kind === "alpine-event" ||
					binding.kind === "citry-event" ||
					binding.kind === "boundary-event"
				) {
					this.activateEvent(binding);
				}
			}

			if ((this.model.rootless.size || this.model.mirrors.size) && globalThis.RootlessLifecycleSpike) {
				this.rootlessRegistry = new globalThis.RootlessLifecycleSpike.RootlessRegistry(document);
				const mirroredRegionIds = new Set();
				for (const mirror of this.model.mirrors.values()) {
					for (const id of mirror.regionIds) mirroredRegionIds.add(id);
					const sharedScope = this.Alpine.reactive({ ...(mirror.initialScope || {}) });
					const group = this.rootlessRegistry.adoptMirrors(mirror.id, mirror.regionIds, {
						anchorKey: mirror.id,
						sharedScope,
					});
					this.rootlessState.set(mirror.id, group);
				}
				for (const record of this.model.rootless.values()) {
					if (mirroredRegionIds.has(record.id)) continue;
					const instance = this.rootlessRegistry.adopt(record.id, {
						anchorKey: record.anchorKey || record.id,
					});
					Object.assign(instance.scope, record.initialScope || {});
					this.rootlessState.set(record.id, instance);
				}
			}
			return this;
		}

		activateProps(binding) {
			const target = this.instanceState.get(binding.targetRenderId);
			const targetRoot = rootsForRegion(this.model, binding.targetRegionId)[0] || null;
			const descriptor = sourceDescriptor(this.model, binding.sourceLocationId, targetRoot);
			this.propsBindings.push({ binding, descriptor });
			let active = true;
			const runner = this.Alpine.effect(() => {
				if (!active) return;
				descriptor.signal.version;
				const supplied = this.Alpine.evaluateRaw(descriptor.carrier, binding.expression);
				invariant(supplied && typeof supplied === "object" && !Array.isArray(supplied), `${binding.id} did not return an object`);
				for (const key of Object.keys(target.props)) {
					if (!Object.hasOwn(supplied, key)) delete target.props[key];
				}
				Object.assign(target.props, supplied);
			});
			this.bindingStops.push(() => {
				active = false;
				this.Alpine.release(runner);
			});
		}

		activateEvent(binding) {
			const target = this.instanceState.get(binding.targetRenderId);
			const targetRoot = rootsForRegion(this.model, binding.targetRegionId)[0] || null;
			const descriptor = sourceDescriptor(this.model, binding.sourceLocationId, targetRoot);
			const source = new globalThis.BoundaryScopeSpike.SourceScopeAnchor(descriptor.carrier, binding.id);
			const clientBinding = new globalThis.BoundaryScopeSpike.BoundaryScopeClientBinding(target.group, source, {
				onDrop: (reason) => this.eventLog.push({ binding: binding.id, dropped: reason }),
			});
			const receive = (_value, event, carrier) => {
				this.eventLog.push({ binding: binding.id, target: event.target.id, carrier: carrier.id });
			};
			const stop = binding.kind === "citry-event"
				? clientBinding.onCitry(binding.event, binding.spec || {}, binding.expression, receive)
				: clientBinding.onAlpine(binding.event, binding.modifiers || [], binding.expression, receive);
			this.clientBindings.push({ binding, descriptor, source, clientBinding, stop });
		}

		refresh() {
			for (const item of this.propsBindings) {
				const targetRoot = rootsForRegion(this.model, item.binding.targetRegionId)[0] || null;
				globalThis.SlotsScopeSpike.refreshDescriptor(item.descriptor, targetRoot);
			}
			for (const instance of this.model.instances.values()) {
				const state = this.instanceState.get(instance.id);
				const roots = rootsForInstance(this.model, instance);
				state.els.splice(0, state.els.length, ...roots);
				state.group?.setRoots(roots);
			}
			for (const fill of this.model.fills.values()) {
				for (const regionId of fill.regionIds || []) {
					for (const root of rootsForRegion(this.model, regionId)) {
						if (globalThis.SlotsScopeSpike.sourceOf(root)) globalThis.SlotsScopeSpike.refreshFor(root);
					}
				}
			}
			for (const item of this.clientBindings) {
				const targetRoot = rootsForRegion(this.model, item.binding.targetRegionId)[0] || null;
				globalThis.SlotsScopeSpike.refreshDescriptor(item.descriptor, targetRoot);
				item.source.setCarrier(item.descriptor.carrier);
			}
			this.rootlessRegistry?.reconcile();
		}

		destroy() {
			if (this.destroyed) return;
			this.destroyed = true;
			for (const stop of this.bindingStops.splice(0)) stop();
			this.propsBindings.length = 0;
			for (const item of this.clientBindings.splice(0)) {
				item.stop();
				item.clientBinding.destroy();
				item.source.destroy();
			}
			for (const state of this.instanceState.values()) state.group?.destroy();
			this.rootlessRegistry?.destroy();
		}
	}

	function mergedScope(carrier, extras) {
		const alpineScope = globalThis.Alpine.mergeProxies(globalThis.Alpine.closestDataStack(carrier));
		return new Proxy(Object.create(null), {
			has(_target, key) {
				return Object.hasOwn(extras, key) || Reflect.has(alpineScope, key);
			},
			get(_target, key) {
				if (key === Symbol.unscopables) return undefined;
				if (Object.hasOwn(extras, key)) return extras[key];
				return Reflect.get(alpineScope, key);
			},
			set(_target, key, value) {
				if (Object.hasOwn(extras, key)) {
					extras[key] = value;
					return true;
				}
				return Reflect.set(alpineScope, key, value);
			},
			ownKeys() {
				return Array.from(new Set([...Reflect.ownKeys(extras), ...Reflect.ownKeys(alpineScope)]));
			},
			getOwnPropertyDescriptor(_target, key) {
				if (Object.hasOwn(extras, key) || Reflect.has(alpineScope, key)) {
					return { configurable: true, enumerable: true };
				}
				return undefined;
			},
		});
	}

	function compileOwnedExpression(expression, statements = false) {
		const key = `${statements ? "s" : "e"}:${expression}`;
		if (compiledExpressions.has(key)) return compiledExpressions.get(key);
		const body = statements
			? `with (scope) { ${expression} }`
			: `with (scope) { return (${expression}); }`;
		const compiled = new Function("scope", body);
		compiledExpressions.set(key, compiled);
		return compiled;
	}

	class CitryDirectiveRuntime {
		constructor(manifest) {
			this.model = new GraphModel(manifest);
			this.Alpine = null;
			this.instanceState = new Map();
			this.locationState = new Map();
			this.stops = [];
			this.groups = [];
			this.eventLog = [];
		}

		install(Alpine) {
			this.Alpine = Alpine;
			for (const instance of this.model.instances.values()) {
				this.instanceState.set(instance.id, {
					id: instance.id,
					props: Alpine.reactive({}),
					scope: Alpine.reactive({ ...(instance.initialScope || {}) }),
				});
			}
			for (const location of this.model.locations.values()) {
				this.locationState.set(location.id, { version: Alpine.reactive({ value: 0 }), carrier: null });
			}
		}

		source(locationId, target = null) {
			const state = this.locationState.get(locationId);
			state.version.value;
			const descriptor = sourceDescriptor(this.model, locationId, target);
			state.carrier = descriptor.carrier;
			return state;
		}

		evaluate(locationId, expression, extras = {}, statements = false, target = null) {
			const source = this.source(locationId, target);
			const lexicalMagics = {
				$refs: this.Alpine.evaluateRaw(source.carrier, "$refs"),
				$root: this.Alpine.evaluateRaw(source.carrier, "$root"),
				$id: this.Alpine.dontAutoEvaluateFunctions(
					() => this.Alpine.evaluateRaw(source.carrier, "$id"),
				),
			};
			const scope = mergedScope(source.carrier, { ...lexicalMagics, ...extras });
			return compileOwnedExpression(expression, statements)(scope);
		}

		bindingCarriers(binding) {
			return carriersForBinding(this.model, binding);
		}

		activate() {
			for (const binding of this.model.bindings.values()) {
				const carriers = this.bindingCarriers(binding);
				invariant(carriers.length > 0, `${binding.id} has no ${binding.attribute} carrier`);
				if (binding.kind === "props") this.activateProps(binding, carriers);
				if (binding.kind === "citry-text" || binding.kind === "owned-text") {
					this.activateText(binding, carriers);
				}
				if (binding.kind === "citry-on" || binding.kind === "boundary-event") {
					this.activateEvent(binding, carriers);
				}
			}
			return this;
		}

		activateProps(binding, carriers) {
			const target = this.instanceState.get(binding.targetRenderId);
			let active = true;
			const runner = this.Alpine.effect(() => {
				if (!active) return;
				const supplied = this.evaluate(binding.sourceLocationId, binding.expression, {}, false, carriers[0]);
				invariant(supplied && typeof supplied === "object" && !Array.isArray(supplied), `${binding.id} did not return an object`);
				for (const key of Object.keys(target.props)) {
					if (!Object.hasOwn(supplied, key)) delete target.props[key];
				}
				Object.assign(target.props, supplied);
			});
			this.stops.push(() => {
				active = false;
				this.Alpine.release(runner);
			});
		}

		activateText(binding, carriers) {
			for (const carrier of carriers) {
				let active = true;
				const runner = this.Alpine.effect(() => {
					if (!active || !carrier.isConnected) return;
					const value = this.evaluate(binding.sourceLocationId, binding.expression, {}, false, carrier);
					carrier.textContent = value == null ? "" : String(value);
				});
				this.stops.push(() => {
					active = false;
					this.Alpine.release(runner);
				});
			}
		}

		activateEvent(binding, carriers) {
			if (binding.kind === "boundary-event") {
				const group = new globalThis.RootGroupSpike.RootGroup(
					rootsForRegion(this.model, binding.targetRegionId),
				);
				this.groups.push(group);
				const stop = group.on(binding.event, binding.modifiers || [], (event, carrier) => {
					this.evaluate(
						binding.sourceLocationId,
						binding.expression,
						{ $el: carrier, $event: event },
						true,
						carrier,
					);
					this.eventLog.push({ binding: binding.id, target: event.target.id, carrier: carrier.id });
				});
				this.stops.push(stop);
				return;
			}
			for (const carrier of carriers) {
				const listener = (event) => {
					this.evaluate(
						binding.sourceLocationId,
						binding.expression,
						{ $el: carrier, $event: event },
						true,
						carrier,
					);
					this.eventLog.push({ binding: binding.id, target: event.target.id, carrier: carrier.id });
				};
				carrier.addEventListener(binding.event, listener);
				this.stops.push(() => carrier.removeEventListener(binding.event, listener));
			}
		}

		refreshSources() {
			for (const [id, state] of this.locationState) {
				const descriptor = sourceDescriptor(this.model, id);
				state.carrier = descriptor.carrier;
				state.version.value += 1;
			}
		}

		destroy() {
			for (const stop of this.stops.splice(0)) stop();
			for (const group of this.groups.splice(0)) group.destroy();
		}
	}

	function parseManifests() {
		return Array.from(document.querySelectorAll(MANIFEST_SELECTOR)).map((script) => ({
			mode: script.getAttribute("data-component-first"),
			manifest: JSON.parse(script.textContent),
		}));
	}

	let resolveReady;
	let rejectReady;
	globalThis.ComponentFirstSpikeReady = new Promise((resolve, reject) => {
		resolveReady = resolve;
		rejectReady = reject;
	});

	document.addEventListener("alpine:init", () => {
		try {
			const runtimes = [];
			for (const entry of parseManifests()) {
				const runtime = entry.mode === "alpine"
					? new GraphFirstAlpineRuntime(entry.manifest)
					: new CitryDirectiveRuntime(entry.manifest);
				runtime.install(globalThis.Alpine);
				runtimes.push(runtime);
			}
			globalThis.ComponentFirstSpikeRuntimes = runtimes;
			queueMicrotask(() => {
				try {
					for (const runtime of runtimes) runtime.activate();
					resolveReady(runtimes);
				} catch (error) {
					rejectReady(error);
				}
			});
		} catch (error) {
			rejectReady(error);
		}
	});

	globalThis.ComponentFirstSpike = {
		CitryDirectiveRuntime,
		GraphFirstAlpineRuntime,
		GraphModel,
		compileOwnedExpression,
		mergedScope,
		carriersForBinding,
		rootsForRegion,
	};
})();
