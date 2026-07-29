---
title: Extensions
url: https://citry.dev/v/0.3.1/advanced/extensions/
description: "How to hook into Citry's lifecycle, install extensions on a Citry instance, and add extension-provided CLI commands."
---
# Extensions

An extension is a plugin that hooks into Citry's component lifecycle. You can watch or change what happens when a component receives input, computes its data, renders, or loads its template, JS, and CSS. Extensions can also add per-component config, HTTP routes, and their own CLI commands.

Extensions are installed per Citry instance, not globally. A component is bound to a [Citry](/v/0.3.1/reference/citry/#citry-citry) instance (via `citry = app` in its class body, or the default instance), and only that instance's extensions fire for it.

## Writing an extension

An extension subclasses [Extension](/v/0.3.1/reference/extensions/#citry-extension), sets a `name`, and overrides one or more `on_*` hooks. Each hook receives a single frozen dataclass context.


```citry
from citry import Citry, Component, Extension

class TimingExtension(Extension):
    name = "timing"

    def on_component_rendered(self, ctx):
        print(f"{type(ctx.component).__name__} rendered")
        return None  # keep the original render

app = Citry(extensions=[TimingExtension])

class Card(Component):
    citry = app
    template = """
      <p>hi</p>
    """

str(Card())  # triggers on_component_rendered
```


The `name` must be a lowercase, valid Python identifier. This is checked the moment the class body runs (in `__init_subclass__`), so a bad name raises `ValueError` even if you never install the extension. The name also becomes a `component.<name>` attribute, so it must not collide with the [Component](/v/0.3.1/reference/component/#citry-component) API. The built-in `cache`, `dependencies`, and `events` names are reserved.

## Installing extensions

Pass extensions to [Citry](/v/0.3.1/reference/citry/#citry-citry) when you construct it. Each entry can be an extension class, an instance, or a dotted import-path string.


```python
c = Citry(extensions=[E1, E2(), "my_pkg.my_module.MyExtension"])
```


Every Citry instance also auto-prepends the built-in `cache`, `dependencies`, and `events` extensions. They power render caching, JS/CSS dependency collection, and server event handling. Bundled developer tools such as [Debug](/v/0.3.1/reference/extensions/#citry-ext-debug-debug) remain opt-in, so applications pay their render-hook cost only when they install them.

Use [Server events](/v/0.3.1/events/) to declare and call component
handlers. The rest of this page is for authors building their own extensions.

The installed extensions are managed by an [ExtensionManager](/v/0.3.1/reference/extensions/#citry-extensionmanager), reachable as `app.extensions`. It only calls extensions that actually override a given hook, so hooks you do not override cost nothing.

### Bundled Debug extension

The opt-in [Debug](/v/0.3.1/reference/extensions/#citry-ext-debug-debug) extension draws blue labeled boundaries around component output and red labeled boundaries around slot output. Install it and enable either boundary type through extension defaults:


```citry
from citry import Citry, Component
from citry.ext.debug import Debug

app = Citry(
    extensions=[Debug],
    extensions_defaults={
        "debug": {
            "highlight_components": True,
            "highlight_slots": True,
        },
    },
)

class Card(Component):
    citry = app
    template = """
      <article><c-slot name="body" /></article>
    """
```


A component can override the defaults with a nested `class Debug` containing the same two boolean fields. See [Visualize component and slot boundaries](/v/0.3.1/guides/troubleshooting/#visualize-component-and-slot-boundaries) for examples and the DOM-layout warning.

## Hooks

Each hook takes one frozen dataclass context. Every context carries `citry`; component-scoped ones also carry `component`. Some hooks watch, some mutate, and some replace a value.

Mutation hooks such as `on_component_input` and `on_component_data` change a dict on the context in place. This example injects a template variable:


```citry
class E(Extension):
    name = "e"

    def on_component_data(self, ctx):
        ctx.template_data["who"] = "world"

app = Citry(extensions=[E])

class Card(Component):
    citry = app
    template = """
      <p>Hello {{ who }}</p>
    """

# render output includes "Hello world"
str(Card())
```


Other hooks thread a value through the extensions: returning a non-None value replaces it for the next extension, and returning `None` keeps the current value. These include `on_component_rendered`, `on_slot_rendered`, `on_attrs_resolved`, `on_serialize`, `on_template_loaded`, `on_template_compiled`, `on_js_loaded`, and `on_css_loaded`.

The full set of hooks (roughly sixteen) covers extension setup, component class creation and deletion, registration, input, data, rendering, slots, attribute resolution, context merging, serialization, and template, JS, and CSS loading and compilation. See the Extensions reference category for each hook and its context fields.

## Per-component config

An extension can provide config that lives on each component. Define a nested `Config` class subclassing `Extension.Config`. For an extension named `view`, it is reachable as `component.view`.


```citry
class ViewExt(Extension):
    name = "view"

    class Config(Extension.Config):
        def title(self):
            return type(self.component).__name__

app = Citry(extensions=[ViewExt])

class Page(Component):
    citry = app
    template = """
      <p>hi</p>
    """

    def template_data(self, kwargs, slots):
        # reachable as component.<extension name>
        assert self.view.title() == "Page"
        return {}

str(Page())
```


Inside an [ExtensionConfig](/v/0.3.1/reference/extensions/#citry-extensionconfig), `self.component` is a weak reference back to the owning component. Accessing it raises `RuntimeError` if it runs outside a component lifecycle or the component was already garbage-collected.

## Extension defaults

Setting the same nested config class on every component gets repetitive. To configure an extension once for all components, pass `extensions_defaults` to [Citry](/v/0.3.1/reference/citry/#citry-citry). It maps each extension's name to the config every component should get for it:


```citry
from citry import Citry, Component, Extension

class AccessExt(Extension):
    name = "access"

    class Config(Extension.Config):
        public = False

app = Citry(
    extensions=[AccessExt],
    extensions_defaults={"access": {"public": True}},
)

class Page(Component):
    citry = app
    template = """
      <p>hi</p>
    """

    def template_data(self, kwargs, slots):
        # every component now defaults to public
        assert self.access.public is True
        return {}

str(Page())
```


As the name says, these are defaults, so a component can still override any of them with its own nested config class:


```citry
class Secret(Component):
    citry = app
    template = """
      <p>hi</p>
    """

    class Access:
        public = False  # overrides the default here

    def template_data(self, kwargs, slots):
        assert self.access.public is False
        return {}

str(Secret())
```


A config value given as a function becomes a method on the config class, exactly as if you had written it in the nested class. The defaults are held on the instance as `app.settings.extensions_defaults` (see [CitrySettings](/v/0.3.1/reference/citry/#citry-citrysettings)).

## Storing state during a render

An extension often needs to carry a value from one hook to a later one in the same render. Citry gives you two places to keep it, each living on the thing it describes: a slot's own `extra` dictionary, and the per-component config object. Both are cleaner than a dictionary you keep on the extension and manage by hand.

### Per-slot metadata

Every [Slot](/v/0.3.1/reference/slots/#citry-slot) carries an `extra` dictionary, the place for an extension to attach per-slot metadata. Citry copies `extra` whenever it copies a slot, so whatever you attach travels with the slot to wherever it renders. Set it when the component receives its input, then read it back when the slot renders:


```citry
from citry import Citry, Component, Extension

class SlotTagExt(Extension):
    name = "slottag"

    def on_component_input(self, ctx):
        for slot in ctx.slots.values():
            slot.extra["tag"] = "hello"

    def on_slot_rendered(self, ctx):
        print(ctx.slot_name, "->", ctx.slot.extra.get("tag"))
        return None  # keep the rendered output

app = Citry(extensions=[SlotTagExt])

class Panel(Component):
    citry = app
    template = """
      <div>
        <c-slot name="body" />
      </div>
    """

str(Panel(slots={"body": "content"}))  # prints: body -> hello
```


### Per-render state

For state tied to one component's render, keep it on the component's config object rather than in a dictionary on the extension keyed by `id(component)`. That side dictionary leaks: you would clear each entry in `on_component_rendered`, but citry skips that hook when a render fails before it settles (for example, a `template_data` method raises), so a stale entry is left behind on every failed render.


```python
import time

# Tempting, but leaks when a render fails (see below).
class TimingExt(Extension):
    name = "timing"

    def __init__(self):
        self.started = {}

    def on_component_input(self, ctx):
        self.started[id(ctx.component)] = time.perf_counter()

    def on_component_rendered(self, ctx):
        # skipped on a failed render, so never removed
        start = self.started.pop(id(ctx.component))
        ...
```


Store the value on the component's config object instead. Every component has one per extension, reachable as `component.<extension name>` (the same object from [Per-component config](#per-component-config)). It lives only for that one render, so nothing accumulates on the extension, even when `on_component_rendered` is skipped:


```citry
import time

class TimingExt(Extension):
    name = "timing"

    def on_component_input(self, ctx):
        # ctx.component.timing is this component's config object
        ctx.component.timing.started = time.perf_counter()

    def on_component_rendered(self, ctx):
        elapsed = time.perf_counter() - ctx.component.timing.started
        print(f"{type(ctx.component).__name__} took {elapsed:.4f}s")
        return None

app = Citry(extensions=[TimingExt])

class Card(Component):
    citry = app
    template = """
      <p>hi</p>
    """

str(Card())  # prints: Card took 0.0003s
```


## CLI commands

An extension can ship CLI commands by listing [ExtensionCommand](/v/0.3.1/reference/extensions/#citry-extensioncommand) subclasses in `commands`. A command sets a `name`, declares [CommandArg](/v/0.3.1/reference/extensions/#citry-commandarg) arguments, and defines a `handle` method. The arguments map straight to argparse.


```python
from citry import Citry, Extension, ExtensionCommand, CommandArg
from citry.command import run

class Greet(ExtensionCommand):
    name = "greet"
    help = "Greet someone"
    arguments = [
        CommandArg("name"),
        CommandArg(["--shout", "-s"], action="store_true"),
    ]

    def handle(self, **kwargs):
        text = f"Hello {kwargs['name']}"
        print(text.upper() if kwargs["shout"] else text)

class Greeter(Extension):
    name = "greeter"
    commands = [Greet]

app = Citry(extensions=[Greeter])
assert app.commands == {"greeter": (Greet,)}

# Run it in-process (the CLI does the same):
run(Greet, ["world", "--shout"])  # prints HELLO WORLD, returns 0
```


From the terminal, the same command runs as:


```sh
citry ext run greeter greet
```


See the [CLI](/v/0.3.1/cli/) page for the command-line entry points.

A few things to keep in mind:

- `handle` receives every parsed option as a keyword, including options declared on a parent command, so it should accept `**kwargs`.
- A command that has only subcommands (via `subcommands`) and no `handle` prints its help instead of running.
- Arguments can be grouped with [CommandArgGroup](/v/0.3.1/reference/extensions/#citry-commandarggroup), and subcommand behavior tuned with [CommandSubcommand](/v/0.3.1/reference/extensions/#citry-commandsubcommand).

## Extension URLs

An extension can serve its own HTTP endpoints. Citry cannot listen on a port itself, so it describes each endpoint as a framework-neutral [URLRoute](/v/0.3.1/reference/web/#citry-urlroute) and a thin adapter mounts them into your web app (see [Web frameworks](/v/0.3.1/web-frameworks/)). List an extension's routes in its `urls`:


```python
from citry import Citry, Extension, RouteResponse, URLRoute

def status(request):
    return RouteResponse(content="ok")

def greet(request, who):
    return RouteResponse(content=f"Hi {who}")

class ApiExt(Extension):
    name = "api"

    urls = [
        URLRoute("status", handler=status, name="status"),
        URLRoute("greet/{who}", handler=greet, name="greet"),
    ]

app = Citry(extensions=[ApiExt])
```


A route's handler takes the request plus any path parameters and returns a [RouteResponse](/v/0.3.1/reference/web/#citry-routeresponse). Path parameters are written as `{name}` and arrive as keyword arguments, so the `greet` handler above receives `who`.

Every extension's routes are gathered into `app.urls`. A user extension's routes are namespaced under `ext/<extension name>/`, so they can never collide with citry's own endpoints or another extension's. The `greet` route is therefore served at:


```text
ext/api/greet/{who}
```


under wherever the adapter mounts the instance. With the default prefix `/citry`, that is `/citry/ext/api/greet/ada`.

When a handler needs to reach engine state, define `urls` as a property so each handler can close over the extension and read `self.citry`:


```python
class InfoExt(Extension):
    name = "info"

    @property
    def urls(self):
        def info(request):
            count = len(set(self.citry.components.values()))
            return RouteResponse(content=f"{count} components")

        return [URLRoute("info", handler=info, name="info")]
```


## Reference

For the complete list of hooks, context dataclasses, and command building blocks, see the Extensions reference category, including [Extension](/v/0.3.1/reference/extensions/#citry-extension), [ExtensionManager](/v/0.3.1/reference/extensions/#citry-extensionmanager), [ExtensionConfig](/v/0.3.1/reference/extensions/#citry-extensionconfig), [ExtensionCommand](/v/0.3.1/reference/extensions/#citry-extensioncommand), [CommandArg](/v/0.3.1/reference/extensions/#citry-commandarg), [CommandArgGroup](/v/0.3.1/reference/extensions/#citry-commandarggroup), and [CommandSubcommand](/v/0.3.1/reference/extensions/#citry-commandsubcommand).