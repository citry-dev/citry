$component({
  props: {value: {}, required: {}, disabled: {}, onValueChange: {}},
  init: ({els, data, props, effect, i18n}) => {
    const root = els[0];
    const native = root?.querySelector(
      ':scope > [data-citry-transfer-native-fallback] > [data-citry-transfer-list-native]',
    );
    const control = root?.querySelector(':scope > [data-citry-ui-part="control"]');
    const available = control?.querySelector('[data-citry-transfer-pane="available"]');
    const chosen = control?.querySelector('[data-citry-transfer-pane="chosen"]');
    const availableList = available?.querySelector('[data-citry-ui-part="listbox"]');
    const chosenList = chosen?.querySelector('[data-citry-ui-part="listbox"]');
    const availableCount = available?.querySelector('[data-citry-ui-part="count"]');
    const chosenCount = chosen?.querySelector('[data-citry-ui-part="count"]');
    const availableEmpty = available?.querySelector('[data-citry-ui-part="empty"]');
    const chosenEmpty = chosen?.querySelector('[data-citry-ui-part="empty"]');
    const status = root?.querySelector(':scope > [data-citry-ui-part="status"]');
    const transport = root?.querySelector(':scope > [data-citry-transfer-list-transport]');
    if (!(root instanceof HTMLElement) || !(native instanceof HTMLSelectElement)
        || !(control instanceof HTMLElement) || !(availableList instanceof HTMLElement)
        || !(chosenList instanceof HTMLElement) || !(availableCount instanceof HTMLElement)
        || !(chosenCount instanceof HTMLElement) || !(availableEmpty instanceof HTMLElement)
        || !(chosenEmpty instanceof HTMLElement) || !(status instanceof HTMLElement)
        || !(transport instanceof HTMLElement)) {
      throw new Error('[citry-ui] CTransferList settled anatomy is invalid.');
    }
    const options = [...control.querySelectorAll('[data-citry-transfer-option]')];
    if (options.some(option => option.querySelector(
      'a[href],button,input,select,textarea,[contenteditable="true"],[tabindex]:not([tabindex="-1"])',
    ))) {
      throw new Error('[citry-ui] CTransferListItem content cannot contain interactive descendants.');
    }
    const nativeOptions = [...native.options];
    const byValue = new Map(options.map(option => [option.dataset.value, option]));
    const nativeByValue = new Map(nativeOptions.map(option => [option.value, option]));
    const authored = options.map(option => option.dataset.value);
    const disabledValues = new Set(options.filter(option => option.hasAttribute('data-disabled'))
      .map(option => option.dataset.value));
    const initialValue = [...data.value];
    const selections = {available: new Set(), chosen: new Set()};
    const active = {available: null, chosen: null};
    const anchors = {available: null, chosen: null};
    const invalid = new Set();
    const bindingDisposers = [];
    let current = [...initialValue];
    let controlled = false;
    let callback = null;
    let required = data.required;
    let disabled = data.disabled;
    let pending = null;
    let alive = true;
    let typeahead = {pane: null, value: '', timer: 0};
    const report = (name, value) => {
      if (invalid.has(name)) return;
      invalid.add(name);
      console.error(`[citry-ui] CTransferList ${name} received invalid client value.`, value, root);
    };
    const validValue = value => Array.isArray(value)
      && value.every(item => typeof item === 'string' && byValue.has(item))
      && new Set(value).size === value.length;
    const same = (left, right) => left.length === right.length
      && left.every((item, index) => item === right[index]);
    const format = (pattern, values) => Object.entries(values).reduce(
      (result, [name, value]) => result.replaceAll(`{${name}}`, String(value)), pattern,
    );
    const translate = (message, values, fallback) => {
      if (i18n && data.catalog[message]) {
        try {
          if (message === 'count') return i18n.tr('citry-ui-transfer-list-count', values);
        }
        catch (error) { console.error('[citry-ui] CTransferList translation failed.', error, root); }
      }
      return format(fallback, values);
    };
    const listFor = pane => pane === 'available' ? availableList : chosenList;
    const valuesFor = pane => [...listFor(pane).querySelectorAll(':scope > [data-citry-transfer-option]')]
      .map(option => option.dataset.value);
    const enabledValues = pane => valuesFor(pane).filter(value => !disabledValues.has(value));
    const ensureActive = pane => {
      const values = valuesFor(pane);
      if (!values.includes(active[pane])) {
        active[pane] = values.find(value => selections[pane].has(value)) ?? values[0] ?? null;
      }
      const node = active[pane] ? byValue.get(active[pane]) : null;
      if (node) listFor(pane).setAttribute('aria-activedescendant', node.id);
      else listFor(pane).removeAttribute('aria-activedescendant');
    };
    const selectedEnabled = pane => valuesFor(pane)
      .filter(value => selections[pane].has(value) && !disabledValues.has(value));
    const updateButtons = () => {
      const availableSelected = selectedEnabled('available');
      const chosenSelected = selectedEnabled('chosen');
      const chosenValues = valuesFor('chosen');
      root.querySelectorAll('[data-citry-transfer-action]').forEach(button => {
        const action = button.dataset.citryTransferAction;
        let enabled = false;
        if (action === 'add') enabled = availableSelected.length > 0;
        else if (action === 'add-all') enabled = enabledValues('available').length > 0;
        else if (action === 'remove') enabled = chosenSelected.length > 0;
        else if (action === 'remove-all') enabled = enabledValues('chosen').length > 0;
        else if (action === 'move-top' || action === 'move-up') {
          enabled = chosenValues.some((value, index) => selections.chosen.has(value)
            && chosenValues.slice(0, index).some(previous => !selections.chosen.has(previous)));
        } else if (action === 'move-bottom' || action === 'move-down') {
          enabled = chosenValues.some((value, index) => selections.chosen.has(value)
            && chosenValues.slice(index + 1).some(next => !selections.chosen.has(next)));
        }
        button.disabled = disabled || !enabled;
      });
    };
    const syncSelection = () => {
      for (const pane of ['available', 'chosen']) {
        const values = new Set(valuesFor(pane));
        selections[pane] = new Set([...selections[pane]].filter(value => values.has(value)));
        ensureActive(pane);
        for (const value of values) {
          const option = byValue.get(value);
          const selected = selections[pane].has(value);
          option.setAttribute('aria-selected', String(selected));
          option.toggleAttribute('data-selected', selected);
        }
      }
      updateButtons();
    };
    const countText = (selected, total) => translate(
      'count', {selected, total}, data.labels.count,
    );
    const updateCounts = () => {
      availableCount.textContent = countText(selections.available.size, valuesFor('available').length);
      chosenCount.textContent = countText(selections.chosen.size, valuesFor('chosen').length);
    };
    const syncTransport = () => {
      const inputs = data.name ? current.map(value => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = data.name;
        input.value = value;
        input.disabled = disabled;
        if (data.form) input.setAttribute('form', data.form);
        return input;
      }) : [];
      transport.replaceChildren(...inputs);
    };
    const syncValue = next => {
      current = [...next];
      const chosenSet = new Set(current);
      for (const value of authored) if (!chosenSet.has(value)) availableList.append(byValue.get(value));
      for (const value of current) chosenList.append(byValue.get(value));
      for (const value of authored) if (!chosenSet.has(value)) native.append(nativeByValue.get(value));
      for (const value of current) native.append(nativeByValue.get(value));
      for (const option of nativeOptions) option.selected = chosenSet.has(option.value);
      syncTransport();
      if (!required || current.length) {
        root.removeAttribute('data-invalid');
        root.removeAttribute('aria-invalid');
      }
      availableEmpty.hidden = availableList.childElementCount > 0;
      chosenEmpty.hidden = chosenList.childElementCount > 0;
      root.toggleAttribute('data-available-empty', !availableEmpty.hidden);
      root.toggleAttribute('data-chosen-empty', !chosenEmpty.hidden);
      syncSelection();
      updateCounts();
    };
    const announce = (kind, count) => {
      if (i18n && data.catalog[kind]) {
        try {
          if (kind === 'added') status.textContent = count === 1
            ? i18n.tr('citry-ui-transfer-list-added-one')
            : i18n.tr('citry-ui-transfer-list-added', {count: String(count)});
          else if (kind === 'removed') status.textContent = count === 1
            ? i18n.tr('citry-ui-transfer-list-removed-one')
            : i18n.tr('citry-ui-transfer-list-removed', {count: String(count)});
          else status.textContent = count === 1
            ? i18n.tr('citry-ui-transfer-list-reordered-one')
            : i18n.tr('citry-ui-transfer-list-reordered', {count: String(count)});
          return;
        } catch (error) {
          console.error('[citry-ui] CTransferList translation failed.', error, root);
        }
      }
      status.textContent = format(data.labels[kind], {count});
    };
    const focusMoved = (pane, moved) => {
      selections.available.clear();
      selections.chosen.clear();
      for (const value of moved) selections[pane].add(value);
      active[pane] = moved[0] ?? active[pane];
      anchors[pane] = moved[0] ?? null;
      syncSelection();
      updateCounts();
      listFor(pane).focus({preventScroll: true});
      byValue.get(active[pane])?.scrollIntoView({block: 'nearest'});
    };
    const notify = (next, moved, source, sourceEvent, destination = null) => {
      if (same(next, current)) return;
      const previous = [...current];
      if (controlled) pending = {next: [...next], moved: [...moved], source, destination};
      else {
        syncValue(next);
        if (destination) focusMoved(destination, moved);
        native.dispatchEvent(new Event('input', {bubbles: true}));
        native.dispatchEvent(new Event('change', {bubbles: true}));
        announce(
          source.startsWith('add') ? 'added' : source.startsWith('remove') ? 'removed' : 'reordered',
          moved.length,
        );
      }
      if (callback) {
        try {
          callback([...next], {
            value: [...next], previousValue: previous, moved: [...moved], source,
            controlled, sourceEvent,
          });
        } catch (error) {
          console.error('[citry-ui] CTransferList onValueChange callback failed.', error, root);
        }
      }
    };
    const transfer = (action, event) => {
      if (disabled) return;
      if (action === 'add' || action === 'add-all') {
        const moved = action === 'add' ? selectedEnabled('available') : enabledValues('available');
        notify([...current, ...moved], moved, action, event, 'chosen');
        return;
      }
      if (action === 'remove' || action === 'remove-all') {
        const moved = action === 'remove' ? selectedEnabled('chosen') : enabledValues('chosen');
        const removed = new Set(moved);
        notify(current.filter(value => !removed.has(value)), moved, action, event, 'available');
        return;
      }
      const moved = selectedEnabled('chosen');
      if (!moved.length) return;
      const selected = new Set(moved);
      let next = [...current];
      if (action === 'move-top') {
        next = [...next.filter(value => selected.has(value)), ...next.filter(value => !selected.has(value))];
      } else if (action === 'move-bottom') {
        next = [...next.filter(value => !selected.has(value)), ...next.filter(value => selected.has(value))];
      }
      else if (action === 'move-up') {
        for (let index = 1; index < next.length; index += 1) {
          if (selected.has(next[index]) && !selected.has(next[index - 1])) {
            [next[index - 1], next[index]] = [next[index], next[index - 1]];
          }
        }
      } else if (action === 'move-down') {
        for (let index = next.length - 2; index >= 0; index -= 1) {
          if (selected.has(next[index]) && !selected.has(next[index + 1])) {
            [next[index], next[index + 1]] = [next[index + 1], next[index]];
          }
        }
      }
      notify(next, moved, action, event, 'chosen');
    };
    const selectRange = (pane, destination) => {
      const values = valuesFor(pane);
      const anchor = anchors[pane] && values.includes(anchors[pane]) ? anchors[pane] : active[pane];
      if (!anchor || !destination) return;
      const start = values.indexOf(anchor);
      const end = values.indexOf(destination);
      selections[pane].clear();
      for (const value of values.slice(Math.min(start, end), Math.max(start, end) + 1)) {
        if (!disabledValues.has(value)) selections[pane].add(value);
      }
    };
    const moveActive = (pane, key, extend) => {
      const values = valuesFor(pane);
      if (!values.length) return;
      let index = Math.max(0, values.indexOf(active[pane]));
      if (key === 'Home') index = 0;
      else if (key === 'End') index = values.length - 1;
      else index = Math.max(0, Math.min(values.length - 1, index + (key === 'ArrowDown' ? 1 : -1)));
      active[pane] = values[index];
      if (extend) selectRange(pane, active[pane]);
      else anchors[pane] = active[pane];
      syncSelection();
      updateCounts();
      byValue.get(active[pane])?.scrollIntoView({block: 'nearest'});
    };
    const onListKeydown = (pane, event) => {
      if (disabled) return;
      if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
        event.preventDefault();
        moveActive(pane, event.key, event.shiftKey);
        return;
      }
      if ((event.key === ' ' || event.key === 'Enter') && active[pane]) {
        event.preventDefault();
        if (event.shiftKey) selectRange(pane, active[pane]);
        else if (!disabledValues.has(active[pane])) {
          if (selections[pane].has(active[pane])) selections[pane].delete(active[pane]);
          else selections[pane].add(active[pane]);
          anchors[pane] = active[pane];
        }
        syncSelection();
        updateCounts();
        return;
      }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'a') {
        event.preventDefault();
        selections[pane] = new Set(enabledValues(pane));
        syncSelection();
        updateCounts();
        return;
      }
      if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
        clearTimeout(typeahead.timer);
        typeahead.value = typeahead.pane === pane ? `${typeahead.value}${event.key}` : event.key;
        typeahead.pane = pane;
        const values = valuesFor(pane);
        const start = Math.max(0, values.indexOf(active[pane]) + 1);
        const ordered = [...values.slice(start), ...values.slice(0, start)];
        const match = ordered.find(value => byValue.get(value).dataset.label
          .toLocaleLowerCase().startsWith(typeahead.value.toLocaleLowerCase()));
        if (match) {
          active[pane] = match;
          anchors[pane] = match;
          syncSelection();
          byValue.get(match)?.scrollIntoView({block: 'nearest'});
        }
        typeahead.timer = setTimeout(() => { typeahead.value = ''; typeahead.pane = null; }, 700);
      }
    };
    const onControlClick = event => {
      const button = event.target.closest('[data-citry-transfer-action]');
      if (button && root.contains(button)) transfer(button.dataset.citryTransferAction, event);
    };
    const onOptionClick = (pane, event) => {
      const option = event.target.closest('[data-citry-transfer-option]');
      if (!option || !listFor(pane).contains(option)) return;
      active[pane] = option.dataset.value;
      if (event.shiftKey) selectRange(pane, active[pane]);
      else if (!disabledValues.has(active[pane]) && !disabled) {
        if (selections[pane].has(active[pane])) selections[pane].delete(active[pane]);
        else selections[pane].add(active[pane]);
        anchors[pane] = active[pane];
      }
      syncSelection();
      updateCounts();
      listFor(pane).focus({preventScroll: true});
    };
    const onAvailableKeydown = event => onListKeydown('available', event);
    const onChosenKeydown = event => onListKeydown('chosen', event);
    const onAvailableClick = event => onOptionClick('available', event);
    const onChosenClick = event => onOptionClick('chosen', event);
    control.addEventListener('click', onControlClick);
    availableList.addEventListener('keydown', onAvailableKeydown);
    chosenList.addEventListener('keydown', onChosenKeydown);
    availableList.addEventListener('click', onAvailableClick);
    chosenList.addEventListener('click', onChosenClick);
    const onAvailableFocus = () => { ensureActive('available'); syncSelection(); };
    const onChosenFocus = () => { ensureActive('chosen'); syncSelection(); };
    availableList.addEventListener('focus', onAvailableFocus);
    chosenList.addEventListener('focus', onChosenFocus);
    const form = native.form;
    const onReset = event => setTimeout(() => {
      if (!alive || event.defaultPrevented) return;
      const next = nativeOptions
        .filter(option => option.defaultSelected
          && !option.hasAttribute('data-citry-transfer-disabled-value-proxy'))
        .map(option => option.value);
      if (controlled) notify(next, next, 'reset', event, next.length ? 'chosen' : 'available');
      else {
        const previous = [...current];
        syncValue(next);
        if (callback) {
          try {
            callback([...next], {
              value: [...next], previousValue: previous, moved: [], source: 'reset', controlled: false,
              sourceEvent: event,
            });
          } catch (error) {
            console.error('[citry-ui] CTransferList onValueChange callback failed.', error, root);
          }
        }
      }
    }, 0);
    form?.addEventListener('reset', onReset);
    const fieldset = native.closest('fieldset');
    const fieldsetObserver = fieldset ? new MutationObserver(() => {
      disabled = data.disabled || fieldset.disabled;
      native.disabled = disabled;
      root.toggleAttribute('data-disabled', disabled);
      root.setAttribute('aria-disabled', String(disabled));
      syncTransport();
      updateButtons();
    }) : null;
    fieldsetObserver?.observe(fieldset, {attributes: true, attributeFilter: ['disabled']});
    const onInvalid = event => {
      event.preventDefault();
      root.setAttribute('data-invalid', '');
      root.setAttribute('aria-invalid', 'true');
      status.textContent = data.catalog.required && i18n
        ? i18n.tr('citry-ui-transfer-list-required') : data.labels.required;
      chosenList.focus();
    };
    native.addEventListener('invalid', onInvalid);
    if (i18n && data.catalog.count) {
      for (const [pane, element] of [['available', availableCount], ['chosen', chosenCount]]) {
        const binding = i18n.bind({
          message: 'citry-ui-transfer-list-count',
          values: () => ({
            selected: String(selections[pane].size), total: String(valuesFor(pane).length),
          }),
          onChange: text => { element.textContent = text; },
        });
        bindingDisposers.push(binding);
      }
    }
    syncValue(current);
    native.removeAttribute('name');
    native.tabIndex = -1;
    control.hidden = false;
    root.setAttribute('data-enhanced', '');
    root.setAttribute('data-citry-transfer-list-initialized', '');
    effect(() => {
      const nextCallback = props.onValueChange;
      if (nextCallback === undefined || nextCallback === null) {
        callback = null;
        invalid.delete('onValueChange');
      }
      else if (typeof nextCallback === 'function') { callback = nextCallback; invalid.delete('onValueChange'); }
      else report('onValueChange', nextCallback);
      for (const name of ['required', 'disabled']) {
        const value = props[name];
        if (value !== undefined && typeof value !== 'boolean') report(name, value);
        else invalid.delete(name);
      }
      required = typeof props.required === 'boolean' ? props.required : data.required;
      disabled = (typeof props.disabled === 'boolean' ? props.disabled : data.disabled)
        || Boolean(fieldset?.disabled);
      native.required = required;
      native.disabled = disabled;
      root.toggleAttribute('data-required', required);
      root.toggleAttribute('data-disabled', disabled);
      root.setAttribute('aria-disabled', String(disabled));
      syncTransport();
      const next = props.value;
      if (next === undefined || next === null) controlled = false;
      else if (validValue(next)) {
        invalid.delete('value');
        controlled = true;
        if (!same(next, current)) {
          syncValue(next);
          if (pending && same(next, pending.next)) {
            if (pending.destination) focusMoved(pending.destination, pending.moved);
            announce(pending.source.startsWith('add') ? 'added'
              : pending.source.startsWith('remove') ? 'removed' : 'reordered', pending.moved.length);
          }
          pending = null;
        }
      } else report('value', next);
      updateButtons();
    });
    return () => {
      alive = false;
      clearTimeout(typeahead.timer);
      bindingDisposers.forEach(binding => binding.dispose());
      fieldsetObserver?.disconnect();
      form?.removeEventListener('reset', onReset);
      native.removeEventListener('invalid', onInvalid);
      control.removeEventListener('click', onControlClick);
      availableList.removeEventListener('keydown', onAvailableKeydown);
      chosenList.removeEventListener('keydown', onChosenKeydown);
      availableList.removeEventListener('click', onAvailableClick);
      chosenList.removeEventListener('click', onChosenClick);
      availableList.removeEventListener('focus', onAvailableFocus);
      chosenList.removeEventListener('focus', onChosenFocus);
      transport.replaceChildren();
      if (data.name) native.name = data.name;
      native.tabIndex = 0;
      control.hidden = true;
      root.removeAttribute('data-enhanced');
      root.removeAttribute('data-citry-transfer-list-initialized');
    };
  },
});
