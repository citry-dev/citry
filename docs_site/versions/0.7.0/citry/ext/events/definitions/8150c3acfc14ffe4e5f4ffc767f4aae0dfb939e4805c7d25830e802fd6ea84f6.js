(function() {

// Page markup can hide a document's or form's members behind named elements. The core runtime's helper
// reads the built-in ones; Citry before 0.7.0 have no helper, so the fallback reads members directly.
const builtIn = globalThis[Symbol.for("citry:built-in-members")] ?? (target => target);

__citryRuntime.registerTypeOptions.bind(null, "CForm_4a6900", "f8280dae15c14a4e25c441f3950e7bd61524bfabe4ee6b534a7ee11462f9cf5e")({
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
    const fieldset = builtIn(form).querySelector('[data-citry-ui-part="fieldset"]');
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
      builtIn(form).toggleAttribute("data-disabled", next.disabled);
      builtIn(form).toggleAttribute("data-readonly", next.readonly);
      builtIn(form).toggleAttribute("data-submitting", next.submitting);
      if (next.submitting) {
        builtIn(form).setAttribute("aria-busy", "true");
      } else {
        builtIn(form).removeAttribute("aria-busy");
      }
    };
    const onInvalid = () => {
      invalidGeneration += 1;
      builtIn(form).setAttribute("data-validation-attempted", "");
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
        builtIn(form).removeAttribute("data-validation-attempted");
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

    builtIn(form).addEventListener("invalid", onInvalid, true);
    builtIn(form).addEventListener("reset", onReset);
    builtIn(form).addEventListener("submit", onSubmit, true);
    Citry.vue.watchEffect(() => {
      applyConfiguration({
        disabled: resolveBoolean("disabled"),
        readonly: resolveBoolean("readonly"),
        submitting: resolveBoolean("submitting"),
      });
    });
    builtIn(form).setAttribute("data-citry-form-initialized", "");

    return () => {
      builtIn(form).removeEventListener("invalid", onInvalid, true);
      builtIn(form).removeEventListener("reset", onReset);
      builtIn(form).removeEventListener("submit", onSubmit, true);
      for (const timer of resetTimers) {
        clearTimeout(timer);
      }
      resetTimers.clear();
      component.formService.form = null;
      builtIn(form).removeAttribute("data-citry-form-initialized");
    };
  },
});

})();