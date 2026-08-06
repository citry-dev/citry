import "monaco-editor/editor/editor.worker.js";

self.postMessage({ type: "citry-editor-worker-ready" });
