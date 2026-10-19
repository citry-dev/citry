(function() {

__citryRuntime.registerTypeOptions.bind(null, "CNumberInput_3f8aee", "7fc740d14ba94d58dfcd87e257de8df9cfe3dd5252d1891acfd9332f404d51b5")({
  props: {
    value: {}, min: {}, max: {}, step: {}, required: {}, disabled: {}, readonly: {}, invalid: {},
    showControls: {}, wheel: {}, commitBehavior: {}, placeholder: {}, autocomplete: {},
    variant: {}, size: {}, onValueChange: {}, onInputValueChange: {},
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
    const control = root.querySelector(':scope > [data-citry-ui-part="control"]');
    const input = control?.querySelector(':scope > [data-citry-ui-part="input"]');
    const decrement = control?.querySelector(':scope > [data-citry-ui-part="decrement"]');
    const increment = control?.querySelector(':scope > [data-citry-ui-part="increment"]');
    const transport = root.querySelector(`:scope > #${CSS.escape(data.transportId)}`);
    if (!(control instanceof HTMLElement && input instanceof HTMLInputElement && transport instanceof HTMLInputElement)) {
      throw new Error('[citry-ui] CNumberInput settled anatomy is invalid.');
    }
    const field = component.fieldService;
    const form = component.formService;
    const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
    if (runtime?.generation !== 1) throw new Error('[citry-ui] CNumberInput form-control runtime is unavailable.');
    const resolver = runtime.resolver(root, props, 'CNumberInput');
    const listeners = runtime.listeners();
    const mutations = runtime.mutations(root);
    const owned = mutations.owned;
    let current = data.serverValue;
    let committed = data.serverValue;
    let draft = data.formattedValue;
    let initialValue = data.serverValue;
    let controlled = false;
    let composing = false;
    let dirty = false;
    let nativeInvalid = false;
    let serverLocalized = data.localizedServerValue;
    let generation = 0;
    let validationBinding = null;
    let lastFailure = null;
    let configuration = null;

    const canonical = value => {
      if (value === null) return null;
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
      if (normalized === undefined || normalized === null) return null;
      const negative = normalized.startsWith('-');
      const unsigned = negative ? normalized.slice(1) : normalized;
      const [integer, fraction = ''] = unsigned.split('.');
      return { integer: BigInt(`${negative ? '-' : ''}${integer}${fraction}`), scale: fraction.length };
    };
    const power = count => BigInt(`1${'0'.repeat(count)}`);
    const fromParts = (integer, scale) => {
      const negative = integer < BigInt(0);
      let digits = (negative ? -integer : integer).toString().padStart(scale + 1, '0');
      const text = scale ? `${digits.slice(0, -scale)}.${digits.slice(-scale)}` : digits;
      return canonical(`${negative ? '-' : ''}${text}`);
    };
    // `parts()` returns each `integer` as a BigInt, so `align()` returns two BigInt values and a scale.
    /**
     * @param {{integer: bigint, scale: number}} left
     * @param {{integer: bigint, scale: number}} right
     * @returns {[bigint, bigint, number]}
     */
    const align = (left, right) => {
      const scale = Math.max(left.scale, right.scale);
      return [left.integer * power(scale - left.scale), right.integer * power(scale - right.scale), scale];
    };
    const compare = (leftValue, rightValue) => {
      const [left, right] = align(parts(leftValue), parts(rightValue));
      return left < right ? -1 : left > right ? 1 : 0;
    };
    const add = (leftValue, rightValue, multiplier = 1) => {
      const left = parts(leftValue), right = parts(rightValue);
      const [a, b, scale] = align(left, right);
      return fromParts(a + b * BigInt(multiplier), scale);
    };
    const onGrid = (value, base, step) => {
      const valueParts = parts(value), baseParts = parts(base), stepParts = parts(step);
      const scale = Math.max(valueParts.scale, baseParts.scale, stepParts.scale);
      const amount = valueParts.integer * power(scale - valueParts.scale) - baseParts.integer * power(scale - baseParts.scale);
      const interval = stepParts.integer * power(scale - stepParts.scale);
      return amount % interval === BigInt(0);
    };
    const clamp = value => {
      if (configuration.min !== null && compare(value, configuration.min) < 0) return configuration.min;
      if (configuration.max !== null && compare(value, configuration.max) > 0) return configuration.max;
      return value;
    };
    const format = value => {
      if (value === null) return '';
      return i18n ? i18n.format.number(value, { format: 'citry-ui-number-input' }) : value;
    };
    const parse = text => {
      if (text === '') return { status: 'empty', value: null, reason: null };
      if (i18n) {
        const result = i18n.parse.number(text, { format: 'citry-ui-number-input' });
        return {
          status: result.state,
          value: result.state === 'valid' ? canonical(result.value) : null,
          reason: result.error,
        };
      }
      if (['-', '.', '-.'].includes(text)) return { status: 'incomplete', value: null, reason: 'incomplete' };
      const value = canonical(text);
      return value === undefined
        ? { status: 'invalid', value: null, reason: 'invalid' }
        : { status: 'valid', value, reason: null };
    };
    const replace = (template, key, value) => template.replaceAll(`{${key}}`, String(value));
    const localizedBound = (value, fallback) => value === null ? '' : format(value || fallback);
    const disposeValidationBinding = () => {
      validationBinding?.dispose();
      validationBinding = null;
    };
    const messageFor = (failure, values) => {
      let text = data.messages[failure];
      for (const [key, value] of Object.entries(values)) text = replace(text, key, value);
      return text;
    };
    const bindFailure = (failure, values) => {
      const fingerprint = `${failure ?? ''}:${JSON.stringify(values)}`;
      if (lastFailure === fingerprint && validationBinding !== null) {
        validationBinding.refresh();
        return;
      }
      disposeValidationBinding();
      lastFailure = fingerprint;
      const apply = text => {
        input.setCustomValidity(text);
        applyState();
      };
      if (!failure) {
        input.setCustomValidity('');
        return;
      }
      if (!i18n || !data.catalog[failure]) {
        apply(messageFor(failure, values));
        return;
      }
      if (failure === 'required') validationBinding = i18n.bind({ message: 'citry-ui-number-input-required', onChange: apply });
      else if (failure === 'invalid') validationBinding = i18n.bind({ message: 'citry-ui-number-input-invalid', onChange: apply });
      else if (failure === 'minimum') validationBinding = i18n.bind({ message: 'citry-ui-number-input-minimum', values: () => values, onChange: apply });
      else if (failure === 'maximum') validationBinding = i18n.bind({ message: 'citry-ui-number-input-maximum', values: () => values, onChange: apply });
      else validationBinding = i18n.bind({ message: 'citry-ui-number-input-step', values: () => values, onChange: apply });
    };
    const validity = (text = input.value) => {
      if (configuration.disabled || configuration.readonly) return { failure: null, parsed: parse(text), values: {} };
      const parsed = parse(text);
      if (parsed.status === 'empty') return { failure: configuration.required ? 'required' : null, parsed, values: {} };
      if (parsed.status !== 'valid' || parsed.value === undefined) return { failure: 'invalid', parsed, values: {} };
      if (configuration.min !== null && compare(parsed.value, configuration.min) < 0) {
        return { failure: 'minimum', parsed, values: { min: localizedBound(configuration.min, '') } };
      }
      if (configuration.max !== null && compare(parsed.value, configuration.max) > 0) {
        return { failure: 'maximum', parsed, values: { max: localizedBound(configuration.max, '') } };
      }
      if (!onGrid(parsed.value, configuration.min ?? '0', configuration.step)) {
        return { failure: 'step', parsed, values: { step: localizedBound(configuration.step, '1') } };
      }
      return { failure: null, parsed, values: {} };
    };
    const validate = () => {
      const result = validity();
      bindFailure(result.failure, result.values);
      return result;
    };
    const syncRelationships = invalid => runtime.relationships([input], field, {
      describedby: data.describedby, errormessage: data.errormessage, control: input,
      required: configuration.required, disabled: configuration.disabled, readonly: configuration.readonly,
    }, invalid);
    function applyState() {
      if (!configuration) return;
      const invalid = configuration.invalid || nativeInvalid || !input.validity.valid;
      owned(() => {
        input.required = configuration.required;
        input.disabled = configuration.disabled;
        input.readOnly = configuration.readonly;
        input.placeholder = configuration.placeholder ?? '';
        input.autocomplete = configuration.autocomplete ?? '';
        input.setAttribute('aria-valuemin', configuration.min ?? '');
        input.setAttribute('aria-valuemax', configuration.max ?? '');
        if (configuration.min === null) input.removeAttribute('aria-valuemin');
        if (configuration.max === null) input.removeAttribute('aria-valuemax');
        if (current === null) {
          input.removeAttribute('aria-valuenow');
          input.removeAttribute('aria-valuetext');
        } else {
          input.setAttribute('aria-valuenow', current);
          input.setAttribute('aria-valuetext', format(current));
        }
        transport.name = configuration.disabled ? '' : (data.name ?? '');
        transport.disabled = configuration.disabled || !data.name;
        transport.value = current ?? '';
        if (data.form) transport.setAttribute('form', data.form); else transport.removeAttribute('form');
        if (data.form) input.setAttribute('form', data.form); else input.removeAttribute('form');
        input.name = '';
        decrement && (decrement.disabled = configuration.disabled || configuration.readonly);
        increment && (increment.disabled = configuration.disabled || configuration.readonly);
        decrement?.toggleAttribute('hidden', !configuration.showControls);
        increment?.toggleAttribute('hidden', !configuration.showControls);
        runtime.states(root, {
          empty: current === null, required: configuration.required, disabled: configuration.disabled,
          readonly: configuration.readonly, invalid,
        });
        root.dataset.variant = configuration.variant;
        root.dataset.size = configuration.size;
        syncRelationships(invalid);
      });
    }
    const inputCallback = event => {
      const previous = draft;
      draft = input.value;
      dirty = true;
      serverLocalized = false;
      const result = validate();
      resolver.callback('onInputValueChange')?.(draft, {
        inputValue: draft, previousInputValue: previous, status: result.parsed.status,
        controlled, composing, sourceEvent: event,
      });
    };
    const nativeCommit = () => {
      transport.dispatchEvent(new Event('input', { bubbles: true }));
      transport.dispatchEvent(new Event('change', { bubbles: true }));
    };
    const request = (next, source, sourceEvent, visible = null) => {
      if (next === current) {
        dirty = false;
        draft = visible ?? format(next);
        input.value = draft;
        validate();
        return false;
      }
      const previous = current;
      dirty = false;
      const callback = resolver.callback('onValueChange');
      if (!controlled) {
        current = next;
        committed = next;
        draft = visible ?? format(next);
        input.value = draft;
      }
      callback?.(next, {
        value: next, previousValue: previous, inputValue: visible ?? format(next), controlled, source, sourceEvent,
      });
      if (!controlled) nativeCommit();
      applyState();
      validate();
      return true;
    };
    const commitDraft = (source, event) => {
      const result = validity();
      let next = result.parsed.status === 'valid' ? result.parsed.value : null;
      if (result.failure && configuration.commitBehavior === 'clamp' && next !== null && ['minimum', 'maximum'].includes(result.failure)) {
        next = clamp(next);
      } else if (result.failure) {
        nativeInvalid = true;
        field?.setNativeInvalid(true);
        bindFailure(result.failure, result.values);
        applyState();
        return false;
      }
      nativeInvalid = false;
      field?.setNativeInvalid(false);
      return request(next, source, event);
    };
    const stepValue = (direction, source, event, multiplier = 1) => {
      if (configuration.disabled || configuration.readonly) return;
      const parsed = parse(input.value);
      let base = parsed.status === 'valid' ? parsed.value : current;
      if (base === null) base = configuration.min ?? '0';
      const next = clamp(add(base, configuration.step, direction * multiplier));
      request(next, source, event);
      input.focus({ preventScroll: true });
      input.select();
    };
    const configurationValue = (name, fallback, optional = false, positive = false) => {
      const raw = props[name];
      if (raw === undefined) return fallback;
      if (raw === null && optional) return null;
      const value = canonical(raw);
      if (value === undefined || value === null || (positive && compare(value, '0') <= 0)) {
        resolver.report(name, raw);
        return fallback;
      }
      resolver.clear(name);
      return value;
    };
    const resolveConfiguration = () => {
      const min = configurationValue('min', data.serverMin, true);
      const max = configurationValue('max', data.serverMax, true);
      return {
        min, max, step: configurationValue('step', data.serverStep, false, true),
        required: field ? field.required : resolver.boolean('required', data.serverRequired),
        disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', data.serverDisabled),
        readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.serverReadonly),
        invalid: field ? field.invalid : resolver.boolean('invalid', data.serverInvalid),
        showControls: resolver.boolean('showControls', data.serverShowControls),
        wheel: resolver.boolean('wheel', data.serverWheel),
        commitBehavior: resolver.choice('commitBehavior', data.serverCommitBehavior, ['validate', 'clamp']),
        placeholder: resolver.string('placeholder', data.serverPlaceholder),
        autocomplete: resolver.string('autocomplete', data.serverAutocomplete),
        variant: resolver.choice('variant', data.serverVariant, ['outline', 'filled', 'plain']),
        size: resolver.choice('size', data.serverSize, ['sm', 'md', 'lg']),
      };
    };
    const reset = runtime.registerReset(root, input, {
      reset: () => {
        const next = initialValue;
        if (controlled) {
          resolver.callback('onValueChange')?.(next, {
            value: next, previousValue: current, inputValue: format(next), controlled: true,
            source: 'reset', sourceEvent: null,
          });
        } else {
          current = next; committed = next; dirty = false; draft = format(next); input.value = draft; nativeCommit();
        }
        nativeInvalid = false; field?.setNativeInvalid(false); validate(); applyState();
      },
      invalidate: () => { generation += 1; },
    });
    const stopFieldset = runtime.watchFieldset(root, input, () => { configuration = resolveConfiguration(); applyState(); });

    listeners.add(input, 'focus', () => {
      if (!i18n && serverLocalized) {
        draft = current ?? '';
        input.value = draft;
        serverLocalized = false;
      }
      owned(() => root.toggleAttribute('data-focused', true));
    });
    listeners.add(input, 'blur', event => {
      owned(() => root.removeAttribute('data-focused'));
      if (!composing) commitDraft('blur', event);
    });
    listeners.add(input, 'input', event => inputCallback(event));
    listeners.add(input, 'compositionstart', () => { composing = true; });
    listeners.add(input, 'compositionend', event => { composing = false; inputCallback(event); });
    listeners.add(input, 'keydown', event => {
      if (composing || event.isComposing || event.keyCode === 229) return;
      if (event.key === 'ArrowUp') { event.preventDefault(); stepValue(1, 'increment', event); }
      else if (event.key === 'ArrowDown') { event.preventDefault(); stepValue(-1, 'decrement', event); }
      else if (event.key === 'PageUp') { event.preventDefault(); stepValue(1, 'page', event, 10); }
      else if (event.key === 'PageDown') { event.preventDefault(); stepValue(-1, 'page', event, 10); }
      else if (event.key === 'Home' && configuration.min !== null) { event.preventDefault(); request(configuration.min, 'home', event); }
      else if (event.key === 'End' && configuration.max !== null) { event.preventDefault(); request(configuration.max, 'end', event); }
      else if (event.key === 'Enter') commitDraft('enter', event);
    });
    listeners.add(input, 'wheel', event => {
      if (!configuration.wheel || document.activeElement !== input || event.deltaY === 0) return;
      event.preventDefault();
      stepValue(event.deltaY < 0 ? 1 : -1, 'wheel', event);
    }, { passive: false });
    decrement && listeners.add(decrement, 'pointerdown', event => event.preventDefault());
    increment && listeners.add(increment, 'pointerdown', event => event.preventDefault());
    decrement && listeners.add(decrement, 'click', event => stepValue(-1, 'decrement', event));
    increment && listeners.add(increment, 'click', event => stepValue(1, 'increment', event));
    listeners.add(input, 'invalid', event => {
      event.preventDefault(); nativeInvalid = true; field?.setNativeInvalid(true); validate(); applyState();
      const token = ++generation;
      queueMicrotask(() => { if (token === generation && root.isConnected) input.focus({ preventScroll: true }); });
    }, true);

    let unsubscribe = null;
    if (i18n) unsubscribe = i18n.subscribe(() => {
      if (!dirty && !composing) {
        draft = format(current); input.value = draft;
      }
      validationBinding?.refresh();
      applyState();
    });
    Citry.vue.watchEffect(() => {
      configuration = resolveConfiguration();
      if (configuration.min !== null && configuration.max !== null && compare(configuration.min, configuration.max) > 0) {
        resolver.report('min', configuration.min, 'min cannot exceed max');
        configuration.min = data.serverMin; configuration.max = data.serverMax;
      }
      const requested = props.value;
      if (requested === undefined) {
        if (controlled) { controlled = false; current = committed; draft = format(current); input.value = draft; }
        resolver.clear('value');
      } else {
        const normalized = requested === null ? null : canonical(requested);
        if (normalized === undefined) resolver.report('value', requested);
        else {
          resolver.clear('value'); controlled = true; current = normalized; dirty = false;
          if (!composing) { draft = format(current); input.value = draft; }
        }
      }
      validate(); applyState();
    });
    mutations.start(() => applyState());
    owned(() => root.setAttribute('data-citry-number-input-initialized', ''));

    return () => {
      generation += 1;
      disposeValidationBinding(); unsubscribe?.(); listeners.stop(); mutations.stop(); stopFieldset(); reset();
      if (nativeInvalid) field?.setNativeInvalid(false);
      owned(() => {
        root.removeAttribute('data-citry-number-input-initialized');
        input.name = data.name ?? '';
        transport.name = '';
        transport.disabled = true;
      });
    };
  },
});

})();