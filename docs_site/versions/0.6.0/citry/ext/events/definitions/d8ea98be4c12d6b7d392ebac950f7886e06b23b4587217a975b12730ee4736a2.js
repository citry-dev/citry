(function() {

__citryRuntime.registerTypeOptions.bind(null, "CMenuCheckboxItem_45058b", "7075156e5d00a2fb915812b0ebf253b919b2cb38f10dd7fcd81c65c74af34c99")({
  props: {
    disabled: {},
    closeOnSelect: {},
    intent: {},
    textValue: {},
    checked: {},
    onCheckedChange: {},
  },
  inject: {menuContext: {from: Symbol.for("citry-ui:menu"), default: null}},
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = {
      componentName: component.componentName, key: component.key,
      kind: component.kind, value: component.value, href: component.href,
      ...component.serverDefaults,
    };
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const context = component.menuContext;
    if (!context) {
      console.error(
        `[citry-ui] ${data.componentName} requires the nearest CMenu client context.`,
        root,
      );
      return;
    }
    const label = root.querySelector(
      ':scope > .cui-menu__item-copy > [data-citry-ui-part="menu-item-label"]',
    );
    const description = root.querySelector(
      ':scope > .cui-menu__item-copy > '
        + '[data-citry-ui-part="menu-item-description"]',
    );
    const contentRegions = [
      root.querySelector(':scope > [data-citry-ui-part="menu-item-start"]'),
      label,
      description,
      root.querySelector(':scope > [data-citry-ui-part="menu-item-end"]'),
    ].filter(Boolean);
    if (!label) {
      console.error(`[citry-ui] ${data.componentName} could not resolve its label.`, root);
      return;
    }
    const invalidEpisodes = new Set();
    let controlledChecked = false;
    const runtimeState = root.__citryUiMenuItemRuntime ?? {
      checked: data.checked,
      serverChecked: data.checked,
    };
    root.__citryUiMenuItemRuntime = runtimeState;
    let committedChecked = runtimeState.serverChecked === data.checked
      ? runtimeState.checked
      : data.checked;
    let onCheckedChange = null;

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
        `[citry-ui] ${data.componentName} ${name} received invalid client value `
          + `${describeValue(value)}; ${fallback}.`,
        root,
      );
    };
    const booleanValue = (name, fallback) => {
      const value = props[name] === undefined ? fallback : props[name];
      if (typeof value === "boolean") {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value, "using the server-rendered fallback");
      return fallback;
    };
    const optionalBoolean = () => {
      const value = props.closeOnSelect === undefined
        ? data.closeOnSelect
        : props.closeOnSelect;
      if (value === null || typeof value === "boolean") {
        invalidEpisodes.delete("closeOnSelect");
        return value;
      }
      reportInvalid("closeOnSelect", value, "using the server-rendered fallback");
      return data.closeOnSelect;
    };
    const intentValue = () => {
      const value = props.intent === undefined ? data.intent : props.intent;
      if (["default", "danger"].includes(value)) {
        invalidEpisodes.delete("intent");
        return value;
      }
      reportInvalid("intent", value, "using the server-rendered fallback");
      return data.intent;
    };
    const textValue = () => {
      const value = props.textValue === undefined ? data.textValue : props.textValue;
      if (value === null) {
        invalidEpisodes.delete("textValue");
        return value;
      }
      const normalized = canonicalString(value);
      if (normalized !== null) {
        invalidEpisodes.delete("textValue");
        return normalized;
      }
      reportInvalid("textValue", value, "using the server-rendered fallback");
      return data.textValue;
    };
    const checkedValue = () => {
      const supplied = props.checked;
      if (supplied === undefined || supplied === null) {
        if (controlledChecked) {
          committedChecked = entry.checked;
        }
        controlledChecked = false;
        invalidEpisodes.delete("checked");
        return committedChecked;
      }
      if (typeof supplied === "boolean" || supplied === "mixed") {
        controlledChecked = true;
        invalidEpisodes.delete("checked");
        return supplied;
      }
      reportInvalid("checked", supplied, "releasing control from the committed state");
      controlledChecked = false;
      return committedChecked;
    };
    const callbackValue = () => {
      const value = props.onCheckedChange;
      if (value === undefined || value === null || typeof value === "function") {
        invalidEpisodes.delete("onCheckedChange");
        return value ?? null;
      }
      reportInvalid("onCheckedChange", value, "ignoring the callback");
      return null;
    };
    const canonicalString = (value) => (
      typeof value === "string" && !value.includes("\0")
        ? value.replace(/\r\n?/g, "\n")
        : null
    );
    const applyState = () => {
      root.toggleAttribute("data-disabled", entry.effectiveDisabled);
      if (entry.effectiveDisabled) {
        root.setAttribute("aria-disabled", "true");
        if (root instanceof HTMLAnchorElement) {
          root.removeAttribute("href");
        }
      } else {
        root.removeAttribute("aria-disabled");
        if (root instanceof HTMLAnchorElement && data.href !== null) {
          root.setAttribute("href", data.href);
        }
      }
      if (entry.kind === "item" || entry.kind === "link") {
        root.dataset.intent = entry.intent;
      }
      if (entry.kind === "checkbox") {
        root.setAttribute("aria-checked", String(entry.checked));
        root.dataset.checked = String(entry.checked);
      }
      if (entry.kind === "radio") {
        root.setAttribute("aria-checked", entry.checked ? "true" : "false");
        root.dataset.checked = entry.checked ? "true" : "false";
      }
    };
    const forbiddenContent = () => {
      const selector = [
        "a[href]",
        "button",
        "input",
        "select",
        "textarea",
        "[contenteditable]:not([contenteditable='false'])",
        "[tabindex]:not([tabindex='-1'])",
        "[role='menuitem']",
        "[role='menuitemcheckbox']",
        "[role='menuitemradio']",
      ].join(",");
      return contentRegions.some((region) => region.querySelector(selector));
    };
    const entry = {
      root,
      element: root,
      label,
      description,
      key: data.key,
      kind: data.kind === "item" && data.href !== null ? "link" : data.kind,
      value: data.value,
      href: data.href,
      surface: context.surface,
      container: context.container,
      path: [...(context.path ?? [])],
      parent: context.parentSubmenu,
      radioGroup: context.radioGroup,
      ownDisabled: data.disabled,
      effectiveDisabled: data.disabled,
      closeOnSelect: data.closeOnSelect,
      intent: data.intent,
      textValue: data.textValue,
      checked: data.checked,
      refresh() {
        entry.effectiveDisabled = booleanValue("disabled", data.disabled);
        entry.closeOnSelect = optionalBoolean();
        entry.textValue = textValue();
        if (entry.kind === "item" || entry.kind === "link") {
          entry.intent = intentValue();
        }
        if (entry.kind === "checkbox") {
          entry.checked = checkedValue();
          onCheckedChange = callbackValue();
        }
        applyState();
      },
      validate() {
        if (forbiddenContent()) {
          console.error(
            `[citry-ui] ${data.componentName} content must remain noninteractive.`,
            root,
          );
          return false;
        }
        return true;
      },
      requestChecked(event, path) {
        if (entry.kind !== "checkbox") {
          return true;
        }
        const previous = entry.checked;
        const requested = previous === "mixed" ? true : !previous;
        const callback = onCheckedChange;
        if (!controlledChecked) {
          committedChecked = requested;
          entry.checked = requested;
          applyState();
        }
        callback?.(requested, {
          checked: requested,
          previousChecked: previous,
          controlled: controlledChecked,
          item: root,
          event,
          path: [...path],
        });
        return true;
      },
      setRadioChecked(checked) {
        entry.checked = checked;
        applyState();
      },
    };
    const unregister = context.register(entry);
    effect(() => {
      entry.refresh();
      context.update(entry);
    });
    return () => {
      if (entry.kind === "checkbox") {
        runtimeState.checked = entry.checked;
        runtimeState.serverChecked = data.checked;
      }
      unregister();
    };
  },
});

})();