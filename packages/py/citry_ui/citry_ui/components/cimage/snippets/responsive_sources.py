from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CImage, CImageSource

citry.register_library(citry_ui)


class ResponsiveImageSources(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        sources = (
            CImageSource(
                media="(max-width: 47.99rem)",
                srcset="/static/img/ui/image/observatory-portrait-640.jpg",
                width=640,
                height=960,
            ),
            CImageSource(
                media="(min-width: 64rem)",
                type="image/avif",
                srcset="/static/img/ui/image/observatory-wide-1280.avif",
                width=1280,
                height=720,
            ),
        )
        return {
            "sources": sources,
            "responsive_srcset": (
                "/static/img/ui/image/observatory-portrait-640.jpg 640w, "
                "/static/img/ui/image/observatory-wide-1280.jpg 1280w"
            ),
            "python_image": CImage(
                src="/static/img/ui/image/observatory-wide-1280.jpg",
                alt="Northstar Observatory beneath the Milky Way",
                width=1280,
                height=720,
                srcset=(
                    "/static/img/ui/image/observatory-portrait-640.jpg 640w, "
                    "/static/img/ui/image/observatory-wide-1280.jpg 1280w"
                ),
                sizes="(max-width: 48rem) 100vw, 48rem",
                sources=sources,
            ),
        }

    template = """
      <section
        class="image-responsive"
        x-data="{selected:'Waiting for native selection'}"
      >
        <p>
          Resize across 48rem and 64rem. The browser selects the first matching
          source, then the final image candidates.
        </p>
        <div class="image-responsive__pair">
          <article>
            <h3>Template-fed records</h3>
            <c-CImage
              src="/static/img/ui/image/observatory-wide-1280.jpg"
              alt="Northstar Observatory beneath the Milky Way"
              c-width="1280"
              c-height="720"
              c-srcset="responsive_srcset"
              sizes="(max-width: 48rem) 100vw, 48rem"
              c-sources="sources"
              $c-props="{
                onStatusChange:(detail)=>{
                  const value=detail.current_src || detail.src;
                  selected=value.split('/').pop().split('?')[0];
                },
              }"
            />
          </article>
          <article>
            <h3>Python records</h3>
            {{ python_image }}
          </article>
        </div>
        <output x-text="`Selected local fixture: ${selected}`">
          Selected local fixture: Waiting for native selection
        </output>
      </section>
    """

    css = """
      :where(.image-responsive) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-responsive__pair) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
      }
      :where(.image-responsive article) { display: grid; gap: 0.5rem; }
      :where(.image-responsive h3, .image-responsive p) { margin: 0; }
      :where(.image-responsive [data-citry-ui-part="image-root"]) { inline-size: 100%; }
    """


preview = ResponsiveImageSources()

preview  # noqa: B018
