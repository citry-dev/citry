"""
Pin every third-party GitHub Action to a full commit SHA.

A tag such as `actions/checkout@v7` can be moved, or rewritten by whoever
controls the action's repository, and the next workflow run then executes the
new code with this repository's tokens and secrets. A 40-character commit SHA
always names the same code. This validator reports every `uses:` value in a
workflow or a composite action under `.github/` that names an action or a
reusable workflow by tag or branch, and every SHA pin that lacks the trailing
`# <tag>` comment Dependabot reads to propose updates. Local actions (`./...`)
and Docker images (`docker://...`) are not checked.
"""

import re
from pathlib import Path

import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[2]

# Lowercase only: GitHub accepts either case, but Dependabot and the other
# validators compare SHAs as written, so one spelling keeps them matching.
_SHA_RE = re.compile(r"[0-9a-f]{40}")
_COMMENT_RE = re.compile(r"\s*#\s*\S")


def _files(root: Path) -> list[Path]:
    github = root / ".github"
    patterns = ("workflows/*.yml", "workflows/*.yaml", "actions/**/action.yml", "actions/**/action.yaml")
    return sorted(path for pattern in patterns for path in github.glob(pattern))


def _uses_values(node: yaml.Node) -> list[yaml.Node]:
    """Return every value stored under a `uses` key anywhere below this node."""
    # Walking the composed YAML, not the raw lines, finds every spelling
    # GitHub accepts: flow mappings, quoted keys, and a value on the next line.
    found: list[yaml.Node] = []
    if isinstance(node, yaml.MappingNode):
        for key, value in node.value:
            if isinstance(key, yaml.ScalarNode) and key.value == "uses":
                found.append(value)
            found.extend(_uses_values(value))
    elif isinstance(node, yaml.SequenceNode):
        for item in node.value:
            found.extend(_uses_values(item))
    return found


def check(root: Path = ROOT) -> list[str]:
    problems: list[str] = []
    for path in _files(root):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        document = yaml.compose(text)
        if document is None:
            continue
        lines = text.splitlines()
        for value in _uses_values(document):
            where = f"{relative}:{value.start_mark.line + 1}"
            if not isinstance(value, yaml.ScalarNode):
                problems.append(f"{where} has a `uses:` value that is not a single string")
                continue
            ref = value.value
            # A local action runs code from this checkout, so there is no tag
            # to move. Docker images are outside this check.
            if ref.startswith(("./", "docker://")):
                continue
            _, _, version = ref.partition("@")
            if not _SHA_RE.fullmatch(version):
                problems.append(
                    f"{where} uses {ref}; pin the action or reusable workflow to its full lowercase "
                    "commit SHA with the tag as a comment, such as `@<40-hex sha> # v7`"
                )
                continue
            # YAML drops comments, so read what follows the value on its own
            # line. Without the comment Dependabot cannot tell which release
            # line the SHA belongs to, so it never proposes an update.
            rest = lines[value.end_mark.line][value.end_mark.column :]
            if not _COMMENT_RE.match(rest):
                problems.append(f"{where} pins {ref} without a `# <tag>` comment naming its release")
    return problems
