"""The published README validator finds relative links wherever a README puts them."""

from pathlib import Path

import pytest
from scripts.validators import published_readme_links


def _check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, readme: str) -> list[str]:
    package = tmp_path / "packages" / "py" / "demo"
    package.mkdir(parents=True)
    (package / "pyproject.toml").write_text('[project]\nname = "demo"\nreadme = "README.md"\n', encoding="utf-8")
    (package / "README.md").write_text(readme, encoding="utf-8")
    monkeypatch.setattr(published_readme_links, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(published_readme_links, "_EXTRA_PUBLISHED", ())
    return published_readme_links.check()


def _problem(line: int, target: str) -> str:
    return (
        f"packages/py/demo/README.md:{line} links to '{target}' by relative path; "
        "published READMEs need an absolute URL"
    )


@pytest.mark.parametrize(
    ("readme", "line", "target"),
    [
        # Markdown links and images, the case the check began with.
        ("See [the license](./LICENSE).\n", 1, "./LICENSE"),
        ("![chart](docs/assets/chart.png)\n", 1, "docs/assets/chart.png"),
        # An <img> whose src sits on its own line.
        ('Intro\n\n<img\n  alt="Chart"\n  src="docs/assets/chart.png"\n>\n', 5, "docs/assets/chart.png"),
        # The dark image of a <picture>, given only in a srcset.
        (
            '<picture>\n  <source\n    media="(prefers-color-scheme: dark)"\n'
            '    srcset="docs/assets/dark.png"\n  >\n</picture>\n',
            4,
            "docs/assets/dark.png",
        ),
        # A later srcset candidate is checked as well as the first.
        (
            '<img srcset="https://example.com/a.png 1x, docs/b.png 2x" src="https://example.com/a.png">\n',
            1,
            "docs/b.png",
        ),
        # An HTML link around an image.
        ('<a href="docs/tutorial.md">\n  <img src="https://example.com/t.png">\n</a>\n', 1, "docs/tutorial.md"),
    ],
)
def test_a_relative_target_is_reported_with_its_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, readme: str, line: int, target: str
) -> None:
    assert _check(tmp_path, monkeypatch, readme) == [_problem(line, target)]


def test_absolute_targets_anchors_and_code_examples_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    readme = (
        "[Docs](https://citry.dev/) and [usage](#usage).\n"
        "<picture>\n"
        '  <source srcset="https://example.com/dark.png">\n'
        '  <img\n    src="https://example.com/light.png"\n  >\n'
        "</picture>\n"
        # A fenced example is shown as code, not followed as a link, and a
        # template attribute such as c-href is not an HTML link.
        '```html\n<img src="local.png">\n<a c-href="url">x</a>\n```\n'
    )
    assert _check(tmp_path, monkeypatch, readme) == []


@pytest.mark.parametrize(
    "fence",
    [
        # A closing fence may be longer than the opening one.
        '```\n<img src="inside.png">\n````\n',
        # Backticks on both sides of the text make inline code, not a fence.
        "```inline code```\n",
    ],
)
def test_text_after_a_code_block_is_still_checked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fence: str) -> None:
    readme = f"{fence}\n![chart](docs/chart.png)\n"
    line = readme.count("\n", 0, readme.index("![chart]")) + 1
    assert _check(tmp_path, monkeypatch, readme) == [_problem(line, "docs/chart.png")]


def test_a_greater_than_sign_in_a_value_does_not_end_the_tag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    readme = '<img alt="a > b" src="docs/chart.png">\n'
    assert _check(tmp_path, monkeypatch, readme) == [_problem(1, "docs/chart.png")]
