/* Research-only scenarios for component_first_harness.py. */
(() => {
	function waitForEffects() {
		return new Promise((resolve) => queueMicrotask(() => queueMicrotask(resolve)));
	}

	function alpineValue(el, expression) {
		return globalThis.Alpine.evaluate(el, expression);
	}

	function removeRootlessRange(id) {
		const startText = `citry-start:${id}`;
		const endText = `citry-end:${id}`;
		const walker = document.createTreeWalker(document, NodeFilter.SHOW_COMMENT);
		let start = null;
		let end = null;
		for (let node = walker.nextNode(); node; node = walker.nextNode()) {
			if (node.data === startText) start = node;
			if (node.data === endText) end = node;
		}
		if (!start || !end) throw new Error(`Missing rootless range ${id}`);
		for (let node = start; node; ) {
			const next = node.nextSibling;
			node.remove();
			if (node === end) break;
			node = next;
		}
	}

	function descriptorRekeyControl() {
		const token = "descriptor-rekey-control";
		const sourceOne = document.createElement("section");
		sourceOne.id = "descriptor-source-one";
		sourceOne.innerHTML = `<!--citry-fill-source:${token}-->`;
		const targetOne = document.createElement("div");
		targetOne.id = "descriptor-target-one";
		document.body.append(sourceOne, targetOne);
		const descriptor = globalThis.SlotsScopeSpike.descriptorFor(token, targetOne);

		const sourceTwo = document.createElement("section");
		sourceTwo.id = "descriptor-source-two";
		sourceTwo.innerHTML = `<!--citry-fill-source:${token}-->`;
		sourceOne.replaceWith(sourceTwo);
		globalThis.SlotsScopeSpike.refreshDescriptor(descriptor, targetOne);

		const targetTwo = document.createElement("div");
		targetTwo.id = "descriptor-target-two";
		sourceTwo.after(targetTwo, sourceOne);
		sourceOne.after(targetOne);
		const sourceTwoDescriptor = globalThis.SlotsScopeSpike.descriptorFor(token, targetTwo);
		const sourceOneDescriptor = globalThis.SlotsScopeSpike.descriptorFor(token, targetOne);
		const result = {
			distinct: sourceOneDescriptor !== descriptor,
			sourceOne: sourceOneDescriptor.carrier.id,
			sourceTwo: sourceTwoDescriptor.carrier.id,
		};
		sourceOne.remove();
		sourceTwo.remove();
		targetOne.remove();
		targetTwo.remove();
		return result;
	}

	async function runGraphFirst(runtime) {
		const source = document.getElementById("a-source");
		const childA = document.getElementById("a-child-a");
		const childB = document.getElementById("a-child-b");
		const outer = document.getElementById("a-outer-fill");
		const initialEls = runtime.instanceState.get("a-child").els;

		const initial = {
			outerText: document.getElementById("a-outer-text").textContent,
			fallbackText: document.getElementById("a-child-fallback").textContent,
			nestedText: document.getElementById("a-nested-text").textContent,
			ifText: document.getElementById("a-if-generated").textContent,
			teleportText: document.getElementById("a-teleported").textContent,
			sharedText: document.getElementById("a-shared").textContent,
			sharedInstances: document
				.getElementById("a-shared")
				.getAttribute("data-cf-instances-graph-a"),
			outerOwner: alpineValue(outer, "owner"),
			outerParentOnly: alpineValue(outer, "parentOnly"),
			outerChildOnlyType: alpineValue(outer, "typeof childOnly"),
			outerRoot: alpineValue(outer, "$root.id"),
			outerSameRef: alpineValue(outer, "$refs.same.id"),
			sourceFillRef: alpineValue(source, "$refs.fillOwned.id"),
			childRoots: initialEls.map((el) => el.id),
			props: { ...runtime.instanceState.get("a-child").props },
		};

		childB.dispatchEvent(new MouseEvent("click", { bubbles: true }));
		childA.dispatchEvent(new MouseEvent("click", { bubbles: true }));
		await waitForEffects();
		const afterGroupedEvent = {
			count: alpineValue(source, "count"),
			props: { ...runtime.instanceState.get("a-child").props },
			events: runtime.eventLog.slice(),
		};

		const propsOnlyInitial = {
			...runtime.instanceState.get("a-props-only-target").props,
		};
		const propsOnlySource = document.getElementById("a-props-only-source");
		const propsOnlyReplacement = document.createElement("section");
		propsOnlyReplacement.id = "a-props-only-source";
		propsOnlyReplacement.setAttribute("data-cf-region", "a-props-only-source-root");
		propsOnlyReplacement.setAttribute("x-data", "{ count: 8, theme: 'amber' }");
		propsOnlyReplacement.innerHTML = "<!--citry-fill-source:a-props-only-->";
		propsOnlySource.replaceWith(propsOnlyReplacement);
		runtime.project();
		globalThis.Alpine.initTree(propsOnlyReplacement);
		runtime.refresh();
		await waitForEffects();
		const propsOnly = {
			initial: propsOnlyInitial,
			replaced: { ...runtime.instanceState.get("a-props-only-target").props },
		};

		const rootless = runtime.rootlessState.get("a-rootless");
		const rootlessElsIdentity = rootless.els;
		const rootlessInitial = {
			initialized: rootless.initialized,
			els: rootless.els.map((el) => el.id),
			scopeOwner: rootless.scope.owner,
		};
		rootless.replace('<span id="a-rootless-element">rooted</span>');
		const rootlessRooted = {
			identity: rootless.els === rootlessElsIdentity,
			els: rootless.els.map((el) => el.id),
		};
		rootless.replace("plain text");
		const rootlessText = {
			identity: rootless.els === rootlessElsIdentity,
			length: rootless.els.length,
		};

		const mirror = runtime.rootlessState.get("a-mirror");
		const mirrorElsIdentity = mirror.els;
		const mirrorBefore = {
			regions: mirror._liveRegions().length,
			els: mirror.els.map((el) => el.id),
		};
		removeRootlessRange("a-mirror-one");
		await new Promise((resolve) => setTimeout(resolve, 0));
		runtime.rootlessRegistry.reconcile();
		const mirrorAfter = {
			destroyed: mirror.destroyed,
			identity: mirror.els === mirrorElsIdentity,
			regions: mirror._liveRegions().length,
			els: mirror.els.map((el) => el.id),
		};

		const replacement = document.createElement("section");
		replacement.id = "a-source";
		replacement.setAttribute("data-cf-region", "a-source-root");
		replacement.setAttribute(
			"x-data",
			"{ owner: 'a-parent-new', parentOnly: 'P2', count: 10, theme: 'green', show: true }",
		);
		replacement.setAttribute("x-id", "['shared']");
		replacement.innerHTML = `
			<span id="a-source-ref-new" x-ref="same"></span>
			<!--citry-fill-source:a-parent-->
		`;
		source.replaceWith(replacement);
		runtime.project();
		globalThis.Alpine.initTree(replacement);
		runtime.refresh();
		await waitForEffects();
		const afterSourceReplacement = {
			outerText: document.getElementById("a-outer-text").textContent,
			owner: alpineValue(outer, "owner"),
			root: alpineValue(outer, "$root.id"),
			ref: alpineValue(outer, "$refs.same.id"),
			props: { ...runtime.instanceState.get("a-child").props },
		};

		const oldChildB = document.getElementById("a-child-b");
		globalThis.Alpine.morph(
			oldChildB,
			`<article
				id="a-child-b-new"
				data-cf-region="a-child-roots"
				data-cf-root="graph-a"
				data-cf-instances-graph-a="a-child"
			>new child root</article>`,
		);
		runtime.refresh();
		const newChildB = document.getElementById("a-child-b-new");
		newChildB.dispatchEvent(new MouseEvent("click", { bubbles: true }));
		await waitForEffects();
		const afterTargetMorph = {
			elsIdentity: runtime.instanceState.get("a-child").els === initialEls,
			roots: initialEls.map((el) => el.id),
			count: alpineValue(replacement, "count"),
			eventTail: runtime.eventLog.at(-1),
		};

		return {
			initial,
			afterGroupedEvent,
			propsOnly,
			rootlessInitial,
			rootlessRooted,
			rootlessText,
			mirrorBefore,
			mirrorAfter,
			afterSourceReplacement,
			afterTargetMorph,
		};
	}

	async function runCitryDirectives(runtime) {
		const source = document.getElementById("b-source");
		const initial = {
			citryText: document.getElementById("b-citry-text").textContent,
			alpineControl: document.getElementById("b-alpine-control").textContent,
			props: { ...runtime.instanceState.get("b-child").props },
			attributes: {
				props: document.getElementById("b-child").getAttribute("$c-props"),
				text: document.getElementById("b-citry-text").getAttribute("$c-text"),
				on: document.getElementById("b-citry-button").getAttribute("$c-on:click"),
			},
		};

		document.getElementById("b-citry-button").dispatchEvent(new MouseEvent("click", { bubbles: true }));
		await waitForEffects();
		const afterEvent = {
			citryText: document.getElementById("b-citry-text").textContent,
			alpineControl: document.getElementById("b-alpine-control").textContent,
			count: alpineValue(source, "count"),
			props: { ...runtime.instanceState.get("b-child").props },
			events: runtime.eventLog.slice(),
		};

		const replacement = document.createElement("section");
		replacement.id = "b-source";
		replacement.setAttribute("data-cf-region", "b-source-root");
		replacement.setAttribute("x-data", "{ owner: 'b-parent-new', count: 7, theme: 'orange' }");
		replacement.innerHTML = "<!--citry-fill-source:b-parent-->";
		source.replaceWith(replacement);
		globalThis.Alpine.initTree(replacement);
		runtime.refreshSources();
		await waitForEffects();
		const afterSourceReplacement = {
			citryText: document.getElementById("b-citry-text").textContent,
			alpineControl: document.getElementById("b-alpine-control").textContent,
			props: { ...runtime.instanceState.get("b-child").props },
		};

		return { initial, afterEvent, afterSourceReplacement };
	}

	function validationControls() {
		const outcomes = [];
		for (const [name, manifest] of [
			["version", { version: 2, runtimeId: "bad", instances: [] }],
			[
				"duplicate-instance",
				{
					version: 1,
					runtimeId: "bad",
					instances: [{ id: "i" }, { id: "i" }],
				},
			],
			[
				"dangling-region",
				{
					version: 1,
					runtimeId: "bad",
					instances: [{ id: "i", regionIds: ["missing"] }],
				},
			],
			[
				"lexical-cycle",
				{
					version: 1,
					runtimeId: "bad",
					instances: [],
					locations: [
						{ id: "a", lexicalParentLocationId: "b" },
						{ id: "b", lexicalParentLocationId: "a" },
					],
				},
			],
			[
				"render-cycle",
				{
					version: 1,
					runtimeId: "bad",
					instances: [
						{ id: "a", renderParentId: "b" },
						{ id: "b", renderParentId: "a" },
					],
				},
			],
			[
				"provide-cycle",
				{
					version: 1,
					runtimeId: "bad",
					instances: [
						{ id: "a", provideParentRenderId: "b" },
						{ id: "b", provideParentRenderId: "a" },
					],
				},
			],
		]) {
			try {
				new globalThis.ComponentFirstSpike.GraphModel(manifest);
				outcomes.push({ name, error: null });
			} catch (error) {
				outcomes.push({ name, error: error.message });
			}
		}
		return outcomes;
	}

	globalThis.runComponentFirstScenarios = async function () {
		const runtimes = await globalThis.ComponentFirstSpikeReady;
		const graph = runtimes.find((runtime) => runtime.model.runtimeId === "graph-a");
		const directives = runtimes.find((runtime) => runtime.model.runtimeId === "directives-b");
		return {
			alpineVersion: globalThis.Alpine.version,
			descriptorRekey: descriptorRekeyControl(),
			graph: await runGraphFirst(graph),
			directives: await runCitryDirectives(directives),
			validation: validationControls(),
		};
	};
})();
