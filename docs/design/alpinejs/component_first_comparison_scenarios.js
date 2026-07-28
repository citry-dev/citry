/* Compare both component-first engines against one DOM and one manifest. */
(() => {
	function frame() {
		return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
	}

	function snapshot(runtime) {
		return {
			control: document.querySelector("#cmp-control").textContent,
			owned: document.querySelector("#cmp-owned").textContent,
			props: { ...runtime.instanceState.get("cmp-child").props },
		};
	}

	async function runComparisonScenario() {
		const [runtime] = await window.ComponentFirstSpikeReady;
		await frame();
		const initial = snapshot(runtime);

		document.querySelector("#cmp-child-b").dispatchEvent(new MouseEvent("click", { bubbles: true }));
		document.querySelector("#cmp-child-a").dispatchEvent(new MouseEvent("click", { bubbles: true }));
		await frame();
		const afterEvent = {
			...snapshot(runtime),
			events: runtime.eventLog.slice(),
		};

		const source = document.querySelector("#cmp-source");
		window.Alpine.morph(
			source,
			`<section
				id="cmp-source"
				data-cf-region="cmp-source-root"
				x-data="{ owner: 'parent-new', count: 9, theme: 'orange' }"
			>
				<span id="cmp-source-ref-new" x-ref="same"></span>
				<!--citry-fill-source:cmp-parent-->
			</section>`,
			{ lookahead: false },
		);
		if (runtime instanceof window.ComponentFirstSpike.GraphFirstAlpineRuntime) {
			runtime.project();
			runtime.refresh();
		} else {
			runtime.refreshSources();
		}
		await frame();
		const afterSourceReplacement = snapshot(runtime);

		const liveSource = document.querySelector("#cmp-source");
		const iterations = 1000;
		const started = performance.now();
		for (let index = 0; index < iterations; index += 1) {
			if (runtime instanceof window.ComponentFirstSpike.GraphFirstAlpineRuntime) {
				window.Alpine.evaluateRaw(liveSource, "owner");
			} else {
				runtime.evaluate("cmp-parent-location", "owner");
			}
		}
		const evaluationMilliseconds = performance.now() - started;

		runtime.destroy();
		liveSource._x_dataStack[0].owner = "after-destroy";
		liveSource._x_dataStack[0].count = 20;
		document.querySelector("#cmp-child-a").dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
		const futureRoot = document.createElement("div");
		futureRoot.id = "cmp-future-root";
		futureRoot.setAttribute("data-cf-root", "comparison");
		futureRoot.setAttribute("data-cf-instances-comparison", "cmp-child");
		futureRoot.setAttribute("x-text", "typeof owner");
		document.body.append(futureRoot);
		window.Alpine.initTree(futureRoot);
		await frame();
		const afterDestroy = {
			owned: document.querySelector("#cmp-owned").textContent,
			events: runtime.eventLog.slice(),
			props: { ...runtime.instanceState.get("cmp-child").props },
			futureRoot: futureRoot.textContent,
			sourceCount: liveSource._x_dataStack[0].count,
		};

		return {
			afterDestroy,
			afterEvent,
			afterSourceReplacement,
			evaluationMilliseconds,
			initial,
			iterations,
			mode: runtime.constructor.name,
		};
	}

	window.runComponentFirstComparison = runComparisonScenario;
})();
