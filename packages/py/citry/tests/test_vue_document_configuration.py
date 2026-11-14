"""Tests for how a Vue document app receives its start configuration."""

import base64
import hashlib
import json
import math
import re
from types import SimpleNamespace

import pytest

from citry import Citry, Component
from citry._vue.serialization import _reserve_vue_app_id
from citry.ext.dependencies.routes import SHARED_RUNTIME
from citry.util.html import script_json

# Strings that would end or hide a script element's text if the JSON carried
# them unescaped, plus the two line separators older JavaScript parsers reject.
HOSTILE = {
    "close": "</script><script>globalThis.pwned = 1</script>",
    "close_upper": "</SCRIPT >",
    "comment": "<!--<script>",
    "open": "<script>",
    "separators": "a\u2028b\u2029c",
}

_BLOCK_RE = re.compile(
    r'<script type="application/json" data-citry-vue-document="(?P<app>[^"]+)"(?P<attrs>[^>]*)>'
    r"(?P<json>.*?)</script>"
    r'<script type="module"(?P<start_attrs>[^>]*)>(?P<start>.*?)</script>',
    re.DOTALL,
)


def _page(registry: Citry, data: dict[str, object]) -> type[Component]:
    class Page(Component):
        citry = registry
        template = """
<!doctype html>
<html>
  <head></head>
  <body><p :title="label">ready</p></body>
</html>
"""

        def js_data(self, kwargs, slots):
            return {"label": "ready", **data}

    return Page


def _blocks(html: str) -> list[re.Match[str]]:
    return list(_BLOCK_RE.finditer(html))


def test_document_sends_one_data_block_followed_by_a_start_script() -> None:
    html = _page(Citry(autodiscover=False), {})().render().serialize()

    [match] = _blocks(html)
    app_id = match["app"]
    # The start script names its own block; the host and the manifest agree.
    assert match["start"] == f'__citryRuntime.startDocument("{app_id}");'
    configuration = json.loads(match["json"])
    assert configuration["manifest"]["appId"] == app_id
    assert configuration["host"] == f"#citry-vue-{app_id}"
    assert f'<div id="citry-vue-{app_id}"' in html
    # The configuration travels only in the data block.
    assert "__citryRuntime.startPrepared(" not in html


def test_hostile_strings_cannot_end_the_data_block_and_round_trip() -> None:
    html = _page(Citry(autodiscover=False), {"hostile": HOSTILE})().render().serialize()

    [match] = _blocks(html)
    text = match["json"]
    lowered = text.lower()
    for sequence in ("</script", "<!--", "<script"):
        assert sequence not in lowered
    # U+2028 and U+2029 are written as escapes, never raw.
    assert "\u2028" not in text
    assert "\u2029" not in text
    assert "\\u2028" in text
    assert "\\u2029" in text
    # The whole page still has exactly one start script, so the hostile text
    # did not open a new script element.
    assert html.count('<script type="module"') == 1


def test_hostile_strings_reach_the_browser_unchanged() -> None:
    html = _page(Citry(autodiscover=False), {"hostile": HOSTILE})().render().serialize()
    [match] = _blocks(html)
    decoded = json.loads(match["json"])
    # JSON.parse (json.loads here) must read back the exact original strings,
    # wherever the manifest stores them.
    found: list[object] = []

    def walk(value: object) -> None:
        if value == HOSTILE:
            found.append(value)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(decoded)
    assert found


def test_nonce_is_on_both_tags_and_the_start_script_carries_no_page_data() -> None:
    nonce = "requestNonce"
    html = _page(Citry(autodiscover=False), {"note": "row data"})().render().serialize(csp_nonce=nonce)
    [match] = _blocks(html)
    assert f'nonce="{nonce}"' in match["attrs"]
    assert f'nonce="{nonce}"' in match["start_attrs"]
    assert "row data" not in match["start"]


def test_integrity_mode_hashes_only_the_small_start_script() -> None:
    registry = Citry(autodiscover=False, security_script_integrity="citry")
    result = _page(registry, {"rows": list(range(200))})().render().serialize_result()
    [match] = _blocks(result.html)

    def source(text: str) -> str:
        return "'sha384-" + base64.b64encode(hashlib.sha384(text.encode()).digest()).decode() + "'"

    hashes = set(result.security.csp_script_hashes)
    # The start script is executable, so its exact text is a CSP hash source.
    assert source(match["start"]) in hashes
    # The data block never runs, so it is not a CSP source.
    assert source(match["json"]) not in hashes


def _mounted(**settings: object) -> Citry:
    registry = Citry(autodiscover=False, **settings)  # type: ignore[arg-type]
    registry.set_mounted_prefix("/citry")
    return registry


def _source_hash(text: str) -> str:
    return "'sha384-" + base64.b64encode(hashlib.sha384(text.encode()).digest()).decode() + "'"


def test_a_mounted_start_script_names_the_hashed_runtime_it_reports() -> None:
    html = _page(_mounted(), {})().render().serialize()

    [match] = _blocks(html)
    start = match["start"]
    url = f"/citry/{SHARED_RUNTIME.hashed_path}"
    # The page links this URL, and the report names the same one, so the
    # message tells the reader which file is missing.
    assert f'src="{url}"' in html
    # The URL is one JSON string joined to the message, so no character of it
    # can close the string.
    assert f'console.error("Citry could not load its runtime: " + {script_json(url)});' in start
    assert f'w.__citryRuntime.startDocument("{match["app"]}")' in start


def test_a_mounted_start_script_reads_both_window_names_as_own_properties() -> None:
    html = _page(_mounted(), {})().render().serialize()

    [match] = _blocks(html)
    start = match["start"]
    # A page element with id="__citryRuntime" answers the plain name, so the
    # script reads each window name only as an own property, which an element's
    # id never is.
    assert 'own.call(w, "__citryRuntime")' in start
    assert 'own.call(w, "__citryRuntimeMissing")' in start
    # Neither name is read as a bare identifier, which would find such an element.
    assert re.findall(r'(?<![\w."])__citryRuntime(?:Missing)?\b', start) == []


def test_a_mounted_start_script_text_is_locked() -> None:
    html = _page(_mounted(), {})().render().serialize()

    [match] = _blocks(html)
    url = script_json(f"/citry/{SHARED_RUNTIME.hashed_path}")
    # Locked as a whole because a host that sends CSP hashes lists the hash of
    # this exact text, and because each line is a rule: both window names are
    # read as own properties, the own property `__citryRuntimeMissing` keeps a
    # page with several apps to one report, and the script sends no request,
    # does not navigate, and stores nothing.
    assert match["start"] == (
        "var w = window, own = Object.prototype.hasOwnProperty;\n"
        f'if (own.call(w, "__citryRuntime")) w.__citryRuntime.startDocument("{match["app"]}");\n'
        'else if (!own.call(w, "__citryRuntimeMissing")) {\n'
        "  w.__citryRuntimeMissing = true;\n"
        f'  console.error("Citry could not load its runtime: " + {url});\n'
        "}"
    )


@pytest.mark.parametrize("prefix", ["/a\\b", "/a\u2028b", "/a</script", "/a<!--b"])
def test_a_mount_prefix_cannot_end_the_start_script_or_its_string(prefix: str) -> None:
    registry = Citry(autodiscover=False)
    registry.set_mounted_prefix(prefix)
    html = _page(registry, {})().render().serialize()

    [match] = _blocks(html)
    start = match["start"]
    assert "</script" not in start.lower()
    assert "<!--" not in start
    assert "\u2028" not in start
    literal = re.search(r'runtime: " \+ (".*?")\);\n', start)
    assert literal is not None
    # The string reads back as the exact URL the page links.
    assert json.loads(literal.group(1)) == f"{prefix}/{SHARED_RUNTIME.hashed_path}"


def test_a_mounted_start_script_carries_no_page_data() -> None:
    first = _blocks(_page(_mounted(), {"note": "first row"})().render().serialize())
    second = _blocks(_page(_mounted(), {"note": "second row"})().render().serialize())

    [first_match], [second_match] = first, second
    assert "first row" not in first_match["start"]
    # Every render gets its own app id, so compare the scripts with it taken out.
    # What is left depends only on the runtime URL, so two renders differ
    # only in the app id.
    assert first_match["start"].replace(first_match["app"], "APP") == second_match["start"].replace(
        second_match["app"], "APP"
    )


def test_a_mounted_start_script_is_a_csp_hash_source() -> None:
    page = _page(_mounted(security_script_integrity="citry"), {})
    result = page().render().serialize_result()

    [match] = _blocks(result.html)
    # The exact text the browser runs is what the page's CSP must allow.
    assert _source_hash(match["start"]) in result.security.csp_script_hashes
    # The data block never runs, so it is not a CSP source.
    assert _source_hash(match["json"]) not in result.security.csp_script_hashes


def test_a_mounted_start_script_carries_the_nonce() -> None:
    registry = _mounted(security_csp="strict")
    html = _page(registry, {})().render().serialize(csp_nonce="requestNonce")

    [match] = _blocks(html)
    assert 'nonce="requestNonce"' in match["start_attrs"]
    assert 'nonce="requestNonce"' in match["attrs"]
    # This is the mounted form of the script, not the one-line call.
    assert "console.error(" in match["start"]


def test_an_unmounted_document_keeps_the_one_line_start_script() -> None:
    html = _page(Citry(autodiscover=False), {})().render().serialize()

    [match] = _blocks(html)
    # The runtime is inline here, so there is no URL that could go missing and nothing to report.
    assert match["start"] == f'__citryRuntime.startDocument("{match["app"]}");'
    assert "__citryRuntimeMissing" not in html


def test_a_fragment_writes_no_start_script() -> None:
    page = _page(_mounted(), {})

    html = page().render().serialize(deps_strategy="fragment")

    # A fragment is started by the loader it carries, not by a start script,
    # and that loader reports a failed runtime itself.
    assert "startDocument" not in html
    assert "__citryRuntimeMissing" not in html
    assert _blocks(html) == []


def test_several_apps_on_one_page_each_get_their_own_block() -> None:
    registry = Citry(autodiscover=False)
    page = _page(registry, {})
    first = page().render().serialize()
    second = page().render().serialize()
    # Two independently rendered documents joined into one page (as a host
    # layout might) keep distinct app ids, so each start script finds one block.
    combined = first + second
    matches = _blocks(combined)
    assert len(matches) == 2
    assert matches[0]["app"] != matches[1]["app"]
    for match in matches:
        assert combined.count(f'data-citry-vue-document="{match["app"]}"') == 1


def test_fragment_descriptor_escapes_hostile_strings() -> None:
    registry = Citry(autodiscover=False)
    registry.set_mounted_prefix("/citry")

    class Widget(Component):
        citry = registry
        template = """
<span :title="label">w</span>
"""

        def js_data(self, kwargs, slots):
            return {"label": "w", "hostile": HOSTILE}

    html = Widget().render().serialize(deps_strategy="fragment")
    match = re.search(r'<script type="application/json" data-citry-vue-fragment>(.*?)</script>', html, re.DOTALL)
    assert match is not None
    lowered = match.group(1).lower()
    for sequence in ("</script", "<!--", "<script"):
        assert sequence not in lowered
    assert "globalThis.pwned" in json.dumps(json.loads(match.group(1)))


def test_script_json_escapes_every_less_than_sign_and_rejects_non_finite_numbers() -> None:
    assert script_json({"a": "</script><!--"}) == '{"a":"\\u003c/script>\\u003c!--"}'
    assert json.loads(script_json({"a": "</script><!--"})) == {"a": "</script><!--"}
    assert script_json({"b": 1, "a": 2}, sort_keys=True) == '{"a":2,"b":1}'
    assert script_json("\u2028") == '"\\u2028"'
    assert script_json("\u2028", ensure_ascii=False) == '"\u2028"'
    with pytest.raises(ValueError, match="Out of range float"):
        script_json(math.nan)


def test_a_preset_app_id_must_keep_the_hex_shape() -> None:
    # The id lands unescaped in the host's id attribute, so a preset value
    # that is not 32 hex characters is refused before any HTML is written.
    context = SimpleNamespace(extra={"_vue_app_id": 'x" onclick="alert(1)'})
    with pytest.raises(ValueError, match="32 lowercase hex"):
        _reserve_vue_app_id(context, Citry(autodiscover=False))  # type: ignore[arg-type]
