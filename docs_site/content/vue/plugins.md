---
title: Plugins and the Vue app
description: Add a global directive, a shared component, or an error reporter to every Vue component on the page with a Vue plugin.
---

# Plugins and the Vue app

Sometimes you want something in every component on the page: a global
directive such as `v-autofocus`, a shared component, or an error reporter.
In a plain Vue project you would set these up on the app returned by
`createApp()`. Citry creates the Vue app for you, so there is no
`createApp()` call to configure. Use a Vue plugin instead.

## Add a Vue plugin { #customize-the-vue-app }

A Vue plugin is an object with an `install(app)` method. Register it with
[`Citry.vue.use(plugin, ...options)`](/reference/browser-apis/#citry-vue-use).
Citry installs it on every Vue app it creates on the page, before the app
mounts.

Here a plugin adds a `v-autofocus` directive:

```js
// static/vue-plugins.js
Citry.vue.use({
  install(app) {
    app.directive("autofocus", {
      mounted(el) {
        el.focus();
      },
    });
  },
});
```

Any template can then use it:

```citry-html
<input v-autofocus />
```

In `install(app)` you can:

- register directives with `app.directive()` and components with
  `app.component()`;
- provide values with `app.provide()`. A component reads a provided value
  with `inject` in `$component({...})`; see
  [`provide` and `inject`](/vue/component-options/#provide-and-inject);
- set `app.config.errorHandler`; see [Handle Vue errors](#handle-vue-errors);
- add `app.config.globalProperties`.

## Load the plugin file

Load the file in the page's `<head>` with `defer`:

```html
<script defer src="/static/vue-plugins.js"></script>
```

`defer` makes the file run after Citry's runtime loads and before Citry
creates the first Vue app, which is the window in which `Citry.vue.use()`
works.

To add the file to every page from Python, write an extension that adds it
to `ctx.early_scripts`; see
[Add scripts and styles](/advanced/extensions/#add-scripts-and-stylesheets-to-a-page).

## Handle Vue errors

To send errors to your own reporting tool, set `app.config.errorHandler`
in the plugin's `install`:

```js
Citry.vue.use({
  install(app) {
    app.config.errorHandler = (error, instance, info) => {
      // With a handler set, Citry leaves logging to you.
      console.error(error);
      // sendToTracker stands for your reporting tool.
      sendToTracker(error, info);
    };
  },
});
```

When a handler is set, Citry passes each error to it instead of the
browser console, so log it there yourself. Errors from Citry's own browser
code, such as a failed `@c-poll` refresh, reach the handler too, with an
`info` text that starts with `Citry`, as in `"Citry @c-poll"`.

With or without a handler, after an error Citry stops sending server
updates to that Vue app. Reload the page to get them again.

## Plugin limits

A plugin runs inside a Vue app that Citry has already set up, so a few
things work differently from a plain Vue project.

### Call `use()` early

Call `Citry.vue.use()` before Citry creates its first Vue app. A later call
throws an `Error`, because that app would run without the plugin. The
reference lists
[the other errors](/reference/browser-apis/#citry-vue-use), such as passing
a value that is not a plugin.

### Components need `render()`

A component registered with `app.component()` can be used in any template
by its name, such as `<my-badge>`. It needs a `render()` function written
with `Citry.vue.h`. A `template` string does not compile in the browser:

```js
Citry.vue.use({
  install(app) {
    app.component("my-badge", {
      props: ["label"],
      render() {
        const h = Citry.vue.h;
        return h("span", { class: "badge" }, this.label);
      },
    });
  },
});
```

### Keep `$loading`, `$error`

Citry adds [`$loading`](/reference/browser-apis/#loading) and
[`$error`](/reference/browser-apis/#error) to `globalProperties`. A plugin
that sets either name replaces Citry's version, and `$loading()` and
`$error()` stop working in every template. Give your properties other
names.

### One install per Vue app

A page can run several Vue apps, for example when
[HTML fragments](/advanced/html-fragments/) add components to it. The
plugin's `install` runs once for each app, and each app has its own
`app.provide()` values. For one value that every app shares, create it
outside `install` and provide that same object:

```js
// One store for the whole page, created once.
const store = Citry.vue.reactive({ cartCount: 0 });

Citry.vue.use({
  install(app) {
    app.provide("store", store);
  },
});
```

### No mixins

A plugin cannot add a mixin to components, because `$component({...})`
rejects `mixins` and `extends`; see
[Unsupported options](/vue/component-options/#unsupported-options).

### Ignored config options

`app.config.compilerOptions` has no effect, because Citry compiles
templates on the server. `app.config.warnHandler` is never called, because
the Vue build Citry loads leaves out Vue's warnings.

### A failing `install`

If the plugin's `install` throws, that Vue app does not start, and the
error shows as a page error.

## See also

- [`Citry.vue.use`](/reference/browser-apis/#citry-vue-use) in the browser
  API reference.
- [Component options](/vue/component-options/) for what
  `$component({...})` accepts.
- [Limits and errors](/vue/limits/) for what Citry does not support.
