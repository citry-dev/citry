import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimelineStatus(Component):
    template = """
      <c-CTimeline label="Deployment status" line_style="dashed">
        <c-CTimelineItem state="complete">
          <strong>Build completed</strong><br />Artifacts signed successfully
        </c-CTimelineItem>
        <c-CTimelineItem state="error">
          <strong>Staging failed</strong><br />Health check timed out
        </c-CTimelineItem>
        <c-CTimelineItem state="current">
          <strong>Retry in progress</strong><br />Current attempt is running
        </c-CTimelineItem>
        <c-CTimelineItem state="pending">
          <strong>Production pending</strong><br />Waiting for staging approval
        </c-CTimelineItem>
      </c-CTimeline>
    """


preview = TimelineStatus()
preview  # noqa: B018
