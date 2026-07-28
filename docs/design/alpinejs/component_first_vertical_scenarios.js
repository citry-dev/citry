/* Exercise a real render plus manually assembled graph through the selected adapter. */
(() => {
	function frame() {
		return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
	}

	function snapshot(runtime, pageId, cardId) {
		return {
			child: document.querySelector("[data-vertical-child]").textContent,
			owned: document.querySelector("#vertical-owned").textContent,
			pageRoots: runtime.instanceState.get(pageId).els.map((el) => el.id),
			props: { ...runtime.instanceState.get(cardId).props },
			roots: runtime.instanceState.get(cardId).els.map((el) => el.id),
		};
	}

	async function runComponentFirstVertical({ pageId, cardId }) {
		const [runtime] = await window.ComponentFirstSpikeReady;
		await frame();
		const elsIdentity = runtime.instanceState.get(cardId).els;
		const initial = snapshot(runtime, pageId, cardId);

		document.querySelector("#vertical-card-b").dispatchEvent(new MouseEvent("click", { bubbles: true }));
		document.querySelector("#vertical-card-a").dispatchEvent(new MouseEvent("click", { bubbles: true }));
		await frame();
		const afterEvent = {
			...snapshot(runtime, pageId, cardId),
			events: runtime.eventLog.slice(),
		};

		const source = document.querySelector("#vertical-source");
		const incoming = source.cloneNode(true);
		incoming.setAttribute(
			"x-data",
			"{ owner: 'parent-new', count: 7, theme: 'orange' }",
		);
		incoming.querySelector("#vertical-source-ref").id = "vertical-source-ref-new";
		window.Alpine.morph(source, incoming.outerHTML, { lookahead: false });
		runtime.project();
		runtime.refresh();
		await frame();
		const afterSourceMorph = snapshot(runtime, pageId, cardId);

		const secondRoot = document.querySelector("#vertical-card-b");
		window.Alpine.morph(
			secondRoot,
			secondRoot.outerHTML
				.replace(/^<button/, "<article")
				.replace(/<\/button>$/, "</article>")
				.replaceAll("vertical-card-b", "vertical-card-b-new"),
			{ lookahead: false },
		);
		runtime.project();
		runtime.refresh();
		const newSecondRoot = document.querySelector("#vertical-card-b-new");
		newSecondRoot.dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
		secondRoot.dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
		await frame();
		const afterTargetMorph = {
			...snapshot(runtime, pageId, cardId),
			elsIdentity: runtime.instanceState.get(cardId).els === elsIdentity,
			eventTail: runtime.eventLog.at(-1),
			secondTag: newSecondRoot.tagName,
		};

		runtime.destroy();
		newSecondRoot.dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
		await frame();
		return {
			afterDestroy: {
				eventCount: runtime.eventLog.length,
				props: { ...runtime.instanceState.get(cardId).props },
			},
			afterEvent,
			afterSourceMorph,
			afterTargetMorph,
			initial,
		};
	}

	window.runComponentFirstVertical = runComponentFirstVertical;
})();
