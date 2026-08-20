from citry import Component


class RatingPrecision(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="rating-demo-stack">
        <c-CField>
          <c-fill name="label">Half-star rating</c-fill>
          <c-fill name="default"><c-CRating value="3.5" precision="0.5" /></c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">Tenth precision</c-fill>
          <c-fill name="default"><c-CRating value="4.2" precision="0.1" /></c-fill>
        </c-CField>
      </section>
    """
    css = ":where(.rating-demo-stack){display:grid;gap:1.25rem}"


preview = RatingPrecision()
preview  # noqa: B018
