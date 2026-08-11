import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisabledSplitter(Component):
    template = """
      <fieldset disabled>
        <legend>Locked layout</legend>
        <c-CSplitter c-sizes="[40, 60]" variant="soft">
          <c-CSplitterPanel id="summary" label="Summary">Summary</c-CSplitterPanel>
          <c-CSplitterPanel id="details" label="Details">Details</c-CSplitterPanel>
        </c-CSplitter>
      </fieldset>
    """


preview = DisabledSplitter()
preview  # noqa: B018
