"""Private browser coordinator shared by anchored Citry UI surfaces."""

from citry.ext.dependencies import Script

_ANCHORED_LAYER_RUNTIME_SOURCE = r"""
      const anchoredLayerRuntime = (() => {
        const runtimeKey = Symbol.for("citry-ui:anchored-layer-runtime");
        const runtimeGeneration = 3;
        const ancestorCloseCapability = "ancestor-close-transaction-v1";
        const installed = globalThis[runtimeKey];
        if (
          installed?.generation === runtimeGeneration
          && installed?.capabilities?.includes?.(ancestorCloseCapability)
        ) {
          return installed;
        }
        if (installed !== undefined) {
          throw new Error(
            "[citry-ui] cannot replace an incompatible anchored-layer runtime; "
              + "a full page reload is required.",
          );
        }

        const coordinators = new WeakMap();
        const activeCoordinators = new Set();
        const stats = installed?.stats ?? {
          listenerSets: 0,
          reconciliations: 0,
        };
        stats.activeListenerSets ??= 0;
        stats.activeCoordinators ??= 0;

        const isOpenShadowRoot = (value) => (
          value instanceof ShadowRoot && value.host.shadowRoot === value
        );
        const actualRoot = (element) => {
          const root = element?.getRootNode?.() ?? null;
          if (root instanceof Document || isOpenShadowRoot(root)) {
            return root;
          }
          return null;
        };
        const composedParent = (node) => {
          if (node?.parentNode) {
            return node.parentNode;
          }
          const root = node?.getRootNode?.() ?? null;
          return root instanceof ShadowRoot ? root.host : null;
        };
        const composedContains = (container, target) => {
          if (!(container instanceof Node) || !(target instanceof Node)) {
            return false;
          }
          let current = target;
          while (current) {
            if (current === container || container.contains(current)) {
              return true;
            }
            const root = current.getRootNode?.() ?? null;
            if (root instanceof ShadowRoot && root !== container) {
              current = root.host;
              continue;
            }
            current = composedParent(current);
          }
          return false;
        };
        const composedAncestors = (node) => {
          const ancestors = [];
          let current = node;
          while (current) {
            ancestors.push(current);
            const root = current.getRootNode?.() ?? null;
            if (root instanceof ShadowRoot && current === root) {
              current = root.host;
            } else {
              current = composedParent(current);
            }
          }
          return ancestors;
        };
        const layerElements = (layer) => [
          layer.trigger,
          layer.surface,
          ...(layer.insideElements ?? []),
        ].filter((value) => value instanceof Node);

        const createCoordinator = (ownerDocument) => {
          const layers = [];
          const scopes = new Map();
          const discoveredRoots = new Set();
          const processedEvents = new WeakSet();
          const modalSequence = new WeakMap();
          const modalOpenState = new WeakMap();
          const ancestorCloseTransactions = new Set();
          let nextModalSequence = 0;
          let nextRegistrationGeneration = 0;
          let bootstrappedModals = false;
          let bootstrapAmbiguous = false;
          let currentModal = null;
          let rootsDirty = true;
          let pendingPointerFocus = null;
          let pointerFocusTimer = null;

          const coordinator = {
            ownerDocument,
            layers,
            tooltipLayer: null,
            tooltipWarmUntil: 0,
          };

          const discoverOpenRoots = () => {
            if (!rootsDirty) {
              return;
            }
            for (const root of discoveredRoots) {
              if (!root.host.isConnected || root.host.ownerDocument !== ownerDocument) {
                discoveredRoots.delete(root);
              }
            }
            const pending = [ownerDocument, ...discoveredRoots];
            const visited = new Set();
            while (pending.length > 0) {
              const root = pending.pop();
              if (visited.has(root)) {
                continue;
              }
              visited.add(root);
              for (const element of root.querySelectorAll?.("*") ?? []) {
                if (isOpenShadowRoot(element.shadowRoot)) {
                  discoveredRoots.add(element.shadowRoot);
                  pending.push(element.shadowRoot);
                }
              }
            }
            rootsDirty = false;
          };
          const knownRoots = () => {
            discoverOpenRoots();
            const roots = new Set([ownerDocument, ...discoveredRoots]);
            for (const layer of layers) {
              const root = actualRoot(layer.surface) ?? actualRoot(layer.trigger);
              if (root) {
                roots.add(root);
              }
            }
            return roots;
          };
          const allModalDialogs = () => {
            const dialogs = [];
            for (const root of knownRoots()) {
              try {
                dialogs.push(...root.querySelectorAll("dialog:modal"));
              } catch {
                // Current supported browsers implement :modal. Treat an
                // unavailable selector as no eligible modal rather than
                // guessing from the open attribute.
              }
            }
            return [...new Set(dialogs)];
          };
          const deepActiveElement = () => {
            let active = ownerDocument.activeElement;
            while (active?.shadowRoot?.activeElement) {
              active = active.shadowRoot.activeElement;
            }
            return active;
          };
          const modalContaining = (node, dialogs) => {
            const matches = dialogs.filter((dialog) => composedContains(dialog, node));
            if (matches.length === 0) {
              return null;
            }
            return matches.reduce((latest, dialog) => (
              (modalSequence.get(dialog) ?? 0) >= (modalSequence.get(latest) ?? 0)
                ? dialog
                : latest
            ));
          };
          const recordModalTransition = (dialog, explicitState = null) => {
            if (!(dialog instanceof HTMLDialogElement)) {
              return;
            }
            const isModal = explicitState ?? dialog.matches(":modal");
            const wasModal = modalOpenState.get(dialog) === true;
            modalOpenState.set(dialog, isModal);
            if (!isModal) {
              if (currentModal === dialog) {
                currentModal = null;
              }
              return;
            }
            if (wasModal) {
              return;
            }
            modalSequence.set(dialog, ++nextModalSequence);
            bootstrapAmbiguous = false;
            currentModal = dialog;
          };

          const descendantsOf = (layer) => layers.filter((candidate) => {
            let parent = candidate.__citryAnchoredParent ?? null;
            const seen = new Set();
            while (parent && !seen.has(parent)) {
              seen.add(parent);
              if (parent === layer) {
                return true;
              }
              parent = parent.__citryAnchoredParent ?? null;
            }
            return false;
          });
          const forceClose = (layer, reason, source) => {
            layer.__citryAnchoredSuppressed = true;
            layer.__citryAnchoredBlockedReason = reason;
            layer.__citryAnchoredRegistration = null;
            layer.forceClose?.(reason, source);
            const index = layers.indexOf(layer);
            if (index !== -1) {
              layers.splice(index, 1);
            }
          };
          const closeDescendants = (layer, reason = "ancestor", source = layer.surface) => {
            const descendants = descendantsOf(layer);
            for (let index = descendants.length - 1; index >= 0; index -= 1) {
              const descendant = descendants[index];
              if (layers.includes(descendant)) {
                forceClose(descendant, reason, source);
              }
            }
            syncScopes();
          };

          const reconcileModal = (event = null) => {
            stats.reconciliations += 1;
            const eventPath = event?.composedPath?.() ?? [];
            const pathHasModal = eventPath.some((node) => (
              node instanceof HTMLDialogElement && node.matches(":modal")
            ));
            if (pathHasModal) {
              for (const node of eventPath) {
                if (isOpenShadowRoot(node)) {
                  discoveredRoots.add(node);
                }
              }
            }
            const dialogs = allModalDialogs();
            if (!bootstrappedModals) {
              bootstrappedModals = true;
              if (dialogs.length === 1) {
                modalSequence.set(dialogs[0], ++nextModalSequence);
                currentModal = dialogs[0];
              } else if (dialogs.length > 1) {
                bootstrapAmbiguous = true;
                currentModal = null;
              }
              for (const dialog of dialogs) {
                modalOpenState.set(dialog, true);
              }
            }

            const newlyDiscovered = dialogs.filter((dialog) => (
              modalOpenState.get(dialog) !== true
            ));
            if (newlyDiscovered.length === 1) {
              const dialog = newlyDiscovered[0];
              modalOpenState.set(dialog, true);
              modalSequence.set(dialog, ++nextModalSequence);
              bootstrapAmbiguous = false;
              currentModal = dialog;
            } else if (newlyDiscovered.length > 1) {
              for (const dialog of newlyDiscovered) {
                modalOpenState.set(dialog, true);
              }
              bootstrapAmbiguous = true;
              currentModal = null;
            }

            const eventDialog = eventPath
              .filter((node) => node instanceof HTMLDialogElement && dialogs.includes(node))
              .at(0) ?? null;
            const focusDialog = modalContaining(deepActiveElement(), dialogs);
            if (dialogs.length === 0) {
              currentModal = null;
              bootstrapAmbiguous = false;
            } else if (bootstrapAmbiguous && (eventDialog || focusDialog)) {
              // An event can resolve unknown initial order. It must not
              // promote a modal whose open transition was already observed.
              bootstrapAmbiguous = false;
              currentModal = eventDialog ?? focusDialog;
              if (!modalSequence.has(currentModal)) {
                modalSequence.set(currentModal, ++nextModalSequence);
              }
            } else if (!bootstrapAmbiguous) {
              if (!currentModal || !dialogs.includes(currentModal)) {
                currentModal = dialogs.reduce((latest, dialog) => (
                  (modalSequence.get(dialog) ?? 0) >= (modalSequence.get(latest) ?? 0)
                    ? dialog
                    : latest
                ));
              }
            }

            if (currentModal && !dialogs.includes(currentModal)) {
              currentModal = null;
            }

            for (const layer of [...layers]) {
              if (!layers.includes(layer)) {
                continue;
              }
              if (!structurallyEligible(layer)) {
                forceClose(layer, "ancestor", event?.target ?? currentModal);
                continue;
              }
              if (
                bootstrapAmbiguous
                || (currentModal && !composedContains(currentModal, layer.trigger))
              ) {
                forceClose(layer, "modal", currentModal);
              }
            }
            syncScopes(true);
            return { current: currentModal, ambiguous: bootstrapAmbiguous };
          };

          const inferLogicalParent = (layer) => {
            if (layer.logicalParent) {
              return layer.logicalParent;
            }
            const childElements = layerElements(layer);
            for (let index = layers.length - 1; index >= 0; index -= 1) {
              const candidate = layers[index];
              if (candidate === layer || !candidate.isOpen()) {
                continue;
              }
              if (layerElements(candidate).some((parentElement) => (
                childElements.some((childElement) => composedContains(parentElement, childElement))
              ))) {
                return candidate;
              }
            }
            return null;
          };
          const structurallyEligible = (layer) => {
            if (
              !layer.trigger?.isConnected
              || !layer.surface?.isConnected
              || !actualRoot(layer.trigger)
              || !actualRoot(layer.surface)
              || layer.trigger.getClientRects().length === 0
              || (layer.isEligible && !layer.isEligible())
            ) {
              return false;
            }
            const activeSurface = layer.isOpen?.() === true;
            if (activeSurface) {
              const surfaceStyle = getComputedStyle(layer.surface);
              if (
                layer.surface.getClientRects().length === 0
                || surfaceStyle.visibility === "hidden"
                || surfaceStyle.visibility === "collapse"
              ) {
                return false;
              }
            }
            const ancestors = new Set([
              ...composedAncestors(layer.trigger),
              ...composedAncestors(layer.surface),
            ]);
            for (const ancestor of ancestors) {
              if (!(ancestor instanceof Element)) {
                continue;
              }
              const inactiveSurface = ancestor === layer.surface && !activeSurface;
              if (!inactiveSurface && (ancestor.hidden || ancestor.inert)) {
                return false;
              }
              if (ancestor instanceof HTMLDialogElement && !ancestor.open) {
                return false;
              }
              if (
                ancestor !== layer.surface
                && ancestor.hasAttribute("popover")
                && !ancestor.matches(":popover-open")
              ) {
                return false;
              }
            }
            const parent = layer.logicalParent ?? layer.__citryAnchoredParent ?? inferLogicalParent(layer);
            if (parent && (!layers.includes(parent) || !parent.isOpen())) {
              return false;
            }
            return true;
          };
          const mayOpen = (layer) => {
            const modal = reconcileModal();
            if (layer.__citryAnchoredSuppressed) {
              return false;
            }
            if (!structurallyEligible(layer)) {
              layer.__citryAnchoredSuppressed = true;
              layer.__citryAnchoredBlockedReason = "ancestor";
              return false;
            }
            if (modal.ambiguous) {
              layer.__citryAnchoredSuppressed = true;
              layer.__citryAnchoredBlockedReason = "modal";
              return false;
            }
            if (modal.current && !composedContains(modal.current, layer.trigger)) {
              layer.__citryAnchoredSuppressed = true;
              layer.__citryAnchoredBlockedReason = "modal";
              return false;
            }
            layer.__citryAnchoredBlockedReason = null;
            return true;
          };

          const containsEvent = (layer, event) => {
            const path = event?.composedPath?.() ?? [];
            let current = layer;
            const seen = new Set();
            while (current && !seen.has(current)) {
              seen.add(current);
              for (const element of layerElements(current)) {
                if (path.includes(element)) {
                  return true;
                }
                if (path.some((node) => composedContains(element, node))) {
                  return true;
                }
              }
              current = current.__citryAnchoredParent ?? null;
            }
            return false;
          };
          const topLayer = () => {
            for (let index = layers.length - 1; index >= 0; index -= 1) {
              const candidate = layers[index];
              if (candidate.isOpen()) {
                return candidate;
              }
            }
            return null;
          };
          const isAncestorClosing = (layer) => (
            [...ancestorCloseTransactions].some((transaction) => (
              transaction.layers.has(layer)
            ))
          );

          const localScopeForEvent = (event) => {
            const path = event.composedPath?.() ?? [];
            return path.find((node) => node instanceof ShadowRoot && scopes.has(node))
              ?? ownerDocument;
          };
          const handleEvent = (scopeRoot, event) => {
            if (scopeRoot === ownerDocument && localScopeForEvent(event) !== ownerDocument) {
              return;
            }
            if (scopeRoot !== localScopeForEvent(event) || processedEvents.has(event)) {
              return;
            }
            processedEvents.add(event);
            reconcileModal(event);
            if (event.type === "focusin" && pendingPointerFocus) {
              const pointerTarget = pendingPointerFocus.target;
              const focusTarget = event.composedPath?.()[0] ?? event.target;
              const labelControl = pointerTarget instanceof HTMLLabelElement
                ? pointerTarget.control
                : null;
              const followsPointer = (
                composedContains(pointerTarget, focusTarget)
                || composedContains(focusTarget, pointerTarget)
                || labelControl === focusTarget
              );
              pendingPointerFocus = null;
              clearTimeout(pointerFocusTimer);
              pointerFocusTimer = null;
              if (followsPointer) {
                return;
              }
            }
            const layer = topLayer();
            if (!layer) {
              return;
            }
            if (
              event.type === "focusin"
              && isAncestorClosing(layer)
            ) {
              // An ancestor such as Disclosure must move focus before it can
              // make the owned subtree inert. Preserve that focus ordering and
              // let the transaction deliver the structural forced close.
              return;
            }
            if (event.type === "keydown") {
              if (event.key !== "Escape" || event.isComposing) {
                return;
              }
              event.preventDefault();
              const registration = layer.__citryAnchoredRegistration;
              queueMicrotask(() => {
                if (
                  registration
                  && layer.__citryAnchoredRegistration === registration
                  && layers.includes(layer)
                  && layer.isOpen()
                ) {
                  layer.requestDismiss("escape", event.target);
                }
              });
              return;
            }
            if (containsEvent(layer, event)) {
              return;
            }
            if (event.type === "pointerdown") {
              pendingPointerFocus = {
                layer,
                registration: layer.__citryAnchoredRegistration,
                target: event.composedPath?.()[0] ?? event.target,
              };
              clearTimeout(pointerFocusTimer);
              pointerFocusTimer = setTimeout(() => {
                pendingPointerFocus = null;
                pointerFocusTimer = null;
              }, 0);
            }
            layer.requestDismiss(
              event.type === "pointerdown" ? "outside" : "focus-outside",
              event.target,
            );
          };

          const attachScope = (root) => {
            const pointerdown = (event) => handleEvent(root, event);
            const focusin = (event) => handleEvent(root, event);
            const keydown = (event) => handleEvent(root, event);
            const beforetoggle = (event) => {
              if (
                event.target instanceof HTMLDialogElement
                && event.oldState === "open"
                && event.newState === "closed"
              ) {
                // `beforetoggle` is the only synchronous standards signal for
                // a close/open generation completed in one JavaScript task.
                recordModalTransition(event.target, false);
              }
            };
            const toggle = (event) => {
              if (event.target instanceof HTMLDialogElement) {
                if (event.oldState === "open" && event.newState === "open") {
                  recordModalTransition(event.target, false);
                }
                const explicitState = event.newState === "closed"
                  ? false
                  : event.target.matches(":modal");
                recordModalTransition(event.target, explicitState);
              }
              reconcileModal(event);
            };
            root.addEventListener("pointerdown", pointerdown, true);
            root.addEventListener("focusin", focusin, true);
            root.addEventListener("keydown", keydown, true);
            root.addEventListener("beforetoggle", beforetoggle, true);
            root.addEventListener("toggle", toggle, true);
            const observer = new MutationObserver((records) => {
              for (const record of records) {
                if (record.type === "childList") {
                  rootsDirty = true;
                }
                if (
                  record.attributeName === "open"
                  && record.target instanceof HTMLDialogElement
                ) {
                  const explicitState = record.oldValue !== null
                    ? false
                    : record.target.matches(":modal");
                  recordModalTransition(record.target, explicitState);
                }
              }
              reconcileModal();
            });
            observer.observe(root, {
              attributes: true,
              attributeOldValue: true,
              attributeFilter: ["open", "hidden", "inert", "style", "class"],
              childList: true,
              subtree: true,
            });
            scopes.set(root, {
              pointerdown,
              focusin,
              keydown,
              beforetoggle,
              toggle,
              observer,
            });
            stats.listenerSets += 1;
            stats.activeListenerSets += 1;
          };
          const detachScope = (root, record) => {
            root.removeEventListener("pointerdown", record.pointerdown, true);
            root.removeEventListener("focusin", record.focusin, true);
            root.removeEventListener("keydown", record.keydown, true);
            root.removeEventListener("beforetoggle", record.beforetoggle, true);
            root.removeEventListener("toggle", record.toggle, true);
            record.observer.disconnect();
            scopes.delete(root);
            stats.activeListenerSets -= 1;
          };
          function syncScopes(preserveModal = false) {
            const desired = layers.length > 0 ? knownRoots() : new Set();
            for (const [root, record] of scopes) {
              if (!desired.has(root)) {
                detachScope(root, record);
              }
            }
            for (const root of desired) {
              if (!scopes.has(root)) {
                attachScope(root);
              }
            }
            if (layers.length > 0) {
              activeCoordinators.add(coordinator);
            } else {
              activeCoordinators.delete(coordinator);
              pendingPointerFocus = null;
              clearTimeout(pointerFocusTimer);
              pointerFocusTimer = null;
              discoveredRoots.clear();
              rootsDirty = true;
              if (!preserveModal) {
                currentModal = null;
                bootstrappedModals = false;
                bootstrapAmbiguous = false;
              }
            }
            stats.activeCoordinators = activeCoordinators.size;
          }

          coordinator.containsEvent = containsEvent;
          coordinator.topLayer = topLayer;
          coordinator.mayOpen = mayOpen;
          coordinator.deepActiveElement = deepActiveElement;
          coordinator.isAncestorClosing = isAncestorClosing;
          coordinator.blockedReason = (layer) => (
            layer.__citryAnchoredBlockedReason ?? null
          );
          coordinator.clearSuppression = (layer) => {
            layer.__citryAnchoredSuppressed = false;
            layer.__citryAnchoredBlockedReason = null;
          };
          /* citry-ui:command-palette-attribution:dialog-layer-preparation:begin */
          coordinator.prepareModal = (container, source = container) => {
            if (!(container instanceof HTMLDialogElement)) {
              throw new TypeError(
                "[citry-ui] anchored-layer modal preparation requires a native Dialog.",
              );
            }
            for (let index = layers.length - 1; index >= 0; index -= 1) {
              const layer = layers[index];
              if (
                layer.isOpen?.()
                && !layerElements(layer).some((element) => composedContains(container, element))
              ) {
                forceClose(layer, "modal", source);
              }
            }
            syncScopes();
          };
          /* citry-ui:command-palette-attribution:dialog-layer-preparation:end */
          coordinator.beginAncestorClose = (container, source = container) => {
            if (!(container instanceof Element)) {
              throw new TypeError(
                "[citry-ui] an anchored-layer ancestor close requires an Element container.",
              );
            }
            const transaction = {
              layers: new Set(layers.filter((layer) => (
                layer.isOpen?.()
                && layerElements(layer).some((element) => composedContains(container, element))
              ))),
              settled: false,
            };
            ancestorCloseTransactions.add(transaction);
            const settle = (commit) => {
              if (transaction.settled) {
                return;
              }
              transaction.settled = true;
              ancestorCloseTransactions.delete(transaction);
              if (!commit) {
                return;
              }
              for (let index = layers.length - 1; index >= 0; index -= 1) {
                const layer = layers[index];
                if (transaction.layers.has(layer) && layer.isOpen?.()) {
                  forceClose(layer, "ancestor", source);
                }
              }
              syncScopes();
            };
            return {
              commit: () => settle(true),
              cancel: () => settle(false),
            };
          };
          coordinator.closeDescendants = closeDescendants;
          coordinator.register = (layer) => {
            if (!mayOpen(layer)) {
              return false;
            }
            const oldIndex = layers.indexOf(layer);
            if (oldIndex === -1) {
              layer.__citryAnchoredRegistration = {
                generation: ++nextRegistrationGeneration,
              };
              layers.push(layer);
            }
            const nextParents = new Map(
              layers.map((candidate) => [
                candidate,
                candidate.logicalParent ?? inferLogicalParent(candidate),
              ]),
            );
            for (const [candidate, parent] of nextParents) {
              candidate.__citryAnchoredParent = parent;
            }
            syncScopes();
            return true;
          };
          coordinator.unregister = (layer, options = {}) => {
            const {
              reason = "ancestor",
              source = layer.surface,
              cascade = true,
            } = options;
            if (cascade) {
              closeDescendants(layer, reason, source);
            }
            const index = layers.indexOf(layer);
            if (index !== -1) {
              layers.splice(index, 1);
            }
            layer.__citryAnchoredParent = null;
            layer.__citryAnchoredRegistration = null;
            syncScopes();
          };
          coordinator.dispose = () => {
            ancestorCloseTransactions.clear();
            for (const layer of [...layers].reverse()) {
              forceClose(layer, "ancestor", ownerDocument);
            }
            syncScopes();
          };
          return coordinator;
        };

        const runtime = {
          version: runtimeGeneration,
          generation: runtimeGeneration,
          capabilities: Object.freeze([ancestorCloseCapability]),
          stats,
          coordinatorFor(element) {
            const ownerDocument = element?.ownerDocument;
            if (!(ownerDocument instanceof Document)) {
              throw new Error(
                "[citry-ui] anchored layers require an element with an ownerDocument.",
              );
            }
            let coordinator = coordinators.get(ownerDocument);
            if (!coordinator) {
              coordinator = createCoordinator(ownerDocument);
              coordinators.set(ownerDocument, coordinator);
            }
            return coordinator;
          },
          composedContains,
        };
        Object.defineProperties(runtime, {
          layers: {
            enumerable: true,
            get: () => [...activeCoordinators].flatMap((coordinator) => coordinator.layers),
          },
          listeners: {
            enumerable: true,
            get: () => (stats.activeListenerSets > 0 ? {} : null),
          },
        });
        globalThis[runtimeKey] = runtime;
        return runtime;
      })();
"""

ANCHORED_LAYER_RUNTIME_DEPENDENCY = Script(
    content=_ANCHORED_LAYER_RUNTIME_SOURCE,
    wrap=True,
)

ANCHORED_LAYER_RUNTIME_JS = r"""
      const anchoredLayerRuntime = globalThis[
        Symbol.for("citry-ui:anchored-layer-runtime")
      ];
      if (
        anchoredLayerRuntime?.generation !== 3
        || !anchoredLayerRuntime?.capabilities?.includes?.(
          "ancestor-close-transaction-v1",
        )
      ) {
        throw new Error("[citry-ui] anchored-layer runtime dependency did not load.");
      }
"""
