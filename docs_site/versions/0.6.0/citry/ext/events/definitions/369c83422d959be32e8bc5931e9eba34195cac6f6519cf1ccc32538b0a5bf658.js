(function() {

__citryRuntime.registerTypeOptions.bind(null, "CRadioGroup_38ad5d", "6e8ed819c8bceffd61165da1f4785accb4b881c0f82538738c6b9b3e1322dc97")({
  props: {
    value: {},
    required: {},
    disabled: {},
    invalid: {},
    orientation: {},
    variant: {},
    size: {},
    label_pos: {},
  },
  inject: {
    fieldService: {from: Symbol.for("citry-ui:field"), default: null},
    formService: {from: Symbol.for("citry-ui:form"), default: null},
  },
  onServerRender: ({component}) => {
    const root = component.$el;
    if (!(root instanceof HTMLFieldSetElement)) {
      throw new Error("[citry-ui] CRadioGroup settled anatomy is invalid.");
    }
    const data = component;
    const props = component.$props;
    const radios = [...root.querySelectorAll('[data-citry-ui-part="input"][type="radio"]')]
      .filter((input) => input.closest('[data-citry-ui-part="radio-group"]') === root);
    if (!radios.length) {
      throw new Error("[citry-ui] CRadioGroup requires at least one owned native radio input.");
    }
    const field = component.fieldService;
    const form = component.formService;
    const unregisterCapabilities = field?.registerCapabilities({required: true, readonly: false});
    const allowed = {
      orientation: ["vertical", "horizontal"],
      variant: ["solid", "outline"],
      size: ["sm", "md", "lg"],
      label_pos: ["start", "end"],
    };
    const invalidEpisodes = new Set();
    const resetTimers = new Set();
    let nativeInvalid = false;
    let controlled = false;
    let controlledValue = null;
    let activationPending = false;
    let reconcileTimer = null;

    const describeValue = (value) => {
      try {
        return JSON.stringify(value) ?? String(value);
      } catch {
        return String(value);
      }
    };
    const reportInvalid = (name, value) => {
      if (invalidEpisodes.has(name)) {
        return;
      }
      invalidEpisodes.add(name);
      console.error(
        `[citry-ui] CRadioGroup ${name} received invalid client value ${describeValue(value)}; `
          + "using the documented fallback.",
        root,
      );
    };
    const reportFieldOwned = (name, value) => {
      const key = `field:${name}`;
      if (invalidEpisodes.has(key)) {
        return;
      }
      invalidEpisodes.add(key);
      console.error(
        `[citry-ui] CRadioGroup ${name} is controlled by its enclosing CField; `
          + `ignoring client value ${describeValue(value)}.`,
        root,
      );
    };
    const canonicalize = (value) => {
      if (typeof value !== "string" || value.includes("\0") || value.length === 0) {
        return undefined;
      }
      return value.replace(/\r\n?/g, "\n");
    };
    const knownValues = new Set(radios.map((input) => input.value));
    const resolveChoice = (name, fallback) => {
      const value = props[name] === undefined ? fallback : props[name];
      if (allowed[name].includes(value)) {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return fallback;
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
    const setCheckedValue = (value) => {
      radios.forEach((input) => {
        input.checked = value !== null && input.value === value;
      });
    };
    const selectedValue = () => radios.find((input) => input.checked)?.value ?? null;
    const syncSelection = () => {
      const value = selectedValue();
      if (value === null) {
        root.removeAttribute("data-value");
      } else {
        root.setAttribute("data-value", value);
      }
      radios.forEach((input) => {
        input.closest('[data-citry-ui-part="radio"]')?.toggleAttribute("data-checked", input.checked);
      });
    };
    const syncInvalid = (invalid) => {
      root.toggleAttribute("data-invalid", invalid);
      if (invalid) {
        root.setAttribute("aria-invalid", "true");
      } else {
        root.removeAttribute("aria-invalid");
      }
      radios.forEach((input) => {
        if (invalid) {
          input.setAttribute("aria-invalid", "true");
        } else {
          input.removeAttribute("aria-invalid");
        }
      });
    };
    const applyState = () => {
      let required;
      let disabled;
      let externalInvalid;
      if (field) {
        ["required", "disabled", "invalid"].forEach((name) => {
          if (props[name] !== undefined) {
            reportFieldOwned(name, props[name]);
          } else {
            invalidEpisodes.delete(`field:${name}`);
          }
        });
        required = field.required;
        disabled = field.disabled;
        externalInvalid = field.invalid;
      } else {
        required = resolveBoolean("required", data.serverRequired);
        disabled = Boolean(form?.disabled) || resolveBoolean("disabled", data.serverDisabled);
        externalInvalid = resolveBoolean("invalid", data.serverInvalid);
      }
      root.disabled = disabled;
      root.toggleAttribute("data-required", required);
      root.toggleAttribute("data-disabled", root.matches(":disabled"));
      root.dataset.orientation = resolveChoice("orientation", data.serverOrientation);
      root.dataset.variant = resolveChoice("variant", data.serverVariant);
      root.dataset.size = resolveChoice("size", data.serverSize);
      root.dataset.labelPos = resolveChoice("label_pos", data.serverLabelPos);
      radios.forEach((input) => {
        input.required = required;
        input.closest('[data-citry-ui-part="radio"]')?.toggleAttribute(
          "data-disabled",
          input.matches(":disabled"),
        );
      });
      syncInvalid(externalInvalid || nativeInvalid);
      syncSelection();
    };
    const clearNativeInvalidWhenValid = () => {
      if (!nativeInvalid || !radios.every((input) => input.validity.valid)) {
        return;
      }
      nativeInvalid = false;
      field?.setNativeInvalid(false);
    };
    const applyControlled = () => {
      const supplied = props.value;
      if (supplied === undefined) {
        controlled = false;
        invalidEpisodes.delete("value");
        return;
      }
      if (supplied === null) {
        controlled = true;
        controlledValue = null;
        invalidEpisodes.delete("value");
        setCheckedValue(null);
        return;
      }
      const value = canonicalize(supplied);
      if (value === undefined || !knownValues.has(value)) {
        reportInvalid("value", supplied);
        if (!controlled) {
          setCheckedValue(data.serverValue);
        }
        return;
      }
      invalidEpisodes.delete("value");
      controlled = true;
      controlledValue = value;
      setCheckedValue(value);
    };
    const reconcile = () => {
      reconcileTimer = null;
      activationPending = false;
      applyControlled();
      clearNativeInvalidWhenValid();
      applyState();
    };
    const scheduleReconcile = () => {
      if (reconcileTimer !== null) {
        clearTimeout(reconcileTimer);
      }
      reconcileTimer = setTimeout(reconcile, 0);
    };
    const onInput = (event) => {
      if (!radios.includes(event.target)) {
        return;
      }
      activationPending = true;
      syncSelection();
      scheduleReconcile();
      if (!controlled) {
        clearNativeInvalidWhenValid();
      }
    };
    const onChange = (event) => {
      if (!radios.includes(event.target)) {
        return;
      }
      if (!activationPending) {
        activationPending = true;
        scheduleReconcile();
      }
      syncSelection();
    };
    const onInvalid = (event) => {
      if (!radios.includes(event.target)) {
        return;
      }
      nativeInvalid = true;
      field?.setNativeInvalid(true);
      applyState();
    };
    const nativeForm = radios[0].form;
    const onReset = (event) => {
      const timer = setTimeout(() => {
        resetTimers.delete(timer);
        if (event.defaultPrevented) {
          return;
        }
        nativeInvalid = false;
        field?.setNativeInvalid(false);
        if (controlled) {
          setCheckedValue(controlledValue);
        }
        applyState();
      }, 0);
      resetTimers.add(timer);
    };

    root.addEventListener("input", onInput);
    root.addEventListener("change", onChange);
    root.addEventListener("invalid", onInvalid, true);
    nativeForm?.addEventListener("reset", onReset);
    Citry.vue.watchEffect(() => {
      applyState();
      if (!activationPending) {
        applyControlled();
        clearNativeInvalidWhenValid();
        applyState();
      }
    });
    root.setAttribute("data-citry-radio-group-initialized", "");

    return () => {
      root.removeEventListener("input", onInput);
      root.removeEventListener("change", onChange);
      root.removeEventListener("invalid", onInvalid, true);
      nativeForm?.removeEventListener("reset", onReset);
      unregisterCapabilities?.();
      if (reconcileTimer !== null) {
        clearTimeout(reconcileTimer);
      }
      resetTimers.forEach((timer) => clearTimeout(timer));
      resetTimers.clear();
      if (nativeInvalid) {
        field?.setNativeInvalid(false);
      }
      root.removeAttribute("data-citry-radio-group-initialized");
    };
  },
});

})();