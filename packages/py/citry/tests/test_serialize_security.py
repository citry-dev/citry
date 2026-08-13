"""Focused security metadata, SRI, and trusted-tag reconciliation tests."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from typing import TYPE_CHECKING

import pytest

from citry import Citry, Component, Extension, Markup
from citry.ext.dependencies import Script, Style
from citry.ext.dependencies.scripts import gen_cache_key
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
                self.calls += 1
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
        assert script.calls == 1

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

    def test_fragment_descriptors_and_preloader_use_owned_integrity(self):
        c = Citry(security_script_integrity="citry")
        c.set_mounted_prefix("/citry")

        class Widget(Component):
            citry = c
            template = "<p>widget</p>"
            js = "$component(() => {});"

            def js_data(self, kwargs, slots):
                return {"count": 2}

        result = Widget().render().serialize_result(deps_strategy="fragment")
        descriptors = _fetch_descriptors(result.html, "js")
        external_records = {record.url: record for record in result.security.scripts if record.url is not None}

        for descriptor in descriptors:
            attrs = descriptor["attrs"]
            assert isinstance(attrs, dict)
            url = attrs["src"]
            assert isinstance(url, str)
            digest = _sha384(_serve(c, url).body)
            assert attrs["integrity"] == digest
            assert external_records[url].digests == (digest,)

        runtime_digest = _sha384(_serve(c, "/citry/citry.js").body)
        assert f's.integrity = "{runtime_digest}";' in result.html
        assert all("data-citry-security-" not in json.dumps(descriptor) for descriptor in descriptors)
        assert result.security.scripts[0].location == "inline"
        assert result.security.scripts[1].url == "/citry/citry.js"

    def test_mounted_document_runtimes_match_their_route_bodies(self):
        c = Citry(security_script_integrity="citry")
        c.set_mounted_prefix("/citry")

        class Widget(Component):
            citry = c
            template = '<button @click="open = true">open</button>'

        result = Widget().render().serialize_result()

        for url in ("/citry/citry.js", "/citry/ext/events/runtime.js"):
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

    def test_missing_fragment_variable_bytes_keep_legacy_output_but_fail_integrity(self):
        c = Citry()
        c.set_mounted_prefix("/citry")

        class Widget(Component):
            citry = c
            template = "<p>widget</p>"
            js = "$component(() => {});"

            def js_data(self, kwargs, slots):
                return {"count": 2}

        rendered = Widget().render()
        record = next(iter(rendered.context.extra["dependencies"]))
        assert record.js_vars_hash is not None
        c.cache.delete(gen_cache_key(Widget.class_id, "js", record.js_vars_hash))

        legacy = rendered.serialize(deps_strategy="fragment")
        legacy_urls = [descriptor["attrs"]["src"] for descriptor in _fetch_descriptors(legacy, "js")]
        assert any(f".{record.js_vars_hash}.js" in url for url in legacy_urls)

        secured = Widget().render()
        secured_record = next(iter(secured.context.extra["dependencies"]))
        assert secured_record.js_vars_hash is not None
        c.cache.delete(gen_cache_key(Widget.class_id, "js", secured_record.js_vars_hash))
        with pytest.raises(RuntimeError, match="Cannot prove the response bytes"):
            secured.serialize_result(deps_strategy="fragment", security_script_integrity="citry")

    def test_owned_declared_integrity_mismatch_fails(self):
        bad = _sha384(b"not the owned body")

        class DeclareWrongDigest(Extension):
            name = "declare_wrong_digest"

            def on_dependencies(self, ctx):
                for script in ctx.scripts:
                    if isinstance(script, Script) and script._owned_resource is not None:
                        script.attrs["integrity"] = bad

        c = Citry(extensions=[DeclareWrongDigest], security_script_integrity="citry")
        c.set_mounted_prefix("/citry")

        class Widget(Component):
            citry = c
            template = "<p>widget</p>"
            js = "$component(() => {});"

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

    def test_nonces_structured_scripts_and_inline_styles_but_not_raw_markup_or_links(self):
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
        assert '<link rel="stylesheet" href="https://cdn.example.test/chart.css"/>' in result.html
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

    def test_nonced_style_is_materialized_once(self):
        class StatefulStyle(Style):
            calls = 0

            def _render(self):
                self.calls += 1
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
        assert style.calls == 1

    def test_fragment_nonce_reaches_preloader_manifests_and_created_dependencies(self):
        nonce = "fragmentNonce"
        c = Citry()
        c.set_mounted_prefix("/citry")

        class Card(Component):
            citry = c
            template = "<p>card</p>"
            js = "$component(() => {});"

            class Dependencies:
                js = [Script(content="globalThis.inlineDependency = true;", wrap=False)]
                css = [
                    Style(content=".inline { color: green; }"),
                    Style(url="https://cdn.example.test/card.css"),
                ]

        result = Card().render().serialize_result(deps_strategy="fragment", csp_nonce=nonce)
        js_descriptors = _fetch_descriptors(result.html, "js")
        css_descriptors = _fetch_descriptors(result.html, "css")

        assert f's.nonce = "{nonce}";' in result.html
        top_level_scripts = re.findall(r"<script\b([^>]*)>", result.html)
        assert top_level_scripts
        assert all(f'nonce="{nonce}"' in attrs for attrs in top_level_scripts)
        assert all(descriptor["attrs"]["nonce"] == nonce for descriptor in js_descriptors)
        inline_style = next(descriptor for descriptor in css_descriptors if descriptor["tag"] == "style")
        external_link = next(descriptor for descriptor in css_descriptors if descriptor["tag"] == "link")
        assert inline_style["attrs"]["nonce"] == nonce
        assert "nonce" not in external_link["attrs"]

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
    def test_warn_reports_but_preserves_standard_output(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = """
                <button @click="items.map(item => item.id)">Save</button>
            """

        rendered = Card().render()
        ordinary = rendered.serialize(security_csp="off")
        with pytest.warns(RuntimeWarning, match="arrow functions"):
            warned = rendered.serialize(security_csp="warn")

        assert warned == ordinary
        assert "Citry events CSP client runtime" not in warned

    def test_strict_rejects_incompatible_expression_at_its_token(self):
        c = Citry(security_csp="strict")

        class Card(Component):
            citry = c
            template = """
                <button @click="items.map(item => item.id)">Save</button>
            """

        with pytest.raises(ValueError, match=r"Card, attribute '@click', settled HTML bytes .*arrow functions"):
            Card().render().serialize(deps_strategy="simple")

    def test_strict_classifies_browser_decoded_attribute_values(self):
        c = Citry(security_csp="strict")

        class Card(Component):
            citry = c
            template = """
                <button @click="items.map(item =&gt; item.id)">Save</button>
            """

        with pytest.raises(ValueError, match=r"Card, attribute '@click', settled HTML bytes .*arrow functions"):
            Card().render().serialize(deps_strategy="simple")

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

    def test_strict_checks_component_boundary_expression_that_is_not_final_html(self):
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

        with pytest.raises(ValueError, match="arrow functions"):
            Parent().render().serialize(deps_strategy="simple")

    def test_reached_diagnostic_names_component_attribute_and_source_range(self):
        c = Citry(security_csp="strict")

        class Child(Component):
            citry = c
            template = "<button>Child</button>"

        class Parent(Component):
            citry = c
            template = '<c-child @click="items.map(item => item.id)" />'

        with pytest.raises(ValueError, match="arrow functions") as error:
            Parent().render().serialize(deps_strategy="simple")

        assert "Parent" in str(error.value)
        assert "attribute '@click'" in str(error.value)
        assert "source bytes" in str(error.value)

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

    def test_entity_expansion_reports_the_complete_raw_entity_span(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<button @click="&NotEqualTilde;">Save</button>'

        rendered = Card().render()
        ordinary = rendered.serialize(deps_strategy="simple", security_csp="off")
        start = ordinary.encode().index(b"&NotEqualTilde;")
        end = start + len(b"&NotEqualTilde;")

        with pytest.raises(ValueError, match="cannot evaluate") as error:
            rendered.serialize(deps_strategy="simple", security_csp="strict")

        assert f"settled HTML bytes {start}:{end}" in str(error.value)

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

    def test_strict_selects_csp_runtime_for_mounted_and_inline_documents(self):
        for mounted in (False, True):
            c = Citry(security_csp="strict")
            if mounted:
                c.set_mounted_prefix("/citry")

            class Card(Component):
                citry = c
                template = """
                    <div x-data="{ count: 0 }" x-text="count"></div>
                """

            html = Card().render().serialize(csp_nonce="requestNonce")
            assert ('src="/citry/ext/events/runtime-csp.js"' in html) is mounted
            assert ("Citry events CSP client runtime" in html) is not mounted
            assert 'data-citry-alpine-runtime="csp"' in html
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
                <div x-data="{}"></div>
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
                <div x-data="{}"></div>
            """

        html = Card().render().serialize(deps_strategy="fragment", csp_nonce="requestNonce")
        manifest = _manifest(html)
        descriptors = _fetch_descriptors(html, "js")

        assert "document.currentScript.remove()" not in html
        assert manifest["alpineRuntime"] == "csp"
        assert any(descriptor["attrs"].get("src") == "/citry/ext/events/runtime-csp.js" for descriptor in descriptors)


class TestJavascriptDeliveryPolicy:
    @pytest.mark.parametrize("strategy", ["document", "simple", "fragment", "ignore"])
    def test_warn_preserves_allow_bytes(self, strategy):
        c = Citry()
        c.set_mounted_prefix("/citry")

        class Card(Component):
            citry = c
            template = '<main x-data="{}"><button @click="save()">Save</button></main>'
            js = "globalThis.cardReady = true;"
            css = ".card { color: rebeccapurple; }"

        rendered = Card().render()
        allowed = rendered.serialize(deps_strategy=strategy, security_javascript="allow")
        with pytest.warns(RuntimeWarning, match="security_javascript='warn'"):
            warned = rendered.serialize(deps_strategy=strategy, security_javascript="warn")

        assert warned == allowed

    @pytest.mark.parametrize("strategy", ["document", "simple", "fragment"])
    def test_omit_keeps_html_and_css_without_managed_javascript(self, strategy):
        c = Citry(security_javascript="omit")

        class Card(Component):
            citry = c
            template = '<main x-data="{}"><p>Server fallback</p></main>'
            js = "globalThis.cardReady = true;"
            css = "p { color: rebeccapurple; }"

        html = Card().render().serialize(deps_strategy=strategy)

        assert "Server fallback" in html
        assert 'x-data="{}"' in html
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
            ("<div x-cloak>Hidden</div>", "x-cloak"),
            ('<button @click="save()">Save</button>', "@click"),
            ('<button onclick="save()">Save</button>', "native inline event"),
            ('<a href="javascript:save()">Save</a>', "javascript: URL"),
            ('<script type="module">save()</script>', "raw executable"),
            ('<div x-unknown-plugin="value"></div>', "x-unknown-plugin"),
        ],
    )
    def test_forbid_rejects_settled_activation_paths(self, template, message):
        c = Citry(security_javascript="forbid")

        class Card(Component):
            citry = c

        Card.template = template
        with pytest.raises(ValueError, match=message):
            Card().render().serialize(deps_strategy="ignore")

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

        with pytest.raises(ValueError, match=r"browser handler|data-cev-on"):
            Card().render().serialize(deps_strategy="ignore")

    def test_omit_composes_with_strict_csp_and_integrity(self):
        c = Citry(
            security_csp="strict",
            security_javascript="omit",
            security_script_integrity="citry",
        )

        class Card(Component):
            citry = c
            template = '<main x-data="items.map(item => item.id)">Fallback</main>'
            js = "globalThis.managed = true;"
            css = "main { color: purple; }"

        result = Card().render().serialize_result(csp_nonce="requestNonce")
        assert 'x-data="items.map(item => item.id)"' in result.html
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
        assert "globalThis.cardReady" in allowed
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
                ctx.before_manifest.append(
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
        with pytest.raises(ValueError, match="embedded HTML document"):
            Card().render().serialize(deps_strategy="ignore")
