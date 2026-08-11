import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GroupAlignment(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CStack class_="flow-alignments" gap="lg">
        <c-for each="justify in justifies">
          <c-CStack gap="xs">
            <strong>justify={{ justify }}</strong>
            <c-CGroup c-justify="justify" class_="flow-alignments__group">
              <span>Trim</span><span>Bisque</span><span>Glaze</span>
            </c-CGroup>
          </c-CStack>
        </c-for>
      </c-CStack>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"justifies": ("start", "center", "end", "between", "around", "evenly")}

    css = """
      :where(.flow-alignments) {
        max-inline-size: 44rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-alignments__group) {
        min-block-size: 3.5rem;
        padding: 0.65rem;
        border-radius: 0.55rem;
        background: light-dark(#f2e4cf, #362c24);
      }

      :where(.flow-alignments__group span) {
        padding: 0.35rem 0.5rem;
        border-radius: 0.35rem;
        background: light-dark(#b96540, #d7815b);
        color: #ffffff;
        font-size: 0.78rem;
      }
    """


preview = GroupAlignment()

preview  # noqa: B018
