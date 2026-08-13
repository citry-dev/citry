import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonVariantsAndSizes(Component):
    template = """
      <section
        class="split-button-variants"
        x-data="{
          variant:'solid',
          intent:'primary',
          size:'md',
          block:false,
          placement:'bottom-end',
          match_width:false
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <div class="split-button-variants__subject">
          <c-CSplitButton
            label="Live collection actions"
            menu_label="More live collection actions"
            $c-props="{
              variant,
              intent,
              size,
              block,
              placement,
              matchWidth: match_width
            }"
          >
            <c-fill name="default">Collect specimen</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="photograph">Photograph first</c-CMenuItem>
              <c-CMenuItem value="label">Print field label</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </div>
        <div class="split-button-variants__matrix">
          <c-CSplitButton
            label="Approve actions"
            menu_label="More approve actions"
            variant="outline"
            intent="success"
            size="sm"
          >
            <c-fill name="default">Approve</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="review">Return to review</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
          <c-CSplitButton
            label="Warning actions"
            menu_label="More warning actions"
            variant="ghost"
            intent="warn"
            size="lg"
          >
            <c-fill name="default">Flag specimen</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="quarantine" intent="danger">
                Quarantine specimen
              </c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </div>
      </section>
    """

    css = """
      :where(.split-button-variants) {
        display: grid;
        gap: 1.5rem;
        min-block-size: 20rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.split-button-variants__subject) {
        inline-size: min(100%, 30rem);
      }

      :where(.split-button-variants__matrix) {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        align-items: start;
      }
    """


preview_controls = (
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "solid",
        "options": (
            ("solid", "Solid"),
            ("outline", "Outline"),
            ("ghost", "Ghost"),
        ),
    },
    {
        "name": "intent",
        "label": "Intent",
        "type": "select",
        "default": "primary",
        "options": (
            ("primary", "Primary"),
            ("neutral", "Neutral"),
            ("success", "Success"),
            ("warn", "Warn"),
            ("danger", "Danger"),
        ),
    },
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {
        "name": "placement",
        "label": "Placement",
        "type": "select",
        "default": "bottom-end",
        "options": (
            ("bottom-start", "Bottom start"),
            ("bottom-end", "Bottom end"),
            ("top-start", "Top start"),
            ("top-end", "Top end"),
        ),
    },
    {"name": "block", "label": "Full width", "type": "checkbox", "default": False},
    {
        "name": "match_width",
        "label": "Match group width",
        "type": "checkbox",
        "default": False,
    },
)


preview = SplitButtonVariantsAndSizes()

preview  # noqa: B018
