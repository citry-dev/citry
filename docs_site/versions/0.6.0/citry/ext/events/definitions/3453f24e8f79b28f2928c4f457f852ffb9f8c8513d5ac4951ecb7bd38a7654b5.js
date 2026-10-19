(function() {

__citryRuntime.registerTypeOptions.bind(null, "CInput_dc895e", "4cca594014cd9ad65b2b8a70c1836ab8ea3ebf3dcd501fe32a467995d4566d1c")({
  props: {
    value: {},
    required: {},
    disabled: {},
    readonly: {},
    invalid: {},
    variant: {},
    size: {},
  },
  inject: {
    fieldService: {from: Symbol.for("citry-ui:field"), default: null},
    formService: {from: Symbol.for("citry-ui:form"), default: null},
  },
  onServerRender: ({component}) => {
    const input = component.$el;
    if (!(input instanceof HTMLInputElement)) throw new Error("[citry-ui] CInput settled anatomy is invalid.");
    const data = component;
    const props = component.$props;
    const field = component.fieldService;
    const form = component.formService;
    const allowedValues = {
      variant: ["outline", "filled", "plain"],
      size: ["sm", "md", "lg"],
    };
    const invalidEpisodes = new Map();
    let nativeInvalid = false;
    let controlled = false;
    let controlledValue = null;
    let composing = false;
    const resetTimers = new Set();

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
        `[citry-ui] CInput ${name} received invalid client value ${describedValue}; `
          + "using the previous valid or server-rendered fallback.",
        input,
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
    const reportFieldOwned = (name, value) => {
      const describedValue = describeValue(value);
      const fingerprint = `field:${typeof value}:${describedValue}`;
      if (invalidEpisodes.get(name) === fingerprint) {
        return;
      }
      invalidEpisodes.set(name, fingerprint);
      console.error(
        `[citry-ui] CInput ${name} is controlled by its enclosing CField; `
          + `ignoring client value ${describedValue}.`,
        input,
      );
    };
    const idrefs = (...values) => {
      const result = [];
      values.forEach((value) => {
        if (typeof value !== "string") {
          return;
        }
        value.split(/\s+/).filter(Boolean).forEach((token) => {
          if (!result.includes(token)) {
            result.push(token);
          }
        });
      });
      return result.join(" ") || null;
    };
    const syncRelationships = (invalid) => {
      const describedBy = idrefs(
        field?.hasDescription ? field.descriptionId : null,
        invalid && field?.hasError ? field.errorId : null,
        data.externalDescribedBy,
      );
      const errorMessage = invalid
        ? idrefs(field?.hasError ? field.errorId : null, data.externalErrorMessage)
        : null;
      if (describedBy) {
        input.setAttribute("aria-describedby", describedBy);
      } else {
        input.removeAttribute("aria-describedby");
      }
      if (errorMessage) {
        input.setAttribute("aria-errormessage", errorMessage);
      } else {
        input.removeAttribute("aria-errormessage");
      }
    };
    const applyState = () => {
      let required;
      let disabled;
      let readonly;
      let externalInvalid;
      if (field) {
        ["required", "disabled", "readonly", "invalid"].forEach((name) => {
          if (props[name] !== undefined) {
            reportFieldOwned(name, props[name]);
          } else {
            invalidEpisodes.delete(name);
          }
        });
        required = field.required;
        disabled = field.disabled;
        readonly = field.readonly;
        externalInvalid = field.invalid;
      } else {
        required = resolveBoolean("required", data.serverRequired);
        // A native disabled CForm fieldset always wins.
        disabled = Boolean(form?.disabled) || resolveBoolean("disabled", data.serverDisabled);
        const readonlyFallback = data.inheritsReadonly && form ? form.readonly : data.serverReadonly;
        readonly = resolveBoolean("readonly", readonlyFallback);
        externalInvalid = resolveBoolean("invalid", data.serverInvalid);
      }
      const invalid = externalInvalid || nativeInvalid;
      const variant = resolveChoice("variant");
      const size = resolveChoice("size");

      input.required = required;
      input.disabled = disabled;
      input.readOnly = readonly;
      input.toggleAttribute("data-required", required);
      input.toggleAttribute("data-disabled", disabled);
      input.toggleAttribute("data-readonly", readonly);
      input.toggleAttribute("data-invalid", invalid);
      input.dataset.variant = variant;
      input.dataset.size = size;
      if (invalid) {
        input.setAttribute("aria-invalid", "true");
      } else {
        input.removeAttribute("aria-invalid");
      }
      syncRelationships(invalid);
    };
    const clearNativeInvalidWhenValid = () => {
      if (!nativeInvalid || !input.validity.valid) {
        return;
      }
      nativeInvalid = false;
      field?.setNativeInvalid(false);
      applyState();
    };
    const onInvalid = () => {
      nativeInvalid = true;
      field?.setNativeInvalid(true);
      applyState();
    };
    const onInput = () => {
      clearNativeInvalidWhenValid();
      if (controlled && !composing) {
        queueMicrotask(() => {
          if (controlled && !composing) {
            input.value = controlledValue;
          }
        });
      }
    };
    const onChange = () => {
      clearNativeInvalidWhenValid();
    };
    const onCompositionStart = () => {
      composing = true;
    };
    const onCompositionEnd = () => {
      composing = false;
      if (controlled) {
        queueMicrotask(() => {
          if (controlled && !composing) {
            input.value = controlledValue;
          }
        });
      }
    };
    const onReset = (event) => {
      const resetTimer = setTimeout(() => {
        resetTimers.delete(resetTimer);
        if (event.defaultPrevented) {
          return;
        }
        nativeInvalid = false;
        field?.setNativeInvalid(false);
        if (controlled) {
          input.value = controlledValue;
        }
        applyState();
      }, 0);
      resetTimers.add(resetTimer);
    };
    const nativeForm = input.form;

    input.addEventListener("invalid", onInvalid);
    input.addEventListener("input", onInput);
    input.addEventListener("change", onChange);
    input.addEventListener("compositionstart", onCompositionStart);
    input.addEventListener("compositionend", onCompositionEnd);
    nativeForm?.addEventListener("reset", onReset);
    const unregisterCapabilities = field?.registerCapabilities({required: true, readonly: true});
    Citry.vue.watchEffect(() => {
      applyState();
      clearNativeInvalidWhenValid();
    });
    Citry.vue.watchEffect(() => {
      const value = props.value;
      if (value === undefined) {
        controlled = false;
        invalidEpisodes.delete("value");
        return;
      }
      if (typeof value !== "string") {
        reportInvalid("value", value);
        return;
      }
      invalidEpisodes.delete("value");
      controlled = true;
      controlledValue = value;
      if (!composing) {
        input.value = value;
      }
    });
    input.setAttribute("data-citry-input-initialized", "");

    return () => {
      unregisterCapabilities?.();
      input.removeEventListener("invalid", onInvalid);
      input.removeEventListener("input", onInput);
      input.removeEventListener("change", onChange);
      input.removeEventListener("compositionstart", onCompositionStart);
      input.removeEventListener("compositionend", onCompositionEnd);
      nativeForm?.removeEventListener("reset", onReset);
      resetTimers.forEach((resetTimer) => clearTimeout(resetTimer));
      resetTimers.clear();
      if (nativeInvalid) {
        field?.setNativeInvalid(false);
      }
      input.removeAttribute("data-citry-input-initialized");
    };
  },
});

})();