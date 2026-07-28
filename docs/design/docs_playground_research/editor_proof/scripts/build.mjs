import { build } from "esbuild";
import { cp, mkdir, rm } from "node:fs/promises";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const dist = path.join(root, "dist");

await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });

await Promise.all([
  build({
    entryPoints: [path.join(root, "src/codemirror.js")],
    outfile: path.join(dist, "codemirror.js"),
    bundle: true,
    format: "esm",
    platform: "browser",
    target: "es2022",
    minify: true,
    sourcemap: false,
    loader: { ".py": "text" },
  }),
  build({
    entryPoints: [path.join(root, "src/monaco.js")],
    outfile: path.join(dist, "monaco.js"),
    bundle: true,
    format: "esm",
    platform: "browser",
    target: "es2022",
    minify: true,
    sourcemap: false,
    loader: { ".py": "text" },
  }),
  build({
    entryPoints: [path.join(root, "src/monaco-editor-worker.js")],
    outfile: path.join(dist, "monaco-editor-worker.js"),
    bundle: true,
    format: "esm",
    platform: "browser",
    target: "es2022",
    minify: true,
    sourcemap: false,
  }),
  cp(path.join(root, "src/editor.css"), path.join(dist, "editor.css")),
  cp(path.join(root, "src/monaco-loader.js"), path.join(dist, "monaco-loader.js")),
]);
