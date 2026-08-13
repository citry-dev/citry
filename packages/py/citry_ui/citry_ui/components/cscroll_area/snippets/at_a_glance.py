from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CScrollArea

citry.register_library(citry_ui)


class ScrollAreaAtAGlance(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        return {
            "python_activity": CScrollArea(
                style={"--cui-scroll-area-max-block-size": "7rem"},
                slots={
                    "default": (
                        "Python composition keeps the same native viewport. ",
                        "Its content remains ordinary escaped slot content. ",
                        "The scrollbar belongs to the browser.",
                    ),
                },
            ),
        }

    template = """
      <section class="scroll-area-glance">
        <article>
          <h3>Recent activity</h3>
          <c-CScrollArea
            aria_label="Recent activity"
            style="--cui-scroll-area-max-block-size: 9rem"
          >
            <ol class="scroll-area-glance__activity">
              <li>Import completed</li>
              <li>Review requested</li>
              <li>Access approved</li>
              <li>Build started</li>
              <li>Checks completed</li>
              <li>Release published</li>
              <li>Audit archived</li>
            </ol>
          </c-CScrollArea>
        </article>

        <article>
          <h3>Applied filters</h3>
          <c-CScrollArea
            axis="inline"
            aria_label="Applied filters"
          >
            <div class="scroll-area-glance__rail">
              <span>Region: Central Europe</span>
              <span>Status: Needs review</span>
              <span>Owner: Operations</span>
              <span>Window: Last 90 days</span>
            </div>
          </c-CScrollArea>
        </article>

        <article>
          <h3>Result matrix</h3>
          <c-CScrollArea
            axis="both"
            aria_label="Result matrix"
            style="--cui-scroll-area-max-block-size: 9rem"
          >
            <div class="scroll-area-glance__matrix">
              <strong>Service</strong><strong>Owner</strong><strong>Region</strong>
              <span>Accounts</span><span>Identity</span><span>Prague</span>
              <span>Ledger</span><span>Finance</span><span>Berlin</span>
              <span>Search</span><span>Discovery</span><span>Vienna</span>
              <span>Archive</span><span>Records</span><span>Warsaw</span>
            </div>
          </c-CScrollArea>
        </article>

        <article>
          <h3>Python composition</h3>
          {{ python_activity }}
        </article>
      </section>
    """

    css = """
      :where(.scroll-area-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-glance article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        min-inline-size: 0;
      }

      :where(.scroll-area-glance h3) {
        margin: 0;
      }

      :where(.scroll-area-glance__activity) {
        display: grid;
        gap: 0.5rem;
        margin: 0;
        padding: 1rem 1rem 1rem 2rem;
      }

      :where(.scroll-area-glance__rail) {
        display: flex;
        inline-size: max-content;
        gap: 0.75rem;
        padding: 1rem;
      }

      :where(.scroll-area-glance__rail span) {
        padding: 0.375rem 0.625rem;
        border-radius: 999px;
        background: color-mix(in srgb, Highlight 14%, Canvas);
      }

      :where(.scroll-area-glance__matrix) {
        display: grid;
        grid-template-columns: repeat(3, minmax(9rem, 1fr));
        gap: 1px;
        inline-size: max-content;
        min-inline-size: 30rem;
        background: color-mix(in srgb, CanvasText 18%, transparent);
      }

      :where(.scroll-area-glance__matrix > *) {
        padding: 0.625rem;
        background: Canvas;
      }
    """


preview = ScrollAreaAtAGlance()

preview  # noqa: B018
