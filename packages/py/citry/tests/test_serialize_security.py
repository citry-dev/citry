"""Focused security metadata, SRI, and trusted-tag reconciliation tests."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import warnings
from typing import TYPE_CHECKING
from urllib.parse import quote, quote_from_bytes

import pytest

from citry import Citry, Component, Extension, Markup
from citry.ext.dependencies import Script, Style
from citry.util.html import (
    decode_attribute_entities,
    decode_character_references,
    escape,
    escape_attribute_value,
    escape_to_str,
)
from citry.util.routing import match_route

if TYPE_CHECKING:
    from pathlib import Path


def _sha384(body: bytes) -> str:
    encoded = base64.b64encode(hashlib.sha384(body).digest()).decode("ascii")
    return f"sha384-{encoded}"


def _manifest(html: str) -> dict[str, object]:
    match = re.search(
        r'<script\b[^>]*\bdata-citry(?:=""|(?=\s|>))[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match is not None
    return json.loads(match.group(1))


def test_strict_csp_validates_exact_opaque_html_payload_before_publication() -> None:
    app = Citry(autodiscover=False, security_csp="strict")

    class UnsafeOpaque(Component):
        citry = app
        template = "{{ body }}"
        js = "$component({data(){return {active: true};}});"

        def template_data(self, kwargs, slots):
            return {"body": Markup('<img src="missing" onerror="globalThis.pwned=true">')}

    with pytest.raises(ValueError, match="strict-CSP incompatibility"):
        UnsafeOpaque().render().serialize()


def test_revisable_app_rejects_policy_drift_before_a_later_opaque_revision() -> None:
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")

    class OpaqueEvent(Component):
        citry = app
        template = '<button @c-click="refresh">refresh</button>{{ body }}'

        class Events:
            def refresh(self):
                return None

        def template_data(self, kwargs, slots):
            return {"body": "initially plain text"}

    with pytest.raises(ValueError, match="Call-local JavaScript/CSP overrides"):
        OpaqueEvent().render().serialize(security_csp="strict", csp_nonce="request-nonce")


def _fetch_descriptors(html: str, kind: str) -> list[dict[str, object]]:
    manifest = _manifest(html)
    fetch = manifest["fetch"]
    assert isinstance(fetch, dict)
    entries = fetch[kind]
    assert isinstance(entries, list)
    descriptors = []
    for entry in entries:
        encoded = entry[0] if isinstance(entry, list) else entry
        descriptors.append(json.loads(base64.b64decode(encoded)))
    return descriptors


def _vue_fragment(html: str) -> dict[str, object]:
    match = re.search(r"<script\b[^>]*data-citry-vue-fragment[^>]*>(.*?)</script>", html, re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))["vue"]


def _prepared(html: str) -> dict[str, object]:
    match = re.search(
        r'<script type="application/json" data-citry-vue-document="[^"]*"[^>]*>(.*?)</script>', html, re.DOTALL
    )
    assert match is not None
    return json.loads(match.group(1))


def _serve(citry: Citry, url: str):
    prefix = f"{citry.mounted_prefix}/"
    matched = match_route(citry.urls, url.removeprefix(prefix))
    assert matched is not None
    return matched.route.handler(None, **matched.params)


class TestInlineMetadata:
    def test_hashes_exact_wrapped_classic_content(self):
        c = Citry(security_script_integrity="citry")

        class Card(Component):
            citry = c
            template = "<p>card</p>"
            js = "console.log('card');"

        result = Card().render().serialize_result(deps_strategy="simple")
        rendered_content = "(function() {\nconsole.log('card');\n})();"
        digest = _sha384(rendered_content.encode())

        assert f"<script>{rendered_content}</script>" in result.html
        assert result.security.scripts[0].digests == (digest,)
        assert result.security.csp_script_hashes == (f"'{digest}'",)

    def test_module_is_hashed_without_classic_wrapper(self):
        module = Script(content="export const answer = 42;", attrs={"type": "module"})
        c = Citry(security_script_integrity="citry")

        class Card(Component):
            citry = c
            template = "<p>card</p>"

            class Dependencies:
                js = [module]

        result = Card().render().serialize_result(deps_strategy="simple")
        digest = _sha384(b"export const answer = 42;")

        assert '<script type="module">export const answer = 42;</script>' in result.html
        assert result.security.csp_script_hashes == (f"'{digest}'",)

    def test_inert_json_is_recorded_but_not_a_csp_source(self):
        class DataBlock(Extension):
            name = "data_block"

            def on_dependencies(self, ctx):
                ctx.scripts.append(Script(content='{"ready":true}', attrs={"type": "application/json"}))

        c = Citry(extensions=[DataBlock], security_script_integrity="citry")

        class Card(Component):
            citry = c
            template = "<p>card</p>"

        result = Card().render().serialize_result(deps_strategy="simple")

        assert result.security.scripts[0].digests == (_sha384(b'{"ready":true}'),)
        assert result.security.csp_script_hashes == ()

    def test_script_attribute_identity_is_ascii_case_insensitive(self):
        c = Citry(security_script_integrity="citry")

        class DataBlock(Component):
            citry = c
            template = "<p>data</p>"

            class Dependencies:
                js = [Script(content='{"ready":true}', attrs={"TYPE": "application/json"})]

        result = DataBlock().render().serialize_result(deps_strategy="simple")

        assert '<script type="application/json">' in result.html
        assert result.security.csp_script_hashes == ()

    def test_src_casing_cannot_turn_inline_metadata_into_an_external_fetch(self):
        c = Citry(security_script_integrity="citry")

        class Card(Component):
            citry = c
            template = "<p>card</p>"

            class Dependencies:
                js = [Script(content="safe()", attrs={"SRC": "https://evil.example/x.js"}, wrap=False)]

        with pytest.raises(ValueError, match=r"Script\(url="):
            Card().render().serialize_result(deps_strategy="simple")

    def test_duplicate_attribute_casing_is_rejected(self):
        class SplitScript(Script):
            def _render(self):
                return "script", {"type": "module", "TYPE": "application/json"}, "safe()"

        c = Citry(security_script_integrity="citry")

        class Card(Component):
            citry = c
            template = "<p>card</p>"

            class Dependencies:
                js = [SplitScript(content="safe()")]

        with pytest.raises(ValueError, match="type attribute more than once"):
            Card().render().serialize_result(deps_strategy="simple")

    def test_materializes_custom_script_once_and_ignores_split_render_overrides(self):
        class StatefulScript(Script):
            calls = 0

            def _render(self):
                # Count on the class: emission renders its own copy of the
                # declared entry, so the declared object itself is never rendered.
                type(self).calls += 1
                return super()._render()

            def render(self):
                raise AssertionError("secure emission must use the captured representation")

            def render_json(self):
                raise AssertionError("secure emission must use the captured representation")

        script = StatefulScript(content="globalThis.once = true;", wrap=False)
        c = Citry(security_script_integrity="citry")

        class Card(Component):
            citry = c
            template = "<p>card</p>"

            class Dependencies:
                js = [script]

        result = Card().render().serialize_result(deps_strategy="simple")

        assert "globalThis.once = true;" in result.html
        assert StatefulScript.calls == 1

    @pytest.mark.parametrize("strategy", ["simple", "fragment"])
    def test_same_script_identity_materializes_once_after_a_global_hook(self, strategy):
        class StatefulScript(Script):
            calls = 0

            def _render(self):
                self.calls += 1
                return super()._render()

        script = StatefulScript(content="globalThis.once = true;", wrap=False)

        class DuplicateStructured(Extension):
            name = "duplicate_structured"

            def on_dependencies(self, ctx):
                ctx.scripts.extend([script, script])

        c = Citry(extensions=[DuplicateStructured], security_script_integrity="citry")
        if strategy == "fragment":
            c.set_mounted_prefix("/citry")

        class Card(Component):
            citry = c
            template = "<p>card</p>"

        result = Card().render().serialize_result(deps_strategy=strategy)

        assert script.calls == 1
        assert len(result.security.scripts) >= 2


class TestExternalIntegrity:
    def test_third_party_declared_integrity_is_preserved_without_fetching(self):
        digest = _sha384(b"third party bytes")
        script = Script(
            url="https://cdn.example.test/chart.js",
            attrs={"crossorigin": "anonymous", "integrity": digest},
        )
        c = Citry(security_script_integrity="citry")

        class Chart(Component):
            citry = c
            template = "<p>chart</p>"

            class Dependencies:
                js = [script]

        result = Chart().render().serialize_result(deps_strategy="simple")

        assert 'crossorigin="anonymous"' in result.html
        assert f'integrity="{digest}"' in result.html
        assert len(result.security.scripts) == 1
        assert result.security.scripts[0].provenance == "declared-unverified"
        assert result.security.csp_script_hashes == (f"'{digest}'",)

    def test_third_party_without_declared_integrity_is_not_claimed(self):
        c = Citry(security_script_integrity="citry")

        class Chart(Component):
            citry = c
            template = "<p>chart</p>"

            class Dependencies:
                js = ["https://cdn.example.test/chart.js"]

        result = Chart().render().serialize_result(deps_strategy="simple")

        assert "integrity=" not in result.html
        assert result.security.scripts == ()

    def test_locally_served_script_integrity_matches_route_body(self, tmp_path: Path):
        source = tmp_path / "chart.js"
        source.write_text("globalThis.chart = true;", encoding="utf-8")
        c = Citry(security_script_integrity="citry")
        c.set_mounted_prefix("/citry")

        class Chart(Component):
            citry = c
            template = "<p>chart</p>"

            class Dependencies:
                js = [source]
                local_files = "serve"

        result = Chart().render().serialize_result(deps_strategy="simple")
        script = result.security.scripts[0]
        assert script.url is not None
        response = _serve(c, script.url)
        digest = _sha384(response.body)

        assert script.digests == (digest,)
        assert f'integrity="{digest}"' in result.html

    def test_vue_fragment_preloader_uses_owned_integrity(self):
        c = Citry(security_script_integrity="citry")
        c.set_mounted_prefix("/citry")

        class Widget(Component):
            citry = c
            template = "<p>widget</p>"
            js = "$component(() => {});"

            def js_data(self, kwargs, slots):
                return {"count": 2}

        result = Widget().render().serialize_result(deps_strategy="fragment")
        runtime_digest = _sha384(_serve(c, "/citry/citry.js").body)
        assert f's.integrity = "{runtime_digest}";' in result.html
        prepared = _vue_fragment(result.html)["prepared"]
        assert prepared["manifest"]["scripts"][0]["source"]["sha256"]
        assert result.security.scripts[0].location == "inline"
        assert result.security.scripts[1].url == "/citry/citry.js"

    def test_mounted_document_runtimes_match_their_route_bodies(self):
        c = Citry(security_script_integrity="citry")
        c.set_mounted_prefix("/citry")

        class Widget(Component):
            citry = c
            template = '<button @click="open = true">open</button>'

        result = Widget().render().serialize_result()

        for url in ("/citry/citry.js",):
            record = next(script for script in result.security.scripts if script.url == url)
            digest = _sha384(_serve(c, url).body)
            assert record.digests == (digest,)
            assert f'src="{url}" integrity="{digest}"' in result.html

    def test_owned_multiple_declared_algorithms_are_verified(self, tmp_path: Path):
        source = tmp_path / "owned.js"
        source.write_text("globalThis.owned = true;", encoding="utf-8")

        class DeclareDigests(Extension):
            name = "declare_digests"

            def on_dependencies(self, ctx):
                owned = next(
                    script
                    for script in ctx.scripts
                    if isinstance(script, Script) and script._owned_resource is not None
                )
                body = owned._owned_resource.body
                sha256 = f"sha256-{base64.b64encode(hashlib.sha256(body).digest()).decode('ascii')}"
                sha512 = f"sha512-{base64.b64encode(hashlib.sha512(body).digest()).decode('ascii')}"
                owned.attrs["integrity"] = f"{sha256} {sha512}"

        c = Citry(extensions=[DeclareDigests], security_script_integrity="citry")
        c.set_mounted_prefix("/citry")

        class Widget(Component):
            citry = c
            template = "<p>widget</p>"

            class Dependencies:
                js = [source]
                local_files = "serve"

        result = Widget().render().serialize_result(deps_strategy="simple")
        record = result.security.scripts[0]

        assert record.provenance == "declared-verified"
        assert {digest.partition("-")[0] for digest in record.digests} == {"sha256", "sha384", "sha512"}

    def test_static_fragment_served_dependency_integrity_matches_owned_bytes(self, tmp_path: Path):
        source = tmp_path / "owned.js"
        source.write_text("globalThis.owned = true;", encoding="utf-8")
        c = Citry(dirs=[tmp_path], security_script_integrity="citry")
        c.set_mounted_prefix("/citry")

        class Widget(Component):
            citry = c
            template = "<p>widget</p>"

            class Dependencies:
                js = [source]
                local_files = "serve"

        result = Widget().render().serialize_result(deps_strategy="fragment")
        record = next(item for item in result.security.scripts if item.url)
        assert record.digests == (_sha384(_serve(c, record.url).body),)
        assert "data-citry-vue-fragment" not in result.html

    def test_owned_declared_integrity_mismatch_fails(self, tmp_path: Path):
        bad = _sha384(b"not the owned body")
        source = tmp_path / "owned.js"
        source.write_text("globalThis.owned = true;", encoding="utf-8")

        class DeclareWrongDigest(Extension):
            name = "declare_wrong_digest"

            def on_dependencies(self, ctx):
                for script in ctx.scripts:
                    if isinstance(script, Script) and script._owned_resource is not None:
                        script.attrs["integrity"] = bad

        c = Citry(
            dirs=[tmp_path],
            extensions=[DeclareWrongDigest],
            extensions_defaults={"dependencies": {"local_files": "serve"}},
            security_script_integrity="citry",
        )
        c.set_mounted_prefix("/citry")

        class Widget(Component):
            citry = c
            template = "<p>widget</p>"

            class Dependencies:
                js = [source]

        with pytest.raises(ValueError, match="does not match the Citry-owned bytes"):
            Widget().render().serialize_result(deps_strategy="fragment")

    @pytest.mark.parametrize(
        "value",
        [True, "sha1-deadbeef", "sha384-not-base64", f"{_sha384(b'bytes')}?"],
    )
    def test_malformed_declared_integrity_fails(self, value):
        script = Script(url="https://cdn.example.test/chart.js", attrs={"integrity": value})
        c = Citry(security_script_integrity="citry")

        class Chart(Component):
            citry = c
            template = "<p>chart</p>"

            class Dependencies:
                js = [script]

        with pytest.raises(ValueError, match="integrity"):
            Chart().render().serialize_result(deps_strategy="simple")


class TestTrustedTagReconciliation:
    def test_later_string_hook_cannot_edit_a_trusted_script(self):
        class EditScript(Extension):
            name = "edit_script"

            def on_serialize(self, ctx):
                return ctx.html.replace("console.log('safe')", "console.log('changed')")

        c = Citry(extensions=[EditScript], security_script_integrity="citry")

        class Card(Component):
            citry = c
            template = "<p>card</p>"
            js = "console.log('safe')"

        with pytest.raises(RuntimeError, match="on_dependencies"):
            Card().render().serialize_result(deps_strategy="simple")

    def test_later_string_hook_cannot_duplicate_a_trusted_script(self):
        class Duplicate(Extension):
            name = "duplicate"

            def on_serialize(self, ctx):
                return ctx.html + ctx.html

        c = Citry(extensions=[Duplicate], security_script_integrity="citry")

        class Card(Component):
            citry = c
            template = "<p>card</p>"
            js = "console.log('safe')"

        with pytest.raises(RuntimeError, match="on_dependencies"):
            Card().render().serialize_result(deps_strategy="simple")

    def test_later_string_hook_cannot_remove_or_edit_a_trusted_script_attribute(self):
        class RemoveMarkerBearingTag(Extension):
            name = "remove_marker_bearing_tag"

            def on_serialize(self, ctx):
                return re.sub(r"<script[^>]*>.*?</script>", "", ctx.html, count=1, flags=re.DOTALL)

        c = Citry(extensions=[RemoveMarkerBearingTag], security_script_integrity="citry")

        class Card(Component):
            citry = c
            template = "<p>card</p>"
            js = "console.log('safe')"

        with pytest.raises(RuntimeError, match="on_dependencies"):
            Card().render().serialize_result(deps_strategy="simple")

    def test_unrelated_string_edits_and_intact_movement_remain_allowed(self):
        class Wrap(Extension):
            name = "wrap"

            def on_serialize(self, ctx):
                return f"<main>{ctx.html}</main>"

        c = Citry(extensions=[Wrap], security_script_integrity="citry")

        class Card(Component):
            citry = c
            template = "<p>card</p>"
            js = "console.log('safe')"

        result = Card().render().serialize_result(deps_strategy="simple")

        assert result.html.startswith("<main>")
        assert "data-citry-security-" not in result.html

    def test_opaque_prerendered_script_is_rejected_only_when_enabled(self):
        off = Citry()

        class Card(Component):
            citry = off
            template = "<p>card</p>"

            class Dependencies:
                js = [Markup("<script>globalThis.opaque = true;</script>")]

        assert "globalThis.opaque" in Card().render().serialize(deps_strategy="simple")

        strict = Citry(security_script_integrity="citry")

        class StrictCard(Component):
            citry = strict
            template = "<p>card</p>"

            class Dependencies:
                js = [Markup("<script>globalThis.opaque = true;</script>")]

        with pytest.raises(TypeError, match="Script objects"):
            StrictCard().render().serialize_result(deps_strategy="simple")


class TestCspNonce:
    @pytest.mark.parametrize("nonce", ["abc", "abc=", "abc==", "Ab9+/_-z"])
    def test_accepts_csp_base64_and_base64url_values(self, nonce):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>card</p>"
            js = "globalThis.card = true;"

        html = Card().render().serialize(csp_nonce=nonce, deps_strategy="simple")

        assert f'nonce="{nonce}"' in html

    @pytest.mark.parametrize("nonce", ["", b"abc", True, "abc ", "abc'", "abc===", "=abc"])
    def test_rejects_invalid_nonce_values_before_emission(self, nonce):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>card</p>"

        with pytest.raises(ValueError, match="Invalid csp_nonce"):
            Card().render().serialize(csp_nonce=nonce)

    def test_nonces_structured_scripts_and_stylesheets_but_not_raw_markup(self):
        nonce = "requestNonce123=="
        c = Citry()

        class Card(Component):
            citry = c
            template = "<main><script>rawScript()</script><style>.raw{color:red}</style></main>"
            js = "globalThis.componentScript = true;"
            css = ".component { color: blue; }"

            class Dependencies:
                js = [Script(url="https://cdn.example.test/chart.js")]
                css = [Style(url="https://cdn.example.test/chart.css")]

        result = Card().render().serialize_result(deps_strategy="simple", csp_nonce=nonce)

        assert "<script>rawScript()</script>" in result.html
        assert "<style>.raw{color:red}</style>" in result.html
        assert f'<script nonce="{nonce}">' in result.html
        assert f'src="https://cdn.example.test/chart.js" nonce="{nonce}"' in result.html
        assert re.search(rf'<style\b[^>]*nonce="{re.escape(nonce)}"', result.html)
        assert f'<link rel="stylesheet" href="https://cdn.example.test/chart.css" nonce="{nonce}"/>' in result.html
        assert result.security.scripts == ()
        assert result.security.csp_script_hashes == ()

    def test_repeated_serialization_uses_fresh_nonce_state_without_mutating_dependencies(self):
        script = Script(content="globalThis.shared = true;", attrs={"data-shared": True}, wrap=False)
        style = Style(content=".shared { display: block; }")
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>card</p>"

            class Dependencies:
                js = [script]
                css = [style]

        rendered = Card().render()
        first = rendered.serialize(deps_strategy="simple", csp_nonce="firstNonce")
        second = rendered.serialize(deps_strategy="simple", csp_nonce="secondNonce")

        assert 'nonce="firstNonce"' in first
        assert "secondNonce" not in first
        assert 'nonce="secondNonce"' in second
        assert "firstNonce" not in second
        assert script.attrs == {"data-shared": True}
        assert style.attrs == {}

    def test_matching_explicit_nonce_is_canonicalized_and_conflicts_fail(self):
        matching = Script(content="globalThis.matching = true;", attrs={"NONCE": "sameNonce"}, wrap=False)
        c = Citry()

        class Matching(Component):
            citry = c
            template = "<p>matching</p>"

            class Dependencies:
                js = [matching]

        html = Matching().render().serialize(deps_strategy="simple", csp_nonce="sameNonce")
        assert 'nonce="sameNonce"' in html
        assert "NONCE=" not in html

        conflicting = Script(content="globalThis.matching = true;", attrs={"nonce": "oldNonce"}, wrap=False)

        class Conflicting(Component):
            citry = c
            template = "<p>conflicting</p>"

            class Dependencies:
                js = [matching]

            @classmethod
            def on_dependencies(cls, scripts, styles):
                # The hook contributes an equal-content second entry. The
                # pre-deduplication check must still inspect its stale nonce.
                scripts.append(conflicting)

        with pytest.raises(ValueError, match="differs from this serialization"):
            Conflicting().render().serialize(deps_strategy="simple", csp_nonce="sameNonce")

    @pytest.mark.parametrize("strategy", ["simple", "fragment"])
    def test_global_hook_conflict_cannot_hide_behind_dependency_deduplication(self, strategy):
        first = Script(content="globalThis.equal = true;", attrs={"nonce": "sameNonce"}, wrap=False)
        conflicting = Script(content="globalThis.equal = true;", attrs={"nonce": "oldNonce"}, wrap=False)

        class AddEqualConflict(Extension):
            name = "add_equal_conflict"

            def on_dependencies(self, ctx):
                ctx.scripts.append(conflicting)

        c = Citry(extensions=[AddEqualConflict])
        if strategy == "fragment":
            c.set_mounted_prefix("/citry")

        class Card(Component):
            citry = c
            template = "<p>card</p>"

            class Dependencies:
                js = [first]

        with pytest.raises(ValueError, match="differs from this serialization"):
            Card().render().serialize(deps_strategy=strategy, csp_nonce="sameNonce")

    @pytest.mark.parametrize("value", [True, "otherNonce"])
    def test_rejects_invalid_or_different_explicit_nonce(self, value):
        script = Script(content="globalThis.bad = true;", attrs={"nonce": value}, wrap=False)
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>card</p>"

            class Dependencies:
                js = [script]

        with pytest.raises(ValueError, match="differs from this serialization"):
            Card().render().serialize(deps_strategy="simple", csp_nonce="requestNonce")

    def test_rejects_duplicate_nonce_casing(self):
        script = Script(
            content="globalThis.bad = true;",
            attrs={"nonce": "requestNonce", "NONCE": "requestNonce"},
            wrap=False,
        )
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>card</p>"

            class Dependencies:
                js = [script]

        with pytest.raises(ValueError, match="more than once"):
            Card().render().serialize(deps_strategy="simple", csp_nonce="requestNonce")

    def test_nonce_and_integrity_compose_on_the_same_captured_script(self):
        c = Citry(security_script_integrity="citry")

        class Card(Component):
            citry = c
            template = "<p>card</p>"
            js = "globalThis.secure = true;"

        result = Card().render().serialize_result(deps_strategy="simple", csp_nonce="requestNonce")

        assert '<script nonce="requestNonce">' in result.html
        assert len(result.security.scripts) == 1
        assert len(result.security.csp_script_hashes) == 1

    def test_later_string_hook_cannot_edit_a_nonced_inline_style(self):
        class EditStyle(Extension):
            name = "edit_style"

            def on_serialize(self, ctx):
                return ctx.html.replace("color: blue", "color: red")

        c = Citry(extensions=[EditStyle])

        class Card(Component):
            citry = c
            template = "<p>card</p>"
            css = ".card { color: blue; }"

        with pytest.raises(RuntimeError, match="on_dependencies"):
            Card().render().serialize_result(deps_strategy="simple", csp_nonce="requestNonce")

    def test_later_string_hook_cannot_edit_a_nonced_stylesheet_link(self):
        class EditStylesheet(Extension):
            name = "edit_stylesheet"

            def on_serialize(self, ctx):
                return ctx.html.replace('nonce="requestNonce"', 'nonce="staleNonce"')

        c = Citry(extensions=[EditStylesheet])

        class Card(Component):
            citry = c
            template = "<p>card</p>"

            class Dependencies:
                css = [Style(url="https://cdn.example.test/card.css")]

        with pytest.raises(RuntimeError, match="on_dependencies"):
            Card().render().serialize_result(deps_strategy="simple", csp_nonce="requestNonce")

    def test_nonced_style_is_materialized_once(self):
        class StatefulStyle(Style):
            calls = 0

            def _render(self):
                # Count on the class: emission renders its own copy of the
                # declared entry, so the declared object itself is never rendered.
                type(self).calls += 1
                return super()._render()

            def render(self):
                raise AssertionError("nonce emission must use the captured representation")

        style = StatefulStyle(content=".once { display: block; }")
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>card</p>"

            class Dependencies:
                css = [style]

        html = Card().render().serialize(deps_strategy="simple", csp_nonce="requestNonce")

        assert ".once { display: block; }" in html
        assert StatefulStyle.calls == 1

    def test_static_fragment_nonce_reaches_direct_dependencies(self):
        nonce = "fragmentNonce"
        c = Citry()
        c.set_mounted_prefix("/citry")

        class Card(Component):
            citry = c
            template = "<p>card</p>"

            class Dependencies:
                js = [Script(content="globalThis.inlineDependency = true;", wrap=False)]
                css = [
                    Style(content=".inline { color: green; }"),
                    Style(url="https://cdn.example.test/card.css"),
                ]

        result = Card().render().serialize_result(deps_strategy="fragment", csp_nonce=nonce)
        assert "data-citry-vue-fragment" not in result.html
        assert f'<script nonce="{nonce}">globalThis.inlineDependency = true;</script>' in result.html
        assert f'<style nonce="{nonce}">.inline {{ color: green; }}</style>' in result.html
        assert re.search(rf'<link[^>]*href="https://cdn\.example\.test/card\.css"[^>]*nonce="{nonce}"', result.html)

    def test_nonce_only_rejects_opaque_dependency_output(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>card</p>"

            class Dependencies:
                js = [Markup("<script>globalThis.opaque = true;</script>")]

        with pytest.raises(TypeError, match="structured Script objects"):
            Card().render().serialize_result(deps_strategy="simple", csp_nonce="requestNonce")


class TestCspSerializationModes:
    def test_native_vue_expressions_need_no_alpine_csp_warning(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = """
                <button @click="items.map(item => item.id)">Save</button>
            """

        rendered = Card().render()
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            warned = rendered.serialize(security_csp="warn")
        assert "data-citry-vue-document" in warned
        # The expression is compiled into the Vue definition, never evaluated
        # from HTML. It appears only as an inert attribute in the server HTML
        # the Vue host carries until Vue replaces it.
        host, scripts = warned.split("<script", 1)
        assert '@click="items.map' in host
        assert '@click="items.map' not in scripts

    def test_strict_accepts_precompiled_native_vue_expression(self):
        c = Citry(security_csp="strict")

        class Card(Component):
            citry = c
            template = """
                <button @click="items.map(item => item.id)">Save</button>
            """

        html = Card().render().serialize(csp_nonce="requestNonce")
        assert "data-citry-vue-document" in html

    def test_strict_accepts_browser_decoded_native_vue_expression(self):
        c = Citry(security_csp="strict")

        class Card(Component):
            citry = c
            template = """
                <button @click="items.map(item =&gt; item.id)">Save</button>
            """

        assert "data-citry-vue-document" in Card().render().serialize(csp_nonce="requestNonce")

    @pytest.mark.parametrize("mutation", ["edit", "duplicate"])
    def test_warn_late_script_changes_match_off_output(self, mutation):
        class ChangeScript(Extension):
            name = "change_script"

            def on_serialize(self, ctx):
                if mutation == "edit":
                    return ctx.html.replace("console.log('safe')", "console.log('changed')")
                return ctx.html + ctx.html

        c = Citry(extensions=[ChangeScript])

        class Card(Component):
            citry = c
            template = "<p>card</p>"
            js = "console.log('safe')"

        rendered = Card().render()
        ordinary = rendered.serialize(deps_strategy="simple", security_csp="off")
        with pytest.warns(RuntimeWarning, match="raw <script>"):
            warned = rendered.serialize(deps_strategy="simple", security_csp="warn")

        assert warned == ordinary

    def test_warn_late_script_removal_matches_off_without_marker_leak(self):
        class RemoveScript(Extension):
            name = "remove_script"

            def on_serialize(self, ctx):
                return re.sub(r"<script[^>]*>.*?</script>", "", ctx.html, flags=re.DOTALL)

        c = Citry(extensions=[RemoveScript])

        class Card(Component):
            citry = c
            template = "<p>card</p>"
            js = "console.log('safe')"

        rendered = Card().render()
        ordinary = rendered.serialize(deps_strategy="simple", security_csp="off")
        warned = rendered.serialize(deps_strategy="simple", security_csp="warn")

        assert warned == ordinary
        assert "data-citry-security" not in warned

    def test_warn_cannot_authenticate_identical_raw_markup_as_a_removed_dependency(self):
        class RemoveEmittedScript(Extension):
            name = "remove_emitted_script"

            def on_serialize(self, ctx):
                return ctx.html[: ctx.html.index("</div>") + len("</div>")]

        c = Citry(extensions=[RemoveEmittedScript])

        class Card(Component):
            citry = c
            template = "<div><script>(function() {\nconsole.log('same')\n})();</script></div>"
            js = "console.log('same')"

        rendered = Card().render()
        ordinary = rendered.serialize(deps_strategy="simple", security_csp="off")
        with pytest.warns(RuntimeWarning, match="raw <script>"):
            warned = rendered.serialize(deps_strategy="simple", security_csp="warn")

        assert warned == ordinary

    def test_strict_compiles_component_boundary_expression(self):
        c = Citry(security_csp="strict")

        class Child(Component):
            citry = c
            template = """
                <button>Child</button>
            """

        class Parent(Component):
            citry = c
            template = """
                <c-child @click="items.map(item => item.id)" />
            """

        assert "data-citry-vue-document" in Parent().render().serialize(csp_nonce="requestNonce")

    def test_component_boundary_expression_is_absent_from_final_html(self):
        c = Citry(security_csp="strict")

        class Child(Component):
            citry = c
            template = "<button>Child</button>"

        class Parent(Component):
            citry = c
            template = '<c-child @click="items.map(item => item.id)" />'

        html = Parent().render().serialize(csp_nonce="requestNonce")
        assert '@click="items.map' not in html

    @pytest.mark.parametrize(
        ("template", "message"),
        [
            ('<script type="application/json">{}</script>', "raw <script>"),
            ("<style>.card { color: red; }</style>", "raw <style>"),
            ('<button onclick="save()">Save</button>', "native inline event"),
            ('<a href="java&#x09;script:save()">Save</a>', "javascript: URL"),
        ],
    )
    def test_strict_rejects_raw_active_html(self, template, message):
        c = Citry(security_csp="strict")

        class Card(Component):
            citry = c

        Card.template = template

        with pytest.raises(ValueError, match=message):
            Card().render().serialize(deps_strategy="simple")

    @pytest.mark.parametrize("attribute", ["oncommand", "ONSCROLLSNAPCHANGE"])
    def test_strict_rejects_browser_native_handler_prefixes(self, attribute):
        c = Citry(security_csp="strict")

        class Card(Component):
            citry = c

        Card.template = f'<button {attribute}="save()">Save</button>'

        with pytest.raises(ValueError, match="native inline event"):
            Card().render().serialize(deps_strategy="simple")

    def test_strict_rejects_javascript_object_data(self):
        c = Citry(security_csp="strict")

        class Card(Component):
            citry = c
            template = '<object data="javascript:save()"></object>'

        with pytest.raises(ValueError, match="javascript: URL"):
            Card().render().serialize(deps_strategy="simple")

    @pytest.mark.parametrize(
        ("reference", "message"),
        [
            # Leading zeros do not change the code point, so this is `j`.
            ("&#" + "0" * 5000 + "106;", "javascript: URL"),
            # Past U+10FFFF, the reference decodes to U+FFFD.
            ("&#" + "9" * 5000 + ";", None),
        ],
    )
    def test_csp_decodes_a_decimal_reference_of_any_length(self, reference, message):
        c = Citry(security_csp="strict")

        class Card(Component):
            citry = c

        Card.template = f'<a href="{reference}avascript:save()">Save</a>'

        rendered = Card().render()
        if message is None:
            rendered.serialize(deps_strategy="simple")
            return
        with pytest.raises(ValueError, match=message):
            rendered.serialize(deps_strategy="simple")

    def test_native_vue_entity_expression_is_compiled_out_of_html(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<button @click="&NotEqualTilde;">Save</button>'

        rendered = Card().render()
        with pytest.raises(ValueError, match="Vue compiler diagnostics"):
            rendered.serialize(security_csp="strict", csp_nonce="requestNonce")

    def test_dedupe_keeps_distinct_sites_and_rendered_instances(self):
        c = Citry(security_csp="strict")

        class TwoSites(Component):
            citry = c
            template = '<main><button onclick="save()"></button><button onclick="save()"></button></main>'

        with pytest.raises(ValueError, match=r"found 2 strict-CSP incompatibility issue\(s\)"):
            TwoSites().render().serialize(deps_strategy="simple")

        class Child(Component):
            citry = c
            template = '<button onclick="save()"></button>'

        class Repeated(Component):
            citry = c
            template = "<main><c-child /><c-child /></main>"

        with pytest.raises(ValueError, match=r"found 2 strict-CSP incompatibility issue\(s\)"):
            Repeated().render().serialize(deps_strategy="simple")

    def test_strict_validates_attributes_added_by_a_late_string_hook(self):
        class AddUnsafeAttribute(Extension):
            name = "add_unsafe_attribute"

            def on_serialize(self, ctx):
                return ctx.html.replace("<button", '<button onclick="save()"')

        c = Citry(extensions=[AddUnsafeAttribute], security_csp="strict")

        class Card(Component):
            citry = c
            template = """
                <button>Save</button>
            """

        with pytest.raises(ValueError, match="native inline event"):
            Card().render().serialize(deps_strategy="simple")

    def test_strict_nonces_native_vue_runtime_for_mounted_and_inline_documents(self):
        for mounted in (False, True):
            c = Citry(security_csp="strict")
            if mounted:
                c.set_mounted_prefix("/citry")

            class Card(Component):
                citry = c
                template = """
                    <button @click="count += 1">Add</button>
                """

            html = Card().render().serialize(csp_nonce="requestNonce")
            assert ('src="/citry/citry.js"' in html) is mounted
            assert ("Citry interactive runtime" in html) is not mounted
            assert 'nonce="requestNonce"' in html

    def test_strict_requires_nonce_only_when_active_code_or_inline_css_is_emitted(self):
        c = Citry(security_csp="strict")

        class Static(Component):
            citry = c
            template = """
                <p>Static</p>
            """

        class Interactive(Component):
            citry = c
            template = """
                    <button @click="ready = true">Ready</button>
            """

        assert "Static" in Static().render().serialize()
        with pytest.raises(ValueError, match="requires csp_nonce"):
            Interactive().render().serialize()

    def test_strict_fragment_is_inert_and_requests_the_csp_runtime(self):
        c = Citry(security_csp="strict")
        c.set_mounted_prefix("/citry")

        class Card(Component):
            citry = c
            template = """
                    <button @click="ready = true">Ready</button>
            """

        html = Card().render().serialize(deps_strategy="fragment", csp_nonce="requestNonce")
        vue = _vue_fragment(html)
        assert 'nonce="requestNonce"' in html
        assert vue["prepared"]["nonce"] == "requestNonce"
        assert "data-citry-vue-fragment" in html


class TestJavascriptDeliveryPolicy:
    @pytest.mark.parametrize("strategy", ["document", "simple", "fragment", "ignore"])
    def test_warn_preserves_allow_bytes(self, strategy):
        c = Citry()
        c.set_mounted_prefix("/citry")

        class Card(Component):
            citry = c
            template = '<main data-card="{}"><button @click="save()">Save</button></main>'
            js = "globalThis.cardReady = true;"
            css = ".card { color: rebeccapurple; }"

        rendered = Card().render()
        allowed = rendered.serialize(deps_strategy=strategy, security_javascript="allow")
        with pytest.warns(RuntimeWarning, match="security_javascript='warn'"):
            warned = rendered.serialize(deps_strategy=strategy, security_javascript="warn")

        if strategy in {"simple", "ignore"}:
            assert warned == allowed
        else:
            assert (
                "data-citry-vue-document" in warned if strategy == "document" else "data-citry-vue-fragment" in warned
            )
            if strategy == "document":
                assert _prepared(warned)["manifest"]["scripts"]
            else:
                assert _vue_fragment(warned)["prepared"]["manifest"]["scripts"]

    @pytest.mark.parametrize("strategy", ["document", "simple", "fragment"])
    def test_omit_keeps_html_and_css_without_managed_javascript(self, strategy):
        c = Citry(security_javascript="omit")

        class Card(Component):
            citry = c
            template = '<main data-card="{}"><p>Server fallback</p></main>'
            js = "globalThis.cardReady = true;"
            css = "p { color: rebeccapurple; }"

        html = Card().render().serialize(deps_strategy=strategy)

        assert "Server fallback" in html
        assert 'data-card="{}"' in html
        assert "rebeccapurple" in html
        assert "<script" not in html
        assert "data-citry-root" not in html
        assert "document.currentScript" not in html

    @pytest.mark.parametrize("strategy", ["document", "simple", "fragment", "ignore"])
    def test_forbid_allows_static_html_and_css(self, strategy):
        c = Citry(security_javascript="forbid")

        class Card(Component):
            citry = c
            template = "<p>Static</p>"
            css = "p { color: green; }"

        html = Card().render().serialize(deps_strategy=strategy)
        assert "Static" in html
        assert "<script" not in html
        assert ("color: green" in html) is (strategy != "ignore")

    @pytest.mark.parametrize(
        ("template", "message"),
        [
            ("<div v-cloak>Hidden</div>", "v-cloak"),
            ('<button @click="save()">Save</button>', "@click"),
            ('<button onclick="save()">Save</button>', "native inline event"),
            ('<a href="javascript:save()">Save</a>', "javascript: URL"),
            ('<script type="module">save()</script>', "raw executable"),
            # Chromium drops U+2028 from the end of a type and runs this.
            ('<script type="text/javascript&#x2028;">save()</script>', "raw executable"),
            ('<div v-unknown-plugin="value"></div>', "v-unknown-plugin"),
        ],
    )
    def test_forbid_rejects_settled_activation_paths(self, template, message):
        c = Citry(security_javascript="forbid")

        class Card(Component):
            citry = c

        Card.template = template
        with pytest.raises(ValueError, match=message):
            Card().render().serialize(deps_strategy="ignore")

    # Chromium 156 decodes the Shift_JIS spelling of U+3000 in a data document
    # that names the encoding, skips it, and opens the refresh URL.
    @pytest.mark.parametrize("charset", [";charset=shift_jis", ";charset=shift_jis;base64"])
    def test_forbid_rejects_a_refresh_padded_in_a_legacy_encoding(self, charset):
        page = b'<meta http-equiv=refresh content="\x81\x400;url=data:text/xml,x">'
        body = base64.b64encode(page).decode() if charset.endswith("base64") else quote_from_bytes(page)
        c = Citry(security_javascript="forbid")

        class Frame(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"page": Markup(f'<iframe src="data:text/html{charset},{body}"></iframe>')}  # noqa: S704 - a fixed test document

            template = """
                {{ page }}
            """

        with pytest.raises(ValueError, match="src"):
            Frame().render().serialize(deps_strategy="ignore")

    # Chromium 156 and Firefox 157 ran what follows these when the page was
    # read in the encoding each needs, which the check cannot see.
    @pytest.mark.parametrize(
        "text",
        [
            "<meta charset=iso-2022-jp><p title='\x1b$B'\x1b(B>x</p>",
            "<meta charset=iso-2022-jp><scr\x1b(Bipt>save()</script>",
            "<meta charset=shift_jis><svg><![CDATA[\u3041]]></svg>",
        ],
    )
    def test_forbid_rejects_markup_whose_tags_depend_on_the_encoding(self, text):
        c = Citry(security_javascript="forbid")

        class Page(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"page": Markup(text)}  # noqa: S704 - a fixed test document

            template = """
                {{ page }}
            """

        with pytest.raises(ValueError, match="another encoding"):
            Page().render().serialize(deps_strategy="ignore")

    # Raw ESC bytes on a page read as ISO-2022-JP let a value take a closing
    # quote with them, and ran code in Chromium 156 and Firefox 157. A value
    # is written with `&#27;`, which the browser reads after it decodes the
    # page, so the page stays safe and the check has nothing to report.
    @pytest.mark.parametrize("value", ["\x1b$B", "\x1b(B", "\x1b(I", "a\x1b$@b"])
    def test_forbid_keeps_an_escaped_value_that_holds_esc(self, value):
        c = Citry(security_javascript="forbid")

        class Page(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"note": value, "notes": [value, value], "extra": {"data-x": value}}

            template = """
                <p c-title="note" c-bind="extra">{{ note }}</p>
                <ul>
                    <li c-for="item in notes" c-title="item">{{ item }}</li>
                </ul>
            """

        html = str(Page().render().serialize(deps_strategy="ignore"))

        assert "\x1b" not in html
        assert value.replace("\x1b", "&#27;") in html

    # Repeated simple Vue leaves and slots each take their own fast path.
    @pytest.mark.parametrize("strategy", ["ignore", "simple", "document", "fragment"])
    def test_python_render_paths_write_no_raw_esc(self, strategy):
        c = Citry()

        class Leaf(Component):
            citry = c
            simple = "vue"

            class Kwargs:
                note: str

            @staticmethod
            def template_data(kwargs, _slots):
                return {"note": kwargs.note}

            template = """
                <li c-title="note">{{ note }}</li>
            """

        class Box(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"note": "\x1b$B"}

            template = """
                <section c-title="note"><c-slot>{{ note }}</c-slot></section>
            """

        class Page(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"notes": ["\x1b$B"] * 3}

            template = """
                <ul><c-leaf c-for="note in notes" c-note="note" /></ul>
                <c-box>{{ notes[0] }}</c-box>
            """

        html = str(Page().render().serialize(deps_strategy=strategy))

        assert "\x1b" not in html
        assert "&#27;$B" in html

    # A hydrated page goes through the Vue server renderer in Rust, and its
    # parse of the page must still accept what it wrote. A shell's text
    # takes its own path.
    @pytest.mark.parametrize("value", ["\x1b$B", "\x1b(B"])
    def test_a_hydrated_page_writes_esc_as_a_reference(self, value):
        c = Citry()

        class Page(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"note": value}

            def js_data(self, kwargs, slots):
                return {"browser_note": value}

            template = """
                <main>
                    <section>
                        <b v-if="dragging">x</b>
                        <p c-title="note">{{ note }}</p>
                        <i :title="browser_note" v-text="browser_note"></i>
                    </section>
                </main>
            """
            js = """
                $component({ data() { return { dragging: false }; } });
            """

        html = str(Page().render().serialize())

        written = value.replace("\x1b", "&#27;")
        assert '"hydrate":true' in html
        assert "\x1b" not in html
        assert f'title="{written}"' in html
        assert f">{written}</p>" in html
        assert f">{written}</i>" in html

    # The check must see ESC in a value the browser reads from the reference,
    # or a `data:` document that holds one stops counting as running.
    @pytest.mark.parametrize("attribute", ['<iframe c-src="url"></iframe>', '<a c-href="url">x</a>'])
    def test_forbid_rejects_a_data_url_value_that_holds_esc(self, attribute):
        c = Citry(security_javascript="forbid")

        class Page(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"url": "data:text/html;charset=iso-2022-jp,<scr\x1b(Bipt>x()</script>"}

        Page.template = attribute
        with pytest.raises(ValueError, match="embedded document"):
            Page().render().serialize(deps_strategy="ignore")

    # `slots["link"]()` hands the value on as escaped HTML, which an attribute
    # decodes again; dropping ESC there would spell a URL the value did not.
    def test_an_attribute_keeps_esc_from_an_escaped_value(self):
        assert decode_attribute_entities("java&#27;script:x") == "java\x1bscript:x"
        assert escape_attribute_value(escape("java\x1bscript:x")) == "java&#27;script:x"

    def test_markup_format_keeps_esc_for_the_check_to_find(self):
        c = Citry(security_javascript="forbid")

        class Page(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"note": Markup("<p>{}</p>").format("\x1b$B")}

            template = """
                {{ note }}
            """

        with pytest.raises(ValueError, match="another encoding"):
            Page().render().serialize(deps_strategy="ignore")

    def test_forbid_still_rejects_esc_in_markup(self):
        c = Citry(security_javascript="forbid")

        class Page(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"note": Markup("\x1b$B")}

            template = """
                <p>{{ note }}</p>
            """

        with pytest.raises(ValueError, match="another encoding"):
            Page().render().serialize(deps_strategy="ignore")

    def test_escaping_writes_esc_as_a_reference_and_leaves_markup_alone(self):
        assert escape("a\x1b$B<") == "a&#27;$B&lt;"
        assert type(escape("\x1b")) is Markup
        assert escape_to_str("a\x1b$B<") == "a&#27;$B&lt;"
        assert escape_attribute_value('a\x1b$B"') == "a&#27;$B&#34;"
        # Trusted HTML stays exactly as written; the check reads it.
        assert escape(Markup("\x1b$B")) == "\x1b$B"
        assert escape_to_str(Markup("\x1b$B")) == "\x1b$B"
        # Vue reads the same text the browser does from the reference.
        assert decode_character_references("&#27;") == "\x1b"

    def test_forbid_keeps_terminal_output_that_stays_in_ascii(self):
        c = Citry(security_javascript="forbid")

        class Page(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"log": "\x1b[31mred\x1b[0m"}

            template = """
                <pre>{{ log }}</pre>
            """

        assert "&#27;[31m" in Page().render().serialize(deps_strategy="ignore")

    # A document passed as Markup to `c-srcdoc` is checked like any other
    # embedded document. The U+000B is typed raw and as `&#11;`, which a
    # browser keeps and this check drops.
    @pytest.mark.parametrize("space", ["\x0b", "&#11;", "&#x3000;"])
    def test_forbid_rejects_a_markup_srcdoc_script_padded_with_a_character_a_browser_may_skip(self, space):
        c = Citry(security_javascript="forbid")

        class Frame(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"doc": Markup(f'<script type="{space}text/javascript">save()</script>')}  # noqa: S704 - a fixed test document

            template = """
                <iframe c-srcdoc="doc"></iframe>
            """

        with pytest.raises(ValueError, match="srcdoc"):
            Frame().render().serialize(deps_strategy="ignore")

    # Chromium 156 drops U+000B and these Unicode spaces from either end of
    # a script type and runs the script. It keeps U+00A0, which the check
    # counts anyway, because it does not track which characters each browser
    # drops.
    @pytest.mark.parametrize("space", ["\x0b", "\u1680", "\u2000", "\u200a", "\u2028", "\u205f", "\u3000", "\xa0"])
    def test_forbid_rejects_a_script_type_padded_with_a_character_a_browser_may_skip(self, space):
        class Block(Extension):
            name = "block"

            def on_dependencies(self, ctx):
                ctx.scripts.append(Script(content="save()", attrs={"type": f"{space}text/javascript"}))

        c = Citry(extensions=[Block], security_javascript="forbid")

        class Card(Component):
            citry = c
            template = """
                <p>card</p>
            """

        with pytest.raises(ValueError, match="executable"):
            Card().render().serialize(deps_strategy="simple")

    def test_forbid_allows_attributes_no_citry_runtime_reads(self):
        # Only Vue directive spellings need the browser runtime. An x-* name
        # is an ordinary attribute to Citry, so forbid keeps it as bytes.
        c = Citry(security_javascript="forbid")

        class Card(Component):
            citry = c
            template = '<div x-data="{}" x-cloak>Plain</div>'

        html = Card().render().serialize(deps_strategy="ignore")
        assert 'x-data="{}"' in html

    @pytest.mark.parametrize("kind", ["component", "dependencies"])
    def test_ignore_cannot_hide_reached_javascript_declarations(self, kind):
        c = Citry(security_javascript="forbid")

        if kind == "component":

            class Card(Component):
                citry = c
                template = "<p>Card</p>"
                js = "globalThis.cardReady = true;"
        else:

            class Card(Component):
                citry = c
                template = "<p>Card</p>"

                class Dependencies:
                    js = ["https://example.test/card.js"]

        with pytest.raises(ValueError, match=r"Component\.js|JavaScript Dependencies"):
            Card().render().serialize(deps_strategy="ignore")

    def test_forbid_uses_mime_essence_and_preserves_inert_data_scripts(self):
        c = Citry(security_javascript="forbid")

        class Data(Component):
            citry = c
            template = "<p>Data</p>"

            class Dependencies:
                js = [Script(content='{"ready":true}', attrs={"type": "application/ld+json"}, wrap=False)]

        assert "application/ld+json" in Data().render().serialize(deps_strategy="simple")

        class Active(Component):
            citry = c
            template = "<p>Active</p>"

            class Dependencies:
                js = [
                    Script(
                        content="globalThis.ready = true;",
                        attrs={"TYPE": "text/javascript;charset=utf-8"},
                        wrap=False,
                    )
                ]

        with pytest.raises(ValueError, match="executable extra Script"):
            Active().render().serialize(deps_strategy="simple")

    def test_omit_preserves_raw_script_and_reports_that_it_remains(self):
        c = Citry(security_javascript="omit")

        class Card(Component):
            citry = c
            template = "<main><script>globalThis.raw = true;</script></main>"
            js = "globalThis.managed = true;"

        with pytest.warns(RuntimeWarning, match="raw executable"):
            html = Card().render().serialize()

        assert "globalThis.raw = true" in html
        assert "globalThis.managed = true" not in html

    def test_forbid_detects_dependency_and_late_hook_output(self):
        class AddScripts(Extension):
            name = "add_scripts"

            def on_dependencies(self, ctx):
                ctx.scripts.append(Script(content="globalThis.dependency = true;", wrap=False))

            def on_serialize(self, ctx):
                return ctx.html + "<script>globalThis.late = true;</script>"

        c = Citry(extensions=[AddScripts], security_javascript="forbid")

        class Card(Component):
            citry = c
            template = "<p>Card</p>"

        with pytest.raises(ValueError, match=r"found 2 client behavior requirement\(s\)") as error:
            Card().render().serialize(deps_strategy="simple")
        assert "dependency list" in str(error.value)
        assert "raw executable" in str(error.value)

    def test_unused_events_declaration_is_not_a_client_requirement(self):
        c = Citry(security_javascript="forbid")

        class Card(Component):
            citry = c
            template = "<p>No event binding</p>"

            class Events:
                def save(self):
                    return None

        html = Card().render().serialize()
        assert "No event binding" in html
        assert "data-citry" not in html

    def test_active_event_binding_is_rejected_even_when_dependencies_are_ignored(self):
        c = Citry(security_javascript="forbid")

        class Card(Component):
            citry = c
            template = '<button @c-click="save">Save</button>'

            class Events:
                def save(self):
                    return None

        with pytest.raises(
            ValueError,
            match=r"selected event, poll, or State control bindings require the Citry Events runtime",
        ):
            Card().render().serialize(deps_strategy="ignore")

    def test_omit_composes_with_strict_csp_and_integrity(self):
        c = Citry(
            security_csp="strict",
            security_javascript="omit",
            security_script_integrity="citry",
        )

        class Card(Component):
            citry = c
            template = '<main data-items="items.map(item => item.id)">Fallback</main>'
            js = "globalThis.managed = true;"
            css = "main { color: purple; }"

        result = Card().render().serialize_result(csp_nonce="requestNonce")
        assert 'data-items="items.map(item => item.id)"' in result.html
        assert re.search(r'<style\b[^>]*\bnonce="requestNonce"', result.html)
        assert "<script" not in result.html
        assert result.security.scripts == ()
        assert result.security.csp_script_hashes == ()

    def test_ignore_does_not_invoke_dependency_hooks_for_inventory(self):
        calls = 0

        class ObserveDependencies(Extension):
            name = "observe_dependencies"

            def on_dependencies(self, ctx):
                nonlocal calls
                calls += 1

        c = Citry(extensions=[ObserveDependencies], security_javascript="forbid")

        class Card(Component):
            citry = c
            template = "<p>Card</p>"
            js = "globalThis.cardReady = true;"

        with pytest.raises(ValueError, match=r"Component\.js"):
            Card().render().serialize(deps_strategy="ignore")
        assert calls == 0

    def test_per_call_javascript_modes_do_not_leak(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>Card</p>"
            js = "globalThis.cardReady = true;"

        rendered = Card().render()
        omitted = rendered.serialize(security_javascript="omit")
        assert "citry:ownership-manifest" not in rendered.context.extra
        allowed = rendered.serialize(security_javascript="allow")

        assert "globalThis.cardReady" not in omitted
        assert _prepared(allowed)["manifest"]["scripts"]
        with pytest.raises(ValueError, match="executable component Script"):
            rendered.serialize(security_javascript="forbid")

    def test_warn_does_not_authenticate_identical_raw_script_as_managed(self):
        class RemoveEmittedScript(Extension):
            name = "remove_emitted_script_for_javascript_inventory"

            def on_serialize(self, ctx):
                return ctx.html[: ctx.html.index("</div>") + len("</div>")]

        c = Citry(extensions=[RemoveEmittedScript])

        class Card(Component):
            citry = c
            template = "<div><script>(function() {\nconsole.log('same')\n})();</script></div>"
            js = "console.log('same')"

        rendered = Card().render()
        ordinary = rendered.serialize(deps_strategy="simple", security_javascript="allow")
        with pytest.warns(RuntimeWarning, match="raw executable"):
            warned = rendered.serialize(deps_strategy="simple", security_javascript="warn")
        assert warned == ordinary

    def test_warn_preserves_secure_materialization_and_metadata(self):
        class OpaqueScript(Script):
            def render(self):
                return Markup("<script>globalThis.override = true;</script>")

        script = OpaqueScript(content="globalThis.canonical = true;", wrap=False)
        c = Citry(security_script_integrity="citry")

        class Card(Component):
            citry = c
            template = "<p>Card</p>"

            class Dependencies:
                js = [script]

        rendered = Card().render()
        allowed = rendered.serialize_result(deps_strategy="simple", security_javascript="allow")
        with pytest.warns(RuntimeWarning, match="opaque OpaqueScript"):
            warned = rendered.serialize_result(deps_strategy="simple", security_javascript="warn")

        assert warned == allowed
        assert "globalThis.canonical" in warned.html
        assert "globalThis.override" not in warned.html

    def test_warn_preserves_nonce_materialization_for_opaque_style(self):
        class OpaqueStyle(Style):
            def render(self):
                return Markup("<script>globalThis.override = true;</script>")

        style = OpaqueStyle(content="p { color: teal; }")
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>Card</p>"

            class Dependencies:
                css = [style]

        rendered = Card().render()
        allowed = rendered.serialize_result(
            deps_strategy="simple",
            security_javascript="allow",
            csp_nonce="requestNonce",
        )
        with pytest.warns(RuntimeWarning, match="opaque OpaqueStyle"):
            warned = rendered.serialize_result(
                deps_strategy="simple",
                security_javascript="warn",
                csp_nonce="requestNonce",
            )

        assert warned == allowed
        assert '<style nonce="requestNonce">p { color: teal; }</style>' in warned.html

    @pytest.mark.parametrize(
        "attrs",
        [
            {"type": 123},
            {"type": "application/json", "TYPE": "application/json"},
        ],
    )
    def test_warn_preserves_allow_bytes_for_unclassifiable_script_type(self, attrs):
        script = Script(content="{}", attrs=attrs, wrap=False)
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>Card</p>"

            class Dependencies:
                js = [script]

        rendered = Card().render()
        allowed = rendered.serialize(deps_strategy="simple", security_javascript="allow")
        with pytest.warns(RuntimeWarning, match="cannot be proven inert"):
            warned = rendered.serialize(deps_strategy="simple", security_javascript="warn")
        assert warned == allowed

    def test_warn_preserves_stateful_duplicate_dependency_bytes(self):
        class StatefulScript(Script):
            calls = 0

            def _render(self):
                self.calls += 1
                return "script", {}, f"globalThis.call{self.calls} = true;"

        script = StatefulScript(content="placeholder", wrap=False)

        class AddTwice(Extension):
            name = "add_stateful_script_twice"

            def on_dependencies(self, ctx):
                ctx.scripts.extend([script, script])

        c = Citry(extensions=[AddTwice])

        class Card(Component):
            citry = c
            template = "<p>Card</p>"

        rendered = Card().render()
        allowed = rendered.serialize(deps_strategy="simple", security_javascript="allow")
        script.calls = 0
        with pytest.warns(RuntimeWarning, match="opaque StatefulScript"):
            warned = rendered.serialize(deps_strategy="simple", security_javascript="warn")
        assert warned == allowed

    def test_omit_removes_opaque_style_renderer(self):
        class OpaqueStyle(Style):
            def render(self):
                return Markup("<script>globalThis.pwned = true;</script>")

        c = Citry(security_javascript="omit")

        class Card(Component):
            citry = c
            template = "<p>Card</p>"

            class Dependencies:
                css = [OpaqueStyle(content="p { color: red; }")]

        html = Card().render().serialize(deps_strategy="simple")
        assert "globalThis.pwned" not in html

    def test_exact_style_active_attribute_is_sanitized_but_css_is_preserved(self):
        style = Style(url="/theme.css", attrs={"onload": "globalThis.pwned = true", "media": "print"})
        c = Citry(security_javascript="omit")

        class Card(Component):
            citry = c
            template = "<p>Card</p>"

            class Dependencies:
                css = [style]

        html = Card().render().serialize(deps_strategy="simple")
        assert 'href="/theme.css"' in html
        assert 'media="print"' in html
        assert "onload" not in html

    @pytest.mark.parametrize(
        "dependency",
        [
            Style(url="/theme.css", attrs={"onload": "globalThis.ready = true"}),
            Script(
                content='{"ready":true}',
                attrs={"type": "application/json", "onanimationstart": "globalThis.ready = true"},
                wrap=False,
            ),
        ],
    )
    def test_warn_preserves_active_structured_attributes(self, dependency):
        class AddDependency(Extension):
            name = "add_active_structured_attribute"

            def on_dependencies(self, ctx):
                target = ctx.styles if isinstance(dependency, Style) else ctx.scripts
                target.append(dependency)

        c = Citry(extensions=[AddDependency])

        class Card(Component):
            citry = c
            template = "<p>Card</p>"

        rendered = Card().render()
        allowed = rendered.serialize(deps_strategy="simple", security_javascript="allow")
        with pytest.warns(RuntimeWarning, match="requires JavaScript"):
            warned = rendered.serialize(deps_strategy="simple", security_javascript="warn")
        assert warned == allowed

    def test_forbid_inspects_css_declarations_even_when_dependencies_are_ignored(self):
        c = Citry(security_javascript="forbid")

        class Card(Component):
            citry = c
            template = "<p>Card</p>"

            class Dependencies:
                css = [Style(url="/theme.css", attrs={"onload": "globalThis.pwned = true"})]

        with pytest.raises(ValueError, match="native inline event attribute"):
            Card().render().serialize(deps_strategy="ignore")

    def test_omit_sanitizes_active_attributes_from_inert_data_script(self):
        script = Script(
            content='{"ready":true}',
            attrs={"type": "application/json", "onanimationstart": "globalThis.pwned = true"},
            wrap=False,
        )
        c = Citry(security_javascript="omit")

        class Card(Component):
            citry = c
            template = "<p>Card</p>"

            class Dependencies:
                js = [script]

        html = Card().render().serialize(deps_strategy="simple")
        assert '{"ready":true}' in html
        assert "onanimationstart" not in html

    def test_forbid_rejects_structured_browser_manifest(self):
        class AddManifest(Extension):
            name = "add_browser_manifest"

            def on_dependencies(self, ctx):
                ctx.early_scripts.append(
                    Script(content="{}", attrs={"type": "application/json", "data-citry-custom": True})
                )

        c = Citry(extensions=[AddManifest], security_javascript="forbid")

        class Card(Component):
            citry = c
            template = "<p>Card</p>"

        with pytest.raises(ValueError, match="browser manifest"):
            Card().render().serialize(deps_strategy="simple")

    @pytest.mark.parametrize(
        "template",
        [
            '<input type="button" @click="save()">',
            '<section hidden :hidden="closed">Fallback</section>',
            '<form :action="target"><button>Save</button></form>',
        ],
    )
    def test_omit_warns_for_unusable_static_fallbacks(self, template):
        c = Citry(security_javascript="omit")

        class Card(Component):
            citry = c

        Card.template = template
        with pytest.warns(RuntimeWarning, match=r"static fallback|no native navigation"):
            Card().render().serialize(deps_strategy="ignore")

    @pytest.mark.parametrize(
        "template",
        [
            '<iframe srcdoc="&lt;script&gt;globalThis.pwned = true;&lt;/script&gt;"></iframe>',
            '<iframe src="data:text/html,%3Cscript%3EglobalThis.pwned=true%3C/script%3E"></iframe>',
            '<iframe src=" &#9;data:text/html,%3Cscript%3EglobalThis.pwned=true%3C/script%3E"></iframe>',
        ],
    )
    def test_forbid_rejects_executable_embedded_html_documents(self, template):
        c = Citry(security_javascript="forbid")

        class Card(Component):
            citry = c

        Card.template = template
        with pytest.raises(ValueError, match="embedded document"):
            Card().render().serialize(deps_strategy="ignore")

    @pytest.mark.parametrize(
        ("payload", "reported"),
        [
            # `<p>hi</p>` in canonical base64 holds no script.
            ("PHA+aGk8L3A+", False),
            # Padding after a complete group, or padding alone, is not valid
            # base64, so the check cannot read the document and reports it.
            ("PHA+aGk8L3A+=", True),
            ("PHA+aGk8L3A+==", True),
            ("=", True),
        ],
    )
    def test_forbid_reads_base64_documents_the_same_on_every_python(self, payload, reported):
        c = Citry(security_javascript="forbid")

        class Card(Component):
            citry = c

        Card.template = f'<iframe src="data:text/html;base64,{payload}"></iframe>'
        rendered = Card().render()
        if not reported:
            rendered.serialize(deps_strategy="ignore")
            return
        with pytest.raises(ValueError, match="embedded document"):
            rendered.serialize(deps_strategy="ignore")

    # Embedded documents whose script the browser runs, written with
    # character references the check must decode the way the browser does.
    _SRCDOC_SCRIPT = "&lta&lt;script&gt;run()&lt;/script&gt;"
    _DATA_SCRIPT = "data:text/html,&lta%3Cscript%3Erun()%3C/script%3E"
    _EMBEDDED_WITH_SCRIPT = [
        f'<iframe srcdoc="{_SRCDOC_SCRIPT}"></iframe>',
        f'<iframe src="{_DATA_SCRIPT}"></iframe>',
        f'<object data="{_DATA_SCRIPT}"></object>',
        f'<embed src="{_DATA_SCRIPT}">',
        # A plain script is reported.
        '<iframe srcdoc="&lt;script&gt;run()&lt;/script&gt;"></iframe>',
    ]

    @pytest.mark.parametrize("markup", _EMBEDDED_WITH_SCRIPT)
    def test_forbid_rejects_an_embedded_document_whose_script_runs(self, markup):
        c = Citry(security_javascript="forbid")

        class Card(Component):
            citry = c
            template = "{{ body }}"

            def template_data(self, kwargs, slots):
                return {"body": Markup(markup)}  # noqa: S704 - the test writes fixed markup

        with pytest.raises(ValueError, match="embedded document"):
            Card().render().serialize(deps_strategy="ignore")

    @pytest.mark.parametrize("markup", _EMBEDDED_WITH_SCRIPT)
    def test_warn_reports_an_embedded_document_whose_script_runs(self, markup):
        c = Citry(security_javascript="warn")

        class Card(Component):
            citry = c
            template = "{{ body }}"

            def template_data(self, kwargs, slots):
                return {"body": Markup(markup)}  # noqa: S704 - the test writes fixed markup

        with pytest.warns(RuntimeWarning, match="embedded document"):
            Card().render().serialize(deps_strategy="ignore")

    def test_forbid_still_passes_an_inert_embedded_document(self):
        c = Citry(security_javascript="forbid")

        class Card(Component):
            citry = c
            template = "{{ body }}"

            def template_data(self, kwargs, slots):
                return {"body": Markup('<iframe srcdoc="&lt;p&gt;hi&lt;/p&gt;"></iframe>')}

        # A well-formed document with no executable content is allowed.
        Card().render().serialize(deps_strategy="ignore")

    @pytest.mark.parametrize(
        "value",
        [
            # A legacy entity an `=` or an alphanumeric follows stays literal,
            # so the check reads these as the plain URLs they are.
            "/search?a=1&copy=2",
            "/path?x=1&notin=y",
        ],
    )
    def test_a_query_string_with_a_legacy_entity_name_passes_forbid(self, value):
        c = Citry(security_javascript="forbid")

        class Card(Component):
            citry = c
            template = "{{ body }}"

            def template_data(self, kwargs, slots):
                return {"body": Markup(f'<a href="{value}">x</a>')}  # noqa: S704 - fixed markup

        # No finding, so forbid serializes without raising.
        Card().render().serialize(deps_strategy="ignore")


def _render_under_javascript_policy(mode: str, page_template: str, data: dict[str, object]) -> str:
    app = Citry(security_javascript=mode)

    class Page(Component):
        citry = app
        template = page_template

        def template_data(self, kwargs, slots):
            return data

    return str(Page().render().serialize(deps_strategy="ignore"))


class TestSelectContents:
    """A browser may keep or drop the tags inside `<select>`, so the checks read a page both ways."""

    _SCRIPT = "<script>console.log(1)</script>"
    _HANDLER = '<img src="x" onerror="console.log(1)">'

    @pytest.mark.parametrize(
        "hidden",
        [
            "<style><!-- </style>{code}<!-- -->",
            "<title><!-- </title>{code}<!-- -->",
            "<xmp><!-- </xmp>{code}<!-- -->",
            "<iframe><!-- </iframe>{code}<!-- -->",
            "<noembed><!-- </noembed>{code}<!-- -->",
            "<noframes><!-- </noframes>{code}<!-- -->",
            "<noscript><!-- </noscript>{code}<!-- -->",
            "<svg><![CDATA[><!-- ]]>{code}<!-- -->",
            "<math><![CDATA[><!-- ]]>{code}<!-- -->",
            '<svg><script type="text/plain">{code}</script></svg>',
        ],
    )
    @pytest.mark.parametrize("around", ["<select>{}</select>", "<select><option>{}</option></select>"])
    @pytest.mark.parametrize("code", [_SCRIPT, _HANDLER])
    @pytest.mark.parametrize("route", ["markup", "srcdoc", "data"])
    def test_forbid_rejects_code_only_a_browser_that_keeps_these_tags_sees(self, hidden, around, code, route):
        page = around.format(hidden.format(code=code))
        if route == "markup":
            template, data = "{{ value }}", {"value": Markup(page)}  # noqa: S704 - a fixed test document
        elif route == "srcdoc":
            template, data = '<iframe c-srcdoc="value"></iframe>', {"value": page}
        else:
            template, data = '<iframe c-src="value"></iframe>', {"value": "data:text/html," + quote(page)}
        with pytest.raises(ValueError, match="security_javascript='forbid'"):
            _render_under_javascript_policy("forbid", template, data)

    def test_strict_csp_reports_a_handler_only_a_browser_that_keeps_these_tags_sees(self):
        class Page(Component):
            citry = Citry(security_csp="strict")
            template = """
                {{ value }}
            """

            def template_data(self, kwargs, slots):
                return {"value": Markup(f"<select><style><!-- </style>{TestSelectContents._HANDLER}<!-- --></select>")}  # noqa: S704 - a fixed test document

        with pytest.raises(ValueError, match="onerror"):
            Page().render().serialize(deps_strategy="ignore")

    def test_a_finding_only_one_reading_makes_is_reported_once(self):
        page = Markup(f"<select><style><!-- </style>{self._SCRIPT}{self._HANDLER}<!-- --></select>")  # noqa: S704 - a fixed test document
        with pytest.warns(RuntimeWarning) as caught:
            _render_under_javascript_policy("warn", "{{ value }}", {"value": page})
        message = str(caught[0].message)
        assert message.count("raw executable <script>") == 1
        assert message.count("event attribute 'onerror'") == 1

    def test_a_script_both_readings_see_is_reported_once(self):
        page = Markup(f"<select>{self._SCRIPT}</select>")  # noqa: S704 - a fixed test document
        with pytest.warns(RuntimeWarning) as caught:
            _render_under_javascript_policy("warn", "{{ value }}", {"value": page})
        assert str(caught[0].message).count("raw executable <script>") == 1

    @pytest.mark.parametrize(
        "page",
        [
            '<select name="a"><option value="1" selected>One</option><option>Two</option></select>',
            "<select><optgroup label='x'><option>One</option></optgroup><hr><option>Two</option></select>",
            "<select><button><selectedcontent></selectedcontent></button><option>One</option></select>",
            "<select><option><img src='flag.png' alt=''> <span>One</span></option></select>",
            "<select><option><svg width='9'><circle r='4'/></svg> One</option></select>",
            "<select><option>a < b</option></select>",
            "<select><style>option { color: red }</style><option>One</option></select>",
            "<SELECT><OPTION>One</OPTION></SELECT>",
            "<table><tr><td><select><option>One</option></select></td></tr></table>",
            "<form><select name='a'><option>One</option></select><input type='hidden' name='b'></form>",
        ],
    )
    def test_forbid_passes_a_select_that_runs_no_code(self, page):
        assert "ption" in _render_under_javascript_policy("forbid", "{{ value }}", {"value": Markup(page)}).lower()  # noqa: S704 - a fixed test document


class TestBrowserDifferencesAroundSvgAndMathml:
    """Browsers differ from html5ever, and from each other, on a few end tags in SVG and MathML."""

    @pytest.mark.parametrize(
        "page",
        [
            # Every browser keeps these elements open.
            "<span><math><mtext></span><![CDATA[><!-- ]]><script>console.log(1)</script><!-- -->",
            "<li><svg><desc><li></li><![CDATA[><!-- ]]><script>console.log(1)</script><!-- -->",
            # Firefox leaves the SVG here, and Chromium stays in it.
            "<svg><a><title></p></a><style><!-- </style><script>console.log(1)</script><!-- -->",
            # Chromium stays in the SVG here, and Firefox leaves it.
            "<clippath><svg></clippath><style><img src=x onerror=console.log(1)></style>",
        ],
    )
    def test_forbid_rejects_code_a_browser_finds_there(self, page):
        with pytest.raises(ValueError, match="security_javascript='forbid'"):
            _render_under_javascript_policy("forbid", "{{ value }}", {"value": Markup(page)})  # noqa: S704 - a fixed test document

    @pytest.mark.parametrize(
        "page",
        [
            "<svg><title>A <b>bold</b> title</title><clipPath id='a'><rect/></clipPath></svg>",
            "<svg><foreignObject><div><p>One<p>Two</div></foreignObject></svg>",
            "<ul><li><svg><desc>x</desc></svg><li>Two</ul>",
            "<span><svg><circle r='1'></svg></span>",
            "<math><mi>x</mi><mo>=</mo><mn>1</mn></math><p>After</p>",
        ],
    )
    def test_forbid_passes_ordinary_svg_and_mathml(self, page):
        rendered = _render_under_javascript_policy("forbid", "{{ value }}", {"value": Markup(page)})  # noqa: S704 - a fixed test document
        assert page[-8:] in rendered

    # In Chromium 156, Firefox 157, or both, each page below builds a
    # different tree from the one html5ever builds, and runs the script
    # html5ever hides. The check refuses the tag where the trees differ, and
    # the message names what to change there.
    @pytest.mark.parametrize(
        ("shape", "message"),
        [
            ("<math><annotation-xml encoding=text/html></br>{cdata}", "<annotation-xml> whose encoding"),
            ("<math><annotation-xml encoding=application/xhtml+xml><svg><br>{cdata}", "<annotation-xml> whose"),
            ("<select></b><math><annotation-xml></select>{cdata}", "'select' end tag is inside an open MathML"),
            ("<p><b></p><svg></b>{style}", "around this 'svg' element"),
            ("<foreignObject><a></foreignobject><math></a><noscript><!-- </noscript>{code}", "around this 'math'"),
            ("<svg><desc><span><isindex></span>{cdata}", "<isindex> as an ordinary element"),
            ("<svg><desc><span><search></span></desc>{style}", "'span' tag reaches past an open <search>"),
            ("<select><option><dd><option><svg><g></dd>{cdata}", "browsers close an element such as <p>"),
            ("<select><b></select>x<svg></b>{style}", "open across the start or end of a <select>"),
            ("<svg><desc><p><b></p></b></desc></svg>x<svg><g></b>{cdata}", "'b' end tag is inside an SVG"),
            ("<svg><desc><b><b><b><b>x</b></b></b></b></desc></svg>{cdata}", "four or more copies of one formatting"),
            (
                '<div><template shadowrootmode="open"><thead><caption><svg><g></caption>{style}</template></div>',
                "a <thead> is open here with no <table>",
            ),
            (
                '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" ""><span><p><table></table>'
                "<svg><g></span>{cdata}",
                "doctype makes some browsers use quirks mode",
            ),
        ],
    )
    @pytest.mark.parametrize("route", ["markup", "srcdoc"])
    def test_forbid_rejects_a_tag_where_browsers_build_a_different_tree(self, shape, message, route):
        code = '<img src="x" onerror="console.log(1)">'
        page = shape.format(
            cdata=f"<![CDATA[><!-- ]]>{code}<!-- -->",
            style=f"<style><!-- </style>{code}<!-- -->",
            code=code,
        )
        if route == "markup":
            with pytest.raises(ValueError, match=re.escape(message)):
                _render_under_javascript_policy("forbid", "{{ value }}", {"value": Markup(page)})  # noqa: S704 - a fixed test document
        else:
            with pytest.raises(ValueError, match="embedded document"):
                _render_under_javascript_policy("forbid", '<iframe c-srcdoc="value"></iframe>', {"value": page})

    # The check reads the open <form> and the closed <b> the way browsers
    # do, so it finds the script itself.
    @pytest.mark.parametrize(
        "page",
        [
            "<math><mtext><form></form><![CDATA[><!-- ]]><script>console.log(1)</script><!-- -->",
            "<svg><desc><p><b></p></desc><style><script>console.log(1)</script></style>",
        ],
    )
    def test_forbid_rejects_code_after_a_form_or_a_closed_formatting_element(self, page):
        with pytest.raises(ValueError, match="raw executable"):
            _render_under_javascript_policy("forbid", "{{ value }}", {"value": Markup(page)})  # noqa: S704 - a fixed test document

    # An app's own `innerHTML` puts the page into another page's body, and
    # Vue builds an opaque HTML block inside a `<template>`. In both places
    # the same markup can build a different tree. A whole document hides
    # each script below. The first two run in a body in Chromium 156 and
    # Firefox 157; the `<noscript>` page runs only in Chromium, inside a
    # template.
    @pytest.mark.parametrize(
        "page",
        [
            '<frameset><textarea><!-- </textarea><img src="x" onerror="console.log(1)"><!-- -->',
            '<span><p><table></table><svg><g></span><style><!--</style><img src="x" onerror="console.log(1)"><!-- -->',
            # Chromium builds Vue's opaque HTML blocks with `template.innerHTML`, which reads `<noscript>`
            # contents as markup.
            '<noscript><img src="x" onerror="console.log(1)"></noscript>',
        ],
    )
    def test_forbid_rejects_code_that_runs_when_the_page_is_put_into_a_body(self, page):
        with pytest.raises(ValueError, match="native inline event attribute 'onerror'"):
            _render_under_javascript_policy("forbid", "{{ value }}", {"value": Markup(page)})  # noqa: S704 - a fixed test document

    def test_warn_reports_a_tag_where_browsers_build_a_different_tree(self):
        page = Markup("<p><b>Bold</p><svg><circle r='1'/></svg>")
        with pytest.warns(RuntimeWarning, match="around this 'svg' element"):
            _render_under_javascript_policy("warn", "{{ value }}", {"value": page})

    def test_warn_lists_a_tag_two_readings_find_once(self):
        # Two readings of this page find the `<select>` start tag under two
        # different cases. It is one place to fix, so it is listed once.
        page = Markup(
            "<thead><select><i><i><th><i><i></i><i><math><form><annotation-xml encoding=text/html></select></x>"
            "<table><tr></p><svg>"
        )
        with pytest.warns(RuntimeWarning) as warned:
            _render_under_javascript_policy("warn", "{{ value }}", {"value": page})
        message = str(warned[0].message)
        assert "found 5 client behavior requirement(s)" in message
        assert sum("'select'" in line for line in message.splitlines()) == 1

    def test_a_tag_name_in_the_message_is_quoted(self):
        # The page chooses the tag name, so the message shows it as a quoted
        # string, and a control character in it cannot reach a log as is.
        page = Markup("<svg><desc><b><span><b><b><b></span></x\x1b[31mRED\x1b[0m>")
        with pytest.raises(ValueError, match="cannot tell what the page runs") as raised:
            _render_under_javascript_policy("forbid", "{{ value }}", {"value": page})
        assert "\x1b" not in str(raised.value)
        assert "\\x1b" in str(raised.value)
        with pytest.warns(RuntimeWarning) as warned:
            _render_under_javascript_policy("warn", "{{ value }}", {"value": page})
        assert all("\x1b" not in str(warning.message) for warning in warned)

    @pytest.mark.parametrize(
        "page",
        [
            "<math><semantics><mi>x</mi><annotation-xml encoding='MathML-Content'><ci>x</ci></annotation-xml>"
            "</semantics></math>",
            "<p><b>Bold</b></p><svg><circle r='1'/></svg>",
            "<p><b>Bold</p> <svg><circle r='1'/></svg>",
            "<search><form><input name='q'><button><svg><path d='M0 0'/></svg></button></form></search>",
            "<table><thead><tr><th>A</th></tr></thead><tbody><tr><td>1</td></tr></tbody></table>",
            "<!DOCTYPE html><p>Before</p><table><tr><td>1</td></tr></table>",
            "<!DOCTYPE html><p>Before<table><tr><td>1</td></tr></table>",
            "<p>Before<table><tr><td>1</td></tr></table>",
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" '
            '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><p>Text<table><tr><td>1</td></tr></table>',
            '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">'
            "<p>Text<table><tr><td>1</td></tr></table>",
            "<html><head><title>T</title></head><body><p>Body</p></body></html>",
            "<select><option>One<option>Two</select>",
        ],
    )
    def test_forbid_passes_ordinary_markup_like_the_refused_pages(self, page):
        rendered = _render_under_javascript_policy("forbid", "{{ value }}", {"value": Markup(page)})  # noqa: S704 - a fixed test document
        assert page[-8:] in rendered


class TestUtf16Text:
    """A response that names UTF-16 makes text with NUL bytes into markup."""

    _SCRIPT = "<script>console.log(1)</script>"

    @pytest.mark.parametrize("spell", ["\0".join(_SCRIPT) + "\0", "\0" + "\0".join(_SCRIPT)])
    def test_forbid_rejects_a_tag_spelled_with_nul_bytes(self, spell):
        with pytest.raises(ValueError, match="another encoding"):
            _render_under_javascript_policy("forbid", "{{ value }}", {"value": Markup(spell)})  # noqa: S704 - a fixed test document

    @pytest.mark.parametrize("value", ["\0", "a\0", "\0a", "<\0s\0", "\0".join(_SCRIPT)])
    @pytest.mark.parametrize("template", ["<p>{{ value }}</p>", '<p c-title="value">x</p>'])
    def test_forbid_passes_an_escaped_value_that_holds_nul(self, template, value):
        assert "<p" in _render_under_javascript_policy("forbid", template, {"value": value})


class TestSvgAnimationUrls:
    """
    An SVG `<animate>` or `<set>` that sets `href` to a `javascript:` URL.

    The animation writes its value into the link's `href` while the page is
    open, so the output checks read it the way they read a plain `href`.
    """

    _ANIMATIONS = [
        '<svg><a><animate attributeName="href" values="javascript:run()" dur="1s"/></a></svg>',
        '<svg><a><animate attributeName="href" to="javascript:run()" dur="1s" fill="freeze"/></a></svg>',
        '<svg><a><animate attributeName="href" from="javascript:run()" to="#x" dur="60s"/></a></svg>',
        '<svg><a><animate attributeName="href" by="javascript:run()" dur="1s"/></a></svg>',
        '<svg><a><set attributeName="href" to="javascript:run()"/></a></svg>',
        '<svg><a><set attributeName="xlink:href" to="javascript:run()"/></a></svg>',
        '<svg><a id="a"></a><set href="#a" attributeName="href" to="javascript:run()"/></svg>',
        # `values` is a list split on `;`, so a later item counts too.
        '<svg><a><animate attributeName="href" values="#a; #b ;javascript:run();#c" dur="1s"/></a></svg>',
        # The browser decodes character references in both attributes.
        '<svg><a><set attributeName="hr&#101;f" to="java&#115;cript&colon;run()"/></a></svg>',
        '<svg><a><set attributeName="href" to="java&#9;script:run()"/></a></svg>',
        '<svg><a><set attributeName="href" to="  &#1;JAVASCRIPT:run()"/></a></svg>',
        # Chromium and Firefox did not run these spellings, but the check
        # reports them anyway.
        '<svg><a><set attributeName="HREF" to="javascript:run()"/></a></svg>',
        '<svg><a><set attributeName=" xlink:href " to="javascript:run()"/></a></svg>',
        # Only the first attributeName counts, as in the browser.
        '<svg><a><set attributeName="href" attributeName="x" to="javascript:run()"/></a></svg>',
    ]
    _INERT_ANIMATIONS = [
        '<svg><a><set attributeName="href" to="#x"/></a></svg>',
        '<svg><a><animate attributeName="href" values="#a;#b" dur="1s"/></a></svg>',
        # Only `href` and `xlink:href` are links.
        '<svg><rect><set attributeName="fill" to="javascript:run()"/></rect></svg>',
        '<svg><a><set attributeName="x" attributeName="href" to="javascript:run()"/></a></svg>',
        '<svg><a><set attributeName="href"/></a></svg>',
        '<svg><a><set to="javascript:run()"/></a></svg>',
        # A control character inside the scheme is not `javascript:`.
        '<svg><a><set attributeName="href" to="java\x01script:run()"/></a></svg>',
        '<svg><a><set attributeName="href" to="javascript"/></a></svg>',
        '<svg><a><set attributeName="href" to="/javascript:run()"/></a></svg>',
        # Not an attribute that holds a value to set.
        '<svg><a><set attributeName="href" title="javascript:run()"/></a></svg>',
        # `animateTransform` sets a transform, not a link.
        '<svg><rect><animateTransform attributeName="transform" to="javascript:run()"/></rect></svg>',
    ]

    @staticmethod
    def _card(app, markup):
        class Card(Component):
            citry = app
            template = "{{ body }}"

            def template_data(self, kwargs, slots):
                return {"body": Markup(markup)}  # noqa: S704 - the test writes fixed markup

        return Card().render()

    @pytest.mark.parametrize("markup", _ANIMATIONS)
    def test_forbid_rejects_an_animation_that_sets_a_javascript_url(self, markup):
        rendered = self._card(Citry(security_javascript="forbid"), markup)
        with pytest.raises(ValueError, match="javascript: URL"):
            rendered.serialize(deps_strategy="ignore")

    @pytest.mark.parametrize("markup", _ANIMATIONS)
    def test_warn_reports_an_animation_that_sets_a_javascript_url(self, markup):
        rendered = self._card(Citry(security_javascript="warn"), markup)
        with pytest.warns(RuntimeWarning, match="javascript: URL"):
            rendered.serialize(deps_strategy="ignore")

    @pytest.mark.parametrize("markup", _ANIMATIONS)
    def test_strict_csp_rejects_an_animation_that_sets_a_javascript_url(self, markup):
        rendered = self._card(Citry(security_csp="strict"), markup)
        with pytest.raises(ValueError, match="javascript: URL"):
            rendered.serialize(deps_strategy="ignore", csp_nonce="requestNonce")

    @pytest.mark.parametrize("markup", _INERT_ANIMATIONS)
    def test_an_animation_that_sets_no_javascript_url_passes(self, markup):
        # Both checks run, so one test shows neither reports the page.
        for app, options in (
            (Citry(security_javascript="forbid"), {}),
            (Citry(security_csp="strict"), {"csp_nonce": "requestNonce"}),
        ):
            self._card(app, markup).serialize(deps_strategy="ignore", **options)

    def test_the_finding_names_the_attribute_that_holds_the_url(self):
        rendered = self._card(
            Citry(security_javascript="forbid"),
            '<svg><a><set attributeName="href" to="javascript:run()"/></a></svg>',
        )
        with pytest.raises(ValueError, match="attribute 'to'"):
            rendered.serialize(deps_strategy="ignore")

    def test_an_embedded_document_with_such_an_animation_is_reported(self):
        document = '<svg><a><set attributeName="href" to="javascript:run()"/></a></svg>'
        escaped = document.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        rendered = self._card(Citry(security_javascript="forbid"), f'<iframe srcdoc="{escaped}"></iframe>')
        with pytest.raises(ValueError, match="embedded document"):
            rendered.serialize(deps_strategy="ignore")


class TestEmbeddedDataUrlDocuments:
    """
    A `data:` URL in a frame, a link, a form, or a meta refresh that is not plain HTML.

    The browser runs the scripts of an SVG or other XML document there, and
    Firefox reads some unknown types as HTML. The check reads only HTML, so
    it reports every such document, with or without a script. A type the
    browser shows as text, an image, media, or a download is not reported.
    """

    # An SVG document whose script calls `run()`.
    _SVG = "%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3Cscript%3Erun()%3C/script%3E%3C/svg%3E"
    _SCRIPT = "%3Cscript%3Erun()%3C/script%3E"
    _UNREAD_DOCUMENTS = [
        f'<iframe src="data:image/svg+xml,{_SVG}"></iframe>',
        f'<object data="data:image/svg+xml,{_SVG}"></object>',
        f'<embed src="data:image/svg+xml,{_SVG}">',
        f'<frameset><frame src="data:image/svg+xml,{_SVG}"></frameset>',
        f'<iframe src="data:application/xhtml+xml,{_SVG}"></iframe>',
        f'<iframe src="data:text/xml,{_SVG}"></iframe>',
        f'<iframe src="data:application/xml,{_SVG}"></iframe>',
        # Any type whose subtype ends in `+xml` loads as XML.
        f'<iframe src="data:application/rss+xml,{_SVG}"></iframe>',
        # Chromium runs a `text/xsl` document too.
        f'<iframe src="data:text/xsl,{_SVG}"></iframe>',
        # Firefox reads these as HTML; other unknown types count as well.
        f'<iframe src="data:*/*,{_SCRIPT}"></iframe>',
        f'<iframe src="data:application/x-unknown-content-type,{_SCRIPT}"></iframe>',
        # The type is read without case, parameters, or spaces around it.
        f'<iframe src="DATA:Image/SVG+XML;charset=utf-8,{_SVG}"></iframe>',
        f'<iframe src="data: image/svg+xml ;base64,{base64.b64encode(b"<svg/>").decode()}"></iframe>',
        # The browser drops tabs and line breaks anywhere in the URL.
        f'<iframe src="da&#9;ta:image/svg+xml,{_SVG}"></iframe>',
        # A document without a script counts too.
        '<iframe src="data:image/svg+xml,%3Csvg/%3E"></iframe>',
    ]
    _HTML_WITH_SCRIPT = [
        # Tabs and line breaks are dropped, also inside the type and payload.
        f'<iframe src="data:text/ht&#10;ml,{_SCRIPT}"></iframe>',
        '<iframe src="data:text/html,&lt;scr&#9;ipt&gt;run()&lt;/script&gt;"></iframe>',
        # Spaces before `base64` still mark base64.
        '<iframe src="data:text/html; base64,PHNjcmlwdD5ydW4oKTwvc2NyaXB0Pg=="></iframe>',
        # UTF-16, by charset or byte order mark, and an ISO-2022-JP escape.
        '<iframe src="data:text/html;charset=utf-16le,%3C%00s%00c%00r%00i%00p%00t%00%3E%00"></iframe>',
        '<iframe src="data:text/html,%FF%FE%3C%00s%00c%00r%00i%00p%00t%00%3E%00"></iframe>',
        '<iframe src="data:text/html,%3Cscr%1B(Bipt%3Erun()%3C/script%3E"></iframe>',
    ]
    # A link or form opens a `data:` document in a frame, which `target` or
    # `<base target>` can pick, and a meta refresh opens one in the page's
    # own frame, so each counts like a frame's URL.
    _OPENED_DOCUMENTS = [
        f'<a href="data:image/svg+xml,{_SVG}">x</a>',
        f'<a target="f" href="data:text/html,{_SCRIPT}">x</a>',
        f'<map><area href="data:image/svg+xml,{_SVG}"></map>',
        f'<svg><a xlink:href="data:image/svg+xml,{_SVG}"></a></svg>',
        f'<form action="data:text/xml,{_SVG}"></form>',
        f'<button formaction="data:text/xml,{_SVG}">x</button>',
        f'<svg><a><set attributeName="href" to="data:image/svg+xml,{_SVG}"/></a></svg>',
        f'<meta http-equiv="refresh" content="0;url=data:image/svg+xml,{_SVG}">',
        f'<meta http-equiv="Refresh" content="0; URL=\'data:text/html,{_SCRIPT}\'">',
    ]
    _NOT_OPENED_DOCUMENTS = [
        f'<a href="data:image/png,{_SCRIPT}">x</a>',
        '<a href="data:text/html,%3Cp%3Ehi%3C/p%3E">x</a>',
        # A stylesheet or an SVG reference is not opened as a page.
        '<link rel="stylesheet" href="data:text/css,p{}">',
        f'<svg><use href="data:image/svg+xml,{_SVG}"></use></svg>',
        '<meta http-equiv="refresh" content="0;url=/next">',
        f'<meta name="refresh" content="0;url=data:text/xml,{_SVG}">',
    ]
    _NOT_DOCUMENTS = [
        # Shown as text, an image, media, or a download.
        f'<iframe src="data:image/svg,{_SVG}"></iframe>',
        f'<iframe src="data:text/plain,{_SVG}"></iframe>',
        f'<iframe src="data:,{_SVG}"></iframe>',
        f'<iframe src="data:image/png,{_SCRIPT}"></iframe>',
        f'<embed src="data:video/mp4,{_SCRIPT}">',
        f'<object data="data:application/pdf,{_SCRIPT}"></object>',
        # An image runs no script.
        f'<img src="data:image/svg+xml,{_SVG}">',
        # HTML without a script.
        '<iframe src="data:text/html; base64,PHA+aGk8L3A+"></iframe>',
    ]

    @staticmethod
    def _card(app, markup):
        class Card(Component):
            citry = app
            template = "{{ body }}"

            def template_data(self, kwargs, slots):
                return {"body": Markup(markup)}  # noqa: S704 - the test writes fixed markup

        return Card().render()

    @pytest.mark.parametrize("markup", _UNREAD_DOCUMENTS + _HTML_WITH_SCRIPT + _OPENED_DOCUMENTS)
    def test_forbid_rejects_an_embedded_document_that_may_run_code(self, markup):
        rendered = self._card(Citry(security_javascript="forbid"), markup)
        with pytest.raises(ValueError, match="embedded document"):
            rendered.serialize(deps_strategy="ignore")

    @pytest.mark.parametrize("markup", _UNREAD_DOCUMENTS + _HTML_WITH_SCRIPT + _OPENED_DOCUMENTS)
    def test_warn_reports_an_embedded_document_that_may_run_code(self, markup):
        rendered = self._card(Citry(security_javascript="warn"), markup)
        with pytest.warns(RuntimeWarning, match="embedded document"):
            rendered.serialize(deps_strategy="ignore")

    @pytest.mark.parametrize("markup", _NOT_DOCUMENTS + _NOT_OPENED_DOCUMENTS)
    def test_forbid_passes_a_data_url_that_runs_no_code(self, markup):
        self._card(Citry(security_javascript="forbid"), markup).serialize(deps_strategy="ignore")

    def test_an_svg_document_inside_an_embedded_html_document_is_reported(self):
        inner = f'<iframe src="data:image/svg+xml,{self._SVG}"></iframe>'
        escaped = inner.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")
        rendered = self._card(Citry(security_javascript="forbid"), f'<iframe srcdoc="{escaped}"></iframe>')
        with pytest.raises(ValueError, match="embedded document"):
            rendered.serialize(deps_strategy="ignore")
