"""Shared Timeline scenario used by repository quality tools."""

from citry import Citry, Component


def timeline_states_component(app: Citry) -> type[Component]:
    class CitryUiTimelineStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack timeline-quality" data-quality-timeline-ready>
            <h1>Timeline states</h1>
            <c-CTimeline label="Deployment history" side="alternate"
              c-attrs="{'data-quality-states':'vertical alternate complete current error custom-indicator md'}">
              <c-CTimelineItem state="complete">
                <c-fill name="opposite"><time datetime="2026-08-20">Yesterday</time></c-fill>
                <c-fill name="indicator"><span>1</span></c-fill>
                <c-fill name="default">
                  <strong>Build complete</strong><p>Signed artifacts are ready.</p>
                </c-fill>
              </c-CTimelineItem>
              <c-CTimelineItem state="error">
                <strong>Staging failed</strong><p>Health check timed out.</p>
              </c-CTimelineItem>
              <c-CTimelineItem state="current">
                <strong>Retry in progress</strong><p>Current deployment is running.</p>
              </c-CTimelineItem>
              <c-CTimelineItem state="pending">
                <strong>Production pending</strong><p>Longcontentwrapswithoutforcingthepageviewporttowiden.</p>
              </c-CTimelineItem>
              <c-CTimelineItem><strong>Audit retained</strong><p>Neutral event metadata.</p></c-CTimelineItem>
            </c-CTimeline>
            <div dir="rtl" style="color-scheme:dark">
              <c-CTimeline label="RTL compact history" density="compact" line_style="dashed" size="sm"
                c-attrs="{'data-quality-states':'rtl dark compact dashed sm'}">
                <c-CTimelineItem state="complete">اكتمل البناء</c-CTimelineItem>
                <c-CTimelineItem state="current">المراجعة الحالية</c-CTimelineItem>
              </c-CTimeline>
            </div>
            <c-CTimeline label="Horizontal roadmap" orientation="horizontal" side="alternate" size="lg"
              c-attrs="{'data-quality-states':'horizontal overflow alternate lg touch'}">
              <c-CTimelineItem state="complete">Research</c-CTimelineItem>
              <c-CTimelineItem state="current">Build</c-CTimelineItem>
              <c-CTimelineItem state="pending">Qualify</c-CTimelineItem>
              <c-CTimelineItem state="pending">Release</c-CTimelineItem>
            </c-CTimeline>
          </section>
        """
        css = """
          :where(.timeline-quality p){margin:.2rem 0 0}
          :where(.timeline-quality [dir="rtl"]){padding:1rem;background:#172033;color:#f8fafc}
        """

    return CitryUiTimelineStates


__all__ = ["timeline_states_component"]
