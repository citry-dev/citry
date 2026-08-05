"""Tests for cross-reference resolution and the objects.inv inventory."""

from __future__ import annotations

import zlib

import yaml

from docs_site._internal.config import DocsConfig
from docs_site._internal.config import config as default_config
from docs_site._internal.crossrefs import (
    build_objects_inv,
    resolve_crossrefs,
    resolve_crossrefs_in_prose,
    symbol_url_index,
)
from docs_site._internal.pipeline import render_page
from docs_site._internal.project import load_docs_project, use_docs_project
from docs_site._internal.reference import _md


def test_index_has_symbols_and_members() -> None:
    index = symbol_url_index()
    assert index["citry.Component"] == "/reference/component/#citry-component"
    assert index["Component"] == index["citry.Component"]  # short-name alias
    assert index["citry.Component.State"] == ("/reference/component/#citry-component-state")
    assert index["citry.Component.Events"] == ("/reference/component/#citry-component-events")
    assert index["Component.template_data"] == "/reference/component/#citry-component-template-data"
    assert index["citry.Component.template_data"] == index["Component.template_data"]
    assert index["citry.Markup"] == "/reference/rendering/#citry-markup"
    assert index["citry.SecurityError"] == "/reference/rendering/#citry-securityerror"
    assert "citry.Markup.format" not in index
    assert "Markup.format" not in index
    assert index["c-slot"] == "/reference/builtins/#c-slot"
    assert index["c-component"] == "/reference/builtins/#c-component"
    assert index["$component"] == "/reference/browser-apis/#component"
    assert index["$state"] == "/reference/browser-apis/#state"
    assert index["Citry.events.send"] == ("/reference/browser-apis/#citry-events-send")


def test_ambiguous_generated_short_name_requires_a_qualified_key() -> None:
    index = symbol_url_index()

    assert "mount" not in index
    assert "citry.contrib.fastapi.mount" in index
    assert "citry.contrib.flask.mount" in index


def test_case_colliding_symbols_get_distinct_consistent_anchors() -> None:
    # The Citry class and the citry instance live on one page and slugify to the
    # same anchor; they must be disambiguated, and the cross-ref index must point
    # at exactly the ids the page renders (so a link never lands on the wrong one).
    from docs_site._internal.reference import reference_anchor_map

    anchors = reference_anchor_map()
    assert anchors["citry.Citry"] != anchors["citry.citry"]

    index = symbol_url_index()
    assert index["citry.Citry"].endswith("#" + anchors["citry.Citry"])
    assert index["citry.citry"].endswith("#" + anchors["citry.citry"])


def test_resolve_explicit_and_shorthand() -> None:
    md, unresolved = resolve_crossrefs("[the class][citry.Component] and [`Component`][]")
    assert md.count("(/reference/component/#citry-component)") == 2
    assert unresolved == []


def test_unknown_ref_degrades_to_text_in_docstrings() -> None:
    md, unresolved = resolve_crossrefs("[gone][citry.Nope]", degrade_unresolved=True)
    assert md == "gone"  # plain text, not a broken [x][y] literal
    assert unresolved == ["citry.Nope"]


def test_non_ref_brackets_survive_in_content() -> None:
    md, _ = resolve_crossrefs_in_prose("array indexing arr[i][j] stays put")
    assert "arr[i][j]" in md


def test_crossrefs_skip_fenced_code() -> None:
    src = "ref [`Component`][citry.Component]\n\n```\n[x][citry.Component]\n```\n"
    md, _ = resolve_crossrefs_in_prose(src)
    assert "(/reference/component/#citry-component)" in md  # the prose ref resolved
    assert "[x][citry.Component]" in md  # the fenced one was left alone


def test_content_page_links_to_reference() -> None:
    html = render_page("See [`Component`][citry.Component].").html
    assert 'href="/reference/component/#citry-component"' in html


def test_docstring_crossrefs_resolve() -> None:
    out = _md("See [the element][citry.CitryElement].")
    assert 'href="/reference/rendering/#citry-citryelement"' in out


def test_docstring_magic_links_use_configured_repository_identity(tmp_path) -> None:
    data = yaml.safe_load(default_config.settings_config.read_text(encoding="utf-8"))
    data["repository"].update(
        owner="acme",
        name="widgets",
        url="https://github.com/acme/widgets",
        issues_url="https://github.com/acme/widgets/issues",
    )
    data["markdown"]["docstrings"] = {
        "extensions": ["pymdownx.magiclink"],
        "extension_configs": {"pymdownx.magiclink": {"repo_url_shorthand": True}},
    }
    settings_path = tmp_path / "settings.yml"
    settings_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    project = load_docs_project(DocsConfig(settings_config=settings_path))

    with use_docs_project(project):
        output = _md("Issue #123")

    assert 'href="https://github.com/acme/widgets/issues/123"' in output


def test_objects_inv_is_a_valid_sphinx_v2_inventory() -> None:
    data = build_objects_inv("9.9.9")
    assert data.startswith(b"# Sphinx inventory version 2")
    assert b"# Version: 9.9.9" in data
    _, _, payload = data.partition(b"compressed using zlib.\n")
    lines = zlib.decompress(payload).decode().splitlines()
    assert any(line.startswith("citry.Component ") for line in lines)
    assert any(".template_data " in line for line in lines)  # a member entry
    roles = {line.split()[0]: line.split()[1] for line in lines}
    assert roles["citry.Component"] == "py:obj"
    assert roles["citry.Component.State"] == "py:obj"
    assert roles["citry.Component.Events"] == "py:obj"
    assert roles["citry.Markup"] == "py:obj"
    assert roles["citry.SecurityError"] == "py:obj"
    assert "citry.Markup.format" not in roles
    assert roles["c-slot"] == "py:obj"
    assert roles["$component"] == "js:function"
    assert roles["$state"] == "js:data"
