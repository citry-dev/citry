import { readdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { transform } from "lightningcss";
import { minify } from "terser";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../../../..");
const checkOnly = process.argv.slice(2).includes("--check");

const componentsRoot = resolve(
  repositoryRoot,
  "packages/py/citry_ui/citry_ui/components",
);

async function discoverAssets() {
  const entries = await readdir(componentsRoot, {
    recursive: true,
    withFileTypes: true,
  });
  return entries
    .filter((entry) => entry.isFile() && /\.source\.(css|js)$/.test(entry.name))
    .map((entry) => {
      const sourcePath = resolve(entry.parentPath, entry.name);
      const kind = entry.name.endsWith(".css") ? "css" : "js";
      return [sourcePath, kind];
    })
    .sort(([left], [right]) => left.localeCompare(right));
}

function outputPath(sourcePath, kind) {
  return sourcePath.replace(`.source.${kind}`, `.min.${kind}`);
}

async function compile(sourcePath, kind) {
  const source = await readFile(sourcePath, "utf8");
  if (kind === "css") {
    const result = transform({
      code: Buffer.from(source),
      filename: sourcePath,
      minify: true,
    });
    return `${result.code.toString().trimEnd()}\n`;
  }
  const result = await minify(source, {
    ecma: 2022,
    compress: { passes: 2 },
    mangle: true,
    format: { comments: false, semicolons: true },
  });
  if (!result.code) {
    throw new Error(`Terser produced no JavaScript for ${sourcePath}.`);
  }
  return `${result.code.trimEnd()}\n`;
}

const assets = await discoverAssets();
const stale = [];
for (const [sourcePath, kind] of assets) {
  const generatedPath = outputPath(sourcePath, kind);
  const generated = await compile(sourcePath, kind);
  if (checkOnly) {
    let current = null;
    try {
      current = await readFile(generatedPath, "utf8");
    } catch {
      // A missing output is reported with the same actionable rebuild command.
    }
    if (current !== generated) stale.push(generatedPath);
  } else {
    await writeFile(generatedPath, generated, "utf8");
  }
}

if (stale.length) {
  process.stderr.write(
    `Citry UI production assets are stale:\n${stale
      .map((path) => `- ${path.slice(repositoryRoot.length + 1)}`)
      .join("\n")}\n` +
      "Run `pnpm citry-ui:build-assets`.\n",
  );
  process.exitCode = 1;
}
