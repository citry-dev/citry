"""
Keep pull request and dispatch values out of the text of `run:` scripts.

GitHub Actions replaces each `${{ ... }}` before the shell starts, so a value
written straight into a `run:` block becomes part of the script. GitHub's
hardening guidance is to pass such a value through `env:` and read it as
`"$NAME"`, so the shell treats it as data. This validator reports every
`run:` block, and every `actions/github-script` `script:`, in a workflow or a
composite action, whose `${{ ... }}` expressions read the event payload
(`github.event.*`), the pull request branch (`github.head_ref`), or a
workflow input (`inputs.*`). Other contexts, such as `matrix.*`,
`steps.*.outputs` and `needs.*.outputs`, are not checked. When a job output
or an `env:` value carries one of these values, read it from the
environment too.
"""

import re
from pathlib import Path

import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[2]

_EXPRESSION_RE = re.compile(r"\$\{\{(.*?)\}\}", re.DOTALL)
# `github.event` but not `github.event_name`; `inputs.` only as a context
# name, not as the tail of a longer property path. Actions accepts the index
# form (`github['head_ref']`) and any letter case, so both are matched too.
_UNTRUSTED_RE = re.compile(
    r"\bgithub\s*(?:\.\s*|\[\s*['\"])(?:event\b(?!_)|head_ref\b)|(?<![\w.])inputs\s*(?:\.|\[)",
    re.IGNORECASE,
)


def _files(root: Path) -> list[Path]:
    github = root / ".github"
    patterns = ("workflows/*.yml", "workflows/*.yaml", "actions/**/action.yml", "actions/**/action.yaml")
    return sorted(path for pattern in patterns for path in github.glob(pattern))


def _run_scripts(node: yaml.Node) -> list[tuple[int, str]]:
    """Return the line and text of every string `run:` or `script:` value under this node."""
    found: list[tuple[int, str]] = []
    if isinstance(node, yaml.MappingNode):
        for key, value in node.value:
            # `defaults: run:` holds a mapping (shell, working-directory), not
            # a script, so only a string value is a step's script. A
            # `script:` key only appears as the input of actions/github-script,
            # whose JavaScript gets the same text replacement as a shell script.
            if key.value in {"run", "script"} and isinstance(value, yaml.ScalarNode):
                found.append((value.start_mark.line + 1, value.value))
            else:
                found.extend(_run_scripts(value))
    elif isinstance(node, yaml.SequenceNode):
        for item in node.value:
            found.extend(_run_scripts(item))
    return found


def check(root: Path = ROOT) -> list[str]:
    """Return one problem for each untrusted expression written into a `run:` script."""
    problems: list[str] = []
    for path in _files(root):
        document = yaml.compose(path.read_text(encoding="utf-8"))
        if document is None:
            continue
        relative = path.relative_to(root).as_posix()
        for line, script in _run_scripts(document):
            for expression in _EXPRESSION_RE.findall(script):
                if _UNTRUSTED_RE.search(expression):
                    problems.append(
                        f"{relative}:{line}: the script starting on this line contains `${{{{{expression}}}}}`; "
                        "pass the value through `env:` and read it from the environment in the script"
                    )
    return problems
