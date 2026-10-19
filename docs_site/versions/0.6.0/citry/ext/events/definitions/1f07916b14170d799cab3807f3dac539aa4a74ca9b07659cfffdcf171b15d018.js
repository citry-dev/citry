(function() {

__citryRuntime.registerTypeOptions.bind(null, "CRating_b89f9c", "ea44d440385b423d6b912f141d9b60a73b8d4b9147b6fb6dfae4ce4ddf14727e")({
  props: { value: {}, required: {}, disabled: {}, readonly: {}, invalid: {}, allowClear: {}, variant: {}, size: {}, onValueChange: {}, onHoverChange: {} },
  inject: {
    fieldService: {from: Symbol.for('citry-ui:field'), default: null},
    formService: {from: Symbol.for('citry-ui:form'), default: null},
  },
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component;
    const props = component.$props;
    const i18n = component.$i18n;
    const choices = root.querySelector(':scope > [data-citry-ui-part="choices"]');
    const inputs = Array.from(choices?.querySelectorAll(':scope > [data-citry-ui-part="choice"] > [data-citry-ui-part="input"]') ?? []);
    const labels = Array.from(choices?.querySelectorAll(':scope > [data-citry-ui-part="choice"]') ?? []);
    const choiceLabels = Array.from(choices?.querySelectorAll(':scope > [data-citry-ui-part="choice"] > [data-citry-ui-part="choice-label"]') ?? []);
    const transport = root.querySelector(':scope > [data-citry-ui-part="readonly-transport"]');
    const readonlyValue = root.querySelector(':scope > [data-citry-ui-part="readonly-value"]');
    if (!(choices instanceof HTMLElement) || !(transport instanceof HTMLInputElement) || inputs.length !== data.values.length || inputs.some(input => !(input instanceof HTMLInputElement)) || labels.length !== inputs.length || choiceLabels.length !== inputs.length) throw new Error('[citry-ui] CRating settled anatomy is invalid.');
    const field = component.fieldService;
    const form = component.formService;
    const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
    if (runtime?.generation !== 1) throw new Error('[citry-ui] CRating form-control runtime is unavailable.');
    const resolver = runtime.resolver(root, props, 'CRating');
    const listeners = runtime.listeners();
    const mutations = runtime.mutations(root);
    const owned = mutations.owned;
    let current = data.serverValue;
    let committed = current;
    let initialValue = data.initialValue;
    let controlled = false;
    let hovered = null;
    let configuration = null;
    let interactionSource = 'pointer';
    let bindings = [];

    const canonical = raw => {
      if (raw === null || raw === '0') return null;
      if (typeof raw !== 'string' || !data.values.includes(raw)) return undefined;
      return raw;
    };
    const resolveConfiguration = () => ({
      required: field ? field.required : resolver.boolean('required', data.serverRequired),
      disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', data.serverDisabled) || runtime.fieldsetDisabled(inputs[0]),
      readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.serverReadonly),
      invalid: field ? field.invalid : resolver.boolean('invalid', data.serverInvalid),
      allowClear: resolver.boolean('allowClear', data.serverAllowClear),
      variant: resolver.choice('variant', data.serverVariant, ['solid', 'subtle']),
      size: resolver.choice('size', data.serverSize, ['sm', 'md', 'lg']),
    });
    const ratio = value => `${value === null ? 0 : Number(value) / Number(data.max) * 100}%`;
    const formatLabel = value => {
      const formattedValue = i18n ? i18n.format.number(value, { format: 'citry-ui-rating' }) : value;
      const formattedMax = i18n ? i18n.format.number(data.max, { format: 'citry-ui-rating' }) : data.max;
      return data.valueLabel.replaceAll('{value}', formattedValue).replaceAll('{max}', formattedMax);
    };
    const syncLabels = () => {
      bindings.forEach(binding => binding.dispose());
      bindings = [];
      inputs.forEach((input, index) => {
        if (i18n && data.catalogValueLabel) bindings.push(i18n.bind({
          message: 'citry-ui-rating-value',
          values: () => ({ value: i18n.format.number(input.value, { format: 'citry-ui-rating' }), max: i18n.format.number(data.max, { format: 'citry-ui-rating' }) }),
          onChange: text => {
            choiceLabels[index].textContent = text;
            if (readonlyValue && input.value === current) readonlyValue.textContent = text;
          },
        }));
        else choiceLabels[index].textContent = formatLabel(input.value);
      });
    };
    const syncRelationships = () => runtime.relationships(inputs, field, { describedby: data.describedby, errormessage: data.errormessage }, configuration.invalid);
    const apply = () => owned(() => {
      root.style.setProperty('--_cui-rating-ratio', ratio(hovered ?? current));
      root.style.setProperty('--_cui-rating-committed-ratio', ratio(current));
      root.toggleAttribute('data-hovering', hovered !== null);
      root.toggleAttribute('data-disabled', configuration.disabled);
      root.toggleAttribute('data-readonly', configuration.readonly);
      root.toggleAttribute('data-required', configuration.required);
      root.toggleAttribute('data-invalid', configuration.invalid);
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      root.setAttribute('aria-disabled', configuration.disabled ? 'true' : 'false');
      root.setAttribute('aria-readonly', configuration.readonly ? 'true' : 'false');
      root.setAttribute('aria-invalid', configuration.invalid ? 'true' : 'false');
      if (configuration.readonly && !configuration.disabled) root.tabIndex = 0; else root.removeAttribute('tabindex');
      choices.setAttribute('aria-hidden', configuration.readonly ? 'true' : 'false');
      inputs.forEach((input, index) => {
        input.checked = input.value === current;
        input.defaultChecked = input.value === initialValue;
        input.name = configuration.disabled || configuration.readonly ? '' : (data.name ?? '');
        input.disabled = configuration.disabled || configuration.readonly;
        input.required = configuration.required && !configuration.disabled && !configuration.readonly;
        labels[index].toggleAttribute('data-checked', input.value === current);
        labels[index].toggleAttribute('data-highlighted', hovered !== null && Number(input.value) <= Number(hovered));
      });
      transport.value = current ?? '';
      transport.name = configuration.disabled || !configuration.readonly || current === null ? '' : (data.name ?? '');
      transport.disabled = configuration.disabled || !configuration.readonly || current === null || !data.name;
      if (readonlyValue) {
        const index = inputs.findIndex(input => input.value === current);
        readonlyValue.textContent = current === null ? '' : (choiceLabels[index]?.textContent ?? formatLabel(current));
      }
      syncRelationships();
    });
    const detail = (value, previousValue, source, event) => ({ value, previousValue, controlled, source, sourceEvent: event });
    const notifyHover = (next, event) => {
      if (next === hovered) return;
      const previousValue = hovered;
      hovered = next;
      resolver.callback('onHoverChange')?.(next, { value: next, previousValue, sourceEvent: event });
      apply();
    };
    const request = (next, source, event, nativeAlreadyChanged = false) => {
      if (next === current) return false;
      const previousValue = current;
      if (!controlled) { current = next; committed = next; }
      resolver.callback('onValueChange')?.(next, detail(next, previousValue, source, event));
      apply();
      if (!controlled && !nativeAlreadyChanged) {
        const eventInput = inputs.find(input => input.value === next) ?? inputs.find(input => input.value === previousValue) ?? inputs[0];
        eventInput.dispatchEvent(new Event('input', { bubbles: true }));
        eventInput.dispatchEvent(new Event('change', { bubbles: true }));
      }
      return true;
    };
    inputs.forEach(input => {
      listeners.add(input, 'pointerdown', () => { interactionSource = 'pointer'; });
      listeners.add(input, 'keydown', event => {
        interactionSource = 'keyboard';
        if (configuration.disabled || configuration.readonly) return;
        if (event.key === 'Home' || event.key === 'End') {
          event.preventDefault();
          const target = event.key === 'Home' ? inputs[0] : inputs.at(-1);
          target.focus({ preventScroll: true });
          request(target.value, 'keyboard', event);
        }
      });
      listeners.add(input, 'click', event => {
        if (configuration.disabled || configuration.readonly) { event.preventDefault(); apply(); return; }
        if (configuration.allowClear && input.value === current) {
          event.preventDefault();
          request(null, interactionSource, event);
          setTimeout(() => { if (root.isConnected) apply(); }, 0);
        }
      });
      listeners.add(input, 'change', event => {
        if (!input.checked || configuration.disabled || configuration.readonly) return;
        request(input.value, interactionSource, event, true);
      });
    });
    labels.forEach(label => {
      listeners.add(label, 'pointerenter', event => { if (!configuration.disabled && !configuration.readonly) notifyHover(label.dataset.value ?? null, event); });
    });
    listeners.add(choices, 'pointerleave', event => notifyHover(null, event));
    const reset = runtime.registerReset(root, inputs[0], {
      reset: event => {
        hovered = null;
        if (controlled) resolver.callback('onValueChange')?.(initialValue, detail(initialValue, current, 'reset', event));
        else { current = initialValue; committed = initialValue; apply(); }
      },
      invalidate: () => {},
    });
    const stopFieldset = runtime.watchFieldset(root, inputs[0], () => { configuration = resolveConfiguration(); apply(); });
    Citry.vue.watchEffect(() => {
      configuration = resolveConfiguration();
      const requested = props.value;
      if (requested === undefined) {
        if (controlled) { controlled = false; current = committed; }
        resolver.clear('value');
      } else {
        const normalized = canonical(requested);
        if (normalized === undefined) resolver.report('value', requested);
        else { resolver.clear('value'); controlled = true; current = normalized; }
      }
      if (configuration.disabled || configuration.readonly) hovered = null;
      apply();
    });
    if (data.fieldLabelId) {
      const fieldLabel = root.ownerDocument.getElementById(data.fieldLabelId);
      if (fieldLabel) listeners.add(fieldLabel, 'click', event => queueMicrotask(() => {
        if (!event.defaultPrevented && root.isConnected && !configuration.disabled) (configuration.readonly ? root : inputs.find(input => input.checked) ?? inputs[0]).focus({ preventScroll: true });
      }));
    }
    syncLabels();
    mutations.start(() => apply());
    root.setAttribute('data-citry-rating-initialized', '');
    apply();
    return () => {
      bindings.forEach(binding => binding.dispose());
      listeners.stop(); mutations.stop(); stopFieldset(); reset();
      root.removeAttribute('data-citry-rating-initialized');
    };
  },
});

})();