(function() {

__citryRuntime.registerTypeOptions.bind(null, "CToggle_5d9b5a", "7027b43b7b1e26d6a6f6d74cc24633ad63443f9e02ebc30c15b2ce3b4bd2cae3")({
  props: {pressed: {}, disabled: {}, variant: {}, size: {}, onPressedChange: {}},
  inject: {formService: {from: Symbol.for("citry-ui:form"), default: null}},
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component;
    const props = component.$props;
    const groupRoot = root.closest('[data-citry-ui-part="toggle-group"]');
    const form = component.formService;
    const grouped = groupRoot !== null;
    let pressed = data.serverPressed;
    let localDisabled = data.serverDisabled;
    let localVariant = data.serverVariant;
    let localSize = data.serverSize;
    let callback = null;
    const invalid = new Set();
    const report = (name, value) => {
      if (invalid.has(name)) return;
      invalid.add(name);
      console.error(`[citry-ui] CToggle ${name} received invalid client value`, value);
    };
    const apply = () => {
      if (props.disabled === undefined) {
        invalid.delete("disabled");
        localDisabled = data.serverDisabled;
      } else if (typeof props.disabled === "boolean") {
        invalid.delete("disabled");
        localDisabled = props.disabled;
      } else report("disabled", props.disabled);
      root.toggleAttribute("data-item-disabled", localDisabled);
      if (grouped) {
        const effectiveDisabled = grouped
          ? groupRoot.hasAttribute("data-disabled") || localDisabled
          : localDisabled;
        root.disabled = effectiveDisabled;
        root.toggleAttribute("data-disabled", effectiveDisabled);
        for (const name of ["pressed", "variant", "size"]) {
          if (props[name] === undefined) invalid.delete(name);
          else report(name, props[name]);
        }
      } else {
        const effectiveDisabled = Boolean(form?.disabled) || localDisabled;
        root.disabled = effectiveDisabled;
        root.toggleAttribute("data-disabled", effectiveDisabled);
        const choices = {variant: ["soft", "outline", "plain"], size: ["sm", "md", "lg"]};
        for (const [name, allowed] of Object.entries(choices)) {
          if (props[name] === undefined) {
            invalid.delete(name);
            if (name === "variant") localVariant = data.serverVariant;
            else localSize = data.serverSize;
          } else if (allowed.includes(props[name])) {
            invalid.delete(name);
            if (name === "variant") localVariant = props[name];
            else localSize = props[name];
          } else report(name, props[name]);
        }
        root.dataset.variant = localVariant;
        root.dataset.size = localSize;
      }
      callback = typeof props.onPressedChange === "function" ? props.onPressedChange : null;
      if (!grouped && props.pressed === undefined) invalid.delete("pressed");
      else if (!grouped && typeof props.pressed === "boolean") {
        invalid.delete("pressed");
        pressed = props.pressed;
        root.setAttribute("aria-pressed", String(pressed));
        root.toggleAttribute("data-pressed", pressed);
      } else if (!grouped) report("pressed", props.pressed);
    };
    const onClick = () => {
      if (grouped || root.disabled) return;
      const previousValue = pressed;
      const value = !pressed;
      callback?.(value, {value, previousValue, source: "activation"});
      if (props.pressed === undefined) {
        pressed = value;
        root.setAttribute("aria-pressed", String(value));
        root.toggleAttribute("data-pressed", value);
      } else setTimeout(apply, 0);
    };
    root.addEventListener("click", onClick);
    const stop = Citry.vue.watchEffect(apply);
    root.setAttribute("data-citry-toggle-initialized", "");
    return () => {
      stop?.();
      root.removeEventListener("click", onClick);
      root.removeAttribute("data-citry-toggle-initialized");
    };
  },
})

})();