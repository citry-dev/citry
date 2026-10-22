"""
A README that ships outside the repository must not link to it by relative path.

PyPI and the VS Code Marketplace render these files on their own domains, where
`docs/assets/citry-wordmark.png` or `./LICENSE` resolves against *their* site and
404s. GitHub resolves the same path fine, so a broken link is invisible until
someone opens the package page.

Every reference in a published README therefore has to be absolute: an image at
`https://raw.githubusercontent.com/...`, a repository file at
`https://github.com/citry-dev/citry/blob/main/...`. In-page anchors (`#usage`)
are fine, since they stay inside the rendered document.

Which files count as published: the `readme` a packaging config points at, plus
the VS Code extension's own README.

The check reads each file whole rather than line by line, because an HTML tag
often spreads its attributes over several lines. It checks Markdown link and
image targets and the `src`, `srcset`, `href`, and `poster` attributes of any
HTML tag, including every candidate in a `srcset` list. Fenced code blocks are
skipped: their text is shown as code, not followed as a link.
"""

import re
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python < 3.11
    import tomli as tomllib  # type: ignore[import-untyped, no-redef]

REPO_ROOT = Path(__file__).resolve().parents[2]

# `[text](target)` in Markdown. Markdown images are the link form with a
# leading `!`, so one pattern covers both.
_MARKDOWN_TARGET_RE = re.compile(r"\]\(([^)\s]+)")
# An HTML start tag, which may run over several lines (`[^>]` matches a line
# break), and the attributes in it that load or link another file. A quoted
# value is skipped whole, so a `>` inside one does not end the tag early. The
# leading whitespace keeps a template attribute such as `c-href` out.
_HTML_TAG_RE = re.compile(r"<[A-Za-z](?:[^>\"']|\"[^\"]*\"|'[^']*')*>")
_HTML_LINK_ATTR_RE = re.compile(r"\s(src|srcset|href|poster)\s*=\s*([\"'])(.*?)\2", re.IGNORECASE | re.DOTALL)
# The line that opens a fenced code block: three or more backticks or tildes,
# indented by at most three spaces. A backtick fence's info text cannot hold a
# backtick, so a line such as ```code``` is inline code, not a fence.
_FENCE_OPEN_RE = re.compile(r" {0,3}(?P<fence>`{3,}(?=[^`]*$)|~{3,})")

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


def _blank_fences(text: str) -> str:
    """Replace every fenced code block with blank lines, keeping the line numbers of the rest."""
    lines = text.split("\n")
    fence = ""
    for index, line in enumerate(lines):
        if not fence:
            match = _FENCE_OPEN_RE.match(line)
            if match:
                fence = match.group("fence")
                lines[index] = ""
            continue
        # A block closes at a line of the same character, at least as long
        # as the opening fence, with nothing after it but spaces. A block
        # that never closes runs to the end of the file, as Markdown renders it.
        stripped = line.strip()
        if not line.startswith("    ") and stripped.startswith(fence) and set(stripped) == {fence[0]}:
            fence = ""
        lines[index] = ""
    return "\n".join(lines)


def _targets(text: str) -> list[tuple[int, str]]:
    """Return each link target in the README text with the offset where it starts."""
    found = [(match.start(1), match.group(1)) for match in _MARKDOWN_TARGET_RE.finditer(text)]
    for tag in _HTML_TAG_RE.finditer(text):
        for attr in _HTML_LINK_ATTR_RE.finditer(tag.group(0)):
            name, value = attr.group(1).lower(), attr.group(3)
            offset = tag.start() + attr.start(3)
            if name != "srcset" or value.lstrip().startswith("data:"):
                found.append((offset, value.strip()))
                continue
            # A srcset lists candidates as "url [descriptor]", separated by
            # commas, and each url needs the same check as a src.
            for candidate in value.split(","):
                url = candidate.split()[0] if candidate.split() else ""
                if url:
                    found.append((offset, url))
    return sorted(found)


def check() -> list[str]:
    problems: list[str] = []
    for readme in _published_readmes():
        where = readme.relative_to(REPO_ROOT)
        text = _blank_fences(readme.read_text(encoding="utf-8"))
        for offset, target in _targets(text):
            if not target.startswith(_ABSOLUTE_PREFIXES):
                number = text.count("\n", 0, offset) + 1
                problems.append(
                    f"{where}:{number} links to '{target}' by relative path; published READMEs need an absolute URL"
                )
    return problems
