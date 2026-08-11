import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CheckboxLabels(Component):
    template = """
      <section class="checkbox-labels">
        <c-CCheckbox label_pos="start" variant="outline">
          <c-fill name="default">
            Preserve this unusually long field-note label when the observation is
            exported to the regional botanical archive
          </c-fill>
          <c-fill name="description">
            Logical start placement and narrow wrapping remain direction-aware.
          </c-fill>
        </c-CCheckbox>
        <div dir="rtl">
          <c-CCheckbox label_pos="start">
            <c-fill name="default">تضمين ملاحظات الموطن</c-fill>
            <c-fill name="description">يبقى موضع التسمية منطقيًا في الاتجاه من اليمين.</c-fill>
          </c-CCheckbox>
        </div>
        <div class="checkbox-labels__row">
          <span>Polypody fern, row 17</span>
          <c-CCheckbox c-input_attrs="{'aria-label': 'Select polypody fern row 17'}" />
        </div>
      </section>
    """

    css = """
      :where(.checkbox-labels) {
        display: grid;
        gap: 1.25rem;
        max-width: 32rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.checkbox-labels > *) {
        min-width: 0;
        padding: 0.9rem;
        border: 1px solid light-dark(#c7d7c5, #3c5541);
        border-radius: 0.75rem;
      }

      :where(.checkbox-labels__row) {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
      }
    """


preview = CheckboxLabels()

preview  # noqa: B018
