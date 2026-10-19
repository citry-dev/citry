(function() {

__citryRuntime.registerTypeOptions.bind(null, "CTag_ae7eea", "f5ead389f908f08456bf9ab6f0b28f56ed8155a8111b4fe87591a1a35dcdbb87")({
  props: {disabled: {}, textValue: {}},
  onServerRender: ({component}) => {
    // The group's callback reads this tag's entry from the root, so the entry's fields are typed here.
    /** @typedef {{root: HTMLElement, label: Element | null, indicator: Element | null,
     *   remove: Element | null, value: string | undefined, localDisabled: boolean,
     *   disabled: boolean, textValue: string}} TagEntry */
    const root = /** @type {HTMLElement & {__citryTagEntry?: TagEntry}} */ (component.$el);
    const data = component.serverDefaults;
    const props = component.$props;
    const group = root.closest('[data-citry-ui-part="tag-group"]');
    if (!group || root.parentElement !== group.querySelector(':scope > [data-citry-ui-part="list"]')) {
      console.error("[citry-ui] CTag must be a direct child of CTagGroup collection output.");
      root.setAttribute("inert", "");
      return () => {};
    }
    const label = root.querySelector(':scope > .cui-tag__cell > [data-citry-ui-part="tag-label"]');
    const indicator = root.querySelector(':scope > .cui-tag__cell > [data-citry-ui-part="indicator"]');
    const remove = root.querySelector(':scope > .cui-tag__cell > [data-citry-ui-part="remove"]');
    const invalid = new Set();
    let localDisabled = data.disabled;
    let textValue = data.textValue;
    const report = (name, value) => {
      if (invalid.has(name)) return;
      invalid.add(name);
      console.error(`[citry-ui] CTag ${name} received invalid client value`, value);
    };
    const entry = {
      root, label, indicator, remove, value: root.dataset.value,
      localDisabled, disabled: localDisabled, textValue,
    };
    // The group may not have run its callback yet, so publish the entry on
    // this root where the group finds it, then ask the group to reconcile.
    root.__citryTagEntry = entry;
    const apply = () => {
      if (props.disabled === undefined) { invalid.delete("disabled"); localDisabled = data.disabled; }
      else if (typeof props.disabled === "boolean") {
        invalid.delete("disabled"); localDisabled = props.disabled;
      }
      else report("disabled", props.disabled);
      if (props.textValue === undefined || props.textValue === null) {
        invalid.delete("textValue"); textValue = data.textValue;
      } else if (typeof props.textValue === "string"
        && props.textValue.length && !props.textValue.includes("\0")) {
        invalid.delete("textValue"); textValue = props.textValue.replace(/\r\n?/g, "\n");
      } else report("textValue", props.textValue);
      entry.localDisabled = localDisabled;
      entry.textValue = textValue;
      group.__citryTagChanged?.();
    };
    const stop = Citry.vue.watchEffect(apply);
    root.setAttribute("data-citry-tag-initialized", "");
    return () => {
      stop?.();
      delete root.__citryTagEntry;
      group.__citryTagChanged?.();
      root.removeAttribute("data-citry-tag-initialized");
    };
  },
})

})();