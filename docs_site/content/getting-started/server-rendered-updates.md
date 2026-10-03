---
title: Update page from Python
description: Replace a component with freshly rendered HTML, browser data, and CSS from a Python event handler.
---

# Update page from Python

Sometimes the result of a call is easier to show as new HTML than as browser
data: a confirmation, an updated table, a different view. A handler can
return a component, and Citry renders it on the server and puts it on the
page.

In the last step, the form showed the accepted address with browser data. In
this step, Python replaces the whole `SignupForm` with a `Confirmation`
component.

Replace `components.py` with:

<c-include-file path="docs_site/snippets/getting_started/components_step12.py" language="citry" />

Submit an invalid address to check that validation still works, then submit
`ada@example.com`. The form becomes a bordered confirmation.

## Return a new component

```python
confirmation = Confirmation(email=email)
return actions.Render(confirmation)
```

[`actions.Render`][citry.ext.events.actions.Render] renders `Confirmation`
on the server and puts it in place of the component whose handler ran, here
`SignupForm`. The response carries everything the new component needs: its
HTML, its browser data, and its CSS.

To update a different part of the page instead, pass a `target`, as
[`<c-mark>` partial update](/events/actions/#update-one-part-of-the-page)
shows.

The swap happens only in the open browser tab. Reloading the page shows the
form again, because `TutorialPage` still renders `SignupForm`.

## Announce the change

`TutorialPage` wraps the form in an `aria-live` region:

```citry-html
<div aria-live="polite">
  <c-SignupForm />
</div>
```

The region belongs to `TutorialPage`, which stays on the page. When
`Confirmation` takes the form's place inside it, screen readers announce the
confirmation.

## Set its browser data

`Confirmation` has its own [`js_data()`][citry.Component.js_data]:

```python
def js_data(self, kwargs: Kwargs, slots: Slots):
    return {"email": kwargs.email}
```

Vue can use `email` as soon as the new component is on the page:

```citry-html
<p
  class="confirmation__status"
  v-text="'Confirmation ready for ' + email"
>
  Preparing confirmation...
</p>
```

The text Python rendered shows until Vue starts. Then `v-text` replaces it.

## Load its CSS and JS

`TutorialPage` now places `<c-css />` in the head and `<c-js />` at the end
of the body. These tags mark where Citry puts the CSS and JavaScript that the
page's components need.

`Confirmation` was not on the first page, so its CSS was not loaded. Citry
sends the missing CSS and JavaScript with the response and loads them before
it shows the new component. That is why the border appears right away.

## Next steps

[Event actions](/events/actions/) lists other things a handler can return,
and [`Render` another component](/events/actions/#swap-in-a-different-component)
lists what the new component does not keep from the old one. [HTML
fragments](/advanced/html-fragments/) covers rendering part of a page in more
depth.

Next, [build a CRUD task list](/getting-started/build-crud-pages/).
