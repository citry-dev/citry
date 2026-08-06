"""Regression tests for the contributor-only Storybook adapter spike."""

from __future__ import annotations

import asyncio
import base64
import importlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from citry import RouteHeaders, RouteRequest
from citry import citry as default_citry

_STORYBOOK_DIR = Path(__file__).resolve().parents[1] / "storybook"


def _trusted_request(**kwargs):
    return RouteRequest(
        headers=RouteHeaders((("Host", "127.0.0.1:8123"),)),
        **kwargs,
    )


@pytest.fixture(scope="module")
def spike_modules():
    default_components_before = {
        "cbutton": default_citry.components.get("cbutton"),
        "creactivecounterprobe": default_citry.components.get("creactivecounterprobe"),
    }
    sys.path.insert(0, str(_STORYBOOK_DIR))
    try:
        yield {
            "app": importlib.import_module("backend.app"),
            "catalog": importlib.import_module("backend.catalog"),
            "generate": importlib.import_module("backend.generate"),
            "default_components_before": default_components_before,
        }
    finally:
        sys.path.remove(str(_STORYBOOK_DIR))
        for module_name in tuple(sys.modules):
            if module_name == "backend" or module_name.startswith("backend."):
                sys.modules.pop(module_name)


def _alternative(control):
    if control.kind == "boolean":
        return not control.default
    if control.kind == "select":
        return control.options[-1]
    return "Changed in Controls"


def _query_value(control):
    value = _alternative(control)
    return str(value).lower() if control.kind == "boolean" else str(value)


def _input_tag(content):
    match = re.search(r"<input\b[^>]*>", content, flags=re.DOTALL)
    assert match is not None
    return match.group()


def _assert_control_effect(scenario_id, control_name, default_content, changed_content):
    assert changed_content != default_content
    if scenario_id == "button/static":
        expected = {
            "label": "Changed in Controls",
            "loading": 'aria-busy="true"',
            "disabled": " disabled",
            "type": 'type="reset"',
        }
        assert expected[control_name] in changed_content
        return
    if scenario_id == "field/static":
        input_tag = _input_tag(changed_content)
        if control_name == "label":
            assert "Changed in Controls" in changed_content
        elif control_name == "value":
            assert 'value="Changed in Controls"' in input_tag
        elif control_name == "required":
            assert " required" not in input_tag
        elif control_name == "disabled":
            assert " disabled" in input_tag
        elif control_name == "readonly":
            assert " readonly" in input_tag
        elif control_name == "invalid":
            assert 'aria-invalid="true"' in input_tag
            assert "Enter a valid email address." in changed_content
        elif control_name == "orientation":
            assert 'data-orientation="horizontal"' in changed_content
        else:
            assert control_name == "density"
            assert 'data-density="compact"' in changed_content
        return
    if scenario_id == "table/static":
        if control_name == "state":
            assert "Unable to load projects" in changed_content
        elif control_name == "density":
            assert 'data-density="compact"' in changed_content
        elif control_name == "striped":
            assert " data-striped" not in changed_content
        elif control_name == "hover":
            assert " data-hover" not in changed_content
        else:
            assert control_name == "sticky_header"
            assert " data-sticky-header" in changed_content
        return
    assert scenario_id == "tabs/server-selected"
    expected = {
        "selected": 'data-value="security"',
        "orientation": 'data-orientation="vertical"',
        "direction": 'dir="rtl"',
        "activation": 'data-activation="manual"',
    }
    assert expected[control_name] in changed_content


def _asgi_get(asgi_app, path, *, headers=()):
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [(name.lower().encode(), value.encode()) for name, value in headers],
        "client": ("127.0.0.1", 50000),
        "server": ("127.0.0.1", 8123),
    }

    def run_asgi():
        asyncio.run(asgi_app(scope, receive, send))

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        run_asgi()
    else:
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(run_asgi).result()
    start = next(message for message in messages if message["type"] == "http.response.start")
    body = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
    return start, body


def test_catalog_is_ordered_unique_and_path_safe(spike_modules):
    scenarios = spike_modules["catalog"].SCENARIOS

    assert [scenario.id for scenario in scenarios] == [
        "button/static",
        "field/static",
        "table/static",
        "tabs/server-selected",
        "readiness/reactive-state",
    ]
    assert len({scenario.id for scenario in scenarios}) == len(scenarios)


def test_every_static_scenario_renders_each_control_independently(spike_modules):
    app_module = spike_modules["app"]
    scenarios = [scenario for scenario in spike_modules["catalog"].SCENARIOS if not scenario.client_interactive]
    extension = app_module.engine.extensions.get_extension("storybook_scenarios")

    for scenario in scenarios:
        family, state = scenario.id.split("/")
        default_response = extension.render(_trusted_request(), family=family, state=state)
        assert default_response.status == 200
        assert "<style" in str(default_response.content)
        if scenario.id in {"button/static", "field/static", "table/static"}:
            assert "<script" in str(default_response.content)
        else:
            assert "<script" not in str(default_response.content)
        assert f'data-scenario-id="{scenario.id}"' in str(default_response.content)
        for control in scenario.controls:
            changed_response = extension.render(
                _trusted_request(query={control.name: (_query_value(control),)}),
                family=family,
                state=state,
            )
            assert changed_response.status == 200
            _assert_control_effect(
                scenario.id,
                control.name,
                str(default_response.content),
                str(changed_response.content),
            )


def test_interactive_scenario_uses_fragment_assets_and_control_input(spike_modules):
    app_module = spike_modules["app"]
    scenario = spike_modules["catalog"].SCENARIOS_BY_ID["readiness/reactive-state"]
    extension = app_module.engine.extensions.get_extension("storybook_scenarios")

    default_response = extension.render(
        _trusted_request(),
        family="readiness",
        state="reactive-state",
    )
    changed_response = extension.render(
        _trusted_request(query={"generation": ("second",)}),
        family="readiness",
        state="reactive-state",
    )
    content = str(default_response.content)

    assert scenario.client_interactive is True
    assert scenario.ready_selector == '.citry-ui-readiness-probe[data-ready="true"]'
    assert default_response.status == 200
    assert changed_response.status == 200
    assert 'data-generation="first"' in content
    assert 'data-generation="second"' in str(changed_response.content)
    assert "data-citry-graph" in content
    assert "data-citry" in content
    assert "/citry/citry.js" in content

    manifest_match = re.search(
        r'<script type="application/json" data-citry>(.*?)</script>',
        content,
        flags=re.DOTALL,
    )
    assert manifest_match is not None
    manifest = json.loads(manifest_match.group(1))
    descriptors = {
        kind: [json.loads(base64.b64decode(value[0]).decode()) for value in manifest["fetch"][kind]]
        for kind in ("css", "js")
    }
    assert any(descriptor["attrs"].get("href", "").startswith("/citry/cache/") for descriptor in descriptors["css"])
    assert any(descriptor["attrs"].get("src", "").startswith("/citry/cache/") for descriptor in descriptors["js"])


def test_tabs_scenario_uses_fragment_assets_and_each_control(spike_modules):
    app_module = spike_modules["app"]
    scenario = spike_modules["catalog"].SCENARIOS_BY_ID["tabs/server-selected"]
    extension = app_module.engine.extensions.get_extension("storybook_scenarios")
    default_response = extension.render(_trusted_request(), family="tabs", state="server-selected")
    default_content = str(default_response.content)

    assert scenario.client_interactive is True
    assert scenario.ready_selector == "[data-citry-tabs-root][data-citry-tabs-initialized]"
    assert "/citry/citry.js" in default_content
    for control in scenario.controls:
        changed_response = extension.render(
            _trusted_request(query={control.name: (_query_value(control),)}),
            family="tabs",
            state="server-selected",
        )
        assert changed_response.status == 200
        _assert_control_effect(
            scenario.id,
            control.name,
            default_content,
            str(changed_response.content),
        )


def test_runner_exposes_catalog_standalone_pages_and_visible_errors(spike_modules):
    app_module = spike_modules["app"]
    extension = app_module.engine.extensions.get_extension("storybook_scenarios")

    catalog_response = extension.urls[0].handler(_trusted_request())
    page_response = extension.page(_trusted_request(), family="button", state="static")
    interactive_page = extension.page(
        _trusted_request(),
        family="readiness",
        state="reactive-state",
    )
    unknown_response = extension.render(_trusted_request(), family="missing", state="scenario")
    invalid_response = extension.render(
        _trusted_request(query={"loading": ("sometimes",)}),
        family="button",
        state="static",
    )
    unexpected_response = extension.render(
        _trusted_request(query={"module": ("citry_ui.components.cbutton.cbutton",)}),
        family="button",
        state="static",
    )

    assert catalog_response is not None
    catalog = json.loads(str(catalog_response.content))
    assert catalog["schemaVersion"] == 1
    assert catalog["scenarios"][-1]["standaloneUrl"] == (
        "/citry/ext/storybook_scenarios/page/readiness/reactive-state"
    )
    assert page_response.status == 200
    assert "<!doctype html>" in str(page_response.content)
    assert "<c-css" not in str(page_response.content)
    assert "<c-js" not in str(page_response.content)
    assert interactive_page.status == 200
    assert 'data-ready="loading"' in str(interactive_page.content)
    assert "Citry.manager" in str(interactive_page.content)
    assert "citry-ui-readiness-probe" in str(interactive_page.content)
    assert unknown_response.status == 404
    assert invalid_response.status == 400
    assert "must be 'true' or 'false'" in str(invalid_response.content)
    assert unexpected_response.status == 400
    assert "Unknown argument" in str(unexpected_response.content)


def test_runner_restricts_live_hosts_and_origins(spike_modules):
    extension = spike_modules["app"].engine.extensions.get_extension("storybook_scenarios")
    allowed = extension.render(
        RouteRequest(
            headers=RouteHeaders(
                (
                    ("Host", "127.0.0.1:8123"),
                    ("Origin", "http://127.0.0.1:6106"),
                )
            )
        ),
        family="button",
        state="static",
    )
    bad_host = extension.render(
        RouteRequest(headers=RouteHeaders((("Host", "example.test"),))),
        family="button",
        state="static",
    )
    missing_host = extension.render(
        RouteRequest(),
        family="button",
        state="static",
    )
    bad_origin = extension.render(
        RouteRequest(headers=RouteHeaders((("Origin", "https://example.test"),))),
        family="button",
        state="static",
    )

    assert allowed.status == 200
    assert ("Access-Control-Allow-Origin", "http://127.0.0.1:6106") in allowed.headers
    assert bad_host.status == 403
    assert missing_host.status == 403
    assert bad_origin.status == 403


def test_asgi_adapter_matches_routes_and_applies_cors(spike_modules):
    start, body = _asgi_get(
        spike_modules["app"].app,
        "/citry/ext/storybook_scenarios/render/button/static",
        headers=(("host", "127.0.0.1:8123"), ("origin", "http://127.0.0.1:6206")),
    )
    response_headers = {(name.decode().lower(), value.decode()) for name, value in start["headers"]}
    missing_host_start, _ = _asgi_get(
        spike_modules["app"].app,
        "/citry/ext/storybook_scenarios/render/button/static",
    )
    blocked_asset_start, _ = _asgi_get(
        spike_modules["app"].app,
        "/citry/citry.js",
        headers=(("host", "attacker.example"),),
    )

    assert start["status"] == 200
    assert missing_host_start["status"] == 403
    assert blocked_asset_start["status"] == 403
    assert b'data-scenario-id="button/static"' in body
    assert ("access-control-allow-origin", "http://127.0.0.1:6206") in response_headers
    assert ("cache-control", "no-store") in response_headers


def test_story_projections_are_deterministic_current_and_adapter_equivalent(spike_modules):
    generator = spike_modules["generate"]
    catalog = spike_modules["catalog"]

    assert generator.write_outputs(check=True)
    outputs = generator.generated_outputs()
    assert len(outputs) == len(catalog.SCENARIOS) * 2

    for scenario in catalog.SCENARIOS:
        stem = scenario.id.replace("/", "--")
        server_story = json.loads(outputs[_STORYBOOK_DIR / "generated" / "server" / f"{stem}.stories.json"])
        html_story = outputs[_STORYBOOK_DIR / "generated" / "html" / f"{stem}.stories.js"]

        projection = generator._projection(scenario)
        citry_parameters = projection["parameters"]["citry"]
        assert citry_parameters["catalogSchemaVersion"] == 1
        assert citry_parameters["generatorVersion"] == 1
        assert re.fullmatch(r"[0-9a-f]{64}", citry_parameters["sourceDigest"])
        assert server_story == {
            "title": projection["title"],
            "argTypes": projection["argTypes"],
            "parameters": projection["parameters"],
            "tags": projection["tags"],
            "stories": [
                {
                    "name": projection["storyName"],
                    "args": projection["args"],
                    "parameters": {"server": {"id": projection["scenarioId"]}},
                }
            ],
        }
        assert f"title: {json.dumps(projection['title'], ensure_ascii=False)}," in html_story
        assert f"name: {json.dumps(projection['storyName'], ensure_ascii=False)}," in html_story
        assert f"args: {json.dumps(projection['args'], indent=2, ensure_ascii=False)}," in html_story
        assert f"argTypes: {json.dumps(projection['argTypes'], indent=2, ensure_ascii=False)}," in html_story
        assert f"parameters: {json.dumps(projection['parameters'], indent=2, ensure_ascii=False)}," in html_story
        assert f"tags: {json.dumps(projection['tags'], ensure_ascii=False)}," in html_story


def test_storybook_engine_does_not_register_ui_components_globally(spike_modules):
    assert spike_modules["app"].engine.get("CButton") is not None
    assert spike_modules["app"].engine.get("CReactiveCounterProbe") is not None
    assert default_citry.components.get("cbutton") is spike_modules["default_components_before"]["cbutton"]
    assert (
        default_citry.components.get("creactivecounterprobe")
        is spike_modules["default_components_before"]["creactivecounterprobe"]
    )
