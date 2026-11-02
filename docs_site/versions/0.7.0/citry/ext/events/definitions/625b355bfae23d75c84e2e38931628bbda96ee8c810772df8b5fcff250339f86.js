(function() {

__citryRuntime.registerTypeOptions.bind(null, "CToggleGroup_81ba63", "e099bb200a1685143f7f13cce55748729edb36e191c66330e95b6ddb9c6559d9")({
  props: {value: {}, disabled: {}, orientation: {}, variant: {}, size: {}, onValueChange: {}},
  inject: {formService: {from: Symbol.for("citry-ui:form"), default: null}},
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component;
    const props = component.$props;
    const form = component.formService;
    const owned = () => [...root.querySelectorAll('[data-citry-ui-part="toggle"]')]
      .filter((item) => item.closest('[data-citry-ui-part="toggle-group"]') === root);
    const known = () => new Set(owned().map((item) => item.dataset.value));
    const invalid = new Set();
    let current = data.multiple ? new Set(data.serverValue ?? []) : data.serverValue;
    let callback = null;
    const report = (name, value) => {
      if (invalid.has(name)) return;
      invalid.add(name);
      console.error(`[citry-ui] CToggleGroup ${name} received invalid client value`, value);
    };
    const normalize = (value) => {
      const values = known();
      if (data.multiple) {
        if (!Array.isArray(value)) return undefined;
        const next = value.map((item) => typeof item === "string" ? item.replace(/\r\n?/g, "\n") : null);
        if (next.includes(null) || new Set(next).size !== next.length
            || next.some((item) => !values.has(item))) return undefined;
        return new Set(next);
      }
      if (value === null) return null;
      if (typeof value !== "string") return undefined;
      const next = value.replace(/\r\n?/g, "\n");
      return values.has(next) ? next : undefined;
    };
    const snapshot = (value) => data.multiple ? [...value] : value;
    const apply = (value) => {
      current = value;
      const selected = data.multiple ? value : new Set(value === null ? [] : [value]);
      owned().forEach((item) => {
        const pressed = selected.has(item.dataset.value);
        item.setAttribute("aria-pressed", String(pressed));
        item.toggleAttribute("data-pressed", pressed);
      });
    };
    const resolveChoice = (name, fallback, allowed) => {
      const supplied = props[name];
      if (supplied === undefined) { invalid.delete(name); return fallback; }
      if (typeof supplied === "string" && allowed.includes(supplied)) { invalid.delete(name); return supplied; }
      report(name, supplied);
      return fallback;
    };
    const reconcile = () => {
      callback = typeof props.onValueChange === "function" ? props.onValueChange : null;
      const disabled = props.disabled === undefined ? data.serverDisabled : props.disabled;
      if (typeof disabled !== "boolean") report("disabled", disabled);
      else invalid.delete("disabled");
      const localDisabled = typeof disabled === "boolean" ? disabled : data.serverDisabled;
      const effectiveDisabled = Boolean(form?.disabled) || localDisabled;
      root.toggleAttribute("data-disabled", effectiveDisabled);
      root.dataset.orientation = resolveChoice("orientation", data.serverOrientation, ["horizontal", "vertical"]);
      const variant = resolveChoice("variant", data.serverVariant, ["soft", "outline", "plain"]);
      const size = resolveChoice("size", data.serverSize, ["sm", "md", "lg"]);
      root.dataset.variant = variant;
      root.dataset.size = size;
      owned().forEach((item) => {
        item.disabled = effectiveDisabled || item.hasAttribute("data-item-disabled");
        item.dataset.variant = variant;
        item.dataset.size = size;
      });
      if (props.value !== undefined) {
        const next = normalize(props.value);
        if (next === undefined) report("value", props.value);
        else { invalid.delete("value"); apply(next); }
      }
    };
    const onClick = (event) => {
      const item = event.target.closest?.('[data-citry-ui-part="toggle"]');
      if (!item || item.closest('[data-citry-ui-part="toggle-group"]') !== root || item.disabled) return;
      const previous = snapshot(current);
      let next;
      if (data.multiple) {
        next = new Set(current);
        if (next.has(item.dataset.value)) {
          if (data.mandatory && next.size === 1) return;
          next.delete(item.dataset.value);
        } else next.add(item.dataset.value);
      } else {
        next = current === item.dataset.value ? (data.mandatory ? current : null) : item.dataset.value;
        if (next === current) return;
      }
      const publicValue = snapshot(next);
      callback?.(publicValue, {value: publicValue, previousValue: previous, source: "activation"});
      if (props.value === undefined) apply(next);
      else setTimeout(reconcile, 0);
    };
    root.addEventListener("click", onClick, true);
    const stop = Citry.vue.watchEffect(reconcile);
    root.setAttribute("data-citry-toggle-group-initialized", "");
    return () => {
      stop?.();
      root.removeEventListener("click", onClick, true);
      root.removeAttribute("data-citry-toggle-group-initialized");
    };
  },
})

})();