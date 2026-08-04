"""
Per-page social-share images (the 1200x630 Open Graph cards).

For each eligible page the ``OgCard`` component is rendered to standalone HTML,
screenshotted to a PNG with a headless browser, and the page's ``og:image`` /
``twitter:image`` is swapped from the site-level default to that per-page card.

Two design choices keep this safe and cheap:

- It degrades gracefully. Every page already carries a valid default card image,
  and a per-page card only *replaces* it where one was produced. If Playwright or
  a browser binary is unavailable, the whole step is skipped and every page keeps
  the working default. The build never fails and no image 404s.
- The cards are content-addressed. A card is keyed by a hash of the template plus
  the title, description, and section, and stored as ``<hash>.png`` in a
  persistent cache directory. The output is wiped each build but the cache is
  not, so an unchanged card is copied without launching a browser, and a fully
  cached build needs no browser at all.
"""

from __future__ import annotations

import hashlib
import shutil
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING

from docs_site._internal.components.doc_page import default_og_image_url
from docs_site._internal.components.og_card import OgCard

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from docs_site._internal.build import PageRecord
    from docs_site._internal.nav import NavTree

OG_VIEWPORT = {"width": 1200, "height": 630}


@dataclass
class SocialCardOutcome:
    """How the social-card step went: how many cards were eligible, made, reused, placed."""

    eligible: int = 0  # pages that should carry a generated card
    rendered: int = 0  # cards freshly screenshotted this run
    cached: int = 0  # cards reused from the persistent cache
    placed: int = 0  # cards copied into the output and og:image rewritten
    skipped_reason: str = ""  # set when generation was skipped wholesale


@dataclass
class _Card:
    page_file: Path
    html: str
    title: str
    description: str
    section: str
    digest: str
    png_rel: str


def og_image_rel(page_url: str) -> str:
    """Output-relative PNG path for a page's card (``concepts/foo/`` -> ``og/concepts/foo.png``)."""
    slug = page_url.strip("/") or "index"
    return f"og/{slug}.png"


def generate_social_cards(
    output_dir: Path,
    records: list[PageRecord],
    nav_tree: NavTree,
    *,
    site_url: str,
    site_name: str,
    cache_dir: Path,
    log: Callable[[str], None] = lambda _msg: None,
) -> SocialCardOutcome:
    """Render or refresh each page's social card and point its og:image at the card."""
    site_url = site_url.rstrip("/")
    default_url = default_og_image_url(site_url)
    template_version = hashlib.sha256(OgCard.template.encode("utf-8")).hexdigest()[:16]

    work = [
        card
        for record in records
        if (card := _card_for(record, output_dir, nav_tree, template_version, default_url, site_name)) is not None
    ]
    outcome = SocialCardOutcome(eligible=len(work))
    if not work:
        return outcome

    cache_dir.mkdir(parents=True, exist_ok=True)
    todo = [c for c in work if not (cache_dir / f"{c.digest}.png").is_file()]
    outcome.cached = len(work) - len(todo)

    if todo:
        outcome.rendered, outcome.skipped_reason = _render_cards(todo, cache_dir, log, site_name)

    for card in work:
        cached_png = cache_dir / f"{card.digest}.png"
        if not cached_png.is_file():
            continue  # render was skipped (no browser): leave the default og:image
        dest = output_dir / card.png_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(cached_png, dest)
        card.page_file.write_text(card.html.replace(default_url, f"{site_url}/{card.png_rel}"), encoding="utf-8")
        outcome.placed += 1

    _prune_cache(cache_dir, {c.digest for c in work})
    return outcome


def _card_for(
    record: PageRecord,
    output_dir: Path,
    nav_tree: NavTree,
    template_version: str,
    default_url: str,
    site_name: str,
) -> _Card | None:
    """Build the work item for a page, or None when it should not get a card."""
    if not record.is_doc_page or record.noindex:
        return None
    page_file = _page_html_path(output_dir, record.url)
    if not page_file.is_file():
        return None
    html = page_file.read_text(encoding="utf-8")
    # A page with a custom front-matter og_image does not carry the default URL;
    # leave it untouched rather than overwrite an intentional image.
    if default_url not in html:
        return None

    title = record.title or site_name
    section = _section_label(nav_tree, record.url)
    digest = _card_hash(template_version, site_name, title, record.description, section)
    return _Card(
        page_file=page_file,
        html=html,
        title=title,
        description=record.description,
        section=section,
        digest=digest,
        png_rel=og_image_rel(record.url),
    )


def _page_html_path(output_dir: Path, url: str) -> Path:
    """The built HTML file for a clean URL (``""`` -> ``index.html``)."""
    slug = url.strip("/")
    return output_dir / "index.html" if not slug else output_dir / slug / "index.html"


def _section_label(nav_tree: NavTree, url: str) -> str:
    """Use a page's group when present, otherwise its primary area."""
    area = nav_tree.find_area(url)
    if area is None:
        return "Documentation"
    normalized = url.strip("/")
    for group in area.groups:
        if any(item.path.strip("/") == normalized for item in group.items):
            return group.label
    if area.label:
        return area.label
    return "Documentation"


def _card_hash(template_version: str, site_name: str, title: str, description: str, section: str) -> str:
    raw = f"{template_version}\x00{site_name}\x00{title}\x00{description}\x00{section}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _render_cards(cards: list[_Card], cache_dir: Path, log: Callable[[str], None], site_name: str) -> tuple[int, str]:
    """
    Screenshot each card to ``<cache_dir>/<hash>.png``. Returns ``(rendered, reason)``.

    ``reason`` is non-empty when rendering was skipped wholesale (no Playwright or
    no browser); the caller then leaves the default OG image on every page.

    The browser pass runs in a dedicated worker thread. Playwright's sync API
    refuses to start when an asyncio event loop is already running in the calling
    thread, so ``build_site`` would break if called from an async host app (or, in
    tests, after a run that keeps a sync-Playwright fixture open, which leaves a
    loop running on the main thread). A fresh thread never has a running loop, so
    the screenshot pass is safe from any calling context.
    """
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="citry-og-cards") as pool:
        return pool.submit(_screenshot_cards, cards, cache_dir, log, site_name).result()


def _screenshot_cards(
    cards: list[_Card], cache_dir: Path, log: Callable[[str], None], site_name: str
) -> tuple[int, str]:
    """Blocking browser pass for :func:`_render_cards`; run in a worker thread with no running loop."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415 - optional dependency
    except ImportError:
        log("Playwright not installed; skipping social cards (pages keep the default OG image)")
        return 0, "playwright-missing"

    rendered = 0
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception as e:  # noqa: BLE001 - any launch failure is a graceful skip
            log(f"Chromium unavailable ({type(e).__name__}); skipping social cards")
            return 0, "chromium-missing"
        try:
            page = browser.new_page(viewport=OG_VIEWPORT, device_scale_factor=1)  # type: ignore[arg-type]
            for card in cards:
                markup = str(
                    OgCard(
                        title=card.title,
                        description=card.description,
                        section=card.section,
                        site_name=site_name,
                    )
                )
                page.set_content(markup, wait_until="load")
                page.screenshot(path=str(cache_dir / f"{card.digest}.png"))
                rendered += 1
        finally:
            browser.close()
    return rendered, ""


def _prune_cache(cache_dir: Path, used: set[str]) -> None:
    """Drop cached PNGs no page references any more, so the cache stays bounded."""
    for png in cache_dir.glob("*.png"):
        if png.stem not in used:
            png.unlink()
