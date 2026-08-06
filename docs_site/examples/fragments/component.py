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
