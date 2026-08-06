"""Deterministic filesystem orchestration for the Citry template formatter."""

from __future__ import annotations

import codecs
import os
import stat
import tempfile
import tokenize
from contextlib import suppress
from dataclasses import dataclass, field
from difflib import unified_diff
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from citry._embedded_provider import (
    BiomeEmbeddedProvider,
    EmbeddedProviderInvalidError,
    EmbeddedProviderUnavailableError,
)
from citry.analysis import (
    PythonComponentAssetKind,
    PythonComponentAssetRequest,
    PythonTemplateFormatError,
    discover_python_component_assets,
    format_python_component_assets,
    format_python_templates,
)
from citry.autodiscovery import _iter_py_files, _path_to_module
from citry_core.template_formatter import (
    EmbeddedFormatResult,
    EmbeddedLanguage,
    TemplateFormatError,
    finish_embedded_format,
    format_template,
    prepare_embedded_format,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


FormatMode = Literal["write", "check", "diff"]
EmbeddedMode = Literal["off", "available", "required"]
FormatFileStatus = Literal["formatted", "unchanged", "skipped", "errored"]
_TargetKind = Literal["python", "template", "javascript", "css"]
_EXPLICIT_TEMPLATE_SUFFIXES = frozenset({".html", ".citry", ".citry-html"})
_TARGET_KIND_BY_ASSET_KIND: dict[PythonComponentAssetKind, _TargetKind] = {
    PythonComponentAssetKind.TEMPLATE: "template",
    PythonComponentAssetKind.JS: "javascript",
    PythonComponentAssetKind.CSS: "css",
}


class FormatUsageError(ValueError):
    """An invalid command scope that must be rejected before formatting starts."""


@dataclass(frozen=True, slots=True)
class FormatFileResult:
    """The deterministic outcome for one normalized file path."""

    path: Path
    display_path: str
    status: FormatFileStatus
    message: str | None = None
    diff: str | None = None
    notices: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FormatReport:
    """All file outcomes for one batch invocation."""

    mode: FormatMode
    results: tuple[FormatFileResult, ...]

    def count(self, status: FormatFileStatus) -> int:
        return sum(result.status == status for result in self.results)

    @property
    def exit_code(self) -> int:
        if self.count("errored"):
            return 2
        if self.mode != "write" and self.count("formatted"):
            return 1
        return 0


@dataclass(frozen=True, slots=True)
class _SourceSnapshot:
    path: Path
    data: bytes
    metadata: os.stat_result


@dataclass(frozen=True, slots=True)
class _DirectoryGuard:
    root: Path
    root_metadata: os.stat_result
    target_metadata: os.stat_result
    target_data: bytes | None = None


@dataclass(slots=True)
class _Target:
    path: Path
    kind: _TargetKind
    dependencies: dict[Path, _SourceSnapshot] = field(default_factory=dict)
    directory_guards: dict[Path, _DirectoryGuard] = field(default_factory=dict)
    explicit: bool = False
    written_snapshot: _SourceSnapshot | None = None


@dataclass(slots=True)
class _Collection:
    targets: dict[Path, _Target]
    errors: dict[Path, list[str]]

    def add_target(
        self,
        path: Path,
        kind: _TargetKind,
        *,
        dependency: _SourceSnapshot | None = None,
        directory_guard: _DirectoryGuard | None = None,
        explicit: bool = False,
    ) -> None:
        if path in self.errors:
            return
        existing = self.targets.get(path)
        if existing is None:
            existing = _Target(path, kind)
            self.targets[path] = existing
        elif existing.kind != kind:
            self.targets.pop(path, None)
            self.add_error(path, "the same file was selected as both Python source and a standalone template")
            return
        if explicit:
            existing.explicit = True
            existing.dependencies.clear()
            existing.directory_guards.clear()
        elif not existing.explicit:
            if dependency is not None:
                previous = existing.dependencies.get(dependency.path)
                if previous is not None and not _same_source_snapshot(previous, dependency):
                    self.add_error(path, f"declaration source changed during discovery: {dependency.path}")
                    return
                existing.dependencies[dependency.path] = dependency
            if directory_guard is not None:
                existing.directory_guards[directory_guard.root] = directory_guard

    def add_error(self, path: Path, message: str) -> None:
        self.targets.pop(path, None)
        messages = self.errors.setdefault(path, [])
        if message not in messages:
            messages.append(message)


def format_paths(
    paths: Sequence[str | Path],
    *,
    mode: FormatMode,
    cwd: Path | None = None,
    embedded: EmbeddedMode = "available",
    javascript_provider: BiomeEmbeddedProvider | None = None,
    css_provider: BiomeEmbeddedProvider | None = None,
) -> FormatReport:
    """Format explicit files and conservatively discovered project templates."""
    if mode not in {"write", "check", "diff"}:
        msg = f"unsupported formatter mode: {mode!r}"
        raise ValueError(msg)
    if embedded not in {"off", "available", "required"}:
        msg = f"unsupported embedded formatter mode: {embedded!r}"
        raise ValueError(msg)
    root = (cwd or Path.cwd()).resolve()
    requested = tuple(Path(path) for path in paths) or (Path(),)
    _validate_explicit_extensions(requested, root)

    collection = _Collection({}, {})
    directory_roots = _outer_directory_roots(requested, root)
    processed_directory_roots: set[Path] = set()
    for requested_path in requested:
        lexical = _absolute_path(requested_path, root)
        if lexical.is_dir():
            directory_root = lexical.resolve()
            if directory_root not in directory_roots or directory_root in processed_directory_roots:
                continue
            processed_directory_roots.add(directory_root)
        _collect_explicit_target(requested_path, root, collection)

    results: list[FormatFileResult] = []
    for path in sorted(collection.targets.keys() | collection.errors.keys(), key=os.fspath):
        messages = collection.errors.get(path)
        if messages is not None:
            results.append(
                FormatFileResult(
                    path,
                    _display_path(path, root),
                    "errored",
                    "; ".join(sorted(messages)),
                ),
            )
            continue
        target = collection.targets[path]
        result = _format_target(
            target,
            mode=mode,
            cwd=root,
            embedded=embedded,
            javascript_provider=javascript_provider,
            css_provider=css_provider,
        )
        results.append(result)
        if target.written_snapshot is not None:
            _refresh_dependencies(collection, target.written_snapshot)
    return FormatReport(mode, tuple(results))


def _validate_explicit_extensions(paths: Sequence[Path], cwd: Path) -> None:
    for path in paths:
        if _absolute_path(path, cwd).is_dir():
            continue
        suffix = path.suffix
        if suffix == ".py" or suffix in _EXPLICIT_TEMPLATE_SUFFIXES or suffix in {".js", ".css"}:
            continue
        msg = (
            f"unsupported explicit file extension {suffix!r} for {os.fspath(path)!r}; "
            "name a .py, .html, .citry, .citry-html, .js, or .css file, or a directory"
        )
        raise FormatUsageError(msg)


def _outer_directory_roots(paths: Sequence[Path], cwd: Path) -> set[Path]:
    roots = {lexical.resolve() for path in paths if (lexical := _absolute_path(path, cwd)).is_dir()}
    return {
        candidate
        for candidate in roots
        if not any(
            other != candidate and _is_within(candidate, other) and _directory_is_discoverable_from(candidate, other)
            for other in roots
        )
    }


def _directory_is_discoverable_from(directory: Path, root: Path) -> bool:
    relative = directory.relative_to(root)
    return all(not part.startswith("_") and "." not in part for part in relative.parts)


def _collect_explicit_target(path: Path, cwd: Path, collection: _Collection) -> None:
    lexical = _absolute_path(path, cwd)
    try:
        metadata = lexical.lstat()
    except OSError as error:
        collection.add_error(lexical, f"cannot inspect explicit path: {error}")
        return

    if stat.S_ISLNK(metadata.st_mode):
        if lexical.is_dir():
            _collect_directory(lexical.resolve(), collection)
        else:
            collection.add_error(lexical, "explicit file is a symlink")
        return
    if stat.S_ISDIR(metadata.st_mode):
        _collect_directory(lexical.resolve(), collection)
        return
    if not stat.S_ISREG(metadata.st_mode):
        collection.add_error(lexical, "explicit path is not a regular file or directory")
        return

    resolved = lexical.resolve()
    if resolved.suffix == ".py":
        kind: _TargetKind = "python"
    elif resolved.suffix == ".js":
        kind = "javascript"
    elif resolved.suffix == ".css":
        kind = "css"
    else:
        kind = "template"
    collection.add_target(resolved, kind, explicit=True)


def _collect_directory(root: Path, collection: _Collection) -> None:
    try:
        _validate_directory_scan(root)
    except OSError as error:
        collection.add_error(root, f"directory cannot be scanned: {error}")
        return
    for path in _iter_py_files(root):
        lexical = _absolute_path(path, root)
        try:
            uses_symlink = _uses_symlink(root, lexical)
        except OSError as error:
            collection.add_error(lexical, f"directory-discovered Python file cannot be inspected: {error}")
            continue
        if uses_symlink:
            collection.add_error(lexical, "directory-discovered Python file resolves through a symlink")
            continue
        try:
            module_name = _path_to_module(lexical)
        except (OSError, ValueError) as error:
            collection.add_error(lexical, str(error))
            continue
        if module_name is None:
            continue

        try:
            resolved = lexical.resolve()
            directory_guard = _directory_guard(root, resolved)
        except OSError as error:
            collection.add_error(lexical, f"directory-discovered Python file cannot be guarded: {error}")
            continue
        collection.add_target(resolved, "python", directory_guard=directory_guard)
        try:
            source, _encoding, data, metadata = _read_source(resolved, "python")
        except (OSError, UnicodeError):
            continue
        try:
            exact_guard = _directory_guard(root, resolved, target_metadata=metadata, target_data=data)
        except OSError as error:
            collection.add_error(resolved, f"directory-discovered Python file cannot be guarded: {error}")
            continue
        collection.add_target(resolved, "python", directory_guard=exact_guard)
        try:
            discovery = discover_python_component_assets(source)
        except SyntaxError:
            continue
        snapshot = _SourceSnapshot(resolved, data, metadata)
        for notice in discovery.notices:
            collection.add_error(
                resolved,
                f"{notice.component_name}.{notice.kind.value}: {notice.message}",
            )
        for asset_file in discovery.files:
            _collect_component_asset_file(
                asset_file.path,
                component_name=asset_file.component_name,
                asset_kind=asset_file.kind,
                declaring_path=resolved,
                declaration_snapshot=snapshot,
                root=root,
                collection=collection,
            )


def _collect_component_asset_file(
    value: str,
    *,
    component_name: str,
    asset_kind: PythonComponentAssetKind,
    declaring_path: Path,
    declaration_snapshot: _SourceSnapshot,
    root: Path,
    collection: _Collection,
) -> None:
    field_name = f"{asset_kind.value}_file" if asset_kind is not PythonComponentAssetKind.TEMPLATE else "template_file"
    if "\0" in value:
        collection.add_error(declaring_path, f"{component_name}.{field_name} contains a null byte")
        return
    try:
        os.fsencode(value)
    except UnicodeError:
        collection.add_error(
            declaring_path,
            f"{component_name}.{field_name} cannot be represented as a filesystem path",
        )
        return
    lexical = _absolute_path(declaring_path.parent / value, declaring_path.parent)
    origin = f"{_display_path(declaring_path, root)}:{component_name}.{field_name}"
    if not _is_within(lexical, root):
        collection.add_error(lexical, f"{origin} escapes directory root")
        return
    try:
        uses_symlink = _uses_symlink(root, lexical)
        resolved = lexical.resolve(strict=False)
    except OSError as error:
        collection.add_error(lexical, f"{origin} cannot be inspected: {error}")
        return
    if uses_symlink:
        collection.add_error(lexical, f"{origin} resolves through a symlink")
        return

    if not _is_within(resolved, root):
        collection.add_error(lexical, f"{origin} escapes directory root after normalization")
        return
    try:
        metadata = resolved.lstat()
    except FileNotFoundError:
        collection.add_error(resolved, f"{origin} does not exist")
        return
    except OSError as error:
        collection.add_error(resolved, f"{origin} cannot be inspected: {error}")
        return
    if not stat.S_ISREG(metadata.st_mode):
        collection.add_error(resolved, f"{origin} is not a regular file")
        return
    try:
        directory_guard = _directory_guard(root, resolved, target_metadata=metadata)
    except OSError as error:
        collection.add_error(resolved, f"{origin} cannot be guarded: {error}")
        return
    collection.add_target(
        resolved,
        _TARGET_KIND_BY_ASSET_KIND[asset_kind],
        dependency=declaration_snapshot,
        directory_guard=directory_guard,
    )


def _format_target(
    target: _Target,
    *,
    mode: FormatMode,
    cwd: Path,
    embedded: EmbeddedMode,
    javascript_provider: BiomeEmbeddedProvider | None,
    css_provider: BiomeEmbeddedProvider | None,
) -> FormatFileResult:
    display = _display_path(target.path, cwd)
    try:
        _validate_directory_guards(target)
        _validate_dependencies(target)
        source, encoding, original, metadata = _read_source(target.path, target.kind)
        notices: tuple[str, ...] = ()
        if target.kind == "python":
            structural = format_python_templates(source)
            if embedded == "off":
                candidate = structural.source
            else:
                asset_result = format_python_component_assets(
                    structural.source,
                    provider=lambda request: _format_python_asset_request(
                        request,
                        source_path=target.path,
                        javascript_provider=javascript_provider,
                        css_provider=css_provider,
                    ),
                    require_providers=embedded == "required",
                )
                candidate = asset_result.source
                notices = tuple(
                    f"{notice.code}: {notice.component_name}.{notice.kind.value}: {notice.message}"
                    for notice in asset_result.notices
                )
            has_templates = bool(discover_python_component_assets(source).regions)
        elif target.kind == "template":
            candidate, notices = _format_template_with_embedded(
                source,
                source_path=target.path,
                embedded=embedded,
                javascript_provider=javascript_provider,
                css_provider=css_provider,
            )
            has_templates = True
        else:
            provider = javascript_provider if target.kind == "javascript" else css_provider
            candidate, notices = _format_standalone_embedded(
                source,
                source_path=target.path,
                language=target.kind,
                embedded=embedded,
                provider=provider,
            )
            has_templates = True
        _validate_directory_guards(target)
        _validate_dependencies(target)
    except PythonTemplateFormatError as error:
        return FormatFileResult(target.path, display, "errored", f"{error.code}: {error}")
    except TemplateFormatError as error:
        return FormatFileResult(target.path, display, "errored", f"{error.code}: {error}")
    except EmbeddedProviderInvalidError as error:
        return FormatFileResult(
            target.path,
            display,
            "errored",
            f"citry.format.provider-invalid: {error}",
        )
    except EmbeddedProviderUnavailableError as error:
        return FormatFileResult(
            target.path,
            display,
            "errored",
            f"citry.format.provider-unavailable: {error}",
        )
    except (OSError, SyntaxError, UnicodeError, ValueError) as error:
        return FormatFileResult(target.path, display, "errored", str(error))

    if candidate == source:
        status: FormatFileStatus = "unchanged" if has_templates else "skipped"
        return FormatFileResult(target.path, display, status, notices=notices)

    if mode == "write":
        try:
            candidate_bytes = candidate.encode(encoding)
            written_metadata = _atomic_replace(
                target.path,
                candidate_bytes,
                expected=original,
                metadata=metadata,
                dependencies=tuple(target.dependencies.values()),
                directory_guards=tuple(target.directory_guards.values()),
            )
        except (OSError, UnicodeError) as error:
            return FormatFileResult(target.path, display, "errored", f"atomic write failed: {error}")
        if target.kind == "python":
            target.written_snapshot = _SourceSnapshot(target.path, candidate_bytes, written_metadata)
        return FormatFileResult(target.path, display, "formatted", notices=notices)
    if mode == "diff":
        return FormatFileResult(
            target.path,
            display,
            "formatted",
            diff=_unified_diff(display, source, candidate),
            notices=notices,
        )
    return FormatFileResult(target.path, display, "formatted", notices=notices)


def _format_template_with_embedded(
    source: str,
    *,
    source_path: Path,
    embedded: EmbeddedMode,
    javascript_provider: BiomeEmbeddedProvider | None,
    css_provider: BiomeEmbeddedProvider | None,
) -> tuple[str, tuple[str, ...]]:
    structural = format_template(source)
    if embedded == "off":
        return structural, ()
    plan = prepare_embedded_format(structural)
    results: list[EmbeddedFormatResult] = []
    for request in plan.requests:
        provider = javascript_provider if request.language is EmbeddedLanguage.JAVASCRIPT else css_provider
        if provider is None:
            results.append(
                EmbeddedFormatResult.unavailable(
                    plan.id,
                    request.id,
                    f"no explicitly configured {request.language.value} provider",
                )
            )
            continue
        suffix = ".js" if request.language is EmbeddedLanguage.JAVASCRIPT else ".css"
        virtual_path = source_path.with_name(f".{source_path.name}.{request.id}{suffix}")
        formatted, provider_identity = provider.format_source_with_identity(
            request.virtual_source,
            source_path=virtual_path,
        )
        stable, stable_identity = provider.format_source_with_identity(formatted, source_path=virtual_path)
        if stable_identity != provider_identity:
            msg = f"{provider.identity} changed effective options during region {request.id}"
            raise EmbeddedProviderInvalidError(msg)
        if stable != formatted:
            msg = f"{provider_identity} is not byte-idempotent for region {request.id}"
            raise EmbeddedProviderInvalidError(msg)
        results.append(
            EmbeddedFormatResult.formatted(
                plan.id,
                request.id,
                formatted,
                provider_identity,
            )
        )
    outcome = finish_embedded_format(plan, results)
    notices = tuple(f"{notice.code}: {notice.message}" for notice in outcome.notices)
    required_notices = tuple(
        f"{notice.code}: {notice.message}"
        for notice in outcome.notices
        if notice.code
        in {
            "citry.format.provider-unavailable",
            "citry.format.embedded-interpolation-unsupported",
            "citry.format.embedded-language-unsupported",
        }
    )
    if embedded == "required" and required_notices:
        msg = "; ".join(required_notices)
        raise EmbeddedProviderUnavailableError(msg)
    return outcome.source, notices


def _format_standalone_embedded(
    source: str,
    *,
    source_path: Path,
    language: Literal["javascript", "css"],
    embedded: EmbeddedMode,
    provider: BiomeEmbeddedProvider | None,
) -> tuple[str, tuple[str, ...]]:
    if embedded == "off":
        return source, (f"citry.format.provider-unavailable: {language} formatting is disabled",)
    if provider is None:
        notice = f"citry.format.provider-unavailable: no explicitly configured {language} provider"
        if embedded == "required":
            raise EmbeddedProviderUnavailableError(notice)
        return source, (notice,)
    formatted, provider_identity = provider.format_source_with_identity(source, source_path=source_path)
    stable, stable_identity = provider.format_source_with_identity(formatted, source_path=source_path)
    if stable_identity != provider_identity:
        msg = f"{provider.identity} changed effective options while formatting {source_path}"
        raise EmbeddedProviderInvalidError(msg)
    if stable != formatted:
        msg = f"{provider_identity} is not byte-idempotent for {source_path}"
        raise EmbeddedProviderInvalidError(msg)
    return formatted, ()


def _format_python_asset_request(
    request: PythonComponentAssetRequest,
    *,
    source_path: Path,
    javascript_provider: BiomeEmbeddedProvider | None,
    css_provider: BiomeEmbeddedProvider | None,
) -> EmbeddedFormatResult:
    provider = javascript_provider if request.language is EmbeddedLanguage.JAVASCRIPT else css_provider
    if provider is None:
        return EmbeddedFormatResult.unavailable(
            request.plan_id,
            request.id,
            f"no explicitly configured {request.language.value} provider",
        )
    suffix = ".js" if request.language is EmbeddedLanguage.JAVASCRIPT else ".css"
    virtual_path = source_path.with_name(f".{source_path.name}.{request.id}{suffix}")
    formatted, provider_identity = provider.format_source_with_identity(
        request.virtual_source,
        source_path=virtual_path,
    )
    stable, stable_identity = provider.format_source_with_identity(formatted, source_path=virtual_path)
    if stable_identity != provider_identity:
        msg = f"{provider.identity} changed effective options during region {request.id}"
        raise EmbeddedProviderInvalidError(msg)
    if stable != formatted:
        msg = f"{provider_identity} is not byte-idempotent for region {request.id}"
        raise EmbeddedProviderInvalidError(msg)
    return EmbeddedFormatResult.formatted(
        request.plan_id,
        request.id,
        formatted,
        provider_identity,
    )


def _read_source(path: Path, kind: _TargetKind) -> tuple[str, str, bytes, os.stat_result]:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode):
        msg = "file became a symlink before it could be read"
        raise OSError(msg)
    if not stat.S_ISREG(metadata.st_mode):
        msg = "path is not a regular file"
        raise OSError(msg)
    data = path.read_bytes()
    source, encoding = _decode_source(data, kind)
    return source, encoding, data, metadata


def _decode_source(data: bytes, kind: _TargetKind) -> tuple[str, str]:
    if kind == "python":
        encoding, _lines = tokenize.detect_encoding(BytesIO(data).readline)
    else:
        encoding = "utf-8-sig" if data.startswith(codecs.BOM_UTF8) else "utf-8"
    source = data.decode(encoding)
    if source.encode(encoding) != data:
        msg = f"source bytes do not round-trip through declared encoding {encoding!r}"
        raise UnicodeError(msg)
    return source, encoding


def _atomic_replace(
    path: Path,
    candidate: bytes,
    *,
    expected: bytes,
    metadata: os.stat_result,
    dependencies: tuple[_SourceSnapshot, ...],
    directory_guards: tuple[_DirectoryGuard, ...],
) -> os.stat_result:
    for guard in directory_guards:
        _validate_directory_guard(path, guard)
    _validate_target_snapshot(path, expected=expected, metadata=metadata)

    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    descriptor_open = True
    try:
        with os.fdopen(descriptor, "wb") as stream:
            descriptor_open = False
            stream.write(candidate)
            stream.flush()
            temporary.chmod(stat.S_IMODE(metadata.st_mode))
            os.fsync(stream.fileno())
        for dependency in dependencies:
            _validate_snapshot(dependency)
        for guard in directory_guards:
            _validate_directory_guard(path, guard)
        _validate_target_snapshot(path, expected=expected, metadata=metadata)
        replacement_metadata = temporary.lstat()
        temporary.replace(path)
        return _validate_target_snapshot(path, expected=candidate, metadata=replacement_metadata)
    finally:
        if descriptor_open:
            os.close(descriptor)
        with suppress(FileNotFoundError):
            temporary.unlink()


def _validate_target_snapshot(path: Path, *, expected: bytes, metadata: os.stat_result) -> os.stat_result:
    current = path.lstat()
    same_file = (current.st_dev, current.st_ino) == (metadata.st_dev, metadata.st_ino)
    if stat.S_ISLNK(current.st_mode) or not stat.S_ISREG(current.st_mode) or not same_file:
        msg = "target identity changed while it was being formatted"
        raise OSError(msg)
    if path.read_bytes() != expected:
        msg = "target contents changed while it was being formatted"
        raise OSError(msg)
    return current


def _validate_dependencies(target: _Target) -> None:
    for dependency in sorted(target.dependencies.values(), key=lambda item: os.fspath(item.path)):
        _validate_snapshot(dependency)


def _directory_guard(
    root: Path,
    path: Path,
    *,
    target_metadata: os.stat_result | None = None,
    target_data: bytes | None = None,
) -> _DirectoryGuard:
    return _DirectoryGuard(
        root,
        root.lstat(),
        target_metadata or path.lstat(),
        target_data,
    )


def _validate_directory_guards(target: _Target) -> None:
    for guard in sorted(target.directory_guards.values(), key=lambda item: os.fspath(item.root)):
        _validate_directory_guard(target.path, guard)


def _validate_directory_guard(path: Path, guard: _DirectoryGuard) -> None:
    root_metadata = guard.root.lstat()
    same_root = (root_metadata.st_dev, root_metadata.st_ino) == (
        guard.root_metadata.st_dev,
        guard.root_metadata.st_ino,
    )
    if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode) or not same_root:
        msg = f"directory discovery root identity changed while formatting: {guard.root}"
        raise OSError(msg)
    if not _is_within(path, guard.root) or _uses_symlink(guard.root, path):
        msg = f"directory-discovered path no longer has a symlink-free route inside {guard.root}: {path}"
        raise OSError(msg)
    if path.resolve(strict=True) != path:
        msg = f"directory-discovered path resolves outside its original route: {path}"
        raise OSError(msg)
    target_metadata = path.lstat()
    same_target = (target_metadata.st_dev, target_metadata.st_ino) == (
        guard.target_metadata.st_dev,
        guard.target_metadata.st_ino,
    )
    if stat.S_ISLNK(target_metadata.st_mode) or not stat.S_ISREG(target_metadata.st_mode) or not same_target:
        msg = f"directory-discovered file identity changed while formatting: {path}"
        raise OSError(msg)
    if guard.target_data is not None and path.read_bytes() != guard.target_data:
        msg = f"directory-discovered Python file contents changed after discovery: {path}"
        raise OSError(msg)


def _validate_snapshot(snapshot: _SourceSnapshot) -> None:
    current = snapshot.path.lstat()
    same_file = (current.st_dev, current.st_ino) == (snapshot.metadata.st_dev, snapshot.metadata.st_ino)
    if stat.S_ISLNK(current.st_mode) or not stat.S_ISREG(current.st_mode) or not same_file:
        msg = f"declaring Python file identity changed during discovery: {snapshot.path}"
        raise OSError(msg)
    if snapshot.path.read_bytes() != snapshot.data:
        msg = f"declaring Python file contents changed during discovery: {snapshot.path}"
        raise OSError(msg)


def _refresh_dependencies(collection: _Collection, snapshot: _SourceSnapshot) -> None:
    try:
        source, _encoding = _decode_source(snapshot.data, "python")
        discovery = discover_python_component_assets(source)
    except (SyntaxError, UnicodeError):
        discovery = None
    authorized_targets: set[tuple[Path, _TargetKind]] = set()
    if discovery is not None:
        for asset_file in discovery.files:
            if "\0" in asset_file.path:
                continue
            try:
                os.fsencode(asset_file.path)
                authorized_targets.add(
                    (
                        _absolute_path(snapshot.path.parent / asset_file.path, snapshot.path.parent),
                        _TARGET_KIND_BY_ASSET_KIND[asset_file.kind],
                    )
                )
            except (OSError, UnicodeError, ValueError):
                continue
    for target in list(collection.targets.values()):
        if snapshot.path not in target.dependencies:
            continue
        if (target.path, target.kind) in authorized_targets:
            target.dependencies[snapshot.path] = snapshot
            continue
        target.dependencies.pop(snapshot.path)
        if not target.dependencies and not target.explicit:
            field_name = {
                "template": "template_file",
                "javascript": "js_file",
                "css": "css_file",
            }.get(target.kind, target.kind)
            collection.add_error(
                target.path,
                f"written Python source no longer authorizes this {field_name} target: {snapshot.path}",
            )


def _same_source_snapshot(left: _SourceSnapshot, right: _SourceSnapshot) -> bool:
    return (
        left.path == right.path
        and left.data == right.data
        and (left.metadata.st_dev, left.metadata.st_ino) == (right.metadata.st_dev, right.metadata.st_ino)
    )


def _unified_diff(display_path: str, source: str, candidate: str) -> str:
    lines = unified_diff(
        source.splitlines(keepends=True),
        candidate.splitlines(keepends=True),
        fromfile=display_path,
        tofile=display_path,
        lineterm="\n",
    )
    output: list[str] = []
    for line in lines:
        has_line_ending = line.endswith(("\n", "\r"))
        if line.endswith("\r\n"):
            printable = line[:-2]
        elif has_line_ending:
            printable = line[:-1]
        else:
            printable = line
        output.append(printable + "\n")
        if not has_line_ending:
            output.append("\\ No newline at end of file\n")
    return "".join(output)


def _absolute_path(path: Path, base: Path) -> Path:
    candidate = path if path.is_absolute() else base / path
    return Path(os.path.normpath(candidate.absolute()))


def _uses_symlink(root: Path, path: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    current = root
    for part in relative.parts:
        current /= part
        try:
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                return True
            if current != path and stat.S_ISDIR(metadata.st_mode) and stat.S_IMODE(metadata.st_mode) & 0o111 == 0:
                msg = f"path directory is not searchable: {current}"
                raise PermissionError(msg)
        except FileNotFoundError:
            return False
    return False


def _validate_directory_scan(root: Path) -> None:
    pending = [root]
    while pending:
        directory = pending.pop()
        metadata = directory.lstat()
        mode = stat.S_IMODE(metadata.st_mode)
        if not stat.S_ISDIR(metadata.st_mode):
            msg = f"scan path is not a directory: {directory}"
            raise OSError(msg)
        if mode & 0o444 == 0 or mode & 0o111 == 0:
            msg = f"scan directory is not readable and searchable: {directory}"
            raise PermissionError(msg)
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.name.startswith("_") or "." in entry.name:
                    continue
                if entry.is_dir(follow_symlinks=False):
                    pending.append(Path(entry.path))


def _is_within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _display_path(path: Path, cwd: Path) -> str:
    try:
        return os.fspath(path.relative_to(cwd)) or "."
    except ValueError:
        return os.fspath(path)


__all__ = [
    "EmbeddedMode",
    "FormatFileResult",
    "FormatMode",
    "FormatReport",
    "FormatUsageError",
    "format_paths",
]
