from citry import Component


class BirthdayDateInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CField>
        <c-fill name="label">Date of birth</c-fill>
        <c-fill name="description">Your browser may offer saved birthday information.</c-fill>
        <c-fill name="default"><c-CDateInput name="birthday" autocomplete="bday" max="2026-08-19" /></c-fill>
      </c-CField>
    """


preview = BirthdayDateInput()
preview  # noqa: B018
