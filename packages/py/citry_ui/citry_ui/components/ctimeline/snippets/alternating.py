import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimelineAlternating(Component):
    template = """
      <c-CTimeline label="Product history" side="alternate">
        <c-CTimelineItem state="complete">
          <strong>Prototype</strong><p>The first field trial validated the core workflow.</p>
        </c-CTimelineItem>
        <c-CTimelineItem state="complete">
          <strong>Private beta</strong><p>Design partners shaped the collaboration model.</p>
        </c-CTimelineItem>
        <c-CTimelineItem state="current">
          <strong>Public beta</strong><p>The current release focuses on reliability and polish.</p>
        </c-CTimelineItem>
        <c-CTimelineItem state="pending">
          <strong>General availability</strong><p>Operational review and migration guidance remain.</p>
        </c-CTimelineItem>
      </c-CTimeline>
    """
    css = ":where(.cui-timeline__content p){margin:.25rem 0 0}"


preview = TimelineAlternating()
preview  # noqa: B018
