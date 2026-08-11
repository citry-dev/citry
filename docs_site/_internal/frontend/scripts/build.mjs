import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";

// Build the authored playground modules into the exact static files shipped by
// the docs site. Citry's pinned wheel owns its matching Events client.
const packageRoot = fileURLToPath(new URL("../", import.meta.url));
const staticRoot = fileURLToPath(new URL("../../../static/playground/", import.meta.url));
const checkOnly = process.argv.includes("--check");

// The full page and deferred inline runtime bundle shared dependencies. The
// small activator stays separate so ordinary docs pages do not load CodeMirror.
const entries = [
  { source: "playground.js", output: "playground.js", bundle: true },
  // Keep the activator independent from CodeMirror. Bundling this dynamic
  // import without code splitting would pull the heavy runtime into every page.
  { source: "live_code.js", output: "live_code.js", bundle: false },
  { source: "live_code_runtime.js", output: "live_code_runtime.js", bundle: true },
  { source: "landing_composer.js", output: "landing_composer.js", bundle: true },
];

async function generate(entry) {
  const result = await build({
    entryPoints: [`${packageRoot}src/${entry.source}`],
    bundle: entry.bundle,
    format: "esm",
    target: ["es2022"],
    minify: true,
    sourcemap: false,
    write: false,
    legalComments: "none",
    banner: {
      js: `// Generated from docs_site/_internal/frontend/src/${entry.source} by docs_site/_internal/frontend/scripts/build.mjs. Do not edit.`,
    },
  });
  return result.outputFiles[0].contents;
}

const generatedEntries = await Promise.all(entries.map(async (entry) => [entry, await generate(entry)]));

async function checkFile(path, expected, label) {
  let committed;
  try {
    committed = await readFile(path);
  } catch {
    console.error(`The committed ${label} is missing. Run pnpm --dir docs_site/_internal/frontend build.`);
    process.exitCode = 1;
    return;
  }
  if (!committed.equals(expected)) {
    console.error(`The committed ${label} is stale. Run pnpm --dir docs_site/_internal/frontend build.`);
    process.exitCode = 1;
  }
}

if (checkOnly) {
  // CI compares bytes so an authored-source change cannot leave stale bundles.
  for (const [entry, generated] of generatedEntries) {
    await checkFile(`${staticRoot}${entry.output}`, generated, entry.output);
  }
} else {
  // The check command detects any partial output left by an interrupted build.
  for (const [entry, generated] of generatedEntries) {
    const outputPath = `${staticRoot}${entry.output}`;
    await writeFile(outputPath, generated);
    console.log(`Wrote ${outputPath} (${generated.byteLength} bytes)`);
  }
}
