(function() {

__citryRuntime.registerTypeOptions.bind(null, "CAccordion_4083eb", "b4532a0aed931fe54d5aa110f3bb2a67481e88cc89182d5746f1e32c02df0468")({
  props: {
    value: {},
    onValueChange: {},
    collapsible: {},
    disabled: {},
    loop: {},
    variant: {},
    size: {},
    indicator: {},
    indicatorPosition: {},
  },
  inject: {
    formService: {from: Symbol.for("citry-ui:form"), default: null},
  },
  setup() {
    const registrations = new Map();
    const service = Citry.vue.markRaw({
      registrations,
      schedule: null,
      registerItem(item) {
        registrations.set(item.root, item);
        service.schedule?.();
        return () => {
          if (registrations.get(item.root) !== item) {
            return;
          }
          registrations.delete(item.root);
          service.schedule?.();
        };
      },
      updateItem(item, disabled) {
        if (registrations.get(item.root) !== item) {
          return;
        }
        item.ownDisabled = disabled;
        service.schedule?.();
      },
    });
    return {accordionService: service};
  },
  provide() {
    return {[Symbol.for("citry-ui:accordion")]: this.accordionService};
  },
  onServerRender: ({component}) => {
    // The accordion keeps its browser-side state on its root element, so a later
    // server render that reruns this callback on the same element restores it.
    /** @typedef {{value: string | string[] | null, itemOrder: string[], focusedValue: string | null,
     *   serverFingerprint: string | null, reconciliations: number}} AccordionRuntime */
    const root = /** @type {HTMLElement & {__citryUiAccordionRuntime?: AccordionRuntime}} */ (component.$el);
    const data = component;
    const defaults = data.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const form = component.formService;
    const rootSelector = "[data-citry-accordion-root]";
    const itemSelector = "[data-citry-accordion-item]";
    const triggerSelector = "[data-citry-accordion-trigger]";
    const panelSelector = "[data-citry-accordion-panel]";
    const allowedValues = {
      variant: ["outline", "soft", "separated", "plain"],
      size: ["sm", "md", "lg"],
      indicatorPosition: ["start", "end"],
    };
    const invalidEpisodes = new Set();
    const animations = new Map();
    let reconciliationTimer = null;
    const runtimeState = root.__citryUiAccordionRuntime ?? {
      value: null,
      itemOrder: [],
      focusedValue: null,
      serverFingerprint: null,
      reconciliations: 0,
    };
    root.__citryUiAccordionRuntime = runtimeState;
    const initialPublicValue = runtimeState.serverFingerprint === data.serverFingerprint
      ? runtimeState.value
      : defaults.value;
    let currentValue = data.multiple
      ? Array.isArray(initialPublicValue) ? [...initialPublicValue] : []
      : typeof initialPublicValue === "string" ? [initialPublicValue] : [];
    let itemOrder = Array.isArray(runtimeState.itemOrder)
      ? [...runtimeState.itemOrder]
      : [];
    let focusedValue = runtimeState.focusedValue;
    let controlled = false;
    let onValueChange = null;
    let configuration = {
      collapsible: defaults.collapsible,
      disabled: defaults.disabled,
      loop: defaults.loop,
      variant: defaults.variant,
      size: defaults.size,
      indicator: defaults.indicator,
      indicatorPosition: defaults.indicatorPosition,
    };

    const isOwned = (element) => element?.closest(rootSelector) === root;
    const orderedItems = () => Array.from(root.querySelectorAll(itemSelector))
      .filter(isOwned)
      .map((element) => registrations.get(element))
      .filter(Boolean);
    const itemForValue = (value, items = orderedItems()) => (
      items.find((item) => item.value === value)
    );
    const values = () => orderedItems().map((item) => item.value);
    const publicValue = (normalized) => data.multiple
      ? [...normalized]
      : normalized[0] ?? null;
    const normalizeCurrent = (value, itemValues = values()) => {
      const available = new Set(itemValues);
      const sequence = Array.isArray(value)
        ? value
        : typeof value === "string"
          ? [value]
          : [];
      if (data.multiple) {
        return itemValues.filter(
          (itemValue) => sequence.includes(itemValue) && available.has(itemValue),
        );
      }
      return sequence.length > 0 && available.has(sequence[0]) ? [sequence[0]] : [];
    };

    const describeValue = (value) => {
      try {
        return JSON.stringify(value) ?? String(value);
      } catch {
        return String(value);
      }
    };
    const reportInvalid = (name, value, fallback, episode = name) => {
      if (invalidEpisodes.has(episode)) {
        return;
      }
      invalidEpisodes.add(episode);
      console.error(
        `[citry-ui] CAccordion ${name} received invalid client value `
          + `${describeValue(value)}; ${fallback}.`,
        root,
      );
    };
    const resolveBoolean = (name, fallback = defaults[name]) => {
      const value = props[name] === undefined ? fallback : props[name];
      if (typeof value === "boolean") {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value, "using the server-rendered fallback");
      return fallback;
    };
    const resolveChoice = (name, fallback = defaults[name]) => {
      const value = props[name] === undefined ? fallback : props[name];
      if (allowedValues[name].includes(value)) {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value, "using the server-rendered fallback");
      return fallback;
    };
    const resolveCallback = () => {
      const value = props.onValueChange;
      if (value === undefined || typeof value === "function") {
        invalidEpisodes.delete("onValueChange");
        return value ?? null;
      }
      reportInvalid("onValueChange", value, "ignoring the callback");
      return null;
    };
    const canonicalizeClientString = (value) => {
      if (typeof value !== "string" || value.includes("\0")) {
        return null;
      }
      return value.replace(/\r\n?/g, "\n");
    };
    const normalizeClientValue = (value, itemValues = values()) => {
      const available = new Set(itemValues);
      if (data.multiple) {
        if (value === null) {
          return [];
        }
        if (!Array.isArray(value)) {
          return null;
        }
        const canonical = value.map(canonicalizeClientString);
        if (
          canonical.some((item) => item === null)
          || new Set(canonical).size !== canonical.length
          || canonical.some((item) => !available.has(item))
        ) {
          return null;
        }
        return itemValues.filter((item) => canonical.includes(item));
      }
      if (value === null) {
        return [];
      }
      const canonical = canonicalizeClientString(value);
      return canonical !== null && available.has(canonical) ? [canonical] : null;
    };

    const durationMs = () => {
      if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
        return 0;
      }
      const raw = getComputedStyle(root).getPropertyValue("--_cui-accordion-duration").trim();
      if (raw.endsWith("ms")) {
        return Math.max(0, Number.parseFloat(raw));
      }
      if (raw.endsWith("s")) {
        return Math.max(0, Number.parseFloat(raw) * 1000);
      }
      return 0;
    };
    const cancelAnimation = (item) => {
      const animation = animations.get(item.root);
      if (!animation) {
        return;
      }
      const height = item.panel.getBoundingClientRect().height;
      animation.cancel();
      animations.delete(item.root);
      item.panel.style.blockSize = `${height}px`;
    };
    const settlePanel = (item, open) => {
      item.panel.style.removeProperty("block-size");
      item.panel.style.removeProperty("overflow");
      if (!open) {
        item.panel.hidden = true;
      }
    };
    const animatePanel = (item, open) => {
      cancelAnimation(item);
      const duration = durationMs();
      // A hidden panel has no measurable box, so opening starts at zero
      // before the panel is revealed long enough to measure its content.
      const wasHidden = item.panel.hidden;
      const start = wasHidden && open
        ? 0
        : item.panel.getBoundingClientRect().height;
      if (open) {
        item.panel.hidden = false;
        item.panel.inert = false;
        item.panel.removeAttribute("aria-hidden");
        if (wasHidden) {
          item.panel.style.blockSize = "auto";
        }
      } else {
        item.panel.inert = true;
        item.panel.setAttribute("aria-hidden", "true");
      }
      if (duration === 0 || typeof item.panel.animate !== "function") {
        settlePanel(item, open);
        return;
      }
      const end = open ? item.panel.scrollHeight : 0;
      item.panel.style.blockSize = `${start}px`;
      item.panel.style.overflow = "clip";
      const easing = getComputedStyle(root)
        .getPropertyValue("--_cui-accordion-easing")
        .trim() || "ease-out";
      const animation = item.panel.animate(
        [{ blockSize: `${start}px` }, { blockSize: `${end}px` }],
        { duration, easing },
      );
      animations.set(item.root, animation);
      animation.finished.then(() => {
        if (animations.get(item.root) !== animation) {
          return;
        }
        animations.delete(item.root);
        settlePanel(item, open);
      }).catch(() => {});
    };
    const nearestEnabled = (fromValue, items = orderedItems()) => {
      const enabled = items.filter((item) => !item.effectiveDisabled);
      if (enabled.length === 0) {
        return null;
      }
      const oldIndex = itemOrder.indexOf(fromValue);
      if (oldIndex < 0) {
        return enabled[0];
      }
      for (let offset = 0; offset <= items.length; offset += 1) {
        const afterValue = itemOrder[oldIndex + offset];
        const after = itemForValue(afterValue, items);
        if (after && !after.effectiveDisabled) {
          return after;
        }
        const beforeValue = itemOrder[oldIndex - offset - 1];
        const before = itemForValue(beforeValue, items);
        if (before && !before.effectiveDisabled) {
          return before;
        }
      }
      return enabled[0];
    };
    const applyConfiguration = () => {
      const requestedCollapsible = resolveBoolean("collapsible");
      configuration = {
        collapsible: data.multiple && !requestedCollapsible ? true : requestedCollapsible,
        disabled: Boolean(form?.disabled) || resolveBoolean("disabled"),
        loop: resolveBoolean("loop"),
        variant: resolveChoice("variant"),
        size: resolveChoice("size"),
        indicator: resolveBoolean("indicator"),
        indicatorPosition: resolveChoice("indicatorPosition"),
      };
      if (data.multiple && !requestedCollapsible) {
        reportInvalid(
          "collapsible",
          false,
          "multiple mode always remains collapsible",
          "collapsible:multiple",
        );
      } else {
        invalidEpisodes.delete("collapsible:multiple");
      }
      root.toggleAttribute("data-multiple", data.multiple);
      root.toggleAttribute("data-collapsible", configuration.collapsible);
      root.toggleAttribute("data-loop", configuration.loop);
      root.toggleAttribute("data-indicator", configuration.indicator);
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      root.dataset.indicatorPos = configuration.indicatorPosition;
    };
    const applyState = ({ animate = false, items = orderedItems() } = {}) => {
      if (items.length === 0) {
        return;
      }
      const itemValues = items.map((item) => item.value);
      const normalized = normalizeCurrent(currentValue, itemValues);
      currentValue = normalized;
      const open = new Set(normalized);
      const previouslyFocused = document.activeElement;
      let disabledFocusedValue = null;
      for (const item of items) {
        const localDisabled = configuration.disabled || item.ownDisabled;
        item.trigger.disabled = localDisabled;
        const nativeDisabled = item.trigger.matches(":disabled");
        item.effectiveDisabled = nativeDisabled;
        if (previouslyFocused === item.trigger && nativeDisabled) {
          disabledFocusedValue = item.value;
        }
      }
      const groupNativeDisabled = items.some(
        (item) => item.trigger.matches(":disabled") && !item.ownDisabled,
      );
      root.toggleAttribute("data-disabled", configuration.disabled || groupNativeDisabled);
      for (const item of items) {
        const expanded = open.has(item.value);
        const wasExpanded = item.trigger.getAttribute("aria-expanded") === "true";
        if (!expanded && wasExpanded && item.panel.contains(document.activeElement)) {
          item.trigger.focus({ preventScroll: true });
        }
        item.root.dataset.state = expanded ? "open" : "closed";
        item.trigger.dataset.state = expanded ? "open" : "closed";
        item.panel.dataset.state = expanded ? "open" : "closed";
        item.root.toggleAttribute("data-disabled", item.effectiveDisabled);
        item.trigger.toggleAttribute("data-disabled", item.effectiveDisabled);
        item.trigger.setAttribute("aria-expanded", expanded ? "true" : "false");
        const fixedOpen = !data.multiple && !configuration.collapsible && expanded;
        if (fixedOpen && !item.effectiveDisabled) {
          item.trigger.setAttribute("aria-disabled", "true");
        } else {
          item.trigger.removeAttribute("aria-disabled");
        }
        item.indicator.hidden = !configuration.indicator;
        if (animate && wasExpanded !== expanded) {
          animatePanel(item, expanded);
        } else {
          cancelAnimation(item);
          if (expanded) {
            item.panel.hidden = false;
            item.panel.inert = false;
            item.panel.removeAttribute("aria-hidden");
          } else {
            item.panel.inert = true;
            item.panel.setAttribute("aria-hidden", "true");
            item.panel.hidden = true;
          }
          settlePanel(item, expanded);
        }
      }
      if (disabledFocusedValue !== null) {
        nearestEnabled(disabledFocusedValue)?.trigger.focus({ preventScroll: true });
      }
      runtimeState.value = publicValue(currentValue);
      runtimeState.itemOrder = itemValues;
      runtimeState.focusedValue = focusedValue;
      runtimeState.serverFingerprint = data.serverFingerprint;
    };

    const callbackDetail = (next, previous, options) => ({
      value: publicValue(next),
      previousValue: publicValue(previous),
      itemValue: options.itemValue,
      removedValues: [...options.removedValues],
      expanded: options.expanded,
      source: options.source,
    });
    const commitRequest = (item) => {
      if (item.effectiveDisabled) {
        return;
      }
      const previous = [...currentValue];
      const isOpen = previous.includes(item.value);
      if (isOpen && !data.multiple && !configuration.collapsible) {
        return;
      }
      let next;
      const itemValues = values();
      if (data.multiple) {
        const requested = new Set(previous);
        if (isOpen) {
          requested.delete(item.value);
        } else {
          requested.add(item.value);
        }
        next = itemValues.filter((value) => requested.has(value));
      } else {
        next = isOpen ? [] : [item.value];
      }
      onValueChange?.(
        publicValue(next),
        callbackDetail(next, previous, {
          itemValue: item.value,
          removedValues: [],
          expanded: !isOpen,
          source: "activation",
        }),
      );
      if (!controlled) {
        currentValue = next;
        applyState({ animate: true });
      }
    };
    const readControlledValue = (itemValues = values()) => {
      const supplied = props.value;
      if (supplied === undefined) {
        controlled = false;
        invalidEpisodes.delete("value");
        return false;
      }
      if (itemValues.length === 0) {
        return false;
      }
      const normalized = normalizeClientValue(supplied, itemValues);
      if (normalized === null) {
        reportInvalid("value", supplied, "retaining the current valid state");
        return false;
      }
      invalidEpisodes.delete("value");
      controlled = true;
      currentValue = normalized;
      return true;
    };
    const reconcileStructure = () => {
      applyConfiguration();
      const items = orderedItems();
      const itemValues = items.map((item) => item.value);
      const seenValues = new Set();
      const duplicate = items.find((item) => {
        if (seenValues.has(item.value)) {
          return true;
        }
        seenValues.add(item.value);
        return false;
      });
      if (duplicate) {
        reportInvalid("items", duplicate.value, "item values must remain unique");
        return;
      }
      invalidEpisodes.delete("items");
      readControlledValue(itemValues);
      const available = new Set(itemValues);
      const previous = [...currentValue];
      const removedValues = previous.filter((value) => !available.has(value));
      let next = previous.filter((value) => available.has(value));
      if (!data.multiple && !configuration.collapsible && removedValues.length > 0 && next.length === 0) {
        const fallback = nearestEnabled(removedValues[0], items);
        next = fallback ? [fallback.value] : [];
      }
      if (removedValues.length > 0) {
        onValueChange?.(
          publicValue(next),
          callbackDetail(next, previous, {
            itemValue: null,
            removedValues,
            expanded: false,
            source: "removal",
          }),
        );
        currentValue = next;
        const fallbackFocus = focusedValue && removedValues.includes(focusedValue)
          ? nearestEnabled(focusedValue, items)
          : null;
        applyState({ items });
        if (fallbackFocus && (
          document.activeElement === document.body
          || document.activeElement === document.documentElement
        )) {
          fallbackFocus.trigger.focus({ preventScroll: true });
        }
      } else {
        currentValue = itemValues.filter((value) => next.includes(value));
        applyState({ items });
      }
      itemOrder = itemValues;
      runtimeState.reconciliations = (runtimeState.reconciliations ?? 0) + 1;
      root.setAttribute("data-citry-accordion-initialized", "");
    };
    const scheduleReconcile = () => {
      // Parent and item initializers all run in one batch. One pending
      // task absorbs their register and disabled-state updates.
      if (reconciliationTimer !== null) {
        return;
      }
      reconciliationTimer = setTimeout(() => {
        reconciliationTimer = null;
        reconcileStructure();
      }, 0);
    };
    const service = component.accordionService;
    const registrations = service.registrations;
    service.schedule = scheduleReconcile;
    scheduleReconcile();

    const onClick = (event) => {
      const trigger = event.target.closest?.(triggerSelector);
      if (!isOwned(trigger)) {
        return;
      }
      const itemRoot = trigger.closest(itemSelector);
      const item = registrations.get(itemRoot);
      if (item && item.trigger === trigger) {
        commitRequest(item);
      }
    };
    const onKeydown = (event) => {
      const trigger = event.target.closest?.(triggerSelector);
      if (!isOwned(trigger)) {
        return;
      }
      const item = registrations.get(trigger.closest(itemSelector));
      if (!item || item.effectiveDisabled) {
        return;
      }
      const enabled = orderedItems().filter((candidate) => !candidate.effectiveDisabled);
      const index = enabled.indexOf(item);
      if (index < 0) {
        return;
      }
      let nextIndex = null;
      if (event.key === "ArrowDown") {
        nextIndex = index + 1;
      } else if (event.key === "ArrowUp") {
        nextIndex = index - 1;
      } else if (event.key === "Home") {
        nextIndex = 0;
      } else if (event.key === "End") {
        nextIndex = enabled.length - 1;
      } else {
        return;
      }
      event.preventDefault();
      if (configuration.loop) {
        nextIndex = (nextIndex + enabled.length) % enabled.length;
      } else {
        nextIndex = Math.max(0, Math.min(enabled.length - 1, nextIndex));
      }
      enabled[nextIndex].trigger.focus();
    };
    const onFocusIn = (event) => {
      const item = orderedItems().find((candidate) => candidate.root.contains(event.target));
      if (!item) {
        return;
      }
      // The outer item remains the focus owner when focus enters one of
      // its actions, panel controls, or a nested Accordion.
      focusedValue = item.value;
      runtimeState.focusedValue = focusedValue;
    };

    // Capture keeps group behavior alive when a trusted descendant
    // listener stops the same event during its target or bubble phase.
    root.addEventListener("click", onClick, true);
    root.addEventListener("keydown", onKeydown, true);
    root.addEventListener("focusin", onFocusIn, true);
    effect(() => {
      applyConfiguration();
      onValueChange = resolveCallback();
      applyState();
    });
    effect(() => {
      if (readControlledValue()) {
        applyState({ animate: true });
      }
    });

    const ancestorFieldsets = [];
    for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
      if (ancestor.matches("fieldset")) {
        ancestorFieldsets.push(ancestor);
      }
    }
    const fieldsetObserver = ancestorFieldsets.length === 0
      ? null
      : new MutationObserver(() => applyState());
    ancestorFieldsets.forEach((fieldset) => {
      // Direct legend order changes the native disabled exception even
      // when the fieldset's own disabled attribute does not change.
      fieldsetObserver?.observe(fieldset, {
        attributes: true,
        attributeFilter: ["disabled"],
        childList: true,
      });
    });
    return () => {
      runtimeState.value = publicValue(currentValue);
      runtimeState.itemOrder = values();
      runtimeState.focusedValue = focusedValue;
      runtimeState.serverFingerprint = data.serverFingerprint;
      fieldsetObserver?.disconnect();
      root.removeEventListener("click", onClick, true);
      root.removeEventListener("keydown", onKeydown, true);
      root.removeEventListener("focusin", onFocusIn, true);
      animations.forEach((animation) => animation.cancel());
      animations.clear();
      if (reconciliationTimer !== null) {
        clearTimeout(reconciliationTimer);
        reconciliationTimer = null;
      }
      registrations.clear();
      service.schedule = null;
      root.removeAttribute("data-citry-accordion-initialized");
    };
  },
});

})();