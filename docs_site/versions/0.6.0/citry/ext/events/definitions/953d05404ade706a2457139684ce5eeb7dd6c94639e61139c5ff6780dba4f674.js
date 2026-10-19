(function() {

__citryRuntime.registerTypeOptions.bind(null, "CDatePicker_42b9f6", "83df283f579d65156ad37b582d16d9c6449703f1130c2dd420d29a305aa2ff8f")({
  props: {
    value: {}, open: {}, min: {}, max: {}, unavailableDates: {}, required: {}, disabled: {}, readonly: {}, invalid: {},
    clearable: {}, dismissible: {}, placement: {}, matchWidth: {}, firstDayOfWeek: {}, showAdjacentDays: {}, fixedWeeks: {},
    variant: {}, size: {}, onValueChange: {}, onOpenChange: {},
  },
  inject: {
    fieldService: {from: Symbol.for('citry-ui:field'), default: null},
    formService: {from: Symbol.for('citry-ui:form'), default: null},
  },
  provide() {
    return {
      [Symbol.for('citry-ui:field')]: null,
      [Symbol.for('citry-ui:form')]: null,
    };
  },
  data() {
    return {
      datePickerOpen: false,
      datePickerCalendarValue: null,
      datePickerVisibleDate: undefined,
      datePickerMin: null,
      datePickerMax: null,
      datePickerUnavailableDates: [],
      datePickerDisabled: false,
      datePickerReadonly: false,
      datePickerDismissible: true,
      datePickerPlacement: 'bottom-start',
      datePickerMatchWidth: true,
      datePickerFirstDayOfWeek: null,
      datePickerShowAdjacentDays: true,
      datePickerFixedWeeks: true,
      datePickerOnPopoverOpenChange: null,
      datePickerOnCalendarValueChange: null,
      datePickerOnVisibleDateChange: null,
    };
  },
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component;
    const props = component.$props;
    const scope = component;
    const effect = Citry.vue.watchEffect;
    const i18n = component.$i18n;
    const input = root.querySelector(':scope > [data-citry-ui-part="fallback-input"]');
    const enhanced = root.querySelector(':scope > [data-citry-ui-part="enhanced-control"]');
    const trigger = root.querySelector('[data-citry-date-picker-trigger]');
    const valueText = trigger?.querySelector('[data-citry-ui-part="value"]');
    const clear = enhanced?.querySelector(':scope > [data-citry-ui-part="clear"]');
    if (!(root instanceof HTMLElement) || !(input instanceof HTMLInputElement) || input.type !== 'date' || !(enhanced instanceof HTMLElement) || !(trigger instanceof HTMLButtonElement) || !(valueText instanceof HTMLElement) || !(clear instanceof HTMLButtonElement)) throw new Error('[citry-ui] CDatePicker settled anatomy is invalid.');

    const field = component.fieldService;
    const form = component.formService;
    const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
    if (runtime?.generation !== 1) throw new Error('[citry-ui] CDatePicker form-control runtime is unavailable.');
    const resolver = runtime.resolver(root, props, 'CDatePicker');
    const listeners = runtime.listeners();
    const mutations = runtime.mutations(root);
    const owned = mutations.owned;
    let current = input.value || data.serverValue || null;
    // A server re-render that keeps this picker keeps its Vue instance, and
    // with it the popup's open state, so a popup that was open before the
    // re-render stays open. The picker has no server `open` input, so there
    // is no server value for it to follow.
    let internalOpen = scope.datePickerOpen === true;
    let controlledValue = false;
    let controlledOpen = false;
    let visibleDate = current || undefined;
    let initialValue = data.serverValue || null;
    let nativeInvalid = false;
    let unavailableMessage = data.unavailableMessage;
    let invalidGeneration = 0;
    let dispatching = false;
    let ready = false;
    let configuration = null;
    let previousConstraints = { min: data.serverMin, max: data.serverMax, unavailableDates: [...data.serverUnavailableDates] };
    const allowedPlacements = ['top-start','top','top-end','bottom-start','bottom','bottom-end'];
    const DISPLAY_PROFILE = 'citry-ui-date-picker-display';

    const canonicalDate = value => {
      if (typeof value !== 'string' || !/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value)) return null;
      const [year, month, day] = value.split('-').map(Number);
      if (year < 1 || year > 9999) return null;
      const result = new Date(0);
      result.setUTCHours(12, 0, 0, 0);
      result.setUTCFullYear(year, month - 1, day);
      return result.getUTCFullYear() === year && result.getUTCMonth() === month - 1 && result.getUTCDate() === day ? value : null;
    };
    const fields = value => { const [year, month, day] = value.split('-').map(Number); return { year, month, day }; };
    const fromIso = value => { const [year, month, day] = value.split('-').map(Number); const result = new Date(0); result.setUTCHours(12,0,0,0); result.setUTCFullYear(year,month-1,day); return result; };
    const formatDate = value => i18n
      ? i18n.format.date(fields(value), { format: DISPLAY_PROFILE })
      : new Intl.DateTimeFormat(data.locale, { day:'numeric', month:'long', year:'numeric', timeZone:'UTC' }).format(fromIso(value));
    const translated = (owner, message, fallback, values = undefined) => i18n && data.catalog[owner] ? i18n.tr(message, values) : fallback;
    const placeholderText = () => translated('placeholder', 'citry-ui-date-picker-placeholder', data.placeholder);
    const pickerLabel = () => translated('picker_label', 'citry-ui-date-picker-label', data.pickerLabel);
    const triggerLabel = value => {
      if (!value) return pickerLabel();
      const date = formatDate(value);
      return data.catalog.change_label
        ? i18n?.tr('citry-ui-date-picker-change', { date }) ?? data.changeLabel.replaceAll('{date}', date)
        : data.changeLabel.replaceAll('{date}', date);
    };
    const optionalDate = (name, fallback) => {
      const requested = props[name];
      if (requested === undefined) { resolver.clear(name); return fallback; }
      if (requested === null) { resolver.clear(name); return null; }
      const normalized = canonicalDate(requested);
      if (normalized !== null) { resolver.clear(name); return normalized; }
      resolver.report(name, requested);
      return previousConstraints[name];
    };
    const unavailableDates = () => {
      const requested = props.unavailableDates;
      if (requested === undefined) { resolver.clear('unavailableDates'); return [...data.serverUnavailableDates]; }
      if (!Array.isArray(requested) || requested.length > 4096) { resolver.report('unavailableDates', requested); return previousConstraints.unavailableDates; }
      const normalized = requested.map(canonicalDate);
      if (normalized.some(value => value === null) || new Set(normalized).size !== normalized.length) { resolver.report('unavailableDates', requested); return previousConstraints.unavailableDates; }
      resolver.clear('unavailableDates');
      return normalized.sort();
    };
    const resolveConstraints = () => {
      const minimum = optionalDate('min', data.serverMin);
      const maximum = optionalDate('max', data.serverMax);
      const unavailable = unavailableDates();
      if (minimum !== null && maximum !== null && minimum > maximum) { resolver.report('min/max', {min:minimum,max:maximum}); return previousConstraints; }
      resolver.clear('min/max');
      previousConstraints = { min: minimum, max: maximum, unavailableDates: unavailable };
      return previousConstraints;
    };
    const firstDay = () => {
      const value = props.firstDayOfWeek;
      if (value === undefined) { resolver.clear('firstDayOfWeek'); return data.serverFirstDayOfWeek; }
      if (value === null || (Number.isInteger(value) && value >= 1 && value <= 7)) { resolver.clear('firstDayOfWeek'); return value; }
      resolver.report('firstDayOfWeek', value); return data.serverFirstDayOfWeek;
    };
    const resolveConfiguration = () => ({
      constraints: resolveConstraints(),
      required: field ? field.required : resolver.boolean('required', data.serverRequired),
      disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', data.serverDisabled) || runtime.fieldsetDisabled(input),
      readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.serverReadonly),
      invalid: field ? field.invalid : resolver.boolean('invalid', data.serverInvalid),
      clearable: resolver.boolean('clearable', data.serverClearable),
      dismissible: resolver.boolean('dismissible', data.serverDismissible),
      placement: resolver.choice('placement', data.serverPlacement, allowedPlacements),
      matchWidth: resolver.boolean('matchWidth', data.serverMatchWidth),
      firstDayOfWeek: firstDay(),
      showAdjacentDays: resolver.boolean('showAdjacentDays', data.serverShowAdjacentDays),
      fixedWeeks: resolver.boolean('fixedWeeks', data.serverFixedWeeks),
      variant: resolver.choice('variant', data.serverVariant, ['outline','filled','plain']),
      size: resolver.choice('size', data.serverSize, ['sm','md','lg']),
    });
    const reportFieldOwned = () => {
      if (!field) return;
      ['required','disabled','readonly','invalid'].forEach(name => props[name] === undefined ? resolver.clear(name) : resolver.report(name, props[name], 'ignoring it because the enclosing CField owns this state'));
    };
    const emitNative = () => {
      dispatching = true;
      try { input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true })); }
      finally { dispatching = false; }
    };
    const valueDetail = (value, previousValue, source, sourceEvent) => ({ value, previousValue, controlled: controlledValue, source, sourceEvent });
    const openDetail = (reason, source, forced = false) => ({ reason, controlled: controlledOpen, forced, source });
    const focusCalendar = () => requestAnimationFrame(() => requestAnimationFrame(() => {
      if (!root.isConnected || !scope.datePickerOpen) return;
      const selected = current ? root.querySelector(`[data-citry-ui-part="day"][data-date="${CSS.escape(current)}"]`) : null;
      const target = selected ?? root.querySelector('[data-citry-ui-part="day"][tabindex="0"]');
      if (target instanceof HTMLElement) target.focus({ preventScroll: true });
    }));
    const requestOpen = (next, reason, source = null, forced = false) => {
      if (next === scope.datePickerOpen && !forced) return;
      if (!controlledOpen || forced) { internalOpen = next; scope.datePickerOpen = next; }
      resolver.callback('onOpenChange')?.(next, openDetail(reason, source, forced));
    };
    const requestValue = (next, source, event) => {
      if (configuration.disabled || configuration.readonly || next === current) return false;
      if (next !== null && (canonicalDate(next) === null || (configuration.constraints.min !== null && next < configuration.constraints.min) || (configuration.constraints.max !== null && next > configuration.constraints.max) || configuration.constraints.unavailableDates.includes(next))) return false;
      const previous = current;
      if (!controlledValue) { current = next; scope.datePickerCalendarValue = next; visibleDate = next || visibleDate; scope.datePickerVisibleDate = visibleDate; }
      resolver.callback('onValueChange')?.(next, valueDetail(next, previous, source, event));
      if (!controlledValue) { render(); emitNative(); }
      requestOpen(false, source === 'calendar' ? 'selection' : 'clear', event);
      return true;
    };
    const render = () => owned(() => {
      const constraints = configuration.constraints;
      input.value = current || '';
      runtime.attr(input, 'min', constraints.min);
      runtime.attr(input, 'max', constraints.max);
      input.required = configuration.required;
      input.disabled = configuration.disabled;
      input.readOnly = configuration.readonly;
      const unavailable = current !== null && constraints.unavailableDates.includes(current);
      input.setCustomValidity(unavailable ? unavailableMessage : '');
      const invalid = configuration.invalid || nativeInvalid || unavailable;
      trigger.disabled = configuration.disabled;
      trigger.setAttribute('aria-label', triggerLabel(current));
      valueText.textContent = current ? formatDate(current) : placeholderText();
      clear.hidden = !configuration.clearable || configuration.required || current === null;
      clear.disabled = configuration.disabled || configuration.readonly;
      runtime.states(root, { empty: current === null, open: scope.datePickerOpen, required: configuration.required, disabled: configuration.disabled, readonly: configuration.readonly, invalid });
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      runtime.relationships([trigger], field, { describedby: data.describedby, errormessage: data.errormessage }, invalid);
      scope.datePickerCalendarValue = current;
      scope.datePickerMin = constraints.min;
      scope.datePickerMax = constraints.max;
      scope.datePickerUnavailableDates = constraints.unavailableDates;
      scope.datePickerDisabled = configuration.disabled;
      scope.datePickerReadonly = configuration.readonly;
      scope.datePickerDismissible = configuration.dismissible;
      scope.datePickerPlacement = configuration.placement;
      scope.datePickerMatchWidth = configuration.matchWidth;
      scope.datePickerFirstDayOfWeek = configuration.firstDayOfWeek;
      scope.datePickerShowAdjacentDays = configuration.showAdjacentDays;
      scope.datePickerFixedWeeks = configuration.fixedWeeks;
    });

    scope.datePickerOpen = internalOpen;
    scope.datePickerCalendarValue = current;
    scope.datePickerVisibleDate = visibleDate;
    scope.datePickerOnPopoverOpenChange = (next, detail) => {
      if (detail?.forced) { internalOpen = false; scope.datePickerOpen = false; resolver.callback('onOpenChange')?.(false, { ...detail, controlled: controlledOpen }); if (ready) render(); return; }
      requestOpen(next, detail?.reason ?? 'native', detail?.source ?? null);
      if (next) focusCalendar();
      if (ready) render();
    };
    scope.datePickerOnCalendarValueChange = (next, detail) => requestValue(next, 'calendar', detail?.sourceEvent ?? null);
    scope.datePickerOnVisibleDateChange = next => { visibleDate = next; scope.datePickerVisibleDate = next; };

    listeners.add(clear, 'click', event => requestValue(null, 'clear', event));
    listeners.add(input, 'input', event => {
      if (dispatching) return;
      const next = input.value || null;
      if (controlledValue) { queueMicrotask(() => render()); return; }
      const previous = current;
      current = next;
      visibleDate = next || visibleDate;
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
      focusCalendar();
    }, true);
    const reset = runtime.registerReset(root, input, {
      reset: event => {
        if (event.defaultPrevented) return;
        nativeInvalid = false;
        field?.setNativeInvalid(false);
        const previous = current;
        if (!controlledValue) { current = initialValue; visibleDate = current || undefined; }
        else resolver.callback('onValueChange')?.(initialValue, valueDetail(initialValue, previous, 'reset', event));
        requestOpen(false, 'reset', event);
        render();
      },
      invalidate: () => { invalidGeneration += 1; },
    });
    const stopFieldset = runtime.watchFieldset(root, input, () => { configuration = resolveConfiguration(); render(); });
    const unavailableBinding = i18n && data.catalog.unavailable_message ? i18n.bind({ message: 'citry-ui-date-picker-unavailable', onChange: text => { unavailableMessage = text; if (ready) render(); } }) : null;
    const unsubscribe = i18n?.subscribe(() => { if (ready) render(); });

    effect(() => {
      // Read before this update changes it: a server re-render keeps this
      // picker's Vue instance, so on the new run's first update this is the
      // open state the previous run left.
      const wasOpen = scope.datePickerOpen === true;
      reportFieldOwned();
      configuration = resolveConfiguration();
      const requestedValue = props.value;
      if (requestedValue === undefined) { controlledValue = false; resolver.clear('value'); }
      else if (requestedValue === null) { controlledValue = true; current = null; resolver.clear('value'); }
      else {
        const normalized = canonicalDate(requestedValue);
        if (normalized === null || (configuration.constraints.min !== null && normalized < configuration.constraints.min) || (configuration.constraints.max !== null && normalized > configuration.constraints.max) || configuration.constraints.unavailableDates.includes(normalized)) resolver.report('value', requestedValue);
        else { controlledValue = true; current = normalized; resolver.clear('value'); }
      }
      const requestedOpen = props.open;
      if (requestedOpen === undefined || requestedOpen === null) { if (controlledOpen) internalOpen = scope.datePickerOpen; controlledOpen = false; resolver.clear('open'); }
      else if (typeof requestedOpen === 'boolean') { const opening = !scope.datePickerOpen && requestedOpen; controlledOpen = true; internalOpen = requestedOpen; scope.datePickerOpen = requestedOpen; resolver.clear('open'); if (opening) focusCalendar(); }
      else { resolver.report('open', requestedOpen); if (controlledOpen) internalOpen = scope.datePickerOpen; controlledOpen = false; }
      if (current) { visibleDate = current; scope.datePickerVisibleDate = current; }
      // A disabled picker cannot stay open, so disabling an open popup closes
      // it, as CMenu does. The owner did not ask for that close, so it is
      // reported once, when the popup was open before this update.
      if (configuration.disabled && scope.datePickerOpen) {
        internalOpen = false;
        scope.datePickerOpen = false;
        if (wasOpen) resolver.callback('onOpenChange')?.(false, openDetail('disabled', null, true));
      }
      ready = true;
      render();
    });
    mutations.start(() => render());
    owned(() => {
      runtime.enhanceNative(input, trigger, { publicId: data.publicId, nativeId: data.nativeId, visibleId: data.visibleId, className: 'cui-form-control__native--enhanced' });
      root.toggleAttribute('data-enhanced', true);
      root.setAttribute('data-citry-date-picker-initialized', '');
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
        runtime.enhanceNative(input, trigger, { publicId: data.publicId, nativeId: data.nativeId, visibleId: data.visibleId, className: 'cui-form-control__native--enhanced' }, false);
        root.removeAttribute('data-enhanced');
        root.removeAttribute('data-citry-date-picker-initialized');
      });
    };
  },
});

})();