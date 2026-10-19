(function() {

__citryRuntime.registerTypeOptions.bind(null, "CDropTarget_afd2f8", "6afd90a1ce0e2714fddef67593cd2f225eb798d5973e6dcd083d15d3ac536cff")({
  props: {
    accept: {}, capture: {}, multiple: {}, required: {}, disabled: {}, invalid: {},
    variant: {}, size: {},
  },
  inject: {
    formService: {from: Symbol.for("citry-ui:form"), default: null},
  },
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = {...component.serverDefaults, hasForm: component.hasForm};
    const props = component.$props;
    const input = root.querySelector(':scope > [data-citry-ui-part="input"]');
    const form = component.formService;
    const invalidEpisodes = new Set();
    const resetTimers = new Set();
    let nativeInvalid = false;
    let structureValid = false;
    let dragDepth = 0;
    let configuredDisabled = data.disabled;

    const report = (name, value) => {
      if (invalidEpisodes.has(name)) return;
      invalidEpisodes.add(name);
      console.error(`[citry-ui] CDropTarget ${name} received invalid value`, value, root);
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
    const fileDrag = event => [...(event.dataTransfer?.types ?? [])].includes("Files");
    const effectiveDisabled = () => !structureValid || input.matches(":disabled");
    const clearDragging = () => {
      dragDepth = 0;
      root.removeAttribute("data-dragging");
    };
    const syncFiles = () => {
      const hasFiles = input.files.length > 0;
      input.toggleAttribute("data-has-files", hasFiles);
      root.toggleAttribute("data-has-files", hasFiles);
    };
    const invalidStructure = () => {
      const forbiddenSelector = 'a[href], button, input, select, textarea, label, '
        + '[contenteditable]:not([contenteditable="false"]), [tabindex]';
      const forbidden = [...root.querySelectorAll(forbiddenSelector)]
        .find(element => element !== input);
      return forbidden ? forbidden.outerHTML : null;
    };
    const applyState = () => {
      input.accept = optionalString("accept", data.accept) ?? "";
      const capture = optionalString("capture", data.capture, ["user", "environment"]);
      if (capture) input.setAttribute("capture", capture);
      else input.removeAttribute("capture");
      input.multiple = booleanValue("multiple", data.multiple);
      input.required = booleanValue("required", data.required);
      configuredDisabled = Boolean(form?.disabled) || booleanValue("disabled", data.disabled);
      input.disabled = configuredDisabled || !structureValid;
      const invalid = booleanValue("invalid", data.invalid) || nativeInvalid;
      root.toggleAttribute("data-required", input.required);
      root.toggleAttribute("data-disabled", effectiveDisabled());
      root.toggleAttribute("data-invalid", invalid);
      root.dataset.variant = choiceValue("variant", data.variant, ["outline", "soft", "plain"]);
      root.dataset.size = choiceValue("size", data.size, ["sm", "md", "lg"]);
      if (invalid) input.setAttribute("aria-invalid", "true");
      else input.removeAttribute("aria-invalid");
      if (effectiveDisabled()) clearDragging();
      syncFiles();
    };
    const reconcileStructure = () => {
      const problem = invalidStructure();
      structureValid = problem === null;
      if (problem) {
        report("structure", problem);
        root.removeAttribute("data-citry-drop-target-initialized");
      } else {
        invalidEpisodes.delete("structure");
        root.setAttribute("data-citry-drop-target-initialized", "");
      }
      applyState();
    };
    const clearNativeInvalid = () => {
      if (!nativeInvalid || !input.validity.valid) return;
      nativeInvalid = false;
      applyState();
    };
    const onInvalid = () => {
      nativeInvalid = true;
      applyState();
    };
    const onInput = () => {
      syncFiles();
      clearNativeInvalid();
    };
    const onDragEnter = event => {
      if (!fileDrag(event) || effectiveDisabled()) return;
      event.preventDefault();
      dragDepth += 1;
      root.setAttribute("data-dragging", "");
    };
    const onDragOver = event => {
      if (!fileDrag(event) || effectiveDisabled()) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = "copy";
    };
    const onDragLeave = event => {
      if (!fileDrag(event)) return;
      dragDepth = Math.max(0, dragDepth - 1);
      if (dragDepth === 0) root.removeAttribute("data-dragging");
    };
    const onDrop = event => {
      if (!fileDrag(event) || effectiveDisabled()) return;
      event.preventDefault();
      clearDragging();
      const dropped = event.dataTransfer.files;
      if (!dropped.length) return;
      let nextFiles = dropped;
      if (!input.multiple && dropped.length > 1) {
        const transfer = new DataTransfer();
        transfer.items.add(dropped[0]);
        nextFiles = transfer.files;
      }
      try {
        input.files = nextFiles;
      } catch (error) {
        report("drop", error);
        return;
      }
      input.dispatchEvent(new Event("input", {bubbles: true, composed: true}));
      input.dispatchEvent(new Event("change", {bubbles: true, composed: true}));
    };
    const onReset = event => {
      const timer = setTimeout(() => {
        resetTimers.delete(timer);
        if (event.defaultPrevented) return;
        nativeInvalid = false;
        clearDragging();
        applyState();
      }, 0);
      resetTimers.add(timer);
    };
    const nativeForm = input.form;
    const fieldsets = [];
    for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
      if (ancestor instanceof HTMLFieldSetElement) fieldsets.push(ancestor);
    }
    const fieldsetObserver = fieldsets.length ? new MutationObserver(applyState) : null;
    fieldsets.forEach(fieldset => fieldsetObserver.observe(fieldset, {
      childList: true, attributes: true, attributeFilter: ["disabled"],
    }));
    const observer = new MutationObserver(records => {
      if (records.some(record => record.target !== input)) reconcileStructure();
    });
    observer.observe(root, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ["contenteditable", "href", "role", "tabindex"],
    });
    input.addEventListener("invalid", onInvalid);
    input.addEventListener("input", onInput);
    input.addEventListener("change", onInput);
    root.addEventListener("dragenter", onDragEnter);
    root.addEventListener("dragover", onDragOver);
    root.addEventListener("dragleave", onDragLeave);
    root.addEventListener("drop", onDrop);
    nativeForm?.addEventListener("reset", onReset);
    const stop = Citry.vue.watchEffect(applyState);
    reconcileStructure();
    return () => {
      stop?.();
      input.removeEventListener("invalid", onInvalid);
      input.removeEventListener("input", onInput);
      input.removeEventListener("change", onInput);
      root.removeEventListener("dragenter", onDragEnter);
      root.removeEventListener("dragover", onDragOver);
      root.removeEventListener("dragleave", onDragLeave);
      root.removeEventListener("drop", onDrop);
      nativeForm?.removeEventListener("reset", onReset);
      resetTimers.forEach(clearTimeout);
      resetTimers.clear();
      observer.disconnect();
      fieldsetObserver?.disconnect();
      root.removeAttribute("data-citry-drop-target-initialized");
      clearDragging();
    };
  },
});

})();