---
title: Extensions
description: Add cross-cutting behavior, settings, routes, and metadata to Citry.
---

# Extensions

Some behavior belongs to every component rather than to one: log each
render, time it, add an analytics script to every page, or let each
component turn a feature on or off. Write that behavior once as an
extension, and Citry runs it for every component.

An extension is a class with methods that Citry calls at fixed points while
it renders, called hooks. An extension can also give components new
settings, serve HTTP routes, add commands to the Citry CLI, and describe
components to tools.

Extensions belong to one [`Citry`][citry.Citry] instance. Only components
registered with that instance use them.

## Install an extension

Pass extension classes to `Citry` when you create it:

```python
from citry import Citry
from citry.ext.debug import Debug

app = Citry(extensions=[Debug])
```

Citry always installs its built-in `cache`, `dependencies`, `events`,
and `i18n` extensions. Other bundled extensions are opt-in, such as
[`Debug`][citry.ext.debug.Debug], which helps when you
[investigate rendered output](/guides/troubleshooting/), and
`PreviewExtension`, which adds the commands for
[component previews](/advanced/previews/).

## Add a hook

Subclass [`Extension`][citry.Extension], give it a lowercase `name`, and
define only the hooks you need:

```citry
from citry import Citry, Component, Extension


class RenderLog(Extension):
    name = "render_log"

    def on_component_rendered(self, ctx):
        component_name = type(ctx.component).__name__
        print(f"Rendered {component_name}")


app = Citry(extensions=[RenderLog])


class Card(Component):
    citry = app

    template = """
      <article>A card</article>
    """
```

Each hook receives a context object, `ctx`, that describes what is
happening, such as the component being rendered. You cannot assign new
values to its fields, but some fields are dictionaries or lists. Hooks for
component inputs and data change those in place:

```python
class Tracking(Extension):
    name = "tracking"

    def on_component_data(self, ctx):
        ctx.template_data["tracking_enabled"] = True
```

Other hooks change a value by returning a new one. Returning `None` keeps
the current value:

```python
class UppercaseOutput(Extension):
    name = "uppercase_output"

    def on_serialize(self, ctx):
        return ctx.html.upper()
```

When several extensions change the same value, each receives the result of
the one before it, in the order you installed them.

The [`Extension` reference][citry.Extension] lists every hook and its
context. Hooks cover component classes and registration, component inputs
and data, rendered components and slots, attributes, serialization,
templates, JavaScript, and CSS.

!!! warning "Keep Citry's Vue element and runtime script in `on_serialize()` output"

    The example above fails with `ValueError` on an interactive page (one
    where a component uses Vue or server events). On such a page, Citry
    writes one element for the Vue app to start in, and rejects an
    `on_serialize()` result that changes, removes, or repeats that element,
    or that drops Citry's runtime script. Edit only the rest of the HTML.

### Return text or HTML

`on_component_rendered()` and `on_slot_rendered()` can return new content
for the component or slot. Citry treats a returned string like a value in
`{{ }}`, on static and interactive pages alike: a plain `str` shows as
text, so its tags appear as characters on the page:

```python
def on_component_rendered(self, ctx):
    if type(ctx.component).__name__ == "Checkout":
        # Wrong: the page shows "<p>Closed today</p>" as text.
        return "<p>Closed today</p>"
    return None
```

Wrap the HTML in [`Markup`][citry.Markup] to insert it as HTML:

```python
def on_component_rendered(self, ctx):
    if type(ctx.component).__name__ == "Checkout":
        # Right: Markup marks the string as HTML.
        return Markup("<p>Closed today</p>")
    return None
```

Never build `Markup` from user input. Return user input as a plain `str`,
which Citry escapes. `on_serialize()` is different: it returns the whole
page's HTML, and Citry uses that as it is.

### Handle a failed render

`on_component_rendered` also runs when a component fails to render. Then
`ctx.render` is `None` and `ctx.error` holds the exception:

- return a render to recover from the error;
- raise to replace the error with your own;
- return `None` to let the error continue.

## Add component settings

An extension can define default settings, and each component can override
them in a nested class. The nested class is named after the extension:
`audit_log` becomes `AuditLog`.

```citry
from citry import Citry, Component, Extension, ExtensionConfig


class AuditConfig(ExtensionConfig):
    enabled = True
    category = "general"


class AuditLog(Extension):
    name = "audit_log"
    Config = AuditConfig

    def validate_config_fields(self, fields, *, component=None):
        allowed = {"enabled", "category"}
        for field in fields:
            if field not in allowed:
                raise ValueError(f"Unknown audit setting: {field}")


app = Citry(
    extensions=[AuditLog],
    extensions_defaults={
        "audit_log": {"category": "storefront"},
    },
)


class Checkout(Component):
    class AuditLog:
        category = "checkout"

    citry = app

    template = """
      <button>Pay</button>
    """
```

Inside a hook, read the settings from the component as
`component.<extension name>`:

```python
def on_component_rendered(self, ctx):
    config = ctx.component.audit_log
    if config.enabled:
        record_render(category=config.category)
```

Citry takes each setting from the first place that sets it:

1. the component's nested class;
2. `extensions_defaults` passed to `Citry`;
3. the extension's `Config` class.

`validate_config_fields()` runs when you create the `Citry` instance or a
component class. Override it, as above, to reject misspelled or unknown
settings. By default it accepts any setting.

## Store data per render

Each component gets its own copy of every installed extension's config,
for that render. Store data there to read it in a later hook:

```python
class Timing(Extension):
    name = "timing"

    def on_component_input(self, ctx):
        ctx.component.timing.started_at = monotonic()

    def on_component_rendered(self, ctx):
        started_at = ctx.component.timing.started_at
        observe_duration(monotonic() - started_at)
```

Do not keep this data in a dictionary on the extension itself. One
extension instance serves many renders, possibly from several threads at
once.

## Add scripts and styles { #add-scripts-and-stylesheets-to-a-page }

The `on_dependencies()` hook runs each time Citry serializes a render, after
it has collected the scripts and stylesheets of every rendered component.
Its context holds three lists you can change in place:

- `ctx.scripts`: the page's scripts, in the order they run.
- `ctx.styles`: the page's stylesheets.
- `ctx.early_scripts`: scripts that run before everything in
  `ctx.scripts`, such as a consent manager.

```python
from citry import Extension
from citry.ext.dependencies import Script


class Analytics(Extension):
    name = "analytics"

    def on_dependencies(self, ctx):
        ctx.early_scripts.append(
            Script(url="https://cdn.example.com/consent.js"),
        )
        ctx.scripts.append(
            Script(url="https://cdn.example.com/analytics.js"),
        )
```

Citry adds its own browser runtime after the hook returns, so the hook
cannot move or remove it. The runtime loads before these scripts.

On a static page, the `early_scripts` entries become `<script>` tags before
the other scripts.

On an interactive page, they become the first scripts Citry loads for the
Vue app, in the order you added them, followed by `ctx.scripts`. Scripts
there must be classic JavaScript: a `type="module"` or
`type="application/json"` script, or one with `async`, `defer`, or
`nomodule`, makes serialization raise `ValueError`.

To install a Vue plugin on the page's Vue apps, add an early script that
calls `Citry.vue.use(plugin)`. It runs before Citry creates the app.

## Support caching

Citry can cache a component's rendered output and reuse it later
([Caching](/performance/caching/)). If your extension's hooks affect a
render, Citry needs to know whether the cached output is still correct
without running your hooks again. Say so with `render_cache_mode`.

The default is `"deny"`: Citry does not cache a render your extension took
part in. Rendering still works; it is just not cached.

Use `"stateless"` when the rendered output already contains everything
your extension added, and reusing it needs nothing else from the
extension:

```python
class StaticWrapper(Extension):
    name = "static_wrapper"
    render_cache_mode = "stateless"
    render_cache_version = 1
```

Use `"payload"` when reusing the output must also restore data your
extension keeps. Return that data as plain JSON values from
`export_render_cache()`. In `stage_render_cache()`, check the data and
describe the changes to make, without changing anything yet. Citry applies
them only after every extension accepts the cached entry.

`"stateless"` and `"payload"` require a positive `render_cache_version`;
without one, creating the `Citry` instance raises `ValueError`. Increase
`render_cache_version` whenever your extension changes what it adds to a
render, so Citry stops reusing entries cached by the older version. The [`Extension` reference][citry.Extension] documents the
cache methods.

## Serve extension routes

An extension can serve HTTP routes that work with any supported web
framework. Citry mounts them under `ext/<extension name>/` below its own
URL prefix:

```python
from citry import Extension, RouteResponse, URLRoute


class Health(Extension):
    name = "health"

    def status(self, request):
        return RouteResponse(
            content='{"status":"ok"}',
            content_type="application/json",
        )

    @property
    def urls(self):
        return [URLRoute("status", handler=self.status)]
```

The handler receives a [`RouteRequest`][citry.RouteRequest] and returns a
[`RouteResponse`][citry.RouteResponse]. `{name}` segments in the path reach
the handler as keyword arguments.

A route accepts `GET` by default. Pass `methods=("POST",)` or another tuple
to change it. With `methods=None`, every HTTP method reaches the handler,
which must then return `405 Method Not Allowed` with an `Allow` header
itself for methods it does not accept.

A plain `def` handler works with every framework integration. An
`async def` handler passed as `handler` works only with the direct ASGI
integration. To support both without blocking the event loop, pass a plain
`handler` and its async version as `handler_async`.

See [Web frameworks](/advanced/web-frameworks/) for mounting Citry's routes in your
application.

## Add CLI commands

List command classes in the extension's `commands` attribute. Citry puts
them under the extension's name, so two packages cannot clash:

```bash
citry --app myproject.engine:app ext list
citry --app myproject.engine:app ext run events openapi
```

See [Command line](/advanced/cli/) for defining arguments and running extension
commands.

## Describe components

Tools can ask Citry to describe the registered components with
`inspect_components()`. An extension can add its own entry to that
description. Set a positive
`introspection_version` and define `inspect_component()`:

```python
class AuditLog(Extension):
    name = "audit_log"
    introspection_version = 1

    def inspect_component(self, ctx):
        config = ctx.component_class.AuditLog
        return {"category": config.category}
```

The entry appears only when the caller asks for the extension by name:

```python
catalog = app.inspect_components(
    include_extensions=["audit_log"],
)
```

Return a plain `dict` of JSON values, or `None` when the component has no
entry. Return the same result every time: do not render, load assets,
change registration, or read the current request.

## Call your own hook

To let extensions react to an event in your application, call a hook by
name through the extension manager:

```python
app.extensions.emit(
    "on_message_sent",
    message_context,
)
```

Each installed extension that defines `on_message_sent` receives the
context, in installation order. Prefer a built-in hook when one fits.

By default, `emit()` ignores what the hooks return. `result="first"` stops
at the first result that is not `None`, and `result="map"` passes each
result on to the next extension through a named context field. See
[`ExtensionManager.emit()`][citry.ExtensionManager.emit].

## Name and install

### Choose a name

`name` must be a lowercase Python identifier. Names of built-in extensions
and names that would clash with the public `Component` API are reserved.
Citry turns the name into the nested settings class name, so `audit_log`
becomes `AuditLog`. Set `class_name` only when your package needs a
different valid class name.

### Install other ways

When you pass a class, Citry creates a new instance of it, and the instance
reaches its `Citry` instance through `self.citry`. You can also pass a
dotted import path or an instance you created:

```python
app = Citry(
    extensions=[
        "acme_citry.Tracing",
        preconfigured_extension,
    ],
)
```

An instance can belong to only one `Citry` instance. Create a new one for
each, or pass the class.

## Related reference

- [`Extension`][citry.Extension]
- [`ExtensionManager`][citry.ExtensionManager]
- [`ExtensionConfig`][citry.ExtensionConfig]
- [`ExtensionCommand`][citry.ExtensionCommand]
- [`URLRoute`][citry.URLRoute]
- [`RouteRequest`][citry.RouteRequest]
- [`RouteResponse`][citry.RouteResponse]
