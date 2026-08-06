"""
A README that ships outside the repository must not link to it by relative path.

PyPI and the VS Code Marketplace render these files on their own domains, where
`docs/assets/benchmark.png` or `./LICENSE` resolves against *their* site and
404s. GitHub resolves the same path fine, so a broken link is invisible until
someone opens the package page.

Every reference in a published README therefore has to be absolute: an image at
`https://raw.githubusercontent.com/...`, a repository file at
`https://github.com/citry-dev/citry/blob/main/...`. In-page anchors (`#usage`)
are fine, since they stay inside the rendered document.

Which files count as published: the `readme` a packaging config points at, plus
the VS Code extension's own README.
"""

import re
from pathlib import Path

import tomllib

REPO_ROOT = Path(__file__).resolve().parents[2]

# `[text](target)` in Markdown, and the `src` of an inline HTML <img>. Markdown
# images are the link form with a leading `!`, so one pattern covers both.
_MARKDOWN_TARGET_RE = re.compile(r"\]\(([^)\s]+)")
_IMG_SRC_RE = re.compile(r"<img[^>]*?\ssrc=[\"']([^\"']+)")

# A target that resolves the same way on any host: a full URL, an in-page
# anchor, or a mail link.
_ABSOLUTE_PREFIXES = ("http://", "https://", "#", "mailto:", "data:")

# Rendered by the VS Code Marketplace rather than by a Python packaging config.
_EXTRA_PUBLISHED = (Path("packages/editors/vscode/README.md"),)


def _published_readmes() -> list[Path]:
    """Every README a package publishes, resolved to a path under the repo root."""
    found: list[Path] = []
    for pyproject in sorted(REPO_ROOT.glob("packages/*/*/pyproject.toml")):
        config = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        readme = config.get("project", {}).get("readme")
        if isinstance(readme, str):
            found.append(pyproject.parent / readme)
    found.extend(REPO_ROOT / path for path in _EXTRA_PUBLISHED)
    # A package may symlink the repo-root README, so the same file can arrive
    # twice under different paths.
    return sorted({path.resolve() for path in found if path.is_file()})


def check() -> list[str]:
    problems: list[str] = []
    for readme in _published_readmes():
        where = readme.relative_to(REPO_ROOT)
        for number, line in enumerate(readme.read_text(encoding="utf-8").splitlines(), start=1):
            targets = _MARKDOWN_TARGET_RE.findall(line) + _IMG_SRC_RE.findall(line)
            for target in targets:
                if not target.startswith(_ABSOLUTE_PREFIXES):
                    problems.append(
                        f"{where}:{number} links to '{target}' by relative path; "
                        f"published READMEs need an absolute URL"
                    )
    return problems
