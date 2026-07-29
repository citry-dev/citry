---
title: Provide and inject
url: https://citry.dev/v/0.3.1/concepts/provide-and-inject/
description: "Pass data to a whole subtree of components without threading props through every level in between."
---
# Provide and inject

Sometimes a piece of data (the current theme, the logged-in user, a request
object) is needed deep in your component tree, but the components in between
have no use for it. Passing it as a prop through every level (prop drilling)
is noise.

Provide and inject solve this. A component makes data available to everything
rendered below it, and any descendant that wants it reads it directly. This is
citry's version of React context or Vue's provide/inject.

## The two halves

- A provider sets data under a string `key`, either with the `<c-provide>`
  built-in tag in a template or with `self.provide(key, **data)` in Python.
- A descendant reads the nearest provided value with `self.inject(key)`.

The data never becomes a template variable. Descendants must opt in by calling
`inject` explicitly.

## Provide in a template

`<c-provide>` is a built-in, transparent component: it adds no markup of its
own. Its `key` attribute names the data, and every other attribute becomes a
provided field.


```citry
from citry import Citry, Component

c = Citry()

class Themed(Component):
    citry = c
    template = """
        <span>{{ mode }}</span>
    """

    def template_data(self, kwargs, slots):
        return {"mode": self.inject("theme").mode}

class Page(Component):
    citry = c
    template = """
        <c-provide key="theme" mode="dark">
          <c-themed />
        </c-provide>
    """

assert "dark" in str(Page())
```


`<c-themed>` never received `mode` as a prop. It reached up the tree and read
it.

## The read shape: attribute access

`self.inject(key)` returns an immutable payload with each provided field
exposed as an attribute. You read `self.inject("theme").mode`, not a dict
lookup.

Static attributes on `<c-provide>` are strings. `c-*` attributes are evaluated
as expressions, and `c-bind` spreads a dict.


```citry
class Page(Component):
    citry = c
    template = """
      <c-provide
        key="my_provide"
        text="hi"
        c-num="1 + 1"
      >
        <c-reader />
      </c-provide>
    """

# inside Reader.template_data:
#   payload = self.inject("my_provide")
#   payload.text == "hi"   (static attribute -> string)
#   payload.num  == 2      (c-* attribute -> evaluated)
```


The payload is immutable. Assigning to a field (`payload.num = 3`) raises
`AttributeError`.

## Provide from Python

You can also provide from an ancestor's `template_data`, before it returns.
`key` is positional-only, so a field named `key` is still allowed.


```citry
from citry import Citry, Component

c = Citry()

class Child(Component):
    citry = c
    template = """
        <span>{{ user }}</span>
    """

    def template_data(self, kwargs, slots):
        return {"user": self.inject("user_data").user}

class Page(Component):
    citry = c
    template = """
        <c-child />
    """

    def template_data(self, kwargs, slots):
        self.provide("user_data", user="Jo")
        return {}

assert "Jo" in str(Page())
```


## Missing keys and defaults

`inject` has three modes:


```python
value = self.inject("maybe_missing", "fallback")  # "fallback" if not provided
value = self.inject("maybe_missing", None)        # None if not provided
value = self.inject("must_exist")                 # raises KeyError if missing
```


An explicit `None` default is honored and is different from omitting the
default. Injecting a never-provided key with no default raises `KeyError` (with
a "Did you mean" hint for similar keys), so pass a default (even `None`) when a
missing key should be non-fatal.

## End an inherited scope

Compound components sometimes need user content to establish a fresh context
before it can use another compound child. Call `self.unprovide(key)` from
`template_data` to make one inherited key appear missing to descendants:


```citry
class CompoundBoundary(Component):
    def template_data(self, kwargs, slots):
        current = self.inject("compound")
        self.unprovide("compound")
        return {"current": current}
```


The boundary component can still inject the inherited payload itself. A direct
descendant observes the key as missing, while a nearer descendant can restore
it with `provide()`. This is useful for rules such as requiring `Tabs > Tab >
Tabs > Tab` instead of letting an inner Tab accidentally join the outer Tabs
state.

## What to watch for

- A component's own provide is invisible to its own inject. `self.provide("x", ...)`
  then `self.inject("x")` in the same `template_data` will not see it;
  provided data flows only to descendants.
- The provide is visible only inside the `<c-provide>` tag. Siblings after the
  closing `</c-provide>` do not see it.
- Provided data does not enter template variables and does not shadow them. A
  provided field named `a` does not change what `{{ a }}` renders. Descendants
  must call `inject`.
- Nested provides with the same key replace wholesale, they do not merge. An
  inner `<c-provide key="k" a="2">` fully shadows an outer
  `<c-provide key="k" a="1" lost="0">` for that subtree, and the outer's `lost`
  field is gone there. Different keys compose independently.
- A key must be a non-empty valid Python identifier. `key=""`, `key="with-dash"`,
  and `key="with space"` all raise.

## How far the data reaches

Provided data travels along the render path, not just the literal nesting in
one template's source. It reaches components rendered inside slot content below
the provider too, so a `<c-provide>` wrapping a slot makes its data available
to whatever fills that slot. See [Slots](/v/0.3.1/concepts/slots/) for how slot content
is rendered.

## Provide and inject in client code

Client components use the same three operations in
[`$component`](/v/0.3.1/reference/browser-apis/#component) setup:


```js
$component(({ reactive, provide, inject, unprovide }) => {
  const parentTheme = inject("theme", null);
  const theme = reactive({ name: parentTheme?.name ?? "light" });

  provide("theme", theme);
  unprovide("outer-tabs");
});
```


Alpine expressions use the corresponding [`$provide`](/v/0.3.1/reference/browser-apis/#provide),
[`$inject`](/v/0.3.1/reference/browser-apis/#inject), and [`$unprovide`](/v/0.3.1/reference/browser-apis/#unprovide) magics. Establish values
and boundaries during initialization, normally in `x-init`:


```html
<section x-init="$provide('theme', { name: 'dark' })">
  <output x-text="$inject('theme').name"></output>

  <div x-init="$unprovide('theme')">
    <output x-text="$inject('theme', 'system')"></output>
  </div>
</section>
```


JavaScript passes one value because plain objects, reactive objects,
functions, and primitives are all natural values in that language. Citry
returns the exact value that was provided. Python uses keyword fields because
that mirrors `<c-provide key="x" field="...">` and makes attribute access on
the resulting payload convenient.

Client keys may be non-empty strings or symbols. A provided `undefined` is
different from a missing key, and an explicit default of `undefined` is
honored. Without a default, a missing key throws a browser error that names
the requested key.

Like the Python API, an owner's own provide or boundary is outgoing only. An
`inject` in the same component setup or on the same element reads the
inherited value. Descendants see the new value or boundary, and a nearer
provide can restore a key after `unprovide`.

`provide` and `unprovide` change context topology, so Citry accepts them only
during synchronous initialization. For changing data, provide one stable
reactive object and mutate its fields later. `inject` remains callable while
its component or element is live. When a morph installs, replaces, or removes
a provider declaration, Alpine expressions containing `$inject` run again and
resolve the current nearest value. Citry still returns the exact provided
value; it does not wrap or copy it.

The same re-resolution happens when live HTML containing a consumer moves
under different ancestors. Providers declared through object-form `x-bind` or
programmatic `Alpine.bind()` have the same lifetime as the Alpine directive
that created them; cleaning up that binding removes its provided value.

Like other Alpine magics, `$inject` is bound when you read it. If you store the
helper in `x-data`, it keeps that element's context when called later, even
after `await`. Write `$inject(...)` directly in a descendant expression when
you want the descendant's rendered context.

Context follows where HTML is rendered. A fill keeps the caller's Alpine
variables, but `$inject` inside it sees providers around the receiver's
`<c-slot>`. A native `x-teleport` keeps the context of its authored origin.
This is why context remains correct even when browser DOM ancestry alone would
point somewhere else.

One component hook can sometimes represent several rendered placements, such
as the same server fragment inserted into several targets. Its `inject()` call
returns only when every placement inherits the same value by JavaScript
identity. If the placements inherit different values, Citry raises an
ambiguity error; use `$inject()` in the placement's template when each copy
should read its own surroundings. A blocked key and a key with no provider are
both missing for this comparison.

## Navigating the component tree

Provide and inject reach data from above. Sometimes you do not want data, only
to know where a component sits when components are nested. citry exposes that,
and a couple of other render-time details, on `self`. All of them are readable
inside the data methods (`template_data`, `js_data`, `css_data`) and inside
`on_render`.

Three attributes describe the component's place in the tree:

- `self.parent` is the component that wrote this one into its template, or
  `None` when this component is the root of the tree.
- `self.root` is the component at the top of that chain. For the root itself,
  `self.root is self`.
- `self.ancestors` walks the whole chain, nearest first: the parent, then its
  parent, up to the root. It is empty for the root.

A descendant can read these to adapt to where it is rendered, with no prop
threaded down to it:


```citry
from citry import Citry, Component

c = Citry()

class Theme(Component):
    citry = c
    template = """
        <div class="theme-dark">
          <c-toolbar />
        </div>
    """

class Toolbar(Component):
    citry = c
    template = """
        <div c-class="css">tools</div>
    """

    def template_data(self, kwargs, slots):
        # Adjust styling when wrapped in a Theme, with no prop passed in.
        in_theme = any(isinstance(a, Theme) for a in self.ancestors)
        return {"css": "toolbar is-themed" if in_theme else "toolbar"}

# Written inside Theme's template, so Theme is an ancestor.
assert "is-themed" in str(Theme())
# Rendered on its own, Toolbar is the root, so no ancestors.
assert "is-themed" not in str(Toolbar())
```


`self.ancestors` is an iterator, so read it fresh each time, or wrap it in
`list(...)` when you need to walk it twice.

These three follow the component that wrote another into its template, not the
component whose slot rendered it. A component passed into another's slot keeps
the fill's author as its parent, so it will not find the slot host among its
ancestors. When you need "what am I rendered inside, slots included", provide
and inject are the tool: they follow the render path and cross slot boundaries,
as shown above. See [Slots](/v/0.3.1/concepts/slots/) for that difference.

## A unique id per render

`self.id` is a short id for the current render call, like `c1a2b3c4d`. A fresh one
is minted every render, so the same component rendered twice gets two different
ids. It is useful for building a DOM id that stays unique when a component
appears many times on one page:


```citry
from citry import Citry, Component

c = Citry()

class Field(Component):
    citry = c
    template = """
        <input c-id="input_id" />
    """

    def template_data(self, kwargs, slots):
        # A fresh id each render, so repeated Fields on one page
        # never collide on the same element id.
        return {"input_id": f"input-{self.id}"}

# The same component rendered twice gets two different ids.
assert str(Field()) != str(Field())
```


The `c-id` here computes the `id` attribute from an expression; see
[Dynamic attributes](/v/0.3.1/syntax/dynamic-attributes/) for that syntax, and `c-bind`
for wiring a matching `<label for>`.

For an id that is stable across renders and runs (handy for keying a cache or a
script URL), read `class_id` instead. It identifies the component class, as the
class name plus a short hash of its import path, and is the same every time:


```citry
from citry import Citry, Component

c = Citry()

class Card(Component):
    citry = c
    template = """
        <div>card</div>
    """

print(Card.class_id)  # e.g. "Card_1a2b3c"
```


Read `class_id` on the class (`Card.class_id`), or as `type(self).class_id`
inside a method. Unlike `self.id`, it is not an attribute of an instance.

## Reading a component's inputs

The data methods receive the component's inputs as their `kwargs` and `slots`
parameters, as the examples throughout this page do. The same inputs are also on
`self` for the length of the render, which is handy in `on_render` or the JS and
CSS data methods:

- `self.kwargs` and `self.slots` are the typed inputs when the component
  declares a `Kwargs` or `Slots` class, and plain dicts otherwise.
- `self.raw_kwargs` and `self.raw_slots` are always plain dicts, whatever typing
  you declared.


```citry
from citry import Citry, Component

c = Citry()

class Banner(Component):
    citry = c

    class Kwargs:
        text: str

    template = """
        <div>{{ text }}</div>
    """

    def template_data(self, kwargs: Kwargs, slots):
        return {"text": kwargs.text}

    def on_render(self):
        # The same inputs are on self, and also as plain dicts.
        assert self.kwargs.text == "hello"
        assert self.raw_kwargs == {"text": "hello"}
        return None

assert "hello" in str(Banner(text="hello"))
```


A citry component is called with keyword arguments and slots, so `kwargs` and
`slots` are the only inputs to read; there are no positional arguments.

The [Component](/v/0.3.1/reference/component/#citry-component) `provide`, `inject`, and `unprovide` methods,
together with the render-time attributes above (`parent`, `root`, `ancestors`,
and `id`), are what a component reaches for while it renders. For where these
fit in a render, see [Rendering](/v/0.3.1/concepts/rendering/).<script src="/citry/citry.js"></script><script type="application/json" data-citry-graph>{"delimiters":{"format":"citry:g1"},"graphs":[{"componentClasses":[],"componentExecutionOrderConstraints":[],"componentInstances":[],"fills":[],"graphId":0,"nestedComponents":[],"slotRegions":[],"sourceLocations":[]}],"mode":"production","protocol":"citry-client-graph/1","revision":"16111e302b0b67f45a6c98682743d59aa151d6f7ac93c97d9e3cf1a14dd08fa7"}</script><script type="application/json" data-citry>{"markLoaded": {"js": ["L2NpdHJ5L2V4dC9ldmVudHMvcnVudGltZS5qcw=="], "css": []}, "fetch": {"js": [], "css": []}, "calls": [], "cssInstances": [], "graph": "16111e302b0b67f45a6c98682743d59aa151d6f7ac93c97d9e3cf1a14dd08fa7"}</script><script src="/citry/ext/events/runtime.js"></script>