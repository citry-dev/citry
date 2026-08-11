import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomSwitch(Component):
    template = """
      <section class="switch-oak">
        <c-CSwitch checked size="lg">Oak reading nook</c-CSwitch>
      </section>
    """
    css = """
      :where(.switch-oak) {
        --cui-switch-on-color: light-dark(#7c4a25, #d8a06f);
        --cui-switch-off-color: light-dark(#8f8376, #9f9385);
        --cui-switch-thumb-color: light-dark(#fffaf2, #2a2119);
        --cui-switch-width: 3.4rem;
        --cui-switch-height: 1.9rem;
        padding: 1rem;
        border: 1px solid light-dark(#c6ad91, #725b44);
        border-radius: 0.8rem;
      }
    """


preview = CustomSwitch()

preview  # noqa: B018
