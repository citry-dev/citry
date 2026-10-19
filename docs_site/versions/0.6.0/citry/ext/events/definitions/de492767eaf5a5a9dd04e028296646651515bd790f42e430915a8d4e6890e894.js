(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormCollectionServerActions_498cd6", "ab18751c7541a885bb36155896f8ae98577dc1338b2a31dba71007e7ab68cdbb")({
  data() {
    return { collectionStatus: 'Order: Ada' };
  },
  methods: {
    applyCollectionAction(detail) {
      this._collectionRuntime?.apply(detail);
    },
  },
  mounted() {
    const component = this;
    const collection = this.$el.querySelector('[data-citry-ui-part="form-collection"]');
  const list = collection.querySelector(':scope > [data-citry-ui-part="items"]');
  const parking = document.createElement('fieldset');
  const parked = document.createElement('ol');
  const maximum = list.children.length;
  parking.disabled = true;
  parking.hidden = true;
  parking.append(parked);
  collection.append(parking);

  const items = () => [...list.querySelectorAll(':scope > [data-citry-form-collection-item]')];
  const sync = () => {
    const current = items();
    collection.dataset.count = String(current.length);
    current.forEach((item, index) => {
      item.toggleAttribute('data-first', index === 0);
      item.toggleAttribute('data-last', index === current.length - 1);
      for (const button of item.querySelectorAll('[data-citry-form-collection-action]')) {
        const fixed = item.hasAttribute('data-citry-form-collection-item-disabled');
        const action = button.dataset.citryFormCollectionAction;
        const unavailable = fixed
          || (action === 'move-up' && index === 0)
          || (action === 'move-down' && index === current.length - 1);
        button.disabled = unavailable;
        button.dataset.citryInitiallyDisabled = String(unavailable);
      }
    });
    const add = collection.querySelector('[data-citry-ui-part="add"]');
    add.disabled = current.length >= maximum || parked.children.length === 0;
    add.dataset.citryInitiallyDisabled = String(add.disabled);
    component.collectionStatus = `Order: ${current.map(item => item.dataset.label).join(', ') || 'No items'}`;
  };

  const apply = (detail) => {
    // Static docs accept the named request locally; a real server returns a keyed rerender.
    detail.sourceEvent.preventDefault();
    const button = detail.sourceEvent.target.closest('[data-citry-form-collection-action]');
    let item = button?.closest('[data-citry-form-collection-item]');
    if (detail.action === 'move-up' && item?.previousElementSibling) item.previousElementSibling.before(item);
    else if (detail.action === 'move-down' && item?.nextElementSibling) item.nextElementSibling.after(item);
    else if (detail.action === 'remove' && item) parked.append(item);
    else if (detail.action === 'add') {
      item = parked.lastElementChild;
      if (item) list.append(item);
    }
    sync();
    requestAnimationFrame(() => {
      const focusTarget = item?.isConnected && !parked.contains(item)
        ? item.querySelector('button:not(:disabled), input:not(:disabled)')
        : collection.querySelector('[data-citry-ui-part="add"]');
      focusTarget?.focus();
    });
  };
  sync();
  Object.defineProperty(this, '_collectionRuntime', {
    configurable: true,
    value: {apply},
  });
  },
  beforeUnmount() {
    delete this._collectionRuntime;
  },
});

})();