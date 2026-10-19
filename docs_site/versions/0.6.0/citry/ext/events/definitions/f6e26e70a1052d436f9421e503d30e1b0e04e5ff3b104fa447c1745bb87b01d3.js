(function() {

__citryRuntime.registerTypeOptions.bind(null, "CField_81c723", "1dec0331aecda775ebb3bd36e3634528d7310d1f0e5d08335dee941a2044c3ae")({
  props: {
    required: {},
    disabled: {},
    readonly: {},
    invalid: {},
    orientation: {},
    density: {},
  },
  inject: {
    formService: {from: Symbol.for("citry-ui:form"), default: null},
  },
  data() {
    const component = this;
    const service = Citry.vue.reactive({
      get controlId() { return component.controlId; },
      get descriptionId() { return component.descriptionId; },
      get errorId() { return component.errorId; },
      get hasDescription() { return component.hasDescription; },
      get hasError() { return component.hasError; },
      required: this.serverRequired,
      disabled: this.serverDisabled,
      readonly: this.serverReadonly,
      invalid: this.serverInvalid,
      nativeInvalid: false,
      supportsRequired: true,
      supportsReadonly: true,
      capabilityGeneration: 0,
      activeCapabilityGeneration: null,
      registerCapabilities(capabilities) {
        const generation = ++service.capabilityGeneration;
        service.activeCapabilityGeneration = generation;
        service.supportsRequired = capabilities.required !== false;
        service.supportsReadonly = capabilities.readonly !== false;
        return () => {
          if (service.activeCapabilityGeneration !== generation) return;
          service.activeCapabilityGeneration = null;
          service.supportsRequired = true;
          service.supportsReadonly = true;
        };
      },
      setNativeInvalid(value) { service.nativeInvalid = Boolean(value); },
    });
    return {fieldService: service};
  },
  provide() { return {[Symbol.for("citry-ui:field")]: this.fieldService}; },
  onServerRender: ({component}) => {
    const root = component.$el;
    if (!(root instanceof HTMLDivElement) || !root.hasAttribute("data-citry-field-root"))
      throw new Error("[citry-ui] CField settled anatomy is invalid.");
    const data = component;
    const props = component.$props;
    const requiredIndicator = root.querySelector(
      ':scope > [data-citry-ui-part="label"] > [data-citry-ui-part="required-indicator"]',
    );
    // Controls may expose parts with the same public names. Restrict the
    // lookup to this Field's direct status node so nested component
    // internals are never mistaken for Field-owned UI.
    const error = root.querySelector(':scope > [data-citry-ui-part="error"]');
    const controls = root.querySelectorAll('[data-citry-field-control]');
    if (controls.length !== 1) {
      throw new Error(
        `[citry-ui] CField requires exactly one marked control, but found ${controls.length}.`,
      );
    }
    const control = controls[0];
    const initialSupportsRequired = control.getAttribute(
      "data-citry-field-supports-required",
    ) !== "false";
    const initialSupportsReadonly = control.getAttribute(
      "data-citry-field-supports-readonly",
    ) !== "false";
    const form = component.formService;
    const allowedValues = {
      orientation: ["vertical", "horizontal"],
      density: ["default", "comfortable", "compact"],
    };
    const invalidEpisodes = new Map();
    let externalInvalid = data.serverInvalid;

    const describeValue = (value) => {
      try {
        return JSON.stringify(value) ?? String(value);
      } catch {
        return String(value);
      }
    };
    const reportInvalid = (name, value) => {
      const describedValue = describeValue(value);
      const fingerprint = `${typeof value}:${describedValue}`;
      if (invalidEpisodes.get(name) === fingerprint) {
        return;
      }
      invalidEpisodes.set(name, fingerprint);
      console.error(
        `[citry-ui] CField ${name} received invalid client value ${describedValue}; `
          + "using the server-rendered fallback.",
        root,
      );
    };
    const reportUnsupported = (name) => {
      const episode = `capability:${name}`;
      const fingerprint = "unsupported:true";
      if (invalidEpisodes.get(episode) === fingerprint) {
        return;
      }
      invalidEpisodes.set(episode, fingerprint);
      console.error(
        `[citry-ui] CField ${name}=true is not supported by its registered control; using false.`,
        root,
      );
    };
    const resolveBoolean = (name, fallback) => {
      const value = props[name] === undefined ? fallback : props[name];
      if (typeof value === "boolean") {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return fallback;
    };
    const resolveChoice = (name) => {
      const fallback = data[`server${name[0].toUpperCase()}${name.slice(1)}`];
      const value = props[name] === undefined ? fallback : props[name];
      if (allowedValues[name].includes(value)) {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return data[`server${name[0].toUpperCase()}${name.slice(1)}`];
    };
    const context = component.fieldService;
    context.supportsRequired = initialSupportsRequired;
    context.supportsReadonly = initialSupportsReadonly;

    const applyInvalid = () => {
      const invalid = externalInvalid || context.nativeInvalid;
      context.invalid = invalid;
      root.toggleAttribute("data-invalid", invalid);
      error.hidden = !(invalid && context.hasError);
    };
    Citry.vue.watchEffect(() => {
      const requestedRequired = resolveBoolean("required", data.serverRequired);
      const readonlyFallback = data.inheritsReadonly && form ? form.readonly : data.serverReadonly;
      // CForm uses a native disabled fieldset, so its disabled state
      // must win over a descendant's local configuration.
      const disabled = Boolean(form?.disabled) || resolveBoolean("disabled", data.serverDisabled);
      const requestedReadonly = resolveBoolean("readonly", readonlyFallback);
      const required = requestedRequired && context.supportsRequired;
      const readonly = requestedReadonly && context.supportsReadonly;
      if (requestedRequired && !context.supportsRequired) {
        reportUnsupported("required");
      } else {
        invalidEpisodes.delete("capability:required");
      }
      if (requestedReadonly && !context.supportsReadonly) {
        reportUnsupported("readonly");
      } else {
        invalidEpisodes.delete("capability:readonly");
      }
      externalInvalid = resolveBoolean("invalid", data.serverInvalid);
      const orientation = resolveChoice("orientation");
      const density = resolveChoice("density");

      context.required = required;
      context.disabled = disabled;
      context.readonly = readonly;
      root.toggleAttribute("data-required", required);
      root.toggleAttribute("data-disabled", disabled);
      root.toggleAttribute("data-readonly", readonly);
      root.dataset.orientation = orientation;
      root.dataset.density = density;
      requiredIndicator.hidden = !required;
      applyInvalid();
    });
    root.setAttribute("data-citry-field-initialized", "");

    return () => {
      root.removeAttribute("data-citry-field-initialized");
    };
  },
});

})();