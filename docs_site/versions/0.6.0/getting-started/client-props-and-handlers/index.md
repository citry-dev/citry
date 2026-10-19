---
title: Connect components in the browser
url: https://citry.dev/v/0.6.0/getting-started/client-props-and-handlers/
description: "Pass a browser value into a child Citry component and handle an event the child sends."
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



### Reactive parent and child components

````citry
from citry import Component


class ChoiceButton(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <button
        class="choice-button"
        type="button"
        @click="$emit('select')"
      >
        Choose
        <span
          class="choice-button__label"
          v-text="label"
        ></span>
      </button>
    """

    js = """
      $component({
        props: {
          label: { type: String, required: true },
        },
        emits: ['select'],
      });
    """


class ChoicePicker(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="choice-picker">
        <p>
          Current choice:
          <output
            class="choice-picker__value"
            v-text="choice"
          ></output>
        </p>

        <c-ChoiceButton
          :label="choice"
          @select="toggleChoice"
        />
      </section>
    """

    js = """
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


page = ChoicePage()

if __name__ == "__main__":
    print(page)

page
````




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


Props are not the same as [`Kwargs`](/v/0.6.0/reference/component/#citry-component-kwargs). Python reads
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

The [Vue](/v/0.6.0/vue/) section of the docs covers more, for example:

- [Content and slots](/v/0.6.0/vue/slots/) for slots in the browser;
- [`v-show` needs one root](/v/0.6.0/vue/limits/#several-root-elements) for
  components with several root elements;
- [`onServerRender` callback](/v/0.6.0/vue/component-options/#react-after-a-server-render)
  for code that runs when a component first appears on the page.

## Next steps

Next, [serve the page with FastAPI](/v/0.6.0/getting-started/fastapi/) so a later click
can reach Python.