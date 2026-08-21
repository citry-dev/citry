---
title: Extensions
url: https://citry.dev/v/0.4.2/advanced/extensions/
description: "Add cross-cutting behavior, settings, routes, and metadata to Citry."
---
# Extensions

An extension can apply one behavior across many components. It can observe or
change rendering, give components new settings, expose HTTP routes, publish
metadata to tools, or add a command to the Citry CLI.

Extensions belong to one [`Citry`](/v/0.4.2/reference/citry/#citry-citry) instance. Only components
registered with that instance use them.

## Install an extension

Pass extension classes to `Citry` when you create the engine:


```python
from citry import Citry
from citry.ext.debug import Debug

app = Citry(extensions=[Debug])
```


A class is the usual choice. Citry creates a fresh extension instance and
gives it access to the engine through `self.citry`.

You may also pass a dotted import path or a ready instance:


```python
app = Citry(
    extensions=[
        "acme_citry.Tracing",
        preconfigured_extension,
    ],
)
```


A ready instance can belong to only one engine. Create a fresh instance for
each engine, or pass its class and let Citry do that for you.

An extension name must be a lowercase Python identifier. Built-in extension
names and names that would collide with the public `Component` API are
reserved. Citry derives the component config class name from it, so
`audit_log` becomes `AuditLog`. Set `class_name` explicitly only when a package
needs another valid Python class name.

Citry always installs its built-in `cache`, `dependencies`, and `events`
extensions. Other bundled extensions, such as [`Debug`](/v/0.4.2/reference/extensions/#citry-ext-debug-debug),
are opt-in. See [Troubleshooting](/v/0.4.2/guides/troubleshooting/) for using `Debug`
while investigating rendered output.

## Add behavior with a lifecycle hook

Subclass [`Extension`](/v/0.4.2/reference/extensions/#citry-extension), give it a lowercase `name`, and
override only the hooks you need:


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


The context object tells you what is happening and which engine owns the
operation. Context dataclasses are frozen, so their fields cannot be replaced.
Some fields deliberately contain mutable dictionaries or lists. Input and data
hooks change those collections in place:


```python
class Tracking(Extension):
    name = "tracking"

    def on_component_data(self, ctx):
        ctx.template_data["tracking_enabled"] = True
```


Hooks that transform a value return its replacement. Returning `None` keeps
the current value:


```python
class UppercaseOutput(Extension):
    name = "uppercase_output"

    def on_serialize(self, ctx):
        return ctx.html.upper()
```


When several extensions transform the same value, Citry passes each result to
the next extension in installation order.

`on_component_rendered` also runs when rendering fails. In that case
`ctx.render` is `None` and `ctx.error` holds the exception. Returning a render
recovers from the error; raising replaces it. Returning `None` lets the current
result or error continue.

The hook catalog covers component classes, registration, component input and
data, rendered components and slots, resolved attributes, nested render
contexts, serialization, templates, JavaScript, and CSS. See the
[`Extension` reference](/v/0.4.2/reference/extensions/#citry-extension) for every hook and its context.

For an application-specific hook, emit a name through the manager:


```python
app.extensions.emit(
    "on_message_sent",
    message_context,
)
```


Installed extensions that define `on_message_sent` receive the context in
order. Prefer the documented lifecycle hooks when one already describes the
job.

The default `result="none"` ignores returned values. `result="first"` stops at
the first non-`None` result. `result="map"` threads replacements through a
named context field. See
[`ExtensionManager.emit()`](/v/0.4.2/reference/extensions/#citry-extensionmanager-emit) for the exact
contract.

## Give components extension settings

An extension can define defaults and let each component override them. The
extension's `name` determines the nested class name: `audit_log` becomes
`AuditLog`.


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


Inside a hook, read the resolved settings from the component:


```python
def on_component_rendered(self, ctx):
    config = ctx.component.audit_log
    if config.enabled:
        record_render(category=config.category)
```


Values are chosen in this order:

1. The component's nested extension class.
2. `extensions_defaults` on the engine.
3. The extension's `Config` class.

Override `validate_config_fields()` to reject misspelled or unsupported fields
when the engine or component class is created. The base implementation accepts
any field.

## Carry data between hooks

Each component gets a fresh instance of every installed extension's config.
That config is a safe place to keep temporary data for the component render:


```python
class Timing(Extension):
    name = "timing"

    def on_component_input(self, ctx):
        ctx.component.timing.started_at = monotonic()

    def on_component_rendered(self, ctx):
        started_at = ctx.component.timing.started_at
        observe_duration(monotonic() - started_at)
```


Use this instead of a dictionary on the extension instance. A single extension
instance serves many renders and may be called from several threads. Also
remember that a later hook does not run if an earlier stage raises.

The config is available as `component.<extension name>`, together with its
resolved settings. It belongs to that component instance and render.

## Keep component caching correct

An extension that participates in rendering must say whether its work can be
replayed from a component cache entry. The safe default is:


```python
class RequestStamp(Extension):
    name = "request_stamp"
    render_cache_mode = "deny"
```


`deny` does not disable rendering. It prevents Citry from storing a cache entry
for a render affected by that extension.

Use `stateless` only when the rendered output already contains everything the
extension contributed and replay needs no extension state:


```python
class StaticWrapper(Extension):
    name = "static_wrapper"
    render_cache_mode = "stateless"
    render_cache_version = 1
```


Use `payload` when replay must restore extension-owned state. Set a positive
`render_cache_version`, return strict JSON data from `export_render_cache()`,
and validate it without mutation in `stage_render_cache()`. The staging result
describes changes for Citry to apply only after every extension accepts the
cached entry.

Treat a cache-mode change or version change as a compatibility decision. See
[Caching](/v/0.4.2/advanced/caching/) and the extension cache methods in the
[`Extension` reference](/v/0.4.2/reference/extensions/#citry-extension).

## Publish metadata to tools

Extension metadata is opt-in so ordinary component inspection stays small and
side-effect free. Set a positive schema version and implement
`inspect_component()`:


```python
class AuditLog(Extension):
    name = "audit_log"
    introspection_version = 1

    def inspect_component(self, ctx):
        config = ctx.component_class.AuditLog
        return {"category": config.category}
```


Callers must request the extension by name:


```python
catalog = app.inspect_components(
    include_extensions=["audit_log"],
)
```


Return an exact built-in `dict` containing only strict JSON values, or `None`
when the component has no entry. Inspection must be deterministic and
observational: do not render, load assets, change registration, or depend on a
request.

## Serve extension routes

An extension can expose framework-neutral HTTP routes. User extension routes
are mounted under `ext/<extension name>/` beneath the application's Citry URL
prefix.


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


The handler receives a [`RouteRequest`](/v/0.4.2/reference/web/#citry-routerequest) and returns a
[`RouteResponse`](/v/0.4.2/reference/web/#citry-routeresponse). A route accepts `GET` by default. Pass
`methods=("POST",)` or another tuple to change it. `{name}` path segments are
passed to the handler as keyword arguments.

A plain `def` handler works with every host adapter. An `async def` handler
passed as `handler` works only with the direct ASGI adapter. To support both
async and sync hosts without blocking the event loop, provide a plain
`handler` and its async twin through `handler_async`.

See [Web frameworks](/v/0.4.2/web-frameworks/) for mounting `app.urls` in your
host application.

## Add CLI commands

Extensions may expose command classes through their `commands` attribute.
Citry namespaces them beneath the extension name, so packages cannot collide:


```bash
citry --app myproject.engine:app ext list
citry --app myproject.engine:app ext run events openapi
```


See [Command line](/v/0.4.2/cli/) for defining arguments and running
extension commands.

## Related reference

- [`Extension`](/v/0.4.2/reference/extensions/#citry-extension)
- [`ExtensionManager`](/v/0.4.2/reference/extensions/#citry-extensionmanager)
- [`ExtensionConfig`](/v/0.4.2/reference/extensions/#citry-extensionconfig)
- [`ExtensionCommand`](/v/0.4.2/reference/extensions/#citry-extensioncommand)
- [`URLRoute`](/v/0.4.2/reference/web/#citry-urlroute)
- [`RouteRequest`](/v/0.4.2/reference/web/#citry-routerequest)
- [`RouteResponse`](/v/0.4.2/reference/web/#citry-routeresponse)