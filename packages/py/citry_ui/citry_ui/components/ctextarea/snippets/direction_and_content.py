from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TextareaDirection(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "english_note": (
                "A very-long-unbroken-specimen-code-FOREST-TRANSECT-NORTH-204 remained readable inside the control."
            ),
            "arabic_note": "كانت أوراق البلوط تتحرك مع الريح الخفيفة قرب الجدول.",
        }

    template = """
      <section class="forest-direction">
        <c-CField>
          <c-fill name="label">English trail note</c-fill>
          <c-fill name="default">
            <c-CTextarea name="english" c-value="english_note" c-attrs="{'dir': 'ltr'}" />
          </c-fill>
        </c-CField>
        <div dir="rtl">
          <c-CField>
            <c-fill name="label">ملاحظة الغابة</c-fill>
            <c-fill name="default">
              <c-CTextarea
                name="arabic"
                c-value="arabic_note"
                c-attrs="{'dir': 'rtl', 'dirname': 'arabic.dir'}"
              />
            </c-fill>
          </c-CField>
        </div>
      </section>
    """

    css = """
      :where(.forest-direction) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.forest-direction > *) {
        min-width: 0;
      }
    """


preview = TextareaDirection()

preview  # noqa: B018
