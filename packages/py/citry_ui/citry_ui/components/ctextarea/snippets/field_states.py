import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TextareaFieldStates(Component):
    template = """
      <section class="forest-states">
        <c-CField required>
          <c-fill name="label">Required survey</c-fill>
          <c-fill name="default"><c-CTextarea name="required_survey" /></c-fill>
        </c-CField>
        <c-CField disabled>
          <c-fill name="label">Closed plot</c-fill>
          <c-fill name="default"><c-CTextarea name="closed_plot" value="Access suspended." /></c-fill>
        </c-CField>
        <c-CField readonly>
          <c-fill name="label">Archived note</c-fill>
          <c-fill name="default"><c-CTextarea name="archived" value="Old-growth marker confirmed." /></c-fill>
        </c-CField>
        <c-CField invalid>
          <c-fill name="label">Unclear location</c-fill>
          <c-fill name="default"><c-CTextarea name="location" value="Near the large tree" /></c-fill>
          <c-fill name="error">Name a trail marker or grid reference.</c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.forest-states) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = TextareaFieldStates()

preview  # noqa: B018
