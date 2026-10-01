---
title: Update page from Python
description: Render the calling component again from Python, with new inputs, browser data, and CSS.
---

# Update page from Python

The form currently reports success with local browser state. This version has
Python render `SignupForm` again with the accepted address, and the new render
shows a `Confirmation` component in place of the form.

<c-include-file path="docs_site/snippets/getting_started/components_step12.py" language="citry" />

Submit an invalid address to confirm validation still works, then submit
`ada@example.com`. The form becomes a bordered confirmation.

## Render the calling component again

```python
return actions.Render(SignupForm(email=email))
```

With no explicit target, [`actions.Render`][citry.ext.events.actions.Render]
updates the component instance whose handler was called. Python renders
`SignupForm` from scratch with the new `email` input, and Vue updates the
form already on the page to match. This public default avoids coupling a
component handler to an arbitrary page selector.

The Render must use the same component as the instance it updates. To show a
different component, render it from inside the calling component, as
`SignupForm` does with `Confirmation`:

```citry-html
<form
  c-if="email is None"
  @c-submit.prevent="submit"
>
  ...
</form>
<div aria-live="polite">
  <c-Confirmation
    c-if="email is not None"
    c-email="email"
  />
</div>
```

The first render has no address, so it shows the form and an empty
`<div aria-live="polite">`. That live region stays on the page in both renders,
so when the confirmation appears inside it, screen readers announce it.

Returning `actions.Render(Confirmation(email=email))` instead fails in the
browser with an error that names both components, because the page that
holds `SignupForm` still expects a `SignupForm` in that place.

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
it after the update is ready.

## Fragment assets

The full page explicitly places collected assets with `<c-css />` in the head
and `<c-js />` near the end of the body. `Confirmation` only appears later, so
the response that renders it carries any dependencies missing from the first
response. Citry loads those assets before showing the new component. That is
why its border and reactive status appear with the confirmation.

Read [Event actions](/events/actions/) for other handler results and [HTML
fragments](/advanced/html-fragments/) for partial-render details.

## Next steps

Next, [build a CRUD task list](/getting-started/build-crud-pages/).
