from citry import Component

# ruff: noqa: E501 - template lines stay readable in the public source example


class DateInputBounds(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CField required>
        <c-fill name="label">Alternating August date</c-fill>
        <c-fill name="description">Choose every second day from 1 through 31 August 2026.</c-fill>
        <c-fill name="default"><c-CDateInput name="day" value="2026-08-19" min="2026-08-01" max="2026-08-31" c-step="2" /></c-fill>
      </c-CField>
    """


preview = DateInputBounds()
preview  # noqa: B018
