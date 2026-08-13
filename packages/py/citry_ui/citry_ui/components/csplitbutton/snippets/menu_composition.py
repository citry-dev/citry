import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonMenuComposition(Component):
    template = """
      <section
        class="split-button-menu-composition"
        x-data="{publicRecord:true, format:'tiff', last:'No Menu action yet'}"
        dir="rtl"
      >
        <h2>Specimen publication</h2>
        <c-CSplitButton
          label="Specimen publication actions"
          menu_label="More specimen publication actions"
          c-close_on_select="False"
          $c-props="{onAction:(value, detail)=>last=`${detail.path.join(' / ') || 'root'}: ${value}`}"
        >
          <c-fill name="default">Publish specimen</c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="copy-citation">Copy citation</c-CMenuItem>
            <c-CMenuItem href="#specimen-public-record">Open public record</c-CMenuItem>
            <c-CMenuCheckboxItem
              value="public-record"
              $c-props="{
                checked: publicRecord,
                onCheckedChange: (next) => publicRecord = next,
              }"
            >
              Publicly visible
            </c-CMenuCheckboxItem>
            <c-CMenuRadioGroup
              value="tiff"
              $c-props="{
                value: format,
                onValueChange: (next) => format = next,
              }"
            >
              <c-fill name="label">Export format</c-fill>
              <c-fill name="default">
                <c-CMenuRadioItem value="tiff">TIFF</c-CMenuRadioItem>
                <c-CMenuRadioItem value="jpeg">JPEG</c-CMenuRadioItem>
              </c-fill>
            </c-CMenuRadioGroup>
            <c-CMenuSeparator />
            <c-CMenuGroup>
              <c-fill name="label">Archive destination</c-fill>
              <c-fill name="default">
                <c-CMenuSubmenu value="regional-archive">
                  <c-fill name="label">Regional archive</c-fill>
                  <c-fill name="default">
                    <c-CMenuItem value="alpine">Alpine collection</c-CMenuItem>
                    <c-CMenuItem value="coastal">Coastal collection</c-CMenuItem>
                  </c-fill>
                </c-CMenuSubmenu>
              </c-fill>
            </c-CMenuGroup>
            <c-CMenuItem value="withdraw" intent="danger">Withdraw record</c-CMenuItem>
          </c-fill>
        </c-CSplitButton>
        <output aria-live="polite" x-text="last">No Menu action yet</output>
        <p id="specimen-public-record">The linked public record remains native navigation.</p>
      </section>
    """

    css = """
      :where(.split-button-menu-composition) {
        display: grid;
        gap: 0.875rem;
        justify-items: start;
        min-block-size: 23rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.split-button-menu-composition h2, .split-button-menu-composition p) { margin: 0; }
      :where(.split-button-menu-composition output) {
        max-inline-size: 100%;
        overflow-wrap: anywhere;
      }
    """


preview = SplitButtonMenuComposition()

preview  # noqa: B018
