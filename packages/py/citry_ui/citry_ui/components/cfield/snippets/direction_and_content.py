import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DirectionAndContent(Component):
    template = """
      <section class="shore-direction-grid">
        <article dir="ltr">
          <c-CField orientation="horizontal" invalid>
            <c-fill name="label">
              Detailed shoreline observation recorded during the lowest tide
            </c-fill>
            <c-fill name="default">
              <c-CInput name="english_note" value="Waves reaching the upper marker" />
            </c-fill>
            <c-fill name="error">
              Add whether the water crossed the protected nesting area.
            </c-fill>
          </c-CField>
        </article>

        <article dir="rtl" lang="ar">
          <c-CField orientation="horizontal">
            <c-fill name="label">
              ملاحظة مفصلة عن الشاطئ أثناء أدنى مستوى للمد
            </c-fill>
            <c-fill name="default">
              <c-CInput name="arabic_note" value="المياه هادئة حول الصخور" />
            </c-fill>
            <c-fill name="description">
              اذكر الأنواع التي ظهرت قرب خط الماء.
            </c-fill>
          </c-CField>
        </article>
      </section>
    """

    css = """
      :where(.shore-direction-grid) {
        display: grid;
        gap: 1.5rem;
        max-width: 62rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.shore-direction-grid article) {
        min-width: 0;
      }
    """


preview = DirectionAndContent()

preview  # noqa: B018
