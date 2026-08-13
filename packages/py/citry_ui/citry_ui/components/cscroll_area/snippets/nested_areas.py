import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaNestedAreas(Component):
    template = """
      <section class="scroll-area-nested" x-data="{direction:'ltr'}">
        <h2>Operations document</h2>
        <p>
          The outer document and inner inspector are separate native scroll
          containers. Tab order and gesture targeting stay with the browser.
        </p>
        <button
          type="button"
          @click="direction=direction === 'ltr' ? 'rtl' : 'ltr'"
        >Flip document direction</button>
        <div :dir="direction">
          <c-CScrollArea
            overscroll="auto"
            style="--cui-scroll-area-max-block-size: 20rem"
          >
            <div class="scroll-area-nested__document">
            <p>
              The deployment plan contains enough content to scroll before
              and after the nested inspector.
            </p>
            <p>
              Review the service boundary, owner, and current policy before
              continuing to the approval section.
            </p>

              <c-CScrollArea
                aria_label="Service inspector"
                overscroll="contain"
                style="--cui-scroll-area-max-block-size: 10rem"
              >
                <dl class="scroll-area-nested__inspector">
                <dt>Service</dt><dd>Ledger export</dd>
                <dt>Owner</dt><dd>Finance platform</dd>
                <dt>Region</dt><dd>Central Europe</dd>
                <dt>Status</dt><dd>Needs approval</dd>
                <dt>Retention</dt><dd>Seven years</dd>
                <dt>Encryption</dt><dd>Customer managed</dd>
                <dt>Review</dt><dd>Quarterly</dd>
                </dl>
              </c-CScrollArea>

              <c-CScrollArea axis="inline" overscroll="none">
                <div class="scroll-area-nested__rail">
                  <span>Plan</span><span>Build</span><span>Review</span>
                  <span>Approve</span><span>Release</span>
                </div>
              </c-CScrollArea>

            <p>
              Continue through the remaining deployment notes after leaving
              the inspector.
            </p>
            <p>
              The outer viewport does not register the inner viewport as a
              widget or arbitrate its gestures.
            </p>
            <p>
              Real wheel, precision trackpad, and touch behavior remains a
              platform acceptance check.
            </p>
            </div>
          </c-CScrollArea>
        </div>
      </section>
    """

    css = """
      :where(.scroll-area-nested) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 40rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-nested h2, .scroll-area-nested p) {
        margin: 0;
      }

      :where(.scroll-area-nested > button) {
        justify-self: start;
      }

      :where(.scroll-area-nested__document) {
        display: grid;
        gap: 1.5rem;
        padding: 1rem;
      }

      :where(.scroll-area-nested__inspector) {
        display: grid;
        grid-template-columns: max-content 1fr;
        gap: 0.625rem 1rem;
        margin: 0;
        padding: 1rem;
      }

      :where(.scroll-area-nested__inspector dt) {
        font-weight: 700;
      }

      :where(.scroll-area-nested__inspector dd) {
        margin: 0;
      }

      :where(.scroll-area-nested__rail) {
        display: flex;
        inline-size: max-content;
        gap: 0.75rem;
        padding: 1rem;
      }

      :where(.scroll-area-nested__rail span) {
        min-inline-size: 7rem;
        padding: 0.5rem;
        background: color-mix(in srgb, Highlight 12%, Canvas);
      }
    """


preview = ScrollAreaNestedAreas()

preview  # noqa: B018
