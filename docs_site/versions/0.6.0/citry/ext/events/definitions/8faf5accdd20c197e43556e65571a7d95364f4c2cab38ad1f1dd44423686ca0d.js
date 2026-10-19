(function() {

__citryRuntime.registerTypeOptions.bind(null, "CSwitch_fa49a4", "23b83a3900831c0dff6a298482711d6424cf396c3d1ee69cbb00fabfb0edc340")({
  props: {
    checked: {},
    value: {},
    required: {},
    disabled: {},
    invalid: {},
    size: {},
    label_pos: {},
  },
  inject: {
    fieldService: {from: Symbol.for("citry-ui:field"), default: null},
    formService: {from: Symbol.for("citry-ui:form"), default: null},
  },
  onServerRender: ({component}) => {
    const root = component.$el;
    if (!(root instanceof HTMLElement)) throw new Error("[citry-ui] CSwitch settled anatomy is invalid.");
    const data = component;
    const props = component.$props;
    const input = root.querySelector(':scope > [data-citry-ui-part="input"]');
    if (!(input instanceof HTMLInputElement) || input.type !== "checkbox") {
      throw new Error("[citry-ui] CSwitch requires one direct native checkbox input.");
    }
    const field = component.fieldService;
    const form = component.formService;
    const handoffKey = Symbol.for("citry-ui:switch-handoff");
    const invalidEpisodes = new Set();
    const resetTimers = new Set();
    let nativeInvalid = false;
    let controlled = false;
    let controlledValue = false;
    let activationPending = false;
    let reconcileTimer = null;
    const handoff = root[handoffKey];
    delete root[handoffKey];
    if (handoff) input.checked = Boolean(handoff.checked);

    const reportInvalid = (name, value) => {
      if (invalidEpisodes.has(name)) return;
      invalidEpisodes.add(name);
      console.error(
        `[citry-ui] CSwitch ${name} received invalid client value; using the fallback.`,
        value,
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
    const resolveChoice = (name, fallback, choices) => {
      const value = props[name] === undefined ? fallback : props[name];
      if (choices.includes(value)) {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return fallback;
    };
    const canonicalValue = () => {
      if (props.value === undefined) return data.serverValue;
      if (typeof props.value !== "string" || props.value.includes("\0")) {
        reportInvalid("value", props.value);
        return data.serverValue;
      }
      invalidEpisodes.delete("value");
      return props.value.replace(/\r\n?/g, "\n");
    };
    const syncRelationships = (invalid) => {
      const values = [
        field?.hasDescription ? field.descriptionId : null,
        data.hasDescription ? data.descriptionId : null,
        invalid && field?.hasError ? field.errorId : null,
        data.externalDescribedBy,
      ];
      const describedBy = [...new Set(values.filter(Boolean).flatMap((value) => value.split(/\s+/)))].join(" ");
      const errorMessage = invalid
        ? [field?.hasError ? field.errorId : null, data.externalErrorMessage].filter(Boolean).join(" ")
        : "";
      describedBy
        ? input.setAttribute("aria-describedby", describedBy)
        : input.removeAttribute("aria-describedby");
      errorMessage
        ? input.setAttribute("aria-errormessage", errorMessage)
        : input.removeAttribute("aria-errormessage");
    };
    const applyState = () => {
      let required;
      let disabled;
      let externalInvalid;
      if (field) {
        ["required", "disabled", "invalid"].forEach((name) => {
          if (props[name] !== undefined) reportInvalid(`${name}:field-owned`, props[name]);
          else invalidEpisodes.delete(`${name}:field-owned`);
        });
        required = field.required;
        disabled = field.disabled;
        externalInvalid = field.invalid;
      } else {
        required = resolveBoolean("required", data.serverRequired);
        disabled = Boolean(form?.disabled) || resolveBoolean("disabled", data.serverDisabled);
        externalInvalid = resolveBoolean("invalid", data.serverInvalid);
      }
      const invalid = externalInvalid || nativeInvalid;
      input.required = required;
      input.disabled = disabled;
      const value = canonicalValue();
      if (input.value !== value) input.value = value;
      root.toggleAttribute("data-required", required);
      root.toggleAttribute("data-disabled", input.matches(":disabled"));
      root.toggleAttribute("data-invalid", invalid);
      root.toggleAttribute("data-checked", input.checked);
      root.dataset.size = resolveChoice("size", data.serverSize, ["sm", "md", "lg"]);
      root.dataset.labelPos = resolveChoice("label_pos", data.serverLabelPos, ["start", "end"]);
      invalid ? input.setAttribute("aria-invalid", "true") : input.removeAttribute("aria-invalid");
      syncRelationships(invalid);
    };
    const applyControlled = () => {
      if (props.checked === undefined) {
        controlled = false;
        invalidEpisodes.delete("checked");
        return;
      }
      if (typeof props.checked !== "boolean") {
        reportInvalid("checked", props.checked);
        if (controlled && !activationPending) input.checked = controlledValue;
        return;
      }
      invalidEpisodes.delete("checked");
      controlled = true;
      controlledValue = props.checked;
      if (!activationPending && input.checked !== controlledValue) input.checked = controlledValue;
    };
    const settle = () => {
      activationPending = false;
      applyControlled();
      if (nativeInvalid && input.validity.valid) {
        nativeInvalid = false;
        field?.setNativeInvalid(false);
      }
      applyState();
    };
    const scheduleSettle = () => {
      if (reconcileTimer !== null) clearTimeout(reconcileTimer);
      reconcileTimer = setTimeout(() => {
        reconcileTimer = null;
        settle();
      }, 0);
    };
    const onInput = () => {
      activationPending = true;
      root.toggleAttribute("data-checked", input.checked);
      scheduleSettle();
    };
    const onChange = () => scheduleSettle();
    const onInvalid = () => {
      nativeInvalid = true;
      field?.setNativeInvalid(true);
      applyState();
    };
    const nativeForm = input.form;
    const onReset = (event) => {
      const timer = setTimeout(() => {
        resetTimers.delete(timer);
        if (event.defaultPrevented) return;
        if (controlled) input.checked = controlledValue;
        nativeInvalid = false;
        field?.setNativeInvalid(false);
        applyState();
      }, 0);
      resetTimers.add(timer);
    };
    input.addEventListener("input", onInput);
    input.addEventListener("change", onChange);
    input.addEventListener("invalid", onInvalid);
    nativeForm?.addEventListener("reset", onReset);
    const unregisterCapability = field?.registerCapabilities({
      required: true,
      readonly: false,
    });
    Citry.vue.watchEffect(() => {
      applyControlled();
      applyState();
    });
    root.setAttribute("data-citry-switch-initialized", "");
    return () => {
      root[handoffKey] = {checked: input.checked};
      input.removeEventListener("input", onInput);
      input.removeEventListener("change", onChange);
      input.removeEventListener("invalid", onInvalid);
      nativeForm?.removeEventListener("reset", onReset);
      if (reconcileTimer !== null) clearTimeout(reconcileTimer);
      resetTimers.forEach((timer) => clearTimeout(timer));
      unregisterCapability?.();
      root.removeAttribute("data-citry-switch-initialized");
    };
  },
})

})();