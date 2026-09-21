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
        def like(self, state: ProductCard.State):
            return ProductCard(
                tags=state.tags,
                likes=state.likes + 1,
            )

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {
            "likes": kwargs.likes,
            "tags": kwargs.tags,
        }

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"likes": kwargs.likes}

    def css_data(self, kwargs: Kwargs, slots: Slots):
        return {"accent": kwargs.accent}

    template = """
      <article
        class="card"
        :class="{ 'card--open': open }"
      >
        <c-slot name="body" />

        <c-for each="tag in tags">
          <c-Tag
            c-label="tag"
            :highlight="open"
            @click="open = !open"
          />
        </c-for>
        <c-empty>
          <p>{{ tr("product-card-no-tags") }}</p>
        </c-empty>

        <button type="button" @c-click="like">
          Like <span v-text="likes">{{ likes }}</span>
        </button>

        <c-slot name="footer">
          No footer yet
        </c-slot>
      </article>
    """

    js = """
      $component({
        data() { return {open: false}; },
        onServerRender: ({ component }) => {
          animateLikes(component.$el, component.likes);
        },
      });
    """

    css = """
      .card {
        border-left: 3px solid var(--accent);
      }

      .card--open {
        color: var(--accent);
      }
    """

    messages = """
      product-card-no-tags = No tags yet.
    """

    class Dependencies:
        js = ["https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/dist/confetti.browser.min.js"]
        css = ["https://unpkg.com/normalize.css@8.0.1/normalize.css"]


html = str(ProductCard(
    tags=["new", "sale"],
    slots={"body": "Aurora Lamp"}
))
