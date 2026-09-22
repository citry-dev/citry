---
title: Update page from Python
description: Replace the calling component with freshly rendered HTML, browser data, and CSS.
---

# Update page from Python

The form currently reports success with local browser state. This version has
Python replace the successful `SignupForm` with a `Confirmation` component.

<c-include-file path="docs_site/snippets/getting_started/components_step12.py" language="citry" />

Submit an invalid address to confirm validation still works, then submit
`ada@example.com`. The form becomes a bordered confirmation.

## Render the replacement

```python
return actions.Render(Confirmation(email=email))
```

With no explicit target, [`actions.Render`][citry.ext.events.actions.Render]
updates the component instance whose handler was called. `Confirmation` is a
fresh component tree, so its HTML, browser data, and CSS travel in the fragment
response. This public default avoids coupling a component handler to an
arbitrary page selector.

## Browser data in the new component

```python
def js_data(self, kwargs: Kwargs, slots: Slots):
    return {"email": kwargs.email}
```

The top-level `email` value is reactive and available to Vue:

```citry-html
<p
  class="confirmation__status"
  v-text="'Confirmation ready for ' + email"
>
  Preparing confirmation...
</p>
```

The server-rendered text remains useful before Vue mounts. `v-text` replaces
it after the fragment is ready.

## Fragment assets

The full page explicitly places collected assets with `<c-css />` in the head
and `<c-js />` near the end of the body. `Confirmation` only appears later, so
its fragment carries any dependencies missing from the first response. Citry
loads those assets before activating the new component. That is why its border
and reactive status appear after replacement.

Read [Event actions](/events/actions/) for other handler results and [HTML
fragments](/advanced/html-fragments/) for partial-render details.

## Next steps

Next, [build a CRUD task list](/getting-started/build-crud-pages/).
