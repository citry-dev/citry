from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from python_candidate import LOCALES, collect

ROOT = Path(__file__).resolve().parent
BROWSER = ROOT / "browser" / "runner.mjs"
REQUIREMENTS = ROOT / "python-requirements.txt"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_browser() -> dict[str, Any]:
    node = shutil.which("node")
    require(node is not None, "node is required")
    process = subprocess.run(
        [node, str(BROWSER)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(process.stdout)


def decimal_digits(text: str) -> str:
    return "".join(character for character in text if character.isdecimal())


def main() -> None:
    python = collect()
    browser = run_browser()

    require(python["runtime"]["babel"] == "2.18.0", "unexpected Babel version")
    require(python["runtime"]["babel_cldr"] == "47", "unexpected Babel CLDR")
    require(python["runtime"]["pyicu"] == "2.16.2", "unexpected PyICU version")
    require(python["runtime"]["icu"] == "78.3", "unexpected linked ICU")
    require(python["runtime"]["tzdata"] == "2026.3", "unexpected tzdata")
    require(python["runtime"]["zoneinfo_tzpath"] == [], "zoneinfo is not package-only")
    require(browser["runtime"]["icu"] == "78.3", "unexpected browser ICU")

    plural_parity = all(
        python["babel"][locale]["plurals"]
        == python["pyicu"][locale]["plurals"]
        == browser["locales"][locale]["plurals"]
        for locale in LOCALES
    )
    require(plural_parity, "plural categories differ")

    compared_kinds = (
        "decimal",
        "currency",
        "percent",
        "unit",
        "list",
        "relative_day",
        "date",
    )
    exact_output_differences = [
        {
            "locale": locale,
            "kind": kind,
            "pyicu": python["pyicu"][locale][kind],
            "intl": browser["locales"][locale][kind],
        }
        for locale in LOCALES
        for kind in compared_kinds
        if python["pyicu"][locale][kind] != browser["locales"][locale][kind]
    ]
    exact_reference_parity = all(
        all(python["pyicu"][locale][kind] == browser["locales"][locale][kind] for kind in compared_kinds)
        for locale in (
            "en-US",
            "cs-CZ",
            "ar-EG",
            "hi-IN-u-nu-deva",
            "th-TH-u-ca-buddhist",
        )
    )
    require(exact_reference_parity, "reference ICU and Intl profiles differ")
    require(exact_output_differences, "expected backend-default differences vanished")
    az_base = python["locale_data_fallback_probe"]["az_base_language"]
    require(
        all(az_base[kind] == browser["locales"]["az-Arab"][kind] for kind in compared_kinds),
        "base-language data probe did not reproduce browser az-Arab output",
    )

    require(
        decimal_digits(python["babel"]["ar-EG"]["decimal"]) == "12345",
        "Babel unexpectedly shaped Arabic digits",
    )
    require(
        decimal_digits(python["babel"]["hi-IN-u-nu-deva"]["decimal"]) == "12345",
        "Babel unexpectedly shaped Devanagari digits",
    )
    require(
        decimal_digits(python["pyicu"]["ar-EG"]["decimal"]) == "١٢٣٤٥",
        "PyICU did not shape Arabic digits",
    )
    require(
        decimal_digits(python["pyicu"]["hi-IN-u-nu-deva"]["decimal"]) == "१२३४५",
        "PyICU did not shape Devanagari digits",
    )

    require(
        python["babel"]["th-TH-u-ca-buddhist"]["date"].endswith("2026"),
        "Babel date no longer demonstrates Gregorian-only result",
    )
    require(
        python["pyicu"]["th-TH-u-ca-buddhist"]["date"].endswith("2569"),
        "PyICU did not honor the Buddhist calendar",
    )

    require(
        python["parsing"]["en-US"]["babel"]["accepted"] and python["parsing"]["cs-CZ"]["babel"]["accepted"],
        "Babel rejected supported Latin parsing cases",
    )
    require(
        not python["parsing"]["ar-EG"]["babel"]["accepted"]
        and not python["parsing"]["hi-IN-u-nu-deva"]["babel"]["accepted"],
        "Babel unexpectedly parsed shaped digits",
    )
    require(
        all(case["pyicu"]["accepted"] for case in python["parsing"].values()),
        "PyICU rejected a declared digit-system parse",
    )
    require(not browser["parsing"]["has_number_parser"], "Intl gained a number parser")

    expected_wall_kinds = {
        "prague_gap": "gap",
        "prague_fold": "fold",
        "new_york_gap": "gap",
        "new_york_fold": "fold",
    }
    require(
        {name: result["kind"] for name, result in python["wall_times"].items()} == expected_wall_kinds,
        "wall-time gap/fold classification differs",
    )

    exact_decimal_parity = all(
        python["exact_decimal"]["pyicu"][value] == browser["exact_decimal"][value]
        for value in ("9007199254740993", "-0", "1.2300")
    )
    require(exact_decimal_parity, "exact-decimal formatting differs")

    output = {
        "result": "PASS_BOUNDED",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "uv": _uv_version(),
        },
        "input_sha256": {
            "harness": digest(Path(__file__)),
            "python_candidate": digest(ROOT / "python_candidate.py"),
            "browser_runner": digest(BROWSER),
            "requirements": digest(REQUIREMENTS),
        },
        "python": python,
        "browser": browser,
        "gates": {
            "plural_semantics_match": plural_parity,
            "reference_pyicu_profiles_match_same_icu_intl_exactly": exact_reference_parity,
            "backend_defaults_can_differ_with_same_icu": bool(exact_output_differences),
            "az_base_language_projection_matches_intl": True,
            "pyicu_and_intl_shape_declared_digits": True,
            "babel_does_not_shape_declared_digits": True,
            "pyicu_and_intl_honor_buddhist_calendar": True,
            "babel_lacks_general_calendar_selection": True,
            "pyicu_parses_declared_digit_systems": True,
            "babel_parser_subset_is_latin_digit_only": True,
            "intl_has_no_number_parser": True,
            "zoneinfo_classifies_declared_gaps_and_folds": True,
            "exact_decimal_string_path_matches": exact_decimal_parity,
        },
        "exact_output_differences": exact_output_differences,
        "bounded_conclusion": {
            "babel": "viable_subset_only",
            "pyicu": "capability_fit_with_native_packaging_cost",
            "intl": "browser_formatter_not_parser",
            "backend_ratified": False,
        },
    }
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def _uv_version() -> str:
    uv = shutil.which("uv")
    require(uv is not None, "uv is required")
    return subprocess.run([uv, "--version"], check=True, capture_output=True, text=True).stdout.strip()


if __name__ == "__main__":
    main()
