---
title: Connect components in the browser
description: Pass a reactive browser value into a child Citry component and handle the child's click in its parent.
---

# Connect components in the browser

A parent component can pass Python values to a child while it renders.
After being rendered and loaded in the browser, components can pass JavaScript values in the client.

You will build a choice button whose label follows its parent. Clicking the
child button will change the parent's choice **in the browser**, and the new label will flow back
down to the child.

Start with [Add browser behavior](/getting-started/browser-interactivity/) if
you have not used `js_data()` with Alpine in Citry yet. This chapter introduces
[`$component`][$component] because the child needs to declare reactive client
props and run setup logic. Components that only expose `js_data()` values to
their own Alpine expressions do not need it.

## Build the parent and child

Save this as `connected_components.py`:

<c-live-code
  path="docs_site/live_snippets/connected_components.py"
  title="Reactive parent and child components"
/>

Create the page and open it:

```sh
python connected_components.py > connected_components.html
```

The parent and button both start with “Ocean.” Click the button and they both
change to “Forest.” Click again and they return to “Ocean.”

## Child client inputs

[`ChoiceButton.js`][citry.Component.js] declares one browser prop called
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

## Handle the child's click

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

The [Client interactivity](/concepts/client-interactivity/) guide covers
multiple roots, slots, handler modifiers, and the complete browser-scope rules.

## Next steps

So far every interaction has stayed in the browser. Next, [serve the page with
FastAPI](/getting-started/fastapi/) so a later click can reach a Python handler.
