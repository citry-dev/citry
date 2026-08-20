"""Build, inspect, install, and promote the citry-ui release pair."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import runpy
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Final

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 qualification runner
    tomllib = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from email.message import Message

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
PACKAGE_ROOT: Final = REPO_ROOT / "packages" / "py" / "citry_ui"
QUALIFIER: Final = PACKAGE_ROOT / "citry_ui" / "quality" / "qualify_wheel.py"
MAX_SDIST_BYTES: Final = 700 * 1024
EXPECTED_REQUIRES_DIST: Final = {"citry<0.5.0,>=0.4.0"}


class DistributionVerificationError(RuntimeError):
    """A built distribution differs from the checked source or cannot run."""


def sha256_bytes(value: bytes) -> str:
    """Return one lowercase SHA-256 digest."""
    return hashlib.sha256(value).hexdigest()


def package_version() -> str:
    """Read the package version from the release manifest."""
    content = (PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    if tomllib is None:
        project = re.search(r"(?ms)^\[project\][ \t]*\n(?P<body>.*?)(?=^\[|\Z)", content)
        version_line = (
            None
            if project is None
            else re.search(
                r"""(?m)^version\s*=\s*["'](?P<version>[^"']+)["']\s*(?:#.*)?$""",
                project.group("body"),
            )
        )
        version: Any = None if version_line is None else version_line.group("version")
    else:
        version = tomllib.loads(content)["project"].get("version")
    if not isinstance(version, str) or not version:
        raise DistributionVerificationError("citry-ui has no project version")
    return version


def expected_release_filenames(version: str) -> set[str]:
    """Return the complete, closed citry-ui release set."""
    return {
        f"citry_ui-{version}-py3-none-any.whl",
        f"citry_ui-{version}.tar.gz",
    }


def _qualifier_namespace() -> dict[str, Any]:
    """Load the wheel boundary without importing the unbuilt citry_ui package."""
    return runpy.run_path(str(QUALIFIER))


def runtime_source_inventory() -> dict[str, str]:
    """Hash every checked source file that belongs in the installed wheel."""
    namespace = _qualifier_namespace()
    expected = namespace["EXPECTED_RUNTIME_FILES"] | namespace["EXPECTED_I18N_FILES"]
    inventory: dict[str, str] = {}
    for name in sorted(expected):
        path = PACKAGE_ROOT / name
        if not path.is_file():
            raise DistributionVerificationError(f"checked runtime file is missing: {name}")
        inventory[name] = sha256_bytes(path.read_bytes())
    return inventory


def _safe_archive_name(name: str, *, artifact: Path) -> PurePosixPath:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or "\\" in name:
        raise DistributionVerificationError(f"{artifact.name} contains unsafe member {name!r}")
    return path


def _parse_metadata(payload: bytes, *, artifact: Path) -> Message:
    try:
        return BytesParser().parsebytes(payload)
    except Exception as error:
        raise DistributionVerificationError(f"cannot parse metadata in {artifact.name}: {error}") from error


def _require_metadata(metadata: Message, *, artifact: Path, version: str) -> None:
    if metadata.get("Name", "").lower().replace("_", "-") != "citry-ui":
        raise DistributionVerificationError(f"{artifact.name} has unexpected Name metadata")
    if metadata.get("Version") != version:
        raise DistributionVerificationError(f"{artifact.name} has unexpected Version metadata")
    if metadata.get("Requires-Python") not in {">=3.10, <4.0", "<4.0,>=3.10"}:
        raise DistributionVerificationError(f"{artifact.name} has unexpected Requires-Python metadata")
    if set(metadata.get_all("Requires-Dist", [])) != EXPECTED_REQUIRES_DIST:
        raise DistributionVerificationError(f"{artifact.name} has unexpected runtime dependencies")
    if metadata.get_all("Provides-Extra", []):
        raise DistributionVerificationError(f"{artifact.name} has unexpected optional extras")
    if "Development Status :: 3 - Alpha" not in metadata.get_all("Classifier", []):
        raise DistributionVerificationError(f"{artifact.name} is missing the alpha classifier")


def archive_inventory(path: Path) -> dict[str, str]:
    """Hash every regular member of a wheel and reject duplicate names."""
    with zipfile.ZipFile(path) as archive:
        entries = [entry for entry in archive.infolist() if not entry.is_dir()]
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)):
            raise DistributionVerificationError(f"{path.name} contains duplicate member names")
        return {name: sha256_bytes(archive.read(name)) for name in sorted(names)}


def verify_wheel(path: Path, *, version: str) -> dict[str, Any]:
    """Validate the closed wheel boundary and its bytes against the checkout."""
    expected_name = f"citry_ui-{version}-py3-none-any.whl"
    if path.name != expected_name:
        raise DistributionVerificationError(f"expected wheel {expected_name!r}, found {path.name!r}")
    namespace = _qualifier_namespace()
    try:
        namespace["qualify_wheel"](path)
    except namespace["WheelQualificationError"] as error:
        raise DistributionVerificationError(str(error)) from error

    expected_payload = runtime_source_inventory()
    with zipfile.ZipFile(path) as archive:
        actual_payload = {name: sha256_bytes(archive.read(name)) for name in expected_payload}
        metadata = _parse_metadata(
            archive.read(f"citry_ui-{version}.dist-info/METADATA"),
            artifact=path,
        )
    _require_metadata(metadata, artifact=path, version=version)
    require_equal("checkout and wheel runtime payload", expected_payload, actual_payload)
    return _release_artifact_report(path)


def _checkout_sdist_files() -> dict[str, bytes]:
    """Return every checked file allowed in the source distribution."""
    result = {
        name: (PACKAGE_ROOT / name).read_bytes()
        for name in (
            "CHANGELOG.md",
            "LICENSE",
            "MANIFEST.in",
            "README.md",
            "THIRD_PARTY_LICENSES.md",
            "pyproject.toml",
        )
    }
    for name in runtime_source_inventory():
        result[name] = (PACKAGE_ROOT / name).read_bytes()
    # The sdist retains the package-level portable tests as build evidence.
    for path in sorted((PACKAGE_ROOT / "tests").glob("test_*.py")):
        result[path.relative_to(PACKAGE_ROOT).as_posix()] = path.read_bytes()
    return result


def verify_sdist(path: Path, *, version: str) -> dict[str, Any]:
    """Validate the closed source archive without extracting or executing it."""
    expected_name = f"citry_ui-{version}.tar.gz"
    if path.name != expected_name:
        raise DistributionVerificationError(f"expected sdist {expected_name!r}, found {path.name!r}")
    if path.stat().st_size > MAX_SDIST_BYTES:
        raise DistributionVerificationError(
            f"{path.name} is {path.stat().st_size} bytes; the release cap is {MAX_SDIST_BYTES} bytes"
        )
    expected_root = f"citry_ui-{version}"
    try:
        with tarfile.open(path, "r:gz") as archive:
            members = archive.getmembers()
            names = [member.name for member in members]
            for name in names:
                _safe_archive_name(name, artifact=path)
            if len(names) != len(set(names)):
                raise DistributionVerificationError(f"{path.name} contains duplicate member names")
            if any(member.issym() or member.islnk() or member.isdev() for member in members):
                raise DistributionVerificationError(f"{path.name} contains links or device members")
            files: dict[str, bytes] = {}
            for member in members:
                if not member.isfile():
                    continue
                stream = archive.extractfile(member)
                if stream is None:
                    raise DistributionVerificationError(f"cannot read {member.name!r} from {path.name}")
                files[member.name] = stream.read()
    except tarfile.TarError as error:
        raise DistributionVerificationError(f"{path.name} is not a valid sdist: {error}") from error

    roots = {PurePosixPath(name).parts[0] for name in files}
    if roots != {expected_root}:
        raise DistributionVerificationError(f"{path.name} must have only the root {expected_root!r}")
    relative = {name.removeprefix(f"{expected_root}/"): payload for name, payload in files.items()}
    generated = {
        "PKG-INFO",
        "setup.cfg",
        "citry_ui.egg-info/PKG-INFO",
        "citry_ui.egg-info/SOURCES.txt",
        "citry_ui.egg-info/dependency_links.txt",
        "citry_ui.egg-info/requires.txt",
        "citry_ui.egg-info/top_level.txt",
    }
    checkout = _checkout_sdist_files()
    expected = set(checkout) | generated
    missing = sorted(expected - set(relative))
    unexpected = sorted(set(relative) - expected)
    if missing or unexpected:
        raise DistributionVerificationError(
            f"{path.name} member inventory mismatch; missing={missing!r}; unexpected={unexpected!r}"
        )
    for name, payload in checkout.items():
        if relative[name] != payload:
            raise DistributionVerificationError(f"{path.name} contains changed source bytes in {name}")

    _require_metadata(_parse_metadata(relative["PKG-INFO"], artifact=path), artifact=path, version=version)
    if relative["citry_ui.egg-info/PKG-INFO"] != relative["PKG-INFO"]:
        raise DistributionVerificationError(f"{path.name} contains inconsistent PKG-INFO files")
    if relative["setup.cfg"] != b"[egg_info]\ntag_build = \ntag_date = 0\n\n":
        raise DistributionVerificationError(f"{path.name} contains an unexpected generated setup.cfg")
    if relative["citry_ui.egg-info/dependency_links.txt"] != b"\n":
        raise DistributionVerificationError(f"{path.name} contains unexpected dependency links")
    if relative["citry_ui.egg-info/requires.txt"] != b"citry<0.5.0,>=0.4.0\n":
        raise DistributionVerificationError(f"{path.name} contains unexpected runtime dependencies")
    if relative["citry_ui.egg-info/top_level.txt"] != b"citry_ui\ncitry_ui_i18n\n":
        raise DistributionVerificationError(f"{path.name} contains unexpected top-level packages")
    sources = relative["citry_ui.egg-info/SOURCES.txt"].decode("utf-8").splitlines()
    expected_sources = set(checkout) | {name for name in generated if name.startswith("citry_ui.egg-info/")}
    if len(sources) != len(set(sources)) or set(sources) != expected_sources:
        raise DistributionVerificationError(f"{path.name} contains an inconsistent SOURCES.txt")
    return _release_artifact_report(path)


def require_equal(label: str, expected: Mapping[str, str], actual: Mapping[str, str]) -> None:
    """Raise with a bounded path diff when two inventories differ."""
    if expected == actual:
        return
    names = sorted(set(expected) | set(actual))
    differences = [name for name in names if expected.get(name) != actual.get(name)]
    shown = ", ".join(differences[:20])
    suffix = "" if len(differences) <= 20 else f" and {len(differences) - 20} more"
    raise DistributionVerificationError(f"{label} differs at {shown}{suffix}")


def _release_artifact_report(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {"name": path.name, "bytes": len(payload), "sha256": sha256_bytes(payload)}


def _release_report(wheel: Path, sdist: Path) -> dict[str, Any]:
    return {
        "version": package_version(),
        "artifacts": sorted(
            (_release_artifact_report(wheel), _release_artifact_report(sdist)),
            key=lambda artifact: artifact["name"],
        ),
    }


def _require_empty_output(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise DistributionVerificationError(f"output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)


def stage_qualification(wheel: Path, sdist: Path, output_dir: Path) -> dict[str, Any]:
    """Copy only the verified release pair and record their exact bytes."""
    version = package_version()
    actual = {wheel.name, sdist.name}
    expected = expected_release_filenames(version)
    if actual != expected:
        raise DistributionVerificationError(
            f"release inventory mismatch; missing={sorted(expected - actual)!r}; "
            f"unexpected={sorted(actual - expected)!r}"
        )
    _require_empty_output(output_dir)
    shutil.copy2(wheel, output_dir / wheel.name)
    shutil.copy2(sdist, output_dir / sdist.name)
    report = _release_report(wheel, sdist)
    (output_dir / "release-inventory.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def verify_staged_bundle(bundle_dir: Path) -> dict[str, Any]:
    """Re-verify a flat qualification bundle against the tagged checkout."""
    if not bundle_dir.is_dir():
        raise DistributionVerificationError(f"qualification bundle is not a directory: {bundle_dir}")
    entries = sorted(bundle_dir.iterdir())
    if any(entry.is_symlink() or not entry.is_file() for entry in entries):
        raise DistributionVerificationError("qualification bundle must contain only regular root files")
    version = package_version()
    expected_artifacts = expected_release_filenames(version)
    expected_names = expected_artifacts | {"release-inventory.json"}
    by_name = {entry.name: entry for entry in entries}
    if set(by_name) != expected_names:
        raise DistributionVerificationError(
            f"qualification bundle mismatch; missing={sorted(expected_names - set(by_name))!r}; "
            f"unexpected={sorted(set(by_name) - expected_names)!r}"
        )
    wheel = by_name[f"citry_ui-{version}-py3-none-any.whl"]
    sdist = by_name[f"citry_ui-{version}.tar.gz"]
    verify_wheel(wheel, version=version)
    verify_sdist(sdist, version=version)
    report = _release_report(wheel, sdist)
    try:
        recorded: Any = json.loads(by_name["release-inventory.json"].read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DistributionVerificationError(f"cannot read release-inventory.json: {error}") from error
    if recorded != report:
        raise DistributionVerificationError("release-inventory.json does not match the artifact bytes")
    return report


def promote_qualification_archive(
    archive_path: Path,
    *,
    expected_digest: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Check GitHub's digest, extract its flat bundle safely, and verify it."""
    match = re.fullmatch(r"sha256:([0-9a-f]{64})", expected_digest)
    if match is None:
        raise DistributionVerificationError(f"invalid qualification artifact digest: {expected_digest!r}")
    if sha256_bytes(archive_path.read_bytes()) != match.group(1):
        raise DistributionVerificationError("qualification archive SHA-256 does not match GitHub's digest")
    _require_empty_output(output_dir)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise DistributionVerificationError(f"qualification archive has a corrupt member {bad_member!r}")
            entries = [entry for entry in archive.infolist() if not entry.is_dir()]
            names = [entry.filename for entry in entries]
            if len(names) != len(set(names)):
                raise DistributionVerificationError("qualification archive contains duplicate member names")
            for entry in entries:
                member = _safe_archive_name(entry.filename, artifact=archive_path)
                if len(member.parts) != 1:
                    raise DistributionVerificationError(
                        f"qualification archive member must be a root file: {entry.filename!r}"
                    )
                if stat.S_ISLNK(entry.external_attr >> 16):
                    raise DistributionVerificationError(
                        f"qualification archive contains a symbolic link: {entry.filename!r}"
                    )
                (output_dir / entry.filename).write_bytes(archive.read(entry))
    except zipfile.BadZipFile as error:
        raise DistributionVerificationError(f"qualification artifact is not a valid zip: {error}") from error
    return verify_staged_bundle(output_dir)


def _run(command: Sequence[str], *, cwd: Path, env: Mapping[str, str] | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        output = (completed.stdout + completed.stderr).strip()
        raise DistributionVerificationError(f"command failed ({' '.join(command)}):\n{output}")
    return completed.stdout


def _unique(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if len(matches) != 1:
        raise DistributionVerificationError(f"expected one {pattern!r} in {directory}, found {len(matches)}")
    return matches[0]


def _build_sdist_wheel(sdist: Path, directory: Path, *, cwd: Path) -> Path:
    sdist = sdist.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "uv",
            "build",
            str(sdist),
            "--wheel",
            "--out-dir",
            str(directory),
            "--clear",
            "--no-config",
            "--no-build-logs",
        ],
        cwd=cwd,
    )
    return _unique(directory, "*.whl")


_SMOKE = r'''
import importlib.metadata
import importlib.resources
import importlib.util
import pathlib
import sys

import citry_ui
from citry import Citry, Component
from citry.ext.i18n import make_context

assert importlib.metadata.version("citry-ui") == "__VERSION__"
assert citry_ui.__version__ == "__VERSION__"
assert len(citry_ui.COMPONENTS) == 107
assert importlib.resources.files("citry_ui").joinpath("py.typed").is_file()
assert importlib.util.find_spec("citry_ui.quality") is None
assert importlib.util.find_spec("citry_ui.components.ctabs.tests") is None
assert pathlib.Path(citry_ui.__file__).resolve().is_relative_to(pathlib.Path(sys.prefix).resolve())

app = Citry(
    mode="production",
    autodiscover=False,
    extensions_defaults={
        "i18n": {
            "source_locale": "en-US",
            "locales": ("en-US",),
            "catalogs": ("citry_ui_i18n",),
        }
    },
)
installed = app.register_library(citry_ui)
assert installed[citry_ui.CButton]

class Page(Component):
    citry = app
    template = """
      <main>
        <c-CButton type="submit">Installed wheel</c-CButton>
        <c-CPagination c-pages="2" c-page="1" />
      </main>
    """

context = make_context(app, locale="en-US")
html = str(Page().render(provides={"citry_i18n": context}))
assert "Installed wheel" in html
assert "Pagination" in html
assert app.extensions.get_extension("i18n").for_context(context).tr(
    "citry-ui-pagination-label"
) == "Pagination"
'''


def _venv_python(root: Path) -> Path:
    if os.name == "nt":
        return root / "Scripts" / "python.exe"
    return root / "bin" / "python"


def smoke_wheel(wheel: Path, *, cwd: Path) -> None:
    """Install one wheel with public binary dependencies and render components."""
    with tempfile.TemporaryDirectory(prefix="citry-ui-install-") as temporary:
        root = Path(temporary)
        environment = root / "venv"
        _run(["uv", "venv", "--python", sys.executable, "--no-config", str(environment)], cwd=root)
        python = _venv_python(environment)
        _run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "--no-config",
                "--only-binary",
                ":all:",
                str(wheel),
            ],
            cwd=root,
        )
        smoke = _SMOKE.replace("__VERSION__", package_version())
        clean_env = {name: value for name, value in os.environ.items() if name != "PYTHONPATH"}
        _run([str(python), "-I", "-c", smoke], cwd=cwd, env=clean_env)


def verify_dist_directory(dist_dir: Path, *, smoke: bool) -> tuple[Path, Path, dict[str, Any]]:
    """Verify one raw wheel/sdist pair and rebuild the sdist outside the checkout."""
    dist_dir = dist_dir.resolve()
    version = package_version()
    wheel = _unique(dist_dir, f"citry_ui-{version}-py3-none-any.whl")
    sdist = _unique(dist_dir, f"citry_ui-{version}.tar.gz")
    with tempfile.TemporaryDirectory(prefix="citry-ui-sdist-") as temporary:
        root = Path(temporary)
        rebuilt_wheel = _build_sdist_wheel(sdist, root / "wheel", cwd=root)
        verify_wheel(wheel, version=version)
        verify_sdist(sdist, version=version)
        verify_wheel(rebuilt_wheel, version=version)
        require_equal(
            "source-built and sdist-built wheel contents",
            archive_inventory(wheel),
            archive_inventory(rebuilt_wheel),
        )
        if smoke:
            smoke_wheel(wheel, cwd=root)
    return (
        wheel,
        sdist,
        {
            "wheel": _release_artifact_report(wheel),
            "sdist": _release_artifact_report(sdist),
            "installedRuntime": {
                "files": len(runtime_source_inventory()),
                "sha256": sha256_bytes(json.dumps(runtime_source_inventory(), sort_keys=True).encode("utf-8")),
            },
        },
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run qualification, stage a bundle, or promote one exact bundle."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", type=Path)
    parser.add_argument("--stage-output-dir", type=Path)
    parser.add_argument("--skip-install-smoke", action="store_true")
    parser.add_argument("--promote-archive", type=Path)
    parser.add_argument("--artifact-digest")
    parser.add_argument("--promotion-output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.promote_archive is not None:
            if not args.artifact_digest or args.promotion_output_dir is None:
                parser.error("promotion requires --artifact-digest and --promotion-output-dir")
            report = promote_qualification_archive(
                args.promote_archive,
                expected_digest=args.artifact_digest,
                output_dir=args.promotion_output_dir,
            )
        else:
            if args.dist_dir is None:
                parser.error("qualification requires --dist-dir")
            wheel, sdist, report = verify_dist_directory(
                args.dist_dir,
                smoke=not args.skip_install_smoke,
            )
            if args.stage_output_dir is not None:
                report["release"] = stage_qualification(wheel, sdist, args.stage_output_dir)
    except DistributionVerificationError as error:
        parser.exit(1, f"citry-ui distribution verification failed: {error}\n")
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
