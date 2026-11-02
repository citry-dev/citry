"""Tests for the package size check that the pull request build runs."""

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

from scripts import (  # noqa: E402
    check_package_sizes,
    verify_citry_distribution,
    verify_citry_lsp_distribution,
    verify_citry_ui_distribution,
)
from scripts.check_package_sizes import (  # noqa: E402
    CappedFile,
    SizeCheckError,
    SizeRecord,
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


def test_a_file_over_its_cap_gets_an_error_that_names_the_file_its_size_and_its_cap(tmp_path: Path) -> None:
    records = measure([_file(tmp_path, "pkg-1.0.whl", 101)], caps=_SMALL_CAP)

    lines = report_lines(records)

    assert lines[0] == "pkg-1.0.whl: 101 of 100 bytes (101 percent of its cap)"
    assert lines[1] == (
        "::error title=Package over its release cap::pkg-1.0.whl is 101 bytes, over its 100-byte release cap, "
        "and the release would fail on it. If the growth is expected, raise "
        "MAX_WHEEL_BYTES in scripts/verify_pkg.py; otherwise make the file smaller."
    )
    # The error replaces the warning: one file never gets both.
    assert len(lines) == 2


def test_the_size_numbers_in_an_error_have_thousands_separators(tmp_path: Path) -> None:
    caps = (CappedFile("big-*.whl", 1_000, "MAX_WHEEL_BYTES in scripts/verify_big.py"),)

    [_, error] = report_lines(measure([_file(tmp_path, "big-1.0.whl", 1_234)], caps=caps))

    assert "big-1.0.whl is 1,234 bytes, over its 1,000-byte release cap" in error


def test_one_byte_over_a_large_cap_does_not_read_as_a_full_hundred_percent(tmp_path: Path) -> None:
    # Rounding down would print "100 percent" for a file that is over its cap,
    # the same as one that is exactly full and passes.
    caps = (CappedFile("big-*.whl", 100_000, "MAX_WHEEL_BYTES in scripts/verify_big.py"),)

    [full] = measure([_file(tmp_path, "big-1.0.whl", 100_000)], caps=caps)
    [over] = measure([_file(tmp_path, "big-2.0.whl", 100_001)], caps=caps)

    assert full.percent == 100
    assert over.percent == 101
    assert "(101 percent of its cap)" in report_lines([over])[0]


def test_a_file_under_its_cap_has_its_percent_rounded_down(tmp_path: Path) -> None:
    # 89.5 percent must not read as 90, the point where the warning starts.
    caps = (CappedFile("big-*.whl", 1_000, "MAX_WHEEL_BYTES in scripts/verify_big.py"),)

    [record] = measure([_file(tmp_path, "big-1.0.whl", 895)], caps=caps)

    assert record.percent == 89
    assert report_lines([record]) == ["big-1.0.whl: 895 of 1,000 bytes (89 percent of its cap)"]


def test_a_file_of_exactly_its_cap_is_not_over_it(tmp_path: Path) -> None:
    # The release verifiers reject a file only when it is larger than the cap,
    # so a file of exactly the cap must pass here, with a warning that it is
    # full, rather than fail a pull request the release would accept.
    [record] = measure([_file(tmp_path, "pkg-1.0.whl", 100)], caps=_SMALL_CAP)

    assert not record.is_over_cap
    lines = report_lines([record])
    assert lines[0] == "pkg-1.0.whl: 100 of 100 bytes (100 percent of its cap)"
    assert lines[1].startswith(
        "::warning title=Package size at or near its release cap::pkg-1.0.whl is at 100 percent"
    )
    assert len(lines) == 2


@pytest.mark.parametrize(("size", "over"), [(89, False), (90, False), (100, False), (101, True)])
def test_a_file_is_over_its_cap_only_when_larger_than_it(tmp_path: Path, size: int, over: bool) -> None:
    [record] = measure([_file(tmp_path, "pkg-1.0.whl", size)], caps=_SMALL_CAP)

    assert record.is_over_cap is over
    assert any(line.startswith("::error ") for line in report_lines([record])) is over


def test_a_file_name_cannot_start_a_second_workflow_command(tmp_path: Path) -> None:
    # `%0A` is how GitHub spells a newline in a command, so the percent sign
    # in a name must be escaped for the name to print as written.
    records = measure([_file(tmp_path, "pkg-1%0A::error::x.whl", 95)], caps=_SMALL_CAP)

    warning = report_lines(records)[1]

    assert "pkg-1%250A::error::x.whl is at 95 percent" in warning
    assert "\n" not in warning


def test_an_over_cap_file_name_cannot_start_a_second_workflow_command(tmp_path: Path) -> None:
    # The error line is the one a failed build shows, so it escapes the name too.
    records = measure([_file(tmp_path, "pkg-1%0A::warning::x.whl", 101)], caps=_SMALL_CAP)

    error = report_lines(records)[1]

    assert error.startswith("::error title=Package over its release cap::pkg-1%250A::warning::x.whl is 101 bytes")
    assert "\n" not in error


@pytest.mark.parametrize("size", [10, 95, 101])
def test_a_file_name_with_a_newline_cannot_start_a_workflow_command_in_any_line(size: int) -> None:
    # Built without a file on disk: a newline is not allowed in a Windows file name.
    record = SizeRecord("pkg-1\n::error::INJECTED.whl", size, _SMALL_CAP[0])

    output = "\n".join(report_lines([record])).splitlines()

    # Every line is the listing or one of the two annotations; none starts a second command.
    allowed = ("pkg-1%0A::error::INJECTED.whl: ", "::error title=Package over", "::warning title=Package size")
    assert output
    assert all(line.startswith(allowed) for line in output), output


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


def test_every_file_is_listed_before_any_annotation_and_each_file_gets_at_most_one(tmp_path: Path) -> None:
    records = measure(
        [
            _file(tmp_path, "pkg-1.0.whl", 150),
            _file(tmp_path, "pkg-2.0.whl", 95),
            _file(tmp_path, "pkg-3.0.whl", 10),
            _file(tmp_path, "pkg-4.0.whl", 101),
        ],
        caps=_SMALL_CAP,
    )

    lines = report_lines(records)

    assert [line.split(":")[0] for line in lines[:4]] == ["pkg-1.0.whl", "pkg-2.0.whl", "pkg-3.0.whl", "pkg-4.0.whl"]
    # The annotations follow in file order, so a run with several files over
    # their caps names every one of them rather than the first.
    assert [line.split("::")[0:2] for line in lines[4:]] == [
        ["", "error title=Package over its release cap"],
        ["", "warning title=Package size at or near its release cap"],
        ["", "error title=Package over its release cap"],
    ]
    assert "pkg-1.0.whl is 150 bytes" in lines[4]
    assert "pkg-2.0.whl is at 95 percent" in lines[5]
    assert "pkg-4.0.whl is 101 bytes" in lines[6]
    assert len(lines) == 7


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

    # A file within its cap must not fail the build, however close it is.
    assert code == 0
    captured = capsys.readouterr()
    assert "pkg-1.0.whl: 95 of 100 bytes" in captured.out
    assert "::warning title=Package size at or near its release cap::" in captured.out
    assert "::error" not in captured.out
    assert captured.err == ""


def test_the_command_fails_when_a_file_is_over_its_cap_and_still_lists_every_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(check_package_sizes, "capped_files", lambda: _SMALL_CAP)

    code = main(
        [
            str(_file(tmp_path, "pkg-1.0.whl", 150)),
            str(_file(tmp_path, "pkg-2.0.whl", 10)),
            str(_file(tmp_path, "pkg-3.0.whl", 101)),
        ]
    )

    assert code == 1
    captured = capsys.readouterr()
    # The files under their cap are listed too, and every file over its cap
    # has its own error, so one failed run shows the whole picture.
    assert "pkg-2.0.whl: 10 of 100 bytes" in captured.out
    errors = [line for line in captured.out.splitlines() if line.startswith("::error ")]
    assert len(errors) == 2
    assert "pkg-1.0.whl is 150 bytes, over its 100-byte release cap" in errors[0]
    assert "pkg-3.0.whl is 101 bytes, over its 100-byte release cap" in errors[1]
    assert captured.err == "package size check failed, files over their release cap: 2 of 3 (see the errors above)\n"


def test_the_message_for_a_file_it_cannot_measure_escapes_the_path(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(check_package_sizes, "capped_files", lambda: _SMALL_CAP)

    # The path does not exist, so no file with this name is created.
    with pytest.raises(SystemExit) as raised:
        main(["pkg-1\n::error::INJECTED.whl"])

    assert raised.value.code == 1
    err = capsys.readouterr().err
    assert (
        err == "package size check failed: pkg-1%0A::error::INJECTED.whl is not a file; the build did not produce it\n"
    )


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


def test_the_script_run_by_path_fails_for_a_file_over_the_real_cap(tmp_path: Path) -> None:
    # The same invocation CI uses, against a real verifier's cap: the exit
    # status is what fails the workflow step. CI merges stdout and stderr into
    # one log, so the streams are merged here too, to check what a reader sees.
    cap = verify_citry_lsp_distribution.MAX_WHEEL_BYTES
    wheel = _file(tmp_path, "citry_lsp-1.0.0-py3-none-any.whl", cap + 1)

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_package_sizes.py"), str(wheel)],
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    lines = result.stdout.splitlines()
    assert lines[0] == f"citry_lsp-1.0.0-py3-none-any.whl: {cap + 1:,} of {cap:,} bytes (101 percent of its cap)"
    assert lines[1].startswith(
        f"::error title=Package over its release cap::citry_lsp-1.0.0-py3-none-any.whl is {cap + 1:,} bytes, "
        f"over its {cap:,}-byte release cap"
    )
    assert "MAX_WHEEL_BYTES in scripts/verify_citry_lsp_distribution.py" in lines[1]
    # The summary points back at the errors, so it must come after them.
    assert lines[2] == "package size check failed, files over their release cap: 1 of 1 (see the errors above)"
    assert len(lines) == 3


def test_the_script_run_by_path_passes_a_file_of_exactly_the_real_cap(tmp_path: Path) -> None:
    wheel = _file(tmp_path, "citry_lsp-1.0.0-py3-none-any.whl", verify_citry_lsp_distribution.MAX_WHEEL_BYTES)

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_package_sizes.py"), str(wheel)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "::error" not in result.stdout
    assert "::warning" in result.stdout
