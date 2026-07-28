/*
 * Throwaway RootGroup prototype for docs/design/alpinejs/root_group_harness.py.
 *
 * This is research code, not product runtime code. It intentionally owns its
 * listener and timer machinery instead of importing Alpine's private on.js.
 */
(() => {
	const ENTER_LEAVE_EVENTS = new Set([
		"mouseenter",
		"mouseleave",
		"pointerenter",
		"pointerleave",
	]);

	function assertElement(root) {
		if (!(root instanceof Element)) {
			throw new TypeError("RootGroup members must be Elements");
		}
	}

	function uniqueRoots(roots) {
		const seen = new Set();
		const result = [];
		for (const root of roots) {
			assertElement(root);
			if (seen.has(root)) continue;
			seen.add(root);
			result.push(root);
		}
		return result;
	}

	function dotSyntax(subject) {
		return subject.replace(/-/g, ".");
	}

	function camelCase(subject) {
		return subject
			.toLowerCase()
			.replace(/-(\w)/g, (_match, char) => char.toUpperCase());
	}

	function isNumeric(subject) {
		return !Array.isArray(subject) && !Number.isNaN(Number(subject));
	}

	function kebabCase(subject) {
		if ([" ", "_"].includes(subject)) return subject;
		return subject
			.replace(/([a-z])([A-Z])/g, "$1-$2")
			.replace(/[_\s]/, "-")
			.toLowerCase();
	}

	function isKeyEvent(event) {
		return ["keydown", "keyup"].includes(event);
	}

	function isClickEvent(event) {
		return ["contextmenu", "click", "mouse"].some((item) =>
			event.includes(item),
		);
	}

	function keyToModifiers(key) {
		if (!key) return [];
		key = kebabCase(key);
		const modifierToKeyMap = {
			ctrl: "control",
			slash: "/",
			space: " ",
			spacebar: " ",
			cmd: "meta",
			esc: "escape",
			up: "arrow-up",
			down: "arrow-down",
			left: "arrow-left",
			right: "arrow-right",
			period: ".",
			comma: ",",
			equal: "=",
			minus: "-",
			underscore: "_",
		};
		modifierToKeyMap[key] = key;
		return Object.keys(modifierToKeyMap).filter(
			(modifier) => modifierToKeyMap[modifier] === key,
		);
	}

	// This deliberately mirrors Alpine 3.15.12, including the fact that the
	// token after `passive` is not excluded from click/key filtering.
	function missesAlpineKeyFilter(event, modifiers) {
		let keyModifiers = modifiers.filter(
			(item) =>
				![
					"window",
					"document",
					"prevent",
					"stop",
					"once",
					"capture",
					"self",
					"away",
					"outside",
					"passive",
					"preserve-scroll",
					"blur",
					"change",
					"lazy",
				].includes(item),
		);

		for (const timing of ["debounce", "throttle"]) {
			if (!keyModifiers.includes(timing)) continue;
			const index = keyModifiers.indexOf(timing);
			const next = keyModifiers[index + 1] || "invalid-wait";
			keyModifiers.splice(index, isNumeric(next.split("ms")[0]) ? 2 : 1);
		}

		if (keyModifiers.length === 0) return false;
		if (
			keyModifiers.length === 1 &&
			keyToModifiers(event.key).includes(keyModifiers[0])
		)
			return false;

		const systemModifiers = ["ctrl", "shift", "alt", "meta", "cmd", "super"];
		const selected = systemModifiers.filter((modifier) =>
			keyModifiers.includes(modifier),
		);
		keyModifiers = keyModifiers.filter(
			(modifier) => !selected.includes(modifier),
		);
		if (selected.length > 0) {
			const active = selected.filter((modifier) => {
				const property =
					modifier === "cmd" || modifier === "super" ? "meta" : modifier;
				return event[`${property}Key`];
			});
			if (active.length === selected.length) {
				if (isClickEvent(event.type)) return false;
				if (keyToModifiers(event.key).includes(keyModifiers[0])) return false;
			}
		}
		return true;
	}

	function timingWait(modifiers, name) {
		const next = modifiers[modifiers.indexOf(name) + 1] || "invalid-wait";
		return isNumeric(next.split("ms")[0]) ? Number(next.split("ms")[0]) : 250;
	}

	function eventPathContainsRoot(event, root) {
		const path =
			typeof event.composedPath === "function" ? event.composedPath() : [];
		if (path.includes(root)) return true;
		return path.some(
			(candidate) => candidate instanceof Node && root.contains(candidate),
		);
	}

	class RootGroup {
		constructor(roots = []) {
			this.els = [];
			this._bindings = new Set();
			this._destroyed = false;
			this.setRoots(roots);
		}

		setRoots(roots) {
			if (this._destroyed)
				throw new Error("Cannot update a destroyed RootGroup");
			const previous = this.els.slice();
			const next = uniqueRoots(Array.from(roots));
			this.els.splice(0, this.els.length, ...next);
			for (const binding of this._bindings) binding.syncRoots(previous, next);
			return this;
		}

		addRoot(root, index = this.els.length) {
			assertElement(root);
			if (this.els.includes(root)) return this;
			const next = this.els.slice();
			next.splice(Math.max(0, Math.min(index, next.length)), 0, root);
			return this.setRoots(next);
		}

		removeRoot(root) {
			return this.setRoots(this.els.filter((candidate) => candidate !== root));
		}

		replaceRoot(previous, next) {
			assertElement(next);
			const roots = this.els.slice();
			const index = roots.indexOf(previous);
			if (index < 0)
				throw new Error("Cannot replace a root that is not in the group");
			roots[index] = next;
			return this.setRoots(roots);
		}

		has(root) {
			return this.els.includes(root);
		}

		hasLive(root) {
			return this.has(root) && root.isConnected;
		}

		firstLiveRoot() {
			return this.els.find((root) => root.isConnected) || null;
		}

		containsNode(node) {
			return (
				node instanceof Node &&
				this.els.some((root) => root === node || root.contains(node))
			);
		}

		containsEvent(event) {
			return this.els.some((root) => eventPathContainsRoot(event, root));
		}

		hasVisibleRoot() {
			return this.els.some(
				(root) =>
					root.isConnected &&
					root._x_isShown !== false &&
					(root.offsetWidth >= 1 || root.offsetHeight >= 1),
			);
		}

		on(event, modifiers, callback) {
			if (this._destroyed) throw new Error("Cannot bind a destroyed RootGroup");
			const binding = new AlpineGroupBinding(this, event, modifiers, callback);
			this._bindings.add(binding);
			binding.syncRoots([], this.els);
			return () => binding.cleanup();
		}

		onCitry(event, spec, callback) {
			if (this._destroyed) throw new Error("Cannot bind a destroyed RootGroup");
			const binding = new CitryGroupBinding(this, event, spec, callback);
			this._bindings.add(binding);
			binding.syncRoots([], this.els);
			return () => binding.cleanup();
		}

		poll(interval, callback) {
			if (this._destroyed) throw new Error("Cannot poll a destroyed RootGroup");
			const binding = new GroupPoll(this, interval, callback);
			this._bindings.add(binding);
			return () => binding.cleanup();
		}

		destroy() {
			if (this._destroyed) return;
			this._destroyed = true;
			for (const binding of Array.from(this._bindings)) binding.cleanup();
			this.els.splice(0, this.els.length);
		}
	}

	class GroupBindingBase {
		constructor(group, event, callback) {
			this.group = group;
			this.event = event;
			this.callback = callback;
			this.destroyed = false;
			this.listening = true;
			this.targets = new Set();
			this.cancelTimers = [];
			this.handleEvent = (domEvent) => {
				const direct = domEvent.currentTarget instanceof Element;
				const carrier = direct
					? domEvent.currentTarget
					: this.group.firstLiveRoot();
				this.handler({ event: domEvent, carrier, direct });
			};
		}

		targetMode() {
			return "direct";
		}

		eventTargets() {
			const mode = this.targetMode();
			if (mode === "window") return this.group.els.length ? [window] : [];
			if (mode === "document" || mode === "outside") {
				return this.group.els.length ? [document] : [];
			}
			// A component-tag client binding, such as `@click` on `<c-card>`, can
			// be attached before incoming roots enter the document. DOM listeners
			// work on detached elements, so attach now and let delivery's liveness
			// check suppress work until the member is connected.
			return this.group.els;
		}

		listenerOptions() {
			return false;
		}

		syncRoots() {
			if (!this.listening || this.destroyed) return;
			const expected = new Set(this.eventTargets());
			for (const target of Array.from(this.targets)) {
				if (expected.has(target)) continue;
				target.removeEventListener(
					this.event,
					this.handleEvent,
					this.listenerOptions(),
				);
				this.targets.delete(target);
			}
			for (const target of expected) {
				if (this.targets.has(target)) continue;
				target.addEventListener(
					this.event,
					this.handleEvent,
					this.listenerOptions(),
				);
				this.targets.add(target);
			}
		}

		stopListening() {
			if (!this.listening) return;
			this.listening = false;
			for (const target of this.targets) {
				target.removeEventListener(
					this.event,
					this.handleEvent,
					this.listenerOptions(),
				);
			}
			this.targets.clear();
		}

		deliver(context) {
			if (this.destroyed) return;
			let carrier = context.carrier;
			if (context.direct) {
				if (!carrier || !this.group.hasLive(carrier)) return;
			} else if (!carrier || !this.group.hasLive(carrier)) {
				carrier = this.group.firstLiveRoot();
				if (!carrier) return;
			}
			this.callback(context.event, carrier);
		}

		cleanup() {
			if (this.destroyed) return;
			this.destroyed = true;
			this.stopListening();
			for (const cancel of this.cancelTimers) cancel();
			this.cancelTimers.length = 0;
			this.group._bindings.delete(this);
		}
	}

	class AlpineGroupBinding extends GroupBindingBase {
		constructor(group, event, modifiers, callback) {
			const normalizedModifiers = Array.from(modifiers);
			let normalizedEvent = event;
			if (normalizedModifiers.includes("dot"))
				normalizedEvent = dotSyntax(normalizedEvent);
			if (normalizedModifiers.includes("camel"))
				normalizedEvent = camelCase(normalizedEvent);
			super(group, normalizedEvent, callback);
			this.modifiers = normalizedModifiers;
			this.options = {};
			if (this.modifiers.includes("capture")) this.options.capture = true;
			if (this.modifiers.includes("passive")) {
				this.options.passive =
					this.modifiers[this.modifiers.indexOf("passive") + 1] !== "false";
			}
			this.handler = this.buildHandler();
		}

		targetMode() {
			if (this.modifiers.includes("away") || this.modifiers.includes("outside"))
				return "outside";
			if (this.modifiers.includes("document")) return "document";
			if (this.modifiers.includes("window")) return "window";
			return "direct";
		}

		listenerOptions() {
			return this.options;
		}

		buildHandler() {
			const wrap = (next, wrapper) => (context) => wrapper(next, context);
			let handler = (context) => this.deliver(context);

			if (this.modifiers.includes("debounce")) {
				const wait = timingWait(this.modifiers, "debounce");
				let timer = 0;
				handler = ((next) => {
					const wrapped = (context) => {
						window.clearTimeout(timer);
						timer = window.setTimeout(() => {
							timer = 0;
							next(context);
						}, wait);
					};
					this.cancelTimers.push(() => window.clearTimeout(timer));
					return wrapped;
				})(handler);
			}

			if (this.modifiers.includes("throttle")) {
				const wait = timingWait(this.modifiers, "throttle");
				let inThrottle = false;
				let timer = 0;
				handler = ((next) => {
					const wrapped = (context) => {
						if (inThrottle) return;
						next(context);
						inThrottle = true;
						timer = window.setTimeout(() => {
							inThrottle = false;
							timer = 0;
						}, wait);
					};
					this.cancelTimers.push(() => {
						window.clearTimeout(timer);
						inThrottle = false;
					});
					return wrapped;
				})(handler);
			}

			if (this.modifiers.includes("prevent")) {
				handler = wrap(handler, (next, context) => {
					context.event.preventDefault();
					next(context);
				});
			}
			if (this.modifiers.includes("stop")) {
				handler = wrap(handler, (next, context) => {
					context.event.stopPropagation();
					next(context);
				});
			}
			if (this.modifiers.includes("once")) {
				handler = wrap(handler, (next, context) => {
					next(context);
					this.stopListening();
				});
			}
			if (this.targetMode() === "outside") {
				handler = wrap(handler, (next, context) => {
					if (this.group.containsEvent(context.event)) return;
					if (
						context.event.target &&
						context.event.target.isConnected === false
					)
						return;
					if (!this.group.hasVisibleRoot()) return;
					next(context);
				});
			}
			if (this.modifiers.includes("self")) {
				handler = wrap(handler, (next, context) => {
					if (this.group.els.includes(context.event.target)) next(context);
				});
			}
			if (ENTER_LEAVE_EVENTS.has(this.event)) {
				handler = wrap(handler, (next, context) => {
					if (
						context.event.relatedTarget &&
						this.group.containsNode(context.event.relatedTarget)
					)
						return;
					next(context);
				});
			}
			if (this.event === "submit") {
				handler = wrap(handler, (next, context) => {
					const updates = context.event.target?._x_pendingModelUpdates;
					if (updates) {
						updates.forEach((update) => {
							update();
						});
					}
					next(context);
				});
			}
			if (isKeyEvent(this.event) || isClickEvent(this.event)) {
				handler = wrap(handler, (next, context) => {
					if (!missesAlpineKeyFilter(context.event, this.modifiers))
						next(context);
				});
			}
			return handler;
		}
	}

	class CitryGroupBinding extends GroupBindingBase {
		constructor(group, event, spec, callback) {
			super(group, event, callback);
			this.spec = { ...spec };
			this.onceExhausted = false;
			this.debounceTimer = 0;
			this.throttleUntil = 0;
			this.handler = (context) => this.run(context);
			this.cancelTimers.push(() => window.clearTimeout(this.debounceTimer));
		}

		keyMatches(event) {
			if (!this.spec.key) return true;
			const expected = { enter: "Enter", escape: "Escape" }[this.spec.key];
			return Boolean(expected && event.key === expected);
		}

		schedule(context) {
			const now = Date.now();
			if (this.spec.throttle > 0) {
				if (this.throttleUntil > now) return;
				this.throttleUntil = now + this.spec.throttle;
			}
			if (!(this.spec.debounce > 0)) {
				this.deliver(context);
				return;
			}
			window.clearTimeout(this.debounceTimer);
			this.debounceTimer = window.setTimeout(() => {
				this.debounceTimer = 0;
				this.deliver(context);
			}, this.spec.debounce);
		}

		run(context) {
			if (!this.keyMatches(context.event)) return;
			if (
				this.spec.self === true &&
				!this.group.els.includes(context.event.target)
			)
				return;
			if (this.spec.once === true) {
				if (this.onceExhausted) return;
				this.onceExhausted = true;
			}
			if (this.spec.prevent === true) context.event.preventDefault();
			if (this.spec.stop === true) context.event.stopPropagation();
			this.schedule(context);
		}
	}

	class GroupPoll {
		constructor(group, interval, callback) {
			if (!(interval > 0))
				throw new TypeError("RootGroup poll intervals must be positive");
			this.group = group;
			this.callback = callback;
			this.destroyed = false;
			this.intervalId = window.setInterval(() => {
				if (document.hidden) return;
				const carrier = this.group.firstLiveRoot();
				if (carrier) this.callback(carrier);
			}, interval);
		}

		syncRoots() {}

		cleanup() {
			if (this.destroyed) return;
			this.destroyed = true;
			window.clearInterval(this.intervalId);
			this.group._bindings.delete(this);
		}
	}

	window.RootGroupSpike = {
		RootGroup,
		onGroup(group, event, modifiers, callback) {
			return group.on(event, modifiers, callback);
		},
		onCitryGroup(group, event, spec, callback) {
			return group.onCitry(event, spec, callback);
		},
	};
})();
