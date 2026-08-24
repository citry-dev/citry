"""Validated data and text projections for the Community package directory."""

from __future__ import annotations

import re
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from html import escape
from typing import TYPE_CHECKING, Any
from unicodedata import category as unicode_category
from urllib.parse import urlsplit

from packaging.specifiers import InvalidSpecifier, SpecifierSet

from docs_site._internal.config_loading import (
    DocsConfigError,
    load_yaml,
    require_bool,
    require_int,
    require_keys,
    require_list,
    require_mapping,
    require_str,
    require_str_list,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


COMMUNITY_PACKAGE_PATHS = frozenset(
    {
        "community/extensions/",
        "community/ui-libraries/",
    }
)
COMMUNITY_PACKAGES_LIST_START = "<!-- docs-community-packages:start:{category} -->"
COMMUNITY_PACKAGES_LIST_END = "<!-- docs-community-packages:end:{category} -->"

_CATALOG_SCHEMA_VERSION = 1
_CATEGORIES = {
    "extension": "Community extensions",
    "ui_library": "Community UI libraries",
}
_OWNERSHIP = {
    "community": "Community maintained",
    "official": "Citry maintained",
}
_FORBIDDEN_TEXT_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Co", "Cn", "Zl", "Zp"})
_DISTRIBUTION_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")
_PACKAGE_LIST_BLOCK_RE = re.compile(
    r"<!-- docs-community-packages:start:(?P<category>[a-z_]+) -->"
    r".*?"
    r"<!-- docs-community-packages:end:(?P=category) -->",
    re.DOTALL,
)


class CommunityPackageCatalogError(DocsConfigError):
    """One invalid catalog value, with its authored location when known."""

    def __init__(self, source: Path, message: str, *, line: int | None = None) -> None:
        self.source = source
        self.line = line
        self.message = message
        location = f"{source}:{line}" if line is not None else str(source)
        super().__init__(f"{location}: {message}")


@dataclass(frozen=True, slots=True)
class CommunityPackage:
    """One reviewed package listing."""

    distribution: str
    name: str
    categories: tuple[str, ...]
    summary: str
    ownership: str
    published: bool
    citry_requirement: str
    source_url: str
    docs_url: str
    maintainer: str
    maintainer_url: str
    notice: str

    @property
    def normalized_distribution(self) -> str:
        """Return the PEP 503-normalized distribution name."""
        return re.sub(r"[-_.]+", "-", self.distribution).lower()

    @property
    def dom_id(self) -> str:
        return f"package-{self.normalized_distribution}"

    @property
    def pypi_url(self) -> str:
        return f"https://pypi.org/project/{self.normalized_distribution}/" if self.published else ""

    @property
    def primary_url(self) -> str:
        return self.docs_url or self.pypi_url or self.source_url

    @property
    def primary_url_external(self) -> bool:
        return _is_external_url(self.primary_url)

    @property
    def docs_url_external(self) -> bool:
        return _is_external_url(self.docs_url)

    @property
    def maintainer_url_external(self) -> bool:
        return _is_external_url(self.maintainer_url)

    @property
    def ownership_label(self) -> str:
        return _OWNERSHIP[self.ownership]

    @property
    def install_command(self) -> str:
        return f"pip install {self.distribution}"


@dataclass(frozen=True, slots=True)
class CommunityPackageCatalog:
    """The immutable, alphabetically ordered reviewed package catalog."""

    source: Path
    packages: tuple[CommunityPackage, ...]

    def packages_for(self, category: str) -> tuple[CommunityPackage, ...]:
        """Return packages in one known category."""
        if category not in _CATEGORIES:
            choices = ", ".join(sorted(_CATEGORIES))
            raise ValueError(f"Unknown Community package category {category!r}; expected one of: {choices}")
        return tuple(package for package in self.packages if category in package.categories)

    def category_label(self, category: str) -> str:
        """Return the reader-facing label for one known category."""
        self.packages_for(category)
        return _CATEGORIES[category]


_current_catalog: ContextVar[CommunityPackageCatalog | None] = ContextVar(
    "docs_community_package_catalog",
    default=None,
)


def load_community_package_catalog(path: Path) -> CommunityPackageCatalog:
    """Load and strictly validate the reviewed Community package catalog."""
    try:
        root = require_mapping(load_yaml(path), str(path))
        require_keys(root, str(path), required={"schema_version", "packages"})
        schema_version = require_int(root["schema_version"], f"{path}.schema_version", minimum=1)
        if schema_version != _CATALOG_SCHEMA_VERSION:
            raise DocsConfigError(f"{path}.schema_version must be {_CATALOG_SCHEMA_VERSION}, got {schema_version}")
        raw_packages = require_list(root["packages"], f"{path}.packages")
    except DocsConfigError as exc:
        raise CommunityPackageCatalogError(path, str(exc), line=1) from exc

    packages: list[CommunityPackage] = []
    seen_distributions: dict[str, int] = {}
    for index, raw_package in enumerate(raw_packages):
        label = f"{path}.packages[{index}]"
        line = _package_line(path, index)
        try:
            item = require_mapping(raw_package, label)
            require_keys(
                item,
                label,
                required={
                    "distribution",
                    "name",
                    "categories",
                    "summary",
                    "ownership",
                    "published",
                    "citry_requirement",
                    "source_url",
                    "maintainer",
                },
                optional={"docs_url", "maintainer_url", "notice"},
            )
            distribution = require_str(item["distribution"], f"{label}.distribution")
            if len(distribution) > 200:
                raise DocsConfigError(f"{label}.distribution may not exceed 200 characters")
            if not _DISTRIBUTION_RE.fullmatch(distribution):
                raise DocsConfigError(f"{label}.distribution must be a valid Python distribution name")
            normalized = re.sub(r"[-_.]+", "-", distribution).lower()
            if normalized in seen_distributions:
                first = seen_distributions[normalized]
                raise DocsConfigError(
                    f"{label}.distribution duplicates packages[{first}] after Python name normalization"
                )

            categories = require_str_list(item["categories"], f"{label}.categories")
            if not categories:
                raise DocsConfigError(f"{label}.categories must contain at least one category")
            unknown_categories = set(categories) - set(_CATEGORIES)
            if unknown_categories:
                choices = ", ".join(sorted(_CATEGORIES))
                raise DocsConfigError(
                    f"{label}.categories contains unknown value(s): "
                    f"{', '.join(sorted(unknown_categories))}; expected: {choices}"
                )

            ownership = require_str(item["ownership"], f"{label}.ownership")
            if ownership not in _OWNERSHIP:
                choices = ", ".join(sorted(_OWNERSHIP))
                raise DocsConfigError(f"{label}.ownership must be one of: {choices}")

            citry_requirement = _require_single_line(
                item["citry_requirement"],
                f"{label}.citry_requirement",
                max_length=200,
            )
            try:
                SpecifierSet(citry_requirement)
            except InvalidSpecifier as exc:
                raise DocsConfigError(f"{label}.citry_requirement is not a valid version specifier") from exc

            package = CommunityPackage(
                distribution=distribution,
                name=_require_single_line(item["name"], f"{label}.name", max_length=120),
                categories=categories,
                summary=_require_single_line(item["summary"], f"{label}.summary", max_length=300),
                ownership=ownership,
                published=require_bool(item["published"], f"{label}.published"),
                citry_requirement=citry_requirement,
                source_url=_require_url(item["source_url"], f"{label}.source_url", absolute_only=True),
                docs_url=_require_url(
                    item.get("docs_url", ""),
                    f"{label}.docs_url",
                    allow_empty=True,
                ),
                maintainer=_require_single_line(item["maintainer"], f"{label}.maintainer", max_length=120),
                maintainer_url=_require_url(
                    item.get("maintainer_url", ""),
                    f"{label}.maintainer_url",
                    allow_empty=True,
                ),
                notice=_require_single_line(
                    item.get("notice", ""),
                    f"{label}.notice",
                    allow_empty=True,
                    max_length=300,
                ),
            )
        except DocsConfigError as exc:
            raise CommunityPackageCatalogError(path, str(exc), line=line) from exc

        seen_distributions[normalized] = index
        packages.append(package)

    packages.sort(key=lambda package: (package.name.casefold(), package.normalized_distribution))
    return CommunityPackageCatalog(source=path, packages=tuple(packages))


@contextmanager
def use_community_package_catalog(
    catalog: CommunityPackageCatalog,
) -> Iterator[CommunityPackageCatalog]:
    """Make ``catalog`` available to package-list components during one render."""
    token = _current_catalog.set(catalog)
    try:
        yield catalog
    finally:
        _current_catalog.reset(token)


def current_community_package_catalog() -> CommunityPackageCatalog:
    """Return the catalog provided for the current render."""
    catalog = _current_catalog.get()
    if catalog is None:
        raise RuntimeError("No Community package catalog is active for this render")
    return catalog


def community_package_list_markdown(catalog: CommunityPackageCatalog, category: str) -> str:
    """Render the concise text projection for one package category."""
    packages = catalog.packages_for(category)
    if not packages:
        return f"No packages are listed under {catalog.category_label(category)} yet."

    lines: list[str] = []
    for package in packages:
        availability = "published on PyPI" if package.published else "not yet published on PyPI"
        links = [_markdown_link("Source", package.source_url)]
        if package.published:
            links.insert(0, _markdown_link("PyPI", package.pypi_url))
        if package.docs_url:
            links.insert(0, _markdown_link("Documentation", package.docs_url))
        maintainer = _escape_markdown_text(package.maintainer)
        if package.maintainer_url:
            maintainer = _markdown_link(package.maintainer, package.maintainer_url)
        lines.append(
            f"- {_markdown_link(package.name, package.primary_url)} "
            f"({package.ownership_label.lower()}; {availability}): "
            f"{_escape_markdown_text(package.summary)} "
            f"Requires `citry{package.citry_requirement}`. Maintained by {maintainer}. "
            f"{' | '.join(links)}"
        )
        if package.notice:
            lines.append(f"  Notice: {_escape_markdown_text(package.notice)}")
    return "\n".join(lines)


def project_community_package_lists_for_text(source: str, catalog: CommunityPackageCatalog) -> str:
    """Replace rendered package-list marker blocks with concise Markdown lists."""

    def replace(match: re.Match[str]) -> str:
        return community_package_list_markdown(catalog, match.group("category"))

    return _PACKAGE_LIST_BLOCK_RE.sub(replace, source)


def _require_single_line(
    value: Any,
    label: str,
    *,
    allow_empty: bool = False,
    max_length: int,
) -> str:
    raw = require_str(value, label, allow_empty=allow_empty)
    if allow_empty and not raw.strip():
        return ""
    if any(unicode_category(character) in _FORBIDDEN_TEXT_CATEGORIES for character in raw):
        raise DocsConfigError(f"{label} must be one line of plain text without control characters")
    text = raw.strip()
    if len(text) > max_length:
        raise DocsConfigError(f"{label} may not exceed {max_length} characters")
    return text


def _require_url(
    value: Any,
    label: str,
    *,
    allow_empty: bool = False,
    absolute_only: bool = False,
) -> str:
    raw = require_str(value, label, allow_empty=allow_empty)
    if allow_empty and not raw.strip():
        return ""
    if any(character.isspace() or unicode_category(character) in _FORBIDDEN_TEXT_CATEGORIES for character in raw):
        raise DocsConfigError(f"{label} may not contain whitespace or control characters")
    url = raw.strip()
    if len(url) > 2048:
        raise DocsConfigError(f"{label} may not exceed 2048 characters")
    if any(character in url for character in "<>\\"):
        raise DocsConfigError(f"{label} may not contain angle brackets or backslashes")
    if url.startswith("/") and not url.startswith("//"):
        if absolute_only:
            raise DocsConfigError(f"{label} must be an absolute HTTPS URL")
        return url
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError as exc:
        raise DocsConfigError(f"{label} must be a valid HTTPS URL") from exc
    if parsed.scheme != "https" or not hostname or parsed.username or parsed.password:
        expected = "an absolute HTTPS URL" if absolute_only else "an HTTPS or root-relative URL"
        raise DocsConfigError(f"{label} must be {expected}")
    return url


def _markdown_link(label: str, url: str) -> str:
    return f"[{_escape_markdown_text(label)}](<{url}>)"


def _is_external_url(url: str) -> bool:
    return url.startswith("https://")


def _escape_markdown_text(value: str) -> str:
    escaped = escape(value, quote=False)
    return re.sub(r"([\\`*_[\]{}])", r"\\\1", escaped)


def _package_line(path: Path, index: int) -> int | None:
    """Find the authored line for a package entry in the conventional YAML shape."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return None
    in_packages = False
    entries: list[int] = []
    for line_number, line in enumerate(lines, start=1):
        if not in_packages:
            in_packages = line.strip() == "packages:"
            continue
        if line and not line.startswith((" ", "\t", "#")):
            break
        if re.match(r"^  -(?:\s|$)", line):
            entries.append(line_number)
    return entries[index] if index < len(entries) else None
