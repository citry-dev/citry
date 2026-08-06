/*
 * Throwaway rootless-lifecycle prototype for rootless_lifecycle_harness.py.
 *
 * This is research code, not Citry runtime code. It deliberately uses the
 * public Alpine surface plus the pinned morph plugin while keeping range
 * identity, liveness, effects, timers, and nested-range protection in a
 * Citry-shaped registry.
 */
(() => {
	const START_PREFIX = "citry-start:";
	const END_PREFIX = "citry-end:";
	const PLACEHOLDER = "data-citry-rootless-placeholder";

	function marker(kind, id) {
		return `${kind === "start" ? START_PREFIX : END_PREFIX}${id}`;
	}

	function isElement(node) {
		return node?.nodeType === Node.ELEMENT_NODE;
	}

	function markerInfo(node) {
		if (node?.nodeType !== Node.COMMENT_NODE) return null;
		if (node.data.startsWith(START_PREFIX)) {
			return { kind: "start", id: node.data.slice(START_PREFIX.length) };
		}
		if (node.data.startsWith(END_PREFIX)) {
			return { kind: "end", id: node.data.slice(END_PREFIX.length) };
		}
		return null;
	}

	function nodesBetween(start, end) {
		const nodes = [];
		for (
			let node = start.nextSibling;
			node && node !== end;
			node = node.nextSibling
		) {
			nodes.push(node);
		}
		return nodes;
	}

	function precedes(start, end) {
		return Boolean(
			start.compareDocumentPosition(end) & Node.DOCUMENT_POSITION_FOLLOWING,
		);
	}

	function exactMarkers(root, id) {
		const starts = [];
		const ends = [];
		const walker = document.createTreeWalker(root, NodeFilter.SHOW_COMMENT);
		for (let node = walker.nextNode(); node; node = walker.nextNode()) {
			if (node.data === marker("start", id)) starts.push(node);
			if (node.data === marker("end", id)) ends.push(node);
		}
		return { starts, ends };
	}

	function directMarkerPairs(parent) {
		const stack = [];
		const pairs = [];
		for (const node of Array.from(parent.childNodes)) {
			const info = markerInfo(node);
			if (!info) continue;
			if (info.kind === "start") {
				stack.push({ id: info.id, start: node });
				continue;
			}
			const opened = stack.pop();
			if (!opened || opened.id !== info.id) {
				throw new Error(
					`Citry rootless markers are crossed or unmatched near ${info.id}`,
				);
			}
			pairs.push({ ...opened, end: node, depth: stack.length });
		}
		if (stack.length) {
			throw new Error(
				`Citry rootless start marker ${stack.at(-1).id} has no end`,
			);
		}
		return pairs.filter((pair) => pair.depth === 0);
	}

	function validateMarkerPair(found, id) {
		const start = found.starts[0];
		const end = found.ends[0];
		if (start.parentNode !== end.parentNode) {
			throw new Error(
				`Citry rootless markers for ${id} have different parents`,
			);
		}
		const stack = [];
		for (const node of Array.from(start.parentNode.childNodes)) {
			const info = markerInfo(node);
			if (!info) continue;
			if (info.kind === "start") {
				stack.push(info.id);
				continue;
			}
			if (stack.at(-1) === info.id) {
				stack.pop();
				continue;
			}
			if (info.id === id || stack.includes(id)) {
				throw new Error(`Citry rootless markers are crossed near ${id}`);
			}
		}
		if (stack.includes(id)) {
			throw new Error(`Citry rootless start marker ${id} has no matching end`);
		}
	}

	function collapsePair(pair, anchorKey = pair.id) {
		const placeholder = document.createElement("template");
		placeholder.setAttribute(PLACEHOLDER, pair.id);
		placeholder.setAttribute("key", `citry-rootless:${anchorKey}`);
		pair.start.before(placeholder);
		for (let node = pair.start; node; ) {
			const next = node.nextSibling;
			placeholder.content.append(node);
			if (node === pair.end) break;
			node = next;
		}
		return placeholder;
	}

	function collapseParsedRanges(root, resolveAnchor) {
		const visit = (parent) => {
			const pairs = directMarkerPairs(parent);
			const covered = new Set();
			for (const pair of pairs) {
				let node = pair.start;
				while (node) {
					covered.add(node);
					if (node === pair.end) break;
					node = node.nextSibling;
				}
				collapsePair(pair, resolveAnchor(pair.id));
			}
			for (const child of Array.from(parent.children)) {
				if (!covered.has(child) && !child.hasAttribute(PLACEHOLDER))
					visit(child);
			}
		};
		visit(root);
	}

	function rangeContains(range, candidate) {
		for (const node of nodesBetween(range.start, range.end)) {
			if (node === candidate) return true;
			if (isElement(node) && node.contains(candidate)) return true;
		}
		return false;
	}

	function expandPlaceholders(range) {
		const placeholders = [];
		for (const node of nodesBetween(range.start, range.end)) {
			if (!isElement(node)) continue;
			if (node.hasAttribute(PLACEHOLDER)) placeholders.push(node);
			placeholders.push(...node.querySelectorAll(`template[${PLACEHOLDER}]`));
		}
		for (const placeholder of placeholders) {
			if (!placeholder.isConnected || !rangeContains(range, placeholder))
				continue;
			placeholder.before(placeholder.content);
			placeholder.remove();
		}
	}

	class RootlessLifecycle {
		constructor(registry, id, options) {
			this.registry = registry;
			this.id = id;
			this.options = options;
			this.anchorKey = options.anchorKey || id;
			this.start = null;
			this.end = null;
			this.els = [];
			this.props = Alpine.reactive({});
			this.scope = options.sharedScope || Alpine.reactive({});
			this.initialized = false;
			this.destroyed = false;
			this.destroyReason = null;
			this.lastError = null;
			this._parent = null;
			this._supplyStop = null;
			this._managedStops = [];
			this._cleanupCallbacks = [];
			this._polls = new Set();
			this._rootScopes = new Map();
			this._everResolved = false;
		}

		_resolve({ settled = false } = {}) {
			if (this.start || this.destroyed) return;
			const found = exactMarkers(this.registry.root, this.id);
			if (found.starts.length === 0 && found.ends.length === 0) return;
			if (found.starts.length !== 1 || found.ends.length !== 1) {
				if (this.options.pending && !settled) return;
				this._fail(
					`Citry rootless instance ${this.id} needs exactly one start and one end marker`,
				);
				this.destroy("invalid-marker-topology");
				return;
			}
			try {
				validateMarkerPair(found, this.id);
			} catch (error) {
				if (this.options.pending && !settled) return;
				this._fail(
					`Citry rootless marker topology is invalid for ${this.id}`,
					error,
				);
				this.destroy("invalid-marker-topology");
				return;
			}
			this.start = found.starts[0];
			this.end = found.ends[0];
			this._everResolved = true;
		}

		isValid() {
			return Boolean(
				this.start?.isConnected &&
					this.end?.isConnected &&
					this.start.data === marker("start", this.id) &&
					this.end.data === marker("end", this.id) &&
					this.start.parentNode === this.end.parentNode &&
					isElement(this.start.parentNode) &&
					precedes(this.start, this.end),
			);
		}

		_reconcile() {
			if (this.destroyed) return;
			this._resolve();
			if (!this.start || !this.end) return;
			if (!this.isValid()) {
				if (this.initialized || this._everResolved) {
					this.destroy("invalid-or-removed-range");
				}
				return;
			}
			const parent = this.start.parentElement;
			if (!this.initialized) {
				this._parent = parent;
				this._syncRoots();
				this._startSupply();
				this._initialize();
				return;
			}
			if (parent !== this._parent) {
				this._parent = parent;
				this._startSupply();
			}
			this._syncRoots();
		}

		_initialize() {
			this.initialized = true;
			if (typeof this.options.init !== "function") return;
			try {
				const cleanup = this.options.init(this.context());
				if (typeof cleanup === "function") this._cleanupCallbacks.push(cleanup);
			} catch (error) {
				this._fail(`Citry rootless init failed for ${this.id}`, error);
				this.destroy("init-error");
			}
		}

		_startSupply() {
			this._supplyStop?.();
			this._supplyStop = null;
			if (!this.options.supplyExpression) return;
			let active = true;
			const runner = Alpine.effect(() => {
				if (!active || this.destroyed || !this.isValid()) return;
				const supplied = Alpine.evaluateRaw(
					this.start.parentElement,
					this.options.supplyExpression,
					this.options.supplyScope ? { scope: this.options.supplyScope } : {},
				);
				if (
					supplied === null ||
					typeof supplied !== "object" ||
					Array.isArray(supplied)
				) {
					this._fail(
						`x-props for rootless instance ${this.id} must evaluate to an object`,
					);
					return;
				}
				for (const key of Object.keys(this.props)) {
					if (!Object.hasOwn(supplied, key)) delete this.props[key];
				}
				Object.assign(this.props, supplied);
			});
			this._supplyStop = () => {
				if (!active) return;
				active = false;
				Alpine.release(runner);
			};
		}

		context() {
			return {
				id: this.id,
				els: this.els,
				props: this.props,
				scope: this.scope,
				reactive: Alpine.reactive,
				effect: (callback) => this.effect(callback),
				onCleanup: (callback) => this.onCleanup(callback),
				poll: (interval, callback) => this.poll(interval, callback),
			};
		}

		effect(callback) {
			if (this.destroyed)
				throw new Error(`Rootless instance ${this.id} is destroyed`);
			let active = true;
			const runner = Alpine.effect(() => {
				if (active && !this.destroyed) callback();
			});
			const stop = () => {
				if (!active) return;
				active = false;
				Alpine.release(runner);
			};
			this._managedStops.push(stop);
			return stop;
		}

		onCleanup(callback) {
			if (typeof callback !== "function")
				throw new TypeError("cleanup must be a function");
			this._cleanupCallbacks.push(callback);
			return callback;
		}

		poll(interval, callback) {
			if (this.destroyed)
				throw new Error(`Rootless instance ${this.id} is destroyed`);
			const timer = window.setInterval(() => {
				if (!this.destroyed && this.isValid())
					callback(this.start.parentElement);
			}, interval);
			this._polls.add(timer);
			return () => {
				window.clearInterval(timer);
				this._polls.delete(timer);
			};
		}

		bindDomEvent() {
			if (this.els.length === 0) {
				throw new Error(
					`Rootless Citry instance ${this.id} has no DOM EventTarget for a component-boundary handler`,
				);
			}
			throw new Error(
				"Research adapter does not implement element event binding",
			);
		}

		_contextualContainer(html) {
			const range = document.createRange();
			range.setStartAfter(this.start);
			range.collapse(true);
			const fragment = range.createContextualFragment(html);
			const container = this.start.parentElement.cloneNode(false);
			container.removeAttribute("id");
			container.append(fragment);
			return container;
		}

		_nestedLifecycles() {
			const candidates = Array.from(this.registry.instances).filter(
				(candidate) =>
					candidate !== this &&
					candidate.isValid() &&
					rangeContains(this, candidate.start) &&
					rangeContains(this, candidate.end),
			);
			return candidates.filter(
				(candidate) =>
					!candidates.some(
						(other) =>
							other !== candidate &&
							rangeContains(other, candidate.start) &&
							rangeContains(other, candidate.end),
					),
			);
		}

		replace(
			html,
			{ protectNested = true, resolveIncomingAnchor = (id) => id } = {},
		) {
			if (!this.isValid())
				throw new Error(`Cannot morph invalid rootless range ${this.id}`);
			const livePlaceholders = [];
			if (protectNested) {
				for (const nested of this._nestedLifecycles()) {
					livePlaceholders.push(
						collapsePair(
							{
								id: nested.id,
								start: nested.start,
								end: nested.end,
							},
							nested.anchorKey,
						),
					);
				}
			}
			try {
				const container = this._contextualContainer(html);
				if (protectNested)
					collapseParsedRanges(container, resolveIncomingAnchor);
				Alpine.morphBetween(this.start, this.end, container, {
					key: (element) => element.getAttribute("key"),
				});
			} finally {
				if (protectNested) {
					expandPlaceholders(this);
					for (const placeholder of livePlaceholders) {
						if (placeholder.isConnected) continue;
						// If the incoming tree removed the nested instance, its nodes stay
						// detached in this inert holder until registry teardown releases it.
					}
				}
			}
			this._syncRoots();
			this.registry.reconcile();
			return this;
		}

		_syncRoots() {
			if (!this.isValid()) return;
			const roots = nodesBetween(this.start, this.end).filter(isElement);
			const previous = this.els.slice();
			this.els.splice(0, this.els.length, ...roots);
			for (const root of previous) {
				if (roots.includes(root)) continue;
				this._rootScopes.get(root)?.();
				this._rootScopes.delete(root);
			}
			for (const root of roots) {
				if (this._rootScopes.has(root)) continue;
				this._rootScopes.set(
					root,
					Alpine.addScopeToNode(root, this.scope, this.start.parentElement),
				);
			}
		}

		_fail(message, cause = null) {
			const error = cause instanceof Error ? cause : new Error(message);
			if (cause instanceof Error && !error.message.startsWith(message)) {
				error.message = `${message}: ${error.message}`;
			}
			this.lastError = error;
			this.options.onError?.(error);
		}

		destroy(reason = "manual") {
			if (this.destroyed) return;
			this.destroyed = true;
			this.destroyReason = reason;
			this._supplyStop?.();
			this._supplyStop = null;
			for (const stop of this._managedStops.splice(0)) {
				try {
					stop();
				} catch (error) {
					this._fail(`Managed-effect cleanup failed for ${this.id}`, error);
				}
			}
			for (const timer of this._polls) window.clearInterval(timer);
			this._polls.clear();
			for (const undo of this._rootScopes.values()) undo();
			this._rootScopes.clear();
			for (const cleanup of this._cleanupCallbacks.splice(0)) {
				try {
					cleanup();
				} catch (error) {
					this._fail(`User cleanup failed for ${this.id}`, error);
				}
			}
			this.els.splice(0);
			this.registry.instances.delete(this);
		}
	}

	class RootlessMirrorGroup {
		constructor(registry, anchorKey, regionIds, options) {
			this.registry = registry;
			this.anchorKey = anchorKey;
			this.options = options;
			this.els = [];
			this.props = Alpine.reactive({});
			this.scope = Alpine.reactive({});
			this.regions = [];
			this.initialized = false;
			this.destroyed = false;
			this.destroyReason = null;
			this._carrier = null;
			this._supplyStop = null;
			this._managedStops = [];
			this._cleanupCallbacks = [];
			this._polls = new Set();
			registry.groups.add(this);
			try {
				for (const regionId of regionIds) {
					const region = registry.adopt(regionId, {
						anchorKey: `${anchorKey}:${regionId}`,
						sharedScope: this.scope,
						init: () => () => queueMicrotask(() => this._reconcile()),
					});
					this.regions.push(region);
				}
			} catch (error) {
				this.destroy("mirror-adoption-rollback");
				throw error;
			}
			this._reconcile();
		}

		_liveRegions() {
			return this.regions.filter((region) => region.isValid());
		}

		_reconcile() {
			if (this.destroyed) return;
			const live = this._liveRegions();
			this._syncEls(live);
			if (live.length === 0) {
				if (this.initialized) this.destroy("all-mirrors-removed");
				return;
			}
			const carrier = live[0];
			if (carrier !== this._carrier) {
				this._carrier = carrier;
				this._startSupply();
			}
			if (!this.initialized) this._initialize();
		}

		_syncEls(live = this._liveRegions()) {
			const elements = live.flatMap((region) => region.els);
			this.els.splice(0, this.els.length, ...elements);
		}

		_startSupply() {
			this._supplyStop?.();
			this._supplyStop = null;
			if (!this.options.supplyExpression || !this._carrier) return;
			let active = true;
			const runner = Alpine.effect(() => {
				if (!active || this.destroyed || !this._carrier?.isValid()) return;
				const supplied = Alpine.evaluateRaw(
					this._carrier.start.parentElement,
					this.options.supplyExpression,
				);
				if (
					supplied === null ||
					typeof supplied !== "object" ||
					Array.isArray(supplied)
				) {
					this.options.onError?.(
						new Error(
							`x-props for mirrored rootless instance ${this.anchorKey} must be an object`,
						),
					);
					return;
				}
				for (const key of Object.keys(this.props)) {
					if (!Object.hasOwn(supplied, key)) delete this.props[key];
				}
				Object.assign(this.props, supplied);
			});
			this._supplyStop = () => {
				if (!active) return;
				active = false;
				Alpine.release(runner);
			};
		}

		_initialize() {
			this.initialized = true;
			if (typeof this.options.init !== "function") return;
			try {
				const cleanup = this.options.init(this.context());
				if (typeof cleanup === "function") this._cleanupCallbacks.push(cleanup);
			} catch (error) {
				this.options.onError?.(error);
				this.destroy("init-error");
			}
		}

		context() {
			return {
				id: this.anchorKey,
				els: this.els,
				props: this.props,
				scope: this.scope,
				reactive: Alpine.reactive,
				effect: (callback) => this.effect(callback),
				poll: (interval, callback) => this.poll(interval, callback),
			};
		}

		effect(callback) {
			let active = true;
			const runner = Alpine.effect(() => {
				if (active && !this.destroyed) callback();
			});
			const stop = () => {
				if (!active) return;
				active = false;
				Alpine.release(runner);
			};
			this._managedStops.push(stop);
			return stop;
		}

		poll(interval, callback) {
			const timer = window.setInterval(() => {
				const carrier = this._liveRegions()[0];
				if (!this.destroyed && carrier) callback(carrier.start.parentElement);
			}, interval);
			this._polls.add(timer);
			return () => {
				window.clearInterval(timer);
				this._polls.delete(timer);
			};
		}

		replace(html, options = {}) {
			for (const region of this._liveRegions()) region.replace(html, options);
			this._reconcile();
			return this;
		}

		destroy(reason = "manual") {
			if (this.destroyed) return;
			this.destroyed = true;
			this.destroyReason = reason;
			this._supplyStop?.();
			for (const stop of this._managedStops.splice(0)) stop();
			for (const timer of this._polls) window.clearInterval(timer);
			this._polls.clear();
			for (const cleanup of this._cleanupCallbacks.splice(0)) {
				try {
					cleanup();
				} catch (error) {
					this.options.onError?.(error);
				}
			}
			this.els.splice(0);
			this.registry.groups.delete(this);
			for (const region of this.regions) region.destroy("mirror-group-destroy");
		}
	}

	class RootlessRegistry {
		constructor(root = document) {
			this.root = root;
			this.instances = new Set();
			this.groups = new Set();
			this.observer = new MutationObserver(() => this.reconcile());
			this.observer.observe(root, {
				childList: true,
				subtree: true,
				characterData: true,
			});
		}

		adopt(id, options = {}, { pending = false } = {}) {
			if (this.find(id))
				throw new Error(`Citry rootless instance ${id} is already registered`);
			const instance = new RootlessLifecycle(this, id, { ...options, pending });
			this.instances.add(instance);
			instance._resolve({ settled: !pending });
			if (instance.destroyed) throw instance.lastError;
			if (!instance.start && !pending) {
				this.instances.delete(instance);
				throw new Error(
					`Citry rootless instance ${id} is missing its start/end comments; comment stripping is unsupported`,
				);
			}
			instance._reconcile();
			return instance;
		}

		settle(id) {
			const instance = this.find(id);
			if (!instance)
				throw new Error(`Citry rootless instance ${id} is not registered`);
			instance._resolve({ settled: true });
			if (!instance.start && !instance.destroyed) {
				instance._fail(
					`Citry rootless instance ${id} is missing its start/end comments; comment stripping is unsupported`,
				);
				instance.destroy("missing-markers");
			}
			instance._reconcile();
			return !instance.destroyed;
		}

		adoptMirrors(anchorKey, regionIds, options = {}) {
			if (regionIds.length < 2) {
				throw new Error(
					"A mirrored rootless instance needs at least two physical ranges",
				);
			}
			return new RootlessMirrorGroup(this, anchorKey, regionIds, options);
		}

		find(id) {
			return (
				Array.from(this.instances).find((instance) => instance.id === id) ||
				null
			);
		}

		reconcile() {
			for (const instance of Array.from(this.instances)) instance._reconcile();
			for (const group of Array.from(this.groups)) group._reconcile();
		}

		destroy() {
			this.observer.disconnect();
			for (const group of Array.from(this.groups))
				group.destroy("registry-destroy");
			for (const instance of Array.from(this.instances))
				instance.destroy("registry-destroy");
		}
	}

	window.RootlessLifecycleSpike = {
		END_PREFIX,
		RootlessLifecycle,
		RootlessMirrorGroup,
		RootlessRegistry,
		START_PREFIX,
		marker,
		nodesBetween,
	};
})();
