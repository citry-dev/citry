"""The release build points published repository links at the package's release tag, and the verifiers insist on it."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from scripts import release_links, verify_citry_lsp_distribution, verify_vscode_citry_distribution

TAG = "demo@1.2.3"
RELEASE = {release_links.TAG_PREFIX_ENV: "demo@"}


@pytest.mark.parametrize(
    ("link", "pinned"),
    [
        (
            "https://github.com/citry-dev/citry/blob/main/LICENSE",
            f"https://github.com/citry-dev/citry/blob/{TAG}/LICENSE",
        ),
        (
            "https://github.com/citry-dev/citry/tree/main/benchmarks/errors",
            f"https://github.com/citry-dev/citry/tree/{TAG}/benchmarks/errors",
        ),
        # A folder link with nothing after the branch.
        ("https://github.com/citry-dev/citry/tree/main", f"https://github.com/citry-dev/citry/tree/{TAG}"),
        # The URL GitHub's own Raw button gives.
        (
            "https://github.com/citry-dev/citry/raw/refs/heads/main/a.png",
            f"https://github.com/citry-dev/citry/raw/{TAG}/a.png",
        ),
        (
            "https://raw.githubusercontent.com/citry-dev/citry/main/docs/a.png",
            f"https://raw.githubusercontent.com/citry-dev/citry/{TAG}/docs/a.png",
        ),
        (
            "https://raw.githubusercontent.com/citry-dev/citry/refs/heads/main/docs/a.png",
            f"https://raw.githubusercontent.com/citry-dev/citry/{TAG}/docs/a.png",
        ),
        # GitHub ignores case in the host and organization.
        (
            "http://www.GitHub.com/Citry-Dev/citry/blob/main/x.md",
            f"http://www.GitHub.com/Citry-Dev/citry/blob/{TAG}/x.md",
        ),
    ],
)
def test_pin_rewrites_each_link_to_main(link: str, pinned: str) -> None:
    assert release_links.main_links(f"see {link} for details") == [link]
    assert release_links.pin(f"[x]({link})", TAG) == f"[x]({pinned})"
    # Pinning an already pinned text changes nothing.
    assert release_links.pin(release_links.pin(link, TAG), TAG) == pinned


@pytest.mark.parametrize(
    "text",
    [
        # Another branch, an existing pin, another repository, and a folder named main.
        "https://github.com/citry-dev/citry/blob/maintenance/LICENSE",
        "https://github.com/citry-dev/citry/blob/citry@0.6.0/LICENSE",
        "https://github.com/someone/citry/blob/main/LICENSE",
        "https://github.com/citry-dev/citry/blob/citry@0.6.0/main/x.py",
        # An edit is always made on main.
        "https://github.com/citry-dev/citry/edit/main/docs/a.md",
    ],
)
def test_other_links_are_left_and_not_reported(text: str) -> None:
    assert release_links.main_links(text) == []
    assert release_links.pin(text, TAG) == text


def test_a_main_link_the_rewrite_cannot_pin_is_still_reported() -> None:
    link = "https://github.com/citry-dev/citry/commits/main/README.md"
    assert release_links.pin(link, TAG) == link
    assert release_links.main_links(link) == [link]


def _package(tmp_path: Path, manifest: str = '[project]\nversion = "1.2.3"\n') -> Path:
    package = tmp_path / "pkg"
    package.mkdir(exist_ok=True)
    (package / "pyproject.toml").write_text(manifest, encoding="utf-8")
    return package


def test_release_tag_joins_the_prefix_and_the_manifest_version(tmp_path: Path) -> None:
    assert release_links.release_tag(_package(tmp_path), {}) is None
    assert release_links.release_tag(_package(tmp_path), RELEASE) == TAG
    # The VS Code extension keeps its version in package.json.
    vscode = tmp_path / "vscode"
    vscode.mkdir()
    (vscode / "package.json").write_text('{"version": "0.3.0"}', encoding="utf-8")
    assert release_links.release_tag(vscode, {release_links.TAG_PREFIX_ENV: "vscode-citry@"}) == "vscode-citry@0.3.0"


@pytest.mark.parametrize("prefix", ["demo", "demo@1.2.3", "Demo@", "@"])
def test_release_tag_rejects_a_malformed_prefix(tmp_path: Path, prefix: str) -> None:
    with pytest.raises(release_links.ReleaseLinkError, match="tag prefix"):
        release_links.release_tag(_package(tmp_path), {release_links.TAG_PREFIX_ENV: prefix})


def test_release_tag_rejects_a_manifest_without_a_version(tmp_path: Path) -> None:
    with pytest.raises(release_links.ReleaseLinkError, match="no usable version"):
        release_links.release_tag(_package(tmp_path, '[project]\nname = "demo"\n'), RELEASE)


def test_checkout_bytes_pins_only_what_the_pin_step_rewrites(tmp_path: Path) -> None:
    link = b"https://github.com/citry-dev/citry/blob/main/LICENSE\n"
    package = _package(tmp_path)
    (package / "nested").mkdir()
    for path in (package / "README.md", package / "module.py", package / "nested" / "README.md"):
        path.write_bytes(link)

    # Outside a release, every file is expected unchanged.
    assert release_links.checkout_bytes(package, package / "README.md", {}) == link
    # During one, the package's own README is expected pinned...
    assert TAG.encode() in release_links.checkout_bytes(package, package / "README.md", RELEASE)
    # ...while code and deeper READMEs keep their bytes, as the pin step leaves them.
    assert release_links.checkout_bytes(package, package / "module.py", RELEASE) == link
    assert release_links.checkout_bytes(package, package / "nested" / "README.md", RELEASE) == link


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"])
def test_pin_step_and_verifier_agree_on_line_endings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, newline: bytes
) -> None:
    package = _package(tmp_path)
    readme = package / "README.md"
    readme.write_bytes(b"# Demo" + newline + b"![x](https://github.com/citry-dev/citry/raw/main/x.png)" + newline)
    expected = release_links.checkout_bytes(package, readme, RELEASE)

    monkeypatch.setenv(release_links.TAG_PREFIX_ENV, "demo@")
    assert release_links.main(["pin", str(package)]) == 0
    # The rewrite keeps the file's own line endings, so the bytes the build
    # sees are the bytes the verifier expects, on every platform.
    assert readme.read_bytes() == expected
    assert newline in readme.read_bytes()


def test_unpinned_links_are_reported_only_during_a_release(tmp_path: Path) -> None:
    package = _package(tmp_path)
    metadata = b"Project-URL: Changelog, https://github.com/citry-dev/citry/blob/main/CHANGELOG.md\n"
    assert release_links.unpinned_links(metadata, package, {}) == []
    assert release_links.unpinned_links(metadata, package, RELEASE) == [
        "https://github.com/citry-dev/citry/blob/main/CHANGELOG.md"
    ]


def test_a_link_to_another_version_of_the_package_is_reported(tmp_path: Path) -> None:
    package = _package(tmp_path)
    metadata = (
        f"[now](https://github.com/citry-dev/citry/tree/{TAG}/examples).\n"
        "[old](https://github.com/citry-dev/citry/tree/demo%401.0.0/examples)\n"
        "See https://github.com/citry-dev/citry/blob/demo@1.1.0.\n"
        # Another package's tag and a compare range name releases that exist.
        "![peer](https://raw.githubusercontent.com/citry-dev/citry/other@2.0.0/a.png)\n"
        "[diff](https://github.com/citry-dev/citry/compare/demo@1.0.0...demo@1.1.0)\n"
    ).encode()
    assert release_links.unpinned_links(metadata, package, RELEASE) == [
        "https://github.com/citry-dev/citry/tree/demo%401.0.0",
        "https://github.com/citry-dev/citry/blob/demo@1.1.0",
    ]


@pytest.mark.parametrize("after", [".", ",", "**", "|", "`"])
def test_a_main_link_followed_by_punctuation_is_pinned_and_reported(after: str) -> None:
    link = "https://github.com/citry-dev/citry/tree/main"
    assert release_links.main_links(f"See {link}{after} now") == [link]
    assert release_links.pin(f"See {link}{after}", TAG) == f"See https://github.com/citry-dev/citry/tree/{TAG}{after}"


def test_pin_command_rewrites_through_a_symlinked_readme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root_readme = tmp_path / "README.md"
    root_readme.write_text("![logo](https://raw.githubusercontent.com/citry-dev/citry/main/logo.png)\n")
    package = _package(tmp_path)
    try:
        (package / "README.md").symlink_to(root_readme)
    except OSError:  # Windows without the symlink privilege.
        pytest.skip("this platform cannot create symlinks")

    monkeypatch.setenv(release_links.TAG_PREFIX_ENV, "demo@")
    assert release_links.main(["pin", str(package)]) == 0
    # The file setuptools reads is the symlink's target, so that is what changes.
    assert (package / "README.md").is_symlink()
    assert f"/citry/{TAG}/logo.png" in root_readme.read_text()


@pytest.mark.parametrize(
    ("prefix", "make_dir"),
    [
        # Without the prefix the command refuses, rather than publishing main links.
        (None, True),
        ("not a prefix", True),
        ("demo@", False),
    ],
)
def test_pin_command_fails_cleanly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    prefix: str | None,
    make_dir: bool,
) -> None:
    monkeypatch.delenv(release_links.TAG_PREFIX_ENV, raising=False)
    if prefix is not None:
        monkeypatch.setenv(release_links.TAG_PREFIX_ENV, prefix)
    package = _package(tmp_path) if make_dir else tmp_path / "missing"
    assert release_links.main(["pin", str(package)]) == 1
    assert capsys.readouterr().err.startswith("release link pinning failed: ")


@pytest.mark.parametrize(
    "module",
    [
        "verify_citry_distribution",
        "verify_citry_core_distribution",
        "verify_citry_lsp_distribution",
        "verify_citry_ui_distribution",
        "verify_pygments_citry_distribution",
    ],
)
def test_python_verifiers_reject_release_metadata_that_links_to_main(
    module: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    verifier = importlib.import_module(f"scripts.{module}")
    metadata = b"Name: demo\nProject-URL: Changelog, https://github.com/citry-dev/citry/blob/main/CHANGELOG.md\n"
    monkeypatch.delenv(release_links.TAG_PREFIX_ENV, raising=False)
    assert verifier._parse_metadata(metadata, artifact=Path("demo.whl"))["Name"] == "demo"

    monkeypatch.setenv(release_links.TAG_PREFIX_ENV, "demo@")
    with pytest.raises(verifier.DistributionVerificationError, match="not the release tag"):
        verifier._parse_metadata(metadata, artifact=Path("demo.whl"))


def test_sdist_check_expects_the_pinned_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # A synthetic citry-lsp package, so the test does not depend on the real files' links.
    package = _package(
        tmp_path,
        '[project]\nversion = "1.2.3"\n[project.urls]\nChangelog = "https://github.com/citry-dev/citry/blob/main/CHANGELOG.md"\n',
    )
    (package / "LICENSE").write_text("MIT\n")
    (package / "README.md").write_text("# Demo\n")
    source = package / "citry_lsp"
    source.mkdir()
    (source / "code.py").write_text('URL = "https://github.com/citry-dev/citry/blob/main/x"\n')
    monkeypatch.setattr(verify_citry_lsp_distribution, "PACKAGE_ROOT", package)
    monkeypatch.setattr(verify_citry_lsp_distribution, "SOURCE_ROOT", source)

    monkeypatch.delenv(release_links.TAG_PREFIX_ENV, raising=False)
    plain = verify_citry_lsp_distribution._checkout_sdist_files()
    monkeypatch.setenv(release_links.TAG_PREFIX_ENV, "demo@")
    pinned = verify_citry_lsp_distribution._checkout_sdist_files()

    # Only the manifest is expected rewritten; code keeps its bytes, links and all.
    assert f"/blob/{TAG}/CHANGELOG.md".encode() in pinned["pyproject.toml"]
    assert {name for name in plain if plain[name] != pinned[name]} == {"pyproject.toml"}


def test_vscode_verifier_expects_the_pinned_readme_and_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = tmp_path / "vscode"
    package.mkdir()
    (package / "package.json").write_text('{"version": "0.3.0", "homepage": "https://citry.dev/"}', encoding="utf-8")
    (package / "README.md").write_text("![x](https://raw.githubusercontent.com/citry-dev/citry/main/x.gif)\n")
    monkeypatch.setattr(verify_vscode_citry_distribution, "PACKAGE_ROOT", package)
    monkeypatch.setenv(release_links.TAG_PREFIX_ENV, "vscode-citry@")

    readme = release_links.checkout_bytes(package, package / "README.md")
    assert readme == b"![x](https://raw.githubusercontent.com/citry-dev/citry/vscode-citry@0.3.0/x.gif)\n"
    assert verify_vscode_citry_distribution.package_manifest()["version"] == "0.3.0"
    # vsce writes the VSIX manifest from package.json, so the verifier scans it directly.
    manifest = b'<Link href="https://github.com/citry-dev/citry/tree/main/packages/editors/vscode"/>'
    assert release_links.unpinned_links(manifest, package) == [
        "https://github.com/citry-dev/citry/tree/main/packages/editors/vscode"
    ]
