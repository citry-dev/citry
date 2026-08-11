from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path

import pytest

import citry._embedded_provider as embedded_provider_module
from citry._embedded_provider import (
    BiomeEmbeddedProvider,
    EmbeddedProviderConfigError,
    EmbeddedProviderInvalidError,
    EmbeddedProviderLanguage,
    EmbeddedProviderUnavailableError,
)

_TEST_PROVIDER_MARKER = b"#!/bin/sh\n# citry-test-self-contained-provider\n"
_validate_real_executable = embedded_provider_module._validate_self_contained_executable


def _provider_script(path: Path, body: str) -> Path:
    if os.name == "nt":
        pytest.skip("this provider behavior uses a POSIX shell fake")
    path.write_bytes(_TEST_PROVIDER_MARKER + body.encode() + b"\n")
    path.chmod(0o755)
    return path


@pytest.fixture(autouse=True)
def _isolated_provider_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = tmp_path / "provider-cache"
    cache.mkdir(mode=0o700)
    monkeypatch.setattr(embedded_provider_module, "_private_executable_root", lambda _language: cache)

    def allow_explicit_test_provider(
        executable: Path,
        data: bytes,
        *,
        language: EmbeddedProviderLanguage,
    ) -> None:
        if data.startswith(_TEST_PROVIDER_MARKER):
            return
        _validate_real_executable(executable, data, language=language)

    monkeypatch.setattr(
        embedded_provider_module,
        "_validate_self_contained_executable",
        allow_explicit_test_provider,
    )


def test_explicit_biome_provider_probes_and_formats_over_stdin(tmp_path: Path) -> None:
    log = tmp_path / "args.log"
    executable = _provider_script(
        tmp_path / "biome",
        f"""
if [ "$1" = "--version" ]; then
  printf '2.5.6'
  exit 0
fi
printf '%s\\n' "$@" > {os.fspath(log)!r}
sed 's/  */ /g; s/ = /=/g; s/= /=/g'
""",
    )
    provider = BiomeEmbeddedProvider.from_spec(
        f"biome:{executable}",
        language="javascript",
    )

    output = provider.format_source(
        "const  value = 1;\n",
        source_path=(tmp_path / "component.js").resolve(),
    )

    assert provider.identity == "biome@2.5.6+effective-options:per-target"
    assert output == "const value=1;\n"
    arguments = log.read_text(encoding="utf-8").splitlines()
    assert arguments[:6] == [
        "format",
        "--write",
        "--colors=off",
        "--line-ending=lf",
        "--use-editorconfig=false",
        "--vcs-enabled=false",
    ]
    assert arguments[6].startswith("--config-path=")
    assert Path(arguments[6].partition("=")[2]).name == "biome.json"
    assert arguments[7].startswith("--stdin-file-path=")
    assert Path(arguments[7].partition("=")[2]).name == "component.js"


@pytest.mark.parametrize(
    "value",
    ["biome", "prettier:/absolute/prettier", "biome:relative/biome", "sh:echo hi"],
)
def test_provider_spec_never_falls_back_to_path_or_shell(value: str) -> None:
    with pytest.raises(EmbeddedProviderConfigError):
        BiomeEmbeddedProvider.from_spec(value, language="css")


@pytest.mark.parametrize(
    ("name", "body"),
    [
        ("biome", "#!/usr/bin/env node\nconsole.log('2.5.6')\n"),
        (
            "biome",
            '#!/bin/sh\nbasedir=$(dirname "$0")\nexec "$basedir/../@biomejs/biome/bin/biome" "$@"\n',
        ),
        ("biome", '#!/bin/sh\nexec /opt/external/biome "$@"\n'),
        ("biome.cmd", "@echo off\necho 2.5.6\n"),
    ],
)
def test_provider_rejects_dependency_resolving_package_launchers(
    tmp_path: Path,
    name: str,
    body: str,
) -> None:
    launcher = tmp_path / name
    launcher.write_text(body, encoding="utf-8")
    launcher.chmod(0o755)

    with pytest.raises(EmbeddedProviderConfigError, match="self-contained native Biome binary"):
        BiomeEmbeddedProvider.from_spec(f"biome:{launcher}", language="javascript")


@pytest.mark.skipif(os.name != "nt", reason="Windows native-executable adapter coverage")
def test_windows_accepts_a_native_executable_without_using_command_shells(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executable = tmp_path / "biome.exe"
    shutil.copy2(sys.executable, executable)

    def fake_provider(
        _executable: Path,
        arguments: tuple[str, ...],
        *,
        input_text: str | None,
        **_kwargs: object,
    ) -> str:
        if arguments == ("--version",):
            return "2.5.6"
        assert input_text is not None
        return input_text

    monkeypatch.setattr(embedded_provider_module, "_run_provider", fake_provider)
    provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="css")
    private_root = Path(provider._private_executable_owner.name)

    try:
        assert provider.format_source(".card {}", source_path=tmp_path / "component.css") == ".card {}"
    finally:
        provider.close()
    provider.close()

    assert provider._private_executable_stream.closed is True
    assert private_root.exists() is False


def test_closed_provider_rejects_later_formatting(tmp_path: Path) -> None:
    executable = _provider_script(
        tmp_path / "biome",
        'if [ "$1" = "--version" ]; then printf \'2.5.6\'; else cat; fi',
    )
    provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="css")
    provider.close()

    with pytest.raises(EmbeddedProviderUnavailableError, match="closed"):
        provider.format_source(".card {}", source_path=(tmp_path / "component.css").resolve())


def test_nonzero_formatter_result_is_provider_invalid(tmp_path: Path) -> None:
    executable = _provider_script(
        tmp_path / "biome",
        """
if [ "$1" = "--version" ]; then printf '2.5.6'; exit 0; fi
printf 'bad css' >&2
exit 3
""",
    )
    provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="css")

    with pytest.raises(EmbeddedProviderInvalidError, match="status 3"):
        provider.format_source(
            ".a{}",
            source_path=(tmp_path / "component.css").resolve(),
        )


@pytest.mark.parametrize("version", ["Version:", "Biome 2.5", "2", "2.5.6\\nextra"])
def test_malformed_biome_version_is_rejected(tmp_path: Path, version: str) -> None:
    executable = _provider_script(tmp_path / "biome", f"printf '%s' {version!r}")

    with pytest.raises(EmbeddedProviderConfigError, match="version"):
        BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="javascript")


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_provider_output_limit_is_enforced_while_streaming(tmp_path: Path, monkeypatch, stream: str) -> None:
    redirect = "" if stream == "stdout" else ">&2"
    executable = _provider_script(
        tmp_path / "biome",
        f"""
if [ "$1" = "--version" ]; then printf '2.5.6'; exit 0; fi
head -c 4096 /dev/zero | tr '\\0' x {redirect}
sleep 5
""",
    )
    provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="javascript")
    monkeypatch.setattr(embedded_provider_module, "_PROVIDER_OUTPUT_LIMIT", 128)

    started = time.monotonic()
    with pytest.raises(EmbeddedProviderInvalidError, match="exceeds 128 bytes"):
        provider.format_source("const value = 1;", source_path=(tmp_path / "component.js").resolve())
    assert time.monotonic() - started < 2


@pytest.mark.skipif(os.name != "posix", reason="process-group cleanup is POSIX-specific")
def test_provider_descendant_cannot_hold_output_pipe_open(tmp_path: Path) -> None:
    executable = _provider_script(
        tmp_path / "biome",
        """
if [ "$1" = "--version" ]; then printf '2.5.6'; exit 0; fi
sleep 5 &
printf 'const value = 1;'
""",
    )
    provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="javascript")

    started = time.monotonic()
    output = provider.format_source("const value=1;", source_path=(tmp_path / "component.js").resolve())

    assert output == "const value = 1;"
    assert time.monotonic() - started < 2


@pytest.mark.skipif(os.name != "posix", reason="process-group cleanup is POSIX-specific")
def test_provider_timeout_terminates_its_process_tree(tmp_path: Path, monkeypatch) -> None:
    executable = _provider_script(
        tmp_path / "biome",
        """
if [ "$1" = "--version" ]; then printf '2.5.6'; exit 0; fi
sleep 5 &
wait
""",
    )
    provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="css")
    monkeypatch.setattr(embedded_provider_module, "_PROVIDER_TIMEOUT_SECONDS", 0.05)

    started = time.monotonic()
    with pytest.raises(EmbeddedProviderUnavailableError, match="timed out"):
        provider.format_source(".card {}", source_path=(tmp_path / "component.css").resolve())
    assert time.monotonic() - started < 2


def test_provider_runner_terminates_cross_platform_descendants_holding_pipes(tmp_path: Path) -> None:
    child = "import time; time.sleep(5)"
    source = (
        "import subprocess, sys; "
        f"subprocess.Popen([sys.executable, '-c', {child!r}]); "
        "print('const value = 1;', end='')"
    )

    started = time.monotonic()
    output = embedded_provider_module._run_provider(
        Path(sys.executable),
        ("-c", source),
        input_text=None,
        cwd=tmp_path,
        language="javascript",
        unavailable_is_config=False,
        environment=os.environ.copy(),
    )

    assert output == "const value = 1;"
    assert time.monotonic() - started < 2


def test_provider_runner_terminates_cross_platform_descendants_on_timeout(tmp_path: Path, monkeypatch) -> None:
    child = "import time; time.sleep(5)"
    source = f"import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', {child!r}]); time.sleep(5)"
    monkeypatch.setattr(embedded_provider_module, "_PROVIDER_TIMEOUT_SECONDS", 0.05)

    started = time.monotonic()
    with pytest.raises(EmbeddedProviderUnavailableError, match="timed out"):
        embedded_provider_module._run_provider(
            Path(sys.executable),
            ("-c", source),
            input_text=None,
            cwd=tmp_path,
            language="css",
            unavailable_is_config=False,
            environment=os.environ.copy(),
        )
    assert time.monotonic() - started < 2


def test_provider_runner_rejects_non_utf8_input_before_spawning(tmp_path: Path, monkeypatch) -> None:
    spawned = False

    def unexpected_popen(*args, **kwargs):
        nonlocal spawned
        spawned = True
        raise AssertionError("provider must not start")

    monkeypatch.setattr(embedded_provider_module.subprocess, "Popen", unexpected_popen)

    with pytest.raises(EmbeddedProviderInvalidError, match="input is not valid UTF-8"):
        embedded_provider_module._run_provider(
            Path(sys.executable),
            ("-c", "raise AssertionError"),
            input_text="\ud800",
            cwd=tmp_path,
            language="javascript",
            unavailable_is_config=False,
            environment=os.environ.copy(),
        )

    assert spawned is False


def test_executable_replacement_after_probe_is_rejected(tmp_path: Path) -> None:
    executable = _provider_script(
        tmp_path / "biome",
        'if [ "$1" = "--version" ]; then printf \'2.5.6\'; else cat; fi',
    )
    provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="css")
    replacement = _provider_script(
        tmp_path / "replacement",
        "if [ \"$1\" = \"--version\" ]; then printf '2.5.6'; else printf 'changed'; fi",
    )
    replacement.replace(executable)

    with pytest.raises(EmbeddedProviderUnavailableError, match="changed after"):
        provider.format_source(".card {}", source_path=(tmp_path / "component.css").resolve())


def test_nested_config_and_source_path_change_invocation_identity(tmp_path: Path, monkeypatch) -> None:
    log = tmp_path / "args.log"
    executable = _provider_script(
        tmp_path / "biome",
        f"""
if [ "$1" = "--version" ]; then printf '2.5.6'; exit 0; fi
config=''
for argument in "$@"; do
  case "$argument" in --config-path=*) config=${{argument#--config-path=}};; esac
done
printf '%s|%s|' "${{BIOME_CONFIG_PATH-unset}}" "$*" >> {os.fspath(log)!r}
if [ -n "$config" ]; then tr '\\n' ' ' < "$config" >> {os.fspath(log)!r}; fi
printf '\\n' >> {os.fspath(log)!r}
cat
""",
    )
    root = tmp_path / "project"
    nested = root / "nested"
    nested.mkdir(parents=True)
    (root / "biome.json").write_text('{"formatter": {"lineWidth": 80}}', encoding="utf-8")
    (nested / "biome.jsonc").write_text(
        '{\n  // target-specific style\n  "formatter": {"lineWidth": 120},\n}',
        encoding="utf-8",
    )
    monkeypatch.setenv("BIOME_CONFIG_PATH", os.fspath(tmp_path / "untrusted.json"))
    provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="javascript")

    _root_text, root_identity = provider.format_source_with_identity(
        "const value = 1;",
        source_path=(root / "component.js").resolve(),
    )
    _nested_text, nested_identity = provider.format_source_with_identity(
        "const value = 1;",
        source_path=(nested / "component.js").resolve(),
    )

    assert root_identity != nested_identity
    lines = log.read_text(encoding="utf-8").splitlines()
    assert all(line.startswith("unset|") for line in lines)
    assert f"--config-path={root / 'biome.json'}" not in lines[0]
    assert f"--config-path={nested / 'biome.jsonc'}" not in lines[1]
    assert '"lineWidth": 80' in lines[0]
    assert '"lineWidth": 120' in lines[1]


@pytest.mark.skipif(os.name != "posix", reason="POSIX directory modes are required")
def test_provider_executable_does_not_require_a_writable_source_directory(tmp_path: Path) -> None:
    directory = tmp_path / "read-only"
    directory.mkdir()
    executable = _provider_script(
        directory / "biome",
        'if [ "$1" = "--version" ]; then printf \'2.5.6\'; else cat; fi',
    )
    directory.chmod(0o555)
    try:
        provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="css")
        output = provider.format_source(
            ".card {}",
            source_path=(tmp_path / "component.css").resolve(),
        )
    finally:
        directory.chmod(0o755)

    assert output == ".card {}"


def test_format_executes_secured_executable_bytes_during_swap_restore(tmp_path: Path, monkeypatch) -> None:
    executable = _provider_script(
        tmp_path / "biome",
        'if [ "$1" = "--version" ]; then printf \'2.5.6\'; else cat; fi',
    )
    original = executable.read_bytes()
    replacement = _provider_script(
        tmp_path / "replacement",
        'if [ "$1" = "--version" ]; then printf \'2.5.6\'; else printf changed; fi',
    ).read_bytes()
    provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="javascript")
    original_stat = executable.stat()
    run_provider = embedded_provider_module._run_provider

    def swap_while_running(*args, **kwargs):
        executable.write_bytes(replacement)
        try:
            return run_provider(*args, **kwargs)
        finally:
            executable.write_bytes(original)
            os.utime(executable, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))

    monkeypatch.setattr(embedded_provider_module, "_run_provider", swap_while_running)

    output = provider.format_source(
        "const value = 1;",
        source_path=(tmp_path / "component.js").resolve(),
    )

    assert output == "const value = 1;"


def test_format_uses_secured_config_bytes_during_swap_restore(tmp_path: Path, monkeypatch) -> None:
    executable = _provider_script(
        tmp_path / "biome",
        """
if [ "$1" = "--version" ]; then printf '2.5.6'; exit 0; fi
for argument in "$@"; do
  case "$argument" in --config-path=*) cat "${argument#--config-path=}"; exit 0;; esac
done
cat
""",
    )
    config = tmp_path / "biome.json"
    original = b'{"formatter": {"lineWidth": 80}}'
    config.write_bytes(original)
    provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="css")
    original_stat = config.stat()
    run_provider = embedded_provider_module._run_provider

    def swap_while_running(*args, **kwargs):
        config.write_bytes(b'{"formatter": {"lineWidth": 1}}')
        try:
            return run_provider(*args, **kwargs)
        finally:
            config.write_bytes(original)
            os.utime(config, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))

    monkeypatch.setattr(embedded_provider_module, "_run_provider", swap_while_running)

    output = provider.format_source(
        ".card {}",
        source_path=(tmp_path / "component.css").resolve(),
    )

    assert output == original.decode()


def test_no_config_invocation_cannot_discover_an_ephemeral_ambient_config(tmp_path: Path, monkeypatch) -> None:
    executable = _provider_script(
        tmp_path / "biome",
        """
if [ "$1" = "--version" ]; then printf '2.5.6'; exit 0; fi
for argument in "$@"; do
  case "$argument" in --config-path=*) cat "${argument#--config-path=}"; exit 0;; esac
done
printf missing
""",
    )
    provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="javascript")
    config = tmp_path / "biome.json"
    run_provider = embedded_provider_module._run_provider

    def add_ambient_config_while_running(*args, **kwargs):
        config.write_text('{"formatter": {"lineWidth": 1}}', encoding="utf-8")
        try:
            return run_provider(*args, **kwargs)
        finally:
            config.unlink()

    monkeypatch.setattr(embedded_provider_module, "_run_provider", add_ambient_config_while_running)

    output = provider.format_source(
        "const value = 1;",
        source_path=(tmp_path / "component.js").resolve(),
    )

    assert output == "{}"


def test_config_extends_is_rejected_when_dependencies_cannot_be_fingerprinted(tmp_path: Path) -> None:
    executable = _provider_script(
        tmp_path / "biome",
        'if [ "$1" = "--version" ]; then printf \'2.5.6\'; else cat; fi',
    )
    (tmp_path / "biome.json").write_text('{"extends": ["./shared.json"]}', encoding="utf-8")
    provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="css")

    with pytest.raises(EmbeddedProviderInvalidError, match="cannot be fingerprinted"):
        provider.format_source(".card {}", source_path=(tmp_path / "component.css").resolve())


@pytest.mark.parametrize(
    "config",
    [
        '{"plugins": ["./my-plugin.grit"]}',
        '{"plugins": [{"path": "./my-plugin.grit"}]}',
    ],
)
def test_config_plugins_are_rejected_when_dependencies_cannot_be_fingerprinted(
    tmp_path: Path,
    config: str,
) -> None:
    executable = _provider_script(
        tmp_path / "biome",
        'if [ "$1" = "--version" ]; then printf \'2.5.6\'; else cat; fi',
    )
    (tmp_path / "biome.json").write_text(config, encoding="utf-8")
    provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="css")

    with pytest.raises(EmbeddedProviderInvalidError, match="uses plugins"):
        provider.format_source(".card {}", source_path=(tmp_path / "component.css").resolve())


def test_config_override_plugins_are_rejected_when_dependencies_cannot_be_fingerprinted(
    tmp_path: Path,
) -> None:
    executable = _provider_script(
        tmp_path / "biome",
        'if [ "$1" = "--version" ]; then printf \'2.5.6\'; else cat; fi',
    )
    (tmp_path / "biome.json").write_text(
        '{"overrides": [{"includes": ["**/*.js"], "plugins": ["./x.grit"]}]}',
        encoding="utf-8",
    )
    provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="javascript")

    with pytest.raises(EmbeddedProviderInvalidError, match="uses plugins"):
        provider.format_source("const value=1", source_path=(tmp_path / "component.js").resolve())


def test_symlinked_config_is_rejected_with_a_structured_error(tmp_path: Path) -> None:
    executable = _provider_script(
        tmp_path / "biome",
        'if [ "$1" = "--version" ]; then printf \'2.5.6\'; else cat; fi',
    )
    shared = tmp_path / "shared"
    shared.mkdir()
    (shared / "biome.json").write_text("{}", encoding="utf-8")
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / "biome.json").symlink_to(shared / "biome.json")
    except OSError:
        pytest.skip("this platform does not permit an unprivileged symlink")
    provider = BiomeEmbeddedProvider.from_spec(f"biome:{executable}", language="css")

    with pytest.raises(EmbeddedProviderInvalidError, match="must not be a symlink"):
        provider.format_source(".card {}", source_path=(project / "component.css").resolve())
