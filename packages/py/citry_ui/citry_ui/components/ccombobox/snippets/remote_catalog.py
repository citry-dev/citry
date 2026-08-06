import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RemoteStarCatalog(Component):
    template = """
      <section
        class="remote-stars"
        x-data
        x-init="Alpine.store('remoteStars', {
          async loadStars({ query, signal }) {
            await new Promise((resolve, reject) => {
              const timer = setTimeout(resolve, 350);
              signal.addEventListener('abort', () => {
                clearTimeout(timer);
                reject(new DOMException('Aborted', 'AbortError'));
              }, { once: true });
            });
            if (query.toLowerCase() === 'offline') {
              throw new Error('Catalog unavailable');
            }
            const stars = [
              { value: 'vega', label: 'Vega', description: 'Blue-white star in Lyra' },
              { value: 'rigel', label: 'Rigel', description: 'Blue supergiant in Orion' },
              { value: 'sirius', label: 'Sirius', description: 'Brightest star in the night sky' },
              { value: 'betelgeuse', label: 'Betelgeuse', description: 'Red supergiant in Orion' },
            ];
            const needle = query.toLowerCase();
            return stars.filter((star) => star.label.toLowerCase().includes(needle));
          },
        })"
      >
        <c-CField>
          <c-fill name="label">
            Star catalog
          </c-fill>
          <c-fill name="default">
            <c-CCombobox
              c-min_chars="2"
              c-debounce_ms="150"
              placeholder="Type at least two letters"
              $c-props="{ loadOptions: $store.remoteStars.loadStars }"
            >
              <c-fill name="loading">
                Reading the catalog...
              </c-fill>
              <c-fill name="empty">
                No catalog match.
              </c-fill>
              <c-fill name="error">
                The catalog could not be read.
              </c-fill>
            </c-CCombobox>
          </c-fill>
          <c-fill name="description">
            Try Vega, Rigel, Sirius, or Betelgeuse. Type offline to preview recovery.
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.remote-stars) {
        max-width: 30rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#a5b4fc, #4338ca);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = RemoteStarCatalog()

preview  # noqa: B018
