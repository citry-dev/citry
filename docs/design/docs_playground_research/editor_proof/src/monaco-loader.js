globalThis.__monacoWorkerRequests = 0;
globalThis.MonacoEnvironment = {
  getWorker() {
    globalThis.__monacoWorkerRequests += 1;
    return new Worker(new URL("./monaco-editor-worker.js", import.meta.url), { type: "module" });
  },
};

const workerAssetProbe = globalThis.MonacoEnvironment.getWorker();
globalThis.__monacoWorkerExecuted = new Promise((resolve) => {
  const timeout = setTimeout(() => resolve(false), 5_000);
  workerAssetProbe.addEventListener("message", (event) => {
    if (event.data?.type !== "citry-editor-worker-ready") return;
    clearTimeout(timeout);
    resolve(true);
  });
});
setTimeout(() => workerAssetProbe.terminate(), 1_000);

await import("./monaco.js");
