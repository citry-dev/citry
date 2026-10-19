(function() {

__citryRuntime.registerTypeOptions.bind(null, "CForm_4a6900", "aa9f87a157055a1d795daabf8eebf5e0c7365e3a5ae87b28fb027e4fd70504c3")({
  props: {
    disabled: {default: undefined},
    readonly: {default: undefined},
    submitting: {default: undefined},
  },
  data() {
    const component = this;
    return {formService: {
      form: null,
      get disabled() { return component.resolvedDisabled; },
      get readonly() { return component.resolvedReadonly; },
    }};
  },
  computed: {
    resolvedDisabled() { return typeof this.disabled === 'boolean' ? this.disabled : this.serverDisabled; },
    resolvedReadonly() { return typeof this.readonly === 'boolean' ? this.readonly : this.serverReadonly; },
    resolvedSubmitting() { return typeof this.submitting === 'boolean' ? this.submitting : this.serverSubmitting; },
  },
  provide() { return {[Symbol.for('citry-ui:form')]: this.formService}; },
  onServerRender: ({component}) => {
    const form = component.$refs.root;
    if (!(form instanceof HTMLFormElement)) throw new Error('[citry-ui] CForm settled anatomy is invalid.');
    const fieldset = form.querySelector('[data-citry-ui-part="fieldset"]');
    if (!(fieldset instanceof HTMLFieldSetElement)) throw new Error('[citry-ui] CForm fieldset is missing.');
    const invalidEpisodes = new Set();
    const resetTimers = new Set();
    let invalidGeneration = 0;
    let configuration = {
      disabled: component.resolvedDisabled,
      readonly: component.resolvedReadonly,
      submitting: component.resolvedSubmitting,
    };

    const describeValue = (value) => {
      try {
        return JSON.stringify(value) ?? String(value);
      } catch {
        return String(value);
      }
    };
    const reportInvalid = (name, value) => {
      const describedValue = describeValue(value);
      if (invalidEpisodes.has(name)) {
        return;
      }
      invalidEpisodes.add(name);
      console.error(
        `[citry-ui] CForm ${name} received invalid client value ${describedValue}; `
          + "using the server-rendered fallback.",
        form,
      );
    };
    const resolveBoolean = (name) => {
      const value = component[name];
      const fallback = component[`server${name[0].toUpperCase()}${name.slice(1)}`];
      if (value === undefined) return fallback;
      if (typeof value === "boolean") {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return fallback;
    };
    component.formService.form = form;

    const applyConfiguration = (next) => {
      configuration = next;
      fieldset.disabled = next.disabled;
      form.toggleAttribute("data-disabled", next.disabled);
      form.toggleAttribute("data-readonly", next.readonly);
      form.toggleAttribute("data-submitting", next.submitting);
      if (next.submitting) {
        form.setAttribute("aria-busy", "true");
      } else {
        form.removeAttribute("aria-busy");
      }
    };
    const onInvalid = () => {
      invalidGeneration += 1;
      form.setAttribute("data-validation-attempted", "");
    };
    const onReset = (event) => {
      // Reset is cancelable. Wait until every listener has run before
      // clearing Form-owned attempted-validation presentation.
      // Keep one task per event: a later canceled reset must not erase
      // the outcome of an earlier uncanceled reset in the same turn.
      const resetInvalidGeneration = invalidGeneration;
      const timer = setTimeout(() => {
        resetTimers.delete(timer);
        if (event.defaultPrevented || invalidGeneration !== resetInvalidGeneration) {
          return;
        }
        form.removeAttribute("data-validation-attempted");
      }, 0);
      resetTimers.add(timer);
    };
    const onSubmit = (event) => {
      if (!configuration.submitting) {
        return;
      }
      event.preventDefault();
      event.stopImmediatePropagation();
    };

    form.addEventListener("invalid", onInvalid, true);
    form.addEventListener("reset", onReset);
    form.addEventListener("submit", onSubmit, true);
    Citry.vue.watchEffect(() => {
      applyConfiguration({
        disabled: resolveBoolean("disabled"),
        readonly: resolveBoolean("readonly"),
        submitting: resolveBoolean("submitting"),
      });
    });
    form.setAttribute("data-citry-form-initialized", "");

    return () => {
      form.removeEventListener("invalid", onInvalid, true);
      form.removeEventListener("reset", onReset);
      form.removeEventListener("submit", onSubmit, true);
      for (const timer of resetTimers) {
        clearTimeout(timer);
      }
      resetTimers.clear();
      component.formService.form = null;
      form.removeAttribute("data-citry-form-initialized");
    };
  },
});

})();