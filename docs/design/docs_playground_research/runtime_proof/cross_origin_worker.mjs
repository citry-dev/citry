self.onmessage = async ({ data }) => {
  if (data?.type !== "start" || !Number.isSafeInteger(data.runId)) {
    return;
  }

  if (data.mode === "infinite") {
    self.postMessage({ type: "loop-started", runId: data.runId });
    while (true) {
      // Deliberately block this disposable Worker.
    }
  }

  if (data.mode === "flood") {
    for (let index = 0; index < 250; index += 1) {
      self.postMessage(`untrusted-worker-message:${index}`);
    }
  }

  if (data.mode === "pyodide") {
    const { loadPyodide } = await import("/artifacts/pyodide/pyodide.mjs");
    const started = performance.now();
    const pyodide = await loadPyodide({ indexURL: "/artifacts/pyodide/" });
    const runtimeReady = performance.now();
    await pyodide.loadPackage(
      "/artifacts/citry_core-1.4.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl",
    );
    const coreReady = performance.now();
    const pythonResult = JSON.parse(await pyodide.runPythonAsync(`
import json
from citry_core.html_transform import mark_html
from citry_core.safe_eval import safe_eval
from citry_core.template_parser import compile_template, parse_template

parsed = parse_template("<h1>{{ title }}</h1>")
compiled = compile_template(parsed)
evaluated = safe_eval("value * 2")({"value": 21})
segments, placeholders = mark_html(
    "<main>Hello</main>", ["data-citry"], "c-render-id"
)

json.dumps({
    "compiled": "def generate_template" in compiled,
    "marked": segments[0],
    "placeholders": placeholders,
    "safe_eval": evaluated,
    "used_variables": [token.content for token in parsed.used_variables],
})
`));
    const docsResponse = await fetch(`${data.docsOrigin}/docs-sensitive`, {
      credentials: "include",
    });
    self.postMessage({
      type: "result",
      runId: data.runId,
      result: {
        docs: await docsResponse.json(),
        python: pythonResult,
        source: data.source,
        timings: {
          core_ms: coreReady - runtimeReady,
          pyodide_ms: runtimeReady - started,
          smoke_ms: performance.now() - coreReady,
        },
        workerOrigin: location.origin,
      },
    });
    return;
  }

  let result = {
    source: data.source,
    workerOrigin: location.origin,
  };
  if (data.mode === "network") {
    const runnerResponse = await fetch("/runner-observe", { credentials: "include" });
    const docsResponse = await fetch(`${data.docsOrigin}/docs-sensitive`, {
      credentials: "include",
    });
    result = {
      ...result,
      docs: await docsResponse.json(),
      runner: await runnerResponse.json(),
    };
  }

  self.postMessage({ type: "result", runId: data.runId, result });
};
