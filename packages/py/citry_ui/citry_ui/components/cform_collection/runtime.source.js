$component({
  props: {disabled: {}, onAction: {}},
  init: ({els, data, props, effect}) => {
    const root = els[0];
    if (!(root instanceof HTMLFieldSetElement)) {
      throw new Error('[citry-ui] CFormCollection settled anatomy is invalid.');
    }
    const invalid = new Set();
    let disabled = data.disabled;
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
        button.disabled = disabled || Boolean(structural) || button.dataset.citryInitiallyDisabled === 'true';
      }
    };
    for (const button of root.querySelectorAll('[data-citry-form-collection-action]')) {
      button.dataset.citryInitiallyDisabled = String(button.disabled);
    }
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
    effect(() => {
      const nextCallback = props.onAction;
      if (nextCallback === undefined || nextCallback === null) { callback = null; invalid.delete('onAction'); }
      else if (typeof nextCallback === 'function') { callback = nextCallback; invalid.delete('onAction'); }
      else report('onAction', nextCallback);
      const nextDisabled = props.disabled;
      if (nextDisabled !== undefined && typeof nextDisabled !== 'boolean') report('disabled', nextDisabled);
      else {
        invalid.delete('disabled');
        disabled = typeof nextDisabled === 'boolean' ? nextDisabled : data.disabled;
      }
      sync();
    });
    return () => {
      root.removeEventListener('click', onClick);
      root.removeAttribute('data-citry-form-collection-initialized');
    };
  },
});
