import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimelineAtAGlance(Component):
    template = """
      <c-CTimeline label="Shipment progress">
        <c-CTimelineItem state="complete">
          <c-fill name="opposite"><time datetime="2026-08-18">18 Aug</time></c-fill>
          <c-fill name="default"><strong>Order confirmed</strong><br />Payment received</c-fill>
        </c-CTimelineItem>
        <c-CTimelineItem state="current">
          <c-fill name="opposite"><time datetime="2026-08-21">Today</time></c-fill>
          <c-fill name="default"><strong>In transit</strong><br />Departed the regional hub</c-fill>
        </c-CTimelineItem>
        <c-CTimelineItem state="pending"><strong>Delivered</strong></c-CTimelineItem>
      </c-CTimeline>
    """


preview = TimelineAtAGlance()
preview  # noqa: B018
