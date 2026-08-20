from citry import Component


class BasicPinInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CField required>
        <c-fill name="label">Verification code</c-fill>
        <c-fill name="description">Enter the six digits from your message.</c-fill>
        <c-fill name="default"><c-CPinInput name="code" /></c-fill>
      </c-CField>
    """


preview = BasicPinInput()
preview  # noqa: B018
