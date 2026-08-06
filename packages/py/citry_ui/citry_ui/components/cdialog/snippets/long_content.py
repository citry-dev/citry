from dataclasses import dataclass

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


@dataclass(frozen=True, slots=True)
class ObservationEntry:
    title: str
    text: str


class DialogLongContent(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="dialog-scroll-demo">
        <p>Expedition archive</p>
        <h2>Choose what scrolls</h2>
        <c-CDialog scroll="body" size="lg">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Keep actions visible
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Seven nights at the ridge
          </c-fill>
          <c-fill name="description">
            Body scrolling keeps this header and the actions fixed.
          </c-fill>
          <c-fill name="default">
            <c-for each="entry in entries">
              <article class="dialog-scroll-demo__entry">
                <strong>{{ entry.title }}</strong>
                <span>{{ entry.text }}</span>
              </article>
            </c-for>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">
              Finish reading
            </c-CButton>
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.dialog-scroll-demo) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 46rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bae6fd, #0369a1);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.dialog-scroll-demo h2, .dialog-scroll-demo p) {
        margin: 0;
      }

      :where(.dialog-scroll-demo > p) {
        color: light-dark(#0369a1, #7dd3fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.dialog-scroll-demo__entry) {
        display: grid;
        gap: 0.25rem;
        padding-block: 0.75rem;
        border-block-end: 1px solid color-mix(in srgb, currentColor 16%, transparent);
      }

      :where(.dialog-scroll-demo__entry span) {
        color: color-mix(in srgb, currentColor 72%, transparent);
      }
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "entries": tuple(
                ObservationEntry(
                    title=f"Night {index}",
                    text="A clear horizon revealed Jupiter, four bright moons, and a faint silver arc.",
                )
                for index in range(1, 10)
            )
        }


preview = DialogLongContent()

preview  # noqa: B018
