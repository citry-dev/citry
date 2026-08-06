"""Strict maintainer-facing settings for the documentation product."""

from __future__ import annotations

import re
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from docs_site._internal.config_loading import (
    DocsConfigError,
    load_yaml,
    require_int,
    require_keys,
    require_list,
    require_mapping,
    require_str,
    require_str_list,
)

_GITHUB_OWNER_RE = re.compile(r"(?!.*--)[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?\Z")
_GITHUB_REPOSITORY_RE = re.compile(r"[A-Za-z0-9_.-]{1,100}\Z")
_PAGEFIND_DIRECTORY_SEGMENT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class RepositorySettings:
    owner: str
    name: str
    url: str
    edit_branch: str
    issues_url: str
    sponsors_url: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"


@dataclass(frozen=True, slots=True)
class QuickLink:
    label: str
    path: str


@dataclass(frozen=True, slots=True)
class MarkdownProfile:
    extensions: tuple[str, ...]
    extension_configs: MappingProxyType[str, MappingProxyType[str, Any]]

    def configs(self) -> dict[str, dict[str, Any]]:
        """Return the mutable shape Python-Markdown expects."""
        return {
            name: {key: _thaw_markdown_option(value) for key, value in values.items()}
            for name, values in self.extension_configs.items()
        }


@dataclass(frozen=True, slots=True)
class BlogSettings:
    feed_path: str
    feed_limit: int
    words_per_minute: int


@dataclass(frozen=True, slots=True)
class GitSettings:
    exclude_patterns: tuple[str, ...]
    max_authors: int


@dataclass(frozen=True, slots=True)
class SeoSettings:
    ai_bots: tuple[str, ...]
    priorities: tuple[tuple[str, float], ...]


@dataclass(frozen=True, slots=True)
class InventorySettings:
    python_docs_url: str


@dataclass(frozen=True, slots=True)
class SiteSettings:
    name: str
    public_url: str
    default_description: str
    language: str
    repository: RepositorySettings
    pypi_url: str
    discord_url: str
    quick_links: tuple[QuickLink, ...]
    pagefind_path: str
    markdown_pages: MarkdownProfile
    markdown_docstrings: MarkdownProfile
    blog: BlogSettings
    git: GitSettings
    seo: SeoSettings
    inventory: InventorySettings
    excluded_releases: tuple[str, ...]


_ROOT_KEYS = frozenset(
    {
        "site",
        "repository",
        "links",
        "search",
        "markdown",
        "blog",
        "git",
        "seo",
        "inventory",
        "release_notes",
    }
)


def load_site_settings(path: Path) -> SiteSettings:
    """Read and fully validate ``settings.yml`` before a build can write output."""
    root = require_mapping(load_yaml(path), str(path))
    require_keys(root, str(path), required=set(_ROOT_KEYS))

    site = require_mapping(root["site"], "site")
    require_keys(site, "site", required={"name", "public_url", "default_description", "language"})

    repository = require_mapping(root["repository"], "repository")
    require_keys(
        repository,
        "repository",
        required={"owner", "name", "url", "edit_branch", "issues_url", "sponsors_url"},
    )
    repo_url = _absolute_url(repository["url"], "repository.url")
    owner = require_str(repository["owner"], "repository.owner")
    repo_name = require_str(repository["name"], "repository.name")
    if not _GITHUB_OWNER_RE.fullmatch(owner):
        raise DocsConfigError("repository.owner must be a GitHub owner name, not a path")
    if not _GITHUB_REPOSITORY_RE.fullmatch(repo_name) or repo_name in {".", ".."}:
        raise DocsConfigError("repository.name must be a GitHub repository name, not a path")
    expected_repo_url = f"https://github.com/{owner}/{repo_name}"
    parsed_repo_url = urlsplit(repo_url)
    if (
        parsed_repo_url.scheme != "https"
        or parsed_repo_url.netloc.lower() != "github.com"
        or parsed_repo_url.path.rstrip("/") != f"/{owner}/{repo_name}"
    ):
        raise DocsConfigError(f"repository.url must be exactly {expected_repo_url}")
    repo_url = repo_url.rstrip("/")
    issues_url = _absolute_url(repository["issues_url"], "repository.issues_url").rstrip("/")
    if issues_url != f"{repo_url}/issues":
        raise DocsConfigError("repository.issues_url must be repository.url plus /issues")

    links = require_mapping(root["links"], "links")
    require_keys(links, "links", required={"pypi", "discord"})

    search = require_mapping(root["search"], "search")
    require_keys(search, "search", required={"pagefind_path", "quick_links"})
    quick_links = tuple(
        _load_quick_link(item, index)
        for index, item in enumerate(require_list(search["quick_links"], "search.quick_links"))
    )
    quick_paths = [link.path for link in quick_links]
    if len(quick_paths) != len(set(quick_paths)):
        raise DocsConfigError("search.quick_links contains duplicate paths")

    markdown_data = require_mapping(root["markdown"], "markdown")
    require_keys(markdown_data, "markdown", required={"pages", "docstrings"})

    blog = require_mapping(root["blog"], "blog")
    require_keys(blog, "blog", required={"feed_path", "feed_limit", "words_per_minute"})
    feed_path = _feed_path(blog["feed_path"], "blog.feed_path")

    git = require_mapping(root["git"], "git")
    require_keys(git, "git", required={"exclude_patterns", "max_authors"})

    seo = require_mapping(root["seo"], "seo")
    require_keys(seo, "seo", required={"ai_bots", "priorities"})
    priorities = tuple(
        _load_priority(item, index) for index, item in enumerate(require_list(seo["priorities"], "seo.priorities"))
    )
    prefixes = [prefix for prefix, _priority in priorities]
    if len(prefixes) != len(set(prefixes)):
        raise DocsConfigError("seo.priorities contains duplicate prefixes")

    inventory = require_mapping(root["inventory"], "inventory")
    require_keys(inventory, "inventory", required={"python_docs_url"})

    releases = require_mapping(root["release_notes"], "release_notes")
    require_keys(releases, "release_notes", required={"exclude"})

    return SiteSettings(
        name=require_str(site["name"], "site.name"),
        public_url=_absolute_url(site["public_url"], "site.public_url", trailing_slash=True),
        default_description=require_str(site["default_description"], "site.default_description"),
        language=require_str(site["language"], "site.language"),
        repository=RepositorySettings(
            owner=owner,
            name=repo_name,
            url=repo_url,
            edit_branch=_git_branch(repository["edit_branch"], "repository.edit_branch"),
            issues_url=issues_url,
            sponsors_url=_absolute_url(repository["sponsors_url"], "repository.sponsors_url"),
        ),
        pypi_url=_absolute_url(links["pypi"], "links.pypi"),
        discord_url=_absolute_url(links["discord"], "links.discord"),
        quick_links=quick_links,
        pagefind_path=_pagefind_path(search["pagefind_path"], "search.pagefind_path"),
        markdown_pages=_load_markdown_profile(markdown_data["pages"], "markdown.pages"),
        markdown_docstrings=_load_markdown_profile(markdown_data["docstrings"], "markdown.docstrings"),
        blog=BlogSettings(
            feed_path=feed_path,
            feed_limit=require_int(blog["feed_limit"], "blog.feed_limit", minimum=1),
            words_per_minute=require_int(blog["words_per_minute"], "blog.words_per_minute", minimum=1),
        ),
        git=GitSettings(
            exclude_patterns=require_str_list(git["exclude_patterns"], "git.exclude_patterns"),
            max_authors=require_int(git["max_authors"], "git.max_authors", minimum=1),
        ),
        seo=SeoSettings(
            ai_bots=require_str_list(seo["ai_bots"], "seo.ai_bots"),
            priorities=priorities,
        ),
        inventory=InventorySettings(
            python_docs_url=_absolute_url(
                inventory["python_docs_url"], "inventory.python_docs_url", trailing_slash=True
            ),
        ),
        excluded_releases=require_str_list(releases["exclude"], "release_notes.exclude"),
    )


def _load_quick_link(value: Any, index: int) -> QuickLink:
    label = f"search.quick_links[{index}]"
    item = require_mapping(value, label)
    require_keys(item, label, required={"label", "path"})
    return QuickLink(
        label=require_str(item["label"], f"{label}.label"),
        path=_root_path(item["path"], f"{label}.path"),
    )


def _load_markdown_profile(value: Any, label: str) -> MarkdownProfile:
    profile = require_mapping(value, label)
    require_keys(profile, label, required={"extensions", "extension_configs"})
    extensions = require_str_list(profile["extensions"], f"{label}.extensions")
    raw_configs = require_mapping(profile["extension_configs"], f"{label}.extension_configs")
    unknown_configs = set(raw_configs) - set(extensions)
    if unknown_configs:
        raise DocsConfigError(
            f"{label}.extension_configs configures disabled extension(s): {', '.join(sorted(unknown_configs))}"
        )
    configs: dict[str, MappingProxyType[str, Any]] = {}
    for extension, raw_values in raw_configs.items():
        values = require_mapping(raw_values, f"{label}.extension_configs.{extension}")
        for key, item in values.items():
            _validate_markdown_option(item, f"{label}.extension_configs.{extension}.{key}")
        configs[extension] = MappingProxyType({key: _freeze_markdown_option(item) for key, item in values.items()})
    return MarkdownProfile(extensions=extensions, extension_configs=MappingProxyType(configs))


def _freeze_markdown_option(value: Any) -> Any:
    """Recursively detach and freeze a validated Markdown option value."""
    if isinstance(value, list):
        return tuple(_freeze_markdown_option(item) for item in value)
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_markdown_option(item) for key, item in value.items()})
    return value


def _thaw_markdown_option(value: Any) -> Any:
    """Return a detached mutable value for Python-Markdown."""
    if isinstance(value, tuple):
        return [_thaw_markdown_option(item) for item in value]
    if isinstance(value, MappingProxyType):
        return {key: _thaw_markdown_option(item) for key, item in value.items()}
    return value


def _validate_markdown_option(
    value: Any,
    label: str,
    *,
    ancestors: frozenset[int] = frozenset(),
    depth: int = 0,
) -> None:
    """Accept only recursively JSON-shaped extension configuration values."""
    if depth > 100:
        raise DocsConfigError(f"{label} is nested too deeply")
    if value is None or isinstance(value, (str, int, bool)):
        return
    if isinstance(value, float):
        if not isfinite(value):
            raise DocsConfigError(f"{label} must be a finite number")
        return
    if isinstance(value, (list, dict)):
        identity = id(value)
        if identity in ancestors:
            raise DocsConfigError(f"{label} contains a cyclic YAML alias")
        ancestors = ancestors | {identity}
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_markdown_option(item, f"{label}[{index}]", ancestors=ancestors, depth=depth + 1)
        return
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        for key, item in value.items():
            _validate_markdown_option(item, f"{label}.{key}", ancestors=ancestors, depth=depth + 1)
        return
    raise DocsConfigError(f"{label} has an unsupported value")


def _load_priority(value: Any, index: int) -> tuple[str, float]:
    label = f"seo.priorities[{index}]"
    item = require_mapping(value, label)
    require_keys(item, label, required={"prefix", "priority"})
    prefix = require_str(item["prefix"], f"{label}.prefix").strip("/")
    if not prefix or not _is_safe_path(prefix, root_relative=False):
        raise DocsConfigError(f"{label}.prefix must be a safe relative URL path prefix")
    priority = item["priority"]
    if isinstance(priority, bool) or not isinstance(priority, (int, float)) or not 0 <= priority <= 1:
        raise DocsConfigError(f"{label}.priority must be a number from 0 through 1")
    return prefix, float(priority)


def _absolute_url(value: Any, label: str, *, trailing_slash: bool = False) -> str:
    url = require_str(value, label)
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise DocsConfigError(f"{label} must be a valid absolute HTTP(S) URL") from exc
    unsafe = any(ord(char) <= 32 or ord(char) == 127 or char in {'"', "'", "<", ">", "\\"} for char in url)
    if (
        unsafe
        or parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or port == 0
        or parsed.query
        or parsed.fragment
    ):
        raise DocsConfigError(f"{label} must be an absolute HTTP(S) URL without a query or fragment")
    if trailing_slash and not url.endswith("/"):
        raise DocsConfigError(f"{label} must end with /")
    return url


def validate_absolute_url(value: Any, label: str, *, trailing_slash: bool = False) -> str:
    """Apply the settings URL policy to runtime overrides too."""
    return _absolute_url(value, label, trailing_slash=trailing_slash)


def google_search_site_target(public_url: str) -> str:
    """Return the host and path accepted by Google's ``site:`` operator."""
    parsed = urlsplit(public_url)
    return f"{parsed.netloc}{parsed.path.rstrip('/')}"


def _root_path(value: Any, label: str) -> str:
    path = require_str(value, label)
    if not _is_safe_path(path, root_relative=True):
        raise DocsConfigError(f"{label} must be a safe root-relative URL path")
    return path


def _feed_path(value: Any, label: str) -> str:
    path = _root_path(value, label)
    if not path.startswith("/blog/") or not path.endswith(".xml"):
        raise DocsConfigError(f"{label} must be an .xml path under /blog/")
    return path


def _pagefind_path(value: Any, label: str) -> str:
    path = _root_path(value, label)
    if path.count("/") < 2 or not path.endswith("/pagefind.js"):
        raise DocsConfigError(f"{label} must end with /pagefind.js inside an output subdirectory")
    directories = path.strip("/").split("/")[:-1]
    if any(not _PAGEFIND_DIRECTORY_SEGMENT_RE.fullmatch(segment) for segment in directories):
        raise DocsConfigError(f"{label} directory segments must contain only letters, digits, _ and -")
    return path


def validate_root_path(value: Any, label: str) -> str:
    """Apply the settings route policy to runtime path overrides too."""
    return _root_path(value, label)


def _git_branch(value: Any, label: str) -> str:
    branch = require_str(value, label)
    parts = branch.split("/")
    if (
        branch.startswith(("-", "/"))
        or branch.endswith(("/", "."))
        or "//" in branch
        or ".." in branch
        or "@{" in branch
        or branch == "@"
        or any(part.startswith(".") or part.endswith(".lock") for part in parts)
        or any(ord(char) <= 32 or ord(char) == 127 or char in "~^:?*[\\\"'<>#" for char in branch)
    ):
        raise DocsConfigError(f"{label} must be a safe Git branch name")
    return branch


def _is_safe_path(path: str, *, root_relative: bool) -> bool:
    if path.startswith("/") is not root_relative:
        return False
    if (
        "//" in path
        or "?" in path
        or "#" in path
        or "%" in path
        or ":" in path
        or "\\" in path
        or any(char.isspace() or char in {'"', "'", "<", ">"} for char in path)
    ):
        return False
    if any(ord(char) < 32 or ord(char) == 127 for char in path):
        return False
    return not any(part in {".", ".."} for part in path.split("/"))
