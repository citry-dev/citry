(function() {

      const anchoredLayerRuntimeCompatible = globalThis[
        Symbol.for("citry-ui:anchored-layer-runtime-compatible")
      ] === true;
      const anchoredLayerRuntime = globalThis[
        Symbol.for("citry-ui:anchored-layer-runtime")
      ];

      const hideNativePopover = (element) => {
        if (!element?.matches?.(":popover-open")) return;
        try {
          HTMLElement.prototype.hidePopover.call(element);
        } catch {
          element.removeAttribute("popover");
        }
      };
      const createMenuService = () => {
        const service = {registrations: new Map(), radioStates: new Map(), controller: null};
        service.register = (entry) => {
          entry.context ??= service;
          service.registrations.set(entry.root, entry);
          service.controller?.attach(entry);
          return () => {
            if (service.registrations.get(entry.root) !== entry) return;
            service.controller?.detach(entry);
            service.registrations.delete(entry.root);
          };
        };
        service.bind = (context) => {
          service.controller = context;
          for (const entry of service.registrations.values()) context.attach(entry);
        };
        service.claimRadioState = (serverValue, path, identity) => {
          const key = identity ?? JSON.stringify([path, serverValue]);
          if (!service.radioStates.has(key)) service.radioStates.set(key, {
            current: serverValue, serverValue, priorOrder: [], pendingRemoval: null,
            controlled: false,
          });
          return service.radioStates.get(key);
        };
        service.releaseRadioState = (identity) => service.radioStates.delete(identity);
        service.child = (options, parent = null) => {
          const child = {...options, identity: Symbol("citry-ui:menu-child")};
          for (const name of ["surface", "container", "parentSubmenu", "radioGroup", "rootLayer"]) {
            let overridden = Object.hasOwn(options, name);
            let localValue = options[name];
            delete child[name];
            Object.defineProperty(child, name, {
              get: () => overridden ? localValue : (parent ?? service)[name],
              set: (value) => {
                overridden = true;
                localValue = value;
              },
            });
          }
          let localPath = [...(options.path ?? [])];
          delete child.path;
          Object.defineProperty(child, "path", {
            get: () => [...(parent?.path ?? []), ...localPath],
            set: (path) => {
              const parentPath = parent?.path ?? [];
              localPath = (
                path.length >= parentPath.length
                && parentPath.every((value, index) => path[index] === value)
              ) ? path.slice(parentPath.length) : [...path];
            },
          });
          child.setOptions = (next) => {
            Object.assign(child, next);
            for (const entry of service.registrations.values()) {
              if (entry.context === child) service.controller?.attach(entry);
            }
          };
          child.register = (entry) => { entry.context ??= child; return service.register(entry); };
          child.child = (options) => service.child(options, child);
          for (const name of ["update", "entries", "addSubmenu",
            "openSubmenu", "closeSubmenu", "dismissFromSubmenu", "size", "defer",
            "claimRadioState", "releaseRadioState"]) child[name] = (...args) => service[name](...args);
          return child;
        };
        for (const name of [
          "update", "entries", "addSubmenu", "openSubmenu", "closeSubmenu",
          "dismissFromSubmenu", "size", "defer",
        ]) service[name] = (...args) => service.controller?.[name](...args);
        for (const name of [
          "surface", "container", "path", "parentSubmenu", "radioGroup", "rootLayer",
        ]) Object.defineProperty(service, name, {get: () => service.controller?.[name]});
        service.dispose = () => {
          for (const entry of service.registrations.values()) service.controller?.detach(entry);
          service.controller = null;
          service.registrations.clear();
          service.radioStates.clear();
        };
        return service;
      };
      const createCompoundAnatomy = (root, data, changed) => {
        const children = [...root.children];
        const primary = children[0];
        const trigger = children[1];
        const surface = children[2];
        if (
          children.length !== 3
          || !(primary instanceof HTMLButtonElement)
          || !(trigger instanceof HTMLButtonElement)
          || !(surface instanceof HTMLDivElement)
          || primary.dataset.citryUiPart !== "split-button-primary"
          || trigger.dataset.citryUiPart !== "split-button-menu-trigger"
          || surface.dataset.citryUiPart !== "menu"
        ) {
          throw new Error(
            "[citry-ui] CSplitButton requires two immediate native Buttons "
              + "followed by its Menu surface.",
          );
        }
        const part = (name) => root.querySelector(`[data-citry-ui-part="${name}"]`);
        const indicator = part("split-button-primary-loading-indicator");
        const content = part("split-button-primary-content");
        const menuIndicator = part("split-button-menu-indicator");
        if (!indicator || !content || !menuIndicator) {
          throw new Error("[citry-ui] CSplitButton could not resolve primary Button content.");
        }
        const start = part("split-button-primary-start");
        const end = part("split-button-primary-end");
        let valid = true;
        let timer = null;
        const attr = (element, name, value) => {
          if (element.getAttribute(name) !== value) element.setAttribute(name, value);
        };
        const classes = (element, ...names) => {
          for (const name of names) element.classList.add(name);
        };
        const repair = () => {
          for (const [element, values, names] of [
            [
              root,
              {
                id: data.rootId,
                role: "group",
                "aria-label": data.label,
                "data-citry-ui-part": "split-button",
                "data-citry-menu-host": "",
              },
              ["cui-split-button"],
            ],
            [
              primary,
              {id: data.primaryId, "data-citry-ui-part": "split-button-primary"},
              ["cui-button", "cui-split-button__primary"],
            ],
            [
              trigger,
              {
                id: data.triggerId,
                "data-citry-ui-part": "split-button-menu-trigger",
                "data-citry-menu-trigger": "",
              },
              ["cui-button", "cui-split-button__menu-trigger"],
            ],
            [surface, {id: data.surfaceId, "data-citry-ui-part": "menu", "data-citry-menu-root": ""}, ["cui-menu"]],
          ]) {
            for (const [name, value] of Object.entries(values)) attr(element, name, value);
            classes(element, ...names);
          }
          for (const [element, name] of [
            [content, "split-button-primary-content"],
            [indicator, "split-button-primary-loading-indicator"],
            [start, "split-button-primary-start"],
            [end, "split-button-primary-end"],
            [menuIndicator, "split-button-menu-indicator"],
          ]) {
            if (element) attr(element, "data-citry-ui-part", name);
          }
          if (primary.type !== data.primaryType) primary.type = data.primaryType;
          if (trigger.type !== "button") trigger.type = "button";
          for (const [element, values] of [
            [trigger, {"aria-label": data.menuLabel, "aria-haspopup": "menu", "aria-controls": data.surfaceId}],
            [surface, {"aria-labelledby": data.triggerId, popover: "manual", role: "menu"}],
          ]) {
            for (const [name, value] of Object.entries(values)) attr(element, name, value);
          }
          root.style.setProperty("anchor-name", data.anchorName);
          surface.style.setProperty("--_cui-menu-anchor", data.anchorName);
          surface.style.setProperty("position-anchor", data.anchorName);
        };
        const validate = () => {
          const forbidden = primary.querySelector(
            "a[href],button,input,select,textarea,details,summary,dialog,audio,video,object,embed,iframe,"
              + "[contenteditable]:not([contenteditable='false']),[tabindex]:not([tabindex='-1'])",
          );
          const custom = [...primary.querySelectorAll("*")].some((element) => (
            element.localName.includes("-") || element.hasAttribute("is") || element.shadowRoot
          ));
          const named = content.textContent?.trim()
            || primary.getAttribute("aria-label")?.trim()
            || primary.getAttribute("aria-labelledby")?.trim();
          const next = !forbidden && !custom && Boolean(named);
          if (!next && valid) {
            console.error(
              "[citry-ui] CSplitButton primary content must remain noninteractive "
                + "and provide an accessible name.",
              primary,
            );
          }
          valid = next;
          return valid;
        };
        const refresh = () => {
          repair();
          return validate();
        };
        const schedule = () => {
          if (timer !== null) return;
          timer = setTimeout(() => {
            timer = null;
            refresh();
            changed();
          }, 0);
        };
        const observer = new MutationObserver(schedule);
        observer.observe(root, {
          subtree: true,
          childList: true,
          characterData: true,
          attributes: true,
          attributeFilter: [
            "aria-label", "aria-labelledby", "aria-controls", "aria-expanded", "aria-haspopup",
            "contenteditable", "class", "data-citry-menu-host", "data-citry-menu-root",
            "data-citry-menu-trigger", "data-citry-ui-part", "data-block", "data-disabled",
            "data-intent", "data-loading", "data-loading-position", "data-match-width",
            "data-menu-disabled", "data-open", "data-placement", "data-primary-disabled",
            "data-size", "data-variant", "disabled", "id", "inert", "is", "popover",
            "role", "style", "tabindex", "type",
          ],
        });
        refresh();
        return {
          primary,
          trigger,
          surface,
          indicator,
          refresh,
          valid: () => valid,
          cleanup() {
            observer.disconnect();
            if (timer !== null) clearTimeout(timer);
          },
        };
      };
      const createMenuController = ({host, data, props, effect, service}, controllerOptions = {}) => {
          const componentName = controllerOptions.componentName ?? "CMenu";
          const externalActivation = controllerOptions.activationMode === "external";
          const hostSelector = "[data-citry-menu-host]";
          const nearestHost = (element) => element?.closest?.(hostSelector) ?? null;
          const surface = controllerOptions.surface
            ?? [...host.querySelectorAll("[data-citry-menu-root]")]
              .find((candidate) => nearestHost(candidate) === host);
          const triggers = controllerOptions.trigger
            ? [controllerOptions.trigger]
            : [...host.querySelectorAll("[data-citry-menu-trigger]")]
              .filter((candidate) => nearestHost(candidate) === host);
          if (
            !surface
            || triggers.length !== 1
            || !(triggers[0] instanceof Element)
            || (!externalActivation && !(triggers[0] instanceof HTMLButtonElement))
          ) {
            throw new Error(
              externalActivation
                ? `[citry-ui] ${componentName} requires exactly one external Menu anchor.`
                : `[citry-ui] ${componentName} requires exactly one native Menu Button.`,
            );
          }
          const trigger = triggers[0];
          const anchor = controllerOptions.anchor ?? trigger;
          // Server HTML may advertise an initially open Menu. Until the
          // settled declaration tree and activator are validated, expose no
          // interactive surface to assistive technology or pointer input.
          surface.inert = true;
          surface.removeAttribute("data-open");
          surface.removeAttribute("data-citry-menu-exiting");
          surface.removeAttribute("data-citry-menu-initialized");
          controllerOptions.readyChanged?.(false);
          if (!externalActivation) {
            trigger.setAttribute("aria-expanded", "false");
          }
          const unsafeInitialTriggerType = !externalActivation && trigger.type !== "button";
          if (unsafeInitialTriggerType) {
            // Normalize before reporting so a malformed native activator can
            // never submit an enclosing Form while initialization fails.
            trigger.type = "button";
            console.error(
              `[citry-ui] ${componentName} Menu Button must use type="button".`,
              trigger,
            );
          }
          if (!externalActivation) {
            if (!trigger.id) {
              trigger.id = `${surface.id}-trigger`;
            }
            surface.setAttribute("aria-labelledby", trigger.id);
          }
          const layerCoordinator = anchoredLayerRuntime.coordinatorFor(surface);
          const anchorName = getComputedStyle(surface)
            .getPropertyValue("--_cui-menu-anchor")
            .trim();
          if (!anchorName.startsWith("--")) {
            throw new Error(`[citry-ui] ${componentName} could not resolve its CSS anchor name.`);
          }
          anchor.style.setProperty("anchor-name", anchorName);
          surface.style.setProperty("position-anchor", anchorName);

          const allowed = {
            placement: [
              "top-start",
              "top",
              "top-end",
              "bottom-start",
              "bottom",
              "bottom-end",
            ],
            size: ["sm", "md", "lg"],
          };
          const entrySelector = "[data-citry-menu-entry]";
          const invalidEpisodes = new Set();
          const registrations = service.registrations;
          const submenus = new Set();
          const scheduledTasks = new Set();
          let reconciliationTimer = null;
          let active = true;
          let logicalOpen = false;
          let structureValid = false;
          let internalOpen = data.open;
          let controlled = false;
          let structuralSuppressed = false;
          let previousControlledOpen = null;
          let onOpenChange = null;
          let onAction = null;
          let pendingOpenRequest = null;
          let currentEntry = null;
          let typeahead = "";
          let typeaheadTimer = null;
          let tabTransition = false;
          let actionTransaction = false;
          let pendingForcedCloseNotice = null;
          let deferredFocusOutside = null;
          let exitAnimation = null;
          let generation = 0;
          let openInputRevision = 0;
          let previousOpenInput = props.open;
          let acceptedPrimaryClick = null;
          const primaryTransactions = new Set();
          let refreshNativeDisabledObserver = () => {};
          const disabledElement = controllerOptions.disabledElement ?? trigger;
          // The trigger's `disabled` as the author's markup or page code left it.
          // The previous run's cleanup put that value back before Vue applied
          // this render, so a `disabled` the component set for an earlier render
          // is never read here as the author's.
          let authorTriggerDisabled = trigger.disabled;
          // The last `disabled` this run wrote, so the cleanup can tell whether
          // anything else changed the trigger since.
          let writtenTriggerDisabled = null;
          // While the server disables the Menu, a disabled trigger may only be
          // the server value the author forwards through `activator_disabled`,
          // so it does not count as the author's own disable.
          let authorDirectDisabled = externalActivation || controllerOptions.ownsTriggerDisabled
            ? false
            : authorTriggerDisabled && !data.disabled;
          // Page code and Vue write the author's `disabled`; the Menu writes the
          // server's. The observer below tells them apart by the values this run
          // wrote, in order. The Menu writes only a changed value, so each of its
          // writes queues exactly one record. A redundant `disabled = true` or
          // `setAttribute("disabled", "")` from page code also queues a record,
          // so it is seen even while the Menu already disables the trigger.
          // `toggleAttribute("disabled", true)` on an already disabled trigger
          // queues none, so that one write is not seen. When no other Menu
          // observes this root, writes made before this run registers its
          // observer produce no record.
          const ownDisabledWrites = [];
          const recordsAuthorDisabled = !externalActivation && !controllerOptions.ownsTriggerDisabled;
          // Write the trigger's `disabled` as the Menu's own value.
          const writeOwnTriggerDisabled = (value) => {
            // Without an observer on the trigger's root no record will arrive,
            // and a queued value would later be matched against an author write.
            if (recordsAuthorDisabled && anchoredLayerRuntime.menuDisabledObservers?.get(trigger.getRootNode())) {
              ownDisabledWrites.push(value);
            }
            trigger.disabled = value;
          };
          let committedEffectiveDisabled = externalActivation
            ? Boolean(controllerOptions.ownerDisabled?.())
            : trigger.matches(":disabled");
          const retainedRuntimeState = surface.__citryUiMenuRuntime ?? null;
          let handoffRecoveryReady = !retainedRuntimeState;
          let handoffRecoveryScheduled = false;
          const runtimeState = retainedRuntimeState ?? {
            open: data.open,
            currentKey: null,
            currentValue: null,
            currentIdentity: null,
            currentOrder: [],
            currentRoot: null,
            currentRoots: [],
            currentSurface: null,
            currentLevelOrder: [],
            currentLevelRoots: [],
            openSubmenuPaths: [],
            radioGroups: {},
            serverOpen: data.open,
            effectiveDisabled: false,
          };
          surface.__citryUiMenuRuntime = runtimeState;
          const sameServerOpen = runtimeState.serverOpen === data.open;
          if (retainedRuntimeState && sameServerOpen) {
            internalOpen = Boolean(runtimeState.open);
          }
          let retainedOpenSubmenuPaths = retainedRuntimeState && sameServerOpen
            ? [...(runtimeState.openSubmenuPaths ?? [])]
            : [];
          // A menu that was showing when this render disabled it closes and
          // reports the close, whether or not the same render also changed the
          // server's `open` input: the disable is what closes it.
          let pendingDisabledHandoff = Boolean(
            retainedRuntimeState
            && runtimeState.open
            && !runtimeState.effectiveDisabled
          );
          let pendingRemovedEntry = null;
          let configuration = {
            disabled: data.disabled,
            loop: data.loop,
            placement: data.placement,
            matchWidth: data.matchWidth,
            closeOnSelect: data.closeOnSelect,
            size: data.size,
          };

          const describeValue = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          const reportInvalid = (name, value, fallback) => {
            if (invalidEpisodes.has(name)) {
              return;
            }
            invalidEpisodes.add(name);
            console.error(
              `[citry-ui] ${componentName} ${name} received invalid client value `
                + `${describeValue(value)}; ${fallback}.`,
              surface,
            );
          };
          const resolveBoolean = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (typeof value === "boolean") {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value, "using the server-rendered fallback");
            return data[name];
          };
          const resolveChoice = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (allowed[name].includes(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value, "using the server-rendered fallback");
            return data[name];
          };
          const resolveCallback = (name) => {
            const value = props[name];
            if (value === undefined || value === null || typeof value === "function") {
              invalidEpisodes.delete(name);
              return value ?? null;
            }
            reportInvalid(name, value, "ignoring the callback");
            return null;
          };
          const scheduleTask = (callback, delay = 0) => {
            const task = setTimeout(() => {
              scheduledTasks.delete(task);
              if (active) {
                callback();
              }
            }, delay);
            scheduledTasks.add(task);
          };
          const ownsEntry = (entry) => (
            registrations.get(entry?.root) === entry
            && entry.root.isConnected
          );
          const directEntries = (container) => [...registrations.values()]
            .filter((entry) => entry.container === container && entry.root.isConnected)
            .sort((left, right) => {
              if (left.root === right.root) {
                return 0;
              }
              return left.root.compareDocumentPosition(right.root)
                & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
            });
          const flattenEntries = (container) => {
            const flattened = [];
            for (const entry of directEntries(container)) {
              if (entry.kind === "group" || entry.kind === "radio-group") {
                flattened.push(...flattenEntries(entry.root));
              } else if (entry.kind !== "separator") {
                flattened.push(entry);
              }
            }
            return flattened;
          };
          const entriesForSurface = (menuSurface) => flattenEntries(menuSurface);
          const entryPath = (entry) => entry.context?.path ?? entry.path ?? [];
          const stableIdentity = (entry) => ({
            kind: entry.kind,
            path: [...entryPath(entry)],
            value: entry.value,
          });
          const samePath = (left, right) => (
            left.length === right.length
            && left.every((value, index) => value === right[index])
          );
          const sameIdentity = (entry, identity) => Boolean(
            identity
            && entry.kind === identity.kind
            && entry.value === identity.value
            && samePath(entryPath(entry), identity.path ?? [])
          );
          const identityToken = (entry) => JSON.stringify(stableIdentity(entry));
          const allActionableEntries = () => [...registrations.values()].filter((entry) => (
            entry.element && entry.kind !== "separator" && ownsEntry(entry)
          ));
          const uniqueSemanticEntry = (identity) => {
            const matches = allActionableEntries().filter((entry) => sameIdentity(entry, identity));
            return matches.length === 1 ? matches[0] : null;
          };
          const entryFromTarget = (target) => {
            const root = target?.closest?.(entrySelector);
            return root ? registrations.get(root) ?? null : null;
          };
          const isInsideTree = (target) => {
            if (!(target instanceof Node)) {
              return false;
            }
            if (
              anchoredLayerRuntime.composedContains(trigger, target)
              || anchoredLayerRuntime.composedContains(surface, target)
              || (controllerOptions.insideElements ?? []).some((element) => (
                anchoredLayerRuntime.composedContains(element, target)
              ))
            ) {
              return true;
            }
            return [...submenus].some((submenu) => (
              anchoredLayerRuntime.composedContains(submenu.childSurface, target)
            ));
          };
          const updateCurrent = (entry) => {
            if (!entry || !ownsEntry(entry)) {
              return;
            }
            currentEntry = entry;
            runtimeState.currentKey = entry.key;
            runtimeState.currentValue = entry.value;
            runtimeState.currentIdentity = stableIdentity(entry);
            runtimeState.currentRoot = entry.root;
            runtimeState.currentSurface = entry.surface;
            runtimeState.currentLevelOrder = entriesForSurface(entry.surface).map(identityToken);
            runtimeState.currentLevelRoots = entriesForSurface(entry.surface).map(
              (candidate) => candidate.root,
            );
            for (const candidate of registrations.values()) {
              if (candidate.element) {
                candidate.element.tabIndex = candidate === entry ? 0 : -1;
              }
            }
          };
          const focusEntry = (entry, scroll = true) => {
            if (!entry?.element?.isConnected) {
              return;
            }
            updateCurrent(entry);
            entry.element.focus({ preventScroll: true });
            if (scroll) {
              entry.element.scrollIntoView({ block: "nearest", inline: "nearest" });
            }
          };
          const focusBoundary = (menuSurface, boundary) => {
            const entries = entriesForSurface(menuSurface);
            const entry = boundary === "last" ? entries.at(-1) : entries[0];
            if (entry) {
              focusEntry(entry);
            }
          };
          const nearestEntry = (removed, entries = entriesForSurface(removed.surface)) => {
            if (entries.length === 0) {
              return null;
            }
            const removedIdentity = stableIdentity(removed);
            const oldRoots = removed.lastRoots ?? [];
            const oldOrder = removed.lastOrder ?? [];
            const oldRootIndex = oldRoots.indexOf(removed.root);
            const semanticMatches = entries.filter((entry) => (
              sameIdentity(entry, removedIdentity)
            ));
            const identityWasAmbiguous = oldOrder.filter((token) => (
              token === identityToken(removed)
            )).length > 1;
            const sameRoot = entries.find((entry) => (
              entry.root === removed.root && sameIdentity(entry, removedIdentity)
            ));
            if (sameRoot) {
              return sameRoot;
            }
            if (!identityWasAmbiguous && semanticMatches.length === 1) {
              return semanticMatches[0];
            }
            const oldIndex = oldRootIndex >= 0
              ? oldRootIndex
              : oldOrder.indexOf(identityToken(removed));
            for (const direction of [1, -1]) {
              for (let distance = 1; distance <= oldOrder.length; distance += 1) {
                const index = oldIndex + direction * distance;
                const expectedToken = oldOrder[index];
                if (expectedToken === undefined) {
                  continue;
                }
                const physical = entries.find((entry) => (
                  entry.root === oldRoots[index]
                  && identityToken(entry) === expectedToken
                ));
                if (physical) {
                  return physical;
                }
                // Indistinguishable anonymous declarations cannot establish
                // which sibling survived by semantic token alone.
                if (identityWasAmbiguous && expectedToken === identityToken(removed)) {
                  continue;
                }
                const logical = entries.filter((entry) => (
                  identityToken(entry) === expectedToken
                ));
                if (logical.length === 1) {
                  return logical[0];
                }
              }
            }
            return oldOrder.length > 0 ? null : entries[0];
          };
          const deepestRetainedAncestor = (identity) => {
            if (!identity?.path?.length) {
              return null;
            }
            return allActionableEntries()
              .filter((entry) => entry.kind === "submenu")
              .filter((entry) => {
                const candidatePath = [...entryPath(entry), entry.value];
                return candidatePath.length <= identity.path.length
                  && candidatePath.every((value, index) => value === identity.path[index]);
              })
              .sort((left, right) => entryPath(right).length - entryPath(left).length)[0] ?? null;
          };
          const resetTypeahead = () => {
            typeahead = "";
            if (typeaheadTimer !== null) {
              clearTimeout(typeaheadTimer);
              typeaheadTimer = null;
            }
          };
          const composedParent = (node) => {
            if (node?.parentNode) {
              return node.parentNode;
            }
            const root = node?.getRootNode?.();
            return root instanceof ShadowRoot ? root.host : null;
          };
          const inheritedLanguage = (element) => {
            let current = element;
            while (current) {
              if (current instanceof Element && current.getAttribute("lang")?.trim()) {
                return current.getAttribute("lang").trim();
              }
              current = composedParent(current);
            }
            return surface.ownerDocument.documentElement.lang || undefined;
          };
          const normalizeText = (value, element) => {
            const collapsed = String(value ?? "")
              .normalize("NFKC")
              .replace(/\s+/gu, " ")
              .trim();
            try {
              return collapsed.toLocaleLowerCase(inheritedLanguage(element));
            } catch {
              return collapsed.toLowerCase();
            }
          };
          const entryText = (entry) => normalizeText(
            entry.textValue ?? entry.label?.textContent ?? "",
            entry.element,
          );
          const handleTypeahead = (event, entry) => {
            const altGraph = event.getModifierState?.("AltGraph") ?? false;
            if (
              event.isComposing
              || event.key.length !== 1
              || event.metaKey
              || (!altGraph && (event.ctrlKey || event.altKey))
            ) {
              return false;
            }
            const key = normalizeText(event.key, entry.element);
            if (!key) {
              return false;
            }
            const repeated = typeahead && [...typeahead].every((character) => character === key);
            typeahead = repeated ? key : `${typeahead}${key}`;
            if (typeaheadTimer !== null) {
              clearTimeout(typeaheadTimer);
            }
            typeaheadTimer = setTimeout(resetTypeahead, 500);
            const entries = entriesForSurface(entry.surface);
            const start = entries.indexOf(entry);
            const candidates = configuration.loop
              ? [...entries.slice(start + 1), ...entries.slice(0, start + 1)]
              : entries.slice(start + 1);
            const match = candidates.find((candidate) => entryText(candidate).startsWith(typeahead));
            if (!match) {
              return false;
            }
            focusEntry(match);
            return true;
          };

          const closeSubmenu = (submenu, options = {}) => {
            if (
              !submenu
              || (!submenu.open && !submenu.childSurface?.matches?.(":popover-open"))
            ) {
              return;
            }
            for (const child of [...submenus].filter((candidate) => candidate.parent === submenu)) {
              closeSubmenu(child, { restore: false });
            }
            submenu.open = false;
            submenu.wrapper.removeAttribute("data-open");
            submenu.trigger.setAttribute("aria-expanded", "false");
            submenu.childSurface.inert = true;
            submenu.childSurface.removeAttribute("data-open");
            hideNativePopover(submenu.childSurface);
            layerCoordinator.unregister(submenu.layer, { cascade: true });
            submenu.stopGeometry?.();
            submenu.cancelIntent?.();
            if (options.restore && submenu.trigger.isConnected) {
              focusEntry(submenu);
            }
          };
          const closeAllSubmenus = () => {
            const open = [...submenus].filter((submenu) => submenu.open);
            for (let index = open.length - 1; index >= 0; index -= 1) {
              closeSubmenu(open[index], { restore: false });
            }
          };
          const effectiveOwnerDisabled = () => (
            configuration.disabled
            || (
              externalActivation
                ? Boolean(controllerOptions.ownerDisabled?.())
                : trigger.matches(":disabled")
            )
          );
          const updateTrigger = () => {
            controllerOptions.committedOpen?.(logicalOpen);
            if (externalActivation) {
              return;
            }
            const expanded = logicalOpen ? "true" : "false";
            if (trigger.getAttribute("aria-expanded") !== expanded) {
              trigger.setAttribute("aria-expanded", expanded);
            }
            const desiredDisabled = configuration.disabled || authorDirectDisabled;
            if (trigger.disabled !== desiredDisabled) {
              writeOwnTriggerDisabled(desiredDisabled);
            }
            writtenTriggerDisabled = desiredDisabled;
          };
          const focusFallback = () => {
            const preferred = controllerOptions.focusReturnTarget?.()
              ?? controllerOptions.disabledFocusTarget?.()
              ?? trigger;
            for (const candidate of [preferred, trigger]) {
              if (
                candidate?.isConnected
                && !candidate.matches(":disabled")
                && candidate.getClientRects().length > 0
              ) {
                candidate.focus({ preventScroll: true });
                if (layerCoordinator.deepActiveElement() === candidate) {
                  return;
                }
              }
            }
            const nearestContainingModal = (start) => {
              let current = start;
              while (current) {
                if (current instanceof HTMLDialogElement && current.matches(":modal")) {
                  return current;
                }
                current = composedParent(current);
              }
              return null;
            };
            // `document.querySelectorAll()` cannot see an open ShadowRoot's
            // modal Dialog. Walk the composed ancestors so both a Dialog
            // outside the Menu's shadow and one inside it are eligible.
            const modal = nearestContainingModal(surface) ?? nearestContainingModal(trigger);
            const target = modal ?? surface.ownerDocument.body;
            const hadTabIndex = target.hasAttribute("tabindex");
            if (!hadTabIndex) {
              target.tabIndex = -1;
            }
            target.focus({ preventScroll: true });
            if (!hadTabIndex) {
              const removeTemporaryTabIndex = () => {
                if (target.getAttribute("tabindex") === "-1") {
                  target.removeAttribute("tabindex");
                }
              };
              if (!externalActivation) {
                target.addEventListener("blur", removeTemporaryTabIndex, { once: true });
              } else if (layerCoordinator.deepActiveElement() === target) {
                removeTemporaryTabIndex();
              } else {
                const currentGeneration = generation;
                target.addEventListener("blur", removeTemporaryTabIndex, { once: true });
                scheduleTask(() => {
                  if (currentGeneration === generation) {
                    removeTemporaryTabIndex();
                  }
                });
              }
            }
          };
          const restoreAfterClose = (reason, source) => {
            if (controllerOptions.shouldRestoreFocus?.(reason, source) === false) {
              return;
            }
            if (["outside", "focus-outside", "tab", "ancestor"].includes(reason)) {
              return;
            }
            if (source instanceof HTMLAnchorElement) {
              return;
            }
            const activeElement = layerCoordinator.deepActiveElement();
            if (
              !isInsideTree(activeElement)
              && activeElement !== surface.ownerDocument.body
              && activeElement !== trigger
            ) {
              return;
            }
            focusFallback();
          };
          const normalizeRootClosed = (reason = "ancestor", source = surface) => {
            closeAllSubmenus();
            logicalOpen = false;
            surface.inert = true;
            surface.removeAttribute("data-open");
            surface.removeAttribute("data-citry-menu-exiting");
            hideNativePopover(surface);
            layerCoordinator.unregister(layer, { reason, source, cascade: true });
            updateTrigger();
            controllerOptions.closed?.();
          };
          const finishExit = (currentGeneration) => {
            if (!active || logicalOpen || currentGeneration !== generation) {
              return;
            }
            hideNativePopover(surface);
            surface.removeAttribute("data-citry-menu-exiting");
            controllerOptions.closed?.();
          };
          const applyRootOpen = (nextOpen, context = {}) => {
            if (nextOpen === logicalOpen) {
              // The previous run leaves an open menu showing so this run can take
              // it over. When this run starts closed because the server's `open`
              // input changed, nothing else hides it. A context menu manages its
              // own handoff, so this applies to a plain menu only. A menu that
              // this run is closing also still shows while its close animation
              // plays; `finishExit` hides that one, so leave it alone.
              if (!nextOpen && !externalActivation && !exitAnimation && surface.matches(":popover-open")) {
                normalizeRootClosed("ancestor", surface);
              }
              return;
            }
            generation += 1;
            const currentGeneration = generation;
            exitAnimation?.cancel();
            exitAnimation = null;
            if (nextOpen) {
              if (
                !structureValid
                || structuralSuppressed
                || effectiveOwnerDisabled()
              ) {
                normalizeRootClosed("ancestor", surface);
                return;
              }
              if (controllerOptions.prepareOpen?.(context) === false) {
                normalizeRootClosed("ancestor", surface);
                return;
              }
              if (!layerCoordinator.mayOpen(layer)) {
                structuralSuppressed = true;
                if (!invalidEpisodes.has("ancestor-open")) {
                  invalidEpisodes.add("ancestor-open");
                  notifyOpen(false, "ancestor", surface, true);
                }
                normalizeRootClosed("ancestor", surface);
                return;
              }
              invalidEpisodes.delete("ancestor-open");
              // Publish the logical state before entering the top layer. Some
              // engines can deliver the native toggle synchronously; the
              // handler must recognize this as our own open transition rather
              // than hide the root and leave submenu restoration detached
              // from a closed surface.
              logicalOpen = true;
              try {
                if (!surface.matches(":popover-open")) {
                  surface.showPopover();
                }
              } catch (error) {
                console.error(
                  `[citry-ui] ${componentName} could not enter the top layer:`,
                  error,
                  surface,
                );
                normalizeRootClosed("ancestor", surface);
                return;
              }
              surface.inert = false;
              surface.removeAttribute("data-citry-menu-exiting");
              surface.setAttribute("data-open", "");
              if (!layerCoordinator.register(layer)) {
                logicalOpen = false;
                hideNativePopover(surface);
                surface.inert = true;
                surface.removeAttribute("data-open");
                updateTrigger();
                controllerOptions.closed?.();
                return;
              }
              updateTrigger();
              queueMicrotask(() => {
                if (active && logicalOpen && currentGeneration === generation) {
                  context.restore?.();
                  if (context.focus === "current") {
                    if (currentEntry) {
                      focusEntry(currentEntry);
                    }
                  } else if (context.focus) {
                    focusBoundary(surface, context.focus ?? "first");
                  }
                }
              });
              return;
            }
            closeAllSubmenus();
            resetTypeahead();
            logicalOpen = false;
            surface.inert = true;
            surface.removeAttribute("data-open");
            surface.setAttribute("data-citry-menu-exiting", "");
            layerCoordinator.unregister(layer, {
              reason: context.reason ?? "ancestor",
              source: context.source ?? surface,
              cascade: true,
            });
            updateTrigger();
            restoreAfterClose(context.reason, context.source);
            const rawDuration = getComputedStyle(surface)
              .getPropertyValue("--_cui-menu-duration")
              .trim();
            const duration = rawDuration.endsWith("ms")
              ? Number.parseFloat(rawDuration)
              : rawDuration.endsWith("s")
                ? Number.parseFloat(rawDuration) * 1000
                : 0;
            if (!duration || typeof surface.animate !== "function") {
              finishExit(currentGeneration);
              return;
            }
            exitAnimation = surface.animate(
              [{ opacity: 1, transform: "none" }, { opacity: 0, transform: "scale(0.98)" }],
              {
                duration,
                easing: getComputedStyle(surface)
                  .getPropertyValue("--_cui-menu-easing")
                  .trim() || "ease",
              },
            );
            exitAnimation.finished.catch(() => {}).finally(() => {
              exitAnimation = null;
              finishExit(currentGeneration);
            });
          };
          const notifyOpen = (nextOpen, reason, source, forced = false) => {
            return onOpenChange?.(nextOpen, {
              reason,
              controlled,
              forced,
              source,
            });
          };
          const requestRootOpen = (nextOpen, reason, source, focus = "first") => {
            if (nextOpen === logicalOpen) {
              return {
                accepted: true,
                callbackResult: undefined,
                controlled,
                request: null,
                same: true,
              };
            }
            if (nextOpen) {
              if (externalActivation && (!structureValid || effectiveOwnerDisabled())) {
                return {
                  accepted: false,
                  callbackResult: undefined,
                  controlled,
                  request: null,
                  same: false,
                };
              }
              structuralSuppressed = false;
              layerCoordinator.clearSuppression(layer);
              invalidEpisodes.delete("ancestor-open");
            }
            if (controlled) {
              if (!nextOpen) {
                // A controlled close request supersedes any queued focus from
                // the opening commit even before the owner prop settles.
                generation += 1;
              }
              pendingOpenRequest = { nextOpen, reason, source, focus };
              const request = pendingOpenRequest;
              const repairEntry = currentEntry;
              const callbackResult = notifyOpen(nextOpen, reason, source);
              if (!nextOpen && ["trigger", "escape"].includes(reason)) {
                queueMicrotask(() => {
                  if (
                    active
                    && logicalOpen
                    && controlled
                    && repairEntry?.element?.isConnected
                    && [trigger, surface.ownerDocument.body].includes(
                      layerCoordinator.deepActiveElement(),
                    )
                  ) {
                    focusEntry(repairEntry);
                  }
                });
              }
              return {
                accepted: Boolean(
                  active
                  && pendingOpenRequest === request
                  && structureValid
                  && !effectiveOwnerDisabled()
                  && (!nextOpen || layerCoordinator.mayOpen(layer))
                ),
                callbackResult,
                controlled: true,
                request,
                same: false,
              };
            }
            internalOpen = nextOpen;
            applyRootOpen(nextOpen, { reason, source, focus });
            let callbackResult;
            if (logicalOpen === nextOpen) {
              callbackResult = notifyOpen(nextOpen, reason, source);
            }
            return {
              accepted: Boolean(
                active
                && logicalOpen === nextOpen
                && (
                  !nextOpen
                  || (surface.matches(":popover-open") && layer.__citryAnchoredRegistration)
                )
              ),
              callbackResult,
              controlled: false,
              request: null,
              same: false,
            };
          };
          const cancelOpenRequest = (request) => {
            if (request !== null && pendingOpenRequest === request) {
              pendingOpenRequest = null;
              return true;
            }
            return false;
          };
          const beginPrimaryAction = (source, event) => {
            if (!active || !logicalOpen) {
              return null;
            }
            if (
              event?.type === "click"
              && acceptedPrimaryClick?.event === event
              && acceptedPrimaryClick.source === source
            ) {
              return acceptedPrimaryClick.transaction;
            }
            const transaction = {
              callback: onOpenChange,
              controlled,
              event,
              source,
              generation: null,
              openInputRevision,
            };
            if (!controlled) {
              internalOpen = false;
              applyRootOpen(false, { reason: "action", source });
            }
            transaction.generation = generation;
            primaryTransactions.add(transaction);
            if (event?.type === "click") {
              acceptedPrimaryClick = { event, source, transaction };
            }
            scheduleTask(() => {
              primaryTransactions.delete(transaction);
              if (acceptedPrimaryClick?.transaction === transaction) {
                acceptedPrimaryClick = null;
              }
              if (
                transaction.generation !== generation
                || transaction.openInputRevision !== openInputRevision
              ) {
                return;
              }
              transaction.callback?.(
                false,
                Object.freeze({
                  reason: "action",
                  controlled: transaction.controlled,
                  forced: false,
                  source: transaction.source,
                }),
              );
            });
            return transaction;
          };
          const observePrimarySubmit = (event) => {
            const source = event?.submitter;
            if (
              acceptedPrimaryClick?.source === source
              && acceptedPrimaryClick.transaction.event?.type === "click"
            ) {
              return acceptedPrimaryClick.transaction;
            }
            return beginPrimaryAction(source, event);
          };
          const hasPrimaryClickToken = (source) => (
            acceptedPrimaryClick?.source === source
            && primaryTransactions.has(acceptedPrimaryClick.transaction)
          );
          const forceRootClose = (reason, source) => {
            const publicReason = reason === "modal" ? "ancestor" : reason;
            const wasOpen = logicalOpen;
            structuralSuppressed = true;
            if (!controlled) {
              internalOpen = false;
            }
            pendingOpenRequest = null;
            if (wasOpen) {
              applyRootOpen(false, { reason: publicReason, source });
              if (actionTransaction) {
                pendingForcedCloseNotice ??= { reason: publicReason, source };
              } else {
                notifyOpen(false, publicReason, source, true);
              }
            } else {
              normalizeRootClosed(publicReason, source);
            }
          };
          const layer = {
            surface,
            trigger,
            isEligible: () => !effectiveOwnerDisabled() && structureValid,
            isOpen: () => active && logicalOpen,
            requestDismiss: (reason, source) => {
              if (
                reason === "focus-outside"
                && controllerOptions.ignoreFocusOutside?.(source)
              ) {
                return;
              }
              if (actionTransaction && reason === "focus-outside") {
                deferredFocusOutside = source;
                return;
              }
              requestRootOpen(false, reason, source);
            },
            forceClose: (reason, source) => forceRootClose(reason, source),
            insideElements: [...new Set([host, ...(controllerOptions.insideElements ?? [])])],
          };

          const openSubmenu = (submenu, options = {}) => {
            if (
              !submenu
              || submenu.effectiveDisabled
              || submenu.trigger?.matches?.('[aria-disabled="true"], [data-disabled]')
              || !logicalOpen
              || !layerCoordinator.mayOpen(submenu.layer)
            ) {
              return;
            }
            for (const sibling of submenus) {
              if (sibling !== submenu && sibling.parent === submenu.parent && sibling.open) {
                closeSubmenu(sibling, { restore: false });
              }
            }
            if (!submenu.open) {
              submenu.choosePlacement?.();
              // Set the logical state before showPopover(). Some engines can
              // deliver the native toggle synchronously for nested popovers.
              submenu.open = true;
              try {
                submenu.childSurface.showPopover();
              } catch (error) {
                submenu.open = false;
                console.error(
                  "[citry-ui] CMenuSubmenu could not enter the top layer:",
                  error,
                  submenu.childSurface,
                );
                return;
              }
              submenu.wrapper.setAttribute("data-open", "");
              submenu.childSurface.inert = false;
              submenu.childSurface.setAttribute("data-open", "");
              submenu.trigger.setAttribute("aria-expanded", "true");
              if (!layerCoordinator.register(submenu.layer)) {
                closeSubmenu(submenu, { restore: false });
                return;
              }
              submenu.startGeometry?.();
            }
            if (options.focus) {
              focusBoundary(submenu.childSurface, options.focus);
            }
          };
          const dismissFromSubmenu = (submenu, reason, source) => {
            if (reason === "escape") {
              closeSubmenu(submenu, { restore: true });
              return;
            }
            requestRootOpen(false, reason, source);
          };
          const requestChoice = (entry, event, path) => {
            if (entry.kind === "checkbox") {
              return entry.requestChecked?.(event, path) ?? false;
            }
            if (entry.kind === "radio") {
              return entry.radioGroup?.requestValue?.(entry, event, path) ?? false;
            }
            return true;
          };
          const activate = (entry, event) => {
            if (!ownsEntry(entry) || entry.effectiveDisabled) {
              event.preventDefault();
              event.stopImmediatePropagation();
              return;
            }
            if (entry.kind === "submenu") {
              event.preventDefault();
              openSubmenu(entry, { focus: "first" });
              return;
            }
            if (entry.kind === "link") {
              if (entry.closeOnSelect ?? configuration.closeOnSelect) {
                scheduleTask(() => {
                  if (ownsEntry(entry)) {
                    requestRootOpen(false, "action", entry.element);
                  }
                });
              }
              return;
            }
            const path = [...entryPath(entry)];
            const callback = onAction;
            actionTransaction = true;
            deferredFocusOutside = null;
            let accepted = false;
            try {
              accepted = requestChoice(entry, event, path);
              if (!accepted) {
                return;
              }
              if (entry.value !== null && entry.value !== undefined) {
                callback?.(entry.value, {
                  kind: entry.kind === "item" ? "command" : entry.kind,
                  item: entry.element,
                  event,
                  path,
                });
              }
            } finally {
              actionTransaction = false;
              const forcedNotice = pendingForcedCloseNotice;
              pendingForcedCloseNotice = null;
              if (forcedNotice && active) {
                notifyOpen(false, forcedNotice.reason, forcedNotice.source, true);
              }
            }
            if (!accepted) {
              return;
            }
            if (!active || !ownsEntry(entry)) {
              return;
            }
            if (entry.closeOnSelect ?? configuration.closeOnSelect) {
              requestRootOpen(false, "action", entry.element);
            } else if (deferredFocusOutside) {
              const source = deferredFocusOutside;
              deferredFocusOutside = null;
              requestRootOpen(false, "focus-outside", source);
            }
          };
          const move = (entry, delta) => {
            const entries = entriesForSurface(entry.surface);
            const index = entries.indexOf(entry);
            if (index < 0 || entries.length === 0) {
              return;
            }
            let next = index + delta;
            if (configuration.loop) {
              next = (next + entries.length) % entries.length;
            } else {
              next = Math.max(0, Math.min(entries.length - 1, next));
            }
            focusEntry(entries[next]);
          };
          const onClick = (event) => {
            if (
              !externalActivation
              && (event.target === trigger || trigger.contains(event.target))
            ) {
              refreshNativeDisabledObserver();
              if (trigger.type !== "button") {
                event.preventDefault();
                trigger.type = "button";
                structureValid = false;
                structuralSuppressed = true;
                normalizeRootClosed("ancestor", trigger);
                reportInvalid(
                  "activator-structure",
                  "submit",
                  'the activator requires type="button"',
                );
                return;
              }
              if (trigger.matches(":disabled")) {
                return;
              }
              requestRootOpen(!logicalOpen, "trigger", trigger);
              return;
            }
            const entry = entryFromTarget(event.target);
            if (!entry) {
              return;
            }
            activate(entry, event);
          };
          const onKeydown = (event) => {
            if (
              !externalActivation
              && (event.target === trigger || trigger.contains(event.target))
            ) {
              if (["ArrowDown", "ArrowUp"].includes(event.key)) {
                event.preventDefault();
                requestRootOpen(true, "trigger", trigger, event.key === "ArrowUp" ? "last" : "first");
              }
              return;
            }
            const entry = entryFromTarget(event.target);
            if (!entry || entry.element !== event.target) {
              return;
            }
            const direction = getComputedStyle(entry.element).direction;
            const forward = direction === "rtl" ? "ArrowLeft" : "ArrowRight";
            const reverse = direction === "rtl" ? "ArrowRight" : "ArrowLeft";
            if (event.key === "ArrowDown") {
              event.preventDefault();
              move(entry, 1);
            } else if (event.key === "ArrowUp") {
              event.preventDefault();
              move(entry, -1);
            } else if (event.key === "Home") {
              event.preventDefault();
              focusBoundary(entry.surface, "first");
            } else if (event.key === "End") {
              event.preventDefault();
              focusBoundary(entry.surface, "last");
            } else if (event.key === forward && entry.kind === "submenu") {
              event.preventDefault();
              openSubmenu(entry, { focus: "first" });
            } else if (event.key === reverse && entry.parent) {
              event.preventDefault();
              closeSubmenu(entry.parent, { restore: true });
            } else if (event.key === "Escape" && entry.parent) {
              event.preventDefault();
              event.stopPropagation();
              closeSubmenu(entry.parent, { restore: true });
            } else if (event.key === "Tab") {
              tabTransition = true;
              scheduleTask(() => {
                tabTransition = false;
              });
              requestRootOpen(false, "tab", entry.element);
            } else if (
              event.key === " "
              && entry.element instanceof HTMLAnchorElement
              && !entry.effectiveDisabled
            ) {
              event.preventDefault();
              entry.element.click();
            } else if (event.key !== " " && handleTypeahead(event, entry)) {
              event.preventDefault();
            }
          };
          const onFocusIn = (event) => {
            if (tabTransition && !isInsideTree(event.target)) {
              tabTransition = false;
              return;
            }
            const entry = entryFromTarget(event.target);
            if (entry && entry.element === event.target) {
              updateCurrent(entry);
            }
          };
          const pointerCanHover = (event) => (
            event.pointerType === "mouse"
            || (event.pointerType === "pen" && event.buttons === 0 && event.pressure === 0)
          );
          const onPointerOver = (event) => {
            if (!pointerCanHover(event)) {
              return;
            }
            const entry = entryFromTarget(event.target);
            if (!entry || entry.effectiveDisabled) {
              return;
            }
            if (entry.element.contains(event.relatedTarget)) {
              return;
            }
            focusEntry(entry, false);
            if (entry.kind === "submenu") {
              entry.scheduleOpen?.();
            } else {
              for (const submenu of submenus) {
                if (submenu.parent === entry.parent && submenu.open) {
                  closeSubmenu(submenu, { restore: false });
                }
              }
            }
          };
          const onPointerOut = (event) => {
            if (!pointerCanHover(event)) {
              return;
            }
            const entry = entryFromTarget(event.target);
            if (entry?.element?.contains(event.relatedTarget)) {
              return;
            }
            if (entry?.kind === "submenu") {
              if (entry.open) {
                entry.beginIntent?.(event);
              } else {
                entry.cancelIntent?.();
              }
            }
          };

          const validateActivator = () => {
            if (externalActivation) {
              const valid = controllerOptions.validateOwner?.() !== false;
              if (!valid && !invalidEpisodes.has("activator-structure")) {
                invalidEpisodes.add("activator-structure");
                console.error(
                  `[citry-ui] ${componentName} external owner structure is invalid.`,
                  host,
                );
              }
              if (valid) {
                invalidEpisodes.delete("activator-structure");
              }
              return valid;
            }
            if (controllerOptions.compound) {
              const children = [...host.children];
              const valid = (
                !unsafeInitialTriggerType
                && children.length === 3
                && children[1] === trigger
                && children[2] === surface
                && children[0] instanceof HTMLButtonElement
                && trigger.type === "button"
              );
              if (!valid && !invalidEpisodes.has("activator-structure")) {
                invalidEpisodes.add("activator-structure");
                console.error(
                  `[citry-ui] ${componentName} requires two immediate native Buttons `
                    + "followed by its Menu surface.",
                  host,
                );
              }
              if (valid) {
                invalidEpisodes.delete("activator-structure");
              }
              return valid;
            }
            const interactive = [...host.querySelectorAll(
              "button, a[href], input, select, textarea, "
                + "[contenteditable]:not([contenteditable='false']), "
                + "[tabindex]:not([tabindex='-1'])",
            )].filter((candidate) => (
              nearestHost(candidate) === host
              && !anchoredLayerRuntime.composedContains(surface, candidate)
            ));
            if (
              unsafeInitialTriggerType
              || interactive.length !== 1
              || interactive[0] !== trigger
              || trigger.type !== "button"
            ) {
              if (!invalidEpisodes.has("activator-structure")) {
                invalidEpisodes.add("activator-structure");
                console.error(
                  `[citry-ui] ${componentName} activator must contain exactly one native `
                    + "Button with type=\"button\" and no additional interactive content.",
                  host,
                );
              }
              return false;
            }
            invalidEpisodes.delete("activator-structure");
            return true;
          };

          const restoreRetainedSubmenus = () => {
            const paths = retainedOpenSubmenuPaths;
            retainedOpenSubmenuPaths = [];
            for (const path of paths.sort((left, right) => left.length - right.length)) {
              const submenu = [...submenus].find((entry) => (
                samePath([...entryPath(entry), entry.value], path)
              ));
              if (submenu) {
                openSubmenu(submenu, { focus: null });
              }
            }
            // A correlated rerender can retain a focused leaf while making
            // one of its ancestor submenu declarations unavailable. Never
            // focus back into that now-inert child surface: collapse to the
            // first unavailable submenu trigger in the root-to-leaf chain.
            const ancestors = [];
            for (let parent = currentEntry?.parent; parent; parent = parent.parent) {
              ancestors.unshift(parent);
            }
            const unavailableAncestor = ancestors.find((submenu) => (
              submenu.effectiveDisabled || !submenu.open
            ));
            if (unavailableAncestor) {
              updateCurrent(unavailableAncestor);
            }
          };

          const reconcile = () => {
            const rootEntries = entriesForSurface(surface);
            let invalid = !validateActivator();
            if (rootEntries.length === 0) {
              reportInvalid("items", null, "a Menu requires at least one actionable item");
              invalid = true;
            } else {
              invalidEpisodes.delete("items");
            }
            const values = new Set();
            for (const entry of registrations.values()) {
              entry.refresh?.();
              if (
                entry.kind === "submenu"
                && entry.trigger?.matches?.('[aria-disabled="true"], [data-disabled]')
              ) {
                closeSubmenu(entry, { restore: false });
              }
              if (entry.value !== null && entry.value !== undefined) {
                const level = `${entry.surface.id}:${entry.value}`;
                if (values.has(level)) {
                  invalid = true;
                }
                values.add(level);
              }
              entry.lastOrder = entriesForSurface(entry.surface).map(identityToken);
              entry.lastRoots = entriesForSurface(entry.surface).map((candidate) => candidate.root);
              if (entry.validate?.() === false) {
                invalid = true;
              }
            }
            if (invalid) {
              const wasOpen = logicalOpen;
              reportInvalid("structure", null, "the settled Menu structure is invalid");
              structureValid = false;
              structuralSuppressed = true;
              pendingOpenRequest = null;
              if (!controlled) {
                internalOpen = false;
              }
              surface.removeAttribute("data-citry-menu-initialized");
              controllerOptions.readyChanged?.(false);
              normalizeRootClosed("ancestor", surface);
              if (wasOpen) {
                notifyOpen(false, "ancestor", surface, true);
              }
              return;
            }
            structureValid = true;
            invalidEpisodes.delete("structure");
            if (!currentEntry || !ownsEntry(currentEntry)) {
              const identity = runtimeState.currentIdentity;
              const priorIdentityOrder = runtimeState.currentLevelOrder?.length
                ? runtimeState.currentLevelOrder
                : runtimeState.currentOrder;
              const identityWasAmbiguous = identity && priorIdentityOrder
                ?.filter((token) => token === JSON.stringify(identity)).length > 1;
              const retainedLevelEntries = runtimeState.currentSurface?.isConnected
                ? entriesForSurface(runtimeState.currentSurface)
                : [];
              if (identity && !handoffRecoveryReady) {
                currentEntry = allActionableEntries().find((entry) => (
                  entry.root === runtimeState.currentRoot
                  && sameIdentity(entry, identity)
                )) ?? null;
                if (!currentEntry && !handoffRecoveryScheduled) {
                  // A portable correlated range can register replacement
                  // declarations over several queued client jobs. Preserve an
                  // exact retained root immediately, but defer nearest-sibling
                  // recovery for one frame so a partial collection cannot win.
                  handoffRecoveryScheduled = true;
                  scheduleTask(() => {
                    handoffRecoveryReady = true;
                    scheduleReconcile();
                  }, 16);
                }
              } else {
                currentEntry = allActionableEntries().find((entry) => (
                  entry.root === runtimeState.currentRoot
                  && sameIdentity(entry, identity)
                ))
                  ?? allActionableEntries().find((entry) => (
                    entry.key === runtimeState.currentKey
                    && sameIdentity(entry, identity)
                  ))
                  ?? (identityWasAmbiguous ? null : uniqueSemanticEntry(identity))
                  ?? (
                    pendingRemovedEntry
                      ? nearestEntry(
                        pendingRemovedEntry,
                        pendingRemovedEntry.surface.isConnected
                          ? entriesForSurface(pendingRemovedEntry.surface)
                          : rootEntries,
                      )
                      : null
                  )
                  ?? (
                    identity && retainedLevelEntries.length > 0
                      ? nearestEntry(
                        {
                          ...identity,
                          key: runtimeState.currentKey,
                          root: runtimeState.currentRoot,
                          lastOrder: runtimeState.currentLevelOrder,
                          lastRoots: runtimeState.currentLevelRoots,
                          surface: runtimeState.currentSurface,
                        },
                        retainedLevelEntries,
                      )
                      : null
                  )
                  ?? deepestRetainedAncestor(identity)
                  ?? (
                    identity && runtimeState.currentOrder?.length
                      ? nearestEntry(
                        {
                          ...identity,
                          key: runtimeState.currentKey,
                          root: runtimeState.currentRoot,
                          lastOrder: runtimeState.currentOrder,
                          lastRoots: runtimeState.currentRoots,
                          surface,
                        },
                        rootEntries,
                      )
                      : null
                  )
                  ?? uniqueSemanticEntry(identity)
                  ?? rootEntries.find((entry) => (
                    runtimeState.currentValue !== null
                    && entry.value === runtimeState.currentValue
                  ))
                  ?? rootEntries.find((entry) => (
                    entry.key === runtimeState.currentKey
                    && sameIdentity(entry, identity)
                  ))
                  ?? rootEntries[0];
              }
            }
            pendingRemovedEntry = null;
            updateCurrent(currentEntry);
            surface.setAttribute("data-citry-menu-initialized", "");
            controllerOptions.readyChanged?.(true);
            const desiredOpen = controlled ? Boolean(props.open) : internalOpen;
            const retainedFocus = runtimeState.currentValue !== null
              || runtimeState.currentKey !== null;
            applyRootOpen(
              desiredOpen,
              pendingOpenRequest ?? {
                focus: retainedFocus ? "current" : "first",
                restore: restoreRetainedSubmenus,
              },
            );
            if (desiredOpen && logicalOpen) {
              const focusGeneration = generation;
              scheduleTask(() => {
                if (!active || !logicalOpen || generation !== focusGeneration) {
                  return;
                }
                restoreRetainedSubmenus();
                if (currentEntry) {
                  focusEntry(currentEntry);
                }
              });
            }
            pendingOpenRequest = null;
          };
          const scheduleReconcile = () => {
            if (reconciliationTimer !== null) {
              return;
            }
            reconciliationTimer = setTimeout(() => {
              reconciliationTimer = null;
              if (!active || !host.isConnected) {
                return;
              }
              reconcile();
            }, 0);
          };
          const context = {
            surface,
            container: surface,
            path: [],
            parentSubmenu: null,
            radioGroup: null,
            rootLayer: layer,
            attach(entry) {
              entry.surface = entry.context?.surface ?? entry.surface ?? surface;
              entry.container = entry.context?.container ?? entry.container ?? surface;
              entry.radioGroup = entry.context?.radioGroup ?? entry.radioGroup ?? null;
              if (entry.context?.path) entry.path = [...entry.context.path];
              entry.parent = entry.context?.parentSubmenu ?? entry.parent ?? null;
              if (entry.kind === "submenu") {
                entry.layer.logicalParent = entry.parent?.layer ?? layer;
              }
              entry.serverBaseline ??= JSON.stringify([
                entry.kind,
                entry.value ?? null,
                entry.href ?? null,
                entry.ownDisabled ?? null,
                entry.closeOnSelect ?? null,
                entry.intent ?? null,
                entry.textValue ?? null,
                entry.checked ?? null,
                entry.serverValue ?? null,
                entry.root.textContent,
                [...entry.root.attributes]
                  .filter((attribute) => (
                    !attribute.name.startsWith("data-cid")
                    && !attribute.name.startsWith("data-cev")
                    && ![
                      "aria-checked",
                      "aria-disabled",
                      "aria-expanded",
                      "data-checked",
                      "data-disabled",
                      "data-open",
                      "tabindex",
                    ].includes(attribute.name)
                  ))
                  .map((attribute) => [attribute.name, attribute.value])
                  .sort(),
              ]);
              if (entry.kind === "submenu") submenus.add(entry);
              scheduleReconcile();
            },
            detach(entry) {
                if (registrations.get(entry.root) !== entry) return;
                if (entry.kind === "submenu") {
                  closeSubmenu(entry, { restore: false });
                  submenus.delete(entry);
                }
                const wasCurrent = currentEntry === entry;
                if (wasCurrent) {
                  runtimeState.currentIdentity = stableIdentity(entry);
                  pendingRemovedEntry = entry;
                  currentEntry = null;
                }
                scheduleReconcile();
            },
            update() {
              scheduleReconcile();
            },
            child(options) {
              return service.child(options);
            },
            entries: directEntries,
            addSubmenu(submenu) {
              submenus.add(submenu);
            },
            openSubmenu,
            closeSubmenu,
            dismissFromSubmenu,
            size: () => configuration.size,
            defer: scheduleTask,
            claimRadioState(serverValue, path, identity) {
              const key = identity ?? JSON.stringify([path, serverValue]);
              if (!service.radioStates.has(key)) service.radioStates.set(key, {
                current: serverValue,
                serverValue,
                priorOrder: [],
                pendingRemoval: null,
                controlled: false,
              });
              return service.radioStates.get(key);
            },
          };
          service.bind(context);

          host.addEventListener("click", onClick, true);
          host.addEventListener("keydown", onKeydown, true);
          host.addEventListener("focusin", onFocusIn, true);
          host.addEventListener("pointerover", onPointerOver, true);
          host.addEventListener("pointerout", onPointerOut, true);
          const onToggle = (event) => {
            if (event.target !== surface) {
              return;
            }
            const nativeOpen = surface.matches(":popover-open");
            if (nativeOpen === logicalOpen || (!logicalOpen && exitAnimation)) {
              return;
            }
            if (nativeOpen) {
              hideNativePopover(surface);
              if (!externalActivation) {
                notifyOpen(true, "native", surface);
              }
              return;
            }
            if (controlled) {
              if (!structureValid || !layerCoordinator.mayOpen(layer)) {
                structuralSuppressed = true;
                normalizeRootClosed(
                  layerCoordinator.blockedReason(layer) ?? "ancestor",
                  surface,
                );
              } else {
                try {
                  surface.showPopover();
                } catch {
                  structuralSuppressed = true;
                  normalizeRootClosed("ancestor", surface);
                }
              }
              notifyOpen(false, "native", surface);
              return;
            }
            internalOpen = false;
            logicalOpen = false;
            closeAllSubmenus();
            surface.inert = true;
            surface.removeAttribute("data-open");
            layerCoordinator.unregister(layer, { cascade: true });
            updateTrigger();
            notifyOpen(false, "native", surface);
            controllerOptions.closed?.();
          };
          surface.addEventListener("toggle", onToggle);

          effect(() => {
            const suppliedOpen = props.open;
            if (!Object.is(suppliedOpen, previousOpenInput)) {
              previousOpenInput = suppliedOpen;
              openInputRevision += 1;
            }
            if (suppliedOpen === undefined || suppliedOpen === null) {
              if (controlled) {
                internalOpen = logicalOpen;
              }
              controlled = false;
              previousControlledOpen = null;
              structuralSuppressed = false;
              layerCoordinator.clearSuppression(layer);
              invalidEpisodes.delete("open");
            } else if (typeof suppliedOpen === "boolean") {
              if (previousControlledOpen === false && suppliedOpen) {
                structuralSuppressed = false;
                layerCoordinator.clearSuppression(layer);
              }
              controlled = true;
              previousControlledOpen = suppliedOpen;
              invalidEpisodes.delete("open");
            } else {
              reportInvalid("open", suppliedOpen, "releasing control from the committed state");
              controlled = false;
              previousControlledOpen = null;
              internalOpen = logicalOpen;
            }
            configuration = {
              disabled: resolveBoolean("disabled"),
              loop: resolveBoolean("loop"),
              placement: resolveChoice("placement"),
              matchWidth: resolveBoolean("matchWidth"),
              closeOnSelect: resolveBoolean("closeOnSelect"),
              size: resolveChoice("size"),
            };
            onOpenChange = resolveCallback("onOpenChange");
            onAction = resolveCallback("onAction");
            if (surface.dataset.placement !== configuration.placement) {
              surface.dataset.placement = configuration.placement;
            }
            if (surface.dataset.size !== configuration.size) {
              surface.dataset.size = configuration.size;
            }
            surface.toggleAttribute("data-match-width", configuration.matchWidth);
            updateTrigger();
            const effectiveDisabled = effectiveOwnerDisabled();
            if (pendingDisabledHandoff && effectiveDisabled) {
              pendingDisabledHandoff = false;
              if (!controlled) {
                internalOpen = false;
              }
              normalizeRootClosed("disabled", trigger);
              focusFallback();
              notifyOpen(false, "disabled", trigger, true);
            } else if (effectiveDisabled && logicalOpen) {
              if (!controlled) {
                internalOpen = false;
              }
              applyRootOpen(false, { reason: "disabled", source: trigger });
              notifyOpen(false, "disabled", trigger, true);
            }
            pendingDisabledHandoff = false;
            committedEffectiveDisabled = effectiveDisabled;
            controllerOptions.disabledChanged?.();
            scheduleReconcile();
          });

          const reconcileNativeDisabled = (records = []) => {
            if (recordsAuthorDisabled) {
              const triggerRecords = records.filter((record) => (
                record.type === "attributes" && record.target === trigger
              ));
              const ownWrites = ownDisabledWrites;
              let authorValue = null;
              triggerRecords.forEach((record, index) => {
                // A record holds only the value before its write; the value
                // after it is the next record's old value, or the trigger's
                // current value for the last record.
                const before = record.oldValue !== null;
                const after = index + 1 < triggerRecords.length
                  ? triggerRecords[index + 1].oldValue !== null
                  : trigger.hasAttribute("disabled");
                if (ownWrites.length > 0 && before !== after && ownWrites[0] === after) {
                  ownWrites.shift();
                } else {
                  authorValue = after;
                }
              });
              if (authorValue !== null) {
                // Page code or Vue wrote the trigger's `disabled`; that is now
                // the author's value, for this run and for the cleanup to put
                // back.
                authorDirectDisabled = authorValue;
                authorTriggerDisabled = authorValue;
              }
            }
            updateTrigger();
            const effectiveDisabled = effectiveOwnerDisabled();
            if (effectiveDisabled && logicalOpen) {
              if (!controlled) {
                internalOpen = false;
              }
              applyRootOpen(false, { reason: "disabled", source: trigger });
              notifyOpen(false, "disabled", trigger, true);
            } else if (!effectiveDisabled && (controlled ? props.open === true : internalOpen)) {
              applyRootOpen(true, { reason: "disabled", source: trigger, focus: "first" });
            }
            committedEffectiveDisabled = effectiveDisabled;
            controllerOptions.disabledChanged?.();
          };
          const registerNativeDisabled = () => {
            anchoredLayerRuntime.menuDisabledObservers ??= new WeakMap();
            const rootNode = disabledElement.getRootNode();
            let manager = anchoredLayerRuntime.menuDisabledObservers.get(rootNode);
            if (!manager) {
              const entries = new Map();
              const observer = new MutationObserver((records) => {
                for (const [registeredTrigger, callback] of entries) {
                  const affected = records.filter((record) => {
                    if (record.target === registeredTrigger) {
                      return true;
                    }
                    if (record.target instanceof Element && record.target.contains(registeredTrigger)) {
                      return true;
                    }
                    return [...record.addedNodes, ...record.removedNodes].some((node) => (
                      node === registeredTrigger
                      || (node instanceof Element && node.contains(registeredTrigger))
                    ));
                  });
                  if (affected.length > 0) {
                    callback(affected);
                  }
                }
              });
              observer.observe(rootNode, {
                subtree: true,
                childList: true,
                attributes: true,
                attributeOldValue: true,
                attributeFilter: ["disabled"],
              });
              manager = { entries, observer };
              anchoredLayerRuntime.menuDisabledObservers.set(rootNode, manager);
            }
            manager.entries.set(disabledElement, reconcileNativeDisabled);
            return () => {
              if (manager.entries.get(disabledElement) !== reconcileNativeDisabled) {
                return;
              }
              manager.entries.delete(disabledElement);
              if (manager.entries.size === 0) {
                manager.observer.disconnect();
                anchoredLayerRuntime.menuDisabledObservers.delete(rootNode);
              }
            };
          };
          let nativeDisabledRoot = null;
          let unregisterNativeDisabled = () => {};
          refreshNativeDisabledObserver = () => {
            const nextRoot = disabledElement.getRootNode();
            if (nextRoot === nativeDisabledRoot) {
              return;
            }
            unregisterNativeDisabled();
            // Records for writes made under an old root may never arrive, so a
            // queued write could later be matched against an author write. The
            // first registration keeps the queue: an observer another Menu
            // already runs on this root still delivers those records.
            if (nativeDisabledRoot !== null) {
              ownDisabledWrites.length = 0;
            }
            nativeDisabledRoot = nextRoot;
            unregisterNativeDisabled = registerNativeDisabled();
          };
          refreshNativeDisabledObserver();
          const structureObserver = new MutationObserver((records) => {
            const affectsAuthoredContent = records.some((record) => {
              if (record.type !== "attributes") {
                return true;
              }
              const entry = registrations.get(record.target);
              if (entry?.element === record.target) {
                return !(
                  record.attributeName === "tabindex"
                  || (record.attributeName === "href" && entry.kind === "link")
                );
              }
              return true;
            });
            if (affectsAuthoredContent) {
              scheduleReconcile();
            }
          });
          structureObserver.observe(host, {
            subtree: true,
            childList: true,
            attributes: true,
            attributeFilter: ["contenteditable", "href", "role", "tabindex", "type"],
          });

          const cleanup = (options = {}) => {
            if (!active) {
              return;
            }
            if (service.controller === context) service.controller = null;
            const handoff = options.handoff === true;
            active = false;
            runtimeState.open = logicalOpen;
            runtimeState.currentKey = currentEntry?.key ?? null;
            runtimeState.currentValue = currentEntry?.value ?? null;
            runtimeState.currentIdentity = currentEntry
              ? stableIdentity(currentEntry)
              : runtimeState.currentIdentity;
            runtimeState.currentOrder = entriesForSurface(surface).map(identityToken);
            runtimeState.currentRoots = entriesForSurface(surface).map((entry) => entry.root);
            if (currentEntry?.surface?.isConnected) {
              runtimeState.currentSurface = currentEntry.surface;
              runtimeState.currentLevelOrder = entriesForSurface(currentEntry.surface).map(identityToken);
              runtimeState.currentLevelRoots = entriesForSurface(currentEntry.surface)
                .map((entry) => entry.root);
            }
            runtimeState.openSubmenuPaths = [...submenus]
              .filter((submenu) => submenu.open)
              .map((submenu) => [...entryPath(submenu), submenu.value]);
            runtimeState.serverOpen = data.open;
            // Read this generation's committed configuration, not the live
            // retained Button attribute: a correlated morph may already have
            // applied the next generation's server-disabled attribute before
            // this cleanup runs.
            runtimeState.effectiveDisabled = committedEffectiveDisabled;
            unregisterNativeDisabled();
            // Put back the author's `disabled` before Vue applies the next render.
            // Vue writes the attribute only when the author's binding changes, so
            // without this a value the component set would outlive the render
            // and the next run would read it as the author's. Leave the trigger
            // alone when something other than this run changed it since its last
            // write, because that value is newer than anything recorded here.
            if (
              !externalActivation
              && !controllerOptions.ownsTriggerDisabled
              && writtenTriggerDisabled !== null
              && trigger.disabled === writtenTriggerDisabled
              && trigger.disabled !== authorTriggerDisabled
            ) {
              // This run no longer listens. If another Menu keeps the observer
              // running, the next run receives this record and reads it as the
              // author's value, which is right, because this write puts the
              // author's value back.
              trigger.disabled = authorTriggerDisabled;
            }
            structureObserver.disconnect();
            host.removeEventListener("click", onClick, true);
            host.removeEventListener("keydown", onKeydown, true);
            host.removeEventListener("focusin", onFocusIn, true);
            host.removeEventListener("pointerover", onPointerOver, true);
            host.removeEventListener("pointerout", onPointerOut, true);
            surface.removeEventListener("toggle", onToggle);
            if (handoff) {
              for (const submenu of submenus) {
                if (submenu.trigger?.matches?.('[aria-disabled="true"], [data-disabled]')) {
                  closeSubmenu(submenu, { restore: false });
                } else {
                  submenu.stopGeometry?.();
                  layerCoordinator.unregister(submenu.layer, { cascade: false });
                }
              }
            } else {
              closeAllSubmenus();
            }
            generation += 1;
            exitAnimation?.cancel();
            resetTypeahead();
            if (reconciliationTimer !== null) {
              clearTimeout(reconciliationTimer);
            }
            for (const task of scheduledTasks) {
              clearTimeout(task);
            }
            scheduledTasks.clear();
            layerCoordinator.unregister(layer, { cascade: !handoff });
            if (!handoff) {
              hideNativePopover(surface);
              surface.inert = true;
              surface.removeAttribute("data-open");
              surface.removeAttribute("data-citry-menu-exiting");
              surface.removeAttribute("data-citry-menu-initialized");
              controllerOptions.readyChanged?.(false);
              if (!externalActivation) {
                trigger.setAttribute("aria-expanded", "false");
              }
              controllerOptions.closed?.();
            }
            submenus.clear();
            primaryTransactions.clear();
            acceptedPrimaryClick = null;
          };
          cleanup.supportsHandoff = true;
          if (controllerOptions.controller) {
            return {
              cleanup,
              beginPrimaryAction,
              cancelOpenRequest,
              forceClose: forceRootClose,
              observePrimarySubmit,
              hasPrimaryClickToken,
              focusRoot(boundary = "first") {
                if (logicalOpen) {
                  focusBoundary(surface, boundary);
                }
              },
              isControlled: () => controlled,
              isOpen: () => logicalOpen,
              declarationSignature: () => JSON.stringify(
                [...registrations.values()]
                  .filter((entry) => entry.root?.isConnected)
                  .sort((left, right) => {
                    if (left.root === right.root) return 0;
                    return left.root.compareDocumentPosition(right.root)
                      & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
                  })
                  .map((entry) => entry.serverBaseline),
              ),
              requestOpen: requestRootOpen,
              repairOwned() {
                if (surface.inert === logicalOpen) {
                  surface.inert = !logicalOpen;
                }
                surface.toggleAttribute("data-open", logicalOpen);
                if (surface.dataset.placement !== configuration.placement) {
                  surface.dataset.placement = configuration.placement;
                }
                if (surface.dataset.size !== configuration.size) {
                  surface.dataset.size = configuration.size;
                }
                surface.toggleAttribute("data-match-width", configuration.matchWidth);
                updateTrigger();
              },
              refreshRootScope() {
                refreshNativeDisabledObserver();
                if (logicalOpen) {
                  layerCoordinator.register(layer);
                }
              },
            };
          }
          return cleanup;
        };
      
      (() => {
        const runtimeKey = Symbol.for('citry-ui:menu-root-runtime');
        const installed = globalThis[runtimeKey];
        if (installed !== undefined) {
          if (installed.generation !== 1 || installed.fingerprint !== '0911f55d695ff8f002f8ece3399e44e7af23d761819beee30477dbdba49dd9af') {
            throw new Error(
              "[citry-ui] cannot replace an incompatible CMenu runtime; "
                + "a full page reload is required.",
            );
          }
          return;
        }
        const definition = {
        helpers: {
          createCompoundAnatomy, createMenuController, createMenuService,
          externalActivationVersion: 1, hideNativePopover,
        },
        props: {
          open: {}, disabled: {}, loop: {}, placement: {}, matchWidth: {},
          closeOnSelect: {}, size: {}, onOpenChange: {}, onAction: {},
        },
        setup() {
          const service = Citry.vue.markRaw(createMenuService());
          Citry.vue.onUnmounted(() => service.dispose());
          return {menuService: service};
        },
        provide() { return {[Symbol.for("citry-ui:menu")]: this.menuService}; },
        onServerRender: ({component}) => {
          if (!anchoredLayerRuntimeCompatible) return;
          return createMenuController({
            host: component.$el,
            data: component.serverDefaults,
            props: component.$props,
            effect: Citry.vue.watchEffect,
            service: component.menuService,
          });
        },
      };
        globalThis[runtimeKey] = {
          generation: 1,
          fingerprint: '0911f55d695ff8f002f8ece3399e44e7af23d761819beee30477dbdba49dd9af',
          definition,
          factory: definition.helpers?.createMenuController,
          helpers: definition.helpers ?? {},
        };
      })();

})();