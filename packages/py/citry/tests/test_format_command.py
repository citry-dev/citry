"""Behavior tests for the development-only ``citry format`` command."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from pathlib import Path

import pytest

import citry._embedded_provider as embedded_provider_module
from citry.__main__ import main
from citry._embedded_provider import (
    BiomeEmbeddedProvider,
    EmbeddedProviderInvalidError,
    EmbeddedProviderLanguage,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
CORPUS_ROOT = REPO_ROOT / "crates" / "citry_template_formatter" / "tests" / "fixtures" / "v1"
_TEST_PROVIDER_MARKER = b"#!/bin/sh\n# citry-test-self-contained-provider\n"
_validate_real_executable = embedded_provider_module._validate_self_contained_executable


@pytest.fixture(autouse=True)
def _sys_path_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the CLI's working-directory import path change local to each test."""
    monkeypatch.setattr(sys, "path", list(sys.path))

    def allow_explicit_test_provider(
        executable: Path,
        data: bytes,
        *,
        language: EmbeddedProviderLanguage,
    ) -> None:
        if data.startswith(_TEST_PROVIDER_MARKER):
            return
        _validate_real_executable(executable, data, language=language)

    monkeypatch.setattr(
        embedded_provider_module,
        "_validate_self_contained_executable",
        allow_explicit_test_provider,
    )


def _run_main(args: list[str]) -> int:
    try:
        return main(args)
    except SystemExit as error:
        return int(error.code)


def _component_source(template: str) -> str:
    return f"from citry import Component\n\nclass Card(Component):\n    template = {template!r}\n"


def _lock_directory_or_skip(directory: Path) -> None:
    """
    Make the directory unreadable, or skip when the filesystem ignores the request.

    Windows grants access through ACLs rather than the mode bits, so clearing them
    there leaves the directory perfectly readable and a test that expects the scan
    to fail instead watches it succeed. Asking the filesystem whether the lock took
    is more honest than checking the platform name, and it also covers running as
    root or a mounted share that ignores permissions.
    """
    directory.chmod(0)
    try:
        list(directory.iterdir())
    except OSError:
        return
    # The lock did not take, so put the directory back before bowing out.
    directory.chmod(0o700)
    pytest.skip("filesystem does not enforce directory permissions")


def _write_component_with_file(path: Path, template_file: str) -> None:
    path.write_text(
        f"from citry import Component\n\nclass Card(Component):\n    template_file = {template_file!r}\n",
        encoding="utf-8",
    )


def _write_fake_biome(path: Path) -> Path:
    if os.name == "nt":
        pytest.skip("this CLI provider behavior uses a POSIX shell fake")
    path.write_bytes(
        _TEST_PROVIDER_MARKER
        + b'if [ "$1" = "--version" ]; then printf \'2.5.6\'; exit 0; fi\n'
        + b"sed 's/  */ /g; s/ = /=/g; s/= /=/g; s/{ */{ /g; s/: */: /g; s/ *}/ }/g'\n"
    )
    path.chmod(0o755)
    return path


@pytest.mark.skipif(os.name != "nt", reason="Windows native-executable CLI coverage")
def test_windows_cli_accepts_a_native_provider(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executable = tmp_path / "biome.exe"
    shutil.copy2(sys.executable, executable)

    def fake_provider(
        _executable: Path,
        arguments: tuple[str, ...],
        *,
        input_text: str | None,
        **_kwargs: object,
    ) -> str:
        if arguments == ("--version",):
            return "2.5.6"
        assert input_text is not None
        return input_text.replace("  ", " ")

    monkeypatch.setattr(embedded_provider_module, "_run_provider", fake_provider)
    target = tmp_path / "component.js"
    target.write_text("const  value = 1;\n", encoding="utf-8")

    assert _run_main(["format", "--javascript-provider", f"biome:{executable}", str(target)]) == 0
    assert target.read_text(encoding="utf-8") == "const value = 1;\n"


def test_standalone_cli_consumes_the_shared_structural_corpus(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    index = json.loads((CORPUS_ROOT / "index.json").read_text(encoding="utf-8"))

    for position, case in enumerate(index["cases"]):
        source = case.get("input_text")
        if source is None:
            source = (CORPUS_ROOT / case["input"]).read_text(encoding="utf-8")
        target = tmp_path / f"case-{position}.citry-html"
        target.write_bytes(source.encode("utf-8"))

        expected_error = case.get("expected_error")
        if expected_error is not None:
            assert _run_main(["format", str(target)]) == 2, case["id"]
            assert target.read_bytes() == source.encode("utf-8"), case["id"]
            assert expected_error["code"] in capsys.readouterr().err, case["id"]
            continue

        expected = case.get("expected_text")
        if expected is None:
            expected = (CORPUS_ROOT / case["expected"]).read_text(encoding="utf-8")
        assert _run_main(["format", str(target)]) == 0, case["id"]
        assert target.read_bytes() == expected.encode("utf-8"), case["id"]
        capsys.readouterr()
        assert _run_main(["format", "--check", str(target)]) == 0, case["id"]
        capsys.readouterr()


def test_python_cli_consumes_the_shared_host_corpus(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    index = json.loads((CORPUS_ROOT / "index.json").read_text(encoding="utf-8"))

    for position, case in enumerate(index["python_hosts"]):
        source = case.get("input_text")
        if source is None:
            source = (CORPUS_ROOT / case["input"]).read_bytes().decode("utf-8")
        target = tmp_path / f"host-{position}.py"
        target.write_bytes(source.encode("utf-8"))

        expected_error = case.get("expected_error")
        if expected_error is not None:
            assert _run_main(["format", str(target)]) == 2, case["id"]
            assert target.read_bytes() == source.encode("utf-8"), case["id"]
            assert expected_error["code"] in capsys.readouterr().err, case["id"]
            continue

        expected = case.get("expected_text")
        if expected is None:
            expected = (CORPUS_ROOT / case["expected"]).read_bytes().decode("utf-8")
        assert _run_main(["format", str(target)]) == 0, case["id"]
        assert target.read_bytes() == expected.encode("utf-8"), case["id"]
        capsys.readouterr()


def test_cli_consumes_every_applicable_shared_embedded_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    index = json.loads((CORPUS_ROOT / "index.json").read_text(encoding="utf-8"))
    biome = _write_fake_biome(tmp_path / "biome")
    active_case: dict[str, object] = {}

    def format_for_case(
        provider: BiomeEmbeddedProvider,
        source: str,
        *,
        source_path: Path,
    ) -> tuple[str, str]:
        del source_path
        results = active_case["results"]
        for raw in results:  # type: ignore[union-attr]
            if raw["status"] == "error":
                raise EmbeddedProviderInvalidError(raw["message"])
            if raw["status"] in {"formatted", "duplicate", "stale-plan"}:
                language = active_case["requests"][raw["region"]]["language"]  # type: ignore[index]
                if provider.language == language:
                    return raw["text"], f"fake-{language}@1+sha256:fixture"
        return source, f"fake-{provider.language}@1+sha256:fixture"

    monkeypatch.setattr(BiomeEmbeddedProvider, "format_source_with_identity", format_for_case)
    exercised: set[str] = set()
    result_validation: set[str] = set()
    for position, case in enumerate(index["embedded_cases"]):
        if case["category"] == "result-validation" and case["id"] != "embedded-formatting.results.delimiter-conflict":
            result_validation.add(case["id"])
            continue
        active_case.clear()
        active_case.update(case)
        source = case.get("input_text")
        if source is None:
            source = (CORPUS_ROOT / case["input"]).read_text(encoding="utf-8")
        target = tmp_path / f"embedded-{position}.citry-html"
        target.write_text(source, encoding="utf-8")
        languages = {request["language"] for request in case["requests"]}
        args = ["format"]
        if case["id"] != "embedded-formatting.providers.unavailable":
            if "javascript" in languages:
                args.extend(("--javascript-provider", f"biome:{biome}"))
            if "css" in languages:
                args.extend(("--css-provider", f"biome:{biome}"))
        args.append(str(target))

        expected_error = case.get("expected_error")
        expected_code = 2 if expected_error is not None else 0
        assert _run_main(args) == expected_code, case["id"]
        captured = capsys.readouterr()
        if expected_error is not None:
            assert target.read_text(encoding="utf-8") == source, case["id"]
            assert expected_error["code"] in captured.err, case["id"]
            assert expected_error["contains"] in captured.err, case["id"]
        else:
            expected = case.get("expected_text")
            if expected is None:
                expected = (CORPUS_ROOT / case["expected"]).read_text(encoding="utf-8")
            assert target.read_text(encoding="utf-8") == expected, case["id"]
        exercised.add(case["id"])

    assert exercised | result_validation == {case["id"] for case in index["embedded_cases"]}
    assert result_validation == {
        "embedded-formatting.results.stale",
        "embedded-formatting.results.duplicate",
        "embedded-formatting.results.missing",
    }


@pytest.mark.parametrize("suffix", [".html", ".citry", ".citry-html"])
def test_explicit_standalone_file_write_check_and_diff_modes(
    suffix: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / f"card{suffix}"
    source = '<div  class = "card" ></div>'
    expected = '<div class="card"></div>'
    target.write_text(source, encoding="utf-8")

    assert _run_main(["format", "--check", str(target)]) == 1
    captured = capsys.readouterr()
    assert captured.out == f"would format: {target.name}\n"
    assert captured.err == "citry format: 1 would format, 0 unchanged, 0 skipped, 0 errored\n"
    assert target.read_text(encoding="utf-8") == source

    assert _run_main(["format", "--diff", str(target)]) == 1
    captured = capsys.readouterr()
    assert f"--- {target.name}\n+++ {target.name}\n" in captured.out
    assert f"-{source}\n\\ No newline at end of file\n" in captured.out
    assert f"+{expected}\n\\ No newline at end of file\n" in captured.out
    assert captured.err == "citry format: 1 would format, 0 unchanged, 0 skipped, 0 errored\n"
    assert target.read_text(encoding="utf-8") == source

    assert _run_main(["format", str(target)]) == 0
    captured = capsys.readouterr()
    assert captured.out == f"formatted: {target.name}\n"
    assert captured.err == "citry format: 1 formatted, 0 unchanged, 0 skipped, 0 errored\n"
    assert target.read_text(encoding="utf-8") == expected


def test_verbose_reports_the_pinned_python_provider(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "card.citry-html"
    target.write_text("<main></main>", encoding="utf-8")

    assert _run_main(["format", "--verbose", str(target)]) == 0

    captured = capsys.readouterr()
    assert (
        "citry-html@1, python-expressions:ruff@0.14.10+45bbb4cbff, javascript:unavailable, css:unavailable\n"
    ) in captured.err


def test_explicit_javascript_and_css_use_only_configured_providers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    biome = _write_fake_biome(tmp_path / "biome")
    javascript = tmp_path / "component.js"
    css = tmp_path / "component.css"
    javascript.write_text("const  value = 1;\n", encoding="utf-8")
    css.write_text(".card{color:red}\n", encoding="utf-8")

    assert (
        _run_main(
            [
                "format",
                "--verbose",
                "--javascript-provider",
                f"biome:{biome}",
                "--css-provider",
                f"biome:{biome}",
                str(javascript),
                str(css),
            ]
        )
        == 0
    )

    assert javascript.read_text(encoding="utf-8") == "const value=1;\n"
    assert css.read_text(encoding="utf-8") == ".card{ color: red }\n"
    captured = capsys.readouterr()
    assert captured.out == "formatted: component.css\nformatted: component.js\n"
    assert "javascript:biome@2.5.6+effective-options:per-target" in captured.err
    assert "css:biome@2.5.6+effective-options:per-target" in captured.err


def test_available_and_required_modes_report_missing_standalone_provider(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "component.js"
    target.write_text("const  value=1", encoding="utf-8")

    assert _run_main(["format", str(target)]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "citry.format.provider-unavailable" in captured.err
    assert target.read_text(encoding="utf-8") == "const  value=1"

    assert _run_main(["format", "--embedded", "required", str(target)]) == 2
    captured = capsys.readouterr()
    assert "citry.format.provider-unavailable" in captured.err
    assert target.read_text(encoding="utf-8") == "const  value=1"


def test_required_embedded_mode_respects_fmt_off(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "card.citry-html"
    source = "{# fmt: off #}<script>const  value=1;</script>"
    target.write_text(source, encoding="utf-8")

    assert _run_main(["format", "--embedded", "required", str(target)]) == 0

    captured = capsys.readouterr()
    assert "citry.format.embedded-suppressed" in captured.err
    assert target.read_text(encoding="utf-8") == source


def test_template_embedded_body_uses_the_explicit_provider_atomically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    biome = _write_fake_biome(tmp_path / "biome")
    target = tmp_path / "card.citry-html"
    target.write_text("<main><script>const  value = 1;</script></main>", encoding="utf-8")

    assert (
        _run_main(
            [
                "format",
                "--javascript-provider",
                f"biome:{biome}",
                str(target),
            ]
        )
        == 0
    )

    assert target.read_text(encoding="utf-8") == ("<main>\n  <script>\n    const value=1;\n  </script>\n</main>")
    assert "provider-invalid" not in capsys.readouterr().err


def test_invalid_provider_configuration_precedes_every_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "card.citry-html"
    source = '<div  class = "card" ></div>'
    target.write_text(source, encoding="utf-8")

    assert _run_main(["format", "--javascript-provider", "biome:relative/biome", str(target)]) == 2
    assert target.read_text(encoding="utf-8") == source
    assert "absolute path" in capsys.readouterr().err


def test_embedded_off_does_not_probe_explicit_provider(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    marker = tmp_path / "probed"
    provider = tmp_path / "biome"
    provider.write_text(
        f"#!/bin/sh\nprintf probed > {os.fspath(marker)!r}\nprintf '2.5.6'\n",
        encoding="utf-8",
    )
    provider.chmod(0o755)
    target = tmp_path / "card.citry-html"
    target.write_text("<script>const  value=1;</script>", encoding="utf-8")

    assert (
        _run_main(
            [
                "format",
                "--embedded=off",
                "--javascript-provider",
                f"biome:{provider}",
                str(target),
            ],
        )
        == 0
    )

    assert marker.exists() is False
    assert target.read_text(encoding="utf-8") == "<script>const  value=1;</script>"
    assert "provider" not in capsys.readouterr().err


def test_python_component_assets_format_as_one_atomic_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    biome = _write_fake_biome(tmp_path / "biome")
    target = tmp_path / "card.py"
    target.write_text(
        "from citry import Component\n\n"
        "class Card(Component):\n"
        '    template = """<main><script>const  inside = 1;</script></main>"""\n'
        '    js = """const  direct = 2;"""\n'
        '    css = """.card{color:red}"""\n',
        encoding="utf-8",
    )

    assert (
        _run_main(
            [
                "format",
                "--javascript-provider",
                f"biome:{biome}",
                "--css-provider",
                f"biome:{biome}",
                str(target),
            ]
        )
        == 0
    )

    output = target.read_text(encoding="utf-8")
    assert "const inside=1;" in output
    assert 'js = """const direct=2;"""' in output
    assert 'css = """.card{ color: red }"""' in output
    assert capsys.readouterr().out == "formatted: card.py\n"


def test_required_python_assets_do_not_expose_partial_template_edits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "card.py"
    source = (
        "from citry import Component\n\n"
        "class Card(Component):\n"
        '    template = """<main><section  id = \'x\' ></section></main>"""\n'
        '    js = """const  value = 1;"""\n'
    )
    target.write_text(source, encoding="utf-8")

    assert _run_main(["format", "--embedded", "required", str(target)]) == 2

    assert target.read_text(encoding="utf-8") == source
    assert "citry.format.provider-unavailable" in capsys.readouterr().err


def test_directory_discovers_only_proven_js_and_css_file_assets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    biome = _write_fake_biome(tmp_path / "biome")
    assets = tmp_path / "assets"
    assets.mkdir()
    javascript = assets / "card.asset"
    css = assets / "card.style"
    unrelated = assets / "unrelated.js"
    javascript.write_text("const  value = 1;\n", encoding="utf-8")
    css.write_text(".card{color:red}\n", encoding="utf-8")
    unrelated.write_text("const  untouched = 1;\n", encoding="utf-8")
    (tmp_path / "card.py").write_text(
        "from citry import Component\n\n"
        "class Card(Component):\n"
        "    js_file = 'assets/card.asset'\n"
        "    css_file = 'assets/card.style'\n",
        encoding="utf-8",
    )

    assert (
        _run_main(
            [
                "format",
                "--javascript-provider",
                f"biome:{biome}",
                "--css-provider",
                f"biome:{biome}",
                ".",
            ]
        )
        == 0
    )

    assert javascript.read_text(encoding="utf-8") == "const value=1;\n"
    assert css.read_text(encoding="utf-8") == ".card{ color: red }\n"
    assert unrelated.read_text(encoding="utf-8") == "const  untouched = 1;\n"
    captured = capsys.readouterr()
    assert captured.out == (
        f"formatted: {Path('assets') / 'card.asset'}\nformatted: {Path('assets') / 'card.style'}\n"
    )


def test_no_path_scans_current_directory_without_claiming_unrelated_html(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    component = tmp_path / "card.py"
    private = tmp_path / "_private.py"
    unrelated = tmp_path / "page.html"
    component.write_text(_component_source("""<div  id = "card" ></div>"""), encoding="utf-8")
    private.write_text(_component_source("""<i  id = "private" ></i>"""), encoding="utf-8")
    unrelated.write_text('<main  id = "page" ></main>', encoding="utf-8")

    assert _run_main(["format"]) == 0

    assert '<div id="card"></div>' in component.read_text(encoding="utf-8")
    assert '<i  id = "private" ></i>' in private.read_text(encoding="utf-8")
    assert unrelated.read_text(encoding="utf-8") == '<main  id = "page" ></main>'
    captured = capsys.readouterr()
    assert captured.out == "formatted: card.py\n"
    assert captured.err == "citry format: 1 formatted, 0 unchanged, 0 skipped, 0 errored\n"


def test_directory_discovers_direct_template_files_and_deduplicates_overlapping_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    templates = tmp_path / "templates"
    templates.mkdir()
    template = templates / "card.tpl"
    template.write_text('<article  class = "card" ></article>', encoding="utf-8")
    component = tmp_path / "card.py"
    component.write_text(
        "from citry import Component, LibraryComponent\n\n"
        "class Card(Component):\n"
        "    template_file = 'templates/card.tpl'\n\n"
        "class CardLibrary(LibraryComponent):\n"
        "    template_file = 'templates/card.tpl'\n",
        encoding="utf-8",
    )

    assert _run_main(["format", ".", str(component)]) == 0

    assert template.read_text(encoding="utf-8") == '<article class="card"></article>'
    captured = capsys.readouterr()
    assert captured.out == f"formatted: {Path('templates') / 'card.tpl'}\n"
    assert captured.err == "citry format: 1 formatted, 0 unchanged, 1 skipped, 0 errored\n"


def test_directory_file_discovery_ignores_indefinite_decorated_class(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    template = tmp_path / "decorated.tpl"
    template.write_text('<div  id = "untouched" ></div>', encoding="utf-8")
    (tmp_path / "components.py").write_text(
        "from citry import Component\n\n"
        "def decorate(value):\n"
        "    return value\n\n"
        "@decorate\n"
        "class Decorated(Component):\n"
        "    template_file = 'decorated.tpl'\n",
        encoding="utf-8",
    )

    assert _run_main(["format", "."]) == 0

    assert template.read_text(encoding="utf-8") == '<div  id = "untouched" ></div>'
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "citry format: 0 formatted, 0 unchanged, 1 skipped, 0 errored\n"


@pytest.mark.parametrize(
    ("declaration", "message"),
    [
        ("template_file = choose_template()", "computed template_file"),
        ("template_file = b'card.html'", "template_file must be a string or None"),
        (
            "template_lang = choose_language()\n    template_file = 'card.html'",
            "template language cannot be proven",
        ),
        (
            "template_lang = 'markdown'\n    template_file = 'card.html'",
            "unsupported non-None template_lang",
        ),
    ],
)
def test_unsupported_definite_file_template_is_an_error(
    declaration: str,
    message: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "component.py").write_text(
        f"from citry import Component\n\nclass Card(Component):\n    {declaration}\n",
        encoding="utf-8",
    )

    assert _run_main(["format", "."]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert message in captured.err
    assert captured.err.endswith("citry format: 0 formatted, 0 unchanged, 0 skipped, 1 errored\n")


def test_unknown_multiple_base_language_with_file_template_is_an_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "component.py").write_text(
        "from citry import Component\n\n"
        "class Mixin:\n"
        "    pass\n\n"
        "class Card(Component, Mixin):\n"
        "    template_file = 'card.html'\n",
        encoding="utf-8",
    )

    assert _run_main(["format", "."]) == 2
    assert "template language cannot be proven" in capsys.readouterr().err


def test_directory_reports_escaping_missing_and_symlinked_template_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.chdir(root)
    outside = tmp_path / "outside.html"
    outside.write_text('<div  id = "outside" ></div>', encoding="utf-8")
    linked = root / "linked.html"
    linked.symlink_to(outside)
    (root / "components.py").write_text(
        "from citry import Component\n\n"
        "class Escape(Component):\n"
        "    template_file = '../outside.html'\n\n"
        "class Missing(Component):\n"
        "    template_file = 'missing.html'\n\n"
        "class Linked(Component):\n"
        "    template_file = 'linked.html'\n",
        encoding="utf-8",
    )

    assert _run_main(["format", "."]) == 2

    assert outside.read_text(encoding="utf-8") == '<div  id = "outside" ></div>'
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "escapes directory root" in captured.err
    assert "does not exist" in captured.err
    assert "resolves through a symlink" in captured.err
    assert captured.err.endswith("citry format: 0 formatted, 0 unchanged, 1 skipped, 3 errored\n")


def test_unreadable_declared_template_is_a_file_error_not_a_crash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    locked = tmp_path / "_locked"
    locked.mkdir()
    template = locked / "card.tpl"
    original = '<div  id = "card" ></div>'
    template.write_text(original, encoding="utf-8")
    _write_component_with_file(tmp_path / "component.py", "_locked/card.tpl")
    _lock_directory_or_skip(locked)

    try:
        assert _run_main(["format", "."]) == 2
    finally:
        locked.chmod(0o700)

    assert template.read_text(encoding="utf-8") == original
    captured = capsys.readouterr()
    assert "cannot be inspected" in captured.err
    assert captured.err.endswith("citry format: 0 formatted, 0 unchanged, 1 skipped, 1 errored\n")


def test_unreadable_explicit_directory_is_not_reported_clean(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    locked = tmp_path / "locked"
    locked.mkdir()
    component = locked / "component.py"
    original = _component_source('<div  id = "card" ></div>')
    component.write_text(original, encoding="utf-8")
    _lock_directory_or_skip(locked)

    try:
        assert _run_main(["format", str(locked)]) == 2
    finally:
        locked.chmod(0o700)

    assert component.read_text(encoding="utf-8") == original
    captured = capsys.readouterr()
    assert "directory cannot be scanned" in captured.err
    assert captured.err.endswith("citry format: 0 formatted, 0 unchanged, 0 skipped, 1 errored\n")


def test_invalid_static_template_file_value_is_an_error_not_a_false_clean(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    _write_component_with_file(tmp_path / "component.py", "bad\0name.html")

    assert _run_main(["format", "."]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Card.template_file contains a null byte" in captured.err
    assert captured.err.endswith("citry format: 0 formatted, 0 unchanged, 0 skipped, 1 errored\n")


def test_overlapping_directory_arguments_use_the_outer_normalized_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    subdirectory = tmp_path / "sub"
    templates = tmp_path / "templates"
    subdirectory.mkdir()
    templates.mkdir()
    template = templates / "card.tpl"
    template.write_text('<div  id = "card" ></div>', encoding="utf-8")
    _write_component_with_file(subdirectory / "card.py", "../templates/card.tpl")

    assert _run_main(["format", "--check", ".", "sub"]) == 1

    captured = capsys.readouterr()
    assert captured.out == f"would format: {Path('templates') / 'card.tpl'}\n"
    assert "escapes directory root" not in captured.err
    assert template.read_text(encoding="utf-8") == '<div  id = "card" ></div>'

    assert _run_main(["format", "--check", "sub"]) == 2
    assert "escapes directory root" in capsys.readouterr().err


def test_explicit_excluded_subdirectory_is_not_collapsed_into_outer_scan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    excluded_name = "_private"
    excluded = tmp_path / excluded_name
    excluded.mkdir()
    component = excluded / "card.py"
    component.write_text(_component_source('<div  id = "card" ></div>'), encoding="utf-8")

    assert _run_main(["format", ".", excluded_name]) == 0

    assert '<div id="card"></div>' in component.read_text(encoding="utf-8")
    captured = capsys.readouterr()
    assert captured.out == f"formatted: {Path(excluded_name) / 'card.py'}\n"
    assert captured.err == "citry format: 1 formatted, 0 unchanged, 0 skipped, 0 errored\n"


def test_non_roundtripping_python_encoding_is_refused_without_changing_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "component.py"
    original = (
        b"# coding: cp932\n"
        b"# untouched alias: \x87\x90\n"
        b"from citry import Component\n\n"
        b"class Card(Component):\n"
        b"    template = '<div  id = \"card\" ></div>'\n"
    )
    target.write_bytes(original)

    assert _run_main(["format", str(target)]) == 2

    assert target.read_bytes() == original
    captured = capsys.readouterr()
    assert "do not round-trip through declared encoding 'cp932'" in captured.err
    assert captured.err.endswith("citry format: 0 formatted, 0 unchanged, 0 skipped, 1 errored\n")


def test_template_write_revalidates_the_declaring_python_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from citry_core.template_formatter import format_template as core_format_template

    monkeypatch.chdir(tmp_path)
    component = tmp_path / "component.py"
    template = tmp_path / "template.tpl"
    _write_component_with_file(component, "template.tpl")
    original_template = '<div  id = "card" ></div>'
    template.write_text(original_template, encoding="utf-8")

    def mutate_declaration(source: str) -> str:
        candidate = core_format_template(source)
        component.write_text("answer = 42\n", encoding="utf-8")
        return candidate

    monkeypatch.setattr("citry._formatter.format_template", mutate_declaration)

    assert _run_main(["format", "."]) == 2

    assert template.read_text(encoding="utf-8") == original_template
    captured = capsys.readouterr()
    assert "declaring Python file contents changed during discovery" in captured.err


def test_formatter_owned_python_write_refreshes_file_template_authorization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    component = tmp_path / "a_component.py"
    template = tmp_path / "z_card.tpl"
    component.write_text(
        "from citry import Component\n\n"
        "class Inline(Component):\n"
        "    template = '<div  id = \"inline\" ></div>'\n\n"
        "class FileCard(Component):\n"
        "    template_file = 'z_card.tpl'\n",
        encoding="utf-8",
    )
    template.write_text('<article  id = "file" ></article>', encoding="utf-8")

    assert _run_main(["format", "."]) == 0

    assert '<div id="inline"></div>' in component.read_text(encoding="utf-8")
    assert template.read_text(encoding="utf-8") == '<article id="file"></article>'
    captured = capsys.readouterr()
    assert captured.out == "formatted: a_component.py\nformatted: z_card.tpl\n"
    assert captured.err == "citry format: 2 formatted, 0 unchanged, 0 skipped, 0 errored\n"


def test_refreshed_python_snapshot_must_reprove_each_file_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from citry import format_python_templates as host_format_templates

    monkeypatch.chdir(tmp_path)
    trigger = tmp_path / "a_trigger.py"
    declaring = tmp_path / "b_component.py"
    template = tmp_path / "z_card.tpl"
    trigger.write_text(_component_source('<div  id = "trigger" ></div>'), encoding="utf-8")
    _write_component_with_file(declaring, "z_card.tpl")
    original_template = '<article  id = "file" ></article>'
    template.write_text(original_template, encoding="utf-8")

    def replace_declaration(source: str):
        result = host_format_templates(source)
        if 'id = "trigger"' in source:
            declaring.write_text(_component_source('<div  id = "replacement" ></div>'), encoding="utf-8")
        return result

    monkeypatch.setattr("citry._formatter.format_python_templates", replace_declaration)

    assert _run_main(["format", ".", str(declaring)]) == 2

    assert '<div id="replacement"></div>' in declaring.read_text(encoding="utf-8")
    assert template.read_text(encoding="utf-8") == original_template
    captured = capsys.readouterr()
    assert "written Python source no longer authorizes this template_file target" in captured.err


def test_directory_template_target_refuses_an_ancestor_symlink_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from citry import format_python_templates as host_format_templates

    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.chdir(root)
    templates = root / "ztemplates"
    templates.mkdir()
    internal = templates / "card.tpl"
    internal_source = '<article  id = "internal" ></article>'
    internal.write_text(internal_source, encoding="utf-8")
    external_directory = tmp_path / "external"
    external_directory.mkdir()
    external = external_directory / "card.tpl"
    external_source = '<article  id = "external" ></article>'
    external.write_text(external_source, encoding="utf-8")
    component = root / "a_component.py"
    component.write_text(
        "from citry import Component\n\n"
        "class Trigger(Component):\n"
        "    template = '<div  id = \"trigger\" ></div>'\n\n"
        "class FileCard(Component):\n"
        "    template_file = 'ztemplates/card.tpl'\n",
        encoding="utf-8",
    )
    original_directory = root / "original-templates"

    def swap_template_parent(source: str):
        result = host_format_templates(source)
        templates.rename(original_directory)
        templates.symlink_to(external_directory, target_is_directory=True)
        return result

    monkeypatch.setattr("citry._formatter.format_python_templates", swap_template_parent)

    assert _run_main(["format", "."]) == 2

    assert (original_directory / "card.tpl").read_text(encoding="utf-8") == internal_source
    assert external.read_text(encoding="utf-8") == external_source
    captured = capsys.readouterr()
    assert "directory-discovered path no longer has a symlink-free route" in captured.err


def test_directory_python_target_refuses_an_ancestor_symlink_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from citry import format_python_templates as host_format_templates

    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.chdir(root)
    package = root / "zpackage"
    package.mkdir()
    internal = package / "component.py"
    internal_source = _component_source('<span  id = "internal" ></span>')
    internal.write_text(internal_source, encoding="utf-8")
    external_package = tmp_path / "external-package"
    external_package.mkdir()
    external = external_package / "component.py"
    external_source = _component_source('<span  id = "external" ></span>')
    external.write_text(external_source, encoding="utf-8")
    trigger = root / "a_trigger.py"
    trigger.write_text(_component_source('<div  id = "trigger" ></div>'), encoding="utf-8")
    original_package = root / "original-package"

    def swap_python_parent(source: str):
        result = host_format_templates(source)
        if 'id = "trigger"' in source:
            package.rename(original_package)
            package.symlink_to(external_package, target_is_directory=True)
        return result

    monkeypatch.setattr("citry._formatter.format_python_templates", swap_python_parent)

    assert _run_main(["format", "."]) == 2

    assert (original_package / "component.py").read_text(encoding="utf-8") == internal_source
    assert external.read_text(encoding="utf-8") == external_source
    captured = capsys.readouterr()
    assert "directory-discovered path no longer has a symlink-free route" in captured.err


def test_explicit_symlink_is_refused_but_an_explicit_external_file_is_allowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.chdir(root)
    external = tmp_path / "external.html"
    external.write_text('<div  id = "external" ></div>', encoding="utf-8")
    linked = root / "linked.html"
    linked.symlink_to(external)

    assert _run_main(["format", str(linked)]) == 2
    assert "explicit file is a symlink" in capsys.readouterr().err
    assert external.read_text(encoding="utf-8") == '<div  id = "external" ></div>'

    assert _run_main(["format", str(external)]) == 0
    capsys.readouterr()
    assert external.read_text(encoding="utf-8") == '<div id="external"></div>'


def test_usage_errors_are_validated_before_any_file_is_written(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    template = tmp_path / "card.html"
    unsupported = tmp_path / "notes.txt"
    template.write_text('<div  id = "card" ></div>', encoding="utf-8")
    unsupported.write_text("notes", encoding="utf-8")

    assert _run_main(["format", str(template), str(unsupported)]) == 2
    assert template.read_text(encoding="utf-8") == '<div  id = "card" ></div>'
    assert "unsupported explicit file extension" in capsys.readouterr().err

    assert _run_main(["format", "--check", "--diff", str(template)]) == 2
    assert template.read_text(encoding="utf-8") == '<div  id = "card" ></div>'
    assert "--check and --diff are mutually exclusive" in capsys.readouterr().err

    assert _run_main(["format", "--static", str(template)]) == 2
    assert template.read_text(encoding="utf-8") == '<div  id = "card" ></div>'
    assert "unrecognized arguments: --static" in capsys.readouterr().err


def test_extensionless_explicit_file_is_a_usage_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "template"
    target.write_text('<div  id = "card" ></div>', encoding="utf-8")

    assert _run_main(["format", str(target)]) == 2
    assert target.read_text(encoding="utf-8") == '<div  id = "card" ></div>'
    assert "unsupported explicit file extension ''" in capsys.readouterr().err


@pytest.mark.parametrize("app_option", ["split", "equals"])
def test_app_selection_is_rejected_without_importing_it(
    app_option: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    marker = tmp_path / "imported"
    (tmp_path / "danger.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry\n"
        f"Path({str(marker)!r}).write_text('yes')\n"
        "engine = Citry()\n",
        encoding="utf-8",
    )
    args = ["--app", "danger:engine", "format"] if app_option == "split" else ["--app=danger:engine", "format"]

    assert _run_main(args) == 2
    assert not marker.exists()
    assert "--app is not accepted by citry format" in capsys.readouterr().err


def test_file_local_error_does_not_hide_other_results_and_exit_two_wins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    good = tmp_path / "a.html"
    bad = tmp_path / "b.html"
    good.write_text('<div  id = "good" ></div>', encoding="utf-8")
    bad.write_text("<div>", encoding="utf-8")

    assert _run_main(["format", "--check", str(bad), str(good)]) == 2

    captured = capsys.readouterr()
    assert captured.out == "would format: a.html\n"
    assert "b.html: citry.format.syntax:" in captured.err
    assert captured.err.endswith("citry format: 1 would format, 0 unchanged, 0 skipped, 1 errored\n")
    assert good.read_text(encoding="utf-8") == '<div  id = "good" ></div>'
    assert bad.read_text(encoding="utf-8") == "<div>"


def test_atomic_write_preserves_crlf_bom_and_file_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "card.py"
    source = _component_source("""<div  class = "card" ></div>""").replace("\n", "\r\n")
    target.write_bytes(b"\xef\xbb\xbf" + source.encode("utf-8"))
    target.chmod(0o640)
    # Windows maps the mode bits onto ACLs and reports 0o666 back, so only assert
    # the mode carries over where the filesystem actually stored what we asked for.
    # The CRLF and BOM checks below stay active everywhere, and Windows is the
    # platform whose line endings they exist to protect.
    mode_is_honored = stat.S_IMODE(target.stat().st_mode) == 0o640

    assert _run_main(["format", str(target)]) == 0

    output = target.read_bytes()
    assert output.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" in output
    assert b'<div class="card"></div>' in output
    if mode_is_honored:
        assert stat.S_IMODE(target.stat().st_mode) == 0o640
    capsys.readouterr()


def test_atomic_write_preserves_special_permission_bits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "card.html"
    target.write_text('<div  id = "card" ></div>', encoding="utf-8")
    target.chmod(0o4755)
    if stat.S_IMODE(target.stat().st_mode) != 0o4755:
        pytest.skip("filesystem does not retain the set-user-ID permission bit")

    assert _run_main(["format", str(target)]) == 0

    assert stat.S_IMODE(target.stat().st_mode) == 0o4755
    capsys.readouterr()


def test_python_without_definite_templates_is_skipped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "plain.py"
    target.write_text("answer = 42\n", encoding="utf-8")

    assert _run_main(["format", str(target)]) == 0

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "citry format: 0 formatted, 0 unchanged, 1 skipped, 0 errored\n"


def test_changed_files_are_reported_in_normalized_sorted_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    second = tmp_path / "z.html"
    first = tmp_path / "a.html"
    for target in (second, first):
        target.write_text('<div  id = "x" ></div>', encoding="utf-8")

    assert _run_main(["format", "--check", str(second), str(first), str(first)]) == 1

    assert capsys.readouterr().out == "would format: a.html\nwould format: z.html\n"


def test_duplicate_normalized_directory_arguments_are_scanned_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    template = tmp_path / "card.tpl"
    template.write_text('<div  id = "card" ></div>', encoding="utf-8")
    _write_component_with_file(tmp_path / "component.py", "card.tpl")

    assert _run_main(["format", "--check", ".", str(tmp_path), "./."]) == 1

    captured = capsys.readouterr()
    assert captured.out == "would format: card.tpl\n"
    assert captured.err == "citry format: 1 would format, 0 unchanged, 1 skipped, 0 errored\n"


def test_atomic_replace_failure_leaves_original_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "card.html"
    source = b'<div  id = "card" ></div>'
    target.write_bytes(source)

    def fail_replace(_source: Path | str, _target: Path | str) -> None:
        raise OSError("replace refused")

    # Patch `Path.replace`, which is what `_atomic_replace` calls. Patching
    # `os.replace` instead only works from 3.11: on 3.10 pathlib binds it at
    # import time, so a later patch is invisible and the failure never happens.
    monkeypatch.setattr(Path, "replace", fail_replace)

    assert _run_main(["format", str(target)]) == 2
    assert target.read_bytes() == source
    captured = capsys.readouterr()
    assert "replace refused" in captured.err
    assert captured.err.endswith("citry format: 0 formatted, 0 unchanged, 0 skipped, 1 errored\n")
