import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsDirection(Component):
    template = """
      <section class="tabs-direction">
        <article class="tabs-direction__card" dir="ltr" lang="en">
          <header>
            <p class="tabs-eyebrow">Left to right</p>
            <h2>Inner planets</h2>
          </header>

          <c-CTabs
            default_value="mercury"
            aria_label="Inner planets in English"
            direction="ltr"
          >
            <c-CTab value="mercury">
              Mercury
            </c-CTab>
            <c-CTab value="venus">
              Venus
            </c-CTab>
            <c-CTab value="earth">
              Earth
            </c-CTab>

            <c-CTabPanel value="mercury">
              The closest planet to the Sun.
            </c-CTabPanel>
            <c-CTabPanel value="venus">
              The second planet from the Sun.
            </c-CTabPanel>
            <c-CTabPanel value="earth">
              Our home in the solar system.
            </c-CTabPanel>
          </c-CTabs>
        </article>

        <article class="tabs-direction__card tabs-direction__card--rtl" dir="rtl" lang="ar">
          <header>
            <p class="tabs-eyebrow">من اليمين إلى اليسار</p>
            <h2>الكواكب الداخلية</h2>
          </header>

          <c-CTabs
            default_value="mercury"
            aria_label="الكواكب الداخلية بالعربية"
            direction="rtl"
            c-attrs="{'lang': 'ar'}"
          >
            <c-CTab value="mercury">
              عطارد
            </c-CTab>
            <c-CTab value="venus">
              الزهرة
            </c-CTab>
            <c-CTab value="earth">
              الأرض
            </c-CTab>

            <c-CTabPanel value="mercury">
              الكوكب الأقرب إلى الشمس.
            </c-CTabPanel>
            <c-CTabPanel value="venus">
              ثاني كوكب من الشمس.
            </c-CTabPanel>
            <c-CTabPanel value="earth">
              موطننا في النظام الشمسي.
            </c-CTabPanel>
          </c-CTabs>
        </article>
      </section>
    """

    css = """
      :where(.tabs-direction) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-direction__card) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.tabs-direction__card--rtl) {
        --cui-tabs-accent: light-dark(#0f766e, #5eead4);
        --cui-tabs-focus-color: light-dark(#0d9488, #2dd4bf);
      }

      :where(.tabs-direction__card header) {
        margin-block-end: 0.75rem;
      }

      :where(.tabs-direction__card h2, .tabs-direction__card p) {
        margin-block: 0;
      }

      :where(.tabs-direction__card header p) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.tabs-eyebrow) {
        color: var(--cui-tabs-accent, LinkText);
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
      }
    """


preview = TabsDirection()

preview  # noqa: B018
