---
title: Update page from Python
description: Render a new component into one chosen part of the page, including its browser data and CSS.
---

# Update page from Python

The form currently reports success by changing a line of text in the browser.
For the final step, Python will render a new `Confirmation` component into the
result area.

The form itself will stay where it is. Only the chosen part of the page will
change.

Continue from [Handle and validate a
form](/getting-started/forms/). Keep `citry_setup.py` and `app.py` unchanged.

## Return a rendered update

Replace `components.py` with the finished version:

The file stays focused on the form. The `New in this step` comments mark the
complete change:

- a new `Confirmation` component
- form's new success action and result area
- two places where the page collects component CSS and JavaScript

<c-include-file path="docs_site/snippets/getting_started/components_step12.py" language="citry" />

Open `http://127.0.0.1:8000/`. Try `ada@elsewhere.test` once more to confirm
that the field error still works. Then submit `ada@example.com`.

The placeholder inside the result area becomes a bordered confirmation. Its
status changes to “Confirmation ready for ada@example.com.” The email form
remains above it.

## Confirmation fragment

`Confirmation` is an ordinary component. Focusing only on its input and
visible HTML, it looks like this:

```citry
class Confirmation(Component):
    class Kwargs:
        email: str

    template = """
      <section class="confirmation">
        <strong>Request received</strong>
        <p>We will write to {{ email }}.</p>
        <p
          class="confirmation__status"
          x-text="'Confirmation ready for ' + email"
        >
          Preparing confirmation...
        </p>
      </section>
    """
```

The complete class above also includes its Citry instance, `Slots`, browser
data, and CSS. This smaller excerpt shows the first connection:
`Confirmation(email=email)` supplies the value that `{{ email }}` inserts.

## Render action

The successful handler now returns an
[`actions.Render`][citry.ext.events.actions.Render] action:

```python
return actions.Render(
    Confirmation(email=email),
    target="#signup-result",
    swap="inner",
)
```

`Confirmation(email=email)` builds a fresh component for this response. Citry
renders it as a browser update, including the information needed for that
component's CSS and browser data. The validation path still raises the same
`EventError`; only a successful submission reaches this return statement.

## Swap target selector

The form contains a stable result area:

```citry-html
<div id="signup-result" aria-live="polite">
  <p>Your confirmation will appear here.</p>
</div>
```

[`target="#signup-result"`][citry.ext.events.actions.Render.target] points to
that element with a CSS selector.
[`swap="inner"`][citry.ext.events.actions.Render.swap] replaces its contents
while keeping the `<div id="signup-result">` itself. The form, input, and
button remain where they are. `aria-live="polite"` also lets assistive
technology announce the new confirmation without moving keyboard focus.

Use a selector that identifies the intended area without matching unrelated
elements.

## Confirmation browser data

The confirmation sends its email address to browser code through
[`js_data()`][citry.Component.js_data]:

```python
def js_data(self, kwargs: Kwargs, slots: Slots):
    return {"email": kwargs.email}
```

Citry seeds the top-level `email` key directly into this component's Alpine
scope. The template can use it without a `$component` callback:

```citry-html
<p
  class="confirmation__status"
  x-text="'Confirmation ready for ' + email"
>
  Preparing confirmation...
</p>
```

When the new component starts, Alpine replaces “Preparing confirmation...”
with the finished status. Use `$component` only when a component also needs
imperative JavaScript setup, client prop declarations, effects, or cleanup.

!!! note

    The value returned by `js_data()` must be JSON-serializable.

## Confirmation CSS

`Confirmation` also owns the border that makes the new result visible:

```css
.confirmation {
  border: 2px solid #2f855a;
  border-radius: 0.5rem;
  padding: 1rem;
}
```

## Asset and data loading order

There are two steps when component assets and browser data reach the page:

### 1. First response - Full page

When you first loaded the entire page, `TutorialPage`, Citry automatically
collected its CSS and JavaScript assets and inserted them into the HTML.

You can customize where to insert the assets with [`<c-css />`][c-css] and [`<c-js />`][c-js]. Adding the tags makes the positions explicit. Read more about [asset placement](/advanced/asset-placement/).

```citry-html
<head>
  ...
  <c-css />
</head>
<body>
  ...
  <c-js />
</body>
```

### 2. Second response - Fragment

`Confirmation` is created later. Its CSS and browser data arrive in the
**second** response when the server responds to the form submission, so it
never sees the `<c-css />` and `<c-js />` tags from the first render.

The second response inserts `Confirmation` into the page. Citry collects the
inserted fragment's assets, loads what is still missing, and seeds its Alpine
scope before the new component starts.

That is why the green border appears and the status changes after the confirmation enters the page.

See [Event actions](/events/actions/) for the other results a handler can
return, and [HTML fragments](/advanced/html-fragments/) for a deeper look at
rendering and inserting partial HTML.

## Next steps

You now know how to build a single page with a view events. Next, let's build a [CRUD admin table](/getting-started/build-crud-pages/) to learn how to manage a page with tens to hundreds of components.
