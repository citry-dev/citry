import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ImagePlaceholderAndError(Component):
    template = """
      <section
        class="image-feedback"
        x-data="{
          source:'/static/img/ui/image/horsehead-nebula-1280.jpg?generation=1',
          status:'waiting',
        }"
      >
        <div class="image-feedback__controls">
          <button
            type="button"
            @click="source='/static/img/ui/image/horsehead-nebula-1280.jpg?generation=2'"
          >Load a valid generation</button>
          <button
            type="button"
            @click="source='/static/img/ui/image/missing-observation.jpg?generation=3'"
          >Load a broken generation</button>
          <button
            type="button"
            @click="source='/static/img/ui/image/horsehead-nebula-640.jpg?generation=4'"
          >Recover with a small image</button>
        </div>

        <div class="image-feedback__grid">
          <article>
            <h3>Visual placeholder and fallback</h3>
            <c-CImage
              src="/static/img/ui/image/horsehead-nebula-1280.jpg"
              alt="Horsehead Nebula behind a dark dust cloud"
              c-width="1280"
              c-height="720"
              $c-props="{
                src:source,
                onStatusChange:(detail)=>status=detail.status,
              }"
            >
              <c-fill name="placeholder">
                <div class="image-feedback__placeholder">
                  <c-CSkeleton height="100%" animation="wave" />
                </div>
              </c-fill>
              <c-fill name="fallback">
                <span class="image-feedback__fallback">Plate unavailable</span>
              </c-fill>
            </c-CImage>
            <output x-text="`Normalized status: ${status}`">Normalized status: waiting</output>
          </article>

          <article>
            <h3>Native broken-image fallback</h3>
            <c-CImage
              src="/static/img/ui/image/missing-native-observation.jpg"
              alt="Missing Northstar archive observation"
              c-width="640"
              c-height="360"
            />
            <p>No custom fallback is supplied, so native broken rendering and alt remain.</p>
          </article>
        </div>
      </section>
    """

    css = """
      :where(.image-feedback) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-feedback__controls) { display: flex; flex-wrap: wrap; gap: 0.5rem; }
      :where(.image-feedback__grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
      }
      :where(.image-feedback article) { display: grid; gap: 0.5rem; align-content: start; }
      :where(.image-feedback h3, .image-feedback p) { margin: 0; }
      :where(.image-feedback [data-citry-ui-part="image-root"]) { inline-size: 100%; }
      :where(.image-feedback__placeholder, .image-feedback__fallback) {
        display: grid;
        place-items: center;
        inline-size: 100%;
        block-size: 100%;
      }
      :where(.image-feedback__fallback) { padding: 1rem; font-weight: 700; }
      @media (forced-colors: active) {
        :where(.image-feedback__fallback) { border: 1px solid CanvasText; }
      }
      @media print {
        :where(.image-feedback__controls, .image-feedback output) { display: none; }
      }
    """


preview = ImagePlaceholderAndError()

preview  # noqa: B018
