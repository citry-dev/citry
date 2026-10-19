(function() {

__citryRuntime.registerTypeOptions.bind(null, "CPinInput_d9d8b4", "c8ddd546b6d9c653f3ba1de38de1e632b92c179e406f0dd86e64408758ef7ca2")({
  props: {
    value: {}, required: {}, disabled: {}, readonly: {}, invalid: {}, mask: {},
    variant: {}, size: {}, onValueChange: {}, onComplete: {}, onValueInvalid: {}, onFocusChange: {},
  },
  inject: {
    fieldService: {from: Symbol.for('citry-ui:field'), default: null},
    formService: {from: Symbol.for('citry-ui:form'), default: null},
  },
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component;
    const props = component.$props;
    const input = root.querySelector(':scope > [data-citry-ui-part="input"]');
    const cellsHost = root.querySelector(':scope > [data-citry-ui-part="cells"]');
    const cells = Array.from(cellsHost?.querySelectorAll(':scope > [data-citry-ui-part="cell"]') ?? []);
    const characters = cells.map(cell => cell.querySelector(':scope > [data-citry-ui-part="character"]'));
    if (!(input instanceof HTMLInputElement && cellsHost instanceof HTMLElement) || cells.length !== data.length || characters.some(node => !(node instanceof HTMLElement))) {
      throw new Error('[citry-ui] CPinInput settled anatomy is invalid.');
    }
    const field = component.fieldService;
    const form = component.formService;
    const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
    if (runtime?.generation !== 1) throw new Error('[citry-ui] CPinInput form-control runtime is unavailable.');
    const resolver = runtime.resolver(root, props, 'CPinInput');
    const listeners = runtime.listeners();
    const mutations = runtime.mutations(root);
    const owned = mutations.owned;
    const accepted = data.kind === 'numeric' ? /[0-9]/ : data.kind === 'alphabetic' ? /[A-Za-z]/ : /[A-Za-z0-9]/;
    let current = data.serverValue;
    let committed = data.serverValue;
    const initialValue = data.initialValue;
    let controlled = false;
    let composing = false;
    let focused = false;
    let nativeInvalid = false;
    let pendingSource = 'input';
    let configuration = null;
    let lastComplete = current.length === data.length ? current : null;
    let invalidGeneration = 0;

    const normalize = raw => {
      if (typeof raw !== 'string') return undefined;
      const values = Array.from(raw).filter(character => accepted.test(character));
      return values.slice(0, data.length).join('');
    };
    const exact = raw => {
      const normalized = normalize(raw);
      return normalized !== undefined && normalized === raw ? normalized : undefined;
    };
    const sourceFor = event => {
      const type = event?.inputType ?? '';
      if (pendingSource === 'paste' || type.includes('Paste')) return 'paste';
      if (type === 'insertReplacementText' || type === 'insertFromDrop') return 'autofill';
      if (pendingSource === 'composition' || type.includes('Composition')) return 'composition';
      return 'input';
    };
    const resolveConfiguration = () => ({
      required: field ? field.required : resolver.boolean('required', data.serverRequired),
      disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', data.serverDisabled) || runtime.fieldsetDisabled(input),
      readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.serverReadonly),
      invalid: field ? field.invalid : resolver.boolean('invalid', data.serverInvalid),
      mask: resolver.boolean('mask', data.serverMask),
      variant: resolver.choice('variant', data.serverVariant, ['outline', 'subtle']),
      size: resolver.choice('size', data.serverSize, ['sm', 'md', 'lg']),
    });
    const selectionIndex = () => {
      const start = input.selectionStart ?? current.length;
      if (!focused) return -1;
      return Math.max(0, Math.min(start, data.length - 1));
    };
    const syncRelationships = invalid => runtime.relationships([input], field, {
      label: data.label, labelledby: data.labelledby, describedby: data.describedby,
      errormessage: data.errormessage, control: input,
      required: configuration.required, disabled: configuration.disabled, readonly: configuration.readonly,
    }, invalid);
    const render = () => owned(() => {
      if (input.value !== current && !composing) input.value = current;
      const active = selectionIndex();
      cells.forEach((cell, index) => {
        const filled = index < current.length;
        characters[index].textContent = filled ? (configuration.mask ? '•' : current[index]) : (data.placeholder ?? '');
        cell.toggleAttribute('data-filled', filled);
        cell.toggleAttribute('data-masked', filled && configuration.mask);
        cell.toggleAttribute('data-active', index === active);
      });
      const invalid = configuration.invalid || nativeInvalid;
      runtime.states(root, {
        required: configuration.required, disabled: configuration.disabled, readonly: configuration.readonly,
        invalid, focused, filled: current.length > 0, complete: current.length === data.length,
      });
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      input.required = configuration.required;
      input.disabled = configuration.disabled;
      input.readOnly = configuration.readonly;
      input.pattern = data.pattern;
      input.maxLength = data.length;
      input.inputMode = data.inputmode;
      input.autocomplete = data.autocomplete ?? '';
      input.name = data.name ?? '';
      if (data.form) input.setAttribute('form', data.form); else input.removeAttribute('form');
      syncRelationships(invalid);
    });
    const invalidNotice = (raw, next, source, event) => {
      const rawCharacters = Array.from(raw);
      const rejectedCharacters = rawCharacters.filter(character => !accepted.test(character));
      const acceptedCharacters = rawCharacters.filter(character => accepted.test(character));
      const rejected = rejectedCharacters.join('') + acceptedCharacters.slice(data.length).join('');
      if (!rejected) return;
      resolver.callback('onValueInvalid')?.({ value: next, rejected, source, sourceEvent: event });
    };
    const complete = (next, source, event) => {
      if (next.length !== data.length) { lastComplete = null; return; }
      if (next === lastComplete) return;
      if (!controlled) lastComplete = next;
      resolver.callback('onComplete')?.(next, { value: next, controlled, source, sourceEvent: event });
    };
    const request = (raw, source, event) => {
      const next = normalize(raw);
      if (next === undefined) return false;
      invalidNotice(raw, next, source, event);
      if (next === current) { input.value = current; render(); return false; }
      const previousValue = current;
      if (!controlled) { current = next; committed = next; }
      resolver.callback('onValueChange')?.(next, { value: next, previousValue, controlled, source, sourceEvent: event });
      complete(next, source, event);
      if (controlled) input.value = current;
      nativeInvalid = false;
      field?.setNativeInvalid(false);
      render();
      return true;
    };
    const syncSelection = () => render();
    const selectCell = index => {
      const position = Math.min(index, current.length);
      input.focus({ preventScroll: true });
      if (position < current.length) input.setSelectionRange(position, position + 1, 'forward');
      else input.setSelectionRange(position, position, 'none');
      render();
    };

    const reset = runtime.registerReset(root, input, {
      reset: event => {
        lastComplete = initialValue.length === data.length ? initialValue : null;
        nativeInvalid = false;
        field?.setNativeInvalid(false);
        if (controlled) resolver.callback('onValueChange')?.(initialValue, {
          value: initialValue, previousValue: current, controlled: true, source: 'reset', sourceEvent: event,
        });
        else { current = initialValue; committed = initialValue; input.value = current; }
        render();
      },
      invalidate: () => { invalidGeneration += 1; },
    });
    const stopFieldset = runtime.watchFieldset(root, input, () => { configuration = resolveConfiguration(); render(); });

    listeners.add(input, 'beforeinput', event => {
      pendingSource = event.inputType?.includes('Paste') ? 'paste'
        : event.inputType === 'insertReplacementText' ? 'autofill'
        : event.inputType?.includes('Composition') ? 'composition' : 'input';
    });
    listeners.add(input, 'paste', () => { pendingSource = 'paste'; });
    listeners.add(input, 'compositionstart', () => { composing = true; pendingSource = 'composition'; });
    listeners.add(input, 'compositionend', event => {
      composing = false;
      request(input.value, 'composition', event);
      pendingSource = 'input';
    });
    listeners.add(input, 'input', event => {
      if (composing || event.isComposing) return;
      request(input.value, sourceFor(event), event);
      pendingSource = 'input';
    });
    listeners.add(input, 'select', syncSelection);
    listeners.add(input, 'keyup', syncSelection);
    listeners.add(input, 'focus', event => {
      focused = true;
      render();
      resolver.callback('onFocusChange')?.(true, { focused: true, sourceEvent: event });
    });
    listeners.add(input, 'blur', event => {
      focused = false;
      render();
      resolver.callback('onFocusChange')?.(false, { focused: false, sourceEvent: event });
    });
    listeners.add(input, 'keydown', event => {
      if (composing || event.isComposing || event.keyCode === 229) return;
      if (event.key === 'Home') { event.preventDefault(); input.setSelectionRange(0, current.length ? 1 : 0, 'forward'); render(); }
      else if (event.key === 'End') {
        event.preventDefault();
        const start = current.length >= data.length ? data.length - 1 : current.length;
        input.setSelectionRange(start, start < current.length ? start + 1 : start, 'forward');
        render();
      }
    });
    cells.forEach((cell, index) => listeners.add(cell, 'pointerdown', event => {
      if (configuration.disabled) return;
      event.preventDefault();
      selectCell(index);
    }));
    listeners.add(input, 'invalid', event => {
      event.preventDefault();
      nativeInvalid = true;
      field?.setNativeInvalid(true);
      render();
      const token = ++invalidGeneration;
      runtime.invalidFocus(root, input, () => token === invalidGeneration);
    }, true);

    Citry.vue.watchEffect(() => {
      configuration = resolveConfiguration();
      const requested = props.value;
      if (requested === undefined) {
        if (controlled) { controlled = false; current = committed; input.value = current; }
        resolver.clear('value');
      } else {
        const normalized = exact(requested);
        if (normalized === undefined) resolver.report('value', requested);
        else {
          resolver.clear('value'); controlled = true; current = normalized; input.value = current;
          lastComplete = current.length === data.length ? current : null;
        }
      }
      render();
    });
    mutations.start(() => render());
    owned(() => root.setAttribute('data-citry-pin-input-initialized', ''));
    render();

    return () => {
      invalidGeneration += 1;
      listeners.stop();
      mutations.stop();
      stopFieldset();
      reset();
      if (nativeInvalid) field?.setNativeInvalid(false);
      owned(() => root.removeAttribute('data-citry-pin-input-initialized'));
    };
  },
});

})();