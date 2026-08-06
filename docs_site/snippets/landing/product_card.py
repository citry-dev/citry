from citry import Component, SlotInput

class ProductCard(Component):
    class Kwargs:
        tags: list[str]
        likes: int = 0
        accent: str = "#175cd3"

    class Slots:
        body: SlotInput
        footer: SlotInput | None = None

    class State(Kwargs):
        pass

    class Events:
        def like(self, state):
            return ProductCard(
                tags=state.tags,
                likes=state.likes + 1,
            )

    def template_data(self, kwargs, slots):
        return {
            "likes": kwargs.likes,
            "tags": kwargs.tags,
        }

    def js_data(self, kwargs, slots):
        return {"likes": kwargs.likes}

    def css_data(self, kwargs, slots):
        return {"accent": kwargs.accent}

    template = """
      <article
        class="card"
        x-data="{ open: false }"
      >
        <c-slot name="body" />

        <c-for each="tag in tags">
          <c-Tag
            c-label="tag"
            $c-props="{ highlight: open }"
            @click="open = !open"
          />
        </c-for>
        <c-empty>
          <p>No tags yet.</p>
        </c-empty>

        <button type="button" @c-click="like">
          Like {{ likes }}
        </button>

        <c-slot name="footer">
          No footer yet
        </c-slot>
      </article>
    """

    js = """
      $component(({ els, data }) => {
        const cardEl = els[0];
        animateLikes(cardEl, data.likes);
      });
    """

    css = """
      .card {
        border-left: 3px solid var(--accent);
      }

      .tag--active {
        color: var(--accent);
      }
    """

    class Dependencies:
        js = ["https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js"]
        css = ["https://unpkg.com/normalize.css@8.0.1/normalize.css"]


html = str(ProductCard(
    tags=["new", "sale"],
    slots={"body": "Aurora Lamp"}
))
