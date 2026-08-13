import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ImageAlternativeText(Component):
    template = """
      <section class="image-alt">
        <article>
          <h3>Informative</h3>
          <c-CImage
            src="/static/img/ui/image/orion-nebula-640.jpg"
            alt="Pink and blue clouds in the Orion Nebula"
            c-width="640"
            c-height="360"
          />
          <p>The alternative conveys the observation's useful content.</p>
        </article>

        <article>
          <h3>Decorative</h3>
          <c-CImage
            src="/static/img/ui/image/orion-nebula-640.jpg"
            c-alt="''"
            c-width="640"
            c-height="360"
          />
          <p>The nearby heading already supplies all meaning, so alt is empty.</p>
        </article>

        <article>
          <h3>Functional</h3>
          <a href="#full-observation">
            <c-CImage
              src="/static/img/ui/image/horsehead-nebula-640.jpg"
              alt="Open the full Horsehead Nebula observation"
              c-width="640"
              c-height="360"
            />
          </a>
          <p>The image is the link's only content, so alt names the destination.</p>
        </article>

        <article>
          <h3>Complex observation</h3>
          <figure>
            <c-CImage
              src="/static/img/ui/image/lunar-terminator-1280.jpg"
              alt="Lunar terrain map; values follow in the table"
              c-width="1280"
              c-height="640"
            />
            <figcaption>Exposure measurements along the lunar terminator.</figcaption>
          </figure>
          <table>
            <caption>Equivalent exposure data</caption>
            <thead><tr><th>Region</th><th>Seconds</th></tr></thead>
            <tbody><tr><td>North rim</td><td>0.008</td></tr><tr><td>South basin</td><td>0.013</td></tr></tbody>
          </table>
        </article>
      </section>
    """

    css = """
      :where(.image-alt) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-alt article) { display: grid; gap: 0.5rem; align-content: start; }
      :where(.image-alt h3, .image-alt p, .image-alt figure) { margin: 0; }
      :where(.image-alt [data-citry-ui-part="image-root"]) { inline-size: 100%; }
      :where(.image-alt a:focus-visible) { outline: 3px solid Highlight; outline-offset: 3px; }
      :where(.image-alt table) { border-collapse: collapse; font-size: 0.8rem; }
      :where(.image-alt th, .image-alt td) { border: 1px solid GrayText; padding: 0.25rem; }
    """


preview = ImageAlternativeText()

preview  # noqa: B018
