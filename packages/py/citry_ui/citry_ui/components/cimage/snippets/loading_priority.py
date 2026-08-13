import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ImageLoadingPriority(Component):
    template = """
      <section class="image-priority">
        <article>
          <p class="image-priority__eyebrow">Above the fold</p>
          <h3>Tonight's featured field</h3>
          <c-CImage
            src="/static/img/ui/image/orion-nebula-1280.jpg"
            alt="Orion Nebula selected as tonight's featured field"
            c-width="1280"
            c-height="720"
            loading="eager"
            decoding="async"
            fetch_priority="high"
          />
          <p>Reserve high priority for the small number of likely LCP images.</p>
        </article>

        <button
          type="button"
          @click="document.querySelector('#image-priority-archive').scrollIntoView({behavior:'auto'})"
        >Scroll to the archive image</button>

        <div class="image-priority__spacer" aria-hidden="true"></div>

        <article id="image-priority-archive">
          <p class="image-priority__eyebrow">Below the fold</p>
          <h3>Archive plate</h3>
          <c-CImage
            src="/static/img/ui/image/horsehead-nebula-1280.jpg"
            alt="Horsehead Nebula archive plate"
            c-width="1280"
            c-height="720"
            loading="lazy"
            decoding="async"
            fetch_priority="auto"
          />
          <p>Lazy loading remains a native hint and needs no data-src indirection.</p>
        </article>
      </section>
    """

    css = """
      :where(.image-priority) {
        display: grid;
        gap: 1rem;
        max-inline-size: 46rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-priority article) { display: grid; gap: 0.5rem; }
      :where(.image-priority h3, .image-priority p) { margin: 0; }
      :where(.image-priority__eyebrow) { color: GrayText; font-weight: 700; }
      :where(.image-priority__spacer) { block-size: 70vh; border-block: 1px dashed GrayText; }
      :where(.image-priority [data-citry-ui-part="image-root"]) { inline-size: 100%; }
    """


preview = ImageLoadingPriority()

preview  # noqa: B018
