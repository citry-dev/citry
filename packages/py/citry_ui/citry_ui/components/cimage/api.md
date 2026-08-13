---
title: Image
description: Render native responsive images with stable geometry and explicit alternative text.
---

# Image

Use `CImage` when content needs one native image with an explicit text
alternative, intrinsic dimensions, responsive candidates, and optional visual
loading or error treatments. The browser still owns fetching, candidate
selection, decoding, caching, CSP, CORS, and native image behavior.

Use the [WAI alternative-text decision tree](https://www.w3.org/WAI/tutorials/images/decision-tree/)
when the image's purpose is not obvious.

## Start with alternative text and geometry

`src`, `alt`, `width`, and `height` are required. Use concise meaningful text
for informative images. Use `alt=""` only when the image is truly decorative or
repeats nearby content. The dimensions reserve the native aspect ratio before
bytes arrive and do not force the final CSS size.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cimage/snippets/basic_image.py"
  title="Render a native image with stable geometry"
  source_open
/>

Choose the alternative for the image's purpose in context. An image-only link
needs destination text. A complex chart needs an adjacent data equivalent.
A caption does not replace `alt`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cimage/snippets/alternative_text.py"
  title="Compare informative, decorative, functional, and complex images"
/>

## Size and crop the rendered image

Use ordinary CSS to constrain rendered size. `fit` and `position` control the
pixels inside that box. Native `width` and `height` remain intrinsic metadata.
Public variables can override the aspect ratio, crop, position, radius, and
state colors without relying on private classes.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cimage/snippets/fit_and_geometry.py"
  title="Compare stable geometry and object fit"
/>

## Author responsive sources

Pass ordered frozen `CImageSource` records to emit a native `<picture>`. The
records are data, not component declarations. Native first-match order matters.
Width-descriptor `srcset` requires `sizes`, and arbitrary `media` text remains
browser syntax that the application must validate.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cimage/snippets/responsive_sources.py"
  title="Use srcset, sizes, art direction, and AVIF"
  source_open
/>

## Choose native loading and priority hints

Use `loading="eager"` and `fetch_priority="high"` only for a genuinely
important above-fold image. Keep ordinary archive media at native lazy or auto
priority. Image adds no observer, data-src indirection, preload, or custom
decode gate, so the resource stays discoverable in server HTML.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cimage/snippets/loading_priority.py"
  title="Compare eager and lazy native loading"
/>

## Add visual loading and error treatments

The `placeholder` and `fallback` slots are inert visual layers. They never
replace the native `<img>` or its `alt`. With JavaScript disabled, both custom
layers stay hidden and the browser shows the native image or broken-image text
fallback. Put meaningful error copy, retry controls, and live announcements
outside Image.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cimage/snippets/placeholder_and_error.py"
  title="Handle loading, error, and recovery"
/>

## Observe and update a request

Client props can update the resource, semantics, dimensions, hints, fit, and
callback. `onStatusChange` reports normalized `loading`, `loaded`, and `error`
settlement plus `current_src`, `natural_width`, and `natural_height`. The
`current_src` value snapshots the native `currentSrc`; treat it as potentially sensitive application data
and redact it before logging.

Responsive settlement follows native event truth. A browser may select a
broken `<picture>` candidate without emitting `error`; in that case Image keeps
the last accepted status and callback ledger. It does not invent an observer or
synthetic failure signal.

Native `@load` and `@error` listeners belong in `img_attrs`. Those events do
not bubble to root `attrs`. Native listeners run in isolated expression scope,
where `$event`, `$store`, `$dispatch`, and globals work but an ancestor's local
`x-data` identifiers do not cross the component boundary. The component
callback is the owner-local surface and also covers cached completion.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cimage/snippets/reactive_image.py"
  title="Switch resources and inspect normalized status"
/>

## Compose with native and Citry structure

Image is not a figure, Card, link, button, Skeleton, lightbox, or gallery. Wrap
it in those structures when they own the semantic job. A neighboring Skeleton
remains decorative, while the real image retains its alternative text.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cimage/snippets/image_composition.py"
  title="Compose Image with Card, Skeleton, figure, and link"
/>

## Keep delivery policy explicit

`cross_origin` and `referrer_policy` select native request modes; they do not
grant canvas access or repair server headers. `img-src` CSP remains
authoritative. Relative, HTTP, HTTPS, data, blob, raster, and SVG image URLs are
consumer-owned resource references, not sanitized or fetched by Citry. Active
`javascript:` and `vbscript:` schemes are rejected. Blob lifetime, data-URL
size, metadata privacy, origin policy, and remote tracking remain application
responsibilities.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cimage/snippets/delivery_and_security.py"
  title="Review CORS, referrer policy, CSP, and URL trust"
/>

## Understand lifecycle and fallback

Equal retained-node server morphs preserve the active request and status.
Changing request fields starts one new generation. Replacing the native image,
removing the owner, invalid structure, a closed ShadowRoot, or cross-document
adoption requires fresh ownership. Late work from an old generation cannot
notify a replacement owner.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cimage/snippets/image_lifecycle.py"
  title="Inspect retained, replaced, removed, and restored images"
/>

Without JavaScript, the server-rendered native image, ordered responsive
sources, required `alt`, dimensions, loading hints, CORS mode, and referrer
policy remain useful. Custom placeholder and fallback slots stay hidden so
they cannot cover the native result.

Image is not form-associated and adds no keyboard, focus, overlay, gesture,
retry, upload, editing, canvas, image-map, or lightbox behavior. Important
print images should use eager loading because printing does not guarantee a
lazy request will start before pagination.

<!-- UI_LIBRARY_API_REFERENCE -->
