from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CImage

citry.register_library(citry_ui)


class BasicImage(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        return {
            "python_image": CImage(
                src="/static/img/ui/image/orion-nebula-1280.jpg",
                alt="Orion Nebula, captured from Northstar Ridge",
                width=1280,
                height=720,
                loading="eager",
            )
        }

    template = """
      <section class="image-basic">
        <article>
          <h3>Template composition</h3>
          <c-CImage
            src="/static/img/ui/image/orion-nebula-1280.jpg"
            alt="Orion Nebula, captured from Northstar Ridge"
            c-width="1280"
            c-height="720"
            loading="eager"
          />
        </article>
        <article>
          <h3>Python composition</h3>
          {{ python_image }}
        </article>
        <p>
          Both forms keep one native image semantic, required alternative text,
          and a reserved 16:9 box before the files finish loading.
        </p>
      </section>
    """

    css = """
      :where(.image-basic) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-basic article) { display: grid; gap: 0.5rem; }
      :where(.image-basic h3, .image-basic p) { margin: 0; }
      :where(.image-basic p) { grid-column: 1 / -1; }
      :where(.image-basic [data-citry-ui-part="image-root"]) {
        inline-size: 100%;
      }
    """


preview = BasicImage()

preview  # noqa: B018
