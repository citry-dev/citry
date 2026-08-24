from citry import Component

from ..citry_app import citry_app
from ..store import LaneView
from .badges import BadgeStyles  # noqa: F401 - registers the template component
from .board import ProjectBoard  # noqa: F401 - registers the template component
from .shell import AppShell  # noqa: F401 - registers the template component


class BoardPage(Component):
    citry = citry_app

    class Kwargs:
        lanes: tuple[LaneView, ...]

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"lanes": kwargs.lanes}

    template = """
      <c-AppShell c-title="'Launch workspace · Project Board'">
        <c-fill name="header">
          <section class="project-hero">
            <div>
              <p class="project-hero__eyebrow">Project Board demo</p>
              <h1>Launch workspace</h1>
              <p class="project-hero__summary">
                Keep the next useful decision visible, move work deliberately,
                and let the server own the records that matter.
              </p>
            </div>
            <dl class="project-hero__facts">
              <div><dt>Cycle</dt><dd>Autumn 2026</dd></div>
              <div><dt>Team</dt><dd>3 collaborators</dd></div>
              <div><dt>Status</dt><dd>In progress</dd></div>
            </dl>
          </section>
        </c-fill>
        <c-fill name="default">
          <div class="board-frame">
            <c-BadgeStyles />
            <c-ProjectBoard c-lanes="lanes" />
          </div>
        </c-fill>
      </c-AppShell>
    """

    css = """
      .project-hero {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: end;
        gap: 2rem;
        padding: clamp(2.5rem, 7vw, 5.5rem) clamp(1rem, 5vw, 4rem) 2.2rem;
        color: #f7f4eb;
        background:
          linear-gradient(125deg, rgb(26 65 48 / 0.97), rgb(45 73 60 / 0.91)),
          #244c39;
      }
      .project-hero__eyebrow {
        margin: 0 0 0.7rem;
        color: #f6b27b;
        font-size: 0.72rem;
        font-weight: 850;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }
      .project-hero h1 {
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        font-size: clamp(2.7rem, 8vw, 5.8rem);
        font-weight: 500;
        letter-spacing: -0.055em;
        line-height: 0.95;
      }
      .project-hero__summary {
        max-width: 44rem;
        margin: 1rem 0 0;
        color: #cdd8d1;
        font-size: 1.05rem;
        line-height: 1.6;
      }
      .project-hero__facts { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 1.4rem; margin: 0; }
      .project-hero__facts div { display: grid; gap: 0.2rem; }
      .project-hero__facts dt { color: #aabbb0; font-size: 0.68rem; text-transform: uppercase; }
      .project-hero__facts dd { margin: 0; font-size: 0.86rem; font-weight: 750; }
      .board-frame { width: min(86rem, calc(100% - 2rem)); margin: 0 auto; padding: 2rem 0 5rem; }
      @media (max-width: 48rem) {
        .project-hero { grid-template-columns: 1fr; }
        .project-hero__facts { justify-content: flex-start; }
      }
    """
