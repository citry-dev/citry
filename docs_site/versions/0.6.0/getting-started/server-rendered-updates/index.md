---
title: Update page from Python
url: https://citry.dev/v/0.6.0/getting-started/server-rendered-updates/
description: "Replace a component with freshly rendered HTML, browser data, and CSS from a Python event handler."
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

```citry
from citry_setup import citry_app

from citry import Component
from citry.ext.events import EventError, actions


# New in this step: render this component after a valid form.
class Confirmation(Component):
    citry = citry_app

    class Kwargs:
        email: str

    class Slots:
        pass

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"email": kwargs.email}

    template = """
      <section class="confirmation">
        <strong>Request received</strong>
        <p>We will write to {{ email }}.</p>
        <p
          class="confirmation__status"
          v-text="'Confirmation ready for ' + email"
        >
          Preparing confirmation...
        </p>
      </section>
    """

    css = """
      .confirmation {
        border: 2px solid #2f855a;
        border-radius: 0.5rem;
        padding: 1rem;
      }
    """


class SignupIn:
    email: str


class SignupForm(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    class Events:
        def submit(self, data: SignupIn):
            email = data.email.strip()
            if not email.endswith("@example.com"):
                raise EventError(
                    "Please fix the email address.",
                    fields={"email": "Use an @example.com address."},
                )
            # New in this step: put Confirmation in place of this form.
            confirmation = Confirmation(email=email)
            return actions.Render(confirmation)

    template = """
      <section class="signup-form">
        <form @c-submit.prevent="submit">
          <label>
            Work email
            <input
              name="email"
              type="email"
              autocomplete="email"
              required
            />
            <span
              class="signup-form__error"
              role="alert"
              v-show="$error('submit')?.fieldErrors?.email"
              v-text="$error('submit')?.fieldErrors?.email || ''"
            ></span>
          </label>
          <button
            type="submit"
            :disabled="$loading('submit')"
            v-text="$loading('submit') ? 'Sending' : 'Send request'"
          >
            Send request
          </button>
        </form>
      </section>
    """


class TutorialPage(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Join the reading room</title>
          {# New in this step: place collected component CSS. #}
          <c-css />
        </head>
        <body>
          <main>
            <h1>Join the reading room</h1>
            {# New in this step: Confirmation replaces SignupForm, #}
            {# so a live region outside it stays on the page and #}
            {# screen readers announce the confirmation. #}
            <div aria-live="polite">
              <c-SignupForm />
            </div>
          </main>
          {# New in this step: place collected component JS. #}
          <c-js />
        </body>
      </html>
    """

```

Submit an invalid address to check that validation still works, then submit
`ada@example.com`. The form becomes a bordered confirmation.

## Return a new component


```python
confirmation = Confirmation(email=email)
return actions.Render(confirmation)
```


[`actions.Render`](/v/0.6.0/reference/events/#citry-ext-events-actions-render) renders `Confirmation`
on the server and puts it in place of the component whose handler ran, here
`SignupForm`. The response carries everything the new component needs: its
HTML, its browser data, and its CSS.

To update a different part of the page instead, pass a `target`, as
[`<c-mark>` partial update](/v/0.6.0/events/actions/#update-one-part-of-the-page)
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

`Confirmation` has its own [`js_data()`](/v/0.6.0/reference/component/#citry-component-js-data):


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

[Event actions](/v/0.6.0/events/actions/) lists other things a handler can return,
and [`Render` another component](/v/0.6.0/events/actions/#swap-in-a-different-component)
lists what the new component does not keep from the old one. [HTML
fragments](/advanced/html-fragments/) covers rendering part of a page in more
depth.

Next, [build a CRUD task list](/v/0.6.0/getting-started/build-crud-pages/).