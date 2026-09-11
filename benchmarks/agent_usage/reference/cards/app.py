"""Reference implementation of the product card task."""

from typing import NotRequired, TypedDict

from citry import Citry, Component, SlotInput

citry_app = Citry(autodiscover=False)


class Item(TypedDict):
    title: str
    price_cents: int
    description: str
    footer: NotRequired[str | None]


class ProductCard(Component):
    citry = citry_app

    class Kwargs:
        title: str
        price_cents: int

    class Slots:
        default: SlotInput
        footer: SlotInput | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
        # Integer arithmetic preserves the cents even for large prices.
        return {
            "title": kwargs.title,
            "price": f"${kwargs.price_cents // 100}.{kwargs.price_cents % 100:02d}",
        }

    template = """
      <article class="product-card">
        <h2>{{ title }}</h2>
        <p class="price">{{ price }}</p>
        <div class="description">
          <c-slot />
        </div>
        <footer>
          <c-slot name="footer">
            Available now
          </c-slot>
        </footer>
      </article>
    """

    css = """
      .product-card {
        border: 1px solid #b0b0b0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem;
      }
      .price {
        font-weight: bold;
      }
    """


class Catalog(Component):
    citry = citry_app

    class Kwargs:
        items: list[Item]

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
        cards = []
        for item in kwargs.items:
            fills = {"default": item["description"]}
            # Omission selects the slot fallback; an empty string is a real fill.
            if item.get("footer") is not None:
                fills["footer"] = item["footer"]
            cards.append(ProductCard(title=item["title"], price_cents=item["price_cents"], slots=fills))
        return {"cards": cards}

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <title>Products</title>
          <c-css />
        </head>
        <body>
          <c-for each="card in cards">
            {{ card }}
          </c-for>
        </body>
      </html>
    """


def render_cards(items: list[Item]) -> str:
    return str(Catalog(items=items))
