"""Tests for the package size report that the pull request build runs."""

from __future__ import annotations

import importlib
import re
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts import check_package_sizes, verify_citry_distribution, verify_citry_ui_distribution  # noqa: E402
from scripts.check_package_sizes import (  # noqa: E402
    CappedFile,
    SizeCheckError,
    capped_files,
    main,
    measure,
    report_lines,
)

# A small cap makes the 90 percent boundary easy to hit with a few bytes.
_SMALL_CAP = (CappedFile("pkg-*.whl", 100, "MAX_WHEEL_BYTES in scripts/verify_pkg.py"),)


def _file(directory: Path, name: str, size: int) -> Path:
    path = directory / name
    path.write_bytes(b"x" * size)
    return path


_VERIFIER_CAPS = [
    ("citry-0.7.0-py3-none-any.whl", "scripts.verify_citry_distribution", "MAX_WHEEL_BYTES"),
    (
        "citry_core-1.0.0-cp311-abi3-manylinux_2_28_x86_64.whl",
        "scripts.verify_citry_core_distribution",
        "MAX_WHEEL_BYTES",
    ),
    ("citry_ui-0.4.0.tar.gz", "scripts.verify_citry_ui_distribution", "MAX_SDIST_BYTES"),
    ("citry_lsp-0.3.0-py3-none-any.whl", "scripts.verify_citry_lsp_distribution", "MAX_WHEEL_BYTES"),
    ("citry_lsp-0.3.0.tar.gz", "scripts.verify_citry_lsp_distribution", "MAX_SDIST_BYTES"),
    ("pygments_citry-0.2.1-py3-none-any.whl", "scripts.verify_pygments_citry_distribution", "MAX_WHEEL_BYTES"),
    ("pygments_citry-0.2.1.tar.gz", "scripts.verify_pygments_citry_distribution", "MAX_SDIST_BYTES"),
]


@pytest.mark.parametrize(("name", "module", "constant"), _VERIFIER_CAPS)
def test_each_cap_follows_the_verifier_that_enforces_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, module: str, constant: str
) -> None:
    verifier = importlib.import_module(module)
    [record] = measure([_file(tmp_path, name, 1)])
    assert record.cap.max_bytes == getattr(verifier, constant)
    assert record.cap.source.startswith(f"{constant} in scripts/")

    # Changing the number in the verifier changes it here, so the script holds
    # no copy of its own.
    monkeypatch.setattr(verifier, constant, 123_456)
    [changed] = measure([_file(tmp_path, name, 1)])
    assert changed.cap.max_bytes == 123_456


def test_the_citry_ui_wheel_cap_follows_its_wheel_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wheel = _file(tmp_path, "citry_ui-0.4.0-py3-none-any.whl", 1)
    qualifier = runpy.run_path(str(verify_citry_ui_distribution.QUALIFIER))
    [record] = measure([wheel])

    assert record.cap.max_bytes == qualifier["MAX_WHEEL_BYTES"]
    assert record.cap.source == "MAX_WHEEL_BYTES in packages/py/citry_ui/citry_ui/quality/qualify_wheel.py"

    monkeypatch.setattr(check_package_sizes.runpy, "run_path", lambda _path: {"MAX_WHEEL_BYTES": 777})
    [changed] = measure([wheel])
    assert changed.cap.max_bytes == 777


def test_the_citry_ui_wheel_check_failing_to_load_is_a_size_check_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    wheel = _file(tmp_path, "citry_ui-0.4.0-py3-none-any.whl", 1)

    # A checkout without the citry_ui source tree fails while the file runs.
    def missing_tree(_path: str) -> dict[str, object]:
        raise FileNotFoundError("citry_ui_i18n")

    monkeypatch.setattr(check_package_sizes.runpy, "run_path", missing_tree)
    with pytest.raises(SizeCheckError, match=r"could not read MAX_WHEEL_BYTES in packages/py/citry_ui"):
        measure([wheel])

    # A renamed constant fails on the lookup.
    monkeypatch.setattr(check_package_sizes.runpy, "run_path", lambda _path: {})
    with pytest.raises(SizeCheckError, match=r"could not read MAX_WHEEL_BYTES in packages/py/citry_ui"):
        measure([wheel])


@pytest.mark.parametrize(
    "module",
    [
        "scripts.verify_citry_lsp_distribution",
        "scripts.verify_citry_ui_distribution",
        "scripts.verify_pygments_citry_distribution",
    ],
)
def test_every_release_file_a_verifier_expects_has_a_cap(tmp_path: Path, module: str) -> None:
    # A verifier that starts expecting a new kind of file must get a cap entry.
    names = sorted(importlib.import_module(module).expected_release_filenames("1.0.0"))
    assert names
    assert len(measure([_file(tmp_path, name, 1) for name in names])) == len(names)


def test_every_wheel_and_sdist_cap_in_a_verifier_has_an_entry() -> None:
    # A verifier that gains a cap, or a new verifier, must also be listed in
    # capped_files(), or its package would never be warned about.
    in_verifiers: set[str] = set()
    for path in sorted((ROOT / "scripts").glob("verify_*_distribution.py")):
        module = importlib.import_module(f"scripts.{path.stem}")
        in_verifiers.update(
            f"{name} in scripts/{path.name}" for name in vars(module) if re.fullmatch(r"MAX_(WHEEL|SDIST)_BYTES", name)
        )

    assert in_verifiers
    assert in_verifiers <= {cap.source for cap in capped_files()}


@pytest.mark.parametrize("bad", [0, 0.5, -1, True, "1024", None, float("nan"), float("inf")])
def test_a_cap_that_is_not_a_size_is_refused(monkeypatch: pytest.MonkeyPatch, bad: object) -> None:
    # True is an int in Python and is really 1 byte; a cap of 0 would divide by zero.
    monkeypatch.setattr(verify_citry_distribution, "MAX_WHEEL_BYTES", bad)
    with pytest.raises(SizeCheckError, match=r"MAX_WHEEL_BYTES in scripts/verify_citry_distribution\.py"):
        capped_files()


def test_a_fractional_cap_is_read_as_whole_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The verifiers only compare sizes with their cap, so `1.5 * 1024` is legal there.
    monkeypatch.setattr(verify_citry_distribution, "MAX_WHEEL_BYTES", 1.5 * 1024)

    [record] = measure([_file(tmp_path, "citry-0.7.0-py3-none-any.whl", 1)])

    assert record.cap.max_bytes == 1536


def test_a_file_below_ninety_percent_prints_only_its_size(tmp_path: Path) -> None:
    records = measure([_file(tmp_path, "pkg-1.0.whl", 89)], caps=_SMALL_CAP)

    assert report_lines(records) == ["pkg-1.0.whl: 89 of 100 bytes (89 percent of its cap)"]


def test_a_file_at_ninety_percent_warns_and_names_where_to_raise_the_cap(tmp_path: Path) -> None:
    records = measure([_file(tmp_path, "pkg-1.0.whl", 90)], caps=_SMALL_CAP)

    lines = report_lines(records)

    assert lines[0] == "pkg-1.0.whl: 90 of 100 bytes (90 percent of its cap)"
    assert lines[1] == (
        "::warning title=Package size at or near its release cap::pkg-1.0.whl is at 90 percent of its "
        "100-byte release cap (90 bytes). If the growth is expected, raise "
        "MAX_WHEEL_BYTES in scripts/verify_pkg.py before the release."
    )
    assert len(lines) == 2


def test_a_file_over_its_cap_warns_that_it_is_over(tmp_path: Path) -> None:
    records = measure([_file(tmp_path, "pkg-1.0.whl", 101)], caps=_SMALL_CAP)

    lines = report_lines(records)

    assert "(101 percent of its cap)" in lines[0]
    assert lines[1].startswith(
        "::warning title=Package size at or near its release cap::pkg-1.0.whl is over its 100-byte"
    )


def test_a_file_name_cannot_start_a_second_workflow_command(tmp_path: Path) -> None:
    # `%0A` is how GitHub spells a newline in a command, so the percent sign
    # in a name must be escaped for the name to print as written.
    records = measure([_file(tmp_path, "pkg-1%0A::error::x.whl", 95)], caps=_SMALL_CAP)

    warning = report_lines(records)[1]

    assert "pkg-1%250A::error::x.whl is at 95 percent" in warning
    assert "\n" not in warning


def test_warnings_come_after_the_size_of_every_file(tmp_path: Path) -> None:
    records = measure(
        [_file(tmp_path, "pkg-2.0.whl", 95), _file(tmp_path, "pkg-1.0.whl", 10)],
        caps=_SMALL_CAP,
    )

    lines = report_lines(records)

    # The listing keeps the order the files were given, so one run reads as a
    # table, and the warnings follow it.
    assert lines[0].startswith("pkg-2.0.whl: ")
    assert lines[1].startswith("pkg-1.0.whl: ")
    assert lines[2].startswith("::warning ")
    assert len(lines) == 3


def test_a_missing_path_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(SizeCheckError, match="is not a file"):
        measure([tmp_path / "pkg-1.0.whl"], caps=_SMALL_CAP)
    with pytest.raises(SizeCheckError, match="is not a file"):
        measure([tmp_path], caps=_SMALL_CAP)


def test_a_file_with_no_known_cap_is_an_error(tmp_path: Path) -> None:
    # A build that starts producing a new kind of file must not pass unmeasured.
    with pytest.raises(SizeCheckError, match=r"other-1\.0\.whl has no known size cap"):
        measure([_file(tmp_path, "other-1.0.whl", 1)], caps=_SMALL_CAP)


def test_the_command_prints_the_report_and_succeeds_when_a_file_is_near_its_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(check_package_sizes, "capped_files", lambda: _SMALL_CAP)

    code = main([str(_file(tmp_path, "pkg-1.0.whl", 95))])

    # The release verifiers own the failure, so a warning never fails this step.
    assert code == 0
    out = capsys.readouterr().out
    assert "pkg-1.0.whl: 95 of 100 bytes" in out
    assert "::warning title=Package size at or near its release cap::" in out


def test_the_command_fails_with_a_message_for_a_file_it_cannot_measure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(check_package_sizes, "capped_files", lambda: _SMALL_CAP)

    with pytest.raises(SystemExit) as raised:
        main([str(_file(tmp_path, "other-1.0.whl", 1))])

    assert raised.value.code == 1
    assert "package size check failed: other-1.0.whl has no known size cap" in capsys.readouterr().err


def test_the_script_runs_by_path_from_another_directory(tmp_path: Path) -> None:
    # CI runs `python scripts/check_package_sizes.py`, where only scripts/ is on
    # sys.path, so the plain-import fallback must work.
    wheel = _file(tmp_path, "citry_lsp-1.0.0-py3-none-any.whl", 1)

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_package_sizes.py"), str(wheel)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("citry_lsp-1.0.0-py3-none-any.whl: 1 of ")
