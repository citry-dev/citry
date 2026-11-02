"""The release cache validator catches a publish job that would restore a GitHub Actions cache."""

from pathlib import Path

import pytest
from scripts.validators import release_caches

_REPO = Path(__file__).resolve().parents[4]
_UV = "astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2"
_LABEL = ".github/workflows/py--demo--publish.yml job build"


def _check(tmp_path: Path, steps: str, *, name: str = "py--demo--publish.yml", env: str = "") -> list[str]:
    path = tmp_path / ".github" / "workflows" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{env}jobs:\n  build:\n    steps:\n{steps}", encoding="utf-8")
    return release_caches.check(tmp_path)


def test_the_repository_publish_workflows_pass() -> None:
    assert release_caches.check(_REPO) == []


def test_clean_setup_steps_pass(tmp_path: Path) -> None:
    steps = (
        f"      - uses: {_UV}\n        with:\n          enable-cache: false\n"
        '      - uses: actions/setup-node@v7\n        with:\n          package-manager-cache: "false"\n'
        "      - uses: actions/setup-python@v7\n"
        "      - uses: pnpm/action-setup@v6\n        with:\n          cache: false\n"
        "      - uses: PyO3/maturin-action@v1\n        with:\n          sccache: false\n"
        "      - run: cargo build\n"
    )
    assert _check(tmp_path, steps, name="py--demo--publish.yaml") == []


@pytest.mark.parametrize(
    "uses",
    [
        "actions/cache@v6",
        "actions/cache/restore@v6",
        "mozilla-actions/sccache-action@v0.0.11",
        "Swatinem/rust-cache@v2",
        # setup-go caches by default, so a new action needs a review first.
        "actions/setup-go@v6",
    ],
)
def test_an_action_nobody_reviewed_is_reported(tmp_path: Path, uses: str) -> None:
    problems = _check(tmp_path, f"      - uses: {uses}\n")
    assert problems == [
        f"{_LABEL} step {uses!r} uses {uses.split('@')[0].lower()}, which is not reviewed for caching; "
        "check its defaults and add it to release_caches.py"
    ]


@pytest.mark.parametrize(
    ("uses", "setting"),
    [
        ("PyO3/maturin-action@v1", 'sccache: "true"'),
        ("actions/setup-python@v7", "cache: pip"),
        ("pnpm/action-setup@v6", "cache: true"),
        # GitHub matches input names without regard to case.
        ("actions/setup-node@v7", "Cache: pnpm\n          package-manager-cache: false"),
    ],
)
def test_a_cache_input_is_reported(tmp_path: Path, uses: str, setting: str) -> None:
    problems = _check(tmp_path, f"      - uses: {uses}\n        with:\n          {setting}\n")
    assert len(problems) == 1
    assert "must not restore or save a cache" in problems[0]


@pytest.mark.parametrize(
    ("uses", "settings", "switch"),
    [
        # Left out, both inputs keep the action's own default, which caches.
        (_UV, "version: 0.13.5", "enable-cache"),
        (_UV, "enable-cache: auto", "enable-cache"),
        (_UV, "enable-cache: true", "enable-cache"),
        ("actions/setup-node@v7", "node-version: 24", "package-manager-cache"),
        # setup-node reads an empty value as its default, which is on.
        ("actions/setup-node@v7", "package-manager-cache: ''", "package-manager-cache"),
        ("actions/setup-node@v7", "package-manager-cache:", "package-manager-cache"),
    ],
)
def test_a_cache_left_on_by_default_is_reported(tmp_path: Path, uses: str, settings: str, switch: str) -> None:
    problems = _check(tmp_path, f"      - uses: {uses}\n        with:\n          {settings}\n")
    assert problems == [
        f"{_LABEL} step {uses!r} must set {switch}: false on {uses.split('@')[0].lower()}; "
        "publish jobs must not restore or save a cache"
    ]


@pytest.mark.parametrize(
    "steps",
    [
        '      - run: echo "RUSTC_WRAPPER=sccache" >> "$GITHUB_ENV"\n',
        "      - uses: PyO3/maturin-action@v1\n        with:\n          docker-options: -e SCCACHE_GHA_ENABLED=true\n",
        "      - run: cargo build\n        env:\n          CARGO_BUILD_RUSTC_WRAPPER: sccache\n",
    ],
)
def test_sccache_turned_on_another_way_is_reported(tmp_path: Path, steps: str) -> None:
    assert len(_check(tmp_path, steps)) == 1


def test_env_is_checked_at_every_level(tmp_path: Path) -> None:
    path = tmp_path / ".github" / "workflows" / "py--demo--publish.yml"
    path.parent.mkdir(parents=True)
    path.write_text(
        "env:\n  SCCACHE_GHA_ENABLED: 'true'\n"
        "jobs:\n  build:\n    env:\n      RUSTC_WRAPPER: sccache\n"
        "    steps:\n      - name: Build\n        run: cargo build\n        env:\n          RUSTC_WRAPPER: sccache\n",
        encoding="utf-8",
    )
    assert release_caches.check(tmp_path) == [
        ".github/workflows/py--demo--publish.yml sets SCCACHE_GHA_ENABLED; "
        "publish jobs must not restore or save a cache",
        f"{_LABEL} sets RUSTC_WRAPPER; publish jobs must not restore or save a cache",
        f"{_LABEL} step 'Build' sets RUSTC_WRAPPER; publish jobs must not restore or save a cache",
    ]


def test_a_reusable_workflow_job_is_reported(tmp_path: Path) -> None:
    path = tmp_path / ".github" / "workflows" / "py--demo--publish.yml"
    path.parent.mkdir(parents=True)
    path.write_text("jobs:\n  build:\n    uses: ./.github/workflows/build.yml\n", encoding="utf-8")
    assert release_caches.check(tmp_path) == [
        f"{_LABEL} calls a reusable workflow, whose caches this validator cannot check"
    ]


def test_ordinary_ci_workflows_keep_their_caches(tmp_path: Path) -> None:
    assert _check(tmp_path, "      - uses: actions/cache@v6\n", name="py--tests.yml") == []


@pytest.mark.parametrize("content", ["", "- a\n", "jobs:\n  build: {steps: [{run: echo}]}\n"])
def test_empty_list_and_flow_style_documents_pass(tmp_path: Path, content: str) -> None:
    path = tmp_path / ".github" / "workflows" / "py--demo--publish.yml"
    path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")
    assert release_caches.check(tmp_path) == []
