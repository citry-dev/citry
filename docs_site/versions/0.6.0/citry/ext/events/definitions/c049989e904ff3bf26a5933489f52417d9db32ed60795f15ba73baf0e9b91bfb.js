(function() {

__citryRuntime.registerTypeOptions.bind(null, "CTree_a2b596", "9f182c7eb4818f8cc388372db2f90f8163713a3a484c593a46bcad6283d1c934")({
  props: {
    expanded: {}, selected: {}, selectionMode: {}, disabled: {}, variant: {}, size: {},
    onExpandedChange: {}, onSelectionChange: {}, onAction: {},
  },
  onServerRender: ({component}) => {
    // The tree keeps its browser-side choices on its root element, so a later
    // server render that reruns this callback on the same element restores them.
    /** @typedef {{serverFingerprint: string, expanded: string[], selected: string[],
     *   activeValue: string | null | undefined}} TreeRuntime */
    const root = /** @type {HTMLElement & {__citryUiTreeRuntime?: TreeRuntime}} */ (component.$el);
    const data = component.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const invalidEpisodes = new Set();
    const allItems = () => [...root.querySelectorAll('[role="treeitem"]')]
      .filter((item) => item.closest('[role="tree"]') === root);
    const values = () => allItems().map((item) => item.dataset.value);
    const branchItems = () => allItems().filter((item) => item.hasAttribute('aria-expanded'));
    const serverFingerprint = JSON.stringify({expanded:data.expanded, selected:data.selected});
    const prior = root.__citryUiTreeRuntime;
    let committedExpanded = prior?.serverFingerprint === serverFingerprint
      ? [...prior.expanded] : [...data.expanded];
    let committedSelected = prior?.serverFingerprint === serverFingerprint
      ? [...prior.selected] : [...data.selected];
    let currentExpanded = [...committedExpanded];
    let currentSelected = [...committedSelected];
    let expandedControlled = false;
    let selectedControlled = false;
    let activeValue = prior?.activeValue ?? null;
    let callbackExpanded = null;
    let callbackSelected = null;
    let callbackAction = null;
    let configuration = {
      selectionMode: data.selectionMode, disabled: data.disabled,
      variant: data.variant, size: data.size,
    };
    let structureValid = false;
    let task = null;
    let generation = 0;
    let typeBuffer = '';
    let typeTimer = null;

    const report = (name, value) => {
      if (invalidEpisodes.has(name)) return;
      invalidEpisodes.add(name);
      console.error(`[citry-ui] CTree ${name} received invalid client value`, value);
    };
    const resolveBoolean = (name, fallback) => {
      const supplied = props[name];
      if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
      if (typeof supplied === 'boolean') { invalidEpisodes.delete(name); return supplied; }
      report(name, supplied); return fallback;
    };
    const resolveChoice = (name, fallback, allowed) => {
      const supplied = props[name];
      if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
      if (typeof supplied === 'string' && allowed.includes(supplied)) {
        invalidEpisodes.delete(name); return supplied;
      }
      report(name, supplied); return fallback;
    };
    const effectivelyDisabled = () => {
      if (configuration.disabled) return true;
      for (let node = root.parentElement; node; node = node.parentElement) {
        if (!(node instanceof HTMLFieldSetElement) || !node.disabled) continue;
        const legend = [...node.children].find((child) => child instanceof HTMLLegendElement);
        if (!(legend instanceof Element) || !legend.contains(root)) return true;
      }
      return false;
    };
    const canonicalVector = (name, supplied, allowed, mode = 'multiple') => {
      if (!Array.isArray(supplied) || !supplied.every((value) => typeof value === 'string'
          && value.length > 0 && !/[\u0000\t\n\f\r ]/.test(value))) return null;
      if (new Set(supplied).size !== supplied.length
          || supplied.some((value) => !allowed.has(value))) return null;
      if (mode === 'none' && supplied.length > 0) return null;
      if (mode === 'single' && supplied.length > 1) return null;
      invalidEpisodes.delete(name);
      return [...supplied];
    };
    const itemFor = (value) => allItems().find((item) => item.dataset.value === value) ?? null;
    const groupFor = (item) => [...item.children]
      .find((child) => child.getAttribute?.('role') === 'group') ?? null;
    const parentItem = (item) => {
      const group = item.parentElement;
      return group?.getAttribute('role') === 'group' ? group.parentElement?.closest('[role="treeitem"]') : null;
    };
    const directChildren = (item) => {
      const group = groupFor(item);
      return group ? [...group.children].filter((child) => child.getAttribute?.('role') === 'treeitem') : [];
    };
    const isItemDisabled = (item) => effectivelyDisabled()
      || item.hasAttribute('data-cui-tree-item-disabled');
    const visibleItems = () => allItems().filter((item) => {
      for (let node = item.parentElement; node && node !== root; node = node.parentElement) {
        if (node.getAttribute?.('role') === 'group' && node.hidden) return false;
      }
      return true;
    });
    const structureProblem = () => {
      const items = allItems();
      if (items.length === 0) return 'requires one or more Items';
      if (new Set(values()).size !== items.length) return 'contains duplicate Item values';
      const roots = [...root.children].filter((child) => child.getAttribute?.('role') === 'treeitem');
      if (roots.length !== root.children.length) return 'contains an unknown direct root child';
      for (const item of items) {
        const children = [...item.children];
        if (!children[0]?.matches?.('[data-citry-ui-part="row"]')) return 'Item row anatomy is invalid';
        const groups = children.filter((child) => child.getAttribute?.('role') === 'group');
        if (groups.length > 1 || children.length !== 1 + groups.length) return 'Item child anatomy is invalid';
        if (groups[0] && [...groups[0].children].some((child) => child.getAttribute?.('role') !== 'treeitem')) {
          return 'Item groups may contain only Tree Items';
        }
      }
      return null;
    };
    const focusItem = (item) => {
      if (!(item instanceof HTMLElement)) return;
      activeValue = item.dataset.value;
      allItems().forEach((entry) => { entry.tabIndex = entry === item ? 0 : -1; });
      item.focus();
    };
    const detail = (value, previous, controlled, source, item, event, stateName, state) => ({
      value, [stateName]: state, [`previous${stateName[0].toUpperCase()}${stateName.slice(1)}`]: [...previous],
      controlled, source, item, sourceEvent: event,
    });
    const requestExpanded = (item, expanded, event, source) => {
      if (isItemDisabled(item) || !groupFor(item)) return;
      const value = item.dataset.value;
      const previous = [...currentExpanded];
      const next = expanded
        ? [...previous.filter((entry) => entry !== value), value]
        : previous.filter((entry) => entry !== value);
      callbackExpanded?.([...next], detail(
        value, previous, expandedControlled, source, item, event, 'expanded', expanded
      ));
      if (!expandedControlled) { committedExpanded = [...next]; currentExpanded = [...next]; sync(); }
      else schedule();
    };
    const requestSelection = (item, event, source) => {
      if (configuration.selectionMode === 'none' || isItemDisabled(item)) return;
      const value = item.dataset.value;
      const previous = [...currentSelected];
      const selected = !previous.includes(value);
      const next = configuration.selectionMode === 'single'
        ? (selected ? [value] : [])
        : (selected ? [...previous, value] : previous.filter((entry) => entry !== value));
      callbackSelected?.([...next], detail(
        value, previous, selectedControlled, source, item, event, 'selected', selected
      ));
      if (!selectedControlled) { committedSelected = [...next]; currentSelected = [...next]; sync(); }
      else schedule();
    };
    const sync = () => {
      const problem = structureProblem();
      if (problem) {
        structureValid = false;
        report('structure', problem);
        root.removeAttribute('data-citry-tree-initialized');
        allItems().forEach((item) => { item.tabIndex = -1; item.setAttribute('aria-disabled', 'true'); });
        return;
      }
      structureValid = true;
      invalidEpisodes.delete('structure');
      const itemValues = new Set(values());
      const branches = new Set(branchItems().map((item) => item.dataset.value));
      let suppliedExpanded = props.expanded;
      if (suppliedExpanded === null) suppliedExpanded = undefined;
      if (suppliedExpanded === undefined) {
        invalidEpisodes.delete('expanded');
        if (expandedControlled) committedExpanded = currentExpanded.filter((value) => branches.has(value));
        expandedControlled = false;
        currentExpanded = committedExpanded.filter((value) => branches.has(value));
      } else {
        const valid = canonicalVector('expanded', suppliedExpanded, branches);
        expandedControlled = true;
        if (valid) currentExpanded = valid;
        else {
          report('expanded', suppliedExpanded);
          currentExpanded = committedExpanded.filter((value) => branches.has(value));
        }
      }
      let suppliedSelected = props.selected;
      if (suppliedSelected === null) suppliedSelected = undefined;
      if (suppliedSelected === undefined) {
        invalidEpisodes.delete('selected');
        if (selectedControlled) committedSelected = currentSelected.filter((value) => itemValues.has(value));
        selectedControlled = false;
        currentSelected = committedSelected.filter((value) => itemValues.has(value));
      } else {
        const valid = canonicalVector('selected', suppliedSelected, itemValues, configuration.selectionMode);
        selectedControlled = true;
        if (valid) currentSelected = valid;
        else {
          report('selected', suppliedSelected);
          currentSelected = committedSelected.filter((value) => itemValues.has(value));
        }
      }
      if (configuration.selectionMode === 'none') currentSelected = [];
      if (configuration.selectionMode === 'single') currentSelected = currentSelected.slice(0, 1);
      const disabled = effectivelyDisabled();
      root.dataset.selectionMode = configuration.selectionMode;
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      root.toggleAttribute('data-disabled', disabled);
      allItems().forEach((item) => {
        const value = item.dataset.value;
        const group = groupFor(item);
        const expanded = Boolean(group && currentExpanded.includes(value));
        const selected = currentSelected.includes(value);
        const itemDisabled = isItemDisabled(item);
        item.setAttribute('aria-disabled', itemDisabled ? 'true' : 'false');
        item.toggleAttribute('data-disabled', itemDisabled);
        if (group) {
          item.setAttribute('aria-expanded', expanded ? 'true' : 'false');
          item.toggleAttribute('data-expanded', expanded);
          group.hidden = !expanded;
          group.inert = !expanded;
        }
        if (configuration.selectionMode === 'none') item.removeAttribute('aria-selected');
        else item.setAttribute('aria-selected', selected ? 'true' : 'false');
        item.toggleAttribute('data-selected', selected);
      });
      const visible = visibleItems();
      let active = itemFor(activeValue);
      if (!(active instanceof HTMLElement) || !visible.includes(active)) {
        active = visible.find((item) => currentSelected.includes(item.dataset.value)) ?? visible[0] ?? null;
      }
      allItems().forEach((item) => { item.tabIndex = item === active && !disabled ? 0 : -1; });
      activeValue = active?.dataset.value ?? null;
      root.__citryUiTreeRuntime = {
        serverFingerprint, expanded:[...committedExpanded], selected:[...committedSelected], activeValue,
      };
      root.setAttribute('data-citry-tree-initialized', '');
    };
    const schedule = () => {
      if (task !== null) return;
      const scheduled = generation;
      task = setTimeout(() => { task = null; if (scheduled === generation) sync(); }, 0);
    };
    const itemFromEvent = (event) => event.composedPath().find(
      (node) => node instanceof HTMLElement && node.getAttribute?.('role') === 'treeitem'
        && node.closest('[role="tree"]') === root
    );
    const onClick = (event) => {
      if (!structureValid) return;
      const item = itemFromEvent(event);
      if (!(item instanceof HTMLElement)) return;
      focusItem(item);
      const indicator = event.composedPath().find(
        (node) => node instanceof Element && node.matches?.('[data-citry-ui-part="indicator"]')
      );
      if (indicator && groupFor(item)) {
        requestExpanded(item, item.getAttribute('aria-expanded') !== 'true', event, 'pointer');
      }
      else requestSelection(item, event, 'pointer');
    };
    const onDoubleClick = (event) => {
      const item = itemFromEvent(event);
      if (!(item instanceof HTMLElement) || isItemDisabled(item)) return;
      callbackAction?.(item.dataset.value, {value:item.dataset.value, item, sourceEvent:event});
    };
    const onKeyDown = (event) => {
      if (!structureValid) return;
      const item = itemFromEvent(event);
      if (!(item instanceof HTMLElement)) return;
      const visible = visibleItems();
      const index = visible.indexOf(item);
      let destination = null;
      if (event.key === 'ArrowDown') destination = visible[index + 1] ?? null;
      else if (event.key === 'ArrowUp') destination = visible[index - 1] ?? null;
      else if (event.key === 'Home') destination = visible[0];
      else if (event.key === 'End') destination = visible.at(-1);
      else if (event.key === 'ArrowRight') {
        const group = groupFor(item);
        if (group && item.getAttribute('aria-expanded') !== 'true') {
          requestExpanded(item, true, event, 'keyboard');
        }
        else if (group) destination = directChildren(item)[0];
      } else if (event.key === 'ArrowLeft') {
        if (groupFor(item) && item.getAttribute('aria-expanded') === 'true') {
          requestExpanded(item, false, event, 'keyboard');
        }
        else destination = parentItem(item);
      } else if (event.key === ' ') {
        requestSelection(item, event, 'keyboard');
      } else if (event.key === 'Enter') {
        requestSelection(item, event, 'keyboard');
        if (!isItemDisabled(item)) callbackAction?.(
          item.dataset.value, {value:item.dataset.value, item, sourceEvent:event}
        );
      } else if (!event.ctrlKey && !event.metaKey && !event.altKey && event.key.length === 1) {
        const key = event.key.toLocaleLowerCase();
        if (typeBuffer.length === 1 && typeBuffer === key) typeBuffer = key;
        else typeBuffer += key;
        if (typeTimer !== null) clearTimeout(typeTimer);
        typeTimer = setTimeout(() => { typeBuffer = ''; typeTimer = null; }, 500);
        const ordered = [...visible.slice(index + 1), ...visible.slice(0, index + 1)];
        destination = ordered.find((entry) => {
          const text = entry.querySelector(':scope > [data-citry-ui-part="row"] > [data-citry-ui-part="label"]')
            ?.textContent?.trim().replace(/\s+/g, ' ').toLocaleLowerCase() ?? '';
          return text.startsWith(typeBuffer);
        });
      } else return;
      event.preventDefault();
      if (destination instanceof HTMLElement) focusItem(destination);
    };
    const onFocusIn = (event) => {
      const item = itemFromEvent(event);
      if (item instanceof HTMLElement) {
        activeValue = item.dataset.value;
        allItems().forEach((entry) => { entry.tabIndex = entry === item ? 0 : -1; });
      }
    };
    root.addEventListener('click', onClick);
    root.addEventListener('dblclick', onDoubleClick);
    root.addEventListener('keydown', onKeyDown);
    root.addEventListener('focusin', onFocusIn);
    const observer = new MutationObserver(schedule);
    observer.observe(root, {childList:true, subtree:true});
    const fieldsets = [];
    for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
      if (!(ancestor instanceof HTMLFieldSetElement)) continue;
      const item = new MutationObserver(schedule);
      item.observe(ancestor, {childList:true, attributes:true, attributeFilter:['disabled']});
      fieldsets.push(item);
    }
    const stop = effect(() => {
      callbackExpanded = typeof props.onExpandedChange === 'function' ? props.onExpandedChange : null;
      callbackSelected = typeof props.onSelectionChange === 'function' ? props.onSelectionChange : null;
      callbackAction = typeof props.onAction === 'function' ? props.onAction : null;
      configuration = {
        selectionMode: resolveChoice('selectionMode', data.selectionMode, ['none','single','multiple']),
        disabled: resolveBoolean('disabled', data.disabled),
        variant: resolveChoice('variant', data.variant, ['plain','soft','outline']),
        size: resolveChoice('size', data.size, ['sm','md','lg']),
      };
      schedule();
    });
    schedule();
    return () => {
      generation += 1;
      if (task !== null) clearTimeout(task);
      if (typeTimer !== null) clearTimeout(typeTimer);
      root.__citryUiTreeRuntime = {
        serverFingerprint, expanded:[...committedExpanded], selected:[...committedSelected], activeValue,
      };
      stop?.(); observer.disconnect(); fieldsets.forEach((item) => item.disconnect());
      root.removeEventListener('click', onClick);
      root.removeEventListener('dblclick', onDoubleClick);
      root.removeEventListener('keydown', onKeyDown);
      root.removeEventListener('focusin', onFocusIn);
      root.removeAttribute('data-citry-tree-initialized');
    };
  },
})

})();