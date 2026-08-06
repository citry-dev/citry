import { brotliCompressSync, gzipSync } from "node:zlib";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");

async function measure(relativePath) {
  const contents = await readFile(path.join(root, relativePath));
  return {
    brotliBytes: brotliCompressSync(contents).byteLength,
    gzipBytes: gzipSync(contents, { level: 9 }).byteLength,
    rawBytes: contents.byteLength,
  };
}

function total(files) {
  return Object.fromEntries(
    ["brotliBytes", "gzipBytes", "rawBytes"].map((key) => [
      key,
      Object.values(files).reduce((sum, file) => sum + file[key], 0),
    ]),
  );
}

const codeMirrorFiles = {
  "dist/codemirror.js": await measure("dist/codemirror.js"),
};
const monacoInitialFiles = {
  "dist/monaco-loader.js": await measure("dist/monaco-loader.js"),
  "dist/monaco.js": await measure("dist/monaco.js"),
  "dist/monaco.css": await measure("dist/monaco.css"),
};
const monacoWorkerFiles = {
  "dist/monaco-editor-worker.js": await measure("dist/monaco-editor-worker.js"),
};

const report = {
  generatedBy: "npm run build && npm run measure",
  notes: [
    "Editor and Worker JavaScript is bundled and minified by esbuild 0.28.1; the small Monaco loader is copied unchanged.",
    "Shared proof-shell CSS is excluded from both editor totals.",
    "The Monaco proof eagerly requests its Worker to verify deployment, so proofInitialTotal includes it.",
    "Monaco worker bytes are also listed separately because production can load that asset on demand.",
  ],
  codemirror: {
    files: codeMirrorFiles,
    initialTotal: total(codeMirrorFiles),
  },
  monaco: {
    files: { ...monacoInitialFiles, ...monacoWorkerFiles },
    initialTotal: total(monacoInitialFiles),
    proofInitialTotal: total({ ...monacoInitialFiles, ...monacoWorkerFiles }),
    workerTotal: total(monacoWorkerFiles),
  },
};

await writeFile(
  path.join(root, "measurements.json"),
  `${JSON.stringify(report, null, 2)}\n`,
  "utf8",
);

console.log(JSON.stringify(report, null, 2));
