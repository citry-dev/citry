import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicTimeInput(Component):
    template = """
      <c-CField required>
        <c-fill name="label">Start time</c-fill>
        <c-fill name="description">Choose when the session starts.</c-fill>
        <c-fill name="default"><c-CTimeInput name="start" /></c-fill>
      </c-CField>
    """


preview = BasicTimeInput()
preview  # noqa: B018
