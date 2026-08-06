"""
``OgCard`` - the 1200x630 social-share card, as a Citry component.

Rendered to a standalone HTML document (not wrapped in DocPage) and then
screenshotted to a PNG by ``social_cards.py``. The markup is fully
self-contained (inline CSS, system fonts, an inline SVG mark) so a headless
browser can load it with no server and no network. The card design lives in
plain CSS a contributor can iterate on in a browser.
"""

from __future__ import annotations

from citry import Component
from docs_site._internal.components.brand import CitryMark  # noqa: F401


class OgCard(Component):
    """A self-contained social-share card; screenshotted to a PNG by the build."""

    transparent = True

    class Kwargs:
        title: str
        description: str = ""
        # Eyebrow label above the title (e.g. the section: "Concepts").
        section: str = ""
        site_name: str = "Citry"

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8">
        </head>
        <body>
          <div class="card">
            <div class="section">{{ section or site_name }}</div>
            <div class="body">
              <div class="title">{{ title }}</div>
              <c-if cond="description">
                <div class="description">{{ description }}</div>
              </c-if>
            </div>
            <div class="footer">
              <!-- Sized against the 30px name beside it at the same proportion
                   the site header uses: the mark sits just under the letters
                   rather than over them. -->
              <c-citry-mark
                color="#2bbdbd"
                width="33"
                height="29"
              />
              <span class="wordmark">{{ site_name }}</span>
            </div>
          </div>
        </body>
      </html>
    """

    css = """
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      html,
      body {
        width: 1200px;
        height: 630px;
      }
      .card {
        position: relative;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        width: 1200px;
        height: 630px;
        padding: 80px;
        color: #e8eaf0;
        background: #151825;
        background-image:
          radial-gradient(circle at 88% 8%, rgba(13, 138, 138, 0.45), transparent 42%),
          radial-gradient(circle at 0% 100%, rgba(13, 138, 138, 0.18), transparent 38%);
        font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      }
      /* Teal accent rail down the left edge */
      .card::before {
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        width: 14px;
        background: #0d8a8a;
        content: "";
      }
      .section {
        color: #2bbdbd;
        font-weight: 600;
        font-size: 26px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }
      .body {
        display: flex;
        flex: 1;
        flex-direction: column;
        justify-content: center;
      }
      .title {
        color: #ffffff;
        font-weight: 800;
        font-size: 76px;
        line-height: 1.08;
        letter-spacing: -0.02em;
        /* Clamp to 3 lines so long titles never overflow the card */
        display: -webkit-box;
        overflow: hidden;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 3;
      }
      .description {
        display: -webkit-box;
        overflow: hidden;
        margin-top: 28px;
        color: #aab2c5;
        font-size: 32px;
        line-height: 1.4;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
      }
      .footer {
        display: flex;
        align-items: center;
        gap: 14px;
      }
      .footer svg {
        display: block;
      }
      .wordmark {
        color: #ffffff;
        font-weight: 700;
        font-size: 30px;
      }
    """
