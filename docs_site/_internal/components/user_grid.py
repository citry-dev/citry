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
        # Contributions count is shown for contributors, hidden for maintainers.
        show_count: bool = False

    template = """
      <div class="user-list">
        <div class="user" c-for="user in users">
          <a c-href="user['url']" target="_blank" rel="noopener">
            <div class="avatar-wrapper">
              <img c-src="user['avatarUrl']" c-alt="'GitHub avatar of ' + user['login']" />
            </div>
            <div class="title">
              @{{ user['login'] }}
            </div>
          </a>
          <div class="info" c-if="show_count">
            Contributions: {{ user['count'] }}
          </div>
        </div>
      </div>
    """
