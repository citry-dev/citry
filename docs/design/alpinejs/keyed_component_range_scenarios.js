/* Browser scenarios for the disposable keyed-component-range experiment. */
(() => {
	const {
		KeyedComponentRangeRegistry,
		inertIslandControl,
		nodesBetween,
		rangeMarkup,
	} = window.KeyedComponentRangeSpike;

	const settle = async () => {
		await Promise.resolve();
		await Alpine.nextTick();
		await new Promise((resolve) => window.setTimeout(resolve, 0));
		await Promise.resolve();
	};

	function rec(id, classId, morphKey, parentId = null) {
		return { id, classId, morphKey, parentId };
	}

	function fixture(markup, tag = "section") {
		const host = document.createElement(tag);
		host.className = "keyed-component-range-fixture";
		host.innerHTML = markup;
		document.body.append(host);
		return host;
	}

	function removeFixture(host) {
		host.remove();
	}

	function text(instance) {
		return nodesBetween(instance.start, instance.end)
			.map((node) => node.textContent)
			.join("");
	}

	function residue(host) {
		return {
			holders: host.querySelectorAll("template[data-citry-vrange-holder]").length,
			sentinels: host.querySelectorAll("template[data-citry-vrange-sentinel]").length,
		};
	}

	async function inertIslandNegativeControl() {
		const host = fixture(
			rangeMarkup(
				"control-root",
				rangeMarkup(
					"control-child-old",
					'<span data-citry-key="root">old child bytes</span>',
				),
			),
		);
		const result = inertIslandControl(
			host,
			"control-root",
			"control-child-old",
			rangeMarkup(
				"control-root-fresh",
				rangeMarkup(
					"control-child-new",
					'<span data-citry-key="root">fresh server bytes</span>',
				),
			),
			"control-child-new",
		);
		removeFixture(host);
		return {
			freshDiscarded: !result.includes("fresh server bytes"),
			result,
		};
	}

	async function stationaryFreshContentAndBrowserState() {
		const child = rangeMarkup(
			"stationary-child-old",
			'<article data-citry-key="child-root" data-server="old" x-data="{ draft: \'initial\' }" x-range-probe="stationary">' +
				'<input data-citry-key="input" x-model="draft">' +
				'<span class="server-label">old label</span>' +
				'<div class="scroller" style="height:20px;overflow:auto"><div style="height:200px"></div></div>' +
				'<iframe srcdoc="<p>stable</p>"></iframe>' +
				"</article>",
		);
		const host = fixture(rangeMarkup("stationary-root-old", `<h2>before</h2>${child}<p>tail</p>`));
		const registry = new KeyedComponentRangeRegistry(host, [
			rec("stationary-root-old", "Page", null),
			rec("stationary-child-old", "Editor", "row-1", "stationary-root-old"),
		]);
		await settle();
		const oldChild = registry.instance("stationary-child-old");
		const oldAnchor = oldChild.anchor;
		const oldStart = oldChild.start;
		const oldEnd = oldChild.end;
		const oldRoot = host.querySelector("article");
		const input = oldRoot.querySelector("input");
		const scroller = oldRoot.querySelector(".scroller");
		const frame = oldRoot.querySelector("iframe");
		const scope = oldRoot._x_dataStack[0];
		input.value = "client draft";
		input.dispatchEvent(new Event("input", { bubbles: true }));
		input.focus();
		input.setSelectionRange(2, 7);
		scroller.scrollTop = 91;
		frame.contentWindow.__citryStamp = "kept";
		oldAnchor.state.logical = "state-kept";
		await settle();

		registry.morph(
			"stationary-root-old",
			rangeMarkup(
				"stationary-root-new",
				'<h2>after</h2>' +
					rangeMarkup(
						"stationary-child-new",
						'<article data-citry-key="child-root" data-server="fresh" x-data="{ draft: \'initial\' }" x-range-probe="stationary">' +
							'<input data-citry-key="input" x-model="draft">' +
							'<span class="server-label">fresh label</span>' +
							'<div class="scroller" style="height:20px;overflow:auto"><div style="height:200px"></div></div>' +
							'<iframe srcdoc="<p>stable</p>"></iframe>' +
							"</article>",
					) +
					"<p>tail fresh</p>",
			),
			[
				rec("stationary-root-new", "Page", null),
				rec("stationary-child-new", "Editor", "row-1", "stationary-root-new"),
			],
			"stationary-root-new",
		);
		await settle();
		const freshChild = registry.instance("stationary-child-new");
		const freshRoot = host.querySelector("article");
		const freshInput = freshRoot.querySelector("input");
		const freshScroller = freshRoot.querySelector(".scroller");
		const freshFrame = freshRoot.querySelector("iframe");
		const result = {
			anchorIdentity: freshChild.anchor === oldAnchor,
			capIdentity: freshChild.start === oldStart && freshChild.end === oldEnd,
			clientDraft: freshInput.value,
			focus: document.activeElement === freshInput,
			frameIdentity: freshFrame === frame,
			frameStamp: freshFrame.contentWindow.__citryStamp,
			freshAttribute: freshRoot.dataset.server,
			freshLabel: freshRoot.querySelector(".server-label").textContent,
			logicalState: freshChild.anchor.state.logical,
			rootIdentity: freshRoot === oldRoot,
			scopeIdentity: freshRoot._x_dataStack[0] === scope,
			scopeDraft: freshRoot._x_dataStack[0].draft,
			scroll: freshScroller.scrollTop,
			selection: [freshInput.selectionStart, freshInput.selectionEnd],
			usedConnectedPath: registry.decisionLog[0].stationary,
			residue: residue(host),
		};
		removeFixture(host);
		return result;
	}

	async function stationaryRangeBeforeElementKeyReorder() {
		const host = fixture(
			rangeMarkup(
				"tail-root-0",
				rangeMarkup("tail-child-0", "stable child") +
					'<div data-citry-key="A">A old</div><div data-citry-key="B">B old</div>',
			),
		);
		const registry = new KeyedComponentRangeRegistry(host, [
			rec("tail-root-0", "Page", null),
			rec("tail-child-0", "Child", "stable", "tail-root-0"),
		]);
		const a = host.querySelector('[data-citry-key="A"]');
		const b = host.querySelector('[data-citry-key="B"]');
		registry.morph(
			"tail-root-0",
			rangeMarkup(
				"tail-root-1",
				rangeMarkup("tail-child-1", "fresh child") +
					'<div data-citry-key="B">B fresh</div><div data-citry-key="A">A fresh</div>',
			),
			[
				rec("tail-root-1", "Page", null),
				rec("tail-child-1", "Child", "stable", "tail-root-1"),
			],
			"tail-root-1",
		);
		await settle();
		const keyed = Array.from(host.querySelectorAll("[data-citry-key]"));
		const result = {
			childText: text(registry.instance("tail-child-1")),
			identities: keyed[0] === b && keyed[1] === a,
			order: keyed.map((element) => element.getAttribute("data-citry-key")),
			residue: residue(host),
			text: keyed.map((element) => element.textContent),
			usedConnectedPath: registry.decisionLog[0].stationary,
		};
		removeFixture(host);
		return result;
	}

	async function rangeMovesRelativeToOrdinaryElement() {
		const run = async (name, oldBody, newBody) => {
			const oldRootId = `${name}-root-old`;
			const newRootId = `${name}-root-new`;
			const oldChildId = `${name}-child-old`;
			const newChildId = `${name}-child-new`;
			const oldChild = rangeMarkup(
				oldChildId,
				'<article data-citry-key="child-root">child old</article>',
			);
			const newChild = rangeMarkup(
				newChildId,
				'<article data-citry-key="child-root">child fresh</article>',
			);
			const ordinaryOld = '<div data-citry-key="ordinary">ordinary old</div>';
			const ordinaryNew = '<div data-citry-key="ordinary">ordinary fresh</div>';
			const host = fixture(
				rangeMarkup(
					oldRootId,
					oldBody.replace("CHILD", oldChild).replace("ORDINARY", ordinaryOld),
				),
			);
			const registry = new KeyedComponentRangeRegistry(host, [
				rec(oldRootId, "Page", null),
				rec(oldChildId, "Mover", "component", oldRootId),
			]);
			const previous = registry.instance(oldChildId);
			const anchor = previous.anchor;
			const start = previous.start;
			const end = previous.end;
			const childRoot = host.querySelector("article");
			const ordinary = host.querySelector('[data-citry-key="ordinary"]');
			registry.morph(
				oldRootId,
				rangeMarkup(
					newRootId,
					newBody.replace("CHILD", newChild).replace("ORDINARY", ordinaryNew),
				),
				[
					rec(newRootId, "Page", null),
					rec(newChildId, "Mover", "component", newRootId),
				],
				newRootId,
			);
			await settle();
			const next = registry.instance(newChildId);
			const result = {
				anchor: next.anchor === anchor,
				capIdentities: next.start === start && next.end === end,
				childIdentity: host.querySelector("article") === childRoot,
				childText: text(next),
				ordinaryIdentity: host.querySelector('[data-citry-key="ordinary"]') === ordinary,
				ordinaryText: ordinary.textContent,
				order: Array.from(host.querySelectorAll("article, div")).map(
					(element) => element.localName,
				),
				residue: residue(host),
				usedConnectedPath: registry.decisionLog[0].stationary,
			};
			removeFixture(host);
			return result;
		};
		return {
			leftToRight: await run("range-ltr", "CHILDORDINARY", "ORDINARYCHILD"),
			rightToLeft: await run("range-rtl", "ORDINARYCHILD", "CHILDORDINARY"),
		};
	}

	async function independentComponentAndElementKeys() {
		const host = fixture(
			rangeMarkup(
				"axes-root-0",
				rangeMarkup(
					"axes-child-0",
					'<div data-citry-key="element-a" x-range-probe="axes-a">old</div>',
				),
			),
		);
		const registry = new KeyedComponentRangeRegistry(host, [
			rec("axes-root-0", "Page", null),
			rec("axes-child-0", "Widget", "component-a", "axes-root-0"),
		]);
		await settle();
		const initial = registry.instance("axes-child-0");
		const initialAnchor = initial.anchor;
		const initialRoot = host.querySelector("div");
		registry.morph(
			"axes-root-0",
			rangeMarkup(
				"axes-root-1",
				rangeMarkup(
					"axes-child-1",
					'<div data-citry-key="element-b" x-range-probe="axes-b">element reset</div>',
				),
			),
			[
				rec("axes-root-1", "Page", null),
				rec("axes-child-1", "Widget", "component-a", "axes-root-1"),
			],
			"axes-root-1",
		);
		await settle();
		const afterElementChange = registry.instance("axes-child-1");
		const elementResetRoot = host.querySelector("div");
		const componentKept = {
			anchorIdentity: afterElementChange.anchor === initialAnchor,
			cleanupCount: initialAnchor.cleanupCount,
			rootIdentity: elementResetRoot === initialRoot,
			text: elementResetRoot.textContent,
		};

		registry.morph(
			"axes-root-1",
			rangeMarkup(
				"axes-root-2",
				rangeMarkup(
					"axes-child-2",
					'<div data-citry-key="element-b" x-range-probe="axes-new-component">component reset</div>',
				),
			),
			[
				rec("axes-root-2", "Page", null),
				rec("axes-child-2", "Widget", "component-b", "axes-root-2"),
			],
			"axes-root-2",
		);
		await settle();
		const afterComponentChange = registry.instance("axes-child-2");
		const componentResetRoot = host.querySelector("div");
		const componentReset = {
			anchorIdentity: afterComponentChange.anchor === initialAnchor,
			newElementDespiteSameInnerKey: componentResetRoot !== elementResetRoot,
			oldAnchorCleanup: initialAnchor.cleanupCount,
			text: componentResetRoot.textContent,
		};
		const result = {
			componentKept,
			componentReset,
			residue: residue(host),
		};
		removeFixture(host);
		return result;
	}

	async function reorderedSiblingRanges() {
		const host = fixture(
			rangeMarkup(
				"reorder-root-old",
				rangeMarkup("reorder-a-old", '<div data-citry-key="same">A old</div>') +
					rangeMarkup("reorder-b-old", '<div data-citry-key="same">B old</div>'),
			),
		);
		const registry = new KeyedComponentRangeRegistry(host, [
			rec("reorder-root-old", "Page", null),
			rec("reorder-a-old", "Row", "A", "reorder-root-old"),
			rec("reorder-b-old", "Row", "B", "reorder-root-old"),
		]);
		const aOld = registry.instance("reorder-a-old");
		const bOld = registry.instance("reorder-b-old");
		const aAnchor = aOld.anchor;
		const bAnchor = bOld.anchor;
		const aStart = aOld.start;
		const aEnd = aOld.end;
		const bStart = bOld.start;
		const bEnd = bOld.end;
		const aRoot = nodesBetween(aOld.start, aOld.end)[0];
		const bRoot = nodesBetween(bOld.start, bOld.end)[0];
		registry.morph(
			"reorder-root-old",
			rangeMarkup(
				"reorder-root-new",
				rangeMarkup("reorder-b-new", '<div data-citry-key="same">B fresh</div>') +
					rangeMarkup("reorder-a-new", '<div data-citry-key="same">A fresh</div>'),
			),
			[
				rec("reorder-root-new", "Page", null),
				rec("reorder-b-new", "Row", "B", "reorder-root-new"),
				rec("reorder-a-new", "Row", "A", "reorder-root-new"),
			],
			"reorder-root-new",
		);
		await settle();
		const aNew = registry.instance("reorder-a-new");
		const bNew = registry.instance("reorder-b-new");
		const result = {
			anchorsFollowKeys: aNew.anchor === aAnchor && bNew.anchor === bAnchor,
			capIdentities:
				aNew.start === aStart &&
				aNew.end === aEnd &&
				bNew.start === bStart &&
				bNew.end === bEnd,
			componentOrder: Array.from(host.childNodes)
				.filter((node) => node === aNew.start || node === bNew.start)
				.map((node) => (node === aNew.start ? aNew.anchor.token : bNew.anchor.token)),
			freshText: [text(bNew), text(aNew)],
			innerRootsFollowComponentKeys:
				nodesBetween(aNew.start, aNew.end)[0] === aRoot &&
				nodesBetween(bNew.start, bNew.end)[0] === bRoot,
			residue: residue(host),
		};
		removeFixture(host);
		return result;
	}

	async function adjacentEmptyRangeReorder() {
		const host = fixture(
			rangeMarkup(
				"empty-root-old",
				rangeMarkup("empty-a-old") + rangeMarkup("empty-b-old"),
			),
		);
		const registry = new KeyedComponentRangeRegistry(host, [
			rec("empty-root-old", "Page", null),
			rec("empty-a-old", "Empty", "A", "empty-root-old"),
			rec("empty-b-old", "Empty", "B", "empty-root-old"),
		]);
		const a = registry.instance("empty-a-old");
		const b = registry.instance("empty-b-old");
		const aAnchor = a.anchor;
		const bAnchor = b.anchor;
		const aStart = a.start;
		const aEnd = a.end;
		const bStart = b.start;
		const bEnd = b.end;
		registry.morph(
			"empty-root-old",
			rangeMarkup(
				"empty-root-new",
				rangeMarkup("empty-b-new") + rangeMarkup("empty-a-new"),
			),
			[
				rec("empty-root-new", "Page", null),
				rec("empty-b-new", "Empty", "B", "empty-root-new"),
				rec("empty-a-new", "Empty", "A", "empty-root-new"),
			],
			"empty-root-new",
		);
		await settle();
		const nextA = registry.instance("empty-a-new");
		const nextB = registry.instance("empty-b-new");
		const startOrder = Array.from(host.childNodes)
			.filter(
				(node) =>
					node.nodeType === Node.COMMENT_NODE &&
					(node.data.includes("citry-vrange:empty-a-") ||
						node.data.includes("citry-vrange:empty-b-")) &&
					node.data.endsWith(":s"),
			)
			.map((node) => node.data);
		const result = {
			anchors: nextA.anchor === aAnchor && nextB.anchor === bAnchor,
			capIdentities:
				nextA.start === aStart &&
				nextA.end === aEnd &&
				nextB.start === bStart &&
				nextB.end === bEnd,
			empty: [
				nodesBetween(nextB.start, nextB.end).length,
				nodesBetween(nextA.start, nextA.end).length,
			],
			residue: residue(host),
			startOrder,
		};
		removeFixture(host);
		return result;
	}

	async function multiRootAndShapeTransitions() {
		const host = fixture(
			rangeMarkup(
				"shape-root-0",
				rangeMarkup(
					"shape-child-0",
					'<i data-citry-key="one">one old</i><b data-citry-key="two">two old</b>',
				),
			),
		);
		const registry = new KeyedComponentRangeRegistry(host, [
			rec("shape-root-0", "Page", null),
			rec("shape-child-0", "Shape", "stable", "shape-root-0"),
		]);
		const anchor = registry.instance("shape-child-0").anchor;
		const one = host.querySelector("i");
		const two = host.querySelector("b");
		const morph = async (fromRoot, nextIndex, body) => {
			const nextRoot = `shape-root-${nextIndex}`;
			const nextChild = `shape-child-${nextIndex}`;
			registry.morph(
				fromRoot,
				rangeMarkup(nextRoot, rangeMarkup(nextChild, body)),
				[
					rec(nextRoot, "Page", null),
					rec(nextChild, "Shape", "stable", nextRoot),
				],
				nextRoot,
			);
			await settle();
			return { nextRoot, child: registry.instance(nextChild) };
		};
		let step = await morph(
			"shape-root-0",
			1,
			'<b data-citry-key="two">two fresh</b><i data-citry-key="one">one fresh</i><u data-citry-key="three">three</u>',
		);
		const reordered = {
			anchor: step.child.anchor === anchor,
			identities: host.querySelector("i") === one && host.querySelector("b") === two,
			names: nodesBetween(step.child.start, step.child.end).map((node) => node.localName),
			text: text(step.child),
		};
		step = await morph(step.nextRoot, 2, "plain text");
		const asText = { anchor: step.child.anchor === anchor, text: text(step.child) };
		step = await morph(step.nextRoot, 3, "");
		const empty = {
			anchor: step.child.anchor === anchor,
			nodes: nodesBetween(step.child.start, step.child.end).length,
		};
		step = await morph(step.nextRoot, 4, '<em data-citry-key="final">element</em>');
		const backToElement = {
			anchor: step.child.anchor === anchor,
			name: nodesBetween(step.child.start, step.child.end)[0].localName,
			text: text(step.child),
		};
		const result = { asText, backToElement, empty, reordered, residue: residue(host) };
		removeFixture(host);
		return result;
	}

	async function nestedBoundaryIsolation() {
		const host = fixture(
			rangeMarkup(
				"nested-root-0",
				rangeMarkup(
					"nested-parent-0",
					'<div data-citry-key="parent-root"><span>parent old</span>' +
						rangeMarkup(
							"nested-grand-0",
							'<button data-citry-key="grand-root">grand old</button>',
						) +
						"</div>",
				),
			),
		);
		const registry = new KeyedComponentRangeRegistry(host, [
			rec("nested-root-0", "Page", null),
			rec("nested-parent-0", "Parent", "P", "nested-root-0"),
			rec("nested-grand-0", "Grand", "G", "nested-parent-0"),
		]);
		const parentAnchor = registry.instance("nested-parent-0").anchor;
		const grandAnchor = registry.instance("nested-grand-0").anchor;
		const grandRoot = host.querySelector("button");
		registry.morph(
			"nested-root-0",
			rangeMarkup(
				"nested-root-1",
				rangeMarkup(
					"nested-parent-1",
					'<div data-citry-key="parent-root"><span>parent fresh</span>' +
						rangeMarkup(
							"nested-grand-1",
							'<button data-citry-key="grand-root">grand fresh</button>',
						) +
						"</div>",
				),
			),
			[
				rec("nested-root-1", "Page", null),
				rec("nested-parent-1", "Parent", "P", "nested-root-1"),
				rec("nested-grand-1", "Grand", "G", "nested-parent-1"),
			],
			"nested-root-1",
		);
		await settle();
		const stable = {
			freshText: text(registry.instance("nested-parent-1")),
			grandAnchor: registry.instance("nested-grand-1").anchor === grandAnchor,
			grandRoot: host.querySelector("button") === grandRoot,
			parentAnchor: registry.instance("nested-parent-1").anchor === parentAnchor,
		};
		registry.morph(
			"nested-root-1",
			rangeMarkup(
				"nested-root-2",
				rangeMarkup(
					"nested-parent-2",
					'<div data-citry-key="parent-root"><span>parent reset</span>' +
						rangeMarkup(
							"nested-grand-2",
							'<button data-citry-key="grand-root">grand reset</button>',
						) +
						"</div>",
				),
			),
			[
				rec("nested-root-2", "Page", null),
				rec("nested-parent-2", "Parent", "P-changed", "nested-root-2"),
				rec("nested-grand-2", "Grand", "G", "nested-parent-2"),
			],
			"nested-root-2",
		);
		await settle();
		const reset = {
			grandAnchorLeaked: registry.instance("nested-grand-2").anchor === grandAnchor,
			grandRootLeaked: host.querySelector("button") === grandRoot,
			oldGrandCleanup: grandAnchor.cleanupCount,
			oldParentCleanup: parentAnchor.cleanupCount,
			parentAnchorLeaked: registry.instance("nested-parent-2").anchor === parentAnchor,
		};
		const result = { reset, residue: residue(host), stable };
		removeFixture(host);
		return result;
	}

	async function selfRenderThenParentRender() {
		const host = fixture(
			rangeMarkup(
				"self-root-0",
				rangeMarkup(
					"self-child-0",
					'<div data-citry-key="self-root">initial</div>',
				),
			),
		);
		const registry = new KeyedComponentRangeRegistry(host, [
			rec("self-root-0", "Page", null),
			rec("self-child-0", "Self", "parent-key", "self-root-0"),
		]);
		const anchor = registry.instance("self-child-0").anchor;
		registry.morph(
			"self-child-0",
			rangeMarkup("self-child-1", '<div data-citry-key="self-root">self fresh</div>'),
			[rec("self-child-1", "Self", null)],
			"self-child-1",
		);
		await settle();
		const afterSelf = registry.instance("self-child-1");
		registry.morph(
			"self-root-0",
			rangeMarkup(
				"self-root-2",
				rangeMarkup(
					"self-child-2",
					'<div data-citry-key="self-root">parent fresh</div>',
				),
			),
			[
				rec("self-root-2", "Page", null),
				rec("self-child-2", "Self", "parent-key", "self-root-2"),
			],
			"self-root-2",
		);
		await settle();
		const afterParent = registry.instance("self-child-2");
		const result = {
			afterParentAnchor: afterParent.anchor === anchor,
			afterSelfAnchor: afterSelf.anchor === anchor,
			inheritedKey: afterSelf.record.morphKey,
			text: text(afterParent),
			residue: residue(host),
		};
		removeFixture(host);
		return result;
	}

	async function wrapperDepthMove() {
		const host = fixture(
			rangeMarkup(
				"wrapper-root-0",
				'<div data-citry-key="old-wrapper">' +
					rangeMarkup(
						"wrapper-child-0",
						'<article data-citry-key="child-root" x-range-probe="portable">old location</article>',
					) +
					"</div>",
			),
		);
		const registry = new KeyedComponentRangeRegistry(host, [
			rec("wrapper-root-0", "Page", null),
			rec("wrapper-child-0", "Mover", "stable", "wrapper-root-0"),
		]);
		await settle();
		const oldChild = registry.instance("wrapper-child-0");
		const anchor = oldChild.anchor;
		const start = oldChild.start;
		const end = oldChild.end;
		const root = host.querySelector("article");
		const directiveLogStart = window.__keyedRangeDirectiveLog.length;
		registry.morph(
			"wrapper-root-0",
			rangeMarkup(
				"wrapper-root-1",
				'<section data-citry-key="new-wrapper"><aside>' +
					rangeMarkup(
						"wrapper-child-1",
						'<article data-citry-key="child-root" x-range-probe="portable">fresh location</article>',
					) +
					"</aside></section>",
			),
			[
				rec("wrapper-root-1", "Page", null),
				rec("wrapper-child-1", "Mover", "stable", "wrapper-root-1"),
			],
			"wrapper-root-1",
		);
		await settle();
		const next = registry.instance("wrapper-child-1");
		const duringMorphLog = window.__keyedRangeDirectiveLog.slice(directiveLogStart);
		const result = {
			anchor: next.anchor === anchor,
			capIdentities: next.start === start && next.end === end,
			cleanupDuringMove: duringMorphLog.filter((entry) => entry === "cleanup:portable")
				.length,
			newAncestors: [next.start.parentElement.localName, next.start.parentElement.parentElement.localName],
			residue: residue(host),
			rootIdentity: host.querySelector("article") === root,
			text: text(next),
		};
		removeFixture(host);
		await settle();
		result.cleanupAfterRemoval = window.__keyedRangeDirectiveLog
			.slice(directiveLogStart)
			.filter((entry) => entry === "cleanup:portable").length;
		return result;
	}

	async function idOnlyWrapperReorder() {
		const host = fixture(
			rangeMarkup(
				"id-wrapper-root-0",
				'<div id="left">' +
					rangeMarkup(
						"id-wrapper-child-0",
						'<article data-citry-key="child-root">old child</article>',
					) +
					'</div><div id="right"><span>right old</span></div>',
			),
		);
		const registry = new KeyedComponentRangeRegistry(host, [
			rec("id-wrapper-root-0", "Page", null),
			rec("id-wrapper-child-0", "Mover", "stable", "id-wrapper-root-0"),
		]);
		const oldChild = registry.instance("id-wrapper-child-0");
		const anchor = oldChild.anchor;
		const start = oldChild.start;
		const end = oldChild.end;
		const root = host.querySelector("article");
		registry.morph(
			"id-wrapper-root-0",
			rangeMarkup(
				"id-wrapper-root-1",
				'<div id="right"><span>right fresh</span></div><div id="left">' +
					rangeMarkup(
						"id-wrapper-child-1",
						'<article data-citry-key="child-root">fresh child</article>',
					) +
					"</div>",
			),
			[
				rec("id-wrapper-root-1", "Page", null),
				rec("id-wrapper-child-1", "Mover", "stable", "id-wrapper-root-1"),
			],
			"id-wrapper-root-1",
		);
		await settle();
		const next = registry.instance("id-wrapper-child-1");
		const result = {
			anchor: next.anchor === anchor,
			capIdentities: next.start === start && next.end === end,
			residue: residue(host),
			rootIdentity: host.querySelector("article") === root,
			text: text(next),
			usedConnectedPath: registry.decisionLog[0].stationary,
			wrapperOrder: Array.from(host.querySelectorAll(":scope > div")).map(
				(element) => element.id,
			),
		};
		removeFixture(host);
		return result;
	}

	async function nullEmptyFalseZeroAndClass() {
		const initialChildren = [
			["empty", "", "Empty"],
			["null", null, "Null"],
			["false", "False", "False"],
			["zero", "0", "Zero"],
		];
		const body = initialChildren
			.map(([name]) => rangeMarkup(`value-${name}-0`, `<span>${name}</span>`))
			.join("");
		const host = fixture(rangeMarkup("value-root-0", body));
		const records = [rec("value-root-0", "Page", null)];
		for (const [name, key] of initialChildren) {
			records.push(rec(`value-${name}-0`, "Value", key, "value-root-0"));
		}
		const registry = new KeyedComponentRangeRegistry(host, records);
		const anchors = Object.fromEntries(
			initialChildren.map(([name]) => [name, registry.instance(`value-${name}-0`).anchor]),
		);
		const freshBody = initialChildren
			.map(([name]) => rangeMarkup(`value-${name}-1`, `<span>${name} fresh</span>`))
			.join("");
		const freshRecords = [rec("value-root-1", "Page", null)];
		for (const [name, key] of initialChildren) {
			freshRecords.push(rec(`value-${name}-1`, "Value", key, "value-root-1"));
		}
		registry.morph(
			"value-root-0",
			rangeMarkup("value-root-1", freshBody),
			freshRecords,
			"value-root-1",
		);
		await settle();
		const valueSemantics = Object.fromEntries(
			initialChildren.map(([name]) => [
				name,
				registry.instance(`value-${name}-1`).anchor === anchors[name],
			]),
		);
		registry.morph(
			"value-root-1",
			rangeMarkup(
				"value-root-2",
				rangeMarkup("value-empty-2", "<span>different class</span>"),
			),
			[
				rec("value-root-2", "Page", null),
				rec("value-empty-2", "OtherValue", "", "value-root-2"),
			],
			"value-root-2",
		);
		await settle();
		const result = {
			classChangePreserved: registry.instance("value-empty-2").anchor === anchors.empty,
			oldEmptyCleanup: anchors.empty.cleanupCount,
			residue: residue(host),
			valueSemantics,
		};
		removeFixture(host);
		return result;
	}

	async function contextualSelectRange() {
		const host = fixture(
			rangeMarkup(
				"select-root-0",
				rangeMarkup(
					"select-child-0",
					'<option data-citry-key="option">old</option>',
				),
			),
			"select",
		);
		const registry = new KeyedComponentRangeRegistry(host, [
			rec("select-root-0", "Select", null),
			rec("select-child-0", "Option", "one", "select-root-0"),
		]);
		const anchor = registry.instance("select-child-0").anchor;
		const option = host.querySelector("option");
		registry.morph(
			"select-root-0",
			rangeMarkup(
				"select-root-1",
				rangeMarkup(
					"select-child-1",
					'<option data-citry-key="option">fresh</option>',
				),
			),
			[
				rec("select-root-1", "Select", null),
				rec("select-child-1", "Option", "one", "select-root-1"),
			],
			"select-root-1",
		);
		await settle();
		const next = registry.instance("select-child-1");
		const result = {
			anchor: next.anchor === anchor,
			identity: host.querySelector("option") === option,
			options: host.options.length,
			residue: residue(host),
			text: host.options[0].textContent,
		};
		removeFixture(host);
		return result;
	}

	window.runKeyedComponentRangeScenarios = async () => ({
		adjacentEmptyRangeReorder: await adjacentEmptyRangeReorder(),
		contextualSelectRange: await contextualSelectRange(),
		idOnlyWrapperReorder: await idOnlyWrapperReorder(),
		independentComponentAndElementKeys: await independentComponentAndElementKeys(),
		inertIslandNegativeControl: await inertIslandNegativeControl(),
		multiRootAndShapeTransitions: await multiRootAndShapeTransitions(),
		nestedBoundaryIsolation: await nestedBoundaryIsolation(),
		nullEmptyFalseZeroAndClass: await nullEmptyFalseZeroAndClass(),
		reorderedSiblingRanges: await reorderedSiblingRanges(),
		rangeMovesRelativeToOrdinaryElement: await rangeMovesRelativeToOrdinaryElement(),
		selfRenderThenParentRender: await selfRenderThenParentRender(),
		stationaryFreshContentAndBrowserState: await stationaryFreshContentAndBrowserState(),
		stationaryRangeBeforeElementKeyReorder: await stationaryRangeBeforeElementKeyReorder(),
		wrapperDepthMove: await wrapperDepthMove(),
		directiveLog: window.__keyedRangeDirectiveLog.slice(),
	});
})();
