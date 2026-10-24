"""
Point the repository links in a package's published text at the package's release tag.

PyPI and the VS Code Marketplace keep each release's README, changelog, and
project URLs forever. A link to `main` in that text breaks for every old
release as soon as the file it names moves or is deleted. The files in the
repository keep their `main` links, because those render correctly on GitHub
and stay current there. The release workflow rewrites them only in its own
checkout, just before it builds the package, so every published copy names
the tag of the release it belongs to, such as `citry-core@1.9.0`.

    python scripts/release_links.py pin packages/py/citry_ui

`pin` rewrites, in place, each file of the package directory that
`PINNED_NAMES` lists. It builds the tag from `CITRY_RELEASE_TAG_PREFIX`, which
each publish workflow sets to its package's tag prefix (`citry-ui@`), and the
version in the package's own manifest. The publish workflow creates that tag
only after it publishes the package, so the links do not resolve yet while
the workflow checks the built package. Nothing here fetches them.

The distribution verifiers read those same files through `checkout_bytes`.
When `CITRY_RELEASE_TAG_PREFIX` is set they expect the rewritten bytes, so an
artifact built without the rewrite, or with another tag, fails verification.
They also reject generated metadata that still links to `main`, or to
another version of the same package. When the
variable is unset (pull-request CI and local runs) they compare the files
unchanged.

This module uses only the standard library because the verifiers import it
on every supported Python, including 3.10.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

_tomllib: Any
try:
    import tomllib as _stdlib_tomllib
except ModuleNotFoundError:  # Python 3.10, where the verifiers also run.
    _tomllib = None
else:
    _tomllib = _stdlib_tomllib

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

TAG_PREFIX_ENV: Final = "CITRY_RELEASE_TAG_PREFIX"

# Files in a package directory that ship as published text: the README and
# changelog a registry displays, and the manifests whose URLs become project
# links. Every other shipped file keeps its bytes.
PINNED_NAMES: Final = frozenset({"README.md", "CHANGELOG.md", "pyproject.toml", "package.json"})

# The start of a URL into this repository. The host and organization are
# matched without regard to case, because GitHub treats them that way.
_REPO: Final = r"(?i:https?://(?:www\.)?github\.com/citry-dev/citry/)"
_RAW: Final = r"(?i:https?://raw\.githubusercontent\.com/citry-dev/citry/)"
# `main` as a whole path segment. Anything but a word character, a hyphen,
# or a dot that starts a file extension may follow, so `tree/main.` at the end
# of a sentence counts while `main.py` and `maintenance` do not.
_MAIN: Final = r"main(?![\w-]|\.\w)"

# A link the rewrite can pin: a GitHub file, folder, or raw view, or a
# raw.githubusercontent.com download, on `main` or its long spelling
# `refs/heads/main`. Group 1 keeps the host and the view, so a rewrite only
# swaps the branch for the tag.
_PINNABLE_RE: Final = re.compile(rf"({_REPO}(?:blob|tree|raw)/|{_RAW})(?:refs/heads/)?{_MAIN}")
# Any link into the repository that names `main`, in any view. This is
# deliberately wider than the rewrite, so a form the rewrite misses (such as
# `commits/main`) fails the release instead of shipping. Edit links are the
# one exception: an edit is always made on `main`.
_ANY_MAIN_RE: Final = re.compile(rf"(?:{_REPO}(?!edit/)[A-Za-z]+/|{_RAW})(?:refs/heads/)?{_MAIN}[^\s\"'<>()\[\]`|*]*")
# A file, folder, or raw link pinned to a release tag, written plainly
# (`citry@0.7.0`) or URL-encoded (`citry%400.7.0`): the form the rewrite
# produces. Group 1 is the tag.
_TAG_LINK_RE: Final = re.compile(
    rf"(?:{_REPO}(?:blob|tree|raw)/|{_RAW})([a-z0-9-]+(?:@|%40)[0-9][^/\s\"'<>()\[\]#?`|*]*)"
)
# Sentence punctuation that can follow a link without being part of it.
_TRAILING_PUNCTUATION: Final = ".,;:!"
_TAG_PREFIX_RE: Final = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*@")
_VERSION_RE: Final = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+[A-Za-z0-9.+-]*")
# The first `version = "..."` line, which is the `[project]` version in every
# package manifest here; the publish workflows read it the same way.
_PYPROJECT_VERSION_RE: Final = re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE)


class ReleaseLinkError(ValueError):
    """The release tag cannot be built, or a file cannot be rewritten."""


def main_links(text: str) -> list[str]:
    """Return each link into the repository that still names `main`, in the order it appears."""
    return [match.group(0).rstrip(_TRAILING_PUNCTUATION) for match in _ANY_MAIN_RE.finditer(text)]


def pin(text: str, ref: str) -> str:
    """Return the text with every pinnable link to `main` pointing at `ref` instead."""
    # The long `refs/heads/` spelling names a branch, so it goes along with `main`.
    return _PINNABLE_RE.sub(lambda match: f"{match.group(1)}{ref}", text)


def package_version(package_dir: Path) -> str:
    """Return the version the package directory's manifest declares."""
    pyproject = package_dir / "pyproject.toml"
    try:
        if pyproject.is_file():
            text = pyproject.read_text(encoding="utf-8")
            # Read `[project].version` the way scripts/release.py does when
            # tomllib exists; the first `version =` line is the 3.10 fallback,
            # the same line the publish workflows read.
            if _tomllib is not None:
                version: object = _tomllib.loads(text).get("project", {}).get("version", "")
            else:
                match = _PYPROJECT_VERSION_RE.search(text)
                version = match.group(1) if match else ""
        else:
            payload = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
            version = payload.get("version", "") if isinstance(payload, dict) else ""
    except (OSError, ValueError) as error:
        msg = f"cannot read the version of {package_dir}: {error}"
        raise ReleaseLinkError(msg) from error
    if not isinstance(version, str) or not _VERSION_RE.fullmatch(version):
        msg = f"{package_dir} declares no usable version: {version!r}"
        raise ReleaseLinkError(msg)
    return version


def release_tag(package_dir: Path, environ: Mapping[str, str] | None = None) -> str | None:
    """Return the tag this package's release will create, or None outside a release."""
    prefix = (os.environ if environ is None else environ).get(TAG_PREFIX_ENV, "")
    if not prefix:
        return None
    # A typo here would publish links to a tag that never exists, so the
    # prefix must look like the `<package>@` prefixes scripts/release.py uses.
    if not _TAG_PREFIX_RE.fullmatch(prefix):
        msg = f"{TAG_PREFIX_ENV} must be a package tag prefix such as 'citry-core@', got {prefix!r}"
        raise ReleaseLinkError(msg)
    return f"{prefix}{package_version(package_dir)}"


def _pinned_bytes(payload: bytes, ref: str) -> bytes:
    # Bytes in and out, so a file's line endings stay exactly as checked in
    # (a text-mode write on Windows would turn every LF into CRLF).
    return pin(payload.decode("utf-8"), ref).encode("utf-8")


def checkout_bytes(package_dir: Path, path: Path, environ: Mapping[str, str] | None = None) -> bytes:
    """
    Return the bytes a release artifact should hold for this checkout file.

    During a release, a file that `pin_package` rewrites (one `PINNED_NAMES`
    lists, directly inside `package_dir`) is expected after `pin`, because
    that is what the build saw. Every other file, and every file outside a
    release, is expected unchanged. A README deeper in the tree, such as a
    crate's, is not rewritten by the pin step, so it is not pinned here either.
    Pinning twice gives the same bytes, so this also holds on a checkout that
    the pin step already rewrote.
    """
    payload = path.read_bytes()
    tag = release_tag(package_dir, environ)
    if tag is None or path.parent != package_dir or path.name not in PINNED_NAMES:
        return payload
    return _pinned_bytes(payload, tag)


def unpinned_links(payload: bytes, package_dir: Path, environ: Mapping[str, str] | None = None) -> list[str]:
    """
    Return the links in an artifact's published text that do not name this release's tag.

    That is every link to `main`, and every file, folder, or raw link pinned
    to another version of this package, such as one left from an older
    release. Links to other packages' tags are left alone: they name a
    release that already exists. Verifiers call this on generated text, such
    as a wheel's METADATA, that no checkout file can be compared against byte
    for byte. Outside a release links to `main` are expected, so the result
    is always empty.
    """
    tag = release_tag(package_dir, environ)
    if tag is None:
        return []
    prefix = tag[: tag.index("@") + 1]
    text = payload.decode("utf-8", errors="replace")
    stale = []
    for match in _TAG_LINK_RE.finditer(text):
        found = match.group(1).replace("%40", "@").rstrip(_TRAILING_PUNCTUATION)
        if found.startswith(prefix) and found != tag:
            stale.append(match.group(0).rstrip(_TRAILING_PUNCTUATION))
    return main_links(text) + stale


def pin_package(package_dir: Path, ref: str) -> list[Path]:
    """Rewrite each published text file in the package directory; return the files that changed."""
    changed: list[Path] = []
    for name in sorted(PINNED_NAMES):
        path = package_dir / name
        if not path.is_file():
            continue
        payload = path.read_bytes()
        pinned = _pinned_bytes(payload, ref)
        if pinned != payload:
            # Writing through the path follows a symlink, so the citry
            # package's README link rewrites the repository-root README it
            # points at, which is the file setuptools reads.
            path.write_bytes(pinned)
            changed.append(path)
    return changed


def main(argv: Sequence[str] | None = None) -> int:
    """Rewrite the published text of the named package directories to their release tag."""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    pin_parser = commands.add_parser("pin", help=f"Rewrite links to main to the tag {TAG_PREFIX_ENV} names.")
    pin_parser.add_argument("package_dirs", nargs="+", type=Path)
    args = parser.parse_args(argv)
    try:
        for package_dir in args.package_dirs:
            if not package_dir.is_dir():
                msg = f"package directory does not exist: {package_dir}"
                raise ReleaseLinkError(msg)
            tag = release_tag(package_dir)
            # The verifiers expect pinned bytes only when the variable is set,
            # so a pin step without it would silently publish links to main.
            if tag is None:
                msg = f"{TAG_PREFIX_ENV} is not set; the publish workflow sets it to the package's tag prefix"
                raise ReleaseLinkError(msg)
            for path in pin_package(package_dir, tag):
                sys.stdout.write(f"pinned links in {path.as_posix()} to {tag}\n")
    except ReleaseLinkError as error:
        sys.stderr.write(f"release link pinning failed: {error}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
