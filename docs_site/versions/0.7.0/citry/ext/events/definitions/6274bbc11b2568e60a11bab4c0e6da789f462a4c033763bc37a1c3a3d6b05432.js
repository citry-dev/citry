(function() {

__citryRuntime.registerTypeOptions.bind(null, "CListboxOption_dfb80c", "11586305cda2122dabc8008465fc2e04be55931cf54a0272a6a2b6dbc871b96e")({
  props: {disabled: {}, textValue: {}},
  onServerRender: ({component}) => {
    const option = component.$el;
    const defaults = component.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const invalidEpisodes = new Set();
    const report = (name, value) => {
      if (invalidEpisodes.has(name)) return;
      invalidEpisodes.add(name);
      console.error(`[citry-ui] CListboxOption ${name} received invalid client value`, value);
    };
    const stop = effect(() => {
      const suppliedDisabled = props.disabled;
      const disabled = suppliedDisabled === undefined
        ? defaults.disabled
        : typeof suppliedDisabled === 'boolean'
          ? suppliedDisabled
          : defaults.disabled;
      if (suppliedDisabled !== undefined && typeof suppliedDisabled !== 'boolean') {
        report('disabled', suppliedDisabled);
      } else invalidEpisodes.delete('disabled');
      option.toggleAttribute('data-cui-listbox-option-disabled', disabled);
      const suppliedText = props.textValue;
      let textValue = defaults.textValue;
      if (suppliedText === null || suppliedText === undefined) {
        invalidEpisodes.delete('textValue');
      } else if (typeof suppliedText === 'string' && suppliedText.trim() && !suppliedText.includes('\0')) {
        textValue = suppliedText.replace(/\r\n?/g, '\n');
        invalidEpisodes.delete('textValue');
      } else report('textValue', suppliedText);
      if (textValue === null) option.removeAttribute('data-cui-listbox-text-value');
      else option.setAttribute('data-cui-listbox-text-value', textValue);
    });
    return () => stop?.();
  },
})

})();