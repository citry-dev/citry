from app.citry_app import citry_app
from app.store import LaneView
from citry import Component


class BoardPage(Component):
    citry = citry_app

    class Kwargs:
        lanes: tuple[LaneView, ...]

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"lanes": kwargs.lanes}

    template = """
      <c-AppShell c-title="'Project Board | Citry demo'">
        <c-fill name="header">
          <section class="project-hero">
            <div>
              <p class="project-hero__eyebrow">Citry Project Board demo</p>
              <h1>Plan the product launch.</h1>
              <p class="project-hero__summary">
                Search the board, add a task, move cards between columns, and
                mark work complete. Citry sends each change to Python and
                updates the board without reloading the page.
              </p>
            </div>
            <dl class="project-hero__facts">
              <div><dt>Cycle</dt><dd>Autumn 2026</dd></div>
              <div><dt>Team</dt><dd>3 people</dd></div>
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
        padding-bottom: 2rem;
        border-bottom: 1px solid var(--color-border);
      }

      .project-hero__eyebrow {
        margin: 0 0 0.4rem;
        color: var(--color-muted);
      }

      .project-hero h1 {
        margin: 0;
        color: var(--color-text);
        font-size: 2.25rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        line-height: 1.3;
      }

      .project-hero__summary {
        max-width: 44rem;
        margin: 0.7rem 0 0;
        color: var(--color-muted);
        font-size: 1.05rem;
      }

      .project-hero__facts {
        display: flex;
        flex-wrap: wrap;
        justify-content: flex-end;
        gap: 1.4rem;
        margin: 0;
      }

      .project-hero__facts div {
        display: grid;
        gap: 0.1rem;
      }

      .project-hero__facts dt {
        color: var(--color-faint);
        font-family: ui-monospace, "Cascadia Code", Menlo, monospace;
        font-size: 0.65rem;
        font-weight: 650;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      .project-hero__facts dd {
        margin: 0;
        color: var(--color-text);
        font-size: 0.86rem;
        font-weight: 650;
      }

      .board-frame {
        padding: 2rem 0 1rem;
      }

      @media (max-width: 48rem) {
        .project-hero {
          grid-template-columns: 1fr;
        }

        .project-hero__facts {
          justify-content: flex-start;
        }
      }

      @media (max-width: 35rem) {
        .project-hero h1 {
          font-size: 2rem;
        }
      }
    """
