import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormCollectionServerActions(Component):
    template = """
      <form
        method="post"
        action="/team"
        x-data
        @submit.prevent="collectionStatus = 'Saved locally'"
      >
        <c-CFormCollection
          label="Team members"
          action_name="team_action"
          c-max_items="1"
          $c-props="{onAction: applyCollectionAction}"
        >
          <c-CFormCollectionItem value="member-17" label="Ada" remove_value="delete:member-17">
            <input type="hidden" name="members[member-17][id]" value="17" />
            <label>Role <input name="members[member-17][role]" value="Owner" required /></label>
          </c-CFormCollectionItem>
        </c-CFormCollection>
        <button type="submit">Save team</button>
        <output aria-live="polite" x-text="collectionStatus">Order: Ada</output>
      </form>
    """

    js = """
      $component(({ scope, els }) => {
        const collection = els[0].querySelector('[data-citry-ui-part="form-collection"]');
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
          scope.collectionStatus = `Order: ${current.map(item => item.dataset.label).join(', ') || 'No items'}`;
        };

        scope.collectionStatus = 'Order: Ada';
        scope.applyCollectionAction = (detail) => {
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
      });
    """


preview = FormCollectionServerActions()
preview  # noqa: B018
