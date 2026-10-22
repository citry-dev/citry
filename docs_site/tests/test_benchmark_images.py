"""Tests for the README benchmark images: their file names, the README block, and the page they are drawn from."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from docs_site._internal.components.error_benchmark import chart_view
from docs_site.scripts import benchmark_images, benchmark_readme

BUCKETS = [
    {"id": "static-error", "label": "Static error"},
    {"id": "static-warning", "label": "Static warning"},
    {"id": "runtime-error", "label": "Runtime error"},
    {"id": "runtime-warning", "label": "Runtime warning"},
    {"id": "missed", "label": "Missed"},
]


def _data(outcomes: dict[str, list[tuple[str, str | None]]]) -> dict[str, Any]:
    # Each framework's list gives one (status, bucket) pair per mistake.
    mistakes = len(next(iter(outcomes.values())))
    return {
        "run": "20990101T000000Z",
        "frameworks": [{"key": key, "name": f'{key.title()} "x"'} for key in outcomes],
        "categories": [{"id": "names", "heading": "Names"}],
        "buckets": BUCKETS,
        "codes": [],
        "mistakes": [{"id": f"m{index}", "title": f"M{index}", "category": "names"} for index in range(mistakes)],
        "results": [
            {
                "framework": key,
                "mistake": f"m{index}",
                "status": status,
                "bucket": bucket,
                "cell": "E",
                "reason": None,
                "evidence": [],
            }
            for key, rows in outcomes.items()
            for index, (status, bucket) in enumerate(rows)
        ],
    }


def _sample() -> dict[str, Any]:
    # Beta and gamma tie on two, and alpha's not-applicable mistake counts for
    # nothing, so the order holds only if both rules are followed.
    return _data(
        {
            "alpha": [("ported", "static-error"), ("not-applicable", None), ("ported", "missed")],
            "beta": [("ported", "static-error"), ("ported", "static-warning"), ("ported", "missed")],
            "gamma": [("ported", "static-warning"), ("ported", "static-error"), ("ported", "runtime-error")],
        },
    )


def test_image_names_hold_the_run_the_bytes_hash_and_the_theme() -> None:
    name = benchmark_readme.image_name("20990101T000000Z", b"png bytes", "dark")
    digest = hashlib.sha256(b"png bytes").hexdigest()[:12]
    assert name == f"errors-20990101T000000Z-{digest}-dark.png"
    assert benchmark_readme.parse_image_name(name) == {"run": "20990101T000000Z", "hash": digest, "theme": "dark"}
    # Different bytes from the same run get a different name, never the same file.
    assert benchmark_readme.image_name("20990101T000000Z", b"other bytes", "dark") != name
    assert benchmark_readme.parse_image_name("errors-run-123-light.png") is None
    # The runner names a second run in the same second with a "-2" suffix.
    second = benchmark_readme.image_name("20990101T000000Z-2", b"png bytes", "light")
    assert benchmark_readme.parse_image_name(second) == {"run": "20990101T000000Z-2", "hash": digest, "theme": "light"}


@pytest.mark.parametrize(
    ("run", "theme", "message"),
    [
        ("20990101T000000Z", "sepia", "Unknown image theme"),
        ("../escape", "light", "only letters, digits, and hyphens"),
    ],
)
def test_image_names_reject_values_that_do_not_fit_a_url(run: str, theme: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        benchmark_readme.image_name(run, b"png", theme)


def test_alt_text_counts_match_the_sorted_chart() -> None:
    data = _sample()
    shares = benchmark_readme.static_shares(data)
    # Alpha's not-applicable mistake leaves it 1 of 2.
    assert [(count, applicable) for _, count, applicable in shares] == [(2, 3), (2, 3), (1, 2)]
    # The README's alt text reads the bars from top to bottom, with the
    # number drawn beside each bar.
    rows = chart_view(data, sort="share", scale="applicable")["rows"]
    assert [f"{count} of {applicable}" for _, count, applicable in shares] == [row["total"] for row in rows]
    assert [name for name, _, _ in shares] == [row["name"] for row in rows]


@pytest.mark.parametrize(
    "change",
    [{"bucket": None}, {"status": "missing", "bucket": None}],
)
def test_counts_refuse_a_case_without_a_result(change: dict[str, Any]) -> None:
    # Data written with --allow-partial can hold a case nobody wrote or scored
    # yet; a README count built from it would look final while missing it.
    data = _sample()
    data["results"][0].update(change)
    with pytest.raises(ValueError, match="alpha / m0 has no result"):
        benchmark_readme.static_shares(data)


def test_readme_block_links_both_images_and_escapes_the_alt_text() -> None:
    block = benchmark_readme.readme_block(_sample(), light_name="light.png", dark_name="dark.png")

    assert block.startswith(benchmark_readme.START_MARKER)
    assert block.endswith(benchmark_readme.END_MARKER)
    assert benchmark_readme.image_names_in(block) == ["dark.png", "light.png"]
    assert f'srcset="{benchmark_readme.ASSET_URL}/dark.png"' in block
    assert f'src="{benchmark_readme.ASSET_URL}/light.png"' in block
    # A quote in a framework name is escaped rather than ending the attribute.
    assert "Beta &quot;x&quot; 2 of 3, Gamma &quot;x&quot; 2 of 3, Alpha &quot;x&quot; 1 of 2." in block
    assert "3 frameworks" in block


def test_replace_block_swaps_only_the_marked_text() -> None:
    readme = f"intro\n{benchmark_readme.START_MARKER}\nold\n{benchmark_readme.END_MARKER}\noutro\n"
    assert benchmark_readme.replace_block(readme, "NEW") == "intro\nNEW\noutro\n"


@pytest.mark.parametrize(
    ("readme", "message"),
    [
        ("no markers here\n", "exactly one"),
        (
            f"{benchmark_readme.START_MARKER}\n{benchmark_readme.END_MARKER}\n"
            f"{benchmark_readme.START_MARKER}\n{benchmark_readme.END_MARKER}\n",
            r"markers on lines \[1, 2, 3, 4\]",
        ),
        (f"{benchmark_readme.END_MARKER}\n{benchmark_readme.START_MARKER}\n", "line 1, before its start marker"),
    ],
)
def test_replace_block_refuses_missing_doubled_or_reversed_markers(readme: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        benchmark_readme.replace_block(readme, "NEW")


def test_page_carries_the_font_inline_and_the_chosen_theme() -> None:
    page = benchmark_images.page_html("<figure>chart</figure>", "dark")
    # A page with no address cannot follow the stylesheet's relative font path.
    assert benchmark_images.FONT_URL not in page
    assert "data:font/woff2;base64," in page
    assert '<html data-theme="dark">' in page
    assert "<figure>chart</figure>" in page


def test_saving_never_overwrites_an_existing_image(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(benchmark_readme, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(benchmark_readme, "ASSET_DIR", tmp_path / "assets")

    name = benchmark_images._save("20990101T000000Z", b"first", "light")
    path = tmp_path / "assets" / name
    assert path.read_bytes() == b"first"
    # A file under the same name is left exactly as it was.
    path.write_bytes(b"published")
    assert benchmark_images._save("20990101T000000Z", b"first", "light") == name
    assert path.read_bytes() == b"published"
