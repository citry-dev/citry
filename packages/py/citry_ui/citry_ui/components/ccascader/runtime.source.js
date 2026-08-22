$component({
  props: {value:{}, open:{}, disabled:{}, onValueChange:{}, onOpenChange:{}},
  init: ({els, data, props, effect, i18n}) => {
    const root = els[0];
    const trigger = root?.querySelector(':scope > [data-citry-ui-part="trigger"]');
    const valueText = trigger?.querySelector('[data-citry-ui-part="value"]');
    const popup = root?.querySelector(':scope > [data-citry-ui-part="popup"]');
    const tree = popup?.querySelector(':scope > [data-citry-ui-part="tree"]');
    const inputs = root?.querySelector(':scope > [data-citry-ui-part="inputs"]');
    const status = root?.querySelector(':scope > [data-citry-ui-part="status"]');
    if (!(root instanceof HTMLElement) || !(trigger instanceof HTMLButtonElement) || !valueText
        || !(popup instanceof HTMLElement) || !(tree instanceof HTMLElement) || !inputs || !status) {
      throw new Error('[citry-ui] CCascader settled anatomy is invalid.');
    }
    const invalid = new Set();
    let accepted = [...data.value];
    let current = [...accepted];
    let activePath = [...accepted];
    let currentOpen = data.open;
    let controlledValue = false;
    let controlledOpen = false;
    let disabled = data.disabled;
    let valueCallback = null;
    let openCallback = null;
    let activeValue = null;
    let outsideListening = false;
    let resizeListening = false;
    let typeBuffer = '';
    let typeTimer = null;
    let reactiveReady = false;
    const report = (name, value) => {
      if (invalid.has(name)) return;
      invalid.add(name);
      console.error(`[citry-ui] CCascader ${name} received invalid client value.`, value, root);
    };
    const all = () => [...popup.querySelectorAll('[role="treeitem"]')];
    const related = id => {
      const element = id ? document.getElementById(id) : null;
      return element && popup.contains(element) ? element : null;
    };
    const parent = item => related(item.dataset.citryCascaderParent);
    const group = item => related(item.dataset.citryCascaderChildGroup);
    const path = item => {
      const result = [];
      for (let node = item; node; node = parent(node)) result.unshift(node.dataset.value);
      return result;
    };
    const labels = item => {
      const result = [];
      for (let node = item; node; node = parent(node)) {
        result.unshift(node.querySelector(':scope > [data-citry-ui-part="option-row"] > [data-citry-ui-part="option-label"]')?.textContent?.trim() ?? '');
      }
      return result;
    };
    const same = (left, right) => left.length === right.length && left.every((value,index) => value === right[index]);
    const itemFor = candidate => Array.isArray(candidate) ? all().find(item => same(path(item), candidate)) ?? null : null;
    const validPath = candidate => {
      if (!Array.isArray(candidate) || !candidate.every(value => typeof value === 'string' && value.trim() && !value.includes('\u0000'))) return null;
      if (candidate.length === 0) return true;
      const item = itemFor(candidate);
      if (!item || (group(item) && !data.change_on_select)) return null;
      for (let node = item; node; node = parent(node)) if (node.getAttribute('aria-disabled') === 'true') return null;
      return item;
    };
    const visible = () => all().filter(item => !item.closest('[data-citry-cascader-column]')?.hidden);
    const column = item => [...item.parentElement.children].filter(entry => entry.getAttribute?.('role') === 'treeitem');
    const focus = item => {
      if (!(item instanceof HTMLElement)) return;
      activeValue = path(item);
      all().forEach(entry => { entry.tabIndex = entry === item ? 0 : -1; });
      item.focus();
    };
    const selectedMessage = joined => {
      if (data.catalog.selected && i18n) {
        try { return i18n.tr('citry-ui-cascader-selected', {path:joined}); }
        catch (error) { console.error('[citry-ui] CCascader translation failed.', error, root); }
      }
      return data.labels.selected.replaceAll('{path}', joined);
    };
    let translatedPlaceholder = data.labels.placeholder;
    const placeholderBinding = data.catalog.placeholder && i18n ? i18n.bind({
      message: 'citry-ui-cascader-placeholder',
      onChange: text => {
        translatedPlaceholder = text;
        if (current.length === 0) valueText.textContent = text;
      },
    }) : null;
    const syncInputs = () => {
      inputs.replaceChildren();
      if (!data.name) return;
      for (const segment of current) {
        const input = document.createElement('input');
        input.type = 'hidden'; input.name = data.name; input.value = segment; input.disabled = disabled;
        if (data.form) input.setAttribute('form', data.form);
        inputs.append(input);
      }
    };
    const choosePopupLayout = () => {
      const inset = 8;
      const viewportWidth = document.documentElement.clientWidth;
      const columns = [...popup.querySelectorAll(':scope > [data-citry-cascader-column]:not([hidden])')];
      const preferredColumns = columns.slice(0, 3);
      const popupStyle = getComputedStyle(popup);
      const borderWidth = (Number.parseFloat(popupStyle.borderLeftWidth) || 0)
        + (Number.parseFloat(popupStyle.borderRightWidth) || 0);
      const preferredWidth = preferredColumns.reduce(
        (total, column) => total + (Number.parseFloat(getComputedStyle(column).flexBasis) || 0),
        borderWidth,
      );
      popup.toggleAttribute('data-citry-cascader-stacked', preferredWidth > viewportWidth - inset * 2);
    };
    const placePopup = () => {
      if (!currentOpen) return;
      choosePopupLayout();
      popup.style.left = '';
      popup.style.right = '';
      const inset = 8;
      const viewportWidth = document.documentElement.clientWidth;
      const box = popup.getBoundingClientRect();
      let shift = 0;
      if (box.right > viewportWidth - inset) shift -= box.right - (viewportWidth - inset);
      if (box.left + shift < inset) shift += inset - (box.left + shift);
      if (shift) {
        if (getComputedStyle(root).direction === 'rtl') popup.style.right = `${-shift}px`;
        else popup.style.left = `${shift}px`;
      }
    };
    const onOutside = event => { if (!root.contains(event.target)) requestOpen(false, 'outside', event); };
    const sync = () => {
      const selected = itemFor(current);
      const selectedLabels = selected ? labels(selected) : [];
      const joined = selectedLabels.join(data.separator);
      valueText.textContent = joined || translatedPlaceholder;
      trigger.disabled = disabled;
      trigger.setAttribute('aria-expanded', String(currentOpen));
      root.toggleAttribute('data-open', currentOpen);
      root.toggleAttribute('data-disabled', disabled);
      for (const item of all()) {
        const itemPath = path(item);
        const childGroup = group(item);
        const active = Boolean(childGroup && same(activePath.slice(0,itemPath.length), itemPath));
        const chosen = same(current, itemPath);
        item.setAttribute('aria-selected', String(chosen));
        item.toggleAttribute('data-selected', chosen);
        item.toggleAttribute('data-active', active);
        if (childGroup) {
          childGroup.hidden = !active;
          item.setAttribute('aria-expanded', String(active));
        }
      }
      if (currentOpen) choosePopupLayout();
      popup.hidden = !currentOpen;
      const candidates = visible();
      let active = itemFor(activeValue);
      if (!active || !candidates.includes(active)) active = selected && candidates.includes(selected) ? selected : candidates[0] ?? null;
      all().forEach(item => { item.tabIndex = item === active && !disabled ? 0 : -1; });
      activeValue = active ? path(active) : null;
      syncInputs();
      if (currentOpen) queueMicrotask(placePopup);
      if (currentOpen && !outsideListening) { document.addEventListener('pointerdown', onOutside, true); outsideListening = true; }
      else if (!currentOpen && outsideListening) { document.removeEventListener('pointerdown', onOutside, true); outsideListening = false; }
      if (currentOpen && !resizeListening) { window.addEventListener('resize', placePopup); resizeListening = true; }
      else if (!currentOpen && resizeListening) { window.removeEventListener('resize', placePopup); resizeListening = false; }
    };
    function requestOpen(next, reason, event) {
      if (disabled || next === currentOpen) return;
      try { openCallback?.(next, {open:next, reason, sourceEvent:event}); }
      catch (error) { console.error('[citry-ui] CCascader onOpenChange callback failed.', error, root); }
      if (!controlledOpen) { currentOpen = next; sync(); }
      if (!next && (reason === 'escape' || reason === 'selection')) trigger.focus();
    }
    const requestValue = (item, source, event) => {
      if (disabled || item.getAttribute('aria-disabled') === 'true') return;
      const next = path(item);
      if (group(item) && !data.change_on_select) return;
      const previous = [...current];
      try { valueCallback?.([...next], {value:[...next],labels:labels(item),previousValue:previous,controlled:controlledValue,source,option:item,sourceEvent:event}); }
      catch (error) { console.error('[citry-ui] CCascader onValueChange callback failed.', error, root); }
      if (!controlledValue) { accepted = [...next]; current = [...next]; status.textContent = selectedMessage(labels(item).join(data.separator)); }
      sync();
    };
    const activate = (item, source, event) => {
      if (disabled || item.getAttribute('aria-disabled') === 'true') return;
      if (group(item)) {
        const opening = item.getAttribute('aria-expanded') !== 'true';
        const itemPath = path(item);
        activePath = opening ? itemPath : itemPath.slice(0, -1);
        if (data.change_on_select) requestValue(item, source, event);
        sync();
        if (source === 'keyboard' && opening) focus([...group(item).children].find(child => child.getAttribute?.('role') === 'treeitem'));
      } else {
        requestValue(item, source, event);
        requestOpen(false, 'selection', event);
      }
    };
    const itemFrom = event => event.composedPath().find(node => node instanceof HTMLElement && node.getAttribute?.('role') === 'treeitem' && popup.contains(node));
    const onTrigger = event => {
      const opening = !currentOpen;
      requestOpen(opening, 'trigger', event);
      if (opening && currentOpen) queueMicrotask(() => focus(itemFor(current) ?? visible()[0]));
      else if (!opening) trigger.focus();
    };
    const onTriggerKeyDown = event => {
      if (!currentOpen) return;
      if (event.key === 'Escape') { event.preventDefault(); requestOpen(false, 'escape', event); }
      else if (event.key === 'Tab') requestOpen(false, 'tab', event);
    };
    const onClick = event => { const item = itemFrom(event); if (item) { focus(item); activate(item, 'pointer', event); } };
    const onKeyDown = event => {
      const item = itemFrom(event);
      if (!item) return;
      const siblings = column(item); const index = siblings.indexOf(item); let destination = null;
      if (event.key === 'ArrowDown') destination = siblings[index + 1] ?? siblings[0];
      else if (event.key === 'ArrowUp') destination = siblings[index - 1] ?? siblings.at(-1);
      else if (event.key === 'Home') destination = siblings[0];
      else if (event.key === 'End') destination = siblings.at(-1);
      else if (event.key === 'ArrowRight') {
        if (group(item)) { activePath = path(item); sync(); destination = [...group(item).children][0]; }
      } else if (event.key === 'ArrowLeft') {
        const parentItem = parent(item);
        if (group(item) && item.getAttribute('aria-expanded') === 'true') {
          activePath = path(item).slice(0, -1);
          sync();
          destination = item;
        } else if (parentItem) {
          activePath = path(parentItem).slice(0, -1);
          sync();
          destination = parentItem;
        }
      }
      else if (event.key === 'Enter' || event.key === ' ') activate(item, 'keyboard', event);
      else if (event.key === 'Escape') requestOpen(false, 'escape', event);
      else if (event.key === 'Tab') { requestOpen(false, 'tab', event); return; }
      else if (!event.altKey && !event.ctrlKey && !event.metaKey && event.key.length === 1) {
        typeBuffer += event.key.toLocaleLowerCase();
        if (typeTimer) clearTimeout(typeTimer);
        typeTimer = setTimeout(() => {typeBuffer='';typeTimer=null;}, 500);
        destination = [...siblings.slice(index + 1),...siblings.slice(0,index + 1)].find(entry => entry.textContent.trim().toLocaleLowerCase().startsWith(typeBuffer));
      } else return;
      event.preventDefault(); if (destination) focus(destination);
    };
    const onReset = event => {
      if (event.target !== root.closest('form') && event.target !== document.getElementById(data.form)) return;
      queueMicrotask(() => {
        if (controlledValue) valueCallback?.([...data.value], {value:[...data.value],labels:labels(itemFor(data.value)),previousValue:[...current],controlled:true,source:'reset',option:itemFor(data.value),sourceEvent:event});
        else {accepted=[...data.value];current=[...data.value];activePath=[...data.value];sync();}
      });
    };
    const resetForms = new Set([root.closest('form'), data.form ? document.getElementById(data.form) : null].filter(form => form instanceof HTMLFormElement));
    trigger.addEventListener('click', onTrigger);
    trigger.addEventListener('keydown', onTriggerKeyDown);
    popup.addEventListener('click', onClick);
    popup.addEventListener('keydown', onKeyDown);
    resetForms.forEach(form => form.addEventListener('reset', onReset, true));
    root.setAttribute('data-citry-cascader-initialized', '');
    effect(() => {
      const previousOpen = currentOpen;
      const previousValue = [...current];
      const nextDisabled = props.disabled;
      if (nextDisabled !== undefined && typeof nextDisabled !== 'boolean') report('disabled', nextDisabled);
      else {invalid.delete('disabled');disabled=typeof nextDisabled === 'boolean'?nextDisabled:data.disabled;}
      const nextValue = props.value;
      controlledValue = nextValue !== undefined && nextValue !== null;
      if (controlledValue) {
        const item = validPath(nextValue);
        if (item) {invalid.delete('value');current=[...nextValue];activePath=[...nextValue];}
        else report('value',nextValue);
      } else {invalid.delete('value');current=[...accepted];activePath=[...accepted];}
      const nextOpen = props.open;
      controlledOpen = nextOpen !== undefined && nextOpen !== null;
      if (controlledOpen && typeof nextOpen !== 'boolean') report('open',nextOpen);
      else {invalid.delete('open');currentOpen=controlledOpen?nextOpen:currentOpen;}
      valueCallback = props.onValueChange == null ? null : typeof props.onValueChange === 'function' ? props.onValueChange : (report('onValueChange',props.onValueChange),null);
      openCallback = props.onOpenChange == null ? null : typeof props.onOpenChange === 'function' ? props.onOpenChange : (report('onOpenChange',props.onOpenChange),null);
      sync();
      if (reactiveReady && !previousOpen && currentOpen) queueMicrotask(() => focus(itemFor(current) ?? visible()[0]));
      if (reactiveReady && controlledValue && !same(previousValue, current)) {
        const selected = itemFor(current);
        status.textContent = selected ? selectedMessage(labels(selected).join(data.separator)) : '';
      }
      reactiveReady = true;
    });
    return () => {
      if (typeTimer) clearTimeout(typeTimer);
      if (outsideListening) document.removeEventListener('pointerdown', onOutside, true);
      if (resizeListening) window.removeEventListener('resize', placePopup);
      resetForms.forEach(form => form.removeEventListener('reset', onReset, true));
      placeholderBinding?.dispose();
      trigger.removeEventListener('click', onTrigger);
      trigger.removeEventListener('keydown', onTriggerKeyDown);
      popup.removeEventListener('click', onClick);
      popup.removeEventListener('keydown', onKeyDown);
      root.removeAttribute('data-citry-cascader-initialized');
    };
  },
});
