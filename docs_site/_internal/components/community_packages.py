"""Render reviewed Community package listings from the active catalog."""

from __future__ import annotations

from typing import Any

from markupsafe import Markup

from citry import Component
from docs_site._internal.community_packages import (
    COMMUNITY_PACKAGES_LIST_END,
    COMMUNITY_PACKAGES_LIST_START,
    current_community_package_catalog,
)
from docs_site._internal.util import lstrip_outside_pre


class CommunityPackageListView(Component):
    """The browser-facing cards for one Community package category."""

    transparent = True

    class Kwargs:
        packages: list
        category_label: str

    class Slots:
        pass

    template = """
      <section class="community-package-directory" c-aria-label="category_label">
        <c-if cond="packages">
          <div class="community-package-directory__list" role="list">
            <article
              c-for="package in packages"
              class="community-package-card"
              c-aria-labelledby="package.dom_id"
              role="listitem"
            >
              <div class="community-package-card__heading">
                <h2 c-id="package.dom_id" class="community-package-card__title">
                  <a
                    c-if="package.primary_url_external"
                    c-href="package.primary_url"
                    target="_blank"
                    rel="noopener"
                  >{{ package.name }}</a>
                  <a c-else c-href="package.primary_url">{{ package.name }}</a>
                </h2>
                <div class="community-package-card__badges">
                  <span class="community-package-card__badge">{{ package.ownership_label }}</span>
                  <span c-if="not package.published" class="community-package-card__badge">
                    Not yet on PyPI
                  </span>
                </div>
              </div>
              <p class="community-package-card__summary">{{ package.summary }}</p>
              <p c-if="package.notice" class="community-package-card__notice">
                <strong>Notice:</strong> {{ package.notice }}
              </p>
              <dl class="community-package-card__facts">
                <div>
                  <dt>Install</dt>
                  <dd c-if="package.published"><code>{{ package.install_command }}</code></dd>
                  <dd c-else>See the source repository for installation instructions.</dd>
                </div>
                <div>
                  <dt>Citry</dt>
                  <dd><code>{{ package.citry_requirement }}</code></dd>
                </div>
                <div>
                  <dt>Maintained by</dt>
                  <dd>
                    <a
                      c-if="package.maintainer_url and package.maintainer_url_external"
                      c-href="package.maintainer_url"
                      target="_blank"
                      rel="noopener"
                    >
                      {{ package.maintainer }}
                    </a>
                    <a c-elif="package.maintainer_url" c-href="package.maintainer_url">
                      {{ package.maintainer }}
                    </a>
                    <span c-else>{{ package.maintainer }}</span>
                  </dd>
                </div>
              </dl>
              <ul class="community-package-card__links" aria-label="Package links">
                <li c-if="package.docs_url and package.docs_url_external">
                  <a c-href="package.docs_url" target="_blank" rel="noopener">Documentation</a>
                </li>
                <li c-elif="package.docs_url"><a c-href="package.docs_url">Documentation</a></li>
                <li c-if="package.published">
                  <a c-href="package.pypi_url" target="_blank" rel="noopener">PyPI</a>
                </li>
                <li>
                  <a c-href="package.source_url" target="_blank" rel="noopener">Source</a>
                </li>
              </ul>
            </article>
          </div>
        </c-if>
        <c-else>
          <p>No packages are listed in this category yet.</p>
        </c-else>
      </section>
    """


class CommunityPackages(Component):
    """``<c-community-packages category="..." />`` renders reviewed packages."""

    transparent = True

    class Kwargs:
        category: str

    class Slots:
        pass

    template = "{{ rendered }}"

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        catalog = current_community_package_catalog()
        category = str(kwargs.category)
        rendered = lstrip_outside_pre(
            str(
                CommunityPackageListView(
                    packages=list(catalog.packages_for(category)),
                    category_label=catalog.category_label(category),
                )
            )
        )
        marked = (
            f"{COMMUNITY_PACKAGES_LIST_START.format(category=category)}\n"
            f"{rendered}\n"
            f"{COMMUNITY_PACKAGES_LIST_END.format(category=category)}"
        )
        return {"rendered": Markup(f"\n\n{marked}\n\n")}  # noqa: S704 - trusted component output
