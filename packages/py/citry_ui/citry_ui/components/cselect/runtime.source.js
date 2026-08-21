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

const selectHandoffKey = Symbol.for("citry-ui:select-handoff");

$component({
  props: {
    value: {}, open: {}, required: {}, disabled: {}, readonly: {}, invalid: {},
    loop: {}, placement: {}, matchWidth: {}, variant: {}, size: {},
    onValueChange: {}, onOpenChange: {},
  },
  init: ({els, data, props, effect, inject}) => {
    const root = els[0];
    const trigger = root.querySelector(':scope > [data-citry-ui-part="control"]');
    const nativeSelect = root.querySelector(':scope > [data-cui-select-native]');
    const readonlyInput = root.querySelector(':scope > [data-cui-select-readonly-value]');
    const popup = root.querySelector(':scope > [data-citry-ui-part="popup"]');
    const listbox = popup?.querySelector(':scope > [data-citry-ui-part="listbox"]');
    if (
      !(trigger instanceof HTMLButtonElement)
      || !(nativeSelect instanceof HTMLSelectElement)
      || !(readonlyInput instanceof HTMLInputElement)
      || !(popup instanceof HTMLElement)
      || !(listbox instanceof HTMLElement)
    ) {
      throw new Error("[citry-ui] CSelect settled anatomy is invalid.");
    }
    const field = inject(Symbol.for("citry-ui:field"), null);
    const form = inject(Symbol.for("citry-ui:form"), null);
    const nativeForm = nativeSelect.form;
    const coordinator = anchoredLayerRuntime.coordinatorFor(popup);
    const invalidEpisodes = new Set();
    const options = () => [...listbox.querySelectorAll('[role="option"]')]
      .filter((option) => option.closest('[role="listbox"]') === listbox);
    const optionFor = (value) => options().find((option) => option.dataset.value === value) ?? null;
    const enabledOptions = () => options().filter((option) => !option.hasAttribute('data-disabled'));
    const canonicalString = (value) => (
      typeof value === 'string' && value.length > 0 && !value.includes('\0')
        ? value.replace(/\r\n?/g, '\n')
        : null
    );
    const report = (name, value, suffix = '') => {
      if (invalidEpisodes.has(name)) return;
      invalidEpisodes.add(name);
      console.error(`[citry-ui] CSelect ${name} received invalid client value${suffix}`, value);
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
        invalidEpisodes.delete(name); return supplied;
      }
      report(name, supplied, '; using the server fallback');
      return fallback;
    };
    const prior = root[selectHandoffKey];
    delete root[selectHandoffKey];
    const serverFingerprint = JSON.stringify(data.value);
    let committedValue = prior?.serverFingerprint === serverFingerprint
      ? prior.committedValue
      : data.value;
    let currentValue = committedValue;
    let internalOpen = prior?.serverFingerprint === serverFingerprint
      ? Boolean(prior.internalOpen)
      : data.open;
    let logicalOpen = false;
    let highlightedValue = prior?.highlightedValue ?? null;
    let controlledValue = false;
    let controlledOpen = false;
    let clientValue;
    let clientOpen;
    let onValueChange = null;
    let onOpenChange = null;
    let nativeInvalid = false;
    let active = true;
    let generation = 0;
    let typeBuffer = '';
    let typeTimer = null;
    let tabGesture = false;
    let pendingOpenDirection = 1;
    let selectionTransaction = false;
    let pendingForcedNotice = null;
    let pendingStructure = prior?.pendingStructure ?? null;
    let configuration = {
      required:data.required,
      disabled:data.disabled,
      readonly:data.readonly,
      invalid:data.invalid,
      loop:data.loop,
      placement:data.placement,
      matchWidth:data.matchWidth,
      variant:data.variant,
      size:data.size,
    };

    const anchorName = data.anchorName;
    if (!anchorName.startsWith('--')) {
      throw new Error('[citry-ui] CSelect could not resolve its CSS anchor name.');
    }
    trigger.style.setProperty('anchor-name', anchorName);
    popup.style.setProperty('position-anchor', anchorName);

    const idrefs = (...values) => {
      const output = [];
      values.forEach((value) => {
        if (typeof value !== 'string') return;
        value.split(/\s+/).filter(Boolean).forEach((token) => {
          if (!output.includes(token)) output.push(token);
        });
      });
      return output.join(' ') || null;
    };
    const effectiveDisabled = () => configuration.disabled || trigger.matches(':disabled');
    const eligible = () => !effectiveDisabled() && !configuration.readonly;
    const selectedOption = () => optionFor(currentValue);
    const labelFor = (value) => data.options.find((option) => option.value === value)?.label ?? null;
    const actualOpen = () => active && logicalOpen;
    const layer = {
      trigger,
      surface:popup,
      isOpen:actualOpen,
      isEligible:eligible,
      requestDismiss:(reason, source) => {
        if (tabGesture && reason === 'focus-outside') return;
        requestOpen(false, reason, source);
      },
      forceClose:(reason, source) => forceClose(reason === 'modal' ? 'ancestor' : reason, source),
    };
    const notifyOpen = (next, reason, source, forced = false) => {
      onOpenChange?.(next, {open:next, reason, controlled:controlledOpen, forced, source});
    };
    const syncRelationships = (invalid) => {
      const describedBy = idrefs(
        field?.hasDescription ? field.descriptionId : null,
        invalid && field?.hasError ? field.errorId : null,
        data.externalDescribedBy,
      );
      const errorMessage = invalid
        ? idrefs(field?.hasError ? field.errorId : null, data.externalErrorMessage)
        : null;
      if (describedBy) trigger.setAttribute('aria-describedby', describedBy);
      else trigger.removeAttribute('aria-describedby');
      if (errorMessage) trigger.setAttribute('aria-errormessage', errorMessage);
      else trigger.removeAttribute('aria-errormessage');
    };
    const syncValue = () => {
      const selected = selectedOption();
      const empty = selected === null;
      root.toggleAttribute('data-empty', empty);
      root.querySelector('[data-citry-ui-part="value"]').textContent = selected?.querySelector(
        '[data-citry-ui-part="option-label"]',
      )?.textContent ?? data.placeholder;
      options().forEach((option) => {
        const chosen = option === selected;
        option.setAttribute('aria-selected', chosen ? 'true' : 'false');
        option.toggleAttribute('data-selected', chosen);
        option.toggleAttribute('data-highlighted', logicalOpen && option.dataset.value === highlightedValue);
      });
      nativeSelect.value = currentValue ?? '';
      readonlyInput.value = currentValue ?? '';
      const readonlySubmission = configuration.readonly && !effectiveDisabled() && Boolean(data.name);
      nativeSelect.name = readonlySubmission ? '' : (data.name ?? '');
      nativeSelect.disabled = effectiveDisabled() || configuration.readonly;
      nativeSelect.required = configuration.required && !configuration.readonly && !effectiveDisabled();
      readonlyInput.name = readonlySubmission ? data.name : '';
      readonlyInput.disabled = !readonlySubmission;
      if (currentValue !== null) nativeInvalid = false;
      const invalid = configuration.invalid || nativeInvalid;
      root.toggleAttribute('data-invalid', invalid);
      if (invalid) trigger.setAttribute('aria-invalid', 'true');
      else trigger.removeAttribute('aria-invalid');
      syncRelationships(invalid);
      field?.setNativeInvalid(nativeInvalid);
    };
    const syncPresentation = () => {
      const disabled = effectiveDisabled();
      root.toggleAttribute('data-open', logicalOpen);
      root.toggleAttribute('data-required', configuration.required);
      root.toggleAttribute('data-disabled', disabled);
      root.toggleAttribute('data-readonly', configuration.readonly);
      root.toggleAttribute('data-match-width', configuration.matchWidth);
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      popup.dataset.placement = configuration.placement;
      trigger.disabled = configuration.disabled;
      trigger.setAttribute('aria-expanded', logicalOpen ? 'true' : 'false');
      if (configuration.required) trigger.setAttribute('aria-required', 'true');
      else trigger.removeAttribute('aria-required');
      if (disabled) trigger.setAttribute('aria-disabled', 'true');
      else trigger.removeAttribute('aria-disabled');
      if (configuration.readonly) trigger.setAttribute('aria-readonly', 'true');
      else trigger.removeAttribute('aria-readonly');
      if (logicalOpen && highlightedValue !== null) {
        trigger.setAttribute('aria-activedescendant', optionFor(highlightedValue)?.id ?? '');
      } else trigger.removeAttribute('aria-activedescendant');
      syncValue();
    };
    const chooseHighlight = (direction = 1) => {
      const enabled = enabledOptions();
      const selected = selectedOption();
      if (selected && !selected.hasAttribute('data-disabled')) return selected.dataset.value;
      return (direction < 0 ? enabled.at(-1) : enabled[0])?.dataset.value ?? null;
    };
    const applyOpen = (next, {reason = null, source = null, focus = false} = {}) => {
      if (next === logicalOpen) {
        if (next && !coordinator.register(layer)) forceClose('ancestor', popup);
        return;
      }
      generation += 1;
      const currentGeneration = generation;
      if (next) {
        if (!eligible() || !coordinator.mayOpen(layer)) {
          internalOpen = false;
          logicalOpen = false;
          popup.hidden = true;
          popup.inert = true;
          syncPresentation();
          return;
        }
        highlightedValue = chooseHighlight(pendingOpenDirection);
        pendingOpenDirection = 1;
        popup.hidden = false;
        popup.inert = false;
        try {
          if (!popup.matches(':popover-open')) popup.showPopover();
        } catch (error) {
          console.error('[citry-ui] CSelect could not open its popup:', error, popup);
          popup.hidden = true;
          popup.inert = true;
          internalOpen = false;
          logicalOpen = false;
          syncPresentation();
          return;
        }
        logicalOpen = true;
        popup.setAttribute('data-open', '');
        if (!coordinator.register(layer)) {
          logicalOpen = false;
          popup.hidePopover();
          popup.hidden = true;
          popup.inert = true;
          popup.removeAttribute('data-open');
          syncPresentation();
          return;
        }
        syncPresentation();
        if (focus) trigger.focus({preventScroll:true});
        const rawDuration = getComputedStyle(popup)
          .getPropertyValue('--_cui-select-duration')
          .trim();
        const milliseconds = rawDuration.endsWith('ms')
          ? Math.max(0, Number.parseFloat(rawDuration) || 0)
          : rawDuration.endsWith('s')
            ? Math.max(0, (Number.parseFloat(rawDuration) || 0) * 1000)
            : Math.max(0, Number.parseFloat(rawDuration) || 0);
        if (milliseconds > 0) {
          popup.animate(
            [{opacity:0, transform:'translateY(-0.2rem) scale(0.98)'}, {opacity:1, transform:'none'}],
            {duration:milliseconds, easing:'ease-out'},
          ).finished.catch(() => {});
        }
        optionFor(highlightedValue)?.scrollIntoView({block:'nearest'});
        return;
      }
      logicalOpen = false;
      highlightedValue = null;
      popup.inert = true;
      popup.removeAttribute('data-open');
      coordinator.unregister(layer);
      if (popup.matches(':popover-open')) popup.hidePopover();
      popup.hidden = true;
      syncPresentation();
      if (
        reason !== 'outside'
        && reason !== 'focus-outside'
        && reason !== 'tab'
        && reason !== 'ancestor'
        && anchoredLayerRuntime.composedContains(popup, coordinator.deepActiveElement())
        && trigger.isConnected
        && !effectiveDisabled()
      ) trigger.focus({preventScroll:true});
      if (currentGeneration !== generation) return;
      void source;
    };
    const requestOpen = (next, reason, source, focus = false, direction = 1) => {
      if (next === logicalOpen) return;
      if (next) {
        pendingOpenDirection = direction;
        coordinator.clearSuppression(layer);
      }
      if (controlledOpen) {
        notifyOpen(next, reason, source);
        return;
      }
      internalOpen = next;
      applyOpen(next, {reason, source, focus});
      notifyOpen(next, reason, source);
    };
    const forceClose = (reason, source) => {
      if (!logicalOpen) { internalOpen = false; return; }
      internalOpen = false;
      applyOpen(false, {reason, source});
      if (selectionTransaction) pendingForcedNotice = {reason, source};
      else notifyOpen(false, reason, source, true);
    };
    const emitNativeCommit = () => {
      nativeSelect.dispatchEvent(new Event('input', {bubbles:true}));
      nativeSelect.dispatchEvent(new Event('change', {bubbles:true}));
    };
    const requestValue = (next, option, source, sourceEvent) => {
      if (next === currentValue || option?.hasAttribute('data-disabled')) return false;
      const previousValue = currentValue;
      const detail = {
        value:next,
        previousValue,
        option,
        controlled:controlledValue,
        source,
        sourceEvent,
      };
      if (!controlledValue) {
        currentValue = next;
        committedValue = next;
        syncValue();
      }
      onValueChange?.(next, detail);
      if (!controlledValue) emitNativeCommit();
      return true;
    };
    const selectOption = (option, event, source) => {
      if (!(option instanceof HTMLElement) || option.hasAttribute('data-disabled')) return;
      selectionTransaction = true;
      const transactionGeneration = generation;
      requestValue(option.dataset.value, option, source, event);
      selectionTransaction = false;
      if (pendingForcedNotice) {
        const notice = pendingForcedNotice;
        pendingForcedNotice = null;
        notifyOpen(false, notice.reason, notice.source, true);
        return;
      }
      if (!active || transactionGeneration !== generation || !root.isConnected) return;
      requestOpen(false, 'selection', option);
    };
    const localeLower = (value) => {
      const lang = root.closest('[lang]')?.getAttribute('lang')
        ?? root.ownerDocument.documentElement.lang
        ?? '';
      try { return lang ? value.toLocaleLowerCase(lang) : value.toLocaleLowerCase(); }
      catch { return value.toLowerCase(); }
    };
    const typeahead = (event) => {
      const altGraph = event.getModifierState?.('AltGraph') ?? false;
      if (
        event.isComposing || event.ctrlKey || event.metaKey
        || (event.altKey && !altGraph) || event.key.length !== 1
      ) return false;
      const key = localeLower(event.key);
      typeBuffer = typeBuffer.length === 1 && typeBuffer === key ? key : typeBuffer + key;
      if (typeTimer !== null) clearTimeout(typeTimer);
      typeTimer = setTimeout(() => { typeBuffer=''; typeTimer=null; }, 500);
      const enabled = enabledOptions();
      const startValue = logicalOpen ? highlightedValue : currentValue;
      const index = enabled.findIndex((option) => option.dataset.value === startValue);
      const ordered = [...enabled.slice(index + 1), ...enabled.slice(0, index + 1)];
      const match = ordered.find((option) => {
        const label = option.querySelector('[data-citry-ui-part="option-label"]')?.textContent ?? '';
        return localeLower(label.trim().replace(/\s+/g, ' ')).startsWith(typeBuffer);
      });
      if (!match) return false;
      if (logicalOpen) {
        highlightedValue = match.dataset.value;
        syncPresentation();
        match.scrollIntoView({block:'nearest'});
      } else requestValue(match.dataset.value, match, 'keyboard', event);
      return true;
    };
    const onClick = (event) => {
      const path = event.composedPath();
      if (path.includes(trigger)) {
        if (!eligible()) return;
        requestOpen(!logicalOpen, 'trigger', trigger, true);
        return;
      }
      const option = path.find((node) => (
        node instanceof HTMLElement
        && node.getAttribute('role') === 'option'
        && node.closest('[role="listbox"]') === listbox
      ));
      if (option) selectOption(option, event, 'pointer');
    };
    const onPointerOver = (event) => {
      if (!logicalOpen || (event.pointerType === 'pen' && (event.buttons > 0 || event.pressure > 0))) return;
      const option = event.composedPath().find((node) => (
        node instanceof HTMLElement
        && node.getAttribute('role') === 'option'
        && node.closest('[role="listbox"]') === listbox
      ));
      if (!(option instanceof HTMLElement) || option.hasAttribute('data-disabled')) return;
      highlightedValue = option.dataset.value;
      syncPresentation();
    };
    const moveHighlight = (direction) => {
      const enabled = enabledOptions();
      if (!enabled.length) return;
      const index = enabled.findIndex((option) => option.dataset.value === highlightedValue);
      const initial = direction > 0 ? enabled[0] : enabled.at(-1);
      const next = index < 0
        ? initial
        : enabled[index + direction]
          ?? (configuration.loop ? initial : enabled[index]);
      highlightedValue = next?.dataset.value ?? null;
      syncPresentation();
      next?.scrollIntoView({block:'nearest'});
    };
    const onKeyDown = (event) => {
      if (event.target !== trigger || !eligible()) return;
      if (!logicalOpen) {
        if (event.key === 'Enter' || event.key === ' ' || event.key === 'ArrowDown' || event.key === 'ArrowUp') {
          event.preventDefault();
          requestOpen(true, 'keyboard', trigger, true, event.key === 'ArrowUp' ? -1 : 1);
          return;
        }
        if (typeahead(event)) event.preventDefault();
        return;
      }
      if (event.key === 'ArrowDown') { event.preventDefault(); moveHighlight(1); }
      else if (event.key === 'ArrowUp') { event.preventDefault(); moveHighlight(-1); }
      else if (event.key === 'Home') {
        event.preventDefault();
        highlightedValue = enabledOptions()[0]?.dataset.value ?? null;
        syncPresentation();
      } else if (event.key === 'End') {
        event.preventDefault();
        highlightedValue = enabledOptions().at(-1)?.dataset.value ?? null;
        syncPresentation();
      } else if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        selectOption(optionFor(highlightedValue), event, 'keyboard');
      } else if (event.key === 'Escape') {
        event.preventDefault();
        requestOpen(false, 'escape', trigger);
      } else if (event.key === 'Tab') {
        tabGesture = true;
        setTimeout(() => { tabGesture=false; }, 0);
        requestOpen(false, 'tab', trigger);
      } else if (typeahead(event)) event.preventDefault();
    };
    const onToggle = (event) => {
      if (event.target !== popup) return;
      const nativeOpen = popup.matches(':popover-open');
      if (nativeOpen === logicalOpen) return;
      if (nativeOpen) {
        if (!coordinator.mayOpen(layer) || controlledOpen) {
          popup.hidePopover();
          if (controlledOpen) notifyOpen(true, 'native', popup);
          return;
        }
        internalOpen = true;
        logicalOpen = true;
        popup.hidden = false;
        popup.inert = false;
        popup.setAttribute('data-open', '');
        highlightedValue = chooseHighlight();
        coordinator.register(layer);
        syncPresentation();
        notifyOpen(true, 'native', popup);
        return;
      }
      if (controlledOpen && coordinator.mayOpen(layer)) {
        popup.hidden = false;
        popup.showPopover();
        notifyOpen(false, 'native', popup);
        return;
      }
      internalOpen = false;
      logicalOpen = false;
      popup.inert = true;
      popup.hidden = true;
      popup.removeAttribute('data-open');
      highlightedValue = null;
      coordinator.unregister(layer);
      syncPresentation();
      notifyOpen(false, 'native', popup);
    };
    const onInvalid = (event) => {
      nativeInvalid = true;
      syncValue();
      event.preventDefault();
      trigger.focus({preventScroll:true});
    };
    const onProxyFocus = () => {
      if (root.hasAttribute('data-citry-select-initialized')) trigger.focus({preventScroll:true});
    };
    const onReset = (event) => {
      const scheduled = generation;
      setTimeout(() => {
        if (!active || event.defaultPrevented || scheduled !== generation) return;
        if (!controlledValue && currentValue !== data.value) {
          const previousValue = currentValue;
          currentValue = data.value;
          committedValue = data.value;
          syncValue();
          onValueChange?.(currentValue, {
            value:currentValue, previousValue, option:selectedOption(), controlled:false,
            source:'reset', sourceEvent:event,
          });
        }
        if (logicalOpen) requestOpen(false, 'reset', nativeForm);
      }, 0);
    };
    const reconcileControlled = () => {
      if (clientValue === undefined) {
        invalidEpisodes.delete('value');
        if (controlledValue) committedValue = currentValue;
        controlledValue = false;
        currentValue = committedValue;
      } else if (clientValue === null) {
        invalidEpisodes.delete('value');
        controlledValue = true;
        currentValue = null;
        pendingStructure = null;
      } else {
        const normalized = canonicalString(clientValue);
        if (normalized === null) {
          report('value', clientValue, '; releasing control from the committed value');
          if (controlledValue) committedValue = currentValue;
          controlledValue = false;
          currentValue = committedValue;
        } else if (!optionFor(normalized)) {
          controlledValue = true;
          currentValue = null;
          report('value', clientValue, '; the settled collection does not contain this value');
          if (pendingStructure !== normalized) {
            pendingStructure = normalized;
            const scheduled = generation;
            queueMicrotask(() => {
              if (active && scheduled === generation && pendingStructure === normalized) {
                onValueChange?.(null, {
                  value:null, previousValue:normalized, option:null, controlled:true,
                  source:'structure', sourceEvent:null,
                });
              }
            });
          }
        } else {
          invalidEpisodes.delete('value');
          pendingStructure = null;
          controlledValue = true;
          currentValue = normalized;
        }
      }
      if (currentValue !== null && !optionFor(currentValue)) {
        const previousValue = currentValue;
        currentValue = null;
        committedValue = null;
        if (pendingStructure !== previousValue) {
          pendingStructure = previousValue;
          queueMicrotask(() => onValueChange?.(null, {
            value:null, previousValue, option:null, controlled:false,
            source:'structure', sourceEvent:null,
          }));
        }
      }
      if (clientOpen === undefined || clientOpen === null) {
        invalidEpisodes.delete('open');
        controlledOpen = false;
        applyOpen(internalOpen, {reason:'owner', source:trigger});
      } else if (typeof clientOpen === 'boolean') {
        invalidEpisodes.delete('open');
        controlledOpen = true;
        applyOpen(clientOpen, {reason:'owner', source:trigger, focus:clientOpen});
      } else {
        report('open', clientOpen, '; releasing control from committed visibility');
        controlledOpen = false;
        applyOpen(internalOpen, {reason:'owner', source:trigger});
      }
      if ((effectiveDisabled() || configuration.readonly) && logicalOpen) {
        forceClose('ancestor', trigger);
      }
      syncPresentation();
    };

    root.addEventListener('click', onClick, true);
    root.addEventListener('pointerover', onPointerOver, true);
    trigger.addEventListener('keydown', onKeyDown, true);
    popup.addEventListener('toggle', onToggle);
    nativeSelect.addEventListener('invalid', onInvalid);
    nativeSelect.addEventListener('focus', onProxyFocus);
    nativeForm?.addEventListener('reset', onReset);

    const fieldsetObservers = [];
    for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
      if (!(ancestor instanceof HTMLFieldSetElement)) continue;
      const observer = new MutationObserver(reconcileControlled);
      observer.observe(ancestor, {attributes:true, childList:true, attributeFilter:['disabled']});
      fieldsetObservers.push(observer);
    }
    const stop = effect(() => {
      clientValue = props.value;
      clientOpen = props.open;
      onValueChange = typeof props.onValueChange === 'function' ? props.onValueChange : null;
      onOpenChange = typeof props.onOpenChange === 'function' ? props.onOpenChange : null;
      if (props.onValueChange != null && onValueChange === null) report('onValueChange', props.onValueChange);
      else invalidEpisodes.delete('onValueChange');
      if (props.onOpenChange != null && onOpenChange === null) report('onOpenChange', props.onOpenChange);
      else invalidEpisodes.delete('onOpenChange');
      configuration = {
        required:field ? field.required : resolveBoolean('required', data.required),
        disabled:field
          ? field.disabled
          : (form?.disabled || resolveBoolean('disabled', data.disabled)),
        readonly:field
          ? field.readonly
          : (form?.readonly || resolveBoolean('readonly', data.readonly)),
        invalid:field ? field.invalid : resolveBoolean('invalid', data.invalid),
        loop:resolveBoolean('loop', data.loop),
        placement:resolveChoice('placement', data.placement, [
          'bottom-start','bottom-end','top-start','top-end',
        ]),
        matchWidth:resolveBoolean('matchWidth', data.matchWidth),
        variant:resolveChoice('variant', data.variant, ['outline','filled','plain']),
        size:resolveChoice('size', data.size, ['sm','md','lg']),
      };
      reconcileControlled();
    });
    root.setAttribute('data-citry-select-initialized', '');
    nativeSelect.tabIndex = -1;
    nativeSelect.setAttribute('aria-hidden', 'true');
    reconcileControlled();

    return () => {
      active = false;
      generation += 1;
      if (typeTimer !== null) clearTimeout(typeTimer);
      root[selectHandoffKey] = {
        serverFingerprint,
        committedValue,
        internalOpen,
        highlightedValue,
        pendingStructure,
      };
      stop?.();
      fieldsetObservers.forEach((observer) => observer.disconnect());
      root.removeEventListener('click', onClick, true);
      root.removeEventListener('pointerover', onPointerOver, true);
      trigger.removeEventListener('keydown', onKeyDown, true);
      popup.removeEventListener('toggle', onToggle);
      nativeSelect.removeEventListener('invalid', onInvalid);
      nativeSelect.removeEventListener('focus', onProxyFocus);
      nativeForm?.removeEventListener('reset', onReset);
      coordinator.unregister(layer, {reason:'ancestor', source:root, cascade:true});
      field?.setNativeInvalid(false);
      root.removeAttribute('data-citry-select-initialized');
      nativeSelect.removeAttribute('tabindex');
      nativeSelect.removeAttribute('aria-hidden');
    };
  },
})
