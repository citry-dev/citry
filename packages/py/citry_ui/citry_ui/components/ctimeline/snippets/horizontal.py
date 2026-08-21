import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimelineHorizontal(Component):
    template = """
      <c-CTimeline label="2026 roadmap" orientation="horizontal" side="alternate" size="lg">
        <c-CTimelineItem state="complete"><strong>Q1</strong><br />Unified accounts</c-CTimelineItem>
        <c-CTimelineItem state="complete"><strong>Q2</strong><br />Regional storage</c-CTimelineItem>
        <c-CTimelineItem state="current"><strong>Q3</strong><br />Audit workspaces</c-CTimelineItem>
        <c-CTimelineItem state="pending"><strong>Q4</strong><br />Policy automation</c-CTimelineItem>
      </c-CTimeline>
    """


preview = TimelineHorizontal()
preview  # noqa: B018
