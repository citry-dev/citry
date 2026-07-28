"""
``ExampleCard`` - the tabbed example widget, as a Citry component.

Shows the example's two source files plus a live-demo iframe
(Pygments-highlighted), using the shared ``.tabbed-set`` markup that
``site.css`` / ``site.js`` already drive. Each card needs per-card-unique radio
ids so two cards on one page do not toggle each other, so the ids and the
matching ``<label for>`` are dynamic: ``c-id`` sets the input id, and
``c-bind="{'for': ...}"`` sets the label's ``for`` (a regular attribute - only
its *dynamic* form lacks a ``c-for`` shorthand, since that name is the loop).

The ``<c-example />`` tag (``_Example`` below) renders this and flushes it left so
the markdown pass treats it as block HTML (see ``docs_site._internal.util.lstrip_outside_pre``).
"""

from __future__ import annotations

from typing import Any

from markupsafe import Markup
from pygments import highlight
from pygments.formatters import HtmlFormatter

from citry import Component
from docs_site._internal.examples import example_not_found, get_example_registry
from docs_site._internal.util import lstrip_outside_pre
from pygments_citry.lexers import CitryPythonLexer


class ExampleCard(Component):
    """Tabbed widget: component source, page source, live demo."""

    transparent = True

    class Kwargs:
        # The example's directory name (drives the demo URL and unique ids).
        name: str
        # The ExampleInfo (docs_site._internal.examples.ExampleInfo); read for example_dir.
        info: Any

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        name = str(kwargs.name)
        info = kwargs.info
        formatter = HtmlFormatter(cssclass="highlight", nowrap=False)
        # The citry lexer highlights the HTML/JS/CSS embedded in the example's
        # template/js/css strings, not just the Python around them.
        lexer = CitryPythonLexer()
        component_code = highlight((info.example_dir / "component.py").read_text(encoding="utf-8"), lexer, formatter)
        page_code = highlight((info.example_dir / "page.py").read_text(encoding="utf-8"), lexer, formatter)

        # self.id is unique per render, so two cards for the same example on one
        # page still get distinct radio ids / names / label targets (valid HTML).
        group = f"__tabbed_ex_{name}_{self.id}"
        return {
            "tabs_attr": f"ex-{name}:3",
            "demo_url": f"/examples/{info.public_slug}/demo/",
            "demo_title": f"{name.replace('_', ' ').replace('-', ' ').title()} example live demo",
            "frame_class": ["example-demo-frame", {"example-demo-frame--theme-sync": name == "card"}],
            "group": group,
            "rid1": f"{group}_1",
            "rid2": f"{group}_2",
            "rid3": f"{group}_3",
            "pid1": f"{group}_panel_1",
            "pid2": f"{group}_panel_2",
            "pid3": f"{group}_panel_3",
            # Trusted: Pygments output over the example's own source files.
            "component_code": Markup(component_code),  # noqa: S704
            "page_code": Markup(page_code),  # noqa: S704
        }

    template = """
      <div
        class="tabbed-set example-card"
        c-data-tabs="tabs_attr"
        data-pagefind-ignore
      >
        <input
          c-id="rid1"
          c-name="group"
          type="radio"
          checked
        >
        <input
          c-id="rid2"
          c-name="group"
          type="radio"
        >
        <input
          c-id="rid3"
          c-name="group"
          type="radio"
        >
        <div class="tabbed-labels" role="tablist">
          <label
            c-bind="{'for': rid1}"
            c-id="rid1 + '_label'"
            role="tab"
            aria-selected="true"
            c-aria-controls="pid1"
            tabindex="0"
          >
            Component
          </label>
          <label
            c-bind="{'for': rid2}"
            c-id="rid2 + '_label'"
            role="tab"
            aria-selected="false"
            c-aria-controls="pid2"
            tabindex="-1"
          >
            Page
          </label>
          <label
            c-bind="{'for': rid3}"
            c-id="rid3 + '_label'"
            role="tab"
            aria-selected="false"
            c-aria-controls="pid3"
            tabindex="-1"
          >
            Live demo
          </label>
        </div>
        <div class="tabbed-content">
          <div
            c-id="pid1"
            class="tabbed-block is-active"
            role="tabpanel"
            c-aria-labelledby="rid1 + '_label'"
          >
            {{ component_code }}
          </div>
          <div
            c-id="pid2"
            class="tabbed-block"
            role="tabpanel"
            c-aria-labelledby="rid2 + '_label'"
            hidden
          >
            {{ page_code }}
          </div>
          <div
            c-id="pid3"
            class="tabbed-block tabbed-block--demo"
            role="tabpanel"
            c-aria-labelledby="rid3 + '_label'"
            hidden
          >
            <iframe
              c-src="demo_url"
              c-title="demo_title"
              c-class="frame_class"
              sandbox="allow-scripts allow-same-origin"
              loading="lazy"
            ></iframe>
          </div>
        </div>
      </div>
    """


class Example(Component):
    """``<c-example name="..." />`` renders the live example card (demo + source)."""

    transparent = True

    class Kwargs:
        name: str

    class Slots:
        pass

    template = "{{ card }}"

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        example_name = str(kwargs.name)
        info = get_example_registry().get(example_name)
        if info is None:
            return {"card": example_not_found(example_name)}
        # Render the card, flush it left (outside <pre>) so the markdown pass
        # treats it as block HTML, and pad with blank lines. Trusted: the card is
        # built from the example's own source plus Pygments output.
        card = lstrip_outside_pre(str(ExampleCard(name=example_name, info=info)))
        marked = f"<!-- docs-example:{example_name}:start -->\n{card}\n<!-- docs-example:{example_name}:end -->"
        return {"card": Markup(f"\n\n{marked}\n\n")}  # noqa: S704
