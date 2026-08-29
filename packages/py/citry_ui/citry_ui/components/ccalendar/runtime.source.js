$component({
  props: {
    value: {}, visibleDate: {}, min: {}, max: {}, unavailableDates: {},
    required: {}, disabled: {}, readonly: {}, invalid: {}, firstDayOfWeek: {},
    showAdjacentDays: {}, fixedWeeks: {}, variant: {}, size: {},
    onValueChange: {}, onVisibleDateChange: {},
    rangeStart: {}, rangeEnd: {}, rangePreview: {}, rangeStartLabel: {}, rangeEndLabel: {},
    accessibleLabel: {},
  },
  init: ({ els, data, props, effect, inject, i18n }) => {
    const root = els[0];
    const header = root.querySelector(':scope > [data-citry-ui-part="header"]');
    const previous = header?.querySelector(':scope > [data-citry-ui-part="previous"]');
    const heading = header?.querySelector(':scope > [data-citry-ui-part="heading"]');
    const next = header?.querySelector(':scope > [data-citry-ui-part="next"]');
    const grid = root.querySelector(':scope > [data-citry-ui-part="grid"]');
    const weekdayRow = grid?.querySelector(':scope > thead > [data-citry-ui-part="weekday-row"]');
    const body = grid?.querySelector(':scope > tbody');
    const input = root.querySelector(':scope > [data-citry-ui-part="fallback-input"]');
    if (!(root instanceof HTMLElement) || !(header instanceof HTMLElement) || !(previous instanceof HTMLButtonElement) || !(heading instanceof HTMLElement) || !(next instanceof HTMLButtonElement) || !(grid instanceof HTMLTableElement) || !(weekdayRow instanceof HTMLTableRowElement) || !(body instanceof HTMLTableSectionElement) || !(input instanceof HTMLInputElement) || input.type !== 'date') throw new Error('[citry-ui] CCalendar settled anatomy is invalid.');

    const field = inject(Symbol.for('citry-ui:field'), null);
    const form = inject(Symbol.for('citry-ui:form'), null);
    const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
    if (runtime?.generation !== 1) throw new Error('[citry-ui] CCalendar form-control runtime is unavailable.');
    const resolver = runtime.resolver(root, props, 'CCalendar');
    const listeners = runtime.listeners();
    const mutations = runtime.mutations(root);
    const owned = mutations.owned;
    const DAY = 86400000;
    const PROFILE = Object.freeze({
      heading: 'citry-ui-calendar-heading',
      year: 'citry-ui-calendar-year',
      weekday: 'citry-ui-calendar-weekday',
      weekdayLong: 'citry-ui-calendar-weekday-long',
      day: 'citry-ui-calendar-day',
      label: 'citry-ui-calendar-date-label',
    });
    const FALLBACK_OPTIONS = Object.freeze({
      [PROFILE.heading]: { month: 'long', year: 'numeric' },
      [PROFILE.year]: { year: 'numeric' },
      [PROFILE.weekday]: { weekday: 'short' },
      [PROFILE.weekdayLong]: { weekday: 'long' },
      [PROFILE.day]: { day: 'numeric' },
      [PROFILE.label]: { day: 'numeric', month: 'long', weekday: 'long', year: 'numeric' },
    });
    let current = input.value || data.value;
    let visible = data.visibleDate || current || null;
    let focused = current;
    let pendingFocus = null;
    let controlledValue = false;
    let controlledVisible = false;
    let configuration = null;
    let previousConstraints = { min: data.min, max: data.max, unavailableDates: [...data.unavailableDates] };
    let initialValue = data.value;
    let initialVisible = data.visibleDate;
    let nativeInvalid = false;
    let invalidGeneration = 0;
    let unavailableMessage = data.unavailableMessage;
    let unavailableBinding = null;
    let ready = false;
    let rangePresentation = { start:null, end:null, preview:false, startLabel:null, endLabel:null, accessibleLabel:null };
    let rangePresentationOwned = false;

    const pad = value => String(value).padStart(2, '0');
    const canonicalDate = value => {
      if (typeof value !== 'string' || !/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value)) return null;
      const [year, month, day] = value.split('-').map(Number);
      if (year < 1 || year > 9999) return null;
      const result = new Date(0);
      result.setUTCHours(12, 0, 0, 0);
      result.setUTCFullYear(year, month - 1, day);
      return result.getUTCFullYear() === year && result.getUTCMonth() === month - 1 && result.getUTCDate() === day ? value : null;
    };
    const setRangePresentation = source => {
      const rangeStart = source?.rangeStart === undefined || source?.rangeStart === null ? null : canonicalDate(source.rangeStart);
      const rangeEnd = source?.rangeEnd === undefined || source?.rangeEnd === null ? null : canonicalDate(source.rangeEnd);
      const next = {
        start: rangeStart,
        end: rangeStart !== null && rangeEnd !== null ? rangeEnd : rangeStart,
        preview: source?.rangePreview === true,
        startLabel: typeof source?.rangeStartLabel === 'string' && source.rangeStartLabel ? source.rangeStartLabel : null,
        endLabel: typeof source?.rangeEndLabel === 'string' && source.rangeEndLabel ? source.rangeEndLabel : null,
        accessibleLabel: typeof source?.accessibleLabel === 'string' && source.accessibleLabel ? source.accessibleLabel : null,
      };
      if (Object.keys(next).every(key => next[key] === rangePresentation[key])) return false;
      rangePresentation = next;
      if (ready) render();
      return true;
    };
    const fromIso = value => {
      const [year, month, day] = value.split('-').map(Number);
      const result = new Date(0);
      result.setUTCHours(12, 0, 0, 0);
      result.setUTCFullYear(year, month - 1, day);
      return result;
    };
    const toIso = value => `${String(value.getUTCFullYear()).padStart(4, '0')}-${pad(value.getUTCMonth() + 1)}-${pad(value.getUTCDate())}`;
    const addDays = (value, amount) => {
      const result = fromIso(value);
      result.setUTCDate(result.getUTCDate() + amount);
      const year = result.getUTCFullYear();
      return year < 1 || year > 9999 ? null : toIso(result);
    };
    const daysBetween = (left, right) => Math.round((fromIso(right) - fromIso(left)) / DAY);
    const isoWeekday = value => fromIso(value).getUTCDay() || 7;
    const fields = value => {
      const parsed = fromIso(value);
      return { year: parsed.getUTCFullYear(), month: parsed.getUTCMonth() + 1, day: parsed.getUTCDate() };
    };
    const locale = () => i18n?.context.locale ?? data.locale;
    const direction = () => i18n?.context.direction ?? getComputedStyle(root).direction ?? data.direction;
    const timeZone = () => i18n?.context.time_zone ?? data.timeZone;
    const formatDate = (value, profile) => i18n
      ? i18n.format.date(fields(value), { format: profile })
      : new Intl.DateTimeFormat(locale(), { ...FALLBACK_OPTIONS[profile], timeZone: 'UTC' }).format(fromIso(value));
    const today = () => {
      const zone = timeZone();
      const now = new Date();
      if (!zone) return `${String(now.getFullYear()).padStart(4, '0')}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
      const parts = Object.fromEntries(new Intl.DateTimeFormat('en-CA-u-ca-gregory-nu-latn', { day: '2-digit', month: '2-digit', timeZone: zone, year: 'numeric' }).formatToParts(now).filter(part => part.type !== 'literal').map(part => [part.type, part.value]));
      return `${String(parts.year).padStart(4, '0')}-${parts.month}-${parts.day}`;
    };
    const localeFirstDay = () => {
      const candidate = new Intl.Locale(locale());
      const info = typeof candidate.getWeekInfo === 'function' ? candidate.getWeekInfo() : candidate.weekInfo;
      return Number.isInteger(info?.firstDay) ? info.firstDay : 7;
    };
    const monthBounds = anchor => {
      const key = formatDate(anchor, PROFILE.heading);
      let start = anchor;
      let end = anchor;
      let guard = 0;
      while (guard < 40) {
        const candidate = addDays(start, -1);
        if (candidate === null || formatDate(candidate, PROFILE.heading) !== key) break;
        start = candidate;
        guard += 1;
      }
      if (guard === 40) throw new Error('[citry-ui] CCalendar could not find a bounded calendar-month start.');
      guard = 0;
      while (guard < 40) {
        const candidate = addDays(end, 1);
        if (candidate === null || formatDate(candidate, PROFILE.heading) !== key) break;
        end = candidate;
        guard += 1;
      }
      if (guard === 40) throw new Error('[citry-ui] CCalendar could not find a bounded calendar-month end.');
      return { start, end, key, count: daysBetween(start, end) + 1 };
    };
    const sameMonth = (left, right) => formatDate(left, PROFILE.heading) === formatDate(right, PROFILE.heading);
    const calendarYear = anchor => {
      const yearKey = formatDate(anchor, PROFILE.year);
      let first = monthBounds(anchor);
      let guard = 0;
      while (guard < 15) {
        const prior = addDays(first.start, -1);
        if (prior === null || formatDate(prior, PROFILE.year) !== yearKey) break;
        first = monthBounds(prior);
        guard += 1;
      }
      if (guard === 15) throw new Error('[citry-ui] CCalendar could not find a bounded calendar-year start.');
      const months = [];
      let candidate = first;
      while (months.length < 15 && formatDate(candidate.start, PROFILE.year) === yearKey) {
        months.push(candidate);
        const after = addDays(candidate.end, 1);
        if (after === null || formatDate(after, PROFILE.year) !== yearKey) break;
        candidate = monthBounds(after);
      }
      if (months.length === 15 && addDays(months.at(-1).end, 1) !== null && formatDate(addDays(months.at(-1).end, 1), PROFILE.year) === yearKey) throw new Error('[citry-ui] CCalendar calendar year exceeds 15 months.');
      const index = Math.max(0, months.findIndex(month => sameMonth(month.start, anchor)));
      return { months, index };
    };
    const hardDisabled = value => configuration.disabled || (configuration.min !== null && value < configuration.min) || (configuration.max !== null && value > configuration.max);
    const unavailable = value => configuration.unavailable.has(value);
    const clampAllowed = value => {
      if (configuration.min !== null && value < configuration.min) return configuration.min;
      if (configuration.max !== null && value > configuration.max) return configuration.max;
      return value;
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
    const resolveUnavailable = () => {
      const requested = props.unavailableDates;
      if (requested === undefined) { resolver.clear('unavailableDates'); return [...data.unavailableDates]; }
      if (!Array.isArray(requested) || requested.length > 4096) { resolver.report('unavailableDates', requested); return previousConstraints.unavailableDates; }
      const normalized = requested.map(canonicalDate);
      if (normalized.some(value => value === null) || new Set(normalized).size !== normalized.length) { resolver.report('unavailableDates', requested); return previousConstraints.unavailableDates; }
      resolver.clear('unavailableDates');
      return normalized;
    };
    const resolveConstraints = () => {
      const min = optionalDate('min', data.min);
      const max = optionalDate('max', data.max);
      const unavailableDates = resolveUnavailable();
      if (min !== null && max !== null && min > max) {
        resolver.report('min/max', { min, max });
        return previousConstraints;
      }
      resolver.clear('min/max');
      previousConstraints = { min, max, unavailableDates };
      return previousConstraints;
    };
    const resolveFirstDay = () => {
      const requested = props.firstDayOfWeek;
      if (requested === undefined) return data.firstDayOfWeek;
      if (requested === null) { resolver.clear('firstDayOfWeek'); return null; }
      if (Number.isInteger(requested) && requested >= 1 && requested <= 7) { resolver.clear('firstDayOfWeek'); return requested; }
      resolver.report('firstDayOfWeek', requested);
      return data.firstDayOfWeek;
    };
    const resolveConfiguration = () => {
      const constraints = resolveConstraints();
      return {
        min: constraints.min,
        max: constraints.max,
        unavailable: new Set(constraints.unavailableDates),
        required: field ? field.required : resolver.boolean('required', data.required),
        disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', data.disabled) || runtime.fieldsetDisabled(input),
        readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.readonly),
        invalid: field ? field.invalid : resolver.boolean('invalid', data.invalid),
        firstDay: resolveFirstDay(),
        showAdjacentDays: resolver.boolean('showAdjacentDays', data.showAdjacentDays),
        fixedWeeks: resolver.boolean('fixedWeeks', data.fixedWeeks),
        variant: resolver.choice('variant', data.variant, ['outline', 'plain']),
        size: resolver.choice('size', data.size, ['sm', 'md', 'lg']),
      };
    };
    const reportFieldOwned = () => {
      if (!field) return;
      ['required', 'disabled', 'readonly', 'invalid'].forEach(name => {
        if (props[name] === undefined) resolver.clear(name);
        else resolver.report(name, props[name], 'ignoring it because the enclosing CField owns this state');
      });
    };
    const syncRelationships = invalid => runtime.relationships([root, input], field, {
      describedby: data.describedby,
      errormessage: data.errormessage,
      control: input,
      required: configuration.required,
      disabled: configuration.disabled,
      readonly: configuration.readonly,
    }, invalid);
    const syncTransport = () => {
      input.value = current ?? '';
      input.min = configuration.min ?? '';
      input.max = configuration.max ?? '';
      input.required = configuration.required;
      input.disabled = configuration.disabled;
      input.readOnly = configuration.readonly;
      input.tabIndex = -1;
      input.setCustomValidity(current !== null && configuration.unavailable.has(current) ? unavailableMessage : '');
    };
    const firstFocusableIn = bounds => {
      for (let value = bounds.start, guard = 0; value !== null && guard < 40; value = addDays(value, 1), guard += 1) {
        if (value > bounds.end) break;
        if (!hardDisabled(value)) return value;
      }
      return null;
    };
    const ensureAnchors = () => {
      const todayValue = today();
      if (visible === null) visible = clampAllowed(current ?? todayValue);
      else visible = clampAllowed(visible);
      const bounds = monthBounds(visible);
      if (focused === null || hardDisabled(focused) || !sameMonth(focused, visible)) {
        focused = current !== null && !hardDisabled(current) && sameMonth(current, visible)
          ? current
          : !hardDisabled(todayValue) && sameMonth(todayValue, visible)
            ? todayValue
            : firstFocusableIn(bounds);
      }
    };
    const render = (focusAfter = false) => owned(() => {
      ensureAnchors();
      const bounds = monthBounds(visible);
      const firstDay = configuration.firstDay ?? localeFirstDay();
      const todayValue = today();
      const invalid = configuration.invalid || nativeInvalid || (current !== null && configuration.unavailable.has(current));
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      root.toggleAttribute('data-disabled', configuration.disabled);
      root.toggleAttribute('data-readonly', configuration.readonly);
      root.toggleAttribute('data-required', configuration.required);
      root.toggleAttribute('data-invalid', invalid);
      root.toggleAttribute('data-empty', current === null);
      root.setAttribute('aria-disabled', configuration.disabled ? 'true' : 'false');
      grid.setAttribute('aria-readonly', configuration.readonly ? 'true' : 'false');
      root.setAttribute('aria-invalid', invalid ? 'true' : 'false');
      heading.textContent = bounds.key;

      const weekdayNodes = [];
      const monday = '2026-08-17';
      for (let index = 0; index < 7; index += 1) {
        const weekday = ((firstDay - 1 + index) % 7) + 1;
        const sample = addDays(monday, weekday - 1);
        const cell = document.createElement('th');
        cell.scope = 'col';
        cell.setAttribute('data-citry-ui-part', 'weekday');
        const abbreviation = document.createElement('abbr');
        abbreviation.textContent = formatDate(sample, PROFILE.weekday);
        abbreviation.title = formatDate(sample, PROFILE.weekdayLong);
        cell.append(abbreviation);
        weekdayNodes.push(cell);
      }
      weekdayRow.replaceChildren(...weekdayNodes);

      const shift = (isoWeekday(bounds.start) - firstDay + 7) % 7;
      const naturalCount = Math.ceil((shift + bounds.count) / 7) * 7;
      const count = configuration.fixedWeeks ? 42 : naturalCount;
      const rows = [];
      for (let rowIndex = 0; rowIndex < count / 7; rowIndex += 1) {
        const row = document.createElement('tr');
        row.setAttribute('data-citry-ui-part', 'week');
        for (let column = 0; column < 7; column += 1) {
          const value = addDays(bounds.start, rowIndex * 7 + column - shift);
          const cell = document.createElement('td');
          cell.setAttribute('data-citry-ui-part', 'day');
          if (value === null) { cell.setAttribute('aria-disabled', 'true'); row.append(cell); continue; }
          const outside = value < bounds.start || value > bounds.end;
          if (outside && !configuration.showAdjacentDays) {
            cell.setAttribute('aria-disabled', 'true');
            cell.setAttribute('data-outside', '');
            row.append(cell);
            continue;
          }
          const isHardDisabled = hardDisabled(value);
          const isUnavailable = unavailable(value);
          const inRange = rangePresentation.start !== null && rangePresentation.end !== null && value >= rangePresentation.start && value <= rangePresentation.end && !isUnavailable;
          cell.dataset.date = value;
          const dateLabel = formatDate(value, PROFILE.label);
          if (rangePresentation.start !== null && value === rangePresentation.start && rangePresentation.startLabel) cell.setAttribute('aria-label', `${rangePresentation.startLabel}: ${dateLabel}`);
          else if (rangePresentation.end !== null && value === rangePresentation.end && rangePresentation.endLabel) cell.setAttribute('aria-label', `${rangePresentation.endLabel}: ${dateLabel}`);
          else cell.setAttribute('aria-label', dateLabel);
          cell.setAttribute('aria-selected', value === current ? 'true' : 'false');
          cell.setAttribute('aria-disabled', isHardDisabled || isUnavailable ? 'true' : 'false');
          if (value === todayValue) cell.setAttribute('aria-current', 'date');
          cell.tabIndex = !isHardDisabled && value === focused ? 0 : -1;
          cell.textContent = formatDate(value, PROFILE.day);
          cell.toggleAttribute('data-selected', value === current);
          cell.toggleAttribute('data-today', value === todayValue);
          cell.toggleAttribute('data-outside', outside);
          cell.toggleAttribute('data-unavailable', isUnavailable);
          cell.toggleAttribute('data-focused', value === focused);
          cell.toggleAttribute('data-in-range', inRange);
          cell.toggleAttribute('data-range-start', rangePresentation.start !== null && value === rangePresentation.start);
          cell.toggleAttribute('data-range-end', rangePresentation.end !== null && value === rangePresentation.end);
          cell.toggleAttribute('data-range-preview', rangePresentation.preview && inRange);
          row.append(cell);
        }
        rows.push(row);
      }
      body.replaceChildren(...rows);
      const previousAnchor = addDays(bounds.start, -1);
      const nextAnchor = addDays(bounds.end, 1);
      previous.disabled = configuration.disabled || previousAnchor === null || (configuration.min !== null && monthBounds(previousAnchor).end < configuration.min);
      next.disabled = configuration.disabled || nextAnchor === null || (configuration.max !== null && monthBounds(nextAnchor).start > configuration.max);
      syncTransport();
      syncRelationships(invalid);
      root.toggleAttribute('data-enhanced', true);
      root.setAttribute('data-citry-calendar-initialized', '');
      if (rangePresentation.accessibleLabel) {
        root.setAttribute('aria-label', rangePresentation.accessibleLabel);
        root.removeAttribute('aria-labelledby');
        input.setAttribute('aria-label', rangePresentation.accessibleLabel);
        input.removeAttribute('aria-labelledby');
      }
      if (focusAfter && focused !== null) body.querySelector(`[data-date="${focused}"]`)?.focus();
    });
    const valueDetail = (value, previousValue, source, sourceEvent) => ({ value, previousValue, controlled: controlledValue, source, sourceEvent });
    const visibleDetail = (value, previousValue, source, sourceEvent) => ({ visibleDate: value, previousVisibleDate: previousValue, controlled: controlledVisible, source, sourceEvent });
    const requestVisible = (value, source, event, focusTarget = null) => {
      const target = clampAllowed(value);
      if (sameMonth(target, visible)) {
        if (focusTarget !== null) focused = focusTarget;
        render(focusTarget !== null);
        return true;
      }
      const prior = visible;
      if (controlledVisible) pendingFocus = focusTarget;
      else { visible = target; focused = focusTarget ?? target; }
      resolver.callback('onVisibleDateChange')?.(target, visibleDetail(target, prior, source, event));
      render(!controlledVisible && focusTarget !== null);
      return !controlledVisible;
    };
    const requestValue = (value, source, event) => {
      if (value === current || hardDisabled(value) || unavailable(value) || configuration.readonly) return false;
      const prior = current;
      if (!controlledValue) current = value;
      resolver.callback('onValueChange')?.(value, valueDetail(value, prior, source, event));
      if (!controlledValue) {
        syncTransport();
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
      if (!sameMonth(value, visible)) requestVisible(value, source, event, value);
      else { focused = value; render(true); }
      return true;
    };
    const moveFocus = (target, source, event) => {
      if (target === null || hardDisabled(target)) return false;
      if (!sameMonth(target, visible)) return requestVisible(target, source, event, target);
      focused = target;
      render(true);
      return true;
    };
    const shiftMonth = (amount, source, event) => {
      const bounds = monthBounds(visible);
      const anchor = amount < 0 ? addDays(bounds.start, -1) : addDays(bounds.end, 1);
      if (anchor === null) return false;
      const targetBounds = monthBounds(anchor);
      const ordinal = focused !== null && focused >= bounds.start && focused <= bounds.end ? daysBetween(bounds.start, focused) : 0;
      const target = addDays(targetBounds.start, Math.min(ordinal, targetBounds.count - 1));
      if (target === null || hardDisabled(clampAllowed(target))) return requestVisible(clampAllowed(target), source, event, clampAllowed(target));
      return requestVisible(target, source, event, target);
    };
    const shiftYear = (amount, source, event) => {
      const year = calendarYear(visible);
      const adjacentAnchor = amount < 0 ? addDays(year.months[0].start, -1) : addDays(year.months.at(-1).end, 1);
      if (adjacentAnchor === null) return false;
      const targetYear = calendarYear(adjacentAnchor);
      const month = targetYear.months[Math.min(year.index, targetYear.months.length - 1)];
      const currentBounds = monthBounds(visible);
      const ordinal = focused !== null && focused >= currentBounds.start && focused <= currentBounds.end ? daysBetween(currentBounds.start, focused) : 0;
      const target = clampAllowed(addDays(month.start, Math.min(ordinal, month.count - 1)));
      return requestVisible(target, source, event, target);
    };
    const clearNativeInvalid = () => {
      if (!nativeInvalid || !input.validity.valid) return;
      nativeInvalid = false;
      field?.setNativeInvalid(false);
    };

    listeners.add(previous, 'click', event => shiftMonth(-1, 'button', event));
    listeners.add(next, 'click', event => shiftMonth(1, 'button', event));
    listeners.add(root, 'citry-ui:calendar-range-presentation', event => {
      if (!(event instanceof CustomEvent)) return;
      event.stopPropagation();
      rangePresentationOwned = true;
      setRangePresentation(event.detail);
    });
    listeners.add(body, 'click', event => {
      const cell = event.target.closest?.('[data-citry-ui-part="day"][data-date]');
      if (!(cell instanceof HTMLTableCellElement) || !body.contains(cell)) return;
      focused = cell.dataset.date;
      if (!requestValue(cell.dataset.date, 'pointer', event)) render(true);
    });
    listeners.add(body, 'focusin', event => {
      const cell = event.target.closest?.('[data-citry-ui-part="day"][data-date]');
      if (cell instanceof HTMLTableCellElement && !hardDisabled(cell.dataset.date)) focused = cell.dataset.date;
    });
    listeners.add(body, 'keydown', event => {
      const cell = event.target.closest?.('[data-citry-ui-part="day"][data-date]');
      if (!(cell instanceof HTMLTableCellElement)) return;
      const value = cell.dataset.date;
      let handled = true;
      if (event.key === 'ArrowLeft') moveFocus(addDays(value, direction() === 'rtl' ? 1 : -1), 'keyboard', event);
      else if (event.key === 'ArrowRight') moveFocus(addDays(value, direction() === 'rtl' ? -1 : 1), 'keyboard', event);
      else if (event.key === 'ArrowUp') moveFocus(addDays(value, -7), 'keyboard', event);
      else if (event.key === 'ArrowDown') moveFocus(addDays(value, 7), 'keyboard', event);
      else if (event.key === 'Home') moveFocus(addDays(value, -((isoWeekday(value) - (configuration.firstDay ?? localeFirstDay()) + 7) % 7)), 'keyboard', event);
      else if (event.key === 'End') moveFocus(addDays(value, 6 - ((isoWeekday(value) - (configuration.firstDay ?? localeFirstDay()) + 7) % 7)), 'keyboard', event);
      else if (event.key === 'PageUp') event.shiftKey ? shiftYear(-1, 'keyboard', event) : shiftMonth(-1, 'keyboard', event);
      else if (event.key === 'PageDown') event.shiftKey ? shiftYear(1, 'keyboard', event) : shiftMonth(1, 'keyboard', event);
      else if (event.key === 'Enter' || event.key === ' ') requestValue(value, 'keyboard', event);
      else handled = false;
      if (handled) event.preventDefault();
    });
    listeners.add(input, 'focus', () => { if (!configuration.disabled) queueMicrotask(() => render(true)); });
    listeners.add(input, 'change', clearNativeInvalid);
    listeners.add(input, 'invalid', event => {
      event.preventDefault();
      nativeInvalid = true;
      field?.setNativeInvalid(true);
      render();
      const token = ++invalidGeneration;
      runtime.invalidFocus(input, root, () => token === invalidGeneration && !configuration.disabled);
      queueMicrotask(() => { if (token === invalidGeneration) render(true); });
    }, true);

    const reset = runtime.registerReset(input, root, {
      reset: event => {
        if (event.defaultPrevented) return;
        nativeInvalid = false;
        field?.setNativeInvalid(false);
        const prior = current;
        if (!controlledValue) current = initialValue;
        if (!controlledVisible) visible = initialVisible || current || today();
        focused = current;
        if (prior !== current) resolver.callback('onValueChange')?.(current, valueDetail(current, prior, 'reset', event));
        render();
      },
      invalidate: () => { invalidGeneration += 1; },
    });
    const stopFieldset = runtime.watchFieldset(input, root, () => {
      configuration = resolveConfiguration();
      render();
    });
    if (i18n && data.catalogUnavailableMessage) unavailableBinding = i18n.bind({
      message: 'citry-ui-calendar-unavailable',
      onChange: text => { unavailableMessage = text; if (ready) render(); },
    });
    const unsubscribe = i18n?.subscribe(() => { if (ready) render(document.activeElement?.matches?.('[data-citry-ui-part="day"]') ?? false); });

    effect(() => {
      reportFieldOwned();
      configuration = resolveConfiguration();
      if (!rangePresentationOwned) setRangePresentation(props);
      const previousValue = current;
      const requestedValue = props.value;
      if (requestedValue === undefined) { controlledValue = false; resolver.clear('value'); }
      else if (requestedValue === null) { controlledValue = true; current = null; resolver.clear('value'); }
      else {
        const normalized = canonicalDate(requestedValue);
        if (normalized === null || hardDisabled(normalized) || unavailable(normalized)) resolver.report('value', requestedValue);
        else { controlledValue = true; current = normalized; resolver.clear('value'); }
      }
      const requestedVisible = props.visibleDate;
      if (requestedVisible === undefined) { controlledVisible = false; resolver.clear('visibleDate'); }
      else {
        const normalized = canonicalDate(requestedVisible);
        if (normalized === null) resolver.report('visibleDate', requestedVisible);
        else {
          controlledVisible = true;
          visible = clampAllowed(normalized);
          if (pendingFocus !== null && sameMonth(pendingFocus, visible)) focused = pendingFocus;
          pendingFocus = null;
          resolver.clear('visibleDate');
        }
      }
      if (current !== previousValue && !controlledVisible && current !== null && !sameMonth(current, visible ?? current)) visible = current;
      clearNativeInvalid();
      ready = true;
      render();
    });
    mutations.start(() => render());

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
        root.removeAttribute('data-enhanced');
        root.removeAttribute('data-citry-calendar-initialized');
        body.replaceChildren();
      });
    };
  },
});
