"""Explicit, non-shell batch providers for component JavaScript and CSS."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import suppress
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Literal, NoReturn

EmbeddedProviderLanguage = Literal["javascript", "css"]

_PROVIDER_TIMEOUT_SECONDS = 15.0
_PROVIDER_OUTPUT_LIMIT = 8 * 1024 * 1024
_PROVIDER_READ_SIZE = 64 * 1024
_PROVIDER_THREAD_JOIN_SECONDS = 1.0
_PROVIDER_DIAGNOSTIC_LIMIT = 4096
_BIOME_VERSION = re.compile(r"(?:Version:\s*)?(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)")
_BIOME_CONFIG_NAMES = ("biome.json", "biome.jsonc")
_BIOME_FIXED_ARGUMENTS = (
    "--write",
    "--colors=off",
    "--line-ending=lf",
    "--use-editorconfig=false",
    "--vcs-enabled=false",
)
_WINDOWS_PROVIDER_LAUNCHER = (
    "import os, subprocess, sys; "
    "os.read(0, 1); "
    "child = subprocess.Popen(sys.argv[1:], stdin=sys.stdin.buffer, "
    "stdout=sys.stdout.buffer, stderr=sys.stderr.buffer); "
    "raise SystemExit(child.wait())"
)


class EmbeddedProviderConfigError(ValueError):
    """An invalid provider option rejected before any formatter write."""


class EmbeddedProviderUnavailableError(RuntimeError):
    """An explicitly selected provider executable is no longer available."""


class EmbeddedProviderInvalidError(RuntimeError):
    """A selected provider failed or returned invalid process output."""


@dataclass(frozen=True, slots=True)
class _FileSnapshot:
    device: int
    inode: int
    mode: int
    size: int
    modified_ns: int


@dataclass(frozen=True, slots=True)
class _ProviderInvocation:
    arguments: tuple[str, ...]
    cwd: Path
    source_directory: Path
    identity: str
    config_path: Path | None
    config_snapshot: _FileSnapshot | None
    config_digest: str | None
    _private_config_owner: tempfile.TemporaryDirectory[str] | None


@dataclass(frozen=True, slots=True)
class BiomeEmbeddedProvider:
    """One explicitly authorized Biome executable for one language."""

    language: EmbeddedProviderLanguage
    executable: Path
    version: str
    _executable_snapshot: _FileSnapshot
    _executable_digest: str
    _private_executable: Path
    _private_executable_owner: tempfile.TemporaryDirectory[str]
    _private_executable_stream: IO[bytes]
    _execution_lock: threading.Lock

    @property
    def identity(self) -> str:
        """Return the provider version and its per-target option policy."""
        return f"biome@{self.version}+effective-options:per-target"

    @classmethod
    def from_spec(
        cls,
        value: str,
        *,
        language: EmbeddedProviderLanguage,
    ) -> BiomeEmbeddedProvider:
        """Parse ``biome:/absolute/path`` and probe the selected executable."""
        if type(value) is not str:
            msg = "embedded provider specification must be a string"
            raise TypeError(msg)
        adapter, separator, raw_path = value.partition(":")
        if not separator or adapter != "biome" or not raw_path:
            msg = f"invalid {language} provider {value!r}; expected biome:/absolute/path/to/biome"
            raise EmbeddedProviderConfigError(msg)
        lexical = Path(raw_path)
        if not lexical.is_absolute():
            msg = f"{language} provider executable must be an absolute path: {raw_path!r}"
            raise EmbeddedProviderConfigError(msg)
        if "\0" in raw_path:
            msg = f"{language} provider executable contains a null byte"
            raise EmbeddedProviderConfigError(msg)
        try:
            executable = lexical.resolve(strict=True)
        except OSError as error:
            msg = f"{language} provider executable is unavailable: {error}"
            raise EmbeddedProviderConfigError(msg) from error
        if not executable.is_file():
            msg = f"{language} provider executable is not a regular file: {executable}"
            raise EmbeddedProviderConfigError(msg)
        snapshot, executable_digest, executable_bytes = _read_executable(
            executable,
            language=language,
            unavailable_is_config=True,
        )
        _validate_self_contained_executable(
            executable,
            executable_bytes,
            language=language,
        )
        if not os.access(executable, os.X_OK):
            msg = f"{language} provider executable is not executable: {executable}"
            raise EmbeddedProviderConfigError(msg)
        private_owner, private_executable = _private_file_copy(
            executable_bytes,
            name=executable.name,
            parent=_private_executable_root(language),
            executable=True,
            language=language,
            unavailable_is_config=True,
        )
        private_stream = _lock_private_executable(
            private_executable,
            expected_digest=executable_digest,
            language=language,
        )
        try:
            raw_version = _run_provider(
                private_executable,
                ("--version",),
                input_text=None,
                cwd=executable.parent,
                language=language,
                unavailable_is_config=True,
                environment=_provider_environment(),
                executable_descriptor=private_stream.fileno(),
            ).strip()
            after, after_digest, _data = _read_executable(
                executable,
                language=language,
                unavailable_is_config=True,
            )
            if after != snapshot or after_digest != executable_digest:
                msg = f"{language} provider executable changed during its version probe"
                raise EmbeddedProviderConfigError(msg)
            _validate_private_copy(
                private_stream,
                expected_digest=executable_digest,
                language=language,
                unavailable_is_config=True,
            )
        except BaseException:
            private_stream.close()
            private_owner.cleanup()
            raise
        match = _BIOME_VERSION.fullmatch(raw_version)
        if match is None:
            private_stream.close()
            private_owner.cleanup()
            msg = f"{language} provider returned an invalid Biome version string"
            raise EmbeddedProviderConfigError(msg)
        return cls(
            language=language,
            executable=executable,
            version=match.group(1),
            _executable_snapshot=after,
            _executable_digest=executable_digest,
            _private_executable=private_executable,
            _private_executable_owner=private_owner,
            _private_executable_stream=private_stream,
            _execution_lock=threading.Lock(),
        )

    def format_source(self, source: str, *, source_path: Path) -> str:
        """Format one standalone source over stdin without provider writes."""
        formatted, _identity = self.format_source_with_identity(source, source_path=source_path)
        return formatted

    def format_source_with_identity(self, source: str, *, source_path: Path) -> tuple[str, str]:
        """Format source and report the exact executable/configuration fingerprint."""
        if type(source) is not str:
            msg = "provider source must be a str"
            raise TypeError(msg)
        if not source_path.is_absolute():
            msg = "provider source_path must be absolute"
            raise ValueError(msg)
        with self._execution_lock:
            self._validate_executable()
            invocation = self._invocation(source_path)
            try:
                formatted = _run_provider(
                    self._private_executable,
                    invocation.arguments,
                    input_text=source,
                    cwd=invocation.cwd,
                    language=self.language,
                    unavailable_is_config=False,
                    environment=_provider_environment(),
                    executable_descriptor=self._private_executable_stream.fileno(),
                )
                self._validate_executable()
                self._validate_config(invocation)
                return formatted, invocation.identity
            finally:
                if invocation._private_config_owner is not None:
                    invocation._private_config_owner.cleanup()

    def _validate_executable(self) -> None:
        current, digest, _data = _read_executable(
            self.executable,
            language=self.language,
            unavailable_is_config=False,
        )
        if current != self._executable_snapshot or digest != self._executable_digest:
            msg = f"{self.language} provider executable changed after its version probe"
            raise EmbeddedProviderUnavailableError(msg)
        _validate_private_copy(
            self._private_executable_stream,
            expected_digest=self._executable_digest,
            language=self.language,
            unavailable_is_config=False,
        )

    def _invocation(self, source_path: Path) -> _ProviderInvocation:
        suffix = ".js" if self.language == "javascript" else ".css"
        try:
            cwd = source_path.parent.resolve(strict=True)
        except OSError as error:
            msg = f"{self.language} provider source directory is unavailable: {error}"
            raise EmbeddedProviderUnavailableError(msg) from error
        virtual_name = source_path.name if source_path.suffix.lower() == suffix else f"{source_path.name}{suffix}"
        virtual_path = cwd / virtual_name
        config_path = _find_biome_config(cwd, language=self.language)
        config_snapshot: _FileSnapshot | None = None
        config_digest: str | None = None
        private_config_owner: tempfile.TemporaryDirectory[str] | None = None
        actual_config_argument: tuple[str, ...]
        logical_config_argument: tuple[str, ...] = ()
        config_bytes = b"{}"
        if config_path is not None:
            config_snapshot, config_digest, config_bytes = _biome_config_snapshot(
                config_path,
                language=self.language,
            )
            logical_config_argument = (f"--config-path={config_path}",)
        private_config_owner, private_config = _private_file_copy(
            config_bytes,
            name=config_path.name if config_path is not None else "biome.json",
            parent=None,
            executable=False,
            language=self.language,
            unavailable_is_config=False,
        )
        private_root = Path(private_config_owner.name)
        relative_virtual_path = (
            virtual_path.relative_to(config_path.parent) if config_path is not None else Path(virtual_name)
        )
        actual_virtual_path = private_root / relative_virtual_path
        actual_virtual_path.parent.mkdir(parents=True, exist_ok=True)
        actual_cwd = actual_virtual_path.parent
        actual_config_argument = (f"--config-path={private_config}",)
        arguments = (
            "format",
            *_BIOME_FIXED_ARGUMENTS,
            *actual_config_argument,
            f"--stdin-file-path={actual_virtual_path}",
        )
        logical_arguments = (
            "format",
            *_BIOME_FIXED_ARGUMENTS,
            *logical_config_argument,
            f"--stdin-file-path={virtual_path}",
        )
        digest = hashlib.sha256()
        digest.update(b"citry-biome-invocation-v1\0")
        digest.update(self.version.encode())
        digest.update(b"\0")
        digest.update(os.fspath(self.executable).encode())
        digest.update(b"\0")
        digest.update(self._executable_digest.encode())
        digest.update(b"\0")
        digest.update(os.fspath(virtual_path).encode())
        digest.update(b"\0")
        digest.update("\0".join(logical_arguments).encode())
        digest.update(b"\0")
        if config_path is not None and config_digest is not None:
            digest.update(os.fspath(config_path).encode())
            digest.update(b"\0")
            digest.update(config_digest.encode())
        else:
            digest.update(b"no-ambient-config\0")
            digest.update(hashlib.sha256(config_bytes).hexdigest().encode())
        identity = f"biome@{self.version}+sha256:{digest.hexdigest()}"
        return _ProviderInvocation(
            arguments=arguments,
            cwd=actual_cwd,
            source_directory=cwd,
            identity=identity,
            config_path=config_path,
            config_snapshot=config_snapshot,
            config_digest=config_digest,
            _private_config_owner=private_config_owner,
        )

    def _validate_config(self, invocation: _ProviderInvocation) -> None:
        if invocation.config_path is None:
            if _find_biome_config(invocation.source_directory, language=self.language) is not None:
                msg = f"{self.language} provider configuration appeared during formatting"
                raise EmbeddedProviderInvalidError(msg)
            return
        snapshot, digest, _data = _biome_config_snapshot(
            invocation.config_path,
            language=self.language,
        )
        if snapshot != invocation.config_snapshot or digest != invocation.config_digest:
            msg = f"{self.language} provider configuration changed during formatting"
            raise EmbeddedProviderInvalidError(msg)


def _read_executable(
    path: Path,
    *,
    language: EmbeddedProviderLanguage,
    unavailable_is_config: bool,
) -> tuple[_FileSnapshot, str, bytes]:
    try:
        snapshot, data = _read_stable_file(path)
    except OSError as error:
        msg = f"{language} provider executable is unavailable: {error}"
        if unavailable_is_config:
            raise EmbeddedProviderConfigError(msg) from error
        raise EmbeddedProviderUnavailableError(msg) from error
    if not stat.S_ISREG(snapshot.mode):
        msg = f"{language} provider executable is not a regular file: {path}"
        if unavailable_is_config:
            raise EmbeddedProviderConfigError(msg)
        raise EmbeddedProviderUnavailableError(msg)
    return snapshot, hashlib.sha256(data).hexdigest(), data


def _read_stable_file(path: Path) -> tuple[_FileSnapshot, bytes]:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    descriptor = os.open(path, flags)
    try:
        before = _snapshot_from_stat(os.fstat(descriptor))
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, _PROVIDER_READ_SIZE):
            chunks.append(chunk)
        after = _snapshot_from_stat(os.fstat(descriptor))
    finally:
        os.close(descriptor)
    if before != after:
        msg = f"file changed while it was read: {path}"
        raise OSError(msg)
    return after, b"".join(chunks)


def _private_executable_root(language: EmbeddedProviderLanguage) -> Path:
    if os.name == "nt":
        raw_root = os.environ.get("LOCALAPPDATA")
        root = Path(raw_root) / "Citry" / "provider-executables" if raw_root else Path.home() / ".citry"
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Caches" / "citry" / "provider-executables"
    else:
        raw_root = os.environ.get("XDG_CACHE_HOME")
        cache = Path(raw_root) if raw_root else Path.home() / ".cache"
        root = cache / "citry" / "provider-executables"
    try:
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        resolved = root.resolve(strict=True)
        metadata = resolved.stat()
    except OSError as error:
        msg = f"{language} provider executable cache is unavailable: {error}"
        raise EmbeddedProviderConfigError(msg) from error
    if not stat.S_ISDIR(metadata.st_mode):
        msg = f"{language} provider executable cache is not a directory: {resolved}"
        raise EmbeddedProviderConfigError(msg)
    if os.name == "posix" and (
        metadata.st_uid != os.getuid()  # type: ignore[attr-defined]
        or stat.S_IMODE(metadata.st_mode) & 0o077
    ):
        msg = f"{language} provider executable cache must be private to the current user: {resolved}"
        raise EmbeddedProviderConfigError(msg)
    return resolved


def _private_file_copy(
    data: bytes,
    *,
    name: str,
    parent: Path | None,
    executable: bool,
    language: EmbeddedProviderLanguage,
    unavailable_is_config: bool,
) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    owner: tempfile.TemporaryDirectory[str] | None = None
    try:
        owner = tempfile.TemporaryDirectory(
            prefix=".citry-biome-",
            dir=parent,
        )
        path = Path(owner.name) / name
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        descriptor = os.open(path, flags, 0o700 if executable else 0o600)
        try:
            view = memoryview(data)
            while view:
                written = os.write(descriptor, view)
                view = view[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        path.chmod(0o500 if executable else 0o400)
        return owner, path
    except OSError as error:
        if owner is not None:
            owner.cleanup()
        kind = "executable" if executable else "configuration"
        msg = f"{language} provider could not secure its {kind} bytes: {error}"
        if unavailable_is_config:
            raise EmbeddedProviderConfigError(msg) from error
        raise EmbeddedProviderInvalidError(msg) from error


def _lock_private_executable(
    path: Path,
    *,
    expected_digest: str,
    language: EmbeddedProviderLanguage,
) -> IO[bytes]:
    stream: IO[bytes] | None = None
    try:
        if os.name == "nt":
            import msvcrt  # noqa: PLC0415 - this module exists only on Windows

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
            kernel32.CreateFileW.restype = wintypes.HANDLE
            handle = kernel32.CreateFileW(
                os.fspath(path),
                0x80000000,
                0x00000001,
                None,
                3,
                0x00000080,
                None,
            )
            if handle == wintypes.HANDLE(-1).value:
                raise ctypes.WinError(ctypes.get_last_error())  # type: ignore[attr-defined]
            descriptor = msvcrt.open_osfhandle(  # type: ignore[attr-defined]
                int(handle),
                os.O_RDONLY | getattr(os, "O_BINARY", 0),
            )
        else:
            descriptor = os.open(path, os.O_RDONLY)
        stream = os.fdopen(descriptor, "rb", buffering=0)
        _validate_private_copy(
            stream,
            expected_digest=expected_digest,
            language=language,
            unavailable_is_config=True,
        )
        if sys.platform == "linux":
            path.unlink()
        return stream
    except OSError as error:
        if stream is not None:
            stream.close()
        msg = f"{language} provider could not lock its secured executable: {error}"
        raise EmbeddedProviderConfigError(msg) from error


def _validate_private_copy(
    stream: IO[bytes],
    *,
    expected_digest: str,
    language: EmbeddedProviderLanguage,
    unavailable_is_config: bool,
) -> None:
    try:
        stream.seek(0)
        data = stream.read()
        stream.seek(0)
    except OSError as error:
        msg = f"{language} provider secured executable is unavailable: {error}"
        if unavailable_is_config:
            raise EmbeddedProviderConfigError(msg) from error
        raise EmbeddedProviderUnavailableError(msg) from error
    if hashlib.sha256(data).hexdigest() != expected_digest:
        msg = f"{language} provider secured executable changed after its version probe"
        if unavailable_is_config:
            raise EmbeddedProviderConfigError(msg)
        raise EmbeddedProviderUnavailableError(msg)


def _find_biome_config(directory: Path, *, language: EmbeddedProviderLanguage) -> Path | None:
    for parent in (directory, *directory.parents):
        candidates = [parent / name for name in _BIOME_CONFIG_NAMES]
        symlinks = [candidate for candidate in candidates if candidate.is_symlink()]
        if symlinks:
            msg = f"{language} provider configuration must not be a symlink: {symlinks[0]}"
            raise EmbeddedProviderInvalidError(msg)
        matches = [candidate for candidate in candidates if candidate.is_file()]
        if len(matches) > 1:
            msg = f"{language} provider found both biome.json and biome.jsonc in {parent}"
            raise EmbeddedProviderInvalidError(msg)
        if matches:
            return matches[0].resolve()
    return None


def _validate_self_contained_executable(
    executable: Path,
    data: bytes,
    *,
    language: EmbeddedProviderLanguage,
) -> None:
    first_line = data.partition(b"\n")[0]
    if executable.suffix.lower() in {".cmd", ".bat", ".ps1"} or first_line.startswith(b"#!"):
        msg = (
            f"{language} provider must name the self-contained native Biome binary; "
            "interpreter and package-manager launchers are not supported"
        )
        raise EmbeddedProviderConfigError(msg)


def _biome_config_snapshot(
    path: Path,
    *,
    language: EmbeddedProviderLanguage,
) -> tuple[_FileSnapshot, str, bytes]:
    try:
        snapshot, data = _read_stable_file(path)
    except OSError as error:
        msg = f"{language} provider configuration is unavailable: {error}"
        raise EmbeddedProviderInvalidError(msg) from error
    try:
        config = json.loads(_remove_jsonc_trailing_commas(_strip_jsonc_comments(data.decode("utf-8"))))
    except (UnicodeError, json.JSONDecodeError) as error:
        msg = f"{language} provider configuration is invalid JSON/JSONC: {error}"
        raise EmbeddedProviderInvalidError(msg) from error
    if type(config) is not dict:
        msg = f"{language} provider configuration root must be an object"
        raise EmbeddedProviderInvalidError(msg)
    external_dependency_keys = [key for key in ("extends", "plugins") if _json_contains_key(config, key)]
    if external_dependency_keys:
        keys = " and ".join(external_dependency_keys)
        msg = (
            f"{language} provider configuration uses {keys}, whose external dependencies "
            "cannot be fingerprinted by this adapter"
        )
        raise EmbeddedProviderInvalidError(msg)
    return snapshot, hashlib.sha256(data).hexdigest(), data


def _json_contains_key(value: object, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_json_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_json_contains_key(item, key) for item in value)
    return False


def _snapshot_from_stat(metadata: os.stat_result) -> _FileSnapshot:
    return _FileSnapshot(
        device=metadata.st_dev,
        inode=metadata.st_ino,
        mode=metadata.st_mode,
        size=metadata.st_size,
        modified_ns=metadata.st_mtime_ns,
    )


def _strip_jsonc_comments(source: str) -> str:
    result: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(source):
        char = source[index]
        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue
        if source.startswith("//", index):
            while index < len(source) and source[index] not in "\r\n":
                result.append(" ")
                index += 1
            continue
        if source.startswith("/*", index):
            result.extend((" ", " "))
            index += 2
            while index < len(source) and not source.startswith("*/", index):
                result.append(source[index] if source[index] in "\r\n" else " ")
                index += 1
            if index < len(source):
                result.extend((" ", " "))
                index += 2
            continue
        result.append(char)
        index += 1
    return "".join(result)


def _remove_jsonc_trailing_commas(source: str) -> str:
    result: list[str] = []
    in_string = False
    escaped = False
    for index, char in enumerate(source):
        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            result.append(char)
            continue
        if char == ",":
            remaining = source[index + 1 :].lstrip()
            if remaining.startswith(("}", "]")):
                continue
        result.append(char)
    return "".join(result)


def _provider_environment() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith("BIOME_")}


@dataclass(slots=True)
class _CaptureState:
    stdout: bytearray
    stderr: bytearray
    size: int
    overflow: threading.Event
    lock: threading.Lock


@dataclass(frozen=True, slots=True)
class _WindowsJob:
    handle: int


def _capture_pipe(stream: IO[bytes], target: bytearray, state: _CaptureState) -> None:
    try:
        while chunk := os.read(stream.fileno(), _PROVIDER_READ_SIZE):
            with state.lock:
                remaining = max(_PROVIDER_OUTPUT_LIMIT + 1 - state.size, 0)
                target.extend(chunk[:remaining])
                state.size += len(chunk)
                if state.size > _PROVIDER_OUTPUT_LIMIT:
                    state.overflow.set()
                    return
    except OSError:
        return


def _write_provider_input(stream: IO[bytes], data: bytes) -> None:
    try:
        stream.write(data)
        stream.close()
    except (BrokenPipeError, OSError):
        return


def _create_windows_job(process: subprocess.Popen[bytes]) -> _WindowsJob:
    class IoCounters(ctypes.Structure):
        _fields_ = [  # noqa: RUF012 - ctypes requires this mutable class attribute
            ("read_operation_count", ctypes.c_uint64),
            ("write_operation_count", ctypes.c_uint64),
            ("other_operation_count", ctypes.c_uint64),
            ("read_transfer_count", ctypes.c_uint64),
            ("write_transfer_count", ctypes.c_uint64),
            ("other_transfer_count", ctypes.c_uint64),
        ]

    class BasicLimitInformation(ctypes.Structure):
        _fields_ = [  # noqa: RUF012 - ctypes requires this mutable class attribute
            ("per_process_user_time_limit", ctypes.c_int64),
            ("per_job_user_time_limit", ctypes.c_int64),
            ("limit_flags", wintypes.DWORD),
            ("minimum_working_set_size", ctypes.c_size_t),
            ("maximum_working_set_size", ctypes.c_size_t),
            ("active_process_limit", wintypes.DWORD),
            ("affinity", ctypes.c_size_t),
            ("priority_class", wintypes.DWORD),
            ("scheduling_class", wintypes.DWORD),
        ]

    class ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [  # noqa: RUF012 - ctypes requires this mutable class attribute
            ("basic_limit_information", BasicLimitInformation),
            ("io_info", IoCounters),
            ("process_memory_limit", ctypes.c_size_t),
            ("job_memory_limit", ctypes.c_size_t),
            ("peak_process_memory_used", ctypes.c_size_t),
            ("peak_job_memory_used", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    kernel32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    handle = kernel32.CreateJobObjectW(None, None)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())  # type: ignore[attr-defined]
    information = ExtendedLimitInformation()
    information.basic_limit_information.limit_flags = 0x00002000
    if not kernel32.SetInformationJobObject(
        handle,
        9,
        ctypes.byref(information),
        ctypes.sizeof(information),
    ):
        error = ctypes.WinError(ctypes.get_last_error())  # type: ignore[attr-defined]
        kernel32.CloseHandle(handle)
        raise error
    if not kernel32.AssignProcessToJobObject(
        handle,
        wintypes.HANDLE(int(process._handle)),  # type: ignore[attr-defined]
    ):
        error = ctypes.WinError(ctypes.get_last_error())  # type: ignore[attr-defined]
        kernel32.CloseHandle(handle)
        raise error
    return _WindowsJob(int(handle))


def _terminate_windows_job(job: _WindowsJob) -> None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
    kernel32.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
    kernel32.TerminateJobObject(wintypes.HANDLE(job.handle), 1)


def _close_windows_job(job: _WindowsJob) -> None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle(wintypes.HANDLE(job.handle))


def _terminate_provider(process: subprocess.Popen[bytes], windows_job: _WindowsJob | None) -> None:
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)  # type: ignore[attr-defined]
        except ProcessLookupError:
            pass
        except OSError:
            process.kill()
    elif windows_job is not None:
        _terminate_windows_job(windows_job)
    else:
        process.kill()
    try:
        process.wait(timeout=_PROVIDER_THREAD_JOIN_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()


def _run_provider(
    executable: Path,
    arguments: tuple[str, ...],
    *,
    input_text: str | None,
    cwd: Path,
    language: EmbeddedProviderLanguage,
    unavailable_is_config: bool,
    environment: dict[str, str],
    executable_descriptor: int | None = None,
) -> str:
    try:
        input_bytes = input_text.encode("utf-8") if input_text is not None else None
    except UnicodeError as error:
        _raise_provider_failure(
            f"{language} provider input is not valid UTF-8: {error}",
            error=error,
            unavailable_is_config=unavailable_is_config,
            invalid=True,
        )
    # Annotated because mypy prunes the branch that does not match the platform
    # it runs on, so without this the two arms disagree when checked on Linux.
    pass_fds: tuple[int, ...]
    if executable_descriptor is not None and sys.platform == "linux":
        os.lseek(executable_descriptor, 0, os.SEEK_SET)
        descriptor_root = "/dev/fd" if Path("/dev/fd").is_dir() else "/proc/self/fd"
        provider_executable = f"{descriptor_root}/{executable_descriptor}"
        pass_fds = (executable_descriptor,)
    else:
        provider_executable = os.fspath(executable)
        pass_fds = ()
    provider_command = (provider_executable, *arguments)
    command = (
        (sys.executable, "-c", _WINDOWS_PROVIDER_LAUNCHER, *provider_command) if os.name == "nt" else provider_command
    )
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE if input_bytes is not None or os.name == "nt" else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=environment,
            shell=False,
            start_new_session=os.name == "posix",
            creationflags=creationflags,
            pass_fds=pass_fds,
        )
    except OSError as error:
        _raise_provider_failure(
            f"{language} provider could not run: {error}",
            error=error,
            unavailable_is_config=unavailable_is_config,
            invalid=False,
        )
    windows_job: _WindowsJob | None = None
    if os.name == "nt":
        try:
            windows_job = _create_windows_job(process)
        except OSError as error:
            process.kill()
            process.wait()
            _raise_provider_failure(
                f"{language} provider could not establish process-tree isolation: {error}",
                error=error,
                unavailable_is_config=unavailable_is_config,
                invalid=False,
            )
    stdout_pipe = process.stdout
    stderr_pipe = process.stderr
    if stdout_pipe is None or stderr_pipe is None:
        msg = "provider process was created without output pipes"
        raise RuntimeError(msg)
    state = _CaptureState(bytearray(), bytearray(), 0, threading.Event(), threading.Lock())
    readers = [
        threading.Thread(target=_capture_pipe, args=(stdout_pipe, state.stdout, state), daemon=True),
        threading.Thread(target=_capture_pipe, args=(stderr_pipe, state.stderr, state), daemon=True),
    ]
    for reader in readers:
        reader.start()
    writer: threading.Thread | None = None
    provider_input = (b"\0" if os.name == "nt" else b"") + (input_bytes or b"")
    if provider_input or os.name == "nt":
        stdin_pipe = process.stdin
        if stdin_pipe is None:
            msg = "provider process was created without an input pipe"
            raise RuntimeError(msg)
        writer = threading.Thread(
            target=_write_provider_input,
            args=(stdin_pipe, provider_input),
            daemon=True,
        )
        writer.start()

    deadline = time.monotonic() + _PROVIDER_TIMEOUT_SECONDS
    timed_out = False
    while process.poll() is None and not state.overflow.is_set():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            break
        try:
            process.wait(timeout=min(remaining, 0.05))
        except subprocess.TimeoutExpired:
            continue
    if timed_out or state.overflow.is_set():
        _terminate_provider(process, windows_job)
    elif os.name == "posix":
        # A provider result belongs to the selected executable, not descendants
        # that outlive it and retain its output pipes.
        with suppress(OSError):
            os.killpg(process.pid, signal.SIGKILL)  # type: ignore[attr-defined]
    elif windows_job is not None:
        _terminate_windows_job(windows_job)

    if windows_job is not None:
        _close_windows_job(windows_job)

    for reader in readers:
        reader.join(_PROVIDER_THREAD_JOIN_SECONDS)
    inherited_pipe = any(reader.is_alive() for reader in readers)
    if inherited_pipe:
        _terminate_provider(process, None)
        stdout_pipe.close()
        stderr_pipe.close()
        for reader in readers:
            reader.join(_PROVIDER_THREAD_JOIN_SECONDS)
    if writer is not None:
        writer.join(_PROVIDER_THREAD_JOIN_SECONDS)

    if state.overflow.is_set():
        _raise_provider_failure(
            f"{language} provider output exceeds {_PROVIDER_OUTPUT_LIMIT} bytes",
            error=None,
            unavailable_is_config=unavailable_is_config,
            invalid=True,
        )
    if timed_out:
        _raise_provider_failure(
            f"{language} provider timed out after {_PROVIDER_TIMEOUT_SECONDS:g} seconds",
            error=None,
            unavailable_is_config=unavailable_is_config,
            invalid=False,
        )
    if inherited_pipe:
        _raise_provider_failure(
            f"{language} provider descendants kept output pipes open",
            error=None,
            unavailable_is_config=unavailable_is_config,
            invalid=True,
        )
    try:
        stdout = bytes(state.stdout).decode("utf-8", errors="strict")
        stderr = bytes(state.stderr).decode("utf-8", errors="strict")
    except UnicodeError as error:
        _raise_provider_failure(
            f"{language} provider returned non-UTF-8 output: {error}",
            error=error,
            unavailable_is_config=unavailable_is_config,
            invalid=True,
        )
    if process.returncode != 0:
        detail = (stderr.strip() or stdout.strip() or "no diagnostic")[:_PROVIDER_DIAGNOSTIC_LIMIT]
        _raise_provider_failure(
            f"{language} provider exited with status {process.returncode}: {detail}",
            error=None,
            unavailable_is_config=unavailable_is_config,
            invalid=True,
        )
    return stdout


def _raise_provider_failure(
    message: str,
    *,
    error: BaseException | None,
    unavailable_is_config: bool,
    invalid: bool,
) -> NoReturn:
    if unavailable_is_config:
        raise EmbeddedProviderConfigError(message) from error
    if invalid:
        raise EmbeddedProviderInvalidError(message) from error
    raise EmbeddedProviderUnavailableError(message) from error


__all__ = [
    "BiomeEmbeddedProvider",
    "EmbeddedProviderConfigError",
    "EmbeddedProviderInvalidError",
    "EmbeddedProviderUnavailableError",
]
