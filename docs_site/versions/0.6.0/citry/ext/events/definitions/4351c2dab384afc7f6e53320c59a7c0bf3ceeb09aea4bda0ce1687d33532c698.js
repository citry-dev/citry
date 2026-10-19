(function() {

__citryRuntime.registerTypeOptions.bind(null, "CNativeSelect_bd67d3", "77d03815c649875f576a679c4d06790986367d95022eefc0e6ca06638473525d")({
  props: {
    value: {},
    required: {},
    disabled: {},
    invalid: {},
    variant: {},
    size: {},
  },
  inject: {
    fieldService: {from: Symbol.for("citry-ui:field"), default: null},
    formService: {from: Symbol.for("citry-ui:form"), default: null},
  },
  onServerRender: ({component}) => {
    const select = component.$el;
    if (!(select instanceof HTMLSelectElement)) {
      throw new Error("[citry-ui] CNativeSelect settled anatomy is invalid.");
    }
    const data = component;
    const props = component.$props;
    const field = component.fieldService;
    const form = component.formService;
    const handoffKey = Symbol.for("citry-ui:native-select-handoff");
    const placeholder = data.hasPlaceholder ? select.options[0] : null;
    const allowedValues = {
      variant: ["outline", "filled", "plain"],
      size: ["sm", "md", "lg"],
    };
    const invalidEpisodes = new Map();
    const optionByValue = new Map();
    Array.from(select.options).forEach((option) => {
      if (option !== placeholder) {
        optionByValue.set(option.value, option);
      }
    });
    let controlled = false;
    let controlledTarget = null;
    let nativeInvalid = false;
    let reconcileTimer = null;
    const resetTimers = new Set();

    const optionEnabled = (option) => Boolean(
      option
        && !option.disabled
        && !(option.parentElement instanceof HTMLOptGroupElement && option.parentElement.disabled)
    );
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
        `[citry-ui] CNativeSelect ${name} received invalid client value ${describedValue}; `
          + "using the documented fallback.",
        select,
      );
    };
    const reportFieldOwned = (name, value) => {
      const describedValue = describeValue(value);
      const fingerprint = `field:${typeof value}:${describedValue}`;
      if (invalidEpisodes.get(name) === fingerprint) {
        return;
      }
      invalidEpisodes.set(name, fingerprint);
      console.error(
        `[citry-ui] CNativeSelect ${name} is controlled by its enclosing CField; `
          + `ignoring client value ${describedValue}.`,
        select,
      );
    };
    const reportUnsupportedRequired = () => {
      const episode = "required:placeholder";
      if (invalidEpisodes.get(episode) === "unsupported:true") {
        return;
      }
      invalidEpisodes.set(episode, "unsupported:true");
      console.error(
        "[citry-ui] CNativeSelect required=true requires a placeholder; using false.",
        select,
      );
    };
    const canonicalize = (value) => {
      if (value.includes("\0")) {
        return null;
      }
      return value.replace(/\r\n?/g, "\n");
    };
    const valueTarget = (value) => {
      if (value === null) {
        return data.hasPlaceholder ? { kind: "value", value: "" } : { kind: "none" };
      }
      if (typeof value !== "string") {
        return null;
      }
      const canonical = canonicalize(value);
      if (canonical === null) {
        return null;
      }
      if (canonical === "") {
        return data.hasPlaceholder ? { kind: "value", value: "" } : null;
      }
      const option = optionByValue.get(canonical);
      return optionEnabled(option) ? { kind: "value", value: canonical } : null;
    };
    const currentTarget = () => {
      if (select.selectedIndex === -1) {
        return { kind: "none" };
      }
      return { kind: "value", value: select.value };
    };
    const targetAvailable = (target) => {
      if (!target) {
        return false;
      }
      if (target.kind === "none") {
        return true;
      }
      if (target.value === "") {
        return Boolean(placeholder);
      }
      return optionEnabled(optionByValue.get(target.value));
    };
    const targetMatches = (target) => {
      if (target.kind === "none") {
        return select.selectedIndex === -1;
      }
      if (target.value === "") {
        return select.selectedIndex === 0 && select.options[0] === placeholder;
      }
      const option = optionByValue.get(target.value);
      return optionEnabled(option)
        && select.selectedOptions.length === 1
        && select.selectedOptions[0] === option;
    };
    const applyTarget = (target) => {
      if (targetMatches(target)) {
        return;
      }
      if (target.kind === "none") {
        select.selectedIndex = -1;
      } else {
        select.value = target.value;
      }
    };
    const structuralFallback = () => {
      if (data.serverValue !== null) {
        const incoming = valueTarget(data.serverValue);
        if (incoming && targetAvailable(incoming)) {
          return incoming;
        }
      }
      if (placeholder) {
        return { kind: "value", value: "" };
      }
      const firstEnabled = Array.from(select.options).find(optionEnabled);
      return firstEnabled ? { kind: "value", value: firstEnabled.value } : { kind: "none" };
    };
    const handoff = select[handoffKey];
    delete select[handoffKey];
    if (handoff?.kind === "none") {
      applyTarget(handoff);
    } else if (handoff?.kind === "value" && targetAvailable(handoff)) {
      applyTarget(handoff);
    } else if (handoff) {
      applyTarget(structuralFallback());
    }
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
      const serverName = `server${name[0].toUpperCase()}${name.slice(1)}`;
      const value = props[name] === undefined ? data[serverName] : props[name];
      if (allowedValues[name].includes(value)) {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return data[serverName];
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
        select.setAttribute("aria-describedby", describedBy);
      } else {
        select.removeAttribute("aria-describedby");
      }
      if (errorMessage) {
        select.setAttribute("aria-errormessage", errorMessage);
      } else {
        select.removeAttribute("aria-errormessage");
      }
    };
    const syncEmpty = () => {
      select.toggleAttribute("data-empty", select.selectedIndex === -1 || select.value === "");
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
            invalidEpisodes.delete(name);
          }
        });
        required = field.required;
        disabled = field.disabled;
        externalInvalid = field.invalid;
      } else {
        const requestedRequired = resolveBoolean("required", data.serverRequired);
        if (requestedRequired && !data.hasPlaceholder) {
          reportUnsupportedRequired();
          required = false;
        } else {
          invalidEpisodes.delete("required:placeholder");
          required = requestedRequired;
        }
        disabled = Boolean(form?.disabled) || resolveBoolean("disabled", data.serverDisabled);
        externalInvalid = resolveBoolean("invalid", data.serverInvalid);
      }
      const invalid = externalInvalid || nativeInvalid;
      select.required = required;
      select.disabled = disabled;
      select.toggleAttribute("data-required", required);
      select.toggleAttribute("data-disabled", disabled);
      select.toggleAttribute("data-invalid", invalid);
      select.dataset.variant = resolveChoice("variant");
      select.dataset.size = resolveChoice("size");
      if (invalid) {
        select.setAttribute("aria-invalid", "true");
      } else {
        select.removeAttribute("aria-invalid");
      }
      syncRelationships(invalid);
      syncEmpty();
    };
    const clearNativeInvalidWhenValid = () => {
      if (!nativeInvalid || !select.validity.valid) {
        return;
      }
      nativeInvalid = false;
      field?.setNativeInvalid(false);
      applyState();
    };
    const applyLatestValueProp = () => {
      const value = props.value;
      if (value === undefined) {
        controlled = false;
        controlledTarget = null;
        invalidEpisodes.delete("value");
        syncEmpty();
        clearNativeInvalidWhenValid();
        return;
      }
      const target = valueTarget(value);
      if (!target) {
        reportInvalid("value", value);
        if (controlled) {
          if (!targetAvailable(controlledTarget)) {
            controlledTarget = structuralFallback();
          }
          applyTarget(controlledTarget);
        }
        syncEmpty();
        clearNativeInvalidWhenValid();
        return;
      }
      invalidEpisodes.delete("value");
      controlled = true;
      controlledTarget = target;
      applyTarget(target);
      syncEmpty();
      clearNativeInvalidWhenValid();
    };
    const scheduleReconcile = () => {
      if (reconcileTimer !== null) {
        clearTimeout(reconcileTimer);
      }
      reconcileTimer = setTimeout(() => {
        reconcileTimer = null;
        applyLatestValueProp();
      }, 0);
    };
    const onInvalid = () => {
      nativeInvalid = true;
      field?.setNativeInvalid(true);
      applyState();
    };
    const onInput = () => {
      syncEmpty();
      if (controlled) {
        scheduleReconcile();
      } else {
        clearNativeInvalidWhenValid();
      }
    };
    const onChange = () => {
      syncEmpty();
      if (!controlled) {
        clearNativeInvalidWhenValid();
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
        applyLatestValueProp();
        applyState();
      }, 0);
      resetTimers.add(resetTimer);
    };
    const unregisterCapabilities = field?.registerCapabilities({
      required: data.hasPlaceholder,
      readonly: false,
    });
    const nativeForm = select.form;

    select.addEventListener("invalid", onInvalid);
    select.addEventListener("input", onInput);
    select.addEventListener("change", onChange);
    nativeForm?.addEventListener("reset", onReset);
    Citry.vue.watchEffect(() => {
      applyState();
      clearNativeInvalidWhenValid();
    });
    Citry.vue.watchEffect(() => {
      applyLatestValueProp();
    });
    select.setAttribute("data-citry-native-select-initialized", "");

    return () => {
      select[handoffKey] = currentTarget();
      select.removeEventListener("invalid", onInvalid);
      select.removeEventListener("input", onInput);
      select.removeEventListener("change", onChange);
      nativeForm?.removeEventListener("reset", onReset);
      unregisterCapabilities?.();
      if (reconcileTimer !== null) {
        clearTimeout(reconcileTimer);
      }
      resetTimers.forEach((resetTimer) => clearTimeout(resetTimer));
      resetTimers.clear();
      if (nativeInvalid) {
        field?.setNativeInvalid(false);
      }
      select.removeAttribute("data-citry-native-select-initialized");
    };
  },
});

})();