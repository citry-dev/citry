import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ImageComposition(Component):
    template = """
      <section class="image-composition">
        <c-CCard tag="article" variant="outline">
          <c-fill name="media">
            <c-CImage
              src="/static/img/ui/image/observatory-wide-1280.jpg"
              alt="Northstar Observatory below the Milky Way"
              c-width="1280"
              c-height="720"
              fit="cover"
            />
          </c-fill>
          <c-fill name="header"><h3>Northstar Ridge</h3></c-fill>
          <c-fill name="default">A clear archive exposure from the western dome.</c-fill>
        </c-CCard>

        <article class="image-composition__delayed">
          <h3>Loading layout reservation</h3>
          <div class="image-composition__pair">
            <c-CSkeleton height="7rem" animation="wave" />
            <c-CImage
              src="/static/img/ui/image/horsehead-nebula-1280.jpg?delayed=1"
              alt="Horsehead Nebula exposure loading beside a decorative skeleton"
              c-width="1280"
              c-height="720"
              loading="lazy"
            />
          </div>
        </article>

        <figure>
          <c-CImage
            src="/static/img/ui/image/lunar-terminator-1280.jpg"
            alt="Craters and mountain shadows along the lunar terminator"
            c-width="1280"
            c-height="640"
          />
          <figcaption>Exposure notes: 0.008 seconds at the north rim.</figcaption>
        </figure>

        <a class="image-composition__link" href="#observation-42">
          <c-CImage
            src="/static/img/ui/image/orion-nebula-640.jpg"
            alt="Open observation 42, Orion Nebula"
            c-width="640"
            c-height="360"
          />
        </a>
      </section>
    """

    css = """
      :where(.image-composition) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-composition h3, .image-composition figure) { margin: 0; }
      :where(.image-composition [data-citry-ui-part="image-root"]) { inline-size: 100%; }
      :where(.image-composition__pair) { display: grid; gap: 0.5rem; }
      :where(.image-composition__link) { align-self: start; border-radius: 0.75rem; }
      :where(.image-composition__link:focus-visible) { outline: 3px solid Highlight; outline-offset: 3px; }
    """


preview = ImageComposition()

preview  # noqa: B018
