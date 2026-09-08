"""Standalone page that loads the FragmentWidget as an HTML fragment on demand."""

from citry import Component


class FragmentsPage(Component):
    """A page with a button that fetches a pre-rendered fragment and inserts it."""

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Fragments example</title>
          <!-- Load citry's client runtime up front. Its MutationObserver notices
               the fragment's manifest when it is inserted below, then fetches and
               runs the fragment's CSS/JS on demand. -->
          <script src="/citry/citry.js"></script>
        </head>
        <body
          style="margin: 0; padding: 1.5rem; font-family: system-ui, sans-serif;"
        >
          <p>Load a component rendered on the server and sent as an HTML fragment:</p>
          <button
            id="frag-load"
            type="button"
            data-fragment-url="/examples/fragments/demo/widget/"
            style="padding: 0.5rem 1rem; cursor: pointer;"
          >
            Load fragment
          </button>
          <button
            id="frag-reset"
            type="button"
            hidden
            style="padding: 0.5rem 1rem; cursor: pointer;"
          >
            Reset demo
          </button>
          <p id="frag-status" role="status"></p>
          <div id="frag-target" style="margin-top: 1rem;"></div>
          <script>
            const loadButton = document.getElementById("frag-load");
            const resetButton = document.getElementById("frag-reset");
            const status = document.getElementById("frag-status");

            loadButton.addEventListener("click", async () => {
              // The static response represents one render. Block repeat clicks
              // before fetching so it can only be inserted once in this page.
              if (loadButton.disabled) return;
              loadButton.disabled = true;
              status.textContent = "Loading fragment...";

              let html;
              try {
                const url = loadButton.dataset.fragmentUrl;
                const response = await fetch(url);
                if (!response.ok) throw new Error("Fragment request failed");
                html = await response.text();
              } catch {
                // A failed fetch has not inserted anything, so retry is safe.
                status.textContent = "Could not load the fragment. Try again.";
                loadButton.disabled = false;
                return;
              }

              // The runtime activates the fragment after its manifests arrive.
              document.getElementById("frag-target").innerHTML = html;
              status.textContent = "Reset the demo to load the fragment again.";
              resetButton.hidden = false;
            });

            resetButton.addEventListener("click", () => {
              // A new document can accept the static fragment again.
              window.location.reload();
            });
          </script>
        </body>
      </html>
    """
