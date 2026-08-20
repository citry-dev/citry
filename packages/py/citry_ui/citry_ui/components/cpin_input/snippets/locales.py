from citry import Component


class PinInputLocales(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="pin-input-demo-stack" dir="rtl">
        <c-CField>
          <c-fill name="label">رمز التحقق</c-fill>
          <c-fill name="description">يبقى رمز البروتوكول من اليسار إلى اليمين.</c-fill>
          <c-fill name="default"><c-CPinInput value="104" /></c-fill>
        </c-CField>
      </section>
    """
    css = ":where(.pin-input-demo-stack){display:grid;justify-items:start;gap:.75rem}"


preview = PinInputLocales()
preview  # noqa: B018
