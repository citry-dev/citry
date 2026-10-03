---
title: Props and events
description: Pass browser values from a parent component to a child with Vue props, and let the child tell its parent what happened with Vue events.
---

# Props and events

A parent component often holds browser data that a child shows: an order
page knows the current status, and a badge displays it. The other way
round, a child often needs to tell its parent what the user did: a color
picker reports which color was picked. Vue props carry values down to a
child, and Vue events carry news back up, without a call to the server.

This page covers what you write on a child's component tag in the parent's
template, and what the child declares in its `$component({...})` options.
For the data a component keeps for itself, see
[Component options](/vue/component-options/).

## Pass props to a child { #pass-props-to-a-child }

A prop is a value the parent passes to a child in the browser. The child
declares the props it takes in its `$component({...})` options:

```js
$component({
  props: {
    status: {
      type: String,
      required: true,
    },
  },
});
```

A short form, such as `props: { status: String }`, declares only the type.

The parent passes a browser value with `:` or `v-bind`:

```citry-html
<c-StatusBadge :status="currentStatus" />
```

`currentStatus` comes from the parent's `data()`, `setup()`, or
`js_data()`. When the parent changes it, the child updates in the browser.

The `:` prefix is what makes `status` a Vue prop. A plain attribute, such as
`status="ok"`, is a Python input instead: Citry passes it to the child's
`Kwargs` when the server renders the child, and it does not change later in
the browser.

## Listen to child events { #listen-to-child-events }

An event is a message a child sends to its parent in the browser. The child
declares the events it sends in `emits` and sends one with Vue's `$emit`:

```js
$component({
  emits: ["select"],
  methods: {
    choose(color) {
      this.$emit("select", color);
    },
  },
});
```

```citry-html
<button type="button" @click="choose('#7f56d9')">Purple</button>
<button type="button" @click="choose('#12b76a')">Green</button>
```

The parent listens with `@` on the child's tag:

```citry-html
<c-ColorPicker @select="chooseColor" />
```

`chooseColor` runs in the parent, the component whose template contains the
`<c-ColorPicker>` tag. It receives the color the child passed to `$emit`.

This listener runs JavaScript in the browser. To run a Python handler on
the server when the child emits `select`, write `@c-select` instead; see
[Bind events in templates](/events/bindings/).

### Typed event payloads { #typed-event-payloads }

The value a child passes with an event is its payload. To tell the editor
what the payload looks like, write `emits` as an object. Each key is an
event name, and the `@type` comment on the function's parameter gives the
payload's type:

```js
$component({
  emits: {
    "drop-task"(/** @type {{taskId: number}} */ payload) {
      return true;
    },
    closed: null,
  },
});
```

- A `null` value, as for `closed`, allows any payload.
- The array form, such as `emits: ["drop-task"]`, allows only the listed
  names, with any payload.
- Without `emits`, the child may emit any name, as in Vue.

The editor uses these types in the parent too. In
`<c-Lane @drop-task="move($event)" />`, `$event` has the payload's type, as
do the parameters of an inline function such as
`@drop-task="(payload) => move(payload)"`, and `$event` in an
`@c-drop-task` binding on that tag. Inside `this.$emit("")`, completion
offers the declared names.

The function only types the payload. The Vue build Citry loads does not
call it while the page runs, so return `true` and do not rely on it to
reject a value.

When `emits` is an array of strings or an object with plain keys, the
editor and `citry check` also check event names:

- Emitting a name that `emits` does not list is an error:
  [`citry.browser.undeclared-emit`](/ide/diagnostics/#citry.browser.undeclared-emit).
- Listening on a child for a name the child does not declare is a warning:
  [`citry.browser.undeclared-component-event`](/ide/diagnostics/#citry.browser.undeclared-component-event).

A prop named `on<Event>`, such as `onPing` for `ping`, also declares the
event, as in Vue.

The editor checks the props you pass on a child's tag the same way. It
reports a prop the child does not declare, a missing required prop, and a
value of a type the prop does not accept. `citry check` reports the missing
and wrong-type cases too. See
[Child component props](/ide/vscode/#child-component-props) and
[Emitted event names](/ide/vscode/#emitted-event-names) for the details.

## Vue on component tags { #use-vue-directives-on-a-component-tag }

A Citry component tag accepts these Vue directives:

| Directive | What it does on a component tag |
| --- | --- |
| `:name`, `v-bind` | Passes a Vue prop to the child. |
| `@event`, `v-on` | Listens for an event the child emits. `v-on="listeners"` adds every listener in an object. |
| `v-if`, `v-else-if`, `v-else` | Adds or removes the component. |
| `v-model` | Passes a value and updates it when the child asks. |
| `v-show` | Hides or shows the child's root element. |
| A custom directive | Runs on the child's root element. |

Other directives fail when the template loads, and the error says what to
write instead:

- To pass content into the child, put `<c-fill name="...">` inside the
  component tag, not `v-slot` or `#name`. See
  [Content and slots](/vue/slots/).
- To repeat a component, use `<c-for>`, not `v-for`; see
  [`v-for` on components](#repeat-a-component).
- For `v-html` or `v-text`, pass a prop or a fill that the child renders.
- `v-once` and `v-memo` fail everywhere; see
  [`v-once` and `v-memo`](/vue/limits/#v-once-and-v-memo).

### `v-model` on a child { #bind-with-v-model }

`v-model` on a component tag passes the value as the `modelValue` prop. It
updates the value when the child emits `update:modelValue`. Here `query` is
the parent's browser data:

```citry-html
<c-SearchField v-model="query" />
```

`modelValue` is a Vue prop, not a Python input, so `SearchField` declares
it, along with the `update:modelValue` event, in `$component({...})` in its
`js`, not in `Kwargs`:

```citry
from citry import Component


class SearchField(Component):
    template = """
      <input
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
      />
    """

    js = """
      $component({
        props: ["modelValue"],
        emits: ["update:modelValue"],
      });
    """
```

An argument names a different prop. Modifiers reach the child in a
`<name>Modifiers` prop:

```citry-html
<c-TitleEditor v-model:title.trim="pageTitle" />
```

Here the child declares `title` and `titleModifiers`, and emits
`update:title`. Vue applies `.trim` and `.number` itself. For `.lazy` or a
modifier of your own, the child reads the modifiers prop and decides.

### `v-if` on a child { #add-or-remove-a-child }

`v-if` works on a component tag as on an element, and one chain can mix
both:

```citry-html
<c-OrderSummary v-if="step === 'review'" />
<p v-else-if="step === 'empty'">Your cart is empty.</p>
<c-CheckoutForm v-else />
```

Python still renders every component in the chain, so the browser can switch
between them without asking the server. When Python should decide whether a
component exists at all, use `<c-if>`; see
[Choose `<c-if>` or `v-if`](/vue/#choose-c-if-or-v-if).

### `v-show` on a child { #use-v-show-on-a-child }

`v-show` and custom directives act on the element at the root of the child's
template. The parent registers a custom directive in its own `js`. Here
`OrderPanel` registers `tooltip` and uses it on the `StatusBadge` in its
template:

```citry
from citry import Component


class OrderPanel(Component):
    template = """
      <c-StatusBadge
        v-show="expanded"
        v-tooltip:top="statusHelp"
        :status="currentStatus"
      />
    """

    js = """
      $component({
        data() {
          return {
            expanded: true,
            statusHelp: "Updated every hour",
            currentStatus: "shipped",
          };
        },
        directives: {
          tooltip: {
            mounted(el, binding) {
              el.title = binding.value;
            },
          },
        },
      });
    """
```

If nothing registers the name, the page's Vue app stops and the browser
console shows an error that names the directive and the component. To
register a directive for every component, use a plugin; see
[Plugins and the Vue app](/vue/plugins/#customize-the-vue-app).

The child's template must render exactly one root element, or the render
fails; see
[One root element](/vue/limits/#several-root-elements).

### `v-for` on components { #repeat-a-component }

A natural first attempt at a list of components is `v-for`:

```citry-html
{# Fails: v-for cannot create Citry components #}
<c-StatusBadge
  v-for="item in items"
  :status="item.status"
/>
```

The template fails when it loads, with an error that says what to write
instead. Only Python creates Citry components. Repeat the component with
`<c-for>` over a Python value, and pass each item's data as a Python input:

```citry-html
<c-for each="item in items">
  <c-StatusBadge c-status="item.status" />
</c-for>
```

See [Choose `v-for` or `<c-for>`](/syntax/vue/#choose-v-for-or-c-for).

## Pass HTML attributes { #pass-arbitrary-html-attributes-explicitly }

A plain attribute on a component tag is a Python input. To let the template
that uses a component set HTML attributes such as `class` or `aria-label`,
accept a mapping as an input and spread it onto the element that should get
them with `c-bind`:

```citry-html
<c-Card c-attrs="{'class': 'featured', 'aria-label': label}" />
```

```citry-html
{# Inside Card #}
<article c-bind="attrs">
  <c-slot />
</article>
```

This happens in Python, while the server renders the page. The mapping
carries plain HTML attributes only, not Vue bindings. To combine it with
the component's own attributes, see
[HTML attributes](/advanced/html-attributes/).

## Forward attributes { #forward-attributes }

Vue has its own way to pass attributes along, which works in the browser.
Attributes and listeners that the parent writes on a child's tag, and that
the child does not declare as props or events, are collected in the child's
`$attrs`. By default, Vue adds them to the child's root element.

To place them on a specific element or component instead, set
`inheritAttrs: false` and spread `$attrs` there:

```js
$component({
  inheritAttrs: false,
});
```

```citry-html
<header>Wrapper content</header>
<c-Child v-bind="$attrs" />
```

Declared props and declared events do not appear in `$attrs`.

To attach an object of Vue listeners, use `v-on` with the object:

```citry-html
<c-Child v-on="listeners" />
```

## See also

- [Content and slots](/vue/slots/) for content you pass into a child, and
  which component's data it reads.
- [Component options](/vue/component-options/) for `data()`, methods, and
  `js_data()`.
- [Bind events in templates](/events/bindings/) for `@c-*` handlers that
  run Python on the server.
- [VS Code](/ide/vscode/#complete-vue-expressions-and-component-javascript)
  for completion and checks in Vue code.
