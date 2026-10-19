(function() {

__citryRuntime.registerTypeOptions.bind(null, "CSlider_27065e", "61946bdb66c99a1bb468b46e313a50efaa0f38fcb6f8c4722c597bf7f96e9d3d")({
  props: {
    value: {}, min: {}, max: {}, step: {}, largeStep: {}, minStepsBetweenThumbs: {},
    disabled: {}, readonly: {}, invalid: {}, orientation: {}, variant: {}, size: {},
    showValue: {}, format: {}, onValueChange: {}, onValueChangeEnd: {},
  },
  inject: {
    fieldService: {from: Symbol.for('citry-ui:field'), default: null},
    formService: {from: Symbol.for('citry-ui:form'), default: null},
  },
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component;
    const props = component.$props;
    const i18n = component.$i18n;
    const nativeInputs = Array.from(root.querySelectorAll(':scope > [data-citry-ui-part="native-input"]'));
    const transports = Array.from(root.querySelectorAll(':scope > [data-citry-ui-part="readonly-transport"]'));
    const control = root.querySelector(':scope > [data-citry-ui-part="control"]');
    const track = control?.querySelector(':scope > [data-citry-ui-part="track"]');
    const fill = track?.querySelector(':scope > [data-citry-ui-part="fill"]');
    const thumbs = Array.from(track?.querySelectorAll(':scope > [data-citry-ui-part="thumb"]') ?? []);
    const expected = data.kind === 'range' ? 2 : 1;
    if (nativeInputs.length !== expected || transports.length !== expected || thumbs.length !== expected || !(control instanceof HTMLElement && track instanceof HTMLElement && fill instanceof HTMLElement) || nativeInputs.some(input => !(input instanceof HTMLInputElement)) || transports.some(input => !(input instanceof HTMLInputElement)) || thumbs.some(thumb => !(thumb instanceof HTMLButtonElement))) {
      throw new Error('[citry-ui] Slider settled anatomy is invalid.');
    }
    const field = component.fieldService;
    const form = component.formService;
    const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
    if (runtime?.generation !== 1) throw new Error('[citry-ui] Slider form-control runtime is unavailable.');
    const resolver = runtime.resolver(root, props, data.kind === 'range' ? 'CRangeSlider' : 'CSlider');
    const listeners = runtime.listeners();
    const mutations = runtime.mutations(root);
    const owned = mutations.owned;
    let current = data.kind === 'range' ? [...data.serverValue] : [data.serverValue];
    let committed = [...current];
    let lastRequested = [...current];
    let initialValue = [...current];
    let controlled = false;
    let configuration = null;
    let activeIndex = 0;
    let lastFocusedIndex = null;
    let dragging = false;
    let changedDuringDrag = false;
    let dragPrevious = null;
    let pendingPointer = null;
    let frame = 0;

    const canonical = value => {
      if (typeof value !== 'string' || !/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$/.test(value)) return undefined;
      let negative = value.startsWith('-');
      let unsigned = negative ? value.slice(1) : value;
      let [integer, fraction = ''] = unsigned.split('.');
      integer = integer.replace(/^0+(?=\d)/, '') || '0';
      fraction = fraction.replace(/0+$/, '');
      let result = integer + (fraction ? `.${fraction}` : '');
      if (negative && result !== '0') result = `-${result}`;
      return result.replace('-', '').replace('.', '').length <= 128 ? result : undefined;
    };
    const parts = value => {
      const normalized = canonical(value);
      if (normalized === undefined) return null;
      const negative = normalized.startsWith('-');
      const unsigned = negative ? normalized.slice(1) : normalized;
      const [integer, fraction = ''] = unsigned.split('.');
      return { integer: BigInt(`${negative ? '-' : ''}${integer}${fraction}`), scale: fraction.length };
    };
    const power = count => BigInt(`1${'0'.repeat(count)}`);
    const fromParts = (integer, scale) => {
      const negative = integer < BigInt(0);
      const digits = (negative ? -integer : integer).toString().padStart(scale + 1, '0');
      const text = scale ? `${digits.slice(0, -scale)}.${digits.slice(-scale)}` : digits;
      return canonical(`${negative ? '-' : ''}${text}`);
    };
    const aligned = values => {
      const parsed = values.map(parts);
      if (parsed.some(value => value === null)) return null;
      const scale = Math.max(...parsed.map(value => value.scale));
      return { values: parsed.map(value => value.integer * power(scale - value.scale)), scale };
    };
    const compare = (left, right) => {
      const result = aligned([left, right]);
      return result.values[0] < result.values[1] ? -1 : result.values[0] > result.values[1] ? 1 : 0;
    };
    const grid = (min, max, step) => {
      const result = aligned([min, max, step]);
      if (!result) return null;
      const [a, b, interval] = result.values;
      const difference = b - a;
      if (a >= b || interval <= BigInt(0) || difference % interval !== BigInt(0)) return null;
      const count = difference / interval;
      if (count <= BigInt(0) || count > BigInt(1000000)) return null;
      return { min: a, max: b, step: interval, count: Number(count), scale: result.scale };
    };
    const indexFor = value => {
      const result = aligned([configuration.min, value, configuration.step]);
      if (!result) return null;
      const [min, item, step] = result.values;
      const difference = item - min;
      if (difference < BigInt(0) || difference % step !== BigInt(0)) return null;
      const index = Number(difference / step);
      return index <= configuration.count ? index : null;
    };
    const valueFor = index => fromParts(configuration.gridMin + configuration.gridStep * BigInt(index), configuration.scale);
    const format = value => i18n ? i18n.format.number(value, { format: configuration.format }) : value;
    const normalizeValue = (raw, fallback) => {
      const value = canonical(raw);
      if (value === undefined) return fallback;
      return indexFor(value) === null ? fallback : value;
    };
    const valuesEqual = (left, right) => left.length === right.length && left.every((value, index) => value === right[index]);
    const boundsFor = index => data.kind === 'range'
      ? index === 0
        ? [0, indexFor(current[1]) - configuration.gap]
        : [indexFor(current[0]) + configuration.gap, configuration.count]
      : [0, configuration.count];
    const clampIndex = (index, thumbIndex) => {
      const [minimum, maximum] = boundsFor(thumbIndex);
      return Math.max(minimum, Math.min(maximum, index));
    };
    const percentFor = value => indexFor(value) / configuration.count * 100;
    const applyGeometry = () => {
      const percentages = current.map(percentFor);
      thumbs.forEach((thumb, index) => thumb.style.setProperty('--_cui-slider-position', `${percentages[index]}%`));
      const start = data.kind === 'range' ? percentages[0] : 0;
      const stop = data.kind === 'range' ? percentages[1] : percentages[0];
      fill.style.setProperty('--_cui-slider-fill-start', `${start}%`);
      fill.style.setProperty('--_cui-slider-fill-stop', `${stop}%`);
    };
    const syncRelationships = () => thumbs.forEach((thumb, index) => runtime.relationships([thumb], field, data.kind === 'range' ? {
      labelledby: data.rangeLabelledby[index], describedby: data.describedby[index], errormessage: data.errormessage[index],
      control: thumb, disabled: configuration.disabled, readonly: configuration.readonly,
    } : {
      label: data.ariaLabel, labelledby: data.ariaLabelledby, describedby: data.describedby[0], errormessage: data.errormessage[0],
      control: thumb, disabled: configuration.disabled, readonly: configuration.readonly,
    }, configuration.invalid));
    const applyState = () => owned(() => {
      root.dataset.orientation = configuration.orientation;
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      root.dataset.showValue = configuration.showValue;
      root.toggleAttribute('data-disabled', configuration.disabled);
      root.toggleAttribute('data-readonly', configuration.readonly);
      root.toggleAttribute('data-invalid', configuration.invalid);
      root.toggleAttribute('data-dragging', dragging);
      current.forEach((value, index) => {
        const native = nativeInputs[index];
        const transport = transports[index];
        const thumb = thumbs[index];
        native.min = configuration.min;
        native.max = configuration.max;
        native.step = configuration.step;
        native.value = value;
        native.name = configuration.disabled || configuration.readonly ? '' : (data.names[index] ?? '');
        native.disabled = configuration.disabled || configuration.readonly || !data.names[index];
        native.tabIndex = -1;
        transport.value = value;
        transport.name = configuration.disabled || !configuration.readonly ? '' : (data.names[index] ?? '');
        transport.disabled = configuration.disabled || !configuration.readonly || !data.names[index];
        thumb.disabled = configuration.disabled;
        thumb.setAttribute('aria-readonly', configuration.readonly ? 'true' : 'false');
        thumb.setAttribute('aria-valuenow', value);
        thumb.setAttribute('aria-valuetext', format(value));
        const [allowedMin, allowedMax] = boundsFor(index);
        thumb.setAttribute('aria-valuemin', valueFor(allowedMin));
        thumb.setAttribute('aria-valuemax', valueFor(allowedMax));
        thumb.setAttribute('aria-invalid', configuration.invalid ? 'true' : 'false');
        if (configuration.orientation === 'vertical') thumb.setAttribute('aria-orientation', 'vertical');
        else thumb.removeAttribute('aria-orientation');
        const bubble = thumb.querySelector(':scope > [data-citry-ui-part="value"]');
        if (bubble) {
          bubble.textContent = format(value);
          bubble.hidden = configuration.showValue === 'never';
        }
        thumb.toggleAttribute('data-active', activeIndex === index && (dragging || document.activeElement === thumb));
      });
      syncRelationships();
      applyGeometry();
    });
    const nativeEvents = (index, phase) => {
      nativeInputs[index].dispatchEvent(new Event(phase === 'change' ? 'input' : 'change', { bubbles: true }));
    };
    const detail = (next, previous, source, event, phase, index) => {
      const result = { value: data.kind === 'range' ? [...next] : next[0], previousValue: data.kind === 'range' ? [...previous] : previous[0], controlled, source, sourceEvent: event, phase };
      if (data.kind === 'range') result.activeThumb = index === 0 ? 'lower' : 'upper';
      return result;
    };
    const request = (next, index, source, event, phase = 'change') => {
      if (valuesEqual(next, controlled ? lastRequested : current)) return null;
      const previous = [...current];
      lastRequested = [...next];
      if (!controlled) {
        current = [...next];
        committed = [...next];
      }
      resolver.callback(phase === 'change' ? 'onValueChange' : 'onValueChangeEnd')?.(data.kind === 'range' ? [...next] : next[0], detail(next, previous, source, event, phase, index));
      if (!controlled) nativeEvents(index, phase);
      applyState();
      return { previous, next: [...next] };
    };
    const changeIndex = (nextIndex, index, source, event) => {
      const bounded = clampIndex(nextIndex, index);
      const next = [...current];
      next[index] = valueFor(bounded);
      return request(next, index, source, event, 'change');
    };
    const end = (index, source, event, previous, next = current) => {
      if (!previous || valuesEqual(previous, next)) return false;
      resolver.callback('onValueChangeEnd')?.(data.kind === 'range' ? [...next] : next[0], detail(next, previous, source, event, 'end', index));
      if (!controlled) nativeEvents(index, 'end');
      else lastRequested = [...current];
      return true;
    };
    const pointerRatio = event => {
      const rect = track.getBoundingClientRect();
      if (configuration.orientation === 'vertical') return Math.max(0, Math.min(1, (rect.bottom - event.clientY) / rect.height));
      const raw = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
      return getComputedStyle(root).direction === 'rtl' ? 1 - raw : raw;
    };
    const pointerIndex = event => Math.round(pointerRatio(event) * configuration.count);
    const chooseThumb = (index, event) => {
      if (data.kind !== 'range') return 0;
      const target = event.target.closest?.('[data-citry-ui-part="thumb"]');
      const direct = thumbs.indexOf(target);
      if (direct >= 0) return direct;
      const distances = current.map(value => Math.abs(indexFor(value) - index));
      if (distances[0] !== distances[1]) return distances[0] < distances[1] ? 0 : 1;
      if (lastFocusedIndex !== null) return lastFocusedIndex;
      return index >= indexFor(current[0]) ? 1 : 0;
    };
    const flushPointer = event => {
      if (!event) return;
      changedDuringDrag = Boolean(changeIndex(pointerIndex(event), activeIndex, 'pointer', event)) || changedDuringDrag;
    };
    const queuePointer = event => {
      pendingPointer = event;
      if (frame) return;
      frame = requestAnimationFrame(() => { frame = 0; const pending = pendingPointer; pendingPointer = null; flushPointer(pending); });
    };
    listeners.add(control, 'pointerdown', event => {
      if (configuration.disabled || configuration.readonly || event.button !== 0) return;
      const index = pointerIndex(event);
      activeIndex = chooseThumb(index, event);
      lastFocusedIndex = activeIndex;
      dragging = true;
      changedDuringDrag = false;
      dragPrevious = [...current];
      lastRequested = [...current];
      control.setPointerCapture(event.pointerId);
      thumbs[activeIndex].focus({ preventScroll: true });
      event.preventDefault();
      changedDuringDrag = Boolean(changeIndex(index, activeIndex, 'pointer', event)) || changedDuringDrag;
      applyState();
    });
    listeners.add(control, 'pointermove', event => { if (dragging && control.hasPointerCapture(event.pointerId)) queuePointer(event); });
    const stopPointer = event => {
      if (!dragging) return;
      if (frame) { cancelAnimationFrame(frame); frame = 0; flushPointer(pendingPointer); pendingPointer = null; }
      dragging = false;
      if (control.hasPointerCapture(event.pointerId)) control.releasePointerCapture(event.pointerId);
      if (changedDuringDrag) end(activeIndex, 'pointer', event, dragPrevious, lastRequested);
      dragPrevious = null;
      applyState();
    };
    listeners.add(control, 'pointerup', stopPointer);
    listeners.add(control, 'pointercancel', stopPointer);
    thumbs.forEach((thumb, index) => {
      listeners.add(thumb, 'focus', () => { activeIndex = index; lastFocusedIndex = index; applyState(); });
      listeners.add(thumb, 'blur', () => applyState());
      listeners.add(thumb, 'keydown', event => {
        if (configuration.disabled || configuration.readonly) return;
        let nextIndex = indexFor(current[index]);
        if (event.key === 'ArrowRight' || event.key === 'ArrowUp') nextIndex += 1;
        else if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') nextIndex -= 1;
        else if (event.key === 'PageUp') nextIndex += configuration.largeSteps;
        else if (event.key === 'PageDown') nextIndex -= configuration.largeSteps;
        else if (event.key === 'Home') nextIndex = boundsFor(index)[0];
        else if (event.key === 'End') nextIndex = boundsFor(index)[1];
        else return;
        event.preventDefault();
        const previous = [...current];
        const requested = changeIndex(nextIndex, index, 'keyboard', event);
        if (requested) end(index, 'keyboard', event, previous, requested.next);
      });
    });
    const reset = runtime.registerReset(root, nativeInputs[0], {
      reset: () => {
        const previous = [...current];
        if (controlled) {
          resolver.callback('onValueChange')?.(data.kind === 'range' ? [...initialValue] : initialValue[0], detail(initialValue, previous, 'reset', null, 'change', 0));
          resolver.callback('onValueChangeEnd')?.(data.kind === 'range' ? [...initialValue] : initialValue[0], detail(initialValue, previous, 'reset', null, 'end', 0));
        } else {
          current = [...initialValue]; committed = [...initialValue]; lastRequested = [...initialValue]; applyState(); nativeInputs.forEach((_, index) => { nativeEvents(index, 'change'); nativeEvents(index, 'end'); });
        }
      },
      invalidate: () => {},
    });
    const stopFieldset = runtime.watchFieldset(root, nativeInputs[0], () => { configuration = resolveConfiguration(); if (dragging && configuration.disabled) dragging = false; applyState(); });
    const configValue = (name, fallback) => {
      const raw = props[name];
      if (raw === undefined) return fallback;
      const value = canonical(raw);
      if (value === undefined) { resolver.report(name, raw); return fallback; }
      resolver.clear(name); return value;
    };
    const resolveConfiguration = () => {
      let min = configValue('min', data.serverMin), max = configValue('max', data.serverMax), step = configValue('step', data.serverStep);
      let exactGrid = grid(min, max, step);
      if (!exactGrid) { resolver.report('min', min, 'min/max/step must form a finite whole-step grid'); min = data.serverMin; max = data.serverMax; step = data.serverStep; exactGrid = grid(min, max, step); }
      const largeStep = configValue('largeStep', data.serverLargeStep);
      const largeIndex = (() => { const result = aligned([largeStep, step]); return result && result.values[0] > BigInt(0) && result.values[0] % result.values[1] === BigInt(0) ? Number(result.values[0] / result.values[1]) : null; })();
      let gap = 0;
      if (data.kind === 'range') {
        const requestedGap = props.minStepsBetweenThumbs;
        if (requestedGap === undefined) {
          gap = data.serverMinStepsBetweenThumbs;
          resolver.clear('minStepsBetweenThumbs');
        } else if (Number.isInteger(requestedGap) && requestedGap >= 0 && requestedGap <= exactGrid.count) {
          gap = requestedGap;
          resolver.clear('minStepsBetweenThumbs');
        } else {
          gap = data.serverMinStepsBetweenThumbs;
          resolver.report('minStepsBetweenThumbs', requestedGap);
        }
      }
      return {
        min, max, step, count: exactGrid.count, gridMin: exactGrid.min, gridStep: exactGrid.step, scale: exactGrid.scale,
        largeSteps: largeIndex ?? Math.min(10, exactGrid.count), gap,
        disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', data.serverDisabled),
        readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.serverReadonly),
        invalid: field ? field.invalid : resolver.boolean('invalid', data.serverInvalid),
        orientation: resolver.choice('orientation', data.serverOrientation, ['horizontal', 'vertical']),
        variant: resolver.choice('variant', data.serverVariant, ['solid', 'subtle']),
        size: resolver.choice('size', data.serverSize, ['sm', 'md', 'lg']),
        showValue: resolver.choice('showValue', data.serverShowValue, ['never', 'interaction', 'always']),
        format: resolver.string('format', data.serverFormat) || data.serverFormat,
      };
    };
    let unsubscribe = null;
    Citry.vue.watchEffect(() => {
      const previousConfiguration = configuration;
      configuration = resolveConfiguration();
      if (previousConfiguration && dragging && (configuration.min !== previousConfiguration.min || configuration.max !== previousConfiguration.max || configuration.step !== previousConfiguration.step || configuration.orientation !== previousConfiguration.orientation || configuration.disabled || configuration.readonly)) {
        dragging = false; changedDuringDrag = false; dragPrevious = null;
      }
      const requested = props.value;
      if (requested === undefined) {
        if (controlled) { controlled = false; current = [...committed]; lastRequested = [...current]; }
        resolver.clear('value');
      } else {
        const raw = data.kind === 'range' ? requested : [requested];
        if (!Array.isArray(raw) || raw.length !== expected) resolver.report('value', requested);
        else {
          const normalized = raw.map((value, index) => normalizeValue(value, current[index]));
          const indices = normalized.map(indexFor);
          const validRange = data.kind !== 'range' || indices[1] - indices[0] >= configuration.gap;
          if (indices.some(index => index === null) || !validRange) resolver.report('value', requested);
          else { resolver.clear('value'); controlled = true; current = normalized; lastRequested = [...normalized]; }
        }
      }
      applyState();
    });
    if (i18n) unsubscribe = i18n.subscribe(() => applyState());
    if (data.kind === 'range' && data.fieldLabelId) {
      const label = root.ownerDocument.getElementById(data.fieldLabelId);
      if (label) listeners.add(label, 'click', event => queueMicrotask(() => {
        if (!event.defaultPrevented && root.isConnected && !configuration.disabled) thumbs[0].focus({ preventScroll: true });
      }));
    }
    mutations.start(() => applyState());
    owned(() => { control.hidden = false; root.setAttribute('data-enhanced', ''); root.setAttribute('data-citry-slider-initialized', ''); });
    applyState();
    return () => {
      if (frame) cancelAnimationFrame(frame);
      unsubscribe?.(); listeners.stop(); mutations.stop(); stopFieldset(); reset();
      owned(() => { control.hidden = true; root.removeAttribute('data-enhanced'); root.removeAttribute('data-citry-slider-initialized'); });
    };
  },
});

})();