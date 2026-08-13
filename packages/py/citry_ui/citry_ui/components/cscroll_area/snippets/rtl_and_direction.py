import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaRtlAndDirection(Component):
    template = """
      <section
        class="scroll-area-direction"
        x-data="{
          direction:'ltr',
          ltrOffset:0,
          rtlOffset:0,
          flipOffset:0,
        }"
      >
        <div class="scroll-area-direction__controls">
          <button
            type="button"
            @click="direction=direction === 'ltr' ? 'rtl' : 'ltr'"
          >Flip the third rail</button>
          <output x-text="`Third rail direction: ${direction}`">
            Third rail direction: ltr
          </output>
        </div>

        <div class="scroll-area-direction__grid">
          <article dir="ltr">
            <h3>LTR</h3>
            <c-CScrollArea
              axis="inline"
              aria_label="LTR deployment stages"
              $c-props="{
                onScrollChange:(detail)=>
                  ltrOffset=Math.round(detail.inlineOffset),
              }"
            >
              <div class="scroll-area-direction__rail">
                <span>Plan</span><span>Build</span><span>Review</span>
                <span>Approve</span><span>Publish</span><span>Archive</span>
              </div>
            </c-CScrollArea>
            <output x-text="`Logical offset ${ltrOffset}`">
              Logical offset 0
            </output>
          </article>

          <article dir="rtl">
            <h3>RTL</h3>
            <c-CScrollArea
              axis="inline"
              aria_label="مراحل النشر"
              $c-props="{
                onScrollChange:(detail)=>
                  rtlOffset=Math.round(detail.inlineOffset),
              }"
            >
              <div class="scroll-area-direction__rail">
                <span>تخطيط</span><span>بناء</span><span>مراجعة</span>
                <span>موافقة</span><span>نشر</span><span>أرشفة</span>
              </div>
            </c-CScrollArea>
            <output x-text="`Logical offset ${rtlOffset}`">
              Logical offset 0
            </output>
          </article>

          <article :dir="direction">
            <h3>Direction change</h3>
            <c-CScrollArea
              axis="inline"
              aria_label="Direction-changing stages"
              $c-props="{
                onScrollChange:(detail)=>
                  flipOffset=Math.round(detail.inlineOffset),
              }"
            >
              <div class="scroll-area-direction__rail">
                <span>North</span><span>South</span><span>East</span>
                <span>West</span><span>Coast</span><span>Harbor</span>
              </div>
            </c-CScrollArea>
            <output x-text="`Logical offset ${flipOffset}`">
              Logical offset 0
            </output>
          </article>
        </div>
      </section>
    """

    css = """
      :where(.scroll-area-direction) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-direction__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
      }

      :where(.scroll-area-direction__grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
      }

      :where(.scroll-area-direction article) {
        display: grid;
        gap: 0.5rem;
        min-inline-size: 0;
      }

      :where(.scroll-area-direction h3) {
        margin: 0;
      }

      :where(.scroll-area-direction__rail) {
        display: flex;
        inline-size: max-content;
        gap: 0.75rem;
        padding: 1rem;
      }

      :where(.scroll-area-direction__rail span) {
        min-inline-size: 7rem;
        padding: 0.625rem;
        border-radius: 0.5rem;
        background: color-mix(in srgb, Highlight 12%, Canvas);
        text-align: center;
      }
    """


preview = ScrollAreaRtlAndDirection()

preview  # noqa: B018
