(function() {

__citryRuntime.registerTypeOptions.bind(null, "CTabs_437718", "f7d5dbd15c60c31abd763b6391a2ba115c777e9415ad51b79fab66fedeca8d92")({
  props: {
    value: {},
    onValueChange: {},
    activation: {},
    orientation: {},
    direction: {},
    loop: {},
    disabled: {},
    variant: {},
    density: {},
    align: {},
    grow: {},
  },
  onServerRender: ({component}) => {
    const root = component.$refs.tabsRoot.$el;
    const data = component.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const rootSelector = "[data-citry-tabs-root]";
    const listSelector = "[data-citry-tabs-list]";
    const tabSelector = "[data-citry-tabs-tab]";
    const panelSelector = "[data-citry-tabs-panel]";
    const allowedValues = {
      activation: ["automatic", "manual"],
      orientation: ["horizontal", "vertical"],
      direction: ["ltr", "rtl", null],
      variant: ["underline", "pill"],
      density: ["default", "comfortable", "compact"],
      align: ["start", "center", "end"],
    };
    const invalidConfigurationEpisodes = new Map();
    // Events can recreate this initializer while preserving the Tabs
    // root. Keep only the focus and ordering history needed to recover
    // from a server-rendered tab removal on that preserved DOM node.
    const runtimeState = root.__citryUiTabsRuntime ?? {
      lastFocusedValue: null,
      lastTabValues: [],
    };
    root.__citryUiTabsRuntime = runtimeState;
    let currentValue = data.value;
    let onValueChange = null;
    let lastFocusedValue = runtimeState.lastFocusedValue;
    let lastTabValues = runtimeState.lastTabValues;
    let configuration = {
      activation: data.activation,
      orientation: data.orientation,
      direction: data.direction,
      loop: data.loop,
      disabled: data.disabled,
      variant: data.variant,
      density: data.density,
      align: data.align,
      grow: data.grow,
    };

    const isOwned = (element) => element?.closest(rootSelector) === root;
    const tabs = () => [...root.querySelectorAll(tabSelector)].filter(isOwned);
    const panels = () => [...root.querySelectorAll(panelSelector)].filter(isOwned);
    const tabList = () => [...root.querySelectorAll(listSelector)].find(isOwned);
    const ownDisabled = (tab) => tab.hasAttribute("data-citry-tabs-own-disabled");
    const isInteractionDisabled = (tab) => configuration.disabled || ownDisabled(tab);
    const enabledTabs = () => tabs().filter((tab) => !isInteractionDisabled(tab));

    const tabForValue = (value) => tabs().find((tab) => tab.dataset.value === value);
    const hasDocumentFallbackFocus = () => (
      document.activeElement === document.body
      || document.activeElement === document.documentElement
    );
    const recordTabValues = () => {
      lastTabValues = tabs().map((tab) => tab.dataset.value);
      runtimeState.lastTabValues = lastTabValues;
    };
    const describeValue = (value) => {
      try {
        return JSON.stringify(value) ?? String(value);
      } catch {
        return String(value);
      }
    };
    const reportInvalidValue = (value) => {
      console.error(
        `[citry-ui] CTabs value ${describeValue(value)} does not identify an enabled tab.`,
        root,
      );
    };
    const reportInvalidConfiguration = (name, value) => {
      const describedValue = describeValue(value);
      const fingerprint = `${typeof value}:${describedValue}`;
      if (invalidConfigurationEpisodes.get(name) === fingerprint) {
        return;
      }
      invalidConfigurationEpisodes.set(name, fingerprint);
      console.error(
        `[citry-ui] CTabs ${name} received invalid client value ${describedValue}; `
          + "using the server-rendered fallback.",
        root,
      );
    };
    const resolveCallback = () => {
      const value = props.onValueChange;
      if (value === undefined || typeof value === "function") {
        invalidConfigurationEpisodes.delete("onValueChange");
        return value ?? null;
      }
      const describedValue = describeValue(value);
      const fingerprint = `${typeof value}:${describedValue}`;
      if (invalidConfigurationEpisodes.get("onValueChange") !== fingerprint) {
        invalidConfigurationEpisodes.set("onValueChange", fingerprint);
        console.error(
          `[citry-ui] CTabs onValueChange received invalid client value ${describedValue}; `
            + "ignoring the callback.",
          root,
        );
      }
      return null;
    };
    const resolveChoice = (name) => {
      const value = props[name] === undefined ? data[name] : props[name];
      if (allowedValues[name].includes(value)) {
        invalidConfigurationEpisodes.delete(name);
        return value;
      }
      reportInvalidConfiguration(name, value);
      return data[name];
    };
    const resolveBoolean = (name) => {
      const value = props[name] === undefined ? data[name] : props[name];
      if (typeof value === "boolean") {
        invalidConfigurationEpisodes.delete(name);
        return value;
      }
      reportInvalidConfiguration(name, value);
      return data[name];
    };

    const setRovingTab = (nextTab) => {
      tabs().forEach((tab) => {
        tab.tabIndex = tab === nextTab && !isInteractionDisabled(tab) ? 0 : -1;
      });
    };

    const applySelection = (value, { preserveFocus = false, scroll = false } = {}) => {
      const selectedTab = tabForValue(value);
      if (!selectedTab || ownDisabled(selectedTab)) {
        reportInvalidValue(value);
        return false;
      }

      const focusedTab = isOwned(document.activeElement) && document.activeElement.matches(tabSelector)
        ? document.activeElement
        : null;
      tabs().forEach((tab) => {
        const selected = tab === selectedTab;
        tab.setAttribute("aria-selected", selected ? "true" : "false");
        tab.dataset.state = selected ? "active" : "inactive";
      });
      panels().forEach((panel) => {
        const selected = panel.dataset.value === value;
        panel.hidden = !selected;
        panel.dataset.state = selected ? "active" : "inactive";
      });
      currentValue = value;
      root.dataset.value = value;
      setRovingTab(preserveFocus && focusedTab ? focusedTab : selectedTab);
      if (scroll) {
        selectedTab.scrollIntoView({ block: "nearest", inline: "nearest" });
      }
      return true;
    };

    const applyDisabled = (disabled) => {
      const focusedTab = isOwned(document.activeElement) && document.activeElement.matches(tabSelector)
        ? document.activeElement
        : null;
      root.toggleAttribute("data-disabled", disabled);
      const list = tabList();
      if (disabled) {
        list?.setAttribute("aria-disabled", "true");
      } else {
        list?.removeAttribute("aria-disabled");
      }
      tabs().forEach((tab) => {
        const tabDisabled = disabled || ownDisabled(tab);
        tab.disabled = tabDisabled;
        tab.toggleAttribute("data-disabled", tabDisabled);
        if (tabDisabled) {
          tab.tabIndex = -1;
        }
      });
      if (!disabled) {
        const selectedTab = tabForValue(currentValue);
        const rovingTab = focusedTab && !isInteractionDisabled(focusedTab)
          ? focusedTab
          : selectedTab;
        if (rovingTab && !isInteractionDisabled(rovingTab)) {
          setRovingTab(rovingTab);
        }
      }
    };

    const applyConfiguration = (next) => {
      configuration = next;
      root.dataset.activation = next.activation;
      root.dataset.orientation = next.orientation;
      root.toggleAttribute("data-loop", next.loop);
      root.dataset.variant = next.variant;
      root.dataset.density = next.density;
      root.dataset.align = next.align;
      root.toggleAttribute("data-grow", next.grow);

      if (next.direction === null) {
        root.removeAttribute("dir");
        root.removeAttribute("data-direction");
      } else {
        root.setAttribute("dir", next.direction);
        root.dataset.direction = next.direction;
      }

      const list = tabList();
      list?.setAttribute("aria-orientation", next.orientation);
      list?.setAttribute("data-orientation", next.orientation);
      applyDisabled(next.disabled);
    };

    const requestSelection = (tab, source) => {
      const value = tab.dataset.value;
      const previousValue = currentValue;
      if (!value || value === previousValue || isInteractionDisabled(tab)) {
        return;
      }
      const detail = { value, previousValue, source };
      onValueChange?.(value, detail);
      if (props.value === undefined) {
        applySelection(value, { preserveFocus: true, scroll: true });
      }
    };

    const fallbackAfterRemoval = (removedValue) => {
      const available = enabledTabs();
      if (available.length === 0) {
        return null;
      }
      const removedIndex = lastTabValues.indexOf(removedValue);
      if (removedIndex < 0) {
        return available[0];
      }
      const currentTabs = tabs();
      for (let offset = 0; offset < currentTabs.length; offset += 1) {
        const after = currentTabs[removedIndex + offset];
        if (after && !isInteractionDisabled(after)) {
          return after;
        }
        const before = currentTabs[removedIndex - offset - 1];
        if (before && !isInteractionDisabled(before)) {
          return before;
        }
      }
      return available[0];
    };

    const reconcileStructure = () => {
      applyDisabled(configuration.disabled);
      const serverValue = root.dataset.value;
      const serverTab = serverValue ? tabForValue(serverValue) : null;
      const currentTab = tabForValue(currentValue);
      const lostFocusedTab = lastFocusedValue !== null && !tabForValue(lastFocusedValue);

      if (serverTab && !isInteractionDisabled(serverTab) && serverValue !== currentValue) {
        applySelection(serverValue, { preserveFocus: true });
        if (lostFocusedTab && hasDocumentFallbackFocus()) {
          serverTab.focus({ preventScroll: true });
        }
      } else if (!currentTab || isInteractionDisabled(currentTab)) {
        const previousValue = currentValue;
        const fallback = fallbackAfterRemoval(previousValue);
        if (fallback) {
          const value = fallback.dataset.value;
          const detail = { value, previousValue, source: "removal" };
          onValueChange?.(value, detail);
          applySelection(value, { scroll: true });
          if (lostFocusedTab && hasDocumentFallbackFocus()) {
            fallback.focus({ preventScroll: true });
          }
        } else {
          tabs().forEach((tab) => {
            tab.setAttribute("aria-selected", "false");
            tab.dataset.state = "inactive";
            tab.tabIndex = -1;
          });
          panels().forEach((panel) => {
            panel.hidden = true;
            panel.dataset.state = "inactive";
          });
          root.removeAttribute("data-value");
        }
      } else {
        applySelection(currentValue, { preserveFocus: true });
      }
      recordTabValues();
    };

    const onClick = (event) => {
      const tab = event.target.closest?.(tabSelector);
      if (!isOwned(tab) || isInteractionDisabled(tab)) {
        return;
      }
      setRovingTab(tab);
      requestSelection(tab, "pointer");
    };

    const onFocusIn = (event) => {
      const tab = event.target.closest?.(tabSelector);
      if (isOwned(tab)) {
        lastFocusedValue = tab.dataset.value;
        runtimeState.lastFocusedValue = lastFocusedValue;
      }
    };

    const onKeydown = (event) => {
      const tab = event.target.closest?.(tabSelector);
      if (!isOwned(tab) || isInteractionDisabled(tab)) {
        return;
      }

      if (configuration.activation === "manual" && (event.key === "Enter" || event.key === " ")) {
        event.preventDefault();
        requestSelection(tab, "keyboard");
        return;
      }

      const available = enabledTabs();
      const index = available.indexOf(tab);
      if (index < 0) {
        return;
      }

      let nextIndex = null;
      if (event.key === "Home") {
        nextIndex = 0;
      } else if (event.key === "End") {
        nextIndex = available.length - 1;
      } else if (configuration.orientation === "vertical" && event.key === "ArrowDown") {
        nextIndex = index + 1;
      } else if (configuration.orientation === "vertical" && event.key === "ArrowUp") {
        nextIndex = index - 1;
      } else if (configuration.orientation === "horizontal" && event.key === "ArrowRight") {
        const rtl = getComputedStyle(root).direction === "rtl";
        nextIndex = index + (rtl ? -1 : 1);
      } else if (configuration.orientation === "horizontal" && event.key === "ArrowLeft") {
        const rtl = getComputedStyle(root).direction === "rtl";
        nextIndex = index + (rtl ? 1 : -1);
      } else {
        return;
      }

      event.preventDefault();
      if (configuration.loop) {
        nextIndex = (nextIndex + available.length) % available.length;
      } else {
        nextIndex = Math.max(0, Math.min(available.length - 1, nextIndex));
      }
      const nextTab = available[nextIndex];
      setRovingTab(nextTab);
      nextTab.focus();
      if (configuration.activation === "automatic") {
        requestSelection(nextTab, "keyboard");
      }
    };

    root.addEventListener("click", onClick);
    root.addEventListener("keydown", onKeydown);
    root.addEventListener("focusin", onFocusIn);
    effect(() => {
      applyConfiguration({
        activation: resolveChoice("activation"),
        orientation: resolveChoice("orientation"),
        direction: resolveChoice("direction"),
        loop: resolveBoolean("loop"),
        disabled: resolveBoolean("disabled"),
        variant: resolveChoice("variant"),
        density: resolveChoice("density"),
        align: resolveChoice("align"),
        grow: resolveBoolean("grow"),
      });
    });
    effect(() => {
      onValueChange = resolveCallback();
    });
    effect(() => {
      const value = props.value;
      if (value !== undefined) {
        applySelection(value, { preserveFocus: true });
      }
    });
    const list = tabList();
    const hasInvalidPhysicalStructure = list?.parentElement !== root
      || tabs().some((tab) => tab.parentElement !== list)
      || panels().some((panel) => panel.parentElement !== root);
    if (hasInvalidPhysicalStructure) {
      console.error(
        "[citry-ui] CTabs requires its generated tab list and TabPanels to be direct "
          + "DOM children of the Tabs root, and Tabs to be direct DOM children of "
          + "the generated tab list. "
          + "Component wrappers are allowed only when they render no extra element.",
        root,
      );
    }
    const focusedValueWasRemoved = lastFocusedValue !== null && !tabForValue(lastFocusedValue);
    const selectedTab = tabForValue(currentValue);
    if (focusedValueWasRemoved && selectedTab && hasDocumentFallbackFocus()) {
      selectedTab.focus({ preventScroll: true });
    }
    recordTabValues();
    const structureObserver = new MutationObserver(reconcileStructure);
    structureObserver.observe(root, { childList: true, subtree: true });
    root.setAttribute("data-citry-tabs-initialized", "");

    return () => {
      structureObserver.disconnect();
      root.removeEventListener("click", onClick);
      root.removeEventListener("keydown", onKeydown);
      root.removeEventListener("focusin", onFocusIn);
      root.removeAttribute("data-citry-tabs-initialized");
    };
  },
});

})();