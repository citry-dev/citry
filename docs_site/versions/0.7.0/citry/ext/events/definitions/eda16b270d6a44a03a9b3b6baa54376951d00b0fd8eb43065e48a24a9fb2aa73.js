(function() {

__citryRuntime.registerTypeOptions.bind(null, "CDateRange_f0cd44", "9e068f0695f9276a22f155883b71202e3432710fa8355f0d0949c9f3c06071a6")({
  props: {
    value: {}, open: {}, required: {}, disabled: {}, readonly: {}, invalid: {}, clearable: {},
    dismissible: {}, placement: {}, matchWidth: {}, variant: {}, size: {}, onValueChange: {}, onOpenChange: {},
  },
  inject: {formService: {from: Symbol.for('citry-ui:form'), default: null}},
  provide() { return {[Symbol.for('citry-ui:form')]: null}; },
  data() {
    return {
      dateRangeOpen: false, dateRangeCalendarValue: null, dateRangeCalendarDisabled: false,
      dateRangeCalendarReadonly: false, dateRangeRangeStart: null, dateRangeRangeEnd: null,
      dateRangeRangePreview: false, dateRangeStartLabel: null, dateRangeEndLabel: null,
      dateRangeAccessibleLabel: null, dateRangeDismissible: true,
      dateRangePlacement: 'bottom-start', dateRangeMatchWidth: true,
      dateRangeOnPopoverOpenChange: null, dateRangeOnCalendarValueChange: null,
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
    const fallback = root.querySelector(':scope > [data-citry-ui-part="fallback-group"]');
    const startInput = fallback?.querySelector('[data-citry-ui-part="start-input"]');
    const endInput = fallback?.querySelector('[data-citry-ui-part="end-input"]');
    const enhanced = root.querySelector(':scope > [data-citry-ui-part="enhanced-control"]');
    const trigger = root.querySelector('[data-citry-date-range-trigger]');
    const valueText = trigger?.querySelector('[data-citry-ui-part="value"]');
    const clear = enhanced?.querySelector(':scope > [data-citry-ui-part="clear"]');
    const calendar = root.querySelector('.cui-date-range__calendar[data-citry-ui-part="calendar"]');
    if (!(root instanceof HTMLElement) || !(fallback instanceof HTMLElement) || !(startInput instanceof HTMLInputElement) || startInput.type !== 'date' || !(endInput instanceof HTMLInputElement) || endInput.type !== 'date' || !(enhanced instanceof HTMLElement) || !(trigger instanceof HTMLButtonElement) || !(valueText instanceof HTMLElement) || !(clear instanceof HTMLButtonElement) || !(calendar instanceof HTMLElement)) throw new Error('[citry-ui] CDateRange settled anatomy is invalid.');

    const form = component.formService;
    const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
    if (runtime?.generation !== 1) throw new Error('[citry-ui] CDateRange form-control runtime is unavailable.');
    const resolver = runtime.resolver(root, props, 'CDateRange');
    const listeners = runtime.listeners();
    const mutations = runtime.mutations(root);
    const owned = mutations.owned;
    const unavailable = new Set(data.unavailableDates);
    const allowedPlacements = ['top-start','top','top-end','bottom-start','bottom','bottom-end'];
    let current = defaults.value ? { ...defaults.value } : null;
    const initialValue = defaults.value ? { ...defaults.value } : null;
    let draftStart = null;
    let previewEnd = null;
    // A server re-render that keeps this picker keeps its Vue instance, and
    // with it the popup's open state, so a popup that was open before the
    // re-render stays open. The picker has no server `open` input, so there
    // is no server value for it to follow.
    let internalOpen = scope.dateRangeOpen === true;
    let controlledValue = false;
    let controlledOpen = false;
    let nativeInvalid = false;
    let unavailableMessage = data.unavailableMessage;
    let invalidGeneration = 0;
    let dispatching = false;
    let ready = false;
    let configuration = null;
    let lastRangePresentation = null;

    const canonicalDate = value => {
      if (typeof value !== 'string' || !/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value)) return null;
      const [year, month, day] = value.split('-').map(Number);
      if (year < 1 || year > 9999) return null;
      const result = new Date(0); result.setUTCHours(12, 0, 0, 0); result.setUTCFullYear(year, month - 1, day);
      return result.getUTCFullYear() === year && result.getUTCMonth() === month - 1 && result.getUTCDate() === day ? value : null;
    };
    const fields = value => { const [year, month, day] = value.split('-').map(Number); return { year, month, day }; };
    const fromIso = value => { const [year, month, day] = value.split('-').map(Number); const result = new Date(0); result.setUTCHours(12, 0, 0, 0); result.setUTCFullYear(year, month - 1, day); return result; };
    const formatDate = value => i18n
      ? i18n.format.date(fields(value), { format:'citry-ui-date-picker-display' })
      : new Intl.DateTimeFormat(data.locale, { day:'numeric', month:'long', timeZone:'UTC', year:'numeric' }).format(fromIso(value));
    const translated = (owner, message, fallback, values = undefined) => i18n && data.catalog[owner] ? i18n.tr(message, values) : fallback;
    const placeholderText = () => translated('placeholder', 'citry-ui-date-range-placeholder', data.placeholder);
    const rangeLabel = () => translated('range_label', 'citry-ui-date-range-label', data.rangeLabel);
    const startLabel = () => translated('start_label', 'citry-ui-date-range-start-label', data.startLabel);
    const endLabel = () => translated('end_label', 'citry-ui-date-range-end-label', data.endLabel);
    const triggerLabel = value => value
      ? translated('change_label', 'citry-ui-date-range-change', data.changeLabel.replaceAll('{start}', formatDate(value.start)).replaceAll('{end}', formatDate(value.end)), { start:formatDate(value.start), end:formatDate(value.end) })
      : rangeLabel();
    const rangeCrossesUnavailable = value => value !== null && data.unavailableDates.some(item => item >= value.start && item <= value.end);
    const normalizePair = (start, end) => start <= end ? { start, end } : { start:end, end:start };
    const validPair = value => value !== null && canonicalDate(value.start) !== null && canonicalDate(value.end) !== null && value.start <= value.end && (data.min === null || value.start >= data.min) && (data.max === null || value.end <= data.max) && !rangeCrossesUnavailable(value);
    const samePair = (left, right) => left === right || (left !== null && right !== null && left.start === right.start && left.end === right.end);
    const resolveConfiguration = () => ({
      required: resolver.boolean('required', defaults.required),
      disabled: Boolean(form?.disabled) || resolver.boolean('disabled', defaults.disabled) || runtime.fieldsetDisabled(startInput) || runtime.fieldsetDisabled(endInput),
      readonly: resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : defaults.readonly),
      invalid: resolver.boolean('invalid', defaults.invalid),
      clearable: resolver.boolean('clearable', defaults.clearable),
      dismissible: resolver.boolean('dismissible', defaults.dismissible),
      placement: resolver.choice('placement', defaults.placement, allowedPlacements),
      matchWidth: resolver.boolean('matchWidth', defaults.matchWidth),
      variant: resolver.choice('variant', defaults.variant, ['outline','filled','plain']),
      size: resolver.choice('size', defaults.size, ['sm','md','lg']),
    });
    const valueDetail = (value, previousValue, source, sourceEvent) => ({ value, previousValue, controlled:controlledValue, source, sourceEvent });
    const openDetail = (reason, source, forced = false) => ({ reason, controlled:controlledOpen, forced, source });
    const emitNative = (previous, next) => {
      dispatching = true;
      try {
        if (previous?.start !== next?.start) { startInput.dispatchEvent(new Event('input', { bubbles:true })); startInput.dispatchEvent(new Event('change', { bubbles:true })); }
        if (previous?.end !== next?.end) { endInput.dispatchEvent(new Event('input', { bubbles:true })); endInput.dispatchEvent(new Event('change', { bubbles:true })); }
      } finally { dispatching = false; }
    };
    const focusCalendar = () => requestAnimationFrame(() => requestAnimationFrame(() => {
      if (!root.isConnected || !scope.dateRangeOpen) return;
      calendar.querySelector('[data-citry-ui-part="day"][tabindex="0"]')?.focus({ preventScroll:true });
    }));
    const requestOpen = (next, reason, source = null, forced = false) => {
      if (next === scope.dateRangeOpen && !forced) return;
      if (next) { draftStart = null; previewEnd = null; scope.dateRangeCalendarValue = null; }
      else { draftStart = null; previewEnd = null; scope.dateRangeCalendarValue = current?.end ?? null; }
      if (!controlledOpen || forced) { internalOpen = next; scope.dateRangeOpen = next; }
      resolver.callback('onOpenChange')?.(next, openDetail(reason, source, forced));
    };
    const requestValue = (next, source, event) => {
      if (configuration.disabled || configuration.readonly || samePair(next, current)) return false;
      if (next !== null && !validPair(next)) return false;
      const previous = current ? { ...current } : null;
      if (!controlledValue) current = next ? { ...next } : null;
      resolver.callback('onValueChange')?.(next ? { ...next } : null, valueDetail(next ? { ...next } : null, previous, source, event));
      if (!controlledValue) { render(); emitNative(previous, current); }
      return true;
    };
    const commitCalendarDate = (next, event) => {
      if (configuration.disabled || configuration.readonly || unavailable.has(next)) return false;
      if (draftStart === null) {
        draftStart = next; previewEnd = next; scope.dateRangeCalendarValue = next; render(); return true;
      }
      const pair = normalizePair(draftStart, next);
      if (!validPair(pair)) { previewEnd = next; render(); return false; }
      draftStart = null; previewEnd = null;
      requestValue(pair, 'calendar', event);
      requestOpen(false, 'selection', event);
      render();
      return true;
    };
    const syncRangePresentation = () => {
      const preview = draftStart !== null ? normalizePair(draftStart, previewEnd ?? draftStart) : null;
      const shown = preview ?? current;
      const presentation = {
        rangeStart:shown?.start ?? null,
        rangeEnd:shown?.end ?? null,
        rangePreview:preview !== null,
        rangeStartLabel:startLabel(),
        rangeEndLabel:endLabel(),
        accessibleLabel:rangeLabel(),
      };
      scope.dateRangeRangeStart = presentation.rangeStart;
      scope.dateRangeRangeEnd = presentation.rangeEnd;
      scope.dateRangeRangePreview = presentation.rangePreview;
      scope.dateRangeStartLabel = presentation.rangeStartLabel;
      scope.dateRangeEndLabel = presentation.rangeEndLabel;
      scope.dateRangeAccessibleLabel = presentation.accessibleLabel;
      const serialized = JSON.stringify(presentation);
      if (serialized === lastRangePresentation) return;
      lastRangePresentation = serialized;
      calendar.dispatchEvent(new CustomEvent('citry-ui:calendar-range-presentation', { detail:presentation }));
    };
    const render = () => owned(() => {
      startInput.value = current?.start ?? '';
      endInput.value = current?.end ?? '';
      startInput.required = configuration.required; endInput.required = configuration.required;
      startInput.disabled = configuration.disabled; endInput.disabled = configuration.disabled;
      startInput.readOnly = configuration.readonly; endInput.readOnly = configuration.readonly;
      startInput.min = data.min ?? ''; startInput.max = current?.end ?? data.max ?? '';
      endInput.min = current?.start ?? data.min ?? ''; endInput.max = data.max ?? '';
      const unavailableValue = current !== null && !validPair(current);
      startInput.setCustomValidity(unavailableValue ? unavailableMessage : '');
      endInput.setCustomValidity(unavailableValue ? unavailableMessage : '');
      const invalid = configuration.invalid || nativeInvalid || unavailableValue;
      trigger.disabled = configuration.disabled;
      trigger.setAttribute('aria-label', triggerLabel(current));
      valueText.textContent = current ? `${formatDate(current.start)} – ${formatDate(current.end)}` : placeholderText();
      clear.hidden = !configuration.clearable || configuration.required || current === null;
      clear.disabled = configuration.disabled || configuration.readonly;
      runtime.states(root, { empty:current === null, open:scope.dateRangeOpen, required:configuration.required, disabled:configuration.disabled, readonly:configuration.readonly, invalid });
      root.dataset.variant = configuration.variant; root.dataset.size = configuration.size;
      root.setAttribute('aria-disabled', configuration.disabled ? 'true' : 'false');
      root.setAttribute('aria-invalid', invalid ? 'true' : 'false');
      scope.dateRangeCalendarDisabled = configuration.disabled;
      scope.dateRangeCalendarReadonly = configuration.readonly;
      scope.dateRangeDismissible = configuration.dismissible;
      scope.dateRangePlacement = configuration.placement;
      scope.dateRangeMatchWidth = configuration.matchWidth;
      syncRangePresentation();
    });

    scope.dateRangeOpen = internalOpen;
    scope.dateRangeCalendarValue = current?.end ?? null;
    scope.dateRangeCalendarDisabled = false;
    scope.dateRangeCalendarReadonly = false;
    scope.dateRangeRangeStart = current?.start ?? null;
    scope.dateRangeRangeEnd = current?.end ?? null;
    scope.dateRangeRangePreview = false;
    scope.dateRangeStartLabel = startLabel();
    scope.dateRangeEndLabel = endLabel();
    scope.dateRangeAccessibleLabel = rangeLabel();
    scope.dateRangeOnPopoverOpenChange = (next, detail) => {
      if (detail?.forced) { internalOpen = false; scope.dateRangeOpen = false; draftStart = null; previewEnd = null; resolver.callback('onOpenChange')?.(false, { ...detail, controlled:controlledOpen }); if (ready) render(); return; }
      requestOpen(next, detail?.reason ?? 'native', detail?.source ?? null);
      if (next) focusCalendar();
      if (ready) render();
    };
    scope.dateRangeOnCalendarValueChange = (next, detail) => commitCalendarDate(next, detail?.sourceEvent ?? null);

    listeners.add(clear, 'click', event => { if (requestValue(null, 'clear', event)) requestOpen(false, 'clear', event); });
    listeners.add(calendar, 'pointerover', event => { const cell = event.target.closest?.('[data-citry-ui-part="day"][data-date]'); if (draftStart !== null && cell instanceof HTMLElement) { previewEnd = cell.dataset.date; render(); } });
    listeners.add(calendar, 'focusin', event => { const cell = event.target.closest?.('[data-citry-ui-part="day"][data-date]'); if (draftStart !== null && cell instanceof HTMLElement) { previewEnd = cell.dataset.date; render(); } });
    listeners.add(calendar, 'click', event => { const cell = event.target.closest?.('[data-citry-ui-part="day"][data-date]'); if (draftStart !== null && cell instanceof HTMLElement && cell.dataset.date === draftStart) { event.stopImmediatePropagation(); commitCalendarDate(draftStart, event); } }, true);
    listeners.add(calendar, 'keydown', event => { const cell = event.target.closest?.('[data-citry-ui-part="day"][data-date]'); if (draftStart !== null && cell instanceof HTMLElement && cell.dataset.date === draftStart && (event.key === 'Enter' || event.key === ' ')) { event.preventDefault(); event.stopImmediatePropagation(); commitCalendarDate(draftStart, event); } }, true);
    const nativeCommit = event => {
      if (dispatching) return;
      const start = startInput.value || null; const end = endInput.value || null;
      if (start === null || end === null) { if (!configuration.required && start === null && end === null) requestValue(null, 'native', event); return; }
      const pair = { start, end };
      if (validPair(pair)) { nativeInvalid = false; requestValue(pair, 'native', event); }
    };
    listeners.add(startInput, 'input', nativeCommit); listeners.add(endInput, 'input', nativeCommit);
    listeners.add(startInput, 'change', nativeCommit); listeners.add(endInput, 'change', nativeCommit);
    const onInvalid = event => {
      event.preventDefault(); nativeInvalid = true; requestOpen(true, 'native', event); render();
      const token = ++invalidGeneration; runtime.invalidFocus(root, trigger, () => token === invalidGeneration && !configuration.disabled); focusCalendar();
    };
    listeners.add(startInput, 'invalid', onInvalid, true); listeners.add(endInput, 'invalid', onInvalid, true);
    const reset = runtime.registerReset(root, startInput, {
      reset: event => { if (event.defaultPrevented) return; nativeInvalid = false; draftStart = null; previewEnd = null; const previous = current; if (!controlledValue) current = initialValue ? { ...initialValue } : null; else resolver.callback('onValueChange')?.(initialValue ? { ...initialValue } : null, valueDetail(initialValue, previous, 'reset', event)); requestOpen(false, 'reset', event); render(); },
      invalidate: () => { invalidGeneration += 1; },
    });
    const stopFieldset = runtime.watchFieldset(root, startInput, () => { configuration = resolveConfiguration(); render(); });
    const unavailableBinding = i18n && data.catalog.unavailable_message ? i18n.bind({ message:'citry-ui-date-range-unavailable', onChange:text => { unavailableMessage = text; if (ready) render(); } }) : null;
    const unsubscribe = i18n?.subscribe(() => { if (ready) render(); });

    effect(() => {
      // Read before this update changes it: a server re-render keeps this
      // picker's Vue instance, so on the new run's first update this is the
      // open state the previous run left.
      const wasOpen = scope.dateRangeOpen === true;
      configuration = resolveConfiguration();
      const requestedValue = props.value;
      if (requestedValue === undefined) { controlledValue = false; resolver.clear('value'); }
      else if (requestedValue === null) { controlledValue = true; current = null; resolver.clear('value'); }
      else if (typeof requestedValue === 'object' && validPair(requestedValue)) { controlledValue = true; current = { start:requestedValue.start, end:requestedValue.end }; resolver.clear('value'); }
      else resolver.report('value', requestedValue);
      const requestedOpen = props.open;
      if (requestedOpen === undefined || requestedOpen === null) { if (controlledOpen) internalOpen = scope.dateRangeOpen; controlledOpen = false; resolver.clear('open'); }
      else if (typeof requestedOpen === 'boolean') { const opening = !scope.dateRangeOpen && requestedOpen; controlledOpen = true; internalOpen = requestedOpen; scope.dateRangeOpen = requestedOpen; resolver.clear('open'); if (opening) { draftStart = null; previewEnd = null; scope.dateRangeCalendarValue = null; focusCalendar(); } }
      else { resolver.report('open', requestedOpen); if (controlledOpen) internalOpen = scope.dateRangeOpen; controlledOpen = false; }
      // A disabled picker cannot stay open, so disabling an open popup closes
      // it, as CMenu does. The owner did not ask for that close, so it is
      // reported once, when the popup was open before this update.
      if (configuration.disabled && scope.dateRangeOpen) {
        internalOpen = false;
        scope.dateRangeOpen = false;
        if (wasOpen) resolver.callback('onOpenChange')?.(false, openDetail('disabled', null, true));
      }
      ready = true; render();
    });
    mutations.start(() => render());
    owned(() => { startInput.tabIndex = -1; endInput.tabIndex = -1; root.toggleAttribute('data-enhanced', true); root.setAttribute('data-citry-date-range-initialized', ''); });
    render();

    return () => {
      ready = false; invalidGeneration += 1; unavailableBinding?.dispose(); unsubscribe?.(); listeners.stop(); mutations.stop(); stopFieldset(); reset();
      owned(() => { startInput.removeAttribute('tabindex'); endInput.removeAttribute('tabindex'); root.removeAttribute('data-enhanced'); root.removeAttribute('data-citry-date-range-initialized'); });
    };
  },
});

})();