import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardMedia(Component):
    template = """
      <section class="card-media">
        <c-CCard variant="outline">
          <c-fill name="media">
            <svg
              class="card-media__illustration"
              viewBox="0 0 360 190"
              role="img"
              aria-label="A round table beside a sunlit arched window"
            >
              <rect width="360" height="190" fill="#d9c5a3" />
              <path d="M220 170V70a58 58 0 0 1 116 0v100" fill="#8da7a0" />
              <circle cx="278" cy="70" r="38" fill="#f7e7a7" opacity=".8" />
              <ellipse cx="105" cy="135" rx="72" ry="18" fill="#7a4e32" />
              <path d="M84 135v42M126 135v42" stroke="#513523" stroke-width="8" />
            </svg>
          </c-fill>
          <c-fill name="header"><h2>Breakfast nook</h2></c-fill>
          <c-fill name="default">
            Card preserves the illustration's own aspect ratio and accessible name.
          </c-fill>
        </c-CCard>

        <c-CCard>
          <c-fill name="media">
            <div class="card-media__swatches">
              <span class="card-media__clay">Clay</span>
              <span class="card-media__linen">Linen</span>
              <span class="card-media__moss">Moss</span>
              <span class="card-media__walnut">Walnut</span>
            </div>
          </c-fill>
          <c-fill name="header"><h2>Autumn materials</h2></c-fill>
          <c-fill name="default">
            Multiple consumer-owned nodes can define their own media layout.
          </c-fill>
        </c-CCard>
      </section>
    """

    css = """
      :where(.card-media) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-media h2) {
        margin: 0;
        font-size: 1rem;
      }

      :where(.card-media__illustration) {
        display: block;
        inline-size: 100%;
        block-size: auto;
      }

      :where(.card-media__swatches) {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        min-block-size: 10rem;
      }

      :where(.card-media__swatches span) {
        display: grid;
        place-items: end center;
        padding: 0.5rem 0.2rem;
        color: #ffffff;
        font-size: 0.72rem;
        font-weight: 700;
      }

      :where(.card-media__clay) {
        background: #a75f46;
      }

      :where(.card-media__linen) {
        background: #b8a98c;
        color: #241f18;
      }

      :where(.card-media__moss) {
        background: #66704a;
      }

      :where(.card-media__walnut) {
        background: #5d3a2a;
      }
    """


preview = CardMedia()

preview  # noqa: B018
