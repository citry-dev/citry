(function() {

__citryRuntime.registerTypeOptions.bind(null, "CStepper_da83ea", "705c6821321a1876390b0bcd20d3b083ba3c6564c46232322e907e6aaca51acb")({
  props: {active: {}, linear: {}, disabled: {}, orientation: {}, variant: {}, size: {}, onActiveChange: {}},
  onServerRender: ({component}) => {
    const root = component.$refs.stepperRoot.$el;
    const data = component.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const stepSelector = ':scope > [data-citry-ui-part="list"] > [data-citry-ui-part="step"]';
    const invalidEpisodes = new Set();
    const prior = root.__citryUiStepperRuntime;
    let committed = prior && prior.serverActive === data.active ? prior.committed : data.active;
    let current = committed;
    let controlled = false;
    let callback = null;
    let configuration = {
      linear: data.linear,
      disabled: data.disabled,
      orientation: data.orientation,
      variant: data.variant,
      size: data.size,
    };
    let generation = 0;
    let task = null;
    let structureValid = false;

    const report = (name, value) => {
      if (invalidEpisodes.has(name)) return;
      invalidEpisodes.add(name);
      console.error(`[citry-ui] CStepper ${name} received invalid client value`, value);
    };
    const resolveBoolean = (name, fallback) => {
      const supplied = props[name];
      if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
      if (typeof supplied === 'boolean') { invalidEpisodes.delete(name); return supplied; }
      report(name, supplied);
      return fallback;
    };
    const resolveChoice = (name, fallback, allowed) => {
      const supplied = props[name];
      if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
      if (typeof supplied === 'string' && allowed.includes(supplied)) {
        invalidEpisodes.delete(name);
        return supplied;
      }
      report(name, supplied);
      return fallback;
    };
    const steps = () => [...root.querySelectorAll(stepSelector)];
    const trigger = (step) => step.querySelector(':scope > [data-citry-ui-part="trigger"]');
    const invalidStructure = (entries) => {
      if (entries.length < 2) return `expected at least two Steps, got ${entries.length}`;
      for (const [index, step] of entries.entries()) {
        if (Number(step.dataset.index) !== index) return 'Step indices do not match settled order';
        const control = trigger(step);
        if (!(control instanceof Element)) return `Step ${index} has no owned trigger`;
        const nested = control.querySelector(
          'a[href], button, input, select, textarea, '
          + '[contenteditable]:not([contenteditable="false"]), [tabindex]'
        );
        if (nested) return `Step ${index} label contains an interactive descendant`;
      }
      return null;
    };
    const normalizeFailed = (entries) => {
      root.removeAttribute('data-citry-stepper-initialized');
      entries.forEach((step) => {
        const control = trigger(step);
        if (control instanceof HTMLButtonElement) control.disabled = true;
      });
    };
    const sync = () => {
      const entries = steps();
      const problem = invalidStructure(entries);
      if (problem) {
        structureValid = false;
        report('structure', problem);
        normalizeFailed(entries);
        return;
      }
      invalidEpisodes.delete('structure');
      structureValid = true;
      if (!Number.isInteger(committed) || committed < 0 || committed >= entries.length) {
        committed = Math.max(0, Math.min(entries.length - 1, Number.isInteger(committed) ? committed : 0));
      }
      let requested = props.active;
      if (requested === null) requested = undefined;
      if (requested === undefined) {
        invalidEpisodes.delete('active');
        if (controlled) committed = current;
        controlled = false;
        current = committed;
      } else if (Number.isInteger(requested) && requested >= 0 && requested < entries.length) {
        invalidEpisodes.delete('active');
        controlled = true;
        current = requested;
      } else {
        report('active', requested);
        controlled = true;
        current = committed;
      }
      root.dataset.active = String(current);
      root.dataset.orientation = configuration.orientation;
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      root.toggleAttribute('data-linear', configuration.linear);
      root.toggleAttribute('data-disabled', configuration.disabled);
      entries.forEach((step, index) => {
        const control = trigger(step);
        const state = index < current ? 'complete' : index === current ? 'current' : 'upcoming';
        const ownDisabled = step.hasAttribute('data-own-disabled');
        const unavailable = configuration.disabled || ownDisabled || (configuration.linear && index > current);
        step.dataset.state = state;
        step.toggleAttribute('data-disabled', unavailable || (control.matches?.(':disabled') ?? false));
        control.toggleAttribute('aria-current', index === current);
        if (index === current) control.setAttribute('aria-current', 'step');
        if (control instanceof HTMLButtonElement) control.disabled = unavailable;
      });
      root.setAttribute('data-citry-stepper-initialized', '');
      root.__citryUiStepperRuntime = {serverActive: data.active, committed};
    };
    const schedule = () => {
      if (task !== null) return;
      const scheduled = generation;
      task = setTimeout(() => {
        task = null;
        if (scheduled === generation) sync();
      }, 0);
    };
    const onClick = (event) => {
      if (!structureValid) return;
      const control = event.composedPath().find(
        (node) => node instanceof Element && node.matches?.('[data-citry-ui-part="trigger"]')
      );
      if (!(control instanceof HTMLButtonElement) || control.disabled || control.matches(':disabled')) return;
      const step = control.closest('[data-citry-ui-part="step"]');
      if (!step || step.closest('[data-citry-ui-part="stepper"]') !== root) return;
      const next = Number(step.dataset.index);
      if (!Number.isInteger(next) || next === current) return;
      const previousActive = current;
      callback?.(next, {active: next, previousActive, controlled, step, sourceEvent: event});
      if (!controlled) { committed = next; current = next; sync(); }
      else schedule();
    };
    const observer = new MutationObserver((records) => {
      if (records.every((record) => record.attributeName === 'disabled'
          && record.target instanceof HTMLButtonElement)) return;
      schedule();
    });
    observer.observe(root, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ['contenteditable', 'href', 'tabindex', 'type'],
    });
    const fieldsets = [];
    for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
      if (!(ancestor instanceof HTMLFieldSetElement)) continue;
      const item = new MutationObserver(schedule);
      item.observe(ancestor, {attributes: true, childList: true, attributeFilter: ['disabled']});
      fieldsets.push(item);
    }
    root.addEventListener('click', onClick);
    const stop = effect(() => {
      callback = typeof props.onActiveChange === 'function' ? props.onActiveChange : null;
      configuration = {
        linear: resolveBoolean('linear', data.linear),
        disabled: resolveBoolean('disabled', data.disabled),
        orientation: resolveChoice('orientation', data.orientation, ['horizontal', 'vertical']),
        variant: resolveChoice('variant', data.variant, ['plain', 'soft', 'outline']),
        size: resolveChoice('size', data.size, ['sm', 'md', 'lg']),
      };
      schedule();
    });
    schedule();
    return () => {
      generation += 1;
      if (task !== null) clearTimeout(task);
      root.__citryUiStepperRuntime = {serverActive: data.active, committed};
      stop?.();
      observer.disconnect();
      fieldsets.forEach((item) => item.disconnect());
      root.removeEventListener('click', onClick);
      root.removeAttribute('data-citry-stepper-initialized');
    };
  },
})

})();