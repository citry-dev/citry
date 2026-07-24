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


class OgCard(Component):
    """A self-contained social-share card; screenshotted to a PNG by the build."""

    transparent = True

    class Kwargs:
        title: str
        description: str = ""
        # Eyebrow label above the title (e.g. the section: "Concepts").
        section: str = ""
        site_name: str = "Citry"

    template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                html, body { width: 1200px; height: 630px; }
                .card {
                    width: 1200px;
                    height: 630px;
                    padding: 80px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    color: #e8eaf0;
                    background: #151825;
                    background-image:
                        radial-gradient(circle at 88% 8%, rgba(13, 138, 138, 0.45), transparent 42%),
                        radial-gradient(circle at 0% 100%, rgba(13, 138, 138, 0.18), transparent 38%);
                    position: relative;
                }
                /* Teal accent rail down the left edge */
                .card::before {
                    content: "";
                    position: absolute;
                    left: 0; top: 0; bottom: 0;
                    width: 14px;
                    background: #0d8a8a;
                }
                .section {
                    font-size: 26px;
                    font-weight: 600;
                    letter-spacing: 0.12em;
                    text-transform: uppercase;
                    color: #2bbdbd;
                }
                .body { display: flex; flex-direction: column; justify-content: center; flex: 1; }
                .title {
                    font-size: 76px;
                    font-weight: 800;
                    line-height: 1.08;
                    letter-spacing: -0.02em;
                    color: #ffffff;
                    /* Clamp to 3 lines so long titles never overflow the card */
                    display: -webkit-box;
                    -webkit-line-clamp: 3;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                }
                .description {
                    margin-top: 28px;
                    font-size: 32px;
                    line-height: 1.4;
                    color: #aab2c5;
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                }
                .footer { display: flex; align-items: center; gap: 18px; }
                .footer svg { display: block; }
                .wordmark { font-size: 30px; font-weight: 700; color: #ffffff; }
            </style>
        </head>
        <body>
            <div class="card">
                <div class="section">{{ section or site_name }}</div>
                <div class="body">
                    <div class="title">{{ title }}</div>
                    <c-if cond="description"><div class="description">{{ description }}</div></c-if>
                </div>
                <div class="footer">
                    <svg width="52" height="52" viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect width="52" height="52" rx="12" fill="#0d8a8a"/>
                        <path d="M21 15 L13 26 L21 37 M31 15 L39 26 L31 37"
                              stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span class="wordmark">{{ site_name }}</span>
                </div>
            </div>
        </body>
        </html>
    """
