"""
Render the Blog index from the catalog active for the current page render.

The public ``<c-blog-list />`` directive has no authored arguments. The build
or development request provides one validated catalog through a ``ContextVar``,
so the cards, navigation, feed, and post pages all project the same immutable
snapshot without a mutable process-global registry.
"""

from __future__ import annotations

from typing import Any

from markupsafe import Markup

from citry import Component
from docs_site._internal.blog import (
    BLOG_FEED_PATH,
    BLOG_LIST_END,
    BLOG_LIST_START,
    current_blog_catalog,
)
from docs_site._internal.util import lstrip_outside_pre


class BlogListView(Component):
    """The browser-facing list of Blog post cards."""

    transparent = True

    class Kwargs:
        posts: list

    class Slots:
        pass

    template = """
      <section
        class="blog-index"
        aria-label="Blog posts"
        data-pagefind-ignore
      >
        <div c-if="posts" class="blog-index__actions">
          <a class="blog-feed-link" c-href="feed_path">
            Subscribe via Atom
          </a>
        </div>
        <c-if cond="posts">
          <div class="blog-index__list" role="list">
            <article
              c-for="post in posts"
              class="blog-card"
              role="listitem"
            >
              <div class="blog-card__meta">
                <time c-datetime="post.date_iso">{{ post.date_label }}</time>
                <span aria-hidden="true">&middot;</span>
                <span>About {{ post.reading_minutes }} min read</span>
              </div>
              <h2 class="blog-card__title">
                <a c-href="post.public_path">{{ post.title }}</a>
              </h2>
              <p class="blog-card__description">{{ post.description }}</p>
              <div class="blog-card__byline">By {{ post.author }}</div>
              <ul
                c-if="post.tags"
                class="blog-tags"
                aria-label="Tags"
              >
                <li c-for="tag in post.tags">{{ tag }}</li>
              </ul>
            </article>
          </div>
        </c-if>
        <c-else>
          <p class="blog-index__empty">No Blog posts have been published yet.</p>
        </c-else>
      </section>
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "feed_path": BLOG_FEED_PATH,
            "posts": kwargs.posts,
        }


class BlogList(Component):
    """``<c-blog-list />`` renders cards from the provided Blog catalog."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    template = "{{ rendered }}"

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        catalog = current_blog_catalog()
        rendered = lstrip_outside_pre(str(BlogListView(posts=list(catalog.posts))))
        marked = f"{BLOG_LIST_START}\n{rendered}\n{BLOG_LIST_END}"
        return {"rendered": Markup(f"\n\n{marked}\n\n")}  # noqa: S704 - trusted component output
