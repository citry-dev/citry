import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ImageDeliveryAndSecurity(Component):
    template = """
      <section class="image-delivery">
        <article>
          <h3>Same-origin archive</h3>
          <c-CImage
            src="/static/img/ui/image/orion-nebula-640.jpg"
            alt="Same-origin Orion Nebula plate"
            c-width="640"
            c-height="360"
            referrer_policy="strict-origin-when-cross-origin"
          />
          <p>Native request policy applies before src. Citry does not proxy bytes.</p>
        </article>

        <article>
          <h3>Credential-free CORS mode</h3>
          <c-CImage
            src="https://cross-origin.citry.test/northstar/observatory-1280.jpg"
            alt="Observatory plate requested in anonymous CORS mode"
            c-width="1280"
            c-height="720"
            cross_origin="anonymous"
            referrer_policy="no-referrer"
          >
            <c-fill name="fallback">Cross-origin plate unavailable in this preview</c-fill>
          </c-CImage>
          <p>The response still needs matching server headers for CORS use.</p>
        </article>

        <article>
          <h3>CSP and unavailable resources</h3>
          <c-CImage
            src="https://blocked-images.citry.test/northstar/blocked.jpg"
            alt="Archive plate unavailable under the current image policy"
            c-width="640"
            c-height="360"
          >
            <c-fill name="fallback">Blocked or unavailable plate</c-fill>
          </c-CImage>
          <p>Browser CSP remains authoritative and failures settle as image error.</p>
        </article>

        <aside>
          <h3>Application trust boundary</h3>
          <ul>
            <li>Relative, HTTPS, data, blob, raster, and SVG URLs remain consumer-owned.</li>
            <li>Do not log signed URLs, currentSrc, query strings, or response bodies.</li>
            <li>Blob lifetime, data-URL size, metadata privacy, and remote tracking are application policy.</li>
          </ul>
          <output>Safe request summary: request modes configured; URLs omitted</output>
        </aside>
      </section>
    """

    css = """
      :where(.image-delivery) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-delivery article, .image-delivery aside) { display: grid; gap: 0.5rem; align-content: start; }
      :where(.image-delivery h3, .image-delivery p, .image-delivery ul) { margin: 0; }
      :where(.image-delivery [data-citry-ui-part="image-root"]) { inline-size: 100%; }
    """


preview = ImageDeliveryAndSecurity()

preview  # noqa: B018
