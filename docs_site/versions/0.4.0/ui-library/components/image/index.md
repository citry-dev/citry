---
title: Image
url: https://citry.dev/v/0.4.0/ui-library/components/image/
description: "Render native responsive images with stable geometry and explicit alternative text."
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


### Render a native image with stable geometry

[Open the rendered preview](/v/0.4.0/ui-library/components/image/_previews/basic-image/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CImage

citry.register_library(citry_ui)


class BasicImage(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        return {
            "python_image": CImage(
                src="/static/img/ui/image/orion-nebula-1280.jpg",
                alt="Orion Nebula, captured from Northstar Ridge",
                width=1280,
                height=720,
                loading="eager",
            )
        }

    template = """
      <section class="image-basic">
        <article>
          <h3>Template composition</h3>
          <c-CImage
            src="/static/img/ui/image/orion-nebula-1280.jpg"
            alt="Orion Nebula, captured from Northstar Ridge"
            c-width="1280"
            c-height="720"
            loading="eager"
          />
        </article>
        <article>
          <h3>Python composition</h3>
          {{ python_image }}
        </article>
        <p>
          Both forms keep one native image semantic, required alternative text,
          and a reserved 16:9 box before the files finish loading.
        </p>
      </section>
    """

    css = """
      :where(.image-basic) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-basic article) { display: grid; gap: 0.5rem; }
      :where(.image-basic h3, .image-basic p) { margin: 0; }
      :where(.image-basic p) { grid-column: 1 / -1; }
      :where(.image-basic [data-citry-ui-part="image-root"]) {
        inline-size: 100%;
      }
    """


preview = BasicImage()

preview  # noqa: B018
````


Choose the alternative for the image's purpose in context. An image-only link
needs destination text. A complex chart needs an adjacent data equivalent.
A caption does not replace `alt`.


### Compare informative, decorative, functional, and complex images

[Open the rendered preview](/v/0.4.0/ui-library/components/image/_previews/alternative-text/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ImageAlternativeText(Component):
    template = """
      <section class="image-alt">
        <article>
          <h3>Informative</h3>
          <c-CImage
            src="/static/img/ui/image/orion-nebula-640.jpg"
            alt="Pink and blue clouds in the Orion Nebula"
            c-width="640"
            c-height="360"
          />
          <p>The alternative conveys the observation's useful content.</p>
        </article>

        <article>
          <h3>Decorative</h3>
          <c-CImage
            src="/static/img/ui/image/orion-nebula-640.jpg"
            c-alt="''"
            c-width="640"
            c-height="360"
          />
          <p>The nearby heading already supplies all meaning, so alt is empty.</p>
        </article>

        <article>
          <h3>Functional</h3>
          <a href="#full-observation">
            <c-CImage
              src="/static/img/ui/image/horsehead-nebula-640.jpg"
              alt="Open the full Horsehead Nebula observation"
              c-width="640"
              c-height="360"
            />
          </a>
          <p>The image is the link's only content, so alt names the destination.</p>
        </article>

        <article>
          <h3>Complex observation</h3>
          <figure>
            <c-CImage
              src="/static/img/ui/image/lunar-terminator-1280.jpg"
              alt="Lunar terrain map; values follow in the table"
              c-width="1280"
              c-height="640"
            />
            <figcaption>Exposure measurements along the lunar terminator.</figcaption>
          </figure>
          <table>
            <caption>Equivalent exposure data</caption>
            <thead><tr><th>Region</th><th>Seconds</th></tr></thead>
            <tbody><tr><td>North rim</td><td>0.008</td></tr><tr><td>South basin</td><td>0.013</td></tr></tbody>
          </table>
        </article>
      </section>
    """

    css = """
      :where(.image-alt) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-alt article) { display: grid; gap: 0.5rem; align-content: start; }
      :where(.image-alt h3, .image-alt p, .image-alt figure) { margin: 0; }
      :where(.image-alt [data-citry-ui-part="image-root"]) { inline-size: 100%; }
      :where(.image-alt a:focus-visible) { outline: 3px solid Highlight; outline-offset: 3px; }
      :where(.image-alt table) { border-collapse: collapse; font-size: 0.8rem; }
      :where(.image-alt th, .image-alt td) { border: 1px solid GrayText; padding: 0.25rem; }
    """


preview = ImageAlternativeText()

preview  # noqa: B018
````


## Size and crop the rendered image

Use ordinary CSS to constrain rendered size. `fit` and `position` control the
pixels inside that box. Native `width` and `height` remain intrinsic metadata.
Public variables can override the aspect ratio, crop, position, radius, and
state colors without relying on private classes.


### Compare stable geometry and object fit

[Open the rendered preview](/v/0.4.0/ui-library/components/image/_previews/fit-and-geometry/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ImageFitAndGeometry(Component):
    template = """
      <section class="image-fit-grid">
        <article>
          <h3>Contain</h3>
          <c-CImage
            src="/static/img/ui/image/lunar-terminator-1280.jpg"
            alt="Lunar craters along the terminator, contained"
            c-width="1280"
            c-height="640"
            fit="contain"
            class_="image-fit-grid__frame"
          />
        </article>
        <article>
          <h3>Cover, left focus</h3>
          <c-CImage
            src="/static/img/ui/image/lunar-terminator-1280.jpg"
            alt="Lunar craters along the terminator, closely cropped"
            c-width="1280"
            c-height="640"
            fit="cover"
            position="20% 50%"
            class_="image-fit-grid__frame"
          />
        </article>
        <article>
          <h3>Scale down</h3>
          <c-CImage
            src="/static/img/ui/image/lunar-terminator-1280.jpg"
            alt="Lunar craters along the terminator, scaled down"
            c-width="1280"
            c-height="640"
            fit="scale-down"
            class_="image-fit-grid__frame image-fit-grid__square"
            c-style="{'--cui-image-radius':'1.25rem'}"
          />
        </article>
      </section>
    """

    css = """
      :where(.image-fit-grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-fit-grid article) { display: grid; gap: 0.5rem; }
      :where(.image-fit-grid h3) { margin: 0; }
      :where(.image-fit-grid__frame) {
        inline-size: 100%;
        --cui-image-aspect-ratio: 4 / 3;
        --cui-image-background: light-dark(#e7e5e4, #1c1917);
      }
      :where(.image-fit-grid__square) { --cui-image-aspect-ratio: 1 / 1; }
    """


preview = ImageFitAndGeometry()

preview  # noqa: B018
````


## Author responsive sources

Pass ordered frozen `CImageSource` records to emit a native `<picture>`. The
records are data, not component declarations. Native first-match order matters.
Width-descriptor `srcset` requires `sizes`, and arbitrary `media` text remains
browser syntax that the application must validate.


### Use srcset, sizes, art direction, and AVIF

[Open the rendered preview](/v/0.4.0/ui-library/components/image/_previews/responsive-sources/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CImage, CImageSource

citry.register_library(citry_ui)


class ResponsiveImageSources(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        sources = (
            CImageSource(
                media="(max-width: 47.99rem)",
                srcset="/static/img/ui/image/observatory-portrait-640.jpg",
                width=640,
                height=960,
            ),
            CImageSource(
                media="(min-width: 64rem)",
                type="image/avif",
                srcset="/static/img/ui/image/observatory-wide-1280.avif",
                width=1280,
                height=720,
            ),
        )
        return {
            "sources": sources,
            "responsive_srcset": (
                "/static/img/ui/image/observatory-portrait-640.jpg 640w, "
                "/static/img/ui/image/observatory-wide-1280.jpg 1280w"
            ),
            "python_image": CImage(
                src="/static/img/ui/image/observatory-wide-1280.jpg",
                alt="Northstar Observatory beneath the Milky Way",
                width=1280,
                height=720,
                srcset=(
                    "/static/img/ui/image/observatory-portrait-640.jpg 640w, "
                    "/static/img/ui/image/observatory-wide-1280.jpg 1280w"
                ),
                sizes="(max-width: 48rem) 100vw, 48rem",
                sources=sources,
            ),
        }

    template = """
      <section
        class="image-responsive"
        x-data="{selected:'Waiting for native selection'}"
      >
        <p>
          Resize across 48rem and 64rem. The browser selects the first matching
          source, then the final image candidates.
        </p>
        <div class="image-responsive__pair">
          <article>
            <h3>Template-fed records</h3>
            <c-CImage
              src="/static/img/ui/image/observatory-wide-1280.jpg"
              alt="Northstar Observatory beneath the Milky Way"
              c-width="1280"
              c-height="720"
              c-srcset="responsive_srcset"
              sizes="(max-width: 48rem) 100vw, 48rem"
              c-sources="sources"
              $c-props="{
                onStatusChange:(detail)=>{
                  const value=detail.current_src || detail.src;
                  selected=value.split('/').pop().split('?')[0];
                },
              }"
            />
          </article>
          <article>
            <h3>Python records</h3>
            {{ python_image }}
          </article>
        </div>
        <output x-text="`Selected local fixture: ${selected}`">
          Selected local fixture: Waiting for native selection
        </output>
      </section>
    """

    css = """
      :where(.image-responsive) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-responsive__pair) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
      }
      :where(.image-responsive article) { display: grid; gap: 0.5rem; }
      :where(.image-responsive h3, .image-responsive p) { margin: 0; }
      :where(.image-responsive [data-citry-ui-part="image-root"]) { inline-size: 100%; }
    """


preview = ResponsiveImageSources()

preview  # noqa: B018
````


## Choose native loading and priority hints

Use `loading="eager"` and `fetch_priority="high"` only for a genuinely
important above-fold image. Keep ordinary archive media at native lazy or auto
priority. Image adds no observer, data-src indirection, preload, or custom
decode gate, so the resource stays discoverable in server HTML.


### Compare eager and lazy native loading

[Open the rendered preview](/v/0.4.0/ui-library/components/image/_previews/loading-priority/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ImageLoadingPriority(Component):
    template = """
      <section class="image-priority">
        <article>
          <p class="image-priority__eyebrow">Above the fold</p>
          <h3>Tonight's featured field</h3>
          <c-CImage
            src="/static/img/ui/image/orion-nebula-1280.jpg"
            alt="Orion Nebula selected as tonight's featured field"
            c-width="1280"
            c-height="720"
            loading="eager"
            decoding="async"
            fetch_priority="high"
          />
          <p>Reserve high priority for the small number of likely LCP images.</p>
        </article>

        <button
          type="button"
          @click="document.querySelector('#image-priority-archive').scrollIntoView({behavior:'auto'})"
        >Scroll to the archive image</button>

        <div class="image-priority__spacer" aria-hidden="true"></div>

        <article id="image-priority-archive">
          <p class="image-priority__eyebrow">Below the fold</p>
          <h3>Archive plate</h3>
          <c-CImage
            src="/static/img/ui/image/horsehead-nebula-1280.jpg"
            alt="Horsehead Nebula archive plate"
            c-width="1280"
            c-height="720"
            loading="lazy"
            decoding="async"
            fetch_priority="auto"
          />
          <p>Lazy loading remains a native hint and needs no data-src indirection.</p>
        </article>
      </section>
    """

    css = """
      :where(.image-priority) {
        display: grid;
        gap: 1rem;
        max-inline-size: 46rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-priority article) { display: grid; gap: 0.5rem; }
      :where(.image-priority h3, .image-priority p) { margin: 0; }
      :where(.image-priority__eyebrow) { color: GrayText; font-weight: 700; }
      :where(.image-priority__spacer) { block-size: 70vh; border-block: 1px dashed GrayText; }
      :where(.image-priority [data-citry-ui-part="image-root"]) { inline-size: 100%; }
    """


preview = ImageLoadingPriority()

preview  # noqa: B018
````


## Add visual loading and error treatments

The `placeholder` and `fallback` slots are inert visual layers. They never
replace the native `<img>` or its `alt`. With JavaScript disabled, both custom
layers stay hidden and the browser shows the native image or broken-image text
fallback. Put meaningful error copy, retry controls, and live announcements
outside Image.


### Handle loading, error, and recovery

[Open the rendered preview](/v/0.4.0/ui-library/components/image/_previews/placeholder-and-error/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ImagePlaceholderAndError(Component):
    template = """
      <section
        class="image-feedback"
        x-data="{
          source:'/static/img/ui/image/horsehead-nebula-1280.jpg?generation=1',
          status:'waiting',
        }"
      >
        <div class="image-feedback__controls">
          <button
            type="button"
            @click="source='/static/img/ui/image/horsehead-nebula-1280.jpg?generation=2'"
          >Load a valid generation</button>
          <button
            type="button"
            @click="source='/static/img/ui/image/missing-observation.jpg?generation=3'"
          >Load a broken generation</button>
          <button
            type="button"
            @click="source='/static/img/ui/image/horsehead-nebula-640.jpg?generation=4'"
          >Recover with a small image</button>
        </div>

        <div class="image-feedback__grid">
          <article>
            <h3>Visual placeholder and fallback</h3>
            <c-CImage
              src="/static/img/ui/image/horsehead-nebula-1280.jpg"
              alt="Horsehead Nebula behind a dark dust cloud"
              c-width="1280"
              c-height="720"
              $c-props="{
                src:source,
                onStatusChange:(detail)=>status=detail.status,
              }"
            >
              <c-fill name="placeholder">
                <div class="image-feedback__placeholder">
                  <c-CSkeleton height="100%" animation="wave" />
                </div>
              </c-fill>
              <c-fill name="fallback">
                <span class="image-feedback__fallback">Plate unavailable</span>
              </c-fill>
            </c-CImage>
            <output x-text="`Normalized status: ${status}`">Normalized status: waiting</output>
          </article>

          <article>
            <h3>Native broken-image fallback</h3>
            <c-CImage
              src="/static/img/ui/image/missing-native-observation.jpg"
              alt="Missing Northstar archive observation"
              c-width="640"
              c-height="360"
            />
            <p>No custom fallback is supplied, so native broken rendering and alt remain.</p>
          </article>
        </div>
      </section>
    """

    css = """
      :where(.image-feedback) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-feedback__controls) { display: flex; flex-wrap: wrap; gap: 0.5rem; }
      :where(.image-feedback__grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
      }
      :where(.image-feedback article) { display: grid; gap: 0.5rem; align-content: start; }
      :where(.image-feedback h3, .image-feedback p) { margin: 0; }
      :where(.image-feedback [data-citry-ui-part="image-root"]) { inline-size: 100%; }
      :where(.image-feedback__placeholder, .image-feedback__fallback) {
        display: grid;
        place-items: center;
        inline-size: 100%;
        block-size: 100%;
      }
      :where(.image-feedback__fallback) { padding: 1rem; font-weight: 700; }
      @media (forced-colors: active) {
        :where(.image-feedback__fallback) { border: 1px solid CanvasText; }
      }
      @media print {
        :where(.image-feedback__controls, .image-feedback output) { display: none; }
      }
    """


preview = ImagePlaceholderAndError()

preview  # noqa: B018
````


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


### Switch resources and inspect normalized status

[Open the rendered preview](/v/0.4.0/ui-library/components/image/_previews/reactive-image/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ReactiveImage(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        return {
            "image_attrs": {
                "@load": "$dispatch('image-native-load')",
                "@error": "$dispatch('image-native-error')",
                "data-native-events": "bridged",
            }
        }

    template = """
      <section
        class="image-reactive"
        x-data="{
          source:'/static/img/ui/image/horsehead-nebula-1280.jpg?frame=slow-red',
          status:'waiting',
          selected:'none',
          callbacks:0,
          nativeLoads:0,
          nativeErrors:0,
          redact:(value)=>value ? value.split('/').pop().split('?')[0] : 'none',
        }"
        @image-native-load="nativeLoads++"
        @image-native-error="nativeErrors++"
      >
        <div class="image-reactive__controls">
          <button
            type="button"
            @click="source='/static/img/ui/image/horsehead-nebula-1280.jpg?frame=slow-red'"
          >Frame A</button>
          <button
            type="button"
            @click="source='/static/img/ui/image/orion-nebula-1280.jpg?frame=fast-blue'"
          >Frame B</button>
          <button
            type="button"
            @click="source='/static/img/ui/image/missing-live-frame.jpg?frame=broken'"
          >Broken</button>
          <button
            type="button"
            @click="
              source='/static/img/ui/image/horsehead-nebula-1280.jpg?frame=rapid-a';
              queueMicrotask(()=>source='/static/img/ui/image/orion-nebula-640.jpg?frame=rapid-b');
            "
          >Rapid A then B</button>
        </div>

        <c-CImage
          src="/static/img/ui/image/horsehead-nebula-1280.jpg"
          alt="Live survey frame from Northstar Ridge"
          c-width="1280"
          c-height="720"
          c-img_attrs="image_attrs"
          $c-props="{
            src:source,
            onStatusChange:(detail)=>{
              callbacks++;
              status=detail.status;
              selected=redact(detail.current_src || detail.src);
            },
          }"
        >
          <c-fill name="fallback">Survey frame unavailable</c-fill>
        </c-CImage>

        <output
          x-text="
            `Status ${status}; selected ${selected}; callbacks ${callbacks};
            native load/error ${nativeLoads}/${nativeErrors}`
          "
        >Status waiting; selected none; callbacks 0; native load/error 0/0</output>
        <p>
          The output redacts paths to filenames. Native events use an img_attrs
          $dispatch bridge; onStatusChange is the owner-local cached-race surface.
        </p>
        <div id="image-reactive-shadow-host" aria-label="Open ShadowRoot fixture"></div>
      </section>
    """

    css = """
      :where(.image-reactive) {
        display: grid;
        gap: 1rem;
        max-inline-size: 44rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-reactive__controls) { display: flex; flex-wrap: wrap; gap: 0.5rem; }
      :where(.image-reactive p) { margin: 0; }
      :where(.image-reactive [data-citry-ui-part="image-root"]) { inline-size: 100%; }
    """


preview = ReactiveImage()

preview  # noqa: B018
````


## Compose with native and Citry structure

Image is not a figure, Card, link, button, Skeleton, lightbox, or gallery. Wrap
it in those structures when they own the semantic job. A neighboring Skeleton
remains decorative, while the real image retains its alternative text.


### Compose Image with Card, Skeleton, figure, and link

[Open the rendered preview](/v/0.4.0/ui-library/components/image/_previews/image-composition/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ImageComposition(Component):
    template = """
      <section class="image-composition">
        <c-CCard tag="article" variant="outline">
          <c-fill name="media">
            <c-CImage
              src="/static/img/ui/image/observatory-wide-1280.jpg"
              alt="Northstar Observatory below the Milky Way"
              c-width="1280"
              c-height="720"
              fit="cover"
            />
          </c-fill>
          <c-fill name="header"><h3>Northstar Ridge</h3></c-fill>
          <c-fill name="default">A clear archive exposure from the western dome.</c-fill>
        </c-CCard>

        <article class="image-composition__delayed">
          <h3>Loading layout reservation</h3>
          <div class="image-composition__pair">
            <c-CSkeleton height="7rem" animation="wave" />
            <c-CImage
              src="/static/img/ui/image/horsehead-nebula-1280.jpg?delayed=1"
              alt="Horsehead Nebula exposure loading beside a decorative skeleton"
              c-width="1280"
              c-height="720"
              loading="lazy"
            />
          </div>
        </article>

        <figure>
          <c-CImage
            src="/static/img/ui/image/lunar-terminator-1280.jpg"
            alt="Craters and mountain shadows along the lunar terminator"
            c-width="1280"
            c-height="640"
          />
          <figcaption>Exposure notes: 0.008 seconds at the north rim.</figcaption>
        </figure>

        <a class="image-composition__link" href="#observation-42">
          <c-CImage
            src="/static/img/ui/image/orion-nebula-640.jpg"
            alt="Open observation 42, Orion Nebula"
            c-width="640"
            c-height="360"
          />
        </a>
      </section>
    """

    css = """
      :where(.image-composition) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-composition h3, .image-composition figure) { margin: 0; }
      :where(.image-composition [data-citry-ui-part="image-root"]) { inline-size: 100%; }
      :where(.image-composition__pair) { display: grid; gap: 0.5rem; }
      :where(.image-composition__link) { align-self: start; border-radius: 0.75rem; }
      :where(.image-composition__link:focus-visible) { outline: 3px solid Highlight; outline-offset: 3px; }
    """


preview = ImageComposition()

preview  # noqa: B018
````


## Keep delivery policy explicit

`cross_origin` and `referrer_policy` select native request modes; they do not
grant canvas access or repair server headers. `img-src` CSP remains
authoritative. Relative, HTTP, HTTPS, data, blob, raster, and SVG image URLs are
consumer-owned resource references, not sanitized or fetched by Citry. Active
`javascript:` and `vbscript:` schemes are rejected. Blob lifetime, data-URL
size, metadata privacy, origin policy, and remote tracking remain application
responsibilities.


### Review CORS, referrer policy, CSP, and URL trust

[Open the rendered preview](/v/0.4.0/ui-library/components/image/_previews/delivery-and-security/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ImageDeliveryAndSecurity(Component):
    template = """
      <section class="image-delivery">
        <article>
          <h3>Same-origin archive</h3>
          <c-CImage
            src="/static/img/ui/image/orion-nebula-640.jpg"
            alt="Same-origin Orion Nebula plate"
            c-width="640"
            c-height="360"
            referrer_policy="strict-origin-when-cross-origin"
          />
          <p>Native request policy applies before src. Citry does not proxy bytes.</p>
        </article>

        <article>
          <h3>Credential-free CORS mode</h3>
          <c-CImage
            src="https://cross-origin.citry.test/northstar/observatory-1280.jpg"
            alt="Observatory plate requested in anonymous CORS mode"
            c-width="1280"
            c-height="720"
            cross_origin="anonymous"
            referrer_policy="no-referrer"
          >
            <c-fill name="fallback">Cross-origin plate unavailable in this preview</c-fill>
          </c-CImage>
          <p>The response still needs matching server headers for CORS use.</p>
        </article>

        <article>
          <h3>CSP and unavailable resources</h3>
          <c-CImage
            src="https://blocked-images.citry.test/northstar/blocked.jpg"
            alt="Archive plate unavailable under the current image policy"
            c-width="640"
            c-height="360"
          >
            <c-fill name="fallback">Blocked or unavailable plate</c-fill>
          </c-CImage>
          <p>Browser CSP remains authoritative and failures settle as image error.</p>
        </article>

        <aside>
          <h3>Application trust boundary</h3>
          <ul>
            <li>Relative, HTTPS, data, blob, raster, and SVG URLs remain consumer-owned.</li>
            <li>Do not log signed URLs, currentSrc, query strings, or response bodies.</li>
            <li>Blob lifetime, data-URL size, metadata privacy, and remote tracking are application policy.</li>
          </ul>
          <output>Safe request summary: request modes configured; URLs omitted</output>
        </aside>
      </section>
    """

    css = """
      :where(.image-delivery) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-delivery article, .image-delivery aside) { display: grid; gap: 0.5rem; align-content: start; }
      :where(.image-delivery h3, .image-delivery p, .image-delivery ul) { margin: 0; }
      :where(.image-delivery [data-citry-ui-part="image-root"]) { inline-size: 100%; }
    """


preview = ImageDeliveryAndSecurity()

preview  # noqa: B018
````


## Understand lifecycle and fallback

Equal retained-node server morphs preserve the active request and status.
Changing request fields starts one new generation. Replacing the native image,
removing the owner, invalid structure, a closed ShadowRoot, or cross-document
adoption requires fresh ownership. Late work from an old generation cannot
notify a replacement owner.


### Inspect retained, replaced, removed, and restored images

[Open the rendered preview](/v/0.4.0/ui-library/components/image/_previews/image-lifecycle/)

````citry
from __future__ import annotations

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ImageLifecycle(Component):
    class Kwargs:
        step: int = 0

    class Slots:
        pass

    class Events:
        def retain(self) -> ImageLifecycle:
            return ImageLifecycle(step=1)

        def change_resource(self) -> ImageLifecycle:
            return ImageLifecycle(step=2)

        def replace(self) -> ImageLifecycle:
            return ImageLifecycle(step=3)

        def remove(self) -> ImageLifecycle:
            return ImageLifecycle(step=4)

        def restore(self) -> ImageLifecycle:
            return ImageLifecycle(step=5)

        def remove_again(self) -> ImageLifecycle:
            return ImageLifecycle(step=6)

        def restore_again(self) -> ImageLifecycle:
            return ImageLifecycle(step=7)

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        source = "/static/img/ui/image/horsehead-nebula-1280.jpg?plate=baseline"
        if kwargs.step >= 2:
            source = "/static/img/ui/image/orion-nebula-1280.jpg?plate=changed"
        image_key = "image-lifecycle-retained" if kwargs.step < 3 else f"image-lifecycle-{kwargs.step}"
        return {
            "image_key": image_key,
            "include_image": kwargs.step not in {4, 6},
            "source": source,
            "step": kwargs.step,
        }

    template = """
      <section
        class="image-lifecycle"
        x-data="{status:'waiting',selected:'none'}"
      >
        <div class="image-lifecycle__controls">
          <button type="button" @c-click="retain">Retain equal server output</button>
          <button type="button" @c-click="change_resource">Change the resource</button>
          <button type="button" @c-click="replace">Replace native ownership</button>
          <button type="button" @c-click="remove">Remove the Image</button>
          <button type="button" @c-click="restore">Restore a fresh Image</button>
          <button type="button" @c-click="remove_again">Remove it again</button>
          <button type="button" @c-click="restore_again">Restore it again</button>
          <button
            type="button"
            @click="
              const root=$root.querySelector('#image-lifecycle-target');
              if (root) root.setAttribute('data-status','forged');
            "
          >Test hostile status fail-closed</button>
          <button
            type="button"
            @click="
              const root=$root.querySelector('#image-lifecycle-target');
              if (root) root.after(root.cloneNode(true));
            "
          >Insert an unowned clone</button>
        </div>

        <p>Signed server step: <output data-image-lifecycle-step>{{ step }}</output></p>

        <c-if cond="include_image">
          <c-CImage
            #c-key="image_key"
            c-src="source"
            alt="Nightly Northstar calibration plate"
            c-width="1280"
            c-height="720"
            c-attrs="{
              'id':'image-lifecycle-target',
              'data-quality-states':
                'lifecycle retained-root replacement-root morph-target removal restore '
                + 'cleanup owner-token shadow-root clone hostile-fail-closed',
            }"
            $c-props="{
              onStatusChange:(detail)=>{
                status=detail.status;
                selected=(detail.current_src || detail.src).split('/').pop().split('?')[0];
              },
            }"
          >
            <c-fill name="placeholder">Loading calibration plate</c-fill>
            <c-fill name="fallback">Calibration plate unavailable</c-fill>
          </c-CImage>
        </c-if>

        <output x-text="`Status ${status}; selected ${selected}`">
          Status waiting; selected none
        </output>
        <div id="image-lifecycle-shadow-host" aria-label="Open ShadowRoot move fixture"></div>
      </section>
    """

    css = """
      :where(.image-lifecycle) {
        display: grid;
        gap: 1rem;
        max-inline-size: 44rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-lifecycle__controls) { display: flex; flex-wrap: wrap; gap: 0.5rem; }
      :where(.image-lifecycle p) { margin: 0; }
      :where(.image-lifecycle [data-citry-ui-part="image-root"]) { inline-size: 100%; }
    """


preview = ImageLifecycle()

preview  # noqa: B018
````


Without JavaScript, the server-rendered native image, ordered responsive
sources, required `alt`, dimensions, loading hints, CORS mode, and referrer
policy remain useful. Custom placeholder and fallback slots stay hidden so
they cannot cover the native result.

Image is not form-associated and adds no keyboard, focus, overlay, gesture,
retry, upload, editing, canvas, image-map, or lightbox behavior. Important
print images should use eager loading because printing does not guarantee a
lazy request will start before pagination.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CImage server inputs

Server inputs are passed in a template through `<c-CImage ... />` or in Python through
`CImage(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 17rem; --ui-api-column-3-width: 13rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="image-input-cimage-server-inputs-src"></span>`src` | `str` | required | Sets the required nonempty escaped fallback image URL. |
| <span id="image-input-cimage-server-inputs-alt"></span>`alt` | `str` | required | Sets the required native text alternative; an exact empty string is an intentional decorative choice. |
| <span id="image-input-cimage-server-inputs-width"></span>`width` | `positive int` | required | Sets native intrinsic width and reserves geometry; bool is rejected. |
| <span id="image-input-cimage-server-inputs-height"></span>`height` | `positive int` | required | Sets native intrinsic height and reserves geometry; bool is rejected. |
| <span id="image-input-cimage-server-inputs-srcset"></span>`srcset` | `str | None` | `None` | Adds native responsive candidates; width descriptors require sizes. |
| <span id="image-input-cimage-server-inputs-sizes"></span>`sizes` | `str | None` | `None` | Adds native image source sizes; auto sizes require lazy loading. |
| <span id="image-input-cimage-server-inputs-sources"></span>`sources` | `Sequence[CImageSource]` | () | Snapshots up to 32 ordered source records and emits picture only when nonempty. |
| <span id="image-input-cimage-server-inputs-loading"></span>`loading` | `"eager" | "lazy"` ([`CImageLoading`](#image-interface-loading)) | `"eager"` | Selects the native loading hint. |
| <span id="image-input-cimage-server-inputs-decoding"></span>`decoding` | `"auto" | "sync" | "async"` ([`CImageDecoding`](#image-interface-decoding)) | `"auto"` | Selects the native decoding hint. |
| <span id="image-input-cimage-server-inputs-fetch-priority"></span>`fetch_priority` | `"auto" | "high" | "low"` ([`CImageFetchPriority`](#image-interface-fetch-priority)) | `"auto"` | Selects native fetchpriority; the application owns scarcity policy. |
| <span id="image-input-cimage-server-inputs-cross-origin"></span>`cross_origin` | `CImageCrossOrigin | None` ([`CImageCrossOrigin`](#image-interface-cross-origin)) | `None` | Selects anonymous or credentialed native CORS mode. |
| <span id="image-input-cimage-server-inputs-referrer-policy"></span>`referrer_policy` | `CImageReferrerPolicy | None` ([`CImageReferrerPolicy`](#image-interface-referrer-policy)) | `None` | Selects the native image request referrer policy. |
| <span id="image-input-cimage-server-inputs-fit"></span>`fit` | `"contain" | "cover" | "fill" | "none" | "scale-down"` ([`CImageFit`](#image-interface-fit)) | `"contain"` | Sets effective object fit and the root mirror. |
| <span id="image-input-cimage-server-inputs-position"></span>`position` | `str` | `"50% 50%"` | Sets validated object-position text; the browser owns final CSS grammar. |
| <span id="image-input-cimage-server-inputs-draggable"></span>`draggable` | `bool` | `False` | Sets the exact native draggable reflection. |
| <span id="image-input-cimage-server-inputs-on-status-change"></span>`onStatusChange` | `browser callback | None` | `None` | Sets the owner-local normalized status callback. |
| <span id="image-input-cimage-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#image-interface-class-value)) | `None` | Adds root classes and merges them with attrs. |
| <span id="image-input-cimage-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#image-interface-style-value)) | `None` | Adds root styles and merges them with attrs before owned style fallbacks. |
| <span id="image-input-cimage-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed neutral-root attributes and isolated-scope native listeners. |
| <span id="image-input-cimage-server-inputs-img-attrs"></span>`img_attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed native image attributes and load or error listeners without replacing owned resources, semantics, dimensions, or policy. |

</div>

#### CImage client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CImage />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 16rem; --ui-api-column-3-width: 15rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="image-input-cimage-client-inputs-src"></span>`src` | `str` | Uses the immutable server baseline; null has the same effect. | Replaces the fallback URL and begins a new request generation. |
| <span id="image-input-cimage-client-inputs-alt"></span>`alt` | `str` | Uses the immutable server baseline; null has the same effect. | Updates the native alternative without creating a second semantic owner. |
| <span id="image-input-cimage-client-inputs-width"></span>`width` | `positive integer` | Uses the immutable server baseline; null has the same effect. | Updates native intrinsic width. |
| <span id="image-input-cimage-client-inputs-height"></span>`height` | `positive integer` | Uses the immutable server baseline; null has the same effect. | Updates native intrinsic height. |
| <span id="image-input-cimage-client-inputs-srcset"></span>`srcset` | `string | null` | Uses the immutable server baseline. | Updates final-image candidates and begins a new request generation when effective selection metadata changes. |
| <span id="image-input-cimage-client-inputs-sizes"></span>`sizes` | `string | null` | Uses the immutable server baseline. | Updates final-image sizes and request selection. |
| <span id="image-input-cimage-client-inputs-loading"></span>`loading` | `"eager" | "lazy"` ([`CImageLoading`](#image-interface-loading)) | Uses the immutable server baseline; null has the same effect. | Updates the native loading hint without fabricating settlement. |
| <span id="image-input-cimage-client-inputs-decoding"></span>`decoding` | `"auto" | "sync" | "async"` ([`CImageDecoding`](#image-interface-decoding)) | Uses the immutable server baseline; null has the same effect. | Updates the native decoding hint. |
| <span id="image-input-cimage-client-inputs-fetch-priority"></span>`fetchPriority` | `"auto" | "high" | "low"` ([`CImageFetchPriority`](#image-interface-fetch-priority)) | Uses the immutable server baseline; null has the same effect. | Updates native fetch priority. |
| <span id="image-input-cimage-client-inputs-cross-origin"></span>`crossOrigin` | `CImageCrossOrigin | null` ([`CImageCrossOrigin`](#image-interface-cross-origin)) | Uses the immutable server baseline. | Updates or clears native CORS mode before a resource write. |
| <span id="image-input-cimage-client-inputs-referrer-policy"></span>`referrerPolicy` | `CImageReferrerPolicy | null` ([`CImageReferrerPolicy`](#image-interface-referrer-policy)) | Uses the immutable server baseline. | Updates or clears native referrer policy before a resource write. |
| <span id="image-input-cimage-client-inputs-fit"></span>`fit` | `"contain" | "cover" | "fill" | "none" | "scale-down"` ([`CImageFit`](#image-interface-fit)) | Uses the immutable server baseline; null has the same effect. | Updates object fit and the root reflection. |
| <span id="image-input-cimage-client-inputs-position"></span>`position` | `string` | Uses the immutable server baseline; null has the same effect. | Updates validated object-position text. |
| <span id="image-input-cimage-client-inputs-draggable"></span>`draggable` | `boolean` | Uses the immutable server baseline; null has the same effect. | Updates native draggable. |
| <span id="image-input-cimage-client-inputs-on-status-change"></span>`onStatusChange` | `function` | Uses the server callback. | Replaces the owner-local normalized status callback; null clears it. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CImage slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="image-slot-cimage-slots-placeholder"></span>`placeholder` | no | `none` | No custom loading layer; native pending rendering remains visible. |
| <span id="image-slot-cimage-slots-fallback"></span>`fallback` | no | `none` | No custom error layer; native broken-image rendering and alt remain visible. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CImage events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="image-event-cimage-events-status-change"></span>`onStatusChange` | `(detail: CImageStatusChangeDetail) => void` ([`CImageStatusChangeDetail`](#image-interface-cimage-status-change-detail)) | Initial loading ownership, a new accepted request generation, cached completion, or matching trusted native success or error settlement for a selected currentSrc change. | `{status, src, current_src, natural_width, natural_height}` ([`CImageStatusChangeDetail`](#image-interface-cimage-status-change-detail)) | Runs after native attributes and public mirrors synchronize; it is not cancelable and stale generations cannot notify. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CImage CSS variables

Apply these variables to `CImage` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="image-css-cimage-css-variables-aspect-ratio"></span>`--cui-image-aspect-ratio` | `positive CSS ratio or auto` | Overrides the rendered native image ratio without changing intrinsic metadata. | `auto` |
| <span id="image-css-cimage-css-variables-fit"></span>`--cui-image-fit` | `object-fit value` | Overrides the effective fit input for pixels inside the media box. | `Effective fit input` |
| <span id="image-css-cimage-css-variables-position"></span>`--cui-image-position` | `object-position value` | Overrides effective pixel position inside the media box. | `Effective position input` |
| <span id="image-css-cimage-css-variables-radius"></span>`--cui-image-radius` | `length or percentage` | Media box corner radius. | `var(--cui-radius-md)` |
| <span id="image-css-cimage-css-variables-background"></span>`--cui-image-background` | `color or image` | Loading and native contain-area background. | `transparent` |
| <span id="image-css-cimage-css-variables-fallback-color"></span>`--cui-image-fallback-color` | `color` | Visual fallback foreground. | `var(--cui-color-muted-fg)` |
| <span id="image-css-cimage-css-variables-fallback-background"></span>`--cui-image-fallback-background` | `color or image` | Visual fallback background. | `var(--cui-color-muted-bg)` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CImage attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="image-attribute-cimage-root-attributes-data-status"></span>`data-status` | Image root | `"loading" | "loaded" | "error"` ([`CImageStatus`](#image-interface-status)) | Mirrors the last accepted normalized status after readiness; a silent browser candidate change does not invent settlement. |
| <span id="image-attribute-cimage-root-attributes-data-fit"></span>`data-fit` | Image root | `"contain" | "cover" | "fill" | "none" | "scale-down"` ([`CImageFit`](#image-interface-fit)) | Mirrors effective configured fit before a public CSS variable override. |
| <span id="image-attribute-cimage-root-attributes-data-has-placeholder"></span>`data-has-placeholder` | Image root | `present | absent` | Reports whether placeholder slot content exists. |
| <span id="image-attribute-cimage-root-attributes-data-has-fallback"></span>`data-has-fallback` | Image root | `present | absent` | Reports whether fallback slot content exists. |
| <span id="image-attribute-cimage-root-attributes-readiness"></span>`data-citry-image-initialized` | Image root | `present | absent` | Marks a live settled runtime owner; the copyable attribute alone is not authority. |

</div>

#### CImage attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="image-attribute-cimage-native-attributes-alt"></span>`alt` | Native img | `string` | Required native alternative text and sole image semantic name. |
| <span id="image-attribute-cimage-native-attributes-width"></span>`width` | Native img or source | `positive integer` | Native intrinsic width metadata. |
| <span id="image-attribute-cimage-native-attributes-height"></span>`height` | Native img or source | `positive integer` | Native intrinsic height metadata. |
| <span id="image-attribute-cimage-native-attributes-src"></span>`src` | Native img | `nonempty URL string` | Required fallback request URL. |
| <span id="image-attribute-cimage-native-attributes-srcset"></span>`srcset` | Native img or source | `native candidate string` | Browser-owned responsive candidate set. |
| <span id="image-attribute-cimage-native-attributes-sizes"></span>`sizes` | Native img or source | `native sizes string` | Browser-owned rendered-size hint. |
| <span id="image-attribute-cimage-native-attributes-media"></span>`media` | Native source | `media query string` | Browser-owned art-direction discriminator. |
| <span id="image-attribute-cimage-native-attributes-type"></span>`type` | Native source | `image MIME essence` | Browser-owned format discriminator. |
| <span id="image-attribute-cimage-native-attributes-loading"></span>`loading` | Native img | `"eager" | "lazy"` ([`CImageLoading`](#image-interface-loading)) | Native request scheduling hint. |
| <span id="image-attribute-cimage-native-attributes-decoding"></span>`decoding` | Native img | `"auto" | "sync" | "async"` ([`CImageDecoding`](#image-interface-decoding)) | Native decode scheduling hint. |
| <span id="image-attribute-cimage-native-attributes-fetchpriority"></span>`fetchpriority` | Native img | `"auto" | "high" | "low"` ([`CImageFetchPriority`](#image-interface-fetch-priority)) | Native relative fetch-priority hint. |
| <span id="image-attribute-cimage-native-attributes-crossorigin"></span>`crossorigin` | Native img | `"anonymous" | "use-credentials" | absent` ([`CImageCrossOrigin`](#image-interface-cross-origin)) | Native CORS request mode. |
| <span id="image-attribute-cimage-native-attributes-referrerpolicy"></span>`referrerpolicy` | Native img | `CImageReferrerPolicy | absent` ([`CImageReferrerPolicy`](#image-interface-referrer-policy)) | Native request referrer policy. |
| <span id="image-attribute-cimage-native-attributes-draggable"></span>`draggable` | Native img | `"true" | "false"` | Exact native drag reflection. |
| <span id="image-attribute-cimage-native-attributes-slot-hidden"></span>`hidden` | Placeholder or fallback wrapper | `present in server output` | Keeps custom visual layers from obscuring native no-JavaScript output. |
| <span id="image-attribute-cimage-native-attributes-slot-aria-hidden"></span>`aria-hidden` | Placeholder or fallback wrapper | `"true"` | Keeps visual slot copy out of the accessibility tree. |
| <span id="image-attribute-cimage-native-attributes-slot-inert"></span>`inert` | Placeholder or fallback wrapper | `present` | Prevents visual slot descendants from becoming interaction surfaces. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CImage selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="image-selector-cimage-selectors-image-root"></span>`[data-citry-ui-part="image-root"]` | Neutral root span | Lifecycle owner and class_, style, and attrs destination. |
| <span id="image-selector-cimage-selectors-picture"></span>`[data-citry-ui-part="picture"]` | Native picture | Ordered responsive source-selection context present only when sources is nonempty. |
| <span id="image-selector-cimage-selectors-image"></span>`[data-citry-ui-part="image"]` | Sole native img | Semantic and request owner plus img_attrs destination. |
| <span id="image-selector-cimage-selectors-placeholder"></span>`[data-citry-ui-part="placeholder"]` | Inert visual span | Optional loading-only visual layer. |
| <span id="image-selector-cimage-selectors-fallback"></span>`[data-citry-ui-part="fallback"]` | Inert visual span | Optional error-only visual layer. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="image-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="image-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="image-interface-fit"></span>`CImageFit` | `Literal["contain", "cover", "fill", "none", "scale-down"]` |
| <span id="image-interface-loading"></span>`CImageLoading` | `Literal["eager", "lazy"]` |
| <span id="image-interface-decoding"></span>`CImageDecoding` | `Literal["auto", "sync", "async"]` |
| <span id="image-interface-fetch-priority"></span>`CImageFetchPriority` | `Literal["auto", "high", "low"]` |
| <span id="image-interface-cross-origin"></span>`CImageCrossOrigin` | `Literal["anonymous", "use-credentials"]` |
| <span id="image-interface-referrer-policy"></span>`CImageReferrerPolicy` | `Literal["no-referrer", "no-referrer-when-downgrade", "origin", "origin-when-cross-origin", "same-origin", "strict-origin", "strict-origin-when-cross-origin", "unsafe-url"]` |
| <span id="image-interface-status"></span>`CImageStatus` | `Literal["loading", "loaded", "error"]` |

</div>

<span id="image-interface-cimage-source"></span>

#### `CImageSource`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="image-interface-cimage-source-srcset"></span>`srcset` | `str` | - | Required native candidate string for one ordered source. |
| <span id="image-interface-cimage-source-media"></span>`media` | `str | None` | - | Optional native media discriminator. |
| <span id="image-interface-cimage-source-type"></span>`type` | `str | None` | - | Optional image MIME essence discriminator. |
| <span id="image-interface-cimage-source-sizes"></span>`sizes` | `str | None` | - | Optional native source sizes; required for width descriptors. |
| <span id="image-interface-cimage-source-width"></span>`width` | `positive int | None` | - | Optional native source width paired with height. |
| <span id="image-interface-cimage-source-height"></span>`height` | `positive int | None` | - | Optional native source height paired with width. |

</div>

<span id="image-interface-cimage-status-change-detail"></span>

#### `CImageStatusChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="image-interface-cimage-status-change-detail-status"></span>`status` | `CImageStatus` ([`CImageStatus`](#image-interface-status)) | - | Accepted normalized loading, loaded, or error state at callback time. |
| <span id="image-interface-cimage-status-change-detail-src"></span>`src` | `string` | - | Current authored fallback URL snapshot. |
| <span id="image-interface-cimage-status-change-detail-current-src"></span>`current_src` | `string` | - | Browser-selected absolute URL snapshot, which may be sensitive. |
| <span id="image-interface-cimage-status-change-detail-natural-width"></span>`natural_width` | `integer` | - | Native selected resource width, including zero for pending, error, or valid zero-size resources. |
| <span id="image-interface-cimage-status-change-detail-natural-height"></span>`natural_height` | `integer` | - | Native selected resource height, including zero for pending, error, or valid zero-size resources. |

</div>

### Translation keys

-