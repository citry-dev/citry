---
title: Pure components
description: Render a component's template once per page when it repeats with the same data, and reuse that HTML for the other copies.
---

# Pure components

A small component such as a status icon can appear hundreds of times on
one page with only a few different values. By default Citry renders its
template again for every copy, even when the data is the same.

Declare [`pure = True`][citry.Component.pure] to render the template once
for each distinct set of template data and reuse that HTML for the other
copies on the same page. Use it only when the template's output depends
on nothing but its template data.

## Reuse repeated HTML

Set the flag on the class:

```citry
from citry import Component


class StatusIcon(Component):
    pure = True

    class Kwargs:
        state: str

    template = """
      <span c-class="state">{{ state }}</span>
    """
```

On a page with 300 `StatusIcon` calls and three states, Citry renders the
template three times. Every other call with the same template data reuses
the HTML of the first one.

Citry keeps that HTML only while it renders one page, meaning one
top-level render call such as `str(Page())`. The next page render starts
empty. To reuse output across requests, see
[Cache rendered output](/performance/caching/).

## What still runs

`pure = True` reuses only the HTML that the template itself produces.
Citry still does the rest for every copy:

- creates the component instance and gives it its own render ID, the
  value that identifies it in the browser;
- runs `template_data()` and the lifecycle hooks;
- renders child components, slot content, and translated text inside
  the template.

The saving is therefore largest for a component whose template does
most of its work itself.

## Check the template

`pure = True` is a promise that rendering the template always produces
the same HTML for the same template data and changes nothing else. Do not
declare it when the template:

- calls a function that changes state, such as a counter;
- reads a one-time iterator, such as a generator;
- reads a value that is not in its template data;
- relies on an extension hook that must run for every element.

If the promise is broken, later copies show the first copy's HTML.

Use it only where equal data repeats within one page. A component that
appears once, or receives different data every time, gains nothing.

## Edge cases

### Later class changes

`pure` is not inherited, and you cannot reassign it after the class is
defined. A subclass must declare `pure = True` itself,
because it can add behavior that breaks the promise.

### Combining with `simple`

A component can declare both `pure = True` and
[`simple = True`](/performance/simple-components/). The simple component
rules still apply, and a `simple = True` template that contains
`<c-slot />` renders again on every call. `simple = "vue"` cannot be
combined with `pure = True`; every call raises an error.

## Related pages

- [Performance overview](/performance/) compares `pure = True` with the
  other ways to speed up rendering.
- [Constant values](/performance/const/) reuse template work for single
  inputs that never change.
- [Simple components](/performance/simple-components/) skip the setup of
  each component instance.
- [Cache rendered output](/performance/caching/) reuses whole rendered
  components across requests.
