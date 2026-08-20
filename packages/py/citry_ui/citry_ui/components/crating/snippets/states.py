from citry import Component


class RatingStates(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="rating-state-grid">
        <c-CRating label="Small subtle rating" value="2" size="sm" variant="subtle" />
        <c-CRating label="Default rating" value="3" />
        <c-CRating label="Large readonly rating" value="4.5" precision="0.5" size="lg" readonly />
        <c-CRating label="Disabled rating" value="1" disabled />
        <div dir="rtl"><c-CRating label="RTL rating" value="4" /></div>
        <c-CRating label="Brand rating" value="5" class_="rating-brand" />
      </section>
    """
    css = """
      :where(.rating-state-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));gap:1.5rem;align-items:start}
      :where(.rating-brand){--cui-rating-fill-color:#059669;--cui-rating-hover-color:#10b981;--cui-rating-gap:.4rem}
    """


preview = RatingStates()
preview  # noqa: B018
