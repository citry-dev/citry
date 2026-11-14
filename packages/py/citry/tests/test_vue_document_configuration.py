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
from citry.serialize import serialize_render, serialize_render_result
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


def test_a_mounted_start_script_names_the_hashed_runtime_and_reads_it_as_an_own_property() -> None:
    html = _page(_mounted(), {})().render().serialize()

    [match] = _blocks(html)
    start = match["start"]
    # The runtime URL is one JSON string, so no character of it can close the string.
    assert f"var url = {script_json(f'/citry/{SHARED_RUNTIME.hashed_path}')}, " in start
    assert f'w.__citryRuntime.startDocument("{match["app"]}")' in start
    # A page element with id="__citryRuntime" answers the plain name, so
    # window names are read only as own properties, which an element's id never is.
    assert 'own.call(w, "__citryRuntime")' in start
    assert 'own.call(w, "__citryRuntimeMissing")' in start
    assert re.findall(r'(?<![\w."])__citryRuntime\b', start) == []
    # The page links the same URL the script probes.
    assert f'src="/citry/{SHARED_RUNTIME.hashed_path}"' in html


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
    literal = re.search(r'var url = (".*?"), key', start)
    assert literal is not None
    # The string reads back as the exact URL the page links.
    assert json.loads(literal.group(1)) == f"{prefix}/{SHARED_RUNTIME.hashed_path}"


@pytest.mark.parametrize(
    ("method", "can_reload"),
    [
        ("GET", True),
        ("get", True),
        ("Head", True),
        ("HEAD", True),
        ("POST", False),
        ("put", False),
        ("PATCH", False),
        ("DELETE", False),
        ("OPTIONS", False),
        ("QUERY", False),
        # Citry cannot tell what the page answers, and a browser may resend a form silently on reload.
        (None, False),
    ],
)
def test_request_method_chooses_whether_the_page_may_reload(method: str | None, can_reload: bool) -> None:
    html = _page(_mounted(), {})().render().serialize(request_method=method)

    [match] = _blocks(html)
    expected = "true" if can_reload else "false"
    # The start script runs when the runtime is missing, so it carries its own copy of the answer.
    assert f"  var canReload = {expected};\n" in match["start"]
    # The runtime reads the same answer from the data it starts with, for a missing browser plugin.
    assert json.loads(match["json"])["canReload"] is can_reload
    assert f'"canReload":{expected}' in match["json"]


def test_leaving_request_method_out_stops_the_reload() -> None:
    html = _page(_mounted(), {})().render().serialize()

    [match] = _blocks(html)
    # Chrome resends a POST on location.reload() without asking, so an unknown method never reloads.
    assert "  var canReload = false;\n" in match["start"]
    assert json.loads(match["json"])["canReload"] is False


def test_the_two_start_scripts_differ_only_in_the_reload_answer() -> None:
    page = _page(_mounted(), {})
    [reloads] = _blocks(page().render().serialize(request_method="GET"))
    [stays] = _blocks(page().render().serialize(request_method="POST"))

    # Every render gets its own app id, so compare the scripts with it taken out.
    reloading = reloads["start"].replace(reloads["app"], "APP")
    staying = stays["start"].replace(stays["app"], "APP")
    assert reloading.replace("var canReload = true;", "var canReload = false;") == staying
    assert reloading != staying


@pytest.mark.parametrize("value", ["", "GE T", "GET\n", " GET", "GET,POST", "GET/1.1", 5, b"GET", ["GET"], True])
def test_a_request_method_that_is_not_a_method_name_raises(value: object) -> None:
    page = _page(_mounted(), {})

    with pytest.raises(ValueError, match="request_method"):
        page().render().serialize(request_method=value)  # type: ignore[arg-type]


@pytest.mark.parametrize("deps_strategy", ["simple", "fragment", "ignore"])
def test_a_wrong_request_method_raises_even_when_no_start_script_is_written(deps_strategy: str) -> None:
    page = _page(_mounted(), {})

    # The rendered output carries no start script here, but a wrong value is
    # reported the first time the view runs, not only on a document render.
    with pytest.raises(ValueError, match="request_method"):
        page().render().serialize(deps_strategy=deps_strategy, request_method="GE T")  # type: ignore[arg-type]
    assert page().render().serialize(deps_strategy=deps_strategy, request_method="POST")  # type: ignore[arg-type]


def test_a_wrong_request_method_raises_on_a_page_with_no_vue_component() -> None:
    registry = _mounted()

    class Plain(Component):
        citry = registry
        template = "<p>plain</p>"

    with pytest.raises(ValueError, match="request_method"):
        Plain().render().serialize(request_method="")
    assert ">plain</p>" in Plain().render().serialize(request_method="POST")


def test_a_page_that_writes_no_start_script_accepts_a_valid_request_method() -> None:
    registry = _mounted()

    class Plain(Component):
        citry = registry
        template = "<p>plain</p>"

    html = Plain().render().serialize(request_method="POST")
    assert "canReload" not in html
    assert 'type="module"' not in html


def test_a_fragment_never_carries_the_reload_answer() -> None:
    html = _page(_mounted(), {})().render().serialize(deps_strategy="fragment", request_method="POST")

    match = re.search(r'<script type="application/json" data-citry-vue-fragment>(.*?)</script>', html, re.DOTALL)
    assert match is not None
    # A fragment's configuration is copied into the page it joins, and a fragment must not reload that page.
    assert '"canReload"' not in match.group(1)
    assert "canReload" not in html


def test_an_unmounted_document_keeps_the_one_line_start_script_and_no_reload_answer() -> None:
    page = _page(Citry(autodiscover=False), {})
    for method in (None, "GET", "POST"):
        html = page().render().serialize(request_method=method)

        [match] = _blocks(html)
        # The runtime is inline here, so there is no URL that could go missing.
        assert match["start"] == f'__citryRuntime.startDocument("{match["app"]}");'
        assert "canReload" not in json.loads(match["json"])


def test_serialize_result_and_the_serialize_functions_take_request_method() -> None:
    page = _page(_mounted(), {})

    posted = page().render().serialize_result(request_method="POST")
    assert "  var canReload = false;\n" in posted.html
    assert "  var canReload = true;\n" in page().render().serialize_result(request_method="GET").html
    assert "  var canReload = false;\n" in serialize_render_result(page().render(), request_method="POST").html
    assert "  var canReload = false;\n" in serialize_render(page().render(), request_method="POST")
    for call in (
        lambda: page().render().serialize_result(request_method=5),
        lambda: serialize_render_result(page().render(), request_method=5),
        lambda: serialize_render(page().render(), request_method=5),
    ):
        with pytest.raises(ValueError, match="request_method"):
            call()  # type: ignore[arg-type]


def test_a_mounted_start_script_is_a_csp_hash_source_in_both_forms() -> None:
    page = _page(_mounted(security_script_integrity="citry"), {})
    hashes = {}
    for method in ("GET", "POST"):
        result = page().render().serialize_result(request_method=method)
        [match] = _blocks(result.html)
        # The exact text the browser runs is what the page's CSP must allow.
        assert _source_hash(match["start"]) in result.security.csp_script_hashes
        hashes[method] = _source_hash(match["start"])
        # The data block never runs, so it is not a CSP source.
        assert _source_hash(match["json"]) not in result.security.csp_script_hashes
    # The two forms are two different scripts, so a host that sends hashes lists the one it rendered.
    assert hashes["GET"] != hashes["POST"]


def test_a_mounted_start_script_carries_the_nonce() -> None:
    registry = _mounted(security_csp="strict")
    html = _page(registry, {})().render().serialize(csp_nonce="requestNonce", request_method="POST")

    [match] = _blocks(html)
    assert 'nonce="requestNonce"' in match["start_attrs"]
    assert 'nonce="requestNonce"' in match["attrs"]
    assert "  var canReload = false;\n" in match["start"]


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
