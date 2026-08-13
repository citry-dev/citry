"""Standalone i18n catalog package loading and project-linking tests."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
import zipfile
from decimal import Decimal
from pathlib import Path

import pytest

from citry import Citry, Component, ComponentLibrary, LibraryComponent
from citry.command import run
from citry.ext.i18n.commands import (
    CheckI18nCommand,
    CompileI18nCommand,
    CoverageI18nCommand,
    ExtractI18nCommand,
    InspectI18nCommand,
)
from citry.ext.i18n.formats import FormatRegistry, NumberFormat
from citry.ext.i18n.packages import compile_catalog_package


def _write_package(
    root: Path,
    name: str,
    *,
    locales: dict[str, dict[str, str]],
    manifest: bool = False,
    formats: dict[str, object] | None = None,
) -> None:
    package = root / name
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf8")
    (package / "citry-i18n.toml").write_text(
        'schema_version = 1\nowner = "demo"\nsource_locale = "en-US"\n',
        encoding="utf8",
    )
    if formats is not None:
        (package / "formats.json").write_text(
            json.dumps(formats, separators=(",", ":")),
            encoding="utf8",
        )
    source_records = []
    for locale, resources in locales.items():
        locale_root = package / "locales" / locale
        locale_root.mkdir(parents=True)
        for relative, content in resources.items():
            path = locale_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf8")
            source_records.append(
                {
                    "path": f"locales/{locale}/{relative}",
                    "sha256": hashlib.sha256(content.encode()).hexdigest(),
                }
            )
    if manifest:
        compiled = package / "_compiled"
        compiled.mkdir()
        server_content = '{"schema_version":1}\n'
        (compiled / "server.json").write_text(server_content, encoding="utf8")
        (compiled / "manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "owner": "demo",
                    "source_locale": "en-US",
                    "sources": sorted(source_records, key=lambda item: item["path"]),
                    "artifacts": {
                        "server.json": {
                            "sha256": hashlib.sha256(server_content.encode()).hexdigest(),
                        }
                    },
                },
                separators=(",", ":"),
            ),
            encoding="utf8",
        )


def test_package_translation_owner_fallback_and_application_override(tmp_path, monkeypatch):
    name = "demo_catalog_package"
    _write_package(
        tmp_path,
        name,
        locales={
            "en-US": {
                "common.ftl": (
                    "# @param {str} $name - User name.\n"
                    "demo-greeting = Library hello, { $name }.\n"
                    "demo-source-only = English only\n"
                )
            },
            "cs-CZ": {"common.ftl": "demo-greeting = Ahoj, { $name }.\n"},
        },
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    app = Citry(
        mode="development",
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
                "catalogs": (name,),
            }
        },
    )

    class Page(Component):
        citry = app
        messages = "demo-greeting = Application hello, { $name }."
        template = '{{ tr("demo-greeting", name=name) }} / {{ tr("demo-source-only") }}'

        class Kwargs:
            name: str

    i18n = app.extensions.get_extension("i18n")
    english = {"citry_i18n": i18n.make_context(locale="en-US")}
    czech = {"citry_i18n": i18n.make_context(locale="cs-CZ")}
    assert str(Page(name="Ada").render(provides=english)) == ("Application hello, \u2068Ada\u2069. / English only")
    # Locale-major lookup chooses the library's Czech translation before
    # considering the application's English-only override.
    assert str(Page(name="Ada").render(provides=czech)) == "Ahoj, \u2068Ada\u2069. / English only"


def test_matching_library_catalog_owns_exported_component_message_at_runtime(tmp_path, monkeypatch):
    name = "exported_library_catalog"
    _write_package(
        tmp_path,
        name,
        locales={
            "en-US": {"common.ftl": "# @param {str} $name - User name.\ndemo-greeting = Packaged hello, { $name }.\n"}
        },
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    app = Citry(
        mode="development",
        autodiscover=False,
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US",),
                "catalogs": (name,),
            }
        },
    )

    class CGreeting(LibraryComponent):
        messages = "# @param {str} $name - User name.\ndemo-greeting = Authored hello, { $name }."

    app.register_library(ComponentLibrary("demo", (CGreeting,)))
    i18n = app.extensions.get_extension("i18n")

    assert i18n.tr("demo-greeting", name="Ada") == "Packaged hello, \u2068Ada\u2069."


def test_new_development_engine_reads_updated_editable_catalog_source(tmp_path, monkeypatch):
    name = "editable_catalog_package"
    _write_package(
        tmp_path,
        name,
        locales={"en-US": {"common.ftl": "demo-status = One\n"}},
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    config = {
        "i18n": {
            "source_locale": "en-US",
            "locales": ("en-US",),
            "catalogs": (name,),
        }
    }

    first = Citry(mode="development", autodiscover=False, extensions_defaults=config)
    assert first.extensions.get_extension("i18n").tr("demo-status") == "One"

    source = tmp_path / name / "locales" / "en-US" / "common.ftl"
    source.write_text("demo-status = Two\n", encoding="utf8")
    importlib.invalidate_caches()
    second = Citry(mode="development", autodiscover=False, extensions_defaults=config)
    assert second.extensions.get_extension("i18n").tr("demo-status") == "Two"


def test_package_owned_format_profiles_load_in_development_and_production(tmp_path, monkeypatch):
    name = "formatted_catalog_package"
    _write_package(
        tmp_path,
        name,
        locales={"en-US": {"common.ftl": "demo-count = Count\n"}},
        formats={"number": {"demo-count": {"input": {"notation": "decimal"}}}},
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    config = {
        "i18n": {
            "source_locale": "en-US",
            "locales": ("en-US",),
            "catalogs": (name,),
        }
    }

    development = Citry(mode="development", extensions_defaults=config)
    service = development.extensions.get_extension("i18n")
    formatter = service.for_context(service.make_context(locale="en-US")).format
    assert formatter.number(Decimal("1234.5"), format="demo-count") == "1,234.5"

    compile_catalog_package(name)
    production = Citry(mode="production", extensions_defaults=config)
    service = production.extensions.get_extension("i18n")
    formatter = service.for_context(service.make_context(locale="en-US")).format
    assert formatter.number(Decimal("1234.5"), format="demo-count") == "1,234.5"


def test_package_format_profiles_are_namespaced_and_cannot_replace_application_profiles(tmp_path, monkeypatch):
    name = "colliding_format_catalog_package"
    _write_package(
        tmp_path,
        name,
        locales={"en-US": {"common.ftl": "demo-count = Count\n"}},
        formats={"number": {"count": {}}},
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    config = {
        "i18n": {
            "source_locale": "en-US",
            "locales": ("en-US",),
            "catalogs": (name,),
        }
    }
    with pytest.raises(ValueError, match="must start with the package namespace 'demo-'"):
        Citry(mode="development", extensions_defaults=config)

    (tmp_path / name / "formats.json").write_text(
        json.dumps({"number": {"demo-count": {}}}),
        encoding="utf8",
    )
    importlib.invalidate_caches()
    config["i18n"]["formats"] = FormatRegistry(number={"demo-count": NumberFormat()})
    with pytest.raises(ValueError, match="collides with application"):
        Citry(mode="development", extensions_defaults=config)


def test_production_package_requires_and_validates_manifest(tmp_path, monkeypatch):
    name = "production_catalog_package"
    _write_package(
        tmp_path,
        name,
        locales={"en-US": {"common.ftl": "demo-title = Title\n"}},
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    config = {
        "i18n": {
            "source_locale": "en-US",
            "locales": ("en-US",),
            "catalogs": (name,),
        }
    }
    with pytest.raises(ValueError, match=r"manifest\.json"):
        Citry(mode="production", extensions_defaults=config)

    compile_catalog_package(name)
    # Production consumes the checked link unit. Authored FTL may be excluded
    # from the installed wheel once the package has been compiled.
    (tmp_path / name / "locales").rename(tmp_path / name / "authored-sources-not-installed")
    importlib.invalidate_caches()
    app = Citry(mode="production", extensions_defaults=config)
    i18n = app.extensions.get_extension("i18n")
    assert i18n.tr("demo-title") == "Title"
    artifact = json.loads(i18n._compiled_catalog.artifact_json())
    assert artifact["stats"]["parsed_catalogs"] == 0


def test_production_rejects_a_hash_valid_but_semantically_fake_server_artifact(tmp_path, monkeypatch):
    name = "tampered_catalog_package"
    _write_package(
        tmp_path,
        name,
        locales={"en-US": {"common.ftl": "demo-title = Title\n"}},
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    compile_catalog_package(name)
    package = tmp_path / name
    fake = '{"schema_version":1}\n'
    (package / "_compiled" / "server.json").write_text(fake, encoding="utf8")
    manifest_path = package / "_compiled" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf8"))
    manifest["artifacts"]["server.json"]["sha256"] = hashlib.sha256(fake.encode()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, separators=(",", ":")), encoding="utf8")

    with pytest.raises(ValueError, match="does not match its checked link artifact"):
        Citry(
            mode="production",
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                    "catalogs": (name,),
                }
            },
        )


def test_production_rejects_a_hash_valid_but_stale_link_revision(tmp_path, monkeypatch):
    name = "tampered_link_catalog_package"
    _write_package(
        tmp_path,
        name,
        locales={"en-US": {"common.ftl": "demo-title = Title\n"}},
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    compile_catalog_package(name)
    package = tmp_path / name
    link_path = package / "_compiled" / "link.json"
    link = json.loads(link_path.read_text(encoding="utf8"))
    link["revision"] = "forged"
    link_text = json.dumps(link, separators=(",", ":"), sort_keys=True) + "\n"
    link_path.write_text(link_text, encoding="utf8")
    manifest_path = package / "_compiled" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf8"))
    manifest["artifacts"]["link.json"]["sha256"] = hashlib.sha256(link_text.encode()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, separators=(",", ":")), encoding="utf8")

    with pytest.raises(ValueError, match="semantic revision"):
        Citry(
            mode="production",
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                    "catalogs": (name,),
                }
            },
        )


def test_production_rejects_malformed_link_catalog_metadata(tmp_path, monkeypatch):
    name = "malformed_link_catalog_package"
    _write_package(
        tmp_path,
        name,
        locales={"en-US": {"common.ftl": "demo-title = Title\n"}},
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    compile_catalog_package(name)
    package = tmp_path / name
    link_path = package / "_compiled" / "link.json"
    link = json.loads(link_path.read_text(encoding="utf8"))
    link["catalogs"][0]["path"] = "missing-package-prefix.ftl"
    link_text = json.dumps(link, separators=(",", ":"), sort_keys=True) + "\n"
    link_path.write_text(link_text, encoding="utf8")
    manifest_path = package / "_compiled" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf8"))
    manifest["artifacts"]["link.json"]["sha256"] = hashlib.sha256(link_text.encode()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, separators=(",", ":")), encoding="utf8")

    with pytest.raises(ValueError, match="unsupported catalog metadata"):
        Citry(
            mode="production",
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                    "catalogs": (name,),
                }
            },
        )


def test_catalog_resources_load_from_zip_import_package(tmp_path, monkeypatch):
    source_root = tmp_path / "source"
    source_root.mkdir()
    name = "zipped_catalog_package"
    _write_package(
        source_root,
        name,
        locales={"en-US": {"nested/common.ftl": "demo-zipped = From zip\n"}},
    )
    archive = tmp_path / "catalogs.zip"
    with zipfile.ZipFile(archive, "w") as output:
        for path in sorted((source_root / name).rglob("*")):
            if path.is_file():
                output.write(path, f"{name}/{path.relative_to(source_root / name).as_posix()}")
    monkeypatch.syspath_prepend(str(archive))
    importlib.invalidate_caches()
    sys.modules.pop(name, None)
    app = Citry(
        mode="development",
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US",),
                "catalogs": (name,),
            }
        },
    )
    assert app.extensions.get_extension("i18n").tr("demo-zipped") == "From zip"


def test_source_free_production_link_unit_loads_from_a_zip_package(tmp_path, monkeypatch):
    source_root = tmp_path / "source"
    source_root.mkdir()
    name = "zipped_compiled_catalog_package"
    _write_package(
        source_root,
        name,
        locales={"en-US": {"common.ftl": "demo-zipped = From compiled zip\n"}},
    )
    monkeypatch.syspath_prepend(str(source_root))
    importlib.invalidate_caches()
    compile_catalog_package(name)
    (source_root / name / "locales").rename(source_root / name / "sources-not-in-wheel")

    archive = tmp_path / "compiled-catalogs.zip"
    with zipfile.ZipFile(archive, "w") as output:
        for path in sorted((source_root / name).rglob("*")):
            if path.is_file() and "sources-not-in-wheel" not in path.parts:
                output.write(path, f"{name}/{path.relative_to(source_root / name).as_posix()}")
    monkeypatch.syspath_prepend(str(archive))
    sys.path.remove(str(source_root))
    importlib.invalidate_caches()
    sys.modules.pop(name, None)

    app = Citry(
        mode="production",
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US",),
                "catalogs": (name,),
            }
        },
    )
    assert app.extensions.get_extension("i18n").tr("demo-zipped") == "From compiled zip"


def test_locale_directories_must_use_canonical_spelling(tmp_path, monkeypatch):
    name = "invalid_locale_catalog_package"
    _write_package(
        tmp_path,
        name,
        locales={"EN-us": {"common.ftl": "demo-title = Title\n"}},
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    with pytest.raises(ValueError, match="canonical spelling 'en-US'"):
        Citry(
            mode="development",
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                    "catalogs": (name,),
                }
            },
        )


def test_compile_command_writes_checked_manifest_and_server_artifact(tmp_path, monkeypatch):
    name = "compiled_catalog_package"
    _write_package(
        tmp_path,
        name,
        locales={
            "en-US": {"common.ftl": "demo-title = Title\n"},
            "cs-CZ": {"common.ftl": "demo-title = Titulek\n"},
        },
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    config = {
        "i18n": {
            "source_locale": "en-US",
            "locales": ("en-US", "cs-CZ"),
            "catalogs": (name,),
        }
    }
    development = Citry(mode="development", extensions_defaults=config)

    assert run(CompileI18nCommand, [], citry=development) == 0
    manifest = json.loads((tmp_path / name / "_compiled" / "manifest.json").read_text(encoding="utf8"))
    artifact = json.loads((tmp_path / name / "_compiled" / "server.json").read_text(encoding="utf8"))
    assert manifest["artifacts"]["server.json"]["sha256"]
    assert manifest["artifacts"]["link.json"]["sha256"]
    assert artifact["schema_version"] == 1

    production = Citry(mode="production", extensions_defaults=config)

    class Page(Component):
        citry = production
        messages = "demo-title = Application title\n"

    production_i18n = production.extensions.get_extension("i18n")
    context = production_i18n.make_context(locale="cs-CZ")
    assert production_i18n.for_context(context).tr("demo-title") == "Titulek"
    english = production_i18n.make_context(locale="en-US")
    assert production_i18n.for_context(english).tr("demo-title") == "Application title"


def test_project_commands_check_extract_and_inspect_the_same_catalog(tmp_path, capsys):
    app = Citry(
        mode="development",
        autodiscover=False,
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US",),
            }
        },
    )

    class Page(Component):
        citry = app
        messages = "demo-title = Title\n"

    assert run(CheckI18nCommand, [], citry=app) == 0
    checked = json.loads(capsys.readouterr().out)
    assert checked["schema_version"] == 1
    assert checked["catalog_revision"]
    assert checked["formats_revision"]

    assert run(ExtractI18nCommand, [], citry=app) == 0
    extracted = json.loads(capsys.readouterr().out)
    assert extracted["schema_version"] == 1
    assert extracted["sources"] == [
        {
            "locale": "en-US",
            "package": "__citry_application__",
            "path": f"{Path(__file__).resolve()}::Page.messages",
        }
    ]

    artifact_path = tmp_path / "i18n-artifact.json"
    assert run(InspectI18nCommand, ["--out", str(artifact_path)], citry=app) == 0
    assert "Wrote the checked i18n artifact" in capsys.readouterr().out
    artifact = json.loads(artifact_path.read_text(encoding="utf8"))
    assert artifact["revision"] == checked["catalog_revision"]
    assert artifact["manifest"]["en-US"]["demo-title"]["selected_path"] == extracted["sources"][0]["path"]


def test_coverage_command_reports_exact_and_source_fallback_outputs(capsys):
    app = Citry(
        autodiscover=False,
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
            }
        },
    )

    class Page(Component):
        citry = app
        messages = "demo-title = Title\n    .aria-label = Page title\n"

    assert run(CoverageI18nCommand, ["--locale", "CS-cz", "--json"], citry=app) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["schema_version"] == 1
    assert report["locales"] == [
        {
            "locale": "cs-CZ",
            "summary": {"exact": 0, "source_fallback": 2, "translation_fallback": 0},
            "outputs": [
                {
                    "definition_path": f"{Path(__file__).resolve()}::Page.messages",
                    "output": "demo-title",
                    "owner": "__citry_application__",
                    "owner_source_locale": "en-US",
                    "selected_locale": "en-US",
                    "status": "source_fallback",
                },
                {
                    "definition_path": f"{Path(__file__).resolve()}::Page.messages",
                    "output": "demo-title.aria-label",
                    "owner": "__citry_application__",
                    "owner_source_locale": "en-US",
                    "selected_locale": "en-US",
                    "status": "source_fallback",
                },
            ],
        }
    ]

    assert run(CoverageI18nCommand, ["--locale", "en-US"], citry=app) == 0
    assert "en-US: 2 exact, 0 translation fallback, 0 source fallback" in capsys.readouterr().out
    with pytest.raises(SystemExit) as failure:
        run(CoverageI18nCommand, ["--locale", "cs-CZ", "--fail-on-missing"], citry=app)
    assert failure.value.code == 1
    assert "demo-title: source fallback via en-US" in capsys.readouterr().out


def test_coverage_command_runs_in_zero_configuration_source_mode(capsys):
    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app

        class I18n:
            messages_locale = "en-US"

        messages = "demo-title = Title\n"

    assert run(CoverageI18nCommand, ["--json"], citry=app) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["locales"][0]["locale"] == "en-US"
    assert report["locales"][0]["summary"] == {
        "exact": 1,
        "source_fallback": 0,
        "translation_fallback": 0,
    }

    assert run(CheckI18nCommand, [], citry=app) == 0
    assert json.loads(capsys.readouterr().out)["schema_version"] == 1
    assert run(ExtractI18nCommand, [], citry=app) == 0
    assert json.loads(capsys.readouterr().out)["sources"][0]["locale"] == "en-US"
    assert run(InspectI18nCommand, [], citry=app) == 0
    assert json.loads(capsys.readouterr().out)["manifest"]["en-US"]["demo-title"]
