import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ImageFitAndGeometry(Component):
    template = """
      <section class="image-fit-grid">
        <article>
          <h3>Contain</h3>
          <c-CImage
            src="/static/img/ui/image/lunar-terminator-1280.jpg"
            alt="Lunar craters along the terminator, contained"
            c-width="1280"
            c-height="640"
            fit="contain"
            class_="image-fit-grid__frame"
          />
        </article>
        <article>
          <h3>Cover, left focus</h3>
          <c-CImage
            src="/static/img/ui/image/lunar-terminator-1280.jpg"
            alt="Lunar craters along the terminator, closely cropped"
            c-width="1280"
            c-height="640"
            fit="cover"
            position="20% 50%"
            class_="image-fit-grid__frame"
          />
        </article>
        <article>
          <h3>Scale down</h3>
          <c-CImage
            src="/static/img/ui/image/lunar-terminator-1280.jpg"
            alt="Lunar craters along the terminator, scaled down"
            c-width="1280"
            c-height="640"
            fit="scale-down"
            class_="image-fit-grid__frame image-fit-grid__square"
            c-style="{'--cui-image-radius':'1.25rem'}"
          />
        </article>
      </section>
    """

    css = """
      :where(.image-fit-grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-fit-grid article) { display: grid; gap: 0.5rem; }
      :where(.image-fit-grid h3) { margin: 0; }
      :where(.image-fit-grid__frame) {
        inline-size: 100%;
        --cui-image-aspect-ratio: 4 / 3;
        --cui-image-background: light-dark(#e7e5e4, #1c1917);
      }
      :where(.image-fit-grid__square) { --cui-image-aspect-ratio: 1 / 1; }
    """


preview = ImageFitAndGeometry()

preview  # noqa: B018
