/*
 * Disposable keyed-component-range experiment.
 *
 * This is research code, not Citry runtime code. It models a component as a
 * comment-bounded virtual node, keeps ordinary element keys on
 * data-citry-key, and drives the real pinned Alpine morphBetween adapter.
 */
(() => {
	const PREFIX = "citry-vrange:";
	const SENTINEL = "data-citry-vrange-sentinel";
	const HOLDER = "data-citry-vrange-holder";
	const SLOT_KEY = "data-citry-vrange-slot";
	const PORTABLE = "data-citry-vrange-portable";

	function marker(kind, id) {
		return `${PREFIX}${id}:${kind === "start" ? "s" : "e"}`;
	}

	function rangeMarkup(id, content = "") {
		return `<!--${marker("start", id)}-->${content}<!--${marker("end", id)}-->`;
	}

	function nodesBetween(start, end) {
		const nodes = [];
		for (let node = start.nextSibling; node && node !== end; node = node.nextSibling) {
			nodes.push(node);
		}
		return nodes;
	}

	function inclusiveNodes(pair) {
		return [pair.start, ...nodesBetween(pair.start, pair.end), pair.end];
	}

	function commentsIn(root) {
		const comments = [];
		if (root.nodeType === Node.COMMENT_NODE) comments.push(root);
		const walker = document.createTreeWalker(root, NodeFilter.SHOW_COMMENT);
		for (let node = walker.nextNode(); node; node = walker.nextNode()) {
			comments.push(node);
		}
		return comments;
	}

	function findPair(root, id) {
		let start = null;
		let end = null;
		for (const comment of commentsIn(root)) {
			if (comment.data === marker("start", id)) {
				if (start) throw new Error(`Duplicate range start for ${id}`);
				start = comment;
			}
			if (comment.data === marker("end", id)) {
				if (end) throw new Error(`Duplicate range end for ${id}`);
				end = comment;
			}
		}
		if (!start || !end) throw new Error(`Missing range caps for ${id}`);
		if (start.parentNode !== end.parentNode) {
			throw new Error(`Range caps for ${id} do not share a parent`);
		}
		let foundEnd = false;
		for (let node = start.nextSibling; node; node = node.nextSibling) {
			if (node === end) {
				foundEnd = true;
				break;
			}
		}
		if (!foundEnd) throw new Error(`Range caps for ${id} are reversed or crossed`);
		return { id, start, end };
	}

	function recordMap(records) {
		const result = new Map();
		for (const raw of records) {
			if (typeof raw.id !== "string" || typeof raw.classId !== "string") {
				throw new TypeError("Range records need string id and classId fields");
			}
			if (raw.morphKey !== null && typeof raw.morphKey !== "string") {
				throw new TypeError("morphKey must be a string or null");
			}
			if (result.has(raw.id)) throw new Error(`Duplicate range record ${raw.id}`);
			result.set(raw.id, {
				id: raw.id,
				classId: raw.classId,
				morphKey: raw.morphKey,
				parentId: raw.parentId ?? null,
			});
		}
		return result;
	}

	function childRecords(records, parentId) {
		return Array.from(records.values()).filter((record) => record.parentId === parentId);
	}

	function componentIdentity(record) {
		return JSON.stringify([record.classId, record.morphKey]);
	}

	function elementKey(element) {
		return element?.nodeType === Node.ELEMENT_NODE
			? element.getAttribute("data-citry-key")
			: null;
	}

	function pathSegment(element) {
		// This must use exactly the same identity source as the Alpine key
		// callback below. An id-only wrapper is positional in this spike.
		const key = elementKey(element);
		if (key) return `${element.localName}#${JSON.stringify(key)}`;
		const siblings = Array.from(element.parentNode?.children || []);
		return `${element.localName}@${siblings.indexOf(element)}`;
	}

	function parentPath(pair, boundaryParent) {
		if (pair.start.parentNode === boundaryParent) return "";
		const segments = [];
		let current = pair.start.parentElement;
		while (current && current !== boundaryParent) {
			segments.push(pathSegment(current));
			current = current.parentElement;
		}
		if (current !== boundaryParent) return null;
		return segments.reverse().join("/");
	}

	function physicalWindowSignature(targetPair, pairs, normalizeRangeId, boundary) {
		const pairByStart = new Map();
		for (const pair of pairs.values()) {
			if (pair.start.parentNode === targetPair.start.parentNode) {
				pairByStart.set(pair.start, pair);
			}
		}
		const tokens = [];
		const boundedByPair =
			boundary?.start && targetPair.start.parentNode === boundary.start.parentNode;
		const boundaryParent = boundary?.start ? boundary.start.parentNode : boundary;
		const boundedByContainer =
			boundaryParent && targetPair.start.parentNode === boundaryParent;
		const stop = boundedByPair ? boundary.end : null;
		let node = boundedByPair
			? boundary.start.nextSibling
			: boundedByContainer
				? boundary.firstChild
				: targetPair.start.parentNode.firstChild;
		for (; node && node !== stop; ) {
			const range = pairByStart.get(node);
			if (range) {
				if (range === targetPair) {
					tokens.push("TARGET");
					break;
				}
				tokens.push(`RANGE:${normalizeRangeId(range.id)}`);
				node = range.end.nextSibling;
				continue;
			}
			if (node.nodeType === Node.ELEMENT_NODE) {
				tokens.push(
					`ELEMENT:${node.localName}:${JSON.stringify(elementKey(node) || null)}`,
				);
			} else if (node.nodeType === Node.TEXT_NODE) {
				tokens.push("TEXT");
			} else if (node.nodeType === Node.COMMENT_NODE) {
				tokens.push("COMMENT");
			} else {
				tokens.push(`NODE:${node.nodeType}:${node.nodeName}`);
			}
			node = node.nextSibling;
		}
		return JSON.stringify(tokens);
	}

	function cloneContents(pair) {
		const container = document.createElement("div");
		for (const node of nodesBetween(pair.start, pair.end)) {
			container.append(node.cloneNode(true));
		}
		return container;
	}

	function collapsePair(pair, slot, kind, oldId, newId) {
		const holder = document.createElement("template");
		holder.setAttribute(HOLDER, kind);
		holder.setAttribute(SLOT_KEY, slot);
		holder.dataset.oldId = oldId || "";
		holder.dataset.newId = newId || "";
		pair.start.before(holder);
		holder.content.append(...inclusiveNodes(pair));
		return holder;
	}

	function insertSentinel(pair, slot, side, oldId, newId) {
		const sentinel = document.createElement("template");
		sentinel.setAttribute(SENTINEL, side);
		sentinel.setAttribute(SLOT_KEY, slot);
		sentinel.dataset.oldId = oldId;
		sentinel.dataset.newId = newId;
		pair.start.before(sentinel);
		return sentinel;
	}

	function elementsWithin(pair, selector) {
		const found = [];
		for (const node of nodesBetween(pair.start, pair.end)) {
			if (node.nodeType !== Node.ELEMENT_NODE) continue;
			if (node.matches(selector)) found.push(node);
			found.push(...node.querySelectorAll(selector));
		}
		return found;
	}

	function expandHolders(pair) {
		for (const holder of elementsWithin(pair, `template[${HOLDER}]`)) {
			if (!holder.isConnected) continue;
			holder.before(holder.content);
			holder.remove();
		}
	}

	function removeSentinels(pair) {
		for (const sentinel of elementsWithin(pair, `template[${SENTINEL}]`)) {
			sentinel.remove();
		}
	}

	function contextualContainer(start, markup) {
		const range = document.createRange();
		range.setStartAfter(start);
		range.collapse(true);
		const fragment = range.createContextualFragment(markup);
		const container = start.parentElement?.cloneNode(false) || document.createElement("div");
		container.removeAttribute?.("id");
		container.append(fragment);
		return container;
	}

	function subtreeIds(records, rootId) {
		const ids = [];
		const visit = (id) => {
			ids.push(id);
			for (const child of childRecords(records, id)) visit(child.id);
		};
		visit(rootId);
		return ids;
	}

	class KeyedComponentRangeRegistry {
		constructor(host, records) {
			this.host = host;
			this.records = recordMap(records);
			this.instances = new Map();
			this.cleanupLog = [];
			this.decisionLog = [];
			this.warnings = [];
			this._anchorSequence = 0;
			for (const record of this.records.values()) {
				this.instances.set(record.id, {
					anchor: this._newAnchor(),
					record,
					...findPair(host, record.id),
				});
			}
			this._syncParents();
		}

		_newAnchor() {
			this._anchorSequence += 1;
			return {
				cleanupCount: 0,
				parentToken: null,
				state: {},
				token: `anchor-${this._anchorSequence}`,
			};
		}

		_syncParents() {
			for (const instance of this.instances.values()) {
				const parent = instance.record.parentId
					? this.instances.get(instance.record.parentId)
					: null;
				instance.anchor.parentToken = parent?.anchor.token ?? null;
			}
		}

		instance(id) {
			const instance = this.instances.get(id);
			if (!instance) throw new Error(`Unknown range instance ${id}`);
			return instance;
		}

		_plan(oldRootId, newRootId, incomingRecords) {
			const newToOld = new Map([[newRootId, oldRootId]]);
			const oldToNew = new Map([[oldRootId, newRootId]]);
			const visit = (oldParentId, newParentId) => {
				const oldChildren = childRecords(this.records, oldParentId);
				const newChildren = childRecords(incomingRecords, newParentId);
				const used = new Set();
				for (const child of newChildren) {
					if (child.morphKey === null) continue;
					const match = oldChildren.find(
						(candidate) =>
							!used.has(candidate.id) &&
							candidate.morphKey !== null &&
							candidate.classId === child.classId &&
							candidate.morphKey === child.morphKey,
					);
					if (!match) continue;
					used.add(match.id);
					newToOld.set(child.id, match.id);
					oldToNew.set(match.id, child.id);
					visit(match.id, child.id);
				}
				const identities = new Set(
					[...oldChildren, ...newChildren]
						.filter((record) => record.morphKey !== null)
						.map(componentIdentity),
				);
				for (const identity of identities) {
					const oldCount = oldChildren.filter(
						(record) =>
							record.morphKey !== null && componentIdentity(record) === identity,
					).length;
					const newCount = newChildren.filter(
						(record) =>
							record.morphKey !== null && componentIdentity(record) === identity,
					).length;
					if (oldCount > 1 || newCount > 1) {
						this.warnings.push(
							`Duplicate component key ${identity} matched in invocation order`,
						);
					}
				}
			};
			visit(oldRootId, newRootId);
			return { newToOld, oldToNew };
		}

		_pairMap(container, records, parentId) {
			const result = new Map();
			for (const child of childRecords(records, parentId)) {
				result.set(child.id, findPair(container, child.id));
			}
			return result;
		}

		_morphRange(oldPair, oldRecord, newPair, newRecord, context) {
			const fresh = cloneContents(newPair);
			const oldChildren = childRecords(this.records, oldRecord.id);
			const newChildren = childRecords(context.incomingRecords, newRecord.id);
			const oldPairs = this._pairMap(oldPair.start.parentNode, this.records, oldRecord.id);
			const newPairs = this._pairMap(fresh, context.incomingRecords, newRecord.id);
			const oldOrder = new Map(oldChildren.map((record, index) => [record.id, index]));
			const newOrder = new Map(newChildren.map((record, index) => [record.id, index]));
			const handledOld = new Set();
			const handledNew = new Set();
			const portableMatches = [];
			let slotSequence = 0;
			const oldWindowSignatures = new Map(
				oldChildren.map((record) => {
					const pair = oldPairs.get(record.id);
					return [
						record.id,
						physicalWindowSignature(
							pair,
							oldPairs,
							(id) => context.plan.oldToNew.get(id) || `old-only:${id}`,
							oldPair,
						),
					];
				}),
			);
			const newWindowSignatures = new Map(
				newChildren.map((record) => [
					record.id,
					physicalWindowSignature(newPairs.get(record.id), newPairs, (id) => id, fresh),
				]),
			);

			for (const nextRecord of newChildren) {
				const previousId = context.plan.newToOld.get(nextRecord.id);
				if (!previousId) continue;
				const previousRecord = this.records.get(previousId);
				if (previousRecord?.parentId !== oldRecord.id) continue;
				const previousPair = oldPairs.get(previousId);
				const nextPair = newPairs.get(nextRecord.id);
				const previousPath = parentPath(previousPair, oldPair.start.parentNode);
				const nextPath = parentPath(nextPair, fresh);
				const sameWindow = previousPath !== null && previousPath === nextPath;
				const stationary =
					oldOrder.get(previousId) === newOrder.get(nextRecord.id) &&
					sameWindow &&
					oldWindowSignatures.get(previousId) ===
						newWindowSignatures.get(nextRecord.id);
				this.decisionLog.push({
					newId: nextRecord.id,
					newOrder: newOrder.get(nextRecord.id),
					newWindow: newWindowSignatures.get(nextRecord.id),
					oldId: previousId,
					oldOrder: oldOrder.get(previousId),
					oldWindow: oldWindowSignatures.get(previousId),
					sameWindow,
					stationary,
				});
				const slot = `matched:${context.operation}:${slotSequence++}`;
				if (stationary) {
					insertSentinel(previousPair, slot, "old", previousId, nextRecord.id);
					insertSentinel(nextPair, slot, "new", previousId, nextRecord.id);
				} else if (sameWindow) {
					collapsePair(previousPair, slot, "old", previousId, nextRecord.id);
					collapsePair(nextPair, slot, "new", previousId, nextRecord.id);
				} else {
					const portableToken = `portable:${context.operation}:${slotSequence++}`;
					const previousHolder = collapsePair(
						previousPair,
						`${portableToken}:old`,
						"portable-old",
						previousId,
						nextRecord.id,
					);
					const nextHolder = collapsePair(
						nextPair,
						`${portableToken}:new`,
						"portable-new",
						previousId,
						nextRecord.id,
					);
					previousHolder.setAttribute(PORTABLE, portableToken);
					previousHolder.dataset.portableSide = "old";
					nextHolder.setAttribute(PORTABLE, portableToken);
					nextHolder.dataset.portableSide = "new";
					portableMatches.push({
						nextId: nextRecord.id,
						portableToken,
						previousHolder,
						previousId,
					});
				}
				handledOld.add(previousId);
				handledNew.add(nextRecord.id);
			}

			for (const previousRecord of oldChildren) {
				if (handledOld.has(previousRecord.id)) continue;
				collapsePair(
					oldPairs.get(previousRecord.id),
					`removed:${context.operation}:${slotSequence++}`,
					"old-unmatched",
					previousRecord.id,
					"",
				);
			}
			for (const nextRecord of newChildren) {
				if (handledNew.has(nextRecord.id)) continue;
				collapsePair(
					newPairs.get(nextRecord.id),
					`added:${context.operation}:${slotSequence++}`,
					"new-unmatched",
					"",
					nextRecord.id,
				);
			}

			Alpine.morphBetween(oldPair.start, oldPair.end, fresh, {
				key: (element) => element.getAttribute(SLOT_KEY) || elementKey(element),
				updating: (from, to, _childrenOnly, skip, _skipChildren, skipUntil) => {
					if (from?.hasAttribute?.(SENTINEL) && to?.hasAttribute?.(SENTINEL)) {
						const previousId = from.dataset.oldId;
						const nextId = to.dataset.newId;
						const previousPair = oldPairs.get(previousId);
						const nextPair = newPairs.get(nextId);
						this._morphRange(
							previousPair,
							this.records.get(previousId),
							nextPair,
							context.incomingRecords.get(nextId),
							context,
						);
						// Stop on the two end caps, not the nodes after them. Alpine
						// computes sibling keys before applying skipUntil; consuming the
						// end comments makes the next iteration recompute keys for the
						// first ordinary siblings after this virtual node.
						skipUntil((node) => node === previousPair.end || node === nextPair.end);
						skip();
						return;
					}
					if (from?.hasAttribute?.(HOLDER) && to?.hasAttribute?.(HOLDER)) {
						if (from.dataset.oldId && to.dataset.newId) {
							const previousId = from.dataset.oldId;
							const nextId = to.dataset.newId;
							this._morphRange(
								findPair(from.content, previousId),
								this.records.get(previousId),
								findPair(to.content, nextId),
								context.incomingRecords.get(nextId),
								context,
							);
						}
						skip();
					}
				},
			});

			for (const portable of portableMatches) {
				const destination = elementsWithin(
					oldPair,
					`template[${PORTABLE}="${CSS.escape(portable.portableToken)}"]`,
				).find((element) => element.dataset.portableSide === "new");
				if (!destination) {
					throw new Error(`Portable range destination vanished for ${portable.nextId}`);
				}
				this._morphRange(
					findPair(portable.previousHolder.content, portable.previousId),
					this.records.get(portable.previousId),
					findPair(destination.content, portable.nextId),
					context.incomingRecords.get(portable.nextId),
					context,
				);
				destination.replaceWith(portable.previousHolder);
			}

			expandHolders(oldPair);
			removeSentinels(oldPair);
			oldPair.start.data = marker("start", newRecord.id);
			oldPair.end.data = marker("end", newRecord.id);
			context.livePairs.set(newRecord.id, {
				id: newRecord.id,
				start: oldPair.start,
				end: oldPair.end,
			});
		}

		morph(oldRootId, incomingMarkup, incomingRecordsRaw, incomingRootId) {
			const oldRoot = this.instance(oldRootId);
			const incomingRecords = recordMap(incomingRecordsRaw);
			const incomingRoot = incomingRecords.get(incomingRootId);
			if (!incomingRoot) throw new Error(`Missing incoming root ${incomingRootId}`);
			if (oldRoot.record.classId !== incomingRoot.classId) {
				throw new Error("The explicitly correlated render root changed component class");
			}
			// A self-render root has no parent invocation. Carry its parent-authored
			// key on the stable logical record instead of restamping a DOM root.
			if (incomingRoot.morphKey === null && oldRoot.record.morphKey !== null) {
				incomingRoot.morphKey = oldRoot.record.morphKey;
			}
			if (incomingRoot.parentId === null && oldRoot.record.parentId !== null) {
				incomingRoot.parentId = oldRoot.record.parentId;
			}
			const parsed = contextualContainer(oldRoot.start, incomingMarkup);
			const incomingPair = findPair(parsed, incomingRootId);
			const plan = this._plan(oldRootId, incomingRootId, incomingRecords);
			const context = {
				incomingRecords,
				livePairs: new Map(),
				operation: `${oldRootId}->${incomingRootId}`,
				plan,
			};
			const oldSubtree = subtreeIds(this.records, oldRootId);
			const incomingSubtree = subtreeIds(incomingRecords, incomingRootId);

			this._morphRange(
				{ id: oldRootId, start: oldRoot.start, end: oldRoot.end },
				oldRoot.record,
				incomingPair,
				incomingRoot,
				context,
			);

			const reusedOld = new Set(plan.newToOld.values());
			for (const id of oldSubtree) {
				if (reusedOld.has(id)) continue;
				const instance = this.instances.get(id);
				if (!instance) continue;
				instance.anchor.cleanupCount += 1;
				this.cleanupLog.push(instance.anchor.token);
			}

			const survivors = new Map(this.instances);
			for (const id of oldSubtree) survivors.delete(id);
			for (const id of incomingSubtree) {
				const record = incomingRecords.get(id);
				const previousId = plan.newToOld.get(id);
				const previous = previousId ? this.instances.get(previousId) : null;
				const pair = context.livePairs.get(id) || findPair(this.host, id);
				survivors.set(id, {
					anchor: previous?.anchor || this._newAnchor(),
					record,
					...pair,
				});
			}
			this.instances = survivors;
			this.records = new Map([
				...Array.from(this.records.entries()).filter(([id]) => !oldSubtree.includes(id)),
				...incomingSubtree.map((id) => [id, incomingRecords.get(id)]),
			]);
			this._syncParents();
			return this.instance(incomingRootId);
		}
	}

	function inertIslandControl(host, outerId, oldChildId, incomingMarkup, newChildId) {
		const outer = findPair(host, outerId);
		const oldChild = findPair(host, oldChildId);
		const oldHolder = collapsePair(oldChild, "control:shared", "old", oldChildId, newChildId);
		const parsed = contextualContainer(outer.start, incomingMarkup);
		const incomingOuter = findPair(parsed, `${outerId}-fresh`);
		const fresh = cloneContents(incomingOuter);
		const newChild = findPair(fresh, newChildId);
		collapsePair(newChild, "control:shared", "new", oldChildId, newChildId);
		Alpine.morphBetween(outer.start, outer.end, fresh, {
			key: (element) => element.getAttribute(SLOT_KEY) || elementKey(element),
		});
		if (oldHolder.isConnected) {
			oldHolder.before(oldHolder.content);
			oldHolder.remove();
		}
		return nodesBetween(outer.start, outer.end)
			.filter((node) => node.nodeType !== Node.COMMENT_NODE)
			.map((node) => node.textContent)
			.join("");
	}

	window.KeyedComponentRangeSpike = {
		KeyedComponentRangeRegistry,
		findPair,
		inertIslandControl,
		marker,
		nodesBetween,
		rangeMarkup,
	};
})();
