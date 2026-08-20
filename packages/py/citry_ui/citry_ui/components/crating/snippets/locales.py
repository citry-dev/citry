from citry import Component


class RatingLocales(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="rating-demo-stack">
        <c-CRating label="Catalog-backed value names" value="3.5" precision="0.5" />
        <c-CRating label="Application-owned value names" value="4" value_label="Score {value} / {max}" />
        <p>The first Rating follows its nearest client-enabled i18n provider; the explicit pattern stays fixed.</p>
      </section>
    """
    css = ":where(.rating-demo-stack){display:grid;justify-items:start;gap:1rem}"


preview = RatingLocales()
preview  # noqa: B018
