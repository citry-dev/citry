---
title: Component JavaScript and CSS
url: https://citry.dev/v/0.4.1/advanced/js-and-css-dependencies/
description: "Give a Citry component its own JavaScript, CSS, and per-render browser data."
---
# Component JavaScript and CSS

A reusable component can bring the behavior and styles it needs. Put its
JavaScript in `js` and its CSS in `css`. Citry collects those assets when the
component renders and includes each one once in the finished page.

This page covers assets owned by one component. For libraries and shared
files, see [Dependency files](/v/0.4.1/advanced/dependency-files/). To control where
the collected tags appear, see
[Place JavaScript and CSS](/v/0.4.1/advanced/asset-placement/).

## Add behavior and styles

This chart sends its points and height from Python to the browser:


```citry
from citry import Component


class Chart(Component):
    class Kwargs:
        points: list[int]
        height: str = "240px"

    class JsData:
        chart_points: list[int]

    class CssData:
        chart_height: str

    def js_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> JsData:
        return self.JsData(chart_points=kwargs.points)

    def css_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> CssData:
        return self.CssData(chart_height=kwargs.height)

    template = """
      <div class="chart"></div>
    """

    js = """
      $component(({ els, data }) => {
        const chartPoints = data.chart_points;
        drawChart(els[0], chartPoints);
      });
    """

    css = """
      .chart {
        height: var(--chart_height);
      }
    """
```


[`$component()`](/v/0.4.1/reference/browser-apis/#component) registers a callback for each rendered `Chart`.
Its `els` value contains the component's root elements. Its `data` value is
what that render returned from [`js_data()`](/v/0.4.1/reference/component/#citry-component-js-data).

Code outside `$component()` runs once when the component script loads. Keep
page-wide setup there. Put code that reads one rendered component's elements
or data inside the callback:


```javascript
console.log("The chart script loaded");

$component(({ els, data }) => {
  console.log("One chart is ready", els, data);
});
```


Citry wraps classic component JavaScript in a self-executing function. Its
top-level variables therefore stay private to that script.

## Send data to JavaScript

[`js_data()`](/v/0.4.1/reference/component/#citry-component-js-data) returns the data for one render. Citry
serializes it as strict JSON, seeds its top-level keys into that render's
Alpine scope, and gives a fresh instance-local graph to that render's
`$component()` callback when one exists.

The returned mapping must follow these rules:

- every key is an exact `str`;
- every value is JSON-serializable;
- numbers are finite, so `NaN` and infinity are rejected.

An Alpine expression can read those keys directly, so `$component()` is not
required only to copy server data into scope. A render with neither Alpine
expressions nor a live `$component()` call does not send the data. Identical
payloads are transported once, but nested arrays and objects are not shared
between instances.

Python names normally use `snake_case`. Assign them to `camelCase` names when
browser code keeps using them:


```javascript
const chartPoints = data.chart_points;
```


That small distinction makes it easier to see which language owns a name.

## Send data to CSS

[`css_data()`](/v/0.4.1/reference/component/#citry-component-css-data) turns one render's values into CSS
custom properties. A returned `{"chart_height": "240px"}` is available as
`var(--chart_height)` inside that component.

CSS data follows a narrower contract:

- every key is an exact `str` and a valid custom-property suffix;
- values are strings, finite numbers, or `None`;
- booleans and structured values are rejected.

Citry quotes and escapes strings with spaces, unless the value starts with a
CSS function such as `calc(...)` or `rgba(...)`. It also rejects values that
could break out of the generated declaration, such as a top-level semicolon,
an unmatched block, or a `</style` end tag. The browser still decides whether
the value makes sense for the CSS property that uses it.

CSS data is only emitted when the component has CSS that could use it.

## Check the returned shape

`JsData` and `CssData` are optional. When present, they catch missing and
unexpected fields in the mapping returned by the matching method. You may
return an instance, as `Chart` does above, or a plain dictionary.

Plain annotated schemas check field names, not the runtime type of every
value. JSON and CSS serialization still apply their own value rules. See
[Inputs and validation](/v/0.4.1/concepts/inputs-and-validation/) for the available
schema styles.

## Read source from files

Use `js_file` or `css_file` when the primary source lives beside the component
instead of inside its Python class:


```citry
from citry import Component


class Calendar(Component):
    template_file = "calendar.html"
    js_file = "calendar.js"
    css_file = "calendar.css"
```


Citry resolves these files like `template_file`. For each asset, choose either
the inline value or the file value. Defining both `js` and `js_file`, or both
`css` and `css_file`, raises `ValueError`.

Use the nested `Dependencies` declaration for files that the component uses
but does not own, such as a charting library or a shared stylesheet.

## Highlight inline source in an editor

JetBrains editors understand a language comment immediately above an inline
asset:


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


VS Code extensions for inline source can use annotations such as
`template: "html"`, `css: "css"`, and `js: "js"`. These hints affect only
editor highlighting.

## Next steps

- [Dependency files](/v/0.4.1/advanced/dependency-files/) adds libraries, shared
  files, tag attributes, and local-file serving.
- [Place JavaScript and CSS](/v/0.4.1/advanced/asset-placement/) controls where and
  how the collected tags are inserted.
- [Component hooks](/v/0.4.1/advanced/hooks/) adjusts the tags contributed by one
  component.
- [HTML fragments](/v/0.4.1/advanced/html-fragments/) carries new dependencies into
  an already-loaded page.