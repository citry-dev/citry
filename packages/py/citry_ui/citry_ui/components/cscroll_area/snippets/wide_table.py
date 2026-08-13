import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaWideTable(Component):
    template = """
      <section class="scroll-area-wide-table" x-data="{direction:'ltr'}">
        <h2 id="quarterly-results-title">Quarterly service results</h2>
        <p>
          The Table keeps its caption and headers. ScrollArea only bounds the
          two-dimensional viewport.
        </p>
        <button
          type="button"
          @click="direction=direction === 'ltr' ? 'rtl' : 'ltr'"
        >Flip table direction</button>
        <div :dir="direction">
          <c-CScrollArea
            axis="both"
            aria_labelledby="quarterly-results-title"
            style="--cui-scroll-area-max-block-size: 16rem"
          >
            <table class="scroll-area-wide-table__table">
            <caption>Latency and availability by quarter</caption>
            <thead>
              <tr>
                <th scope="col">Service</th>
                <th scope="col">Q1 latency</th>
                <th scope="col">Q2 latency</th>
                <th scope="col">Q3 latency</th>
                <th scope="col">Q4 latency</th>
                <th scope="col">Availability</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row"><a href="#quarterly-results-title">Accounts</a></th>
                <td>112 ms</td><td>104 ms</td><td>98 ms</td>
                <td>91 ms</td><td>99.99%</td>
              </tr>
              <tr>
                <th scope="row"><a href="#quarterly-results-title">Ledger</a></th>
                <td>190 ms</td><td>172 ms</td><td>160 ms</td>
                <td>151 ms</td><td>99.97%</td>
              </tr>
              <tr>
                <th scope="row"><a href="#quarterly-results-title">Search</a></th>
                <td>86 ms</td><td>81 ms</td><td>74 ms</td>
                <td>69 ms</td><td>99.95%</td>
              </tr>
              <tr>
                <th scope="row"><a href="#quarterly-results-title">Archive</a></th>
                <td>244 ms</td><td>231 ms</td><td>218 ms</td>
                <td>205 ms</td><td>99.90%</td>
              </tr>
              <tr>
                <th scope="row"><a href="#quarterly-results-title">Reports</a></th>
                <td>155 ms</td><td>149 ms</td><td>141 ms</td>
                <td>134 ms</td><td>99.96%</td>
              </tr>
            </tbody>
            </table>
          </c-CScrollArea>
        </div>
        <p class="scroll-area-wide-table__print-note">
          This fixture supplies its own compact print table so the final
          column fits inside the physical page.
        </p>
      </section>
    """

    css = """
      :where(.scroll-area-wide-table) {
        display: grid;
        gap: 0.75rem;
        inline-size: min(100%, 42rem);
        min-inline-size: 0;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-wide-table h2, .scroll-area-wide-table p) {
        margin: 0;
      }

      :where(.scroll-area-wide-table > button) {
        justify-self: start;
      }

      :where(.scroll-area-wide-table__table) {
        inline-size: 52rem;
        border-collapse: collapse;
      }

      :where(.scroll-area-wide-table__table caption) {
        padding: 0.75rem;
        font-weight: 700;
        text-align: start;
      }

      :where(.scroll-area-wide-table__table th,
        .scroll-area-wide-table__table td) {
        min-inline-size: 7rem;
        padding: 0.625rem;
        border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
        text-align: start;
      }

      :where(.scroll-area-wide-table__table thead th) {
        background: color-mix(in srgb, Highlight 12%, Canvas);
      }

      @media print {
        :where(.scroll-area-wide-table) {
          inline-size: 100%;
        }

        :where(.scroll-area-wide-table__table) {
          inline-size: 100%;
          table-layout: fixed;
          font-size: 8pt;
        }

        :where(.scroll-area-wide-table__table th,
          .scroll-area-wide-table__table td) {
          min-inline-size: 0;
          padding: 0.2rem;
          overflow-wrap: anywhere;
        }
      }
    """


preview = ScrollAreaWideTable()

preview  # noqa: B018
