import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GridAsymmetricLayout(Component):
    template = """
      <c-CContainer class_="field-journal" size="lg">
        <c-CGrid cols="12" gap="lg">
          <c-CGridItem tag="article" span="12" md="8" class_="field-journal__notes">
            <p class="field-journal__eyebrow">Expedition 14 · obsidian ridge</p>
            <h2>Glass formed at the lava margin</h2>
            <p>
              The largest fragments show conchoidal fractures, faint silver
              banding, and almost no visible crystal growth.
            </p>
          </c-CGridItem>
          <c-CGridItem tag="aside" span="12" md="4" class_="field-journal__index">
            <h3>Specimen index</h3>
            <dl>
              <div><dt>R-14A</dt><dd>Black glass</dd></div>
              <div><dt>R-14B</dt><dd>Snowflake</dd></div>
              <div><dt>R-14C</dt><dd>Mahogany</dd></div>
            </dl>
          </c-CGridItem>
        </c-CGrid>
      </c-CContainer>
    """

    css = """
      :where(.field-journal) {
        color: CanvasText;
        font-family: ui-serif, Georgia, serif;
      }

      :where(.field-journal__notes, .field-journal__index) {
        padding: 1.1rem;
        border: 1px solid light-dark(#cec8b8, #625d52);
        border-radius: 0.65rem;
        background: light-dark(#fffdf6, #25231f);
      }

      :where(.field-journal h2, .field-journal h3, .field-journal p, .field-journal dl) {
        margin: 0;
      }

      :where(.field-journal__eyebrow) {
        color: light-dark(#8d4727, #eab08d);
        font-family: ui-sans-serif, system-ui, sans-serif;
        font-size: 0.68rem;
        font-weight: 750;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.field-journal h2) {
        margin-block: 0.35rem 0.65rem;
        font-size: 1.05rem;
      }

      :where(.field-journal__notes > p:last-child) {
        color: GrayText;
        font-size: 0.8rem;
        line-height: 1.55;
      }

      :where(.field-journal h3) {
        margin-block-end: 0.6rem;
        font-size: 0.85rem;
      }

      :where(.field-journal dl > div) {
        display: flex;
        justify-content: space-between;
        gap: 0.5rem;
        padding-block: 0.35rem;
        border-block-end: 1px dotted GrayText;
        font-size: 0.76rem;
      }

      :where(.field-journal dd) {
        margin: 0;
        color: GrayText;
      }
    """


preview = GridAsymmetricLayout()

preview  # noqa: B018
