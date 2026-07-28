/* Browser scenarios for the throwaway rootless-lifecycle prototype. */
(() => {
	const { RootlessRegistry, marker, nodesBetween } =
		window.RootlessLifecycleSpike;
	const sleep = (milliseconds) =>
		new Promise((resolve) => window.setTimeout(resolve, milliseconds));
	const settle = async () => {
		await Promise.resolve();
		await Alpine.nextTick();
		await Promise.resolve();
	};

	function comments(id, content = "") {
		return `<!--${marker("start", id)}-->${content}<!--${marker("end", id)}-->`;
	}

	function fixture(markup = "", tag = "section") {
		const host = document.createElement(tag);
		host.className = "rootless-fixture";
		host.innerHTML = markup;
		document.body.append(host);
		return host;
	}

	function betweenText(instance) {
		return nodesBetween(instance.start, instance.end)
			.map((node) => node.textContent)
			.join("");
	}

	function betweenNames(instance) {
		return nodesBetween(instance.start, instance.end).map((node) =>
			node.nodeType === Node.ELEMENT_NODE
				? node.localName
				: `#${node.nodeName}`,
		);
	}

	function moveRange(instance, destination) {
		const moving = [
			instance.start,
			...nodesBetween(instance.start, instance.end),
			instance.end,
		];
		const fragment = document.createDocumentFragment();
		fragment.append(...moving);
		destination.append(fragment);
	}

	async function initialLogicalLifecycle() {
		const host = fixture(comments("logical", "ready"));
		host.setAttribute("x-data", "{ value: 1 }");
		await settle();
		const registry = new RootlessRegistry();
		const observed = {
			cleanup: 0,
			effects: [],
			init: 0,
			pollParents: [],
		};
		let elsReference = null;
		const instance = registry.adopt("logical", {
			supplyExpression: "({ value })",
			init(ctx) {
				observed.init += 1;
				elsReference = ctx.els;
				ctx.scope.local = "rootless-scope";
				ctx.effect(() => observed.effects.push(ctx.props.value));
				ctx.poll(8, (parent) => observed.pollParents.push(parent === host));
				return () => {
					observed.cleanup += 1;
				};
			},
		});
		await settle();
		const before = {
			elsEmpty: instance.els.length === 0,
			elsStable: instance.els === elsReference,
			init: observed.init,
			props: instance.props.value,
			scope: instance.scope.local,
		};
		host._x_dataStack[0].value = 2;
		await settle();
		await sleep(26);
		const active = {
			effects: observed.effects.slice(),
			pollCount: observed.pollParents.length,
			pollParents: observed.pollParents.every(Boolean),
			cleanup: observed.cleanup,
		};
		instance.start.remove();
		await settle();
		const pollAtDestroy = observed.pollParents.length;
		await sleep(20);
		const after = {
			cleanup: observed.cleanup,
			destroyed: instance.destroyed,
			pollStopped: observed.pollParents.length === pollAtDestroy,
		};
		registry.destroy();
		host.remove();
		return { active, after, before };
	}

	async function shapeTransitionsAndAlpine() {
		window.__rootlessDirectiveLog.splice(0);
		const host = fixture(comments("shape", "initial"));
		const registry = new RootlessRegistry();
		let cleanup = 0;
		let init = 0;
		let elsReference = null;
		const instance = registry.adopt("shape", {
			init(ctx) {
				init += 1;
				elsReference = ctx.els;
				ctx.scope.label = "from-scope";
				return () => {
					cleanup += 1;
				};
			},
		});
		const snapshots = [];
		const snap = (name) =>
			snapshots.push({
				name,
				els: instance.els.map((element) => element.localName),
				stable: instance.els === elsReference,
				text: betweenText(instance),
			});

		snap("initial-text");
		instance.replace("");
		await settle();
		snap("empty");
		instance.replace("plain text");
		await settle();
		snap("text");
		instance.replace(
			'<span x-text="label" x-rootless-probe="one"></span><b x-text="label" x-rootless-probe="two"></b>',
		);
		await settle();
		snap("several-elements");
		const renderedLabels = instance.els.map((element) => element.textContent);
		instance.replace('<i x-text="label" x-rootless-probe="three"></i>');
		await settle();
		snap("one-element");
		instance.replace("tail");
		await settle();
		snap("back-to-text");
		const directiveLog = window.__rootlessDirectiveLog.slice();
		const beforeRemoval = { cleanup, init };
		instance.end.remove();
		await settle();
		const afterRemoval = { cleanup, destroyed: instance.destroyed, init };
		registry.destroy();
		host.remove();
		return {
			afterRemoval,
			beforeRemoval,
			directiveLog,
			renderedLabels,
			snapshots,
		};
	}

	async function contextualParsing() {
		const results = {};

		const tableHost = fixture(
			`<table><tbody>${comments("row")}</tbody></table>`,
		);
		const tableRegistry = new RootlessRegistry();
		const row = tableRegistry.adopt("row");
		row.replace("<tr><td>cell</td></tr>");
		await settle();
		results.tbody = {
			names: betweenNames(row),
			namespace: row.els[0].namespaceURI,
			text: betweenText(row),
		};
		tableRegistry.destroy();
		tableHost.remove();

		const trHost = fixture(
			`<table><tbody><tr>${comments("cell")}</tr></tbody></table>`,
		);
		const trRegistry = new RootlessRegistry();
		const cell = trRegistry.adopt("cell");
		cell.replace("<td>value</td><td>second</td>");
		await settle();
		results.tr = betweenNames(cell);
		trRegistry.destroy();
		trHost.remove();

		const selectHost = fixture(`<select>${comments("option")}</select>`);
		const selectRegistry = new RootlessRegistry();
		const option = selectRegistry.adopt("option");
		option.replace(
			'<optgroup label="g"><option>one</option></optgroup><option>two</option>',
		);
		await settle();
		results.select = {
			names: betweenNames(option),
			options: selectHost.querySelectorAll("option").length,
		};
		selectRegistry.destroy();
		selectHost.remove();

		const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
		const svgStart = document.createComment(marker("start", "svg"));
		const svgEnd = document.createComment(marker("end", "svg"));
		svg.append(svgStart, svgEnd);
		document.body.append(svg);
		const svgRegistry = new RootlessRegistry();
		const svgRange = svgRegistry.adopt("svg");
		svgRange.replace('<circle cx="4" cy="4" r="3"></circle>');
		await settle();
		results.svg = {
			name: svgRange.els[0].localName,
			namespace: svgRange.els[0].namespaceURI,
		};
		svgRegistry.destroy();
		svg.remove();

		const stockHost = fixture(
			`<table><tbody>${comments("stock")}</tbody></table>`,
		);
		const stockStart = Array.from(
			stockHost.querySelector("tbody").childNodes,
		).find((node) => node.data === marker("start", "stock"));
		const stockEnd = Array.from(
			stockHost.querySelector("tbody").childNodes,
		).find((node) => node.data === marker("end", "stock"));
		Alpine.morphBetween(stockStart, stockEnd, "<tr><td>stock</td></tr>");
		await settle();
		results.stockStringTbody = Array.from(stockStart.parentNode.childNodes)
			.filter((node) => node !== stockStart && node !== stockEnd)
			.map((node) =>
				node.nodeType === Node.ELEMENT_NODE
					? node.localName
					: `#${node.nodeName}`,
			);
		stockHost.remove();

		return results;
	}

	async function nestedAndAdjacent() {
		const host = fixture(
			comments(
				"outer",
				comments(
					"inner-old",
					'<span key="inner" x-rootless-probe="nested">client</span>',
				),
			) + comments("adjacent", '<div key="same">adjacent</div>'),
		);
		const registry = new RootlessRegistry();
		const cleanups = { adjacent: 0, inner: 0, outer: 0 };
		const outer = registry.adopt("outer", {
			init: () => () => {
				cleanups.outer += 1;
			},
		});
		const inner = registry.adopt("inner-old", {
			anchorKey: "inner-anchor",
			init: () => () => {
				cleanups.inner += 1;
			},
		});
		const adjacent = registry.adopt("adjacent", {
			init: () => () => {
				cleanups.adjacent += 1;
			},
		});
		const innerStart = inner.start;
		const innerEnd = inner.end;
		const innerElement = inner.els[0];
		const adjacentStart = adjacent.start;
		const adjacentElement = adjacent.els[0];
		innerElement.dataset.clientState = "kept";
		await settle();
		const directiveLogStart = window.__rootlessDirectiveLog.length;
		outer.replace(
			'<p key="lead">lead</p>' +
				comments(
					"inner-fresh",
					'<span key="inner" x-rootless-probe="nested">server</span>',
				) +
				'<p key="tail">tail</p>',
			{
				resolveIncomingAnchor: (id) =>
					id === "inner-fresh" ? "inner-anchor" : id,
			},
		);
		await settle();
		const protectedMorph = {
			adjacentIdentity:
				adjacent.start === adjacentStart && adjacent.els[0] === adjacentElement,
			cleanups: { ...cleanups },
			innerElementIdentity: inner.els[0] === innerElement,
			innerEndIdentity: inner.end === innerEnd,
			innerStartIdentity: inner.start === innerStart,
			innerState: inner.els[0].dataset.clientState,
			liveRenderId: inner.id,
			outerNames: betweenNames(outer),
		};

		outer.replace('<p key="only">only</p>');
		await settle();
		const nestedRemoval = {
			adjacentLive: adjacent.isValid(),
			cleanups: { ...cleanups },
			directiveLog: window.__rootlessDirectiveLog.slice(directiveLogStart),
			innerDestroyed: inner.destroyed,
			outerLive: outer.isValid(),
		};

		const adjacentBefore = adjacent.els[0];
		adjacent.replace('<div key="same">changed</div><em key="extra">extra</em>');
		await settle();
		const adjacentMorph = {
			cleanups: { ...cleanups },
			firstIdentity: adjacent.els[0] === adjacentBefore,
			names: betweenNames(adjacent),
			text: betweenText(adjacent),
		};
		registry.destroy();
		host.remove();

		const stockHost = fixture(
			comments(
				"stock-outer",
				comments("stock-inner", '<span key="s">state</span>'),
			),
		);
		const stockRegistry = new RootlessRegistry();
		const stockOuter = stockRegistry.adopt("stock-outer");
		const stockInner = stockRegistry.adopt("stock-inner");
		const stockStart = stockInner.start;
		stockOuter.replace(
			'<p key="prepend">prepend</p>' +
				comments("stock-inner", '<span key="s">state</span>'),
			{ protectNested: false },
		);
		await settle();
		const unprotectedControl = {
			destroyed: stockInner.destroyed,
			identityPreserved:
				stockInner.start === stockStart && stockStart.isConnected,
			valid: stockInner.isValid(),
		};
		stockRegistry.destroy();
		stockHost.remove();

		const resetHost = fixture(
			comments(
				"reset-outer",
				comments("reset-old", '<span key="reset">old child</span>'),
			),
		);
		const resetRegistry = new RootlessRegistry();
		let oldCleanup = 0;
		let freshInit = 0;
		const resetOuter = resetRegistry.adopt("reset-outer");
		const resetOld = resetRegistry.adopt("reset-old", {
			anchorKey: "reset-anchor",
			init: () => () => {
				oldCleanup += 1;
			},
		});
		resetOuter.replace(
			comments("reset-fresh", '<span key="reset">fresh child</span>'),
		);
		await settle();
		const resetFresh = resetRegistry.adopt("reset-fresh", {
			init: () => {
				freshInit += 1;
			},
		});
		const refusedIdentityLink = {
			freshInit,
			freshText: betweenText(resetFresh),
			oldCleanup,
			oldDestroyed: resetOld.destroyed,
		};
		resetRegistry.destroy();
		resetHost.remove();

		const insertionHost = fixture(comments("insertion-outer"));
		const insertionRegistry = new RootlessRegistry();
		const insertionOuter = insertionRegistry.adopt("insertion-outer");
		insertionOuter.replace(
			comments("inserted-inner", '<strong key="new">new child</strong>'),
		);
		let insertedInit = 0;
		const insertedInner = insertionRegistry.adopt("inserted-inner", {
			init: () => {
				insertedInit += 1;
			},
		});
		await settle();
		const nestedInsertion = {
			init: insertedInit,
			names: betweenNames(insertedInner),
			valid: insertedInner.isValid(),
		};
		insertionRegistry.destroy();
		insertionHost.remove();

		const emptyHost = fixture(comments("empty-a") + comments("empty-b"));
		const emptyRegistry = new RootlessRegistry();
		const emptyA = emptyRegistry.adopt("empty-a");
		const emptyB = emptyRegistry.adopt("empty-b");
		const emptyBStart = emptyB.start;
		emptyA.replace("A");
		await settle();
		const emptyAdjacent = {
			firstText: betweenText(emptyA),
			secondEmpty: emptyB.els.length === 0 && betweenText(emptyB) === "",
			secondIdentity: emptyB.start === emptyBStart,
			secondValid: emptyB.isValid(),
		};
		emptyRegistry.destroy();
		emptyHost.remove();

		return {
			adjacentMorph,
			emptyAdjacent,
			nestedInsertion,
			nestedRemoval,
			protectedMorph,
			refusedIdentityLink,
			unprotectedControl,
		};
	}

	async function keyedRangeLocality() {
		const host = fixture(
			comments(
				"keys-a",
				'<input key="a" value="server-a"><input key="b" value="server-b">',
			) + comments("keys-b", '<input key="a" value="other">'),
		);
		const registry = new RootlessRegistry();
		const first = registry.adopt("keys-a");
		const second = registry.adopt("keys-b");
		const [a, b] = first.els;
		const other = second.els[0];
		a.value = "client-a";
		b.value = "client-b";
		a.dataset.identity = "a";
		b.dataset.identity = "b";
		first.replace('<input key="b" value="new-b"><input key="a" value="new-a">');
		await settle();
		const result = {
			identitiesPreserved: first.els[0] === b && first.els[1] === a,
			otherIdentity: second.els[0] === other,
			secondValue: other.value,
			values: first.els.map((element) => element.value),
		};
		registry.destroy();
		host.remove();
		return result;
	}

	async function movementAndRemoval() {
		const host = fixture(
			'<div id="source" x-data="{ value: 10 }"></div><div id="destination" x-data="{ value: 20 }"></div>',
		);
		const source = host.querySelector("#source");
		const destination = host.querySelector("#destination");
		source.innerHTML = comments("moving", "payload");
		await settle();
		const registry = new RootlessRegistry();
		let cleanup = 0;
		let init = 0;
		const moving = registry.adopt("moving", {
			supplyExpression: "({ value })",
			init: () => {
				init += 1;
				return () => {
					cleanup += 1;
				};
			},
		});
		moveRange(moving, destination);
		await settle();
		const sameTaskMove = {
			cleanup,
			init,
			parent: moving.start.parentElement.id,
			props: moving.props.value,
			valid: moving.isValid(),
		};

		const detached = document.createDocumentFragment();
		moveRange(moving, detached);
		await settle();
		const acrossTaskDetach = { cleanup, destroyed: moving.destroyed, init };
		destination.append(detached);
		await settle();
		const noResurrection = { cleanup, destroyed: moving.destroyed, init };
		registry.destroy();
		host.remove();

		const elementHost = fixture(
			'<div id="element-source" x-data="{ value: 30 }"></div>' +
				'<div id="element-destination" x-data="{ value: 40 }"></div>',
		);
		await settle();
		const elementSource = elementHost.querySelector("#element-source");
		const elementDestination = elementHost.querySelector(
			"#element-destination",
		);
		elementSource.innerHTML = comments(
			"moving-element",
			"<div x-data=\"{ own: 'local' }\"><span x-text=\"own + ':' + shared\"></span></div>",
		);
		const elementRegistry = new RootlessRegistry();
		const movingElement = elementRegistry.adopt("moving-element", {
			supplyExpression: "({ value })",
			init(ctx) {
				ctx.scope.shared = "shared";
			},
		});
		await settle();
		const elementRoot = movingElement.els[0];
		moveRange(movingElement, elementDestination);
		await settle();
		elementRoot._x_dataStack[0].own = "changed";
		movingElement.scope.shared = "updated";
		await settle();
		const elementMove = {
			identity: movingElement.els[0] === elementRoot,
			ownScopePresent: elementRoot._x_dataStack.some(
				(layer) => layer.own === "changed",
			),
			props: movingElement.props.value,
			sharedScopePresent: elementRoot._x_dataStack.includes(
				movingElement.scope,
			),
			text: elementRoot.textContent,
			valid: movingElement.isValid(),
		};
		elementRegistry.destroy();
		elementHost.remove();

		async function removalCase(id, mutate) {
			const caseHost = fixture(comments(id, "content"));
			const caseRegistry = new RootlessRegistry();
			let count = 0;
			const instance = caseRegistry.adopt(id, {
				init: () => () => {
					count += 1;
				},
			});
			mutate(caseHost, instance);
			await settle();
			caseRegistry.reconcile();
			const result = {
				cleanup: count,
				destroyed: instance.destroyed,
				reason: instance.destroyReason,
			};
			caseRegistry.destroy();
			caseHost.remove();
			return result;
		}

		return {
			acrossTaskDetach,
			ancestor: await removalCase("ancestor", (caseHost) => caseHost.remove()),
			endOnly: await removalCase("end-only", (_host, instance) =>
				instance.end.remove(),
			),
			elementMove,
			innerHtml: await removalCase("html", (caseHost) => {
				caseHost.innerHTML = "comments stripped";
			}),
			noResurrection,
			sameTaskMove,
			startOnly: await removalCase("start-only", (_host, instance) =>
				instance.start.remove(),
			),
		};
	}

	async function pendingAndCommentStripping() {
		const host = fixture();
		const registry = new RootlessRegistry();
		let init = 0;
		const pending = registry.adopt(
			"late",
			{
				init: () => {
					init += 1;
				},
			},
			{ pending: true },
		);
		host.innerHTML = comments("late", "late content");
		await settle();
		const manifestBeforeCaps = {
			init,
			resolved: Boolean(pending.start && pending.end),
			valid: pending.isValid(),
		};

		let missingError = null;
		try {
			registry.adopt("stripped");
		} catch (error) {
			missingError = error.message;
		}

		const template = document.createElement("template");
		template.innerHTML = comments("template-inert", "blueprint");
		host.append(template);
		let templateInit = 0;
		const inert = registry.adopt(
			"template-inert",
			{ init: () => (templateInit += 1) },
			{ pending: true },
		);
		await settle();
		const templateContent = {
			init: templateInit,
			resolved: Boolean(inert.start),
		};

		registry.destroy();
		host.remove();

		const separateHost = fixture();
		const separateRegistry = new RootlessRegistry();
		const separateErrors = [];
		let separateInit = 0;
		const separate = separateRegistry.adopt(
			"separate",
			{
				init: () => {
					separateInit += 1;
				},
				onError: (error) => separateErrors.push(error.message),
			},
			{ pending: true },
		);
		separateHost.append(document.createComment(marker("start", "separate")));
		await settle();
		const partialCaps = {
			errors: separateErrors.slice(),
			init: separateInit,
			resolved: Boolean(separate.start),
		};
		separateHost.append(document.createComment(marker("end", "separate")));
		await settle();
		const completeCaps = {
			errors: separateErrors.slice(),
			init: separateInit,
			settled: separateRegistry.settle("separate"),
			valid: separate.isValid(),
		};
		separateRegistry.destroy();
		separateHost.remove();

		async function invalidPending(id, markup) {
			const invalidHost = fixture(markup);
			const invalidRegistry = new RootlessRegistry();
			const errors = [];
			const instance = invalidRegistry.adopt(
				id,
				{ onError: (error) => errors.push(error.message) },
				{ pending: true },
			);
			const settled = invalidRegistry.settle(id);
			const result = {
				destroyed: instance.destroyed,
				errors,
				reason: instance.destroyReason,
				settled,
			};
			invalidRegistry.destroy();
			invalidHost.remove();
			return result;
		}

		const duplicate = await invalidPending(
			"duplicate",
			comments("duplicate") + comments("duplicate"),
		);
		const crossed = await invalidPending(
			"cross-a",
			`<!--${marker("start", "cross-a")}--><!--${marker("start", "cross-b")}-->` +
				`<!--${marker("end", "cross-a")}--><!--${marker("end", "cross-b")}-->`,
		);

		const siblingHost = fixture(
			`${comments("sibling-a")}<!--${marker("start", "sibling-b")}-->`,
		);
		const siblingRegistry = new RootlessRegistry();
		let siblingAInit = 0;
		let siblingBInit = 0;
		const siblingB = siblingRegistry.adopt(
			"sibling-b",
			{ init: () => (siblingBInit += 1) },
			{ pending: true },
		);
		const siblingA = siblingRegistry.adopt("sibling-a", {
			init: () => (siblingAInit += 1),
		});
		siblingHost.append(document.createComment(marker("end", "sibling-b")));
		await settle();
		const unrelatedPartialSibling = {
			aInit: siblingAInit,
			aValid: siblingA.isValid(),
			bInit: siblingBInit,
			bSettled: siblingRegistry.settle("sibling-b"),
			bValid: siblingB.isValid(),
		};
		siblingRegistry.destroy();
		siblingHost.remove();

		return {
			completeCaps,
			crossed,
			duplicate,
			manifestBeforeCaps,
			missingError,
			partialCaps,
			templateContent,
			unrelatedPartialSibling,
		};
	}

	async function mirroredLogicalInstance() {
		const host = fixture(
			`<div id="mirror-a" x-data="{ value: 1 }">${comments("mirror-region-a")}</div>` +
				`<div id="mirror-b" x-data="{ value: 2 }">${comments("mirror-region-b")}</div>`,
		);
		await settle();
		const registry = new RootlessRegistry();
		let cleanup = 0;
		let init = 0;
		const effects = [];
		const polls = [];
		let elsReference = null;
		const group = registry.adoptMirrors(
			"mirror-anchor",
			["mirror-region-a", "mirror-region-b"],
			{
				supplyExpression: "({ value })",
				init(ctx) {
					init += 1;
					elsReference = ctx.els;
					ctx.scope.shared = "shared";
					ctx.effect(() => effects.push(ctx.props.value));
					ctx.poll(8, (parent) => polls.push(parent.id));
					return () => {
						cleanup += 1;
					};
				},
			},
		);
		const initial = {
			cleanup,
			elsEmpty: group.els.length === 0,
			elsStable: group.els === elsReference,
			init,
			props: group.props.value,
		};
		group.replace('<span x-text="shared"></span>');
		await settle();
		const rendered = {
			els: group.els.map((element) => element.textContent),
			regions: group.regions.map((region) => region.els.length),
		};
		await sleep(20);
		const pollsBeforePartial = polls.length;
		host.querySelector("#mirror-a").remove();
		await settle();
		await sleep(12);
		const partialRemoval = {
			cleanup,
			els: group.els.map((element) => element.textContent),
			effects: effects.slice(),
			init,
			pollContinued: polls.length > pollsBeforePartial,
			props: group.props.value,
		};
		host.querySelector("#mirror-b").remove();
		await settle();
		const pollsAtDestroy = polls.length;
		await sleep(12);
		const finalRemoval = {
			cleanup,
			destroyed: group.destroyed,
			init,
			pollStopped: polls.length === pollsAtDestroy,
		};
		registry.destroy();
		host.remove();

		const rollbackHost = fixture(comments("mirror-rollback-good"));
		const rollbackRegistry = new RootlessRegistry();
		let rollbackInit = 0;
		let rollbackError = null;
		try {
			rollbackRegistry.adoptMirrors(
				"mirror-rollback",
				["mirror-rollback-good", "mirror-rollback-missing"],
				{ init: () => (rollbackInit += 1) },
			);
		} catch (error) {
			rollbackError = error.message;
		}
		const failedConstruction = {
			error: rollbackError,
			groups: rollbackRegistry.groups.size,
			init: rollbackInit,
			instances: rollbackRegistry.instances.size,
		};
		rollbackRegistry.destroy();
		rollbackHost.remove();
		return {
			failedConstruction,
			finalRemoval,
			initial,
			partialRemoval,
			rendered,
		};
	}

	async function managedCleanupAndErrors() {
		const host = fixture(comments("managed"));
		const registry = new RootlessRegistry();
		const state = Alpine.reactive({ value: 0 });
		const order = [];
		const errors = [];
		let effectRuns = 0;
		let pollRuns = 0;
		const instance = registry.adopt("managed", {
			onError: (error) => errors.push(error.message),
			init(ctx) {
				ctx.effect(() => {
					state.value;
					effectRuns += 1;
				});
				const manualStop = ctx.effect(() => state.value);
				manualStop();
				ctx.poll(7, () => (pollRuns += 1));
				ctx.onCleanup(() => {
					order.push(`cleanup-sees-runs:${effectRuns}`);
					throw new Error("expected cleanup throw");
				});
				ctx.onCleanup(() => order.push("second-cleanup"));
				return () => order.push("returned-cleanup");
			},
		});
		state.value = 1;
		await settle();
		await sleep(18);
		const before = { effectRuns, pollRuns };
		instance.start.remove();
		state.value = 2;
		await settle();
		const pollAtDestroy = pollRuns;
		await sleep(16);
		const after = {
			destroyed: instance.destroyed,
			effectRuns,
			errors,
			order,
			pollStopped: pollRuns === pollAtDestroy,
		};
		registry.destroy();
		host.remove();

		const initHost = fixture(comments("throw-init"));
		const initRegistry = new RootlessRegistry();
		const initErrors = [];
		const throwInit = initRegistry.adopt("throw-init", {
			onError: (error) => initErrors.push(error.message),
			init: () => {
				throw new Error("expected init throw");
			},
		});
		const throwingInit = {
			destroyed: throwInit.destroyed,
			errors: initErrors,
			reason: throwInit.destroyReason,
		};
		initRegistry.destroy();
		initHost.remove();
		return { after, before, throwingInit };
	}

	async function handlerBoundary() {
		const host = fixture(comments("handler"));
		const registry = new RootlessRegistry();
		const instance = registry.adopt("handler");
		let error = null;
		try {
			instance.bindDomEvent("click", () => {});
		} catch (caught) {
			error = caught.message;
		}
		registry.destroy();
		host.remove();
		return error;
	}

	async function runRootlessLifecycleScenarios() {
		return {
			alpineVersion: Alpine.version,
			contextualParsing: await contextualParsing(),
			handlerBoundary: await handlerBoundary(),
			initialLogicalLifecycle: await initialLogicalLifecycle(),
			keyedRangeLocality: await keyedRangeLocality(),
			managedCleanupAndErrors: await managedCleanupAndErrors(),
			mirroredLogicalInstance: await mirroredLogicalInstance(),
			movementAndRemoval: await movementAndRemoval(),
			nestedAndAdjacent: await nestedAndAdjacent(),
			pendingAndCommentStripping: await pendingAndCommentStripping(),
			shapeTransitionsAndAlpine: await shapeTransitionsAndAlpine(),
		};
	}

	window.runRootlessLifecycleScenarios = runRootlessLifecycleScenarios;
})();
