(function() {

__citryRuntime.registerTypeOptions.bind(null, "CTagGroup_765ed5", "4a4d55fef444b2cb7bc849e6fa63518f5a25bc858c7de5aff04f57ff84e6237b")({
  props: {
    value: {}, disabled: {}, variant: {}, size: {},
    onValueChange: {}, onAction: {}, onRemove: {},
  },
  inject: {formService: {from: Symbol.for("citry-ui:form"), default: null}},
  onServerRender: ({component}) => {
    // The group keeps its browser-side selection on its root element, so a later
    // server render that reruns this callback on the same element restores it.
    // Each CTag calls `__citryTagChanged` on this root to ask the group to check its tags again.
    /** @typedef {{selection: string | string[] | null, serverValueFingerprint: string | null,
     *   focusedValue: string | null | undefined, order: string[]}} TagGroupRuntime */
    const root = /** @type {HTMLElement & {__citryUiTagRuntime?: TagGroupRuntime,
     *   __citryTagChanged?: () => void}} */ (component.$el);
    const data = {...component.serverDefaults,
      serverValueFingerprint: component.serverValueFingerprint};
    const props = component.$props;
    const list = root.querySelector(':scope > [data-citry-ui-part="list"]');
    const form = component.formService;
    const invalidEpisodes = new Set();
    // Each CTag publishes its entry on its own root. Vue runs child callbacks
    // before this one, and a server revision may rerun only this callback, so
    // the group reads entries from the DOM instead of keeping its own registry.
    const entryOf = (tag) => tag.__citryTagEntry ?? null;
    const runtime = root.__citryUiTagRuntime ?? {
      selection: data.selectionMode === "multiple" ? [] : null,
      serverValueFingerprint: null,
      focusedValue: null,
      order: [],
    };
    root.__citryUiTagRuntime = runtime;
    if (runtime.serverValueFingerprint !== data.serverValueFingerprint) {
      runtime.selection = data.selectionMode === "multiple" ? [...(data.value ?? [])] : data.value;
      runtime.serverValueFingerprint = data.serverValueFingerprint;
    }
    let committed = data.selectionMode === "multiple"
      ? new Set(runtime.selection ?? [])
      : runtime.selection;
    let controlled = false;
    let reconcileTimer = null;
    let typeaheadTimer = null;
    let typeaheadBuffer = "";
    let focusWithin = false;
    let structureInvalid = false;
    let generation = 1;
    const report = (name, value) => {
      if (invalidEpisodes.has(name)) return;
      invalidEpisodes.add(name);
      console.error(`[citry-ui] CTagGroup ${name} received invalid client value`, value);
    };
    const clearEpisode = (name) => invalidEpisodes.delete(name);
    const directTags = () => [...list.querySelectorAll(':scope > [data-citry-ui-part="tag"]')];
    const entries = () => directTags().map(entryOf).filter(Boolean);
    const canonical = (value) => typeof value === "string" && !value.includes("\0")
      ? value.replace(/\r\n?/g, "\n") : null;
    const known = () => new Set(entries().map((entry) => entry.value));
    const publicValue = (value) => data.selectionMode === "multiple" ? [...value] : value;
    const selectedSet = (value) => data.selectionMode === "multiple"
      ? value : new Set(value === null ? [] : [value]);
    const validCallback = (name) => {
      const supplied = props[name];
      if (supplied === undefined || supplied === null) { clearEpisode(name); return null; }
      if (typeof supplied === "function") { clearEpisode(name); return supplied; }
      report(name, supplied);
      return null;
    };
    const resolveChoice = (name, fallback, allowed) => {
      const supplied = props[name];
      if (supplied === undefined) { clearEpisode(name); return fallback; }
      if (typeof supplied === "string" && allowed.includes(supplied)) {
        clearEpisode(name); return supplied;
      }
      report(name, supplied);
      return fallback;
    };
    const inDisabledFieldset = () => {
      let node = root.parentElement;
      while (node) {
        if (node instanceof HTMLFieldSetElement && node.disabled) {
          const firstLegend = [...node.children].find((child) => child instanceof HTMLLegendElement);
          if (!firstLegend || !firstLegend.contains(root)) return true;
        }
        node = node.parentElement;
      }
      return false;
    };
    const localDisabled = () => {
      if (props.disabled === undefined) { clearEpisode("disabled"); return data.disabled; }
      if (typeof props.disabled === "boolean") { clearEpisode("disabled"); return props.disabled; }
      report("disabled", props.disabled);
      return data.disabled;
    };
    const effectiveGroupDisabled = () => Boolean(form?.disabled) || inDisabledFieldset() || localDisabled();
    const validStructure = () => {
      const children = [...list.children];
      if (children.some((child) => !child.matches('[data-citry-ui-part="tag"]'))) return false;
      if (children.some((child) => !entryOf(child))) return false;
      const values = children.map((child) => child.dataset.value);
      if (values.length !== new Set(values).size) return false;
      const interactiveSelector = [
        "a[href]", "button", "input", "select", "textarea", "label",
        "[contenteditable]:not([contenteditable='false'])", "[tabindex]",
      ].join(",");
      return !children.some((tag) => [...tag.querySelectorAll(
        '[data-citry-ui-part="tag-label"], [data-citry-ui-part="start"]'
      )].some((region) => region.matches(interactiveSelector) || region.querySelector(interactiveSelector)));
    };
    const nearest = (priorOrder, missingValue, candidates) => {
      const priorIndex = priorOrder.indexOf(missingValue);
      if (priorIndex < 0) return candidates[0] ?? null;
      for (let distance = 1; distance <= priorOrder.length; distance += 1) {
        const following = priorOrder[priorIndex + distance];
        const preceding = priorOrder[priorIndex - distance];
        const foundFollowing = candidates.find((entry) => entry.value === following);
        if (foundFollowing) return foundFollowing;
        const foundPreceding = candidates.find((entry) => entry.value === preceding);
        if (foundPreceding) return foundPreceding;
      }
      return candidates[0] ?? null;
    };
    const normalizeClientValue = (supplied) => {
      const values = known();
      if (data.selectionMode === "multiple") {
        if (!Array.isArray(supplied)) return null;
        const normalized = supplied.map(canonical);
        if (normalized.includes(null) || new Set(normalized).size !== normalized.length) return null;
        const knownValues = normalized.filter((value) => values.has(value));
        return {value: new Set(knownValues), invalid: knownValues.length !== normalized.length};
      }
      if (supplied === null) return {value: null, invalid: false};
      const normalized = canonical(supplied);
      if (normalized === null) return null;
      return {value: values.has(normalized) ? normalized : null, invalid: !values.has(normalized)};
    };
    const applySelection = (value) => {
      committed = value;
      runtime.selection = publicValue(value);
      const selected = selectedSet(value);
      entries().forEach((entry) => {
        const isSelected = selected.has(entry.value);
        entry.root.toggleAttribute("data-selected", isSelected);
        if (data.selectionMode !== "none") entry.root.setAttribute("aria-selected", String(isSelected));
        else entry.root.removeAttribute("aria-selected");
        entry.indicator.hidden = !isSelected;
      });
    };
    const applyRoving = (groupDisabled) => {
      const enabled = entries().filter((entry) => !groupDisabled && !entry.disabled);
      let current = enabled.find((entry) => entry.value === runtime.focusedValue) ?? enabled[0] ?? null;
      if (runtime.focusedValue && !entries().some((entry) => entry.value === runtime.focusedValue)) {
        current = nearest(runtime.order, runtime.focusedValue, enabled);
        if (focusWithin && current) queueMicrotask(() => current.root.focus());
        else if (focusWithin && !current) queueMicrotask(() => list.focus());
      }
      runtime.focusedValue = current?.value ?? null;
      entries().forEach((entry) => { entry.root.tabIndex = entry === current ? 0 : -1; });
    };
    const reconcile = () => {
      reconcileTimer = null;
      if (!validStructure()) {
        structureInvalid = true;
        report("structure", "Tag content must remain direct and noninteractive");
        list.inert = true;
        entries().forEach((entry) => { entry.root.tabIndex = -1; });
        root.removeAttribute("data-citry-tag-group-initialized");
        return;
      }
      structureInvalid = false;
      clearEpisode("structure");
      list.inert = false;
      const currentEntries = entries();
      const currentOrder = currentEntries.map((entry) => entry.value);
      const groupDisabled = effectiveGroupDisabled();
      const variant = resolveChoice("variant", data.variant, ["soft", "solid", "outline"]);
      const size = resolveChoice("size", data.size, ["sm", "md", "lg"]);
      root.toggleAttribute("data-disabled", groupDisabled);
      root.dataset.variant = variant;
      root.dataset.size = size;
      currentEntries.forEach((entry) => {
        entry.disabled = groupDisabled || entry.localDisabled;
        entry.root.toggleAttribute("data-disabled", entry.disabled);
        entry.root.setAttribute("aria-disabled", String(entry.disabled));
        entry.root.dataset.variant = variant;
        entry.root.dataset.size = size;
        if (entry.remove) entry.remove.disabled = entry.disabled;
      });
      controlled = props.value !== undefined;
      if (controlled && data.selectionMode !== "none") {
        const normalized = normalizeClientValue(props.value);
        if (normalized === null) report("value", props.value);
        else {
          if (normalized.invalid) report("value", props.value); else clearEpisode("value");
          applySelection(normalized.value);
        }
      } else if (!controlled) {
        clearEpisode("value");
        if (data.selectionMode === "multiple") {
          const surviving = new Set([...committed].filter((value) => known().has(value)));
          applySelection(surviving);
        } else if (committed !== null && !known().has(committed)) applySelection(null);
        else applySelection(committed);
      }
      applyRoving(groupDisabled);
      runtime.order = currentOrder;
      if (groupDisabled && focusWithin) queueMicrotask(() => list.focus());
      root.setAttribute("data-citry-tag-group-initialized", "");
    };
    const schedule = () => {
      if (reconcileTimer !== null) return;
      reconcileTimer = setTimeout(reconcile, 0);
    };
    // A Tag calls this after it publishes, changes, or withdraws its entry.
    root.__citryTagChanged = schedule;
    const ownedEntry = (target) => {
      const tag = target.closest?.('[data-citry-ui-part="tag"]');
      return tag?.closest('[data-citry-ui-part="tag-group"]') === root ? entryOf(tag) : null;
    };
    const focusEntry = (entry) => {
      if (!entry || entry.disabled) return;
      runtime.focusedValue = entry.value;
      entries().forEach((candidate) => { candidate.root.tabIndex = candidate === entry ? 0 : -1; });
      entry.root.focus();
    };
    const requestRemove = (entry, source, nativeEvent) => {
      if (structureInvalid || !data.removable || entry.disabled) return;
      const callback = validCallback("onRemove");
      const selected = selectedSet(committed);
      const values = data.selectionMode === "multiple" && selected.has(entry.value)
        ? entries().filter((item) => selected.has(item.value) && !item.disabled).map((item) => item.value)
        : [entry.value];
      callback?.([...values], {
        values: [...values], tagValue: entry.value, source, nativeEvent,
      });
    };
    const activate = (entry, nativeEvent) => {
      if (structureInvalid || !entry || entry.disabled) return;
      const beforeGeneration = generation;
      if (data.selectionMode !== "none") {
        const previous = publicValue(committed);
        let next;
        if (data.selectionMode === "multiple") {
          next = new Set(committed);
          if (next.has(entry.value)) {
            if (!data.mandatory || next.size > 1) next.delete(entry.value);
          } else next.add(entry.value);
        } else {
          next = committed === entry.value && !data.mandatory ? null : entry.value;
        }
        const changed = JSON.stringify(publicValue(next)) !== JSON.stringify(previous);
        if (changed) {
          validCallback("onValueChange")?.(publicValue(next), {
            value: publicValue(next), previousValue: previous, tagValue: entry.value,
            source: "activation", controlled, nativeEvent,
          });
          if (!controlled) applySelection(next);
          else schedule();
        }
      }
      if (generation === beforeGeneration && data.actionable) {
        validCallback("onAction")?.(entry.value, {
          value: entry.value, source: "activation", nativeEvent,
        });
      }
    };
    const onClick = (event) => {
      const entry = ownedEntry(event.target);
      if (!entry) return;
      if (event.target.closest?.('[data-citry-ui-part="remove"]')) {
        event.preventDefault();
        event.stopPropagation();
        requestRemove(entry, "remove-button", event);
        return;
      }
      focusEntry(entry);
      activate(entry, event);
    };
    const normalizedText = (entry) => {
      const raw = entry.textValue || entry.label.textContent || "";
      return raw.replace(/\s+/g, " ").trim();
    };
    const lower = (value) => {
      const lang = root.closest("[lang]")?.getAttribute("lang") || document.documentElement.lang;
      try { return lang ? value.toLocaleLowerCase(lang) : value.toLocaleLowerCase(); }
      catch { return value.toLowerCase(); }
    };
    const move = (entry, direction) => {
      const enabled = entries().filter((candidate) => !candidate.disabled);
      const index = enabled.indexOf(entry);
      if (index < 0 || !enabled.length) return;
      focusEntry(enabled[(index + direction + enabled.length) % enabled.length]);
    };
    const onKeyDown = (event) => {
      const entry = ownedEntry(event.target);
      if (!entry) return;
      if (event.target.closest?.('[data-citry-ui-part="remove"]')) {
        if (event.key === "Tab" && event.shiftKey) {
          event.preventDefault(); focusEntry(entry);
        }
        return;
      }
      const rtl = getComputedStyle(root).direction === "rtl";
      if (["ArrowRight", "ArrowDown", "ArrowLeft", "ArrowUp"].includes(event.key)) {
        event.preventDefault();
        const forward = event.key === "ArrowDown" || event.key === (rtl ? "ArrowLeft" : "ArrowRight");
        move(entry, forward ? 1 : -1); return;
      }
      if (event.key === "Home" || event.key === "End") {
        event.preventDefault();
        const enabled = entries().filter((candidate) => !candidate.disabled);
        focusEntry(event.key === "Home" ? enabled[0] : enabled.at(-1)); return;
      }
      if ((event.key === "Delete" || event.key === "Backspace") && data.removable) {
        event.preventDefault(); requestRemove(entry, "delete-key", event); return;
      }
      if (event.key === "Tab" && !event.shiftKey && data.removable && entry.remove && !entry.disabled) {
        event.preventDefault(); entry.remove.focus(); return;
      }
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault(); activate(entry, event); return;
      }
      if (!event.isComposing && !event.ctrlKey && !event.metaKey && !event.altKey
          && event.key.length === 1) {
        event.preventDefault();
        const char = lower(event.key);
        typeaheadBuffer = typeaheadBuffer && [...typeaheadBuffer].every((item) => item === char)
          ? char : typeaheadBuffer + char;
        clearTimeout(typeaheadTimer);
        typeaheadTimer = setTimeout(() => { typeaheadBuffer = ""; }, 500);
        const enabled = entries().filter((candidate) => !candidate.disabled);
        const start = enabled.indexOf(entry);
        for (let offset = 1; offset <= enabled.length; offset += 1) {
          const candidate = enabled[(start + offset) % enabled.length];
          if (lower(normalizedText(candidate)).startsWith(typeaheadBuffer)) {
            focusEntry(candidate); break;
          }
        }
      }
    };
    const onFocusIn = (event) => {
      focusWithin = true;
      const entry = ownedEntry(event.target);
      if (entry) runtime.focusedValue = entry.value;
    };
    const onFocusOut = () => setTimeout(() => {
      focusWithin = root.contains(root.ownerDocument.activeElement);
    }, 0);
    root.addEventListener("click", onClick, true);
    root.addEventListener("keydown", onKeyDown, true);
    root.addEventListener("focusin", onFocusIn, true);
    root.addEventListener("focusout", onFocusOut);
    const fieldsets = [];
    let ancestor = root.parentElement;
    while (ancestor) {
      if (ancestor instanceof HTMLFieldSetElement) fieldsets.push(ancestor);
      ancestor = ancestor.parentElement;
    }
    const fieldsetObserver = fieldsets.length ? new MutationObserver(schedule) : null;
    fieldsets.forEach((fieldset) => fieldsetObserver.observe(fieldset, {
      attributes: true, attributeFilter: ["disabled"], childList: true,
    }));
    const structureObserver = new MutationObserver((records) => {
      if (records.some((record) => record.type === "childList"
        // The observer watches child lists and attributes, and child-list records match
        // earlier, so this target is an element whose attribute changed.
        || /** @type {Element} */ (record.target).closest?.(
          '[data-citry-ui-part="tag-label"], [data-citry-ui-part="start"]',
        ))) {
        schedule();
      }
    });
    structureObserver.observe(list, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ["contenteditable", "href", "tabindex"],
    });
    const stop = Citry.vue.watchEffect(() => {
      void props.value;
      void props.disabled;
      void props.variant;
      void props.size;
      void props.onValueChange;
      void props.onAction;
      void props.onRemove;
      void form?.disabled;
      schedule();
    });
    schedule();
    return () => {
      generation += 1;
      stop?.();
      fieldsetObserver?.disconnect();
      structureObserver.disconnect();
      clearTimeout(reconcileTimer);
      clearTimeout(typeaheadTimer);
      root.removeEventListener("click", onClick, true);
      root.removeEventListener("keydown", onKeyDown, true);
      root.removeEventListener("focusin", onFocusIn, true);
      root.removeEventListener("focusout", onFocusOut);
      root.removeAttribute("data-citry-tag-group-initialized");
      delete root.__citryTagChanged;
    };
  },
})

})();