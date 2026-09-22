$component({
  props: {
    disabled: {default: undefined},
    onAction: {default: undefined},
  },
  computed: {
    resolvedDisabled() {
      return typeof this.disabled === 'boolean' ? this.disabled : this.serverDefaults.disabled;
    },
  },
  onServerRender: ({component}) => {
    const root = component.$refs.root;
    if (!(root instanceof HTMLFieldSetElement)) {
      throw new Error('[citry-ui] CFormCollection settled anatomy is invalid.');
    }
    const invalid = new Set();
    let disabled = component.resolvedDisabled;
    let callback = null;
    const report = (name, value) => {
      if (invalid.has(name)) return;
      invalid.add(name);
      console.error(`[citry-ui] CFormCollection ${name} received invalid client value.`, value, root);
    };
    const items = () => [...root.querySelectorAll(':scope > [data-citry-ui-part="items"] > [data-citry-form-collection-item]')];
    const sync = () => {
      root.toggleAttribute('data-disabled', disabled);
      for (const item of items()) {
        item.toggleAttribute(
          'data-disabled',
          disabled || item.hasAttribute('data-citry-form-collection-item-disabled'),
        );
      }
      for (const button of root.querySelectorAll('[data-citry-form-collection-action]')) {
        const item = button.closest('[data-citry-form-collection-item]');
        const structural = item?.hasAttribute('data-citry-form-collection-item-disabled');
        const serverDisabled = button.dataset.citryFormCollectionActionDisabled === 'true';
        button.disabled = disabled || Boolean(structural) || serverDisabled;
      }
    };
    const onClick = event => {
      const button = event.target.closest('[data-citry-form-collection-action]');
      if (!button || !root.contains(button) || button.disabled || disabled) return;
      const action = button.dataset.citryFormCollectionAction;
      const item = button.closest('[data-citry-form-collection-item]');
      const ordered = items();
      const index = item ? ordered.indexOf(item) : null;
      const toIndex = action === 'move-up' ? Math.max(0, index - 1)
        : action === 'move-down' ? Math.min(ordered.length - 1, index + 1) : null;
      if (callback) {
        try {
          callback({
            action, value: item?.dataset.value ?? null, index, toIndex, sourceEvent: event,
          });
        } catch (error) {
          console.error('[citry-ui] CFormCollection onAction callback failed.', error, root);
        }
      }
    };
    root.addEventListener('click', onClick);
    root.setAttribute('data-citry-form-collection-initialized', '');
    Citry.vue.watchEffect(() => {
      const nextCallback = component.onAction;
      if (nextCallback === undefined || nextCallback === null) { callback = null; invalid.delete('onAction'); }
      else if (typeof nextCallback === 'function') { callback = nextCallback; invalid.delete('onAction'); }
      else report('onAction', nextCallback);
      const nextDisabled = component.disabled;
      if (nextDisabled !== undefined && typeof nextDisabled !== 'boolean') report('disabled', nextDisabled);
      else {
        invalid.delete('disabled');
        disabled = component.resolvedDisabled;
      }
      sync();
    });
    return () => {
      root.removeEventListener('click', onClick);
      root.removeAttribute('data-citry-form-collection-initialized');
    };
  },
});
