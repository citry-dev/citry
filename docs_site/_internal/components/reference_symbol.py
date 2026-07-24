"""
``ReferenceSymbol`` - draws one API-reference symbol, as a Citry component.

Takes the structure from ``reference.extract_symbol`` (name, kind, signature,
description, parameters/returns/raises/attributes, and nested members) and
renders the heading, signature, docstring, and member sections. A class renders
its members by recursing into itself, so a whole class reference is one render.
"""

from __future__ import annotations

from typing import Any

from markupsafe import Markup

from citry import Component


class ReferenceSymbol(Component):
    """Heading + signature + docstring + members for one documented symbol."""

    # No explicit `name`: the class name auto-registers both `referencesymbol`
    # and `reference-symbol`, so the recursive <c-ReferenceSymbol> tag resolves.
    transparent = True

    class Kwargs:
        # A SimpleNamespace from reference.extract_symbol.
        data: Any
        # Heading level for this symbol: a top-level symbol sits under the page
        # H1 at level 2; each nested member is one level deeper.
        level: int = 2

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        # Headings run h2..h6; members render one level deeper, capped at h6.
        level = min(max(kwargs.level, 2), 6)
        # The empty badge span carries the symbol kind so the right-rail TOC (built
        # by toc.merge_html_headings_into_toc from the rendered HTML) can show it.
        # Each base is already linked <code> Markup; join once here so the template
        # can drop it in with a comma between entries.
        return {
            "data": kwargs.data,
            "heading_tag": f"h{level}",
            "member_level": min(level + 1, 6),
            "kind_badge": f"doc-symbol doc-symbol-{kwargs.data.kind}",
            "bases": Markup(", ").join(kwargs.data.bases),
        }

    # Keep <pre><code> adjacent below so source indentation does not become
    # whitespace in the displayed signature.
    template = """
      <div class="doc-object">
        <c-if cond="data.source_url">
          <a
            class="doc-source-link"
            c-href="data.source_url"
            target="_blank"
            rel="noopener"
          >
            View source
          </a>
        </c-if>
        <c-element
          c-is="heading_tag"
          c-id="data.anchor"
          class="doc-heading"
        >
          <span c-class="kind_badge"></span>
          <span class="doc-object-name">
            <code>{{ data.name }}</code>
          </span>
          <span class="doc-kind">{{ data.kind }}</span>
        </c-element>
        <c-if cond="data.bases">
          <p class="doc-class-bases">Bases: {{ bases }}</p>
        </c-if>
        <c-if cond="data.signature">
          <div class="doc-signature highlight">
            <pre><code>{{ data.signature }}</code></pre>
          </div>
        </c-if>
        <div class="doc-body">
          {{ data.description }}
          <c-if cond="data.params">
            <p class="doc-section">Parameters</p>
            <ul class="doc-list">
              <c-for each="p in data.params">
                <li>
                  <code>{{ p.name }}</code>
                  <c-if cond="p.annotation">
                    <code>{{ p.annotation }}</code>
                  </c-if>
                  - {{ p.description }}
                </li>
              </c-for>
            </ul>
          </c-if>
          <c-if cond="data.returns">
            <p class="doc-section">Returns</p>
            <p class="doc-returns">{{ data.returns }}</p>
          </c-if>
          <c-if cond="data.raises">
            <p class="doc-section">Raises</p>
            <ul class="doc-list">
              <c-for each="r in data.raises">
                <li>
                  <code>{{ r.name }}</code> - {{ r.description }}
                </li>
              </c-for>
            </ul>
          </c-if>
          <c-if cond="data.attributes">
            <p class="doc-section">Attributes</p>
            <ul class="doc-list">
              <c-for each="a in data.attributes">
                <li>
                  <code>{{ a.name }}</code>
                  <c-if cond="a.annotation">
                    <code>{{ a.annotation }}</code>
                  </c-if>
                  - {{ a.description }}
                </li>
              </c-for>
            </ul>
          </c-if>
          <c-if cond="data.members">
            <div class="doc-members">
              <c-for each="m in data.members">
                <c-ReferenceSymbol
                  c-data="m"
                  c-level="member_level"
                />
              </c-for>
            </div>
          </c-if>
        </div>
      </div>
    """
