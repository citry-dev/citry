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


def test_worker_revalidates_the_coupled_runtime_files() -> None:
    worker = _WORKER.read_text(encoding="utf-8")

    assert 'cache: "no-cache"' in worker
    assert 'cache: "force-cache"' not in worker
    assert "new URL(packageInfo.url, import.meta.url).href" in worker
    assert 'importlib.metadata.version("citry-ui")' in worker
    assert "runtime.citry.ui_version" in worker


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
