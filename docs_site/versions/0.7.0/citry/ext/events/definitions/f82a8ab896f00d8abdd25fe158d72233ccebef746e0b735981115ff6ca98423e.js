(function() {

__citryRuntime.registerTypeOptions.bind(null, "CTimeInput_f74743", "05ce7aa9fe88adc75dc7adaa8364e6509fb234ea9fe8bd1397c12011e3ff0ea3")({
  props: {
    value: {}, min: {}, max: {}, step: {}, required: {}, disabled: {}, readonly: {}, invalid: {},
    variant: {}, size: {},
  },
  inject: {
    fieldService: {from: Symbol.for('citry-ui:field'), default: null},
    formService: {from: Symbol.for('citry-ui:form'), default: null},
  },
  onServerRender: ({component}) => {
    const input = component.$el;
    if (!(input instanceof HTMLInputElement) || input.type !== 'time') {
      throw new Error('[citry-ui] CTimeInput settled anatomy is invalid.');
    }
    const data = component;
    const props = component.$props;
    const field = component.fieldService;
    const form = component.formService;
    const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
    if (runtime?.generation !== 1) throw new Error('[citry-ui] CTimeInput form-control runtime is unavailable.');
    const resolver = runtime.resolver(input, props, 'CTimeInput');
    const listeners = runtime.listeners();
    const mutations = runtime.mutations(input);
    const owned = mutations.owned;
    let controlled = false;
    let current = data.serverValue ?? '';
    const initialValue = current;
    let nativeInvalid = false;
    let invalidGeneration = 0;
    let configuration = null;
    let previousConstraints = { min: data.serverMin, max: data.serverMax, step: data.serverStep };

    const canonicalTime = value => {
      if (typeof value !== 'string') return null;
      const match = value.match(/^([0-9]{2}):([0-9]{2})(?::([0-9]{2}))?$/);
      if (match === null) return null;
      const hour = Number(match[1]);
      const minute = Number(match[2]);
      const second = Number(match[3] ?? 0);
      return hour <= 23 && minute <= 59 && second <= 59 ? value : null;
    };
    const optionalTime = (name, fallback) => {
      const value = props[name];
      if (value === undefined) { resolver.clear(name); return fallback; }
      if (value === null) { resolver.clear(name); return null; }
      const valid = canonicalTime(value);
      if (valid !== null) { resolver.clear(name); return valid; }
      resolver.report(name, value);
      return previousConstraints[name];
    };
    const resolveConstraints = () => {
      const minimum = optionalTime('min', data.serverMin);
      const maximum = optionalTime('max', data.serverMax);
      const requestedStep = props.step === undefined ? data.serverStep : props.step;
      const step = Number.isInteger(requestedStep) && requestedStep > 0
        ? requestedStep : previousConstraints.step;
      if (step === requestedStep) resolver.clear('step'); else resolver.report('step', requestedStep);
      previousConstraints = { min: minimum, max: maximum, step };
      return previousConstraints;
    };
    const resolveConfiguration = () => ({
      required: field ? field.required : resolver.boolean('required', data.serverRequired),
      disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', data.serverDisabled) || runtime.fieldsetDisabled(input),
      readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.serverReadonly),
      invalid: field ? field.invalid : resolver.boolean('invalid', data.serverInvalid),
      variant: resolver.choice('variant', data.serverVariant, ['outline', 'filled', 'plain']),
      size: resolver.choice('size', data.serverSize, ['sm', 'md', 'lg']),
      constraints: resolveConstraints(),
    });
    const reportFieldOwned = () => {
      if (!field) return;
      ['required', 'disabled', 'readonly', 'invalid'].forEach(name => {
        if (props[name] === undefined) resolver.clear(name);
        else resolver.report(name, props[name], 'ignoring it because the enclosing CField owns this state');
      });
    };
    const syncRelationships = invalid => runtime.relationships([input], field, {
      describedby: data.describedby,
      errormessage: data.errormessage,
      control: input,
      required: configuration.required,
      disabled: configuration.disabled,
      readonly: configuration.readonly,
    }, invalid);
    const render = () => owned(() => {
      if (input.value !== current) input.value = current;
      const constraints = configuration.constraints;
      runtime.attr(input, 'min', constraints.min);
      runtime.attr(input, 'max', constraints.max);
      input.step = String(constraints.step);
      input.required = configuration.required;
      input.disabled = configuration.disabled;
      input.readOnly = configuration.readonly;
      const invalid = configuration.invalid || nativeInvalid;
      runtime.states(input, {
        required: configuration.required,
        disabled: configuration.disabled,
        readonly: configuration.readonly,
        invalid,
        empty: !current,
      });
      input.dataset.variant = configuration.variant;
      input.dataset.size = configuration.size;
      syncRelationships(invalid);
    });
    const clearNativeInvalid = () => {
      if (!nativeInvalid || !input.validity.valid) return;
      nativeInvalid = false;
      field?.setNativeInvalid(false);
    };
    const onInput = () => {
      const requested = input.value;
      clearNativeInvalid();
      if (controlled) {
        queueMicrotask(() => { if (controlled) render(); });
        return;
      }
      current = requested;
      render();
    };
    const reset = runtime.registerReset(input, input, {
      reset: event => {
        if (event.defaultPrevented) return;
        nativeInvalid = false;
        field?.setNativeInvalid(false);
        if (!controlled) current = initialValue;
        render();
      },
      invalidate: () => { invalidGeneration += 1; },
    });
    const stopFieldset = runtime.watchFieldset(input, input, () => {
      configuration = resolveConfiguration();
      render();
    });

    listeners.add(input, 'input', onInput);
    listeners.add(input, 'change', clearNativeInvalid);
    listeners.add(input, 'invalid', event => {
      event.preventDefault();
      nativeInvalid = true;
      field?.setNativeInvalid(true);
      render();
      const token = ++invalidGeneration;
      runtime.invalidFocus(input, input, () => token === invalidGeneration);
    }, true);
    Citry.vue.watchEffect(() => {
      reportFieldOwned();
      configuration = resolveConfiguration();
      const requested = props.value;
      if (requested === undefined) {
        controlled = false;
        resolver.clear('value');
      } else if (requested === null) {
        controlled = true;
        current = '';
        resolver.clear('value');
      } else {
        const normalized = canonicalTime(requested);
        if (normalized === null) resolver.report('value', requested);
        else { controlled = true; current = normalized; resolver.clear('value'); }
      }
      clearNativeInvalid();
      render();
    });
    mutations.start(() => render());
    owned(() => input.setAttribute('data-citry-time-input-initialized', ''));
    render();

    return () => {
      invalidGeneration += 1;
      listeners.stop();
      mutations.stop();
      stopFieldset();
      reset();
      if (nativeInvalid) field?.setNativeInvalid(false);
      owned(() => input.removeAttribute('data-citry-time-input-initialized'));
    };
  },
});

})();