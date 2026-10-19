(function() {

__citryRuntime.registerTypeOptions.bind(null, "CFileInput_4f6cdb", "429764e231a7f6a4f250825240570490bb69781d987d2355e6c55949c3cfc45c")({
  props: {
    accept: {}, capture: {}, multiple: {}, required: {}, disabled: {}, invalid: {},
    variant: {}, size: {},
  },
  inject: {
    fieldService: {from: Symbol.for("citry-ui:field"), default: null},
    formService: {from: Symbol.for("citry-ui:form"), default: null},
  },
  onServerRender: ({component}) => {
    const input = component.$el;
    const data = {...component.serverDefaults,
      externalDescribedBy: component.externalDescribedBy,
      externalErrorMessage: component.externalErrorMessage,
      inheritsFormDisabled: component.inheritsFormDisabled};
    const props = component.$props;
    const field = component.fieldService;
    const form = component.formService;
    const invalidEpisodes = new Set();
    const resetTimers = new Set();
    let nativeInvalid = false;

    const report = (name, value, message = "received invalid client value") => {
      if (invalidEpisodes.has(name)) return;
      invalidEpisodes.add(name);
      console.error(`[citry-ui] CFileInput ${name} ${message}`, value, input);
    };
    const booleanValue = (name, fallback) => {
      const value = props[name] === undefined ? fallback : props[name];
      if (typeof value === "boolean") {
        invalidEpisodes.delete(name);
        return value;
      }
      report(name, value);
      return fallback;
    };
    const choiceValue = (name, fallback, allowed) => {
      const value = props[name] === undefined ? fallback : props[name];
      if (typeof value === "string" && allowed.includes(value)) {
        invalidEpisodes.delete(name);
        return value;
      }
      report(name, value);
      return fallback;
    };
    const optionalString = (name, fallback, allowed = null) => {
      if (props[name] === undefined) {
        invalidEpisodes.delete(name);
        return fallback;
      }
      const value = props[name];
      if (typeof value === "string" && !value.includes("\0") && (!allowed || allowed.includes(value))) {
        invalidEpisodes.delete(name);
        return value;
      }
      report(name, value);
      return fallback;
    };
    const idrefs = (...values) => {
      const tokens = [];
      values.forEach(value => {
        if (typeof value !== "string") return;
        value.split(/\s+/).filter(Boolean).forEach(token => {
          if (!tokens.includes(token)) tokens.push(token);
        });
      });
      return tokens.join(" ") || null;
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
      if (describedBy) input.setAttribute("aria-describedby", describedBy);
      else input.removeAttribute("aria-describedby");
      if (errorMessage) input.setAttribute("aria-errormessage", errorMessage);
      else input.removeAttribute("aria-errormessage");
    };
    const syncFiles = () => input.toggleAttribute("data-has-files", input.files.length > 0);
    const applyState = () => {
      let required;
      let disabled;
      let externalInvalid;
      if (field) {
        ["required", "disabled", "invalid"].forEach(name => {
          if (props[name] !== undefined) report(name, props[name], "is owned by CField; ignoring");
          else invalidEpisodes.delete(name);
        });
        required = field.required;
        disabled = field.disabled;
        externalInvalid = field.invalid;
      } else {
        required = booleanValue("required", data.required);
        disabled = Boolean(form?.disabled) || booleanValue("disabled", data.disabled);
        externalInvalid = booleanValue("invalid", data.invalid);
      }
      input.accept = optionalString("accept", data.accept) ?? "";
      const capture = optionalString("capture", data.capture, ["user", "environment"]);
      if (capture) input.setAttribute("capture", capture);
      else input.removeAttribute("capture");
      input.multiple = booleanValue("multiple", data.multiple);
      input.required = required;
      input.disabled = disabled;
      const invalid = externalInvalid || nativeInvalid;
      input.toggleAttribute("data-required", required);
      input.toggleAttribute("data-disabled", input.matches(":disabled"));
      input.toggleAttribute("data-invalid", invalid);
      input.dataset.variant = choiceValue("variant", data.variant, ["outline", "soft", "plain"]);
      input.dataset.size = choiceValue("size", data.size, ["sm", "md", "lg"]);
      if (invalid) input.setAttribute("aria-invalid", "true");
      else input.removeAttribute("aria-invalid");
      syncRelationships(invalid);
      syncFiles();
    };
    const clearNativeInvalid = () => {
      if (!nativeInvalid || !input.validity.valid) return;
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
      syncFiles();
      clearNativeInvalid();
    };
    const onReset = (event) => {
      const timer = setTimeout(() => {
        resetTimers.delete(timer);
        if (event.defaultPrevented) return;
        nativeInvalid = false;
        field?.setNativeInvalid(false);
        applyState();
      }, 0);
      resetTimers.add(timer);
    };
    const nativeForm = input.form;
    const fieldsets = [];
    for (let ancestor = input.parentElement; ancestor; ancestor = ancestor.parentElement) {
      if (ancestor instanceof HTMLFieldSetElement) fieldsets.push(ancestor);
    }
    const fieldsetObserver = fieldsets.length
      ? new MutationObserver(applyState)
      : null;
    fieldsets.forEach(fieldset => fieldsetObserver.observe(fieldset, {
      childList: true, attributes: true, attributeFilter: ["disabled"],
    }));
    const unregisterCapabilities = field?.registerCapabilities({required: true, readonly: false});
    input.addEventListener("invalid", onInvalid);
    input.addEventListener("input", onInput);
    input.addEventListener("change", onInput);
    nativeForm?.addEventListener("reset", onReset);
    const stop = Citry.vue.watchEffect(applyState);
    input.setAttribute("data-citry-file-input-initialized", "");
    return () => {
      stop?.();
      input.removeEventListener("invalid", onInvalid);
      input.removeEventListener("input", onInput);
      input.removeEventListener("change", onInput);
      nativeForm?.removeEventListener("reset", onReset);
      resetTimers.forEach(clearTimeout);
      resetTimers.clear();
      fieldsetObserver?.disconnect();
      unregisterCapabilities?.();
      if (nativeInvalid) field?.setNativeInvalid(false);
      input.removeAttribute("data-citry-file-input-initialized");
    };
  },
});

})();