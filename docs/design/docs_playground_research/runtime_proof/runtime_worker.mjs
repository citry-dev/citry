import { loadPyodide } from "/artifacts/pyodide/pyodide.mjs";

let pyodide;

async function initialize(indexURL, wheelURL) {
  const started = performance.now();
  self.postMessage({ type: "phase", phase: "loading-pyodide" });
  pyodide = await loadPyodide({ indexURL });
  const runtimeReady = performance.now();
  self.postMessage({ type: "phase", phase: "loading-core" });
  await pyodide.loadPackage(wheelURL);
  self.postMessage({ type: "phase", phase: "core-ready" });
  return {
    core_ms: performance.now() - runtimeReady,
    pyodide_ms: runtimeReady - started,
  };
}

self.onmessage = async ({ data }) => {
  if (data.type === "ping") {
    self.postMessage({ type: "pong" });
    return;
  }

  if (data.type !== "start") {
    return;
  }

  try {
    const timings = await initialize(data.indexURL, data.wheelURL);

    if (data.mode === "infinite") {
      self.postMessage({ type: "loop-started", timings });
      await pyodide.runPythonAsync("while True:\n    pass");
      return;
    }

    const smokeStarted = performance.now();
    const result = await pyodide.runPythonAsync(`
import json
from js import fetch, globalThis, postMessage
from citry_core.html_transform import mark_html
from citry_core.safe_eval import safe_eval
from citry_core.template_parser import compile_template, parse_template

parsed = parse_template("<h1>{{ title }}</h1>")
compiled = compile_template(parsed)
evaluated = safe_eval("value * 2")({"value": 21})
segments, placeholders = mark_html(
    "<main>Hello</main>", ["data-citry"], "c-render-id"
)
network_response = await fetch("/worker-fetch")
network_observation = json.loads(await network_response.text())

for index in range(250):
    postMessage(f"worker-flood:{index}")

json.dumps({
    "capabilities": {
        name: hasattr(globalThis, name)
        for name in (
            "fetch", "postMessage", "close", "WebSocket", "indexedDB",
            "caches", "localStorage", "document",
        )
    },
    "compiled": "def generate_template" in compiled,
    "marked": segments[0],
    "network": network_observation,
    "placeholders": placeholders,
    "safe_eval": evaluated,
    "used_variables": [token.content for token in parsed.used_variables],
})
`);
    timings.smoke_ms = performance.now() - smokeStarted;
    self.postMessage({ type: "result", result: JSON.parse(result), timings });
  } catch (error) {
    self.postMessage({
      type: "failure",
      error: String(error),
      stack: String(error?.stack ?? ""),
    });
  }
};
