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
# fragment, at examples/fragments/demo/<name>/, for the page to fetch.
FRAGMENTS = {"widget": FragmentWidget}
