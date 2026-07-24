"""
Image / asset guard.

Checks that every local ``<img src>``, ``<script src>``, and ``<link href>`` on a
doc page points at a file that actually exists. ``/static/...`` references resolve
against the source static dir (copied verbatim into the deployed site); other
absolute paths resolve against the build output. External and anchor/data
references are skipped.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from docs_site._internal.guards.base import GuardContext

_STATIC_PREFIX = "/static/"

# Files the citry build emits OUTSIDE the static dir (objects.inv, the SEO and
# llms text files, the pagefind search bundle, and the mounted citry runtime
# under /citry/). A reference to one of these is valid even though it does not
# resolve to a file under static_dir or to a built page.
_GENERATED_ROOT_ASSETS = frozenset(
    {"/objects.inv", "/sitemap.xml", "/robots.txt", "/llms.txt", "/llms-full.txt"},
)
_GENERATED_PREFIXES = ("/pagefind/", "/citry/")


def _asset_exists(src: str, build_dir: Path, static_dir: Path, page_dir: Path) -> bool:
    path, _, _ = src.partition("#")
    path, _, _ = path.partition("?")
    if not path:
        return True
    if path in _GENERATED_ROOT_ASSETS or path.startswith(_GENERATED_PREFIXES):
        return True
    if path.startswith(_STATIC_PREFIX):
        # Resolve against the source static dir, which is copied verbatim into
        # the deployed site's /static/ tree.
        return (static_dir / path[len(_STATIC_PREFIX) :]).is_file()
    if path.startswith("/"):
        rel = path.lstrip("/")
        return (build_dir / rel).is_file() or (build_dir / rel / "index.html").is_file()
    # Relative asset path: resolve the way a browser does - against the page's
    # output directory (pages are directory URLs, so that's the page's own dir).
    return (page_dir / path).resolve().is_file()


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    index = ctx.site_index
    if index is None:
        return

    seen: set[str] = set()  # dedupe identical broken assets across pages
    for page in index.pages:
        # Only check docs-owned assets. Example demo pages reference the
        # runtime-injected citry static, which is not part of the docs tree.
        if not page.is_doc_page:
            continue
        page_dir = (index.build_dir / page.label).parent
        for asset in page.assets:
            if asset.is_external or not asset.src:
                continue
            if _asset_exists(asset.src, index.build_dir, ctx.static_dir, page_dir):
                continue
            key = asset.src
            if key in seen:
                continue
            seen.add(key)
            yield GuardResult.error(
                guard="asset",
                message=f"Broken {asset.tag} asset: {asset.src!r}",
                source=page.label,
            )
