"""Shared Image scenario used by repository quality tools."""

from __future__ import annotations

from typing import Any

from citry import Citry, Component
from citry_ui import CImageSource

_ASSET = "https://images.citry.test/northstar"
_CROSS_ASSET = "https://cross-origin.citry.test/northstar"


def image_states_component(app: Citry) -> type[Component]:
    """Create the reusable native-image, delivery, and lifecycle scenario."""

    class CitryUiImageStates(Component):
        citry = app

        class Kwargs:
            morph_step: int = 0

        class State(Kwargs):
            pass

        class Slots:
            pass

        class Events:
            def refresh(self, state: Any) -> CitryUiImageStates:
                state.morph_step += 1
                component_type: Any = CitryUiImageStates
                return component_type(morph_step=state.morph_step)

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            source = f"{_ASSET}/horsehead-1280.jpg?generation=baseline"
            if kwargs.morph_step >= 2:
                source = f"{_ASSET}/orion-1280.jpg?generation=changed"
            lifecycle_key = (
                "image-quality-retained" if kwargs.morph_step < 3 else f"image-quality-replacement-{kwargs.morph_step}"
            )
            return {
                "blocked_asset": "https://blocked-images.citry.test/northstar/blocked.jpg",
                "cross_asset": f"{_CROSS_ASSET}/observatory-1280.jpg",
                "include_lifecycle": kwargs.morph_step not in {4, 6},
                "lifecycle_key": lifecycle_key,
                "lifecycle_source": source,
                "morph_step": kwargs.morph_step,
                "orion": f"{_ASSET}/orion-1280.jpg",
                "orion_small": f"{_ASSET}/orion-640.jpg",
                "horsehead": f"{_ASSET}/horsehead-1280.jpg",
                "missing": f"{_ASSET}/missing.jpg",
                "native_image_attrs": {
                    "@load": "$dispatch('quality-image-native-load')",
                    "@error": "$dispatch('quality-image-native-error')",
                },
                "responsive_sources": (
                    CImageSource(
                        media="(max-width: 47.99rem)",
                        srcset=f"{_ASSET}/observatory-portrait-640.jpg 640w",
                        sizes="(max-width: 48rem) 100vw, 48rem",
                        width=640,
                        height=960,
                    ),
                    CImageSource(
                        media="(min-width: 64rem)",
                        type="image/avif",
                        srcset=f"{_ASSET}/observatory-1280.avif 1280w",
                        sizes="(max-width: 48rem) 100vw, 48rem",
                        width=1280,
                        height=720,
                    ),
                ),
                "responsive_src": f"{_ASSET}/observatory-1280.jpg",
                "responsive_srcset": (
                    f"{_ASSET}/observatory-portrait-640.jpg 640w, {_ASSET}/observatory-1280.jpg 1280w"
                ),
            }

        template = """
          <section
            class="citry-ui-quality-stack image-quality"
            aria-labelledby="image-quality-title"
            x-data="{
              reactiveSource:null,
              reactiveStatus:'waiting',
              reactiveSelected:'none',
              reactiveCallbacks:0,
              nativeLoads:0,
              nativeErrors:0,
              lifecycleStatus:'waiting',
              lifecycleCallbacks:0,
              redact:(value)=>value ? value.split('/').pop().split('?')[0] : 'none',
            }"
            @c-quality-morph="refresh"
            @quality-image-native-load="nativeLoads++"
            @quality-image-native-error="nativeErrors++"
          >
            <h1 id="image-quality-title">Image states</h1>
            <output hidden data-quality-morph-step>{{ morph_step }}</output>

            <div class="citry-ui-quality-grid">
              <article>
                <h2>Informative native image</h2>
                <c-CImage
                  c-src="orion"
                  alt="Orion Nebula, captured from Northstar Ridge"
                  c-width="1280"
                  c-height="720"
                  loading="eager"
                  fetch_priority="high"
                  c-attrs="{
                    'id':'quality-image-basic',
                    'data-quality-states':
                      'informative native alt geometry loading eager priority current-src cached '
                      + 'no-js light dark rtl zoom-200 zoom-400',
                  }"
                />
              </article>

              <article>
                <h2>Below-fold native loading</h2>
                <c-CImage
                  c-src="orion_small"
                  alt="Northstar archive thumbnail"
                  c-width="640"
                  c-height="360"
                  loading="lazy"
                  decoding="async"
                  fetch_priority="auto"
                  c-attrs="{
                    'id':'quality-image-lazy',
                    'data-quality-states':'lazy decoding auto below-fold',
                  }"
                />
              </article>

              <article>
                <h2>Decorative image</h2>
                <c-CImage
                  c-src="orion_small"
                  c-alt="''"
                  c-width="640"
                  c-height="360"
                  c-attrs="{
                    'id':'quality-image-decorative',
                    'data-quality-states':'decorative empty-alt semantics native-context drag-disabled',
                  }"
                />
              </article>

              <article>
                <h2>Responsive art direction</h2>
                <c-CImage
                  c-src="responsive_src"
                  alt="Northstar Observatory beneath the Milky Way"
                  c-width="1280"
                  c-height="720"
                  c-srcset="responsive_srcset"
                  sizes="(max-width: 48rem) 100vw, 48rem"
                  c-sources="responsive_sources"
                  c-attrs="{
                    'id':'quality-image-responsive',
                    'data-quality-states':
                      'responsive picture source-order srcset sizes media type avif '
                      + 'candidate-switch dpr narrow wide',
                  }"
                />
              </article>

              <article>
                <h2>Fit and public styling</h2>
                <c-CImage
                  c-src="horsehead"
                  alt="Horsehead Nebula in a square crop"
                  c-width="1280"
                  c-height="720"
                  fit="cover"
                  position="35% 50%"
                  class_="image-quality__crop"
                  c-style="{'--cui-image-radius':'1rem'}"
                  c-img_attrs="{'class':'image-quality__pixels','title':'Northstar archive crop'}"
                  c-attrs="{
                    'id':'quality-image-fit',
                    'data-quality-states':
                      'fit position aspect-ratio variables selectors class style img-attrs '
                      + 'forced-colors print reduced-motion',
                  }"
                />
              </article>
            </div>

            <div class="citry-ui-quality-grid">
              <article>
                <h2>Placeholder and fallback</h2>
                <c-CImage
                  c-src="missing"
                  alt="Unavailable Northstar archive plate"
                  c-width="1280"
                  c-height="720"
                  c-attrs="{
                    'id':'quality-image-error',
                    'data-quality-states':
                      'placeholder fallback error inert aria-hidden alt-retained recovery '
                      + 'no-transition print-fallback',
                  }"
                >
                  <c-fill name="placeholder"><c-CSkeleton height="100%" animation="wave" /></c-fill>
                  <c-fill name="fallback"><span>Archive plate unavailable</span></c-fill>
                </c-CImage>
              </article>

              <article>
                <h2>Reactive and native events</h2>
                <div class="image-quality__actions">
                  <button
                    type="button"
                    @click="reactiveSource='https://images.citry.test/northstar/horsehead-1280.jpg?frame=a'"
                  >Frame A</button>
                  <button
                    type="button"
                    @click="reactiveSource='https://images.citry.test/northstar/orion-1280.jpg?frame=b'"
                  >Frame B</button>
                  <button
                    type="button"
                    @click="reactiveSource='https://images.citry.test/northstar/missing.jpg?frame=broken'"
                  >Broken</button>
                  <button
                    type="button"
                    @click="
                      reactiveSource='https://images.citry.test/northstar/horsehead-1280.jpg?frame=rapid-a';
                      queueMicrotask(
                        ()=>reactiveSource='https://images.citry.test/northstar/orion-640.jpg?frame=rapid-b'
                      );
                    "
                  >Rapid A then B</button>
                </div>
                <c-CImage
                  c-src="horsehead"
                  alt="Live survey frame"
                  c-width="1280"
                  c-height="720"
                  c-img_attrs="native_image_attrs"
                  c-attrs="{
                    'id':'quality-image-reactive',
                    'data-quality-states':
                      'reactive client-props callback native-events isolated-scope dispatch '
                      + 'rapid supersession stale-events redacted cached shadow-root',
                  }"
                  $c-props="{
                    src:reactiveSource,
                    onStatusChange:(detail)=>{
                      reactiveCallbacks++;
                      reactiveStatus=detail.status;
                      reactiveSelected=redact(detail.current_src || detail.src);
                    },
                  }"
                >
                  <c-fill name="fallback">Live frame unavailable</c-fill>
                </c-CImage>
                <output
                  id="quality-image-reactive-output"
                  x-text="`${reactiveStatus}|${reactiveSelected}|${reactiveCallbacks}|${nativeLoads}|${nativeErrors}`"
                >waiting|none|0|0|0</output>
                <div id="quality-image-shadow-host"></div>
              </article>

              <article>
                <h2>Delivery policy</h2>
                <c-CImage
                  c-src="cross_asset"
                  alt="Cross-origin Northstar Observatory plate"
                  c-width="1280"
                  c-height="720"
                  cross_origin="anonymous"
                  referrer_policy="no-referrer"
                  c-attrs="{
                    'id':'quality-image-delivery',
                    'data-quality-states':
                      'cors anonymous referrer-policy csp cross-origin privacy '
                      + 'data-url blob svg offline',
                  }"
                >
                  <c-fill name="fallback">Cross-origin plate unavailable</c-fill>
                </c-CImage>
                <output id="quality-image-request-summary">Safe request summary only</output>
                <c-CImage
                  c-src="blocked_asset"
                  alt="CSP-blocked Northstar archive plate"
                  c-width="1280"
                  c-height="720"
                  c-attrs="{
                    'id':'quality-image-csp',
                    'data-quality-states':'csp csp-blocked privacy error fallback',
                  }"
                >
                  <c-fill name="fallback">Archive policy blocked this plate</c-fill>
                </c-CImage>
              </article>
            </div>

            <article>
              <h2>Composition</h2>
              <div class="image-quality__composition">
                <c-CCard tag="article" variant="outline">
                  <c-fill name="media">
                    <c-CImage
                      c-src="orion_small"
                      alt="Orion Nebula archive card"
                      c-width="640"
                      c-height="360"
                      c-attrs="{'data-quality-states':'card skeleton figure link functional-alt composition focus'}"
                    />
                  </c-fill>
                  <c-fill name="header"><h3>Archive card</h3></c-fill>
                  <c-fill name="default">One native semantic image inside Card media.</c-fill>
                </c-CCard>
                <figure>
                  <a href="#quality-image-observation">
                    <c-CImage
                      c-src="horsehead"
                      alt="Open the full Horsehead Nebula observation"
                      c-width="1280"
                      c-height="720"
                      c-attrs="{'data-quality-states':'figure link functional-alt composition focus'}"
                    />
                  </a>
                  <figcaption>Exposure notes remain ordinary figure content.</figcaption>
                </figure>
              </div>
            </article>

            <article class="image-quality__lifecycle">
              <h2>Signed lifecycle</h2>
              <button type="button" @c-click="refresh">Advance signed image lifecycle</button>
              <c-if cond="include_lifecycle">
                <c-CImage
                  #c-key="lifecycle_key"
                  c-src="lifecycle_source"
                  alt="Nightly calibration plate"
                  c-width="1280"
                  c-height="720"
                  c-attrs="{
                    'id':'quality-image-lifecycle',
                    'data-quality-states':
                      'lifecycle morph-target retained-root resource-change replacement-root '
                      + 'removal restore second-removal second-restore cleanup owner-token clone '
                      + 'hostile-fail-closed listener-count observer-count readiness request-fingerprint '
                      + 'selection-fingerprint',
                  }"
                  $c-props="{
                    onStatusChange:(detail)=>{
                      lifecycleCallbacks++;
                      lifecycleStatus=detail.status;
                    },
                  }"
                >
                  <c-fill name="placeholder">Loading calibration plate</c-fill>
                  <c-fill name="fallback">Calibration plate unavailable</c-fill>
                </c-CImage>
              </c-if>
              <output id="quality-image-lifecycle-output" x-text="`${lifecycleStatus}|${lifecycleCallbacks}`">
                waiting|0
              </output>
            </article>
          </section>
        """

        css = """
          :where(.image-quality) {
            color: CanvasText;
            font-family: ui-sans-serif, system-ui, sans-serif;
          }
          :where(.image-quality article) { display: grid; gap: 0.75rem; align-content: start; }
          :where(.image-quality h1, .image-quality h2, .image-quality h3, .image-quality figure) {
            margin: 0;
          }
          :where(.image-quality [data-citry-ui-part="image-root"]) { inline-size: 100%; }
          :where(.image-quality__crop) { --cui-image-aspect-ratio: 1 / 1; }
          :where(.image-quality__actions) { display: flex; flex-wrap: wrap; gap: 0.5rem; }
          :where(.image-quality__composition) {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
            gap: 1rem;
          }
          :where(.image-quality a:focus-visible) { outline: 3px solid Highlight; outline-offset: 3px; }
          @media (forced-colors: active) {
            :where(.image-quality [data-citry-ui-part="fallback"]) { border: 1px solid CanvasText; }
          }
          @media print {
            :where(.image-quality button, .image-quality output) { display: none; }
          }
        """

    return CitryUiImageStates
