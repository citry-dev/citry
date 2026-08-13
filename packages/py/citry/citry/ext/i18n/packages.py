"""Load standalone i18n resource packages through ``importlib.resources``."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING

import tomllib

from citry_core.i18n import CatalogCompiler, canonicalize_locale

if TYPE_CHECKING:
    from importlib.resources.abc import Traversable
    from typing import Literal

    from .formats import FormatRegistry

_OWNER_RE = re.compile(r"[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?\Z")


@dataclass(frozen=True, slots=True)
class CatalogSource:
    """One standalone FTL source unit with its stable topology identity."""

    import_package: str
    owner: str
    source_locale: str
    locale: str
    path: str
    content: str
    layer: str
    precedence: int

    @property
    def digest(self) -> str:
        return sha256(self.content.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class LoadedCatalogPackage:
    """Validated descriptor and every deterministic locale source it names."""

    import_package: str
    owner: str
    source_locale: str
    sources: tuple[CatalogSource, ...]
    manifest_revision: str
    link_artifact: str | None = None
    formats: FormatRegistry | None = None


def load_catalog_packages(
    names: tuple[str, ...],
    *,
    mode: Literal["development", "production"],
) -> tuple[LoadedCatalogPackage, ...]:
    """Load configured packages from lowest to highest precedence."""
    loaded = tuple(_load_catalog_package(name, precedence=index, mode=mode) for index, name in enumerate(names))
    owners: dict[str, str] = {}
    for package in loaded:
        previous = owners.setdefault(package.owner, package.import_package)
        if previous != package.import_package:
            raise ValueError(
                f"i18n catalog packages {previous!r} and {package.import_package!r} "
                f"both claim stable owner {package.owner!r}."
            )
    return loaded


def _load_catalog_package(
    name: str,
    *,
    precedence: int,
    mode: Literal["development", "production"],
    validate_manifest: bool = True,
) -> LoadedCatalogPackage:
    try:
        root = files(name)
    except (ImportError, ModuleNotFoundError) as error:
        raise ValueError(f"Could not import configured i18n catalog package {name!r}: {error}") from error

    descriptor_path = root.joinpath("citry-i18n.toml")
    if not descriptor_path.is_file():
        raise ValueError(f"i18n catalog package {name!r} has no citry-i18n.toml descriptor.")
    try:
        descriptor = tomllib.loads(descriptor_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"Could not read {name!r}/citry-i18n.toml: {error}") from error
    if set(descriptor) != {"schema_version", "owner", "source_locale"}:
        raise ValueError(f"{name!r}/citry-i18n.toml must contain exactly schema_version, owner, and source_locale.")
    if descriptor["schema_version"] != 1:
        raise ValueError(f"{name!r}/citry-i18n.toml requires schema_version = 1.")
    owner = descriptor["owner"]
    if type(owner) is not str or _OWNER_RE.fullmatch(owner) is None:
        raise ValueError(f"{name!r}/citry-i18n.toml has invalid stable owner {owner!r}.")
    source_locale = _canonical_exact_locale(descriptor["source_locale"], source=f"{name!r} source_locale")
    formats = _load_package_formats(name=name, owner=owner, root=root)

    manifest_path = root.joinpath("_compiled", "manifest.json")
    if mode == "production":
        if not manifest_path.is_file():
            raise ValueError(
                f"Production i18n catalog package {name!r} has no _compiled/manifest.json. "
                "Run 'citry ext run i18n compile' while building the package."
            )
        link_artifact, manifest_revision = _validate_production_artifacts(
            name=name,
            owner=owner,
            source_locale=source_locale,
            path=manifest_path,
            artifacts_root=root.joinpath("_compiled"),
            formats_path=root.joinpath("formats.json"),
            formats=formats,
        )
        return LoadedCatalogPackage(
            import_package=name,
            owner=owner,
            source_locale=source_locale,
            sources=(),
            manifest_revision=manifest_revision,
            link_artifact=link_artifact,
            formats=formats,
        )

    locales_root = root.joinpath("locales")
    if not locales_root.is_dir():
        raise ValueError(f"i18n catalog package {name!r} has no locales directory.")
    sources: list[CatalogSource] = []
    canonical_directories: dict[str, str] = {}
    for locale_dir in sorted(locales_root.iterdir(), key=lambda item: item.name):
        if not locale_dir.is_dir():
            raise ValueError(f"Unexpected file in {name!r}/locales: {locale_dir.name!r}.")
        locale = _canonical_exact_locale(locale_dir.name, source=f"{name!r} locale directory")
        previous = canonical_directories.setdefault(locale, locale_dir.name)
        if previous != locale_dir.name:
            raise ValueError(
                f"i18n catalog package {name!r} has canonically duplicate locale directories "
                f"{previous!r} and {locale_dir.name!r}."
            )
        for resource, relative in _walk_ftl(locale_dir):
            path = f"locales/{locale_dir.name}/{relative}"
            try:
                content = resource.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                raise ValueError(f"Could not read {name!r}/{path}: {error}") from error
            sources.append(
                CatalogSource(
                    import_package=name,
                    owner=owner,
                    source_locale=source_locale,
                    locale=locale,
                    path=f"{name}:{path}",
                    content=content,
                    layer=f"package:{precedence}:{owner}",
                    precedence=precedence,
                )
            )
    sources.sort(key=lambda source: source.path)
    if not any(source.locale == source_locale for source in sources):
        raise ValueError(f"i18n catalog package {name!r} has no FTL source for its source locale {source_locale!r}.")

    manifest_revision = "development"
    if manifest_path.is_file() and validate_manifest:
        manifest_revision = _validate_manifest(
            name=name,
            owner=owner,
            source_locale=source_locale,
            sources=tuple(sources),
            path=manifest_path,
            artifacts_root=root.joinpath("_compiled"),
            formats_path=root.joinpath("formats.json"),
            formats=formats,
        )
    return LoadedCatalogPackage(
        import_package=name,
        owner=owner,
        source_locale=source_locale,
        sources=tuple(sources),
        manifest_revision=manifest_revision,
        formats=formats,
    )


def compile_catalog_package(name: str) -> tuple[Path, Path, Path]:
    """Check one source-tree catalog package and write its deterministic server artifacts."""
    package = _load_catalog_package(
        name,
        precedence=0,
        mode="development",
        validate_manifest=False,
    )
    root = Path(str(files(name)))
    if not root.is_dir():
        raise ValueError(
            f"i18n catalog package {name!r} is not a writable source-tree package. "
            "Run compile before building its wheel or zip archive."
        )
    request = _package_compile_request(
        owner=package.owner,
        source_locale=package.source_locale,
        sources=package.sources,
        formats=package.formats,
    )
    compiler = CatalogCompiler()
    request_json = json.dumps(request, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    compiled = compiler.compile(request_json)
    artifact_text = compiled.artifact_json()
    link_text = compiler.compile_link_unit(request_json)
    compiled_root = root / "_compiled"
    compiled_root.mkdir(exist_ok=True)
    server_path = compiled_root / "server.json"
    server_path.write_text(artifact_text + "\n", encoding="utf-8")
    link_path = compiled_root / "link.json"
    link_path.write_text(link_text + "\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "owner": package.owner,
        "source_locale": package.source_locale,
        "sources": [{"path": source.path.split(":", 1)[1], "sha256": source.digest} for source in package.sources],
        "artifacts": {
            "server.json": {
                "sha256": sha256((artifact_text + "\n").encode()).hexdigest(),
            },
            "link.json": {
                "sha256": sha256((link_text + "\n").encode()).hexdigest(),
            },
        },
    }
    formats_path = root / "formats.json"
    if formats_path.is_file():
        manifest["formats"] = {
            "path": "formats.json",
            "sha256": sha256(formats_path.read_bytes()).hexdigest(),
        }
    manifest_path = compiled_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _load_catalog_package(name, precedence=0, mode="production")
    return manifest_path, server_path, link_path


def _package_compile_request(
    *,
    owner: str,
    source_locale: str,
    sources: tuple[CatalogSource, ...],
    formats: FormatRegistry | None,
) -> dict[str, object]:
    """Build the one canonical compiler request used to write and verify a package artifact."""
    active_locales = sorted({source.locale for source in sources} | {source_locale})
    return {
        "schema_version": 1,
        "active_locales": active_locales,
        "fallbacks": {},
        "packages": [
            {
                "name": owner,
                "source_locale": source_locale,
                "exports": [],
            }
        ],
        "catalogs": [
            {
                "path": source.path,
                "package": source.owner,
                "layer": source.layer,
                "precedence": source.precedence,
                "locale": source.locale,
                "source": source.content,
            }
            for source in sources
        ],
        "formats": {} if formats is None else formats.to_wire(),
    }


def _walk_ftl(root: Traversable, prefix: str = "") -> list[tuple[Traversable, str]]:
    result: list[tuple[Traversable, str]] = []
    for item in sorted(root.iterdir(), key=lambda child: child.name):
        relative = f"{prefix}/{item.name}" if prefix else item.name
        if item.is_dir():
            result.extend(_walk_ftl(item, relative))
        elif item.is_file() and item.name.endswith(".ftl"):
            result.append((item, relative))
    return result


def _load_package_formats(*, name: str, owner: str, root: Traversable) -> FormatRegistry | None:
    path = root.joinpath("formats.json")
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read {name!r}/formats.json: {error}") from error
    from .formats import format_registry_from_wire  # noqa: PLC0415

    registry = format_registry_from_wire(payload, source=f"{name!r}/formats.json")
    prefix = f"{owner}-"
    for kind in registry.to_wire():
        invalid = sorted(profile for profile in getattr(registry, kind) if not profile.startswith(prefix))
        if invalid:
            raise ValueError(
                f"{name!r}/formats.json {kind} profile names must start with the package namespace "
                f"{prefix!r}; got {invalid[0]!r}."
            )
    return registry


def _canonical_exact_locale(value: object, *, source: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{source} must be an exact non-empty locale string; got {value!r}.")
    try:
        canonical = canonicalize_locale(value)
    except ValueError as error:
        raise ValueError(f"{source} is invalid: {error}") from error
    if canonical != value:
        raise ValueError(f"{source} must use canonical spelling {canonical!r}, got {value!r}.")
    return canonical


def _validate_manifest(
    *,
    name: str,
    owner: str,
    source_locale: str,
    sources: tuple[CatalogSource, ...],
    path: Traversable,
    artifacts_root: Traversable,
    formats_path: Traversable,
    formats: FormatRegistry | None,
) -> str:
    try:
        raw = path.read_text(encoding="utf-8")
        manifest = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read {name!r}/_compiled/manifest.json: {error}") from error
    if type(manifest) is not dict:
        raise ValueError(f"{name!r}/_compiled/manifest.json must contain one JSON object.")
    expected_keys = {"schema_version", "owner", "source_locale", "sources", "artifacts"}
    if formats_path.is_file():
        expected_keys.add("formats")
    if set(manifest) != expected_keys:
        raise ValueError(f"{name!r}/_compiled/manifest.json must contain exactly {', '.join(sorted(expected_keys))}.")
    if manifest["schema_version"] != 1 or manifest["owner"] != owner or manifest["source_locale"] != source_locale:
        raise ValueError(f"{name!r}/_compiled/manifest.json does not match its authored descriptor.")
    expected_sources = [{"path": source.path.split(":", 1)[1], "sha256": source.digest} for source in sources]
    if manifest["sources"] != expected_sources:
        raise ValueError(f"{name!r}/_compiled/manifest.json does not match its installed FTL sources.")
    if manifest["artifacts"] != {
        artifact: {
            "sha256": _resource_sha256(
                artifacts_root.joinpath(artifact),
                source=f"{name!r} {artifact} artifact",
            )
        }
        for artifact in ("link.json", "server.json")
    }:
        raise ValueError(f"{name!r}/_compiled/manifest.json does not match its installed server artifact.")
    if "formats" in expected_keys and manifest["formats"] != {
        "path": "formats.json",
        "sha256": _resource_sha256(formats_path, source=f"{name!r} formats.json"),
    }:
        raise ValueError(f"{name!r}/_compiled/manifest.json does not match its installed format profiles.")
    try:
        server_payload = json.loads(artifacts_root.joinpath("server.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read {name!r}/_compiled/server.json: {error}") from error
    if type(server_payload) is not dict or server_payload.get("schema_version") != 1:
        raise ValueError(f"{name!r}/_compiled/server.json has an unsupported artifact schema.")
    try:
        compiler = CatalogCompiler()
        request_json = json.dumps(
            _package_compile_request(owner=owner, source_locale=source_locale, sources=sources, formats=formats),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        expected_server_payload = json.loads(compiler.compile(request_json).artifact_json())
        expected_link_payload = json.loads(compiler.compile_link_unit(request_json))
        installed_link_payload = json.loads(artifacts_root.joinpath("link.json").read_text(encoding="utf-8"))
    except Exception as error:
        raise ValueError(f"Could not verify {name!r}/_compiled/server.json: {error}") from error
    if server_payload != expected_server_payload:
        raise ValueError(
            f"{name!r}/_compiled/server.json does not match the installed FTL sources and package descriptor."
        )
    if installed_link_payload != expected_link_payload:
        raise ValueError(f"{name!r}/_compiled/link.json does not match the installed FTL sources and descriptor.")
    return sha256(raw.encode()).hexdigest()


def _validate_production_artifacts(
    *,
    name: str,
    owner: str,
    source_locale: str,
    path: Traversable,
    artifacts_root: Traversable,
    formats_path: Traversable,
    formats: FormatRegistry | None,
) -> tuple[str, str]:
    """Validate generated package inputs without opening an authored FTL file."""
    try:
        raw = path.read_text(encoding="utf-8")
        manifest = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read {name!r}/_compiled/manifest.json: {error}") from error
    expected_keys = {"schema_version", "owner", "source_locale", "sources", "artifacts"}
    if formats_path.is_file():
        expected_keys.add("formats")
    if type(manifest) is not dict or set(manifest) != expected_keys:
        raise ValueError(f"{name!r}/_compiled/manifest.json has an unsupported manifest shape.")
    if manifest["schema_version"] != 1 or manifest["owner"] != owner or manifest["source_locale"] != source_locale:
        raise ValueError(f"{name!r}/_compiled/manifest.json does not match its authored descriptor.")
    expected_artifacts = {
        artifact: {
            "sha256": _resource_sha256(
                artifacts_root.joinpath(artifact),
                source=f"{name!r} {artifact} artifact",
            )
        }
        for artifact in ("link.json", "server.json")
    }
    if manifest["artifacts"] != expected_artifacts:
        raise ValueError(f"{name!r}/_compiled/manifest.json does not match its installed artifacts.")
    if "formats" in expected_keys and manifest["formats"] != {
        "path": "formats.json",
        "sha256": _resource_sha256(formats_path, source=f"{name!r} formats.json"),
    }:
        raise ValueError(f"{name!r}/_compiled/manifest.json does not match its installed format profiles.")
    try:
        link_text = artifacts_root.joinpath("link.json").read_text(encoding="utf-8").strip()
        link_payload = json.loads(link_text)
        server_payload = json.loads(artifacts_root.joinpath("server.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read {name!r} compiled i18n artifacts: {error}") from error
    if type(link_payload) is not dict or type(link_payload.get("catalogs")) is not list:
        raise ValueError(f"{name!r}/_compiled/link.json has an unsupported artifact shape.")
    packages = link_payload.get("packages")
    if packages != [{"name": owner, "source_locale": source_locale, "exports": []}]:
        raise ValueError(f"{name!r}/_compiled/link.json does not match its authored descriptor.")
    try:
        linked_sources = []
        linked_locales: set[str] = set()
        for catalog in link_payload["catalogs"]:
            if type(catalog) is not dict:
                raise TypeError("catalog entries must be objects")
            path_value = catalog["path"]
            digest_value = catalog["source_digest"]
            locale_value = catalog["locale"]
            if type(path_value) is not str or ":" not in path_value:
                raise TypeError("catalog paths must contain their package prefix")
            if type(digest_value) is not str or type(locale_value) is not str:
                raise TypeError("catalog digests and locales must be strings")
            linked_sources.append(
                {
                    "path": path_value.split(":", 1)[1],
                    "sha256": digest_value,
                }
            )
            linked_locales.add(locale_value)
        linked_sources.sort(key=lambda item: item["path"])
    except (KeyError, TypeError) as error:
        raise ValueError(f"{name!r}/_compiled/link.json has unsupported catalog metadata: {error}") from error
    if manifest["sources"] != linked_sources:
        raise ValueError(f"{name!r}/_compiled/link.json does not match its source manifest.")
    active_locales = sorted(linked_locales | {source_locale})
    try:
        rebuilt = CatalogCompiler().compile(
            json.dumps(
                {
                    "schema_version": 1,
                    "active_locales": active_locales,
                    "fallbacks": {},
                    "packages": [],
                    "catalogs": [],
                    "link_units": [
                        {
                            "artifact_json": link_text,
                            "layer": f"package:0:{owner}",
                            "precedence": 0,
                        }
                    ],
                    "formats": {} if formats is None else formats.to_wire(),
                },
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        rebuilt_payload = json.loads(rebuilt.artifact_json())
    except Exception as error:
        raise ValueError(f"Could not validate {name!r}/_compiled/link.json: {error}") from error
    for payload in (server_payload, rebuilt_payload):
        if type(payload) is dict:
            payload.pop("stats", None)
    if server_payload != rebuilt_payload:
        raise ValueError(f"{name!r}/_compiled/server.json does not match its checked link artifact.")
    return link_text, sha256(raw.encode()).hexdigest()


def _resource_sha256(path: Traversable, *, source: str) -> str:
    if not path.is_file():
        raise ValueError(f"{source} is missing.")
    try:
        return sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise ValueError(f"Could not read {source}: {error}") from error
