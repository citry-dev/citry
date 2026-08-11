import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PopoverPlacements(Component):
    template = """
      <section
        class="placement-preview"
        x-data="{ placement: 'bottom-start', match_width: false }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <c-CPopover
          $c-props="{ placement, matchWidth: match_width }"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Position orbital summary
            </c-CButton>
          </c-fill>
          <c-fill name="title">Orbital summary</c-fill>
          <c-fill name="default">
            Collision fallback may flip the requested side near a viewport edge.
          </c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.placement-preview) {
        display: grid;
        place-items: center;
        min-block-size: 22rem;
      }
    """


preview_controls = (
    {
        "name": "placement",
        "label": "Placement",
        "type": "select",
        "default": "bottom-start",
        "options": (
            ("top-start", "Top start"),
            ("top", "Top"),
            ("top-end", "Top end"),
            ("bottom-start", "Bottom start"),
            ("bottom", "Bottom"),
            ("bottom-end", "Bottom end"),
        ),
    },
    {
        "name": "match_width",
        "label": "Match activator width",
        "type": "checkbox",
        "default": False,
    },
)

preview = PopoverPlacements()

preview  # noqa: B018
