import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaActivityAndFocus(Component):
    template = """
      <section
        class="scroll-area-focus"
        x-data="{last:'Focus the viewport, a link, or an action'}"
        @activity-focus="last=$event.detail"
        @activity-blur="last=$event.detail"
      >
        <p>
          Tab enters the viewport before its descendants. Native scrolling
          keys keep focus on the viewport.
        </p>
        <c-CScrollArea
          aria_label="Deployment activity"
          style="--cui-scroll-area-max-block-size: 15rem"
          c-attrs="{
            '@focus':'$dispatch(`activity-focus`, `Focused ${$event.target.id}`)',
            '@blur':'$dispatch(`activity-blur`, `Left ${$event.target.id}`)',
          }"
          $c-props="{
            onScrollChange:(detail)=>
              last=`Block offset ${Math.round(detail.blockOffset)}`,
          }"
          id="deployment-activity"
        >
          <ol class="scroll-area-focus__timeline">
            <li>
              <strong>09:10</strong>
              <span>Build completed.</span>
              <a href="#build-details">View build details</a>
            </li>
            <li>
              <strong>09:18</strong>
              <span>Security review requested.</span>
              <c-CButton size="sm" variant="outline">Open review</c-CButton>
            </li>
            <li>
              <strong>09:26</strong>
              <span>Staging deployment completed.</span>
              <a href="#staging-log">Read staging log</a>
            </li>
            <li>
              <strong>09:42</strong>
              <span>Production approval received.</span>
              <c-CButton size="sm">Publish release</c-CButton>
            </li>
            <li>
              <strong>09:51</strong>
              <span>Release notes archived.</span>
              <a href="#release-notes">Open release notes</a>
            </li>
          </ol>
        </c-CScrollArea>
        <output x-text="last">Focus the viewport, a link, or an action</output>
      </section>
    """

    css = """
      :where(.scroll-area-focus) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-focus p, .scroll-area-focus output) {
        margin: 0;
      }

      :where(.scroll-area-focus__timeline) {
        display: grid;
        gap: 1rem;
        margin: 0;
        padding: 1rem 1rem 1rem 2.5rem;
      }

      :where(.scroll-area-focus__timeline li) {
        display: grid;
        grid-template-columns: 4rem 1fr;
        gap: 0.375rem 0.75rem;
        align-items: center;
      }

      :where(.scroll-area-focus__timeline li > :not(strong)) {
        grid-column: 2;
      }
    """


preview = ScrollAreaActivityAndFocus()

preview  # noqa: B018
