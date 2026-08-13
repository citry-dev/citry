import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonCustomization(Component):
    template = """
      <section class="split-button-brand-demo">
        <article class="split-button-brand-demo__card split-button-brand-demo__card--orchard">
          <p>Orchard field guide</p>
          <c-CSplitButton
            class_="split-button-brand-demo__subject"
            label="Orchard specimen publishing actions"
            menu_label="More Orchard specimen publishing actions"
            open
          >
            <c-fill name="default">Publish alpine gentian observation</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="orchard-draft">Save Orchard draft</c-CMenuItem>
              <c-CMenuItem value="orchard-export">Export Orchard record</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </article>

        <article
          class="split-button-brand-demo__card split-button-brand-demo__card--harbor"
          dir="rtl"
        >
          <p>دليل ميناء للأبحاث الميدانية</p>
          <c-CSplitButton
            class_="split-button-brand-demo__subject"
            label="إجراءات نشر ملاحظة العينة الساحلية"
            menu_label="المزيد من إجراءات نشر ملاحظة العينة الساحلية"
            variant="outline"
            open
          >
            <c-fill name="default">نشر ملاحظة العينة الساحلية الطويلة</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="harbor-draft">حفظ المسودة الساحلية</c-CMenuItem>
              <c-CMenuItem value="harbor-export">تصدير السجل الساحلي</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </article>
      </section>
    """

    css = """
      :where(.split-button-brand-demo) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.split-button-brand-demo__card) {
        min-block-size: 18rem;
        padding: 1.25rem;
        border-radius: 1rem;
      }
      :where(.split-button-brand-demo__card > p) { margin-block: 0 1rem; font-weight: 700; }
      :where(.split-button-brand-demo__subject) { max-inline-size: 20rem; }

      :where(.split-button-brand-demo__card--orchard) {
        color-scheme: light;
        background: #f5f0df;
        --cui-button-background: #315f37;
        --cui-button-foreground: #fffdf5;
        --cui-button-hover-background: #244c2a;
        --cui-menu-background: #fffdf5;
        --cui-menu-foreground: #203422;
        --cui-menu-focus-background: #d9e9cf;
        --cui-menu-focus-foreground: #17351c;
        --cui-split-button-divider-color: #c5d7bb;
        --cui-split-button-divider-width: 2px;
        --cui-split-button-radius: 0.75rem;
      }

      :where(.split-button-brand-demo__card--harbor) {
        color-scheme: dark;
        background: #102b38;
        --cui-button-background: #c6ecff;
        --cui-button-foreground: #082633;
        --cui-button-border-color: #79bfdc;
        --cui-button-hover-background: #a7ddf5;
        --cui-menu-background: #173c4c;
        --cui-menu-foreground: #eefaff;
        --cui-menu-focus-background: #95d9f4;
        --cui-menu-focus-foreground: #062531;
        --cui-split-button-divider-color: #29586b;
        --cui-split-button-divider-width: 1px;
        --cui-split-button-radius: 0.375rem;
      }

      :where(.split-button-brand-demo [data-citry-ui-part="split-button-primary"]) {
        min-inline-size: 0;
      }
      :where(.split-button-brand-demo [data-citry-ui-part="split-button-primary-content"]) {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      @media (prefers-reduced-motion: reduce) {
        :where(.split-button-brand-demo) {
          --cui-menu-duration: 0ms;
        }
      }
      @media (forced-colors: active) {
        :where(.split-button-brand-demo__card) {
          border: 1px solid CanvasText;
          forced-color-adjust: auto;
        }
      }
      @media print {
        :where(.split-button-brand-demo__card) {
          break-inside: avoid;
          border: 1px solid currentColor;
          background: transparent;
          color: black;
        }
      }
    """


preview = SplitButtonCustomization()

preview  # noqa: B018
