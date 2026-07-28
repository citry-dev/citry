---
title: Replace part of the page from Python
description: Render a new component into one chosen part of the page, including the component's JavaScript and CSS.
---

# Replace part of the page from Python

The form currently reports success by changing a line of text in the browser.
For the final step, Python will render a new `Confirmation` component into the
result area.

The form itself will stay where it is. Only the chosen part of the page will
change.

Continue from [Handle and validate a
form](/getting-started/forms/). Keep `citry_setup.py` and `app.py` unchanged.

## Return a rendered update

Replace `components.py` with the finished version:

The `New in this step` comments mark the complete change: the new
`Confirmation` component, the form's new success action and result area, and
the two places where the page collects component CSS and JavaScript.

<c-include-file path="docs_site/snippets/getting_started/components.py" language="citry" />

Open `http://127.0.0.1:8000/`. Try `ada@elsewhere.test` once more to confirm
that the field error still works. Then submit `ada@example.com`.

The placeholder inside the result area becomes a bordered confirmation. Its
status changes to “Confirmation ready for ada@example.com.” The email form
remains above it.

## Build the component Python will return

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
        <p class="confirmation__status">
          Preparing confirmation...
        </p>
      </section>
    """
```

The complete class above also includes its Citry instance, `Slots`, browser
data, JavaScript, and CSS. This smaller excerpt shows the first connection:
`Confirmation(email=email)` supplies the value that `{{ email }}` prints.

## Return the component from the handler

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
component's CSS and JavaScript. The validation path still raises the same
`EventError`; only a successful submission reaches this return statement.

## Choose the part of the page to update

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

## Give the new component browser data

The confirmation sends its email address to browser code through
[`js_data()`][citry.Component.js_data]:

```python
class JsData:
    email: str


def js_data(self, kwargs: Kwargs, slots: Slots) -> JsData:
    return self.JsData(email=kwargs.email)
```

The [`$component`][$component] callback receives that value as `data.email`:

```javascript
$component(({ els, data }) => {
  els[0].querySelector(".confirmation__status").textContent =
    `Confirmation ready for ${data.email}`;
});
```

When the new component starts, this changes “Preparing confirmation...” to the
finished status. As with the browser data from the earlier lesson, the value
returned by `js_data()` must be JSON-serializable.

## Bring the component's styles and script

`Confirmation` also owns the border that makes the new result visible:

```css
.confirmation {
  border: 2px solid #2f855a;
  border-radius: 0.5rem;
  padding: 1rem;
}
```

The full page provides places for component CSS and JavaScript:

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

[`<c-css />`][c-css] and [`<c-js />`][c-js] place the assets needed by
components in the first response. Earlier pages worked without these tags
because Citry can choose the usual document positions automatically. Adding
the tags makes the positions explicit.

`Confirmation` is created later, so its assets arrive with the rendered
update, not through the two tags in the first response. Citry loads them before
the new component starts. That is why the green border appears and the status
changes after the confirmation enters the page.

See [Event actions](/events/actions/) for the other results a handler can
return, and [HTML fragments](/advanced/html-fragments/) for a deeper look at
rendering and inserting partial HTML.

## Keep building

You have now used Citry from both sides of the connection. Python rendered the
first page, browser data handled instant changes, server events called typed
Python handlers, State continued across calls, form errors came back beside
their fields, and a final handler replaced one part of the page with a new
component.

From here:

- use [Examples](/examples/) when you want working code for a specific task;
- read [Docs](/getting-started/installation/) when you want a concept or guided
  workflow; or
- open [Reference](/reference/) when you need the exact API for a class,
  method, or return action.
