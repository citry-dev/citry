/* Browser scenarios for the throwaway RootGroup prototype. */
(() => {
	const { RootGroup } = window.RootGroupSpike;
	const sleep = (milliseconds) =>
		new Promise((resolve) => window.setTimeout(resolve, milliseconds));

	function fixture(
		markup = '<button class="root"><span class="child">child</span></button>',
	) {
		const host = document.createElement("section");
		host.className = "fixture";
		host.innerHTML = markup;
		document.body.append(host);
		return host;
	}

	function currentTargetName(event, root) {
		if (event.currentTarget === null) return null;
		if (event.currentTarget === root) return "root";
		if (event.currentTarget === window) return "window";
		if (event.currentTarget === document) return "document";
		return event.currentTarget.id || event.currentTarget.tagName.toLowerCase();
	}

	function dispatch(target, type, init = {}) {
		let EventClass = Event;
		if (type.startsWith("key")) EventClass = KeyboardEvent;
		else if (type.startsWith("mouse") || type === "click")
			EventClass = MouseEvent;
		else if (type.startsWith("pointer")) EventClass = PointerEvent;
		const event = new EventClass(type, {
			bubbles: true,
			cancelable: true,
			composed: true,
			...init,
		});
		target.dispatchEvent(event);
		return event;
	}

	function install(mode, root, event, modifiers, callback) {
		if (mode === "alpine") {
			const suffix = modifiers.length ? `.${modifiers.join(".")}` : "";
			return Alpine.bind(root, { [`@${event}${suffix}`]: callback });
		}
		const group = new RootGroup([root]);
		const cleanup = group.on(event, modifiers, (domEvent, carrier) =>
			callback(domEvent, carrier),
		);
		return () => {
			cleanup();
			group.destroy();
		};
	}

	async function composite(mode) {
		const host = fixture(
			'<div class="outer"><button class="root"><span class="child">child</span></button></div>',
		);
		const outer = host.querySelector(".outer");
		const root = host.querySelector(".root");
		const child = host.querySelector(".child");
		let bubbled = 0;
		const callbacks = [];
		outer.addEventListener("click", () => {
			bubbled += 1;
		});
		const cleanup = install(
			mode,
			root,
			"click",
			["self", "prevent", "stop", "once", "debounce", "15ms"],
			(event, carrier) => {
				callbacks.push({
					currentTarget: currentTargetName(event, root),
					carrier: carrier ? carrier === root : true,
					target: event.target === root ? "root" : "child",
				});
			},
		);
		const childEvent = dispatch(child, "click");
		const firstRootEvent = dispatch(root, "click");
		const secondRootEvent = dispatch(root, "click");
		await sleep(30);
		const result = {
			defaultPrevented: [
				childEvent.defaultPrevented,
				firstRootEvent.defaultPrevented,
				secondRootEvent.defaultPrevented,
			],
			bubbled,
			callbacks,
		};
		cleanup();
		host.remove();
		return result;
	}

	async function keyAndThrottle(mode) {
		const host = fixture();
		const root = host.querySelector(".root");
		const keyCallbacks = [];
		const throttleCallbacks = [];
		const cleanKey = install(
			mode,
			root,
			"keyup",
			["ctrl", "enter"],
			(event) => {
				keyCallbacks.push(event.key);
			},
		);
		dispatch(root, "keyup", { key: "Enter" });
		dispatch(root, "keyup", { key: "Escape", ctrlKey: true });
		dispatch(root, "keyup", { key: "Enter", ctrlKey: true });

		const cleanThrottle = install(
			mode,
			root,
			"click",
			["throttle", "15ms"],
			(event) => {
				throttleCallbacks.push(currentTargetName(event, root));
			},
		);
		dispatch(root, "click");
		dispatch(root, "click");
		await sleep(20);
		dispatch(root, "click");
		const result = { keyCallbacks, throttleCallbacks };
		cleanThrottle();
		cleanKey();
		host.remove();
		return result;
	}

	async function outside(mode, modifier) {
		const host = fixture(
			'<button class="root sized">root</button><button class="external">external</button>',
		);
		const root = host.querySelector(".root");
		const external = host.querySelector(".external");
		const callbacks = [];
		const cleanup = install(mode, root, "click", [modifier], (event) => {
			callbacks.push(currentTargetName(event, root));
		});
		dispatch(root, "click");
		dispatch(external, "click");
		root._x_isShown = false;
		dispatch(external, "click");
		root._x_isShown = true;
		root.style.display = "none";
		dispatch(external, "click");
		cleanup();
		host.remove();
		return callbacks;
	}

	async function globals(mode) {
		const host = fixture('<button class="root">root</button>');
		const root = host.querySelector(".root");
		const callbacks = [];
		const cleanWindow = install(
			mode,
			root,
			"rootgroup-window",
			["window"],
			(event) => {
				callbacks.push(currentTargetName(event, root));
			},
		);
		const cleanDocument = install(
			mode,
			root,
			"rootgroup-document",
			["document"],
			(event) => {
				callbacks.push(currentTargetName(event, root));
			},
		);
		window.dispatchEvent(new CustomEvent("rootgroup-window"));
		document.dispatchEvent(new CustomEvent("rootgroup-document"));
		const result = callbacks.slice();
		cleanDocument();
		cleanWindow();
		host.remove();
		return result;
	}

	async function namesSubmitAndOptions(mode) {
		const host = fixture(
			'<form class="root"><button class="child" type="submit">submit</button></form>',
		);
		const root = host.querySelector(".root");
		const names = [];
		const options = [];
		const captureOrder = [];
		const originalAdd = root.addEventListener;
		root.addEventListener = function (event, callback, listenerOptions) {
			if (event === "options-probe") {
				options.push({
					capture: listenerOptions.capture === true,
					passive: listenerOptions.passive === true,
				});
			}
			return originalAdd.call(this, event, callback, listenerOptions);
		};
		const cleanDot = install(mode, root, "custom-event", ["dot"], () =>
			names.push("dot"),
		);
		const cleanCamel = install(mode, root, "custom-event", ["camel"], () =>
			names.push("camel"),
		);
		const cleanOptions = install(
			mode,
			root,
			"options-probe",
			["capture", "passive"],
			() => {},
		);
		host.addEventListener(
			"capture-order",
			() => captureOrder.push("outer-capture"),
			true,
		);
		host.addEventListener("capture-order", () =>
			captureOrder.push("outer-bubble"),
		);
		root
			.querySelector(".child")
			.addEventListener("capture-order", () => captureOrder.push("target"));
		const cleanCapture = install(mode, root, "capture-order", ["capture"], () =>
			captureOrder.push("binding"),
		);
		root.dispatchEvent(new CustomEvent("custom.event"));
		root.dispatchEvent(new CustomEvent("customEvent"));
		dispatch(root.querySelector(".child"), "capture-order");

		const submitOrder = [];
		root._x_pendingModelUpdates = [() => submitOrder.push("flush")];
		const cleanSubmit = install(mode, root, "submit", ["prevent"], () =>
			submitOrder.push("callback"),
		);
		dispatch(root, "submit");

		let passiveFalseClicks = 0;
		const cleanPassiveFalse = install(
			mode,
			root,
			"click",
			["passive", "false"],
			() => {
				passiveFalseClicks += 1;
			},
		);
		dispatch(root, "click");
		const result = {
			names,
			options,
			captureOrder,
			submitOrder,
			passiveFalseClicks,
		};
		cleanPassiveFalse();
		cleanSubmit();
		cleanCapture();
		cleanOptions();
		cleanCamel();
		cleanDot();
		root.addEventListener = originalAdd;
		host.remove();
		return result;
	}

	async function runDifferential() {
		const result = {};
		for (const mode of ["alpine", "group"]) {
			result[mode] = {
				composite: await composite(mode),
				keyAndThrottle: await keyAndThrottle(mode),
				outside: await outside(mode, "outside"),
				away: await outside(mode, "away"),
				globals: await globals(mode),
				namesSubmitAndOptions: await namesSubmitAndOptions(mode),
			};
		}
		return result;
	}

	async function cleanupDivergence() {
		const result = {};
		for (const mode of ["alpine", "group"]) {
			const host = fixture();
			const root = host.querySelector(".root");
			let callbacks = 0;
			const cleanup = install(
				mode,
				root,
				"rootgroup-cleanup",
				["debounce", "15ms"],
				() => {
					callbacks += 1;
				},
			);
			dispatch(root, "rootgroup-cleanup");
			cleanup();
			await sleep(25);
			result[mode] = callbacks;
			host.remove();
		}
		return result;
	}

	function twoRootFixture() {
		const host = fixture(`
      <div class="ancestor">
        <button id="a" class="root sized"><span id="a-child">A child</span></button>
        <button id="b" class="root sized"><span id="b-child">B child</span></button>
        <button id="gap" class="sized">gap</button>
      </div>
    `);
		return {
			host,
			ancestor: host.querySelector(".ancestor"),
			a: host.querySelector("#a"),
			b: host.querySelector("#b"),
			gap: host.querySelector("#gap"),
		};
	}

	async function multiRootCore() {
		const { host, ancestor, a, b, gap } = twoRootFixture();
		const group = new RootGroup([a, b]);
		const direct = [];
		const self = [];
		const stopped = [];
		let ancestorBubbles = 0;
		group.on("rootgroup-direct", [], (event, carrier) => {
			direct.push({
				target: event.target.id,
				current: event.currentTarget.id,
				carrier: carrier.id,
			});
		});
		group.on("rootgroup-self", ["self"], (_event, carrier) =>
			self.push(carrier.id),
		);
		group.on("rootgroup-stop", ["stop", "prevent"], (_event, carrier) =>
			stopped.push(`first:${carrier.id}`),
		);
		group.on("rootgroup-stop", [], (_event, carrier) =>
			stopped.push(`second:${carrier.id}`),
		);
		ancestor.addEventListener("rootgroup-stop", () => {
			ancestorBubbles += 1;
		});

		dispatch(a, "rootgroup-direct");
		dispatch(b.querySelector("#b-child"), "rootgroup-direct");
		dispatch(a.querySelector("#a-child"), "rootgroup-self");
		dispatch(a, "rootgroup-self");
		dispatch(b, "rootgroup-self");
		const stopEvent = dispatch(b, "rootgroup-stop");

		const once = [];
		group.on("rootgroup-once", ["once"], (_event, carrier) =>
			once.push(carrier.id),
		);
		dispatch(a, "rootgroup-once");
		dispatch(b, "rootgroup-once");

		const debounce = [];
		group.on("rootgroup-debounce", ["debounce", "15ms"], (event, carrier) => {
			debounce.push({ carrier: carrier.id, current: event.currentTarget });
		});
		dispatch(a, "rootgroup-debounce");
		dispatch(b, "rootgroup-debounce");
		await sleep(25);

		const throttle = [];
		group.on("rootgroup-throttle", ["throttle", "15ms"], (_event, carrier) =>
			throttle.push(carrier.id),
		);
		dispatch(a, "rootgroup-throttle");
		dispatch(b, "rootgroup-throttle");
		await sleep(20);
		dispatch(b, "rootgroup-throttle");

		const outside = [];
		group.on("click", ["outside"], (event, carrier) => {
			outside.push({
				target: event.target.id,
				current: currentTargetName(event, carrier),
				carrier: carrier.id,
			});
		});
		dispatch(a, "click");
		dispatch(b.querySelector("#b-child"), "click");
		dispatch(gap, "click");
		a._x_isShown = false;
		dispatch(gap, "click");
		b._x_isShown = false;
		dispatch(gap, "click");
		a._x_isShown = true;
		b._x_isShown = true;

		const bothTiming = [];
		group.on(
			"rootgroup-both-timing",
			["debounce", "10ms", "throttle", "30ms"],
			(_event, carrier) => bothTiming.push(carrier.id),
		);
		dispatch(a, "rootgroup-both-timing");
		dispatch(b, "rootgroup-both-timing");
		await sleep(15);
		await sleep(20);
		dispatch(b, "rootgroup-both-timing");
		await sleep(15);

		let windowCount = 0;
		let documentCount = 0;
		group.on("rootgroup-global", ["window"], () => {
			windowCount += 1;
		});
		group.on("rootgroup-global", ["document"], () => {
			documentCount += 1;
		});
		window.dispatchEvent(new CustomEvent("rootgroup-global"));
		document.dispatchEvent(new CustomEvent("rootgroup-global"));

		const sameEvent = new Event("rootgroup-redispatch", { bubbles: true });
		let redispatchCount = 0;
		group.on("rootgroup-redispatch", [], () => {
			redispatchCount += 1;
		});
		a.dispatchEvent(sameEvent);
		a.dispatchEvent(sameEvent);

		const focus = [];
		group.on("focus", [], (_event, carrier) =>
			focus.push(`focus:${carrier.id}`),
		);
		group.on("blur", [], (_event, carrier) => focus.push(`blur:${carrier.id}`));
		a.focus();
		b.focus();

		const asyncCurrentTarget = [];
		group.on("rootgroup-async", [], async (event, carrier) => {
			asyncCurrentTarget.push({
				phase: "sync",
				current: event.currentTarget.id,
				carrier: carrier.id,
			});
			await Promise.resolve();
			asyncCurrentTarget.push({
				phase: "async",
				current: event.currentTarget,
				carrier: carrier.id,
			});
		});
		dispatch(b, "rootgroup-async");
		await sleep(0);

		let sharedPhysicalRoot = 0;
		const secondLogicalGroup = new RootGroup([b]);
		group.on("rootgroup-shared-physical", [], () => {
			sharedPhysicalRoot += 1;
		});
		secondLogicalGroup.on("rootgroup-shared-physical", [], () => {
			sharedPhysicalRoot += 1;
		});
		dispatch(b, "rootgroup-shared-physical");

		const result = {
			direct,
			self,
			stopped,
			stopDefaultPrevented: stopEvent.defaultPrevented,
			ancestorBubbles,
			once,
			debounce,
			throttle,
			bothTiming,
			outside,
			globals: { windowCount, documentCount },
			redispatchCount,
			focus,
			asyncCurrentTarget,
			sharedPhysicalRoot,
		};
		secondLogicalGroup.destroy();
		group.destroy();
		host.remove();
		return result;
	}

	async function dynamicRootsAndCleanup() {
		const { host, a, b, gap } = twoRootFixture();
		gap.id = "c";
		const c = gap;
		const group = new RootGroup([a, b]);
		const stableEls = group.els;
		const globalAnchors = [];
		group.on("rootgroup-anchor", ["document"], (_event, carrier) =>
			globalAnchors.push(carrier.id),
		);
		document.dispatchEvent(new CustomEvent("rootgroup-anchor"));
		const poll = [];
		await new Promise((resolve) => {
			const stopPoll = group.poll(10, (carrier) => {
				poll.push(carrier.id);
				if (poll.length === 1) group.removeRoot(a);
				if (poll.length === 2) group.addRoot(a, 0);
				if (poll.length === 3) {
					stopPoll();
					resolve();
				}
			});
		});
		await sleep(15);
		const dynamic = [];
		group.on("rootgroup-dynamic", ["throttle", "15ms"], (_event, carrier) =>
			dynamic.push(carrier.id),
		);
		dispatch(a, "rootgroup-dynamic");
		group.removeRoot(a);
		document.dispatchEvent(new CustomEvent("rootgroup-anchor"));
		group.addRoot(c);
		dispatch(c, "rootgroup-dynamic");
		await sleep(20);
		dispatch(c, "rootgroup-dynamic");

		const pendingRemovedCarrier = [];
		group.on(
			"rootgroup-pending-removed",
			["debounce", "15ms"],
			(_event, carrier) => {
				pendingRemovedCarrier.push(carrier.id);
			},
		);
		dispatch(b, "rootgroup-pending-removed");
		group.removeRoot(b);
		await sleep(25);

		const survivorPending = [];
		group.on(
			"rootgroup-pending-survivor",
			["debounce", "15ms"],
			(_event, carrier) => {
				survivorPending.push(carrier.id);
			},
		);
		dispatch(c, "rootgroup-pending-survivor");
		const d = document.createElement("button");
		d.id = "d";
		d.className = "sized";
		c.after(d);
		group.addRoot(d, 0);
		await sleep(25);

		const destroyedPending = [];
		group.on("rootgroup-destroyed", ["debounce", "15ms"], () =>
			destroyedPending.push("fired"),
		);
		dispatch(c, "rootgroup-destroyed");
		const beforeDestroyEls = stableEls.map((root) => root.id);
		group.destroy();
		await sleep(25);
		const result = {
			stableArrayIdentity: stableEls === group.els,
			beforeDestroyEls,
			afterDestroyLength: stableEls.length,
			dynamic,
			globalAnchors,
			poll,
			pendingRemovedCarrier,
			survivorPending,
			destroyedPending,
		};
		host.remove();
		return result;
	}

	async function detachedLifecycle() {
		const host = document.createElement("section");
		host.innerHTML = '<button id="detached-root" class="sized">root</button>';
		const root = host.querySelector("#detached-root");
		const group = new RootGroup([root]);
		let direct = 0;
		let global = 0;
		group.on("rootgroup-detached-direct", [], () => {
			direct += 1;
		});
		group.on("rootgroup-detached-global", ["window"], () => {
			global += 1;
		});
		dispatch(root, "rootgroup-detached-direct");
		window.dispatchEvent(new CustomEvent("rootgroup-detached-global"));
		const whileDetached = { direct, global };

		document.body.append(host);
		dispatch(root, "rootgroup-detached-direct");
		window.dispatchEvent(new CustomEvent("rootgroup-detached-global"));
		const afterConnect = { direct, global };

		host.remove();
		dispatch(root, "rootgroup-detached-direct");
		window.dispatchEvent(new CustomEvent("rootgroup-detached-global"));
		const afterDisconnect = { direct, global };

		document.body.append(host);
		dispatch(root, "rootgroup-detached-direct");
		window.dispatchEvent(new CustomEvent("rootgroup-detached-global"));
		const afterReconnect = { direct, global };

		group.destroy();
		host.remove();
		return { whileDetached, afterConnect, afterDisconnect, afterReconnect };
	}

	async function boundariesAndShadow() {
		const { host, a, b, gap } = twoRootFixture();
		const group = new RootGroup([a, b]);
		const transitions = [];
		for (const type of [
			"mouseenter",
			"mouseleave",
			"pointerenter",
			"pointerleave",
		]) {
			group.on(type, [], (_event, carrier) =>
				transitions.push(`${type}:${carrier.id}`),
			);
		}
		dispatch(a, "mouseenter", { relatedTarget: null });
		dispatch(a, "mouseleave", { relatedTarget: b });
		dispatch(b, "mouseenter", { relatedTarget: a });
		dispatch(b, "mouseleave", { relatedTarget: gap });
		dispatch(a, "pointerenter", { relatedTarget: null });
		dispatch(a, "pointerleave", { relatedTarget: b });
		dispatch(b, "pointerenter", { relatedTarget: a });
		dispatch(b, "pointerleave", { relatedTarget: gap });

		const shadowHost = document.createElement("div");
		shadowHost.id = "shadow-host";
		const shadow = shadowHost.attachShadow({ mode: "open" });
		shadow.innerHTML =
			'<button id="shadow-root" class="sized"><span id="shadow-child">inside</span></button>';
		host.append(shadowHost);
		const shadowRoot = shadow.querySelector("#shadow-root");
		const shadowChild = shadow.querySelector("#shadow-child");
		const shadowGroup = new RootGroup([shadowRoot]);
		const shadowOutside = [];
		shadowGroup.on("click", ["outside"], (event) =>
			shadowOutside.push(event.target.id),
		);
		dispatch(shadowChild, "click");
		dispatch(gap, "click");

		const result = { transitions, shadowOutside };
		shadowGroup.destroy();
		group.destroy();
		host.remove();
		return result;
	}

	async function citrySubset() {
		const { host, ancestor, a, b } = twoRootFixture();
		const group = new RootGroup([a, b]);
		const keySelfOnce = [];
		group.onCitry(
			"keyup",
			{ key: "enter", self: true, once: true },
			(event, carrier) =>
				keySelfOnce.push({ key: event.key, carrier: carrier.id }),
		);
		dispatch(a.querySelector("#a-child"), "keyup", { key: "Enter" });
		dispatch(a, "keyup", { key: "Escape" });
		dispatch(b, "keyup", { key: "Enter" });
		dispatch(a, "keyup", { key: "Enter" });

		const debounce = [];
		group.onCitry(
			"rootgroup-citry-debounce",
			{ debounce: 15 },
			(event, carrier) => {
				debounce.push({ carrier: carrier.id, current: event.currentTarget });
			},
		);
		dispatch(a, "rootgroup-citry-debounce");
		dispatch(b, "rootgroup-citry-debounce");
		await sleep(25);

		const throttle = [];
		group.onCitry(
			"rootgroup-citry-throttle",
			{ throttle: 15 },
			(_event, carrier) => {
				throttle.push(carrier.id);
			},
		);
		dispatch(a, "rootgroup-citry-throttle");
		dispatch(b, "rootgroup-citry-throttle");
		await sleep(20);
		dispatch(b, "rootgroup-citry-throttle");

		let bubbled = 0;
		ancestor.addEventListener("rootgroup-citry-stop", () => {
			bubbled += 1;
		});
		let stopped = 0;
		group.onCitry("rootgroup-citry-stop", { prevent: true, stop: true }, () => {
			stopped += 1;
		});
		const stoppedEvent = dispatch(b, "rootgroup-citry-stop");
		const result = {
			keySelfOnce,
			debounce,
			throttle,
			stopped,
			bubbled,
			defaultPrevented: stoppedEvent.defaultPrevented,
		};
		group.destroy();
		host.remove();
		return result;
	}

	window.runRootGroupScenarios = async () => {
		return {
			alpineVersion: Alpine.version,
			differential: await runDifferential(),
			cleanupDivergence: await cleanupDivergence(),
			multiRootCore: await multiRootCore(),
			dynamicRootsAndCleanup: await dynamicRootsAndCleanup(),
			detachedLifecycle: await detachedLifecycle(),
			boundariesAndShadow: await boundariesAndShadow(),
			citrySubset: await citrySubset(),
		};
	};

	window.setupRootGroupPointerProbe = (capture = false) => {
		const { host, a, b } = twoRootFixture();
		host.id = "pointer-probe";
		a.style.position = "absolute";
		a.style.left = "100px";
		a.style.top = "100px";
		a.style.width = "80px";
		a.style.height = "50px";
		b.style.position = "absolute";
		b.style.left = "260px";
		b.style.top = "100px";
		b.style.width = "80px";
		b.style.height = "50px";
		const group = new RootGroup([a, b]);
		const events = [];
		for (const type of [
			"mouseenter",
			"mouseleave",
			"pointerenter",
			"pointerleave",
		]) {
			group.on(type, [], (event, carrier) => {
				events.push({
					type,
					carrier: carrier.id,
					related: event.relatedTarget?.id ? event.relatedTarget.id : null,
				});
			});
		}
		if (capture) {
			a.addEventListener("pointerdown", (event) =>
				a.setPointerCapture(event.pointerId),
			);
			a.addEventListener("gotpointercapture", () =>
				events.push({ type: "gotpointercapture", carrier: "a", related: null }),
			);
			a.addEventListener("lostpointercapture", () =>
				events.push({
					type: "lostpointercapture",
					carrier: "a",
					related: null,
				}),
			);
		}
		window.__rootGroupPointerProbe = { group, host, events };
	};

	window.readRootGroupPointerProbe = () => {
		const probe = window.__rootGroupPointerProbe;
		const result = probe.events.slice();
		probe.group.destroy();
		probe.host.remove();
		delete window.__rootGroupPointerProbe;
		return result;
	};
})();
