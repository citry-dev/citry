---
title: Subclassing components
url: https://citry.dev/v/0.4.6/advanced/subclassing/
description: "Reuse a component contract while changing its template, browser code, styles, dependencies, or Python behavior."
---
# Subclassing components

Subclass a component when several variants deliberately share the same inputs
and behavior. Put the shared work on one base class, then let each child change
only the part that makes it different.

When two pieces need independent public APIs, build one from the other as
nested components. Inheritance is most useful when every child really is
another form of the same component.

## Reuse Python inputs and behavior

A child keeps the inputs and methods of its parent. Declare another nested
schema on the child when it needs more fields. Citry combines those fields
with the ones from the parent.


```citry
from citry import Component


class Message(Component):
    class Kwargs:
        text: str

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, str]:
        return {"message": self.format_message(kwargs.text)}

    def format_message(self, text: str) -> str:
        return text

    template = """
      <p>{{ message }}</p>
    """


class LoudMessage(Message):
    class Kwargs:
        pass

    class Slots:
        pass

    def format_message(self, text: str) -> str:
        return text.upper()
```


The empty nested declarations give `LoudMessage` its own schema types while
keeping the fields from `Message`. It also keeps the parent's data method and
template. The inherited `template_data()` calls the child's
`format_message()`, so the final text is uppercase.

A child may also call `super()` and adjust the returned data:


```citry
class TitledMessage(Message):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, str]:
        data = super().template_data(kwargs, slots)
        data["message"] = f"Notice: {data['message']}"
        return data
```


Citry combines the same set of declarations across a component family:

- [`Kwargs`][cotry.Component.Kwargs] and [`Slots`](/v/0.4.6/reference/component/#citry-component-slots) describe inputs;
- [`TemplateData`](/v/0.4.6/reference/component/#citry-component-templatedata), [`JsData`](/v/0.4.6/reference/component/#citry-component-jsdata), and [`CssData`](/v/0.4.6/reference/component/#citry-component-cssdata) describe returned data;
- the events extension adds [`State`](/v/0.4.6/reference/component/#citry-component-state) and [`Events`](/v/0.4.6/reference/component/#citry-component-events).

Set a declaration to `None` when the child should start without the parent's
declaration:


```citry
class FreeformMessage(Message):
    Kwargs = None
```


Plain classes, dataclasses, named tuples, Pydantic models, and other supported
schema styles do not all combine in the same way. Citry reports incompatible
mixtures when the child class is created. See
[Inputs and validation](/v/0.4.6/concepts/inputs-and-validation/) before mixing schema
styles across a component family.

## Change one primary asset

The primary assets form three independent inline-or-file pairs:

- [`template`](/v/0.4.6/reference/component/#citry-component-template) and `template_file`;
- [`js`](/v/0.4.6/reference/component/#citry-component-js) and `js_file`;
- [`css`](/v/0.4.6/reference/component/#citry-component-css) and `css_file`.

If a child does not mention a pair, it inherits that pair. If it sets either
member, that child owns the whole pair. This means a child `template_file`
replaces a parent's inline `template`, while the parent's JS and CSS can still
be inherited:


```citry
from citry import Component


class BaseCard(Component):
    class Kwargs:
        title: str

    template = """
      <article class="card">
        <h2>{{ title }}</h2>
      </article>
    """
    js = """
      $component(({ els }) => {
        els[0].dataset.ready = "true";
      });
    """
    css = """
      .card {
        border: 1px solid currentColor;
      }
    """


class LinkedCard(BaseCard):
    template_file = "linked_card.html"
```


`LinkedCard` reads its own template file and keeps `BaseCard`'s JS and CSS.
Setting both non-empty members of one pair on the same class raises
`ValueError` when the class is defined.

Set one member to `None` when a child should have no asset for that pair:


```citry
class StaticCard(BaseCard):
    js = None
```


Leaving `js` out would inherit it. Writing `js = None` makes the choice
explicit and stops the search through base classes for that pair.

## Dependencies inheritance

The nested `Dependencies` class lists secondary scripts and styles. These
entries merge across base classes by default. Base entries come first and the
child's entries come last, so the child's stylesheet wins an
equal-specificity CSS tie by document order.


```citry
from citry import Component, SlotInput


class BaseDialog(Component):
    class Slots:
        default: SlotInput

    class Dependencies:
        js = ["/static/dialog.js"]
        css = ["/static/dialog.css"]

    template = """
      <dialog>
        <c-slot />
      </dialog>
    """


class ConfirmDialog(BaseDialog):
    class Dependencies:
        css = ["/static/confirm-dialog.css"]
```


`ConfirmDialog` receives `dialog.js`, `dialog.css`, and then
`confirm-dialog.css`. Duplicate URLs and duplicate inline content keep their
first position. The first entry wins completely, including its tag
attributes; a later duplicate cannot add another attribute.

The `extend` setting chooses which branches contribute:

- `extend = True`, the default, includes the ordinary base classes;
- `extend = False` includes only this class's entries;
- `extend = [CompactTheme, BrandTheme]` includes exactly those classes and
  their selected bases, in the written order.

Set `Dependencies = None` to contribute no secondary assets and stop
dependency inheritance through that branch.

The [Dependency files](/v/0.4.6/advanced/dependency-files/) guide covers dependency
entry forms, local files, URLs, and serving.

## Keep the shared contract deliberate

Before adding a child, ask whether it should keep the parent's inputs,
browser behavior, styles, and future changes. A shared base works well when
the answer is yes. Composition is easier to change independently when the
answer differs for only one part of the component.