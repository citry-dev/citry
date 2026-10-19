(function() {

__citryRuntime.registerTypeOptions.bind(null, "CListbox_1a159f", "fdc5338a77b2822ab37daeb4131760d9ac49785722a44778890c3f81eb349f96")({
  props: {
    value: {}, mandatory: {}, disabled: {}, loop: {}, variant: {}, size: {}, onValueChange: {},
  },
  onServerRender: ({component}) => {
    // The listbox keeps its browser-side choices on its root element, so a later
    // server render that reruns this callback on the same element restores them.
    /** @typedef {{serverFingerprint: string, committed: string[], activeValue: string | null | undefined,
     *   order: string[], pendingStructural: string | null}} ListboxRuntime */
    const root = /** @type {HTMLElement & {__citryUiListboxRuntime?: ListboxRuntime}} */ (component.$el);
    const data = component;
    const defaults = data.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const surface = root.querySelector(':scope > [data-citry-ui-part="listbox"]');
    const invalidEpisodes = new Set();
    const prior = root.__citryUiListboxRuntime;
    const serverFingerprint = JSON.stringify(defaults.value);
    let committed = prior?.serverFingerprint === serverFingerprint
      ? [...prior.committed]
      : [...defaults.value];
    let current = [...committed];
    let controlled = false;
    let activeValue = prior?.activeValue ?? null;
    let previousOrder = Array.isArray(prior?.order) ? [...prior.order] : [];
    let pendingStructural = prior?.pendingStructural ?? null;
    let configuration = {
      mandatory: defaults.mandatory,
      disabled: defaults.disabled,
      loop: defaults.loop,
      variant: defaults.variant,
      size: defaults.size,
    };
    let onValueChange = null;
    let clientValue;
    let structureValid = false;
    let task = null;
    let generation = 0;
    let typeBuffer = '';
    let typeTimer = null;

    const options = () => [...surface.querySelectorAll('[role="option"]')]
      .filter((option) => option.closest('[role="listbox"]') === surface);
    const canonicalString = (value) => (
      typeof value === 'string' && value.length > 0 && !value.includes('\0')
        ? value.replace(/\r\n?/g, '\n')
        : null
    );
    const report = (name, value, suffix = '') => {
      if (invalidEpisodes.has(name)) return;
      invalidEpisodes.add(name);
      console.error(`[citry-ui] CListbox ${name} received invalid client value${suffix}`, value);
    };
    const resolveBoolean = (name, fallback) => {
      const supplied = props[name];
      if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
      if (typeof supplied === 'boolean') { invalidEpisodes.delete(name); return supplied; }
      report(name, supplied, '; using the server fallback');
      return fallback;
    };
    const resolveChoice = (name, fallback, allowed) => {
      const supplied = props[name];
      if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
      if (typeof supplied === 'string' && allowed.includes(supplied)) {
        invalidEpisodes.delete(name);
        return supplied;
      }
      report(name, supplied, '; using the server fallback');
      return fallback;
    };
    const deepActiveElement = (documentRoot) => {
      let active = documentRoot.activeElement;
      while (active?.shadowRoot?.activeElement) active = active.shadowRoot.activeElement;
      return active;
    };
    const composedContains = (ancestor, node) => {
      for (let currentNode = node; currentNode;) {
        if (currentNode === ancestor) return true;
        currentNode = currentNode.parentNode ?? currentNode.getRootNode?.().host ?? null;
      }
      return false;
    };
    const focusBody = () => {
      const body = root.ownerDocument.body;
      if (!(body instanceof HTMLElement)) return;
      const hadTabIndex = body.hasAttribute('tabindex');
      if (!hadTabIndex) body.tabIndex = -1;
      body.focus({preventScroll:true});
      if (!hadTabIndex) queueMicrotask(() => body.removeAttribute('tabindex'));
    };
    const fieldsetDisabled = () => {
      for (let node = root.parentElement; node; node = node.parentElement) {
        if (!(node instanceof HTMLFieldSetElement) || !node.disabled) continue;
        const legend = [...node.children].find((child) => child instanceof HTMLLegendElement);
        if (!(legend instanceof Element) || !legend.contains(root)) return true;
      }
      return false;
    };
    const rootDisabled = () => configuration.disabled || fieldsetDisabled();
    const ownDisabled = (option) => option.hasAttribute('data-cui-listbox-option-disabled');
    const optionDisabled = (option) => rootDisabled() || ownDisabled(option);
    const enabledOptions = () => options().filter((option) => !optionDisabled(option));
    const valueOf = (option) => option.dataset.value;
    const optionFor = (value) => options().find((option) => valueOf(option) === value) ?? null;
    const values = () => options().map(valueOf);
    const isOption = (node) => node instanceof HTMLElement
      && node.getAttribute('role') === 'option'
      && node.closest('[role="listbox"]') === surface;
    const optionFromEvent = (event) => event.composedPath().find(isOption) ?? null;
    const formatValue = (vector) => data.multiple ? [...vector] : (vector[0] ?? null);
    const normalizeSupplied = (supplied) => {
      if (supplied === null) return {valid:true, values:[]};
      if (data.multiple) {
        if (!Array.isArray(supplied)) return {valid:false, values:[]};
        const normalized = supplied.map(canonicalString);
        if (normalized.some((value) => value === null) || new Set(normalized).size !== normalized.length) {
          return {valid:false, values:[]};
        }
        return {valid:true, values:normalized};
      }
      const normalized = canonicalString(supplied);
      return normalized === null ? {valid:false, values:[]} : {valid:true, values:[normalized]};
    };
    const nearestSurvivor = (removedValue) => {
      const enabled = new Set(enabledOptions().map(valueOf));
      const oldIndex = previousOrder.indexOf(removedValue);
      if (oldIndex >= 0) {
        for (let distance = 1; distance < previousOrder.length; distance += 1) {
          const following = previousOrder[oldIndex + distance];
          if (enabled.has(following)) return optionFor(following);
          const preceding = previousOrder[oldIndex - distance];
          if (enabled.has(preceding)) return optionFor(preceding);
        }
      }
      return enabledOptions()[0] ?? null;
    };
    const structureProblem = () => {
      const entries = options();
      if (entries.length === 0) return 'requires one or more Options';
      if (new Set(values()).size !== entries.length) return 'contains duplicate Option values';
      for (const child of surface.children) {
        if (isOption(child)) continue;
        if (child.getAttribute?.('role') !== 'group') return 'contains an unknown direct child';
        const groupChildren = [...child.children];
        if (!groupChildren[0]?.matches?.('[data-citry-ui-part="listbox-group-label"]')) {
          return 'Group label anatomy is invalid';
        }
        const grouped = groupChildren.slice(1);
        if (grouped.length === 0 || grouped.some((option) => !isOption(option))) {
          return 'Group must contain direct Options';
        }
      }
      const forbidden = [
        'a[href]', 'button', 'input', 'select', 'textarea', 'summary', 'label',
        '[contenteditable]:not([contenteditable="false"])',
        '[tabindex]:not([tabindex="-1"])', '[role="listbox"]', '[role="option"]',
      ].join(',');
      for (const option of entries) {
        const regions = option.querySelectorAll('[data-cui-listbox-slot-region]');
        if ([...regions].some((region) => region.querySelector(forbidden))) {
          return 'Option content must remain noninteractive';
        }
      }
      return null;
    };
    const saveRuntime = () => {
      root.__citryUiListboxRuntime = {
        serverFingerprint,
        committed:[...committed],
        activeValue,
        order:[...previousOrder],
        pendingStructural,
      };
    };
    const focusOption = (option, {moveFocus = true} = {}) => {
      if (!(option instanceof HTMLElement) || optionDisabled(option)) return;
      activeValue = valueOf(option);
      options().forEach((entry) => {
        const active = entry === option;
        entry.tabIndex = active && !rootDisabled() ? 0 : -1;
        entry.toggleAttribute('data-active', active);
      });
      if (moveFocus) option.focus({preventScroll:false});
    };
    const callbackDetail = (next, previous, option, selected, source, sourceEvent) => ({
      value:formatValue(next),
      previousValue:formatValue(previous),
      option,
      selected,
      controlled,
      source,
      sourceEvent,
    });
    const emitChange = (next, previous, option, selected, source, sourceEvent) => {
      onValueChange?.(
        formatValue(next),
        callbackDetail(next, previous, option, selected, source, sourceEvent),
      );
    };
    const applyState = () => {
      const disabled = rootDisabled();
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      root.toggleAttribute('data-multiple', data.multiple);
      root.toggleAttribute('data-mandatory', configuration.mandatory);
      root.toggleAttribute('data-disabled', disabled);
      surface.setAttribute('aria-disabled', disabled ? 'true' : 'false');
      if (data.multiple) surface.setAttribute('aria-multiselectable', 'true');
      else surface.removeAttribute('aria-multiselectable');
      options().forEach((option) => {
        const selected = current.includes(valueOf(option));
        const itemDisabled = optionDisabled(option);
        option.setAttribute('aria-selected', selected ? 'true' : 'false');
        option.setAttribute('aria-disabled', itemDisabled ? 'true' : 'false');
        option.toggleAttribute('data-selected', selected);
        option.toggleAttribute('data-disabled', itemDisabled);
      });
      let active = optionFor(activeValue);
      if (!(active instanceof HTMLElement) || optionDisabled(active)) {
        active = options().find((option) => current.includes(valueOf(option)) && !optionDisabled(option))
          ?? enabledOptions()[0]
          ?? null;
      }
      options().forEach((option) => {
        const isActive = option === active;
        option.tabIndex = isActive && !disabled ? 0 : -1;
        option.toggleAttribute('data-active', isActive);
      });
      activeValue = active ? valueOf(active) : null;
      previousOrder = values();
      saveRuntime();
    };
    const failClosed = (problem) => {
      const active = deepActiveElement(root.ownerDocument);
      if (composedContains(surface, active)) focusBody();
      structureValid = false;
      report('structure', problem);
      root.removeAttribute('data-citry-listbox-initialized');
      surface.inert = true;
      surface.setAttribute('aria-disabled', 'true');
      options().forEach((option) => { option.tabIndex = -1; });
    };
    const reconcileValue = () => {
      const allowed = new Set(values());
      const supplied = clientValue;
      if (supplied === undefined) {
        invalidEpisodes.delete('value');
        if (controlled) committed = [...current];
        controlled = false;
        current = committed.filter((value) => allowed.has(value));
      } else {
        const normalized = normalizeSupplied(supplied);
        if (!normalized.valid) {
          report('value', supplied, '; releasing control from the committed selection');
          if (controlled) committed = [...current];
          controlled = false;
          current = committed.filter((value) => allowed.has(value));
        } else {
          controlled = true;
          const missing = normalized.values.filter((value) => !allowed.has(value));
          current = normalized.values.filter((value) => allowed.has(value));
          if (missing.length === 0) {
            invalidEpisodes.delete('value');
            pendingStructural = null;
          } else {
            report('value', supplied, '; filtering values missing from the settled collection');
            const fingerprint = JSON.stringify([missing, current]);
            if (pendingStructural !== fingerprint) {
              const previous = [...normalized.values];
              const next = [...current];
              const scheduled = generation;
              pendingStructural = fingerprint;
              queueMicrotask(() => {
                if (generation === scheduled && pendingStructural === fingerprint) {
                  emitChange(next, previous, null, false, 'structure', null);
                }
              });
            }
          }
        }
      }
      const removedCommitted = committed.filter((value) => !allowed.has(value));
      if (!controlled && removedCommitted.length > 0) {
        const previous = [...committed];
        committed = committed.filter((value) => allowed.has(value));
        current = [...committed];
        emitChange(current, previous, null, false, 'structure', null);
      }
      if (!controlled && configuration.mandatory && current.length === 0) {
        const first = enabledOptions()[0];
        if (first) {
          const previous = [...current];
          current = [valueOf(first)];
          if (!controlled) committed = [...current];
          if (previousOrder.length > 0) {
            emitChange(current, previous, first, true, 'structure', null);
          }
        }
      }
    };
    const sync = () => {
      const focusBefore = deepActiveElement(root.ownerDocument);
      const focusRoot = root.getRootNode();
      const focusWasOwned = composedContains(surface, focusBefore);
      const focusWasLost = focusBefore === root.ownerDocument.body
        || (focusRoot instanceof ShadowRoot && focusBefore === focusRoot.host);
      const priorActive = activeValue;
      const disabled = rootDisabled();
      if (!wasDisabled && disabled) {
        const active = deepActiveElement(root.ownerDocument);
        if (composedContains(root, active)) focusBody();
      }
      wasDisabled = disabled;
      const problem = structureProblem();
      if (problem) { failClosed(problem); return; }
      structureValid = true;
      invalidEpisodes.delete('structure');
      surface.inert = false;
      reconcileValue();
      const activeOption = optionFor(activeValue);
      const activeUnavailable = activeValue !== null
        && (!(activeOption instanceof HTMLElement) || optionDisabled(activeOption));
      if (activeUnavailable) {
        const replacement = nearestSurvivor(activeValue);
        activeValue = replacement ? valueOf(replacement) : null;
      }
      applyState();
      if (activeUnavailable && (focusWasOwned || focusWasLost)) {
        const replacement = optionFor(activeValue);
        if (replacement instanceof HTMLElement) replacement.focus({preventScroll:true});
        else focusBody();
      } else if (priorActive !== null && activeValue === null && focusWasOwned) {
        focusBody();
      }
      root.setAttribute('data-citry-listbox-initialized', '');
    };
    const schedule = () => {
      if (task !== null) return;
      const scheduled = generation;
      task = setTimeout(() => {
        task = null;
        if (scheduled === generation) sync();
      }, 0);
    };
    const requestSelection = (option, event, source) => {
      if (!structureValid || !isOption(option) || optionDisabled(option)) return;
      const value = valueOf(option);
      const previous = [...current];
      const wasSelected = previous.includes(value);
      let next;
      if (data.multiple) {
        if (wasSelected && configuration.mandatory && previous.length === 1) return;
        next = wasSelected
          ? previous.filter((entry) => entry !== value)
          : [...previous, value];
      } else {
        if (wasSelected) return;
        next = [value];
      }
      if (!controlled) {
        committed = [...next];
        current = [...next];
        applyState();
      }
      emitChange(next, previous, option, !wasSelected, source, event);
      if (controlled) schedule();
    };
    const clearSelection = (event) => {
      if (configuration.mandatory || current.length === 0 || rootDisabled()) return false;
      const previous = [...current];
      const next = [];
      if (!controlled) {
        committed = [];
        current = [];
        applyState();
      }
      emitChange(next, previous, optionFor(activeValue), false, 'keyboard', event);
      if (controlled) schedule();
      return true;
    };
    const localeLower = (value) => {
      const lang = root.closest('[lang]')?.getAttribute('lang')
        ?? root.ownerDocument.documentElement.lang
        ?? '';
      try { return lang ? value.toLocaleLowerCase(lang) : value.toLocaleLowerCase(); }
      catch { return value.toLowerCase(); }
    };
    const typeaheadText = (option) => {
      const explicit = option.getAttribute('data-cui-listbox-text-value');
      const label = option.querySelector('[data-citry-ui-part="listbox-option-label"]');
      const raw = explicit ?? label?.textContent ?? '';
      return localeLower(raw.trim().replace(/\s+/g, ' '));
    };
    const onClick = (event) => {
      const option = optionFromEvent(event);
      if (!isOption(option) || optionDisabled(option)) return;
      focusOption(option);
      requestSelection(option, event, 'pointer');
    };
    const onKeyDown = (event) => {
      const option = optionFromEvent(event);
      if (!isOption(option) || optionDisabled(option) || rootDisabled()) return;
      const enabled = enabledOptions();
      const index = enabled.indexOf(option);
      let destination = null;
      if (event.key === 'ArrowDown') {
        destination = enabled[index + 1] ?? (configuration.loop ? enabled[0] : null);
      } else if (event.key === 'ArrowUp') {
        destination = enabled[index - 1] ?? (configuration.loop ? enabled.at(-1) : null);
      } else if (event.key === 'Home') destination = enabled[0] ?? null;
      else if (event.key === 'End') destination = enabled.at(-1) ?? null;
      else if (event.key === ' ' || event.key === 'Enter') {
        event.preventDefault();
        requestSelection(option, event, 'keyboard');
        return;
      } else if (event.key === 'Escape') {
        if (clearSelection(event)) event.preventDefault();
        return;
      } else {
        const altGraph = event.getModifierState?.('AltGraph') ?? false;
        if (
          event.isComposing
          || event.ctrlKey
          || event.metaKey
          || (event.altKey && !altGraph)
          || event.key.length !== 1
        ) return;
        const key = localeLower(event.key);
        typeBuffer = typeBuffer.length === 1 && typeBuffer === key ? key : typeBuffer + key;
        if (typeTimer !== null) clearTimeout(typeTimer);
        typeTimer = setTimeout(() => { typeBuffer = ''; typeTimer = null; }, 500);
        const ordered = [...enabled.slice(index + 1), ...enabled.slice(0, index + 1)];
        destination = ordered.find((entry) => typeaheadText(entry).startsWith(typeBuffer)) ?? null;
      }
      if (destination instanceof HTMLElement) {
        event.preventDefault();
        focusOption(destination);
      }
    };
    const onFocusIn = (event) => {
      const option = optionFromEvent(event);
      if (isOption(option) && !optionDisabled(option)) focusOption(option, {moveFocus:false});
    };
    const observeStructure = (records) => {
      const relevant = records.some((record) => {
        if (record.type === 'childList') return true;
        if (record.attributeName === 'tabindex' && isOption(record.target)) return false;
        return true;
      });
      if (relevant) schedule();
    };
    root.addEventListener('click', onClick, true);
    root.addEventListener('keydown', onKeyDown, true);
    root.addEventListener('focusin', onFocusIn, true);
    const observer = new MutationObserver(observeStructure);
    observer.observe(surface, {
      childList:true,
      subtree:true,
      attributes:true,
      attributeFilter:[
        'data-cui-listbox-option-disabled', 'data-cui-listbox-text-value',
        'href', 'tabindex', 'contenteditable', 'role',
      ],
    });
    const fieldsets = [];
    for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
      if (!(ancestor instanceof HTMLFieldSetElement)) continue;
      const fieldsetObserver = new MutationObserver(schedule);
      fieldsetObserver.observe(ancestor, {
        attributes:true,
        childList:true,
        attributeFilter:['disabled'],
      });
      fieldsets.push(fieldsetObserver);
    }
    let wasDisabled = rootDisabled();
    const stop = effect(() => {
      clientValue = props.value;
      onValueChange = typeof props.onValueChange === 'function' ? props.onValueChange : null;
      if (props.onValueChange !== undefined && props.onValueChange !== null && onValueChange === null) {
        report('onValueChange', props.onValueChange, '; ignoring the callback');
      } else invalidEpisodes.delete('onValueChange');
      configuration = {
        mandatory: resolveBoolean('mandatory', defaults.mandatory),
        disabled: resolveBoolean('disabled', defaults.disabled),
        loop: resolveBoolean('loop', defaults.loop),
        variant: resolveChoice('variant', defaults.variant, ['plain','soft','outline']),
        size: resolveChoice('size', defaults.size, ['sm','md','lg']),
      };
      schedule();
    });
    schedule();
    return () => {
      generation += 1;
      if (task !== null) clearTimeout(task);
      if (typeTimer !== null) clearTimeout(typeTimer);
      saveRuntime();
      stop?.();
      observer.disconnect();
      fieldsets.forEach((item) => item.disconnect());
      root.removeEventListener('click', onClick, true);
      root.removeEventListener('keydown', onKeyDown, true);
      root.removeEventListener('focusin', onFocusIn, true);
      root.removeAttribute('data-citry-listbox-initialized');
    };
  },
})

})();