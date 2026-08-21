import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimelineActivity(Component):
    template = """
      <c-CTimeline label="Repository activity" density="compact">
        <c-CTimelineItem>
          <c-fill name="opposite"><time datetime="2026-08-21T09:15:00Z">09:15</time></c-fill>
          <c-fill name="default">
            <strong>Mina opened pull request #184</strong><p>Improve invoice import diagnostics.</p>
          </c-fill>
        </c-CTimelineItem>
        <c-CTimelineItem>
          <c-fill name="opposite"><time datetime="2026-08-21T10:04:00Z">10:04</time></c-fill>
          <c-fill name="default"><strong>Leo approved the changes</strong><p>All required checks passed.</p></c-fill>
        </c-CTimelineItem>
        <c-CTimelineItem state="current">
          <c-fill name="opposite"><time datetime="2026-08-21T10:12:00Z">10:12</time></c-fill>
          <c-fill name="default">
            <strong>Ready to merge</strong><p><a href="#review">Review the final diff</a></p>
          </c-fill>
        </c-CTimelineItem>
      </c-CTimeline>
    """
    css = ":where(.cui-timeline__content p){margin:.25rem 0 0}"


preview = TimelineActivity()
preview  # noqa: B018
