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
            data-fragment-url="/examples/fragments/demo/widget/"
            style="padding: 0.5rem 1rem; cursor: pointer;"
          >
            Load fragment
          </button>
          <div id="frag-target" style="margin-top: 1rem;"></div>
          <script>
            document
              .getElementById("frag-load")
              .addEventListener("click", async (event) => {
                const url = event.currentTarget.dataset.fragmentUrl;
                const response = await fetch(url);
                const html = await response.text();
                // Inserting the fragment's manifest triggers the runtime, which
                // loads the component scripts from static /citry/cache/ files.
                document.getElementById("frag-target").innerHTML = html;
              });
          </script>
        </body>
      </html>
    """
