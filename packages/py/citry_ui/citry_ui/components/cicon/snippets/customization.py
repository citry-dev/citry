import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IconCustomization(Component):
    template = """
      <section class="field-keys">
        <article class="field-key field-key--light">
          <h2>Day survey key</h2>
          <p><c-CIcon name="leaf" /> Native species</p>
          <p><c-CIcon name="circle-help" /> Identity uncertain</p>
          <p><c-CIcon name="warn" /> Habitat under pressure</p>
        </article>
        <article class="field-key field-key--dark">
          <h2>Night survey key</h2>
          <p><c-CIcon name="leaf" /> Native species</p>
          <p><c-CIcon name="circle-help" /> Identity uncertain</p>
          <p><c-CIcon name="warn" /> Habitat under pressure</p>
        </article>
      </section>
    """

    css = """
      :where(.field-keys) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 54rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.field-key) {
        --cui-icon-size: 1.25rem;
        --cui-icon-stroke-width: 1.6;
        padding: 1rem;
        border: 1px solid currentColor;
        border-radius: 0.75rem;
      }

      :where(.field-key--light) {
        color-scheme: light;
        color: #20452a;
        background: #f4f9f1;
      }

      :where(.field-key--dark) {
        color-scheme: dark;
        color: #d7f3dc;
        background: #172b1c;
      }

      :where(.field-key h2) {
        margin: 0 0 0.8rem;
        font-size: 0.95rem;
      }

      :where(.field-key p) {
        display: flex;
        gap: 0.65rem;
        align-items: center;
        margin: 0.6rem 0;
      }

      :where(.field-key [data-citry-ui-part="icon"]) {
        color: light-dark(#15803d, #86efac);
      }

      :where(.field-key [data-name="warn"]) {
        color: light-dark(#b45309, #fcd34d);
      }
    """


preview = IconCustomization()

preview  # noqa: B018
