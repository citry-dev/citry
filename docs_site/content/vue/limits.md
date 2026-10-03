---
title: Limits and errors
description: See which Vue features Citry does not support, and fix the common errors a template or a page shows when Vue code goes wrong.
---

# Limits and errors

Something failed: the template does not load, the page shows an error, or
a part of the page does nothing in the browser. This page lists the Vue
features Citry does not support, then the common errors with their fixes.
Each entry starts with what you see. When an error comes from the browser,
start with [Diagnose failures](#diagnose-failures).

## What is not supported { #what-is-not-supported }

Each of these fails when the template loads, and the error says what to
write instead. `citry check` and the editor report them too.

### Vue built-in components { #vue-built-in-components }

`<Transition>`, `<TransitionGroup>`, `<KeepAlive>`, `<Teleport>`, and
`<Suspense>` fail on every page, in any spelling, such as `<KeepAlive>` or
`<keep-alive>`. Use these instead:

| Vue component | Use instead |
| --- | --- |
| `<Transition>`, `<TransitionGroup>` | A CSS transition or animation, with the class changed by `:class`. |
| `<KeepAlive>` | Leave the child rendered and hide it with `v-show`. |
| `<Teleport>` | The HTML `<dialog>` element, the `popover` attribute, or Citry UI's `<c-CDialog>` and `<c-CPopover>`. |
| `<Suspense>` | A loading flag in the component's data, with `v-if` and `v-else`. |

### `v-once` and `v-memo` { #v-once-and-v-memo }

Both fail on elements and component tags alike. To compute a fixed value
once, do it in `data()`. To keep an element's contents as the server
first rendered them, use
[`#c-ignore`](/syntax/attributes/#c-ignore-keep-contents-that-a-library-manages).

### Alpine modifiers { #unknown-modifiers }

`.outside`, `.window`, `.document`, `.debounce`, and `.throttle` are
Alpine modifiers. Citry 0.6.0 moved from Alpine to Vue, which has none of
these modifiers, so Citry rejects them on a Vue listener, and the error
says how to write the same behavior in Vue:

```citry-html
{# Fails: .outside is an Alpine modifier #}
<div @click.outside="open = false;">...</div>
```

For a click outside, listen for `click` on `document` in `mounted()`,
skip clicks inside the component, and remove the listener in
`unmounted()`:

```js
$component({
  data() {
    return { open: false };
  },
  methods: {
    closeOnOutsideClick(event) {
      // A click inside the component keeps it open.
      if (!this.$el.contains(event.target)) {
        this.open = false;
      }
    },
  },
  mounted() {
    document.addEventListener("click", this.closeOnOutsideClick);
  },
  unmounted() {
    document.removeEventListener("click", this.closeOnOutsideClick);
  },
});
```

`this.$el` is the root element of the component's template, so the
template needs exactly one root element.

To call a Python event handler, use an `@c-*` attribute: it accepts
`.debounce` and `.throttle`; see
[Bind events in templates](/events/bindings/). The
[0.6.0 upgrade guide](/guides/upgrading-to-0-6-0/#rewrite-alpine-modifiers)
covers the rest of the move from Alpine.

### `mixins` and `extends`

`$component({...})` rejects both. See
[Unsupported options](/vue/component-options/#unsupported-options).

## Common errors { #common-errors }

Each entry below is short. Follow its link for the full explanation.

### A Python name in Vue

A Vue attribute that reads a Python name sets nothing, such as
`:title="item"` inside a `c-for` loop. A Vue expression runs in the
browser and cannot see Python names; `citry check` and the editor report
it. Set the attribute from Python with `c-title`, or send the value to
the browser with `js_data()`. See
[Tell Python from Vue](/vue/#tell-python-from-vue).

### Unknown directive

A template uses a custom directive, such as `v-tooltip`, that nothing
registers. The page's Vue app stops, and the browser console shows an
error that names the directive and the component.

Check the spelling, or register the directive: in the `directives` option
of the component's `$component({...})`, as in
[`v-show` on a child](/vue/props-and-events/#use-v-show-on-a-child), or
for every component with a [Vue plugin](/vue/plugins/#customize-the-vue-app).

### Key names on clicks

`@click.enter` fails when the template loads. Citry accepts a key name
such as `.enter` or `.escape` only on `keydown`, `keyup`, and `keypress`,
because other events have no key and Vue would run the listener on every
event. Listen to `keydown` or `keyup` instead, as in `@keydown.enter`. See
[Vue `v-*` directives](/syntax/vue/#use-vue-directives) for the full
rule, which covers `@c-*` attributes too.

### Name clashes

The component fails with an error that names a value. Two cases cause
it:

- a `js_data()` key reuses a name from `data()`, `setup()`, props,
  injections, methods, or computed values;
- the component defines a name that Citry adds to every component, such
  as `$loading`.

Rename your value. See
[Reserved names](/vue/component-options/#names-citry-reserves-on-the-component-instance).

### `v-show` needs one root { #several-root-elements }

`v-show` or a custom directive on a component tag, such as
`<c-Panel v-show="open">`, needs the child's template to render exactly
one root element, because Vue applies the directive to that element.
Otherwise the render fails with an error naming the directive and the
child. That happens when the child's template has:

- several top-level elements, or an element next to text;
- a top-level `v-for`, `<c-for>`, or `<c-slot>`;
- only text;
- top-level HTML from Python, such as `<c-raw>`.

When the child's root is another component with such a template, the
browser reports the error instead.

Wrap the child's template in one element, or put the directive on an
element around the child tag:

```citry-html
<div v-show="open">
  <c-Panel />
</div>
```

### Directive spelling

`V-IF` and `v-If` fail when the template loads. Write the `v-` prefix and
Vue's own directive names in lowercase. Names that start with `v-c-` or
`v-citry-` fail too, because Citry keeps them for its own use. See
[Vue `v-*` directives](/syntax/vue/#use-vue-directives).

### Vue on built-in tags { #vue-on-built-in-tags }

`<c-element is="div">` renders a plain HTML element, so every Vue
directive works on it. When Python picks the tag with `c-is`, `:`
bindings and `@` listeners still work, but a `v-` directive such as
`v-if` or `v-show` makes the render fail with an error that names it. Put
the directive on an element around the `<c-element>`.

A built-in tag that renders only its content, such as `<c-provide>`,
accepts no Vue syntax. The render fails, and the error says to put the
binding on an element inside the tag.

`<c-slot>` accepts no Vue syntax either; see
[`v-if` around a slot](/vue/slots/#v-if-around-a-slot).

### Vue code in `c-bind`

The page fails to render, and the error names an attribute such as
`'@click'`. A Vue directive, `:` binding, or `@` listener came from
`c-bind`, or was written with a `c-` prefix such as `c-v-if`. Write it
directly in the template. See
[No Vue code in `c-bind`](/vue/csp/#c-bind-never-carries-vue-code).

## Diagnose failures { #diagnose-failures }

When a page fails in the browser, start with the first `[Citry]` error in
the browser console. Later errors are often caused by the first one.
In the causes below, the Vue host is the element Citry writes around the
part of the page that Vue runs. Common causes:

- a fragment or asset that did not load completely;
- a Vue host or configuration script that an optimizer changed or
  removed; see [Preserve page HTML](/vue/server-rendering/#preserve-interactive-html);
- component data from the server that the runtime rejects;
- browser code that moved or removed elements inside the Vue host.

[Troubleshooting](/guides/troubleshooting/) covers the wider server and
browser investigation.

## See also

- [Vue in templates](/syntax/vue/) for directives and expressions.
- [Component options](/vue/component-options/) for what
  `$component({...})` accepts.
- [Plugins and the Vue app](/vue/plugins/) for global directives and
  components.
