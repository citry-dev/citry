"""
``UserGrid`` - the avatar grid rendered by the ``<c-people />`` directive.

Renders a centered, wrapping row of linked GitHub avatars from a list of person
records (``{login, avatarUrl, url, count?}``). The ``.user-list`` / ``.user`` /
``.avatar-wrapper`` classes are styled by the vendored ``site.css``. The data
comes from ``data/people.yml``; see ``components.people.People``.
"""

from __future__ import annotations

from citry import Component


class UserGrid(Component):
    """A centered grid of linked GitHub avatars, one per person record."""

    # Injected into the page markdown by the directive, so no data-cid marker.
    transparent = True

    class Kwargs:
        # Each user is a dict from people.yml: {login, avatarUrl, url, count?}.
        users: list
        # Contribution count is shown for contributors only.
        show_count: bool = False
        # The @handle under each avatar. A page that only acknowledges a group
        # can drop it and let the avatars read as one shape.
        show_name: bool = True
        # Whether each avatar links to its GitHub profile. The name still
        # reaches a screen reader through the image's alt text either way.
        link: bool = True

    class Slots:
        pass

    template = """
      <div class="user-list">
        <div c-for="user in users" class="user">
          <c-if cond="link">
            <a
              c-href="user['url']"
              target="_blank"
              rel="noopener"
            >
              <div class="avatar-wrapper">
                <img
                  c-src="user['avatarUrl']"
                  c-alt="'GitHub avatar of ' + user['login']"
                />
              </div>
              <div c-if="show_name" class="title">
                @{{ user['login'] }}
              </div>
            </a>
          </c-if>
          <c-else>
            <div class="avatar-wrapper">
              <img
                c-src="user['avatarUrl']"
                c-alt="'GitHub avatar of ' + user['login']"
              />
            </div>
            <div c-if="show_name" class="title">
              @{{ user['login'] }}
            </div>
          </c-else>
          <div c-if="show_count" class="info">
            Contributions: {{ user['count'] }}
          </div>
        </div>
      </div>
    """
