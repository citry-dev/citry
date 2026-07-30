---
title: Connect components in the browser
url: https://citry.dev/v/0.3.1/getting-started/client-props-and-handlers/
description: "Pass a reactive browser value into a child Citry component and handle the child's click in its parent."
---
# Connect components in the browser

A parent component can pass Python values to a child while it renders.
After being rendered and loaded in the browser, components can pass JavaScript values in the client.

You will build a choice button whose label follows its parent. Clicking the
child button will change the parent's choice **in the browser**, and the new label will flow back
down to the child.

Start with [Add browser behavior](/v/0.3.1/getting-started/browser-interactivity/) if
you have not used Alpine or [`$component`](/v/0.3.1/reference/browser-apis/#component) in Citry yet.

## Build the parent and child

Save this as `connected_components.py`:


```citry
from citry import Component

class ChoiceButton(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      {# 'x-text' shows current value, as given by parent #}
      <button class="choice-button" type="button">
        Choose
        <span
          class="choice-button__label"
          x-text="clientProps.label"
        ></span>
      </button>
    """

    js = """
      $component({
        // Declare the browser value ChoiceButton accepts
        // through '$c-props'.
        props: {
          label: { type: String, required: true },
        },
        init: ({ props, scope }) => {
          // Share the reactive prop with Alpine.
          scope.clientProps = props;
        },
      });
    """


class ChoicePicker(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      {# 'choice' lives in the parent's 'x-data'  #}
      <section class="choice-picker" x-data="{ choice: 'Ocean' }">
        <p>
          Current choice:
          <output
            class="choice-picker__value"
            x-text="choice"
          ></output>
        </p>

        {# `$c-props` passes 'choice' down as browser data. #}
        {# `@click` allows parent to react to child's click. #}
        <c-ChoiceButton
          $c-props="{ label: choice }"
          @click="choice = choice === 'Ocean' ? 'Forest' : 'Ocean'"
        />
      </section>
    """


class ChoicePage(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Connect components</title>
        </head>
        <body>
          <c-ChoicePicker />
        </body>
      </html>
    """

print(ChoicePage())
```


Create the page and open it:


```sh
python connected_components.py > connected_components.html
```


The parent and button both start with “Ocean.” Click the button and they both
change to “Forest.” Click again and they return to “Ocean.”

## Let the child name the values it needs

[`ChoiceButton.js`](/v/0.3.1/reference/component/#citry-component-js) declares one browser prop called
`label`:


```js
$component({
  props: {
    label: { type: String, required: true },
  },
  init: ({ props, scope }) => {
    scope.clientProps = props;
  },
});
```


Citry checks that the parent supplies a string. The `props` object stays
[reactive](https://alpinejs.dev/advanced/reactivity){: target="_blank" rel="noopener"}, so the span can keep reading `clientProps.label` after the first
render.

This is separate from `Kwargs`. A `Kwargs` value comes from Python while Citry
renders HTML. A client prop comes from browser state and can change without a
new Python render.

## Pass a reactive value down

The parent supplies the current choice with `$c-props`:


```citry-html
<c-ChoiceButton $c-props="{ label: choice }" />
```


The expression runs where the parent wrote it, so `choice` refers to the
parent's Alpine data. Whenever `choice` changes, Citry updates the child's
`label` prop.

Use `$c-props` for values that must remain reactive in the browser. Use an
ordinary option such as `label="Ocean"` or a dynamic Python option such as
`c-label="python_choice"` when the value belongs to the server render.

## Handle the child's click in the parent

The click handler also sits on the child component tag:


```citry-html
<c-ChoiceButton
  $c-props="{ label: choice }"
  @click="choice = choice === 'Ocean' ? 'Forest' : 'Ocean'"
/>
```


The browser listens on the real button rendered by `ChoiceButton`, but the
expression changes the parent component's `choice`. This lets a reusable child
announce an interaction without needing to know what its parent will do next.

The [Client interactivity](/v/0.3.1/concepts/client-interactivity/) guide covers
multiple roots, slots, handler modifiers, and the complete browser-scope rules.

## Let the browser reach Python

So far every interaction has stayed in the browser. Next, [serve the page with
FastAPI](/getting-started/fastapi/) so a later click can reach a Python handler.