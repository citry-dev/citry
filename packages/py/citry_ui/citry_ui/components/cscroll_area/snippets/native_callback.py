import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaNativeCallback(Component):
    template = """
      <section
        class="scroll-area-callback"

        @scroll-area-native="nativeCount += 1"
        @scroll-area-settled="settled += 1"
      >
        <div class="scroll-area-callback__controls">
          <button type="button" @click="rows += 2">Add content</button>
          <button type="button" @click="rows = Math.max(1, rows - 2)">
            Remove content
          </button>
          <button type="button" @click="sentinelTop += 80">
            Move absolute marker
          </button>
          <button
            type="button"
            @click="setTimeout(()=>imageVisible=true,350)"
          >Load a delayed image</button>
          <button type="button" @click="expanded=!expanded">
            Toggle content stylesheet
          </button>
        </div>

        <c-CScrollArea
          axis="both"
          aria_label="Event-scoped audit log"
          style="--cui-scroll-area-max-block-size: 13rem"
          @scroll="
            $event.currentTarget.dispatchEvent(
              new $event.currentTarget.ownerDocument.defaultView.CustomEvent(
                'scroll-area-native', {bubbles:true}
              )
            )
          "
          @scrollend="
            $event.currentTarget.dispatchEvent(
              new $event.currentTarget.ownerDocument.defaultView.CustomEvent(
                'scroll-area-settled', {bubbles:true}
              )
            )
          "
          :onScrollChange="(detail)=>{
              callbackCount += 1;
              lastInline = Math.round(detail.inlineOffset);
              lastBlock = Math.round(detail.blockOffset);
            }"
        >
          <div
            class="scroll-area-callback__content"
            :class="{'scroll-area-callback__content--expanded':expanded}"
          >
            <template v-for="row in rows" :key="row">
              <p v-text="`Audit row ${row}: current native content`"></p>
            </template>
            <span
              class="scroll-area-callback__sentinel"
              :style="`inset-block-start:${sentinelTop}px`"
            >Absolute marker</span>
            <template v-if="imageVisible">
              <img
                class="scroll-area-callback__image"
                alt="Delayed audit chart"
                src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
              />
            </template>
            <div ref="shadowHost" class="scroll-area-callback__shadow-host">
              <div ref="shadowFixture">
                <p style="inline-size:26rem;min-block-size:5rem;padding:0.5rem">
                  Open ShadowRoot content changes native layout without creating
                  a component callback.
                </p>
              </div>
            </div>
          </div>
        </c-CScrollArea>

        <dl class="scroll-area-callback__readout">
          <dt>Native scroll events</dt><dd v-text="nativeCount">0</dd>
          <dt>Native scrollend events</dt><dd v-text="settled">0</dd>
          <dt>Component callbacks</dt><dd v-text="callbackCount">0</dd>
          <dt>Logical inline offset</dt><dd v-text="lastInline">0</dd>
          <dt>Block offset</dt><dd v-text="lastBlock">0</dd>
        </dl>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            rows:6,
            sentinelTop:150,
            imageVisible:false,
            expanded:false,
            nativeCount:0,
            settled:0,
            callbackCount:0,
            lastInline:0,
            lastBlock:0,
          };
        },
        mounted() {
          this.$nextTick(() => {
          const host = this.$refs.shadowHost;
          const fixture = this.$refs.shadowFixture;
          if (!host.shadowRoot && fixture) host.attachShadow({mode:'open'}).append(fixture);
          })
        },
      });
    """

    css = """
      :where(.scroll-area-callback) {
        display: grid;
        gap: 1rem;
        max-inline-size: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-callback__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.scroll-area-callback__content) {
        position: relative;
        inline-size: 44rem;
        min-block-size: 26rem;
        padding: 1rem;
      }

      :where(.scroll-area-callback__content--expanded) {
        min-block-size: 34rem;
      }

      :where(.scroll-area-callback__content p) {
        margin: 0 0 1rem;
      }

      :where(.scroll-area-callback__sentinel) {
        position: absolute;
        inset-inline-start: 28rem;
        padding: 0.375rem 0.625rem;
        border-radius: 0.375rem;
        background: color-mix(in srgb, Highlight 18%, Canvas);
      }

      :where(.scroll-area-callback__image) {
        display: block;
        inline-size: 30rem;
        block-size: 6rem;
        margin-block: 1rem;
        background: color-mix(in srgb, Highlight 14%, Canvas);
      }

      :where(.scroll-area-callback__shadow-host) {
        display: block;
        min-inline-size: 26rem;
        min-block-size: 5rem;
        border: 1px dashed GrayText;
      }

      :where(.scroll-area-callback__readout) {
        display: grid;
        grid-template-columns: max-content 1fr;
        gap: 0.375rem 1rem;
        margin: 0;
      }

      :where(.scroll-area-callback__readout dt) {
        font-weight: 700;
      }

      :where(.scroll-area-callback__readout dd) {
        margin: 0;
      }
    """


preview = ScrollAreaNativeCallback()

preview  # noqa: B018
