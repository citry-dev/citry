import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormCollectionClientActions(Component):
    template = """
      <section x-data>
        <c-CFormCollection
          label="Phone numbers"
          $c-props="{onAction: applyCollectionAction}"
        >
          <c-CFormCollectionItem value="mobile" label="Mobile">
            <label>Number <input name="phones[mobile]" /></label>
          </c-CFormCollectionItem>
          <c-CFormCollectionItem value="office" label="Office">
            <label>Number <input name="phones[office]" /></label>
          </c-CFormCollectionItem>
        </c-CFormCollection>
        <output aria-live="polite" x-text="collectionStatus">Order: Mobile, Office</output>
      </section>
    """

    js = """
      $component({
        init: ({ scope, els, i18n }) => {
        const collection = els[0].querySelector('[data-citry-ui-part="form-collection"]');
        const list = collection.querySelector(':scope > [data-citry-ui-part="items"]');
        const parking = document.createElement('fieldset');
        const parked = document.createElement('ol');
        const bindings = [];
        let nextSequence = 3;
        parking.disabled = true;
        parking.hidden = true;
        parking.append(parked);
        collection.append(parking);

        const bindActionLabel = (button, action, label) => {
          let binding = null;
          if (action === 'move-up') {
            button.setAttribute('aria-label', `Move ${label} up`);
            binding = i18n?.bind({
              message: 'citry-ui-form-collection-move-up',
              values: () => ({ item: label }),
              onChange: value => button.setAttribute('aria-label', value),
            });
          } else if (action === 'move-down') {
            button.setAttribute('aria-label', `Move ${label} down`);
            binding = i18n?.bind({
              message: 'citry-ui-form-collection-move-down',
              values: () => ({ item: label }),
              onChange: value => button.setAttribute('aria-label', value),
            });
          } else {
            button.setAttribute('aria-label', `Remove ${label}`);
            binding = i18n?.bind({
              message: 'citry-ui-form-collection-remove',
              values: () => ({ item: label }),
              onChange: value => button.setAttribute('aria-label', value),
            });
          }
          if (binding) bindings.push(binding);
        };

        const makeAction = (action, symbol, label) => {
          const button = document.createElement('button');
          button.type = 'button';
          button.dataset.citryFormCollectionAction = action;
          button.textContent = symbol;
          bindActionLabel(button, action, label);
          return button;
        };

        const makeItem = () => {
          const sequence = nextSequence;
          nextSequence += 1;
          const value = `phone-${sequence}`;
          const label = `Phone ${sequence}`;
          const labelId = `client-phone-${sequence}-label`;
          const item = document.createElement('li');
          item.className = 'cui-form-collection__item';
          item.dataset.value = value;
          item.dataset.label = label;
          item.dataset.citryFormCollectionItem = '';
          item.dataset.citryUiPart = 'item';

          const group = document.createElement('div');
          group.setAttribute('role', 'group');
          group.setAttribute('aria-labelledby', labelId);
          const header = document.createElement('header');
          header.dataset.citryUiPart = 'item-header';
          const itemLabel = document.createElement('div');
          itemLabel.id = labelId;
          itemLabel.dataset.citryUiPart = 'item-label';
          itemLabel.textContent = label;
          const actions = document.createElement('div');
          actions.dataset.citryUiPart = 'item-actions';
          actions.append(
            makeAction('move-up', '↑', label),
            makeAction('move-down', '↓', label),
            makeAction('remove', '\u00d7', label),
          );
          header.append(itemLabel, actions);

          const content = document.createElement('div');
          content.dataset.citryUiPart = 'item-content';
          const field = document.createElement('label');
          const input = document.createElement('input');
          input.name = `phones[${value}]`;
          field.append('Number ', input);
          content.append(field);
          group.append(header, content);
          item.append(group);
          return item;
        };

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
          add.disabled = false;
          add.dataset.citryInitiallyDisabled = 'false';
          scope.collectionStatus = `Order: ${current.map(item => item.dataset.label).join(', ') || 'No items'}`;
        };

        scope.collectionStatus = 'Order: Mobile, Office';
        scope.applyCollectionAction = (detail) => {
          // The static preview owns this local record set; production owners rerender their own state.
          detail.sourceEvent.preventDefault();
          const button = detail.sourceEvent.target.closest('[data-citry-form-collection-action]');
          let item = button?.closest('[data-citry-form-collection-item]');
          if (detail.action === 'move-up' && item?.previousElementSibling) item.previousElementSibling.before(item);
          else if (detail.action === 'move-down' && item?.nextElementSibling) item.nextElementSibling.after(item);
          else if (detail.action === 'remove' && item) parked.append(item);
          else if (detail.action === 'add') {
            item = parked.lastElementChild || makeItem();
            list.append(item);
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
        return () => bindings.forEach(binding => binding.dispose());
        },
      });
    """


preview = FormCollectionClientActions()
preview  # noqa: B018
