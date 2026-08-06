import { loadPyodide } from "/artifacts/pyodide/pyodide.mjs";

let pyodide;

async function initialize(wheelURLs) {
  const started = performance.now();
  pyodide = await loadPyodide({ indexURL: "/artifacts/pyodide/" });
  const runtimeReady = performance.now();
  await pyodide.loadPackage(wheelURLs);
  const packagesReady = performance.now();
  await pyodide.runPythonAsync(`
import gc
import json
import sys

from citry import Citry, Component

_browser_app = Citry(id_generator=lambda: "performance-render")
_browser_source = '''
class PerformanceBadge(Component):
    citry = browser_app

    class Kwargs:
        label: str

    template = "<strong>{{ label }}</strong>"

    def template_data(self, kwargs, slots):
        return {"label": kwargs.label}


class PerformanceCard(Component):
    citry = browser_app
    css = ".performance-card { color: rebeccapurple; }"
    js = 'console.log("performance card")'
    template = """
      <article class="performance-card">
        <h1>{{ title }}</h1>
        <ul>
          <c-for each="item in items">
            <li><c-performance-badge c-label="item" /></li>
          </c-for>
        </ul>
      </article>
    """

    def template_data(self, kwargs, slots):
        return kwargs


rendered = str(PerformanceCard(title=title, items=items))
'''


def _browser_run(index):
    _browser_app.clear()
    namespace = {
        "Component": Component,
        "browser_app": _browser_app,
        "items": ["one", "two", "three"],
        "title": "Browser performance",
    }
    exec(compile(_browser_source, "<performance>", "exec"), namespace)
    return namespace["rendered"]


def _browser_metrics():
    gc.collect()
    return json.dumps({
        "allocated_blocks": sys.getallocatedblocks(),
        "gc_objects": len(gc.get_objects()),
        "modules": len(sys.modules),
    })
`);
  return {
    packages_ms: packagesReady - runtimeReady,
    pyodide_ms: runtimeReady - started,
    setup_ms: performance.now() - packagesReady,
  };
}

function metrics() {
  const python = JSON.parse(pyodide.runPython("_browser_metrics()"));
  return {
    ...python,
    wasm_heap_bytes: pyodide._module?.HEAP8?.buffer?.byteLength ?? null,
  };
}

self.onmessage = async ({ data }) => {
  try {
    if (data?.type === "initialize") {
      const timings = await initialize(data.wheelURLs);
      self.postMessage({ type: "ready", metrics: metrics(), timings });
      return;
    }
    if (data?.type === "run" && Number.isSafeInteger(data.runId)) {
      const started = performance.now();
      pyodide.globals.set("_browser_run_index", data.runId);
      const html = pyodide.runPython("_browser_run(_browser_run_index)");
      self.postMessage({
        type: "result",
        runId: data.runId,
        duration_ms: performance.now() - started,
        html,
      });
      return;
    }
    if (data?.type === "metrics" && Number.isSafeInteger(data.sampleId)) {
      self.postMessage({
        type: "metrics",
        sampleId: data.sampleId,
        metrics: metrics(),
      });
    }
  } catch (error) {
    self.postMessage({
      type: "failure",
      message: String(error),
      stack: String(error?.stack ?? ""),
    });
  }
};
