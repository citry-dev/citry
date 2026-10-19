(function() {

__citryRuntime.registerTypeOptions.bind(null, "CTextarea_8ea155", "84be36e1ee732bdbfa81a0fd85b6686201eae645ff46b58170f3557d7d02ec78")({
  props: {
    value: {},
    rows: {},
    required: {},
    disabled: {},
    readonly: {},
    invalid: {},
    variant: {},
    size: {},
    resize: {},
  },
  inject: {
    fieldService: {from: Symbol.for("citry-ui:field"), default: null},
    formService: {from: Symbol.for("citry-ui:form"), default: null},
  },
  onServerRender: ({component}) => {
    const textarea = component.$el;
    if (!(textarea instanceof HTMLTextAreaElement)) {
      throw new Error("[citry-ui] CTextarea settled anatomy is invalid.");
    }
    const data = component;
    const props = component.$props;
    const field = component.fieldService;
    const form = component.formService;
    const allowedValues = {
      variant: ["outline", "filled", "plain"],
      size: ["sm", "md", "lg"],
      resize: ["none", "vertical", "horizontal", "both"],
    };
    const invalidEpisodes = new Map();
    let nativeInvalid = false;
    let controlled = false;
    let controlledValue = null;
    let composing = false;
    let reconcileTimer = null;
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
        `[citry-ui] CTextarea ${name} received invalid client value ${describedValue}; `
          + "using the previous valid value or server-rendered fallback.",
        textarea,
      );
    };
    const normalizeNewlines = (value) => value.replace(/\r\n?/g, "\n");
    const resolveBoolean = (name, fallback) => {
      const value = props[name] === undefined ? fallback : props[name];
      if (typeof value === "boolean") {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return fallback;
    };
    const resolveRows = () => {
      const value = props.rows === undefined ? data.serverRows : props.rows;
      if (Number.isInteger(value) && value > 0) {
        invalidEpisodes.delete("rows");
        return value;
      }
      reportInvalid("rows", value);
      return data.serverRows;
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
    const reportFieldOwned = (name, value) => {
      const describedValue = describeValue(value);
      const fingerprint = `field:${typeof value}:${describedValue}`;
      if (invalidEpisodes.get(name) === fingerprint) {
        return;
      }
      invalidEpisodes.set(name, fingerprint);
      console.error(
        `[citry-ui] CTextarea ${name} is controlled by its enclosing CField; `
          + `ignoring client value ${describedValue}.`,
        textarea,
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
        textarea.setAttribute("aria-describedby", describedBy);
      } else {
        textarea.removeAttribute("aria-describedby");
      }
      if (errorMessage) {
        textarea.setAttribute("aria-errormessage", errorMessage);
      } else {
        textarea.removeAttribute("aria-errormessage");
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
        // A disabled native CForm fieldset always wins.
        disabled = Boolean(form?.disabled) || resolveBoolean("disabled", data.serverDisabled);
        const readonlyFallback = data.inheritsReadonly && form ? form.readonly : data.serverReadonly;
        readonly = resolveBoolean("readonly", readonlyFallback);
        externalInvalid = resolveBoolean("invalid", data.serverInvalid);
      }
      const invalid = externalInvalid || nativeInvalid;

      textarea.required = required;
      textarea.disabled = disabled;
      textarea.readOnly = readonly;
      textarea.rows = resolveRows();
      textarea.toggleAttribute("data-required", required);
      textarea.toggleAttribute("data-disabled", disabled);
      textarea.toggleAttribute("data-readonly", readonly);
      textarea.toggleAttribute("data-invalid", invalid);
      textarea.dataset.variant = resolveChoice("variant");
      textarea.dataset.size = resolveChoice("size");
      textarea.dataset.resize = resolveChoice("resize");
      if (invalid) {
        textarea.setAttribute("aria-invalid", "true");
      } else {
        textarea.removeAttribute("aria-invalid");
      }
      syncRelationships(invalid);
    };
    const clearNativeInvalidWhenValid = () => {
      if (!nativeInvalid || !textarea.validity.valid) {
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
        invalidEpisodes.delete("value");
        return;
      }
      if (typeof value !== "string") {
        reportInvalid("value", value);
        if (controlled && !composing && textarea.value !== controlledValue) {
          textarea.value = controlledValue;
        }
        return;
      }
      invalidEpisodes.delete("value");
      controlled = true;
      controlledValue = normalizeNewlines(value);
      if (!composing && textarea.value !== controlledValue) {
        textarea.value = controlledValue;
      }
    };
    const scheduleReconcile = () => {
      if (reconcileTimer !== null) {
        clearTimeout(reconcileTimer);
      }
      // Consumer event handlers and Vue updates settle before this
      // task reads the latest value prop.
      reconcileTimer = setTimeout(() => {
        reconcileTimer = null;
        if (!composing) {
          applyLatestValueProp();
        }
      }, 0);
    };
    const onInvalid = () => {
      nativeInvalid = true;
      field?.setNativeInvalid(true);
      applyState();
    };
    const onInput = () => {
      clearNativeInvalidWhenValid();
      if (controlled && !composing) {
        scheduleReconcile();
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
      scheduleReconcile();
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
    const nativeForm = textarea.form;

    textarea.addEventListener("invalid", onInvalid);
    textarea.addEventListener("input", onInput);
    textarea.addEventListener("change", onChange);
    textarea.addEventListener("compositionstart", onCompositionStart);
    textarea.addEventListener("compositionend", onCompositionEnd);
    nativeForm?.addEventListener("reset", onReset);
    Citry.vue.watchEffect(() => {
      applyState();
      clearNativeInvalidWhenValid();
    });
    Citry.vue.watchEffect(() => {
      applyLatestValueProp();
    });
    textarea.setAttribute("data-citry-textarea-initialized", "");

    return () => {
      textarea.removeEventListener("invalid", onInvalid);
      textarea.removeEventListener("input", onInput);
      textarea.removeEventListener("change", onChange);
      textarea.removeEventListener("compositionstart", onCompositionStart);
      textarea.removeEventListener("compositionend", onCompositionEnd);
      nativeForm?.removeEventListener("reset", onReset);
      if (reconcileTimer !== null) {
        clearTimeout(reconcileTimer);
      }
      resetTimers.forEach((resetTimer) => clearTimeout(resetTimer));
      resetTimers.clear();
      if (nativeInvalid) {
        field?.setNativeInvalid(false);
      }
      textarea.removeAttribute("data-citry-textarea-initialized");
    };
  },
});

})();