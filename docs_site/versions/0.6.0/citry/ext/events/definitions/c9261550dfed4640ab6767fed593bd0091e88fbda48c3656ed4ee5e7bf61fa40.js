(function() {

__citryRuntime.registerTypeOptions.bind(null, "CCheckbox_05d638", "64dd9133eb3a3a6bfc460fb80d3b1f1f99814fd3b17cf92f26b66195ac898906")({
  props: {
    checked: {},
    indeterminate: {},
    value: {},
    required: {},
    disabled: {},
    invalid: {},
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
    if (!(root instanceof HTMLElement)) throw new Error("[citry-ui] CCheckbox settled anatomy is invalid.");
    const data = component;
    const props = component.$props;
    const input = root.querySelector(':scope > [data-citry-ui-part="input"]');
    if (!(input instanceof HTMLInputElement) || input.type !== "checkbox") {
      throw new Error("[citry-ui] CCheckbox requires one direct native checkbox input.");
    }
    const field = component.fieldService;
    const form = component.formService;
    const handoffKey = Symbol.for("citry-ui:checkbox-handoff");
    const allowedValues = {
      variant: ["solid", "outline"],
      size: ["sm", "md", "lg"],
      label_pos: ["start", "end"],
    };
    const invalidEpisodes = new Map();
    const resetTimers = new Set();
    let nativeInvalid = false;
    let controlledChecked = false;
    let controlledCheckedValue = false;
    let controlledIndeterminate = false;
    let controlledIndeterminateValue = false;
    let activationPending = false;
    let reconcileTimer = null;

    const handoff = root[handoffKey];
    delete root[handoffKey];
    // Correlated rerenders replace the initializer but may retain this root.
    // Restore browser-owned current state after HTML updates reset defaults.
    if (handoff) {
      input.checked = Boolean(handoff.checked);
      input.indeterminate = Boolean(handoff.indeterminate);
    } else {
      input.indeterminate = data.serverIndeterminate;
    }

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
        `[citry-ui] CCheckbox ${name} received invalid client value ${describedValue}; `
          + "using the documented fallback.",
        root,
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
        `[citry-ui] CCheckbox ${name} is controlled by its enclosing CField; `
          + `ignoring client value ${describedValue}.`,
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
    const resolveChoice = (name, fallback) => {
      const value = props[name] === undefined ? fallback : props[name];
      if (allowedValues[name].includes(value)) {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return fallback;
    };
    const canonicalizeValue = (value) => {
      if (typeof value !== "string" || value.includes("\0")) {
        return null;
      }
      return value.replace(/\r\n?/g, "\n");
    };
    const resolveValue = () => {
      if (props.value === undefined) {
        invalidEpisodes.delete("value");
        return data.serverValue;
      }
      const canonical = canonicalizeValue(props.value);
      if (canonical === null) {
        reportInvalid("value", props.value);
        return data.serverValue;
      }
      invalidEpisodes.delete("value");
      return canonical;
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
        data.hasDescription ? data.descriptionId : null,
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
    const syncNativeMirrors = () => {
      root.toggleAttribute("data-checked", input.checked);
      root.toggleAttribute("data-indeterminate", input.indeterminate);
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
        required = resolveBoolean("required", data.serverRequired);
        disabled = Boolean(form?.disabled) || resolveBoolean("disabled", data.serverDisabled);
        externalInvalid = resolveBoolean("invalid", data.serverInvalid);
      }
      const invalid = externalInvalid || nativeInvalid;
      const variant = resolveChoice("variant", data.serverVariant);
      const size = resolveChoice("size", data.serverSize);
      const labelPos = resolveChoice("label_pos", data.serverLabelPos);
      const value = resolveValue();

      input.required = required;
      input.disabled = disabled;
      if (input.value !== value) {
        input.value = value;
      }
      root.toggleAttribute("data-required", required);
      root.toggleAttribute("data-disabled", input.matches(":disabled"));
      root.toggleAttribute("data-invalid", invalid);
      root.dataset.variant = variant;
      root.dataset.size = size;
      root.dataset.labelPos = labelPos;
      if (invalid) {
        input.setAttribute("aria-invalid", "true");
      } else {
        input.removeAttribute("aria-invalid");
      }
      syncRelationships(invalid);
      syncNativeMirrors();
    };
    const clearNativeInvalidWhenValid = () => {
      if (!nativeInvalid || !input.validity.valid) {
        return;
      }
      nativeInvalid = false;
      field?.setNativeInvalid(false);
      applyState();
    };
    const applyControlledBoolean = (name, property) => {
      const value = props[name];
      const controlledName = name === "checked" ? "controlledChecked" : "controlledIndeterminate";
      if (value === undefined) {
        invalidEpisodes.delete(name);
        if (controlledName === "controlledChecked") {
          controlledChecked = false;
        } else {
          controlledIndeterminate = false;
        }
        return;
      }
      if (typeof value !== "boolean") {
        reportInvalid(name, value);
        const isControlled = controlledName === "controlledChecked"
          ? controlledChecked
          : controlledIndeterminate;
        const retained = controlledName === "controlledChecked"
          ? controlledCheckedValue
          : controlledIndeterminateValue;
        if (isControlled && !activationPending && input[property] !== retained) {
          input[property] = retained;
        }
        return;
      }
      invalidEpisodes.delete(name);
      if (controlledName === "controlledChecked") {
        controlledChecked = true;
        controlledCheckedValue = value;
      } else {
        controlledIndeterminate = true;
        controlledIndeterminateValue = value;
      }
      if (!activationPending && input[property] !== value) {
        input[property] = value;
      }
    };
    const applyLatestControlled = () => {
      applyControlledBoolean("checked", "checked");
      applyControlledBoolean("indeterminate", "indeterminate");
      syncNativeMirrors();
    };
    const scheduleReconcile = () => {
      if (reconcileTimer !== null) {
        clearTimeout(reconcileTimer);
      }
      reconcileTimer = setTimeout(() => {
        reconcileTimer = null;
        activationPending = false;
        applyLatestControlled();
        clearNativeInvalidWhenValid();
        applyState();
      }, 0);
    };
    const onInvalid = () => {
      nativeInvalid = true;
      field?.setNativeInvalid(true);
      applyState();
    };
    const onInput = () => {
      // A microtask can run between native input and change. Keep the
      // browser-produced state visible to both consumer handlers.
      activationPending = true;
      syncNativeMirrors();
      scheduleReconcile();
      if (!controlledChecked) {
        clearNativeInvalidWhenValid();
      }
    };
    const onChange = () => {
      if (!activationPending) {
        activationPending = true;
        scheduleReconcile();
      }
      syncNativeMirrors();
      if (!controlledChecked) {
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
        activationPending = false;
        applyLatestControlled();
        applyState();
      }, 0);
      resetTimers.add(resetTimer);
    };
    const unregisterCapabilities = field?.registerCapabilities({
      required: true,
      readonly: false,
    });
    const nativeForm = input.form;
    const ancestorFieldsets = [];
    for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
      if (ancestor instanceof HTMLFieldSetElement) {
        ancestorFieldsets.push(ancestor);
      }
    }
    // Native fieldset disabledness does not change input.disabled. Watch
    // only the resolved ancestor fieldsets so the public mirror follows
    // the browser's effective :disabled state.
    const fieldsetObserver = ancestorFieldsets.length > 0
      ? new MutationObserver(() => applyState())
      : null;
    ancestorFieldsets.forEach(fieldset => fieldsetObserver.observe(fieldset, {
      attributes: true,
      attributeFilter: ["disabled"],
    }));

    input.addEventListener("invalid", onInvalid);
    input.addEventListener("input", onInput);
    input.addEventListener("change", onChange);
    nativeForm?.addEventListener("reset", onReset);
    Citry.vue.watchEffect(() => {
      applyState();
      applyLatestControlled();
      if (!activationPending) {
        clearNativeInvalidWhenValid();
      }
    });
    root.setAttribute("data-citry-checkbox-initialized", "");

    return () => {
      root[handoffKey] = {
        checked: input.checked,
        indeterminate: input.indeterminate,
      };
      input.removeEventListener("invalid", onInvalid);
      input.removeEventListener("input", onInput);
      input.removeEventListener("change", onChange);
      nativeForm?.removeEventListener("reset", onReset);
      if (reconcileTimer !== null) {
        clearTimeout(reconcileTimer);
      }
      resetTimers.forEach((resetTimer) => clearTimeout(resetTimer));
      resetTimers.clear();
      fieldsetObserver?.disconnect();
      unregisterCapabilities?.();
      if (nativeInvalid) {
        field?.setNativeInvalid(false);
      }
      root.removeAttribute("data-citry-checkbox-initialized");
    };
  },
});

})();