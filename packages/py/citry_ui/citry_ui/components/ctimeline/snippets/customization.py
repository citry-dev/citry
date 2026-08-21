import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimelineCustomization(Component):
    template = """
      <div class="custom-timeline">
        <c-CTimeline label="Team activity"
          c-style="{'--cui-timeline-indicator-size':'2rem','--cui-timeline-track-size':'2.75rem'}">
          <c-CTimelineItem>
            <c-fill name="indicator"><span class="avatar">AK</span></c-fill>
            <c-fill name="default">
              <strong>Ada assigned the issue</strong><br />Ownership moved to Platform.
            </c-fill>
          </c-CTimelineItem>
          <c-CTimelineItem state="current">
            <c-fill name="indicator"><span class="avatar">JM</span></c-fill>
            <c-fill name="default">
              <strong>Jules is investigating</strong><br />Current work is linked in the incident log.
            </c-fill>
          </c-CTimelineItem>
        </c-CTimeline>
      </div>
    """
    css = """
      :where(.custom-timeline) { --cui-timeline-current-color:#7c3aed; }
      :where(.custom-timeline .avatar) {
        display:grid;
        inline-size:100%;
        block-size:100%;
        place-items:center;
        border-radius:50%;
        background:currentcolor;
        color:Canvas;
        font-size:.65rem;
        font-weight:800;
      }
    """


preview = TimelineCustomization()
preview  # noqa: B018
