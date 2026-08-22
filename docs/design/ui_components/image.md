# Image

**Status:** implemented and independently reviewed, 2026-08-12.

**Research snapshot:** 2026-08-12. Browser probes used Chromium 151, Firefox 153,
and WebKit 26.5 from the repository Playwright installation.

This specification follows the
[`Citry UI family workflow`](../../../packages/py/citry_ui/docs/component-authoring.md#requalify-one-component-family-at-a-time),
the Fable research workflow, and the shared [component template](./_template.md).

## 1. Purpose and product bar

`CImage` renders a meaningful or decorative native image with stable reserved
geometry, browser-owned responsive source selection, and a small observable
load-settlement layer. It generalizes the proven `CAvatar` image lifecycle
without copying Avatar's identity semantics or becoming an image service.

The nearest native model is one `<img>`, optionally preceded by ordered
`<source>` elements in a `<picture>`. The native `<img>` remains the request,
fallback-text, accessibility, print, and decoding authority. The component is
earned over raw HTML by supplying all of the following as one reviewed family:

- required alternative-text and intrinsic-dimension decisions;
- validated responsive source metadata with native ordering;
- stable loading, loaded, and error settlement across cached responses,
  responsive candidate changes, source supersession, and morphs;
- visual placeholder and error fallback slots that never replace native image
  semantics;
- a compact, styled root with stable parts, fit and position variables, and
  no-JavaScript output; and
- callback details that identify the authored fallback `src` and the actual
  browser-selected `currentSrc`; applications retain their own identity for a
  larger responsive set when they need to distinguish equal selected URLs.

Common jobs and their shortest intended forms are:

| Job | Template or Python expression | Support path |
|---|---|---|
| Informative image | `<c-CImage src="/nebula.jpg" alt="The Orion Nebula" width="1280" height="720" />` | Direct API |
| Decorative image | `<c-CImage src="/wash.jpg" alt="" width="1280" height="720" />` | Direct API using native empty `alt` |
| Art direction | `CImage(..., sources=(CImageSource(media="(min-width: 60rem)", srcset="/wide.jpg"),))` | Direct `sources` record API and native `<picture>` |
| Density or width candidates | `srcset` plus `sizes` on `CImage` | Direct API and native selection |
| Stable crop | `fit="cover"`, intrinsic `width` and `height`, optional CSS size | Direct API plus CSS |
| Below-fold loading | `loading="lazy"` | Native attribute; no observer loader |
| Important hero | `loading="eager"`, `fetch_priority="high"` used sparingly | Native attributes and application performance policy |
| Placeholder and error treatment | `placeholder` and `fallback` slots | Composition; visual only |
| Card media | `CImage` in `CCard`'s `media` slot | Composition |
| User identity | `CAvatar` | Separate component |
| Captioned figure | native `<figure>` and `<figcaption>` around `CImage` | Native composition |
| Image preview, zoom, crop, transform, or gallery | dedicated viewer/editor/gallery family | Separate component |
| CDN transforms, proxying, signing, optimization, or upload | application or delivery infrastructure | Outside Citry UI |

There is no headless Image API. Raw `<img>` and `<picture>` already are the
headless platform surface.

Non-goals are a client image proxy, format transcoder, resize service, URL
builder, preload engine, intersection-observer loader, low-resolution prefetch,
decode gate, preview modal, zoom or rotate UI, animation controller, background
image, caption owner, or `prefers-reduced-data` polyfill. `CImage` does not
promise that an origin, CSP, browser cache, service worker, or printer will
fetch or render a resource.

## 2. Prior art and complaints

### Current-source record

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| HTML Living Standard | Living Standard, last updated 2026-08-11 | [Embedded content](https://html.spec.whatwg.org/multipage/embedded-content.html) | Native `picture` ordering, source selection, `alt`, dimensions, `complete`, `currentSrc`, and `decode()` remain authoritative. |
| W3C WAI Images Tutorial | Updated 2024-05-13 | [Alt decision tree](https://www.w3.org/WAI/tutorials/images/decision-tree/) | Require an explicit `alt`; empty text is the intentional decorative case. |
| CSP Level 3 | Working Draft 2026-05-05 | [CSP](https://www.w3.org/TR/CSP/) | `img-src` and the browser fetch pipeline remain authoritative; no bypass or proxy. |
| web.dev | Reviewed 2026-08-12 | [Responsive images](https://web.dev/learn/design/responsive-images), [browser lazy loading](https://web.dev/articles/browser-level-image-lazy-loading), [LCP images](https://web.dev/articles/optimize-lcp#optimize_when_the_resource_is_discovered), [responsive preload](https://web.dev/articles/preload-responsive-images) | Emit discoverable native URLs in server HTML; do not lazy-load likely LCP images or add a component preload engine. |
| Citry `CAvatar` | Repository snapshot 2026-08-12 | `cavatar.py`, server tests, three-engine E2E | Reuse cached-complete settlement and owner-token cleanup concepts, but not Avatar's root `role=img`, empty inner `alt`, or src-only generation. |
| Citry Card and Skeleton | Repository snapshot 2026-08-12 | `ccard.py`, `cskeleton.py`, designs and tests | Image semantics stay with Image; Card media and Skeleton remain composition surfaces. |
| Vuetify `VImg` | 4.1.8 | [Image docs](https://dev.vuetifyjs.com/en/components/images/), [VImg source](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VImg/VImg.tsx), [VResponsive source](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VResponsive/VResponsive.tsx), [polling cleanup issue #23011](https://github.com/vuetifyjs/vuetify/issues/23011) (affected 3.11.4/4.1.5, closed for 3.12.x), [breakpoint source request #20804](https://github.com/vuetifyjs/vuetify/issues/20804) (closed not planned) | Adopt source ordering, fit, placeholder, error, and settlement; reject IO loading, low-res preloader, polling, transition, gradient, and breakpoint-specific prop syntax. |
| Chakra UI Image | `@chakra-ui/react` 3.36.1 | [Image docs](https://chakra-ui.com/docs/components/image), [source](https://github.com/chakra-ui/chakra-ui/blob/%40chakra-ui%2Freact%403.36.1/packages/react/src/components/image/image.tsx), [v3 migration](https://chakra-ui.com/docs/get-started/migration) | Native `img` props and CSS fit are sufficient for most jobs; Chakra's removal of fallback machinery argues for a small wrapper. |
| Ark UI Avatar | `@ark-ui/react` 5.38.1 | [Avatar docs](https://ark-ui.com/docs/components/avatar) | Status callback and visual fallback are useful lifecycle evidence, but identity-specific compound anatomy does not generalize to Image. |
| Mantine Image | `@mantine/core` 9.5.1 | [Image docs](https://mantine.dev/core/image/), [source](https://github.com/mantinedev/mantine/blob/9.5.1/packages/%40mantine/core/src/components/Image/Image.tsx) | Adopt minimal fit and fallback composition; reject fallback URL swapping because it obscures the authored request and alt failure. |
| Base UI | 1.7.0 | [Component catalog](https://base-ui.com/react/overview/about) | No general Image component. This is evidence that native markup is the baseline and Citry must keep its added contract narrow. |
| shadcn/ui | Reviewed 2026-08-12 | [Aspect Ratio](https://ui.shadcn.com/docs/components/radix/aspect-ratio), [Card image composition](https://ui.shadcn.com/docs/components/radix/card#image) | Adopt composition with layout/card primitives; do not make Image own captions or card structure. |
| Web Awesome | 3.11.0 | [Component catalog](https://webawesome.com/docs/components/), [Animated Image](https://webawesome.com/docs/components/animated-image/) | General Image remains native; animated playback/canvas/CORS behavior belongs to a specialist component. |
| PrimeVue Image | 5.0.0 | [Image docs](https://primevue.dev/image/), [touch preview issue #7969](https://github.com/primefaces/primevue/issues/7969) (open when repository archived 2026-06-28), [preview cleanup issue #4710](https://github.com/primefaces/primevue/issues/4710) (3.38.1, closed cannot-replicate) | Native image forwarding is relevant; preview, zoom, rotate, focus trapping, and overlay cleanup are a separate family. |

The local complaint register flags hidden layout assumptions, wrappers that
change native semantics, duplicated state owners, broad prop forwarding,
unbounded async work, stale callbacks, payload growth, and examples that work
only in one renderer. Image addresses those complaints by preserving the
native `img`, requiring geometry, snapshotting all record inputs, binding every
settlement to a generation and selected URL, and proving template plus direct
Python composition.

### Vuetify disposition

Vuetify is the primary styled-suite comparison. The full `VImg` public job is
disposed as follows:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `src` string or object | Direct API | `src`, `srcset`, `sizes`, `sources` | Split native concerns explicitly; no magic object union. |
| `alt` | Direct API | required `alt` | Adopt and require explicit intent. |
| `width`, `height`, dimensions | Direct API plus CSS | required native `width`, `height`; root class/style/attrs | Adopt intrinsic dimensions; ordinary CSS owns rendered size. |
| `aspectRatio` / responsive ratio | Native dimensions plus CSS | native width/height; `--cui-image-aspect-ratio` | Adopt without a duplicate geometry state owner. |
| `cover` | Direct API | `fit="cover"`; default `contain` | Adopt capability, choose noncropping default. |
| `position` | Direct API | `position` | Adopt as validated plain CSS object-position text. |
| `absolute` | CSS/composition | root class/style in a positioned owner | Omit layout-position prop. |
| `draggable` | Direct native API | `draggable` | Adopt with a strict boolean. |
| `rounded`, `color`, dimensions, inline | CSS or utility classes | root `class_`, `style`, public variables | Omit prop aliases. |
| `imageClass` | Root part selector or `img_attrs` | `[data-citry-ui-part="image"]`, `img_attrs` | Adopt stable destination without a dedicated prop. |
| `gradient` | Composition/CSS | consumer pseudo-element or Card media composition | Omit; not an image request job. |
| `eager` | Native attribute | `loading="eager" | "lazy"` | Use native vocabulary and default eager. |
| intersection-observer options | Native HTML | native `loading` | Reject private loader and observer. |
| `lazySrc` and low-res preloader | Composition/application delivery | `placeholder` slot or service-generated `srcset` | Reject second request engine. |
| `crossorigin`, `referrerpolicy` | Direct native API | `cross_origin`, `referrer_policy` | Adopt with native enumerations. |
| `srcset`, `sizes` | Direct native API | `srcset`, `sizes` | Adopt. |
| `sources` slot | Structured record API | `sources: Sequence[CImageSource]` | Adopt native order but validate server-side; no arbitrary raw source slot. |
| default content slot | Composition around Image | parent layout/Card | Reject overlay content ownership. |
| `placeholder` slot | Named slot | `placeholder` | Adopt as visual, hidden from accessibility tree. |
| `error` slot | Named slot | `fallback` | Adopt under native semantic image; do not replace alt semantics. |
| `loadstart` event | Component callback | first `loading` status notification | Adopt through `onStatusChange`, not a synthetic native event. |
| `load` / `error` events | Native listeners plus callback | `img_attrs`, `onStatusChange` | Preserve native events and add normalized owner callback. |
| pre-intersection `idle` state | Native HTML | none; server image is always discoverable | Reject component-owned idle state. |
| transition | CSS/composition | none in Image | Reject; lifecycle must not depend on leave animation. |
| natural dimensions/current source refs | Callback detail and native ref | `CImageStatusChangeDetail`; ordinary DOM ref | Adopt observable detail; no public imperative controller. |
| loading/loaded/error state | Internal state and public mirror | `data-status`, callback detail | Adopt. |
| automatic natural-size polling | Native events/complete settlement | no API | Reject; issue #23011 demonstrates cleanup risk. |
| breakpoint-specific sources | Native responsive metadata | `sources`, `srcset`, `sizes` | Reject prop breakpoint DSL; native media/source selection is richer. |

Citry adopts native semantics, ordered responsive metadata, stable geometry,
fit, visual settlement, and callbacks. It rejects competing fetch, decode,
preload, transition, breakpoint, preview, and processing engines.

### Browser probes and implications

The frozen probe matrix established:

- an `<img>` with no `src` is `complete === true` and `naturalWidth === 0` in
  all three engines, so `complete` alone cannot mean loaded;
- width and height `320` by `180` reserve the same geometry before and after
  load in all three engines;
- a matching `<source width="400" height="100">` supplies the selected image's
  `auto 400 / 100` preferred ratio before/after load in all three engines,
  producing a 200 by 50 rendered image despite the fallback image's 200 by 200
  dimensions;
- a `<picture>` media change can change `currentSrc` and emit a second trusted
  `load` while `img.getAttribute("src")` stays unchanged in all three engines;
- rapid slow-to-fast source replacement settled only the surviving fast
  request in the tested engines, but the component still must guard stale
  events because browser request timing is not an ownership token; and
- a valid zero-dimension SVG fires `load`, resolves `decode()`, and still has
  `naturalWidth === 0` in all three engines, so zero natural width cannot by
  itself classify a cached complete request as broken; and
- `decode()` rejects with `EncodingError` after source supersession in all
  three engines, so an ambiguous cached probe must bind decode settlement to
  the current owner and generation rather than treating rejection as the new
  request's error.

## 3. Public composition and anatomy

The smallest template form is:

```html
<c-CImage
  src="/images/orion-nebula.jpg"
  alt="The Orion Nebula glowing pink and blue"
  width="1280"
  height="720"
/>
```

The Python equivalent is:

```python
CImage(
    src="/images/orion-nebula.jpg",
    alt="The Orion Nebula glowing pink and blue",
    width=1280,
    height=720,
)
```

Responsive Python composition uses records:

```python
CImage(
    src="/images/observatory-960.jpg",
    alt="Snow-covered observatory below the Milky Way",
    width=960,
    height=640,
    srcset="/images/observatory-480.jpg 480w, /images/observatory-960.jpg 960w",
    sizes="(max-width: 48rem) 100vw, 48rem",
    sources=(
        CImageSource(
            media="(min-width: 64rem)",
            srcset="/images/observatory-wide-1600.jpg 1600w",
            sizes="100vw",
            width=1600,
            height=700,
        ),
        CImageSource(type="image/avif", srcset="/images/observatory.avif"),
    ),
)
```

`CImageSource` is a frozen public data record, not a component. One `CImage`
is sufficient because each source is void browser-selection metadata: it has
no state, semantics, slot, callback, styling root, or standalone validity.
Declaration children would add compound registration, direct-child validation,
and public component identity without enabling a user job. The record sequence
also snapshots mutable Python input and renders identically from template-fed
server data and direct Python composition.

The stable anatomy is:

```text
span [part=image-root] [data-status]
├─ picture [part=picture]                 only when sources is nonempty
│  ├─ source                              one per CImageSource, ordered
│  └─ img [part=image]                    sole semantic/request owner
│
├─ img [part=image]                       instead when sources is empty
├─ span [part=placeholder] aria-hidden    when slot supplied
└─ span [part=fallback] aria-hidden       when slot supplied
```

| Component or record | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CImage` | styled neutral `<span>` | `class_`, `style`, `attrs` land on root; `img_attrs` land on native `<img>` | exactly one native `<img>`; optional `<picture>` owns ordered sources and the image |
| `CImageSource` | none; emits one `<source>` | record fields only | only through `CImage.sources`, before the native `<img>` |

The root is not a figure, link, button, or ARIA image. Consumers wrap it in
those native or Citry structures. The native `<img>` owns `src`, `srcset`,
`sizes`, `alt`, dimensions, loading and fetch hints, cross-origin and referrer
policy, draggable, and current request. Consumers cannot replace owned
attributes through `attrs` or `img_attrs`.

The wrapper is required because visual placeholders and error content must
share stable geometry without moving native semantics to a changing node. The
exact presence of `<picture>` is contractual only when `sources` is nonempty.
No other wrapper is public.

## 4. Server inputs and client inputs

Public aliases:

```python
CImageFit = Literal["contain", "cover", "fill", "none", "scale-down"]
CImageLoading = Literal["eager", "lazy"]
CImageDecoding = Literal["auto", "sync", "async"]
CImageFetchPriority = Literal["auto", "high", "low"]
CImageCrossOrigin = Literal["anonymous", "use-credentials"]
CImageReferrerPolicy = Literal[
    "no-referrer",
    "no-referrer-when-downgrade",
    "origin",
    "origin-when-cross-origin",
    "same-origin",
    "strict-origin",
    "strict-origin-when-cross-origin",
    "unsafe-url",
]
CImageStatus = Literal["loading", "loaded", "error"]
```

Public records:

```python
@dataclass(frozen=True, slots=True)
class CImageSource:
    srcset: str
    media: str | None = None
    type: str | None = None
    sizes: str | None = None
    width: int | None = None
    height: int | None = None

@dataclass(frozen=True, slots=True)
class CImageStatusChangeDetail:
    status: CImageStatus
    src: str
    current_src: str
    natural_width: int
    natural_height: int
```

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `src` | `str` | required | reactive configuration | Nonempty, no U+0000 or ASCII control; native fallback URL. |
| `alt` | `str` | required | reactive configuration | Plain string, may be exactly empty for decorative use; always emitted. |
| `width` | positive `int` | required | reactive configuration | Native intrinsic width; bool rejected. |
| `height` | positive `int` | required | reactive configuration | Native intrinsic height; bool rejected. |
| `srcset` | `str | None` | `None` | reactive configuration | Plain nonempty responsive candidate string when supplied. Browser parses candidates. |
| `sizes` | `str | None` | `None` | reactive configuration | Plain nonempty sizes string; width-descriptor `srcset` always requires it; `auto`/`auto, ...` is accepted only with native lazy loading. |
| `sources` | `Sequence[CImageSource]` | `()` | structural server data | Snapshotted once per render, ordered, every member and paired dimensions validated; nonempty emits `<picture>`. |
| `loading` | `CImageLoading` | `"eager"` | reactive configuration | Native loading hint. |
| `decoding` | `CImageDecoding` | `"auto"` | reactive configuration | Native decoding hint. It is independent of the one ambiguous cached-complete `decode()` probe. |
| `fetch_priority` | `CImageFetchPriority` | `"auto"` | reactive configuration | Emits `fetchpriority`; application owns scarcity policy. |
| `cross_origin` | `CImageCrossOrigin | None` | `None` | reactive configuration | Emits native `crossorigin`. |
| `referrer_policy` | `CImageReferrerPolicy | None` | `None` | reactive configuration | Valid native token; emits `referrerpolicy`. |
| `fit` | `CImageFit` | `"contain"` | reactive configuration | Sets effective object fit and root mirror. |
| `position` | `str` | `"50% 50%"` | reactive configuration | Plain nonempty CSS object-position text; browser validates CSS grammar. |
| `draggable` | `bool` | `False` | reactive configuration | Exact native draggable reflection. |
| `onStatusChange` | browser callback or `None` | `None` | reactive configuration | Owner-local normalized settlement callback. |
| `class_` | `CClassValue | None` | `None` | structural server data | Merged on root. |
| `style` | `CStyleValue | None` | `None` | structural server data | Merged on root. |
| `attrs` | `Mapping[str, object] | None` | `None` | structural server data | Safe root attrs/listeners; owned/reserved names rejected. |
| `img_attrs` | `Mapping[str, object] | None` | `None` | structural server data | Safe native image attrs/listeners such as `title` and `aria-describedby`; resource, image-map, and semantic owners rejected. |

`sources` records do not expose arbitrary attrs. The native source vocabulary is
small and each field affects native selection or selected-image geometry.
`width` and `height` on a
source are either both omitted or both positive. Duplicate records are allowed
because native first-match order can be intentional; order is never sorted.

Validation enforces the structural conditions needed for conforming picture
content, not merely individually nonempty records:

- each source `srcset` using a width descriptor requires that same record's
  nonempty `sizes`;
- source `sizes` without `srcset` is rejected;
- when a source has a following source or a following image with `srcset`, that
  source must carry `type` or a nontrivial `media` discriminator; stripped,
  case-insensitive `media="all"` does not satisfy that requirement by itself;
- `type` is restricted in v1 to an ASCII `image/` MIME essence with valid token
  characters and no parameters, whitespace, or controls;
- `media` is a copied plain nonempty native media-query string with no controls.
  Citry does not ship a CSS media-query parser, so the caller owns its grammar
  and resulting HTML conformance. Public examples and every library-authored
  media string pass the WHATWG HTML validator;
- the final image's width-descriptor `srcset` always requires a present
  nonempty image `sizes`; and
- image `sizes` beginning with native `auto` is accepted only when the image
  has `loading="lazy"`; source `sizes` beginning with `auto` additionally
  requires the following final image's own `sizes` to begin with `auto`, so the
  image actually allows auto-sizes.

HTML validation is a release gate for zero, one, and many library-authored
source arrangements. The guide states that arbitrary consumer `media` strings
are native syntax and must be validated by the application.

Client `$c-props` accepts `src`, `alt`, `width`, `height`, `srcset`, `sizes`,
`loading`, `decoding`, `fetchPriority`, `crossOrigin`, `referrerPolicy`, `fit`,
`position`, `draggable`, and `onStatusChange`. `sources` is structural and
changes only by server render/morph. Inputs are reactive, but only the exact
request/selection fields listed in section 5 begin a new generation.

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| required resource/semantic inputs | matching server type | server value | server value | diagnose once, retain last valid | native image and request fingerprint |
| optional strings/enums | matching server type | server value | clear to native omission/server default as applicable | diagnose once, retain last valid | native image and root mirrors |
| `draggable` | boolean | server value | server value | diagnose once, retain last valid | native image |
| `onStatusChange` | callback | server callback | clear callback | ignore and diagnose by type only | notifications only |

On first initialization, server values are the baseline and valid client props
override them. Later removal returns that input to its immutable server
baseline. No DOM reflection is a writable input. Nested Images resolve their
own props and owner tokens.

## 5. State model

Public status is exactly `loading`, `loaded`, or `error`. The visual fallback
is not a fourth semantic state: a supplied fallback is displayed during
`error`, while the native `<img>` remains in the document and accessibility
tree. Before JavaScript, no public status is asserted by script and the server
image is visible.

| Current | Trigger and guard | Next | Native/visual effect | Callback |
|---|---|---|---|---|
| initial | client takes ownership of valid anatomy and request/selection fingerprint | `loading` | attach listeners before reconciliation; show placeholder if supplied | one `loading` notice after ownership |
| `loading` | same-generation trusted `load`, or cached `complete && naturalWidth > 0`, with nonempty same-generation `currentSrc` | `loaded` | show native pixels; hide visual slots | `loaded` detail |
| `loading` | cached `complete && currentSrc && naturalWidth == 0` | `loading` | start one generation-bound `decode()` probe because valid 0x0 content and broken content are ambiguous | none yet |
| `loading` | same-generation ambiguous probe resolves | `loaded` | accept even when natural dimensions remain zero | `loaded` detail |
| `loading` | same-generation trusted `error`, or same-generation ambiguous probe rejects while the same request remains complete/current | `error` | show fallback if supplied, otherwise native broken-image rendering | `error` detail |
| `loaded` | browser selects and loads a different `currentSrc` without authored input change | `loaded` | retain pixels; update current source/dimensions | notify because selected resource changed |
| `loaded` | environment-selected candidate emits same-generation trusted `error` | `error` | preserve native broken rendering or show visual fallback; no invented loading phase | `error` detail with current native snapshot |
| `error` | environment-selected candidate emits same-generation trusted `load` | `loaded` | show newly selected native pixels | `loaded` detail with current native snapshot |
| `error` | another environment-selected candidate emits trusted `error` with a changed `currentSrc` | `error` | retain fallback/native error | one error detail for the changed candidate |
| `loaded` or `error` | accepted request/selection fingerprint changes | `loading` | increment generation; keep native server discoverability; show placeholder if supplied | `loading` detail |
| any | only alt, base height, loading, decoding, fetch priority, fit, position, draggable, callback, or allowed attrs change | unchanged | repair native/layout/configuration surface; do not fabricate request status | none |
| any | stale event or queued settle from older generation | unchanged | no effect | none |
| any | invalid anatomy, hostile owned mutation, or runtime capability loss | server fallback / unready | detach owned behavior; do not intercept native image | none after teardown |
| any | cleanup/removal | none | remove listeners/tasks/owner token and readiness | none |

The request/selection fingerprint contains `src`, `srcset`, `sizes`, base
`width`, the full ordered source snapshot including every source dimension,
`cross_origin`, and `referrer_policy`. Source width/height are included because
the standard treats their mutation as relevant, and they can affect selected
geometry and auto-sizes behavior.
Those are the authored fields that can replace or select a request. Base
`height`, `alt`, `loading`, `decoding`, `fetch_priority`, fit, position,
draggable, and
callback are layout, semantic, or policy surfaces and repair without a
synthetic generation. Changing loading can let the browser start a deferred
request, but the existing loading episode continues until a real native
settlement. Any native candidate load/error still reconciles the current
request even when caused by a policy or environmental change.

Every event is checked against the current element object, owner token,
generation, and observed `currentSrc`. A responsive candidate switch is a real
settlement even when `src` is unchanged. Repeated load for the same generation,
same current URL, and same natural dimensions is idempotent. Native `error`
after a newer candidate has settled cannot overwrite it.

A user agent can update `currentSrc` for an environment-selected candidate yet
emit no matching `load` or `error`. In that case Image retains its last accepted
status and rendered-pixel interpretation until a trusted native settlement or a
later owned configuration/morph cached preflight. It does not infer failure from
`complete && naturalWidth == 0` outside that guarded preflight, install media,
DPR, or resize observers, or fabricate a callback for a silent browser
transition. A native Chromium 151 probe selecting a malformed picture source
on a viewport change exhibited this silent behavior; Firefox 153 and WebKit
26.5 emitted the trusted error for the same arrangement.

`complete === true` is never sufficient for loaded. Positive natural dimensions
prove cached success, but zero is ambiguous because a valid 0x0 SVG can load.
Only that complete/current/zero-width cached case calls `img.decode()`. Its
resolve proves success; its rejection proves error only if the same owner,
element, generation, `currentSrc`, and complete request still apply. Source
supersession or cleanup makes the result inert. An empty or missing request is
invalid at the server API; if hostile client mutation creates it, the runtime
fails closed rather than calling it an image error.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CImage` | `placeholder` | no | zero or one | none | no custom placeholder; native image remains visible while loading |
| `CImage` | `fallback` | no | zero or one | none | native broken-image rendering and `alt` text |

Both slots are server-rendered static visual content. Their wrappers are
`aria-hidden="true"` and `inert`, cannot contain the native semantic image,
and never replace or rename it. The placeholder is visible only while a ready
component is `loading`. The fallback is visible only while a ready component
is `error`. When a slot is visible, CSS makes the image pixels transparent but
does not apply `hidden`, `display:none`, `visibility:hidden`, or
`aria-hidden`; the native `alt` remains the accessibility fallback.

If a placeholder exists, old or incomplete pixels are not shown during a new
generation. If no placeholder exists, Image does not hide native pending
rendering. If a fallback exists, broken native pixels are visually suppressed.
If none exists, the user agent's broken-image rendering remains visible.

Slot wrappers render with `hidden` in server output. Component CSS changes
their visibility only after the root has a live readiness marker. With
JavaScript disabled, the native image and native `alt` fallback remain useful,
and neither custom slot can obscure them.

The slots intentionally have no status data because Citry slot content is
rendered on the server and the wrappers already provide the state boundary.
Applications needing a meaningful failure message or retry control place it
outside `CImage`, update it from `onStatusChange`, and own its live-region or
button semantics. Interactive slot descendants are rejected server-side where
detectable and fail settled client anatomy because inert visual content is not
an interaction surface.

There is no raw sources slot, image replacement slot, dynamic slot namespace,
caption slot, or content overlay slot.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onStatusChange` | `CImageStatusChangeDetail` | initial ownership, accepted request-generation start, same-generation success/error, or selected `currentSrc` change | after native attrs and public mirrors are synchronized; never during server rendering | notification only; callback cannot veto browser loading | not cancelable; newer generation cancels stale queued notice |

The first ready initialization queues `loading`, then reconciles cached
completion. A cached image may therefore notify `loading` followed by `loaded`
or `error` in ordered tasks. This gives every ready component the same public
sequence whether the response was cached or arrived after listener attachment.

The detail reports normalized values, not the native event. `current_src` is a
snapshot of the browser-selected absolute URL and can differ from `src`. It is
intended for application telemetry and state, so applications must treat it as
potentially sensitive. Library diagnostics never print it or an authored
resource string.

During a new loading episode the browser can retain the previous current
request and pixels while a pending request loads. The loading detail therefore
reports that live previous `currentSrc` and positive natural dimensions when
present; it does not claim they belong to the new authored source set. Natural
dimensions can also be zero in any status, including valid loaded 0x0 content.
The private generation is deliberately absent from public detail because it is
an ownership mechanism, not application identity. Applications needing to
distinguish two source sets with the same base and selected URL keep an
owner-side key alongside the callback.

Native `load` and `error` listeners belong in `img_attrs` using Alpine
`@load`/`@error`. These native events do not bubble, so placing a listener in
root `attrs` does not observe them. Listeners execute on the real native image
in the isolated component expression scope. `$event`, `$store`, `$dispatch`,
and explicit globals work; ancestor component-local identifiers are not
captured across that isolated root. `onStatusChange` is the supported
owner-local callback surface. Raw HTML `onload`/`onerror` attributes are
rejected.

Native listeners observe only events that occur after they are attached. The
component callback additionally reconciles the cached `complete` race. The
component does not redispatch or synthesize native load/error events.

There are no public methods. Native DOM refs provide `currentSrc`,
`naturalWidth`, `naturalHeight`, `complete`, and `decode()` when an application
explicitly needs them. Citry exposes no decode-complete callback and never
turns a superseded decode rejection into the current request's error. Its only
internal decode use disambiguates a cached complete zero-width request.

## 8. Semantics, keyboard, focus, and assistive technology

The only image semantic is the native `<img alt>`. The root is a neutral
`<span>` with no role, name, description, live region, focusability, or ARIA
state. `<picture>` is a source-selection context and contributes no separate
semantics. Visual slot wrappers are inert and hidden from assistive technology.

`alt` is required as an explicit string:

- `alt=""` means decorative or redundant according to the HTML and WAI model;
- nonempty `alt` is a concise contextual equivalent;
- an image that is the only content of a link or button uses `alt` to describe
  the destination or action;
- a complex chart needs its equivalent data or explanation elsewhere in the
  document; and
- a nearby caption is not automatically an alternative. Use native `<figure>`
  and `<figcaption>` for a caption and still choose `alt` intentionally.

Image never copies `alt` to `aria-label`, the wrapper, placeholder, or fallback.
It never assigns `role="img"` to the root, avoiding the duplicate image model
used by Avatar for its different identity job.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| Informative image | browse/virtual cursor | native image announced using nonempty `alt` | unchanged | no |
| Decorative image | browse/virtual cursor | empty-alt image omitted according to user agent/AT | unchanged | no |
| Image-only link/button | Tab then activation | surrounding native control is named by image `alt` | native control focus/activation | native control owns |
| Pointer/touch on ordinary image | click, drag, context menu | native browser behavior including image context menu | unchanged | no |
| `draggable=False` | drag gesture | native image drag disabled | unchanged | no component prevention |
| Broken image with custom visual fallback | browse/virtual cursor | native `alt` remains the semantic fallback; visual slot is not announced | unchanged | no |

Image adds no keyboard bindings, roving focus, focus entry, focus restoration,
selection behavior, or gesture ownership. Forward and reverse Tab skip an
ordinary Image. A focusable ancestor owns its native tab order. Image does not
hide browser context menus, copying, saving, or dragging
beyond the explicit native `draggable` value.

Screen-reader acceptance covers informative, decorative, functional, broken,
placeholder, and fallback examples in NVDA/Firefox, JAWS/Chromium, and
VoiceOver/WebKit. Automated axe checks supplement but do not replace that
review.

## 9. Native forms and validation

`CImage` is not a form-associated component. It has no name, value, disabled,
readonly, required, validity, reset, submission, autocomplete, or form-owner
contract. It never emits hidden inputs.

An image can be composed inside a native link or Button. `usemap` and `ismap`
are rejected in v1: they introduce external map identity, focus/activation
relationships, responsive coordinate semantics, and an ancestor-link validity
rule that opaque attrs cannot validate. Applications needing an image map or
`<input type="image">` use native markup directly and own its areas, name,
coordinates, validation, submitter, fallback, and responsive behavior.

Citry Events can replace an Image as ordinary server output. Pending browser
fetches are not Citry form requests, and transport failure is reported only as
image `error` settlement. Form retry/cancellation semantics do not apply.

## 10. Styling and theme contract

The root participates in `citry-ui.theme` with low-specificity defaults. It is
a positioned inline-block whose normal-flow native image sizes the root. The
image's fallback width/height or the matching source width/height supplies its
preferred ratio before bytes load. The image has `max-inline-size:100%` and
`block-size:auto`, so constraining a 1280 by 720 source to 200 CSS pixels yields
a 200 by 112.5 box instead of a distorted 200 by 720 box. The root does not
copy that ratio into competing JavaScript state.
Consumers can override rendered width, block size, or ratio through normal
root/image class/style without changing native intrinsic metadata.

The native image is a normal-flow block. Placeholder and fallback wrappers are
absolutely positioned at logical inset zero, so their copy never changes image
geometry. The image uses effective object fit and position within its native
concrete object size. `--cui-image-aspect-ratio` is read by the replaced image's
`aspect-ratio` property, not only by the wrapper; an explicit `1 / 1` therefore
makes the constrained example 200 by 200 and object fit controls its pixels.
Fit is visibly relevant when authored dimensions or consumer CSS make the box
ratio differ from the selected resource. `<picture>`
uses `display:contents` so it adds no competing layout box. The root uses
logical sizing, does not create a stacking context, and clips only the visual
media box required for border radius and crop.

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-image-aspect-ratio` | positive CSS ratio or `auto` | Overrides rendered box ratio without changing native dimension metadata | `auto`, using the selected native image/source dimensions |
| `--cui-image-fit` | CSS `object-fit` value | Overrides the `fit` input's visual fallback | effective `fit` input, initially `contain` |
| `--cui-image-position` | CSS `object-position` value | Overrides the `position` input's visual fallback | effective `position`, initially `50% 50%` |
| `--cui-image-radius` | CSS length/percentage | Media box corner radius | `var(--cui-radius-md)` |
| `--cui-image-background` | CSS color/image | Loading/native contain-area background | `transparent` |
| `--cui-image-fallback-color` | CSS color | Visual fallback foreground | `var(--cui-color-muted-fg)` |
| `--cui-image-fallback-background` | CSS color/image | Visual fallback background | `var(--cui-color-muted-bg)` |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="image-root"]` | styled neutral root and reserved geometry | every Image | owns all other documented parts |
| `[data-citry-ui-part="picture"]` | native responsive-selection context | only with nonempty sources | direct root child; directly owns sources then image |
| `[data-citry-ui-part="image"]` | sole native semantic/request `<img>` | every Image | direct root child without sources, otherwise direct picture child |
| `[data-citry-ui-part="placeholder"]` | inert loading visual | only with slot | direct root child |
| `[data-citry-ui-part="fallback"]` | inert error visual | only with slot | direct root child |

| Public reflected attribute | Values | Meaning |
|---|---|---|
| `data-status` | `loading`, `loaded`, `error` | current normalized settlement; reliable after readiness |
| `data-fit` | `contain`, `cover`, `fill`, `none`, `scale-down` | effective configured fit before public CSS-variable override |
| `data-has-placeholder` | present/absent | placeholder slot exists |
| `data-has-fallback` | present/absent | fallback slot exists |
| `data-citry-image-initialized` | present/absent | a live owner controls runtime settlement |

Root `class_` and `style` accept structured values and merge with safe values
in `attrs`. `img_attrs` can apply a class/style to the native image. Consumer
unlayered rules override theme defaults regardless of load order; named layers
must be ordered after `citry-ui.theme`. Public variables inherit from ancestors
or the root and beat component fallback values. Tests assert computed results,
not only attribute presence.

## 11. Environmental behavior

- **Light, dark, and nested schemes:** image pixels and native selection do not
  change. Loading/background and fallback colors resolve through the nearest
  color-scheme scope. Art-direction changes use authored native media, not
  theme detection in JavaScript.
- **RTL:** source order, intrinsic geometry, and default centered object
  position are unchanged. CSS sizing is logical. An explicitly authored
  physical `left` or `right` object position remains physical; Image does not
  rewrite CSS text.
- **Reduced motion:** Image defines no transition, fade, shimmer, or movement.
  An animated resource remains a native image behavior. Applications needing
  user-controlled animated playback use a specialist animated-image family.
- **Reduced data:** Image does not inspect the experimental
  `prefers-reduced-data` query or replace sources after load. Applications may
  choose a smaller server source set or let the browser choose from `srcset`.
- **Forced colors:** image pixels remain browser-managed. Image adds no filter
  or forced-color override. Placeholder/fallback foreground, background, and
  any focus-free boundary use system `CanvasText`, `Canvas`, and
  `GrayText` fallbacks in forced colors.
- **Zoom and text spacing:** at 200% and 400% zoom, the root stays within its
  container and maintains its ratio unless consumer CSS changes it. Placeholder
  or fallback content wraps without changing intrinsic semantics. Alternative
  text is not rendered by the component and follows native broken-image/AT
  behavior.
- **Narrow and wide viewports:** the browser may reevaluate `media`, `srcset`,
  and `sizes`. A resulting `currentSrc` settlement is generation-owned and can
  notify without an authored `src` change. Tests use a deterministic picture
  media-query switch for live mutation; they do not promise that every engine
  will dynamically upgrade a plain `srcset` candidate on the same schedule.
  Image runs no resize handler.
- **DPR changes:** native candidate reevaluation is handled like a viewport
  candidate change. Automation covers a browser-context DPR restart and manual
  review covers live display movement where the platform supports it.
- **Coarse pointer and touch:** native context menu, drag, save, and selection
  behavior remains the platform result. Image installs no gesture listener.
- **Virtual keyboard:** not applicable because Image creates no focusable or
  editable UI.
- **Print:** component print CSS always suppresses the placeholder. A loaded
  native image prints normally. An error fallback that was already settled may
  print visually while the native `alt` remains semantic. During unresolved
  loading, print CSS reveals the native image rather than a JS placeholder, but
  does not promise that a lazy resource will be fetched before pagination.
  Important printable images use `loading="eager"`.

The component authors no visible string. Slot copy, alternative text, and any
external failure message belong to the application and its locale.

## 12. Overlay and layering behavior

Image never creates or controls an overlay, Popover, portal, top-layer node,
focus trap, backdrop, scroll lock, or stacking coordinator entry. It adds no
z-index. A picture viewer, lightbox, cropper, image editor, tooltip, context
menu, or Dialog composed around Image owns its own anchor, dismissal, focus,
modal, and cleanup contract.

The root does not intercept outside interaction or Escape. Image inside an
overlay remains ordinary content and follows that overlay's color scheme and
removal lifecycle. Placeholder/fallback layers are local positioned visuals
with no contractual stacking precedence relative to a consumer-authored
interactive overlay.

## 13. Collections, async data, and identity

`sources` is a finite ordered metadata sequence, not an interactive
collection. It is snapshotted exactly once per server render, rejects strings,
generators, mappings, mutable record impersonators, and non-`CImageSource`
members, and is limited to 32 records to bound rendered anatomy and
fingerprints. Native first-match order is identity; Image never sorts,
deduplicates, merges, or invents keys. Reordering otherwise equal sources is a
request/selection-fingerprint change.

The browser owns network scheduling, cache reuse, candidate choice, decode,
redirects, CORS, CSP, service workers, offline behavior, and cancellation of
obsolete requests. Citry owns only notification identity:

- each accepted authored request/selection-fingerprint change begins one generation;
- every queued reconcile and callback carries that generation and owner token;
- the current element and `currentSrc` are re-read at settlement;
- a newer generation makes older work inert;
- cleanup invalidates all pending work; and
- a candidate change within one authored generation can notify another loaded
  result without fabricating a new authored generation.

Setting a new native source lets the browser supersede the old request. Image
does not create an `AbortController` because native image fetching exposes no
matching abort contract. It does not retry automatically. An application
retries by supplying a new `src`, `srcset`, source record, or cache-busting URL
and owns retry policy and copy.

Reactive native writes apply request hints and dimensions first, responsive
metadata next, and `src` last. Only the request/selection fields begin a
generation; applying a non-request hint does not. A server morph renders native
`<source>` nodes before `<img>`. Browsers may still react to individual DOM
mutations or preload-scanner discoveries, so Image guarantees callback
supersession, not one physical request or zero speculative bytes.

An offline/cache failure is ordinary `error`. Restoration requires a new
browser request trigger; going online alone is not a component state
transition. Multiple Images loading the same URL remain independent semantic
and callback owners even when the browser shares response bytes.

## 14. Server render, morph, and cleanup

Server output contains the actual `src`, optional responsive metadata, fetch
hints, required `alt`, and required dimensions. It never hides the native
image, rewrites URLs into `data-src`, or depends on JavaScript for discovery.
Placeholder and fallback wrappers are present only when supplied and carry
`hidden`, `aria-hidden`, and `inert` in server HTML. This is the useful
no-JavaScript contract.

Client initialization follows this order:

1. validate the exact root, direct optional picture, ordered source count and
   attributes, sole native image, and visual-slot identities;
2. acquire a root-object owner token and shared mutation-scope registration;
3. attach image `load` and `error` listeners before changing any reactive
   attribute;
4. resolve client props and atomically record the request/selection fingerprint;
5. publish readiness and `loading`; then
6. queue one cached-completion reconcile using `complete`, `naturalWidth`, and
   the generation's `currentSrc`; only an ambiguous complete/current/zero-width
   request starts a generation-bound decode probe.

The exact root object plus a live controller registry is ownership. The
copyable readiness attribute alone is never authority. A detached or inserted
clone cannot inherit callbacks or initialized status; lifecycle observation
scrubs copied readiness on an unowned root. Nested fallback content bearing
forged part names cannot satisfy direct-owned anatomy.

For a correlated server morph:

- retaining the exact root, picture/image objects, ordered source objects,
  actual Document or open ShadowRoot, and equal request/selection fingerprint preserves
  generation, status, selected URL, natural dimensions, and listener counts;
- changing `alt`, base height, loading, decoding, fetch priority, fit,
  position, draggable, callback, or allowed attrs repairs
  those surfaces without resetting an equal request;
- changing any request/selection-fingerprint field or source order begins one new
  generation and loading notice after the new server baseline is installed;
- replacing the image or picture is a fresh request owner even if its strings
  compare equal;
- moving a retained tree between a Document and its open ShadowRoot preserves
  ownership after root-scope refresh because listeners live on the image;
- cross-Document adoption, a closed ShadowRoot, missing/duplicate direct
  anatomy, or a changed correlation signature fails closed and requires fresh
  initialization; and
- full replacement closes the old notification generation before the new one
  can notify.

Handoff uses three separate ledgers:

1. the correlation signature validates Citry ownership, exact retained objects,
   actual root, direct anatomy, and reserved markers;
2. the request/selection fingerprint decides whether status/generation can be
   preserved or one new loading generation begins; and
3. copied allowed root/image attr baselines are repairable consumer output and
   do not participate in equal-request identity.

Framework-generated `data-cid*`, `data-cev*`, fill-source, and Alpine-state
markers are excluded from request identity. Request identity includes every
authored source record but never derives from mutable `data-status`, allowed
consumer attrs, or `currentSrc` alone. A correlated morph may change root or
image class/style/title/data/aria-describedby without replacing equal image
objects or restarting loading; the new validated server baseline becomes the
repair target.

Unauthorized mutation of owned structure, resource attributes, part markers,
readiness, or reserved runtime markers removes readiness, detaches component
behavior, and leaves a safe native server/DOM fallback. The runtime does not
fight arbitrary external source mutation. Recovery needs a legitimate
correlated morph or reinitialization. Allowed consumer class/style/title/data
mutations are not hostile and do not restart loading.

Cleanup is owner-token guarded. It removes exactly its two native listeners,
queued tasks, mutation registration, readiness, and controller record. A stale
cleanup cannot remove a replacement controller's registration or reset its
DOM. After final removal, shared scope observers disconnect and registries are
empty. Late native events and decode work cannot notify. Repeated init/cleanup,
1/10/100 roots, fragment insertion, signed retained/replacement morphs, raw
clones, nested roots, and ShadowRoot moves are acceptance cases.

## 15. Security and content trust

`src`, `srcset`, `sizes`, `media`, `type`, `alt`, and callback details are data,
not HTML. The server renderer escapes them as attributes. Plain-string
normalization rejects U+0000 and disallowed ASCII controls. Active
`javascript:` and `vbscript:` URL schemes are rejected after ASCII whitespace
normalization. Relative, `http`, `https`, `data`, and `blob` image URLs remain
application-trusted resource references and browser/CSP inputs, not sanitized
or fetched by Citry.

The HTML image model does not execute scripted SVG as an image resource, but
Citry does not parse or sanitize SVG, bitmap metadata, data URLs, or blob
contents. Data URLs can enlarge HTML and expose embedded data; blob URLs have
application-managed lifetime; cross-origin images can track users and affect
privacy; remote SVG and raster resources can be expensive or malicious. The
application chooses trusted origins and CSP. `img-src` remains authoritative.

`cross_origin` only selects the native CORS mode. It does not grant canvas
readback or repair server headers, and a refused cross-origin response can
settle as error. `referrer_policy` is applied before `src` and controls the
native request's referrer according to the browser. Image never logs full
resource strings, signed query parameters, `currentSrc`, callback objects,
native events, Errors, or response bodies. Diagnostics use input names,
indexes, primitive enum values, and constant type categories only.

Root `attrs` rejects `role`, `tabindex`, `hidden`, `inert`, `popover`, every
`aria-*`, owned/public reflection names, runtime prefixes, ownership
directives, raw `on*` handlers, and dynamic bindings to those destinations.
Semantics belong on the image or surrounding native structure.

`img_attrs` rejects owned `src`, `srcset`, `sizes`, `alt`, `width`, `height`,
`loading`, `decoding`, `fetchpriority`, `crossorigin`, `referrerpolicy`,
`draggable`, `hidden`, `inert`, `popover`, role/name-hiding ARIA, part/runtime
markers, raw `on*`, ownership directives, and dynamic bindings to them. It
allows reviewed ordinary global/image semantics including `title`,
`aria-describedby`, class/style, test data, Alpine native
listeners, and unrelated bindings. The `img_attrs` mapping and every source
record are copied before rendering so later caller mutation cannot bypass
validation. `usemap` and `ismap` are explicitly rejected with the other
relationship-owning destinations.

`position` rejects controls, semicolons, braces, and backslashes before it can
enter a CSS declaration; the browser then validates object-position grammar.
Structured `style` values are explicit consumer-authored CSS trust, governed by
the package-wide style contract.

Slot content is ordinary escaped Citry composition unless an application
explicitly uses a separately documented trusted-HTML surface. Its wrapper is
inert and hidden from AT. Image never evaluates fallback markup, creates a
canvas, reads pixels, parses EXIF, proxies bytes, or uploads files.

## 16. Assets and performance

The family emits one Image runtime and one Image theme asset. It adds no icon,
font, fetch helper, canvas, preload link, decoder, worker, viewport listener,
pointer listener, or overlay dependency. Each live image owns one `load` and one
`error` listener. Structural observation reuses one affected-registrant observer
per actual root scope, so 1, 10, and 100 instances do not add scope observers.

The production limits are intentionally simple and apply to the complete Image family payload:

| Asset | Raw | gzip | Brotli |
|---|---:|---:|---:|
| Image JavaScript | `< 32 KiB` | `< 7.5 KiB` | `< 6.5 KiB` |
| Image CSS | `< 6 KiB` | `< 1.25 KiB` | `< 1 KiB` |

The asset report and its focused tests are authoritative for current
measurements. Volatile implementation snapshots are not duplicated here.
Behavior, trust boundaries, diagnostics, readiness, and cleanup cannot be
removed merely to meet a size limit; a legitimate overage returns to design
review.

Static server output still includes the small runtime because cached
settlement, error fallback, callbacks, and morph ownership are the component's
durable value. Network bytes for caller images are never attributed as library
assets, but examples use local bounded fixtures and document their dimensions.

There is no first-interaction path. Initialization is O(number of sources),
does not synchronously decode, and forces no layout beyond the one cached-state
read. The asynchronous decode probe exists only for an ambiguous cached
complete/current/zero-width request. Each accepted browser settlement schedules
at most one notification task.
No polling or recurring task is allowed. After settled readiness, an idle page
has zero component task churn and zero redundant attribute mutations. Cleanup
returns listener, observer-entry, task, and controller counts to baseline.

## 17. Acceptance matrix

Implementation cannot begin until this design receives independent review.
Release requires the following evidence on the final implementation.

### Server, schema, typing, and packaging

| Gate | Required evidence |
|---|---|
| Public API | Exact import/export assertions for `CImage`, records, details, and aliases; no private controller/helper export. |
| Template rendering | Smallest informative and decorative forms render valid native image output with required alt/dimensions. |
| Python rendering | Direct `CImage(...)` plus tuple `CImageSource` records renders byte-equivalent anatomy and source order. |
| Picture content model | Zero sources emits no picture; one and many emit ordered sources followed by exactly one image; width descriptors have same-owner sizes; eager/lazy/final-image/source auto-sizes and discriminator arrangements pass the WHATWG HTML validator. |
| Input validation | Wrong types, bool dimensions, nonpositive dimensions, unpaired source dimensions, width descriptors without sizes, eager image `auto` sizes, source `auto` sizes with absent/non-auto final image sizes, exact/case/whitespace `media=all` as the sole required discriminator, invalid MIME essence, structurally required media/type omissions, invalid enums, NUL/controls, active URL schemes, unsafe position text, image-map attrs, more than 32 sources, and invalid attrs fail with constant redacted errors. |
| Native media grammar boundary | Controls/empty media fail server validation; a deliberately malformed but plain consumer media query demonstrates documented caller grammar ownership, while every library-authored media query passes the HTML validator and C/F/W `matchMedia`. |
| Snapshot safety | One-shot/mutable sequences and nested mappings are consumed/copied once; later mutation cannot affect rendered bytes. |
| Attr destinations | Structured root class/style/attrs and image attrs merge at exact documented nodes; every owned/static/dynamic spelling is rejected. |
| Slots | Placeholder and fallback wrappers have exact hidden/inert/ARIA anatomy; detectable interactive content is rejected. |
| Structured docs | `api.yml`, family guide, all aliases/records/parts/attrs/variables, and example catalog validate. |
| Registration | Family catalog, package root, actual wheel, docs preview, server route, and private helper registration include exactly intended symbols/assets. |

### Automated browser behavior

Unless an item names a narrower browser, it runs in Chromium 151, Firefox 153,
and WebKit 26.5 or the repository's later qualified replacements.

| Gate | Required evidence |
|---|---|
| Basic success/error | Trusted load and error produce exact status, detail, mirror, slot visibility, natural dimensions, and no duplicate callback. |
| Cached race | Success and broken responses complete before initializer attachment; ordered loading then loaded/error notices still occur once. |
| Empty-complete guard | A hostile missing/empty resource can never become loaded merely because `complete` is true. |
| Stable geometry | Exact root/image boxes before readiness, during delayed load, after load, and after error equal the required width/height ratio at narrow and unconstrained widths; 1280×720 constrained to 200px is 200×112.5 in C/F/W. |
| Fit and position | Every fit token, object position, root style override, public variable override, and part selector produces computed expected values; a `1 / 1` public ratio produces a 200×200 replaced-element box in C/F/W. |
| Responsive width candidates | Separate narrow/wide route loads and DPR contexts produce `currentSrc` that belongs to the valid authored candidate set, with callback/network agreement; no exact UA candidate or same-document upgrade schedule is asserted. |
| Art direction and format | Ordered media/type records select the expected candidate; a deterministic live picture-media mutation changes `currentSrc` with unchanged `src`; reorder/change begins one authored generation. |
| DPR | Density selection belongs to the valid authored candidate set in isolated 1x and 2x contexts and callback agrees; no component DPR listener or exact-choice promise exists. |
| Candidate failure/recovery | A disjoint picture media valid→broken→valid probe records the native event ledger in C/F/W. Where the browser emits matching trusted settlements, Image produces loaded→error→loaded and exact selected-source callbacks without an invented loading callback. Chromium's proven silent broken-candidate transition changes `currentSrc` but retains the last accepted status/callback ledger; no observer or synthetic error is added. |
| Rapid supersession | Delayed A to immediate B, valid to broken, broken to valid, and three-step churn accept only current generation notices. |
| Cached zero-width decode | Valid 0x0 SVG resolves to loaded; broken cached request rejects to error; superseded decode rejection is inert while the new request can load. |
| Loading detail snapshot | Slow replacement after a loaded image emits loading detail containing the live retained prior `currentSrc`/dimensions, then final detail for the promoted request; same base src with changed source set follows owner state, not a public private-generation token. |
| Non-request mutations | Settled changes to height, alt, loading, decoding, fetch priority, fit, position, draggable, callback, and allowed attrs produce no synthetic loading, duplicate request, or status callback. |
| Visual slots | Placeholder appears only during ready loading, fallback only on ready error, native pixels are transparent only when corresponding slot exists, and native img is never hidden from AT. |
| No custom slots | Without placeholder/fallback, native pending and broken rendering remain visible. |
| Native events | Image-level native listeners receive real events; root listener does not rely on bubbling; `$dispatch`/`$store` bridge works; callback remains owner-local. |
| Semantics | Accessible-name snapshots and axe cover informative, decorative, functional-link, figure, broken, placeholder, and fallback cases without duplicate root image role. |
| Pointer/keyboard | Native context menu, drag setting, surrounding link/button activation, and Tab order remain native; component prevents no event; image-map attrs are rejected. |
| CSP/CORS/referrer | Local two-origin fixture verifies `img-src` block, anonymous/credential mode attribute, referrer-policy request header, and error settlement without URL-bearing diagnostics. |
| No-JS | JavaScript-disabled route shows native image or native broken alt, intrinsic geometry, ordered sources, and no visual slot obstruction. |
| Morph, equal | Signed correlated retained morph preserves root/picture/image/source object identities, status/currentSrc/private generation, and exactly two listeners with no callback, including allowed root/image attr baseline changes. |
| Morph, resource change | Signed same-object resource change begins one loading generation and accepts only the final settlement. |
| Morph, source dimensions | Retained selected-source width/height changes under density and lazy auto-sizes begin one generation, preserve element identities, and settle to native URL/geometry/callback results in C/F/W. |
| Morph, replacement | Image/picture replacement invalidates old listeners/events, initializes fresh anatomy, and never inherits readiness. |
| Remove/restore | Two removal/restore cycles end at baseline counts; late events do nothing; restored root initializes once. |
| Clone and hostile anatomy | Direct cloned readiness, nested forged parts, duplicate/missing source/image, owned attr mutations, unknown runtime prefixes, and cross-Document/closed-root moves fail closed. |
| Open ShadowRoot | Full lifecycle and responsive switch work after retained Document/open-ShadowRoot moves; callbacks remain single. |
| Scaling | 1/10/100 roots share runtime/style/helper and mutation scope; listener count is exactly two per live image; final cleanup is zero. |
| Idle | Two idle animation frames and 500 ms after settle show zero recurring tasks and zero owned-attribute mutation churn. |
| Print | Chromium print emulation hides placeholder, preserves loaded image/error fallback, and does not assert a lazy-fetch guarantee. |
| Environment | Light/dark/nested schemes, RTL, forced colors, 200%/400% zoom, text spacing, narrow width, and reduced motion screenshots/computed styles meet section 11. |
| Console | Every focused route has zero unexpected page errors, unhandled rejections, warnings, or sensitive-value diagnostics. |

The signed lifecycle sequence is: initial ready, equal retained morph, resource
change, image replacement, removal, restore, second removal, second restore. It
records object identities, exact callbacks, statuses, current source suffixes
without logging secrets, listeners, observer registrants, readiness, and final
cleanup after every step.

### Performance and quality

- the family and catalog payloads pass the section 16 raw/gzip/Brotli caps for
  Image-only, Avatar-only, combined, 1/10/100 roots, and the actual wheel;
- shared runtime and style payloads emit only once;
- delayed local fixture images cause no layout shift attributable to Image's
  box in Lighthouse/PerformanceObserver evidence;
- a likely-LCP eager/high example remains discoverable in initial HTML and has
  no `data-src`, JS insertion, or component preload;
- a below-fold lazy example verifies native attributes but does not assert
  engine-specific distance thresholds; and
- axe, HTML validation, Ruff, typing, API schema, diff audit, em-dash audit,
  wheel inclusion, and license checks pass.

### Manual release evidence

- NVDA with Firefox, JAWS with Chromium, and VoiceOver with WebKit review the
  semantic cases in section 8;
- keyboard-only and touch review confirms surrounding links/buttons and native
  context menus are unaffected;
- design review covers crop quality, placeholder/fallback clarity, dark and
  forced-colors treatment, print, narrow layouts, and 400% zoom;
- network review checks actual LCP/lazy selection, CORS, referrer policy, CSP,
  cache/offline behavior, and responsive byte choice on representative devices;
  and
- human copy review verifies every public image has intentional alternative
  text rather than filename or duplicated caption text.

## 18. Compatibility classification

### Stable public API

- `CImage`;
- `CImageSource` and `CImageStatusChangeDetail` fields and frozen-record
  meanings;
- `CImageStatus`, `CImageFit`, `CImageLoading`, `CImageDecoding`,
  `CImageFetchPriority`, `CImageCrossOrigin`, and `CImageReferrerPolicy`
  literal aliases;
- all section 4 input names, defaults, validation meanings, and destinations;
- `placeholder` and `fallback` slot names and visual-only meanings;
- `onStatusChange` timing and detail meaning;
- public CSS variables, selectors, reflected attributes, and readiness name;
  and
- the absence of public methods, form output, synthetic events, or a source
  declaration component.

### Behavioral and structural contract

- one neutral root, exactly one native semantic image, optional native picture
  with ordered source-before-image children, and optional inert visual slots;
- required native alt and dimensions, native source selection and fetch hints,
  no-JavaScript discoverability, and native broken-image fallback;
- status transitions, cached settlement, current-source notifications,
  generation supersession, responsive environment behavior, and visual-slot
  policy;
- native keyboard/pointer/focus/context-menu behavior and non-form status;
- morph handoff, exact replacement behavior, readiness ownership, hostile
  mutation failure, cleanup, security, and redacted diagnostics; and
- asset caps and no proxy/observer/preload/decode/overlay engines.

### Evolvable design

Exact theme token values, radius, fallback colors, loading background, internal
spacing, visual fallback arrangement, and undocumented class names may improve
without changing public variables, parts, states, semantics, or geometry.
Changes visible to users need release notes and regression evidence.

### Private implementation

Private classes and variables, normalized record shapes, fingerprint encoding,
controller/owner-token keys, registry representation, task scheduling, direct
listener functions, correlation markers, and any pure shared Avatar/Image
lifecycle helper are private. Framework-generated `data-cid*`, `data-cev*`,
fill-source, and Alpine markers are not public Image selectors.

Changing a stable name, type, default, destination, callback meaning, part,
variable, reflected attribute, or advertised behavior follows semantic
versioning and deprecation policy.

## 19. Public documentation contract

The component guide is `citry_ui/components/cimage/api.md`; the exhaustive
structured reference is `api.yml`. The guide order is:

1. required source, alternative text, and stable dimensions;
2. rendered size, fit, position, and theme customization;
3. responsive `srcset`, `sizes`, and ordered `CImageSource` art direction;
4. eager/lazy loading, decoding, fetch priority, CORS, and referrer policy;
5. visual placeholder/error fallback and status callbacks;
6. Card, Skeleton, figure, link/button, and ShadowRoot composition;
7. reactive sources, cached settlement, native event scope, and morph behavior;
8. security, CSP, data/blob/SVG caveats, print, and reduced-data policy; and
9. boundaries: Avatar, animated image, gallery/preview, optimizer/proxy, upload,
   and preload.

The guide begins with the rule that `alt`, `width`, and `height` are decisions,
not boilerplate. It links the WAI decision tree and shows `alt=""` only in an
explicitly decorative example. It never teaches filenames as alt text,
duplicates a caption as alt by default, hides URLs in `data-src`, lazy-loads a
hero, uses `fetch_priority="high"` on multiple images, or makes placeholder
content the accessible replacement.

`api.yml` is grouped by Inputs, Slots, Events, Methods, CSS, Attributes,
Selectors, and Interfaces. Inputs distinguish server fields from client
`$c-props` names and exact root/image destinations. Slots document their
inert/ARIA-hidden visual role. Events distinguish `onStatusChange` from native
`@load`/`@error`. Methods is `-`. Interfaces expand every alias and record
field inline. Each row has a stable kebab-case ID.

### Exact public example catalog

The docs preview suite uses one local “Northstar Observatory Archive” theme.
All images are repository fixtures with declared pixel dimensions, small byte
sizes, license metadata, deterministic valid/error/delayed routes, and no
third-party availability dependency.

| Order and source module | Reader task | Fixture theme and copy | Visible states | Controls | Interaction | Environmental profiles | Contract coverage | Focused browser evidence |
|---|---|---|---|---|---|---|---|---|
| 1 `basic_image.py` | Render a meaningful stable image | “Orion Nebula, captured from Northstar Ridge”; 1280x720 local JPEG | loaded informative image; initial loading captured in test | none | inspect source disclosure | light and dark | smallest template and Python calls, required alt/width/height, no-JS, native semantics, geometry | server parity; JS-disabled screenshot; C/F/W delayed box and loaded status; axe |
| 2 `alternative_text.py` | Choose informative, decorative, functional, and complex-image text | nebula photo, decorative star wash, “Open full observation” image link, chart plus adjacent data table | four semantic cases side by side | none | Tab/activate functional image link | light, 200% zoom, screen-reader task | empty alt, meaningful alt, functional naming, figure/table composition, no duplicate root role | accessibility tree/axe in C/F/W; manual NVDA/JAWS/VoiceOver checklist |
| 3 `fit_and_geometry.py` | Keep a stable box while selecting crop behavior | same lunar panorama shown contain/cover/scale-down; labels are real text | loading placeholders then loaded crops | server controls for fit and position use full route reload; side-by-side fixed variants | compare crops; no custom keyboard | narrow/wide, RTL, 400% zoom | intrinsic ratio, rendered CSS size, fit/position inputs, public variables, root/image selectors, structured class/style | exact pre/post/error boxes and computed style in C/F/W; screenshots |
| 4 `responsive_sources.py` | Author width candidates and art direction | observatory portrait under 48rem, wide dome above 64rem, AVIF type candidate with JPEG fallback | selected current candidate labeled outside Image from callback | viewport presets 360/768/1280 and DPR route variants | resize disjoint media preview; source disclosure | narrow/wide, DPR 1/2, RTL | `CImageSource` records, native picture order, srcset/sizes/media/type/source dimensions, unchanged src with changed currentSrc | C/F/W exact disjoint-media ledger; server/HTML source validation; plain srcset/network membership assertion |
| 5 `loading_priority.py` | Choose native loading and priority responsibly | one above-fold “Tonight’s featured field” hero, one below-fold archive image | eager/high hero and lazy/auto archive | scroll-to-archive button outside Image | scroll; observe request ledger | narrow/wide, JavaScript disabled, print | native discoverability, eager vs lazy, fetchpriority/decoding, LCP warning, no IO/preload/data-src | initial HTML assertion, Chromium performance/network diagnostic, C/F/W native attrs, JS-disabled load |
| 6 `placeholder_and_error.py` | Add visual loading and error treatments without losing alt semantics | delayed Horsehead image, intentionally missing archive plate, ordinary broken image | loading placeholder, custom fallback, native broken rendering, later success | reload generation; switch valid/broken buttons update owner props | trigger success/error/recovery | light/dark/forced colors/reduced motion/print | placeholder/fallback slots, inert/aria-hidden, native alt retention, no transition, error recovery | C/F/W state/slot ledger and accessible tree; forced-color and print screenshot; zero layout shift |
| 7 `reactive_image.py` | Observe current selection and safely supersede requests | “Live survey frame” switches slow red/fast blue/responsive frames; status log displays redacted filenames only | loading/loaded/error and callback ledger | buttons A, B, broken, responsive; rapid A→B action | source churn and viewport change | Document and open ShadowRoot variants | client inputs, generation, currentSrc detail, native event `$dispatch` bridge, callback isolation, cached completion, stale suppression | C/F/W rapid/cached/responsive exact ledger; late-event cleanup; console check |
| 8 `image_composition.py` | Put Image in Card, Skeleton layout, figure, and image-only link | archive card, “Exposure notes” figure/caption, linked observation thumbnail | loaded card media and decorative skeleton neighboring a delayed image | none | Tab and activate linked thumbnail | light/dark, narrow, text spacing | Card media ownership, Skeleton remains decorative/static, figure/caption, functional alt, ordinary composition | server anatomy; C/F/W focus/accessibility/geometry; screenshots |
| 9 `delivery_and_security.py` | Configure CORS/referrer policy and understand trusted URLs | same-origin plate, credential-free second-origin plate, CSP-blocked plate, explanatory safe text | loaded and error cases; no secret URL printed | same-origin/cross-origin/CSP route selector via reload | inspect safe request summary | strict CSP, offline diagnostic profile | crossorigin/referrerpolicy, CSP authority, data/blob/SVG guidance, redacted diagnostics, no proxy/canvas | local two-origin C/F/W request/header/error test; strict-CSP preview; console scan |
| 10 `image_lifecycle.py` | Verify retained/replaced/removed image behavior | “Nightly calibration plate” with numbered deterministic generations | open status ledger, retained selection, replacement loading, absent/restored roots | signed refresh controls and one rapid-update control | equal morph, source change, replacement, two remove/restores | Document/open ShadowRoot move; 1/10 roots in quality route | owner tokens, exact anatomy, request/selection fingerprint, readiness, clone/hostile repair, listener/observer cleanup | signed C/F/W lifecycle; identity/count assertions; hostile and clone falsifiers; axe/console |

Example controls mutate only true client inputs or perform documented server
refreshes. No configurator pretends that structural source records change
client-side without a server morph. Each page names its expected visual state,
has visible copy outside the image when status matters, and uses source
disclosure that is valid in both template and Python composition.

The component quality scenario reuses `image_lifecycle.py`'s Python-owned
fixture data for standalone routes, docs preview, Playwright, screenshots,
axe, and manual tasks. Browser checks select roles, native relationships, or
stable public parts only when the part itself is under contract.

## 20. Open decisions and deferred work

No open decision blocks implementation.

| Deferred work | Evidence required to revisit | Owner | Blocks v1? |
|---|---|---|---|
| Public `CImageSource` declaration component | A real per-source slot, callback, reactive identity, independent styling, or ambient ownership job that a frozen ordered record cannot express | future Image research | no; explicitly rejected for v1 |
| Optional/missing base `src` and a public empty state | Product examples where source absence is meaningful and native no-JS fallback remains clearer than conditional rendering | future product design | no; v1 requires nonempty `src` |
| Built-in fallback URL | Evidence that a second image request can preserve truthful alt/error identity, avoid loops, and improve common code over a visual fallback slot | future design | no; rejected for v1 |
| Automatic reduced-data source selection | Stable cross-engine standard support and product policy for quality/consent tradeoffs | platform/application research | no |
| Image preload API | Measured LCP cases where server `<link>` ownership cannot solve discovery without duplicate responsive downloads | performance infrastructure | no; outside v1 |
| Image optimizer, CDN transform/signing, proxy, or upload | Separate security, cache, deployment, and cost design | infrastructure families | no; outside Citry UI |
| Preview/lightbox/gallery | Dedicated overlay, collection, gestures, zoom, focus, and mobile interaction design | future Gallery/ImageViewer family | no |
| Animated image playback controls | Dedicated canvas/CORS/reduced-motion/AT design | future AnimatedImage family | no |
| AspectRatio component | Non-image media and generic content examples that earn a separate layout primitive | future layout family | no; Image v1 uses native dimensions/CSS |
| Decode-complete callback | A user job that needs decode readiness and can distinguish normal supersession rejection from actual resource failure | future async research | no; explicitly rejected for v1 |

The first implementation must repeat the anatomy review. It must confirm that
the stable root remains justified by visual slot/layout contracts and that
`CImageSource` still has no declaration-component job. Any change to the
native-first boundary, required geometry, alt policy, status semantics,
security model, or asset caps reopens design and independent review before
runtime changes.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
