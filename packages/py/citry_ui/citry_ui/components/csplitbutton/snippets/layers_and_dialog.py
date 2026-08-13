import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonLayersAndDialog(Component):
    template = """
      <section
        class="split-button-layer-demo"
        x-data="{dialogOpen:false,last:'No layer action yet'}"
        @click="if ($event.target.closest('[data-open-provenance]')) dialogOpen=true"
        x-init="$nextTick(() => {
          const host = $refs.shadowHost;
          const fixture = $refs.shadowFixture;
          if (!host.shadowRoot && fixture) host.attachShadow({mode:'open'}).append(fixture);
        })"
      >
        <h2>Clipped specimen tray</h2>
        <div class="split-button-layer-demo__clip" dir="rtl">
          <c-CSplitButton
            label="Clipped specimen actions"
            menu_label="More clipped specimen actions"
            placement="bottom-end"
            c-primary_attrs="{'data-open-provenance':'','@click':'last=`Primary requested provenance`'}"
            $c-props="{onAction:(value)=>{
              last=value;
              if (value === 'open-provenance') dialogOpen=true;
            }}"
          >
            <c-fill name="default">Record provenance</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="open-provenance">Open provenance Dialog</c-CMenuItem>
              <c-CMenuSubmenu value="archive">
                <c-fill name="label">Archive destination</c-fill>
                <c-fill name="default">
                  <c-CMenuItem value="alpine-archive">Alpine archive</c-CMenuItem>
                  <c-CMenuItem value="coastal-archive">Coastal archive</c-CMenuItem>
                </c-fill>
              </c-CMenuSubmenu>
            </c-fill>
          </c-CSplitButton>
        </div>

        <div x-ref="shadowHost" class="split-button-layer-demo__shadow-host">
          <div x-ref="shadowFixture">
            <c-CSplitButton
              label="Shadow specimen actions"
              menu_label="More Shadow specimen actions"
            >
              <c-fill name="default">Save Shadow specimen</c-fill>
              <c-fill name="menu">
                <c-CMenuItem value="shadow-export">Export from ShadowRoot</c-CMenuItem>
              </c-fill>
            </c-CSplitButton>
          </div>
        </div>

        <output aria-live="polite" x-text="last">No layer action yet</output>
        <c-CDialog
          size="sm"
          $c-props="{
            open:dialogOpen,
            onOpenChange:(next)=>dialogOpen=next,
          }"
        >
          <c-fill name="title">Specimen provenance</c-fill>
          <c-fill name="default">Collected above the tree line during the August survey.</c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">Close provenance</c-CButton>
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.split-button-layer-demo) {
        display: grid;
        gap: 1rem;
        justify-items: start;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.split-button-layer-demo h2) { margin: 0; }
      :where(.split-button-layer-demo__clip) {
        overflow: hidden;
        inline-size: min(100%, 24rem);
        block-size: 7rem;
        padding: 2rem;
        border: 1px solid color-mix(in srgb, CanvasText 30%, transparent);
        border-radius: 0.75rem;
      }
      :where(.split-button-layer-demo__shadow-host) {
        display: block;
        padding: 0.75rem;
        border: 1px dashed GrayText;
      }
    """


preview = SplitButtonLayersAndDialog()

preview  # noqa: B018
