---
title: Fragments
url: https://citry.dev/v/0.6.0/examples/fragments/
description: "Load a server-rendered component and its assets on demand."
---
# Fragments

Use this pattern to add a component to a page after it has loaded, for
example when the user opens a panel. The server renders the component
as an HTML fragment, a piece of HTML that is not a whole page. Your
JavaScript inserts it, and Citry loads the component's JavaScript and
CSS and starts it.



### Component

````citry
"""
A widget that the page loads as an HTML fragment, used as a live docs
example.

The server renders the widget on its own. When the page inserts that
HTML, Citry's browser runtime fetches the widget's JavaScript and CSS
and starts it. The widget keeps its JavaScript and CSS on the class,
without ``js_data()`` or ``css_data()``, so every render of it shares
the same two files.
"""

from citry import Component


class FragmentWidget(Component):
    """A small widget, rendered and loaded as an HTML fragment."""

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <div class="frag-widget">
        <strong class="frag-widget__title">
          Loaded over the wire
          <span v-if="scriptRan">(JS ran)</span>
        </strong>
        <p>
          This widget's HTML, CSS, and JS arrived as an HTML fragment.
        </p>
      </div>
    """

    js = """
      $component({
        data() {
          return { scriptRan: false };
        },
        mounted() {
          // The label appears only once the widget's own script has
          // run in the page that inserted the fragment.
          this.scriptRan = true;
        },
      });
    """

    css = """
      .frag-widget {
        padding: 1rem 1.25rem;
        border: 2px solid #8250df;
        border-radius: 8px;
        background: #faf5ff;
        font-family: system-ui, sans-serif;
      }
      .frag-widget__title {
        color: #8250df;
      }
    """


# The docs build renders each component listed here as a separate HTML
# fragment, at examples/fragments/demo/<name>/, for the page to fetch,
# and writes the component's JavaScript and CSS files beside it.
FRAGMENTS = {"widget": FragmentWidget}
````

### Page

````citry
"""Standalone page that loads FragmentWidget as an HTML fragment."""

from citry import Component


class FragmentsPage(Component):
    """A page whose button fetches a fragment and inserts it."""

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
          <!-- Load citry's client runtime up front. Its
               MutationObserver notices the fragment's manifest when
               it is inserted below, then fetches and runs the
               fragment's CSS/JS on demand. -->
          <script src="/citry/citry.js"></script>
          <style>
            body {
              margin: 0;
              padding: 1.5rem;
              font-family: system-ui, sans-serif;
            }
          </style>
        </head>
        <body>
          <p>
            Load a component rendered on the server and sent as an
            HTML fragment:
          </p>
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
              // The static response represents one render. Block
              // repeat clicks before fetching, so it can only be
              // inserted once in this page.
              if (loadButton.disabled) return;
              loadButton.disabled = true;
              status.textContent = "Loading fragment...";

              let html;
              try {
                const url = loadButton.dataset.fragmentUrl;
                const response = await fetch(url);
                if (!response.ok) {
                  throw new Error("Fragment request failed");
                }
                html = await response.text();
              } catch {
                // A failed fetch has not inserted anything, so a
                // retry is safe.
                status.textContent =
                  "Could not load the fragment. Try again.";
                loadButton.disabled = false;
                return;
              }

              // The runtime activates the fragment after its
              // manifests arrive.
              document.getElementById("frag-target").innerHTML = html;
              status.textContent =
                "Reset the demo to load the fragment again.";
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
````

[Open the live result](/v/0.6.0/examples/fragments/demo/)



The lines to notice:

- The page loads `/citry/citry.js` up front. That script notices the
  inserted fragment and fetches its JavaScript and CSS.
- The button's script fetches the fragment and sets it as the
  `innerHTML` of an empty element. No other setup is needed.
- "(JS ran)" appears in the widget once its own script has started.

This docs site is static, so the example serves one prepared fragment,
and you reload the page to try again. To render and serve fragments from
your own routes, see [HTML fragments](/v/0.6.0/advanced/html-fragments/).