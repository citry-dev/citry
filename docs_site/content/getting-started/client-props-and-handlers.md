---
title: Connect components in the browser
description: Pass a reactive value into a child Citry component and handle an event the child emits.
---

# Connect components in the browser

A parent can pass a reactive browser value to a child component. The child can
emit an event without deciding what its parent should do.

You will build a choice button whose label follows its parent. Clicking it
changes the parent's choice in the browser, then the new label flows back down.

## Build the parent and child

<c-live-code path="docs_site/live_snippets/connected_components.py" title="Reactive parent and child components" />

```sh
python connected_components.py > connected_components.html
```

The picker starts at “Ocean.” Each click alternates between “Forest” and
“Ocean.”

## Declare the child's public client contract

The child declares a `label` prop and a `select` event with Vue Options:

```js
$component({
  props: {
    label: { type: String, required: true },
  },
  emits: ['select'],
});
```

The template reads `label` directly with `v-text` and emits from the button:

```citry-html
<button type="button" @click="$emit('select')">
  Choose <span v-text="label"></span>
</button>
```

Client props differ from [`Kwargs`][citry.Component.Kwargs]. Kwargs are Python
inputs resolved while rendering. Props are Vue inputs whose values can change
without another Python render. See Vue's official guides to
[props](https://vuejs.org/guide/components/props.html){: target="_blank" rel="noopener"}
and [component events](https://vuejs.org/guide/components/events.html){: target="_blank" rel="noopener"}.

## Bind the prop and event in the parent

```citry-html
<c-ChoiceButton :label="choice" @select="toggleChoice" />
```

`:label` evaluates `choice` in the parent and keeps the child prop updated.
`@select` calls the parent's method when the child emits. The parent owns the
state and decision:

```js
$component({
  data() {
    return { choice: 'Ocean' };
  },
  methods: {
    toggleChoice() {
      this.choice = this.choice === 'Ocean' ? 'Forest' : 'Ocean';
    },
  },
});
```

The [Client interactivity](/concepts/client-interactivity/) guide covers slots,
multiple roots, lifecycle hooks, and the full browser API.

## Next steps

Next, [serve the page with FastAPI](/getting-started/fastapi/) so a later click
can reach Python.
