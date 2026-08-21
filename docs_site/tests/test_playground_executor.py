"""Behavior contract for the Python module adapter shipped to Pyodide."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_EXECUTOR = Path(__file__).parents[1] / "static" / "playground" / "executor.py"
_SNIPPETS = Path(__file__).parents[1] / "live_snippets"
_STARTER = _SNIPPETS / "welcome.py"
_WORKER = Path(__file__).parents[1] / "static" / "playground" / "worker.js"
_RUNTIME = Path(__file__).parents[1] / "static" / "playground" / "runtime.json"


def _run_sources(*sources: str) -> list[dict]:
    program = (
        "import json, runpy, sys; "
        f"run = runpy.run_path({_EXECUTOR.as_posix()!r})['run_source_json']; "
        "print(json.dumps([json.loads(run(source)) for source in json.load(sys.stdin)]))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        input=json.dumps(sources),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def _dispatch_source(source: str, handler: str, *, run_id: int = 7) -> tuple[dict, dict]:
    program = f"""
import json
import re
import runpy
import sys

adapter = runpy.run_path({_EXECUTOR.as_posix()!r})
payload = json.load(sys.stdin)
rendered = json.loads(adapter["run_source_json"](payload["source"], payload["run_id"]))
manifest = json.loads(re.search(
    r'<script[^>]*data-citry-events[^>]*>(.*?)</script>',
    rendered["html"],
    re.DOTALL,
).group(1))
instance = manifest["componentInstances"][0]
call = {{
    "componentClassId": instance["componentClassId"],
    "handlerName": payload["handler"],
    "callerRenderId": instance["renderId"],
    "args": {{}},
    "sendSequence": 1,
}}
if instance["stateToken"] is not None:
    call["stateToken"] = instance["stateToken"]
envelope = {{
    "protocol": "citry-events/1",
    "requestId": "playground-test",
    "calls": [call],
}}
result = json.loads(adapter["dispatch_event_json"](json.dumps(envelope), payload["run_id"]))
print(json.dumps([rendered, result]))
"""
    completed = subprocess.run(
        [sys.executable, "-c", program],
        input=json.dumps({"source": source, "handler": handler, "run_id": run_id}),
        text=True,
        capture_output=True,
        check=True,
    )
    rendered, result = json.loads(completed.stdout)
    return rendered, result


def _dispatch_render_source(source: str, handler: str, *, run_id: int = 7) -> tuple[dict, dict, list[dict]]:
    program = f"""
import base64
import json
import re
import runpy
import sys

adapter = runpy.run_path({_EXECUTOR.as_posix()!r})
payload = json.load(sys.stdin)
rendered = json.loads(adapter["run_source_json"](payload["source"], payload["run_id"]))
manifest = json.loads(re.search(
    r'<script[^>]*data-citry-events[^>]*>(.*?)</script>',
    rendered["html"],
    re.DOTALL,
).group(1))
instance = manifest["componentInstances"][0]
envelope = {{
    "protocol": "citry-events/1",
    "requestId": "playground-render-test",
    "calls": [{{
        "componentClassId": instance["componentClassId"],
        "handlerName": payload["handler"],
        "callerRenderId": instance["renderId"],
        "args": {{}},
        "sendSequence": 1,
    }}],
}}
response = json.loads(adapter["dispatch_event_json"](json.dumps(envelope), payload["run_id"]))
action = response["results"][0]["actions"][0]
dependency = json.loads(re.search(
    r'<script[^>]*data-citry(?:>|=[^>]*>)(.*?)</script>',
    action["html"],
    re.DOTALL,
).group(1))
paths = []
for kind in ("js", "css"):
    for encoded in dependency["fetch"][kind]:
        encoded = encoded[0] if isinstance(encoded, list) else encoded
        descriptor = json.loads(base64.b64decode(encoded).decode())
        path = descriptor.get("attrs", {{}}).get("src") or descriptor.get("attrs", {{}}).get("href")
        if path:
            paths.append(path)
assets = json.loads(adapter["load_playground_assets_json"](json.dumps(paths), payload["run_id"]))
print(json.dumps([rendered, response, assets]))
"""
    completed = subprocess.run(
        [sys.executable, "-c", program],
        input=json.dumps({"source": source, "handler": handler, "run_id": run_id}),
        text=True,
        capture_output=True,
        check=True,
    )
    rendered, result, assets = json.loads(completed.stdout)
    return rendered, result, assets


def test_worker_revalidates_the_coupled_runtime_files() -> None:
    worker = _WORKER.read_text(encoding="utf-8")

    assert 'cache: "no-cache"' in worker
    assert 'cache: "force-cache"' not in worker
    assert "new URL(packageInfo.url, import.meta.url).href" in worker
    assert 'importlib.metadata.version("citry-ui")' in worker
    assert "runtime.citry.ui_version" in worker
    assert "citry-events.js" not in worker
    assert "install_events_client_runtime" not in worker


def test_runtime_manifest_pins_the_complete_published_tuple() -> None:
    runtime = json.loads(_RUNTIME.read_text(encoding="utf-8"))
    packages = {package["name"]: package for package in runtime["packages"]}

    assert runtime["pyodide"] == {
        "version": "314.0.3",
        "python": "3.14.2",
        "index_url": "https://cdn.jsdelivr.net/pyodide/v314.0.3/full/",
        "module_url": "https://cdn.jsdelivr.net/pyodide/v314.0.3/full/pyodide.mjs",
    }
    assert runtime["citry"] == {
        "version": "0.4.2",
        "core_version": "1.5.1",
        "ui_version": "0.1.0",
    }
    assert len(packages) == len(runtime["packages"])
    assert packages["citry-core"] == {
        "name": "citry-core",
        "version": "1.5.1",
        "url": (
            "https://files.pythonhosted.org/packages/e8/e3/"
            "a3f65946b66fb78f6395c71f1d81c5db2dc48eaeea807ac8db4d1d31a238/"
            "citry_core-1.5.1-cp314-cp314-pyemscripten_2026_0_wasm32.whl"
        ),
    }
    assert packages["citry"]["version"] == "0.4.2"
    assert packages["citry"]["url"].endswith("/citry-0.4.2-py3-none-any.whl")
    assert packages["citry-ui"]["version"] == "0.1.0"
    assert packages["citry-ui"]["url"].endswith("/citry_ui-0.1.0-py3-none-any.whl")


def test_executor_accepts_html_markup_element_render_and_starter() -> None:
    string, markup, element, render, starter = _run_sources(
        "value = '<p>string</p>'\nvalue",
        "from markupsafe import Markup\nMarkup('<p>markup</p>')",
        "from citry import Component\nclass Card(Component):\n    template = '<p>element</p>'\nCard()",
        "from citry import Component\nclass Card(Component):\n    template = '<p>render</p>'\nCard().render()",
        _STARTER.read_text(encoding="utf-8"),
    )

    assert string["ok"]
    assert string["html"] == "<p>string</p>"
    assert markup["ok"]
    assert markup["html"] == "<p>markup</p>"
    assert element["ok"]
    assert ">element</p>" in element["html"]
    assert render["ok"]
    assert ">render</p>" in render["html"]
    assert starter["ok"]
    assert "Welcome, <strong>Ada Lovelace</strong>" in starter["html"]


def test_executor_registers_and_resolves_citry_ui_on_every_run() -> None:
    direct, registered, repeated = _run_sources(
        """from citry_ui import CButton

CButton(slots={"default": "Direct save"})
""",
        """from citry import Component

class Page(Component):
    template = "<main><c-CButton>Registered save</c-CButton></main>"

Page()
""",
        """from citry_ui import CButton

CButton(slots={"default": "Second run"})
""",
    )

    assert direct["ok"] is True
    assert "Direct save" in direct["html"]
    assert registered["ok"] is True
    assert "Registered save" in registered["html"]
    assert repeated["ok"] is True
    assert "Second run" in repeated["html"]


def test_successful_run_publishes_a_bounded_component_catalog() -> None:
    [result] = _run_sources(
        '''from citry import Citry, Component

app = Citry(autodiscover=False)

class ProfileCard(Component):
    citry = app

    class Kwargs:
        title: str

    template = """
    <p>{{ title }}</p>
    """

ProfileCard(title="Ada")
'''
    )

    assert result["ok"] is True
    snapshot = result["catalog"]
    assert snapshot["schemaVersion"] == 1
    components = [
        component
        for registry in snapshot["registries"]
        for component in registry["components"]
        if component["className"] == "ProfileCard"
    ]
    assert len(components) == 1
    assert components[0]["name"] == "profile-card"
    assert components[0]["aliases"] == ["profilecard"]
    assert components[0]["kwargs"] == [
        {
            "name": "title",
            "required": True,
            "typeDisplay": "str",
            "description": None,
        }
    ]


def test_every_authored_live_snippet_renders_without_console_output() -> None:
    paths = sorted(_SNIPPETS.glob("*.py"))
    results = _run_sources(*(path.read_text(encoding="utf-8") for path in paths))

    assert paths
    assert len(results) == len(paths)
    for path, result in zip(paths, results, strict=True):
        assert result["ok"], f"{path.name}: {result}"
        assert result["html"], path.name
        assert result["stdout"] == "", path.name
        assert result["stderr"] == "", path.name


def test_starter_state_and_dispatch_handler_round_trip() -> None:
    rendered, response = _dispatch_source(_STARTER.read_text(encoding="utf-8"), "welcome")

    assert rendered["ok"]
    [result] = response["results"]
    assert result["ok"]
    assert result["sendSequence"] == 1
    state, dispatched = result["actions"]
    assert state["action"] == "state"
    assert state["stateToken"].startswith("cev1.")
    assert dispatched == {
        "action": "event",
        "eventName": "welcome-card:welcomed",
        "detail": {"greetings": 1},
        "target": f"render:{state['targetRenderId']}",
    }


def test_render_action_resolves_its_browser_assets() -> None:
    source = '''
from citry import Component
from citry.ext.events import actions


class LoadedFragment(Component):
    class Kwargs:
        kind: str

    class Events:
        def ping(self):
            return actions.Dispatch("fragment:ping", {"kind": "nested"})

    def js_data(self, kwargs, slots):
        return {"kind": kwargs.kind}

    template = """
      <section class="loaded-fragment">
        <button type="button" @c-click="ping">Ping</button>
      </section>
    """

    js = """
      window.__fragmentAssetLoads = (window.__fragmentAssetLoads || 0) + 1;
      $component(({ els, data }) => {
        els[0].setAttribute("data-component-js", data.kind);
      });
    """

    css = """
      .loaded-fragment {
        background-color: rgb(231, 241, 255);
      }
    """


class FragmentLoader(Component):
    class Events:
        def load(self):
            return actions.Render(
                LoadedFragment(kind="rendered"),
                target="#fragment-target",
                swap="inner",
            )

    template = """
      <main>
        <button type="button" @c-click="load">Load</button>
        <div id="fragment-target"></div>
      </main>
    """


FragmentLoader()
'''

    rendered, response, assets = _dispatch_render_source(source, "load")

    assert rendered["ok"]
    [result] = response["results"]
    assert result["ok"]
    [render] = result["actions"]
    assert render["action"] == "render"
    assert render["target"] == "#fragment-target"
    assert render["swap"] == "inner"
    assert "loaded-fragment" in render["html"]
    assert assets
    assert all(asset["path"].startswith("/__citry_playground__/") for asset in assets)
    assert {asset["contentType"] for asset in assets} == {"text/css", "text/javascript"}
    contents = "\n".join(asset["content"] for asset in assets)
    assert "__fragmentAssetLoads" in contents
    assert "background-color" in contents


def test_browser_asset_loader_rejects_unowned_and_stale_requests() -> None:
    program = f"""
import json
import runpy

adapter = runpy.run_path({_EXECUTOR.as_posix()!r})
json.loads(adapter["run_source_json"]("value = '<p>ready</p>'\\nvalue", 7))
errors = []
for paths, run_id in [
    (["/__citry_playground__/visitor.js"], 7),
    (["/__citry_playground__/citry.js?unexpected=1"], 7),
    (["/__citry_playground__/asset/../citry.js"], 7),
    (["/__citry_playground__/asset/file%2fescape.js"], 7),
    (["/__citry_playground__/citry.js", "/__citry_playground__/citry.js"], 7),
    (["/__citry_playground__/citry.js"], 8),
]:
    try:
        adapter["load_playground_assets_json"](json.dumps(paths), run_id)
    except Exception as error:
        errors.append([type(error).__name__, str(error)])
print(json.dumps(errors))
"""
    completed = subprocess.run(
        [sys.executable, "-c", program],
        text=True,
        capture_output=True,
        check=True,
    )

    assert json.loads(completed.stdout) == [
        ["ValueError", "Unsupported playground asset path: '/__citry_playground__/visitor.js'."],
        [
            "ValueError",
            "Unsupported playground asset path: '/__citry_playground__/citry.js?unexpected=1'.",
        ],
        [
            "ValueError",
            "Unsupported playground asset path: '/__citry_playground__/asset/../citry.js'.",
        ],
        [
            "ValueError",
            "Unsupported playground asset path: '/__citry_playground__/asset/file%2fescape.js'.",
        ],
        [
            "ValueError",
            "Duplicate playground asset path: '/__citry_playground__/citry.js'.",
        ],
        [
            "RuntimeError",
            "These assets belong to a preview that is no longer active. Run the module again.",
        ],
    ]


def test_event_request_is_synthetic_and_server_only_action_is_rejected() -> None:
    source = """
from citry import Component
from citry.ext.events import actions


class RequestProbe(Component):
    class Events:
        def inspect(self, request, event):
            return {
                "content_type": request.content_type,
                "method": request.method,
                "path": request.path,
                "transport": event.transport,
            }

        def leave(self):
            return actions.Redirect("/elsewhere")

    template = '<button @c-click="inspect">Inspect</button>'


RequestProbe()
"""
    _, inspected = _dispatch_source(source, "inspect")
    _, rejected = _dispatch_source(source, "leave")

    [data] = inspected["results"][0]["actions"]
    assert data == {
        "action": "data",
        "value": {
            "content_type": "application/citry-events+json",
            "method": "POST",
            "path": "/playground/events",
            "transport": "playground",
        },
    }
    [result] = rejected["results"]
    assert not result["ok"]
    assert "unsupported playground action(s): redirect" in result["error"]["message"]


def test_download_and_async_event_handlers_are_rejected() -> None:
    source = """
from citry import Component
from citry.ext.events import actions


class UnsupportedHandlers(Component):
    class Events:
        def download(self):
            return actions.Download(b"hello", "hello.txt")

        async def later(self):
            return {"too": "late"}

    template = '<button @c-click="download">Download</button>'


UnsupportedHandlers()
"""
    _, download = _dispatch_source(source, "download")
    _, async_handler = _dispatch_source(source, "later")

    [download_result] = download["results"]
    assert not download_result["ok"]
    assert "non-HTTP transports must return actions" in download_result["error"]["message"]

    [async_result] = async_handler["results"]
    assert not async_result["ok"]
    assert "async" in async_result["error"]["message"].lower()


def test_missing_preview_executes_first_and_preserves_program_output() -> None:
    result = _run_sources("print('before missing')\nanswer = 42")[0]

    assert not result["ok"]
    assert result["diagnostic"]["kind"] == "missing_preview"
    assert result["diagnostic"]["line"] == 2
    assert result["stdout"] == "before missing\n"


def test_executor_rejects_bad_values_async_and_control_flow_exceptions() -> None:
    none_value, object_value, top_level_await, stopped = _run_sources(
        "None",
        "object()",
        "await something()",
        "raise SystemExit(2)",
    )

    assert none_value["diagnostic"]["kind"] == "none_preview"
    assert object_value["diagnostic"]["kind"] == "unsupported_preview_type"
    assert top_level_await["diagnostic"]["kind"] == "top_level_await"
    assert top_level_await["diagnostic"]["line"] == 1
    assert stopped["diagnostic"]["kind"] == "execution_stopped"


def test_executor_preserves_module_semantics_locations_and_private_names() -> None:
    future, main_guard, collision, runtime_error = _run_sources(
        "from __future__ import annotations\nvalue: Missing = '<p>future</p>'\nvalue",
        "if __name__ == '__main__':\n    raise AssertionError('must not run')\n'<p>module</p>'",
        "__citry_playground_result = 'visitor'\n__citry_playground_normalize = 'visitor'\n'<p>collision</p>'",
        "def explode():\n    raise ValueError('boom')\nexplode()",
    )

    assert future["ok"]
    assert future["html"] == "<p>future</p>"
    assert main_guard["ok"]
    assert main_guard["html"] == "<p>module</p>"
    assert collision["ok"]
    assert collision["html"] == "<p>collision</p>"
    assert runtime_error["diagnostic"]["line"] == 2
    assert 'File "<playground>", line 2' in runtime_error["diagnostic"]["traceback"]


def test_executor_registers_the_playground_module_and_its_source() -> None:
    [result] = _run_sources(
        "import inspect\n"
        "import sys\n"
        "def example(value: str):\n"
        "    return value\n"
        "registered = sys.modules[__name__].__dict__ is globals()\n"
        "source_available = 'value: str' in inspect.getsource(example)\n"
        "f'<p>{registered}:{source_available}</p>'",
    )

    assert result["ok"]
    assert result["html"] == "<p>True:True</p>"


def test_event_input_annotation_resolves_in_the_dynamic_module() -> None:
    [result] = _run_sources(
        "from citry import Component\n"
        "from citry.ext.events import actions\n"
        "class SignupIn:\n"
        "    email: str\n"
        "class SignupForm(Component):\n"
        "    class Events:\n"
        "        def submit(self, data: SignupIn):\n"
        "            return actions.Dispatch('signup:sent', {'email': data.email})\n"
        '    template = \'<form @c-submit.prevent="submit"><input name="email"></form>\'\n'
        "SignupForm()",
    )

    assert result["ok"], result
    assert "<form" in result["html"]
    assert "data-cev-on" in result["html"]
