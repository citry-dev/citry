---
title: v1.1.0
url: https://citry.dev/v/1.2.0/releases/v1.1.0/
description: "What changed in citry v1.1.0."
---
# v1.1.0

Citry 1.1.0 is a security release, and it adds the first Experimental
APIs for the citry-django integration. It still requires citry-core
2.1.2.

## Fixes

- Security: on an interactive page, a value in an HTML attribute that
  contains `</head>` or `</body>` can no longer move Citry's CSS or JS
  tags into that attribute. Before, the stylesheet link could end the
  attribute and turn the rest of the value into markup that runs in
  the browser, and a `</body>` made `serialize()` fail. Citry now puts
  its tags only at the page's real `</head>` and `</body>`, in any
  letter case, and at the start or end of the output when the page has
  none or when Citry cannot tell which one is real. See
  [GHSA-5mm2-p7xq-jchq](https://github.com/citry-dev/citry/security/advisories/GHSA-5mm2-p7xq-jchq).
- You can now pass a `str` subclass, such as the `SafeString` URL
  that django-compressor produces, as `Script(url=...)` or
  `Style(url=...)`. Before, a page that Vue renders or an Events
  response failed with "Prepared browser asset URL differs from its
  structured dependency URL". Citry still checks such a URL like any
  other.
- An Events `Render` no longer fails with "unsupported raw output:
  Markup" when a `Markup` value reaches the rendered component, such as
  slot content passed from Python. It now renders as on the first page
  load, with the same checks.

## Added

- Experimental, groundwork for the citry-django integration: you can
  now get a render's asset tags apart from its HTML with
  `serialize_result(deps_position="separate")`, so a page that combines
  several renders writes shared tags, such as the browser runtime,
  once. `combine_assets()` does that for you, with one stylesheet tag
  for all the Vue apps that load the same file.
  `CitryRender.needs_browser_runtime()` returns whether
  a render needs the browser runtime. See
  [Combine several renders](https://citry.dev/advanced/asset-placement/#combine-several-renders).
- Experimental, groundwork for the citry-django integration: the asset
  tags that `deps_position="separate"` returns now say which components
  declared each tag and whether it holds one render's data, in each
  group's `css_entries` and `js_entries`. A tool that bundles tags can
  use them instead of reading the tags' attributes. See
  [Find a tag's components](https://citry.dev/advanced/asset-placement/#find-a-tags-components).
- Experimental, groundwork for the citry-django integration: when you
  serialize a child render on its own and it holds slot content from
  outside it, Citry now raises `OutsideSlotContentError`, so you can
  catch that case by type. It is a subclass of `TypeError`, so existing
  handlers keep working.
- An interactive component can now hold HTML from a template with
  foreign spans, such as a fill with Django tags, on the first render
  and in an Events `Render`. Citry inserts it as static HTML that Vue
  never compiles, and raises an error that names the problem when the
  HTML is not a complete fragment, holds a `<script>`, has an
  interactive component inside one of its elements, or comes from a
  template that also has Vue syntax such as `@click`. This prepares the
  citry-django integration. See
  [Put foreign output inside interactive components](https://citry.dev/advanced/extensions/#foreign-output-in-vue).
- Experimental, groundwork for the citry-django integration: you can
  catch each of those errors by type. They subclass `StaticHtmlError`:
  `IncompleteStaticHtmlError`, `VueInsideStaticHtmlError`,
  `ScriptInStaticHtmlError`, `VueSyntaxInStaticHtmlError`, and
  `StaticHtmlPlacementError`. Each one also subclasses the `ValueError`
  or `TypeError` that Citry raised before, so existing handlers keep
  working.
- Experimental: a component that an event handler returns can now
  read request values such as the current user or the locale, as it
  does when a view renders the page. Set `_render_inputs` in
  `extensions_defaults["events"]`, or on one component's `Events`
  class, to a function that takes the event call's `EventRequest` and
  returns a `RenderInputs` dict (from `citry.ext.events`): the `template_globals` and `provides`
  Citry passes to `.render()` for that call's renders. See
  [Pass request values](https://citry.dev/events/actions/#give-every-render-the-request-values).