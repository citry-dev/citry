import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagsInputCustomization(Component):
    template = """
      <section class="tags-input-customization">
        <article class="tags-input-brand tags-input-brand--orchard">
          <h3>Orchard field notes</h3>
          <c-CTagsInput
            class_="brand-tags"
            c-value="['pear', 'pollinator']"
            c-input_attrs="{'aria-label':'Orchard labels'}"
          />
        </article>

        <article
          class="tags-input-brand tags-input-brand--harbor"
          style="color-scheme:dark"
        >
          <h3>Harbor field notes</h3>
          <c-CTagsInput
            class_="brand-tags"
            variant="filled"
            c-value="['tide', 'harbor']"
            c-input_attrs="{'aria-label':'Harbor labels'}"
          />
        </article>
      </section>
    """

    css = """
      :where(.tags-input-customization) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-brand) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        min-block-size: 12rem;
        padding: 1rem;
        border-radius: 1rem;
      }

      :where(.tags-input-brand h3) {
        margin: 0;
      }

      :where(.tags-input-brand--orchard) {
        background: #f5f0df;
        color: #203422;
        --cui-tags-input-background: #fffdf5;
        --cui-tags-input-border-color: #78916d;
        --cui-tags-input-focus-color: #315f37;
        --cui-tags-input-tag-background: #d9e9cf;
        --cui-tags-input-tag-border-color: #78916d;
      }

      :where(.tags-input-brand--harbor) {
        background: #102b38;
        color: #eefaff;
        --cui-tags-input-background: #173c4c;
        --cui-tags-input-foreground: #eefaff;
        --cui-tags-input-border-color: #72b5ce;
        --cui-tags-input-focus-color: #c6ecff;
        --cui-tags-input-tag-background: #29586b;
        --cui-tags-input-tag-foreground: #eefaff;
      }

      .tags-input-brand .brand-tags
      [data-citry-ui-part="remove"] {
        border-radius: 999px;
        outline-offset: 2px;
      }

      @media (forced-colors: active) {
        :where(.tags-input-brand) {
          border: 1px solid CanvasText;
        }
      }

      @media print {
        :where(.tags-input-brand) {
          min-block-size: auto;
          background: transparent;
          color: black;
        }
      }
    """


preview = TagsInputCustomization()

preview  # noqa: B018
