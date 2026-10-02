---
title: Connect components in the browser
description: Pass a browser value into a child Citry component and handle an event the child sends.
---

# Connect components in the browser

Often a parent component holds a value and a child component shows it or asks
to change it, all in the browser: a picker and its button, a list and its
filter. In Vue, the parent passes the value down as a **prop**, and the child
sends a named **event** up when something happens. The child does not decide
what the event does; the parent does.

In this step you build a choice button whose label comes from its parent.
Clicking the button tells the parent, the parent changes its choice, and the
new label shows in the button.

## Build parent and child

Save this as `connected_components.py`:

<c-live-code path="docs_site/live_snippets/connected_components.py" title="Reactive parent and child components" />

```sh
python connected_components.py > connected_components.html
```

The picker starts at “Ocean.” Each click switches between “Forest” and
“Ocean.”

## Declare props and events

`ChoiceButton` declares a `label` prop and a `select` event in its Vue
options:

```js
$component({
  props: {
    label: { type: String, required: true },
  },
  emits: ['select'],
});
```

The template shows `label` with `v-text`, and the button sends `select` with
`$emit` when clicked:

```citry-html
<button type="button" @click="$emit('select')">
  Choose <span v-text="label"></span>
</button>
```

Props are not the same as [`Kwargs`][citry.Component.Kwargs]. Python reads
Kwargs once, when it renders the HTML. A prop lives in the browser and can
change without another Python render. Vue's guides cover
[props](https://vuejs.org/guide/components/props.html){: target="_blank" rel="noopener"}
and [component events](https://vuejs.org/guide/components/events.html){: target="_blank" rel="noopener"}
in more depth.

## Connect parent to child

`ChoicePicker` uses the button like this:

```citry-html
<c-ChoiceButton :label="choice" @select="toggleChoice" />
```

`:label` passes the parent's `choice` to the child, and keeps it up to date
when `choice` changes. `@select` calls the parent's `toggleChoice` method
when the child sends `select`. The parent holds the value and decides what
to do:

```js
$component({
  data() {
    return { choice: 'Ocean' };
  },
  methods: {
    toggleChoice() {
      this.choice =
        this.choice === 'Ocean' ? 'Forest' : 'Ocean';
    },
  },
});
```

`data()` gives the parent its starting browser data from JavaScript, as
`js_data()` does from Python.

The [Client interactivity](/concepts/client-interactivity/) guide covers
more, such as slots in the browser, components with several root elements,
and code that runs when a component first appears on the page.

## Next steps

Next, [serve the page with FastAPI](/getting-started/fastapi/) so a later click
can reach Python.
