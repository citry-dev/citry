"""A case's edits decide what every tool sees, so a wrong edit must stop the run instead of testing another page."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

import pytest
from citry_errors import work
from citry_errors.cli import port_problems
from citry_errors.config import ConfigError, Edit, Framework, load_port
from citry_errors.work import apply_edits, changed_files, materialize

if TYPE_CHECKING:
    from pathlib import Path

PAGE = "<h1>Projects</h1>\n<p>Owner: {{ owner.name }}</p>\n<p>API: /api</p>\n"


def _framework(tmp_path: Path, page: str = PAGE) -> Framework:
    root = tmp_path / "frameworks" / "jinja"
    (root / "baseline" / "templates").mkdir(parents=True)
    (root / "baseline" / "templates" / "index.html").write_text(page)
    return Framework("jinja", "Jinja", (), (), (), None, "", root)


def _port(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "cases" / "m08-attribute-typo" / "jinja" / "port.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    return path


EDITED = """\
status = "ported"
mistake = { file = "templates/index.html", contains = "owner.nmae" }

[[edits]]
file = "templates/index.html"
old = "owner.name"
new = "owner.nmae"
"""


def test_edits_are_applied_to_the_clean_text_in_any_order() -> None:
    edits = [Edit("f", "API", "Api"), Edit("f", "Projects", "Projcts")]
    expected = "<h1>Projcts</h1>\n<p>Owner: {{ owner.name }}</p>\n<p>Api: /api</p>\n"
    assert apply_edits(PAGE, edits, "case") == expected
    assert apply_edits(PAGE, edits[::-1], "case") == expected
    # Edits that share no characters are allowed, even when one ends where the next begins.
    assert apply_edits("abcd", [Edit("f", "ab", "x"), Edit("f", "cd", "y")], "case") == "xy"


@pytest.mark.parametrize(
    ("text", "edits", "message"),
    [
        (PAGE, [Edit("f", "Ownr", "x")], "is not in f"),
        (PAGE, [Edit("f", "<p>", "<div>")], "appears more than once"),
        # str.count would see one "aa" in "aaa"; the second match overlaps the first.
        ("aaa", [Edit("f", "aa", "b")], "appears more than once"),
        (PAGE, [Edit("f", "Owner: {{", "x"), Edit("f", "{{ owner", "y")], "overlap"),
    ],
)
def test_an_edit_that_does_not_match_exactly_once_is_rejected(text: str, edits: list[Edit], message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        apply_edits(text, edits, "case")


def test_a_port_reads_edits_and_rejects_ones_that_cannot_be_meant(tmp_path: Path) -> None:
    port = load_port(_port(tmp_path, EDITED))
    assert port.edits == (Edit("templates/index.html", "owner.name", "owner.nmae"),)
    assert port.files == {}
    with pytest.raises(ConfigError, match="empty old text"):
        load_port(_port(tmp_path, EDITED.replace('old = "owner.name"', 'old = ""')))
    with pytest.raises(ConfigError, match="changes nothing"):
        load_port(_port(tmp_path, EDITED.replace('new = "owner.nmae"', 'new = "owner.name"')))
    (tmp_path / "cases" / "m08-attribute-typo" / "jinja" / "index.html").write_text(PAGE)
    both = EDITED.replace('status = "ported"', 'status = "ported"\nfiles = { "templates/index.html" = "index.html" }')
    with pytest.raises(ConfigError, match="both replaces and edits"):
        load_port(_port(tmp_path, both))
    neither = 'status = "ported"\nmistake = { file = "templates/index.html", contains = "x" }\n'
    with pytest.raises(ConfigError, match="needs files or edits"):
        load_port(_port(tmp_path, neither))
    elsewhere = EDITED.replace('mistake = { file = "templates/index.html"', 'mistake = { file = "main.py"')
    with pytest.raises(ConfigError, match="not one of the changed files"):
        load_port(_port(tmp_path, elsewhere))
    with pytest.raises(ConfigError, match="unknown keys"):
        load_port(_port(tmp_path, EDITED + 'extra = "x"\n'))


HEAD = 'status = "ported"\nmistake = { file = "templates/index.html", contains = "x" }\n'


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (HEAD + 'edits = { file = "templates/index.html", old = "a", new = "b" }\n', "must be a list"),
        (HEAD + 'edits = ["owner.name"]\n', "must be a table"),
        (HEAD + 'edits = [{ file = "templates/index.html", old = "a" }]\n', "missing"),
        (HEAD + 'edits = [{ file = "templates/index.html", old = 1, new = "b" }]\n', "needs text"),
        (HEAD + 'files = "index.html"\n', "files must be a table"),
        (HEAD + 'files = { "templates/index.html" = 1 }\n', "files must be a table"),
    ],
)
def test_a_port_with_edits_or_files_of_the_wrong_shape_names_its_file(tmp_path: Path, body: str, message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        load_port(_port(tmp_path, body))


def test_materialize_writes_the_edited_file_and_finds_the_mistake_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(work, "CACHE", tmp_path / "cache")
    framework = _framework(tmp_path)
    copy = materialize(framework, load_port(_port(tmp_path, EDITED)))
    assert (copy.path / "templates" / "index.html").read_text() == PAGE.replace("owner.name", "owner.nmae")
    assert copy.mistake_line == 2
    # The clean app is left as it was.
    assert (framework.baseline / "templates" / "index.html").read_text() == PAGE


def test_an_edited_file_keeps_its_line_endings(tmp_path: Path) -> None:
    framework = _framework(tmp_path)
    (framework.baseline / "templates" / "index.html").write_bytes(PAGE.replace("\n", "\r\n").encode())
    changed = changed_files(framework, load_port(_port(tmp_path, EDITED)))
    assert changed["templates/index.html"] == PAGE.replace("owner.name", "owner.nmae").replace("\n", "\r\n").encode()


def test_validate_names_the_case_when_the_baseline_no_longer_matches(tmp_path: Path) -> None:
    port = load_port(_port(tmp_path, EDITED))
    assert port_problems(_framework(tmp_path), port) == []
    renamed = _framework(tmp_path / "renamed", PAGE.replace("owner.name", "owner.full_name"))
    [problem] = port_problems(renamed, port)
    assert str(port.root) in problem
    assert "'owner.name' is not in templates/index.html" in problem
    missing = _framework(tmp_path / "missing")
    (missing.baseline / "templates" / "index.html").unlink()
    [problem] = port_problems(missing, port)
    assert problem == f"{port.root} edits 'templates/index.html', which the baseline does not have"
    # The edited text, not the clean text, must carry the mistake on one line.
    twice = _framework(tmp_path / "twice", PAGE + "<!-- owner.nmae -->\n")
    assert port_problems(twice, port) == [f"{port.root}: mistake text is on 2 lines, expected 1"]


def test_a_case_can_still_replace_a_whole_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(work, "CACHE", tmp_path / "cache")
    framework = _framework(tmp_path)
    copied = "<h1>Projects</h1>\n<p>Owner: {{ owner.nmae }}</p>\n"
    path = _port(
        tmp_path,
        'status = "ported"\nfiles = { "templates/index.html" = "index.html" }\n'
        'mistake = { file = "templates/index.html", contains = "owner.nmae" }\n',
    )
    (path.parent / "index.html").write_text(copied)
    port = load_port(path)
    copy = materialize(framework, port)
    assert (copy.path / "templates" / "index.html").read_text() == copied
    assert copy.mistake_line == 2
    assert port_problems(framework, port) == []
    # A copy may only stand in for a file the clean app has.
    (framework.baseline / "templates" / "index.html").unlink()
    [problem] = port_problems(framework, port)
    assert problem == f"{port.root} replaces 'templates/index.html', which the baseline does not have"


@pytest.mark.parametrize(
    "path",
    [
        "/etc/passwd",
        "../frameworks/next/baseline/app/page.tsx",
        "templates/../../outside.html",
        "./templates/index.html",
        "templates//index.html",
        "templates/",
        "",
        "templates\\..\\..\\outside.html",
        "C:/outside.html",
        "c:outside.html",
        ".",
        "..",
        "templates/index\u0000.html",
        "templates/index.html\n",
        "templates/index.html.",
        "templates /index.html",
        ".. /outside.html",
    ],
)
def test_a_path_that_could_leave_the_working_copy_is_rejected_when_the_port_loads(tmp_path: Path, path: str) -> None:
    # A JSON string is also a valid TOML basic string, so backslashes reach the loader as written.
    spelled = json.dumps(path)
    named = re.escape(repr(path))
    edited = EDITED.replace('file = "templates/index.html"', f"file = {spelled}")
    with pytest.raises(ConfigError, match=f"edit 0 edits {named}, which must be a plain relative path"):
        load_port(_port(tmp_path, edited))
    head = 'status = "ported"\nmistake = { file = "a", contains = "x" }\n'
    with pytest.raises(ConfigError, match=f"replaces {named}, which must be a plain relative path"):
        load_port(_port(tmp_path, head + f"files = {{ {spelled} = 'index.html' }}\n"))
    with pytest.raises(ConfigError, match=f"copies from {named}"):
        load_port(_port(tmp_path, head + f"files = {{ a = {spelled} }}\n"))


def test_a_nested_path_is_accepted_and_a_link_out_of_the_baseline_is_not(tmp_path: Path) -> None:
    framework = _framework(tmp_path)
    port = load_port(_port(tmp_path, EDITED))
    assert port.edits[0].file == "templates/index.html"
    assert port_problems(framework, port) == []
    # A link inside the baseline passes the text check but would read a file from outside it.
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "index.html").write_text(PAGE)
    (framework.baseline / "templates" / "index.html").unlink()
    (framework.baseline / "templates").rmdir()
    (framework.baseline / "templates").symlink_to(outside)
    [problem] = port_problems(framework, port)
    assert problem == f"{port.root} names 'templates/index.html', which resolves outside the baseline"


def test_a_copy_may_sit_in_a_subfolder_but_not_link_out_of_the_case(tmp_path: Path) -> None:
    head = 'status = "ported"\nmistake = { file = "templates/index.html", contains = "x" }\n'
    path = _port(tmp_path, head + 'files = { "templates/index.html" = "sub/index.html" }\n')
    (path.parent / "sub").mkdir()
    (path.parent / "sub" / "index.html").write_text("x\n")
    framework = _framework(tmp_path)
    port = load_port(path)
    assert port.files == {"templates/index.html": path.parent / "sub" / "index.html"}
    assert port_problems(framework, port) == []
    # A link next to port.toml would copy a file from anywhere into the working copy.
    (tmp_path / "secret.txt").write_text("x\n")
    (path.parent / "sub" / "index.html").unlink()
    (path.parent / "sub" / "index.html").symlink_to(tmp_path / "secret.txt")
    with pytest.raises(
        ConfigError, match=re.escape("copies from 'sub/index.html', which resolves outside the case folder")
    ):
        load_port(path)
    # The baseline side of a copy is resolved as well.
    (path.parent / "sub" / "index.html").unlink()
    (path.parent / "sub" / "index.html").write_text("x\n")
    (framework.baseline / "templates" / "index.html").unlink()
    (framework.baseline / "templates" / "index.html").symlink_to(tmp_path / "secret.txt")
    [problem] = port_problems(framework, load_port(path))
    assert problem.endswith("names 'templates/index.html', which resolves outside the baseline")


def test_one_file_cannot_be_changed_under_two_spellings(tmp_path: Path) -> None:
    (tmp_path / "cases" / "m08-attribute-typo" / "jinja").mkdir(parents=True)
    (tmp_path / "cases" / "m08-attribute-typo" / "jinja" / "index.html").write_text(PAGE)
    copied = EDITED.replace(
        'status = "ported"', 'status = "ported"\nfiles = { "Templates/INDEX.html" = "index.html" }'
    )
    with pytest.raises(
        ConfigError, match=re.escape("names 'templates/index.html', the same file as 'Templates/INDEX.html'")
    ):
        load_port(_port(tmp_path, copied))
    second = EDITED + '\n[[edits]]\nfile = "templates/Index.html"\nold = "API"\nnew = "Api"\n'
    with pytest.raises(
        ConfigError, match=re.escape("edit 1 names 'templates/Index.html', the same file as 'templates/index.html'")
    ):
        load_port(_port(tmp_path, second))


def test_a_change_inside_a_folder_the_working_copy_leaves_out_is_reported(tmp_path: Path) -> None:
    framework = _framework(tmp_path)
    (framework.baseline / "node_modules").mkdir()
    (framework.baseline / "node_modules" / "x.js").write_text("owner.name\n")
    port = load_port(_port(tmp_path, EDITED.replace("templates/index.html", "node_modules/x.js")))
    [problem] = port_problems(framework, port)
    assert problem.endswith("names 'node_modules/x.js', inside a folder the working copy leaves out")
