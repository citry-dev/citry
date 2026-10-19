(function() {

const editableHandoffKey = Symbol.for("citry-ui:editable-handoff");
__citryRuntime.registerTypeOptions.bind(null, "CEditable_620b5b", "97f0fd7400bcef885a49cabe930089d67e81e06ed878f768cae5ca2d2495e875")({
  props: {
    value: {}, editing: {}, required: {}, disabled: {}, readonly: {}, invalid: {},
    submitMode: {}, selectOnFocus: {}, actionPosition: {}, variant: {}, size: {},
    onValueChange: {}, onEditChange: {},
  },
  inject: {
    fieldService: {from: Symbol.for("citry-ui:field"), default: null},
    formService: {from: Symbol.for("citry-ui:form"), default: null},
  },
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component;
    const props = component.$props;
    const i18n = component.$i18n;
    const preview = root.querySelector(':scope > [data-citry-ui-part="preview"]');
    const previewValue = preview?.querySelector('[data-citry-ui-part="preview-value"]');
    const editAction = preview?.querySelector('[data-citry-ui-part="edit-action"]');
    const editSurface = root.querySelector(':scope > [data-citry-ui-part="edit-surface"]');
    const input = editSurface?.querySelector(':scope > [data-citry-ui-part="input"]');
    const actions = editSurface?.querySelector(':scope > [data-citry-ui-part="actions"]');
    const submitAction = actions?.querySelector('[data-citry-ui-part="submit-action"]');
    const cancelAction = actions?.querySelector('[data-citry-ui-part="cancel-action"]');
    if (!(preview instanceof HTMLElement) || !(previewValue instanceof HTMLElement)
      || !(editAction instanceof HTMLButtonElement) || !(editSurface instanceof HTMLElement)
      || !(input instanceof HTMLInputElement) || !(actions instanceof HTMLElement)
      || !(submitAction instanceof HTMLButtonElement) || !(cancelAction instanceof HTMLButtonElement)) {
      throw new Error("[citry-ui] CEditable settled anatomy is invalid.");
    }

    const field = component.fieldService;
    const form = component.formService;
    const invalidEpisodes = new Set();
    const prior = root[editableHandoffKey];
    delete root[editableHandoffKey];
    const serverFingerprint = data.serverValue;
    let committed = prior?.serverFingerprint === serverFingerprint ? prior.committed : data.serverValue;
    let draft = prior?.serverFingerprint === serverFingerprint ? prior.draft : committed;
    let dirty = prior?.serverFingerprint === serverFingerprint ? Boolean(prior.dirty) : false;
    let internalEditing = prior?.serverFingerprint === serverFingerprint
      ? Boolean(prior.internalEditing)
      : data.serverEditing;
    let editing = false;
    let controlledValue = false;
    let controlledEditing = false;
    let clientValue;
    let clientEditing;
    let onValueChange = null;
    let onEditChange = null;
    let nativeInvalid = false;
    let composing = false;
    let actionPressPending = false;
    let active = true;
    let generation = 0;
    let pendingFocus = false;
    let configuration = {
      required: data.serverRequired,
      disabled: data.serverDisabled,
      readonly: data.serverReadonly,
      invalid: data.serverInvalid,
      submitMode: data.serverSubmitMode,
      selectOnFocus: data.serverSelectOnFocus,
      actionPosition: data.serverActionPosition,
      variant: data.serverVariant,
      size: data.serverSize,
    };

    const report = (name, value, suffix = "") => {
      if (invalidEpisodes.has(name)) return;
      invalidEpisodes.add(name);
      console.error(`[citry-ui] CEditable ${name} received invalid client value${suffix}`, value);
    };
    const boolean = (name, fallback) => {
      const value = props[name];
      if (value === undefined) { invalidEpisodes.delete(name); return fallback; }
      if (typeof value === "boolean") { invalidEpisodes.delete(name); return value; }
      report(name, value, "; using the server fallback");
      return fallback;
    };
    const choice = (name, fallback, allowed) => {
      const value = props[name];
      if (value === undefined) { invalidEpisodes.delete(name); return fallback; }
      if (typeof value === "string" && allowed.includes(value)) {
        invalidEpisodes.delete(name);
        return value;
      }
      report(name, value, "; using the server fallback");
      return fallback;
    };
    const idrefs = (...values) => {
      const result = [];
      values.forEach((value) => {
        if (typeof value !== "string") return;
        value.split(/\s+/).filter(Boolean).forEach((token) => {
          if (!result.includes(token)) result.push(token);
        });
      });
      return result.join(" ") || null;
    };
    const effectiveDisabled = () => configuration.disabled || input.matches(":disabled");
    const syncRelationships = (invalid) => {
      const described = idrefs(
        field?.hasDescription ? field.descriptionId : null,
        invalid && field?.hasError ? field.errorId : null,
        data.externalDescribedBy,
      );
      const error = invalid
        ? idrefs(field?.hasError ? field.errorId : null, data.externalErrorMessage)
        : null;
      if (described) input.setAttribute("aria-describedby", described);
      else input.removeAttribute("aria-describedby");
      if (error) input.setAttribute("aria-errormessage", error);
      else input.removeAttribute("aria-errormessage");
    };
    const focusInput = () => {
      const scheduled = ++generation;
      queueMicrotask(() => {
        if (!active || scheduled !== generation || !editing || !input.isConnected) return;
        input.focus({ preventScroll: true });
        if (configuration.selectOnFocus) input.select();
      });
    };
    const sync = () => {
      const disabled = effectiveDisabled();
      const invalid = configuration.invalid || nativeInvalid;
      root.toggleAttribute("data-editing", editing);
      root.toggleAttribute("data-empty", !committed);
      root.toggleAttribute("data-required", configuration.required);
      root.toggleAttribute("data-disabled", disabled);
      root.toggleAttribute("data-readonly", configuration.readonly);
      root.toggleAttribute("data-invalid", invalid);
      root.dataset.submitMode = configuration.submitMode;
      root.dataset.actionPosition = configuration.actionPosition;
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      previewValue.textContent = committed || data.placeholder;
      editAction.disabled = disabled || configuration.readonly;
      submitAction.disabled = disabled || configuration.readonly;
      cancelAction.disabled = disabled || configuration.readonly;
      input.required = configuration.required;
      input.disabled = configuration.disabled;
      input.readOnly = configuration.readonly;
      if (invalid) input.setAttribute("aria-invalid", "true");
      else input.removeAttribute("aria-invalid");
      syncRelationships(invalid);
      field?.setNativeInvalid(nativeInvalid);
    };
    const notifyEdit = (next, reason, source, forced = false) => {
      onEditChange?.(next, { editing: next, reason, controlled: controlledEditing, forced, source });
    };
    const applyEditing = (next, { focus = false } = {}) => {
      if (next && (effectiveDisabled() || configuration.readonly)) next = false;
      if (next === editing) {
        if (next && focus) focusInput();
        return;
      }
      editing = next;
      if (next) {
        if (!dirty) {
          draft = committed;
          input.value = draft;
        }
        sync();
        if (focus) focusInput();
      } else {
        pendingFocus = false;
        sync();
      }
    };
    const requestEditing = (next, reason, source, { focus = false, forced = false } = {}) => {
      if (forced) {
        internalEditing = next;
        applyEditing(next, { focus });
        notifyEdit(next, reason, source, true);
        return;
      }
      if (controlledEditing) {
        notifyEdit(next, reason, source);
        return;
      }
      internalEditing = next;
      applyEditing(next, { focus });
      notifyEdit(next, reason, source);
    };
    const startEdit = (source) => {
      if (effectiveDisabled() || configuration.readonly || editing) return;
      dirty = false;
      draft = committed;
      input.value = draft;
      requestEditing(true, "edit", source, { focus: true });
    };
    const clearNativeInvalid = () => {
      if (!nativeInvalid || !input.validity.valid) return;
      nativeInvalid = false;
      field?.setNativeInvalid(false);
    };
    const requestValue = (next, source, sourceEvent) => {
      if (next === committed) return false;
      const previous = committed;
      const detail = {
        value: next,
        previousValue: previous,
        controlled: controlledValue,
        source,
        sourceEvent,
      };
      if (!controlledValue) committed = next;
      onValueChange?.(next, detail);
      return true;
    };
    const submit = (reason, sourceEvent) => {
      if (!editing || effectiveDisabled() || configuration.readonly) return;
      if (!input.checkValidity()) {
        nativeInvalid = true;
        sync();
        input.focus({ preventScroll: true });
        return;
      }
      draft = input.value.replace(/\r\n?/g, "\n");
      dirty = false;
      requestValue(draft, reason === "blur" ? "blur" : "submit", sourceEvent);
      clearNativeInvalid();
      requestEditing(false, reason, sourceEvent);
      sync();
      if (!controlledEditing && !effectiveDisabled() && !configuration.readonly) {
        queueMicrotask(() => editAction.focus({ preventScroll: true }));
      }
    };
    const cancel = (sourceEvent, reason = "cancel") => {
      if (!editing) return;
      draft = committed;
      dirty = false;
      input.value = committed;
      nativeInvalid = false;
      requestEditing(false, reason, sourceEvent);
      sync();
      if (!controlledEditing && !effectiveDisabled() && !configuration.readonly) {
        queueMicrotask(() => editAction.focus({ preventScroll: true }));
      }
    };
    const forceClosed = (reason, source) => {
      if (!editing) return;
      draft = committed;
      dirty = false;
      input.value = committed;
      internalEditing = false;
      applyEditing(false);
      notifyEdit(false, reason, source, true);
    };

    const onClick = (event) => {
      const path = event.composedPath();
      if (path.includes(editAction)) startEdit(editAction);
      else if (path.includes(submitAction)) submit("submit", event);
      else if (path.includes(cancelAction)) cancel(event);
    };
    const onPointerDown = (event) => {
      const path = event.composedPath();
      if (!path.includes(submitAction) && !path.includes(cancelAction)) return;
      actionPressPending = true;
      setTimeout(() => { actionPressPending = false; }, 0);
    };
    const onInput = () => {
      draft = input.value;
      dirty = draft !== committed;
      clearNativeInvalid();
      sync();
    };
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        cancel(event);
      } else if (
        event.key === "Enter"
        && !event.isComposing
        && !composing
        && ["enter", "both"].includes(configuration.submitMode)
      ) {
        event.preventDefault();
        submit("submit", event);
      }
    };
    const onFocusOut = (event) => {
      if (!editing || !["blur", "both"].includes(configuration.submitMode)) return;
      const scheduled = generation;
      queueMicrotask(() => {
        if (!active || scheduled !== generation || !editing || actionPressPending) return;
        const activeElement = root.ownerDocument.activeElement;
        if (root.contains(activeElement) || event.relatedTarget && root.contains(event.relatedTarget)) return;
        submit("blur", event);
      });
    };
    const onInvalid = (event) => {
      nativeInvalid = true;
      if (!editing) requestEditing(true, "invalid", input, { focus: true, forced: true });
      sync();
      void event;
    };
    const onReset = (event) => {
      const scheduled = generation;
      setTimeout(() => {
        if (!active || event.defaultPrevented || scheduled !== generation) return;
        const previous = committed;
        const next = data.serverValue;
        nativeInvalid = false;
        dirty = false;
        draft = next;
        if (controlledValue) {
          input.value = committed;
          if (next !== committed) {
            onValueChange?.(next, {
              value: next,
              previousValue: previous,
              controlled: true,
              source: "reset",
              sourceEvent: event,
            });
          }
        } else {
          committed = next;
          input.value = next;
          if (next !== previous) {
            onValueChange?.(next, {
              value: next,
              previousValue: previous,
              controlled: false,
              source: "reset",
              sourceEvent: event,
            });
          }
        }
        if (editing) requestEditing(false, "reset", event);
        sync();
      }, 0);
    };
    const onCompositionStart = () => { composing = true; };
    const onCompositionEnd = () => { composing = false; };

    root.addEventListener("click", onClick, true);
    root.addEventListener("pointerdown", onPointerDown, true);
    root.addEventListener("focusout", onFocusOut);
    input.addEventListener("input", onInput);
    input.addEventListener("keydown", onKeyDown);
    input.addEventListener("invalid", onInvalid);
    input.addEventListener("compositionstart", onCompositionStart);
    input.addEventListener("compositionend", onCompositionEnd);
    input.form?.addEventListener("reset", onReset);
    const fieldsetObservers = [];
    for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
      if (!(ancestor instanceof HTMLFieldSetElement)) continue;
      const observer = new MutationObserver(() => {
        if (effectiveDisabled()) forceClosed("disabled", ancestor);
        sync();
      });
      observer.observe(ancestor, { attributes: true, childList: true, attributeFilter: ["disabled"] });
      fieldsetObservers.push(observer);
    }

    const stop = Citry.vue.watchEffect(() => {
      clientValue = props.value;
      clientEditing = props.editing;
      onValueChange = typeof props.onValueChange === "function" ? props.onValueChange : null;
      onEditChange = typeof props.onEditChange === "function" ? props.onEditChange : null;
      if (props.onValueChange != null && onValueChange === null) report("onValueChange", props.onValueChange);
      else invalidEpisodes.delete("onValueChange");
      if (props.onEditChange != null && onEditChange === null) report("onEditChange", props.onEditChange);
      else invalidEpisodes.delete("onEditChange");

      configuration = {
        required: field ? field.required : boolean("required", data.serverRequired),
        disabled: field ? field.disabled : Boolean(form?.disabled) || boolean("disabled", data.serverDisabled),
        readonly: field ? field.readonly : Boolean(form?.readonly) || boolean("readonly", data.serverReadonly),
        invalid: field ? field.invalid : boolean("invalid", data.serverInvalid),
        submitMode: choice("submitMode", data.serverSubmitMode, ["enter", "blur", "both", "explicit"]),
        selectOnFocus: boolean("selectOnFocus", data.serverSelectOnFocus),
        actionPosition: choice("actionPosition", data.serverActionPosition, ["inside", "outside"]),
        variant: choice("variant", data.serverVariant, ["outline", "filled", "plain"]),
        size: choice("size", data.serverSize, ["sm", "md", "lg"]),
      };

      if (clientValue === undefined || clientValue === null) {
        invalidEpisodes.delete("value");
        controlledValue = false;
      } else if (typeof clientValue === "string" && !clientValue.includes("\0")) {
        invalidEpisodes.delete("value");
        controlledValue = true;
        committed = clientValue.replace(/\r\n?/g, "\n");
        if (!editing || !dirty) {
          draft = committed;
          input.value = committed;
        }
      } else {
        report("value", clientValue, "; releasing control to the committed value");
        controlledValue = false;
      }

      if (clientEditing === undefined || clientEditing === null) {
        invalidEpisodes.delete("editing");
        controlledEditing = false;
        applyEditing(internalEditing, { focus: internalEditing && pendingFocus });
      } else if (typeof clientEditing === "boolean") {
        invalidEpisodes.delete("editing");
        controlledEditing = true;
        internalEditing = clientEditing;
        applyEditing(clientEditing, { focus: clientEditing && !editing });
      } else {
        report("editing", clientEditing, "; releasing control to committed mode");
        controlledEditing = false;
        applyEditing(internalEditing);
      }
      pendingFocus = false;
      if (effectiveDisabled()) forceClosed("disabled", input);
      else if (configuration.readonly) forceClosed("readonly", input);
      sync();
    });

    const placeholderBinding = i18n && data.catalogPlaceholder
      ? i18n.bind({
          message: "citry-ui-editable-click-to-edit",
          onChange: (text) => {
            data.placeholder = text;
            input.placeholder = text;
            sync();
          },
        })
      : null;

    root.setAttribute("data-citry-editable-initialized", "");
    input.value = draft;
    applyEditing(internalEditing, { focus: internalEditing });
    sync();

    return () => {
      active = false;
      generation += 1;
      root[editableHandoffKey] = {
        serverFingerprint,
        committed,
        draft,
        dirty,
        internalEditing,
      };
      stop?.();
      placeholderBinding?.dispose();
      fieldsetObservers.forEach((observer) => observer.disconnect());
      root.removeEventListener("click", onClick, true);
      root.removeEventListener("pointerdown", onPointerDown, true);
      root.removeEventListener("focusout", onFocusOut);
      input.removeEventListener("input", onInput);
      input.removeEventListener("keydown", onKeyDown);
      input.removeEventListener("invalid", onInvalid);
      input.removeEventListener("compositionstart", onCompositionStart);
      input.removeEventListener("compositionend", onCompositionEnd);
      input.form?.removeEventListener("reset", onReset);
      if (nativeInvalid) field?.setNativeInvalid(false);
      root.removeAttribute("data-citry-editable-initialized");
    };
  },
});

})();