---
title: Form Collection
url: https://citry.dev/v/0.4.3/ui-library/components/form-collection/
description: "Compose keyed repeatable field groups inside one real form with accessible add remove and reorder requests."
---
# Form Collection

Use `CFormCollection` for an ordered set of repeated fields or repeated
multi-field groups. It never creates a nested form. Put it inside your normal
`form` or `CForm`, and keep names, parsing, records, and persistence in the
application.

## Repeat one field

Each `CFormCollectionItem` has a stable `value`, a visible `label`, and ordinary
form controls in its default slot.


### Collect several email addresses

[Open the rendered preview](/v/0.4.3/ui-library/components/form-collection/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormCollectionAtAGlance(Component):
    template = """
      <form>
        <c-CFormCollection
          label="Email addresses"
          c-allow_add="False"
          c-allow_remove="False"
          c-allow_reorder="False"
        >
          <c-CFormCollectionItem value="primary" label="Primary email">
            <label>Email <input name="emails[primary]" type="email" value="ada@example.com" /></label>
          </c-CFormCollectionItem>
          <c-CFormCollectionItem value="backup" label="Backup email">
            <label>Email <input name="emails[backup]" type="email" /></label>
          </c-CFormCollectionItem>
        </c-CFormCollection>
      </form>
    """


preview = FormCollectionAtAGlance()
preview  # noqa: B018
````


The component does not rewrite indexes or bracketed names. Choose stable keys
when an edit must survive a keyed server rerender.

## Repeat a multi-field group

An Item may contain any coherent set of fields. All controls remain direct
members of the one outer form for native validation, autofill, reset, and
`FormData`.


### Edit several contacts

[Open the rendered preview](/v/0.4.3/ui-library/components/form-collection/_previews/field-groups/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormCollectionFieldGroups(Component):
    template = """
      <form>
        <c-CFormCollection
          label="Escalation contacts"
          description="Contacts are notified in shown order."
          c-allow_add="False"
          c-allow_remove="False"
          c-allow_reorder="False"
        >
          <c-CFormCollectionItem value="primary" label="Primary contact">
            <label>Name <input name="contacts[primary][name]" value="Ada Lovelace" /></label>
            <label>Email <input name="contacts[primary][email]" type="email" value="ada@example.com" /></label>
          </c-CFormCollectionItem>
          <c-CFormCollectionItem value="secondary" label="Secondary contact">
            <label>Name <input name="contacts[secondary][name]" value="Grace Hopper" /></label>
            <label>Email <input name="contacts[secondary][email]" type="email" value="grace@example.com" /></label>
          </c-CFormCollectionItem>
        </c-CFormCollection>
      </form>
    """


preview = FormCollectionFieldGroups()
preview  # noqa: B018
````


Nested collections may be placed inside Item content, but the first release
does not coordinate their action protocols or focus policy.

## Handle requests with Citry Events

Set `action_name` to turn Add, Remove, Move up, and Move down into real named
submit buttons. Each uses `formnovalidate`, so an incomplete new row does not
block a collection mutation. The server reads the activated button's value and
returns a keyed rerender.


### Send collection actions through the outer form

[Open the rendered preview](/v/0.4.3/ui-library/components/form-collection/_previews/server-actions/)

````citry
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
````


The docs preview accepts those named requests locally because this static page
has no application endpoint. In an application, let the named submit continue
and return the updated keyed collection from the server.

Defaults encode `add`, `remove:<value>`, `move-up:<value>`, and
`move-down:<value>`. Override each value when your server protocol differs.
For example, `remove_value="delete:member-17"` makes the Remove button submit
`team_action=delete:member-17`. The colon has no Citry-specific meaning; the
whole string is simply the application-defined value of the activated submit
button.

## Handle requests in Alpine

Without `action_name`, controls use `type=button`. Pass `onAction` through
`$c-props` to receive `{action, value, index, toIndex, sourceEvent}` and update
application state or send a Citry Event.


### Apply client collection requests

[Open the rendered preview](/v/0.4.3/ui-library/components/form-collection/_previews/client-actions/)

````citry
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

          const group = document.createElement('section');
          group.setAttribute('role', 'group');
          group.setAttribute('aria-labelledby', labelId);
          const header = document.createElement('header');
          header.dataset.citryUiPart = 'item-header';
          const heading = document.createElement('h3');
          heading.id = labelId;
          heading.dataset.citryUiPart = 'item-label';
          heading.textContent = label;
          const actions = document.createElement('div');
          actions.dataset.citryUiPart = 'item-actions';
          actions.append(
            makeAction('move-up', '↑', label),
            makeAction('move-down', '↓', label),
            makeAction('remove', '\u00d7', label),
          );
          header.append(heading, actions);

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
````


The component deliberately does not clone existing component DOM. The owner
must add, remove, or reorder records and render the resulting keyed Items.
The preview emulates that owner locally. It creates stable records for new
phone fields and keeps removed Items connected while applying the same callback
details, so Add remains unbounded and edits survive reorder and restoration on
this static page.

## Limit available actions

`min_items` and `max_items` guard Remove and Add controls. Root `disabled`
disables mutation controls without silently disabling consumer fields.
`removable`, `movable`, and Item `disabled` refine one group.


### Keep required and fixed groups

[Open the rendered preview](/v/0.4.3/ui-library/components/form-collection/_previews/limits/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormCollectionLimits(Component):
    template = """
      <c-CFormCollection label="Approvers" c-min_items="1" c-max_items="2">
        <c-CFormCollectionItem value="owner" label="Account owner" c-removable="False" c-movable="False">
          <label>Email <input name="approvers[owner]" value="owner@example.com" /></label>
        </c-CFormCollectionItem>
        <c-CFormCollectionItem value="security" label="Security reviewer" c-disabled="True">
          <label>Email <input name="approvers[security]" value="security@example.com" /></label>
        </c-CFormCollectionItem>
      </c-CFormCollection>
    """


preview = FormCollectionLimits()
preview  # noqa: B018
````


If the entire form group must stop submitting, disable its actual native
controls or an application-owned ancestor fieldset too.

## Preserve edits and choose focus

Citry keyed rerenders can retain surviving native controls, their browser-owned
edits, selection, and focus while Items reorder. After adding or removing an
Item, the application chooses the new focus target because it owns the new
record and business policy.


### Label repeated shipping addresses

[Open the rendered preview](/v/0.4.3/ui-library/components/form-collection/_previews/accessibility/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormCollectionAccessibility(Component):
    template = """
      <form>
        <c-CFormCollection
          label="Shipping addresses"
          description="The first address is used by default."
          c-allow_add="False"
          c-allow_remove="False"
          c-allow_reorder="False"
        >
          <c-CFormCollectionItem value="home" label="Home address">
            <label>Street <input name="addresses[home][street]" autocomplete="street-address" /></label>
            <label>City <input name="addresses[home][city]" autocomplete="address-level2" /></label>
          </c-CFormCollectionItem>
          <c-CFormCollectionItem value="office" label="Office address">
            <label>Street <input name="addresses[office][street]" /></label>
            <label>City <input name="addresses[office][city]" /></label>
          </c-CFormCollectionItem>
        </c-CFormCollection>
      </form>
    """


preview = FormCollectionAccessibility()
preview  # noqa: B018
````


The fieldset, legend, grouped Items, and native buttons provide the semantic
baseline. Action labels come from Citry UI catalog messages; application Item
labels and fields retain their own locale and direction.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CFormCollection server inputs

Server inputs are passed in a template through `<c-CFormCollection ... />` or in Python
through `CFormCollection(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="form-collection-input-cform-collection-server-inputs-label"></span>`label` | `str` | required | Supplies the visible native legend and collection name. |
| <span id="form-collection-input-cform-collection-server-inputs-id"></span>`id` | `str | None` | generated | Sets the fieldset ID and bases stable Item label IDs. |
| <span id="form-collection-input-cform-collection-server-inputs-description"></span>`description` | `str | None` | `None` | Adds plain described-by guidance below the legend. |
| <span id="form-collection-input-cform-collection-server-inputs-action-name"></span>`action_name` | `str | None` | `None` | When supplied actions are named submit buttons; otherwise they are client-only Buttons. |
| <span id="form-collection-input-cform-collection-server-inputs-add-value"></span>`add_value` | `str` | `"add"` | Sets the Add submit-button value. |
| <span id="form-collection-input-cform-collection-server-inputs-allow-add"></span>`allow_add` | `bool` | `True` | Includes the Add control. |
| <span id="form-collection-input-cform-collection-server-inputs-allow-remove"></span>`allow_remove` | `bool` | `True` | Includes permitted Item Remove controls. |
| <span id="form-collection-input-cform-collection-server-inputs-allow-reorder"></span>`allow_reorder` | `bool` | `True` | Includes permitted Move controls. |
| <span id="form-collection-input-cform-collection-server-inputs-min-items"></span>`min_items` | `int` | `0` | Rejects fewer rendered Items and disables Remove at the minimum. |
| <span id="form-collection-input-cform-collection-server-inputs-max-items"></span>`max_items` | `int | None` | `None` | Rejects more rendered Items and disables Add at the maximum. |
| <span id="form-collection-input-cform-collection-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables collection mutation controls without disabling consumer fields. |
| <span id="form-collection-input-cform-collection-server-inputs-size"></span>`size` | `CFormCollectionSize` ([`CFormCollectionSize`](#form-collection-interface-size)) | `"md"` | Selects collection spacing density. |
| <span id="form-collection-input-cform-collection-server-inputs-add-label"></span>`add_label` | `str` | `"Add item"` | Overrides the localized Add text. |
| <span id="form-collection-input-cform-collection-server-inputs-remove-label"></span>`remove_label` | `str` | `"Remove {item}"` | Overrides localized Remove names and must retain item. |
| <span id="form-collection-input-cform-collection-server-inputs-move-up-label"></span>`move_up_label` | `str` | `"Move {item} up"` | Overrides localized Move up names and must retain item. |
| <span id="form-collection-input-cform-collection-server-inputs-move-down-label"></span>`move_down_label` | `str` | `"Move {item} down"` | Overrides localized Move down names and must retain item. |
| <span id="form-collection-input-cform-collection-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#form-collection-interface-class-value)) | `None` | Adds classes to the fieldset. |
| <span id="form-collection-input-cform-collection-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#form-collection-interface-style-value)) | `None` | Adds styles to the fieldset. |
| <span id="form-collection-input-cform-collection-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed fieldset attributes. |

</div>

#### CFormCollection client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CFormCollection />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="form-collection-input-cform-collection-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server value. | Reactively disables mutation controls. |
| <span id="form-collection-input-cform-collection-client-inputs-on-action"></span>`onAction` | `function` | No component callback runs. | Receives Add Remove Move up and Move down requests. |

</div>

#### CFormCollectionItem server inputs

Server inputs are passed in a template through `<c-CFormCollectionItem ... />` or in Python
through `CFormCollectionItem(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="form-collection-input-cform-collection-item-server-inputs-value"></span>`value` | `str` | required | Supplies unique stable Item identity and default action-value suffix. |
| <span id="form-collection-input-cform-collection-item-server-inputs-label"></span>`label` | `str` | required | Supplies the visible group heading and action-name interpolation. |
| <span id="form-collection-input-cform-collection-item-server-inputs-remove-value"></span>`remove_value` | `str | None` | generated | Overrides the default remove colon value action protocol. |
| <span id="form-collection-input-cform-collection-item-server-inputs-move-up-value"></span>`move_up_value` | `str | None` | generated | Overrides the default move-up colon value action protocol. |
| <span id="form-collection-input-cform-collection-item-server-inputs-move-down-value"></span>`move_down_value` | `str | None` | generated | Overrides the default move-down colon value action protocol. |
| <span id="form-collection-input-cform-collection-item-server-inputs-removable"></span>`removable` | `bool` | `True` | Includes this Item's Remove control when root removal is allowed. |
| <span id="form-collection-input-cform-collection-item-server-inputs-movable"></span>`movable` | `bool` | `True` | Includes this Item's Move controls when root reorder is allowed. |
| <span id="form-collection-input-cform-collection-item-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables this Item's collection actions only. |
| <span id="form-collection-input-cform-collection-item-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#form-collection-interface-class-value)) | `None` | Adds classes to the Item group. |
| <span id="form-collection-input-cform-collection-item-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#form-collection-interface-style-value)) | `None` | Adds styles to the Item group. |
| <span id="form-collection-input-cform-collection-item-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed Item-group attributes. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CFormCollection slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="form-collection-slot-cform-collection-slots-default"></span>`default` | no | `{}` ([`CFormCollectionDefaultSlotData`](#form-collection-interface-cform-collection-default-slot-data)) | Empty collection. |

</div>

#### CFormCollectionItem slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="form-collection-slot-cform-collection-item-slots-default"></span>`default` | yes | `{value, label, index, count, is_first, is_last, disabled}` ([`CFormCollectionItemSlotData`](#form-collection-interface-cform-collection-item-slot-data)) | None; contains the actual repeated fields. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CFormCollection events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="form-collection-event-cform-collection-events-action"></span>`onAction` | `(detail: CFormCollectionActionDetail) => void` ([`CFormCollectionActionDetail`](#form-collection-interface-cform-collection-action-detail)) | An enabled collection action Button is activated. | `{action, value, index, toIndex, sourceEvent}` ([`CFormCollectionActionDetail`](#form-collection-interface-cform-collection-action-detail)) | Reports a request and never mutates the collection DOM. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CFormCollection CSS variables

Apply these variables to `CFormCollection` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="form-collection-css-cform-collection-css-variables-gap"></span>`--cui-form-collection-gap` | `length` | Space between Item groups and Add. | `0.875rem` |
| <span id="form-collection-css-cform-collection-css-variables-surface"></span>`--cui-form-collection-item-surface` | `color` | Item group surface. | `Canvas` |
| <span id="form-collection-css-cform-collection-css-variables-border"></span>`--cui-form-collection-item-border` | `complete border` | Item and header boundary. | `Adaptive 1px neutral` |
| <span id="form-collection-css-cform-collection-css-variables-radius"></span>`--cui-form-collection-item-radius` | `length` | Item corners. | `0.75rem` |
| <span id="form-collection-css-cform-collection-css-variables-action-gap"></span>`--cui-form-collection-action-gap` | `length` | Gap between mutation controls. | `0.375rem` |
| <span id="form-collection-css-cform-collection-css-variables-focus"></span>`--cui-form-collection-focus` | `color` | Mutation-control focus ring. | `Highlight` |
| <span id="form-collection-css-cform-collection-css-variables-disabled-opacity"></span>`--cui-form-collection-disabled-opacity` | `number` | Disabled collection and control opacity. | `0.55` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CFormCollection attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="form-collection-attribute-cform-collection-attributes-data-count"></span>`data-count` | Root | `nonnegative integer string` | Reflects rendered Item count. |
| <span id="form-collection-attribute-cform-collection-attributes-data-size"></span>`data-size` | Root | `CFormCollectionSize` ([`CFormCollectionSize`](#form-collection-interface-size)) | Reflects spacing density. |
| <span id="form-collection-attribute-cform-collection-attributes-data-disabled"></span>`data-disabled` | Root and Item | `present | absent` | Reflects unavailable collection actions. |
| <span id="form-collection-attribute-cform-collection-attributes-data-first"></span>`data-first` | Item | `present | absent` | Marks first current Item. |
| <span id="form-collection-attribute-cform-collection-attributes-data-last"></span>`data-last` | Item | `present | absent` | Marks last current Item. |
| <span id="form-collection-attribute-cform-collection-attributes-data-value"></span>`data-value` | Item | `string` | Exposes stable Item identity. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CFormCollection selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="form-collection-selector-cform-collection-selectors-form-collection"></span>`[data-citry-ui-part="form-collection"]` | Native fieldset root | Semantic theme and reflected-state destination. |
| <span id="form-collection-selector-cform-collection-selectors-legend"></span>`[data-citry-ui-part="legend"]` | Native legend | Visible collection name. |
| <span id="form-collection-selector-cform-collection-selectors-description"></span>`[data-citry-ui-part="description"]` | Optional paragraph | Collection guidance. |
| <span id="form-collection-selector-cform-collection-selectors-items"></span>`[data-citry-ui-part="items"]` | Ordered list | Current server Item order. |
| <span id="form-collection-selector-cform-collection-selectors-item"></span>`[data-citry-ui-part="item"]` | Grouped list item | Stable repeated group. |
| <span id="form-collection-selector-cform-collection-selectors-item-header"></span>`[data-citry-ui-part="item-header"]` | Header | Groups label and actions. |
| <span id="form-collection-selector-cform-collection-selectors-item-label"></span>`[data-citry-ui-part="item-label"]` | Heading | Visible Item group name. |
| <span id="form-collection-selector-cform-collection-selectors-item-actions"></span>`[data-citry-ui-part="item-actions"]` | Action container | Move and Remove controls. |
| <span id="form-collection-selector-cform-collection-selectors-item-content"></span>`[data-citry-ui-part="item-content"]` | Content div | Actual repeated fields. |
| <span id="form-collection-selector-cform-collection-selectors-add"></span>`[data-citry-ui-part="add"]` | Native Button | Add request. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="form-collection-interface-size"></span>`CFormCollectionSize` | `Literal["sm", "md", "lg"]` |
| <span id="form-collection-interface-action"></span>`CFormCollectionAction` | `Literal["add", "remove", "move-up", "move-down"]` |
| <span id="form-collection-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="form-collection-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="form-collection-interface-cform-collection-default-slot-data"></span>

#### `CFormCollectionDefaultSlotData`

Empty dataclass: `{}`.

<span id="form-collection-interface-cform-collection-item-slot-data"></span>

#### `CFormCollectionItemSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="form-collection-interface-cform-collection-item-slot-data-value"></span>`value` | `str` | - | Stable Item identity. |
| <span id="form-collection-interface-cform-collection-item-slot-data-label"></span>`label` | `str` | - | Plain application-owned Item label. |
| <span id="form-collection-interface-cform-collection-item-slot-data-index"></span>`index` | `int` | - | Zero-based current server index. |
| <span id="form-collection-interface-cform-collection-item-slot-data-count"></span>`count` | `int` | - | Current rendered Item count. |
| <span id="form-collection-interface-cform-collection-item-slot-data-is-first"></span>`is_first` | `bool` | - | Whether this is the first Item. |
| <span id="form-collection-interface-cform-collection-item-slot-data-is-last"></span>`is_last` | `bool` | - | Whether this is the last Item. |
| <span id="form-collection-interface-cform-collection-item-slot-data-disabled"></span>`disabled` | `bool` | - | Initial effective collection-action disabled state. |

</div>

<span id="form-collection-interface-cform-collection-action-detail"></span>

#### `CFormCollectionActionDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="form-collection-interface-cform-collection-action-detail-action"></span>`action` | `CFormCollectionAction` ([`CFormCollectionAction`](#form-collection-interface-action)) | - | Requested mutation. |
| <span id="form-collection-interface-cform-collection-action-detail-value"></span>`value` | `str | None` | - | Item value or null for Add. |
| <span id="form-collection-interface-cform-collection-action-detail-index"></span>`index` | `int | None` | - | Current Item index or null for Add. |
| <span id="form-collection-interface-cform-collection-action-detail-to-index"></span>`toIndex` | `int | None` | - | Requested adjacent destination or null. |
| <span id="form-collection-interface-cform-collection-action-detail-source-event"></span>`sourceEvent` | `object` | - | Native click Event. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CFormCollection translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="form-collection-translation-cform-collection-translations-add"></span>`citry-ui-form-collection-add` | Labels the Add control. | `None.` | `add_label` | Stable `$c-tr` text. |
| <span id="form-collection-translation-cform-collection-translations-remove"></span>`citry-ui-form-collection-remove` | Names an Item Remove control. | `item: str` | `remove_label` with `{item}` | Stable reactive `$c-tr` attribute. |
| <span id="form-collection-translation-cform-collection-translations-move-up"></span>`citry-ui-form-collection-move-up` | Names an Item Move up control. | `item: str` | `move_up_label` with `{item}` | Stable reactive `$c-tr` attribute. |
| <span id="form-collection-translation-cform-collection-translations-move-down"></span>`citry-ui-form-collection-move-down` | Names an Item Move down control. | `item: str` | `move_down_label` with `{item}` | Stable reactive `$c-tr` attribute. |

</div>