"""
``SearchModal`` - the search overlay, as a Citry component.

Renders the centered search dialog: the input, a results region that
``search.js`` fills from the Pagefind index, an empty state listing a few
popular pages, and a keyboard-help footer. The header button that opens this
modal lives in ``DocPage``; the behavior (loading the index on first use,
debounced queries, result rendering, keyboard navigation) lives in
``static/js/search.js``.

The whole overlay carries ``data-pagefind-ignore`` so the search UI never ends
up in its own index. The ``djc-*`` class names match the vendored
``search.css`` / ``search.js`` and stay until the wider rebrand.
"""

from __future__ import annotations

from typing import Any

from citry import Component


class SearchModal(Component):
    """The search overlay markup; behavior lives in search.js."""

    transparent = True

    class Kwargs:
        # None falls back to DEFAULT_QUICK_LINKS (a mutable list cannot be a
        # dataclass default, which the Kwargs class becomes).
        quick_links: list | None = None
        pagefind_path: str = "/pagefind/pagefind.js"
        site_target: str = ""

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "quick_links": kwargs.quick_links or [],
            "pagefind_path": kwargs.pagefind_path,
            "site_target": kwargs.site_target,
        }

    # Keep the arrow <kbd> tags adjacent so the hint has no artificial gap.
    template = """
      <div class="djc-search" data-pagefind-ignore>
        <div
          class="djc-search__overlay"
          c-data-pagefind-path="pagefind_path"
          c-data-search-site-target="site_target"
          hidden
        >
          <div class="djc-search__backdrop" data-search-close></div>
          <div
            id="djc-search-dialog"
            class="djc-search__dialog"
            role="dialog"
            aria-modal="true"
            aria-label="Search documentation"
          >
            <div class="djc-search__inputbar">
              <svg
                class="djc-search__input-icon"
                viewBox="0 0 24 24"
                width="18"
                height="18"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <circle
                  cx="11"
                  cy="11"
                  r="8"
                />
                <line
                  x1="21"
                  y1="21"
                  x2="16.65"
                  y2="16.65"
                />
              </svg>
              <input
                type="search"
                class="djc-search__input"
                placeholder="Search the docs..."
                autocomplete="off"
                autocorrect="off"
                autocapitalize="off"
                spellcheck="false"
                aria-label="Search documentation"
                aria-controls="djc-search-results"
              >
              <button
                class="djc-search__esc"
                type="button"
                data-search-close
                aria-label="Close search"
              >
                Esc
              </button>
            </div>
            <div
              id="djc-search-results"
              class="djc-search__results"
              role="listbox"
              aria-label="Search results"
            >
              <div class="djc-search__empty" data-search-empty>
                <div class="djc-search__section-label">Popular pages</div>
                <ul class="djc-search__quicklinks">
                  <li c-for="link in quick_links">
                    <a
                      class="djc-search__quicklink"
                      c-href="link.path"
                    >
                      {{ link.label }}
                    </a>
                  </li>
                </ul>
              </div>
              <div
                class="djc-search__message"
                data-search-noresults
                hidden
              ></div>
              <div
                class="djc-search__message"
                data-search-error
                hidden
              ></div>
              <div class="djc-search__list" data-search-list></div>
            </div>
            <div class="djc-search__footer">
              <span class="djc-search__hint">
                <kbd>&uarr;</kbd><kbd>&darr;</kbd> navigate
              </span>
              <span class="djc-search__hint">
                <kbd>&crarr;</kbd> select
              </span>
              <span class="djc-search__hint">
                <kbd>esc</kbd> close
              </span>
            </div>
          </div>
        </div>
      </div>
    """
