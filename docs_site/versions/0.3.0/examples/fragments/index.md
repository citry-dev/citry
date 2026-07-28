---
title: Fragments
url: https://citry.dev/v/0.3.0/examples/fragments/
description: "Load a server-rendered component and its assets on demand."
---
# Fragments

Load a rendered component over the wire on demand; Citry loads its JavaScript
and CSS for you.



### Component

````citry
"""
An HTML fragment: a component rendered on its own and loaded into a page over the
wire, used as a live docs example.

The widget ships class-level JS and CSS. When the page fetches and inserts the
fragment, citry's client runtime loads those on demand from the static dep files
the build wrote (see build._pre_render_examples / static_deps.export_fragment_deps).
Kept to class-level js/css (no js_data/css_data), so the fragment references only
the two class-level dep URLs.
"""

from citry import Component


class FragmentWidget(Component):
    """A small self-contained widget, rendered and loaded as an HTML fragment."""

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <div class="frag-widget">
        <strong class="frag-widget__title">Loaded over the wire</strong>
        <p>This widget's HTML, CSS, and JS arrived as an HTML fragment.</p>
      </div>
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

    js = """
      $component(({ els }) => {
        // Proof the fragment's own JS ran after it was inserted.
        els[0].dataset.ready = "1";
        els[0].querySelector(".frag-widget__title").textContent += " (JS ran)";
      });
    """


# Variant name -> the component class rendered as a fragment. The build
# instantiates and pre-renders each below examples/fragments/demo/<variant>/,
# and writes its dep files.
FRAGMENTS = {"widget": FragmentWidget}
````

### Page

````citry
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
````

[Open the live result](/v/0.3.0/examples/fragments/demo/)

