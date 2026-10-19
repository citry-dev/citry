(function() {

__citryRuntime.registerTypeOptions.bind(null, "CTimePicker_7f3684", "6b607635c5740d3ecc3915f0a0078f6181fc123cf5ea018991e9a9b74fe02eda")({
  props: {
    value: {}, open: {}, required: {}, disabled: {}, readonly: {}, invalid: {}, clearable: {},
    dismissible: {}, placement: {}, matchWidth: {}, variant: {}, size: {}, onValueChange: {}, onOpenChange: {},
  },
  inject: {
    fieldService: {from: Symbol.for('citry-ui:field'), default: null},
    formService: {from: Symbol.for('citry-ui:form'), default: null},
  },
  provide() {
    return {[Symbol.for('citry-ui:field')]: null, [Symbol.for('citry-ui:form')]: null};
  },
  data() {
    return {
      timePickerOpen: false, timePickerListValue: null, timePickerListDisabled: false,
      timePickerDismissible: true, timePickerPlacement: 'bottom-start', timePickerMatchWidth: true,
      timePickerOnPopoverOpenChange: null, timePickerOnListValueChange: null,
    };
  },
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component;
    const defaults = data.serverDefaults;
    const props = component.$props;
    const scope = component;
    const effect = Citry.vue.watchEffect;
    const i18n = component.$i18n;
    const input = root.querySelector(':scope > [data-citry-ui-part="fallback-input"]');
    const enhanced = root.querySelector(':scope > [data-citry-ui-part="enhanced-control"]');
    const trigger = root.querySelector('[data-citry-time-picker-trigger]');
    const valueText = trigger?.querySelector('[data-citry-ui-part="value"]');
    const clear = enhanced?.querySelector(':scope > [data-citry-ui-part="clear"]');
    if (!(root instanceof HTMLElement) || !(input instanceof HTMLInputElement) || input.type !== 'time' || !(enhanced instanceof HTMLElement) || !(trigger instanceof HTMLButtonElement) || !(valueText instanceof HTMLElement) || !(clear instanceof HTMLButtonElement)) throw new Error('[citry-ui] CTimePicker settled anatomy is invalid.');

    const field = component.fieldService;
    const form = component.formService;
    const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
    if (runtime?.generation !== 1) throw new Error('[citry-ui] CTimePicker form-control runtime is unavailable.');
    const resolver = runtime.resolver(root, props, 'CTimePicker');
    const listeners = runtime.listeners();
    const mutations = runtime.mutations(root);
    const owned = mutations.owned;
    const optionSet = new Set(data.optionValues);
    const allowedPlacements = ['top-start','top','top-end','bottom-start','bottom','bottom-end'];
    const profile = data.showSeconds ? 'citry-ui-time-picker-display-seconds' : 'citry-ui-time-picker-display';
    let current = input.value || defaults.value || null;
    let initialValue = defaults.value || null;
    // A server re-render that keeps this picker keeps its Vue instance, and
    // with it the popup's open state, so a popup that was open before the
    // re-render stays open. The picker has no server `open` input, so there
    // is no server value for it to follow.
    let internalOpen = scope.timePickerOpen === true;
    let controlledValue = false;
    let controlledOpen = false;
    let nativeInvalid = false;
    let unavailableMessage = data.unavailableMessage;
    let invalidGeneration = 0;
    let dispatching = false;
    let ready = false;
    let configuration = null;

    const canonicalTime = value => {
      if (typeof value !== 'string') return null;
      const match = value.match(/^([0-9]{2}):([0-9]{2})(?::([0-9]{2}))?$/);
      if (match === null || Number(match[1]) > 23 || Number(match[2]) > 59 || Number(match[3] ?? 0) > 59) return null;
      return value;
    };
    const fields = value => { const [hour, minute, second = '0'] = value.split(':'); return { hour:Number(hour), minute:Number(minute), second:Number(second) }; };
    const fromIso = value => { const result = new Date(0); const parsed = fields(value); result.setUTCHours(parsed.hour, parsed.minute, parsed.second, 0); return result; };
    const formatTime = value => i18n
      ? i18n.format.time(fields(value), { format: profile })
      : new Intl.DateTimeFormat(data.locale, { hour:'numeric', minute:'2-digit', second:data.showSeconds?'2-digit':undefined, timeZone:'UTC' }).format(fromIso(value));
    const translated = (owner, message, fallback, values = undefined) => i18n && data.catalog[owner] ? i18n.tr(message, values) : fallback;
    const placeholderText = () => translated('placeholder', 'citry-ui-time-picker-placeholder', data.placeholder);
    const pickerLabel = () => translated('picker_label', 'citry-ui-time-picker-label', data.pickerLabel);
    const triggerLabel = value => {
      if (!value) return pickerLabel();
      const formatted = formatTime(value);
      return data.catalog.change_label
        ? i18n?.tr('citry-ui-time-picker-change', { time: formatted }) ?? data.changeLabel.replaceAll('{time}', formatted)
        : data.changeLabel.replaceAll('{time}', formatted);
    };
    const resolveConfiguration = () => ({
      required: field ? field.required : resolver.boolean('required', defaults.required),
      disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', defaults.disabled) || runtime.fieldsetDisabled(input),
      readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : defaults.readonly),
      invalid: field ? field.invalid : resolver.boolean('invalid', defaults.invalid),
      clearable: resolver.boolean('clearable', defaults.clearable),
      dismissible: resolver.boolean('dismissible', defaults.dismissible),
      placement: resolver.choice('placement', defaults.placement, allowedPlacements),
      matchWidth: resolver.boolean('matchWidth', defaults.matchWidth),
      variant: resolver.choice('variant', defaults.variant, ['outline','filled','plain']),
      size: resolver.choice('size', defaults.size, ['sm','md','lg']),
    });
    const reportFieldOwned = () => {
      if (!field) return;
      ['required','disabled','readonly','invalid'].forEach(name => props[name] === undefined ? resolver.clear(name) : resolver.report(name, props[name], 'ignoring it because the enclosing CField owns this state'));
    };
    const emitNative = () => {
      dispatching = true;
      try { input.dispatchEvent(new Event('input', { bubbles:true })); input.dispatchEvent(new Event('change', { bubbles:true })); }
      finally { dispatching = false; }
    };
    const valueDetail = (value, previousValue, source, sourceEvent) => ({ value, previousValue, controlled: controlledValue, source, sourceEvent });
    const openDetail = (reason, source, forced = false) => ({ reason, controlled: controlledOpen, forced, source });
    const focusListbox = () => requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(() => {
      if (!root.isConnected || !scope.timePickerOpen) return;
      const selected = current ? root.querySelector(`[data-citry-ui-part="listbox-option"][data-value="${CSS.escape(current)}"]`) : null;
      const target = selected ?? root.querySelector('[data-citry-ui-part="listbox-option"][tabindex="0"]');
      if (target instanceof HTMLElement) target.focus({ preventScroll:true });
    })));
    const requestOpen = (next, reason, source = null, forced = false) => {
      if (next === scope.timePickerOpen && !forced) return;
      if (!controlledOpen || forced) { internalOpen = next; scope.timePickerOpen = next; }
      resolver.callback('onOpenChange')?.(next, openDetail(reason, source, forced));
    };
    const requestValue = (next, source, event) => {
      if (configuration.disabled || configuration.readonly || next === current) return false;
      if (next !== null && (canonicalTime(next) === null || !optionSet.has(next))) return false;
      const previous = current;
      if (!controlledValue) { current = next; scope.timePickerListValue = next; }
      resolver.callback('onValueChange')?.(next, valueDetail(next, previous, source, event));
      if (!controlledValue) { render(); emitNative(); }
      requestOpen(false, source === 'option' ? 'selection' : 'clear', event);
      return true;
    };
    const updateGeneratedLabels = () => {
      const label = root.querySelector('[data-citry-ui-part="listbox-label"]');
      if (label instanceof HTMLElement) label.textContent = pickerLabel();
      root.querySelectorAll('[data-citry-ui-part="listbox-option"]').forEach(option => {
        const copy = option.querySelector('[data-citry-ui-part="listbox-option-label"]');
        if (copy instanceof HTMLElement && option instanceof HTMLElement && option.dataset.value) copy.textContent = formatTime(option.dataset.value);
      });
    };
    const render = () => owned(() => {
      input.value = current || '';
      input.required = configuration.required;
      input.disabled = configuration.disabled;
      input.readOnly = configuration.readonly;
      const unavailable = current !== null && !optionSet.has(current);
      input.setCustomValidity(unavailable ? unavailableMessage : '');
      const invalid = configuration.invalid || nativeInvalid || unavailable;
      trigger.disabled = configuration.disabled;
      trigger.setAttribute('aria-label', triggerLabel(current));
      valueText.textContent = current ? formatTime(current) : placeholderText();
      clear.hidden = !configuration.clearable || configuration.required || current === null;
      clear.disabled = configuration.disabled || configuration.readonly;
      runtime.states(root, { empty:current === null, open:scope.timePickerOpen, required:configuration.required, disabled:configuration.disabled, readonly:configuration.readonly, invalid });
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      runtime.relationships([trigger], field, { describedby:data.describedby, errormessage:data.errormessage }, invalid);
      scope.timePickerListValue = current;
      scope.timePickerListDisabled = configuration.disabled || configuration.readonly;
      scope.timePickerDismissible = configuration.dismissible;
      scope.timePickerPlacement = configuration.placement;
      scope.timePickerMatchWidth = configuration.matchWidth;
      updateGeneratedLabels();
    });

    scope.timePickerOpen = internalOpen;
    scope.timePickerListValue = current;
    scope.timePickerListDisabled = false;
    scope.timePickerOnPopoverOpenChange = (next, detail) => {
      if (detail?.forced) { internalOpen = false; scope.timePickerOpen = false; resolver.callback('onOpenChange')?.(false, { ...detail, controlled: controlledOpen }); if (ready) render(); return; }
      requestOpen(next, detail?.reason ?? 'native', detail?.source ?? null);
      if (next) focusListbox();
      if (ready) render();
    };
    scope.timePickerOnListValueChange = (next, detail) => requestValue(next, 'option', detail?.sourceEvent ?? null);

    listeners.add(clear, 'click', event => requestValue(null, 'clear', event));
    listeners.add(input, 'input', event => {
      if (dispatching) return;
      const next = input.value || null;
      if (controlledValue) { queueMicrotask(() => render()); return; }
      const previous = current;
      current = next;
      resolver.callback('onValueChange')?.(next, valueDetail(next, previous, 'native', event));
      render();
    });
    listeners.add(input, 'change', () => {
      if (nativeInvalid && input.validity.valid) { nativeInvalid = false; field?.setNativeInvalid(false); render(); }
    });
    listeners.add(input, 'invalid', event => {
      event.preventDefault();
      nativeInvalid = true;
      field?.setNativeInvalid(true);
      requestOpen(true, 'trigger', event);
      render();
      const token = ++invalidGeneration;
      runtime.invalidFocus(root, trigger, () => token === invalidGeneration && !configuration.disabled);
      focusListbox();
    }, true);
    const reset = runtime.registerReset(root, input, {
      reset: event => {
        if (event.defaultPrevented) return;
        nativeInvalid = false;
        field?.setNativeInvalid(false);
        const previous = current;
        if (!controlledValue) current = initialValue;
        else resolver.callback('onValueChange')?.(initialValue, valueDetail(initialValue, previous, 'reset', event));
        requestOpen(false, 'reset', event);
        render();
      },
      invalidate: () => { invalidGeneration += 1; },
    });
    const stopFieldset = runtime.watchFieldset(root, input, () => { configuration = resolveConfiguration(); render(); });
    const unavailableBinding = i18n && data.catalog.unavailable_message ? i18n.bind({ message:'citry-ui-time-picker-unavailable', onChange:text => { unavailableMessage = text; if (ready) render(); } }) : null;
    const unsubscribe = i18n?.subscribe(() => { if (ready) render(); });

    effect(() => {
      // Read before this update changes it: a server re-render keeps this
      // picker's Vue instance, so on the new run's first update this is the
      // open state the previous run left.
      const wasOpen = scope.timePickerOpen === true;
      reportFieldOwned();
      configuration = resolveConfiguration();
      const requestedValue = props.value;
      if (requestedValue === undefined) { controlledValue = false; resolver.clear('value'); }
      else if (requestedValue === null) { controlledValue = true; current = null; resolver.clear('value'); }
      else {
        const normalized = canonicalTime(requestedValue);
        if (normalized === null || !optionSet.has(normalized)) resolver.report('value', requestedValue);
        else { controlledValue = true; current = normalized; resolver.clear('value'); }
      }
      const requestedOpen = props.open;
      if (requestedOpen === undefined || requestedOpen === null) { if (controlledOpen) internalOpen = scope.timePickerOpen; controlledOpen = false; resolver.clear('open'); }
      else if (typeof requestedOpen === 'boolean') { const opening = !scope.timePickerOpen && requestedOpen; controlledOpen = true; internalOpen = requestedOpen; scope.timePickerOpen = requestedOpen; resolver.clear('open'); if (opening) focusListbox(); }
      else { resolver.report('open', requestedOpen); if (controlledOpen) internalOpen = scope.timePickerOpen; controlledOpen = false; }
      // A disabled picker cannot stay open, so disabling an open popup closes
      // it, as CMenu does. The owner did not ask for that close, so it is
      // reported once, when the popup was open before this update.
      if (configuration.disabled && scope.timePickerOpen) {
        internalOpen = false;
        scope.timePickerOpen = false;
        if (wasOpen) resolver.callback('onOpenChange')?.(false, openDetail('disabled', null, true));
      }
      ready = true;
      render();
    });
    mutations.start(() => render());
    owned(() => {
      runtime.enhanceNative(input, trigger, { publicId:data.publicId, nativeId:data.nativeId, visibleId:data.visibleId, className:'cui-form-control__native--enhanced' });
      root.toggleAttribute('data-enhanced', true);
      root.setAttribute('data-citry-time-picker-initialized', '');
    });
    render();

    return () => {
      ready = false;
      invalidGeneration += 1;
      unavailableBinding?.dispose();
      unsubscribe?.();
      listeners.stop();
      mutations.stop();
      stopFieldset();
      reset();
      if (nativeInvalid) field?.setNativeInvalid(false);
      owned(() => {
        runtime.enhanceNative(input, trigger, { publicId:data.publicId, nativeId:data.nativeId, visibleId:data.visibleId, className:'cui-form-control__native--enhanced' }, false);
        root.removeAttribute('data-enhanced');
        root.removeAttribute('data-citry-time-picker-initialized');
      });
    };
  },
});

})();