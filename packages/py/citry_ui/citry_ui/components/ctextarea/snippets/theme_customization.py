import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TextareaThemes(Component):
    template = """
      <section class="forest-themes">
        <div class="forest-themes__fern">
          <c-CField>
            <c-fill name="label">Fern journal</c-fill>
            <c-fill name="default"><c-CTextarea value="New fronds opened after rain." /></c-fill>
          </c-CField>
        </div>
        <div class="forest-themes__charcoal" style="color-scheme: dark">
          <c-CField>
            <c-fill name="label">Charcoal journal</c-fill>
            <c-fill name="default"><c-CTextarea value="Embers cooled before dawn patrol." /></c-fill>
          </c-CField>
        </div>
      </section>
    """

    css = """
      :where(.forest-themes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.forest-themes > div) {
        padding: 1rem;
        border-radius: 1rem;
      }

      :where(.forest-themes__fern) {
        --cui-textarea-background: #f7fff7;
        --cui-textarea-foreground: #153d24;
        --cui-textarea-border-color: #739b7d;
        --cui-textarea-hover-border-color: #315f3c;
        --cui-textarea-focus-color: #16713a;
        --cui-textarea-invalid-border-color: #b42318;
        --cui-textarea-disabled-background: #e1eee3;
        --cui-textarea-placeholder-color: #58715e;
        --cui-textarea-radius: 1rem;
        --cui-textarea-inline-padding: 1rem;
        --cui-textarea-block-padding: 0.875rem;
        --cui-textarea-font-size: 1rem;
        --cui-textarea-line-height: 1.6;
        background: #e2f0e4;
      }

      :where(.forest-themes__charcoal) {
        --cui-textarea-background: #162019;
        --cui-textarea-foreground: #e6f2e9;
        --cui-textarea-border-color: #66806d;
        --cui-textarea-hover-border-color: #9abc9f;
        --cui-textarea-focus-color: #8de49e;
        --cui-textarea-invalid-border-color: #ff8a80;
        --cui-textarea-disabled-background: #242d26;
        --cui-textarea-placeholder-color: #a7b8ab;
        --cui-textarea-radius: 0.25rem;
        --cui-textarea-inline-padding: 0.875rem;
        --cui-textarea-block-padding: 0.75rem;
        --cui-textarea-font-size: 1.025rem;
        --cui-textarea-line-height: 1.55;
        background: #0c120e;
      }

      :where(.forest-themes [data-citry-ui-part="textarea"]:focus-visible) {
        outline-style: double;
      }
    """


preview = TextareaThemes()

preview  # noqa: B018
