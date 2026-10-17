---
title: Component JS and CSS
description: Give a Citry component its own JavaScript and CSS, send it data from Python, and see how both behave on the page.
---

# Component JS and CSS

A component often needs a little browser code or a few styles of its own: a
panel that opens and closes, a chart that draws itself, a banner in a color
the page chooses. Put that code on the component, in `js` and `css`. Citry
adds it to every page that renders the component, once per page however many
times the component appears.

This page covers code that belongs to one component. To add a library or a
shared file, see [Dependency files](/advanced/dependency-files/). To choose
where the tags go in the page, see
[Place JavaScript and CSS](/advanced/asset-placement/). For the Vue
attributes you write in templates, such as `@click` and `v-show`, see
[Vue in templates](/syntax/vue/), and for the options the `js` passes to
Vue, see [Component options](/vue/component-options/).

## `js` and `css` attributes

```citry
from citry import Component


class Disclosure(Component):
    template = """
      <section class="disclosure">
        <button type="button" @click="toggle">
          Details
        </button>
        <div v-show="open">
          <c-slot />
        </div>
      </section>
    """

    js = """
      $component({
        data() {
          return { open: false };
        },
        methods: {
          toggle() {
            this.open = !this.open;
          },
        },
      });
    """

    css = """
      .disclosure {
        border: 1px solid #d0d5dd;
      }
    """
```

Python renders the HTML on the server. In the browser, each `Disclosure` on
the page becomes a [Vue](https://vuejs.org/){: target="_blank" rel="noopener"}
component with its own `open` value, and the CSS styles all of them.

## Component JavaScript

The code in `js` runs in the browser. It calls
[`$component({...})`][$component] once, at its top level, with the same
options as a Vue component. [Component options](/vue/component-options/)
covers what goes there:

- [`data()`, `computed`, `methods`, and `watch`](/vue/component-options/#data-and-methods)
  for browser state and behavior;
- [`js_data()`](/vue/component-options/#seed-browser-data-from-python) to
  start that state from Python values;
- [`onServerRender`](/vue/component-options/#react-after-a-server-render)
  for code that runs again after each server render;
- [shared helpers](/vue/component-options/#share-helpers) outside
  `$component()`, and [`Citry.vue`](/vue/component-options/#use-citry-vue)
  for Vue's own functions.

For props and events between components, see
[Props and events](/vue/props-and-events/).
[Where each value goes](/vue/#where-each-value-goes) shows which Python
value reaches the template, the JavaScript, and the CSS.

## JS data must be JSON

Citry sends the values that
[`js_data()`](/vue/component-options/#seed-browser-data-from-python)
returns to the browser as JSON. Each value must be one of:

- `str`, `int`, `bool`, or `None`;
- a `float` that is finite (`NaN` and infinity raise `ValueError`);
- a `list` or `tuple` (sent as a list) of these values;
- a `dict` with `str` keys and these values.

The top-level keys must be `str` too. Any other value raises an error when
you turn the render into HTML by calling `str()` or `.serialize()` on it.
That includes `datetime`, `Decimal`, `set`, enum members, subclasses of
`str` such as `Markup`, and dataclass or Pydantic instances nested inside
the data. The error names the component and the type:

```text
TypeError: js_data() of component 'Sparkline_c92051' returned an
unsupported value: data sent to the browser must contain only dicts,
lists, strings, numbers, booleans, and None, got datetime.
```

Convert such values in `js_data()` first:

```python
def js_data(self, kwargs: Kwargs, slots):
    return {
        "updatedAt": kwargs.updated_at.isoformat(),
        "total": str(kwargs.total),  # a Decimal
        "task": dataclasses.asdict(kwargs.task),
        "user": kwargs.user.model_dump(mode="json"),
    }
```

Returning a dataclass or Pydantic instance as the whole result works:
Citry turns its fields into the top-level keys. Values inside those fields
must still follow the rules above.

JavaScript numbers lose precision above 2^53, so send large IDs as
strings.

## Send values to CSS

Return a mapping from [`css_data()`][citry.Component.css_data] to give one
render's values to its CSS. Each key becomes a CSS custom property that
you read with `var(--<key>)`:

```citry
from citry import Component


class Banner(Component):
    class Kwargs:
        color: str = "#fde68a"

    def css_data(self, kwargs: Kwargs, slots):
        return {"banner_color": kwargs.color}

    template = """
      <div class="banner">
        <c-slot />
      </div>
    """

    css = """
      .banner {
        background: var(--banner_color);
      }
    """
```

Citry marks the component's root element with a generated attribute and
sets the property only on the elements that carry it. Simplified,
`Banner()` renders:

```html
<style>
  .banner {
    background: var(--banner_color);
  }
</style>
<style>
  [data-ccss-b097b034] {
    --banner_color: #fde68a;
  }
</style>
<div class="banner" data-ccss-b097b034></div>
```

So the banner's background is `#fde68a`. Citry generates the attribute
name from the values, so do not write selectors against it. A
`Banner(color="#bfdbfe")` on the same page gets a different attribute and
its own color. Renders with the same values share one attribute and one
stylesheet.

The component needs its own `css` for this to work. Without it, Citry
drops the `css_data()` values without an error.

Each value must be a string, a finite number (not a boolean), or `None`,
which leaves the property empty. Any other value, such as a `bool` or a
`list`, raises `ValueError` when the component renders. A key must
be a string that is valid as the name of a custom property, without the
leading `--`. Citry quotes a string that contains spaces,
unless it starts with a CSS function such as `calc(...)` or `rgba(...)`.
It raises `ValueError` for a value that could break out of the generated
CSS, such as one with a top-level `;` or a `</style` end tag.

!!! warning "Keep secrets out of CSS data"

    Citry can deliver these values as a stylesheet at a URL. Anyone who
    has the URL can download it, so never put a secret in `css_data()`.

## Name CSS classes

Component CSS is not scoped to the component. Citry adds the rules to the
page as written, so `.label` in one component styles every `.label` on the
page, including those in other components.

Start every class name with the component's name, and name the parts and
variants after it:

```citry
class PriceBadge(Component):
    template = """
      <span
        class="price-badge"
        c-class="{'price-badge--high': high}"
      >
        <span class="price-badge__label">Price</span>
        {{ amount }}
      </span>
    """

    css = """
      .price-badge {
        padding: 0 0.5rem;
      }
      .price-badge__label {
        font-weight: 600;
      }
      .price-badge--high {
        color: #b42318;
      }
    """
```

This is the BEM naming style: `block__element` for a part and
`block--modifier` for a variant. Citry has no option that scopes component
CSS for you.

## `js_file` and `css_file`

Use `js_file` and `css_file` to keep the code in files next to the
component:

```citry
from citry import Component


class Calendar(Component):
    template_file = "calendar.html"
    js_file = "calendar.js"
    css_file = "calendar.css"
```

Citry finds these files the same way it finds `template_file`. Set either
`js` or `js_file`, not both, and either `css` or `css_file`. Setting both
raises `ValueError` when the class is defined.

## `JsData` and `CssData`

Declare a nested `JsData` or `CssData` class to have Citry check the names
that `js_data()` or `css_data()` returns. A missing or unexpected name then
raises `TypeError` when the component renders. Return either an instance of
the class or a plain dictionary:

```citry
class Sparkline(Component):
    class JsData:
        points: list[int]

    def js_data(self, kwargs: Kwargs, slots) -> JsData:
        return self.JsData(points=kwargs.points)
```

A plain annotated class checks names, not the type of each value. See
[Inputs and validation](/concepts/inputs-and-validation/) for schema styles
that also check types.

## How CSS loads

- **Once per page.** A component's CSS appears once, however many copies
  render. Two components with exactly the same CSS share one stylesheet.
- **Order.** Stylesheets from [dependency files](/advanced/dependency-files/)
  come first, then component CSS, in the order the components first
  render. When two rules conflict, give one a more specific selector
  rather than relying on the order.
- **Place.** By default the styles go at the end of `<head>`. See
  [Place JavaScript and CSS](/advanced/asset-placement/) to change it.
- **Media types.** Component CSS applies to every media type. To load a
  stylesheet only for print or another media type, use a
  [dependency file](/advanced/dependency-files/).
- **CSP nonce.** A nonce passed to `serialize(csp_nonce=...)` goes on every
  style tag Citry adds; see
  [Add a CSP nonce](/vue/csp/#use-content-security-policy).

## When CSS is removed

On an interactive page, Citry tracks which components on the page use each
stylesheet. When a server render removes the last component that uses one,
Citry removes the stylesheet too, and adds it back if the component
returns. A stylesheet that other components on the page still use stays.

A component that disappears only in the browser, such as one inside a
`v-if` that turned false, keeps its stylesheet. So does every stylesheet
on a page without Vue, where nothing runs in the browser to remove it.

## Highlight inline code

JetBrains editors highlight a string in the language named by a comment
just above it:

```citry
class Calendar(Component):
    # language=HTML
    template = """
      <div class="calendar">Today</div>
    """

    # language=CSS
    css = """
      .calendar {
        width: 12rem;
      }
    """
```

Some VS Code extensions read type annotations instead, such as
`template: "html"`, `css: "css"`, and `js: "js"`. These hints change only
how the editor shows the code.

## Next steps

- [Component options](/vue/component-options/) covers everything you can
  pass to `$component({...})`.
- [Props and events](/vue/props-and-events/) covers Vue props, events, and
  attributes between components.
- [Browser APIs](/reference/browser-apis/) lists `$component`,
  `onServerRender`, and `Citry.vue` in full.
- [Dependency files](/advanced/dependency-files/) adds libraries and shared
  files that several components use.
- [Place JavaScript and CSS](/advanced/asset-placement/) chooses where the
  tags go in the page.
- [Component hooks](/advanced/hooks/) changes the tags one component adds.
- [HTML fragments](/advanced/html-fragments/) adds the JavaScript and CSS
  of new components to a page that is already open.
